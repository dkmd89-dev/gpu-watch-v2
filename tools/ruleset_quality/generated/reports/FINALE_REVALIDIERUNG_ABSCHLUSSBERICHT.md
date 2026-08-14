# Abschlussbericht: Finale Read-only-Revalidierung vor Preishistorie-Update

**Erstellt:** 2026-08-14 · **Repo-HEAD:** `4311683` · **Charakter:** ausschließlich Analyse und
Validierung. Keine YAML-, Matcher-, Scoring- oder Preislogik-Änderung, keine `found.json`-,
`seen.json`- oder `price_history.jsonl`-Änderung, kein Commit, kein Push, kein Merge, kein PR.
Alle Aussagen aus frisch ausgeführten Skripten gegen den aktuellen Repository-Zustand, nicht aus
dem vorigen Bericht übernommen.

---

## A. Repository-Zustand (frisch verifiziert, nicht aus altem Bericht übernommen)

```text
Kategorien:      19
Regeln:          355
Ruleset-Signatur: acd510eb61845cb5  (identisch zum Stand nach PR #29 — seither KEINE Regeländerung)
Tests vorher:    1277 passed, 0 failed (Stand nach PR #29)
Tests nachher:   1296 passed, 0 failed (642,76s) — inkl. 19 neuer Tests für Gate v2
Rule Analyzer:   355 Regeln, 19 Kategorien, 0 Findings (Errors/Warnings/Infos)
```

Die Ruleset-Signatur ist **byteweise identisch** zum letzten Stand — bestätigt, dass seit dem
Merge von PR #29 keine Regeländerung stattgefunden hat. Jede in diesem Bericht gemessene
Abweichung stammt entweder aus dem Vergleich mit dem **historischen** Vor-Audit-Ruleset (Commit
`01afd5b`) oder aus reiner Korpus-Fluktuation (`found.json`/`price_history.jsonl`), nicht aus einer
Ruleset-Änderung in dieser Session.

---

## B. Snapshot

```text
Zeitpunkt:         2026-08-14T13:56:36Z
Einträge:          2500  (found.json ist seit Phase 19 von 2477 auf 2500 gewachsen — Live-Scanner
                    läuft weiter, bestätigt durch `git status`)
Ruleset-Signatur:  acd510eb61845cb5
Sichtbar:          2500 / 2500 (100,0%)
```

Neu eingefroren: `generated/baselines/baseline_20260814T135636Z_acd510eb61845cb5.json`.

**Wichtigster, in dieser Session neu gewonnener Befund:** Die Ground-Truth-Abdeckung des
*aktuellen* `found.json`-Korpus gegen den Forensik-Snapshot ist in den 3 Tagen seit Phase 19 von
**19,2% auf 0,6%** eingebrochen (16 von 2500 Einträgen gelabelt, davon 16× TRUE_POSITIVE, 0× FALSE_
POSITIVE/UNCLEAR). 12 der 19 Kategorien haben aktuell **0,0%** Ground-Truth-Abdeckung (u. a. gpu,
handhelds, office_pc, vintage_elektronik — vollständige Tabelle:
`generated/reports/category_quality_current.md`). Der `found.json`-Korpus ist damit als alleinige
Grundlage für eine TP/FP/UNCLEAR-Bewertung praktisch aufgebraucht — jede belastbare Aussage in
diesem Bericht stützt sich stattdessen auf den **historischen Regressionsvergleich** (Abschnitt C),
der unabhängig von der Korpus-Fluktuation ist.

---

## C. Benchmark

Datengrundlage: `docs/DASHBOARD_MATCH_FORENSICS.json` (2306 Einträge, Commit `01afd5b`,
2026-08-10, vor dem 19-Kategorien-Audit) erneut gegen das **aktuelle** Ruleset ausgewertet — über
`matcher.evaluate()` mit dem tatsächlichen gespeicherten Preis, niemals `price=0.0`.

