# Abschlussbericht: Ruleset-Qualitätssystem (Phase 19.1–19.5)

**Erstellt:** 2026-08-11 · **Repo-HEAD:** `2691da6` · **Ruleset-Signatur (aktuell):** `acd510eb61845cb5`
**Charakter:** ausschließlich Analyse, Instrumentierung, Testaufbau. Keine YAML-, Matcher-, Scoring- oder
Preislogik-Änderung. Kein Commit. Alle Werkzeuge unter `tools/ruleset_quality/`, alle Ausgaben unter
`tools/ruleset_quality/generated/`.

---

## A. Projektzustand

```text
Kategorien:      19
Regeln:          355
Tests (vorher):  1241 passed (Stand STATUS.md, PR #25)
Tests (jetzt):   1277 passed, 0 failed (614,79s) — inkl. 20 neuer Tests für dieses Tooling
Rule Analyzer:   355 Regeln, 19 Kategorien, 0 Findings (Errors/Warnings/Infos)
```

Rule Analyzer real ausgeführt (`app/rule_analyzer.py::analyze_ruleset()`), nicht aus Dokumentation
übernommen: 0 unerreichbare Regeln, 0 Duplikate, 0 Exclude-Konflikte, 0 Überschneidungen — deckt sich
mit STATUS.md.

---

## B. Baseline (2.500er-Korpus)

