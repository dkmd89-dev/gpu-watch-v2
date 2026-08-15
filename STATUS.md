# STATUS — Aktueller technischer Projektstatus

> **Stand:** 2026-08-15  
> **Repository:** `dkmd89-dev/gpu-watch-v2`  
> **Branch:** `main`  
> **Letzter Code-Commit auf `main` (vor dieser Doku-Aktualisierung):** `a3e5060` (Merge PR #38)  
> **Technische Referenz:** `TECHNISCHER_PROJEKTSTATUS.md`

## Gesamtstatus

**Stabil / aktiv weiterentwickelbar.** Seit dem letzten dokumentierten Stand (`a3e5060`, PR #38)
wurde ein vollständiger, read-only Kategorie-Audit durchgeführt (YAML ↔ Dashboard ↔ found.json ↔
category_validation.py — keine Abweichungen gefunden), gefolgt von einer Nutzer-gemeldeten
Live-Fehltreffer-Analyse gegen `tools/ruleset_quality/`-Regression-Benchmarks. **5 real bestätigte
Fehltreffer über 3 Kategorien behoben** (`vintage_elektronik`/„fernbedienung" kontextbewusst statt
bare, `handhelds`/„module"-Plural, `konsolen_bundles`/„zubehör set"-Leerzeichen-Variante +
„mainboard"/„motherboard") sowie ein **Preis-Mindestbetrag-Guard** gegen einen Quoka-seitigen
Preis-Parsing-Defekt (0€-Treffer verzerrten `price_history.jsonl`) — siehe Batch 14 unten. Drei
weitere real gefundene, aber strukturell risikoreichere Fehltreffer-Muster bewusst
**zurückgestellt** (siehe Batch 14, „Bewusst nicht gefixt").

## Verifizierter Stand

```text
main (vor dieser Doku-Aktualisierung): a3e5060 (Merge PR #38)

Vollständiger Testlauf (vom Nutzer lokal ausgeführt und verifiziert):
pytest app/tests/ -> 1337 passed, 0 failed (80,33s)

Rule Analyzer:
355 Regeln
19 Kategorien
0 Findings
Ruleset-Signatur: b863e724db9b393c (geändert gegenüber 133dcd1a9f614e7e -- YAML-Änderungen
  in vintage_elektronik.yaml/handhelds.yaml/konsolen_bundles.yaml, siehe Batch 14)

data/found.json: 2500 Einträge
data/price_history.jsonl: 15.199 Datenpunkte (laufender Produktivbetrieb, nicht Teil dieses Batches)
```

Vorheriger dokumentierter Teststand (PR #38): 1334/1334. 15 neue Tests in diesem Batch (siehe
Batch 14 unten) — die Differenz zum tatsächlich verifizierten Vorher-Stand (1337−15 = 1322) legt
nahe, dass die zuvor dokumentierte „1334" bereits vor diesem Batch nicht mehr exakt mit einem real
verifizierten lokalen Lauf übereinstimmte (bekannte Einschränkung, siehe CLAUDE.md Abschnitt 7 —
STATUS.md wird nicht in jeder Session live gegengeprüft). Keine Aktion nötig, der jetzt
dokumentierte Stand (1337) ist frisch verifiziert.

## Zuletzt abgeschlossene Batches

### 1. Cross-Category-Routing-Audit (PR #26–#28) — unverändert, siehe vorheriger Stand

### 2. Ruleset-Qualitätssystem Aufbau + 3 offene Entscheidungen geklärt (PR #29 + Folge-Sessions) — unverändert, siehe vorheriger Stand

### 3. 251-Listing-Worksheet gelabelt + 3 Exclude-Fixes (PR #31, `c577207`)

**KI-gestütztes Labeling** aller 251 Listings (Titel/Preis/Regel-Diagnose-basiert, explizit
**keine** unabhängige menschliche Verifikation): 217 TRUE_POSITIVE / 21 FALSE_POSITIVE / 13
UNCLEAR. Vier strukturelle Muster identifiziert, jeweils mehrfach unabhängig bestätigt:

1. **Flektierte Exclude-Begriffe entgehen dem Whole-Word-Match** (4 Fälle) — "Defekte"/"defekten"
   statt "defekt", "Tausche" statt "tausch". **Gefixt:** `exclude_global` um `defekte`/`defekter`/
   `defektes`/`defekten` erweitert (Blast Radius gemessen: 23 Punkte im Gesamtkorpus, 0
   Negationsfälle). "tausch" bewusst **nicht** erweitert (Risiko: "Akku tauschen" u.ä. harmlose
   Wartungsformulierungen).
2. **Zubehör/Ersatzteil als Hauptgerät gematcht** (6 Fälle) — Lötwerkzeug, interne SSDs "für
   Steam Deck", Kopfhörer, Kabelset, Joy-Con-Set. **Nicht gefixt** — strukturelles Muster ohne
   einfache Exclude-Lösung.
3. **Spieltitel ohne Konsole** (5 Fälle) — bestätigt die bereits dokumentierte Restlücke, jetzt
   auch in `retro_konsolen` nachgewiesen (nicht nur `konsolen_bundles`). **Nicht gefixt.**
4. **Notebook-Marken, die die office_pc-Notebook-Exclude nicht erfasst** (2 Fälle) — "Dynabook
   Satellite Pro", "Dell Latitude". **Gefixt:** `office_pc.yaml` um `dynabook`/`satellite pro`/
   `latitude` erweitert (Blast Radius: 13 Punkte, 0 Kollisionen).
   Zusätzlich `handhelds.yaml`: `sd karten` (Plural) ergänzt (Muster 1, analog).

9 neue Regressionstests, volle Suite 1305/1305 grün nach diesem Batch. Details:
`tools/ruleset_quality/generated/reports/WORKSHEET_LABELING_BERICHT_2026-08-14.md`.

### 4. Menschlich verifiziertes Labeling (Listings 1–30 einzeln, 31–251 pauschal auf Nutzerwunsch)

Dialogbasiertes Labeling in Batches à 10: Listings 1–30 wurden einzeln gezeigt und explizit
bestätigt (0 Abweichungen vom KI-Vorschlag), Listings 31–251 auf ausdrücklichen Nutzerwunsch
("bestätigt alle batches") pauschal übernommen — im Label-Store (`review_modus`-Feld:
`einzeln_bestaetigt`/`pauschal_bestaetigt`) transparent unterschieden. Als eigene Quelle
`human_verified_labels_2026-08-14.json` abgelegt, weder die KI-Quelle noch die Forensik-Quelle
überschrieben. Details:
`tools/ruleset_quality/generated/reports/HUMAN_VERIFIED_LABELING_ABSCHLUSSBERICHT_2026-08-14.md`.

### 5. Umlaut-Fingerprint-Fix (STATUS.md Nr. 11, `c9967ba`)

`duplicate_detection.normalize_title()` erhält jetzt deutsche Umlaute (ä/ö/ü/ß) statt sie durch
ein Leerzeichen zu ersetzen. **Wichtige Einschränkung:** wirkt nur auf **künftig neu
geschriebene** `price_history.jsonl`-Zeilen — bereits gespeicherte Zeilen bleiben unverändert im
alten Format, weil der Rohtitel dort nie persistiert wurde (keine rückwirkende Reparatur
möglich). Rückwärtskompatibel für die produktive Duplicate-Erkennung (vergleicht nur innerhalb
desselben Scan-Laufs, nie gegen Historie). 4 neue Tests.

### 6. `lego_bundle`-Migration/-Bereinigung ausgeführt (freigegeben, price_history.jsonl)

Nach exaktem Dry-Run und expliziter Freigabe der 5 Ziel-Titel/-Preise: **5 Punkte migriert** (2×
`lego_bundle` → `lego_ninjago_bundle`, 3× → `lego_minifig_bundle`, nur `model`-Feld geändert),
**655 Punkte gelöscht** (396× nicht rekonstruierbare `lego_bundle`, 210× `playmobil_bundle`, 49×
`spielzeug_bundle_sonstige` — beide strukturell ohne Nachfolgeregel). 3 rekonstruierbare, aber
nicht eindeutig migrierbare `lego_bundle`-Punkte bewusst unverändert erhalten.
`price_history.jsonl`: 15.554 → 14.899 Zeilen. Nachher-Validierung: valides JSONL, exakte
Zählungen bestätigt.

### 7. Kontrollierte Preishistorie-Revalidierung v3 (read-only)

Vollkorpus-Revalidierung (14.899 Punkte) unter Nutzung des Umlaut-Fixes:

- **15 nicht vom Umlaut-Bug betroffene Kategorien** (10.337 Punkte): verlässlich, 91,1%
  unverändert — Bewegungen größtenteils durch bereits bekannte Ursachen erklärbar (z.B.
  `lego_ninjago_bundle` 60% Modellwechsel durch später hinzugekommene granularere Lego-Sub-Modelle;
  `office_pc`/`thinkpad_modern`-Drift durch bereits gebilligte Notebook-Fixes).
- **4 zuvor betroffene Kategorien** (3.389 Punkte, `handhelds`/`konsolen_bundles`/
  `retro_konsolen`/`vintage_elektronik`): "kein Treffer"-Rate (35,9%) **nicht verlässlich
  interpretierbar** — für `retro_konsolen`/`vintage_elektronik` praktisch 0% der betroffenen
  Punkte beurteilbar (Titel nicht rekonstruierbar), da der Fix nicht rückwirkend wirkt.
- **Cross-Validierung gegen die menschlichen Labels bestätigt den PR-#31-Fix direkt** auf den
  echten Daten: exakt die 4 gefixten Titel wechseln von FALSE_POSITIVE-Match zu kein Treffer, die
  übrigen 10 von 14 auffindbaren FP-Fälle matchen unverändert (bestätigt: reale, weiterhin offene
  strukturelle Muster).

Keine Korrektur-Aktion an `price_history.jsonl` vorgeschlagen oder ausgeführt — Datenlage trägt
für die 4 betroffenen Kategorien keine verlässliche Einzelfallentscheidung. Details:
`tools/ruleset_quality/generated/reports/PREISHISTORIE_REVALIDIERUNG_V3_BERICHT_2026-08-14.md`.

### 8. Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation gelöst (Datenqualität Punkt 14)

Vier unabhängige Root Causes für die 6 in der Stichprobe gefundenen Fälle, je gezielt gefixt
(Blast Radius je gemessen, 0 Kollisionen):

- **`controller`**: `lötaufsatz`/`lötspitze` ergänzt — Kompositum-Lücke (bestehendes bare
  `"aufsatz"` greift nur als eigenes Wort, nicht in "Löt**aufsatz**").
- **`handhelds`**: `ssd`/`festplatte`/`headset`/`kopfhörer`/`in-ear` ergänzt — bisher fehlende
  bare Excludes (kein Handheld-Gerät wird selbst so beworben).
- **`netzteil`**: `kabelset` ergänzt — Regel matcht rein über den Watt-Detector, exclude_category
  deckte bisher nur komplette Systeme ab, kein PSU-Zubehör.
- **`konsolen_bundles`**: neuer kontextbewusster Exclude `joy-con`/`joycon`/`joy con`
  (`exclude_category_unless_also_contains`, blockiert nur ohne Geräte-Marker) — ein bare Exclude
  wurde in einer früheren Session wegen 9 verifizierten Kollisionen mit echten
  Konsole+Joy-Con-Bundles bewusst verworfen; neue Marker-Liste ergänzt `konsole` (fehlte in der
  bestehenden Liste).

6 neue Regressionstests (`test_zubehoer_ersatzteil_vs_geraet_fix.py`), 190 kategorienbezogene
Tests + volle Suite 1315/1315 grün, `rule_analyzer.py` 0 Findings.

### 9. `controller`/`ladekabel`-Restlücke gelöst (Datenqualität Punkt 5)

Analyse ergab: der bestehende `ladekabel`-Mechanismus (`exclude_category_unless_preceded_by`)
funktioniert korrekt — Standalone-Kabel werden blockiert, echte "Controller inkl.
Ladekabel"-Bundles bleiben erhalten. Die tatsächliche Lücke betraf einen **anderen** Zubehör-Typ:
Lade-**Stationen/-Geräte** (Dock-artiges Zubehör statt Kabel), real bestätigt:

- "PS5 Controller USB Dual-Charger Station" (6,99€)
- "PowerA Twin Charging Station für PS5 Controller" (15€)
- "5in1 Switch Aufladegerät für 4 Joycons und 1 Pro Controller" (9€) — Kompositum-Lücke,
  identisches Muster wie "Lötaufsatz": "ladegerät" existierte bereits als Exclude, aber nur als
  eigenes Wort geprüft, "aufladegerät" hat davor keine Wortgrenze.

`exclude_category` um `aufladegerät`/`charging station`/`charger station` ergänzt (unbedingt, wie
bei `ladestation`/`dock` — keine legitime Bundle-Formulierung mit diesen Begriffen im Korpus
gefunden). Blast Radius: 3 Treffer, 0 Kollisionen. 4 neue Regressionstests
(`test_controller_ladezubehoer_fix.py`), 73 `controller`-Tests grün, `rule_analyzer.py` 0
Findings.

### 10. `RX 7600 XT`/`RX 7600`-Überlappung gelöst + 4 weitere GPU-Modelle (Datenqualität Punkt 4)

Die ursprünglich dokumentierte Match-Präzedenz-Überlappung war bereits vor dieser Session
gefixt. Die tatsächliche, bisher unentdeckte Ursache für die weiterhin extrem dünne
`rx_7600`-Datenlage (nur 1 Punkt in `price_history.jsonl`): ohne eigenes `min_vram_gb` fiel die
Regel auf den globalen Default (`_global.yaml`, `min_vram_gb: 12`) zurück — RX 7600 hat aber nur
8GB VRAM. `matcher.py::_vram_gb()` erkennt "8GB" im Titel, nicht "8G" — jedes Angebot mit der
weit häufigeren Schreibweise "8GB" wurde fälschlich verworfen (real verifiziert: identischer
Titel, nur "8G"→"8GB" geändert, Match verschwindet komplett).

**Wichtiger Zusatzfund, direkt mitgefixt:** derselbe strukturelle Bug betraf 4 weitere
GPU-Modelle ohne eigenes `min_vram_gb` und VRAM < 12GB:

| Modell | VRAM | Historische Punkte | Aktuell im Live-Korpus |
|---|---|---|---|
| `rtx_3070` | 8GB | 149 | 16 |
| `rtx_3060_ti` | 8GB | 110 | 12 |
| `rtx_2080_ti` | 11GB | 60 | 3 |
| `rtx_4060` | 8GB | 29 | 4 |

Alle 5 Modelle (10 Regeln) erhalten `min_vram_gb: 0` — match-Begriffe bereits eindeutig
modellspezifisch, bestehende Excludes (z.B. RTX 3070 Ti/RTX 4060 Ti/RTX 2080 Super) bleiben
unverändert wirksam (per Kollisions-Test verifiziert). 10 neue Regressionstests
(`test_gpu_rx7600_vram_fix.py`, `test_gpu_low_vram_models_fix.py`), 54 `gpu`-Tests grün,
`rule_analyzer.py` 0 Findings.

### 11. Scan-Performance gemessen + Scraping parallelisiert

Echte End-to-End-Scan-Messung anhand von 35 Produktiv-Scan-Läufen aus dem Log (`data/
gpu_watch.log`, ~22h Zeitraum) — kein synthetischer Benchmark. Ergebnis:

- Median-Gesamtdauer 28,5 Minuten pro Scan (bei konfiguriertem `SCAN_INTERVAL_MINUTES=10` —
  faktisch ~3× langsamer als beabsichtigt).
- **Scraping: 88,9%** der Gesamtzeit — lief seriell (drei Einzeldauern summierten sich exakt zur
  Gesamtzeit).
- **Persistence: 10,1%** (bis zu 267s) — korreliert nahezu perfekt (r=0,997) mit der Anzahl neuer
  Treffer; Root Cause: atomares Neuschreiben der kompletten `found.json` bei jedem einzelnen
  neuen Treffer (bewusste Crash-Sicherheit, kein Bug). **Nicht verändert** — Tradeoff (Crash-
  Sicherheit vs. Geschwindigkeit) erfordert eine eigene Entscheidung.
- Matching+Scoring/Price-Stats/Notification zusammen < 0,5% — unauffällig.

**Größter Hebel direkt umgesetzt:** die drei Scraper-Quellen (eBay/Kleinanzeigen/Quoka) laufen
jetzt über `concurrent.futures.ThreadPoolExecutor` parallel statt seriell — unabhängige
HTTP-Ziele ohne geteilten Zustand (kein gemeinsames Session-Objekt, kein geteilter
Rate-Limiter), rechnerisches Potenzial ~57% kürzere Gesamtdauer (28,5 → ~12,2 min). Zusätzlich
ein bestehendes Robustheitsproblem behoben: es gab **kein** try/except um `plugin.search()` — ein
Fehler in einer Quelle riss bisher den kompletten Scan ab und verwarf auch die Ergebnisse der
anderen beiden, bereits erfolgreichen Quellen. Jetzt wird jede Quelle einzeln abgefangen.

Fehlenden Quoka-Mock in `test_app_deal_cleanup.py` nachgetragen (bestehende Testlücke, direkt an
diesem Codepfad hängend). 3 neue Tests (`test_app_parallel_scraping.py`, inkl. Timing-Nachweis
echter Parallelität), volle Suite 1332/1332 grün (vom Nutzer lokal verifiziert). Ruleset
unverändert (reine Python-Änderung). Berichte: `docs/SCAN_PERFORMANCE_MESSUNG_2026-08-15.md`.

**Reale Wirkung auf die Produktiv-Scandauer noch nicht verifiziert** — die 57%-Schätzung ist
rechnerisch (aus den 35 historischen Läufen abgeleitet), nicht durch einen tatsächlichen
Nach-Fix-Scan bestätigt (erfordert Deployment: `docker compose up --build -d`).

### 12. Persistence-Batching umgesetzt

Folgeschritt zu Batch 11. **Korrektur der ursprünglichen Analyse:** der dominante Kostentreiber
war nicht nur `found.json` (2,7 MB), sondern vor allem **`seen.json` — 16,7 MB, 47.355
Einträge** —, das bisher bei **jedem einzelnen neu gesehenen Angebot** (nicht nur bei echten
Treffern) komplett neu geschrieben wurde. Das erklärt die ursprünglich gemessene Korrelation
(r=0,997) mit der `dedupliziert`-Zahl (neu gesehene Angebote), nicht mit `new_hits` (echte
Treffer).

**Fix:** neue Konstante `PERSIST_BATCH_INTERVAL_SECONDS` (Default 5s) + ein gemeinsamer
Batching-Helper ersetzen beide bisherigen Sofort-Speicherstellen — schreibt `seen.json` und
`found.json` gemeinsam, höchstens einmal je Intervall statt bei jedem einzelnen Ereignis. Der
finale, unbedingte Save am Scan-Ende bleibt unverändert (Absicherung gegen Datenverlust).

**Tradeoff (bewusst):** vorher 0 Sekunden Risikofenster bei einem Absturz zwischen "als gesehen
markiert" und "persistiert", jetzt bis zu 5 Sekunden — bei einer Matching-Phase von nur ~6-9s
Gesamtdauer ein kleines, begrenztes Fenster.

2 neue Tests (`test_app_persistence_batching.py`), darunter ein Korrektheitsnachweis: mit
künstlich hochgesetztem Intervall (999s) finden **0 Zwischen-Speicherungen** während des Scans
statt (vorher: 1 Save je neuem Angebot), trotzdem sind am Scan-Ende alle Treffer und alle
gesehenen URLs korrekt persistiert — kein Datenverlust. Volle Suite **1334/1334 grün** (vom
Nutzer lokal verifiziert, 76,51s). Ruleset unverändert.

**Reale Wirkung auf die Produktiv-Scandauer: siehe Batch 13 unten — inzwischen verifiziert.**

### 13. Scraping-Parallelisierung + Persistence-Batching: reale Wirkung verifiziert

Erster echter Produktiv-Scan nach Deployment (`docker compose up --build -d`), vom Nutzer aus dem
Log geteilt:

```text
2026-08-14 23:36:59 INFO ✅ Scan komplett: 304 Treffer (von 14206 geprüften Angeboten).
📊 Scan-Metriken: Gesamtdauer=746.44s, Scraping={'ebay': 444.532, 'kleinanzeigen': 535.931,
'quoka': 544.318}, gescrapt=14206, dedupliziert=9135, Matching+Scoring=166.51s,
Price-Stats=0.27s, Persistence=19.10s, Notification=14.22s
```

**Scraping läuft nachweislich parallel:** die drei Einzeldauern summieren sich seriell auf
1524,8s, aber Gesamtdauer minus allem anderen (Matching+PriceStats+Persistence+Notification =
200,1s) ergibt eine tatsächliche Scraping-Wandzeit von nur 546,3s — praktisch identisch mit der
langsamsten Einzelquelle (Quoka, 544,3s, nur ~2s Overhead).

**Gesamtdauer: 746,44s (12,4 min) statt Median 1712s (28,5 min) — 56,4% schneller**, fast exakt
die vorhergesagten ~57%. Bei konfiguriertem 10-Minuten-Intervall ist die reale Kadenz jetzt nur
noch ~1,24× statt ~2,85× langsamer als beabsichtigt.

**Persistence: 19,10s statt Median 173,6s — 89% schneller**, trotz eines für diesen Scan
ungewöhnlich hohen `dedupliziert=9135` (normal: 186–642).

**Eingeordnete Auffälligkeit (kein neues Problem):** `Matching+Scoring=166,51s` liegt deutlich
über dem historischen Median (~5,9s), korreliert aber plausibel mit dem ungewöhnlich hohen
`dedupliziert`-Wert (9135 statt normal <650) — vermutlich ein einmaliger Übergangseffekt: die
mehrfach geänderte Ruleset-Signatur aus den heutigen Fixes lässt `needs_reevaluation()` für sehr
viele bereits bekannte `seen.json`-Einträge auf einmal "True" zurückgeben, zusätzlich zur direkt
vorher geloggten Bereinigung (7128 delistete Alt-Einträge entfernt). Empfehlung: einen der
nächsten 1-2 Scans gegenchecken, sobald sich `dedupliziert` wieder im Normalbereich einpendelt.

### 14. Kategorie-Audit (read-only) + Live-Fehltreffer-Fixes über 3 Kategorien + Preis-Guard

**Teil A — Kategorie-Audit (read-only, keine Änderung).** Vollständiger Abgleich aller 19
Kategorie-YAMLs gegen `category_validation.py`, `api/deals.py`/`api/status.py`,
`templates/index.html` und `found.json`: `all_categories`/`category_labels` werden ausschließlich
dynamisch aus den YAMLs abgeleitet (kein zweiter, hartcodierter Namensraum), `found.json` enthält
exakt die 19 dokumentierten Kategoriewerte, 0 Abweichungen in Schreibweise/Groß-Klein/Singular-
Plural. Einziger Nebenbefund: `price_history.jsonl` enthält weiterhin 8 Orphan-Punkte der
entfernten Kategorie `spielzeug_bundles` (dokumentierter Altbestand, CLAUDE.md nennt „663" —
Zahlendiskrepanz nur beobachtet, nicht geklärt, keine Aktion ohne separaten Auftrag).

**Teil B — Nutzer-gemeldete Live-Fehltreffer.** Ausgehend von 7 vom Nutzer gemeldeten,
aktuell im Dashboard sichtbaren Fehltreffern (davon mehrere mit Deal-Rating „Top-Deal") wurde
gegen den Regression-Benchmark (`tools/ruleset_quality/`) sowie gezielt gegen `found.json`
geprüft, welche echte Bugs sind und welche bereits dokumentierte, freigegebene Architektur-
entscheidungen widerspiegeln:

- **97 CRITICAL-Regressionsfälle** aus dem historischen Vor-Audit-Benchmark einzeln geprüft: 96
  waren bereits korrekt (64× dokumentierte, freigegebene `office_pc`-Notebook-Exclusion, 2×
  dokumentierte `autoradio_opel_corsa`-OEM-Teile-Exclusion, 6× dokumentierte `gaming_pc`-
  Notebook-Exclusion, Rest zu Recht ausgeschlossenes Zubehör/Fotos/Spiele). **1 echter Bug:**
  `vintage_elektronik` — bare `"fernbedienung"` (Kategorie- UND Regel-Ebene bei den drei
  Röhrenfernseher-Regeln) blockierte echte Markenverstärker/-Receiver/-Fernseher, die ihre
  Fernbedienung als Ausstattungsmerkmal nennen ("Pioneer Stereo Verstärker mit Fernbedienung").
  **Fix:** auf `exclude_category_unless_preceded_by` umgestellt (identisches, bereits in
  `controller.yaml`/`ladekabel` etabliertes Muster). Blast Radius: ≥8 betroffene Markentitel in
  `price_history.jsonl`, 0 Kollisionen. Messbar verifiziert über Regression-Benchmark: CRITICAL
  97 → 96.
- **4 vom Nutzer gemeldete Live-Fehltreffer** einzeln geprüft, dabei 4 weitere, bisher ungemeldete
  Fehltreffer im selben Regelbereich gefunden:
  - **`handhelds`**: „module" (Plural von bereits vorhandenem „modul") fehlte — fixt
    "Nintendo DS und 3DS Spiele (AUSWAHL) Module - Sammlung Konvolut - 2DS DSi XL". Bewusst
    **nicht** „spiele" (Plural von „spiel") ergänzt: Blast-Radius-Check zeigt 5 echte
    Konsole+Spiele-Bundles, die dadurch fälschlich ausgeschlossen würden.
  - **`konsolen_bundles`**: „zubehör set" (Leerzeichen-Variante, nur Bindestrich/Zusammen-
    schreibung waren gelistet) + „mainboard"/„motherboard" (identisches, bereits in
    `office_pc.yaml`/`gaming_pc.yaml`/`notebook_resell.yaml` etabliertes Muster) ergänzt. Fixt
    3 Fälle: „12-in-1 Sport Zubehör Set…", „Nintendo Switch Sports Zubehör Set…", „Sony
    Playstation 4 Pro & PS4 Mainboard … Reparatur" (39€, Top-Deal — defektes Ersatzteil).
  - Blast Radius für alle 4 Ergänzungen: 0 Kollisionen mit echten Bundle-/Geräte-Titeln.
    Baseline-Regeneration bestätigt: sichtbare Einträge 2480 → 2476 (exakt die 4 jetzt korrekt
    ausgeblendeten Fehltreffer).

**Bewusst NICHT gefixt** (Analyse gegeben, keine Umsetzung ohne separate Freigabe/Datenbasis):

1. **„Xenoblade Chronicles für Nintendo New 3DS OVP"** (`handhelds`) — Spieltitel ohne jedes
   generische Signalwort ("spiel"/"modul"). Ein Fix bräuchte entweder eine Spieltitel-Blacklist
   (keine Datenbasis, Regel 4) oder einen neuen Matcher-Mechanismus (Umkehrung von
   `exclude_category_unless_preceded_by`) — Änderung an `matcher.py` selbst, verdient eigenen
   Schritt.
2. **„pro"-Kollision in `konsolen_bundles`** (3 bestätigte Fälle: „Snakebyte PS4 Wireless
   Pro-Controller", „Astro MixAmp Pro TR Gen 4 für PS4/PC", „Chin Fai Vertical Stand für PS4 /
   PS4 Slim / PS4 Pro") — bare „pro" in einer für 6 PS4-Regeln geteilten `require_all_of`-Gruppe
   kollidiert mit Produktnamen wie „Pro-Controller"/„MixAmp Pro". Restrukturierung der geteilten
   Gruppe berührt bereits bestehende, eingespielte Tests
   (`test_konsolen_bundles_plattform_referenz_fix.py`) — höheres Risiko als die additiven Fixes.
3. **„netzteil" als Positivsignal in `retro_konsolen`** (2 Fälle: „PS2 Netzteil Original…",
   „Nintendo 64 Netzteil") — anders als in `handhelds`/`konsolen_bundles` ist „netzteil" hier
   **bewusst** positives Signal (Vollständigkeitsindikator) in einer für 6 Regeln geteilten
   Gruppe. Eine Änderung wäre ein Architektur-Redesign, kein additiver Fix.

**Teil C — GPU-Preis-0€-Diagnose.** „ZOTAC Gaming GeForce RTX 4060 Spider-Man Edition" für 0€
als Top-Deal-Rating (`deal_intelligence_label: "VERY GOOD DEAL"`) gemeldet. **Root Cause
gefunden:** kein Matcher-/Kategorie-Bug, sondern ein **Quoka-seitiger Preis-Parsing-Defekt** —
`_price_to_float()` liefert vereinzelt `0.0` statt `None`. Bestätigt über den vollen
Datenbestand: 5 Punkte in `price_history.jsonl`, 2 aktuell in `found.json`, **ausschließlich**
`source="Quoka"` (RTX 4060, 2× MacBook Pro M3/M4, iPhone 16 Pro Max). Eigentliche
HTML-Parsing-Ursache **nicht** untersucht (bräuchte Live-Zugriff auf die aktuelle Quoka-Seite).

**Fix (Symptom, auf Nutzerwunsch):** `app.py::run_scan()` überspringt Items mit `price<=0` jetzt
genau wie bereits `price is None` (identischer, bestehender Mechanismus erweitert, keine neue
Logik). Schwelle bewusst `<=0` statt einer erfundenen Mindestsumme — einziger belegter
Fehlerwert (Regel 4), ein 7,99€-Legitimtreffer aus Batch 8 zeigt, dass eine höhere Pauschalgrenze
echte Deals kosten würde. **Python-Änderung → Rebuild nötig** (`docker compose up --build -d`),
anders als die reinen YAML-Fixes in Teil B.

15 neue Regressionstests (`test_vintage_elektronik_fernbedienung_kontext_fix.py`,
`test_handhelds_module_plural_fix.py`,
`test_konsolen_bundles_zubehoer_set_mainboard_fix.py`, `test_app_zero_price_skip.py`).
Zielgerichtete Suiten: 230 passed (`vintage`/`handheld`/`konsolen_bundle`/`app_`-Tests). Volle
Suite **1337/1337 grün** (vom Nutzer lokal verifiziert, 80,33s). `rule_analyzer.py`: 0 Findings.
Ruleset-Signatur geändert (`133dcd1a9f614e7e` → `b863e724db9b393c`, YAML-Änderungen in 3
Dateien).

## Abgeschlossen

- ursprüngliche Phasen 0–10
- YAML-Regelwerk und dynamische Kategorie-Discovery
- Scraper- und Detector-Registry
- Deal Score und Notification-Gating
- Price History / Marktpreisstatistik
- separates Resale-Price-Grouping
- Profit-/Flip-Kandidaten mit Margin-Feldern
- Top-Deal-Logik und Dashboard-KPIs
- Duplicate Detection und Presence Tracking
- Kategorie-Revalidierung und Data-Quality-Bausteine
- Rule Analyzer und Rule Coverage
- Rules-/Entry-/Regex-Caching
- Condition-/Lieferumfang-Detektoren
- mehrere neue Kategorien ohne Python-Code
- Phase-15-Performance-Optimierungen
- Systematischer Active-False-Positive-Audit über alle 19 Kategorien (PR #11–#25)
- Cross-Category-Routing-Audit mit zwei realen Fixes (PR #26–#28)
- Ruleset-Qualitätssystem: Baseline-Freeze, Regression-Benchmark, Kategoriequalitäts-Report,
  Preishistorie-Simulation, Cross-Category-Analyse (`tools/ruleset_quality/`, PR #29 + Folge-Sessions)
- 251-Listing-Worksheet vollständig gelabelt (KI-gestützt + menschlich verifiziert) und 3
  Exclude-Fixes daraus umgesetzt (PR #31)
- Umlaut-Fingerprint-Fix (`duplicate_detection.normalize_title()`)
- `lego_bundle`-Migration/-Bereinigung ausgeführt (freigegeben)
- Kontrollierte Preishistorie-Revalidierung v3 (read-only, Kernbefunde siehe Batch 7 oben)
- Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation gelöst, 4 Kategorien (Batch 8 oben)
- `controller`/`ladekabel`-Restlücke gelöst (Batch 9 oben)
- `RX 7600 XT`/`RX 7600`-Überlappung gelöst + min_vram_gb-Bug bei 4 weiteren GPU-Modellen
  (`rtx_3060_ti`/`rtx_3070`/`rtx_4060`/`rtx_2080_ti`) behoben (Batch 10 oben)
- Echte End-to-End-Scan-Performance-Messung + Scraping parallelisiert (Batch 11 oben)
- Persistence-Batching für seen.json/found.json (Batch 12 oben)
- Reale Wirkung beider Performance-Fixes gegen Produktivdaten verifiziert (Batch 13 oben)
- Vollständiger read-only Kategorie-Audit (0 Abweichungen) + 5 Live-Fehltreffer über 3 Kategorien
  behoben + Preis-Mindestbetrag-Guard gegen Quoka-Parsing-Defekt (Batch 14 oben)

## Aktuelle Systemkette

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

Zusätzlich (read-only, außerhalb der Produktionskette): `tools/ruleset_quality/` — Regression-
Benchmark/Qualitätssystem, siehe Batch-Einträge oben und `tools/ruleset_quality/README.md`.

Wichtige Architekturregeln:

- `market_price` und `estimated_resale_price` bleiben getrennt.
- Dünne Resale-Daten dürfen keinen künstlich optimistischen Flip-Kandidaten erzeugen.
- YAML bleibt die primäre Erweiterungsebene für Kategorien.
- Neue Detector-Typen benötigen weiterhin Python-Code.
- Fixes verwenden bestehende YAML-/Matcher-Primitive statt eines neuen generischen Matcher-Systems.
- `tools/ruleset_quality/` ist kein Bestandteil der Produktionskette und wird von `app.py`/
  `matcher.py` nicht importiert.

## Datenqualität / offene Punkte

1. Coverage-/False-Positive-Rate: 251-Listing-Stichprobe jetzt gelabelt (217 TP/21 FP/13 UNCLEAR,
   davon nur 30 Listings unabhängig einzeln geprüft, 221 pauschal übernommen — siehe Batch 4).
   Precision 91,2% (KI-Vorbewertung, nicht durch die 221 pauschalen Bestätigungen zusätzlich
   verifiziert).
2. 19 Regeln ohne Produktivdaten weiter beobachten.
3. Orphan-Datenpunkte aus der entfernten `spielzeug_bundles`-Kategorie: **erledigt** (Batch 6) —
   5 migriert, 655 gelöscht, 3 bewusst erhalten.
4. `RX 7600 XT`/`RX 7600`-Überlappung: **erledigt** (Batch 10) — die eigentliche Ursache war ein
   min_vram_gb-Bug (globaler 12GB-Default blockierte 8GB-Karten mit "8GB"-Schreibweise im Titel),
   nicht die längst gefixte Match-Präzedenz. Gleicher Bug bei 4 weiteren GPU-Modellen mitgefixt.
5. `controller`-`ladekabel`-Exclude: **erledigt** (Batch 9) — Lücke betraf Lade-Stationen/-Geräte,
   nicht den Kabel-Mechanismus selbst (der bereits korrekt funktionierte).
6. Resale-Confidence (`HIGH/MEDIUM/LOW`) ist eine mögliche nächste Qualitätsstufe.
7. automatische Data-Quality-Warnungen weiterentwickeln.
8. `konsolen_bundles`/`retro_konsolen`: "Spieltitel ohne Plattform-Bindestrich"-Restlücke —
   weiterhin offen, jetzt auch in `retro_konsolen` bestätigt (Batch 3, Muster 3).
9. 9 real belegte, aber bewusst zurückgestellte Fehltreffer-Muster (27 Titel) aus dem Active-FP-
   Audit — vollständige Liste: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.
10. Restliche unauditierte Nischen-Feinheiten nur bei neuem Datenpunkt erneut aufgreifen.
11. Umlaut-Fingerprint-Bug: **Code-Fix umgesetzt** (Batch 5), aber **nicht rückwirkend** — für
    `retro_konsolen`/`vintage_elektronik` bleibt die historische Preishistorie-Revalidierung
    praktisch unmöglich (Titel nicht rekonstruierbar, siehe Batch 7). Dauerhafte, dokumentierte
    Einschränkung, keine weitere Aktion vorgesehen.
12. Ground-Truth-Label-Abdeckung: 251-Listing-Worksheet jetzt vollständig gelabelt (siehe Nr. 1).
13. Regel "Switch Pro Controller" hat nur zwei Preisstufen (bis 35 €) statt der sonst üblichen
    drei — explizit auf Nutzerentscheidung **nicht** um eine dritte Stufe erweitert (keine
    belastbare Datenbasis für eine Preisgrenze, siehe
    `ENTSCHEIDUNGEN_TECHNISCHE_VORBEREITUNG_BERICHT.md`).
14. Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation: **erledigt** (Batch 8) — 4 gezielte
    Exclude-Fixes in `controller`/`handhelds`/`netzteil`/`konsolen_bundles`.
15. `M.2`-Punktuation wird von `normalize_title()` entfernt (aus "M.2" wird "m 2"),
    wodurch ein Fingerprint vereinzelt andere Signalwörter enthalten kann als der echte Titel
    (1 beobachteter Fall: `m2_ssd` → `sata_ssd`-Fehlklassifikation bei Fingerprint-Revalidierung).
    Nur beobachtet, nicht verallgemeinert, keine Aktion.
16. Drei neue, real bestätigte, aber bewusst zurückgestellte Fehltreffer-Muster (Batch 14):
    Spieltitel ohne generisches Signalwort (`handhelds`, z.B. "Xenoblade Chronicles für Nintendo
    New 3DS"), „pro"-Kollision in einer für 6 `konsolen_bundles`-Regeln geteilten Gruppe (3
    Fälle), „netzteil" als bewusstes Positivsignal in einer für 6 `retro_konsolen`-Regeln
    geteilten Gruppe (2 Fälle) — alle drei bräuchten ein Redesign geteilter Regelgruppen bzw.
    einen neuen Matcher-Mechanismus statt eines additiven Excludes, daher zurückgestellt.
17. Quoka-Preis-Parsing-Defekt: Symptom gefixt (Batch 14, `price<=0`-Guard in `run_scan()`),
    HTML-seitige Ursache in `scrapers/quoka.py::_price_to_float()` **nicht** untersucht (bräuchte
    Live-Zugriff auf die aktuelle Quoka-Seite, spekulativ ohne diesen nicht sinnvoll lösbar).

## Nächste Prioritäten

### P0 — offene Punkte

- Keine offenen P0-Punkte (alle in Batch 1–14 dokumentierten Punkte abgeschlossen und verifiziert).
  Nächste Schritte laut Datenqualität/offene Punkte: Nr. 6 (Resale-Confidence), Nr. 16 (drei
  zurückgestellte Fehltreffer-Muster) oder Nr. 17 (Quoka-Root-Cause) — alle drei explizit auf
  Nutzerentscheidung zurückgestellt, kein aktiver Blocker.
- **Rebuild ausstehend:** Batch 14 enthält eine Python-Änderung (`app.py`, Preis-Guard) —
  `docker compose up --build -d` nötig, bevor der Fix produktiv wirkt (die YAML-Fixes in
  Batch 14 wirken bereits ohne Rebuild, volume-gemountet).
- Beobachtung aus Batch 13 (kein Blocker): einen der nächsten 1-2 Scans gegenchecken, sobald sich
  `dedupliziert` wieder im Normalbereich (<650) einpendelt, für eine "steady state"-Bestätigung
  der Matching+Scoring-/Persistence-Werte.
- Ein möglicher, bisher nicht gemessener Verdacht: derselbe min_vram_gb-Musterbug (Batch 10)
  könnte theoretisch auch außerhalb von `gpu` relevant sein — bisher nicht geprüft, kein aktiver
  Punkt.

### P1 — Datenqualität

- Resale-Confidence ausbauen.
- Datenqualitätsdiagnosen automatisieren.

### P2 — Wartbarkeit

- `app.py` nur schrittweise weiter modularisieren, wenn konkreter Änderungsdruck besteht.
- keine Komplett-Refaktorierung.

### P3 — Features

Neue Kategorien oder weitere Deal-Intelligence erst nach den Stabilitäts-/Qualitätsschritten
priorisieren.

## Arbeitsregeln

- Kein Big-Bang-Rewrite.
- Keine Threshold-Änderungen ohne Datenbasis.
- Keine Tests löschen oder abschwächen.
- Keine Performance-Optimierung ohne Messung.
- Keine bestehende Business-Logik duplizieren.
- Nach technischen Änderungen vollständige Testsuite ausführen.
- `TECHNISCHER_PROJEKTSTATUS.md` und `STATUS.md` nach abgeschlossenen Änderungen synchron halten.

## Dokumentationsregel

`TECHNISCHER_PROJEKTSTATUS.md` ist die aktuelle technische Referenz. Historische Phase-/
Completion-Reports bleiben als Entscheidungs- und Messnachweise erhalten, gelten aber nicht als
aktueller HEAD- oder Teststand.
