# Technischer Projektstatus — gpu-watch-v2

> **Single Source of Truth für den technischen Ist-Zustand.**
>
> Stand: **2026-08-14**
> Repository: `dkmd89-dev/gpu-watch-v2`
> Branch: `main`
> **Letzter Code-Commit (vor dieser Doku-Aktualisierung):** `a6e8df1` (fix:
> Zubehör/Ersatzteil-vs-Gerät-Fehltreffer aus 251-Listing-Stichprobe schließen)
> **HEAD (main, vor dieser Doku-Aktualisierung):** `3c9a678` (Merge PR #32)
> Vorheriger dokumentierter Stand: `2745a95` (PR #29 + Folge-Sessions)
> Vergleich `2745a95...a6e8df1`: PR #31 (251-Listing-Worksheet gelabelt + 3 Exclude-Fixes,
> `c577207`) + PR #32 (Umlaut-Fingerprint-Fix + menschliches Labeling + Preishistorie-
> Revalidierung v3, `3c9a678`) + `a6e8df1` (4 weitere Exclude-Fixes, Zubehör/Ersatzteil-vs-Gerät)
> + freigegebene `lego_bundle`-Datenbereinigung (`data/price_history.jsonl`, kein Code-Commit)
>
> Diese Datei ersetzt `PROJEKTSTAND_KOMPLETT.md` (Datei mittlerweile aus dem Repository entfernt). Historische Phasenberichte bleiben als Detaildokumentation erhalten; widersprüchliche ältere Ist-Stand-Angaben gelten nicht mehr als aktuell.

---

## 1. Kurzfazit

`gpu-watch-v2` ist ein modularer, YAML-gesteuerter **Hardware Deal Finder** für Second-Hand-Angebote. Das System kombiniert Scraper, kategoriebasiertes Matching, Hardware-Detektoren, Deal-Scoring, Marktpreis-/Resale-Statistik, Profit-/Flip-Bewertung, Duplicate Detection, Presence Tracking, Dashboard-KPIs und ntfy-Benachrichtigungen.

