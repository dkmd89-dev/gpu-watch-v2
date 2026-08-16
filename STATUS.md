# STATUS — Aktueller technischer Projektstatus

> **Stand:** 2026-08-16
> **Repository:** `dkmd89-dev/gpu-watch-v2`
> **Branch:** `main`
> **Letzter Code-Commit auf `main` (remote):** `75e0b82` (Merge PR #56)
> **Category Recall Gate:** `CATEGORY_RECALL_MAXIMALLY_SECURED` (siehe Abschnitt 1a)
> **Technische Referenz:** `TECHNISCHER_PROJEKTSTATUS.md`
> **Vollständige Batch-Historie (wortgetreu):** `docs/STATUS_HISTORY.md`

---

## 1. Gesamtstatus

**Stabil / aktiv weiterentwickelbar.** Seit dem letzten dokumentierten Stand (`9ec8f86`, PR #44)
wurden Batch 19 (Forensics-Tool, PR #45–46), Batch 20 (PR #47–51) und Batch 21 (PR #52) gemergt:

- **Batch 19** (bereits vollständig dokumentiert): Category-False-Positive-Forensics-Tool +
  priorisierte Fix-Queue (PR #45), Wiederherstellung einer versehentlich gelöschten
  `konsolen_bundles.yaml` (PR #46).
- **Batch 20** (bereits vollständig dokumentiert): die Fix-Queue aus Batch 19a wurde vollständig
  abgearbeitet — `iphone`-Mainboard-Fehltreffer und PS4/PS5-HDMI-Reparatur-Fehltreffer per YAML
  gefixt (PR #47–48), Ground-Truth-Snapshot und aktueller Routing-Zustand sauber als zwei getrennte
  Dimensionen modelliert statt vermischt (PR #49–50), und die verbleibenden 35 historisch
  UNCLEAR-Fälle forensisch klassifiziert (PR #51): 11× vermutlich echter Treffer, 23× vermutlich
  Fehltreffer, 1× Manual-Review.
- **Batch 21** (neu in dieser Aktualisierung): die 23 `LIKELY_FALSE_POSITIVE`-Kandidaten aus
  Batch 20e wurden root-cause-geclustert (7 Cluster, `unclear_fp_root_cause_analysis.{json,md}`) und
  gegen die 11 `LIKELY_TRUE_POSITIVE`-Gegenbeispiele geprüft, **bevor** irgendeine YAML-Änderung
  erfolgte. Ergebnis: 20/23 Kandidaten waren durch frühere Batches bereits gelöst (keine Aktion
  nötig), 2/23 wurden gezielt neu gefixt (`konsolen_bundles.yaml`: „Split Pad Pro"- und
  „Joy-Con Set"-Fehltreffer, PR #52), 1/23 (RDR2/PS4-Steelbook-Bundle) bewusst **nicht** gefixt —
  „bundle" ist dort gleichzeitig Trigger- und Verstärkungssignal für 3 echte Treffer, bleibt
  Manual-Review.

Ergebnis: von den ursprünglich 19 historisch bestätigten FALSE_POSITIVE-Fällen sind weiterhin **16
gelöst**, 3 bewusst offen (2 Ground-Truth-Konflikt, 1 Manual-Review) — unverändert zu Batch 20, da
Batch 21 die 35 UNCLEAR-Fälle betrifft, ein separates Set. Von den 23 UNCLEAR-
`LIKELY_FALSE_POSITIVE`-Kandidaten sind jetzt **22/23 gelöst** (20 bereits vorher, 2 neu in
Batch 21), 1 bewusst offen.

Seither zwei weitere Batches (PR #53–54, neu in dieser Aktualisierung):

- **Batch 22** (PR #53): Resale-/Profit-Audit auf echten Produktivdaten identifizierte 3 live
  bestätigte, Profit-verzerrende Matching-Fehler; Root-Cause-Audit + gezielter Fix in 3
  unabhängigen Kategorien (`konsolen_bundles`: „pro Stück"-Spiele-Einzelverkauf,
  `vintage_elektronik`: „Hefte"-Zeitschriftenkonvolut, `monitor_curved`: „Teildefekt"-Kompositum-
  Wortgrenzenbug). 8 neue Tests, 0 Regressionen gegen den vollständigen 2306-Eintrag-Ground-Truth-
  Korpus. Ein bewusst akzeptierter Ground-Truth-Konflikt (2 „PS4 Spiele...pro Stück"-Fälle,
  analog zum bereits dokumentierten Switch/Xbox-Artefakt aus Batch 20b).
- **Batch 23** (PR #54): Notebook-Recall-Optimierung nach vorgelagerter 99-TRUE_POSITIVE-Recall-
  Forensics (Analyse-Phase, keine Codeänderung — identifizierte 43 bestätigte Recall-Gaps, davon
  42 im Notebook-Resale-Bereich). Davon 21 Gaps gezielt geschlossen: ThinkPad-Preisgrenze
  datenbasiert 240€ → 330€ (11), Wortgrenzen-/Modellcode-Lücken „T490s"/„T14s"/„E15" (7), neue
  Regel „Gaming Laptop (GTX 1650)" (2), neue Marken-Regeln Dell Latitude/ACEMAGIC/Lenovo V330 (5,
  jeweils nur für Titel mit explizitem „laptop"/„notebook"-Wort — Architektur- und
  Preisbasis-kritische Fälle wie „L480"/„L590", GTX 1650 Ti/RTX 2060/RTX 4070, HP (generic)
  bewusst zurückgestellt). Jede Änderung einzeln blast-radius-geprüft, 23 neue Tests, 1
  bestehender Test korrigiert (überholte Nebenerwartung). Vollständige Details:
  `docs/STATUS_HISTORY.md`, Batch 20–23.
- **Batch 24** (`8016eea`/`e7e1919`, ohne PR direkt auf `main`): `app/matcher.py` (1317 Zeilen)
  in das Package `app/matcher/` modularisiert (`core.py`, `text_matching.py`, `vram.py`,
  `hardware_requirements.py`, `score_bridge.py`, `rules_io.py`) — reine Strukturänderung,
  Ruleset-Signatur vor/nach identisch. Die alte `app/matcher.py` blieb zunächst als Datei
  liegen und wurde erst in Batch 25 final entfernt.
- **Batch 25** (PR #55, `471795a`/`fe05a72`, neu in dieser Aktualisierung): drei weitere
  additive Notebook-Recall-Gap-Fixes in `notebook_resell.yaml`, jeweils per vollständigem
  2306-Eintrag-Korpus-Diff und Adversarial-Test abgesichert: ThinkPad „L480"/„L590" (Marken-Gate
  um die Modellcodes selbst erweitert — Titel enthalten „ThinkPad" nicht wörtlich, damit den in
  Batch 23 dokumentierten Zurückstellungsgrund aufgelöst), „Lenovo IdeaPad Gaming 3" (Gerätewort-
  Gate um das eng gefasste Zwei-Wort-Signal „ideapad gaming" erweitert, GPU-Gate bleibt zwingend),
  Dell Latitude 5500/5501/7400 (feste, korpus-verifizierte Modellcode-Liste als Gerätewort-
  Alternative — Varianten mit generischer Zahlenerkennung bestanden den Adversarial-Test nicht).
  Zusätzlich: veraltete `app/matcher.py` final entfernt (Batch 24 nachgeholt), Ruleset-Quality-
  Reports/Baseline aktualisiert, `.gitignore` um `data/*.log`/`data/seen.json` ergänzt (bisher
  fehlende Ausschlussregel für Laufzeitdaten). 40 zielgerichtete + 68 kategorie-bezogene Tests
  grün; volle Suite in dieser Aktualisierung nicht erneut ausgeführt (keine explizite Freigabe in
  diesem Schritt).
- **Batch 26** (PR #56, `62fd678`/`75e0b82`, neu in dieser Aktualisierung): „Category Recall
  Maximal Absichern"-Workflow — systematische Prüfung aller verbleibenden 69 unmatched
  TRUE_POSITIVE-Fälle plus der 24 unmatched UNCLEAR-Fälle, bevor irgendeine Preis-/Profit-
  Validierung beginnt. Ergebnis: 1 echter, technisch klarer Recall-Gap gefunden und gefixt
  (`konsolen_bundles.yaml`: „OVP"-Kontext-Guard-Lücke — „1./2. Generation" fehlte inkonsistent in
  der `exclude_category_unless_also_contains["ovp"]`-Liste, „1 TB"/„2 TB" mit Leerzeichen wurde
  nicht als „1tb"/„2tb" erkannt; markengebundene Phrasen statt bare Begriffe nach Adversarial-Test
  2 Kollisionen aufdeckte). Löst 2 UNCLEAR-Fälle (125€, 80€), 0 Kollateralschäden im vollen
  2306-Eintrag-Korpus, 84/84 kategoriebezogene Tests grün. Alle übrigen 4 geprüften Cluster
  (Aufrüstkit 28, konsolen_bundles Zubehör 6, controller Zubehör 6, handhelds 6, retro_konsolen 3,
  lego_minifiguren 2, autoradio_opel_corsa 2, iPhone 1, RAM 1) erwiesen sich bei näherer Prüfung
  als bereits bewusste, dokumentierte Ground-Truth-Konflikte — die jeweiligen Excludes
  funktionieren korrekt, keine YAML-Änderung vorgesehen. 4 weitere Einzelfälle (netzteil,
  sata_ssd, vintage_elektronik, monitor_curved) als reine GT-Kategorie-Fehlzuordnungen
  identifiziert (kein Matcher-Fix technisch sinnvoll möglich). Alle 69 unmatched TRUE_POSITIVE-
  Fälle sind damit vollständig klassifiziert — Ergebnis: **`CATEGORY_RECALL_MAXIMALLY_SECURED`**
  (Details: Abschnitt 1a).

## 1a. Category Recall Gate (Batch 26, abgeschlossen)

```text
HEAD: 75e0b82 (Merge PR #56)
Ruleset-Signatur: 09d66cde97932a9f
Rule Analyzer: 0 Findings
TP: 2252 gesamt / 2183 matched (69 unmatched, alle klassifiziert)
FP: 19 gesamt / 3 matched
UNCLEAR: 35 gesamt / 13 matched (22 unmatched, alle klassifiziert)
Letzter Full-Corpus-Diff (PR #56): 2 Aenderungen, 0 Kollateralschaeden
```

Alle 69 unmatched TRUE_POSITIVE-Fälle einzeln geprüft und einer von fünf Endzuständen zugeordnet:

| Klasse | Anzahl | Beispiele |
|---|---:|---|
| Gefixt (Batch 26) | 2 (UNCLEAR) | konsolen_bundles OVP-Kontext-Guard, PR #56 |
| GT-Konflikt (bewusste, dokumentierte Excludes greifen korrekt) | 54 | Aufrüstkit (28), konsolen_bundles (6), controller (5), handhelds (6), retro_konsolen (3), lego_minifiguren (2), autoradio_opel_corsa (2), iPhone (1), RAM (1) |
| Design-Entscheidung offen (vollständig analysiert) | 3 | HP generic (2, `NEEDS_DESIGN_DECISION`), HP ZBook (1, `NEEDS_DEFINITION`) |
| Technisch nicht sicher lösbar (`BLOCKED`) | 2 | Alienware, Fujitsu Lifebook |
| Fehlende Datenbasis | 6 | GPU-Tier-Lücken (3), IdeaPad 5 (2), VOYEE-Controller (1) |
| GT-Kategorie-Fehlzuordnung (kein Matcher-Fix möglich) | 4 | netzteil→Audio-Verstärker, sata_ssd→externe USB-SSD, vintage_elektronik→Foto, monitor_curved→Heimtrainer |

**Status: `CATEGORY_RECALL_MAXIMALLY_SECURED`.** Keine unerklärten Cluster mehr vorhanden. Die
HP-Design-Entscheidungen (`NEEDS_DESIGN_DECISION`/`NEEDS_DEFINITION`) bleiben bewusst separat
offen und **blockieren das Recall-Gate nicht** — sie sind vollständig analysiert, die
verbleibende Entscheidung ist eine Business-/Produktfrage, keine technische. **Nächster
Haupt-Workstream: Price Validation / Profit Validation** (siehe Abschnitt 5, P0).

## 2. Verifizierter Stand

```text
main: 75e0b82 (Merge PR #56, HEAD dieser Aktualisierung)

Batch 26 (PR #56, 62fd678): konsolen_bundles.yaml OVP-Kontext-Guard-Fix +
  vollstaendiger Category-Recall-Gate-Abschluss. 2 UNCLEAR-Faelle recovered,
  0 Kollateralschaeden. Alle 69 unmatched TRUE_POSITIVE-Faelle klassifiziert.
  Ergebnis: CATEGORY_RECALL_MAXIMALLY_SECURED. 84/84 kategoriebezogene Tests
  gruen. Signatur 0a9c9f4bb3590872 -> 09d66cde97932a9f.


Batch 24 (8016eea/e7e1919, direkt auf main): matcher.py -> app/matcher/-Package
  modularisiert, reine Strukturaenderung, Signatur unveraendert.

Batch 25 (PR #55, 471795a): 3 additive Notebook-Recall-Gap-Fixes in
  notebook_resell.yaml -- ThinkPad L480/L590 (Marken-Gate-Erweiterung),
  IdeaPad Gaming 3 (Geraetewort-Gate-Erweiterung "ideapad gaming"), Dell
  Latitude 5500/5501/7400 (Modellcode-Liste als Geraetewort-Alternative).
  Alte app/matcher.py final entfernt. Jede Aenderung einzeln gegen den
  vollstaendigen 2306-Eintrag-Korpus verifiziert: 0 unerwartete
  Routing-Aenderungen. 40 zielgerichtete + 68 kategoriebezogene Tests gruen.
  Volle Suite in diesem Schritt NICHT erneut ausgefuehrt (keine explizite
  Freigabe).

Batch 22 (PR #53): 3 Profit-verzerrende Matching-Fehler behoben --
  konsolen_bundles.yaml ("pro stueck"-Exclude), vintage_elektronik.yaml
  ("hefte"-Exclude), monitor_curved.yaml ("teildefekt"-Exclude, lokal, NICHT
  global -- "teildefekt" ist in iphone/retro_konsolen ein TRUE_POSITIVE-Marker).
  8 neue Tests. Vollkorpus-Regression: 0 unerwartete Aenderungen, 1 bewusst
  akzeptierter Ground-Truth-Konflikt (2 "PS4 Spiele...pro Stueck"-Faelle).

Batch 23 (PR #54): Notebook-Recall-Optimierung, 21 von 43 im vorgelagerten
  99-TRUE_POSITIVE-Recall-Forensics-Audit bestaetigten Gaps geschlossen --
  ausschliesslich notebook_resell.yaml:
  - ThinkPad-Preisgrenze "Guter Preis" 240€ -> 330€ (11 Faelle, datenbasiert
    kalibriert auf hoechsten real bestaetigten Preis).
  - "T490s"/"T14s" ergaenzt (Wortgrenzen-/Kompositum-Bug in _contains_term(),
    kein neues Modell), "ThinkPad E15" ergaenzt (7 Faelle).
  - Neue Regel "Gaming Laptop (GTX 1650)" (2 Faelle, Preisbasis 3 GT-Faelle).
  - Neue Marken-Regeln Dell Latitude/ACEMAGIC/Lenovo V330 (5 Faelle, nur
    Titel mit explizitem "laptop"/"notebook"-Wort).
  Bewusst zurueckgestellt (dokumentiert, nicht Teil dieses Batches):
  "L480"/"L590" (fehlendes "ThinkPad"-Wort im Titel), GTX 1650 Ti/RTX
  2060/RTX 4070 (je nur 1 GT-Datenpunkt, keine belastbare Preisbasis),
  HP (generic, Cross-Category-Risiko ueber A10/Zbook nicht kontrollierbar),
  7 Faelle ohne Geraetewort, A10-Workstation-Grenzfall.
  23 neue Tests, 1 bestehender Test korrigiert (ueberholte Nebenerwartung,
  siehe docs/STATUS_HISTORY.md Batch 23). Jede Aenderung einzeln
  blast-radius-geprueft gegen den vollstaendigen 2306-Eintrag-Ground-Truth-
  Korpus, kumuliert 0 unerwartete Routing-Aenderungen.

Rule Analyzer (verifiziert nach Batch 26):
360 Regeln
19 Kategorien
0 Findings
Ruleset-Signatur: 0a9c9f4bb3590872 -> 09d66cde97932a9f (konsolen_bundles.yaml in
  Batch 26 um 6 markengebundene OVP-Kontext-Phrasen erweitert)

TP/FP/UNCLEAR (verifiziert nach Batch 26):
TP: 2252 gesamt / 2183 matched
FP: 19 gesamt / 3 matched
UNCLEAR: 35 gesamt / 13 matched (vorher 11)

Zielgerichtete Tests (verifiziert nach Batch 26):
pytest app/tests/ -k konsolen_bundles -q -> 84 passed, 1448 deselected

data/found.json: laufender Produktivbetrieb (Scanner aktiv), nicht Teil dieser
  Doku-Aktualisierung -- Zaehlung daher bewusst nicht erneut ausgewiesen.
```

**Volle Suite zuletzt vollständig ausgeführt und grün: 1509/1509 (Batch 23).** In Batch 25/26 wurden
gezielt die jeweils relevanten Tests ausgeführt (CLAUDE.md Abschnitt 3, Punkt 4.4); die
volle Suite läuft ausschließlich nach expliziter Nutzer-Freigabe.

## 3. Batch-Übersicht (1–19)

Kompakte Referenz. Vollständige Analyse, Root-Cause-Herleitung und Blast-Radius-Nachweise je
Batch: **`docs/STATUS_HISTORY.md`**.

| # | Batch | Ergebnis | Tests danach | Ref. |
|---|---|---|---|---|
| 1 | Cross-Category-Routing-Audit | unverändert, siehe vorheriger Stand | — | PR #26–28 |
| 2 | Ruleset-Qualitätssystem Aufbau | Baseline/Benchmark/Reports aufgebaut, 3 Entscheidungen geklärt | — | PR #29 |
| 3 | 251-Listing-Worksheet gelabelt + 3 Exclude-Fixes | 217 TP/21 FP/13 UNCLEAR, 4 Strukturmuster identifiziert | 1305/1305 | PR #31, `c577207` |
| 4 | Menschlich verifiziertes Labeling | Listings 1–30 einzeln, 31–251 pauschal bestätigt | — | — |
| 5 | Umlaut-Fingerprint-Fix | `normalize_title()` erhält ä/ö/ü/ß, nur für künftige Zeilen | +4 | `c9967ba` |
| 6 | `lego_bundle`-Migration/-Bereinigung | 5 migriert, 655 gelöscht, 3 bewusst erhalten | — | — |
| 7 | Preishistorie-Revalidierung v3 (read-only) | 15 Kategorien verlässlich, 4 Kategorien nicht rückwirkend beurteilbar | — | — |
| 8 | Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation | 4 unabhängige Root Causes, je gezielt gefixt | +6, 1315/1315 | — |
| 9 | `controller`/`ladekabel`-Restlücke | Lücke betraf Lade-Stationen, nicht den Kabel-Mechanismus | +4, 73 controller | — |
| 10 | `RX 7600 XT`/`RX 7600` + 4 weitere GPU | `min_vram_gb`-Default-Bug bei 5 Modellen ohne eigenes VRAM-Limit | +10, 54 gpu | — |
| 11 | Scan-Performance gemessen + Scraping parallelisiert | 88,9% Zeitanteil war seriell, jetzt `ThreadPoolExecutor` | +3, 1332/1332 | — |
| 12 | Persistence-Batching | `seen.json`/`found.json` batched statt pro Event, Tradeoff: bis 5s Risikofenster | +2, 1334/1334 | — |
| 13 | Batch 11+12: reale Wirkung verifiziert | Scan 56,4% schneller (12,4 statt 28,5 min), Persistence 89% schneller | — | — |
| 14 | Kategorie-Audit (read-only) + Live-FP-Fixes + Preis-Guard | 5 Fehltreffer über 3 Kategorien, `price<=0`-Guard in `app.py` | +15, 1337/1337 | — |
| 15 | „pro"-Kollision `konsolen_bundles` gelöst | 3 unabhängige Ursachen (Bindestrich-Schreibweise, MixAmp, Vertical Stand) | +6, 1355/1355 | — |
| 16 | 3 verbleibende Batch-14-Punkte gelöst | Xenoblade-Spieltitel, `netzteil`-Kontext, Quoka-Parsing-Root-Cause | +8, 1358/1358 | — |
| 17 | `found.json`-Vollanalyse (extern) | 36 Fehltreffer über `konsolen_bundles`/`retro_konsolen`/`gpu` behoben | +9, **1372/1372** | — |
| 18 | Nutzer-Fehltreffer-Analyse (Fix A–E) | 25/34 bestätigte FP behoben, 1€-Preisanomalie bewusst nicht gefixt | +13, 218 (targeted) | — |
| 19a | Category-False-Positive-Forensics-Tool | Read-only, priorisierte Fix-Queue, keine YAML-Änderung | +24, 63 (targeted) | PR #45, `8008414` |
| 19b | Korrektur: `konsolen_bundles.yaml` versehentlich gelöscht | Wiederhergestellt via `git checkout`, reine Restauration | 373 (targeted) | — |
| 20a | `iphone`-Mainboard-Fehltreffer behoben | 15/19 historische FP gelöst, 4 bewusst offen (Analyse) | 373+ (targeted) | PR #47, `869562b` |
| 20b | PS4/PS5-HDMI-Reparatur-Fehltreffer behoben, Switch/Xbox als Ground-Truth-Artefakt | 16/19 gelöst, Switch/Xbox-FP-Label als fehlerhaft erkannt (keine YAML-Änderung dafür) | — | PR #48, `8f855e9` |
| 20c | Ground Truth / Routing Assessment sauber getrennt | Neues Modul, `queue_category` statt Label-Vermischung | +44 | PR #49, `7159b6c` |
| 20d | Fix-Queue strikt aus `assessment.status` abgeleitet | Bug behoben (`CATEGORY_CHANGED` fälschlich zu `ACTIVE_ROUTING_FP`), Konsistenz-Check ergänzt | +19 | PR #50, `8988854` |
| 20e | 35 UNCLEAR-Fälle forensisch klassifiziert | 11 vermutlich TP / 23 vermutlich FP / 1 Manual-Review, **noch nicht in YAML umgesetzt** | — | PR #51, `33b6091` |
| 21 | Root-Cause-Clustering der 23 `LIKELY_FALSE_POSITIVE` + gezielter Fix | 7 Cluster; 20/23 bereits gelöst, 2/23 neu gefixt (`konsolen_bundles`: „Split Pad Pro"/„Joy-Con Set"), 1/23 bewusst offen (Manual-Review) | +8, 1478/1478 | PR #52, `2a3d514` |
| 22 | Resale-/Profit-Audit (real) + 3 Profit-verzerrende Matching-Fehler behoben | `konsolen_bundles`/„pro Stück", `vintage_elektronik`/„Hefte", `monitor_curved`/„Teildefekt" (lokal); 1 bewusst akzeptierter Ground-Truth-Konflikt | +8, 1486/1486 | PR #53, `2ce1e04` |
| 23 | Notebook-Recall-Optimierung (99-TP-Audit-Folgeschritt) | 21/43 bestätigte Gaps geschlossen — ThinkPad-Preisgrenze, Wortgrenzen-/Modellcode-Lücken, GTX-1650-Regel, 3 neue Marken; mehrere Fälle bewusst dokumentiert zurückgestellt | +23, **1509/1509** | PR #54, `9fc967c`/`8507c44` |
| 24 | `matcher.py` → `app/matcher/`-Package modularisiert | Reine Strukturänderung, Signatur unverändert, kein Aufrufer musste angepasst werden | 301/301 (targeted) | direkt auf `main`, `8016eea` |
| 25 | Notebook-Recall-Fortsetzung: L480/L590, IdeaPad Gaming 3, Latitude-Modellcodes | 3 weitere additive Recall-Gap-Fixes in `notebook_resell.yaml`, alte `matcher.py` final entfernt | 40 (targeted), 68 (kategoriebezogen) | PR #55, `471795a` |
| 26 | Category Recall Maximal Absichern — OVP-Kontext-Guard-Fix + vollständiges Recall-Gate | 2 UNCLEAR-Fälle recovered, alle 69 unmatched TP klassifiziert, `CATEGORY_RECALL_MAXIMALLY_SECURED` | 84 (kategoriebezogen) | PR #56, `62fd678` |

**Nach Batch 26 (verifiziert):** 360 Regeln, 19 Kategorien, 0 Findings, Ruleset-Signatur
`09d66cde97932a9f`. TP 2252/2183 matched, FP 19/3, UNCLEAR 35/13. Zielgerichtete Tests grün
(84 kategoriebezogen); volle Suite zuletzt vollständig verifiziert in Batch 23 (1509/1509),
seither nicht erneut ohne explizite Freigabe ausgeführt. **Category Recall Gate:
`CATEGORY_RECALL_MAXIMALLY_SECURED`** — siehe Abschnitt 1a.

## 4. Datenqualität — offene Punkte

| # | Thema | Status | Batch |
|---|---|---|---|
| 1 | Coverage-/FP-Rate 251-Listing-Stichprobe | 217 TP/21 FP/13 UNCLEAR, Precision 91,2% (nur 30 unabhängig einzeln geprüft) | 3–4 |
| 2 | 19 Regeln ohne Produktivdaten | offen — weiter beobachten | — |
| 3 | Orphan-Datenpunkte `spielzeug_bundles` | ✅ erledigt (5 migriert, 655 gelöscht, 3 erhalten) | 6 |
| 4 | `RX 7600 XT`/`RX 7600`-Überlappung | ✅ erledigt (min_vram_gb-Bug, 5 Modelle) | 10 |
| 5 | `controller`-`ladekabel`-Exclude | ✅ erledigt (Lade-Stationen, nicht Kabel-Mechanismus) | 9 |
| 6 | Resale-Confidence (HIGH/MEDIUM/LOW) | offen — mögliche nächste Qualitätsstufe | — |
| 7 | Automatische Data-Quality-Warnungen | offen — weiterentwickeln | — |
| 8 | „Spieltitel ohne Plattform-Bindestrich" (`konsolen_bundles`/`retro_konsolen`) | offen, bestätigt in beiden Kategorien | 3 |
| 9 | 9 zurückgestellte FP-Muster (27 Titel) | offen — vollständige Liste: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md` | — |
| 10 | Restliche unauditierte Nischen-Feinheiten | offen — nur bei neuem Datenpunkt erneut aufgreifen | — |
| 11 | Umlaut-Fingerprint-Bug | Code-Fix umgesetzt, **nicht rückwirkend** (dauerhafte Einschränkung) | 5 |
| 12 | Ground-Truth-Label-Abdeckung | ✅ 251-Listing-Worksheet vollständig gelabelt | 1 |
| 13 | „Switch Pro Controller"-Regel: nur 2 statt 3 Preisstufen | offen — bewusst nicht erweitert (keine Datenbasis) | — |
| 14 | Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation | ✅ erledigt (4 gezielte Exclude-Fixes) | 8 |
| 15 | `M.2`-Punktuation in `normalize_title()` | beobachtet, 1 Fall, nicht verallgemeinert, keine Aktion | — |
| 16 | 3 in Batch 14 zurückgestellte Punkte | ✅ alle erledigt (additiv lösbar, kein Redesign nötig) | 15–16 |
| 17 | Quoka-Preis-Parsing-Defekt | ✅ an der Wurzel gelöst (Leerzeichen-Tausendertrennzeichen) | 16 |
| 18 | `found.json`-Vollanalyse | ✅ 36 Fehltreffer über 3 Kategorien erledigt | 17 |
| 19 | Nutzer-Fehltreffer-Analyse | ✅ 25/34 erledigt, Fix E bewusst nicht (kein isolierter Root Cause) | 18 |
| 20 | Category-FP-Forensics-Tool | ✅ Fix-Queue vollständig abgearbeitet — 16/19 historische FP gelöst, 3 bewusst offen (2 Ground-Truth-Konflikt, 1 Manual-Review), 0 `ACTIVE_ROUTING_FP` | 19a, 20a–d |
| 21 | 35 historisch UNCLEAR-Fälle (`konsolen_bundles`/`retro_konsolen`) | forensisch klassifiziert (11 vermutlich TP, 23 vermutlich FP, 1 Manual-Review) | 20e |
| 22 | Fix-Queue für die 23 `LIKELY_FALSE_POSITIVE`-Kandidaten aus Batch 20e | ✅ root-cause-geclustert (7 Cluster) + 22/23 gelöst (20 bereits vorher, 2 neu: „Split Pad Pro"/„Joy-Con Set"), 1/23 bewusst offen (RDR2/PS4-Steelbook-Bundle, „bundle" = Trigger- und Verstärkungssignal für 3 echte Treffer, Manual-Review) | 21 |
| 23 | 3 live bestätigte Profit-verzerrende Matching-Fehler (Resale-/Profit-Audit) | ✅ 3 unabhängige Root Causes gezielt gefixt (`konsolen_bundles`/„pro Stück", `vintage_elektronik`/„Hefte", `monitor_curved`/„Teildefekt"), 1 bewusst akzeptierter Ground-Truth-Konflikt | 22 |
| 24 | Notebook-Recall-Gap (99-TRUE_POSITIVE-Recall-Forensics-Audit) | 21/43 bestätigte Gaps geschlossen, mehrere Fälle dokumentiert zurückgestellt (s. Abschnitt 5 P0) | 23 |
| 25 | Notebook-Recall-Fortsetzung: 3 weitere Gaps geschlossen | ✅ L480/L590 (Marken-Gate), IdeaPad Gaming 3 (Gerätewort-Gate), Dell Latitude 5500/5501/7400 (Modellcode-Liste) — je per Vollkorpus-Diff + Adversarial-Test abgesichert, 0 Regressionen | 25 |
| 26 | Category Recall Maximal Absichern (vollständiges Gate) | ✅ Alle 69 unmatched TRUE_POSITIVE + 24 unmatched UNCLEAR einzeln klassifiziert; 1 echter Recall-Gap gefunden+gefixt (konsolen_bundles OVP-Kontext-Guard), 9 Cluster als GT-Konflikt/Datenbasis-Problem/GT-Kategorie-Fehlzuordnung bestätigt; `CATEGORY_RECALL_MAXIMALLY_SECURED` | 26 |

## 5. Nächste Prioritäten

### P0 — offen

- **✅ Category Recall Gate: `CATEGORY_RECALL_MAXIMALLY_SECURED` (Batch 26, PR #56).** Alle 69
  unmatched TRUE_POSITIVE-Fälle und alle 24 unmatched UNCLEAR-Fälle einzeln geprüft und klassifiziert
  (Details: Abschnitt 1a). Der einzige gefundene echte Recall-Gap (konsolen_bundles OVP-Kontext-
  Guard) ist gefixt. **Nächster Haupt-Workstream: Price Validation / Profit Validation.**
- **HP-Design-Entscheidungen bleiben separat offen und blockieren das Recall-Gate NICHT:**
  - **HP generic** (2 TP, 100€/270€): `NEEDS_DESIGN_DECISION` — ein Fixkandidat (regel-eigene
    Zubehör-Excludes) löst den 270€-Fall ohne reale Korpus-Kollateralschäden (100€-Fall bleibt an
    einem separaten Format-Problem „8 GB" mit Leerzeichen blockiert), trägt aber einen
    architektonisch nachgewiesenen, nicht auflösbaren Trade-off: rule-level `exclude:` kann
    „Akku 85%" (Zustandsangabe) nicht von „Akku" (Zubehörprodukt) unterscheiden (siehe
    TECHNISCHER_PROJEKTSTATUS.md Abschnitt 6). Eine vollständige technische Lösung (Regex-Kontext-
    Primitiv) wäre möglich, erfordert aber eine Erweiterung von `matcher/core.py` (geschütztes
    Kernsystem) — eigene Freigabe nötig.
  - **HP ZBook/Workstation** (1 Fall, TRUE_POSITIVE im GT-JSON): `NEEDS_DEFINITION` —
    Definitionsfrage, ob eine Workstation-Sublinie unter `notebook_resell` fallen soll.
  - Alle Analysen rein im Chat-Verlauf dokumentiert (keine Datei im Repo), Ergebnisse hier
    zusammengefasst. Braucht eigene Freigabe für einen etwaigen nächsten Schritt.
- **BLOCKED / fehlende Datenbasis, als Teil des Category-Recall-Gate klassifiziert, technisch
  nicht gelöst:** Fujitsu Lifebook (`BLOCKED`, Adversarial-Kollision), Alienware (`BLOCKED`,
  Größen-Gruppe strukturell unlösbar), GTX 1650 Ti/RTX 2060/RTX 4070 (je 1 GT-Datenpunkt, keine
  Preisbasis), IdeaPad 5 (2, keine Datenbasis), VOYEE-Controller (1, keine Datenbasis), RDR2/PS4-
  Steelbook-Bundle (Cluster C6, „bundle" gleichzeitig Trigger- und Verstärkungssignal, kein
  sicherer Keyword-Fix), 7 Notebook-Fälle ganz ohne „laptop"/„notebook"-Wort im Titel.
- ~~Fix-Queue für die 23 `LIKELY_FALSE_POSITIVE`-Fälle aus Batch 20e~~ — **erledigt in Batch 21**:
  root-cause-geclustert, 22/23 gelöst (20 bereits vorher, 2 neu gefixt), 1/23 s.o. offen.
- ~~Volle Testsuite stand seit Batch 18 aus~~ — **erledigt** (Batch 20): 1470/1470 grün, seither
  erneut verifiziert in Batch 21 (1478/1478) und Batch 23: **1509/1509**.
- ~~Fix-Queue-P0-Eintrag Batch 19a (`iphone`)~~ — **erledigt** (Batch 20a).
- 9 bewusst offene Restlücken aus Batch 18 (Teil 2, „zweifelhafte Treffer") — nur bei neuem,
  eindeutigerem Datenpunkt erneut aufgreifen.
- 3 dokumentierte Nicht-Fixes aus Batch 20a–d bleiben bewusst offen: `retro_konsolen`/DS-Lite
  (Manual-Review, Fix würde 3 echte Handheld-Titel mitblockieren),
  `konsolen_bundles`/Switch+Xbox (Ground-Truth-Konflikt, Label vermutlich selbst fehlerhaft,
  keine YAML-Änderung vorgesehen).
- Mögliche Folgeaufgabe (noch nicht freigegeben): Tausch-/Barter-Anzeigen-Erkennung
  (Titel-Muster „tausche"/„gegen") aus Notification/Preisstatistik ausschließen — betrifft
  geschützte Kernsysteme (Notification-Gate, Price-History-Persistenz).
- **Rebuild ausstehend:** Batch 14 (`app.py`-Preisguard) UND Batch 16 (`scrapers/quoka.py`-Fix)
  enthalten Python-Änderungen — `docker compose up --build -d` nötig, bevor beide produktiv
  wirken. Alle YAML-Fixes aus Batch 14–16 wirken bereits ohne Rebuild.
- Beobachtung aus Batch 13 (kein Blocker): einen der nächsten 1–2 Scans gegenchecken, sobald
  `dedupliziert` wieder im Normalbereich (<650) liegt.
- Ungeprüfter Verdacht: derselbe `min_vram_gb`-Musterbug (Batch 10) könnte theoretisch auch
  außerhalb von `gpu` relevant sein — bisher nicht geprüft, kein aktiver Punkt.
- Ansonsten keine offenen P0-Punkte. Nächster Schritt nach freiem Ermessen: #6
  (Resale-Confidence) oder neue Nutzeranfrage.

### P1 — Datenqualität

- Resale-Confidence ausbauen.
- Datenqualitätsdiagnosen automatisieren.

### P2 — Wartbarkeit

- `app.py` nur schrittweise weiter modularisieren, wenn konkreter Änderungsdruck besteht.
- Keine Komplett-Refaktorierung.

### P3 — Features

Neue Kategorien oder weitere Deal-Intelligence erst nach den Stabilitäts-/Qualitätsschritten
priorisieren.

## 6. Abgeschlossen (übergeordnet)

- Ursprüngliche Phasen 0–10
- YAML-Regelwerk und dynamische Kategorie-Discovery
- Scraper- und Detector-Registry
- Deal Score und Notification-Gating
- Price History / Marktpreisstatistik, separates Resale-Price-Grouping
- Profit-/Flip-Kandidaten mit Margin-Feldern
- Top-Deal-Logik und Dashboard-KPIs
- Duplicate Detection und Presence Tracking
- Kategorie-Revalidierung und Data-Quality-Bausteine
- Rule Analyzer und Rule Coverage, Rules-/Entry-/Regex-Caching
- Condition-/Lieferumfang-Detektoren
- Mehrere neue Kategorien ohne Python-Code
- Phase-15-Performance-Optimierungen
- Systematischer Active-False-Positive-Audit über alle 19 Kategorien (PR #11–25)
- Cross-Category-Routing-Audit mit 2 realen Fixes (PR #26–28)
- Ruleset-Qualitätssystem: Baseline-Freeze, Regression-Benchmark, Kategoriequalitäts-Report,
  Preishistorie-Simulation, Cross-Category-Analyse (`tools/ruleset_quality/`, PR #29)
- 251-Listing-Worksheet vollständig gelabelt + 3 Exclude-Fixes (PR #31, Batches 3–4)
- Umlaut-Fingerprint-Fix, `lego_bundle`-Migration, Preishistorie-Revalidierung v3 (Batches 5–7)
- Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation über 4 Kategorien gelöst (Batch 8)
- `controller`/`ladekabel`-Restlücke gelöst (Batch 9)
- `RX 7600 XT`/`RX 7600`-Überlappung + `min_vram_gb`-Bug bei 4 weiteren GPU-Modellen (Batch 10)
- Echte End-to-End-Scan-Performance-Messung + Scraping parallelisiert (Batch 11)
- Persistence-Batching für `seen.json`/`found.json` (Batch 12), reale Wirkung verifiziert (Batch 13)
- Vollständiger read-only Kategorie-Audit + 5 Live-Fehltreffer + Preis-Mindestbetrag-Guard (Batch 14)
- „pro"-Kollision `konsolen_bundles.yaml` + 3 weitere Live-Fehltreffer gelöst (Batch 15)
- Xenoblade-Spieltitel-, `netzteil`-Positivsignal- und Quoka-Preis-Parsing-Fix (Batch 16)
- Vollanalyse extern bereitgestellter `found.json`: 36 Fehltreffer über 3 Kategorien (Batch 17)
- Nutzer-Fehltreffer-Analyse: 25/34 bestätigte Fehltreffer behoben (Batch 18)
- Category-False-Positive-Forensics-Tool + Fix-Queue, PR #45 (Batch 19a)
- Wiederherstellung versehentlich gelöschter `konsolen_bundles.yaml` (Batch 19b)
- Fix-Queue aus Batch 19a vollständig abgearbeitet: `iphone`-Mainboard- und
  PS4/PS5-HDMI-Reparatur-Fehltreffer per YAML gefixt, 16/19 historische FP gelöst,
  Switch/Xbox-Fehllabel als Ground-Truth-Artefakt erkannt (PR #47–48, Batch 20a–b)
- Historical Ground Truth / Current Routing Assessment sauber getrennt, Fix-Queue-Kopplungsbug
  behoben, Konsistenz-Check ergänzt (PR #49–50, Batch 20c–d)
- 35 historisch UNCLEAR-Fälle forensisch klassifiziert (11 TP/23 FP/1 Manual-Review) (PR #51,
  Batch 20e)
- Root-Cause-Clustering der 23 `LIKELY_FALSE_POSITIVE`-Kandidaten (7 Cluster) + gezielter Fix:
  „Split Pad Pro"- und „Joy-Con Set"-Fehltreffer in `konsolen_bundles.yaml` behoben (0
  Regressionen bei 2252 TRUE_POSITIVE- und 19 FALSE_POSITIVE-Fällen, Vollkorpus verifiziert);
  RDR2/PS4-Steelbook-Bundle-Fall bewusst nicht angefasst (PR #52, Batch 21)
- Resale-/Profit-Audit auf echten Produktivdaten + 3 live bestätigte Profit-verzerrende
  Matching-Fehler root-cause-analysiert und gefixt: `konsolen_bundles`/„pro Stück",
  `vintage_elektronik`/„Hefte", `monitor_curved`/„Teildefekt" (lokal, nicht global — Kollision
  mit TRUE_POSITIVE-Verwendung in `iphone`/`retro_konsolen`); 0 Regressionen, 1 bewusst
  akzeptierter Ground-Truth-Konflikt (PR #53, Batch 22)
- 99-TRUE_POSITIVE-Recall-Forensics-Audit (Analyse, keine Codeänderung): 43 bestätigte
  Recall-Gaps identifiziert und root-cause-geclustert, davon 21 in der Notebook-Recall-
  Optimierung gezielt geschlossen — ThinkPad-Preisgrenze datenbasiert kalibriert,
  Wortgrenzen-/Modellcode-Lücken ergänzt, neue GTX-1650-Regel, 3 neue Marken-Regeln (Dell
  Latitude, ACEMAGIC, Lenovo V330); mehrere Fälle bewusst dokumentiert zurückgestellt
  (fehlende Preisbasis, Architekturfrage, unkontrollierbares Cross-Category-Risiko) (PR #54,
  Batch 23)
- `matcher.py` (1317 Zeilen) zu `app/matcher/`-Package modularisiert — reine Strukturänderung,
  Ruleset-Signatur unverändert, kein Aufrufer musste angepasst werden (`8016eea`, Batch 24)
- Notebook-Recall-Fortsetzung: 3 weitere additive Gap-Fixes in `notebook_resell.yaml` — ThinkPad
  L480/L590 (Marken-Gate-Erweiterung), IdeaPad Gaming 3 (Gerätewort-Gate-Erweiterung), Dell
  Latitude 5500/5501/7400 (Modellcode-Liste als Gerätewort-Alternative); alte `app/matcher.py`
  final entfernt; je Fix per Vollkorpus-Diff + Adversarial-Test abgesichert, 0 Regressionen
  (PR #55, Batch 25)
- Vier isolierte Recall-Cluster tiefenanalysiert (Fujitsu Lifebook, HP generic, HP ZBook,
  Alienware) — Fujitsu und Alienware `BLOCKED` (technisch unlösbar mit bestehenden Primitiven),
  HP generic `NEEDS_DESIGN_DECISION` (löst 1 von 2 Zielfällen, offener Trade-off zwischen
  Zubehör-Precision und Akku-Zustands-Recall), HP ZBook `NEEDS_DEFINITION`; keine Codeänderung,
  siehe Abschnitt 5 P0 für Details
- „Category Recall Maximal Absichern"-Workflow vollständig durchlaufen (Batch 26, PR #56): alle
  69 unmatched TRUE_POSITIVE- und 24 unmatched UNCLEAR-Fälle einzeln geprüft und klassifiziert.
  1 echter Recall-Gap gefunden und gefixt (`konsolen_bundles.yaml` OVP-Kontext-Guard-Lücke, 2
  UNCLEAR-Fälle recovered, 0 Kollateralschäden). 9 weitere Cluster (Aufrüstkit, konsolen_bundles
  Zubehör, controller Zubehör, handhelds, retro_konsolen, lego_minifiguren, autoradio_opel_corsa,
  iPhone, RAM) als bereits bewusste, dokumentierte Ground-Truth-Konflikte bestätigt — die
  jeweiligen Excludes funktionieren korrekt, keine YAML-Änderung vorgesehen. 4 Einzelfälle
  (netzteil, sata_ssd, vintage_elektronik, monitor_curved) als reine GT-Kategorie-Fehlzuordnungen
  identifiziert. Ergebnis: **`CATEGORY_RECALL_MAXIMALLY_SECURED`** — nächster Haupt-Workstream
  Price Validation / Profit Validation (PR #56, Batch 26)

*Vollständige Details, Root-Cause-Analysen und Blast-Radius-Nachweise: `docs/STATUS_HISTORY.md`.*

## 7. Aktuelle Systemkette

```text
Scraper
  → Dedup / Presence
  → YAML Rules
  → Matcher + Detectoren
  → Deal Score
  → Marktpreis / Resale
  → Profit / Flip
  → Top-Deal / KPIs
  → Notifications
  → Dashboard / API / Statistics
```

Zusätzlich (read-only, außerhalb der Produktionskette): `tools/ruleset_quality/` —
Regression-Benchmark/Qualitätssystem, siehe `docs/STATUS_HISTORY.md` und
`tools/ruleset_quality/README.md`.

### Architekturregeln

- `market_price` und `estimated_resale_price` bleiben getrennt.
- Dünne Resale-Daten dürfen keinen künstlich optimistischen Flip-Kandidaten erzeugen.
- YAML bleibt die primäre Erweiterungsebene für Kategorien.
- Neue Detector-Typen benötigen weiterhin Python-Code.
- Fixes verwenden bestehende YAML-/Matcher-Primitive statt eines neuen generischen Matcher-Systems.
- `tools/ruleset_quality/` ist kein Bestandteil der Produktionskette und wird von `app.py`/
  `matcher/` nicht importiert.
- `matcher.py` ist seit `8016eea` (Batch 24, direkt auf `main`) ein Package (`app/matcher/`):
  `core.py` (`MatchResult`, `evaluate()`), `text_matching.py`, `vram.py`,
  `hardware_requirements.py`, `score_bridge.py`, `rules_io.py`. `__init__.py` re-exportiert die
  komplette bisherige Oberfläche — alle Importpfade (auch privater Funktionen) bleiben
  unverändert, keine Logikänderung. Die alte `app/matcher.py`-Datei blieb zunächst als Altlast
  liegen und wurde erst in Batch 25 (PR #55) final entfernt.

## 8. Arbeitsregeln

- Kein Big-Bang-Rewrite.
- Keine Threshold-Änderungen ohne Datenbasis.
- Keine Tests löschen oder abschwächen.
- Keine Performance-Optimierung ohne Messung.
- Keine bestehende Business-Logik duplizieren.
- Nach technischen Änderungen vollständige Testsuite ausführen.
- `TECHNISCHER_PROJEKTSTATUS.md` und `STATUS.md` nach abgeschlossenen Änderungen synchron halten.

## 9. Dokumentationsregel

`TECHNISCHER_PROJEKTSTATUS.md` ist die aktuelle technische Referenz. `docs/STATUS_HISTORY.md`
enthält die vollständige, wortgetreue Batch-Historie (1–19) und wird bei jedem neuen
abgeschlossenen Batch um einen Eintrag ergänzt; `STATUS.md` erhält dazu nur die kompakte
Tabellenzeile in Abschnitt 3. Historische Phase-/Completion-Reports bleiben als Entscheidungs-
und Messnachweise erhalten, gelten aber nicht als aktueller HEAD- oder Teststand.
