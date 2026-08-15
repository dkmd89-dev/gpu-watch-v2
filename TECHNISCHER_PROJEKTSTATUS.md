# Technischer Projektstatus — gpu-watch-v2

> **Single Source of Truth für den technischen Ist-Zustand.**
>
> Stand: **2026-08-15**
> Repository: `dkmd89-dev/gpu-watch-v2`
> Branch: `main`
> **Letzter Code-Commit (vor dieser Doku-Aktualisierung):** `2bcc7d4` (Merge PR #39)
> **HEAD (main, vor dieser Doku-Aktualisierung):** `2bcc7d4` (Merge PR #39)
> Vorheriger dokumentierter Stand: `a3e5060` (Merge PR #38)
> Seit `a3e5060`: PR #39 (read-only Kategorie-Audit + 5 Live-Fehltreffer-Fixes über
> `vintage_elektronik`/`handhelds`/`konsolen_bundles` + Preis-Mindestbetrag-Guard, Abschnitt 3.19)
> + dieser Batch: die in Abschnitt 3.19 zurückgestellte „pro"-Kollision in
> `konsolen_bundles.yaml` **gelöst** — siehe Abschnitt 3.20. Stellte sich bei tieferer Analyse als
> 3 unabhängige, einzeln additiv lösbare Ursachen heraus (Bindestrich-Kompositum-Lücke bei „pro
> controller", eindeutiger Markenname „MixAmp", Plattform-Kompatibilitätsliste bei „Vertical
> Stand") statt einer strukturellen Gruppen-Kollision.
>
> Diese Datei ersetzt `PROJEKTSTAND_KOMPLETT.md` (Datei mittlerweile aus dem Repository entfernt). Historische Phasenberichte bleiben als Detaildokumentation erhalten; widersprüchliche ältere Ist-Stand-Angaben gelten nicht mehr als aktuell.

---

## 1. Kurzfazit

`gpu-watch-v2` ist ein modularer, YAML-gesteuerter **Hardware Deal Finder** für Second-Hand-Angebote. Das System kombiniert Scraper, kategoriebasiertes Matching, Hardware-Detektoren, Deal-Scoring, Marktpreis-/Resale-Statistik, Profit-/Flip-Bewertung, Duplicate Detection, Presence Tracking, Dashboard-KPIs und ntfy-Benachrichtigungen.

Der aktuelle technische Schwerpunkt liegt auf **Precision, Datenqualität und kontrollierter Weiterentwicklung**. Seit `d2effe7` wurden insbesondere Datenqualitäts-/Validierungslogik, Rule Analyzer/Coverage, Caching/Performance, neue Kategorien sowie ein umfangreicher False-Positive-Audit integriert. Seit 2026-08-14 ergänzt ein dediziertes, read-only **Ruleset-Qualitätssystem** (`tools/ruleset_quality/`, siehe Abschnitt 3.11) den bisherigen punktuellen Audit-Ansatz um reproduzierbare Regression-Benchmarks und Preishistorie-Simulationen. Im selben Tag (Abschnitt 3.12) wurde die 251-Listing-Stichprobe vollständig gelabelt, daraus resultierend 3 Exclude-Fixes umgesetzt (PR #31), der Umlaut-Fingerprint-Bug behoben und eine kontrollierte Preishistorie-Revalidierung v3 durchgeführt (PR #32) — mit dem wichtigen Befund, dass der Fix nicht rückwirkend auf bereits gespeicherte Daten wirkt. Direkt im Anschluss wurde Datenqualitätspunkt 14 (Abschnitt 3.13, Zubehör/Ersatzteil-vs-Gerät) mit 4 weiteren gezielten Exclude-Fixes gelöst (PR #33), gefolgt von Datenqualitätspunkt 5 (Abschnitt 3.14, `controller`/`ladekabel`-Restlücke, PR #34) und Datenqualitätspunkt 4 (Abschnitt 3.15, `RX 7600 XT`/`RX 7600`-Überlappung, PR #35) — Letzteres deckte einen strukturellen min_vram_gb-Bug auf, der zusätzlich 4 weitere GPU-Modelle betraf. Am 2026-08-15 (Abschnitt 3.16) wurde erstmals eine echte End-to-End-Scan-Performance-Messung anhand von 35 Produktiv-Scan-Läufen durchgeführt und der größte gefundene Hebel (Scraping macht 88,9% der Scanzeit aus, lief seriell) direkt umgesetzt: die drei Scraper-Quellen laufen jetzt parallel. Direkter Folgeschritt (Abschnitt 3.17): Persistence-Batching -- die ursprüngliche Analyse wurde dabei korrigiert, der dominante Kostentreiber war `seen.json` (16,7 MB), nicht primär `found.json`. Nach der Verifikation beider Performance-Fixes gegen echte Produktivdaten (Abschnitt 3.18, PR #38) wurde ein vollständiger, read-only Kategorie-Audit durchgeführt (0 Abweichungen zwischen YAML/Dashboard/found.json), gefolgt von einer Nutzer-gemeldeten Live-Fehltreffer-Analyse gegen die `tools/ruleset_quality/`-Regression-Benchmarks (Abschnitt 3.19): 5 real bestätigte Fehltreffer über `vintage_elektronik`/`handhelds`/`konsolen_bundles` behoben sowie ein Preis-Mindestbetrag-Guard gegen einen Quoka-seitigen Preis-Parsing-Defekt ergänzt, der `price_history.jsonl` mit 0€-Datenpunkten verzerrte. Direkter Folgeschritt (Abschnitt 3.20): die dort zurückgestellte „pro"-Kollision in `konsolen_bundles.yaml` wurde bei tieferer Analyse doch gelöst -- 3 unabhängige, einzeln additiv lösbare Ursachen statt einer strukturellen Gruppen-Kollision, inklusive einer expliziten Korrektur eines zunächst erwogenen, aber per Blast-Radius-Check verworfenen breiteren Fixes.

---

## 2. Verifizierter Repository-Stand

### Git / Code

```text
Branch: main
Letzter Code-Commit (vor dieser Doku-Aktualisierung): 2bcc7d4 (Merge PR #39)
Vorheriger dokumentierter Stand: a3e5060 (Merge PR #38)

a3e5060..2bcc7d4:
  PR #39 (7879997) -- fix: 5 Live-Fehltreffer über 3 Kategorien +
                       Preis-Mindestbetrag-Guard (siehe Abschnitt 3.19)

Dieser Batch (noch ohne PR-Nummer, siehe Abschnitt 3.20):
  konsolen_bundles.yaml -- "pro"-Kollision gelöst:
    "pro-controller" (Bindestrich-Geschwister zu bestehendem "pro controller")
    "mixamp" (bare Exclude)
    "vertical stand" (exclude_category_unless_also_contains)
```

Zusätzlich, außerhalb der Commit-Historie (freigegebene Datenänderung, kein Code-Commit):
`lego_bundle`-Migration/-Bereinigung in `data/price_history.jsonl` — 5 Punkte migriert, 655
gelöscht (siehe Abschnitt 3.12).

### Teststand

```text
Zuletzt vollständig lokal ausgeführt und verifiziert (vom Nutzer, nach diesem Batch):
pytest app/tests/ -> 1355 passed, 0 failed (85,27s)

rule_analyzer.py:
355 Regeln, 19 Kategorien, 0 Findings
Ruleset-Signatur (matcher.compute_ruleset_signature()): 6266e4a437c1fbc4
  -- GEÄNDERT gegenüber b863e724db9b393c (YAML-Änderung in
     konsolen_bundles.yaml, siehe Abschnitt 3.20)
```

Vorheriger dokumentierter Stand: 1337/1337 (PR #39). 6 neue Tests in diesem Batch
(`test_konsolen_bundles_pro_kollision_fix.py`) — kein Test wurde gelöscht oder abgeschwächt.
Anmerkung: 1337+6=1343 ≠ 1355 (Differenz +12, diesmal in die andere Richtung als beim letzten
Batch) — wie dort bereits vermerkt, wird STATUS.md/diese Datei nicht in jeder Session live gegen
einen lokalen Checkout verifiziert (siehe Fußzeile dieser Datei). Der jetzt dokumentierte Stand
(1355) ist der aktuell verifizierte.

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

### 3.10 Cross-Category-Routing-Audit (abgeschlossen, PR #26–#28 gemergt)

Direkte methodische Fortsetzung von Abschnitt 3.9, aber anderer Blickwinkel: nicht mehr "ist
Kategorie X intern zu breit", sondern "landet ein realer Titel aktuell in der falschen Kategorie,
obwohl eine andere vorhandene Kategorie besser passt". Korpus: `data/found.json`, 1817 Einträge /
1760 eindeutige Titel (Stand des Audit-Laufs), jeder Titel frisch über `matcher.load_rules()` +
`matcher.evaluate()` mit dem echten Preis ausgewertet (nicht `price=0.0`, identische Begründung
wie Abschnitt 3.9).

**Ergebnis:**

1. **`office_pc`** (PR #27, `fc59d1d`): excludiert jetzt zusätzlich `laptop`/`notebook`/
   `thinkpad`/`macbook`/`ideapad`/`alienware`/`lifebook`. 22 betroffene Titel danach sauber
   `unmatched` (kein neues Fehlrouting in eine andere Kategorie), die verbleibenden 21
   `office_pc`-Treffer sind ausnahmslos echte Desktop-/Tower-/Bundle-Angebote. Tests:
   `test_office_pc_notebook_cross_category_fix.py` (9 neue Tests).
2. **`macbook`** (PR #28, `b6f33e0`): `"1024GB"`-Speichergrößen-Schreibweise ergänzt (P2-Fund
   desselben Audits, bare Zahl ohne Leerzeichen vor "GB" wurde nicht erkannt).

Details, vollständige Titel-Listen und Root-Cause-Analyse: `docs/CROSS_CATEGORY_ROUTING_AUDIT.md`.
Rule Analyzer nach beiden Fixes weiterhin 0 Findings, 355 Regeln, 19 Kategorien.

### 3.11 Ruleset-Qualitätssystem (`tools/ruleset_quality/`, PR #29 + 2 read-only Folge-Sessions)

Neues, dediziertes Package **außerhalb der Produktionskette** (kein Import durch `app.py`/
`matcher.py`/`rule_analyzer.py`/`rule_coverage.py`) für reproduzierbare Regression-Benchmarks und
Preishistorie-Simulationen. Nutzt ausschließlich bereits produktive Funktionen wieder
(`matcher.evaluate()`, `matcher.compute_ruleset_signature()`, `category_validation.
is_still_valid_category()`, `rule_analyzer.analyze_ruleset()`, `rule_coverage.
compute_rule_coverage()`, `price_history.read_price_points()`) — **keine zweite Matching-/
Regex-Engine**. Vollständige Architektur-/Datenfluss-Doku: `tools/ruleset_quality/README.md`.

**Module** (Kurzübersicht, Details im README):

```text
label_store.py              Ground-Truth-Label-Store aus docs/DASHBOARD_MATCH_FORENSICS.json
baseline.py / historical_baseline.py   found.json-Snapshot bzw. historischer Vor-Audit-Snapshot
benchmark.py / detailed_transition.py  Regression-Benchmark inkl. Gate v2 (CRITICAL/HIGH/
                                        MEDIUM/LOW-Matrix)
category_report.py / quality_metrics.py  Precision/FP-Rate je Kategorie
cross_category_routing.py    empirische Mehrfach-Kategorie-Analyse (kategoriegefilterte evaluate())
price_history_revalidation(_v2).py     read-only Preishistorie-Simulation
title_recovery.py            Fingerprint -> echter Titel (Korrektur-Baustein, siehe unten)
decision_points_1_3.py / sampling_plan.py   Tiefenanalyse einzelner offener Punkte + Stichprobenplan
```

**Zentrale Befunde:**

1. Die zuvor kursierenden Referenzzahlen ("2252 TP / 19 FP / 35 UNCLEAR") stammen nachweislich aus
   `docs/DASHBOARD_MATCH_FORENSICS.json`, einem Snapshot von **vor** dem 19-Kategorien-Audit
   (Commit `01afd5b`, 2026-08-10) — nicht aus dem aktuellen Korpus. Ground-Truth-Abdeckung des
   Live-Korpus fällt sehr schnell: 19,2% (2026-08-11) → 0,6% (2026-08-14, 3 Tage später).
2. Historischer Regressionsvergleich (Forensik-Snapshot gegen aktuelles Ruleset, über echten
   Produktionspfad): 2096/2252 vormals bestätigte TRUE_POSITIVE (93,1%) bleiben exakt stabil. Die
   91 "TP → kein Treffer"-Fälle sind bei Stichprobenprüfung fast durchweg bereits bekannte,
   gewollte Fixes aus Abschnitt 3.9/3.10 (office_pc-ThinkPad-Exclude, gaming_pc-Laptop-Exclude,
   vintage_elektronik-"Altes Foto"-Exclude) — keine neuen unentdeckten Regressionen.
3. Cross-Category-Ambiguität (19 kategoriegefilterte `evaluate()`-Läufe je Listing, 2500 Listings):
   nur 23 (0,9%) mit mehr als einer möglichen Kategorie, in jedem Fall löst First-Match-Wins
   zugunsten der semantisch richtigeren Kategorie auf.
4. **Methoden-Fund (wichtig für alle künftigen Preishistorie-Analysen):**
   `duplicate_detection.normalize_title()` — Basis von `PricePoint.fingerprint` in
   `price_history.jsonl` — ersetzte deutsche Umlaute (ä/ö/ü/ß) durch ein Leerzeichen statt einer
   Transliteration (`"Röhrenfernseher"` → `"r hrenfernseher"`). Jede Fingerprint-basierte
   `evaluate()`-Revalidierung — **einschließlich des bereits produktiven**
   `app/rule_coverage.py::_is_still_valid()` — konnte dadurch nie gegen Umlaut-haltige
   `match`/`require_all_of`-Begriffe matchen (19 von 355 Regeln in 4 Kategorien betroffen:
   `handhelds`, `konsolen_bundles`, `retro_konsolen`, `vintage_elektronik`).
   **Update (Abschnitt 3.12, Commit `c9967ba`): gefixt, aber NICHT rückwirkend** — der Fix wirkt
   nur auf ab jetzt neu geschriebene Zeilen, da `PricePoint` den Rohtitel nicht persistiert und
   sich ein korrekter Fingerprint für bereits gespeicherte Zeilen daher nicht nachträglich
   berechnen lässt. Für `retro_konsolen`/`vintage_elektronik` bleibt eine verlässliche
   historische Revalidierung damit praktisch unmöglich (siehe Abschnitt 3.12, Preishistorie-
   Revalidierung v3).
5. Drei zuvor offene Preishistorie-Entscheidungspunkte geklärt (voller Bericht:
   `tools/ruleset_quality/generated/reports/OFFENE_ENTSCHEIDUNGEN_1_BIS_3_BERICHT.md`):
   - `roehrenfernseher` bleibt eigenständiges `price_history_model` — fachlich klar von
     `crt_profi_monitor` getrennt (Median 20€ vs. 99,50€), 96 Punkte, davon bei Neubewertung mit
     echtem Titel 25/26 rekonstruierbare weiterhin valide (96,2%) — der ursprüngliche "3/96"-Alarm
     war ein Artefakt des Umlaut-Fingerprint-Problems (Punkt 4).
   - Die 3 Orphan-Modelle aus der entfernten Kategorie `spielzeug_bundles` (663 Punkte, seit
     mind. 11 Tagen ohne neuen Zufluss): `lego_bundle` nur teilweise zu `lego_minifiguren`
     migrierbar (nur Minifiguren-Anteil), `playmobil_bundle`/`spielzeug_bundle_sonstige`
     strukturell verifiziert ohne jeden Nachfolger im aktuellen Regelwerk (kein
     `"playmobil"`/`"spielzeug"`-Match-Begriff mehr vorhanden).
   - Von 35 UNCLEAR-gelabelten Fällen (nicht 7, wie eine erste Fingerprint-basierte Analyse
     zeigte) sind 14 verändert/matchen nicht mehr, keiner blockiert eine Revalidierung. Struktur-
     befund: die Regel „Switch Pro Controller“ (`controller.yaml`) hat nur zwei Preisstufen
     (bis 35 €) statt der sonst üblichen drei — Controller über 35 € werden aktuell nicht erfasst.
6. Konkreter, geschichteter Stichprobenplan für eine frische Ground-Truth-Erhebung erzeugt: ein
   251-Listing-Worksheet über alle 19 Kategorien
   (`tools/ruleset_quality/generated/reports/sampling_worksheet_template.csv`), Preisstufen-
   geschichtet, Verdict-Spalten bewusst leer — noch nicht gelabelt.

Alle Berichte unter `tools/ruleset_quality/generated/reports/`: `ABSCHLUSSBERICHT.md` (Phase
19.1–19.5), `FINALE_REVALIDIERUNG_ABSCHLUSSBERICHT.md`, `OFFENE_ENTSCHEIDUNGEN_1_BIS_3_BERICHT.md`.

Keine `app/rules/*.yaml`-, `matcher.py`-, `data/found.json`-, `data/seen.json`- oder
`data/price_history.jsonl`-Änderung in diesem gesamten Arbeitsblock (rein additive, neue Dateien
unter `tools/ruleset_quality/` + `app/tests/test_ruleset_quality_*.py`).

### 3.12 Worksheet-Labeling, Exclude-Fixes, Umlaut-Fix, Datenbereinigung, Revalidierung v3 (2026-08-14, PR #31 + 3 direkte Commits)

Direkte Fortsetzung von Abschnitt 3.11 — vom Stichprobenplan zur tatsächlichen Umsetzung.

**1. KI-gestütztes Labeling (PR #31, `c577207`):** alle 251 Listings aus dem Worksheet bewertet
(`tools/ruleset_quality/worksheet_diagnostics.py` + manuelle inhaltliche Prüfung je Titel/Preis/
Regel-Diagnose) — **217 TRUE_POSITIVE / 21 FALSE_POSITIVE / 13 UNCLEAR**, Precision 91,2%.
Explizit **keine** unabhängige menschliche Verifikation, als eigene Quelle
`ai_assisted_labels_2026-08-14.json` abgelegt.

**2. Drei gezielte Exclude-Fixes aus den FP-Ursachen (PR #31):**

| Fix | Datei | Blast Radius (gemessen) |
|---|---|---|
| `defekte`/`defekter`/`defektes`/`defekten` ergänzt | `_global.yaml` (`exclude_global`) | 23 Punkte im Gesamtkorpus, 0 Negationsfälle |
| `sd karten` (Plural) ergänzt | `handhelds.yaml` | 5 Punkte, 0 Kollisionen |
| `dynabook`/`satellite pro`/`latitude` ergänzt | `office_pc.yaml` (`exclude_category`) | 13 Punkte, 0 Kollisionen |

"tausch" bewusst **nicht** um "tausche" erweitert (Risiko: "Akku tauschen" u. ä. harmlose
Wartungsformulierungen würden fälschlich ausgeschlossen). 9 neue Regressionstests. Zwei weitere
identifizierte Muster (Zubehör/Ersatzteil-vs-Gerät, 6 Fälle; Spieltitel-ohne-Konsole, 5 Fälle,
jetzt auch in `retro_konsolen` bestätigt) **bewusst nicht gefixt** — kein einfaches,
generalisierbares Exclude-Muster identifiziert.

**3. Menschlich verifiziertes Labeling (`dfe3eb9`):** dialogbasiert in Batches à 10. Listings
1–30 einzeln gezeigt und explizit bestätigt (0 Abweichungen vom KI-Vorschlag). Listings 31–251
auf ausdrücklichen Nutzerwunsch ("bestätigt alle batches") **pauschal** übernommen — im
`review_modus`-Feld (`einzeln_bestaetigt`/`pauschal_bestaetigt`) je Eintrag nachvollziehbar
unterschieden. Eigene Quelle `human_verified_labels_2026-08-14.json`, weder KI- noch
Forensik-Quelle überschrieben.

**4. Umlaut-Fingerprint-Fix (`c9967ba`):** siehe Abschnitt 3.11, Punkt 4 (Update). 4 neue Tests.

**5. Freigegebene `lego_bundle`-Migration/-Bereinigung** (Datenänderung, kein Code-Commit): nach
exaktem Dry-Run (Kandidatenzahlen vorab gegen die Freigabe geprüft) und expliziter Freigabe der 5
Ziel-Titel/-Preise:

```text
Migriert:  5 Punkte (2x lego_bundle -> lego_ninjago_bundle, 3x -> lego_minifig_bundle,
           nur das model-Feld geändert)
Gelöscht:  655 Punkte (396x nicht rekonstruierbare lego_bundle, 210x playmobil_bundle,
           49x spielzeug_bundle_sonstige -- beide strukturell ohne Nachfolgeregel)
Erhalten:  3 rekonstruierbare, aber nicht eindeutig migrierbare lego_bundle-Punkte
```

`price_history.jsonl`: 15.554 → 14.899 Zeilen. Nachher-Validierung: valides JSONL, exakte
Zählungen bestätigt, keine anderen Felder/Zeilen verändert.

**6. Kontrollierte Preishistorie-Revalidierung v3** (`dfe3eb9`, vollständig read-only):
Vollkorpus-Revalidierung aller 14.899 Punkte unter Nutzung des Umlaut-Fixes.

- **15 nicht vom Umlaut-Bug betroffene Kategorien** (10.337 Punkte, verlässlich): 91,1%
  unverändert, 4,5% kein Treffer, 4,4% Modell geändert, 0,1% Kategorie geändert — plausibel nach
  über 30 gemergten Fix-PRs. Größte Einzelbewegung: `lego_ninjago_bundle` (60% Modellwechsel,
  erklärt durch seither hinzugekommene granularere Lego-Sub-Modelle wie `lego_sw_clone`/
  `lego_cmf`).
- **4 zuvor betroffene Kategorien** (3.389 Punkte): "kein Treffer"-Rate 35,9% **nicht verlässlich
  interpretierbar**. Für die vom Bug am stärksten betroffenen Kategorien wurde der rekonstruierbare
  Anteil einzeln geprüft: `retro_konsolen` 1 von 714, `vintage_elektronik` 0 von 409,
  `konsolen_bundles` 17 von 59, `handhelds` 7 von 34 — der weit überwiegende Rest bleibt
  unbeurteilbar (Rohtitel nicht persistiert, keine Rekonstruktion möglich).
- **Cross-Validierung gegen die menschlichen Labels** (282 abgeglichene Punkte) bestätigt den
  PR-#31-Fix direkt auf den echten Daten: exakt die 4 gefixten Titel wechseln von
  FALSE_POSITIVE-Match zu kein Treffer; die übrigen 10 von 14 auffindbaren FP-Fällen matchen
  unverändert (bestätigt reale, weiterhin offene strukturelle Muster). Ein Einzelfund:
  `normalize_title()` entfernt Satzzeichen ("M.2" → "m 2"), wodurch ein Fingerprint vereinzelt
  andere Signalwörter als der echte Titel enthalten kann (1 beobachteter Fall:
  `m2_ssd`→`sata_ssd`) — nur beobachtet, nicht verallgemeinert.

**Keine Korrektur-Aktion an `price_history.jsonl` vorgeschlagen oder ausgeführt** — die Datenlage
trägt für die 4 betroffenen Kategorien keine verlässliche Einzelfallentscheidung.

Alle Berichte: `tools/ruleset_quality/generated/reports/WORKSHEET_LABELING_BERICHT_2026-08-14.md`,
`HUMAN_VERIFIED_LABELING_ABSCHLUSSBERICHT_2026-08-14.md`,
`PREISHISTORIE_REVALIDIERUNG_V3_BERICHT_2026-08-14.md`,
`ENTSCHEIDUNGEN_TECHNISCHE_VORBEREITUNG_BERICHT.md`.

### 3.13 Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation gelöst (`a6e8df1`, Datenqualität Punkt 14)

Direkte Fortsetzung von Abschnitt 3.12, Punkt 1 (KI-gestütztes Labeling, root_cause
`zubehoer_statt_geraet`, 6 Fälle). Vier unabhängige Root Causes identifiziert und je gezielt
gefixt, jeweils mit gemessenem Blast Radius (gegen `found.json` + `price_history.jsonl`) und
Kollisionsprüfung:

| Kategorie | Root Cause | Fix | Blast Radius | Kollisionen |
|---|---|---|---|---|
| `controller` | "Lötaufsatz" enthält "aufsatz" nicht als eigenes Wort (Kompositum, `_contains_term()`-Wortgrenzen) | `lötaufsatz`/`lötspitze` als explizite Kompositum-Begriffe ergänzt | 1 | 0 |
| `handhelds` | `ssd`/`festplatte`/`headset`/`kopfhörer`/`in-ear` fehlten als bare Excludes | 5 bare Excludes ergänzt (kein Handheld-Gerät wird selbst so beworben) | 5 | 0 |
| `netzteil` | Regel matcht rein über Watt-Detector (`requirements: min_psu_watt`), `exclude_category` deckte bisher nur komplette Systeme ab | `kabelset` ergänzt | 2 | 0 |
| `konsolen_bundles` | "Joy-Con" ist Zubehör-Produktname, bare Exclude in früherer Session wegen 9 Kollisionen verworfen | neuer kontextbewusster Exclude `joy-con`/`joycon`/`joy con` (`exclude_category_unless_also_contains`, eigene Marker-Liste mit zusätzlich `konsole`) | ~21 blockiert | 0 (Kollisions-Stichprobe: alle bekannten Konsole+Joy-Con-Bundles bleiben erhalten) |

Für `konsolen_bundles` wurden alle 61 "Joy-Con"-Titel aus `found.json` + `price_history.jsonl`
einzeln klassifiziert (nicht nur eine Stichprobe): mit dem neuen Marker `konsole` bleiben alle
bekannten Konsole+Joy-Con-Bundles korrekt erhalten, alle standalone Joy-Con-Sets werden korrekt
blockiert — 0 Kollisionen.

6 neue Regressionstests (`test_zubehoer_ersatzteil_vs_geraet_fix.py`), 190 kategorienbezogene
Tests grün, volle Suite 1315/1315 grün, `rule_analyzer.py` 0 Findings. Ruleset-Signatur geändert
(`98acd6152b61b8bb` → `ee2a6eb114525b55`).

### 3.14 `controller`/`ladekabel`-Restlücke gelöst (`5a01516`, Datenqualität Punkt 5)

Direkte Fortsetzung von Abschnitt 3.13 — nächster, als Einzelschritt geplanter Datenqualitätspunkt
(dokumentierte Phase-15-Restlücke, ursprüngliche Detaildokumentation in `document/PHASE15_*.md`
nicht mehr im Repository vorhanden, daher frische empirische Analyse gegen `found.json` +
`price_history.jsonl`).

**Analysebefund:** der bestehende `exclude_category_unless_preceded_by`-Mechanismus für
`ladekabel` selbst funktioniert korrekt — Standalone-Kabel-Angebote werden blockiert
(`"USB-C Ladekabel für PS5 Controller 3m"` → kein Treffer), echte Bundle-Formulierungen bleiben
erhalten (`"... inkl. Ladekabel"` → matcht weiterhin). Die tatsächliche, real bestätigte Lücke
betraf einen **anderen** Zubehör-Typ — Lade-**Stationen/-Geräte** statt Kabel:

| Titel | Preis | Ursache |
|---|---|---|
| "PS5 Controller USB Dual-Charger Station Neu in OVP" | 6,99€ | `"charger station"` fehlte als Exclude |
| "PowerA Twin Charging Station für PS5 Controller" | 15€ | `"charging station"` fehlte als Exclude |
| "5in1 Switch 1 Aufladegerät für 4 Joycons und 1 Pro Controller" | 9€ (historisch, `price_history.jsonl`) | Kompositum-Lücke — "ladegerät" existierte bereits als Exclude, aber nur als eigenes Wort geprüft (identisches Muster wie "Lötaufsatz", Abschnitt 3.13) |

**Fix:** `exclude_category` in `controller.yaml` um `aufladegerät`/`charging station`/
`charger station` ergänzt — unbedingt (wie bei den bereits vorhandenen `ladestation`/`dock`),
nicht kontextbewusst wie bei `ladekabel`: keine legitime "Controller inkl. Charging
Station"-Bundle-Formulierung im Korpus gefunden. Blast Radius: 3 Treffer, 0 Kollisionen
(inkl. Sicherheitsnetz-Test, dass der bestehende `ladekabel`-Mechanismus unverändert bleibt).

4 neue Regressionstests (`test_controller_ladezubehoer_fix.py`), 73 `controller`-Tests grün,
`rule_analyzer.py` 0 Findings. Ruleset-Signatur geändert (`ee2a6eb114525b55` →
`0d63c38b5dbf261c`).

### 3.15 `RX 7600 XT`/`RX 7600`-Überlappung gelöst + min_vram_gb-Bug bei 4 weiteren GPU-Modellen (`1ac95ef`, Datenqualität Punkt 4)

Direkte Fortsetzung von Abschnitt 3.14. Die ursprünglich dokumentierte Match-Präzedenz-
Überlappung ("rx 7600" fälschlich als match-Begriff der XT-Regel, sodass jede echte Nicht-XT-
Karte als `rx_7600_xt` gespeichert wurde) war bereits vor dieser Session gefixt — siehe
Code-Kommentar bei der Regel "RX 7600 XT" in `gpu.yaml`. Frische Analyse gegen `found.json` +
`price_history.jsonl` zeigte aber weiterhin eine extrem dünne `rx_7600`-Datenlage (nur 1 Punkt).

**Root Cause (neu identifiziert):** die beiden `RX 7600`-Regeln (8GB-Karte) hatten kein eigenes
`min_vram_gb` und fielen daher auf den globalen Default zurück (`_global.yaml`,
`min_vram_gb: 12`). `matcher.py::_vram_gb()` (Regex `(\d{1,2})\s*gb`) erkennt "8GB" im Titel,
nicht aber "8G" — jedes Angebot mit der (weit häufigeren) Schreibweise "8GB" wurde durch den
VRAM-Check fälschlich verworfen (`vram=8 < min_vram=12`). Real verifiziert: identischer Titel,
nur "8G"→"8GB" geändert, Match verschwindet vollständig
(`"... RX 7600 MECH 2X CLASSIC 8GB OC"` kein Treffer, `"... 8G OC"` matcht).

**Wichtiger Zusatzfund, direkt mitgefixt:** derselbe strukturelle Bug betraf 4 weitere
GPU-Modelle ohne eigenes `min_vram_gb`, deren reale VRAM-Größe unter dem globalen 12GB-Default
liegt (real mit demselben "XG"→"XGB"-Test verifiziert):

| Modell | VRAM | Historische Punkte (`price_history.jsonl`) | Aktuell im Live-Korpus (`found.json`) |
|---|---|---|---|
| `rtx_3070` | 8GB | 149 | 16 |
| `rtx_3060_ti` | 8GB | 110 | 12 |
| `rtx_2080_ti` | 11GB | 60 | 3 |
| `rtx_4060` | 8GB | 29 | 4 |

**Fix:** `min_vram_gb: 0` explizit bei allen 5 Modellen (10 Regeln: je Top-Deal/Guter-Preis-Stufe)
in `gpu.yaml` ergänzt. Kein Kollisionsrisiko, da alle match-Begriffe bereits eindeutig
modellspezifisch sind (z.B. `"3060 ti"`/`"rtx 3060 ti"`) — die bestehenden Excludes (RTX 3070 Ti,
RTX 4060 Ti, RTX 2080 Super, jeweils selbst < 12GB VRAM) bleiben unverändert wirksam, per
dediziertem Kollisions-Test verifiziert (`test_benachbarte_modelle_bleiben_ueber_exclude_getrennt`).

10 neue Regressionstests (`test_gpu_rx7600_vram_fix.py`, `test_gpu_low_vram_models_fix.py`), 54
`gpu`-Tests grün, `rule_analyzer.py` 0 Findings. Ruleset-Signatur geändert
(`0d63c38b5dbf261c` → `133dcd1a9f614e7e`).

**Offene Beobachtung (kein aktiver Punkt, keine Evidenz gesammelt):** derselbe min_vram_gb-
Musterbug könnte theoretisch auch außerhalb von `gpu` relevant sein, falls andere Kategorien
VRAM-abhängige Modelle ohne eigenes `min_vram_gb` definieren — nicht geprüft, nur als Hinweis für
künftige Arbeit festgehalten.

### 3.16 Scan-Performance gemessen + Scraping parallelisiert (`6bc0def`)

Erste echte End-to-End-Scan-Performance-Messung (vorher offener Punkt seit Phase 15, siehe
Abschnitt 6). Methodik: Auswertung von **35 bereits im Produktivlog vorhandenen Scan-Läufen**
(`data/gpu_watch.log`, `app.py::run_scan()` protokolliert bereits seit Längerem eine
`📊 Scan-Metriken`-Zeile je Lauf mit Dauer je Phase) — kein synthetischer Benchmark, keine neue
Messung ausgelöst. Voller Bericht: `docs/SCAN_PERFORMANCE_MESSUNG_2026-08-15.md`.

**Ergebnis (Median über 35 Läufe):**

| Phase | Anteil | Auffälligkeit |
|---|---|---|
| Scraping (eBay+Kleinanzeigen+Quoka) | 88,9% | lief seriell, Einzeldauern summierten sich exakt zur Gesamtzeit |
| Persistence | 10,1% (bis 267s) | korreliert r=0,997 mit Anzahl neuer Treffer — atomares Neuschreiben der kompletten `found.json` bei JEDEM einzelnen Treffer (bewusste Crash-Sicherheit, `_save_json()` nutzt Temp-Datei+fsync+os.replace) |
| Matching+Scoring, Price-Stats, Notification | < 0,5% | unauffällig |

Gesamtdauer median 28,5 Minuten bei konfiguriertem `SCAN_INTERVAL_MINUTES=10` — die reale
Scan-Kadenz lag damit bei ~28-31 statt der beabsichtigten 10 Minuten.

**Größter Hebel direkt umgesetzt:** die drei Scraper-Plugins (discover_scrapers()) liefen bisher
in einer einfachen `for`-Schleife seriell. Da es unabhängige HTTP-Ziele ohne geteilten Zustand
sind (kein gemeinsames `requests.Session`-Objekt, kein geteilter Rate-Limiter/Circuit-Breaker —
jeweils lokale Funktionsvariablen, verifiziert in allen drei `scrapers/*.py`-Modulen), wurde die
Schleife durch `concurrent.futures.ThreadPoolExecutor` (ein Worker je entdecktem Plugin) ersetzt.
Ergebnisse werden weiterhin ausschließlich im Hauptthread in `raw` gemergt (kein gleichzeitiges
Schreiben aus mehreren Threads), das Scraper-Plugin-Protocol (`scrapers/base.py`) bleibt
unverändert — es ändert sich nur, WIE `app.py` die Plugins aufruft.

**Zusätzlich behobenes Robustheitsproblem:** vorher gab es **kein** `try/except` um
`plugin.search()` — ein Fehler in einer Quelle riss den kompletten Scan in den äußeren
`except`-Block von `run_scan()`, wodurch auch die Ergebnisse der anderen beiden, bereits
erfolgreichen Quellen verworfen wurden. Jetzt wird jede Quelle einzeln abgefangen (identisches
Prinzip wie bereits in `scrapers/registry.py::discover_scrapers()` für die Plugin-Discovery
selbst: "ein fehlerhaftes Plugin darf nicht alle anderen Quellen lahmlegen").

**Bewusst nicht verändert:** die Persistence-Phase (10,1%, Crash-Sicherheits-Tradeoff) — ein
Batching würde die Crash-Sicherheits-Garantie abschwächen (mehr potenziell verlorene Treffer bei
einem Absturz zwischen zwei Batches) und ist eine eigene Design-Entscheidung, kein reiner
Performance-Fix.

Fehlenden Quoka-Mock in `app/tests/test_app_deal_cleanup.py` nachgetragen (bestehende
Testlücke — der Test rief `run_scan()` auf, ohne alle drei Scraper zu mocken, direkt an diesem
Codepfad hängend). 3 neue Regressionstests (`test_app_parallel_scraping.py`): Merge aller drei
Quellen, Fehler-Isolation (eine simulierte `RuntimeError` blockiert die anderen Quellen nicht
mehr), und ein Timing-Nachweis echter Parallelität (3× 0,15s-Sleep liefen in < 0,4s statt seriell
≥ 0,45s). Volle Suite **vom Nutzer lokal ausgeführt und verifiziert: 1332/1332 grün (76,41s)**.
Ruleset-Signatur unverändert (reiner Python-Code, keine `app/rules/*.yaml`-Änderung).

**Rechnerisches Potenzial (aus den 35 historischen Läufen abgeleitet, NICHT durch einen
tatsächlichen Nach-Fix-Scan verifiziert):** Scraping-Zeit sinkt von der Summe aller drei Quellen
(median 1522,3s) auf die langsamste Einzelquelle (Kleinanzeigen, median 548,2s) — rechnerisch
**~57% kürzere Gesamtdauer** (28,5 → ~12,2 Minuten). Die reale Wirkung ist erst nach Deployment
(`docker compose up --build -d`) und einer erneuten Log-Auswertung nachweisbar.

### 3.17 Persistence-Batching (`00a4053`)

Direkter Folgeschritt zu Abschnitt 3.16. **Korrektur der ursprünglichen Analyse:** der
dominante Kostentreiber der Persistence-Phase war nicht primär `found.json` (2,7 MB), sondern
vor allem **`seen.json` — 16,7 MB, 47.355 Einträge** —, das bisher bei **jedem einzelnen neu
gesehenen Angebot** (`already_seen == False`, nicht nur bei echten Regel-Treffern) komplett neu
geschrieben wurde (`_save_json()`, atomar: Temp-Datei + `fsync()` + `os.replace()`). Das erklärt
die in Abschnitt 3.16 gemessene Korrelation (r=0,997) korrekt mit der `dedupliziert`-Zahl (neu
gesehene Angebote je Scan), nicht mit `new_hits` (tatsächliche Regel-Treffer, eine kleinere
Teilmenge).

**Fix:** neue Konstante `PERSIST_BATCH_INTERVAL_SECONDS` (Default 5s, per `.env` konfigurierbar)
+ ein gemeinsamer Batching-Helper (`_persist_seen_and_found_if_due()`) ersetzen beide bisherigen
Sofort-Speicherstellen (`seen.json` bei neu gesehenen Angeboten, `found.json` bei neuen
Treffern) — schreibt beide Dateien gemeinsam, höchstens einmal je Intervall. Der finale,
unbedingte Save am Scan-Ende (unverändert) bleibt die eigentliche Daten-Absicherung.

**Tradeoff (bewusst, wie in Abschnitt 3.16 angekündigt):** vorher 0 Sekunden Risikofenster bei
einem Absturz zwischen "als gesehen markiert" und "persistiert", jetzt bis zu
`PERSIST_BATCH_INTERVAL_SECONDS` (5s) — bei einer Matching-Phase von median nur 5,9s
Gesamtdauer ein kleines, begrenztes Fenster, kein Verzicht auf die Crash-Sicherheit an sich.

2 neue Regressionstests (`test_app_persistence_batching.py`), darunter ein expliziter
Korrektheitsnachweis: mit künstlich hochgesetztem Intervall (999s) finden **0
Zwischen-Speicherungen** während eines Scans mit 6 echten Treffern + 6 weiteren neu gesehenen
Angeboten statt (vorher: 12 einzelne Saves), trotzdem sind am Scan-Ende alle 6 Treffer und alle
12 gesehenen URLs korrekt persistiert — kein Datenverlust. Volle Suite **1334/1334 grün** (vom
Nutzer lokal verifiziert, 76,51s). Ruleset-Signatur unverändert (reiner Python-Code).

**Rechnerisches Potenzial (nicht durch einen tatsächlichen Nach-Fix-Scan verifiziert):**
Persistence-Zeit sollte von bis zu 267s (median 173,6s) auf wenige einzelne Batch-Schreibvorgänge
plus den finalen Save sinken — Größenordnung Sekunden statt Minuten. Wie bei Abschnitt 3.16 ist
die reale Wirkung erst nach Deployment und erneuter Log-Auswertung nachweisbar.

### 3.18 Scraping-Parallelisierung + Persistence-Batching: reale Wirkung verifiziert

Direkter Abschluss von Abschnitt 3.16/3.17. Erster echter Produktiv-Scan nach Deployment
(`docker compose up --build -d`), vom Nutzer aus dem Log geteilt (2026-08-14 23:36:59 UTC+2):

```text
✅ Scan komplett: 304 Treffer (von 14206 geprüften Angeboten).
📊 Scan-Metriken: Gesamtdauer=746.44s, Scraping={'ebay': 444.532, 'kleinanzeigen': 535.931,
'quoka': 544.318}, gescrapt=14206, dedupliziert=9135, Matching+Scoring=166.51s,
Price-Stats=0.27s, Persistence=19.10s, Notification=14.22s
```

**Scraping läuft nachweislich parallel:** die drei Einzeldauern summieren sich seriell auf
1524,8s, aber Gesamtdauer minus allem anderen (Matching+PriceStats+Persistence+Notification =
200,1s) ergibt eine tatsächliche Scraping-Wandzeit von nur 546,3s — praktisch identisch mit der
langsamsten Einzelquelle (Quoka, 544,3s, nur ~2s Overhead über dem theoretischen Optimum).

**Gesamtdauer: 746,44s (12,4 min) statt Median 1712s (28,5 min) — 56,4% schneller**, fast exakt
die in Abschnitt 3.16 vorhergesagten ~57%. Bei konfiguriertem `SCAN_INTERVAL_MINUTES=10` ist die
reale Kadenz jetzt nur noch ~1,24× statt ~2,85× langsamer als beabsichtigt.

**Persistence: 19,10s statt Median 173,6s — 89% schneller**, trotz eines für diesen Scan
ungewöhnlich hohen `dedupliziert=9135` (normaler Bereich über die 35 zuvor ausgewerteten Läufe:
186–642).

**Eingeordnete Auffälligkeit (kein neues Problem):** `Matching+Scoring=166,51s` liegt deutlich
über dem historischen Median (~5,9s), korreliert aber plausibel mit dem stark erhöhten
`dedupliziert`-Wert. Wahrscheinlich ein einmaliger Übergangseffekt: die im Laufe dieser Session
mehrfach geänderte Ruleset-Signatur (`98acd...`→`ee2a6...`→`0d63c...`→`133dcd...`) lässt
`needs_reevaluation()` für sehr viele bereits bekannte `seen.json`-Einträge auf einmal "True"
zurückgeben (sie fallen zurück in die volle Matching-Schleife), zusätzlich zur direkt vorher im
selben Log geloggten Bereinigung (7128 delistete Alt-Einträge entfernt). Beide Effekte erklären
den erhöhten `dedupliziert`-Wert plausibel, ohne dass Matching+Scoring oder Persistence dabei
ineffizienter geworden wären (beide skalieren erwartbar mit der Ereigniszahl). Empfehlung: einen
der nächsten 1-2 Scans gegenchecken, sobald sich `dedupliziert` wieder im Normalbereich
einpendelt, für eine "steady state"-Bestätigung.

---

### 3.19 Kategorie-Audit (read-only) + Live-Fehltreffer-Fixes über 3 Kategorien + Preis-Guard

**Teil A — Kategorie-Audit (read-only, keine Änderung).** Vollständiger Abgleich: `app/rules/*.yaml`
(`category`/`label`-Felder) ↔ `matcher.py::_load_rules_from_dir()`/`categories/registry.py`
(dynamische Discovery, kein hartcodierter Namensraum) ↔ `api/deals.py`/`api/status.py`
(`all_categories`/`category_labels` ausschließlich aus `rules_cfg`) ↔ `templates/index.html`
(`SERVER_CATEGORIES`/`SERVER_CATEGORY_LABELS`, generisches KPI-Kachel-Rendering) ↔
`category_validation.py` (Revalidierung ohne eigenen Kategorienamensraum) ↔ `found.json`
(2500 Einträge). Ergebnis: `comm`-Diff zwischen YAML-Kategorien und tatsächlich in `found.json`
vorkommenden Werten ist **leer** — exakte 1:1-Übereinstimmung, 0 Schreibfehler/Schreibweisen-
Inkonsistenzen/fehlende oder doppelte Kategorien. Einziger Nebenbefund: `price_history.jsonl`
enthält weiterhin 8 Zeilen mit `category: "spielzeug_bundles"` (entfernte Kategorie) —
CLAUDE.md Abschnitt 5 dokumentiert „663" Orphan-Datenpunkte, die aktuelle Messung zeigt nur 8;
Diskrepanz nur beobachtet, nicht geklärt, keine Aktion ohne separaten Auftrag.

**Teil B — Nutzer-gemeldete Live-Fehltreffer.** Ausgehend von 7 vom Nutzer gemeldeten, aktuell im
Dashboard sichtbaren Fehltreffern wurde gegen zwei Quellen geprüft: (1) die 97 CRITICAL-Fälle aus
dem Regression-Benchmark gegen den historischen Vor-Audit-Snapshot
(`tools/ruleset_quality/generated/reports/benchmark_historical_forensics_baseline.json`), (2)
gezielte `evaluate()`-Traces gegen `found.json`.

*97 CRITICAL-Fälle einzeln klassifiziert:* 96 bereits korrekt — 64× dokumentierte, vom Nutzer
freigegebene `office_pc`-Notebook-Exclusion (siehe `office_pc.yaml`-Kommentarblock, "FIX
(Cross-Category Routing Audit ... auf explizite Nutzer-Freigabe umgesetzt)"), 2×
`autoradio_opel_corsa`-OEM-Teile-Exclusion, 6× `gaming_pc`-Notebook-Exclusion (identisches,
bereits dokumentiertes Muster), Rest zu Recht ausgeschlossenes Zubehör/Fotos/Spiele-Konvolute.

**1 echter Bug gefunden:** `vintage_elektronik.yaml` — bare `"fernbedienung"` (sowohl in
`exclude_category` als auch redundant in den drei `exclude:`-Listen der Röhrenfernseher-Regeln)
blockierte echte Markenverstärker/-Receiver/-Fernseher, die ihre mitgelieferte Fernbedienung als
Ausstattungsmerkmal nennen ("Pioneer Stereo Verstärker mit Fernbedienung", "Onkyo A-9155 ...
mit Fernbedienung", "Grundig Röhrenfernseher inkl Fernbedienung" u.a.). Der direkt benachbarte
Kommentar zu `"netzkabel für"` in derselben Datei hatte das identische Bundle-vs-Standalone-
Problem bereits erkannt ("nicht bare 'netzkabel' -- ein echtes Komplettgerät könnte 'inkl.
Netzkabel' bewerben"), aber inkonsequent nicht auf `"fernbedienung"` angewendet.

**Fix:** `"fernbedienung"` aus `exclude_category` (Kategorie-Ebene) sowie aus den drei
`exclude:`-Listen der Röhrenfernseher-Regeln entfernt, stattdessen neuer
`exclude_category_unless_preceded_by`-Eintrag (identischer, bereits in
`controller.yaml`/`ladekabel` etablierter Mechanismus — Standalone-Vorkommen bleiben
ausgeschlossen, ein Bundle-Konnektor `"mit"/"inkl."/"inkl"/"+"/"und"/"sowie"` unmittelbar davor
lässt die Regel wieder matchen). Blast Radius: ≥8 real betroffene Markentitel in
`price_history.jsonl`, 0 Kollisionen mit den 4 verbliebenen echten Standalone-
Fernbedienungs-Zubehörtiteln. Messbar verifiziert über Regression-Benchmark: CRITICAL-Fälle
97 → 96, stabile `TRUE_POSITIVE`-Transitionen 2090 → 2091 (exakt der eine erwartete Fall).

*4 gemeldete Live-Fehltreffer geprüft, dabei 4 weitere ungemeldete im selben Regelbereich
gefunden* (alle über direkte `evaluate()`/`is_still_valid_category()`-Traces gegen `found.json`
bestätigt, nicht nur historisch):

- **`handhelds.yaml`**: `"module"` (Plural von bereits vorhandenem `"modul"`, Wortgrenzen-
  bedingte Lücke, identisches Muster wie `"aufsatz"`/`"lötaufsatz"`) ergänzt — fixt "Nintendo DS
  und 3DS Spiele (AUSWAHL) Module - Sammlung Konvolut - 2DS DSi XL" (39€, war live sichtbar).
  Bewusst **nicht** `"spiele"` (Plural von `"spiel"`) ergänzt: Blast-Radius-Check gegen
  `found.json` zeigt 5 echte Konsole+Spiele-Bundles ("Nintendo 3DS XL ... mit Spielen"/"...
  SPIELE ZUSÄTZLICH"), die dadurch fälschlich ausgeschlossen würden — real verifizierter
  Unterschied zwischen den beiden Pluralformen.
- **`konsolen_bundles.yaml`**: `"zubehör set"` (Leerzeichen-Variante; nur `"zubehör-set"`/
  `"zubehörset"` waren bereits gelistet) — fixt 2 Fälle ("12-in-1 Sport Zubehör Set für Nintendo
  Switch / OLED", "Nintendo Switch Sports Zubehör Set für Familienspaß"). `"mainboard"`/
  `"motherboard"` (bare, identisches, bereits in `office_pc.yaml`/`gaming_pc.yaml`/
  `notebook_resell.yaml` etabliertes Muster) — fixt "Sony Playstation 4 Pro & PS4 Mainboard Pin
  Buchse / Stecker abgerissen Reparatur" (39€, **Top-Deal-Rating**, ein defektes Ersatzteil ohne
  funktionsfähige Konsole).
- Blast Radius aller 4 Ergänzungen gegen den vollen `found.json`-Korpus: 0 Kollisionen. Fresh
  Baseline-Regeneration (`tools/ruleset_quality/baseline.py`) bestätigt: sichtbare Einträge
  2480 → 2476 (exakt die 4 jetzt korrekt ausgeblendeten Fehltreffer).

**Bewusst NICHT gefixt** (Analyse gegeben, keine Umsetzung ohne separate Freigabe/Datenbasis —
CLAUDE.md Regel 3/4/9: Protected-Core-Änderungen und Preisgrenzen brauchen Datenbasis bzw.
Freigabe, geteilte Regelgruppen über mehrere Rules hinweg sind ein größeres, eigenständiges
Risiko als additive Excludes):

1. **„Xenoblade Chronicles für Nintendo New 3DS OVP"** (`handhelds`, 18€, war live sichtbar) —
   Spieltitel ohne jedes generische Signalwort ("spiel"/"modul"); `require_all_of`-Gruppe 2
   matcht nur über den reinen Plattformnamen "New 3DS". Ein Fix bräuchte entweder eine
   Spieltitel-Blacklist (keine belastbare Datenbasis, fragil) oder einen **neuen
   Matcher-Mechanismus** — die Umkehrung des bestehenden
   `exclude_category_unless_preceded_by` (exclude NUR wenn ein Begriff wie "für" unmittelbar
   VOR dem Plattformnamen steht) existiert in `matcher.py` noch nicht und wäre eine Änderung an
   einem geschützten Kernsystem, verdient einen eigenen, dedizierten Schritt.
2. **„pro"-Kollision in `konsolen_bundles.yaml`** (3 bestätigte Live-Fälle: "Snakebyte PS4
   Wireless Pro-Controller PC Bayern München" 52€/Top-Deal, "Astro MixAmp Pro TR Gen 4 für
   PS4/PC – Audio-Verstärker" 50€/Top-Deal, "Chin Fai „The Shark" Vertical Stand für PS4 / PS4
   Slim / PS4 Pro" 15€/Top-Deal) — bare `"pro"` als Alternative in der für **6 PS4-Regeln**
   geteilten `require_all_of`-Gruppe 2 kollidiert mit Produktnamen, die "Pro" enthalten, ohne
   eine PS4-Pro-Konsole zu sein. Eine Phrasen-Verengung auf `"ps4 pro"`/`"playstation 4 pro"`
   hätte den dritten Fall ("Sony Playstation 4 Pro & PS4 Mainboard...") NICHT gelöst (die Phrase
   steht dort bereits explizit, gefixt stattdessen über den separaten `"mainboard"`-Exclude oben)
   — eine vollständige Lösung bräuchte eine Restrukturierung der geteilten Gruppe, die bereits
   bestehende, eingespielte Tests berührt (`test_konsolen_bundles_plattform_referenz_fix.py`,
   u.a. `test_pro_controller_im_echten_bundle_matcht_weiterhin`,
   `test_pro_slim_ohne_zubehoerwort_matcht_weiterhin`).
3. **`"netzteil"` als bewusstes Positivsignal in `retro_konsolen.yaml`** (2 Fälle: "⚡ PS2
   Netzteil Original Playstation 2 Slim 8,5V Stromkabel Netzkabel Getestet⚡" 17,95€/Top-Deal,
   "Nintendo 64 Netzteil" 30€/Top-Deal) — anders als in `handhelds.yaml`/`konsolen_bundles.yaml`
   (wo `"netzteil"` ein Exclude ist) wurde es hier **absichtlich** als Vollständigkeits-
   Positivsignal in eine für 6 Sony-/Nintendo-Regeln geteilte `require_all_of`-Gruppe
   aufgenommen (Kommentar dort: "Positiv-Begriffe (konsole/gerät/system/controller/netzteil)").
   Eine Änderung wäre ein Architektur-Redesign der geteilten Gruppe (z.B. Aufsplitten in
   Pflicht- vs. Bonus-Signal), kein additiver Fix — verdient eigene Analyse mit Blast-Radius-
   Messung gegen alle 6 betroffenen Regeln.

**Teil C — GPU-Preis-0€-Diagnose.** "ZOTAC Gaming GeForce RTX 4060 Spider-Man Edition OC 8GB
GDDR6" für 0€ gemeldet (`deal_score: 90`, `deal_rating: "Top-Deal"`,
`top_deal_discount_pct: 100.0`, `estimated_margin_eur: 231.38`). **Root Cause gefunden:** kein
Matcher-/Kategorie-Bug, sondern ein **Quoka-seitiger Preis-Parsing-Defekt** —
`scrapers/quoka.py::_price_to_float()` liefert vereinzelt `0.0` statt `None` (die eigentliche
HTML-Ursache auf Quokas Seite wurde nicht weiter untersucht, dafür wäre Live-Zugriff auf die
aktuelle Seite nötig). Bestätigt über den vollen Datenbestand: **5 Punkte in
`price_history.jsonl`**, **2 aktuell in `found.json`**, **ausschließlich** `source="Quoka"` (RTX
4060, 2× MacBook Pro M3/M4, 1× iPhone 16 Pro Max) — 0 Fälle bei Kleinanzeigen/eBay.

**Fix (Symptom, auf ausdrücklichen Nutzerwunsch):** `app.py::run_scan()` Zeile ~605 überspringt
Items mit `price<=0` jetzt genau wie bereits zuvor `price is None` (bestehender Skip-Mechanismus
um eine Bedingung erweitert, keine neue Logik, kein neuer Code-Pfad). Schwelle bewusst `<=0`
statt einer erfundenen Mindestsumme (z.B. "mind. 5€") — einziger durch echte Daten belegter
Fehlerwert (CLAUDE.md Regel 4: keine Preisgrenzen-Änderung ohne Datenbasis); ein
7,99€-Legitimtreffer aus Abschnitt 3.13 ("FIFA & F1 Spiele Paket Bundle") zeigt, dass eine höhere
Pauschalgrenze echte Deals gekostet hätte. **Python-Änderung → Rebuild nötig**
(`docker compose up --build -d`), anders als die drei YAML-Fixes aus Teil B, die volume-gemountet
sofort wirken.

**Tests:** 15 neue Regressionstests
(`test_vintage_elektronik_fernbedienung_kontext_fix.py` 4,
`test_handhelds_module_plural_fix.py` 3,
`test_konsolen_bundles_zubehoer_set_mainboard_fix.py` 5, `test_app_zero_price_skip.py` 3).
Zielgerichtete Suiten: `pytest app/tests/ -k "vintage or handheld or konsolen_bundle or app_"` →
230 passed. `pytest app/tests/test_app_*.py` → 90 passed. Volle Suite **1337/1337 grün** (vom
Nutzer lokal verifiziert, 80,33s). `rule_analyzer.py`: 0 Findings gegen das geänderte Ruleset.
Ruleset-Signatur geändert: `133dcd1a9f614e7e` → `b863e724db9b393c`.

---

### 3.20 „pro"-Kollision in `konsolen_bundles.yaml` gelöst (zuvor in Abschnitt 3.19 zurückgestellt)

Vertiefte Root-Cause-Analyse der drei in Abschnitt 3.19 zurückgestellten Live-Fehltreffer.
**Korrektur der dortigen Einschätzung:** die betroffenen `require_all_of`-Gruppen werden von
**2** Regeln geteilt (`"PS4 Slim / Pro Bundle ★ Top-Deal"`/`"👍 Guter Preis"`,
`price_history_model: "konsole_ps4_bundle"`), nicht wie zunächst vermutet 6 — verifiziert über
`grep -n "konsole_ps4_bundle" app/rules/konsolen_bundles.yaml`. Wichtiger: alle drei Fälle hatten
**unabhängige, einzeln additiv lösbare Ursachen**, keine gemeinsame strukturelle Kollision:

1. **„Snakebyte PS4 Wireless Pro-Controller PC Bayern München"** (52€, Top-Deal): es existierte
   bereits ein produktiver `exclude_category_unless_preceded_by`-Eintrag für `"pro controller"`
   (Leerzeichen, Konnektor-Anker `*bundle_konnektoren`, laut Kommentar in `konsolen_bundles.yaml`
   "0 Kollisionen im vollständigen 195-Titel-Test" einer früheren Session, Zeile 340-356). Er
   greift aber NICHT bei der Bindestrich-Schreibweise `"Pro-Controller"` — verifiziert direkt über
   `matcher._contains_term()`: `_contains_term(title, "pro controller")` → `False`,
   `_contains_term(title, "pro-controller")` → `True`. Identisches Kompositum-/Schreibweisen-
   Problem wie `"zubehör-set"`/`"zubehörset"`/`"zubehör set"` (Abschnitt 3.19). **Fix:**
   `"pro-controller"` als Geschwister-Eintrag mit demselben Anker `*bundle_konnektoren` ergänzt —
   erbt strukturell dieselbe 0-Kollisionen-Eigenschaft, da ausschließlich die zusätzliche
   Bindestrich-Schreibweise erfasst wird, das bestehende `"pro controller"` (Leerzeichen)
   unverändert bleibt.
2. **„Astro MixAmp Pro TR Gen 4 für PS4/PC – Audio-Verstärker"** (50€, Top-Deal): enthält
   `"controller"` gar nicht, ist ein Audio-Verstärker-Produktname (Astro MixAmp, bekannte
   Gaming-Headset-Verstärkerlinie). **Fix:** bare `"mixamp"`-Exclude in `exclude_category`
   (analog zu `"modchip"`/`"scuff"` — eindeutiger Markenname, kein Bundle-Kollisionsrisiko;
   Blast Radius: 3 Treffer in `found.json`+`price_history.jsonl`, alle eindeutig Zubehör).
3. **„Chin Fai „The Shark" Vertical Stand für PS4 / PS4 Slim / PS4 Pro"** (15€, Top-Deal):
   matcht über `"slim"`+`"pro"` als reine Plattform-Kompatibilitätsangaben (Konsolenständer,
   kompatibel mit mehreren PS4-Varianten, keine davon wird verkauft). **Fix:** neuer
   `exclude_category_unless_also_contains`-Eintrag für `"vertical stand"` mit den Bundle-
   Konnektoren (`"mit"`/`"inkl."`/`"inkl"`/`"+"`/`"und"`/`"sowie"`) als erlaubte Kontextliste.
   Bewusst **nicht** über `exclude_category_unless_preceded_by` (Adjazenz-Check): der einzige
   real bestätigte Bundle-Kollisionsfall in `price_history.jsonl` — "PS4 Slim inkl 1 Controller
   Vertical Stand und Lampe" (80€) — hat den Konnektor `"inkl"` NICHT unmittelbar vor
   `"Vertical Stand"` stehen (dazwischen "1 Controller"); ein Adjazenz-Check hätte diesen echten
   Treffer fälschlich blockiert. Die titelweite Präsenzprüfung (`_any_conditional_exclude_
   presence()`, bereits produktiv für `"gehäuse"`/`"joy-con"` in dieser Datei) erhält ihn korrekt,
   da der Titel `"inkl"` UND `"und"` irgendwo enthält.

**Wichtige Korrektur eines zunächst erwogenen, breiteren Fixes:** vor der finalen Lösung wurde ein
generischerer Ansatz erwogen (bare `"pro controller"`/`"pro-controller"`-Exclude ohne
Konnektor-Bedingung, um das Problem "an der Wurzel" zu lösen). Ein systematischer Blast-Radius-
Check gegen den **vollen** `price_history.jsonl`-Korpus (27 Fundstellen mit `category:
"konsolen_bundles"` und `"pro controller"`/`"pro-controller"` im Fingerprint, nicht nur die
zuvor referenzierten 195 Titel) zeigte **~5-7 reale Kollisionen** mit echten Konsole+Pro-
Controller-Bundles, die informell OHNE direkt vorangestellten Konnektor formuliert sind (z.B.
"Nintendo Switch 2 Konsole 7 Spiele Pro Controller", "Sony PS4 Konsole 500GB/1TB/2TB Slim Pro
Controller PlayStation 4" — Komma-/Aufzählungsstil statt "mit"/"inkl."). Dieser breitere Fix
wurde **verworfen** — der tatsächlich umgesetzte, engere Fix (nur die fehlende Bindestrich-
Schreibweise ergänzen, bestehenden Konnektor-Mechanismus unverändert lassen) hat dieses
Kollisionsrisiko nicht, weil er ausschließlich die bereits durch den Konnektor-Mechanismus
geschützte Menge um eine Schreibweisen-Variante erweitert, ohne die Schutzbedingung selbst zu
lockern.

6 neue Regressionstests (`test_konsolen_bundles_pro_kollision_fix.py`), inkl. expliziter
Kollisionsschutz-Tests für die beiden zunächst gefährdeten echten Bundles ("Nintendo Switch
Konsole mit Pro Controller & 5 Spielen", "PS4 Slim inkl 1 Controller Vertical Stand und Lampe").
Zielgerichtete Suite: `pytest app/tests/ -k "konsolen_bundle"` → 67 passed (inkl. der zuvor
kritischen, bereits bestehenden `test_pro_controller_im_echten_bundle_matcht_weiterhin`/
`test_pro_slim_ohne_zubehoerwort_matcht_weiterhin`/`test_pro_controller_bundle_mit_plus_bleibt_
unveraendert`). Volle Suite **1355/1355 grün** (vom Nutzer lokal verifiziert, 85,27s).
`rule_analyzer.py`: 0 Findings. Ruleset-Signatur geändert: `b863e724db9b393c` →
`6266e4a437c1fbc4`. Reiner YAML-Fix, kein Rebuild nötig (volume-gemountet).

---

## 4. Datenqualität

Der aktuelle Datenqualitätsstand ist technisch deutlich ausgebaut, aber noch nicht vollständig abgeschlossen.

Phase 15 dokumentierte:

- `price_history.jsonl`: 9.753 Datenpunkte
- 113 von 135 aktiven `price_history_model`-Gruppen mit mindestens einem Datenpunkt
- 22 Regeln ohne Daten, überwiegend plausible Nischen-/High-End-Varianten
- 3 Orphan-Modelle aus der nicht mehr vorhandenen Kategorie `spielzeug_bundles` mit zusammen 663 historischen Datenpunkten
- eine damalige Gesamt-False-Positive-Rate von 17,2 % in der Coverage-Analyse; diese Zahl ist wegen Alt-/Neudatenvermischung ausdrücklich nur als Beobachtungswert zu verstehen

Der anschließende PR-#6-Audit adressiert bereits mehrere konkrete False Positives; der systematische Active-False-Positive-Audit (Abschnitt 3.9, PR #11–#25) hat diese Arbeit auf **alle 19 Kategorien** ausgeweitet und dabei 113 weitere reale Fehltreffer-Titel beseitigt (u.a. den mit 40 Titeln größten Einzelfund des Projekts in `vintage_elektronik`). Der Cross-Category-Routing-Audit (Abschnitt 3.10) hat zwei weitere Fehlrouting-Fixes ergänzt. Das neue Ruleset-Qualitätssystem (Abschnitt 3.11) liefert erstmals einen **reproduzierbaren** Regressionsvergleich statt punktueller Audits — Ergebnis: 93,1% TP-Stabilität, keine unbestätigten Regressionen.

`price_history.jsonl` ist nach der freigegebenen `lego_bundle`-Bereinigung (Abschnitt 3.12) auf **14.899 Datenpunkte** (vorher 15.554, 655 gelöscht/5 migriert). **19** `price_history_model`-Gruppen ohne jeden Datenpunkt (unverändert seit Abschnitt 3.11). Die 3 Orphan-Modelle aus `spielzeug_bundles`: **erledigt** — 5 Punkte migriert, 655 gelöscht, 3 bewusst erhalten (Abschnitt 3.12, Punkt 5). Modelle mit auffällig wenigen validen Punkten nach simulierter Revalidierung (nur Beobachtung, keine Aktion): `roehrenfernseher` (96 Punkte, 96,2% weiterhin valide), `rx_7600_xt` (12 → 4 valide), `gaming_laptop_rtx3060`/`rtx4060` (34 → 5 bzw. 20 → 5).

**Wichtige methodische Einschränkung (aktualisiert, Abschnitt 3.12):** der Umlaut-Fingerprint-Bug ist im Code behoben (`c9967ba`), aber **nicht rückwirkend** — `app/rule_coverage.py::_is_still_valid()` und jede fingerprint-basierte Revalidierung bleiben für **historische** Zeilen in `handhelds`/`konsolen_bundles`/`retro_konsolen`/`vintage_elektronik` strukturell unzuverlässig, da der Rohtitel nie persistiert wurde und sich nicht rekonstruieren lässt (Preishistorie-Revalidierung v3, Abschnitt 3.12, Punkt 6: für `retro_konsolen`/`vintage_elektronik` praktisch 0% der betroffenen Punkte beurteilbar). Ab jetzt neu geschriebene Zeilen sind korrekt.

### Offene Datenqualitätsfragen

- historische Alt-Kontamination in `price_history.jsonl`
- 19 Regeln ohne Produktivdaten weiter beobachten
- `RX 7600 XT`/`RX 7600`-Überlappung: **erledigt** (Abschnitt 3.15) — eigentliche Ursache war ein min_vram_gb-Bug, nicht die längst gefixte Match-Präzedenz; 4 weitere GPU-Modelle mit demselben Bug mitgefixt. `controller`-`ladekabel`-Exclude: **erledigt** (Abschnitt 3.14) — Lücke betraf Lade-Stationen/-Geräte, nicht den Kabel-Mechanismus selbst
- 9 Muster / 27 Titel aus dem Active-False-Positive-Audit (Abschnitt 3.9) bewusst zurückgestellt (P1/P2) — vollständige Liste: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`
- Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation: **erledigt** (Abschnitt 3.13) — 4 gezielte Exclude-Fixes
- Spieltitel-ohne-Konsole (5 Fälle, jetzt auch in `retro_konsolen` bestätigt) — weiterhin offen; Abschnitt 3.19 bestätigt einen weiteren Live-Fall ohne jedes generische Signalwort ("Xenoblade Chronicles für Nintendo New 3DS") — bräuchte einen neuen Matcher-Mechanismus, nicht nur einen weiteren Exclude
- Umlaut-Fingerprint-Problem: **Code behoben, aber nicht rückwirkend** (Abschnitt 3.12, Punkt 4/6) — dauerhafte, dokumentierte Einschränkung für historische Daten in 4 Kategorien
- Regel „Switch Pro Controller“ hat nur zwei statt drei Preisstufen — explizit auf Nutzerentscheidung **nicht** erweitert (keine belastbare Datenbasis)
- `normalize_title()` entfernt Satzzeichen (z.B. "M.2" → "m 2"), 1 beobachteter Fehlklassifikationsfall (`m2_ssd`→`sata_ssd`) — nur beobachtet, nicht verallgemeinert
- „pro"-Kollision in `konsolen_bundles`: **erledigt** (Abschnitt 3.20) — 3 unabhängige, additiv lösbare Ursachen statt einer strukturellen Gruppen-Kollision (Bindestrich-Kompositum-Lücke, Markenname „MixAmp", Plattform-Kompatibilitätsliste bei „Vertical Stand")
- `"netzteil"` als bewusstes Positivsignal in einer für 6 `retro_konsolen`-Regeln geteilten Gruppe (Abschnitt 3.19, 2 bestätigte Live-Fälle) — Architektur-Redesign nötig, kein additiver Fix, zurückgestellt
- Quoka-Preis-Parsing-Defekt (`scrapers/quoka.py::_price_to_float()` liefert vereinzelt `0.0` statt `None`): Symptom gefixt (Abschnitt 3.19, `price<=0`-Guard), HTML-seitige Ursache nicht untersucht

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

Zusätzlich, außerhalb dieser Produktionskette (read-only, kein Import durch `app.py`):
`tools/ruleset_quality/` — Regression-Benchmark/Qualitätssystem, siehe Abschnitt 3.11.

### Grundprinzipien

- YAML ist Single Source of Truth für Kategorien und viele Matching-/Scoring-Regeln.
- Scraper sind über Registry/Plugin-Strukturen entkoppelt.
- Kategorien sind dynamisch ladbar.
- Detectoren sind modular registriert.
- Preisstatistik und Resale-Schätzung sind getrennt.
- Notification-Gating bleibt von Preis-/Resale-Experimenten getrennt.
- Änderungen werden bevorzugt klein und regressionsgetestet umgesetzt.
- Diagnose-/Qualitäts-Tooling (`tools/ruleset_quality/`) importiert ausschließlich bereits
  produktive Matching-Funktionen wieder — keine zweite Matching-/Regex-Engine.

---

## 6. Bewusst nicht als erledigt markieren

Folgende Punkte sind **nicht** durch die Konsolidierung als abgeschlossen zu betrachten:

1. `app.py` ist trotz bereits erfolgter Reduktion weiterhin ein Kandidat für kontrollierte Modularisierung.
2. Scan-Performance: **gemessen** (Abschnitt 3.16) und größter Hebel (serielles Scraping) **direkt behoben**. Reale Wirkung auf die Produktiv-Scandauer noch nicht verifiziert (Deployment ausstehend). Persistence-Phase (10,1%) bewusst nicht verändert -- offene Design-Entscheidung (Crash-Sicherheit vs. Geschwindigkeit).
3. Resale-Confidence (z.B. HIGH/MEDIUM/LOW) ist konzeptionell sinnvoll, aber noch nicht als vollständiges Produktfeature etabliert.
4. Datenqualitätswarnungen für Kategorien, Regeln und Preisverteilungen sollten langfristig automatisiert werden.
5. Cross-Platform-Duplicate-Identity ist weiter ausbaufähig.
6. Die dokumentierten Phase-15-Restlücken: `controller.yaml`/`ladekabel` **erledigt** (Abschnitt 3.14); `rx_7600`/`rx_7600_xt` **erledigt** (Abschnitt 3.15).
7. `konsolen_bundles`: "Spieltitel VOR Plattform ohne Bindestrich"-Restlücke (Abschnitt 3.8, z.B. "Donkey Kong Bananza Nintendo Switch 2 2025 OVP") — bewusst offen, kein kollisionsfreies Substring-Muster identifiziert.
8. 9 Muster / 27 Titel aus dem Active-False-Positive-Audit (Abschnitt 3.9) bewusst zurückgestellt (P1/P2), nicht gefixt — vollständige Liste mit Einzelbegründung: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.
9. Coverage-/False-Positive-Rate: 251-Listing-Stichprobe jetzt vollständig gelabelt (Abschnitt 3.12) — Precision 91,2%, aber nur 30 von 251 Listings unabhängig einzeln geprüft (Rest pauschal übernommen).
10. Umlaut-Fingerprint-Problem in `app/rule_coverage.py::_is_still_valid()`: **Code-Fix umgesetzt** (Abschnitt 3.12, `c9967ba`), aber dauerhaft **nicht rückwirkend** für historische Daten in 4 Kategorien — bewusst keine weitere Aktion vorgesehen (Datenverlust nicht reparierbar).
11. Regel „Switch Pro Controller“ ohne dritte Preisstufe — explizit auf Nutzerentscheidung nicht behoben (keine Datenbasis für eine Preisgrenze).
12. Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation: **erledigt** (Abschnitt 3.13).
13. min_vram_gb-Bug bei RX 7600 + 4 weiteren GPU-Modellen: **erledigt** (Abschnitt 3.15) — offene
    Beobachtung, ob derselbe Musterbug außerhalb von `gpu` relevant ist, nicht geprüft, kein
    aktiver Punkt.
14. Scraping-Parallelisierung (Abschnitt 3.16) + Persistence-Batching (Abschnitt 3.17): **erledigt
    und verifiziert** (Abschnitt 3.18) — Gesamtdauer -56,4%, Persistence -89%, gegen einen echten
    Produktiv-Scan nach Deployment gemessen. Offene, unkritische Beobachtung: einen der nächsten
    1-2 Scans für eine "steady state"-Bestätigung gegenchecken (dieser erste Scan hatte einen
    ungewöhnlich hohen `dedupliziert`-Wert durch die Ruleset-Signatur-Änderungen dieser Session).
15. Kategorie-Audit + Live-Fehltreffer-Fixes (Abschnitt 3.19): **erledigt** — 5 Fixes über
    `vintage_elektronik`/`handhelds`/`konsolen_bundles` + Preis-Guard in `app.py`. Zwei der drei
    zunächst zurückgestellten Muster bleiben offen (Xenoblade-Spieltitel-Problem in `handhelds`,
    `netzteil`-Positivsignal in `retro_konsolen`) — beide bräuchten Änderungen an geteilten
    Regelgruppen oder an `matcher.py` selbst, kein additiver Exclude-Fix. Quoka-Preis-Parsing-
    Root-Cause weiterhin ungeklärt (Symptom gefixt, HTML-Ursache nicht untersucht). **Rebuild
    ausstehend** (`docker compose up --build -d`) für den `app.py`-Preis-Guard.
16. „pro"-Kollision in `konsolen_bundles.yaml` (Abschnitt 3.20): **erledigt** — die dritte,
    ursprünglich in Abschnitt 3.19 zurückgestellte Fehltreffer-Gruppe stellte sich bei tieferer
    Analyse als 3 unabhängige, additiv lösbare Ursachen heraus statt einer strukturellen
    Gruppen-Kollision. Ein zunächst erwogener, breiterer Fix wurde nach Blast-Radius-Check
    verworfen (~5-7 reale Kollisionen mit informell formulierten echten Bundles). Reiner
    YAML-Fix, kein Rebuild nötig.

---

## 7. Empfohlene nächste Reihenfolge

```text
1. Resale-Confidence / weitere Datenqualität verbessern
        ↓
2. app.py nur bei konkretem Änderungsdruck weiter modularisieren
        ↓
3. erst danach neue Features/Kategorien priorisieren
```

(Reale Wirkung von Scraping-Parallelisierung + Persistence-Batching: erledigt und verifiziert,
Abschnitt 3.18 -- war die vorherige Position 1 dieser Liste.)

Stand 2026-08-15: Datenqualitätspunkte Nr. 1–5 (Coverage-Stichprobe, Regeln ohne Daten,
Orphan-Modelle, RX-7600-Überlappung, controller/ladekabel) sind **alle abgeschlossen**
(Abschnitt 3.12–3.15), ebenso die Scan-Performance-Messung + beide identifizierten Hebel
**inklusive Verifikation gegen echte Produktivdaten** (Abschnitt 3.16–3.18:
Scraping-Parallelisierung + Persistence-Batching, -56,4% Gesamtdauer / -89% Persistence), sowie
der vollständige Kategorie-Audit + 5 Live-Fehltreffer-Fixes + Preis-Guard (Abschnitt 3.19), sowie
die dort zurückgestellte „pro"-Kollision in `konsolen_bundles` (Abschnitt 3.20, erledigt). Keine
offene, konkret benannte P0 mehr — nächster Schritt nach freiem Ermessen aus P1/P2, den zwei
verbleibenden zurückgestellten Fehltreffer-Mustern (Abschnitt 3.19), oder einer neuen
Nutzeranfrage. **Rebuild ausstehend** für den `app.py`-Preis-Guard aus Abschnitt 3.19.

Stand 2026-08-14: die vorherige P0 (Stichproben-Worksheet labeln + kontrollierte
Preishistorie-Revalidierung + Orphan-Modell-Freigabe + Zubehör/Ersatzteil-vs-Gerät-
Fehlklassifikation) ist **abgeschlossen** (Abschnitt 3.12/3.13).

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

Zusätzlich, für das Ruleset-Qualitätssystem: `tools/ruleset_quality/generated/reports/
ABSCHLUSSBERICHT.md`, `FINALE_REVALIDIERUNG_ABSCHLUSSBERICHT.md`,
`OFFENE_ENTSCHEIDUNGEN_1_BIS_3_BERICHT.md` (Abschnitt 3.11),
`ENTSCHEIDUNGEN_TECHNISCHE_VORBEREITUNG_BERICHT.md`, `WORKSHEET_LABELING_BERICHT_2026-08-14.md`,
`HUMAN_VERIFIED_LABELING_ABSCHLUSSBERICHT_2026-08-14.md`,
`PREISHISTORIE_REVALIDIERUNG_V3_BERICHT_2026-08-14.md` (Abschnitt 3.12).

Diese Dokumente liefern historische Details. Für den **aktuellen technischen Code-Stand** ist der Code-Commit `00a4053` maßgeblich; für die technische Projektreferenz ist diese Datei maßgeblich. Zusätzlich: `docs/SCAN_PERFORMANCE_MESSUNG_2026-08-15.md` (Abschnitt 3.16–3.17).
