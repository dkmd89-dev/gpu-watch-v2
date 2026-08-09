# PROJEKTSTAND_KOMPLETT.md — gpu-watch-v2 / Hardware Deal Finder

> Diese Datei ist die einzige verlässliche Referenz für den Ist-Zustand des
> Projekts. Jede Angabe wurde gegen den realen Code verifiziert (Dateisystem,
> `git log`/`status`, echter `pytest`-Lauf).
> Stand: Repo `main`, letzter committeter Commit `d2effe7` (Schritt B/Option 2 —
> separates Grouping für `estimated_resale_price`, siehe Commit-Message).
> Working Tree clean, keine unversionierten Änderungen.
> Ersetzt/ergänzt `PHASE_0_ANALYSE_VERIFIZIERT.md`.
>
> **Update (2026-08-08, nach Root-Cause-Fix der 2 Testfehler):** Beide unten
> beschriebenen Testfehler waren **Test-eigene Defekte, kein App-Bug**
> (Details siehe Git-Historie: Fixture ohne `fingerprint` wurde von
> `burst_cleanup.py` fälschlich zu einem einzigen Datenpunkt kollabiert;
> zweite Assertion erwartete Platzhalter-Score `50` statt der tatsächlichen,
> projektweiten Konstante `_PLACEHOLDER_SCORE = 60`). Nach Korrektur der
> beiden Testdateien: **615 passed, 0 failed.** Kein Produktionscode
> geändert.
>
> **⚠️ Realer Testlauf (verifiziert am 2026-08-08): 613 passed, 2 failed**
> (56 Testdateien), nicht wie zuvor hier dokumentiert 599/599 grün. Beide
> Fehlschläge betreffen denselben Bereich — "Flip-Kandidaten Schritt B/Option 1"
> (Resale-Preis-Fallback bei dünner Preishistorie):
> - `tests/test_app_margin_field.py::test_found_json_enthaelt_margin_bei_vorhandener_preishistorie`
>   — erwartet `estimated_margin_eur is not None`, tatsächlich `None`.
> - `tests/test_matcher_deal_score_integration.py::test_evaluate_resale_prices_none_wert_faellt_nicht_auf_market_price_zurueck`
>   — erwartet `deal_score == 50`, tatsächlich `60`.
>
> Root Cause noch nicht analysiert (Abgleich zwischen dem in Abschnitt 3c
> beschriebenen `None`-Fallback-Pfad und dem tatsächlichen Verhalten von
> `_resale_prices_from_stats()`/`compute_profit()`/`_profit_score()` steht aus).
> Diese Datei dokumentiert nur den Ist-Zustand — die Behebung ist ein
> eigener, separat freizugebender Schritt.
>
> **Update (2026-08-09): neue Kategorie „autoradio_opel_corsa"
> VORBEREITET, NICHT im Repo committet.** In einer separaten Dev-Session
> lokal erstellt und gegen eine isolierte Kopie des Matchers verifiziert
> (siehe Abschnitt 19). **Keine Push-/Schreibrechte auf `origin/main`
> in dieser Session** — die Aussage „Working Tree clean" oben bezieht
> sich weiterhin nur auf `d2effe7`. Abschnitt 19 beschreibt einen
> vorbereiteten, noch nicht eingespielten Änderungsvorschlag.

---

## 1. Zweck & Scope

Hardware Deal Finder für Second-Hand-Angebote (primär Kleinanzeigen, dazu
eBay und Quoka), der Angebote nach Deal-Potenzial bewertet und bei starken
Treffern per ntfy benachrichtigt. Reale Kategorien-Abdeckung geht über den
im Entwicklungsauftrag beschriebenen PC-Fokus hinaus (Details: Abschnitt 6).

## 2. Repo-Zustand

```
Branch: main
Letzter committeter Commit: d2effe7 feat(profit): Schritt B Option 2 -- separates
  Grouping fuer estimated_resale_price
Working Tree: clean

Commits seit b9eb637 (chronologisch, neueste zuerst d2effe7):
  d2effe7 feat(profit): Schritt B Option 2 -- separates Grouping fuer estimated_resale_price
  d8774bd feat(dashboard): KPI-Filter (Top-Deals/Sehr gute Deals/Flip/Neue Top-Deals)
  0849a4e feat(top-deal): neue Score+Discount-Logik aktiviert + found.json recomputed
  90c65dd fix(profit): margin_pct-Guard gegen absurde Werte bei Mini-Kaufpreisen
  bfd7077 docs: Flip-Kandidaten-Bugfix Schritt A dokumentiert, Schritt B offen
  91e20e2 fix(rules): RAM-Preisgrenzen 16GB/32GB DDR4 kalibriert
  9f79ed3 fix(rules): CPU+Mainboard-Bundle X-Varianten + Ryzen-5600-Preise
  e834914 fix(rules): Notebook-Suchbegriffe von Matching-Regel entkoppelt
```
Tests: `pytest app/tests/` → **613 passed, 2 failed** (siehe Warnhinweis oben).
Vormals dokumentierte 599/599-grün-Aussage war an einem älteren HEAD
(`e834914`) erhoben und ist überholt.

## 3a. Top-Deal-Logik — neu abgeschlossener Workstream (STATUS.md Abschnitt 32)

