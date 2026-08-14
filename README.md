# GPU Watch v2

Ein selbst gehosteter Deal-Scanner für Kleinanzeigen, eBay und Quoka,
der gebrauchte Hardware- und Elektronik-Angebote automatisch erkennt,
bewertet und bei guten Preisen per Push-Benachrichtigung meldet.

Ursprünglich für GPU-Angebote gebaut, mittlerweile auf 19 Kategorien
gewachsen (siehe unten) — von Grafikkarten über Konsolen und Handhelds
bis zu iPhones und MacBooks.

## Funktionsweise

1. **Scan** — durchsucht periodisch konfigurierte Quellen
   (Kleinanzeigen, eBay, Quoka) nach neuen Angeboten.
2. **Matching** — gleicht jeden Angebotstitel gegen ein YAML-basiertes
   Regelwerk (`app/rules/*.yaml`) ab: Kategorie, Preisgrenzen,
   Ausschlussbegriffe. Bei Treffer wird das Angebot einer konkreten
   Regel (z.B. „RTX 4070 Ti ★ Top-Deal“) zugeordnet.
3. **Scoring** — berechnet einen Deal-Score aus Preis, Ausstattung,
   Hardware-Qualität, Hersteller, Zustand und Lieferumfang (Gewichtung
   pro Kategorie konfigurierbar) sowie eine Top-Deal-/Flip-Einstufung
   auf Basis der historischen Preisverteilung.
4. **Persistenz** — Preisverlauf (`price_history.jsonl`, append-only),
   aktueller Fundbestand (`found.json`) und Presence-/Delisting-Tracking
   (`seen.json`) werden lokal unter `data/` gespeichert.
5. **Benachrichtigung** — Angebote, die eine Mindestbewertung und
   Preisgrenze überschreiten, werden per [ntfy](https://ntfy.sh) als
   Push-Nachricht verschickt.
6. **Dashboard** — eine Flask-Weboberfläche zeigt den aktuellen
   Fundbestand, gefiltert nach Kategorie/Deal-Typ, inkl. Marktwert- und
   Flip-Kandidaten-Anzeige.

## Quickstart

Voraussetzung: Docker + Docker Compose.

```bash
cp .env.example .env   # anlegen, siehe "Konfiguration" unten
docker compose up -d --build
```

Das Dashboard ist danach unter `http://localhost:5000` erreichbar.

## Konfiguration

Alle Einstellungen erfolgen über Umgebungsvariablen (`.env`, wird von
`docker-compose.yml` eingebunden):

| Variable | Default | Beschreibung |
|---|---|---|
| `NTFY_TOPIC` | — | ntfy-Topic für Push-Benachrichtigungen (ohne Topic keine Benachrichtigungen) |
| `NTFY_SERVER` | `https://ntfy.sh` | ntfy-Server, z.B. eigene Instanz |
| `SCAN_INTERVAL_MINUTES` | `10` | Abstand zwischen zwei Scan-Durchläufen |
| `DATA_DIR` | `/data` | Datenverzeichnis (im Compose-Setup auf `./data` gemountet) |
| `FOUND_MAX_ITEMS` | `200` | Maximale Anzahl aktiver Treffer im Dashboard (Rotation) |
| `DEAL_MAX_AGE_DAYS` | `7` | Nach wie vielen Tagen ein Fund aus dem aktiven Bestand fällt |
| `SEEN_MAX_ITEMS` | `50000` | Obergrenze für das Presence-Tracking (`seen.json`) |
| `SEEN_DELISTED_MAX_AGE_DAYS` | `3` | Aufbewahrungsdauer delisteter Einträge im Presence-Tracking |

Globale Benachrichtigungs-Schwellen (Mindestbewertung, Preisgrenze) und
kategorieweite Ausschlussbegriffe stehen in `app/rules/_global.yaml`.

## Regelwerk erweitern

Jede Kategorie ist eine eigenständige YAML-Datei unter `app/rules/`:

```yaml
category: "beispiel"
label: "Beispiel-Kategorie"
search_terms: ["Suchbegriff A", "Suchbegriff B"]
exclude_category: ["hülle", "ersatzteil"]   # kategorieweite Ausschlüsse

rules:
  - label: "Beispielgerät ★ Top-Deal"
    require_all_of:
      - ["begriff a", "alternative a"]      # Gruppe 1: mind. einer davon
      - ["begriff b"]                       # Gruppe 2: UND mind. einer davon
    exclude: ["defekt", "bastler"]
    max_price: 100
    deal_rating: "Top-Deal"
```

Aktuell abgedeckte Kategorien: GPUs, Gaming-/Office-PCs, CPU+Mainboard-
Bundles, RAM, Netzteile, M.2-/SATA-SSDs, Curved-Monitore, Handhelds
(Steam Deck, ROG Ally, 3DS, PS Vita, ...), Controller, moderne
Konsolen-Bundles, Retro-Konsolen, iPhones, MacBooks, Notebooks (Resell),
Autoradios (Opel Corsa), LEGO-Minifiguren, Vintage-Elektronik.

Vor jeder Regeländerung empfiehlt sich ein Lauf des read-only
Diagnose-Moduls `app/rule_analyzer.py` (prüft u.a. auf unerreichbare
Regeln, Duplikate und Exclude-Konflikte) sowie die Testsuite.

Für das Ruleset-Qualitätstooling (Benchmark-, Coverage- und
Cross-Category-Analysen, ebenfalls read-only und kein Bestandteil der
Produktionskette) siehe
[`tools/ruleset_quality/README.md`](tools/ruleset_quality/README.md).

Alle 19 Kategorien wurden im Rahmen eines systematischen
Active-False-Positive-Audits einmal vollständig gegen den echten
Produktivkorpus geprüft (113 real bestätigte Fehltreffer über 14
Kategorien behoben, 4 Kategorien ohne Befund) — Details und
Methodik in `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.

## Entwicklung

```bash
cd app
pip install -r requirements.txt
pytest tests/
```

Die Testsuite läuft sowohl gegen synthetische Fixtures als auch gegen
das echte, produktive Regelwerk unter `app/rules/`.

## Architektur (Kurzüberblick)

```
app/
├── app.py                 # Flask-Einstiegspunkt, Scan-Loop, Persistenz-Orchestrierung
├── matcher.py              # Kern-Matching-Logik gegen die YAML-Regeln
├── scrapers/                # Kleinanzeigen-/eBay-/Quoka-Scraper
├── rules/                   # Ein YAML pro Kategorie
├── scoring/                  # Deal-Score-, Profit-/Flip-Berechnung
├── categories/detectors/     # Kategorie-spezifische Ausstattungs-Erkennung
├── api/                      # Flask-Blueprints (Dashboard, /api/found, /api/status, /api/history)
├── persistence/               # JSON-/Log-I/O-Helfer
└── tests/                     # pytest-Suite
```

Geschützte Kernsysteme (Deal-Score, Top-Deal-Logik, Flip-/Resale-
Berechnung, Notification-Gate, Price-History-Persistenz, Duplicate
Detection, Presence Tracking, Category Validation) werden nur bei
nachgewiesenen Matcher-Bugs gezielt angepasst — Details zur
Entwicklungshistorie stehen in `TECHNISCHER_PROJEKTSTATUS.md` und
`STATUS.md`.
