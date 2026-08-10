# Technischer Projektstatus — gpu-watch-v2

> **Single Source of Truth für den technischen Ist-Zustand.**
>
> Stand: **2026-08-10**
> Repository: `dkmd89-dev/gpu-watch-v2`
> Branch: `main`
> HEAD: `fa218a0826f3b8ae6868c0228c1267a5cd861265`
> HEAD-Commit: `fix: reduce false positives across five categories`
> Ausgangspunkt dieser Konsolidierung: `d2effe7`
> Vergleich: **61 Commits ahead, 0 behind**
>
> Diese Datei ersetzt `PROJEKTSTAND_KOMPLETT.md`. Historische Phasenberichte bleiben als Detaildokumentation erhalten; widersprüchliche ältere Ist-Stand-Angaben gelten nicht mehr als aktuell.

---

## 1. Kurzfazit

`gpu-watch-v2` ist ein modularer, YAML-gesteuerter **Hardware Deal Finder** für Second-Hand-Angebote. Das System kombiniert Scraper, kategoriebasiertes Matching, Hardware-Detektoren, Deal-Scoring, Marktpreis-/Resale-Statistik, Profit-/Flip-Bewertung, Duplicate Detection, Presence Tracking, Dashboard-KPIs und ntfy-Benachrichtigungen.

Der aktuelle technische Schwerpunkt liegt auf **Precision, Datenqualität und kontrollierter Weiterentwicklung**. Seit `d2effe7` wurden insbesondere Datenqualitäts-/Validierungslogik, Rule Analyzer/Coverage, Caching/Performance, neue Kategorien sowie ein umfangreicher False-Positive-Audit integriert.

**Wichtig:** Die Dokumentation war dem Repository-HEAD zuletzt deutlich voraus bzw. hinterher. Diese Datei korrigiert das durch einen auf `main` verifizierten Stand.

---

## 2. Verifizierter Repository-Stand

### Git

```text
Branch: main
HEAD: fa218a0
Commit: fix: reduce false positives across five categories
Datum: 2026-08-09
Vergleich d2effe7...main: 61 Commits ahead, 0 behind
```

Der aktuelle HEAD ist der Merge von PR #6. Der PR wurde am 2026-08-09 gemergt und ist kein Draft mehr.

### Teststand

Der zuletzt im Repository dokumentierte vollständige Lauf gegen `main` vor dem Merge von PR #6 war **979 passed / 0 failed** (Phase-15-Abschlussbericht). PR #6 fügte 74 Regressionstests hinzu und dokumentiert danach:

```text
pytest app/tests/
1142 passed, 0 failed
```

Zusätzlich wurde das komplette Ruleset nach PR #6 erneut mit dem Rule Analyzer geprüft:

```text
355 Regeln
19 Kategorien
0 Findings
```

**Hinweis:** Ein neuer lokaler `pytest`-Lauf war in dieser Dokumentationssession nicht möglich, weil kein Repository-Checkout im Ausführungscontainer vorhanden war. Deshalb wird 1142/0 als der zuletzt im GitHub-PR dokumentierte Verifikationsstand geführt und nicht als hier lokal erneut ausgeführt behauptet.

---

## 3. Was seit `d2effe7` integriert wurde

Der Vergleich `d2effe7...main` umfasst 61 Commits und enthält mehrere klar erkennbare Workstreams.

### 3.1 Neue Infrastruktur und Services

Unter anderem hinzugekommen bzw. erweitert:

- `app/api/deals.py`
- `app/api/history.py`
- `app/api/status.py`
- `app/data_quality.py`
- `app/deal_intelligence.py`
- `app/category_validation.py`
- `app/persistence/json_store.py`
- `app/rule_analyzer.py`
- `app/rule_coverage.py`
- `app/rules_loader.py`
- `app/scan/scheduler.py`
- `app/services/statistics_service.py`
- neue Detectoren für Zustand und Lieferumfang

`app/app.py` wurde dabei bereits deutlich reduziert bzw. umgebaut, ohne einen Big-Bang-Rewrite durchzuführen.

### 3.2 Matching und Regelwerk

Der Matcher wurde in mehreren kleinen Schritten robuster gemacht:

- kontextbewusste Excludes
- Regex-/Term-Cache
- Ruleset-Signatur/Cache-Unterstützung
- Kategorie-Revalidierung
- globale Excludes korrekt berücksichtigen
- Regressionstests gegen konkrete Fehlklassifikationen

Das YAML-Regelwerk bleibt die primäre Erweiterungsebene. Neue Kategorien können innerhalb der vorhandenen Matcher-/Detector-Primitive ohne Python-Code ergänzt werden. Neue Detector-Typen erfordern weiterhin Python-Code.

### 3.3 Neue bzw. aktualisierte Kategorien

