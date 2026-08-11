# Technischer Projektstatus — gpu-watch-v2

> **Single Source of Truth für den technischen Ist-Zustand.**
>
> Stand: **2026-08-11**
> Repository: `dkmd89-dev/gpu-watch-v2`
> Branch: `main`
> **Letzter Code-Commit:** `1f6555317152b453415e8f74f043a2bcdd758095` (PR #25, Merge-Commit)
> **Commit:** `docs: kompletten 19-Kategorien-Ruleset-Audit abschließen (#25)`
> **HEAD (main):** `1f6555317152b453415e8f74f043a2bcdd758095`
> Ausgangspunkt dieser Konsolidierung: `d2effe7`
> Vergleich zum vorherigen dokumentierten Stand (`ca4b35b`, PR #8): 17 gemergte PRs (#9–#25) — 15 mit Code-/Regeländerung (PR #10–#24), 3 reine Doku-Commits (#9, #21, #25)
>
> PR #11–#25 (systematischer Active-False-Positive-Audit über alle 19 Kategorien, siehe Abschnitt 3.9) sind gemergt. Der technische Code-Stand von `main` ist damit `1f65553`.
>
> Diese Datei ersetzt `PROJEKTSTAND_KOMPLETT.md` (Datei mittlerweile aus dem Repository entfernt). Historische Phasenberichte bleiben als Detaildokumentation erhalten; widersprüchliche ältere Ist-Stand-Angaben gelten nicht mehr als aktuell.

---

## 1. Kurzfazit

`gpu-watch-v2` ist ein modularer, YAML-gesteuerter **Hardware Deal Finder** für Second-Hand-Angebote. Das System kombiniert Scraper, kategoriebasiertes Matching, Hardware-Detektoren, Deal-Scoring, Marktpreis-/Resale-Statistik, Profit-/Flip-Bewertung, Duplicate Detection, Presence Tracking, Dashboard-KPIs und ntfy-Benachrichtigungen.

Der aktuelle technische Schwerpunkt liegt auf **Precision, Datenqualität und kontrollierter Weiterentwicklung**. Seit `d2effe7` wurden insbesondere Datenqualitäts-/Validierungslogik, Rule Analyzer/Coverage, Caching/Performance, neue Kategorien sowie ein umfangreicher False-Positive-Audit integriert.

---

## 2. Verifizierter Repository-Stand

### Git / Code

```text
Branch: main
Letzter Code-Commit: 1f65553 (PR #25, Merge-Commit)
Commit: docs: kompletten 19-Kategorien-Ruleset-Audit abschließen (#25)
Datum: 2026-08-11
Davor: 158f2ed (docs: kompletten 19-Kategorien-Ruleset-Audit abschließen)
Vorheriger dokumentierter Stand: ca4b35b (PR #8)
ca4b35b..1f65553: 17 gemergte PRs (#9-#25) -- #9/#21/#25 reine
Doku-Commits, #10-#24 mit Code-/Regeländerung (#10 konsolen_bundles,
#11 handhelds, #12 office_pc+retro_konsolen, #13 gpu+lego_minifiguren,
#14 iphone, #15 monitor_curved, #16 vintage_elektronik, #17 netzteil,
#18 notebook_resell, #19 ram, #20 sata_ssd, #22 controller, #23
autoradio_opel_corsa, #24 gaming_pc+macbook)
```

PR #6 wurde am 2026-08-09 gemergt, PR #8 am 2026-08-10. PR #11–#25 (systematischer Active-False-Positive-Audit über alle 19 Kategorien, siehe Abschnitt 3.9) wurden zwischen 2026-08-10 und 2026-08-11 gemergt, jeweils als eigener Feature-Branch → PR → Merge-Commit auf `main`.

### Teststand

In dieser Session tatsächlich lokal ausgeführt und verifiziert (kein Sandbox-Installationsproblem mehr, `pytest`/`flask`/`pyyaml` verfügbar):

```text
Zwischenstand (nach den ersten 12 der 19 Kategorien):
pytest app/tests/ -> 1233 passed, 0 failed (620,33s)

Finaler Stand (nach Abschluss aller 19 Kategorien, PR #25):
pytest app/tests/ -> 1241 passed, 0 failed (622,17s)

rule_analyzer.py (nach jedem Einzel-Fix erneut verifiziert):
355 Regeln, 19 Kategorien, 0 Findings -- durchgehend unverändert
```

Vorheriger dokumentierter Stand (`3eed07f`, aus Commit-Message übernommen, nicht selbst reproduziert): 1175/1175. Die volle Suite wurde in diesem Durchlauf bewusst nicht nach jeder Einzelkategorie ausgeführt (Vorgabe des Nutzers), sondern nur an den beiden genannten Batch-Grenzen — nach jedem Einzel-Fix lief stattdessen ausschließlich der kategorienbezogene Testlauf (`pytest app/tests/ -k "<kategorie>"`).

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

### 3.8 Dashboard-Match-Validierung Variante C (abgeschlossen, PR #8 gemergt)

Branch `claude/dashboard-match-validation-q5g86t`, gemergt als Squash-Commit `ca4b35b`. Ausgangspunkt: Live-Verifikation der Dashboard-Instanz (`romajagijo.zapto.org`) gegen den `3eed07f`-Fix, ausschließlich über öffentliche HTTP-Endpunkte (`/`, `/api/status`, `/api/found`) — kein SSH-/Docker-Zugriff auf den Produktionshost verfügbar, Git-Commit/Deploy-Zeitpunkt der Live-Instanz daher nicht direkt beweisbar.

Ergebnis: zwei `konsolen_bundles`-Match-Lücken nach `3eed07f` identifiziert und **beide geschlossen**:

1. **"GameCube Controller" ohne "für"/"pro controller"** (z.B. "Nintendo Switch 2 GameCube Controller | OVP | NEU") — `app/rules/konsolen_bundles.yaml`: neuer Eintrag unter `exclude_category_unless_preceded_by`, identisches Muster wie der bereits produktive "pro controller"-Eintrag (YAML-Anker `*bundle_konnektoren`), kein neuer Matcher-Code. Verifiziert gegen den vollständigen 318-Fingerprint-Korpus für `konsolen_bundles` aus `data/price_history.jsonl`: genau 2 Treffer ändern sich (beide reale, vorher fälschlich matchende Zubehör-Angebote), 0 Kollisionen mit echten Bundles.
2. **"Plattform + Bindestrich" ohne "für"** (z.B. "Nintendo Switch - Minecraft FRA mit OVP", real bestätigt in `price_history.jsonl`) — zunächst dokumentiert offen gelassen (Nutzerentscheidung, "Option 1"), danach in einer separaten Review-Runde (Schritt 2, auf Ansage des Nutzers) geschlossen: `matcher.py::_contains_term()` prüft den Titel nur per `.lower()`, ohne Interpunktion zu entfernen — der Bindestrich ist damit regulärer Bestandteil eines `exclude_category_unless_also_contains`-Schlüssels, exakt derselbe Mechanismus wie bei "für Plattform", kein neuer Matcher-Code. Beide Strich-Varianten ("-"/"–") abgedeckt. Verifiziert gegen den 318-Fingerprint-Korpus UND einen zusätzlich für diese Review-Runde erschlossenen 186-Titel-Rohkorpus aus `data/gpu_watch.log.{1,2}` (mit erhaltener Interpunktion, da normalisierte Fingerprints Bindestriche verschlucken) — 0 Kollisionen in beiden. Zwei echte Bundle-Titel treffen das neue Muster wörtlich, bleiben aber durch vorhandene Geräte-Marker über die bestehende Ausnahme unverändert erhalten.

Beide Fixes verwenden ausschließlich bereits produktive YAML-Primitiven; es wurde kein neuer generischer Matcher-Mechanismus eingeführt.

**Neue, kleinere Restlücke (bewusst nicht geschlossen):** Spieltitel VOR der Plattform OHNE nachfolgenden Bindestrich (z.B. "Donkey Kong Bananza Nintendo Switch 2 2025 OVP", "Metroid Prime Remastered Nintendo Switch 2023 gebraucht in OVP") — dafür gibt es kein Substring-Muster, das nicht auch echte Geräte-Titel träfe; als dokumentierter Testfall festgehalten (`test_bekannte_restluecke_spieltitel_vor_plattform_ohne_bindestrich`).

Testabdeckung: `app/tests/test_konsolen_bundles_plattform_referenz_fix.py` (23/23 bestanden, manuell per Funktionsaufruf verifiziert, siehe Teststand-Hinweis oben, da `pytest` in der Sandbox nicht installierbar war). 8 weitere themennahe Testdateien ebenso manuell geprüft: 194 bestanden, 5 Fehlschläge — ausschließlich durch fehlende Module (`flask`/`pytest`) im Sandbox-Container, nicht durch die Änderung verursacht. `rule_analyzer.py`: 0 Findings.

### 3.9 Systematischer Active-False-Positive-Audit über alle 19 Kategorien (abgeschlossen, PR #11–#25 gemergt)

Direkte methodische Fortsetzung von Abschnitt 3.7/3.8, jetzt aber **vollständig statt exemplarisch**: statt einzelner, punktuell gemeldeter Fehltreffer wurde für jede der 19 Kategorien in `app/rules/` der komplette aktuell live matchende `found.json`-Korpus einzeln gegen die produktiven Regeln geprüft — nicht nur eine Stichprobe. Reihenfolge der Kategorien: evidenzbasiert nach aktuellem Matchvolumen (höchstes zuerst), neu bestimmt nach jeder abgeschlossenen Kategorie, nicht nach Gefühl vorab festgelegt.

**Methodik je Kategorie:**

1. Live-Auswertung aller aktuell matchenden Titel via `matcher.load_rules()` + `matcher.evaluate()` gegen die produktiven `app/rules/*.yaml`, mit dem **echten** `found.json`-Preis (nicht `price=0.0` — ein früher Testartefakt zeigte, dass `price=0.0` First-Match-Wins bei preisgedeckelten Regeln systematisch verzerrt, siehe `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`, Abschnitt "Routing / First-Match-Wins").
2. Jeder Treffer einzeln auf reale Fehlklassifikation geprüft (kein Ruleset-Review auf Verdacht).
3. Root-Cause-Analyse je gefundenem Muster, Kollisionsprüfung gegen den vollständigen Korpus der Kategorie vor jeder Änderung.
4. Fix ausschließlich additiv über bestehende YAML-Primitiven (`exclude_category`, `exclude_category_unless_also_contains`, `exclude_category_unless_preceded_by`) — kein neuer Matcher-Mechanismus, keine neue Detector-Logik.
5. Dedizierte Regressionstestdatei pro Kategorie (`app/tests/test_<kategorie>_active_fp_audit_fix.py`), kategorienbezogener Testlauf sofort danach.
6. Ergebnis in `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md` dokumentiert statt in einer neuen Report-Datei je Kategorie.

**Ergebnis (14 Kategorien mit realen Fixes, 42 Muster / 113 Titel):**

| Kategorie | Muster | Titel | Kernbefund |
|---|---:|---:|---|
| handhelds | 8 | 10 | Displayschutz/Ersatzstift/Schutzhülle-Komposita, "Spiele für"-Software statt Gerät |
| office_pc | 2 | 27 | Bare Mainboard/Aufrüstkit-Bundles ohne Gehäuse (Kategorie hatte bisher bewusst kein `exclude_category`) |
| retro_konsolen | 3 | 9 | Standalone Memory Cards (kontextbewusst gelöst, ohne 2 echte Bundles zu zerstören) |
| lego_minifiguren | 1 | 1 | Negation "Ohne Figuren" vor bare "figuren" |
| iphone | 1 | 1 | "Leere Originalverpackung" ohne Gerät |
| monitor_curved | 2 | 2 | PS-Konsolen-Kurzform ("ps4slim"), Heimtrainer-Display |
| vintage_elektronik | 11 | 40 | **Größter Einzelfund** — Sony-PVM/BVM-Ersatzteile (Platine/Akku/Chip), da die "Profi-CRT-Monitor"-Regel die Excludes der Schwesterregel "Röhrenfernseher" nicht geerbt hatte |
| netzteil | 1 | 2 | HiFi-Verstärker mit Watt-Angabe, vom PSU-Detector fehlinterpretiert |
| notebook_resell | 1 | 2 | "Ohne SSD/RAM" — Negation vor bare "ssd" |
| ram | 2 | 2 | Pluralform "Laptops", Schreibweise "SO- DIMM" |
| sata_ssd | 1 | 3 | Externe USB-SSDs ("Portable", "Externer Speicher") |
| controller | 5 | 6 | Zubehör (Halter/Akku/Empfänger/Ersatzteile) + real bestätigtes, im Code bereits dokumentiertes Konsolen-Bundle-Restrisiko |
| autoradio_opel_corsa | 1 | 2 | OEM-Werksteile über generisches "multimedia"-Signalwort |
| gaming_pc | 3 | 6 | Gaming-Laptops + bares Mainboard-Bundle (identische Root Cause wie office_pc, dort bereits real widerlegte "kein exclude_category"-Annahme) |

**4 Kategorien mit verifiziert 0 Findings** (kein Fix, dokumentiert statt stillschweigend übersprungen): `gpu`, `macbook`, `m2_ssd`, `cpu_mainboard_bundle`.

**9 Muster / 27 Titel real belegt, aber bewusst zurückgestellt** (P1/P2 — zu dünne Evidenz für eine verallgemeinerbare Regel oder ungelöstes Kollisionsrisiko, z.B. `iphone` "Zubehörpaket" mit widersprüchlicher Evidenz auf beiden Seiten). Vollständige Liste mit Einzelbegründung: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.

**Methodischer Nebenbefund:** `data/found.json` wird von einem laufenden Produktiv-Scanner (Docker Compose) live verändert — Titelzahlen zwischen Audit-Schritten sind Momentaufnahmen, keine stabilen, exakt reproduzierbaren Werte. Ohne Einfluss auf die Korrektheit der einzelnen Fixes (jeder Fund wurde zum jeweiligen Auswertungszeitpunkt einzeln real verifiziert).

Testabdeckung: 14 neue Regressionstestdateien. Innerhalb dieses Audit-Durchlaufs (PR #11–#24, ab dem zu Beginn selbst verifizierten Stand 1197/1197 nach handhelds) wuchs die volle Suite auf **1241/1241** — 44 neue Tests. Der ältere Referenzwert 1175/1175 (`3eed07f`, vor PR #8/#10) ist nicht direkt vergleichbar, da die volle Suite zwischen `3eed07f` und dem Start dieses Durchlaufs nicht durchgehend lokal reproduziert wurde (siehe Abschnitt 3.8, Teststand-Hinweis dort). `rule_analyzer.py`: durchgehend 0 Findings, 355 Regeln, 19 Kategorien — unverändert über den gesamten Durchlauf.

---

## 4. Datenqualität

Der aktuelle Datenqualitätsstand ist technisch deutlich ausgebaut, aber noch nicht vollständig abgeschlossen.

Phase 15 dokumentierte:

- `price_history.jsonl`: 9.753 Datenpunkte
- 113 von 135 aktiven `price_history_model`-Gruppen mit mindestens einem Datenpunkt
- 22 Regeln ohne Daten, überwiegend plausible Nischen-/High-End-Varianten
- 3 Orphan-Modelle aus der nicht mehr vorhandenen Kategorie `spielzeug_bundles` mit zusammen 663 historischen Datenpunkten
- eine damalige Gesamt-False-Positive-Rate von 17,2 % in der Coverage-Analyse; diese Zahl ist wegen Alt-/Neudatenvermischung ausdrücklich nur als Beobachtungswert zu verstehen

Der anschließende PR-#6-Audit adressiert bereits mehrere konkrete False Positives; der systematische Active-False-Positive-Audit (Abschnitt 3.9, PR #11–#25) hat diese Arbeit auf **alle 19 Kategorien** ausgeweitet und dabei 113 weitere reale Fehltreffer-Titel beseitigt (u.a. den mit 40 Titeln größten Einzelfund des Projekts in `vintage_elektronik`). `price_history.jsonl` ist inzwischen auf 11.799 Datenpunkte gewachsen (Stand 2026-08-11, reine Zeilenzählung — keine erneute vollständige Coverage-/Model-Abdeckungsanalyse in dieser Session durchgeführt). Eine erneute Coverage-Messung mit überwiegend Post-Audit-Daten bleibt der nächste sinnvolle Schritt (siehe Abschnitt 7, P0).

### Offene Datenqualitätsfragen

- historische Alt-Kontamination in `price_history.jsonl`
- 22 Regeln ohne Produktivdaten weiter beobachten
- Orphan-Daten der entfernten `spielzeug_bundles`-Kategorie nicht ohne expliziten Auftrag löschen
- `RX 7600 XT`/`RX 7600`-Überlappung und `controller`-`ladekabel`-Exclude als dokumentierte Restlücken aus Phase 15
- 9 Muster / 27 Titel aus dem Active-False-Positive-Audit (Abschnitt 3.9) bewusst zurückgestellt (P1/P2) — vollständige Liste: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`
- Coverage-/False-Positive-Rate erneut messen, sobald überwiegend Post-Audit-Daten vorliegen (letzter Beobachtungswert 17,2 % gilt weiterhin als nicht belastbar, siehe oben)

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
7. `konsolen_bundles`: "Spieltitel VOR Plattform ohne Bindestrich"-Restlücke (Abschnitt 3.8, z.B. "Donkey Kong Bananza Nintendo Switch 2 2025 OVP") — bewusst offen, kein kollisionsfreies Substring-Muster identifiziert.
8. 9 Muster / 27 Titel aus dem Active-False-Positive-Audit (Abschnitt 3.9) bewusst zurückgestellt (P1/P2), nicht gefixt — vollständige Liste mit Einzelbegründung: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.
9. Coverage-/False-Positive-Rate-Neumessung nach dem Audit (Abschnitt 3.9) steht noch aus — der 17,2-%-Beobachtungswert aus Phase 15 bleibt bis dahin nicht belastbar.

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

Diese Dokumente liefern historische Details. Für den **aktuellen technischen Code-Stand** ist der Code-Commit `ca4b35b` maßgeblich; für die technische Projektreferenz ist diese Datei maßgeblich.