```text
TP (vorher, Ground Truth): 2252
FP (vorher, Ground Truth):   19
UNCLEAR (vorher):            35
Precision (vorher) = TP/(TP+FP)             = 0,9916
False-Positive-Rate (vorher) = FP/(TP+FP)   = 0,0084
```

Formeln exakt wie im Auftrag definiert, keine alternative Definition verwendet.

---

## D. Regressionen (Regression-Gate v2, exakt nach vorgegebener Matrix)

```text
CRITICAL: 91   (TRUE_POSITIVE -> kein Treffer — objektiv bestätigt)
HIGH:     65   (TRUE_POSITIVE: Regelwechsel bei gleicher Kategorie, First-Match-Wins — objektiv
                bestätigt als Matchpfad-Änderung; ob daraus TRUE_POSITIVE->FALSE_POSITIVE/UNCLEAR
                folgt, ist NICHT automatisch entscheidbar, siehe Methodik-Hinweis unten)
MEDIUM:    0
LOW/INFO: 32   (12× FALSE_POSITIVE -> kein Treffer [Fix bestätigt], 7× FALSE_POSITIVE unverändert
                weiterhin aktiv, 13× UNCLEAR -> kein Treffer)
```

**Methodik-Hinweis (zentral, nicht verschweigen):** "TRUE_POSITIVE → FALSE_POSITIVE" im engeren
Sinn (derselbe Match, aber neu als falsch erkannt) ist aus `evaluate()` allein **nicht** ableitbar —
das würde eine komplette Neu-Labeling-Aufgabe voraussetzen, keine Regressionsmessung. Wo der
Match-Zustand **unverändert** ist (identische Kategorie UND identische Regel), gilt das alte Urteil
logisch zwingend weiter (der bewertete Gegenstand hat sich nicht geändert) — das ist automatisch
und sicher ableitbar. Wo sich der Matchpfad geändert hat, wird das als objektiver Fakt ausgewiesen
(HIGH/MEDIUM je nach vorherigem Status), aber **nicht** stillschweigend in ein neues TP/FP/UNCLEAR-
Urteil übersetzt — stattdessen `new_status = "MANUELLE_PRUEFUNG_NOETIG"`.

Da die Ruleset-Signatur seit Phase 19 unverändert ist (Abschnitt A), sind alle 91 CRITICAL- und 65
HIGH-Funde **identisch** zu den in Phase 19 bereits identifizierten und dort stichprobenartig gegen
`docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`/`docs/CROSS_CATEGORY_ROUTING_AUDIT.md` verifizierten Fällen
(office_pc-ThinkPad-/Aufrüstkit-Exclude, gaming_pc-Laptop-Exclude, vintage_elektronik-„Altes Foto“-
Exclude usw.) — **keine neuen, unbestätigten Regressionen** in dieser Session.

**Neu in dieser Session:** die 65 HIGH-Fälle wurden erstmals im Detail durchgesehen (nicht nur
gezählt). Zwei klar unterscheidbare Muster:

1. **iPhone-Fälle** (z. B. „iPhone 15 Pro 128 GB Titan Natur“, 350 €): identischer Preis, identisches
   Gerät — nur das Preis-Rating (⚠️ Okay/👍 Guter Preis → ★ Top-Deal) hat sich geändert. Ursache:
   der zugrundeliegende Marktpreis wird aus `price_history.jsonl` neu berechnet und verschiebt sich
   mit wachsendem Datenbestand — **kein First-Match-Wins-Problem**, sondern erwartetes Verhalten der
   marktpreisbasierten Bewertung.
2. **LEGO-Fälle** (z. B. „Lego Star Wars Minifiguren Konvolut“): echte Regel-/Modell-Konsolidierung
   zwischen dem historischen und dem aktuellen Ruleset (z. B. `LEGO Ninjago – Figuren-Konvolut` →
   `LEGO Minifiguren-Sammlung`). Stichprobe zeigt: `price_history_model` bleibt dabei überwiegend
   identisch (z. B. `lego_minifig_bundle` → `lego_minifig_bundle`) — reine Label-Umbenennung, kein
   Datenverlust. Deckt sich mit der in Abschnitt G gefundenen, umfangreicheren LEGO-Modell-
   Konsolidierung auf Preishistorie-Ebene.