Der aktuelle Stand enthält 19 aktive Kategorien:

- `autoradio_opel_corsa`
- `controller`
- `cpu_mainboard_bundle`
- `gaming_pc`
- `gpu`
- `handhelds`
- `iphone`
- `konsolen_bundles`
- `lego_minifiguren`
- `m2_ssd`
- `macbook`
- `monitor_curved`
- `netzteil`
- `notebook_resell`
- `office_pc`
- `retro_konsolen`
- `sata_ssd`
- `vintage_elektronik`

Die 19. Kategorie wird im aktuellen Ruleset durch die vollständige Liste der aktiven YAML-Dateien repräsentiert; `_global.yaml` ist dabei keine Kategorie.

### 3.4 Preis, Resale und Profit

Die Trennung bleibt ausdrücklich erhalten:

```text
market_price
    !=
estimated_resale_price
```

Die Resale-Schätzung verwendet ein separates, gröberes Gruppierungsmodell. Bei zu dünner Preishistorie (<5 Samples pro Resale-Gruppe) wird keine belastbare Resale-Schätzung erzwungen; dadurch sollen strukturell falsche Flip-Kandidaten vermieden werden.

Der Profit-/Flip-Workstream umfasst außerdem:

- `estimated_margin_eur`
- `estimated_margin_pct`
- Mindestkaufpreis-Schutz gegen absurde Prozentwerte
- Resale-Price-Grouping
- Dashboard-/KPI-Anbindung

### 3.5 Top-Deal-Logik und Dashboard

Die Top-Deal-Regel wurde verschärft auf:

```text
(Score >= 80 UND Discount >= 25%)
ODER
(Score >= 90 UND Discount >= 20%)
```

Zusätzlich existieren vier KPI-Kategorien:

- Top Deals
- Sehr gute Deals
- Flip-Kandidaten
- Neue Top Deals

Die Filterung erfolgt clientseitig anhand vom Backend gelieferter Schwellenwerte. Marktpreis, Rabatt, Score und Regel werden auf den Deal-Karten transparent dargestellt.

### 3.6 Performance

Phase 15 führte mehrere kontrollierte Caches ein:

- Rules-Cache
- Entry-/Ruleset-Cache bei der Kategorie-Revalidierung
- Regex-Cache im Matcher

Dokumentierte Messwerte aus dem Phase-15-Abschlussbericht:

```text
load_rules() warm:        0,161 ms
/api/status Median:       3,0 ms
matcher.evaluate():       3,625 ms
```

Die dokumentierten Verbesserungen lagen ungefähr bei:

```text
load_rules():      ~1700x warm
/api/status:       ~109x
Regex evaluate():  ~2,1x
```

### 3.7 False-Positive-Audit / PR #6

Der letzte Merge (`fa218a0`) basiert auf einem vollständigen Audit von 2.500 `found.json`-Einträgen über 19 Kategorien.

Gezielt korrigiert wurden:

1. **`notebook_resell`** — `gaming` nicht mehr als zu generisches Geräte-Signal; 32/32 identifizierte Fehltreffer blockiert.
2. **`retro_konsolen`** — `controller` nicht mehr allein ausreichend; präzisere Ersatzsignale erhalten echte Bundles.
3. **`handhelds`** — Ausschlüsse für Dockingstation, Mainboard, Ersatzteile, Defekt-/For-Parts-Angebote, Memory Card, MicroSD und M.2-SSD; `joystick`/`thumbstick` kontextbewusst behandelt.
4. **`konsolen_bundles`** — präzise Negativphrasen gegen Spielelinien, Zubehör und Reseller-Muster; `ovp` bewusst nicht pauschal entfernt.
5. **`controller`** — Restlücken `controller reparatur` und `schutzhülle` geschlossen.

Die Fixes verwenden vorhandene YAML-Primitiven und den bestehenden kontextbewussten Exclude-Mechanismus; es wurde kein neuer generischer Matcher-Mechanismus eingeführt.

---

## 4. Datenqualität

Der aktuelle Datenqualitätsstand ist technisch deutlich ausgebaut, aber noch nicht vollständig abgeschlossen.

Phase 15 dokumentierte:

- `price_history.jsonl`: 9.753 Datenpunkte
- 113 von 135 aktiven `price_history_model`-Gruppen mit mindestens einem Datenpunkt
- 22 Regeln ohne Daten, überwiegend plausible Nischen-/High-End-Varianten
- 3 Orphan-Modelle aus der nicht mehr vorhandenen Kategorie `spielzeug_bundles` mit zusammen 663 historischen Datenpunkten
- eine damalige Gesamt-False-Positive-Rate von 17,2 % in der Coverage-Analyse; diese Zahl ist wegen Alt-/Neudatenvermischung ausdrücklich nur als Beobachtungswert zu verstehen

