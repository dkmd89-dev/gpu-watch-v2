# STATUS — Aktueller technischer Projektstatus

> **Stand:** 2026-08-15  
> **Repository:** `dkmd89-dev/gpu-watch-v2`  
> **Branch:** `main`  
> **Letzter Code-Commit auf `main` (vor dieser Doku-Aktualisierung):** `1ac95ef` (davor `c3b9443`
> = Merge PR #34, `5fea3ec` = Merge PR #33)  
> **Technische Referenz:** `TECHNISCHER_PROJEKTSTATUS.md`

## Gesamtstatus

**Stabil / aktiv weiterentwickelbar.** Seit dem letzten dokumentierten Stand (`2745a95`, PR #29 +
Folge-Sessions) wurde die 251-Listing-Stichprobe vollständig gelabelt, 3 gezielte Exclude-Fixes
umgesetzt (PR #31), der Umlaut-Fingerprint-Bug behoben (PR #32), die freigegebene
`lego_bundle`-Migration/-Bereinigung ausgeführt, eine kontrollierte Preishistorie-Revalidierung v3
durchgeführt (PR #32), **STATUS.md Punkt 14 (Zubehör/Ersatzteil-vs-Gerät) gelöst** (PR #33),
**Punkt 5 (`controller`/`ladekabel`) gelöst** (PR #34) und jetzt **Punkt 4 (`RX 7600 XT`/`RX 7600`)
gelöst** — inklusive eines wichtigen Zusatzfundes: derselbe VRAM-Filter-Bug betraf strukturell 4
weitere GPU-Modelle (`rtx_3060_ti`, `rtx_3070`, `rtx_4060`, `rtx_2080_ti`), ebenfalls mitgefixt.
**Ruleset-Signatur hat sich erneut geändert** (`0d63c38b5dbf261c` → `133dcd1a9f614e7e`).

## Verifizierter Stand

```text
main (vor dieser Doku-Aktualisierung): c3b9443 (Merge PR #34)

Rule Analyzer:
355 Regeln
19 Kategorien
0 Findings
Ruleset-Signatur: 133dcd1a9f614e7e (GEÄNDERT seit PR #34 — Punkt-4-Fix ergänzt
  min_vram_gb: 0 bei 5 GPU-Modellen/10 Regeln in gpu.yaml)

data/found.json: 2500 Einträge
data/price_history.jsonl: 14.899 Datenpunkte (unverändert seit der lego_bundle-Bereinigung)
```

Teststand: 10 neue Tests (`test_gpu_rx7600_vram_fix.py`, `test_gpu_low_vram_models_fix.py`) + 54
`gpu`-bezogene Tests lokal grün verifiziert. Volle Suite zuletzt bei 1315/1315 (PR #33, vom Nutzer
lokal verifiziert) — für diesen Einzelkategorie-Fix nicht erneut automatisch ausgeführt
(CLAUDE.md-Regel: nur nach expliziter Freigabe).

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

## Nächste Prioritäten

### P0 — offene Punkte

- Keine dringenden P0-Punkte mehr offen (alle in Batch 1–10 dokumentierten Punkte abgeschlossen,
  Nr. 1–5 der Datenqualitätsliste sind jetzt vollständig erledigt). Nächste Schritte laut
  Datenqualität/offene Punkte: Nr. 6 (Resale-Confidence) oder P1/P2 unten. Ein möglicher, bisher
  nicht gemessener Verdacht: derselbe min_vram_gb-Musterbug (Batch 10) könnte theoretisch auch
  außerhalb von `gpu` relevant sein, wo Kategorien VRAM-abhängige Modelle mit eigenem
  `min_vram_gb` nutzen — bisher nicht geprüft, keine konkrete Evidenz, kein aktiver Punkt.

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