**Wichtigster Befund der gesamten Analyse:** Die im Auftrag genannten Referenzzahlen
(TP 2252 / FP 19 / UNCLEAR 35, sichtbar 2306 von 2500) sind **verifiziert real**, stammen aber aus
`docs/DASHBOARD_MATCH_FORENSICS.json` — einem bereits im Repo vorhandenen Forensik-Snapshot von
**Commit `01afd5b`, 2026-08-10, VOR dem 19-Kategorien-Active-FP-Audit (PR #11–#28)**. Sie sind exakt
reproduzierbar aus dieser Datei, aber **nicht** identisch mit dem heutigen Live-Zustand:

```text
Heutiger found.json-Korpus:      2477 Einträge
Sichtbar (is_still_valid_category, echter Produktionspfad): 2335 (94,3%)
Überschneidung mit Forensik-Snapshot (URL-Basis):             476 (19,2%)
Neu seit Snapshot (kein Ground-Truth-Label):                 2001 (80,8%)
Aus dem Snapshot verschwunden (Alter/Delisting/Cleanup):      1830
```

`data/found.json` wird von einem laufenden Produktiv-Scanner kontinuierlich verändert (bestätigt durch
`git status`: Datei ist seit Sessionstart modifiziert) — ein "2.500er-Korpus" ist strukturell eine
Momentaufnahme, kein stabiler Datensatz.

**Neue Baseline eingefroren:** `generated/baselines/baseline_20260811T135259Z_acd510eb61845cb5.json`
— 2477 Einträge, Ruleset-Signatur `acd510eb61845cb5`, jeder Eintrag neu bewertet über
`matcher.evaluate()` + `category_validation.is_still_valid_category()` (echter Produktionspfad).
Ground-Truth-Verdict nur für die 476 überlappenden URLs übernommen (aus dem Label-Store, s.u.), Rest
ausdrücklich `UNLABELED`:

| | TRUE_POSITIVE | FALSE_POSITIVE | UNCLEAR | UNLABELED |
|---|---:|---:|---:|---:|
| heutige Baseline (2477) | 471 | 2 | 3 | 2001 |

**Historische Baseline zusätzlich rekonstruiert:** `generated/baselines/historical_forensics_baseline.json`
— alle 2306 Forensik-Einträge, plus die zugehörige Ruleset-Signatur **exakt neu berechnet** aus den
`app/rules/*.yaml`-Dateien zu Commit `01afd5b` (`git archive`, rein lesend, kein Checkout):
Signatur `1e7fcec77b51c375` (355 Regeln — Regelanzahl unverändert, nur Match-/Exclude-Bedingungen
innerhalb bestehender Regeln haben sich geändert, konsistent mit der additiven Fix-Methodik des Audits).

Ground-Truth-Label-Store (`generated/ground_truth_labels.json`): reiner Nachschlage-Store URL→Verdict,
keine neue Bewertungslogik. Für alle nicht enthaltenen URLs gilt ausdrücklich UNLABELED statt einer
Annahme.

---

## C. Benchmark

Zwei Läufe, beide über den echten Produktionspfad (`matcher.evaluate()`, keine zweite Matching-Logik):

### C.1 Selbstkonsistenz-Check (heutige Baseline vs. sich selbst, Ruleset unverändert)

```text
Eintraege: 2477 · Ruleset unveraendert: true (beide acd510eb61845cb5)
NEUTRAL: 2418 · INFO: 5 · CRITICAL: 53 · WARNING: 1
```

53 "CRITICAL"-Treffer bei **identischem** Ruleset wirken zunächst wie ein Tool-Fehler, sind es aber
nicht: Stichprobenprüfung (3 Einträge) zeigt, dass es sich durchweg um found.json-Datensätze handelt,
deren gespeicherte Kategorie **vor** einem späteren, bereits gemergten Rule-Fix (z. B. office_pc-
ThinkPad-Exclude, gaming_pc-Lenovo-IdeaPad-Exclude) gesetzt und seither nie erneut gescannt/
neubewertet wurde — `is_still_valid_category()` filtert das am Dashboard bereits korrekt heraus
(94,3% Sichtbarkeit), aber die physischen `found.json`-Datensätze bleiben stehen. Kein Fehler in
diesem Werkzeug, sondern eine reale, bereits durch die vorhandene Architektur (read-time-Filter statt
Datei-Mutation) abgefangene Alterungs-Erscheinung — siehe Abschnitt F.

### C.2 Echter Regressionsvergleich (Forensik-Snapshot vor Audit vs. aktuelles Ruleset)

```text
Eintraege: 2306 · Ruleset unveraendert: false (1e7fcec77b51c375 -> acd510eb61845cb5)
NEUTRAL (TP->TP stabil): 2096 (93,1% aller vormaligen TP)
CRITICAL (TP->kein Treffer): 91
HIGH_CANDIDATE: 72  [65x TP mit anderem Matchpfad, 7x FP weiterhin aktiv]
INFO: 47  [12x FP->kein Treffer, 13x UNCLEAR->kein Treffer, 22x UNCLEAR weiterhin unklar]
WARNING (Kategoriewechsel): 0
```

Stichprobenprüfung aller 91 CRITICAL-Titel (händisch gegen `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md` und
`docs/CROSS_CATEGORY_ROUTING_AUDIT.md` abgeglichen): Kategorieverteilung ist office_pc 61, gaming_pc 6,
controller 5, handhelds 5, konsolen_bundles 3, lego_minifiguren 2, vintage_elektronik 2,
autoradio_opel_corsa 2, netzteil 1, sata_ssd 1, retro_konsolen 1, ram 1, monitor_curved 1 — deckt sich
fast titelgenau mit den in beiden Audit-Dokumenten dokumentierten, bereits freigegebenen Fixes
(office_pc: 27 Aufrüstkit/Mainboard-Titel + ~34 ThinkPad/Notebook-Titel aus dem separaten
Cross-Category-Fix ≈ 61; gaming_pc Lenovo/MSI/HP-Gaming-Laptops; vintage_elektronik "Altes Foto";
autoradio "Multimedia"-OEM-Teile; ram "für Laptops"). **Diese CRITICAL-Treffer sind damit ganz
überwiegend keine unentdeckten Regressionen, sondern der Nachweis, dass bereits gemergte Fixes wirken**
— inklusive der Erkenntnis, dass der Forensik-Snapshot selbst an diesen Stellen ein (mittlerweile
überholtes) TRUE_POSITIVE-Label trug. Eine erschöpfende 1:1-Titel-Zuordnung wurde aus Aufwandsgründen
nicht automatisiert (das wäre wieder eine zweite Bewertungslogik) — für eine lückenlose Bestätigung
empfiehlt sich ein manueller Abgleich der 91 Titel in
`generated/reports/benchmark_historical_forensics_baseline.json` gegen die Audit-Doku.

Die 7 "FALSE_POSITIVE weiterhin aktiv"-Fälle decken sich der Größenordnung nach mit den in STATUS.md
dokumentierten "9 Muster / 27 Titel bewusst zurückgestellt" (P1/P2).

---

## D. Kategoriequalität

Aus `generated/reports/category_quality_current.md` (nur gelabelte Teilmenge fließt in
Precision/FP-Rate ein — Formeln: `Precision = TP/(TP+FP)`, `FP-Rate = FP/(TP+FP)`):

| Kategorie | Getestet | Sichtbar | TP | FP | UNCLEAR | Gelabelt (n) | Abdeckung % | Precision | FP-Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| autoradio_opel_corsa | 64 | 62 | 59 | 0 | 0 | 59 | 92,2 | 1,000 | 0,000 |
| controller | 97 | 91 | 44 | 0 | 0 | 44 | 45,4 | 1,000 | 0,000 |
| cpu_mainboard_bundle | 1 | 1 | 1 | 0 | 0 | 1 | 100,0 | 1,000 | 0,000 |
| gaming_pc | 29 | 23 | 7 | 0 | 0 | 7 | 24,1 | 1,000 | 0,000 |
| gpu | 68 | 68 | 7 | 0 | 0 | 7 | 10,3 | 1,000 | 0,000 |
| handhelds | 30 | 20 | 9 | 0 | 0 | 9 | 30,0 | 1,000 | 0,000 |
| iphone | 424 | 423 | 29 | 0 | 0 | 29 | 6,8 | 1,000 | 0,000 |
| konsolen_bundles | 161 | 158 | 44 | 0 | 3 | 47 | 29,2 | 1,000 | 0,000 |
| lego_minifiguren | 562 | 561 | 93 | 0 | 0 | 93 | 16,5 | 1,000 | 0,000 |
| m2_ssd | 3 | 3 | 1 | 0 | 0 | 1 | 33,3 | 1,000 | 0,000 |
| macbook | 82 | 82 | 12 | 0 | 0 | 12 | 14,6 | 1,000 | 0,000 |
| monitor_curved | 183 | 181 | 18 | 0 | 0 | 18 | 9,8 | 1,000 | 0,000 |
| netzteil | 105 | 100 | 16 | 0 | 0 | 16 | 15,2 | 1,000 | 0,000 |
| notebook_resell | 93 | 91 | 50 | 0 | 0 | 50 | 53,8 | 1,000 | 0,000 |
| office_pc | 78 | 30 | 45 | 1 | 0 | 46 | 59,0 | 0,978 | 0,022 |
| ram | 111 | 109 | 12 | 0 | 0 | 12 | 10,8 | 1,000 | 0,000 |
| retro_konsolen | 145 | 136 | 12 | 1 | 0 | 13 | 9,0 | 0,923 | 0,077 |
| sata_ssd | 103 | 100 | 6 | 0 | 0 | 6 | 5,8 | 1,000 | 0,000 |
| vintage_elektronik | 138 | 96 | 6 | 0 | 0 | 6 | 4,3 | 1,000 | 0,000 |
| **GESAMT** | **2477** | **2335** | **471** | **2** | **3** | **476** | **19,2** | **0,996** | **0,004** |

**Warnhinweis zur Lesbarkeit:** Precision 1,000 in 17/19 Kategorien bedeutet **nicht** "keine
Fehltreffer mehr", sondern "kein gelabelter Fehltreffer in einer oft sehr kleinen Stichprobe"
(z. B. vintage_elektronik: nur 6 von 138 aktuellen Treffern gelabelt = 4,3% Abdeckung). Die Zahl ist
für Kategorien mit <15% Abdeckung (gpu, iphone, monitor_curved, ram, retro_konsolen, sata_ssd,
vintage_elektronik) nicht belastbar interpretierbar.

Auffällig niedrige Sichtbarkeits-Quote (`sichtbar/getestet`): **office_pc 30/78 (38,5%)**,
vintage_elektronik 96/138 (69,6%), gaming_pc 23/29 (79,3%) — konsistent mit den in C.1/C.2 gefundenen
Alterungs-/Fix-Effekten in genau diesen Kategorien.

**Auffällige Regeln / Überschneidungen:** 0 (Rule Analyzer, siehe A). **Unbenutzte Regeln**
(`price_history_model` ohne jeden Datenpunkt in `price_history.jsonl`, über `rule_coverage.py`,
Single Source of Truth): 19 Modelle über 7 Kategorien — autoradio_opel_corsa (5), iphone (5),
macbook (3), cpu_mainboard_bundle (2), lego_minifiguren (2), m2_ssd (1), gpu (1, `rx_7600`, bereits als
Restlücke in STATUS.md dokumentiert). Weicht leicht von der historisch dokumentierten Zahl "22" ab
(Datenlage wächst kontinuierlich) — aktuell frisch gemessen, nicht aus Doku übernommen.

Gesamtbericht als JSON: `generated/reports/category_quality_current.json`,
`generated/reports/category_quality_historical_regression.json`.

---

## E. Preishistorie (nur Analyse, `price_history.jsonl` unverändert)

```text
historische Einträge:          12365
davon mit fingerprint (rekonstruierbar): 11192 (90,5%)
UNVERAENDERT:                  8555
NICHT_MEHR_GUELTIG:            1906
KATEGORIEWECHSEL:                181
MODELLWECHSEL:                   550
NICHT_REKONSTRUIERBAR:          1173 (kein fingerprint, ältere Zeilen)
```

**Einschränkung, explizit:** `PricePoint` speichert nur `category`+`model`, kein `rule_label` — "alte
Regel"/"neue Regel" ist daher nur auf Kategorie-/Modell-Ebene nachvollziehbar, nicht auf
Einzelregel-Ebene.

**Potenziell betroffene historische Einträge:** 181 (Kategoriewechsel) + 550 (Modellwechsel) = 731
Einträge, die bei einer echten Revalidierung eine andere Zuordnung erhielten als beim Sammeln.

**Betroffene Kategorien (Top-Kategoriewechsel):** `spielzeug_bundles → lego_minifiguren` (88, aus der
bereits bekannten, entfernten Kategorie), `office_pc → cpu_mainboard_bundle` (26), `office_pc →
notebook_resell` (16), `notebook_resell → gpu` (14), `konsolen_bundles → controller` (13).

**Betroffene price_history_models mit bekannten False-Positive-Indikatoren** (Anteil historischer
Punkte, die bei Neubewertung nicht mehr zu Kategorie+Modell passen — **kein automatisches
TP/FP-Urteil**, sondern der bereits produktive `rule_coverage.py`-Mechanismus):

| Kategorie | Modell | Sample | FP-Indikatoren | Rate |
|---|---|---:|---:|---:|
| lego_minifiguren | lego_ninjago_bundle | 568 | 405 | 71,3% |
| retro_konsolen | nintendo_retro_konsole | 670 | 378 | 56,4% |
| retro_konsolen | sony_retro_konsole | 705 | 320 | 45,4% |
| vintage_elektronik | vintage_hifi_verstaerker | 471 | 202 | 42,9% |
| office_pc | office_pc | 216 | 95 | 44,0% |
| lego_minifiguren | lego_sw_rare | 109 | 90 | 82,6% |
| **vintage_elektronik** | **roehrenfernseher** | **81** | **78** | **96,3%** |

**Risiken (Auftrags-Checkliste):**
- *historische Daten falsch zugeordnet:* ja, 181 Kategoriewechsel real gemessen (Tabelle oben).
- *`price_history_model` ändert sich unerwartet:* ja, 550 Modellwechsel, größtenteils LEGO-
  Rekalibrierung (`lego_sw_rare`→`lego_ninjago_rare`/`lego_promo`/`lego_cmf`) und RAM-Größenklassen.
- *Modelle verschiedener Kategorien werden zusammengeführt:* kein Fall beobachtet, in dem zwei
  unterschiedliche AKTUELLE Kategorien auf dasselbe Modell zusammenlaufen — nur Kategoriewechsel
  einzelner Punkte.
- *alte False Positives beeinflussen weiterhin Marktpreise:* ja, akut — `roehrenfernseher` mit 96,3%
  FP-Indikator-Rate ist der gravierendste Einzelfall im ganzen Projekt (deckt sich mit dem in
  STATUS.md als "größter Einzelfund" dokumentierten vintage_elektronik-Audit).
- *echte historische Treffer gehen verloren:* 1906 Punkte (15,4% aller Punkte, 17,0% der
  rekonstruierbaren) matchen aktuell gar nicht mehr.
- *kleine Samples werden durch Rekategorisierung unbrauchbar:* 1 betroffenes Modell mit <5 Samples
  (`iphone_13_mini_512gb`) — geringes Risiko in der Breite.

Vollständiger Bericht: `generated/reports/price_history_revalidation_simulation.json`.

---

## F. Gefundene Optimierungsmöglichkeiten (nicht umgesetzt)

**CRITICAL**
- Keine.

**HIGH**
- `vintage_elektronik/roehrenfernseher`-Marktpreis basiert zu 96,3% auf Punkten, die gegen das
  aktuelle Ruleset nicht mehr matchen (Sammlerfotos/Ersatzteile aus der Zeit vor dem Audit-Fix). Jede
  Markpreis-/Resale-Berechnung, die diesen Datenpool nutzt, ist mit hoher Wahrscheinlichkeit verzerrt.
  **Empfehlung:** Priorität 1 für die geplante kontrollierte Preishistorie-Revalidierung.
- `lego_minifiguren/lego_ninjago_bundle` (71,3%) und `lego_sw_rare` (82,6%) — ähnliches Muster, zweiter
  Kandidat für die Revalidierung.
- Ground-Truth-Label-Store (`docs/DASHBOARD_MATCH_FORENSICS.json`) enthält nachweislich mindestens
  einen falsch-positiven TRUE_POSITIVE-Eintrag (Lenovo IdeaPad Gaming 3, seither als echter FP
  bestätigt und gefixt) — die 2252 TP-Labels sollten vor jeder Nutzung als Trainings-/Testgrundlage
  gegen `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md` re-annotiert werden, nicht blind übernommen werden.

**MEDIUM**
- Ground-Truth-Abdeckung des aktuellen Korpus liegt bei nur 19,2% — für eine belastbare
  Precision-Aussage je Kategorie fehlt in 12 von 19 Kategorien eine ausreichende gelabelte
  Stichprobe (<30%). Ohne neue menschliche Labels bleibt jede künftige Precision-Zahl auf denselben
  476 Alt-Einträgen sitzen, die selbst weiter aus dem Korpus herausaltern.
- 142 `found.json`-Einträge (5,7%) sind aktuell laut `is_still_valid_category()` nicht mehr sichtbar,
  bleiben aber physisch in der Datei stehen (Alterungseffekt, siehe C.1) — funktional unkritisch
  (Dashboard filtert korrekt), aber ein Kandidat für eine spätere, separat zu beauftragende
  Aufräum-Routine.
- 731 `price_history.jsonl`-Punkte (Kategorie-/Modellwechsel) sollten vor jeder Marktpreis-Neuko-
  Kalibrierung gesondert betrachtet werden, nicht pauschal gelöscht oder übernommen.

**LOW**
- 19 Regeln ohne jeden Datenpunkt (Tabelle Abschnitt D) — reine Beobachtung, konsistent mit
  bestehender Dokumentation ("Nischenregeln weiter beobachten").
- 3 Orphan-Modelle aus `spielzeug_bundles` mit 663 Datenpunkten (404+210+49, exakt reproduziert) —
  bereits bekannt und laut STATUS.md bewusst nicht ohne separaten Auftrag zu löschen.

Keine dieser Beobachtungen wurde umgesetzt — ausschließlich dokumentiert, wie im Auftrag gefordert.

---

## G. Empfehlung

**1. Ist das aktuelle Ruleset bereit für eine Preishistorie-Revalidierung?**
Ja, mit Einschränkung: Die Simulation (Abschnitt E) zeigt klar verwertbare, konkrete Kandidaten
(`roehrenfernseher`, `lego_ninjago_bundle`, `lego_sw_rare`, `office_pc`). Das Ruleset selbst ist über
den historischen Regressionsvergleich (C.2) gut abgesichert (93,1% TP-Stabilität, 0 unerwartete
Kategoriewechsel). Eine Revalidierung sollte mit den HIGH-Kandidaten aus Abschnitt F beginnen.

**2. Gibt es noch Regressionen?**
Keine unbestätigten. Die 91 CRITICAL-Treffer aus C.2 sind bei Stichprobenprüfung nahezu vollständig
bereits bekannte, gewollte Audit-Fixes — keine neu entdeckten, unbeabsichtigten Verluste. Eine
lückenlose 1:1-Bestätigung aller 91 Titel steht noch aus (siehe C.2, letzter Satz) und wäre der
nächste sinnvolle Verifikationsschritt vor einer abschließenden Freigabe dieser Aussage.

**3. Welche Kategorien sind noch auffällig?**
`office_pc` (niedrigste Sichtbarkeits-Quote, 38,5%, hoher Anteil gealterter Einträge),
`vintage_elektronik` (69,6% Sichtbarkeit, höchste bekannte FP-Rate in der Preishistorie),
`retro_konsolen` (einziger zweiter Fall mit gelabeltem FP im aktuellen Korpus, dazu 56,4%/45,4%
FP-Indikator-Raten in der Preishistorie).

**4. Welche Änderungen wären sinnvoll?**
Menschliche Nachlabelung eines frischen, größeren Samples (aktuell nur 19,2% Abdeckung) sowie die in
Abschnitt F skizzierte, gesondert zu beauftragende Preishistorie-Revalidierung für die vier
HIGH-Kandidaten — beides jeweils als eigener, einzeln freizugebender Schritt (CLAUDE.md Regel 10).

**5. Welche Änderungen sollten NICHT vorgenommen werden?**
Keine automatische Bereinigung von `price_history.jsonl` oder `found.json` auf Basis der
FP-Indikator-Raten — das wäre eine automatische Regelreparatur/Datenmigration, die der Auftrag
ausdrücklich ausschließt. Keine Übernahme der 2252 TP-Labels aus dem Forensik-Snapshot als neue,
unhinterfragte Ground Truth (siehe F, HIGH-Punkt 3).

**6. Ist der Benchmark ausreichend reproduzierbar?**
Ja: Ruleset-Signatur (`compute_ruleset_signature()`, bereits produktiv) macht jeden Baseline-/
Benchmark-Lauf eindeutig einem Regelstand zuordenbar; der Selbstkonsistenz-Check (C.1) bestätigt, dass
bei unverändertem Ruleset auch die Match-Zustände unverändert reproduzierbar sind (die dort
beobachteten 53 CRITICAL-Fälle sind auf Dateningen im `found.json`-Korpus zurückzuführen, nicht auf
Nichtdeterminismus im Werkzeug). Historische Baseline ist über `git archive` exakt und beliebig oft
reproduzierbar. 20 dedizierte Tests für die Klassifikationslogik grün, volle Suite weiterhin
1277/1277 grün.

---

## Geänderte/neue Dateien (kein Commit)

```text
tools/ruleset_quality/__init__.py
tools/ruleset_quality/common.py
tools/ruleset_quality/label_store.py
tools/ruleset_quality/baseline.py
tools/ruleset_quality/historical_baseline.py
tools/ruleset_quality/benchmark.py
tools/ruleset_quality/category_report.py
tools/ruleset_quality/price_history_revalidation.py
tools/ruleset_quality/generated/**  (Baselines, Reports, Label-Store — Diagnoseartefakte)
app/tests/test_ruleset_quality_tooling.py  (20 neue Tests, alle grün)
```

Keine Datei unter `app/rules/`, `app/matcher.py`, `app/scoring/`, `data/*.json(l)` wurde erstellt,
verändert oder gelöscht. `data/found.json`/`data/gpu_watch.log.*`/`data/price_history.jsonl` zeigen in
`git status` Änderungen, die ausschließlich vom weiterhin laufenden Produktiv-Scanner stammen, nicht
von dieser Session.