Eigenständiger Auftrag ("Top-Deal-Logik optimieren + Dashboard-KPIs
erweitern"), NICHT Teil der ursprünglichen Phase-0/1-Zielliste dieses
Dokuments, deshalb hier nur zusammengefasst — Details in STATUS.md:

- **Neue Top-Deal-Regel** (`top_deal.py`): `(Score≥80 UND Discount≥25%)
  ODER (Score≥90 UND Discount≥20%)` statt der alten reinen 15%-Regel.
  `evaluate_top_deal()` nimmt jetzt optional `deal_score` entgegen
  (Default `None`, rückwärtskompatibel).
- **Vier KPIs in `/api/status`**: `top_deal_count`,
  `very_good_deals_count` (gut, aber nicht Top-Deal),
  `flip_candidates_count` (`estimated_margin_pct >= MIN_FLIP_MARGIN_PCT`),
  `new_top_deals_count` (Top-Deals seit letztem Scan-Start) — alle
  ausschließlich aus vorhandenen `found.json`-Feldern abgeleitet, keine
  neue Persistenz.
- **Dashboard**: 4 KPI-Kacheln, Top-Deal-Transparenz-Zeile auf Deal-Karten
  (Score/Preis/Marktwert/Rabatt/Regel), sowie **neu ein KPI-Filter**
  (Top-Deals/Sehr gute Deals/Flip-Kandidaten/Neue Top-Deals) in der
  bestehenden Filterleiste — client-seitig über neue `data-*`-Attribute
  je Karte (`data-is-top-deal`, `data-margin-pct`, `data-found-at`),
  Schwellen per `kpi_filter_thresholds` aus dem Backend injiziert (single
  source of truth, keine doppelte Zahl in JS).
- **Nicht verändert** (laut Auftrag bewusst ausgeschlossen): Price-History,
  PriceStats, Deal-Score-Engine, Scraper/Registries, YAML-Kategorien,
  Notification-Gate.

Reale KPI-Zahlen (Top-Deals/Sehr gute Deals/Flip-Kandidaten gegen die
produktive `found.json`) stehen noch aus — in der Entwicklungs-Sandbox
liegen keine Produktionsdaten vor.

## 3b. Repo-Hygiene (erledigt)

Änderungen aus diesem Workstream sind mittlerweile committet
(`d8774bd`, `0849a4e`, siehe Abschnitt 2). Reale KPI-Auswertung gegen
produktive `found.json`-Daten (siehe 3a, letzter Absatz) steht weiterhin
aus — unabhängig vom Commit-Status.

## 3c. Flip-Kandidaten-Bugfix — Schritt A + B/Option 1 abgeschlossen, B/Option 2 offen

Eigenständiger Auftrag ("Flip-Kandidaten-Logik anpassen/optimieren"),
ausgelöst durch produktiven Befund: KPI `flip_candidates_count` zeigte
**730 von 2500** Angeboten (29 %) — deutlich zu hoch, um plausibel zu sein.

**Root-Cause-Analyse (gegen echte `found.json`-Produktivdaten
verifiziert):**
- **Ursache 1 (Bug, behoben — Schritt A):** `estimated_margin_pct =
  margin_abs / purchase_price * 100` divergiert bei sehr niedrigen/
  fehlerhaften Kaufpreisen (Tausch-/VB-Inserate mit `price=1€`) ins
  Absurde — beobachteter Extremfall `+58.695 %` bei einem MacBook-Inserat
  für 1 €. 70 der 730 Treffer hatten `price ≤ 5 €`.
- **Ursache 2 (methodisch, behoben via Schritt B/Option 1):** Auch ohne
  die Ausreißer aus Ursache 1 blieben **~500 Treffer mit plausiblem Preis
  (>20 €)** über der 20 %-Schwelle. Grund: `price_stats.py::
  _estimated_resale_price()` fiel bei `< 5` Preishistorie-Datenpunkten je
  `price_history_model` auf den bisherigen Maximalpreis zurück — bei
  granularen Regel-Labels (einzelnes iPhone-Modell+Speicher, einzelnes
  Lego-Set, einzelne Retro-Konsole) ist die Datenbasis oft dünn, wodurch
  die Marge strukturell zu optimistisch wurde. Betroffene Kategorien:
  `lego_minifiguren` (185/386 Treffer), `iphone` (152/1110),
  `retro_konsolen` (103/240), `vintage_elektronik`, `monitor_curved`.
  Seit Schritt B/Option 1 zählen diese Treffer nicht mehr als
  Flip-Kandidat (siehe unten) — Option 2 (Granularität der
  `price_history_model`-Schlüssel) bleibt als separate, weitergehende
  Verfeinerung offen.

**Schritt A — umgesetzt (committet als `90c65dd`, siehe Abschnitt 2):**
- `scoring/profit.py`: neue Konstante `MIN_PURCHASE_PRICE_FOR_MARGIN_PCT`
  (Default 10 €). `margin_pct` wird `None` statt eines irreführenden Werts,
  wenn `purchase_price` darunter liegt — `margin_abs` (Euro) bleibt
  unverändert gesetzt. Überschreibbar via
  `fees.min_purchase_price_for_margin_pct` in `_global.yaml`.
- `rules/_global.yaml`: neuer optionaler Key im bestehenden `fees:`-Block
  (kein neuer Ladepfad in `matcher.py` nötig).
- `tests/test_profit.py`: 3 neue Tests. Volle Suite: **599/599 grün**.
- Simulation gegen `found.json`-Produktivdaten: **730 → 624**
  Flip-Kandidaten (−106 Fehltreffer mit `price < 10 €`).

**Schritt B, Option 1 — umgesetzt (committet, in `d2effe7` enthalten):** methodische
Verfeinerung von `estimated_resale_price` bei dünner Preishistorie
(< 5 Datenpunkte je `price_history_model`). Angebote, deren
`price_history_model` unter der Mindest-Sample-Schwelle liegt, zählen jetzt
nicht mehr als Flip-Kandidat — statt wie bisher den Max-Preis-Fallback als
Verkaufsreferenz zu nutzen, liefert `_estimated_resale_price()` in diesem
Fall `None`. Umgesetzt in `price_stats.py`, `app.py`
(`_resale_prices_from_stats()`) und `matcher.py` (`evaluate()`) — die
Rückfall-Logik musste in zwei zusätzlichen Dateien angepasst werden, damit
ein `None`-Wert nicht versehentlich wieder auf `market_price` zurückfällt
(siehe STATUS.md Abschnitt 33b für Details). `market_price` und das
Notification-Gate sind unverändert. 2 bestehende Tests angepasst, 1 neuer
Test ergänzt.

**Schritt B, Option 2 — umgesetzt (committet in `d2effe7`, ⚠️ mit den 2
offenen Testfehlern, s. Kopfbereich dieser Datei):** separates, gröberes
Gruppierungs-Mapping ausschließlich für die Resale-Preis-Schätzung
(`market_price` bleibt bei der bisherigen, feingranularen Gruppierung).
Umgesetzt:
- `price_stats.py`: neu `group_by_resale_group()` /
  `compute_resale_stats_by_group()` (additiv, kein Eingriff in die
  bestehende `market_price`-Berechnung).
- `matcher.py::_load_rules_from_dir()`: baut ein `resale_price_groups`-
  Mapping aus einem optionalen YAML-Key `resale_price_group` je Regel
  (Default: Identität, also rückwärtskompatibel für Regeln ohne diesen Key).
- `app.py`: neu `_load_resale_stats_by_group()`; `_resale_prices_from_stats()`
  um 2 optionale Parameter erweitert, `market_prices`-Pfad unverändert.
- `rules/lego_minifiguren.yaml`: 7 Einzelfigur-Regeln → Gruppe
  `lego_rare_minifig_common`, 2 Konvolut-Regeln → `lego_bundle_common`.
- `rules/retro_konsolen.yaml`: `nintendo_retro_konsole` +
  `sony_retro_konsole` → gemeinsame Gruppe `retro_konsole_single`.
- `rules/iphone.yaml` bewusst **nicht** angepasst (laut Commit-Message: keine
  sichere Gruppierungsachse ohne Preisniveau-Vermischung).
- 15 neue Tests laut Commit-Message (`price_stats`, Matcher-Mapping,
  App-Grouping) — dennoch bestehen aktuell 2 Testfehler in angrenzenden
  Bereichen (Kopfbereich dieser Datei); ob diese durch `d2effe7` verursacht
  oder vorbestehend sind, ist noch nicht analysiert.
- `deal_score`/Notification-Gate laut Commit-Message für ALLE Kategorien
  unverändert (Default-Gewicht `profit` weiterhin 0.0 in fast allen
  Kategorien, siehe Abschnitt 7).

## 3d. RAM/CPU+Mainboard/Notebook — Preisgrenzen & Matching-Fixes (abgeschlossen, STATUS.md Abschnitt 34)

Drei in Abschnitt 30 (STATUS.md) neu eingeführte Kategorien lieferten in
der Produktivumgebung kaum Treffer. Ursache je Kategorie per
Live-Marktrecherche (Kleinanzeigen) und Code-Review verifiziert, drei
unabhängige Commits:

- **`ram.yaml`** (`91e20e2`): unkalibrierte Platzhalter-Preisgrenzen bei
  16GB/32GB DDR4 lagen weit unter realem Marktniveau. Neu: 16GB
  35€/55€, 32GB 70€/110€ (Top-Deal/Guter Preis). 8GB unverändert.
- **`cpu_mainboard_bundle.yaml`** (`9f79ed3`): `matcher._contains_term()`
  prüft exakte Wortgrenzen — Regeln matchten `"5600"`/`"3600"` nicht bei
  den in der Praxis dominierenden X-Varianten (`"5600X"`/`"3600X"`).
  Synonyme ergänzt. Zusätzlich Ryzen-5600-Bundle-Preisgrenzen live
  verifiziert und auf 150€/200€ angehoben (`notify_max_price` → 200€).
  12400F-/Ryzen-3600-Preisgrenzen bewusst unverändert (keine belastbaren
  Marktdaten verfügbar — offener Punkt).
- **`notebook_resell.yaml`** (`e834914`): `search_terms` enger als die
  Matching-Regel — `"ThinkPad Ryzen"` (AND-Suche) filterte
  Intel-ThinkPads (Mehrheit der Angebote) schon vor der Bewertung heraus,
  obwohl die Matching-Regel kein `"ryzen"` verlangt. Suchbegriffe auf
  Modellcodes umgestellt (`"ThinkPad T14"`/`"X13"`/`"T490"`/`"X390"`/
  `"L14"`).

Reine YAML-Änderungen, kein Python-Code betroffen, **599/599 Tests
grün**. Details, Root-Cause-Analyse und Nebenwirkungen: STATUS.md
Abschnitt 34.

## 3. Architektur — Datenfluss

```
app.py::run_scan()  (Scan-Loop, alle SCAN_INTERVAL_MINUTES via scheduler_loop())
  │
  ├─ 1. scrapers/registry.py::discover_scrapers()
  │      → pkgutil-Scan über scrapers/-Package, findet alle search_<name>()
  │      → kleinanzeigen.py, ebay.py, quoka.py implementieren scrapers/base.py::Scraper-Protocol
  │      → liefern NUR Rohdaten (Listing-TypedDict: source/title/price/url/
  │        location/description/images) — keinerlei Bewertungslogik (Phase 3, erledigt)
  │
  ├─ 2. matcher.py::evaluate(listing, rules)  je Angebot
  │      → _load_rules_from_dir() liest rules/*.yaml (siehe Abschnitt 4)
  │      → categories/detectors/*.py liefern strukturierte Merkmale
  │        (CPU-Tier/Generation, RAM GB+Typ, SSD/HDD/NVMe GB, PSU Watt,
  │        Gehäusetyp, dedizierte GPU, Windows-Version, Hersteller)
  │      → _evaluate_hardware_requirements() prüft Mindestanforderungen
  │        gegen die Kategorie-Regel (min_ram_gb, min_cpu, case, GPU, ...)
  │      → scoring/deal_score.py::compute_deal_score() → 0–100 + Sterne
  │      → scoring/profit.py::compute_profit() (Reselling-Marge, optional)
  │      → Zusatzsignale: part_out_*, price_history_model (siehe Abschnitt 7)
  │
  ├─ 3. Persistenz (app.py, atomare JSON-Writes)
  │      → data/seen.json (alle je gesehenen Angebote, 14 MB)
  │      → data/found.json (Treffer über Schwelle, 2,1 MB) — Dashboard-Quelle
  │      → data/price_history.jsonl (append-only, jeder Datenpunkt)
  │      → data/time_to_sell.jsonl (append-only, Delisting-Ereignisse)
  │
  ├─ 4. Notification-Gate (notify.py + rules/_global.yaml::notifications)
  │      → NUR bei stars >= gate_min_stars UND price <= (kategorie.notify_max_price
  │        ODER gate_max_price als Fallback) wird ntfy ausgelöst
  │      → alle anderen Treffer: nur gespeichert + im Dashboard sichtbar
  │
  └─ 5. Dashboard (templates/index.html + app.py-API-Routen)
         → 8 Flask-Routen: "/", /api/found, /api/status, /api/price-history[/model],
           /api/time-to-sell, /api/cross-platform, /api/scan-now (POST)
```

## 4. Regeln (YAML) — Struktur & Vererbung

```
rules/
  _global.yaml            Infrastruktur, KEINE Kategorie (siehe categories/registry.py::_NON_PLUGIN_FILES)
    defaults:              min_vram_gb, location_plz, radius_km
    exclude_global:         wortübergreifende Ausschlussphrasen (Defekt/Bastler/Verpackung/Kabel-only/Gesuche)
    notifications:          urgent_price_threshold, tags, gate_min_stars, gate_max_price (Fallback)
    scoring_weights:        Default-Gewichte (price 0.7 / ausstattung 0.15 / hardware_qualitaet 0.15 / hersteller,zustand,lieferumfang: 0)
    manufacturer_reputation: Tabelle 0–100 je Hersteller (Score-Komponente technisch vorhanden, Gewicht bewusst 0)
    fees:                   Reselling-Gebührenmodell (platform_fee_pct, payment_fee_pct, shipping_cost, packaging_cost)
    duplicate_detection:    price_tolerance_pct, window_days
    part_out_detection:     gpu_value_ratio_threshold_pct
    presence_tracking:      delisting_threshold_scans

  gaming_pc.yaml, gpu.yaml, iphone.yaml, lego_minifiguren.yaml, macbook.yaml,
  monitor_curved.yaml, netzteil.yaml, office_pc.yaml, retro_konsolen.yaml,
  sata_ssd.yaml, vintage_elektronik.yaml   → je 1 Kategorie-Plugin
```

**Fallback-Kette pro Kategorie:** eigene YAML-Werte → `_global.yaml`
(`scoring_weights`, `notify_max_price`→`gate_max_price`) → Modulkonstanten
(z. B. `DEFAULT_PART_OUT_THRESHOLD_PCT=70.0` in `matcher.py`, wenn
`part_out_detection` fehlt) — überall rückwärtskompatibel, kein Crash bei
unvollständiger Config.

**Kategorie-Schema (Beispiel `office_pc.yaml`):** `category`, `label`,
`notify_max_price`, `search_terms`, `rules:` (Liste, je Regel: `label`,
`price_history_model`, `requirements` [min_ram_gb, ram_type_exclude, min_cpu
{intel/amd: min_tier_rank, min_generation}, case.exclude_categories,
requires_dedicated_gpu], `max_price`, `deal_rating`,
`negotiation_tolerance_pct`, `negotiation_min_score`,
`negotiation_score_component`).

## 5. Plugin-Discovery — was ist WIRKLICH codefrei erweiterbar?

| Ebene | Mechanismus | Codefrei erweiterbar? |
|---|---|---|
| **Kategorien** (`rules/*.yaml`) | `categories/registry.py::discover_categories()` scannt `rules/*.yaml` per `pathlib.glob`, matcher nutzt dieselbe Quelle | **Ja, verifiziert** — `tests/test_rules_category_plugin_contract.py` beweist es aktiv. Neue YAML-Datei = neue Kategorie, ohne Python-Änderung. |
| **Scraper** (`scrapers/*.py`) | `scrapers/registry.py::discover_scrapers()` per `pkgutil`, `app.py` ruft generisch alle Treffer mit gleicher Signatur auf | Neue **Quelle** braucht eine neue `.py`-Datei mit `search_<name>()` nach `scrapers/base.py`-Protocol — kein Eingriff in `app.py` nötig, aber es ist Code (kein YAML). |
| **Detectors** (`categories/detectors/*.py`) | `categories/detectors/registry.py::discover_detectors()` existiert **nur als Discovery/Test-Infrastruktur** | **Nein.** `matcher.py` importiert Detectors weiterhin **statisch** (`from categories.detectors.cpu import detect_cpu`, ...) und ruft sie **gezielt** in `_evaluate_hardware_requirements()` auf. Bewusste Design-Entscheidung laut Docstring (Risiko-Minimierung), aber: **eine Kategorie, die ein komplett neues Hardware-Merkmal braucht (z. B. Mainboard-Chipsatz erkennen), erfordert einen neuen Detector in Python + einen neuen Aufruf in `matcher.py`.** |

**Konsequenz für den Auftrag** ("Neue Kategorien sollen künftig
ausschließlich über YAML-Dateien ergänzt werden können"): Das gilt bereits
uneingeschränkt für Kategorien, die mit **vorhandenen** Detector-Merkmalen
auskommen (z. B. eine neue reine GPU-Untervariante, ein neues Titel-Keyword-
Set analog zu `gpu.yaml`). Für Kategorien, die ein **neues** Hardware-Merkmal
erfordern (Mainboard-Chipsatz, PCIe-Generation-Details, Monitor-Panel-Typ),
ist zusätzlich ein neuer Detector nötig — das ist ein echter, noch offener
Punkt (siehe Lücken-Liste, Abschnitt 8).

## 6. Kategorien — Ist-Abdeckung vs. Auftrags-Zielliste

| Auftrags-Zielkategorie | Status |
|---|---|
| Office-PC | ✅ implementiert (`office_pc.yaml`), inkl. CPU-Tier/Generation-Muster statt Modell-Whitelist (bewusste Interpretation, dokumentiert in der YAML) |
| Gaming-PC | ✅ implementiert (`gaming_pc.yaml`) |
| Grafikkarten | ✅ implementiert (`gpu.yaml`) — bereits vor der V2-Anforderung vorhanden |
| CPUs (eigene Kategorie) | ⚠️ abweichend umgesetzt — auf Robins expliziten Wunsch KEINE separate CPU-Kategorie, sondern kombiniert mit Mainboard (`cpu_mainboard_bundle.yaml`, reines Titel-Keyword-Matching, kein Chipsatz-Detector nötig) |
| Mainboards | ⚠️ abweichend umgesetzt — s. o., nur als Bestandteil von `cpu_mainboard_bundle.yaml`, keine eigenständige Mainboard-Kategorie |
| RAM (eigene Kategorie) | ✅ implementiert (`ram.yaml`) — DDR4-only, 3 Kapazitätsstufen (8/16/32GB), Titel-Keyword-Matching (Begründung: `min_ram_gb`-Requirement kennt kein Obergrenzen-Pendant, siehe YAML-Kommentar) |
| SSDs | ⚠️ teilweise — `sata_ssd.yaml` existiert (SATA-SSD als Einzelkategorie), NVMe als eigene Kategorie fehlt weiterhin |
| Netzteile | ✅ implementiert (`netzteil.yaml`) |
| Monitore | ⚠️ teilweise — `monitor_curved.yaml` existiert (nur Curved-Segment), keine allgemeine Monitor-Kategorie |
| Notebooks | ✅ implementiert (`notebook_resell.yaml`, category-Feld `notebook_resell`) — ThinkPad (modern) + Gaming-Notebooks (RTX 3060/4060); `macbook.yaml` bleibt separat (anderer Scope, Apple) |

**Zusätzlich vorhanden, außerhalb der Auftrags-Zielliste:** `iphone.yaml`,
`macbook.yaml`, `retro_konsolen.yaml`, `vintage_elektronik.yaml`,
`lego_minifiguren.yaml` — fünf Kategorien ohne PC-Hardware-Bezug.

**Reselling-Erweiterung (`notebook_resell.yaml`):** erste Kategorie, die
das `profit`-Scoring-Gewicht aktiv setzt (`0.25`, war zuvor projektweit
`0.0` und nur in `scoring/deal_score.py` vorbereitet). Rückwärtskompatibel,
da ohne gesammelte `price_history`-Daten für die dortigen
`price_history_model`-Schlüssel `compute_profit()` auf den neutralen
Platzhalter-Score (60) zurückfällt — keine Verzerrung bestehender
Kategorien, siehe `scoring/deal_score.py::_profit_score()`.

## 7. Reselling-Zusatzlogik (über den ursprünglichen Auftrag hinaus)

Vorhanden und produktiv, aber im Entwicklungsauftrag nicht erwähnt:

- **Deal-Score-Erweiterung:** `scoring/profit.py` — Margen-/Profit-Score
  auf Basis von `fees:` (Plattform-/Zahlungsgebühr, Versand, Verpackung)
- **Part-Out-Erkennung:** `matcher.py` markiert PCs, deren enthaltene GPU
  laut Marktpreis-Tabelle (`rules/mappings/component_values.yaml`) einen
  großen Anteil des PC-Preises ausmacht (Schwelle konfigurierbar) — reines
  Zusatzsignal, kein Einfluss auf `deal_score`/Notification-Gate
- **Duplicate-/Cross-Posting-Erkennung:** `duplicate_detection.py`,
  konfigurierbar über `_global.yaml::duplicate_detection`
- **Cross-Platform-Preisvergleich:** `cross_platform_stats.py`
- **Time-to-Sell-Schätzung:** `presence_tracking.py` (Delisting-Erkennung)
  + `time_to_sell.py`/`time_to_sell_stats.py`, append-only JSONL nach dem
  Muster von `price_history.py`
- **Burst-Cleanup:** `burst_cleanup.py` — zeitbasierte Alt-Daten-Duplikat-
  Bereinigung in der Preishistorie
- **Verhandlungs-Assistent:** `negotiation_tolerance_pct` /
  `negotiation_min_score` / `negotiation_score_component` je Kategorie-Regel

Diese Logik ist bereits durch 596 Tests abgesichert und produktiv im
Einsatz — sie sollte in Phase 1 bewusst als **bestehender Bestandteil**
behandelt werden, nicht als etwas, das "neu geplant" werden muss.

## 8. Bekannte Lücken & offene Punkte

| # | Lücke | Auswirkung | Vorschlag Priorität |
|---|---|---|---|
| L1 | **Abgeschlossen (siehe Abschnitt 9c)** — Robin verzichtet bewusst auf NVMe-SSD- und allgemeine Monitor-Kategorie, bestehende `sata_ssd.yaml`/`monitor_curved.yaml` reichen aus | — | Erledigt |
| L2 | Detector-Ebene ist NICHT codefrei erweiterbar (Abschnitt 5) | Neue Kategorien mit neuem Hardware-Merkmal brauchen Python-Änderung | **Entschieden (siehe Abschnitt 9a)** — bewusst kontrolliert bei statischen Imports geblieben |
| L5 | ✅ Abgeschlossen (`SEEN_MAX_ITEMS`, Abschnitt 31 STATUS.md) — harte Obergrenze von 50.000 Einträgen, älteste werden zuerst entfernt | Perf./Speicher langfristig | Erledigt |
| L6 | Scope-Drift: 5 Nicht-PC-Kategorien | Klärungsbedarf, kein Bug | **Entschieden (siehe Abschnitt 9b)** — bewusst behalten, unabhängig weiterlaufen lassen |
| L7 | `app.py` als 1155-Zeilen-Monolith (Routen + Scan-Loop + Scheduler in einer Datei) | Wartbarkeit bei weiterem Wachstum | Niedrig, vorausschauend — Umsetzung: `roadmap.md` Phase 3 |
| L8 | Hersteller/Zustand/Lieferumfang-Scoring-Gewichte bewusst auf 0 (kein Detector für Zustand/Lieferumfang) | Deal-Score nutzt nur 3 von 6 Komponenten aktiv | Mittel, hängt von L1/L2 ab |
| L9 | **Abgeschlossen (siehe Abschnitt 9c / Commit `da666ec`)** — `estimated_resale_price` lieferte bei < 5 Preishistorie-Datenpunkten bisher einen Max-Preis-Fallback, der `flip_candidates_count` bei dünner Datenbasis (iPhone/Lego/Retro-Konsolen) strukturell zu optimistisch machte; liefert seit Option 1 `None` statt Fallback, Option 2 gruppiert zusätzlich Lego/Retro-Konsolen gröber für die Resale-Schätzung. Die 2 angrenzenden Testfehler (`test_app_margin_field.py`, `test_matcher_deal_score_integration.py`) waren Test-eigene Defekte, kein App-Bug — behoben, Produktionscode unverändert | Kein offener Punkt mehr, Teststand 615 passed / 0 failed | Erledigt |

### 9a. Architekturentscheidung L2 — ENTSCHIEDEN (kein Code geändert)

**Entscheidung:** Option B — kontrolliert bei statischen Imports in
`matcher.py` bleiben. `categories/detectors/registry.py` bleibt reine
Discovery-/Test-Infrastruktur, `matcher.py` wird NICHT auf sie umgestellt.

**Begründung (verifiziert an `_evaluate_hardware_requirements()`,
`matcher.py` Zeilen 491–556):** Jeder Requirement-Typ ist kein reiner
Detector-Aufruf, sondern ein Dreiklang aus Detector + eigener
Validierungsfunktion (`_ram_meets_requirement`, `_storage_meets_requirement`,
`_psu_meets_requirement`, `_cpu_meets_requirement`, `_case_meets_requirement`,
`_gpu_meets_requirement`) + Weiterverwendung des Feature-Werts in
`_build_score_inputs()` (Headroom-Berechnung, `has_ssd`, `has_dedicated_gpu`).
Die "fehlend"-Semantik ist zudem NICHT einheitlich — `_case_meets_requirement`
kehrt sie bewusst um (kein erkannter Gehäusetyp = erfüllt, nicht wie bei
RAM/SSD/PSU = nicht erfüllt). Ein generischer Dispatcher würde diese enge
Kopplung nicht auflösen, sondern nur zusätzliche Indirektion um denselben
speziellen Code bauen — bei hohem Risiko für einen zentralen, produktiv
laufenden Pfad (596 Tests hängen daran) und nachweislich geringem Nutzen,
da jede neue Kategorie mit bestehendem Requirement-Vokabular (`min_ram_gb`,
`min_cpu`, `case`, `min_psu_watt`, `requires_dedicated_gpu`, …) bereits
heute rein per YAML funktioniert (bewiesen durch `monitor_curved`,
`sata_ssd`, `netzteil`). Widerspricht zudem der Grundregel "nicht komplett
umschreiben, nur erweitern".

**Konsequenz für Punkt 3 (Kategorien ergänzen):** Kategorien, die mit
bestehendem Requirement-Vokabular auskommen (z. B. RAM als eigene
Kategorie, SSD/NVMe-Erweiterung) → reines YAML, kein Detector-Aufwand.
Kategorien mit einem genuin NEUEN Hardware-Merkmal (Mainboard-Chipsatz,
Monitor-Panel-Typ, notebook-spezifische Merkmale) → dokumentiertes,
wiederholbares Zwei-Schritt-Muster als bewusste, kontrollierte Ausnahme
vom "nur YAML"-Ziel:
1. neue `detect_<n>()`-Funktion in `categories/detectors/`
2. neuer `if "<key>" in requirements:`-Block in
   `_evaluate_hardware_requirements()` (~10 Zeilen, gleiches Muster wie
   die sechs bestehenden Blöcke)

Kein Rewrite, minimales Risiko, sofort testbar — genau dieses Muster wurde
bereits einmal real angewendet (SATA-SSD-Kapazitätsprüfung, siehe
STATUS.md Abschnitt 10).


3. **Kategorien nacheinander ergänzen** (je ein Schritt, Freigabe-Workflow):
   RAM → SSD/NVMe-Erweiterung → Mainboard → CPU → Monitor (allgemein) →
   Notebook (PC, nicht Apple). Reihenfolge nach vorhandenen vs. fehlenden
   Detectors gestaffelt (RAM/SSD nutzen bestehende Detectors, Mainboard/
   CPU-Einzelkategorie brauchen ggf. neue).
4. **L5 (Datenrotation)** als eigener, späterer Schritt — nicht blockierend
   für die Kategorie-Arbeit.
### 9b. Scope-Entscheidung L6 — ENTSCHIEDEN (kein Code geändert)

**Entscheidung:** Option A — die 5 Nicht-PC-Kategorien (`iphone`, `macbook`,
`retro_konsolen`, `vintage_elektronik`, `lego_minifiguren`) bleiben
unverändert bestehen und laufen unabhängig weiter.

**Begründung:** Alle fünf sind vollständig isolierte YAML-Plugins
(`categories/registry.py::discover_categories()`), ohne jede Kopplung zu
`office_pc`/`gaming_pc`. Sie wurden in eigenen, separat freigegebenen
Sessions (Reselling-/Nischen-Erweiterung, STATUS.md Abschnitte 22/23)
bewusst hinzugefügt und sind produktiv im Einsatz (Preishistorie,
Notification-Gate). Der PC-Fokus des aktuellen Entwicklungsauftrags
("Version 2 konzentriert sich ausschließlich auf komplette PCs") gilt für
die *neue* Zielliste (Grafikkarten, CPUs, Mainboards, RAM, SSDs, Netzteile,
Monitore, Notebooks) — keine der fünf Nischen-Kategorien steht dort.
Behalten hat keinen technischen Konflikt mit Punkt 3 (PC-Kategorien
ergänzen) und keinen Aufwand; Entfernen/Archivieren hätte produktiv
gesammelte Daten ohne technischen Grund verworfen bzw. stillgelegt.

**Konsequenz:** Keine weitere Aktion nötig. Künftige Kategorie-Arbeit
(Punkt 3) fokussiert sich ausschließlich auf die PC-Zielliste des
Auftrags, ohne die bestehenden 5 Kategorien anzufassen.

### 9c. Abschluss L1 — ENTSCHIEDEN (kein Code geändert)

**Entscheidung:** Robin verzichtet bewusst auf die zwei verbleibenden
Teilbereiche der ursprünglichen Auftrags-Zielliste — NVMe-SSD als eigene
Kategorie und eine allgemeine Monitor-Kategorie über das Curved-Segment
hinaus. `sata_ssd.yaml`/`monitor_curved.yaml` decken den tatsächlichen
Bedarf ausreichend ab. L1 gilt damit als abgeschlossen, keine weitere
Kategorie-Arbeit in diesem Bereich vorgesehen.

**Konsequenz:** Punkt 3 des Umsetzungsplans (Kategorien nacheinander
ergänzen) ist damit vollständig beendet. Kategorie-Abdeckung final:
Office-PC, Gaming-PC, Grafikkarten, RAM, Netzteile, SATA-SSD (statt
NVMe), Curved-Monitor (statt allgemein), CPU+Mainboard-Bundle (statt
getrennt), Notebook-Reselling — plus die 5 unabhängigen Nicht-PC-
Kategorien (Abschnitt 9b). Offene Punkte reduzieren sich auf L5
(Datenrotation), L7 (`app.py`-Monolith) und L8 (Scoring-Komponenten ohne
Detector), keiner davon blockierend.



---

**Phase 0 + Phase 1 abgeschlossen, keine funktionalen Code-Änderungen dort**
(diese Aktualisierung ist reine Dokumentations-Synchronisation gemäß
`roadmap.md` Phase 1). Punkt 3 (Kategorien) laut Abschnitt 9c final
abgeschlossen. Top-Deal-Logik-Workstream (Abschnitt 3a) und
Flip-Kandidaten-Bugfix Schritt A + B/Option 1 + B/Option 2 (Abschnitt 3c)
sind inzwischen alle im HEAD-Commit `d2effe7` committet.

**Neuer, wichtigster offener Punkt:** ✅ Behoben (2026-08-08) — die 2
fehlschlagenden Tests (`test_app_margin_field.py`,
`test_matcher_deal_score_integration.py`) waren Test-eigene Defekte
(Burst-Cleanup-Kollision im Fixture bzw. falsch kalibrierte Assertion),
kein App-Bug. Beide Testdateien korrigiert, Produktionscode unverändert.
Aktueller Teststand: **615 passed, 0 failed.**

Weitere offene Punkte: L5 (Datenrotation, ✅ bereits erledigt), L7
(`app.py`-Monolith, → `roadmap.md` Phase 3), L8 (Scoring-Komponenten ohne
Detector, → Phase 6). Keiner davon blockierend.

Zusätzlich identifiziert (Phase-0-Analyse, `roadmap.md`-Kontext, siehe
separate Freigabe): `data/found.json.bak-*`, `data/time_to_sell.jsonl` und
`STATUS.md` waren trotz teils gegenteiliger `.gitignore`-Regeln im Git
getrackt — Produktivdaten im Repo. Behoben in einem separaten,
nicht-funktionalen Hygiene-Schritt (siehe Commit-Nachricht dieses Schritts).

---

## 10. `roadmap.md` Phase 3 (`app.py` kontrolliert modularisieren) — ABGESCHLOSSEN

**Ausgangslage:** `app.py` war auf 1230 Zeilen gewachsen (L7, siehe
Abschnitt 9c). Ziel: schrittweise Extraktion nach dem in `roadmap.md`
vorgeschlagenen Muster (`persistence/`, `services/`, `api/`, `scan/`),
jeder Teilschritt einzeln freigegeben und per vollständigem `pytest`-Lauf
verifiziert.

**Umgesetzte Schritte (alle 1:1-Extraktionen, kein Verhalten geändert,
615/615 Tests nach jedem Schritt grün):**

| Schritt | Extraktion | Neues Modul |
|---|---|---|
| 3.1 | `_load_json`, `_save_json`, `_tail_log` | `persistence/json_store.py` |
| 3.2 | `_load_price_stats`, `_load_resale_stats_by_group`, `_market_prices_from_stats`, `_resale_prices_from_stats` | `services/statistics_service.py` |
| 3.3 | `/api/price-history`, `/api/price-history/<model>`, `/api/time-to-sell`, `/api/cross-platform` (zustandslose Lesepfade) | `api/history.py` (Blueprint) |
| 3.4 | `/`, `/api/found`, `/api/scan-now` bzw. `/api/status` | `api/deals.py` + `api/status.py` (Blueprints) |
| 3.5a | `scheduler_loop()` | `scan/scheduler.py` |

Durchgängiges Muster: reine Verschiebung, Abhängigkeiten (Dateipfade,
Locks, mutable State-Objekte, `run_scan`-Referenz) werden per
Factory-Funktion im Closure übergeben statt dupliziert oder zirkulär
reimportiert — `app.py` bleibt einzige Quelle der Wahrheit für alle
Konstanten/State-Objekte. URL-Pfade und öffentliche `app_mod.*`-Attribute
unverändert (gegen die vollständige Testsuite verifiziert, siehe Lehre
unten).

**Bewusst NICHT extrahiert: `run_scan()` (~534 Zeilen).**

**Begründung (Risikoabwägung, keine Zeitnot):** `run_scan()` referenziert
**46 verschiedene modul-globale Namen** (Locks, das `_scan_status`-Dict,
7 Datei-Pfad-Konstanten, ~25 Funktionen aus anderen Modulen) — etwa 3×
mehr Kopplung als alle Schritte 3.1–3.5a zusammen. Eine saubere Extraktion
hätte entweder eine Factory-Funktion mit 15–20+ Parametern erfordert
(unübersichtlich, hohe Fehlerwahrscheinlichkeit beim Verdrahten) oder neue
Bündelungs-Objekte (z. B. `ScanPaths`/`ScanConfig`/`ScanState`-Dataclasses)
— das wäre keine reine Verschiebung mehr, sondern echte neue Abstraktion
und damit ein Verstoß gegen die `roadmap.md`-Regel "keine unnötige
Abstraktion". Zusätzliches Risiko: `global _scan_running` funktioniert nur
innerhalb von `app.py` als echtes Modul-Global, nicht über Modulgrenzen
hinweg per Closure — ein Detail, das bei einer mechanischen Verschiebung
leicht übersehen würde.

**Lehre aus dieser Session (Schritt 3.4):** Ein als "ungenutzt" entfernter
Import (`MIN_FLIP_MARGIN_PCT`) brach `test_app_status_kpis.py`, weil der
Test über `app_mod.MIN_FLIP_MARGIN_PCT` öffentlich darauf zugriff — durch
den vollständigen Testlauf sofort aufgedeckt und korrigiert. Konsequenz:
jeder künftige "ungenutzte Import"-Kandidat wird vor dem Entfernen gegen
`grep -rn "app_mod\." app/tests/` geprüft.

**Ergebnis:** `app.py` **1230 → 790 Zeilen (−36 %)**. Neue Module:
`persistence/json_store.py` (71 Z.), `services/statistics_service.py`
(139 Z.), `api/history.py` (125 Z.), `api/deals.py` (94 Z.),
`api/status.py` (139 Z.), `scan/scheduler.py` (46 Z.). `run_scan()` bleibt
vollständig und unverändert in `app.py` (L7 damit nicht vollständig
geschlossen, aber deutlich entschärft — verbleibende Monolith-Kritik
konzentriert sich jetzt allein auf `run_scan()`, nicht mehr auf die
gesamte Datei).

**Teststand:** `pytest app/tests/` → **615 passed, 0 failed** (nach jedem
Teilschritt einzeln verifiziert, nicht nur am Ende).

**Konsequenz für spätere Sessions:** Sollte `run_scan()` künftig doch
modularisiert werden, ist das kein "Phase 3 fortsetzen", sondern ein
eigener, bewusst als "neue Abstraktion" (nicht "reine Verschiebung")
gekennzeichneter Schritt mit eigener Freigabe — z. B. über 2–3
Dataclasses zur Bündelung der 46 Abhängigkeiten.

Phase 3 gilt damit als abgeschlossen.

---

## 11. `roadmap.md` Phase 4 (Persistenz analysieren und verbessern) — ABGESCHLOSSEN

**Analyse (erst messen, dann entscheiden — kein Vorgriff):** Real gemessenes
Lade-/Schreib-Benchmark für `seen.json` (atomarer Pfad via
`persistence.json_store`):

| Einträge | Größe | Schreiben | Lesen |
|---|---|---|---|
| 10.000 | 2,5 MB | 161 ms | 16 ms |
| 46.062 (letzter bekannter Produktivstand) | 11,7 MB | 737 ms | 77 ms |
| 100.000 | 25,5 MB | 1.437 ms | 176 ms |
| 200.000 | 51 MB | 2.634 ms | 378 ms |

`time_to_sell.jsonl` (echte Produktivdaten, 7.761 Zeilen/1,71 MB): Lesen
48 ms — unkritisch. Crash-Sicherheit bereits gelöst (atomarer Schreibpfad,
Schritt 3.1). Nebenläufigkeit: Single-Process-Deployment (`python app.py`,
kein gunicorn/mehrere Worker) — bestehende `threading.Lock`-Objekte
ausreichend, kein Multi-Prozess-Zugriffsschutz nötig.

**Kritischer Befund (während der Analyse entdeckt, nicht gesucht):**
`SEEN_MAX_ITEMS`/`enforce_max_size()` — laut STATUS.md Abschnitt 31 als
"L5 abgeschlossen" dokumentiert — waren im tatsächlichen Code NICHT mehr
verdrahtet. Ursache: der unmittelbar folgende, thematisch unabhängige
Commit `00bd8e8` hatte `app.py` überschrieben und die Verdrahtung dabei
still entfernt (`enforce_max_size()` blieb als toter Code liegen,
weiterhin von `test_presence_tracking.py` unit-getestet, aber nie aus
`app.py` heraus aufgerufen). `seen.json` wuchs seitdem wieder unbegrenzt.

**Sofort-Fix (freigegeben, umgesetzt):** `SEEN_MAX_ITEMS`
(Env-Var, Default 50000) + `enforce_max_size()`-Aufruf erneut in `app.py`
verdrahtet, exakt an der ursprünglich freigegebenen Stelle. Zusätzlich ein
End-to-End-Regressionstest ergänzt (`test_seen_json_wird_bei_ueberschreitung_
von_seen_max_items_gekappt`), der `run_scan()` selbst prüft — nicht nur
`enforce_max_size()` isoliert. Per Gegenprobe verifiziert: Fix temporär
entfernt → Test wird rot → Fix wiederhergestellt → Test grün. Dieser Test
hätte die ursprüngliche Regression erkannt; reine Funktions-Unit-Tests
tun das nicht, wenn die Verdrahtung selbst verloren geht.

**Entscheidung Option A vs. B:** **Option A — JSON beibehalten.** Bei
aktueller/absehbarer Größenordnung (≤200k Einträge, Schreibzeit <3s) steht
eine SQLite-Migration (Option B) in keinem Verhältnis zum Nutzen, sobald
der Sofort-Fix das unbegrenzte Wachstum verhindert. Re-Evaluation nur
falls `seen.json` trotz `SEEN_MAX_ITEMS` erneut zum Problem wird.

**Nebenbei behoben (außerhalb dieser Session, vom Auftraggeber selbst):**
`.gitignore`-Lücke (`data/time_to_sell.jsonl` war nicht von den
bestehenden `data/*.json`/`data/*.log`/`data/*.txt`-Mustern erfasst,
weshalb es trotz vorheriger "Hygiene"-Behauptung in Abschnitt 9c weiter
committet wurde) — behoben.

**Teststand:** `pytest app/tests/` → **616 passed, 0 failed** (615 + 1
neuer Regressionstest).

**Lehre für spätere Sessions:** Eine als "abgeschlossen" dokumentierte
Änderung ist nicht automatisch dauerhaft — ein späterer, thematisch
unabhängiger Commit kann sie versehentlich rückgängig machen, wenn kein
Test die *Verdrahtung* (nicht nur die Funktion selbst) prüft. Bei
sicherheits-/stabilitätsrelevanten Fixes künftig immer einen
End-to-End-Test ergänzen, der die tatsächliche Anbindung in `app.py`
verifiziert, nicht nur die isolierte Funktion.

Phase 4 gilt damit als abgeschlossen.

---

## 12. `roadmap.md` Phase 5 (Price-History/Resale-Confidence) — ABGESCHLOSSEN

**Umsetzung (Schritt 5.1, einziger Schritt dieser Phase):** `PriceStats`
um vier rein informative Felder erweitert: `percentile_25`,
`percentile_90` (P90 wurde intern bereits berechnet, jetzt zusätzlich
gespeichert), `data_age_days` (Tage seit dem jüngsten Datenpunkt der
Gruppe), `confidence` (`"LOW"`/`"MEDIUM"`/`"HIGH"`). Alle vier mit
Defaults — rückwärtskompatibel zu bestehenden `PriceStats(...)`-
Konstruktionsstellen (`test_top_deal.py`, `test_app_resale_price_groups.py`
— beide nutzen ausschließlich Keyword-Argumente, kein Regressionsrisiko
durch die neuen Felder am Ende der Dataclass).

**Confidence-Klassifizierung:** ausschließlich an der Datenpunkt-Anzahl
festgemacht (`count`), bewusst NICHT zusätzlich mit `data_age_days`
verknüpft — zwei überlagerte Schwellen in einem Label wären weniger
nachvollziehbar. `LOW` deckt sich mit der bestehenden
`_MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE`-Schwelle (5) — dort ist
`estimated_resale_price` ohnehin bereits `None`. `MEDIUM`: 5–14.
`HIGH`: ab 15 (Platzhalter-Schwelle, Robins Freigabe, mangels echter
Kalibrierungsdaten für dieses neue Feld).

**Bestehende Regel "< 5 Datenpunkte → kein Flip-Kandidat" nicht
verschlechtert** (roadmap.md-Vorgabe): `_estimated_resale_price()` selbst
wurde nicht angefasst, die neuen Felder sind rein additiv und beeinflussen
`market_price`/`estimated_resale_price`/Deal-Score/Notification-Gate
NICHT — per eigenem Regressionstest abgesichert
(`test_confidence_und_neue_perzentile_sind_rein_informativ`).

**`resale_price_group`-Konzept:** automatisch mit abgedeckt, ohne
eigenen Code — `compute_resale_stats_by_group()` (Abschnitt 33b, Option 2)
ruft intern dieselbe `compute_price_stats()`-Funktion auf, liefert also
für jede Resale-Gruppe dieselben neuen Felder (P25/P90/Datenalter/
Confidence) wie für einzelne Modelle.

**Dashboard-Anbindung:** `PriceStats` wird per `asdict()` in
`/api/price-history` serialisiert (Schritt 3.3) — die neuen Felder stehen
damit automatisch im Backend zur Verfügung, ohne `api/history.py`
anzufassen. Tatsächliche Dashboard-Darstellung (Confidence-Badge o.ä.)
ist Teil von Phase 8, nicht dieser Phase.

**Geänderte Dateien:** `app/price_stats.py` (+45 Zeilen: 370 → 415),
`app/tests/test_price_stats.py` (+9 Tests).

**Teststand:** `pytest app/tests/` → **625 passed, 0 failed** (616 + 9
neue).

Phase 5 gilt damit als abgeschlossen.

---

## 13. `roadmap.md` Phase 6 (Deal-Score vervollständigen) — ABGESCHLOSSEN

**Präzisierter Ausgangsbefund (L8):** Von den ursprünglich "3 von 6
ungenutzten Komponenten" war nur eine wirklich ohne Detector —
`hersteller` hatte bereits Detector + Reputationstabelle, nur das Gewicht
stand auf 0.

**Umsetzung, vier Teilschritte:**
- **6a — Hersteller aktiviert:** `scoring_weights.hersteller` 0 → 0.05
  in `_global.yaml`, reine YAML-Änderung, kein Code. `compute_deal_score()`
  normalisiert automatisch, übrige Gewichte unverändert.
- **6b — Zustand-Detector gebaut:** `categories/detectors/condition.py`,
  Vokabular exakt aus dem Auftrag (neu/wie neu/sehr gut/gut/gebraucht/
  beschädigt/defekt/Bastler) + deutsche Adjektiv-Flexionsformen
  (gebrauchter/defektes/in gutem Zustand). Zwei Regex-Bugs bei der
  Entwicklung selbst gefunden und behoben. Nur Titel (keine Beschreibung
  — `evaluate()` bekommt aktuell keinen `description`-Parameter).
- **6c — Lieferumfang-Detector gebaut:** `categories/detectors/
  lieferumfang.py`, positive Signale (OVP/Rechnung/Originalzubehör/
  Netzteil/Controller/Zubehör) und negative Signale (ohne Netzteil/nur
  Gerät/defekt) — anders als Zustand mehrere gleichzeitige Signale pro
  Titel möglich, daher zwei Listen statt einem Label. Zwei Bugs
  (Doppelzählung "original Zubehör", Fehlsignal bei "kein Zubehör")
  gefunden und per Lookbehind behoben.
- **6d — Beide Detectors verdrahtet:** `matcher.py::_build_score_inputs()`
  ruft beide auf, neue Scoring-Funktionen `_zustand_score()`/
  `_lieferumfang_score()` in `deal_score.py` (Muster wie
  `_hersteller_score()`), zwei neue YAML-Tabellen (`condition_scores`,
  `lieferumfang_signal_scores`, Platzhalter-Kalibrierung).

**Gewichte `zustand`/`lieferumfang` bleiben bei 0** — bewusst, exakt nach
roadmap.md-Vorgabe ("Keine Gewichtung aktivieren, solange die Erkennung
nicht ausreichend zuverlässig getestet ist"). Per Regressionstest gegen
die echte produktive `_global.yaml` abgesichert: ein Titel mit
erkennbarem Zustand/Lieferumfang liefert exakt denselben Score wie ein
sonst identischer Titel ohne solche Angaben — die Detectors sind aktiv
und sichtbar (`DealScoreResult.components`), aber wirkungslos auf den
Gesamt-Score, bis eine bewusste Aktivierungsentscheidung fällt (wie bei
`hersteller` in 6a).

**Geänderte Dateien:** `app/categories/detectors/condition.py` (neu),
`app/categories/detectors/lieferumfang.py` (neu), `app/matcher.py`,
`app/scoring/deal_score.py`, `app/rules/_global.yaml`,
`app/tests/test_detector_condition.py` (neu, 22 Tests),
`app/tests/test_detector_lieferumfang.py` (neu, 21 Tests),
`app/tests/test_deal_score.py` (+12), `app/tests/
test_matcher_deal_score_integration.py` (+7).

**Teststand:** `pytest app/tests/` → **687 passed, 0 failed** (625 + 62
neue über die vier Teilschritte).

**Offener Folgepunkt (nicht Teil dieser Phase):** Aktivierung von
`zustand`/`lieferumfang` (Gewicht > 0) erst nach Verlässlichkeitsprüfung
an echten Produktivtiteln — analog zum bereits etablierten Vorgehen bei
`hersteller`.

Phase 6 gilt damit als abgeschlossen.

---

## 14. `roadmap.md` Phase 7 (Deal Intelligence) — ABGESCHLOSSEN

**Umsetzung, zwei Teilschritte:**
- **7a — `deal_intelligence.py` gebaut:** reine Funktion `classify_deal()`,
  führt drei bereits bestehende Signale zusammen — `is_top_deal`
  (`top_deal.py`), `estimated_margin_pct` (`scoring/profit.py`),
  `deal_stars` (`scoring/deal_score.py`) — zu einer gemeinsamen
  Einstufung: TOP DEAL > FLIP DEAL > VERY GOOD DEAL > WATCH. **Keine
  neuen Schwellenwerte** — importiert exakt dieselben Konstanten
  (`MIN_FLIP_MARGIN_PCT`, `TOP_DEAL_SCORE_THRESHOLD_A` über
  `stars_meet_minimum`), die bereits die KPI-Zählung in `api/status.py`
  verwendet. Per Gegenprobe an 5 Beispieldatensätzen deckungsgleich mit
  der bestehenden Logik verifiziert.
- **7b — Verdrahtung:** `run_scan()` berechnet `classify_deal()` pro
  Treffer, plus Time-to-Sell-Kategorie-Lookup (`expected_days_to_sell`,
  rein informativ, Median-Verweildauer der Kategorie — NICHT des
  Einzelangebots, das ist für ein noch aktives Angebot per Definition
  unbekannt). Drei neue additive `found.json`-Felder:
  `deal_intelligence_label`, `deal_intelligence_emoji`,
  `expected_days_to_sell`.

**Kein Einfluss auf bestehende Systeme** (roadmap.md-Vorgabe wörtlich
erfüllt: "Bestehende Systeme nicht ersetzen, sondern zusammenführen"):
`deal_score`, Notification-Gate und die bisherige Top-Deal-Logik bleiben
unverändert. Regressionsschutz-Test stellt sicher, dass `is_top_deal=True`
immer `deal_intelligence_label == "TOP DEAL"` ergibt (keine
widersprüchlichen Signale zwischen altem und neuem Feld).

**Geänderte Dateien:** `app/deal_intelligence.py` (neu), `app/app.py`,
`app/tests/test_deal_intelligence.py` (neu, 13 Tests),
`app/tests/test_app_deal_intelligence_field.py` (neu, 3 Tests).

**Teststand:** `pytest app/tests/` → **703 passed, 0 failed** (687 + 16
neue).

Phase 7 gilt damit als abgeschlossen.

---

## 15. `roadmap.md` Phase 8 (Notifications optimieren) — ABGESCHLOSSEN

**Umsetzung, zwei Teilschritte:**
- **8a — Cross-Posting-Duplikate von Notifications ausgeschlossen:**
  `find_duplicate()` (bereits vorhanden, wirkte bisher nur auf die
  Preishistorie) wird jetzt zusätzlich als dritte Notification-Gate-
  Bedingung genutzt (`not is_duplicate`). Behebt die einzige real
  bestehende Lücke bei "bereits gemeldetes Angebot → nicht erneut
  melden" — für identische URLs war das durch `seen.json` ohnehin
  bereits erfüllt. Per Gegenprobe verifiziert (Fix entfernt → Test
  wird rot → wiederhergestellt → grün).
- **8b — Priorität verfeinert:** neue Funktion `_notification_priority()`
  — zusätzlich zum bisherigen preisbasierten `urgent`-Fall löst jetzt
  auch ★★★★☆/★★★★★ + Preisvorteil ≥ 25 % (wiederverwendete
  `TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT`, keine neue Zahl) `urgent` aus.
  Logik bewusst in eine reine, separate Funktion extrahiert (statt
  inline im Notification-Block) — direkt testbar, u. a. exakter
  Grenzwert (25,0 % vs. 24,9 %) und expliziter Regressionsschutz für
  den unveränderten preisbasierten Fall.

**Kein Ersatz des bestehenden Gates** (roadmap.md-Vorgabe wörtlich
erfüllt: "Bestehendes Notification-Gate nicht unnötig ersetzen"): beide
Schritte sind reine, ODER-/UND-verknüpfte Ergänzungen um bereits
vorhandene Signale (`find_duplicate()`, `top_deal_result.discount_pct`).

**Geänderte Dateien:** `app/app.py`,
`app/tests/test_app_duplicate_detection.py` (+1 Test),
`app/tests/test_app_notification_priority.py` (neu, 10 Tests).

**Teststand:** `pytest app/tests/` → **714 passed, 0 failed** (703 + 11
neue).

Phase 8 gilt damit als abgeschlossen.

---

## 16. `roadmap.md` Phase 9 (Duplicate Detection verbessern) — ABGESCHLOSSEN (eingegrenzt)

**Wichtigster Befund der Analyse:** Von den in roadmap.md vorgeschlagenen
Zusatzsignalen (Quelle, Titel, Seller, Location, Preis, Bilder) sind
**Seller und Bilder aktuell gar nicht verfügbar**: kein Scraper extrahiert
einen Verkäufernamen; `images` wird nur von `quoka.py` befüllt
(`kleinanzeigen.py`/`ebay.py` liefern immer `[]`). Eine Nutzung hätte
zuerst scraperseitige Erweiterungen vorausgesetzt — auf Wunsch bewusst
**nicht umgesetzt** (Robins Entscheidung). `location` bleibt weiterhin
bewusst ausgeschlossen (bereits vor dieser Session begründet:
Kleinanzeigen-Ortsangaben zu ungenau).

**Umsetzung, eingegrenzt auf verlässlich verfügbare Signale:**
wortstellungs-unabhängiger Fingerprint-Vergleich — "Asus RTX 3060 12GB"
und "RTX 3060 12GB Asus" gelten jetzt als dasselbe Angebot. Neue Funktion
`_fingerprint_words()` (sortierte Wortfolge) in `find_duplicate()`
verwendet, `normalize_title()` selbst bewusst **unverändert** (Wort-
reihenfolge im gespeicherten Fingerprint bleibt erhalten — kein
Formatwechsel, keine Migration bestehender `price_history.jsonl`-Zeilen
nötig). `sorted()` statt `set()`: Wort-*Häufigkeit* bleibt weiterhin
unterscheidungsrelevant (keine Lockerung der Erkennungsgenauigkeit,
roadmap.md-Vorgabe "keine aggressiven False-Positive-Regeln" eingehalten).

**Geänderte Dateien:** `app/duplicate_detection.py`,
`app/tests/test_duplicate_detection.py` (+3 Tests).

**Teststand:** `pytest app/tests/` → **717 passed, 0 failed** (714 + 3
neue).

**Offener, bewusst zurückgestellter Punkt:** Seller-/Bilder-basierte
Erkennung — erst sinnvoll nach einer eigenen, separaten
Scraper-Erweiterung (nicht Teil dieser Phase).

Phase 9 gilt damit als abgeschlossen.

---

## 17. `roadmap.md` Phase 10 (Automatische Datenqualitätskontrolle) — ABGESCHLOSSEN

**Analyse-Ergebnis:** Von den fünf in roadmap.md genannten Warnsignalen
sind zwei praktisch kostenlos aus bereits vorhandenen Daten ableitbar
(dünne Preishistorie über `PriceStats.confidence`, Phase 5; veraltete
Kategorie über `price_history.jsonl`), eines mit vorhandenen Zählwerten
strukturierbar (Kategorie-Trefferquote), eines bewusst nicht umgesetzt
(siehe unten).

**Wichtiger Befund:** `found.json` ist für "N Tage keine Treffer"
ungeeignet — wird nach `DEAL_MAX_AGE_DAYS` (Default 7 Tage) automatisch
bereinigt, würde sich bei einer Prüfung nahe dieser Schwelle selbst ins
Leere laufen. `price_history.jsonl` (append-only) ist die verlässliche
Quelle.

**Schritt 10a:** neues Modul `data_quality.py` —
`check_thin_price_history()` (nutzt `PriceStats.confidence`, keine neue
Schwelle) und `check_stale_categories()` (Kategorien ohne neuen
`price_history.jsonl`-Punkt seit >7 Tagen, Schwelle wörtlich aus
roadmap.md übernommen). Zunächst bewusst nicht verdrahtet.

**Schritt 10b:** `check_zero_match_categories()` ergänzt — nutzt
`len(bucket)` je Kategorie, das `run_scan()` beim Aufbau der
`category_buckets` ohnehin schon erzeugt (bisher nur als Log-Zeile
sichtbar), keine neue Zählung nötig. Alle drei Prüfungen jetzt am
Scan-Ende in `run_scan()` verdrahtet, Ergebnisse werden geloggt
(`⚠️ Datenqualität [...]`) — reine Beobachtungsschicht, kein Einfluss auf
`deal_score`/Notification-Gate/Matching. Dashboard-Anzeige ist bewusst
NICHT Teil dieser Phase (roadmap.md behandelt "Dashboard" als eigenen,
separaten Abschnitt außerhalb der nummerierten Phasen).

**Bewusst NICHT umgesetzt:** "Regel: 91% ausgeschlossen"
(feingranulare Ausschlussquote je einzelner YAML-Regel) — hätte eine
Instrumentierung innerhalb von `matcher.py::evaluate()`s Kernschleife
vorausgesetzt (deutlich invasiver als alle übrigen Prüfungen, die nur
bereits vorhandene End-Ergebnisse auswerten). `check_zero_match_categories()`
liefert dafür eine erreichbare Annäherung ohne Eingriff in die zentrale
Matching-Logik.

**Geänderte Dateien:** `app/data_quality.py` (neu, 187 Zeilen),
`app/app.py` (Verdrahtung), `app/tests/test_data_quality.py` (neu, 20
Tests), `app/tests/test_app_data_quality_wiring.py` (neu, 2
End-to-End-Tests).

**Teststand:** `pytest app/tests/` → **739 passed, 0 failed** (717 + 22
neue über beide Teilschritte).

Phase 10 gilt damit als abgeschlossen.

---

## Roadmap (Phasen 0–10) vollständig abgeschlossen

Damit ist die in `roadmap.md` unter "Empfohlene Reihenfolge" definierte
komplette Phasen-Sequenz (0 Analyse → 1 Doku-Sync → 2 Performance messen
→ 3 app.py modularisieren → 4 Persistenz → 5 Price-History/Resale-
Confidence → 6 Deal-Score → 7 Deal Intelligence → 8 Notifications → 9
Duplicate Detection → 10 Datenqualitätskontrolle) durchlaufen. Jede Phase
wurde einzeln analysiert, umgesetzt, getestet und dokumentiert (siehe
Abschnitte 9–17 oben), mit vollständiger Testabdeckung nach jedem
einzelnen Schritt (kein Rückgang der Testanzahl, keine geschwächten
Tests).

**Bewusst nicht Teil dieser Roadmap-Phasen** (roadmap.md behandelt sie
als eigene, nachgelagerte Abschnitte, nicht als nummerierte Phasen):
Dashboard-Weiterentwicklung, sowie mehrere im Projektverlauf bewusst
zurückgestellte Einzelpunkte:
- `run_scan()` (~534 Zeilen) nicht weiter modularisiert (Abschnitt 10:
  46 modul-globale Abhängigkeiten, Risiko/Nutzen-Abwägung)
- Aktivierung der Deal-Score-Komponenten `zustand`/`lieferumfang`
  (Gewicht > 0) — Detectors gebaut und verdrahtet (Abschnitt 13), aber
  noch nicht an echten Produktivtiteln verlässlichkeitsgeprüft
- Seller-/Bilder-basierte Duplicate Detection (Abschnitt 16) — setzt
  eine eigene Scraper-Erweiterung voraus, auf Wunsch nicht umgesetzt
- Regel-Ausschlussquote je YAML-Regel (Abschnitt 17) — hätte eine
  invasivere Instrumentierung von `matcher.py::evaluate()` vorausgesetzt

Diese vier Punkte sind bewusste, begründete Auslassungen (Risiko/Nutzen-
bzw. Aufwand/Nutzen-Abwägung oder ausdrücklicher Wunsch des
Auftraggebers), keine übersehenen Lücken.

---

## 18. Phase 11 (Flip-Kandidaten und neue Kategorien korrigieren) — ABGESCHLOSSEN

**Vorab: Repository-Sync.** Der Sandbox-Klon war 12 Commits hinter
`origin/main` (unabhängig weiterentwickelt, deckt sich inhaltlich exakt
mit den bis Phase 10a vorgeschlagenen Änderungen). Per
`git reset --hard origin/main` synchronisiert, ein dabei fehlender Test
wiederhergestellt (738/738 grün vor Phase-11-Beginn).

**A) Ursache der überhöhten Flip-Kandidaten-Zahl:** `api/status.py` und
`deal_intelligence.py` nutzten beide ausschließlich
`estimated_margin_pct >= MIN_FLIP_MARGIN_PCT` (20 %) — ohne absolute
Marge, Deal-Score oder Resale-Confidence. Ein 15 €-Artikel mit 3 €
absolutem Gewinn zählte damit genauso wie ein 300 €-Artikel mit 100 €
Gewinn.

**Fix:** `scoring/profit.py::is_robust_flip_candidate()` — Single Source
of Truth für beide bisherigen Aufrufstellen, prüft ALLE VIER Faktoren
(`margin_pct >= 20 %` UND `margin_eur >= 30 €` UND `deal_score >= 75`
UND `resale_confidence != LOW`, Robins Phase-11-Startwerte). Dafür wurde
`resale_confidence` (aus `PriceStats.confidence`, Phase 5) erstmals bis
`MatchResult`/`found.json` durchgereicht (`_resale_confidence_from_stats()`
in `services/statistics_service.py`, spiegelt exakt die Gruppen-/
Fallback-Logik von `_resale_prices_from_stats()`).

**B) Sichere Re-Evaluierung (an Robins Vorgabe angepasst):**
`matcher.compute_ruleset_signature()` — bewusst EIN globaler Hash über
alle matching-relevanten Regelfelder, kein Hash pro Kategorie (Begründung:
`evaluate()` iteriert bereits linear durch alle Regeln aller Kategorien
in einem Durchlauf, first-match-wins — ein Pro-Kategorie-Hash hätte
keinen Verhaltensunterschied, nur mehr Zustand, siehe Docstring).
`presence_tracking.needs_reevaluation()`: **nur** Angebote, die NIE
gematcht wurden (`category is None`) UND deren Ruleset-Hash veraltet
ist, werden erneut evaluiert. Bereits gematchte Angebote werden NIE
erneut evaluiert — zentrale Sicherheitsgarantie gegen doppelte
Preishistorie/Notifications, per eigenem Test abgesichert.

**C) `cpu_mainboard_bundle = 0 Treffer`:** Ursache ist derselbe
Mechanismus wie A — Angebote, die vor dem jüngsten YAML-Fix (Stand
2026-08-08: Word-Boundary-Bug 5600X/3600X, Preis-Rekalibrierung
Ryzen-5600) bereits gescannt und nie gematcht wurden, saßen dauerhaft in
`seen.json` fest. Per synthetischem End-to-End-Test bestätigt: ein
zuvor "seen, nie gematcht"-Angebot mit realistischem Bundle-Titel wird
nach dem Fix korrekt der Kategorie `cpu_mainboard_bundle` zugeordnet.
**Zusätzlich dokumentiert, nicht geändert** (Auftrags-Vorgabe): die
Preisgrenzen der Ryzen-3600-Combo (55 €/75 €) und der i5-12400F-Combo
(100 €/130 €) wurden laut YAML-Kommentar nie mit echten Marktdaten
verifiziert und wirken unrealistisch niedrig — Kalibrierung ist
ausdrücklich Phase 12 vorbehalten.

