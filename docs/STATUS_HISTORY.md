# STATUS-Historie — vollständige Batch-Dokumentation

> **Zweck:** Dieses Dokument enthält die vollständige, wortgetreue Historie aller bisher
> abgeschlossenen Arbeits-Batches (1–19), die vor der STATUS.md-Restrukturierung vom
> 2026-08-16 direkt in `STATUS.md` unter „Zuletzt abgeschlossene Batches" standen.
>
> `STATUS.md` selbst enthält ab jetzt nur noch eine kompakte Tabellenübersicht (Batch,
> Kurzbeschreibung, Testergebnis, Referenz) und verweist für Details hierher. **Kein
> Informationsverlust** — dieses Dokument ist eine reine Auslagerung, kein Kürzung.
>
> Aktueller technischer Stand: siehe `STATUS.md`. Technische Referenz-Tiefe: siehe
> `TECHNISCHER_PROJEKTSTATUS.md`.

---

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

### 15. „pro"-Kollision in `konsolen_bundles.yaml` gelöst (zuvor in Batch 14 zurückgestellt)

Vertiefte Root-Cause-Analyse ergab: die 3 in Batch 14 gemeldeten Live-Fehltreffer betrafen **2**
(nicht wie zunächst vermutet 6) für PS4-Regeln geteilte `require_all_of`-Gruppen
(`"PS4 Slim / Pro Bundle ★ Top-Deal"`/`"👍 Guter Preis"`) — und hatten **drei unabhängige, einzeln
lösbare Ursachen**, keine gemeinsame:

1. **„Snakebyte PS4 Wireless Pro-Controller PC Bayern München"** (52€, Top-Deal): es existierte
   bereits ein `exclude_category_unless_preceded_by`-Eintrag für „pro controller" (Leerzeichen,
   0 Kollisionen im vollständigen 195-Titel-Test einer früheren Session) — er griff aber nicht bei
   der Bindestrich-Schreibweise „Pro-Controller" (identisches Kompositum-Problem wie
   „zubehör-set"/„zubehörset"/„zubehör set"). **Fix:** „pro-controller" als Geschwister-Eintrag mit
   demselben Konnektor-Anker ergänzt — erbt dieselbe 0-Kollisionen-Eigenschaft, da nur die
   Bindestrich-Schreibweise zusätzlich erfasst wird.
2. **„Astro MixAmp Pro TR Gen 4 für PS4/PC – Audio-Verstärker"** (50€, Top-Deal): ein
   Audio-Verstärker-Produktname ohne jeden Bezug zu „Controller". **Fix:** bare `"mixamp"`-Exclude
   (eindeutiger Markenname, kein Bundle-Kollisionsrisiko).
3. **„Chin Fai „The Shark" Vertical Stand für PS4 / PS4 Slim / PS4 Pro"** (15€, Top-Deal): matchte
   über „slim"+„pro" als reine Plattform-Kompatibilitätsangaben. **Fix:** neuer
   `exclude_category_unless_also_contains`-Eintrag für „vertical stand" — bewusst **nicht** über
   `unless_preceded_by` (Adjazenz-Check), weil der einzige echte Bundle-Kollisionsfall in
   `price_history.jsonl` ("PS4 Slim inkl 1 Controller Vertical Stand und Lampe", 80€) den
   Konnektor „inkl" NICHT unmittelbar vor „Vertical Stand" stehen hat (dazwischen "1 Controller")
   — ein Adjazenz-Check hätte diesen echten Treffer zerstört, die titelweite Präsenzprüfung
   (Konnektor irgendwo im Titel) erhält ihn korrekt.

**Wichtige Korrektur der Batch-14-Einschätzung:** ein initial erwogener, breiterer Fix (bare
Exclude für „pro controller"/„pro-controller" ohne Konnektor-Bedingung) wurde **verworfen**, nachdem
ein systematischer Blast-Radius-Check gegen den vollen `price_history.jsonl`-Korpus ~5-7 reale
Kollisionen mit echten Konsole+Pro-Controller-Bundles zeigte, die informell ohne direkten
Konnektor formuliert sind (z.B. "Nintendo Switch Konsole mit Pro Controller & 5 Spielen" — der
bereits bestehende, engere Fix mit Konnektor-Bedingung bleibt davon unberührt und schützt diese
Fälle weiterhin korrekt).

6 neue Regressionstests (`test_konsolen_bundles_pro_kollision_fix.py`). Zielgerichtete Suite:
67 `konsolen_bundle`-Tests grün (inkl. der zuvor kritischen `test_pro_controller_im_echten_
bundle_matcht_weiterhin`/`test_pro_slim_ohne_zubehoerwort_matcht_weiterhin`). Volle Suite
**1355/1355 grün** (vom Nutzer lokal verifiziert, 85,27s). `rule_analyzer.py`: 0 Findings.
Ruleset-Signatur geändert (`b863e724db9b393c` → `6266e4a437c1fbc4`). Reiner YAML-Fix, kein
Rebuild nötig.

### 16. Alle drei verbleibenden Batch-14-Punkte gelöst

**Xenoblade-Spieltitel-Problem (`handhelds.yaml`):** die require_all_of-Gruppe 2 für 3DS/2DS hat
kein plattformunabhängiges Signalwort (anders als `retro_konsolen`: „konsole"/„gerät"/„system"),
sondern matcht bereits über den reinen Plattformnamen. Zusätzlich zum gemeldeten Fall gefunden:
„Super Mario 3D Land für Nintendo 3DS 3DS XL" (5€, price_history.jsonl) — identisches Muster.
**Fix:** neuer `exclude_category_unless_also_contains`-Eintrag für „für nintendo new 3ds"/„für
nintendo 3ds" (Kontextliste: „konsole"/„system"/„gerät", bewusst OHNE „xl"/„new 3ds" — das wären
dieselben mehrdeutigen Wörter, die das Problem verursachen). Erstmalige Einführung dieses bereits
in `konsolen_bundles.yaml` etablierten Mechanismus in `handhelds.yaml`. Bewusst nicht auf 2DS/Steam
Deck/ROG Ally/Legion Go erweitert — für Letztere sind alle „für [Marke]"-Treffer im Korpus bereits
eindeutiges, anderweitig abgedecktes Zubehör, kein Spieltitel-Problem.