---

## E. Cross-Category-Routing (Auftrag Abschnitt 8, empirisch über echte kategoriegefilterte `evaluate()`-Läufe)

```text
Untersuchte Listings (aktueller Korpus): 2500
Getestete Kategorien:                      19
Listings mit >1 möglicher Kategorie:       23  (0,9%)
```

| Gewinner-Kategorie | Überschattete Kategorie | Anzahl | Beispiel |
|---|---|---:|---|
| gaming_pc | office_pc | 21 | „Gaming PC AMD Ryzen 5 5500, RX 6500 XT, 8GB DDR4, SSD 250GB“ |
| controller | handhelds | 1 | „Steam Deck Oled gegen PS5 Standard Edition ohne Controller“ (Tausch-Angebot) |
| m2_ssd | sata_ssd | 1 | „MSI Gaming M.2 SSD 1TB mit Intel SSD Inside Sticker“ |

**Einordnung:** In allen 23 Fällen gewinnt die alphabetisch zuerst geladene Kategorie
(`discover_categories()` iteriert `sorted(*.yaml)`, siehe `app/categories/registry.py`) — und in
jedem Einzelfall ist das auch die **semantisch korrektere** Kategorie (ein Gaming-PC mit dedizierter
GPU sollte `gaming_pc` sein, nicht `office_pc`; eine M.2-SSD sollte `m2_ssd` sein, nicht `sata_ssd`).
Das ist aktuell **eher Zufall der alphabetischen Reihenfolge als eine bewusste Priorisierung** —
strukturelle Beobachtung, keine akute Fehlfunktion. Der eine `controller`/`handhelds`-Fall ist ein
Tausch-/Trade-Angebot, bei dem beide Kategorien nur schwach zutreffen — geringe Praxisrelevanz.

---

## F. Rule Changes / First-Match-Wins

```text
Regeländerungen seit letztem Bericht:  0  (Ruleset-Signatur unverändert, siehe Abschnitt A)
First-Match-Wins-relevante Fälle (historischer Vergleich): 65 (siehe Abschnitt D)
Auffällige Regeln (Rule Analyzer):     0
```

First-Match-Wins-Reihenfolge wird durch `sorted(rules_dir.glob("*.yaml"))` (alphabetisch nach
Dateiname) bestimmt, `category_order`/`scan_priority` steuert **nur** Anzeige/Scan-Gruppierung, nicht
die Matching-Reihenfolge — verifiziert in `app/matcher.py`/`app/categories/registry.py`. Innerhalb
einer Kategorie ist die Preis-Tier-Kaskade (Top-Deal → Guter Preis → Okay) die vorgesehene
Mehrfachregel-Struktur; `rule_analyzer.check_overlaps()` findet dort strukturell 0 unbeabsichtigte
Überschneidungen.

---

## G. Price-History-Simulation

Zwei komplementäre, rein lesende Läufe gegen den (seit Phase 19 gewachsenen) Korpus:

```text
historische Einträge:            15554  (Phase 19: 12365 — +3189 in 3 Tagen, Live-Scanner)
davon mit fingerprint:            14381
UNVERAENDERT:                     11603
NICHT_MEHR_GUELTIG:                1994
KATEGORIEWECHSEL:                   184
MODELLWECHSEL:                      600
nicht rekonstruierbar:              1173
```

**Modelle mit price_history_model-Ebene, Median/Spanne alt vs. neu, Schwellen-Warnungen**
(`generated/reports/price_history_revalidation_v2.json`, 125 Modelle gesamt, 9 mit Warnung):