**Geänderte Dateien:** `scoring/profit.py`, `services/statistics_
service.py`, `matcher.py`, `presence_tracking.py`, `app.py`,
`api/status.py`, `deal_intelligence.py`, plus Tests in `test_profit.py`
(+8), `test_matcher_ruleset_signature.py` (neu, 8), `test_presence_
tracking.py` (+9), `test_app_presence_tracking.py` (2 ersetzt 1),
`test_deal_intelligence.py` (7 ersetzen 4), `test_app_status_kpis.py`
(1 aktualisiert).

**Teststand:** `pytest app/tests/` → **766 passed, 0 failed** (738 vor
Phase 11 + netto 28 neue/aktualisierte).

**Offene Punkte für Phase 12:**
- Vollständige Preisgrenzen-Kalibrierung aller Kategorien (explizit
  ausgeklammert in Phase 11)
- Insbesondere: Ryzen-3600- und i5-12400F-Bundle-Preisgrenzen (siehe C)
- Beobachten, ob die Phase-11-Startwerte (20 %/30 €/75/nicht-LOW) nach
  echten Produktivdaten nachjustiert werden müssen

Phase 11 gilt damit als abgeschlossen.

---

## 19. Neue Kategorie „autoradio_opel_corsa" — VORBEREITET, NICHT COMMITTET