**`netzteil`-Positivsignal (`retro_konsolen.yaml`):** systematischer Blast-Radius-Check ergab: von
24 Titeln, die AUSSCHLIESSLICH über „netzteil" matchen (kein anderes Gruppe-2-Wort), hat genau 1
(„Nintendo N64 Control Deck 2 Original Controller Netzteil Erweiterungskarte", 99€) „controller"
im Titel — alle anderen 23 sind Standalone-Netzteil-/Ladegerät-Angebote, u.a. die beiden gemeldeten
Fälle. **Fix:** identisches, bereits produktives Muster wie das bestehende „memory card"-Exclude
in derselben Datei — `"netzteil": ["controller", "konsole", "ersatzkonsole"]` unter
`exclude_category_unless_also_contains`.

**Quoka-Preis-Parsing-Defekt (`scrapers/quoka.py`):** Root Cause **an der Wurzel gelöst**, nicht
nur das Symptom (Batch 14s `price<=0`-Guard in `app.py` bleibt zusätzlich als Sicherheitsnetz
bestehen). Live-Recherche gegen quoka.de (Suche „RTX 4060") ergab: das Normalpreisfeld
(`span.article-price`, ohne verschachteltes `.new-price`) nutzt ab 1000€ ein **Leerzeichen als
Tausendertrennzeichen** (z.B. „1 000 EUR", „1 050 EUR" — live auf der Seite bestätigt), das
`_price_to_float()` bisher nicht kannte. Bei runden Tausendern (Rest nach letztem Leerzeichen =
"000") entstand dadurch 0.0, sonst ein stiller Trunkierungsfehler (z.B. "1 050 EUR" → 50.0 statt
1050.0). `_price_to_float()`-Regex um eine dritte Alternative (`\d{1,3}(?: \d{3})+`) ergänzt,
gegen 17 Preisformate verifiziert (alle bisherigen Formate inkl. Rabattpreis-Punkt-Varianten
bleiben korrekt, inkl. mehrstelliger Tausenderpunkt-Fall „850.000 EUR" = 850.000€, live gegen
Fahrzeuganzeigen verifiziert). **Nebeneffekt:** Angebote, die zuvor durch den `price<=0`-Guard
still verworfen wurden, erscheinen jetzt korrekt mit echtem Preis — Recall-Verbesserung, nicht
nur Korrektheit. Wirkt nur auf künftige Scans, keine rückwirkende Korrektur bereits gespeicherter
0€-Punkte (analog Umlaut-Fingerprint-Fix, Batch 5).

8 neue Regressionstests (`test_handhelds_spieltitel_fuer_3ds_fix.py`,
`test_retro_konsolen_netzteil_kontext_fix.py`, 2 neue Fälle in `test_scraper_quoka.py`).
Zielgerichtete Suiten: 139 passed (`handheld`/`retro_konsolen`/`quoka`/`scraper`-Tests). Volle
Suite **1358/1358 grün** (vom Nutzer lokal verifiziert, 85,27s). `rule_analyzer.py`: 0 Findings.
Baseline-Regeneration bestätigt: alle 3 gemeldeten Ziel-Titel korrekt ausgeblendet.
Ruleset-Signatur geändert (`6266e4a437c1fbc4` → `20737fe48c8f52af`). YAML-Fixes wirken ohne
Rebuild, der Quoka-Scraper-Fix (`scrapers/quoka.py`) ist eine Python-Änderung und braucht
`docker compose up --build -d`.

### 17. `found.json`-Vollanalyse (extern bereitgestellter Snapshot): 36 Fehltreffer über 3 Kategorien behoben

Der Nutzer öffnete eine aktuellere `found.json` (2.474 Einträge, `/home/robin/Downloads/`,
außerhalb des Repos) im IDE und bat um eine vollständige Kategorie-Fehleranalyse, mit 3
Beispielen (PS-Vita-Spiele als `handhelds`, Grafikkartenlüfter als `gpu`, Switch-Spiel als
`konsolen_bundles`). Systematischer Scan aller 2.474 Einträge nach Kategorie (Zubehör-/Spiel-
Rotflaggen-Heuristik, jeder Kandidat einzeln gegen `evaluate()`/`is_still_valid_category()`
verifiziert) ergab **17 real bestätigte Live-Fehltreffer über 3 Kategorien** — bei der
Root-Cause-Analyse während der Umsetzung stellten sich zwei der drei Cluster als deutlich größer
heraus (**36 behoben insgesamt**):

**`konsolen_bundles` (10 Fälle) — „ovp"/„bundle"/„set" als zu schwache Positivsignale.** Die
`require_all_of`-Gruppe 2 nutzt diese Wörter als Gerätenachweis, sie tauchen aber auch in reinen
Spiele-Sammlungen ohne Konsole auf (z.B. "Nintendo Switch Spiele Bundle", "FIFA & F1 Spiele Paket
Bundle (7 Spiele) PlayStation 3 & 4"). **Fix:** neuer `exclude_category_unless_also_contains`-
Eintrag für `"spiele"` mit Kontextliste = alle echten Geräte-/Modell-Marker der Kategorie
(konsole/system/slim/pro/Speichergrößen/xl/oled/lite/...). Blast-Radius-Check gegen 120 Titel mit
"spiele" in dieser Kategorie: 26 ohne jeden Marker (ausnahmslos reine Spiele-Angebote), die
übrigen ~94 haben jeweils mindestens einen echten Marker — 0 Kollisionen. Zusätzlich
`"panzerglas"`/`"displayschutz"` (bare, 1 Treffer: "Panzerglas Displayschutz Nintendo Switch
Lite").

**`retro_konsolen` (25 Fälle, ursprünglich 6 gemeldet) — „komplett" als Zustands- statt
Gerätebeweis.** Root-Cause-Analyse der 6 gemeldeten Fälle deckte einen deutlich größeren Cluster
auf: „komplett" (group2-Alternative) ist in der Praxis ein Vollständigkeits-/CIB-Zustandsbegriff,
der bei EINZELSPIELEN mindestens genauso häufig vorkommt wie bei Konsolen (z.B. "Phantasy Star
Online... - Nintendo GameCube - komplett", "FIFA Football 2003 – PS1 – deutsche PAL-Version –
komplett" — 12 weitere Einzelspieltitel ohne das Wort „Spiel" im Titel, die daher auch von der
Batch-16-Fix nicht erfasst wurden). **Fix:** `exclude_category_unless_also_contains` für
`"komplett"` (Kontextliste: konsole/heimkonsole/spielekonsole/gerät/system/kabel/slim/fat/memory
card/**controller**) sowie ergänzend `"spiel"`/`"spiele"` mit derselben Liste. „Controller" wurde
bewusst in die Kontextliste aufgenommen, nachdem ein Testlauf eine bereits bestehende,
absichtliche Testerwartung (`test_signal_komplett_positiv`: "Nintendo 64 / N64 + Controller +
Spiel Tetris komplett" soll matchen) brach — Ergänzung verifiziert ohne erneute Kollision mit den
36 bestätigten Fehltreffern. Blast-Radius-Check gegen den vollen, aktuell sichtbaren
`found.json`-Korpus: 20 Treffer für „komplett" ohne jeden stärkeren Marker, ausnahmslos reale
Einzelspiel-/Zubehör-Fehltreffer. Zusätzlich `"emul"` (bare, Abkürzung von „Emulator" — real
bestätigt: "R36 Ultra X handheld Konsole... Ps1 Spiele Emul", ein moderner Android-Emulations-
Handheld, keine echte Konsole; bestehendes `"emulator"`-Exclude griff bei der Abkürzung nicht).

**`gpu` (1 Fall).** „Grafikkartenlüfter für MSI RTX 3060 TI GAMING X, RX 6700 XT GAMING-X"
(25,95€, Top-Deal) — reines Lüfter-Zubehörteil, kein `"lüfter"`-Exclude in `gpu.yaml` vorhanden.
**Fix:** bare `"grafikkartenlüfter"` (Kompositum, nicht bare `"lüfter"` — hätte echte Karten mit
eigener Dual-/Custom-Lüfter-Beschreibung fälschlich blockiert, z.B. "ZOTAC ... RTX 3060 TI
Grafikkarte Dual-Lüfter").

9 neue Regressionstests (`test_konsolen_bundles_spiele_bundle_fix.py` 3,
`test_retro_konsolen_einzelspiele_ohne_geraet_fix.py` 4,
`test_gpu_grafikkartenluefter_fix.py` 2). Zielgerichtete Suite: `pytest app/tests/ -k
"konsolen_bundle or retro_konsolen or gpu"` → 164 passed. Volle Suite **1372/1372 grün** (vom
Nutzer lokal verifiziert, 87,97s). `rule_analyzer.py`: 0 Findings. Baseline-Regeneration:
sichtbare Einträge 2467 → 2430 (−37, passt zu den 36 gefixten Fällen plus normalem
Scan-Rauschen). Ruleset-Signatur geändert (`20737fe48c8f52af` → `59f03f5a2f2c1d7c`). Reiner
YAML-Fix, kein Rebuild nötig.

### 18. Nutzer-Fehltreffer-Analyse (`FALSE_POSITIVES_ANALYSE_2026-08-15.txt`): 25 von 34 bestätigten Fehltreffern über 3 Kategorien behoben, Preis-Anomalie bewusst nicht gefixt

Der Nutzer öffnete eine selbst erstellte, manuelle Analyse (34 bestätigte + 6 zweifelhafte
Fehltreffer aus einem 2.500-Einträge-Live-`found.json`-Snapshot, jeder Titel einzeln geprüft) mit
5 unabhängigen Root Causes (A–E) und gab die Umsetzung schrittweise frei (A einzeln, dann B–E im
Batch).

**A) `konsolen_bundles`, Nintendo Switch (18 Fälle) — bare „ovp" matcht Spieltitel als Konsole.**
Vollständige Entfernung von „ovp" aus `require_all_of` (wie in der Analyse zunächst vorgeschlagen)
hätte eine bereits bestehende, dokumentierte Auftragsvorgabe („ovp bleibt Positivsignal") sowie
mehrere Regressionstests gebrochen, die kurze, echte Kurz-Verkäufe wie "Nintendo Switch OLED 64GB
OVP" absichern. **Fix:** stattdessen `exclude_category_unless_also_contains` für `"ovp"` nach
demselben, bereits etablierten Muster wie `"spiele"` — „ovp" bleibt Positivsignal, blockiert aber,
wenn im gesamten Titel kein Geräte-Marker vorkommt. Ein bestehender Test
(`test_bare_ovp_ohne_zusatzangabe_matcht_weiterhin`) musste dadurch bewusst umgekehrt werden (die
zugrundeliegende Annahme war identisch mit dem jetzt gefixten FP-Muster, lexikalisch nicht
unterscheidbar); ein zweiter, vormals dokumentiert offener Grenzfall
("Donkey Kong Bananza Nintendo Switch 2 2025 OVP") wurde als Nebeneffekt mitgeschlossen.

**B) `retro_konsolen`, PS1/PS2/N64/GameCube (8 Fälle) — „kabel"/„netzteil" ohne Gerät.**
„netzteil" hatte bereits einen kontextbewussten Exclude (deckte 4 der 8 Fälle bereits ab);
„kabel" fehlte noch. **Fix:** identischer Mechanismus für `"kabel"` ergänzt (Kontextliste:
controller/konsole/ersatzkonsole). Bewusste Restlücke: 2 Analyse-Grenzfälle (Teil 2, "eher echtes
Gerät") werden mitblockiert, lexikalisch nicht von den bestätigten FP unterscheidbar.

**C) `handhelds`, PS Vita (3 Fälle) — bare „ovp" matcht Spieltitel als Konsole.** Anders als bei A:
ein bare „ovp"-Trigger hätte in `handhelds.yaml` **kategorieweit** gewirkt (mehrere Geräte in
einer Datei) und echte Steam-Deck-/ROG-Ally-/3DS-Verkäufe mitblockiert — real aufgetreten und im
ersten Testlauf korrigiert. **Fix:** stattdessen die PS-Vita-Plattformbegriffe selbst als Trigger
(`"ps vita"`/`"psvita"`/`"playstation vita"`), Kontextliste ergänzt um `"pch"`
(Modellcode-Präfix, rettet echte Kurz-Verkäufe wie "PS Vita PCH-1004").

**D) `konsolen_bundles`, 3 Zubehör-Einzelfälle.** Gezielte Excludes für SD-Karte (`"microsdxc"`),
PS4-Ersatzfestplatte (`"interne festplatte"`, dabei einen zweiten, in der Analyse nicht gemeldeten
PS4-Pro-Fall zusätzlich gefangen) und Switch-Tragetasche (`"travelcase"`/`"tragetasche"` —
Kompositum-Lücke, das bereits vorhandene bare „tasche" greift wegen Wortgrenzen-Matching nicht).

**E) 1€-PS4-Preisanomalie — bewusst NICHT umgesetzt.** Anders als beim GPU-0€-Fund (Batch 16, ein
isolierter, mechanistisch bestätigter Quoka-Parsing-Defekt) zeigte eine Korpus-Analyse aller
Treffer ≤3€ (34 in `found.json`, 266 in `price_history.jsonl`) mindestens drei unterschiedliche
Ursachen ohne gemeinsamen Root Cause: legitime Billig-Kategorie (Lego-Konvolute), Tausch-/
Barter-Anzeigen mit Preis-Platzhalter ("Tausche iPhone 16 Pro Max gegen..."), sowie der gemeldete
Einzelfall selbst (keines der beiden Muster, Quelle Kleinanzeigen, kein bekannter Parsing-Bug).
Ohne belastbare Datenbasis für eine einzelne Schwelle (CLAUDE.md Abschnitt 2.4) nicht umgesetzt.
Mögliche Folgeaufgabe (separat zu entscheiden): Tausch-/Barter-Anzeigen anhand Titel-Mustern
("tausche"/"gegen") aus Notification/Preisstatistik ausschließen — nicht Teil dieses Batches.

13 neue Regressionstests (`test_retro_konsolen_kabel_kontext_fix.py` 4,
`test_handhelds_ps_vita_ovp_kontext_fix.py` 5, `test_konsolen_bundles_zubehoer_einzelfaelle_fix.py`
4), 1 bestehender Test umgekehrt/umbenannt
(`test_bare_ovp_ohne_zusatzangabe_matcht_weiterhin` →
`test_bare_ovp_ohne_geraete_marker_matcht_nicht_mehr`), 1 bestehender Test aktualisiert
(vormals dokumentierte Restlücke jetzt geschlossen). Zielgerichtete Suite: `pytest app/tests/ -k
"konsolen_bundle or retro_konsolen or handheld or vita or switch or ovp or kabel"` → 218 passed.
Volle Suite in dieser Session **nicht** ausgeführt (CLAUDE.md Abschnitt 3.4.4, ausstehende
Nutzer-Freigabe). `rule_analyzer.py`: 0 Findings. Ruleset-Signatur geändert
(`59f03f5a2f2c1d7c` → `f6216b45c6440ab5`). Reiner YAML-Fix, kein Rebuild nötig.

### 19. Category-False-Positive-Forensics-Tool + Fix-Queue (PR #45, `8008414`) + Korrektur: versehentlich gelöschte `konsolen_bundles.yaml` wiederhergestellt

**19a — neues Tool (`tools/ruleset_quality/forensics_false_positives.py`).** Setzt den
vom Nutzer vorgegebenen Auftrag „Category False-Positive Forensics + gezielte Fix-Queue" um.
Vorab vollständige Analyse der bestehenden `tools/ruleset_quality/`-Toolchain (Phase 19.1–19.5) —
das neue Tool baut **ausschließlich** auf vorhandenen Bausteinen auf
(`benchmark._after_match_state()`, `label_store.py`, `common.evaluate()`/`load_current_rules()`),
keine zweite Matching-/Bewertungslogik. Extrahiert die 19 bestätigten `FALSE_POSITIVE`-Fälle aus
`docs/DASHBOARD_MATCH_FORENSICS.json`, gruppiert sie nach gespeicherter Kategorie, ermittelt den
aktuellen Match-Zustand über den echten Produktionspfad und leitet eine priorisierte Fix-Queue ab
(P0–P3). `UNCLEAR`-Fälle werden strikt getrennt als FP-Kandidaten geführt, nie mit bestätigten FP
vermischt. Root-Cause-Klassifikation übersetzt nur das im Forensik-Snapshot bereits belegte
`root_cause`/`reason`-Feld in eine feste Taxonomie (`missing_exclude`/`weak_signal`/
`replacement_part_false_positive`/…) mit `confidence` — unbekannte Werte werden als
`ambiguous`/`manual_review` ausgewiesen, nie geraten. `FALSE_POSITIVE → andere Kategorie` zählt
nirgends automatisch als Fix. **Ändert keine YAML-Regeln.**

Lauf gegen den echten Datensatz: 19 bestätigte FP, Konsistenz mit dem bekannten Referenzstand
(TP 2252/FP 19/UNCLEAR 35) bestätigt. **17 von 19 bereits durch spätere Fixes verschwunden**
(`KEIN_TREFFER`), 2 weiterhin aktiv: `iphone` (P0, `replacement_part_false_positive`, "Mainboard
Platine" matcht weiterhin `iPhone 15 Pro Max (≥512GB)`) und `retro_konsolen` (P1, `weak_signal`,
ein Nintendo-DS-Lite-Fall). 24 neue Tests (`test_forensics_false_positives.py`), zielgerichtete
Suite `pytest app/tests/ -k "ruleset_quality or forensics"` → 63 passed. Reiner Zusatz unter
`tools/ruleset_quality/` + `tools/ruleset_quality/generated/` — keine Produktionsdatei berührt.

**19b — Korrektur einer vorbestehenden, unbeabsichtigten Löschung.** Bei der routinemäßigen
gestuften Testverifikation nach 19a fielen 4 Tests fehl (`test_matcher_handheld_false_positives.py`
u. a., "Nintendo Switch Lite" matcht nicht mehr). Ursache: `app/rules/konsolen_bundles.yaml` war
bereits **vor** dieser Session im Working Tree gelöscht — unbestätigt, ohne Commit, ohne
dokumentierte Migration (verifiziert: kein `konsolen_bundles`-Inhalt in einer anderen YAML
aufgegangen, `konsolen_bundles` ist weiterhin eine aktive, in `STATUS.md` 28-fach referenzierte
Kategorie). Vor der Korrektur geprüft, ob ein laufender Prozess dafür verantwortlich sein könnte:
nein — der aktiv laufende Produktions-Scanner (`python app.py`, seit 05:41 Uhr) liest YAML nur
lesend, schreibt sie nie. Datei wiederhergestellt via `git checkout HEAD -- app/rules/
konsolen_bundles.yaml` (reine Restauration bereits committeten Inhalts, keine inhaltliche
Änderung, Ruleset-Signatur unverändert). Nachweislich behoben: `pytest app/tests/ -k "matcher or
category_validation or ruleset"` → 373 passed (zuvor 4 failed). **Bewusst nicht angefasst:**
`data/found.json`/`price_history.jsonl`/`time_to_sell.jsonl` (+ neue `data/seen.json`/
`gpu_watch.log`) — deren Diffs sind kein Fehler, sondern Live-Laufzeitzustand des aktiv laufenden
Produktions-Scanners; ein Zurücksetzen hätte reale, über Stunden gesammelte Scan-Ergebnisse
gelöscht. Ebenfalls bewusst nicht angefasst: mehrere gelöschte, durch neuere Zeitstempel-Versionen
ersetzte Diagnose-Reports unter `tools/ruleset_quality/generated/` — auf Nutzerentscheidung als
beabsichtigtes Aufräumen belassen, keine Produktionsauswirkung.

### 20. Fix-Queue abgearbeitet + Ground-Truth/Routing-Assessment sauber getrennt + 35 UNCLEAR-Fälle klassifiziert (PR #47–#51)

Direkter Folgeschritt zu Batch 19a (Forensics-Tool + Fix-Queue). Fünf Commits, alle auf derselben
Fix-Queue (`tools/ruleset_quality/generated/false_positive_fix_queue.json`) aufbauend:

**20a — `iphone`-Mainboard-Fehltreffer behoben (PR #47, `869562b`).** Setzt den P0-Eintrag aus
Batch 19a um: `exclude_category` in `app/rules/iphone.yaml` um `"mainboard"`/`"motherboard"`
ergänzt — identisches, bereits 5-fach etabliertes Muster aus `gaming_pc.yaml`/`office_pc.yaml`/
`notebook_resell.yaml`/`handhelds.yaml`/`konsolen_bundles.yaml`. Behebt den bestätigten
Fehltreffer „Apple iPhone 15 Pro Max 512GB Mainboard Platine..." (0 Kollisionen gegen 478
historische `iphone`-TRUE_POSITIVE-Titel). **Bewusst NICHT gefixt** (Pflicht-Analyse vor jedem Fix
ergab konkretes Risiko, echte Treffer zu zerstören): `konsolen_bundles`/PS4-PS5-HDMI-Reparatur
(explizite Auftragsvorgabe, Manual-Review), `retro_konsolen`/DS-Lite (Fix würde 3 weitere,
lexikalisch identische, vermutlich echte Handheld-Titel mitblockieren), `konsolen_bundles`/Switch
+ Xbox (Standard-Fix-Mechanismus würde beide Fälle gar nicht lösen, engere Variante würde
mindestens 2 vermutlich echte Konsolen-Bundles mitblockieren). Ergebnis: 15 von 19 historischen FP
dauerhaft gelöst, 4 bewusst offen mit dokumentierter Begründung. 0 Regressionen (`rule_analyzer.py`
0 Findings, Benchmark gegen `historical_forensics_baseline.json`: 0 neue CRITICAL/HIGH_CANDIDATE-
Fälle, 373+ gezielte Tests grün). Zusätzlich (`17c18fd`, dokumentierender Commit): FP-/UNCLEAR-
Reports aus der Ground-Truth-Analyse committet (19 FALSE_POSITIVE, 35 UNCLEAR identifiziert;
Hauptcluster: `konsolen_bundles` 6 FP/34 UNCLEAR „ovp"/„bundle"/„set" ohne Konsole, `retro_konsolen`
4 FP/1 UNCLEAR Zubehör ohne Konsole, `handhelds` 4 FP Zubehör ohne Gerät).

**20b — PS4/PS5-HDMI-Reparatur-Fehltreffer behoben, Switch/Xbox als Ground-Truth-Artefakt
dokumentiert (PR #48, `8f855e9`).** `exclude_category_unless_also_contains` in
`konsolen_bundles.yaml` um `"reparatur"` ergänzt (identischer Mechanismus wie „spiele"/„ovp" in
derselben Datei). Setzt einen Nutzer-Vorschlag um, korrigiert dabei 2 Bugs im Erstentwurf:
Markennamen („nintendo"/„playstation") waren im Zielfall selbst bereits vorhanden (hätten die
Regel nie ausgelöst — jede Regel dieser Datei verlangt ohnehin eine Markennennung in
`require_all_of`-Gruppe 1), „slim"/„pro" sind Teil der `require_all_of`-Gruppe 2 der auslösenden
Regel selbst (wären für diese Regelfamilie immer trivial erfüllt gewesen). Behebt „Playstation 5
PS4 PS5 Slim HDMI Port Nintendo Reparatur USB PRO" (0 Belege für eine echte „repariert"-
Zustandsbeschreibung im gesamten verfügbaren Korpus), als Nebeneffekt zusätzlich ein zweiter,
identisch gelagerter Live-Fall. **Switch/Xbox-Fälle** („Nintendo Switch 32GB Mario Kart 8 Deluxe
Bundle...", „Xbox One S 1TB mit Spiele") nach Nutzerprüfung als korrekt gematchte TRUE_POSITIVE
bestätigt — das FALSE_POSITIVE-Label im historischen Forensik-Snapshot war vermutlich selbst
fehlerhaft. **Keine YAML-Änderung** für diese beiden Fälle. DS-Lite-Fall bleibt unverändert offen
(Risikoabwägung). Ergebnis: 16 von 19 historischen FP dauerhaft gelöst. 0 Regressionen.

**20c — Historical Ground Truth / Current Routing Assessment sauber getrennt (PR #49,
`7159b6c`).** Neues Modul `tools/ruleset_quality/ground_truth_routing_assessment.py`: reine
Report-Schicht über `forensics_false_positives.py`, keine eigene Matching-/Klassifikationslogik.
Jeder Fall trägt jetzt explizit getrennt `historical_ground_truth` (Forensik-Snapshot, nie
verändert), `current_routing_assessment` (`evaluate()`, echter Produktionspfad) und `assessment`
(status/confidence/evidence). Ein historisches FALSE_POSITIVE-Label impliziert nicht mehr
automatisch „aktuell noch ein Fehltreffer", ein aktueller Treffer in derselben Kategorie nicht mehr
automatisch „Label war falsch" — Default bleibt `STILL_ACTIVE`, nur ein dokumentierter, nie
heuristisch erzeugter manueller Override (`_MANUAL_ASSESSMENT_OVERRIDES`) darf
`GROUND_TRUTH_CONFLICT`/`MANUAL_REVIEW` vergeben (die 3 bereits getroffenen Entscheidungen:
Switch/Xbox als Ground-Truth-Konflikt, DS-Lite als Manual-Review). Fix-Queue-Anpassung:
`false_positive_fix_queue.json` impliziert nicht mehr „historischer FP = aktuell zu fixender Fall"
— jeder Eintrag trägt jetzt `queue_category`
(`ACTIVE_ROUTING_FP`/`GROUND_TRUTH_CONFLICT`/`MANUAL_REVIEW`/`ALREADY_FIXED`), nur
`ACTIVE_ROUTING_FP` bekommt eine P0–P3-Priorität. 44 neue/erweiterte Tests, decken alle 6 im
Auftrag geforderten Fälle ab (FIXED/STILL_ACTIVE/CATEGORY_CHANGED/MANUAL_REVIEW/
GROUND_TRUTH_CONFLICT/Ground-Truth-Datei bleibt unverändert). Keine `app/rules/*.yaml`- oder
`docs/DASHBOARD_MATCH_FORENSICS.json`-Änderung, `rule_analyzer.py`: 0 Findings (355 Regeln, 19
Kategorien, unverändert).

**20d — Fix-Queue strikt aus `assessment.status` abgeleitet (PR #50, `8988854`).** Behobener Bug:
`queue_category` folgte bisher einer Präzedenz-Heuristik über `still_active_count`, wodurch
`CATEGORY_CHANGED` fälschlich mit `STILL_ACTIVE` zu `ACTIVE_ROUTING_FP` zusammengelegt wurde.
Jetzt ausschließlich 1:1-Mapping aus `assessment.status`
(`_ASSESSMENT_TO_QUEUE_CATEGORY`), eigene `queue_category=CATEGORY_CHANGED`.
`build_fix_queue()` buckettet zusätzlich nach `assessment_status`, wodurch ein Bucket strukturell
nie mehr mehrere Queue-Kategorien mischen kann — die vorherige Präzedenzfunktion
`_bucket_queue_category()` entfällt ersatzlos. Neu: `case_listing_ids` (vollständige Case-ID-Liste
statt nur 3 representative Listings) + `validate_queue_consistency()` — gleicht Assessment-Cases
und Fix-Queue-Einträge über stabile `listing_id`s ab, CLI bricht mit Exitcode 1 ab, wenn
`consistency_ok=false`. Verifiziert gegen die 4 im Auftrag genannten Referenzfälle (alle
`consistent=true`): Nintendo-Switch-Bundle/Xbox-Bundle bleiben `GROUND_TRUTH_CONFLICT`,
Nintendo-DS-Lite bleibt `MANUAL_REVIEW`. Der PS4/PS5-HDMI-Fall zeigt
`assessment.status=FIXED`/`queue_category=ALREADY_FIXED` — kein Bug: bereits in Batch 20b real per
YAML gefixt. 19 neue Tests. Keine `app/rules/*.yaml`- oder
`docs/DASHBOARD_MATCH_FORENSICS.json`-Änderung, `rule_analyzer.py`: 0 Findings.

**20e — Forensische Klassifikation der 35 UNCLEAR-Fälle (PR #51, `33b6091`, aktueller HEAD).**
Neues Read-only-Modul `unclear_routing_assessment.py` klassifiziert die 35 historischen
UNCLEAR-Fälle aus `docs/DASHBOARD_MATCH_FORENSICS.json` anhand des vollen Titeltexts
(`LIKELY_TRUE_POSITIVE`/`LIKELY_FALSE_POSITIVE`/`GROUND_TRUTH_CONFLICT`/`MANUAL_REVIEW` +
Confidence), da das automatisierte `require_all_of`-Kriterium bei jedem der 35 Fälle nur über ein
generisches Sekundärsignal (ovp/set/bundle) erfüllt wurde und daher Spieltitel nicht zuverlässig
von echten Konsolenverkäufen unterscheiden konnte. **Ergebnis: 11× LIKELY_TRUE_POSITIVE, 23×
LIKELY_FALSE_POSITIVE, 0× GROUND_TRUTH_CONFLICT, 1× MANUAL_REVIEW** (Nintendo DS Lite —
lexikalisch identisch zum bereits bestätigten FALSE_POSITIVE-Fall aus Batch 20a/c). Keine
YAML-Änderung, keine Änderung an `docs/DASHBOARD_MATCH_FORENSICS.json`. **Rein diagnostisch — die
23 LIKELY_FALSE_POSITIVE-Fälle sind noch nicht in YAML-Fixes umgesetzt, siehe STATUS.md P0.**

**Stand nach Batch 20 (verifiziert):** `false_positive_fix_queue.json` — 13 Buckets: 10
`ALREADY_FIXED`, 2 `GROUND_TRUTH_CONFLICT` (Switch, Xbox), 1 `MANUAL_REVIEW` (DS-Lite), **0
`ACTIVE_ROUTING_FP`** — alle ursprünglich 19 historischen FP sind entweder gelöst oder als
bewusste Nicht-Fixes dokumentiert, keine offene P0-Regelarbeit aus Batch 19a mehr. Ruleset:
355 Regeln, 19 Kategorien, 0 Findings, Signatur `f6216b45c6440ab5` → **`f8e07b8b8d97d61a`** (2
YAML-Dateien geändert: `iphone.yaml`, `konsolen_bundles.yaml`). **Volle Testsuite ausgeführt und
grün: `pytest app/tests/` → 1470 passed, 0 failed** (66,9s) — erste Vollverifikation seit Batch 17
(1372/1372), deckt damit auch die seit Batch 18 ausstehende Vollsuite-Pflicht (STATUS.md P0) ab.

### 21. Root-Cause-Clustering der 23 `LIKELY_FALSE_POSITIVE`-Kandidaten + gezielter Fix (PR #52, `2a3d514`)

Direkter Folgeschritt zu Batch 20e. Vor jeder YAML-Änderung: neues Analyse-Artefakt
`unclear_fp_root_cause_analysis.{json,md}` clustert die 23 in Batch 20e als
`LIKELY_FALSE_POSITIVE` klassifizierten UNCLEAR-Fälle in 7 technische Cluster (C1–C7) und prüft
jeden Cluster gegen die 11 `LIKELY_TRUE_POSITIVE`-Gegenbeispiele, um versehentliche Kollisionen
auszuschließen. Sicherheitsverteilung: C1–C4 (19 Kandidaten) waren bereits durch frühere Batches
gelöst, keine Aktion nötig; C5 („Split Pad Pro") und C7 („Joy-Con Set") als `PROBABLY_SAFE`
eingestuft und gefixt; C6 (RDR2/PS4-Steelbook-Bundle) als `HIGH_RISK` eingestuft und bewusst NICHT
geändert — „bundle" ist im `require_all_of` gleichzeitig das auslösende Signal UND das
Verstärkungssignal des ovp-Kontext-Guards, 3 bestätigte TRUE_POSITIVE-Fälle nutzen „bundle" selbst
als Signal, kein sicherer Keyword-Fix identifiziert. Fix in `app/rules/konsolen_bundles.yaml`:
`"split pad pro"` als `exclude_category_unless_preceded_by`-Eintrag (C5), `"joy-con set"` als bare
`exclude_category`-Eintrag (C7). Geteilte generische Marker („pro"/„oled") bewusst nicht
angefasst. 8 neue Tests. Vollkorpus-Regression (`docs/DASHBOARD_MATCH_FORENSICS.json`, 2306
Einträge, vorher/nachher-Diff via `matcher.evaluate()`): exakt 2 Routing-Änderungen, beide
beabsichtigt. 0 Regressionen bei allen 2252 TRUE_POSITIVE- und 19 FALSE_POSITIVE-Fällen sowie den
übrigen 33 UNCLEAR-Fällen; `konsolen_bundles`-TRUE_POSITIVE-Treffer vorher/nachher: 191/191
unverändert. Ruleset: 355 Regeln, 19 Kategorien, 0 Findings, Signatur `f8e07b8b8d97d61a` →
`ff535311dcd59009`. Volle Testsuite: 1478 passed, 0 failed (105,74s).

**Stand nach Batch 21 (verifiziert):** von den ursprünglich 19 historischen FALSE_POSITIVE-Fällen
weiterhin 16 gelöst, 3 bewusst offen (unverändert zu Batch 20). Von den 23 UNCLEAR-
`LIKELY_FALSE_POSITIVE`-Kandidaten aus Batch 20e: 22/23 gelöst (20 bereits vorher, 2 neu), 1/23
bewusst offen (RDR2/PS4-Steelbook-Bundle, Manual-Review).

### 22. Resale-/Profit-Audit auf echten Produktivdaten + 3 live bestätigte Profit-verzerrende Matching-Fehler behoben (PR #53, `2ce1e04`)

Zweistufige Aufgabe. **Phase 1 (reiner Analyse-Audit, keine Code-/YAML-Änderung):** Prüfung des
Resale-/Profit-Systems anhand echter Produktivdaten (`data/found.json`, `data/price_history.jsonl`,
`data/time_to_sell.jsonl`). Bestätigte u. a., dass `estimated_resale_price` weiterhin denselben
Purchase-Perspective-Bias hat wie dokumentiert (kein echtes Sale-Price-Signal existiert im
gesamten Projekt) und dass `time_to_sell.jsonl` (Presence-Tracking-basiert) keine bestätigten
Verkäufe misst. Als Nebenbefund: 3 live bestätigte, `margin_eur`/`margin_pct` verzerrende
Matching-Fehler gefunden und als `AUDIT-FUND` markiert, bewusst nicht gefixt. **Phase 2 (gezielter
Root-Cause-Audit + Fix):** ausschließlich für genau diese 3 Fälle, kein genereller Ruleset-Review.

Drei technisch unabhängige Root Causes:

- **Cluster A (`konsolen_bundles`):** „pro" ist gleichzeitig `require_all_of`-Signal („PS4 Pro")
  und Verstärkungsmarker des „spiele"-Kontext-Guards — kollidiert mit der deutschen Präposition
  „pro" („je Stück"). Fix: `"pro stück"` als bare `exclude_category`-Eintrag. Bewusst akzeptierter
  Ground-Truth-Konflikt: 2 als TRUE_POSITIVE gelabelte „Ps4 Spiele...pro Stück"-Fälle matchen
  dadurch ebenfalls nicht mehr — inhaltlich eindeutig Spiele-Einzelverkäufe, vermutlich Label-Fehler
  analog zum Switch/Xbox-Artefakt aus Batch 20b.
- **Cluster B (`vintage_elektronik`):** `require_all_of` unterscheidet nicht zwischen einem echten
  Verstärker und einem Zeitschriften-/Heft-Konvolut, das nur ÜBER Verstärker berichtet („Image hifi
  Hefte Röhrenverstärker"). Fix: `"hefte"` als bare `exclude_category`-Eintrag, identisches Muster
  wie die bereits vorhandenen Sammler-/Dokumentations-Excludes „foto"/„funktionsbeschreibung".
- **Cluster C (`monitor_curved`):** „Teildefekt" (Kompositum) wird vom globalen „defekt"-Exclude
  wegen fehlender Wortgrenze (`matcher.py::_contains_term()`) nicht erfasst. Fix: lokaler
  `exclude_category`-Eintrag NUR in `monitor_curved.yaml`, bewusst NICHT global in `_global.yaml` —
  „teildefekt" gilt in `iphone`/`retro_konsolen` als bestätigter TRUE_POSITIVE-Marker.

8 neue Tests (`test_profit_matching_root_cause_audit_fix.py`), je ein Fixtest + ein
Sicherheitstest pro Cluster (echte Konsolen/Verstärker/Monitore matchen weiterhin) plus ein
Cross-Kategorie-Regressionstest („teildefekt" bleibt in `iphone`/`retro_konsolen`
TRUE_POSITIVE). Vollkorpus-Regression: 0 unerwartete Änderungen. Ruleset unverändert bei 355
Regeln (3 additive Excludes in bestehenden Kategorien), 0 Findings.

### 23. Notebook-Recall-Optimierung — 99-TRUE_POSITIVE-Recall-Forensics-Audit + gezielte Fixes (PR #54, `9fc967c`/`8507c44`)

Mehrstufige Aufgabe, beginnend mit einer reinen Analysephase. **99-TRUE_POSITIVE-Recall-Forensics
(Analyse, keine Codeänderung):** systematische Untersuchung aller unmatched TRUE_POSITIVE-Fälle aus
`docs/DASHBOARD_MATCH_FORENSICS.json` — 101 Fälle (nicht 99, siehe unten), einzeln klassifiziert als
`GROUND_TRUTH_CONFIRMED`/`GROUND_TRUTH_UNCLEAR`/`GROUND_TRUTH_SUSPECT` statt die Ground-Truth-Labels
ungeprüft zu übernehmen. Ergebnis: 43 CONFIRMED (davon 42 Notebook-Resale, 1 `controller`/„akku"),
31 UNCLEAR (v. a. `office_pc`-Aufrüstkit-Definitionsfrage), 27 SUSPECT (mutmaßliche
Ground-Truth-Label-Fehler: Zubehör/Ersatzteile, Spieltitel, bereits bekannte historische Fixes).
Root Cause der 42 Notebook-Gaps: `notebook_resell.yaml` deckt nur eine schmale
Marken-/Modell-/GPU-Whitelist ab, während `office_pc`/`gaming_pc` Laptops bereits korrekt
ausschließen (Nachwirkung eines früheren, korrekten Precision-Fixes).

**Fix-Phasen (schrittweise mit Zwischenfreigaben), alle ausschließlich in
`app/rules/notebook_resell.yaml`:**

- **Cluster B (11 Fälle):** ThinkPad-Preisgrenze „Guter Preis" 240€ → 330€ — datenbasiert
  kalibriert auf den höchsten real bestätigten TRUE_POSITIVE-Preis (329€, aufgerundet), keine
  price_history.jsonl-Datenpunkte vorhanden. Blast Radius im vollständigen 2306-Eintrag-Korpus:
  exakt die 11 bekannten Fälle, 0 zusätzliche Kandidaten.
- **Cluster A1 (6 Fälle):** „T490s"/„T14s" ergänzt — kein neues Modell, sondern derselbe
  Wortgrenzen-/Kompositum-Bug in `_contains_term()` wie bei „teildefekt"/„defekt" (Batch 22) und
  „ps4slim"/„ps4". Bewusst lokal gelöst, kein globaler Matcher-Eingriff (Blast Radius von 625
  projektweiten Begriffen wäre unverhältnismäßig).
- **Cluster A2 (2 von 4 Fällen):** „ThinkPad E15" ergänzt. „L480"/„L590" bewusst NICHT gefixt — die
  Titel enthalten „ThinkPad" nicht wörtlich, scheitern am Marken-Gate; Lockerung wäre eine
  Architekturänderung außerhalb des Scopes.
- **Cluster A8 (2 von 4 Fällen):** neue Regel „Gaming Laptop (GTX 1650)", Preisbasis nur 3
  GT-Fälle (285–349€), `max_price: 350`. „GTX 1650 Ti"/„RTX 2060"/„RTX 4070" bewusst NICHT
  ergänzt — je nur 1 Datenpunkt, keine belastbare Preisverteilung
  (`PROPOSED_PRICE_CALIBRATION`).
- **A3–A7-Gerätewort-Fälle (5 von 7 Fällen mit explizitem „laptop"/„notebook"-Wort im Titel):**
  neue Marken-Regeln „Dell Latitude", „ACEMAGIC Laptop", „Lenovo V330" (Preisgrenzen wiederverwendet,
  keine neuen Zahlen erfunden). „HP" (generic) bewusst NICHT implementiert — Cross-Category-Risiko
  über HP OMEN/Pavilion Gaming (bereits eigene Regeln)/HP Zbook (= A10, außerhalb des Scopes)/
  unbekannte Sublinien (EliteBook/ProBook/Envy/Spectre) nicht sicher kontrollierbar (`BLOCKED`).
  7 weitere Fälle ganz ohne Gerätewort im Titel bewusst nicht bearbeitet (harte Scope-Grenze).

Insgesamt 21 von 43 bestätigten Recall-Gaps geschlossen. Jede Teiländerung einzeln
blast-radius-geprüft gegen den vollständigen 2306-Eintrag-Ground-Truth-Korpus, kumuliert 0
unerwartete Routing-Änderungen. 23 neue Tests über 3 Testdateien
(`test_notebook_resell_cluster_b_price_calibration_fix.py`,
`test_notebook_resell_cluster_a1_a2_a8_fix.py`, `test_notebook_resell_a3_a7_geraetewort_fix.py`).
1 bestehender Test notwendig aktualisiert (`test_office_pc_notebook_cross_category_fix.py` — testete
explizit die durch die neue Datenbasis überholte alte 240€-Preisdeckel-Entscheidung, Kernaussage
unverändert). Nach dem committen ausgelöste volle Testsuite (1509 Tests) deckte einen weiteren,
vorher nicht erfassten Testfehler auf: `test_matcher_psu_requirement.py` verwendete „Dell Latitude
Laptop..." als generischen Test-Titel für einen PSU-/Netzteil-Test und erwartete „matched is
False" — ein Nebenprodukt der damals fehlenden Latitude-Markenabdeckung, nicht der eigentliche
Testzweck (Nicht-Matchen als „netzteil"); korrigiert, Kernaussage bleibt erhalten und wird jetzt
explizit geprüft.

Bewusst zurückgestellt und dokumentiert (nicht Teil dieses Batches): „L480"/„L590"
(Architekturfrage), GTX 1650 Ti/RTX 2060/RTX 4070 (fehlende Preisbasis), HP generic
(Cross-Category-Risiko), 7 Fälle ohne Gerätewort, A10 (HP Zbook/Quadro-P600-Workstation-Grenzfall).

**Stand nach Batch 23 (verifiziert):** 360 Regeln, 19 Kategorien, 0 Findings, Signatur
`ff535311dcd59009` → `87626edfc333ff71` (1 YAML-Datei mehrfach erweitert). **Volle Testsuite
ausgeführt und grün: `pytest app/tests/` → 1509 passed, 0 failed** (111,3s), vorheriger
dokumentierter Vollstand: 1478/1478 (Batch 21).

### 24. `matcher.py` zu Package modularisiert (`8016eea`, direkt auf `main`)

`matcher.py` (1317 Zeilen, dokumentiertes God-File) in 6 Schritten auf `app/matcher/` verteilt:
`core.py` (`MatchResult`, `evaluate()`), `text_matching.py` (Term-/Regex-Primitive), `vram.py`
(`_vram_gb`), `hardware_requirements.py` (`PC_AUSSCHLIESSEN`, Hardware-Anforderungsprüfung),
`score_bridge.py` (`_build_score_inputs`), `rules_io.py` (`load_rules`,
`compute_ruleset_signature`). `__init__.py` re-exportiert die komplette bisherige Oberfläche
(auch die intern als API genutzten privaten Funktionen) — kein Aufrufer (`app.py`,
`category_validation.py`, `rule_analyzer.py`, `rule_coverage.py`, `rules_loader.py`,
`recompute_top_deal.py`, `tools/ruleset_quality/common.py`, Testsuite) musste angepasst werden.
Reine Strukturänderung, keine Logikänderung — Ruleset-Signatur vor/nach identisch
(`87626edfc333ff71`). Getestet: `pytest -k matcher` (301/301), abhängige Module (86/86). Die alte
`app/matcher.py`-Datei blieb zunächst als Altlast im Repository liegen (nicht Teil dieses
Commits) und wurde erst in Batch 25 final entfernt. Direkt auf `main` committet und gepusht (kein
PR), Commit `8016eea`.

### 25. Notebook-Recall-Fortsetzung: L480/L590, IdeaPad Gaming 3, Latitude-Modellcodes (PR #55, `471795a`/`fe05a72`)

Direkte Fortsetzung von Batch 23 — drei der dort bewusst zurückgestellten bzw. in separaten
Analysephasen identifizierten Recall-Gaps additiv geschlossen, ausschließlich
`app/rules/notebook_resell.yaml`. Jede Änderung einzeln blast-radius-geprüft gegen den
vollständigen 2306-Eintrag-Ground-Truth-Korpus sowie adversarial getestet (temporäre,
nicht-persistierte Synthetik-Fälle):

- **ThinkPad L480/L590 (2 Fälle, Marken-Gate-Erweiterung, Variante A):** in Batch 23 identifiziert,
  aber zurückgestellt — „Lenovo Laptop L480..."/„Notebook Lenovo L590..." erfüllten die
  Modellcode- und Größen-Gruppe bereits vollständig, scheiterten aber an der Marken-Gate-Gruppe
  (verlangte zwingend „thinkpad"/„think pad", beide Titel enthalten das Wort nicht). Fix: „l480"/
  „l590" zusätzlich als Marken-Alternative in Gruppe 1 beider ThinkPad-Preisstufen ergänzt.
  Gegenüber einer separaten „Lenovo"+Modellcode-Regel (Variante B) bevorzugt: bleibt konsistent
  mit der bestehenden Ein-Regel-Struktur und deckt zusätzlich Titel wie „ThinkPad L480 ..." (ohne
  das Wort „Lenovo") ab. Blast Radius: je 1 Treffer gesamt im Korpus (die beiden Zielfälle selbst),
  0 Zubehör-/Mainboard-/Akku-/Display-/Tastatur-/Docking-Kollisionen. Adversarial-Test (16
  synthetische Fälle): 0 Fehlklassifikationen.
- **Lenovo IdeaPad Gaming 3 (1 Fall, Gerätewort-Gate-Erweiterung, „C1 Minimal Recall Fix"):**
  „Lenovo IdeaPad Gaming 3...GTX 1650..." (339€, TRUE_POSITIVE) erfüllte die GPU-Gruppe der Regel
  „Gaming Laptop (GTX 1650)" bereits vollständig, scheiterte aber am Gerätewort-Gate — der Titel
  enthält „gaming" (bewusst nicht als Ersatz akzeptiert, analog zur RTX3060-Regel-Entscheidung),
  aber nicht „laptop"/„notebook". Fix: eng gefasstes Zwei-Wort-Signal „ideapad gaming" als
  zusätzliche OR-Alternative zur Gerätewort-Gruppe ergänzt — bewusst als Erweiterung dieser Regel
  statt einer separaten, generischen „ideapad"-Marken-Regel (hätte das Risiko geborgen, GPU-Fälle
  mit falscher, nicht GPU-kalibrierter Preisbasis zu erfassen). Zwei normale, nicht-GPU IdeaPad-5-
  Fälle bleiben bewusst weiterhin unmatched (keine sichere Variante identifiziert, Adversarial-Test
  zeigte 3/12 Fehlklassifikationen für das einzig verfügbare Modellsignal „bare 5"). Blast Radius:
  1 Treffer gesamt im Korpus (der Zielfall selbst), 0 Kollisionen. Adversarial-Test (12
  synthetische Fälle inkl. Desktop-Gaming-PC mit identischer GPU): 0 Fehlklassifikationen.
- **Dell Latitude 5500/5501/7400 (3 Fälle, Modellcode-Liste als Gerätewort-Alternative, „Variante
  B"):** siehe `tools/ruleset_quality/generated/reports/latitude_recall_gap_simulation.{json,md}`
  für die vollständige Simulation. Fix: Gerätewort-Gruppe um die 5 im Korpus tatsächlich
  beobachteten Latitude-Modellcodes („5300","5401","5500","5501","7400") als zusätzliche
  OR-Alternativen zu „laptop"/„notebook" ergänzt. Bewusst KEINE globale 5xxx/7xxx- oder generische
  Zahlenerkennung (Variante A) und KEINE „Zahl direkt nach Latitude"-Positionslogik (Variante C):
  beide bestanden im Simulationsbericht den synthetischen Adversarial-Test nicht (Zubehör-/
  Ladegerät-Bundles mit unrelated 4-stelligen Zahlen matchten fälschlich). Nur die feste,
  geschlossene Codeliste (Variante B) bestand sowohl den vollständigen Korpus-Test (3/3 Gaps
  behoben, 0 Regressionen, 0 neue FP, 0 UNCLEAR-Änderungen) als auch beide Adversarial-Fälle.
  Liste bewusst nicht ohne erneuten Korpus-Beleg erweiterbar.

Zusätzlich: veraltete `app/matcher.py` (aus Batch 24 als Altlast liegen geblieben, 1317 Zeilen,
vollständig durch das `matcher/`-Package abgelöst) final entfernt. Ruleset-Quality-Reports
(`ground_truth_routing_assessment.{json,md}`, `unclear_routing_assessment.{json,md}`) und
-Baseline (`baseline_20260815T193318Z_f8e07b8b8d97d61a.json`) auf aktuellen Stand aktualisiert.
`.gitignore` um `data/*.log` und `data/seen.json` ergänzt (bisher fehlende Ausschlussregel für
Laufzeit-Log bzw. 16MB-Presence-Tracking-State — beide waren zuvor weder getrackt noch
ausgeschlossen). Drei Ad-hoc-Debug-Skripte (`script/debug_*.py`) aus vorherigen Sessions bewusst
NICHT committet (Laufzeit-/Debug-Artefakte, kein Quellcode).

3 neue Testdateien (`test_notebook_resell_ideapad_gaming3_c1_fix.py`,
`test_notebook_resell_l480_l590_marken_gate_fix.py`, `test_notebook_resell_latitude_variant_b_fix.py`),
2 bestehende Testdateien erweitert (`test_notebook_resell_a3_a7_geraetewort_fix.py`,
`test_notebook_resell_cluster_a1_a2_a8_fix.py`) um die neuen Fälle. Zielgerichtete Tests:
`pytest app/tests/test_notebook_resell_*.py -v` → 40 passed; `pytest app/tests/ -k
notebook_resell -q` → 68 passed, 1464 deselected. Volle Suite in diesem Batch nicht erneut
ausgeführt (keine explizite Nutzer-Freigabe für diesen Schritt, zuletzt vollständig verifiziert in
Batch 23: 1509/1509).

**Workflow:** Branch `claude/notebook-recall-l480-l590-ideapad-gaming-latitude-b` von `main`,
PR #55 erstellt und vom Nutzer gemerged (Merge-Commit `fe05a72`) — konsistent mit dem in diesem
Repository durchgängig etablierten Feature-Branch-→-PR-→-Merge-Workflow.

**Stand nach Batch 25 (verifiziert):** 360 Regeln, 19 Kategorien, 0 Findings, Signatur
`87626edfc333ff71` → `0a9c9f4bb3590872` (`notebook_resell.yaml` dreifach erweitert).

**Im Anschluss (keine Codeänderung):** vier isolierte Recall-Cluster (Fujitsu Lifebook, HP
generic, HP ZBook, Alienware) einzeln tiefenanalysiert — Root-Cause, Vollkorpus-Blast-Radius,
In-Memory-Simulation mehrerer Fixvarianten, Adversarial-Tests, jeweils mit Hard Stop nach dem
Bericht. Fujitsu Lifebook: `BLOCKED` (einziger Fixkandidat kollidiert im Adversarial-Test mit
einem Zubehörtitel gleichen Modellcodes). Alienware: `BLOCKED` (die gemeinsame Größen-Gruppe
scheitert strukturell an Kompositum-Schreibweisen wie „16GbDDR4" — unabhängig von Marken-/Modell-/
GPU-Fragen technisch unlösbar mit bestehenden Primitiven). HP generic: erste Analyse `BLOCKED`,
vertiefte Folgeanalyse (regel-eigene Zubehör-Excludes) verbessert auf `NEEDS_DESIGN_DECISION` —
löst den 270€-Zielfall ohne reale Korpus-Kollateralschäden (100€-Fall bleibt an einem separaten
Format-Problem blockiert), trägt aber einen architektonisch nachgewiesenen Trade-off: rule-level
`exclude:` (reine, kontextfreie Presence-Prüfung) kann „Akku 85%" (Zustandsangabe) nicht von
„Akku" (Zubehörprodukt) unterscheiden. Die bestehenden kontextbewussten Primitiven
(`exclude_category_unless_also_contains`/`_preceded_by`) sind strukturell ausschließlich
kategorienweit (Zuweisung in `rules_io.py` vor der Regel-Schleife, nicht rule-scoped nutzbar) und
selbst dort nur wortlisten-, nicht regex-basiert — „%" wird von `_contains_term()` nach einer
Ziffer wegen der Wortgrenzen-Lookbehind nicht erkannt. Eine vollständige technische Lösung wäre
eine kleine Erweiterung von `matcher/core.py` um ein Regex-Kontext-Primitiv — betrifft ein
geschütztes Kernsystem, eigene Freigabe nötig, nicht Teil dieser Analyse. HP ZBook: separat
behandelt (TRUE_POSITIVE im GT-JSON, aber Definitionsfrage, ob eine Workstation-Sublinie unter
`notebook_resell` fallen soll), `NEEDS_DEFINITION`. Keine Datei geändert, kein Commit — alle vier
Analysen ausschließlich im Chat-Verlauf dokumentiert.
