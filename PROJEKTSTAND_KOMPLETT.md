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

Warte auf Freigabe für den nächsten Schritt.