Der anschließende PR-#6-Audit adressiert bereits mehrere konkrete False Positives. Eine erneute Coverage-Messung nach ausreichend neuer Datensammlung bleibt sinnvoll.

### Offene Datenqualitätsfragen

- historische Alt-Kontamination in `price_history.jsonl`
- 22 Regeln ohne Produktivdaten weiter beobachten
- Orphan-Daten der entfernten `spielzeug_bundles`-Kategorie nicht ohne expliziten Auftrag löschen
- `RX 7600 XT`/`RX 7600`-Überlappung und `controller`-`ladekabel`-Exclude als dokumentierte Restlücken aus Phase 15

---

## 5. Aktuelle Architektur

```text
Scraper / Quellen
      |
      v
Dedup / Presence / Persistence
      |
      v
YAML Rules Loader
      |
      v
Matcher + Hardware/Condition/Bundle Detectors
      |
      +----> Category Validation / Data Quality
      |
      v
Deal Score
      |
      +----> Market Price
      +----> Resale Price
      +----> Profit / Margin / Flip
      +----> Deal Intelligence
      |
      +----> Top-Deal / KPI Logic
      |
      +----> Notifications
      |
      v
Dashboard / API / Statistics
```

### Grundprinzipien

- YAML ist Single Source of Truth für Kategorien und viele Matching-/Scoring-Regeln.
- Scraper sind über Registry/Plugin-Strukturen entkoppelt.
- Kategorien sind dynamisch ladbar.
- Detectoren sind modular registriert.
- Preisstatistik und Resale-Schätzung sind getrennt.
- Notification-Gating bleibt von Preis-/Resale-Experimenten getrennt.
- Änderungen werden bevorzugt klein und regressionsgetestet umgesetzt.

---

## 6. Bewusst nicht als erledigt markieren

Folgende Punkte sind **nicht** durch die Konsolidierung als abgeschlossen zu betrachten:

1. `app.py` ist trotz bereits erfolgter Reduktion weiterhin ein Kandidat für kontrollierte Modularisierung.
2. Scan-Performance sollte mit echten End-to-End-Scanmetriken gemessen werden, bevor weitere Optimierungen erfolgen.
3. Resale-Confidence (z.B. HIGH/MEDIUM/LOW) ist konzeptionell sinnvoll, aber noch nicht als vollständiges Produktfeature etabliert.
4. Datenqualitätswarnungen für Kategorien, Regeln und Preisverteilungen sollten langfristig automatisiert werden.
5. Cross-Platform-Duplicate-Identity ist weiter ausbaufähig.
6. Die dokumentierten Phase-15-Restlücken (`rx_7600_xt`, `controller.yaml`/`ladekabel`) warten auf eine bewusst getrennte Regeländerung.

---

## 7. Empfohlene nächste Reihenfolge

```text
1. Dokumentation synchron halten
        ↓
2. Scan-Performance messen
        ↓
3. False-Positive-/Coverage-Audit erneut gegen neue Daten
        ↓
4. Resale-Confidence / Datenqualität verbessern
        ↓
5. app.py nur bei konkretem Änderungsdruck weiter modularisieren
        ↓
6. erst danach neue Features/Kategorien priorisieren
```

### Harte Regeln für Folgearbeiten

- Kein Big-Bang-Rewrite.
- Keine Threshold-Änderung ohne Datenbasis.
- Keine Tests löschen oder abschwächen.
- Keine neue Kategorie nur zum Feature-Zählen.
- Keine Performance-Optimierung ohne Messung.
- Keine bestehende Business-Logik duplizieren.
- Nach jeder technischen Änderung: vollständige Testsuite + Dokumentationsupdate.

---

## 8. Historische Detaildokumentation

Die folgenden Dokumente bleiben als Detail-/Arbeitsnachweise bestehen:

- `PHASE15_OPTIMIERUNG.md`
- `document/PHASE13_VALIDATION_REPORT.md`
- `document/PHASE14_DATA_QUALITY_REPORT.md`
- `document/PHASE15_COMPLETION_REPORT.md`
- `document/PHASE15_PERFORMANCE_REPORT.md`
- `document/PHASE15_RULE_ANALYSIS_REPORT.md`
- `document/PHASE15_RULE_COVERAGE_REPORT.md`
- `document/PRICE_CALIBRATION_REPORT.md`
- `document/PRICE_CALIBRATION_REVIEW.md`
- `document/PRICE_CALIBRATION_REVIEW_V2.md`
- `document/PRICE_CALIBRATION_APPLIED.md`

Diese Dokumente liefern historische Details. Für den **aktuellen Ist-Zustand** ist ausschließlich diese Datei maßgeblich.
