# Technischer Projektstatus — gpu-watch-v2

> **Single Source of Truth für den technischen Ist-Zustand.**
>
> Stand: **2026-08-10**
> Repository: `dkmd89-dev/gpu-watch-v2`
> Branch: `main`
> **Letzter Code-Commit:** `3eed07f8823d1a62e8137b63f26c57f7b0a89de1`
> **Commit:** `fix: Plattformbegriff/Mainboard/Zubehör-Fehltreffer in drei Kategorien beheben`
> **HEAD (main, inkl. Doku-Commits):** `0757580aac4c0c579edf2fc160cb6207aabdfa38`
> Ausgangspunkt dieser Konsolidierung: `d2effe7`
> Vergleich: **61 Commits ahead, 0 behind** bis `fa218a0`; danach `3eed07f` (Code) + 4 reine Doku-/Chore-Commits bis `0757580`
>
> Seit `3eed07f` wurden auf `main` ausschließlich Dokumentationsänderungen vorgenommen. Der technische Code-Stand von `main` ist daher `3eed07f`. Ein separater, noch nicht gemergter Fix-Batch liegt auf Branch `claude/dashboard-match-validation-q5g86t` (siehe Abschnitt 3.8).
>
> Diese Datei ersetzt `PROJEKTSTAND_KOMPLETT.md`. Historische Phasenberichte bleiben als Detaildokumentation erhalten; widersprüchliche ältere Ist-Stand-Angaben gelten nicht mehr als aktuell.

---

## 1. Kurzfazit

`gpu-watch-v2` ist ein modularer, YAML-gesteuerter **Hardware Deal Finder** für Second-Hand-Angebote. Das System kombiniert Scraper, kategoriebasiertes Matching, Hardware-Detektoren, Deal-Scoring, Marktpreis-/Resale-Statistik, Profit-/Flip-Bewertung, Duplicate Detection, Presence Tracking, Dashboard-KPIs und ntfy-Benachrichtigungen.

Der aktuelle technische Schwerpunkt liegt auf **Precision, Datenqualität und kontrollierter Weiterentwicklung**. Seit `d2effe7` wurden insbesondere Datenqualitäts-/Validierungslogik, Rule Analyzer/Coverage, Caching/Performance, neue Kategorien sowie ein umfangreicher False-Positive-Audit integriert.

---

## 2. Verifizierter Repository-Stand

### Git / Code

```text
Branch: main
Letzter Code-Commit: 3eed07f
Commit: fix: Plattformbegriff/Mainboard/Zubehör-Fehltreffer in drei Kategorien beheben
Datum: 2026-08-10
HEAD (main, inkl. Doku-Commits): 0757580
Vergleich d2effe7...fa218a0: 61 Commits ahead, 0 behind
fa218a0..3eed07f: 1 Code-Commit; 3eed07f..0757580: 4 reine Doku-/Chore-Commits
```

PR #6 wurde am 2026-08-09 gemergt. `3eed07f` wurde direkt gegen `main` committet (kein separater PR-Merge-Vorgang dokumentiert). Die danach folgenden Commits betreffen ausschließlich die Dokumentationskonsolidierung.

### Teststand

Der zuletzt dokumentierte vollständige Lauf, direkt aus der Commit-Message von `3eed07f` übernommen:

```text
Vollständige Testsuite: 1175/1175 bestanden
(PR #6 / fa218a0 dokumentierte zuvor 1142/0; 3eed07f fügte 3 neue
Regressions-Testdateien für den Plattformbegriff-/Mainboard-/
Zubehör-Fix hinzu)
```

**Hinweis:** Ein neuer lokaler `pytest`-Lauf war in dieser Dokumentationssession nicht möglich — `pytest` selbst ließ sich im Sandbox-Container nicht installieren (kein PyPI-Zugriff, 403 beim Nachinstallieren von `pytest`/`flask`/`pyyaml`). 1175/0 wird deshalb als der zuletzt im Commit dokumentierte Verifikationsstand geführt, nicht als in dieser Session selbst reproduziert. Für den separaten, noch nicht gemergten Batch (Abschnitt 3.8) wurden die betroffenen Testdateien stattdessen per direktem Funktionsaufruf (ohne `pytest`-Runner) ausgeführt.

---

## 3. Was seit `d2effe7` integriert wurde

Der Vergleich `d2effe7...fa218a0` umfasst 61 Commits und enthält mehrere klar erkennbare Workstreams.

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

### 3.3 Aktive Kategorien

Der aktuelle Stand enthält 19 aktive Kategorien. `_global.yaml` ist dabei keine Kategorie.

Die aktive Liste wird durch die aktuellen YAML-Dateien unter `app/rules/` bestimmt; historische Kategorienamen aus alten Statusabschnitten sind nicht maßgeblich.

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

Dokumentierte Messwerte:

```text
load_rules() warm:        0,161 ms
/api/status Median:       3,0 ms
matcher.evaluate():       3,625 ms
```