| Modell | Samples alt | Samples neu | Warnung |
|---|---:|---:|---|
| **roehrenfernseher** | **96** | **3** | <5 UND <10 Samples — praktisch unbrauchbar |
| lego_bundle (Orphan) | 404 | 0 | vollständiger Datenverlust (erwartet, entfernte Kategorie) |
| playmobil_bundle (Orphan) | 210 | 0 | vollständiger Datenverlust (erwartet) |
| spielzeug_bundle_sonstige (Orphan) | 49 | 0 | vollständiger Datenverlust (erwartet) |
| gaming_laptop_rtx3060 | 34 | 5 | <10 Samples — **neu, nicht in Phase 19 erkannt** |
| gaming_laptop_rtx4060 | 20 | 5 | <10 Samples — **neu, nicht in Phase 19 erkannt** |
| rx_7600_xt | 12 | 4 | <5 UND <10 — bestätigt bekannte RX-7600/7600-XT-Restlücke |
| handheld_ps_vita | 9 | 3 | <5 Samples |
| controller_ps5_drift | 10 | 9 | knapp <10 (grenzwertig) |

**Kritisch markiert** (Auftrag: "TRUE_POSITIVE + price_history_model geändert" sowie
"Kategorie geändert"), via Fingerprint-Kreuzreferenz mit dem Ground-Truth-Label-Store
(`duplicate_detection.normalize_title()`, Single Source of Truth):

- **148 Datenpunkte**: Fingerprint gehört zu einem TRUE_POSITIVE-gelabelten Listing UND
  `price_history_model` hat sich geändert. Stichprobe zeigt: ganz überwiegend LEGO-Modell-
  Konsolidierung (`lego_bundle`→`lego_minifig_bundle`, `lego_ninjago_bundle`→`lego_minifig_bundle`,
  `lego_sw_rare`→`lego_ninjago_rare`) — plausibel, aber real und zahlenmäßig relevant für die
  spätere Revalidierung.
- **7 Datenpunkte**: Fingerprint gehört zu einem UNCLEAR-gelabelten Listing UND `price_history_model`
  hat sich geändert — ausnahmslos Nintendo-Switch-/Xbox-Pro-Controller-Angebote, die vorher gegen
  `konsole_switch_standard`/`konsole_xbox_one` gebucht wurden, jetzt aber (korrekt) gegen
  `controller_switch_pro`/`controller_xbox_series` matchen würden. Fachlich naheliegend richtig
  (ein Controller sollte nicht gegen Konsolen-Marktpreise bewertet werden), aber diese 7 Punkte waren
  bereits vorher UNCLEAR — sollten vor einer Revalidierung final geklärt werden, nicht während.

Erwartete Betroffenheit gesamt: 184 (Kategoriewechsel) + 600 (Modellwechsel) = 784 Datenpunkte, die
bei einer echten Revalidierung eine andere Zuordnung erhielten als beim Sammeln.

---

## H. Empfehlung

**1. Ist das Ruleset stabil genug?**
Ja. Ruleset-Signatur seit Phase 19 unverändert, 0 Rule-Analyzer-Findings, Cross-Category-Rate niedrig
(0,9%) und in allen Fällen semantisch korrekt aufgelöst.

**2. Gibt es CRITICAL- oder HIGH-Regressionen?**
Keine **neuen**. Die 91 CRITICAL + 65 HIGH sind identisch zu den bereits in Phase 19 identifizierten,
überwiegend bereits als gewollte Audit-Fixes eingeordneten Fällen (gleiches Ruleset, gleicher
historischer Vergleichspunkt). Die 65 HIGH-Fälle wurden diese Session erstmals im Detail
durchgesehen: kein First-Match-Wins-Defekt, sondern entweder marktpreisbedingte Rating-Verschiebung
(iPhone) oder bereits erfolgte, unschädliche Modell-Konsolidierung (LEGO).

**3. Gibt es relevante Cross-Category-Probleme?**
Nein akut (0,9%, korrekt aufgelöst), aber ein struktureller Hinweis: die Auflösung erfolgt über
Datei-Alphabet, nicht über eine explizite Priorität — funktioniert aktuell zufällig richtig,
verdient aber Aufmerksamkeit, falls neue Kategorien mit ähnlichem Namensraum hinzukommen.