**Wichtig — Abgrenzung zu allen Abschnitten oben:** Alle bisherigen
Abschnitte (1–18) beschreiben den tatsächlichen, committeten Zustand von
`origin/main` (Commit `d2effe7`, Working Tree clean). Dieser Abschnitt
beschreibt einen in einer separaten Dev-Session **vorbereiteten, lokal
verifizierten, aber noch nicht ins Repo eingespielten** Änderungsvorschlag.
Diese Session hatte keinen Schreibzugriff auf `origin/main` — die Datei
`app/rules/autoradio_opel_corsa.yaml` existiert in `origin/main` bislang
**nicht**.

**Auslöser:** Nutzerwunsch, eine neue Hardware-Kategorie für Android-
Autoradios im Opel-Design (Plug & Play, Opel Corsa D) zu ergänzen — als
Praxistest der bestehenden Plugin-Architektur (Abschnitt „Phase 10",
Kategorien = reine YAML-Ergänzung, kein Code-Zugriff nötig).

**A) Plugin-Kontrakt verifiziert.** Die vom Nutzer bereitgestellte YAML
wurde unverändert in eine isolierte Kopie von `rules/` geladen
(`matcher.load_rules()` + `categories/registry.discover_categories()`)
und gegen Beispieltitel ausgewertet. Ergebnis: Kategorie wird ohne jede
Code-Änderung erkannt (`category`, `label`, `search_terms`,
`exclude_category`, `notify_max_price`, `rules` mit `require_all_of`/
`exclude`/`max_price`/`deal_rating`/`price_history_model` — identisches
Schema zu `rules/gpu.yaml`). Bestätigt exakt den in
`tests/test_rules_category_plugin_contract.py` bewiesenen Kontrakt für
eine reale, nicht-synthetische Kategorie.