### 3.7 False-Positive-Audit / PR #6

Der letzte Code-Merge (`fa218a0`) basiert auf einem vollständigen Audit von 2.500 `found.json`-Einträgen über 19 Kategorien.

Gezielt korrigiert wurden:

1. **`notebook_resell`** — `gaming` nicht mehr als zu generisches Geräte-Signal; 32/32 identifizierte Fehltreffer blockiert.
2. **`retro_konsolen`** — `controller` nicht mehr allein ausreichend; präzisere Ersatzsignale erhalten echte Bundles.
3. **`handhelds`** — Ausschlüsse für Dockingstation, Mainboard, Ersatzteile, Defekt-/For-Parts-Angebote, Memory Card, MicroSD und M.2-SSD; `joystick`/`thumbstick` kontextbewusst behandelt.
4. **`konsolen_bundles`** — präzise Negativphrasen gegen Spielelinien, Zubehör und Reseller-Muster; `ovp` bewusst nicht pauschal entfernt.
5. **`controller`** — Restlücken `controller reparatur` und `schutzhülle` geschlossen.

Die Fixes verwenden vorhandene YAML-Primitiven und den bestehenden kontextbewussten Exclude-Mechanismus; es wurde kein neuer generischer Matcher-Mechanismus eingeführt.

### 3.8 Dashboard-Match-Validierung Variante C (in Arbeit, PR #8, nicht gemergt)

Branch `claude/dashboard-match-validation-q5g86t`. Ausgangspunkt: Live-Verifikation der Dashboard-Instanz (`romajagijo.zapto.org`) gegen den `3eed07f`-Fix, ausschließlich über öffentliche HTTP-Endpunkte (`/`, `/api/status`, `/api/found`) — kein SSH-/Docker-Zugriff auf den Produktionshost verfügbar, Git-Commit/Deploy-Zeitpunkt der Live-Instanz daher nicht direkt beweisbar.

Ergebnis: zwei verbleibende `konsolen_bundles`-Match-Lücken nach `3eed07f` identifiziert und einzeln bewertet:

1. **"GameCube Controller" ohne "für"/"pro controller"** (z.B. "Nintendo Switch 2 GameCube Controller | OVP | NEU") — **geschlossen**. `app/rules/konsolen_bundles.yaml`: neuer Eintrag unter `exclude_category_unless_preceded_by`, identisches Muster wie der bereits produktive "pro controller"-Eintrag (YAML-Anker `*bundle_konnektoren`), kein neuer Matcher-Code. Verifiziert gegen den vollständigen 318-Fingerprint-Korpus für `konsolen_bundles` aus `data/price_history.jsonl`: genau 2 Treffer ändern sich (beide reale, vorher fälschlich matchende Zubehör-Angebote), 0 Kollisionen mit echten Bundles.
2. **"Spieltitel + Plattform ohne 'für'"** (z.B. "Nintendo Switch - Minecraft FRA mit OVP", real bestätigt u.a. auch bei "Donkey Kong Bananza", "Metroid Prime Remastered") — **bewusst nicht geschlossen** (Nutzerentscheidung, Option 1: als dokumentierte Restlücke offen lassen). Eine Lösung würde entweder die bereits geschützte Design-Entscheidung "OVP bleibt Positivsignal auch ohne Geräte-Marker" (`3eed07f`) umkehren oder Einzelspieltitel als Excludes sammeln — beides im Projekt bereits explizit verworfen. Braucht eine eigene, separat freigegebene, datengetestete Review-Runde.

Testabdeckung: `app/tests/test_konsolen_bundles_plattform_referenz_fix.py` aktualisiert (18/18 bestanden, manuell per Funktionsaufruf verifiziert, siehe Teststand-Hinweis oben). 8 weitere themennahe Testdateien ebenso manuell geprüft: 194 bestanden, 5 Fehlschläge — ausschließlich durch fehlende Module (`flask`) im Sandbox-Container, nicht durch die Änderung verursacht.

**Offener Punkt:** PR #8 wurde ohne Merge geschlossen. Der GameCube-Controller-Fix ist damit noch **nicht** Teil von `main`. Weiteres Vorgehen (PR #8 reopen oder neuer PR) ist mit dem Auftraggeber zu klären, bevor dieser Abschnitt als abgeschlossen gilt.

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
7. `konsolen_bundles`: "Spieltitel + Plattform ohne 'für'"-Restlücke (Abschnitt 3.8) — bewusst offen, braucht eigene datengetestete Review-Runde.
8. PR #8 (Dashboard-Match-Validierung Variante C, GameCube-Controller-Fix) ist ohne Merge geschlossen — noch nicht Teil von `main`.

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

Diese Dokumente liefern historische Details. Für den **aktuellen technischen Code-Stand** ist der Code-Commit `fa218a0` maßgeblich; für die technische Projektreferenz ist diese Datei maßgeblich.