**4. Gibt es relevante `price_history_model`-Änderungen?**
Ja, deutlich: 784 von 15554 historischen Punkten (5,0%) wären bei Revalidierung betroffen, davon
148 mit TRUE_POSITIVE- und 7 mit UNCLEAR-Ground-Truth-Bezug konkret identifiziert.

**5. Gibt es Modelle, die durch Rekategorisierung datenarm werden?**
Ja, 9 Modelle, angeführt von `roehrenfernseher` (96→3 Samples — das gravierendste Einzelrisiko im
gesamten Projekt) und den neu erkannten `gaming_laptop_rtx3060`/`rtx4060` (34→5, 20→5).

**6. Ist die Preishistorie bereit für eine kontrollierte Revalidierung?**
Für die große Mehrheit der 125 Modelle (116 ohne Schwellen-Warnung) ja. **Nicht pauschal** für alle:
`roehrenfernseher` braucht vor jeder Revalidierung eine gesonderte Entscheidung (nur noch 3 valide
Punkte); die 3 Orphan-Modelle (663 Punkte, `spielzeug_bundles`) benötigen laut STATUS.md ohnehin
einen separaten Freigabe-Schritt vor jeder Löschung/Migration; `gaming_laptop_rtx3060/4060` und
`rx_7600_xt` sollten einzeln geprüft werden.

**7. Was muss vorher noch geklärt werden?**
- Endgültige Entscheidung zu `roehrenfernseher`: eigenständiges, aktuell fast datenleeres Preismodell
  behalten oder mit einer verwandten Kategorie zusammenführen?
- Freigabe-Entscheidung für die 3 Orphan-Modelle aus `spielzeug_bundles` (STATUS.md, bereits
  bekannter offener Punkt).
- Finale Klärung der 7 UNCLEAR-Controller/Konsolen-Fälle, bevor ihre Preispunkte migriert werden.
- **Wichtigster Prozesspunkt:** Die Ground-Truth-Abdeckung des Live-Korpus zerfällt sehr schnell
  (19,2% → 0,6% in 3 Tagen). Eine Revalidierung sollte mit einer **frisch gezogenen, eigens für
  diesen Zweck gelabelten Stichprobe** arbeiten, nicht mit den Phase-19-Altlabels.

---

## Tests (Abschnitt 14)

```text
Vorher (Stand nach PR #29): 1277 passed, 0 failed
Nachher (diese Session):    1296 passed, 0 failed (642,76s) — 19 neue Tests für Gate v2
Rule Analyzer:              0 Findings (unverändert)
Rule Coverage / Benchmark:  erfolgreich ausgeführt, alle Reports unter generated/reports/
```

Keine Fehlschläge zu analysieren — nichts wurde automatisch "repariert".

---

## Sicherheitsabschluss (Abschnitt 16)

```text
app/rules/*.yaml       unverändert
app/matcher.py          unverändert
app/scoring/**          unverändert
data/found.json          unverändert (nur vom weiterhin laufenden Live-Scanner modifiziert, nicht
                          von dieser Session — verifiziert über `git status` vor/nach der Arbeit)
data/seen.json           unverändert (dito)
data/price_history.jsonl unverändert (dito, nur gelesen über read_price_points())
Commit:  keiner
Push:    keiner
Merge:   keiner
PR:      keiner
```

Neue/geänderte Dateien ausschließlich unter `tools/ruleset_quality/**` (neue Module:
`detailed_transition.py`, `cross_category_routing.py`, `quality_metrics.py`,
`price_history_revalidation_v2.py`, generierte Reports) und `app/tests/test_ruleset_quality_
detailed_transition.py` (19 neue Tests). Kein Commit erstellt — wartet auf ausdrückliche Freigabe.

**STOPP. Warte auf Freigabe.**