**B) Deal-Score-Gewichtung ergänzt.** Ohne kategorie-eigene
`scoring_weights` greift der globale Default aus `_global.yaml`
(Preis 70 % / Ausstattung 15 % / Hardwarequalität 15 % / Hersteller 5 %).
Da diese Kategorie ausschließlich titelbasiert matcht
(`require_all_of`, kein `requirements:`-Block wie bei Office-/
Gaming-PC), liefern `ausstattung` und `hersteller` strukturell nur den
neutralen Platzhalterwert (`_PLACEHOLDER_SCORE = 60`, siehe
`scoring/deal_score.py`) — kein echtes Signal. Ergänzt wurde ein
kategorie-eigener Block, analog zum bereits produktiven Muster in
`rules/gpu.yaml`:

```yaml
scoring_weights:
  price: 0.7
  ausstattung: 0
  hardware_qualitaet: 0.1
  hersteller: 0
  zustand: 0
  lieferumfang: 0
  profit: 0.2
```

**C) Bekannte Einschränkung (dokumentiert, nicht behoben — identisch zu
GPU-Kategorie).** Verifiziert gegen Beispieltitel: Der `price`-Score
(`_rule_based_price_score()`) berechnet sich aus `(1 - Preis/max_price) *
100`. Bei einem Preis nahe der `max_price`-Grenze der jeweiligen Regel
(z.B. 95 € gegen `max_price: 100`) bleibt der Preis-Score niedrig
(~5/100) — unabhängig von der Gewichtung. ★★★★★ (Score ≥ 95) ist mit den
aktuellen `max_price`-Werten der Regeln praktisch **nicht erreichbar**,
solange (a) keine Angebote deutlich unter `max_price` liegen oder (b)
keine lokale Preishistorie/`profit`-Daten für die jeweiligen
`price_history_model`-Schlüssel aufgebaut sind. Exakt dasselbe
Verhalten wie bei `rules/gpu.yaml` (dort im YAML-Kommentar begründet) —
kein neuer Bug, sondern eine bekannte Eigenschaft des Preis-Score-
Modells bei frisch angelegten Kategorien ohne Marktdaten.

