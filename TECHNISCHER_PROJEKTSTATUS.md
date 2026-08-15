# Technischer Projektstatus — gpu-watch-v2

> **Single Source of Truth für den technischen Ist-Zustand (Architektur, Module, Invarianten).**
> Für Priorität, offene Punkte und die kompakte Batch-Tabelle: `STATUS.md`.
> Für die vollständige, wortgetreue Historie jedes Batches: `docs/STATUS_HISTORY.md`.
>
> **Stand:** 2026-08-16
> **Repository:** `dkmd89-dev/gpu-watch-v2`  ·  **Branch:** `main`
> **HEAD:** `ee26893` (Merge PR #51, Batch 20)
> **Ruleset-Signatur:** `f8e07b8b8d97d61a`  ·  355 Regeln, 19 Kategorien, 0 Findings
> **Volle Testsuite (zuletzt verifiziert):** `pytest app/tests/` → **1470 passed, 0 failed** (66,9s)

**Restrukturierung dieser Version:** Frühere Fassungen dieser Datei enthielten eine
vollständige Batch-für-Batch-Erzählung (Abschnitte 3.1–3.24). Das duplizierte
`docs/STATUS_HISTORY.md`, dessen ausdrücklicher Zweck genau das ist (siehe
STATUS.md Abschnitt 9, „Dokumentationsregel"). Diese Fassung ist stattdessen als
**Architektur-/Subsystem-Referenz** aufgebaut: Was gibt es, wie hängt es zusammen,
welche Invarianten gelten — nicht mehr, wie es historisch entstanden ist. Alle
Batch-Details, Root-Cause-Analysen und Blast-Radius-Nachweise bleiben vollständig in
`docs/STATUS_HISTORY.md` erhalten und werden hier nicht erneut ausgeführt.

---

## 1. Kurzfazit

`gpu-watch-v2` ist ein modularer, YAML-gesteuerter **Hardware Deal Finder** für
Second-Hand-Angebote (aktuell Kleinanzeigen, Quoka; eBay/weitere Quellen als
Erweiterungsebene vorgesehen). Das System kombiniert Scraper, kategoriebasiertes
Matching, Hardware-/Zustands-/Lieferumfang-Detektoren, Deal-Scoring,
Marktpreis-/Resale-Statistik, Profit-/Flip-Bewertung, Duplicate Detection, Presence
Tracking, ein Dashboard mit KPIs und ntfy-Benachrichtigungen. Produktiv im Einsatz
via Docker Compose.

Der aktuelle technische Schwerpunkt liegt auf **Precision und Datenqualität** des
Regelwerks: ein dediziertes, read-only **Ruleset-Qualitätssystem**
(`tools/ruleset_quality/`, siehe Abschnitt 4.8) liefert seit 2026-08-14
reproduzierbare Regression-Benchmarks statt punktueller Audits. Darauf aufbauend
wurde ein Category-False-Positive-Forensics-Tool samt priorisierter Fix-Queue
gebaut und die Fix-Queue vollständig abgearbeitet (Batch 19a/20a–20e, siehe
Abschnitt 5) — offen ist aktuell nur noch die YAML-Umsetzung für 23 neu
klassifizierte `LIKELY_FALSE_POSITIVE`-Kandidaten (STATUS.md P0).

---

## 2. Verifizierter Repository-Stand

```text
Branch: main
HEAD:   ee26893 (Merge PR #51)

Ruleset (rule_analyzer.py):
  355 Regeln, 19 Kategorien, 0 Findings
  Signatur: f8e07b8b8d97d61a

Testsuite:
  pytest app/tests/ -q -> 1470 passed, 0 failed (66,9s)
  Erste vollständige Verifikation seit Batch 17 (1372/1372) —
  deckt die seit Batch 18 offene P0-Pflicht „volle Suite nach
  expliziter Freigabe" ab (CLAUDE.md Abschnitt 3, Punkt 4.4).

data/found.json: laufender Produktivbetrieb (Scanner aktiv) — kein
  stabiler, hier ausgewiesener Zählwert (siehe Abschnitt 4.1).
```

Detaillierte Commit-für-Commit-Aufschlüsselung der letzten Batches (PR-Nummern,
Testzahlen je Zwischenstand): `STATUS.md` Abschnitt 3, `docs/STATUS_HISTORY.md`.

---

## 3. Systemarchitektur

### 3.1 Datenfluss

```text
Scraper / Quellen (Kleinanzeigen, Quoka)
      │
      ▼
Dedup / Presence / Persistence
      │
      ▼
YAML Rules Loader
      │
      ▼
Matcher + Hardware-/Condition-/Bundle-Detektoren
      │
      ├──> Category Validation / Data Quality
      │
      ▼
Deal Score
      │
      ├──> Market Price
      ├──> Resale Price
      ├──> Profit / Margin / Flip
      ├──> Deal Intelligence
      │
      ├──> Top-Deal / KPI-Logik
      │
      ├──> Notifications (ntfy)
      │
      ▼
Dashboard / API / Statistics
```

Zusätzlich, **außerhalb** dieser Produktionskette (read-only, kein Import durch
`app.py`/`matcher.py`): `tools/ruleset_quality/` — Regression-Benchmark- und
Qualitätssystem (Abschnitt 4.8).

### 3.2 Verzeichnisstruktur

```text
app/
├── app.py                    # Flask-Einstiegspunkt, Scan-Loop, Persistenz-Orchestrierung
│                              # (bereits reduziert, weiterhin Kandidat für
│                              #  kontrollierte, bedarfsgetriebene Modularisierung)
├── matcher.py                 # Kern-Matching-Logik gegen YAML-Regeln
├── rules_loader.py             # YAML-Regeln laden (Rules-Cache)
├── rule_analyzer.py            # read-only Diagnose: unerreichbare Regeln, Duplikate, Exclude-Konflikte
├── rule_coverage.py            # Coverage-Messung
├── category_validation.py      # Kategorie-Revalidierung
├── data_quality.py             # Datenqualitäts-Diagnosen
├── deal_intelligence.py        # Deal-Intelligence-Layer
├── price_history.py            # Preishistorie-I/O (PricePoint, Fingerprint)
├── scan/
│   └── scheduler.py            # Scan-Scheduling
├── scrapers/                   # Kleinanzeigen-/Quoka-Scraper (Plugin-Registry)
├── rules/                      # ein YAML pro Kategorie, `_global.yaml` = globale Excludes/Thresholds
│   └── mappings/                # unterstützende Mapping-Tabellen
├── scoring/                    # Deal-Score, Profit-/Flip-Berechnung (`scoring/profit.py`)
├── categories/detectors/       # Kategorie-spezifische Ausstattungs-/Zustands-/Lieferumfang-Detektoren
├── api/                        # Flask-Blueprints
│   ├── deals.py                 # /api/found
│   ├── history.py               # /api/history
│   └── status.py                 # /api/status
├── services/
│   └── statistics_service.py   # Marktpreis-/Resale-Statistik
├── persistence/
│   └── json_store.py           # JSON-/Log-I/O-Helfer (seen.json, found.json, price_history.jsonl)
└── tests/                       # pytest-Suite (synthetische Fixtures + echtes Produktiv-Regelwerk)

tools/ruleset_quality/          # read-only Regression-Benchmark-/Qualitätssystem, siehe 4.8
```

### 3.3 Grundprinzipien

- YAML ist Single Source of Truth für Kategorien und viele Matching-/Scoring-Regeln.
- Scraper liefern ausschließlich standardisierte Rohdaten, keine Bewertungslogik.
- Alle Bewertung erfolgt im Matcher/Scoring, nicht im Scraper.
- Neue Kategorien sind ohne Python-Code über `app/rules/*.yaml` möglich; neue
  **Detector-Typen** erfordern weiterhin Python-Code (Architekturentscheidung,
  kein Fehler).
- `market_price` und `estimated_resale_price` bleiben strikt getrennt — niemals
  zusammenführen oder eines aus dem anderen ableiten.
- Dünne Resale-Daten (< 5 Samples pro Resale-Gruppe) erzeugen keine künstlich
  optimistische Flip-Einstufung.
- Notification-Gating ist von Preis-/Resale-Experimenten entkoppelt.
- Diagnose-/Qualitäts-Tooling (`tools/ruleset_quality/`) importiert ausschließlich
  bereits produktive Matching-Funktionen wieder — keine zweite Matching-/Regex-Engine.
- Fixes verwenden bestehende YAML-/Matcher-Primitive (`exclude_category`,
  `exclude_category_unless_also_contains`, `exclude_category_unless_preceded_by`)
  statt eines neuen generischen Matcher-Mechanismus.

---

## 4. Kern-Subsysteme

### 4.1 Scraper / Dedup / Persistence

Scraper (Kleinanzeigen, Quoka; eBay als vorgesehene Erweiterung) liefern
standardisierte Angebotsdaten über eine Plugin-Registry. Neue Scraper benötigen
Mocks in **allen** `run_scan()`-aufrufenden Tests (bekannter Fallstrick, siehe
CLAUDE.md Abschnitt 5). Persistence ist gebatcht (`seen.json`/`found.json` werden
nicht mehr pro Event geschrieben) — Tradeoff: bis zu 5s Risikofenster bei einem
Crash. `data/found.json` wird vom laufenden Produktiv-Scanner kontinuierlich
verändert; jeder hier oder in Reports ausgewiesene Zählwert ist eine Momentaufnahme,
kein stabiler Referenzwert.

### 4.2 YAML-Regelwerk & Matcher

19 aktive Kategorien unter `app/rules/*.yaml`, `_global.yaml` ist keine eigene
Kategorie (globale Excludes/Thresholds). Der Matcher (`matcher.py`) bewertet jeden
Titel gegen `require_all_of`-Gruppen, kontextbewusste Excludes
(`exclude_category`, `exclude_category_unless_also_contains`,
`exclude_category_unless_preceded_by`), First-Match-Wins-Routing bei
Kategorie-Mehrdeutigkeit sowie einen Regex-/Term-Cache und eine
Ruleset-Signatur (`compute_ruleset_signature()`) für Cache-Invalidierung und
Regressionsvergleiche. `rule_analyzer.py` prüft read-only auf unerreichbare
Regeln, Duplikate und Exclude-Konflikte; `rule_coverage.py` misst Coverage gegen
`price_history.jsonl`.

### 4.3 Hardware-/Condition-/Bundle-Detektoren

Modular registrierte, kategoriespezifische Detektoren unter
`app/categories/detectors/` für Ausstattung, Zustand und Lieferumfang. Neue
Detector-Typen erfordern Python-Code (siehe Grundprinzipien, 3.3).

### 4.4 Deal Score

Score-Gewichtung ist YAML-konfigurierbar. `profit`-Gewicht defaultet auf `0.0` —
keine implizite Scoring-Änderung an bestehenden Kategorien, solange eine
Kategorie-YAML kein explizites Non-Zero-Gewicht setzt (bekannter Fallstrick).

### 4.5 Preis, Resale und Profit

```text
market_price
    !=
estimated_resale_price
```

Die Resale-Schätzung verwendet ein separates, gröberes Gruppierungsmodell
(Resale-Price-Grouping). Bei zu dünner Preishistorie (< 5 Samples pro
Resale-Gruppe) wird keine belastbare Resale-Schätzung erzwungen, um strukturell
falsche Flip-Kandidaten zu vermeiden.

Profit-/Flip-Workstream: `estimated_margin_eur`, `estimated_margin_pct`,
Mindestkaufpreis-Schutz gegen absurde Prozentwerte
(`MIN_PURCHASE_PRICE_FOR_MARGIN_PCT`, konfigurierbar über
`fees.min_purchase_price_for_margin_pct` in `rules/_global.yaml`), Dashboard-/
KPI-Anbindung.

**Bekannte Einschränkung:** `estimated_resale_price` hat aktuell einen
Purchase-Perspective-Bias (== `market_price` als Platzhalter). Eine
Sell-Perspective-Anpassung ist ein offener, dokumentierter Punkt — nicht
stillschweigend fixen.

### 4.6 Top-Deal-Logik & Dashboard/API

```text
(Score ≥ 80 UND Discount ≥ 25%)  ODER  (Score ≥ 90 UND Discount ≥ 20%)
```

Vier KPI-Kategorien: Top Deals, Sehr gute Deals, Flip-Kandidaten, Neue Top Deals.
Filterung clientseitig anhand vom Backend gelieferter Schwellenwerte; Marktpreis,
Rabatt, Score und auslösende Regel werden auf den Deal-Karten transparent
dargestellt. API-Blueprints: `/api/found` (`api/deals.py`), `/api/history`
(`api/history.py`), `/api/status` (`api/status.py`).

### 4.7 Notifications

ntfy-Benachrichtigung ausschließlich bei `min_rating` UND `max_price`-Kriterium
gleichzeitig erfüllt (kategorie-/global-konfigurierbar). `notify_max_price` ist
ausschließlich category-level, kein Per-Rule-Feld (bekannter Fallstrick).
Notification-Gating bleibt von Preis-/Resale-Experimenten entkoppelt (geschütztes
Kernsystem, siehe CLAUDE.md Abschnitt 2, Punkt 9).

### 4.8 Ruleset-Qualitätssystem (`tools/ruleset_quality/`)

Read-only Analyse-, Benchmark- und Forensics-Tooling, **kein Bestandteil der
Produktionskette** (kein Import durch `app.py`/`matcher.py`/`rule_analyzer.py`/
`rule_coverage.py`). Importiert ausschließlich bereits produktive Funktionen
(`matcher.evaluate()`, `matcher.compute_ruleset_signature()`,
`category_validation.is_still_valid_category()`, `rule_analyzer.analyze_ruleset()`,
`rule_coverage.compute_rule_coverage()`, `price_history.read_price_points()`) —
keine zweite Matching-/Regex-Engine. Kernbausteine:

- **Label-Store / Baseline / Benchmark** — Ground-Truth aus
  `docs/DASHBOARD_MATCH_FORENSICS.json`, Baseline-Freeze des aktuellen Korpus,
  Regressionsvergleich mit CRITICAL/HIGH_CANDIDATE/WARNING/INFO/NEUTRAL-Gate.
- **`forensics_false_positives.py`** — extrahiert bestätigte
  `FALSE_POSITIVE`-Fälle, ermittelt den aktuellen Match-Zustand über den echten
  Produktionspfad, leitet eine nach `assessment.status` strikt abgeleitete,
  priorisierte Fix-Queue (P0–P3, `queue_category`:
  `ACTIVE_ROUTING_FP`/`GROUND_TRUTH_CONFLICT`/`MANUAL_REVIEW`/`ALREADY_FIXED`) ab
  und validiert deren Konsistenz (`validate_queue_consistency()`) — ändert
  selbst nie eine YAML-Regel.
- **`ground_truth_routing_assessment.py`** — reine Report-Schicht: trennt
  `historical_ground_truth` (Forensik-Snapshot, nie verändert) strikt von
  `current_routing_assessment` (echter Produktionspfad); ein historisches
  FALSE_POSITIVE-Label impliziert nicht mehr automatisch „aktuell noch aktiv",
  Default bleibt `STILL_ACTIVE`, nur ein dokumentierter manueller Override
  (`_MANUAL_ASSESSMENT_OVERRIDES`) darf `GROUND_TRUTH_CONFLICT`/`MANUAL_REVIEW`
  vergeben.
- **`unclear_routing_assessment.py`** — klassifiziert die 35 historischen
  `UNCLEAR`-Fälle anhand des vollen Titeltexts
  (`LIKELY_TRUE_POSITIVE`/`LIKELY_FALSE_POSITIVE`/`GROUND_TRUTH_CONFLICT`/
  `MANUAL_REVIEW` + Confidence), rein diagnostisch — keine YAML-Änderung.
- **`price_history_revalidation(_v2/_v3).py`** — read-only Preishistorie-Simulation.

Vollständige Modul-/Datenfluss-Dokumentation, CLI-Befehle und Artefaktliste:
`tools/ruleset_quality/README.md`.

---

## 5. Datenqualität — aktueller Stand

Kompakte Zusammenfassung; vollständige Tabelle mit allen 21 Punkten:
`STATUS.md` Abschnitt 4.

| Bereich | Status |
|---|---|
| 19 historische FALSE_POSITIVE-Fälle (Forensics-Fix-Queue) | ✅ 16/19 gelöst, 3 bewusst offen (2 Ground-Truth-Konflikt: Switch/Xbox, 1 Manual-Review: DS-Lite) |
| 35 historische UNCLEAR-Fälle | ⚠️ forensisch klassifiziert (11 TP / 23 FP / 1 Manual-Review), **YAML-Fix für die 23 FP-Fälle noch offen** (STATUS.md P0) |
| Umlaut-Fingerprint-Bug | Code behoben, **nicht rückwirkend** — historische Zeilen in `handhelds`/`konsolen_bundles`/`retro_konsolen`/`vintage_elektronik` bleiben strukturell unzuverlässig für Fingerprint-Revalidierung |
| `RX 7600 XT`/`RX 7600`-Überlappung | ✅ erledigt (min_vram_gb-Bug, 5 Modelle) |
| `controller`/`ladekabel`-Exclude | ✅ erledigt |
| Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation | ✅ erledigt (4 gezielte Exclude-Fixes) |
| Quoka-Preis-Parsing-Defekt | ✅ an der Wurzel gelöst (Scraper-Fix) |
| `found.json`-Vollanalyse (extern) | ✅ 36 Fehltreffer über 3 Kategorien behoben |
| Nutzer-Fehltreffer-Analyse | ✅ 25/34 erledigt, 1€-Preisanomalie bewusst nicht gefixt (≥3 unabhängige Ursachen, keine Datenbasis für neue Schwelle) |
| 19 Regeln ohne Produktivdaten | offen — weiter beobachten |
| Resale-Confidence (HIGH/MEDIUM/LOW) | offen — mögliche nächste Qualitätsstufe |
| Automatische Data-Quality-Warnungen | offen — weiterentwickeln |

---

## 6. Bekannte Einschränkungen / dauerhafte Nicht-Fixes

- **Umlaut-Fingerprint-Fix wirkt nicht rückwirkend.** `PricePoint` persistiert den
  Rohtitel nicht, ein korrekter Fingerprint lässt sich für historische Zeilen
  nicht mehr rekonstruieren.
- **`retro_konsolen`/DS-Lite** bleibt Manual-Review: ein Fix würde 3 echte,
  lexikalisch identische Handheld-Titel mitblockieren.
- **`konsolen_bundles`/Switch + Xbox** bleiben Ground-Truth-Konflikt: das
  historische FALSE_POSITIVE-Label ist vermutlich selbst fehlerhaft, aktuelle
  Evidenz spricht für echte Treffer — keine YAML-Änderung vorgesehen.
- **„Switch Pro Controller"-Regel** hat bewusst nur zwei statt drei Preisstufen —
  keine Datenbasis für eine Erweiterung.
- **`estimated_resale_price`** hat Purchase-Perspective-Bias (siehe 4.5) —
  dokumentiert, nicht stillschweigend fixen.
- **Tausch-/Barter-Anzeigen-Erkennung** (Titel-Muster „tausche"/„gegen") aus
  Notification/Preisstatistik ausschließen: mögliche Folgeaufgabe, noch nicht
  freigegeben — betrifft geschützte Kernsysteme.

---

## 7. Nächste Prioritäten

Vollständige, aktuell gepflegte Priorisierung: `STATUS.md` Abschnitt 5.

```text
P0  Fix-Queue für die 23 LIKELY_FALSE_POSITIVE-Fälle aus Batch 20e (offen,
    braucht eigene Freigabe)
     ↓
P1  Resale-Confidence ausbauen, Datenqualitätsdiagnosen automatisieren
     ↓
P2  app.py nur bei konkretem Änderungsdruck weiter modularisieren
     ↓
P3  Neue Kategorien/Deal-Intelligence erst nach Stabilitäts-/Qualitätsschritten
```

### Harte Regeln für Folgearbeiten

- Kein Big-Bang-Rewrite.
- Keine Threshold-Änderung ohne Datenbasis.
- Keine Tests löschen oder abschwächen.
- Keine neue Kategorie nur zum Feature-Zählen.
- Keine Performance-Optimierung ohne Messung.
- Keine bestehende Business-Logik duplizieren.
- Nach jeder technischen Änderung: gestuft testen (CLAUDE.md Abschnitt 3, Punkt
  4.4); volle Suite nur nach expliziter Nutzer-Freigabe.
- `STATUS.md` und diese Datei nach abgeschlossenen Batches synchron halten.

---

## 8. Historische Detaildokumentation

- **`docs/STATUS_HISTORY.md`** — vollständige, wortgetreue Batch-Historie
  (Batch 1–20), Root-Cause-Analysen und Blast-Radius-Nachweise je Fix.
- **`docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`** — vollständige Liste der 9
  zurückgestellten FP-Muster (27 Titel) aus dem 19-Kategorien-Audit.
- **`docs/CROSS_CATEGORY_ROUTING_AUDIT.md`** — Cross-Category-Routing-Audit,
  Details und Titel-Listen.
- **`docs/SCAN_PERFORMANCE_MESSUNG_2026-08-15.md`** — Scan-Performance-Messung
  vor/nach Parallelisierung + Persistence-Batching.
- **`tools/ruleset_quality/generated/reports/`** — `ABSCHLUSSBERICHT.md`,
  `FINALE_REVALIDIERUNG_ABSCHLUSSBERICHT.md`,
  `OFFENE_ENTSCHEIDUNGEN_1_BIS_3_BERICHT.md`,
  `forensics_false_positives_report.{json,md}`,
  `ground_truth_routing_assessment.{json,md}`,
  `unclear_routing_assessment.{json,md}`.
- **`tools/ruleset_quality/generated/false_positive_fix_queue.{json,md}`** —
  priorisierte, nicht automatisch angewendete Fix-Queue.
- **`document/PHASE13_VALIDATION_REPORT.md`** und weitere `document/PHASE*.md` —
  frühe Phasenberichte (Performance, Rule-Analysis/-Coverage, Preiskalibrierung).

Diese Dokumente liefern historische Details und Nachweise. Für den aktuellen
technischen Code-Stand ist HEAD `ee26893` maßgeblich; für die technische
Projektreferenz ist diese Datei maßgeblich.
