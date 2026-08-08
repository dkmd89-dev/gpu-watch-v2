# PROJEKTSTAND_KOMPLETT.md — gpu-watch-v2 / Hardware Deal Finder

> Diese Datei ist die einzige verlässliche Referenz für den Ist-Zustand des
> Projekts. Jede Angabe wurde gegen den realen Code verifiziert (Dateisystem,
> `git log`/`status`, echter `pytest`-Lauf — **569/569 Tests grün**).
> Stand: Repo `main`, letzter Commit `ac09d06`, 4 Commits vor `origin/main`.
> Ersetzt/ergänzt `PHASE_0_ANALYSE_VERIFIZIERT.md`. Keine Code-Änderungen in
> Phase 0 oder Phase 1 vorgenommen.

---

## 1. Zweck & Scope

Hardware Deal Finder für Second-Hand-Angebote (primär Kleinanzeigen, dazu
eBay und Quoka), der Angebote nach Deal-Potenzial bewertet und bei starken
Treffern per ntfy benachrichtigt. Reale Kategorien-Abdeckung geht über den
im Entwicklungsauftrag beschriebenen PC-Fokus hinaus (Details: Abschnitt 6).

## 2. Repo-Zustand

```
Branch: main (4 Commits vor origin/main)
Letzter Commit: ac09d06 fix(presence-tracking): fehlende prune_delisted_entries() ergänzt + Repo-Bereinigung
Uncommittet:
  D  .env.0.tmp
  M  data/time_to_sell.jsonl (Laufzeitdaten)
```
Tests: `pytest app/tests/` → **569 passed** (43 s, keine Fehler/Skips).

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
| CPUs (eigene Kategorie) | ❌ fehlt — Detector `cpu.py` existiert, aber keine eigenständige CPU-Kategorie-YAML |
| Mainboards | ❌ fehlt — kein Detector, keine YAML |
| RAM (eigene Kategorie) | ❌ fehlt — Detector `ram.py` existiert (für PC-Anforderungsprüfung), keine eigenständige RAM-Kategorie |
| SSDs | ⚠️ teilweise — `sata_ssd.yaml` existiert (SATA-SSD als Einzelkategorie), NVMe als eigene Kategorie fehlt |
| Netzteile | ✅ implementiert (`netzteil.yaml`) |
| Monitore | ⚠️ teilweise — `monitor_curved.yaml` existiert (nur Curved-Segment), keine allgemeine Monitor-Kategorie |
| Notebooks | ❌ fehlt als PC-Notebook-Kategorie — `macbook.yaml` deckt nur Apple-Notebooks ab (anderer Scope, s. u.) |

**Zusätzlich vorhanden, außerhalb der Auftrags-Zielliste:** `iphone.yaml`,
`macbook.yaml`, `retro_konsolen.yaml`, `vintage_elektronik.yaml`,
`lego_minifiguren.yaml` — fünf Kategorien ohne PC-Hardware-Bezug.

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

Diese Logik ist bereits durch 569 Tests abgesichert und produktiv im
Einsatz — sie sollte in Phase 1 bewusst als **bestehender Bestandteil**
behandelt werden, nicht als etwas, das "neu geplant" werden muss.

## 8. Bekannte Lücken & offene Punkte

| # | Lücke | Auswirkung | Vorschlag Priorität |
|---|---|---|---|
| L1 | 6 der 8 PC-Hardware-Zielkategorien aus dem Auftrag fehlen ganz/teilweise (CPU, Mainboard, RAM, NVMe-SSD, allg. Monitor, Notebook) | Auftragsziel "modularer Hardware Deal Finder" ist zur Hälfte offen | Hoch — Kern des Auftrags |
| L2 | Detector-Ebene ist NICHT codefrei erweiterbar (Abschnitt 5) | Neue Kategorien mit neuem Hardware-Merkmal brauchen Python-Änderung | **Entschieden (siehe Abschnitt 9a)** — bewusst kontrolliert bei statischen Imports geblieben |
| L5 | `seen.json`/`found.json` wachsen unbegrenzt (14 MB / 2,1 MB) | Perf./Speicher langfristig | Mittel |
| L6 | Scope-Drift: 5 Nicht-PC-Kategorien | Klärungsbedarf, kein Bug | Entscheidung nötig, keine technische Priorität |
| L7 | `app.py` als 977-Zeilen-Monolith (Routen + Scan-Loop + Scheduler in einer Datei) | Wartbarkeit bei weiterem Wachstum | Niedrig, vorausschauend |
| L8 | Hersteller/Zustand/Lieferumfang-Scoring-Gewichte bewusst auf 0 (kein Detector für Zustand/Lieferumfang) | Deal-Score nutzt nur 3 von 6 Komponenten aktiv | Mittel, hängt von L1/L2 ab |

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
laufenden Pfad (569 Tests hängen daran) und nachweislich geringem Nutzen,
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
5. **L6 (Scope-Drift)** vor Schritt 3 entscheiden: bleiben Nicht-PC-
   Kategorien bestehen (kein Aufwand, laufen unabhängig) oder werden sie
   bewusst aus dem Fokus genommen (rein organisatorisch, kein Löschen
   nötig, da YAML-Plugins isoliert sind).

---

**Keine Code-Änderungen vorgenommen (Phase 0 + Phase 1 abgeschlossen).**
Warte auf Freigabe, mit welchem Punkt aus Abschnitt 9 konkret begonnen
werden soll (Empfehlung: Punkt 1, dann Punkt 2 als Entscheidung, dann
Punkt 3 Schritt für Schritt).