**Geänderte/neue Dateien (lokal, NICHT committet):**
- `app/rules/autoradio_opel_corsa.yaml` (neu)

**Empfohlene Tests vor dem Einspielen:**
- `pytest app/tests/test_rules_category_plugin_contract.py -q`
- Manueller Smoke-Test: `matcher.load_rules()` + `evaluate()` gegen
  reale Kleinanzeigen-Titel vor Produktivgang

**Offene Punkte:**
- `max_price`-Werte je Regel (90–240 €, je nach Marke/Rating) sind laut
  YAML-Kommentar noch nicht mit echten Marktdaten kalibriert — analog zu
  den in Abschnitt 18 offen dokumentierten Ryzen-3600-/i5-12400F-
  Bundle-Preisgrenzen.
- Regelreihenfolge: die allgemeine Regel „Android-Designradio" steht in
  der YAML VOR den markenspezifischen Regeln (JUNSUN/Eonon/A-Sure/
  Xtrons/Joying) — bei first-match-wins (`matcher.evaluate()`) fängt die
  allgemeine Regel Treffer ab, bevor die (großzügigeren) marken-
  spezifischen `max_price`-Grenzen greifen können. Noch nicht mit dem
  Auftraggeber geklärt, ob das gewünscht ist.
- Datei noch nicht committet/gepusht (kein Schreibzugriff in dieser
  Session) — Integration in `origin/main` steht aus.

Abschnitt 19 gilt als **vorbereitet, Freigabe zur Übernahme steht aus.**