Der aktuelle technische Schwerpunkt liegt auf **Precision, Datenqualität und kontrollierter Weiterentwicklung**. Seit `d2effe7` wurden insbesondere Datenqualitäts-/Validierungslogik, Rule Analyzer/Coverage, Caching/Performance, neue Kategorien sowie ein umfangreicher False-Positive-Audit integriert. Seit 2026-08-14 ergänzt ein dediziertes, read-only **Ruleset-Qualitätssystem** (`tools/ruleset_quality/`, siehe Abschnitt 3.11) den bisherigen punktuellen Audit-Ansatz um reproduzierbare Regression-Benchmarks und Preishistorie-Simulationen. Im selben Tag (Abschnitt 3.12) wurde die 251-Listing-Stichprobe vollständig gelabelt, daraus resultierend 3 Exclude-Fixes umgesetzt (PR #31), der Umlaut-Fingerprint-Bug behoben und eine kontrollierte Preishistorie-Revalidierung v3 durchgeführt (PR #32) — mit dem wichtigen Befund, dass der Fix nicht rückwirkend auf bereits gespeicherte Daten wirkt. Direkt im Anschluss (Abschnitt 3.13) wurde Datenqualitätspunkt 14 (Zubehör/Ersatzteil-vs-Gerät) mit 4 weiteren gezielten Exclude-Fixes gelöst.

---

## 2. Verifizierter Repository-Stand

### Git / Code

```text
Branch: main
Letzter Code-Commit (vor dieser Doku-Aktualisierung): a6e8df1
Vorheriger dokumentierter Stand: 2745a95 (PR #29 + Folge-Sessions)

2745a95..a6e8df1:
  PR #31 (c577207) -- 251-Listing-Worksheet KI-gestützt gelabelt (217 TP/
                       21 FP/13 UNCLEAR) + 3 gezielte Exclude-Fixes:
                       exclude_global (defekt-Flexionsformen), handhelds
                       (sd karten Plural), office_pc (dynabook/latitude)
  PR #32 (3c9a678)  -- fix: Umlaut-Fingerprint-Bug behoben (STATUS.md
                       Nr. 11, wirkt NUR auf künftig neue Daten) +
                       menschlich verifiziertes Labeling (Listings 1-30
                       einzeln, 31-251 pauschal) + kontrollierte,
                       read-only Preishistorie-Revalidierung v3
  a6e8df1           -- fix: Zubehör/Ersatzteil-vs-Gerät-Fehltreffer
                       geschlossen (STATUS.md Nr. 14): controller
                       (Kompositum-Lücke "Lötaufsatz"), handhelds
                       (ssd/festplatte/headset/kopfhörer/in-ear),
                       netzteil (kabelset), konsolen_bundles
                       (kontextbewusster joy-con-Exclude)
```

Zusätzlich, außerhalb der Commit-Historie (freigegebene Datenänderung, kein Code-Commit):
`lego_bundle`-Migration/-Bereinigung in `data/price_history.jsonl` — 5 Punkte migriert, 655
gelöscht (siehe Abschnitt 3.12).

### Teststand

In dieser Session tatsächlich lokal ausgeführt und verifiziert (nicht aus Commit-Historie übernommen):

```text
pytest app/tests/ -> 1315 passed, 0 failed (623,91s)

rule_analyzer.py:
355 Regeln, 19 Kategorien, 0 Findings
Ruleset-Signatur (matcher.compute_ruleset_signature()): ee2a6eb114525b55
  -- GEÄNDERT seit PR #31/#32 (98acd6152b61b8bb -> ee2a6eb114525b55), erwartbar:
     der Punkt-14-Fix erweitert exclude_category in 3 Kategorien + einen neuen
     exclude_category_unless_also_contains-Schlüssel in konsolen_bundles
```

Vorheriger dokumentierter Stand: 1309/1309 (PR #32). Die 6 neuen Tests:
`test_zubehoer_ersatzteil_vs_geraet_fix.py` (Punkt-14-Fix, siehe Abschnitt 3.13) — kein Test
wurde gelöscht oder abgeschwächt.

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
- `RX 7600 XT`/`RX 7600`-Überlappung — weiterhin offen. `controller`-`ladekabel`-Exclude: **nächster geplanter Einzelschritt** (noch nicht bearbeitet)
- 9 Muster / 27 Titel aus dem Active-False-Positive-Audit (Abschnitt 3.9) bewusst zurückgestellt (P1/P2) — vollständige Liste: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`
- Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation: **erledigt** (Abschnitt 3.13) — 4 gezielte Exclude-Fixes
- Spieltitel-ohne-Konsole (5 Fälle, jetzt auch in `retro_konsolen` bestätigt) — weiterhin offen
- Umlaut-Fingerprint-Problem: **Code behoben, aber nicht rückwirkend** (Abschnitt 3.12, Punkt 4/6) — dauerhafte, dokumentierte Einschränkung für historische Daten in 4 Kategorien
- Regel „Switch Pro Controller“ hat nur zwei statt drei Preisstufen — explizit auf Nutzerentscheidung **nicht** erweitert (keine belastbare Datenbasis)
- `normalize_title()` entfernt Satzzeichen (z.B. "M.2" → "m 2"), 1 beobachteter Fehlklassifikationsfall (`m2_ssd`→`sata_ssd`) — nur beobachtet, nicht verallgemeinert

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
2. Scan-Performance sollte mit echten End-to-End-Scanmetriken gemessen werden, bevor weitere Optimierungen erfolgen.
3. Resale-Confidence (z.B. HIGH/MEDIUM/LOW) ist konzeptionell sinnvoll, aber noch nicht als vollständiges Produktfeature etabliert.
4. Datenqualitätswarnungen für Kategorien, Regeln und Preisverteilungen sollten langfristig automatisiert werden.
5. Cross-Platform-Duplicate-Identity ist weiter ausbaufähig.
6. Die dokumentierten Phase-15-Restlücken (`rx_7600_xt`, `controller.yaml`/`ladekabel`) warten auf eine bewusst getrennte Regeländerung — `controller`/`ladekabel` ist der als Nächstes geplante Einzelschritt (Abschnitt 7).
7. `konsolen_bundles`: "Spieltitel VOR Plattform ohne Bindestrich"-Restlücke (Abschnitt 3.8, z.B. "Donkey Kong Bananza Nintendo Switch 2 2025 OVP") — bewusst offen, kein kollisionsfreies Substring-Muster identifiziert.
8. 9 Muster / 27 Titel aus dem Active-False-Positive-Audit (Abschnitt 3.9) bewusst zurückgestellt (P1/P2), nicht gefixt — vollständige Liste mit Einzelbegründung: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.
9. Coverage-/False-Positive-Rate: 251-Listing-Stichprobe jetzt vollständig gelabelt (Abschnitt 3.12) — Precision 91,2%, aber nur 30 von 251 Listings unabhängig einzeln geprüft (Rest pauschal übernommen).
10. Umlaut-Fingerprint-Problem in `app/rule_coverage.py::_is_still_valid()`: **Code-Fix umgesetzt** (Abschnitt 3.12, `c9967ba`), aber dauerhaft **nicht rückwirkend** für historische Daten in 4 Kategorien — bewusst keine weitere Aktion vorgesehen (Datenverlust nicht reparierbar).
11. Regel „Switch Pro Controller“ ohne dritte Preisstufe — explizit auf Nutzerentscheidung nicht behoben (keine Datenbasis für eine Preisgrenze).
12. Zubehör/Ersatzteil-vs-Gerät-Fehlklassifikation: **erledigt** (Abschnitt 3.13).

---

## 7. Empfohlene nächste Reihenfolge

```text
1. controller/ladekabel-Exclude separat bewerten (Datenqualität Nr. 5,
   Phase-15-Restlücke) -- nächster geplanter Einzelschritt
        ↓
2. Scan-Performance messen
        ↓
3. Resale-Confidence / weitere Datenqualität verbessern
        ↓
4. app.py nur bei konkretem Änderungsdruck weiter modularisieren
        ↓
5. erst danach neue Features/Kategorien priorisieren
```

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

Diese Dokumente liefern historische Details. Für den **aktuellen technischen Code-Stand** ist der Code-Commit `a6e8df1` maßgeblich; für die technische Projektreferenz ist diese Datei maßgeblich.
