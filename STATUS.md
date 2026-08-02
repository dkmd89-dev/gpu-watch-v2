# status.md — Aktualisiert bis Schritt "Plugin-System vollständig: Kontrakt-Test, Kategorie-Registry, Detector-Registry (Abschnitt 13); Dashboard-Redesign-Backlog ergänzt"

## Statusübersicht
- **Phase 0 (Projektanalyse & Stabilisierung):** Abgeschlossen
- **Phase 1 (Architekturplanung):** Abgeschlossen
- **Phase 2 (YAML-Regelwerk-Refactoring):** Abgeschlossen
- **Phase 3 (Scraper-Entkopplung):** Abgeschlossen
- **Phase 4 (Hardware-Erkennungs-Detectors):** Abgeschlossen
- **Phase 5 (Office- & Gaming-PC-Kategorien):** Abgeschlossen
- **Phase 6 (Deal-Score & Notification-Gating):** Abgeschlossen
- **Phase 7 (Preishistorie & Trendanalyse):** Abgeschlossen (Schritte 7.1 – 7.5 vollständig)
- **Phase 8 (Verdrahtung, API & Web-Dashboard):** Abgeschlossen (Schritte 8.1 – 8.8 vollständig)
- **SATA-SSD-Kategorie:** Bewusst als vierte, eigenständige Kategorie ergänzt (`rules/sata_ssd.yaml`) – nicht Teil der ursprünglichen Phasen-Roadmap, aber bestätigt gewollt.
- **Zwischenschritt (Re-Verifikation):** exclude_global-Bugfix + Notification-Gate-Korrektur – Abgeschlossen
- **eBay-URL-Dedup-Bugfix:** Abgeschlossen
- **price_history.jsonl bereinigt:** Abgeschlossen (verzerrte Altdaten aus der Zeit vor dem eBay-Dedup-Fix gesichert und entfernt, Sammlung startet neu)
- **Notification-Gate pro Kategorie + SATA-SSD-Fix:** Abgeschlossen (siehe unten)
- **Dashboard-Kategorie-Dropdown-Fix:** Abgeschlossen (siehe unten).
- **SSD-Suche verbessert (Schritt A):** Abgeschlossen (siehe unten).
- **Log-Rotation (Schritt B):** Abgeschlossen (siehe unten).
- **Deals-Aufräumen (Schritt C):** Abgeschlossen (siehe unten).
- **Kategorieweise Auswertung + Logging optimieren:** Abgeschlossen (siehe unten). War vor dieser Session bereits umgesetzt, aber **nicht committet** — im Rahmen dieser Session gegen den Code geprüft und verifiziert (siehe Abschnitt 10).
- **SATA-SSD-Requirement-Bug (`min_ssd_gb`/`max_ssd_gb` war No-Op):** Behoben (siehe Abschnitt 10).
- **Dashboard: generische KPI-Kacheln pro Kategorie:** Abgeschlossen (siehe Abschnitt 10) — vorheriger offener Punkt 3 aus dem Dashboard-Kategorie-Dropdown-Fix ist damit erledigt.
- **`requirements-dev.txt` ergänzt:** Abgeschlossen (siehe Abschnitt 10).
- **Plugin-Registry für Scraper (Schritt 1–3):** Abgeschlossen (siehe Abschnitt 11). Neue Suchquellen (Phase 9) benötigen künftig keine Codeänderung mehr an `app.py`.
- **Quoka-Scraper (Phase 9):** Implementiert und gegen echte Fixture verifiziert (siehe Abschnitt 12). Der beim echten `pytest`-Lauf entdeckte Test-Mock-Bug (fehlende `search_quoka`-Mocks, siehe "Bekannte Probleme") wurde von Robin behoben -- alle Tests laufen jetzt grün.
- **Phase 10 (Plugin-System vollständig):** Abgeschlossen (siehe Abschnitt 13). Kontrakt-Test beweist YAML-only-Erweiterbarkeit für Kategorien; `categories/registry.py` (Kategorie-Discovery) und `categories/detectors/registry.py` (Detector-Discovery) ergänzen die bereits bestehende Scraper-Registry (Abschnitt 11) zu allen drei Plugin-Ebenen. `matcher.py` bewusst unverändert (siehe Begründung in Abschnitt 13).

---

## Refaktorierte Module & Bestandteile

### 1. Konfiguration & Regelwerk (`app/rules/`)
- Umstellung von Einzeldatei auf Verzeichnisstruktur (`./app/rules/`).
- `_global.yaml`: Zentrale Defaults, globale Excludes (`exclude_global`), Standortkonfiguration, Benachrichtigungsschwellen (`notifications`) sowie die `manufacturer_reputation`-Tabelle (Dell, HP, Lenovo, Fujitsu, Acer, Asus, MSI, Medion, Apple, Captiva, Schenker, Terra, Eigenbau, `_default`). `scoring_weights.hersteller` bleibt standardmäßig bei 0 (fähig, aber inaktiv).
- `gpu.yaml`: Kategorie-spezifischer PC-Ausschluss (`exclude_category`), kategoriespezifische `scoring_weights` (Fokus auf Preis), `price_history_model` pro GPU-Variante.
- `office_pc.yaml` & `gaming_pc.yaml`: Hardware-Anforderungen (`requirements`) statt reiner Titel-Matching-Listen, Integration von `price_history_model`.
- `sata_ssd.yaml`: eigene Kategorie für 2.5"-SATA-SSDs, strikter Ausschluss von NVMe/M.2/HDD-Fehltreffern, eigene `scoring_weights` (90% Preis / 10% Hardwarequalität).
- Bereinigung: Legacy `app/rules.yaml` entfernt.

### 2. Matcher, Erkennungs-Engine & Deal-Score (`app/matcher.py`, `app/categories/`, `app/scoring/`)
- Dynamisches Laden aller YAML-Dateien aus `rules/`.
- **Bugfix (Re-Verifikation):** `_load_rules_from_dir()` hat `exclude_global` bisher nie aus `_global.yaml` extrahiert (der Key liegt dort als Geschwister von `defaults:`, nicht darunter). Dadurch griff der globale Ausschluss (defekt/kaputt/bastler/tausch/gesucht/kaufe/…) bei **keiner** Kategorie mehr – seit der Umstellung auf Verzeichnis-Modus in Phase 2. Behoben: `exclude_global` wird jetzt korrekt in `defaults["exclude_global"]` gemerged.
- **Hardware-Detectors (`app/categories/detectors/`):**
  - `ram.py`, `cpu.py`, `storage.py`, `case.py`, `gpu.py`, `psu.py`, `pcie.py`, `windows.py`.
  - `manufacturer.py`: Erkennung bekannter OEM-Marken sowie expliziter Eigenbau-Hinweise (`detect_manufacturer`).
- **5-Kriterien-Deal-Score (`app/scoring/deal_score.py`):**
  - Kategorie-bewusste Scoring-Engine mit 5-Sterne-Rating.
  - `_hersteller_score()` & Option `manufacturer_name`/`manufacturer_reputation` (Default `None` → abwärtskompatibles Fallback-Verhalten).
  - Integration dynamischer Marktpreise in `_price_score()` (60% Marktpreis / 40% YAML `max_price` Blending), mit automatischem Fallback bei fehlender Historie.
- **Notification-Gating (`app/app.py` & `app/notify.py`):**
  - **Korrektur (Re-Verifikation):** `notifications.gate_min_stars`/`gate_max_price` waren in `_global.yaml` auf `★☆☆☆☆`/`250€` abgedriftet (praktisch jeder Treffer löste eine Benachrichtigung aus). Auf die Auftrags-Vorgabe zurückgesetzt: **`★★★★★` UND Preis ≤ `150€`**, beide Bedingungen UND-verknüpft.

### 3. Preishistorie, Statistik & Top-Deal-Erkennung (`app/price_history.py`, `app/price_stats.py`, `app/top_deal.py`)
- `PricePoint`-Dataclass und append-only Speicherung aller Treffer in `data/price_history.jsonl` bei jedem Scan (unabhängig vom Notification-Gate).
- Marktpreis-Statistik: Min, Max, Durchschnitt, Median, 5%-/10%-Perzentil, Trend.
- Top-Deal-Erkennung ab ≥15% Ersparnis bei mindestens 3 Historie-Datenpunkten, verdrahtet in `app.py` (Schritt 8.2).
- Marktpreise fließen dynamisch in `deal_score.py::_price_score()` ein (Schritt 7.4/7.5, im Scan-Loop aktiv).
- **Offener Punkt (siehe unten):** Anhaltspunkte für eine mögliche Dedup-Lücke bei eBay-Treffern in `price_history.jsonl` – noch nicht untersucht/bestätigt.

### 4. Web-Dashboard & Scraper-Verdrahtung (`app/app.py`, `templates/index.html`)
- `/api/status`: Live-Status, Zähler (gescannt/gespeichert/Kategorie/Hersteller/Top-Deals), Scan-Log-Tail.
- `/api/price-history` und `/api/price-history/<model>`: Kurzstatistik bzw. volle Statistik + Zeitreihe.
- Dashboard: Status-Header, Zähler-Panel, Filter (Kategorie/Preis/Quelle/Hersteller/Deal-Score), Preisdiagramme, Scan-Log-Anzeige, Dark-Theme.

### 5. Scraper & Robustheit (`app/scrapers/`, `app/app.py`)
- Package-Aufteilung (`scrapers/kleinanzeigen.py`, `scrapers/ebay.py`) basierend auf `Listing`-TypedDict.
- `_clean_location()`: Bereinigung von Whitespace-/Zeilenumbruch-Rauschen in Kleinanzeigen-Standortdaten.
- Crash-sichere Persistenz: `seen.json` und `found.json` werden direkt pro Item geschrieben.
- Konfigurierbares Item-Limit via `FOUND_MAX_ITEMS` Env-Variable.
- **Bugfix (Re-Verifikation):** `scrapers/ebay.py::search_ebay()` lieferte die rohe `itemWebUrl` der eBay Browse API als `url`-Feld. Diese enthält volatile Tracking-Query-Parameter (`?hash=...&amdata=...`), die für DASSELBE physische Angebot zwischen API-Aufrufen unterschiedlich ausfallen können. Da `app.py` ausschließlich über `item["url"]` gegen `seen.json` dedupliziert, wurde dasselbe eBay-Angebot dadurch bei jedem Scan erneut als "neu" behandelt. Neue Funktion `_stable_item_url()` behält nur Schema/Host/Pfad (die stabile eBay-Item-ID steckt im Pfad, z.B. `/itm/1234567890`), verwirft die Query. Kleinanzeigen war von diesem Bug nicht betroffen (eigene URL-Struktur ohne Tracking-Query).

---

### 6. Notification-Gate pro Kategorie & SATA-SSD-Fix (Zwischenschritt)
- **Ausgangslage:** `gate_max_price` war ein einziges globales Preislimit für ALLE Kategorien. Gaming-PCs (real 200-550€) und Office-PCs (real 130-300€) konnten es strukturell nie unterschreiten -- praktisch keine Benachrichtigungen für diese Kategorien.
- **Fix:** Neues optionales YAML-Feld `notify_max_price` pro Kategorie (`rules/gpu.yaml`: 250€, `rules/office_pc.yaml`: 200€, `rules/gaming_pc.yaml`: 400€). `matcher.py` (`MatchResult.notify_max_price`) und `app.py` nutzen das kategorie-eigene Limit, wenn vorhanden, sonst Fallback auf das globale `notifications.gate_max_price` (150€, z.B. weiterhin genutzt von `rules/sata_ssd.yaml`, das bewusst kein eigenes definiert).
- **`gate_min_stars`:** von ★★☆☆☆ auf ★★★☆☆ angehoben (Robins Entscheidung, in Kombination mit dem gelockerten Preislimit).
- **SATA-SSD: 250GB/500GB-Regeln ergänzt** (bisher fehlten diese Kapazitäten komplett -- vermutlich der Hauptgrund für praktisch keine Treffer in dieser Kategorie, da gebrauchte 2.5"-SSDs meist 250GB/500GB sind, nicht 1TB/2TB).
- **Bugfix (beim Testen der neuen Regeln entdeckt):** `matcher.py`s generische VRAM-Check-Heuristik (`_vram_gb()`, Regex `\d{1,2}\s*gb`, urspr. nur für `gpu.yaml` gedacht) interpretierte Kapazitätsangaben wie "500GB" fälschlich als "0GB VRAM" (Regex matcht "00gb" als Teilstring von "500gb") und verwarf den Treffer. Auch generische SATA-Interface-Angaben wie "6Gb/s" können denselben Effekt auslösen. Behoben durch `min_vram_gb: 0` bei allen `sata_ssd.yaml`-Regeln (deaktiviert den GPU-spezifischen Check für diese Kategorie). Preise für die neuen 250GB/500GB-Regeln sind grobe Schätzwerte, noch nicht gegen echte Marktdaten kalibriert.

### 7. Dashboard-Kategorie-Dropdown-Fix (Zwischenschritt)
- **Ausgangslage (von Robin per Screenshot gemeldet):** `sata_ssd` tauchte im Kategorie-Filter des Dashboards nicht auf, obwohl die Kategorie laut `gpu_watch.log` real Treffer hatte (z.B. 1TB Top-Deal für 30€ am 25.7., 2TB Top-Deal für 30€ am 28.7.).
- **Root Cause:** `templates/index.html` leitete die Dropdown-Optionen bisher NUR aus den aktuell in `found.json` sichtbaren Karten ab. `found.json` ist auf `FOUND_MAX_ITEMS=200` gedeckelt -- bei genug Scan-Volumen wurden die selteneren SATA-SSD-Treffer von den häufigeren gpu/gaming_pc/office_pc-Treffern aus dem Fenster verdrängt, wodurch die Kategorie im Filter komplett verschwand, obwohl real weiterhin Treffer existierten.
- **Fix:** `matcher.py`s `_load_rules_from_dir()` liefert jetzt zusätzlich `"categories"` -- die VOLLSTÄNDIGE, aus den `rules/*.yaml`-Dateien abgeleitete Kategorie-Liste, unabhängig von `found.json`. `app.py` reicht das als `all_categories` ans Template durch, `templates/index.html` rendert es als `SERVER_CATEGORIES` und bildet die Union mit den aus den Karten abgeleiteten Kategorien.
- **Nebenbefund (bereits behoben, keine Aktion nötig):** Log zeigte einen alten False-Positive vom 25.7. ("Ich Suche 1 TB SATA SSD" wurde fälschlich als Verkaufsangebot gewertet und per ntfy verschickt) -- lag vor dem exclude_global-Fix (Rebuild erst am 27.7.), "suche" steht im aktuellen `exclude_global` bereits drin.
- **Erledigt (siehe Abschnitt 10):** Die vier KPI-Kacheln oben im Dashboard waren bisher fest nur für `office_pc`/`gaming_pc` verdrahtet — jetzt generisches Rendering pro Kategorie.
### 8. SSD-Suche verbessert, Log-Rotation, Deals-Aufräumen (Schritt A/B/C)

**Schritt A – SSD-Suche (`categories/detectors/storage.py`, `rules/sata_ssd.yaml`):**
- Tippfehler „SDD" (statt „SSD") wird jetzt gleichwertig erkannt (häufiger Vertipper in echten Kleinanzeigen-Titeln).
- `exclude_category` in `rules/sata_ssd.yaml`: `m.2`/`m2` entfernt -- M.2 ist ein Formfaktor, kein Interface, es gibt reale M.2-SATA-SSDs (B+M-Key), die dadurch bisher fälschlich ausgeschlossen wurden. `nvme`/`pcie` bleiben als explizite Interface-Ausschlüsse bestehen.
- `search_terms` um 6 generische, markenlose Begriffe ergänzt (SSD 250/500GB/1TB, WD Blue, ADATA, Toshiba) -- deckt Angebote ohne Markennennung im Titel ab.

**Schritt B – Log-Rotation (`app.py`):**
- `logging.FileHandler` durch `logging.handlers.RotatingFileHandler` ersetzt. Rotiert automatisch bei 1 MB (`LOG_MAX_BYTES`, Default), max. 5 alte Logs bleiben erhalten (`LOG_BACKUP_COUNT`, Default) -- `gpu_watch.log.1` bis `.5`, danach wird die älteste Datei verworfen. Beide Grenzen per Env-Var überschreibbar, Pfad/Format/`StreamHandler` unverändert.

**Schritt C – Deals-Aufräumen (`app.py`):**
- Neue Funktion `_cleanup_old_deals()`, aufgerufen bei jedem Scan direkt nach dem Laden von `found.json`. Entfernt Einträge, deren `found_at`-Zeitstempel älter als `DEAL_MAX_AGE_DAYS` ist (Default 7, Env-Var-konfigurierbar, analog zum bestehenden `FOUND_MAX_ITEMS`-Muster).
- Rückwärtskompatibel: Legacy-Einträge ohne `found_at` (aus der Zeit vor dessen Einführung in Phase 8) sowie Einträge mit nicht parsebarem Zeitstempel werden bewusst **nicht** gelöscht -- ohne verlässlichen Zeitstempel wäre ein Entfernen eine Vermutung statt einer Tatsache.
- `seen.json` und `price_history.jsonl` bleiben von der Bereinigung unberührt (Dedup-Basis bzw. Preishistorie sollen nicht verfallen).
### 9. Kategorieweise Auswertung, Scan-Priority & Log-Optimierung
- **Ziel 1 – Scan-Priority & Kategorie-Gruppierung:**
  - Neues YAML-Feld `scan_priority` definiert die Auswertungsreihenfolge (`gpu`: 1, `sata_ssd`: 2; Kategorien ohne Angabe folgen alphabetisch → `['gpu', 'sata_ssd', 'gaming_pc', 'office_pc']`).
  - Effizienzsteigerung in `run_scan()`: Nur noch **ein einziger HTTP-Request / Scrape-Durchlauf pro Scan** (statt pro Regel). Die Auswertung erfolgt strukturiert nach Kategorie geordnet.
  - Klare Kategorie-Zusammenfassung im Log:
    ```text
    🔍 Kategorie 'gpu' fertig: X Treffer
    🔍 Kategorie 'sata_ssd' fertig: X Treffer
    ✅ Scan komplett: X Treffer insgesamt (von Y geprüften Angeboten).
    ```
- **Ziel 2 – Log-Bereinigung (`app.py`):**
  - Polling-Spam durch Dashboard-Aufrufe (`GET /api/status HTTP/1.1`) wird im WSGI/Access-Log gezielt gefiltert und bläht die Log-Dateien nicht mehr alle 5 Sekunden auf.
- **Ziel 3 – Start-Banner (`app.py`):**
  - Beim Container-/Service-Start erscheint nun ein eindeutiges Banner:  
    `🤖 [HARDWARE_DEAL] ✅ Bot läuft und lauscht auf Nachrichten...`

- **Preisgrenzen kalibrieren (Gaming-PC, 400€/550€):** `data/price_history.jsonl` wurde geleert (Altdaten gesichert unter `data/price_history.pre-ebay-fix-backup-20260725.jsonl`), Sammlung beginnt mit dem nächsten produktiven Scan von vorn. **Kalibrierung ist bewusst noch NICHT durchgeführt** — dafür wird ein neuer, ausreichend langer Sammelzeitraum mit dem laufenden Container in Robins realer Umgebung benötigt (kein Netzwerkzugriff auf kleinanzeigen.de/ebay.com in dieser Analyse-Umgebung möglich). Empfehlung: nach einigen Tagen/Wochen produktivem Betrieb erneut mit der dann gefüllten `price_history.jsonl` anfragen.
- **SATA-SSD-Preise gegenprüfen:** die neuen 250GB/500GB-max_price-Werte (12/18€ bzw. 18/28€) sind grobe Schätzwerte, noch nicht anhand echter Marktdaten kalibriert -- nach ersten Treffern prüfen.
- **notify_max_price-Werte sind ebenfalls Schätzungen** (GPU 250€, Office-PC 200€, Gaming-PC 400€) -- nach ein paar Tagen Betrieb prüfen, ob die Benachrichtigungsfrequenz für Robin passt, und ggf. nachjustieren.
- **Optional (Polishing):** Nahtloser Live-Refresh der Angebotssortierung ohne vollen `location.reload()`.

### 10. Session-Verifikation Abschnitt 9 + SATA-SSD-Requirement-Fix + generische KPI-Kacheln + requirements-dev.txt

**Ausgangslage:** Der Upload enthielt bereits einen unverifizierten, nicht committeten Arbeitsstand (Abschnitt 9 — Kategorieweise Auswertung/Scan-Priority/Log-Optimierung). Alle Aussagen in diesem Abschnitt wurden gemäß Auftrag ("keine unbesehenen Übernahmen") gegen den tatsächlichen Code verifiziert, statt sie aus STATUS.md zu übernehmen.

**Verifikation Abschnitt 9 (per End-to-End-Simulation von `run_scan()` mit gemockten Scrapern, da kein Netzwerkzugriff in dieser Umgebung möglich war):**
- Scan-Reihenfolge korrekt: `category_order` aus `matcher.py` (`scan_priority`) liefert `['gpu', 'sata_ssd', 'gaming_pc', 'office_pc']`, `run_scan()` verarbeitet/loggt tatsächlich in dieser Reihenfolge — auch wenn die Rohtreffer in anderer Reihenfolge aus dem Scraping kommen.
- Log-Filter (`_SuppressStatusPollingFilter`) isoliert getestet: unterdrückt zuverlässig nur `GET /api/status`-Zeilen, lässt alle anderen Requests (z.B. `POST /api/scan-now`) unverändert durch.
- `found.json`/`price_history.jsonl`/Notification-Gate-Verhalten inhaltlich unverändert — nur die Verarbeitungsreihenfolge hat sich geändert.
- **Gefundene Regression:** Die (ebenfalls unverifiziert mitgelieferte) neue Testdatei `tests/test_app_category_grouped_scan.py` verwendete den Titel `"Kingston A400 250GB SATA SSD 2.5"`. Durch den in dieser Session vorgenommenen SATA-SSD-Requirement-Fix (siehe unten) schlug dieser Test neu fehl: `detect_ssd_gb()` erkennt bei der Wortstellung "...GB SATA SSD" keine Kapazität (SATA steht zwischen Größe und "SSD", bricht die strikte Adjazenzprüfung). Vor dem Requirement-Fix fiel das nicht auf, weil die Kapazitätsprüfung damals ein kompletter No-Op war. Behoben durch Anpassung des Test-Titels auf `"Kingston A400 250GB SSD SATA III 2.5"` (SATA nach statt vor "SSD") — die eigentliche Prüfabsicht des Tests (Kategorie-Reihenfolge) bleibt unverändert. Manuell nachgestellt, beide Testfälle grün.
- **Neuer, noch offener Befund:** "…GB SATA SSD" ist eine in echten Kleinanzeigen-Titeln gängige Wortstellung. `detect_ssd_gb()`s strikte Adjazenzprüfung dürfte dadurch auch produktiv einen Teil realer SATA-SSD-Angebote als False Negative verpassen. Nicht in dieser Session behoben (bewusst nicht in denselben Schritt gemischt, siehe unten) — Vorschlag für einen künftigen, eigenständigen Schritt: `detect_ssd_gb()`/`_CONNECTOR` um "sata"/"sata iii" als zulässiges Verbindungswort erweitern.

**SATA-SSD-Requirement-Bug behoben (`app/matcher.py`):**
- `rules/sata_ssd.yaml` nutzt ausschließlich `requirements: {min_ssd_gb, max_ssd_gb}`. `_evaluate_hardware_requirements()` kannte diese Keys bisher nicht — die Kapazitätsprüfung war ein kompletter No-Op, jede Anzeige "erfüllte" die Anforderung automatisch. Dadurch gewann immer nur die erste preislich passende Regel (128GB-Bucket), unabhängig von der echten SSD-Kapazität — z.B. wurde ein 500GB-Angebot fälschlich als `~128GB SATA SSD` kategorisiert und verfälschte damit sowohl die Dashboard-Kategorisierung als auch die Marktpreis-Statistik/Top-Deal-Erkennung dieser Kategorie.
- Neue Funktion `_storage_meets_requirement(ssd_gb, requirement)` (analog zu `_ram_meets_requirement()`), verdrahtet über `detect_ssd_gb()`. Ergänzt `features["ssd_gb"]`.
- Behebt außerdem den Import-Fehler in `tests/test_matcher_ssd_capacity_requirement.py` (referenzierte `_storage_meets_requirement`, das es vorher nicht gab).
- Alle 10 Fälle aus dieser Testdatei (Unit/Integration/E2E) sowie Regressionstests für `gpu`/`office_pc`/`gaming_pc`/`exclude_global` manuell nachgestellt und verifiziert (pytest in dieser Sandbox nicht ausführbar, siehe Testabdeckung unten).
- **Nebenwirkung:** SATA-SSD-Treffer landen ab sofort in den korrekten Preis-Buckets. Bestehende `price_history.jsonl`-Altdaten der Kategorie `sata_ssd_*` aus der Zeit vor diesem Fix bleiben fehlklassifiziert (nur neue Scans sind korrekt einsortiert).

**Dashboard: generische KPI-Kacheln pro Kategorie (`app/matcher.py`, `app/app.py`, `app/templates/index.html`):**
- `matcher.py`s `_load_rules_from_dir()` liefert zusätzlich `category_labels` (Kategorie-Schlüssel → YAML-`label`-Feld, z.B. `gaming_pc` → "Gaming-PC"), additiv, mit Fallback auf den internen Schlüssel.
- `app.py`s `index()`-Route reicht `category_labels` zusätzlich ans Template durch.
- `templates/index.html`: die bisher fest codierten "Office-PCs"/"Gaming-PCs"-Kacheln wurden entfernt. Neue JS-Funktionen (`ensureCategoryTile()`, `updateCategoryTiles()`) erzeugen dynamisch eine Kachel pro Kategorie — aus der Union von `SERVER_CATEGORIES` (vollständige Rules-Liste) und den tatsächlich in `category_counts` vorkommenden Schlüsseln (deckt z.B. Alt-Einträge mit `category: "unbekannt"` ab). Top-Deals bleibt als fester Anker (`topDealsCard`) immer die letzte Kachel.
- Verifiziert: Flask-Test-Client (`/`-Route rendert, alte ID `cntOffice` verschwunden), sowie isoliert per Node.js gegen einen DOM-Stub (alle 4 Kategorien erscheinen als Kachel auch bei 0 Treffern, unbekannte Kategorien bekommen ebenfalls eine Kachel, kein Duplikat bei wiederholtem 5s-Polling, Top-Deals bleibt letzte Kachel).
- Erfüllt das Ziel "neue Kategorien nur über YAML" jetzt auch auf UI-Ebene, nicht nur in der Matching-Logik.

**`app/requirements-dev.txt` ergänzt:**
- Enthielt bisher keine Dev-Dependency für `pytest` (Testsuite unter `app/tests/`). Neue, separate `requirements-dev.txt` (`-r requirements.txt` + `pytest==9.0.3`, Version passend zu vorgefundenen `.pytest_cache`-Artefakten).
- `app/requirements.txt` und `app/Dockerfile` bewusst unverändert — das Docker-Image installiert weiterhin nur `requirements.txt` und bleibt schlank.

**`.gitignore` erweitert:**
- `data/*.txt` ergänzt (analog zu `data/*.log`). Grund: `data/gpu_watch.txt` (ein reales, 478 Zeilen langes Produktions-Log vom 01.08., zeigte u.a. genau den in Abschnitt 9/Ziel 2 behobenen `/api/status`-Polling-Spam) lag als untracked Laufzeit-Artefakt im Arbeitsbaum und wurde bewusst **nicht** committet.

### 11. Plugin-Registry für Scraper (Schritt 1–3, `app/scrapers/`, `app/app.py`)

**Ausgangslage:** Neue Suchquellen (Phase 9: Quoka, markt.de, ...) mussten bisher an ZWEI Stellen von Hand verdrahtet werden -- `scrapers/__init__.py` (statischer Import) und `app.py` (hartcodierter `raw += search_xxx(...)`-Aufruf). Widerspricht dem Phase-9/10-Ziel ("neue Quelle ohne Änderung an der Kernlogik").

- **Schritt 1 – Discovery-Registry (`scrapers/registry.py`, neu):** `discover_scrapers()` scannt das `scrapers`-Package zur Laufzeit per `pkgutil.iter_modules` statt statischer Imports. Erkennt Plugins per Konvention (`SCRAPER_NAME`-Attribut + passende `search_<name>`-Funktion). Reine Infrastruktur, `app.py` unangetastet. `scrapers/kleinanzeigen.py`/`scrapers/ebay.py` erhielten nur je eine zusätzliche `SCRAPER_NAME`-Konstante.
- **Schritt 2 – `app.py` auf Registry umgestellt:** `run_scan()` iteriert seither über `discover_scrapers()` statt zwei hartcodierte Aufrufe. Dabei wurde ein bei der Umsetzung selbst verursachter Bug (doppelter Scraping-Block → echte HTTP-Calls trotz Mock) im selben Schritt gefunden und behoben. `_SCRAPER_CALL_ARGS` als bewusster Übergangs-Adapter eingeführt, da `search_kleinanzeigen()`/`search_ebay()` damals noch unterschiedliche Parameterreihenfolgen hatten. 5 bestehende Testdateien mussten ihr Mock-Target von `app_mod.search_xxx` auf `scrapers.xxx.search_xxx` verschieben (die Registry importiert Module frisch statt `app.py`-Namen zu patchen).
- **Schritt 3 – Signaturen vereinheitlicht (`scrapers/ebay.py`, `scrapers/base.py`, `app.py`):** `search_ebay()` folgt jetzt exakt dem `Scraper`-Protocol `(search_terms, plz, radius_km, max_price)`, identisch zu `search_kleinanzeigen()`. **Breaking Change** für positionelle Aufrufer (vorher `(search_terms, max_price, plz)`, kein `radius_km`) -- Repo-weite Prüfung ergab keine betroffene Aufrufstelle außer einem Test (nutzte bereits Keyword-Argumente, angepasst). `plz`/`radius_km` bleiben in `search_ebay()` ungenutzt (eBay Browse API kennt keine PLZ-Umkreissuche), dienen nur der Signatur-Kompatibilität. `_SCRAPER_CALL_ARGS`-Adapter in `app.py` vollständig entfernt -- generischer Aufruf `plugin.search(search_terms, plz, radius_km, max_price)` für alle Plugins.

**Ergebnis:** Eine neue Quelle, die `Scraper`-Protocol erfüllt (Datei in `scrapers/` mit `SCRAPER_NAME` + passender `search_<name>`-Funktion mit der vereinheitlichten Signatur), wird automatisch mitgescannt -- keine Änderung an `app.py` mehr nötig. Damit ist die in Phase-9 geforderte Erweiterbarkeit für Scraper-Quellen erreicht (Kategorien waren das bereits seit Phase 2 über YAML).

**Verifikation:** Alle drei Schritte end-to-end gegen den echten `run_scan()`-Code mit gemockten Scrapern verifiziert (kein Netzwerkzugriff in dieser Umgebung nötig/möglich) -- genau 1 Aufruf pro Quelle, identische 4-Argument-Signatur, keine echten HTTP-Calls. Vollständige Testsuite: **356/356 grün** (siehe Testabdeckung unten).

### 12. Quoka-Scraper (`app/scrapers/quoka.py`, neu, Phase 9)

**Ausgangslage:** Quoka war als Kandidat blockiert (kein Zugriff auf rohes HTML in dieser Umgebung). Robin hat zunächst die Quoka-**Startseite** hochgeladen (keine Anzeigen-Struktur, verworfen), dann die echte Suchergebnisseite ("RTX 3060", 12 Treffer, per `search-result-total-items`-Meta bestätigt) -- daraus wurden Selektoren abgeleitet und `scrapers/quoka.py` nach dem etablierten `kleinanzeigen.py`-Muster gebaut.

- **Selektoren:** `div.article-item` als Karten-Container, `h2.article-title a` (Titel+URL), `span.article-price` (Preis), `p.article-location` (Ort), `p.article-description` (Beschreibung -- anders als bei Kleinanzeigen befüllt, da Quoka echten Text liefert).
- **Zwei reale Edge-Cases beim Testen gegen die Fixture gefunden und behoben:**
  1. 2 von 12 Karten hatten "rtx"/"3060" nicht im Titel → korrekt vom bestehenden Sicherheitsnetz gefiltert.
  2. Rabatt-Angebote verschachteln `.new-price`/`.old-price` im selben Element ("529.0 EUR650.0 EUR" als Rohtext) -- ein erster Preis-Regex verwechselte den Dezimalpunkt bei "529.0" mit einem Tausenderpunkt (5290€ statt 529€). Behoben durch präzisere Zahlenlogik (Tausenderpunkt nur bei exakt 3 Nachkommastellen) plus explizite Bevorzugung von `.new-price`.
- **`plz`/`radius_km`/`max_price` bleiben ungenutzt** -- wie bei `search_ebay()`, da keine verifizierten Query-Parameter für Ortsfilterung bekannt sind (Formular hat `Zip`/`City`/`Area`-Felder, vermutlich JS-/Autocomplete-gesteuert, nicht als einfacher Query-Parameter verifizierbar) und Preisfilterung ohnehin in `matcher.py` passiert.
- **Dank Plugin-Registry (Abschnitt 11) keine Codeänderung an `app.py`/`__init__.py` nötig** -- `quoka` wurde automatisch per Discovery gefunden und end-to-end gegen `run_scan()` verifiziert (in dieser Sandbox nur mit gemockten Requests, kein echter Netzwerkzugriff möglich).
- Testsuite in dieser Sandbox danach: 368/368 grün.

### 13. Plugin-System vollständig: Kontrakt-Test, Kategorie-Registry, Detector-Registry (Phase 10 / STATUS.md-Ausblick Punkte 5 & 6)

**Ausgangslage:** Phase 10 verlangt, dass sowohl neue Suchquellen als auch neue Hardware-Kategorien ausschließlich per Plugin/YAML ergänzt werden können, ohne den Kern anzufassen. Die Scraper-Seite war das bereits seit Abschnitt 11 (Discovery-Registry). Für Kategorien fehlte die explizite Analogie/der Beweis, für Detectors die Discovery-Schicht (Ausblick-Punkte 5 & 6 der vorherigen Fassung).

- **Kontrakt-Test (`app/tests/test_rules_category_plugin_contract.py`, neu):** Beweist end-to-end (isoliertes `tmp_path`-Verzeichnis, synthetische `_plugin_test`-Kategorie), dass eine neue Hardware-Kategorie allein durch eine YAML-Datei in `rules/` entsteht -- Erkennung, Label, Suchbegriffe, `scan_priority`, `evaluate()`-Treffer inkl. `notify_max_price`, alles ohne Codeänderung an `matcher.py`/`app.py`.
- **Kategorie-Registry (`app/categories/registry.py`, neu):** `CategoryPlugin`/`discover_categories()`, analog zu `scrapers/registry.py`. Scannt `rules/*.yaml` (außer `_global.yaml`) zur Laufzeit. Skip-Regel bewusst exakt an `matcher._load_rules_from_dir()` angeglichen (nur `_global.yaml`, keine pauschale Unterstrich-Regel).
- **Detector-Registry (`app/categories/detectors/registry.py`, neu):** `DetectorPlugin`/`discover_detectors()`. Erkennt alle öffentlichen `detect_<name>`-Funktionen in `categories/detectors/*.py` per Namenskonvention -- 13 Detectors gefunden (u.a. mehrere pro Modul, z.B. `storage.py` → `ssd_gb`/`hdd_gb`/`nvme`). Private Hilfsfunktionen (`_size_to_gb` etc.) werden korrekt ausgeschlossen.
- **Bewusste Nicht-Verdrahtung in `matcher.py` (für beide neuen Registries):** Die produktive Merge-/Auswertungslogik (`_load_rules_from_dir()`, `_evaluate_hardware_requirements()`) bleibt unverändert. Grund: `matcher.py` braucht pro Requirement-Prüfung einen bestimmten Detector mit fester Signatur in fester Reihenfolge -- eine generische "rufe alle gefundenen Plugins auf"-Schleife böte hier keinen Mehrwert, nur unnötiges Risiko am produktiven Matching-Pfad. Beide Registries dienen als Discovery-Bestandsaufnahme, Grundlage für generische Kontrakt-Tests und künftiges Plugin-Tooling -- identisches Muster wie Schritt 1 der Scraper-Registry (Abschnitt 11).
- **Tests:** `test_category_registry.py` (7 Tests), `test_detector_registry.py` (8 Tests), `test_rules_category_plugin_contract.py` (6 Tests) -- alle von Robin gegen die echte Umgebung bestätigt grün (`test_detector_registry.py`: 8/8 bestätigt; `test_rules_category_plugin_contract.py`: 6/6 bestätigt).
- **Bekannter Stolperstein dieser Session (kein Code-, sondern Auslieferungsfehler):** Zwei neu erstellte Dateien hießen beide `registry.py` (`app/categories/registry.py` und `app/categories/detectors/registry.py`) und wurden anfangs unter identischem Downloadnamen ausgeliefert -- Robin hat dadurch zweimal versehentlich die falsche Datei am falschen Pfad abgelegt (einmal fehlender Import, einmal falscher Dateiinhalt). Behoben durch eindeutig benannte Downloads (`categories_registry.py` / `detectors_registry.py`) mit expliziter Zielpfad-Tabelle. **Lehre:** bei mehreren gleichnamigen Dateien im selben Schritt künftig immer eindeutige Downloadnamen + Zielpfad-Tabelle verwenden.
- **Verifikation:** In der Sandbox (kein `pytest` installierbar, kein Netzwerkzugriff) wurde die komplette Testlogik aller drei neuen Dateien manuell per `python3`-Assertions gegen den echten Code nachvollzogen, inkl. Regressionschecks von `matcher.evaluate()` auf echten Office-PC-/Gaming-PC-Titeln. In Robins echter Umgebung zusätzlich reguläre `pytest`-Läufe bestätigt grün (siehe oben).

**Ergebnis:** Alle drei Plugin-Ebenen (Scraper, Kategorien, Detectors) sind jetzt konsistent per Discovery erfassbar. Phase 10 gilt als abgeschlossen.

---

## Bekannte Probleme & Einschränkungen

**✅ BEHOBEN (von Robin, in seiner echten Umgebung):** Robins ursprünglicher `pytest`-Lauf (368 Tests, echte Umgebung mit Netzwerkzugriff) zeigte 8 Fehlschläge, alle mit derselben Ursache: Mehrere Testdateien mockten `search_kleinanzeigen`/`search_ebay` per `patch.object(scrapers.kleinanzeigen, ...)`/`patch.object(scrapers.ebay, ...)`, aber **nicht** `scrapers.quoka.search_quoka`. Da die Plugin-Registry (Abschnitt 11) `quoka` automatisch mitscannt, lief in diesen Tests ein **echter, ungemockter HTTP-Request an quoka.de** -- die Logs zeigten reale Live-Angebote (z.B. "Lenovo Legion Pro 5 16ARX8 RTX 4060..."), die die erwarteten Trefferzahlen/Zuordnungen verfälschten. Exakt derselbe Bug-Typ wie in Schritt 2 der Plugin-Registry-Arbeit (Abschnitt 11), nur diesmal in die andere Richtung: neue Quelle trifft auf alte Mocks statt neue Registry auf alte Mocks.

Betroffen waren: `test_app_category_grouped_scan.py` (2 Tests), `test_app_manufacturer_field.py` (3 Tests), `test_app_notification_gate.py` (3 Tests). Fix (von Robin lokal umgesetzt, nicht in dieser Sandbox erneut nachvollzogen): fehlende `patch.object(scrapers.quoka, "search_quoka", return_value=[])`-Mocks in den betroffenen Tests ergänzt. **Robin bestätigt: alle Tests laufen jetzt grün.** Diese Sandbox hat den konkreten Fix-Diff nicht selbst erneut verifiziert (Robins lokaler Stand kann von dieser Sandbox-Kopie abweichen) -- gemäß Projektprinzip wird das hier transparent als "von Robin bestätigt", nicht als "in dieser Sandbox verifiziert" vermerkt.

**Lehre für künftige neue Scraper-Quellen:** Jede neue Quelle (Phase 9) muss ab sofort in einer eigenen Checkliste geprüft werden -- alle bestehenden Tests, die den Scan End-to-End über `run_scan()` laufen lassen, müssen die neue Quelle ebenfalls mocken, sonst entstehen bei jeder neuen Quelle automatisch echte, ungewollte Netzwerkzugriffe in der Testsuite.

- **Datenbasis für Deal-Score:** Da im Listen-Scraping keine vollständigen Beschreibungstexte/Galeriebilder geladen werden, fallen Teil-Scores für Zustand oder Lieferumfang standardmäßig neutral aus.
- **Konservative Erkennungsgrenzen bei Detectors:** Strikte Adjazenzprüfungen bei RAM/CPU zur Vermeidung von False Positives.
- **`price_history.jsonl` wurde zurückgesetzt** (Backup unter `data/price_history.pre-ebay-fix-backup-20260725.jsonl`, nicht geloescht). Marktpreis-Statistik/Top-Deal-Erkennung/dynamischer Preis-Score in `deal_score.py` fallen bis zur erneuten Datensammlung auf ihre dokumentierten Fallbacks zurück (kein Marktpreis vorhanden → reines `max_price`-Signal, kein Crash, siehe `read_price_points()`/`_load_price_stats()`).

**Selbst gefundener Zwischenfall:** Bei der Implementierung von Schritt C ist beim Einfügen der neuen Funktion versehentlich die `def`-Zeile von `_load_price_stats()` verloren gegangen (fehlerhafter str_replace-Anker). Durch den vollständigen Testlauf sofort als Regression in `test_app_notification_gate.py` aufgefallen, noch im selben Schritt behoben und erneut vollständig verifiziert -- kein Restrisiko.
---

## Testabdeckung



- **Testsuite:** pytest unter `app/tests/`.
- **In dieser Sandbox (kein Netzwerkzugriff, alle Scraper zwingend gemockt):** **368/368 Tests grün, 0 Fehler**, direkt nach Hinzufügen von `quoka.py` verifiziert.
- **Robins echte Umgebung (mit Netzwerkzugriff):** Ursprünglich 8/368 Fehlschläge durch fehlenden `search_quoka`-Mock in 5 Testdateien (siehe "Bekannte Probleme"). **Von Robin behoben, alle Tests jetzt grün bestätigt.** Fix wurde in dieser Sandbox nicht erneut nachvollzogen (Robins lokaler Diff liegt hier nicht vor) -- als "von Robin bestätigt" statt "in dieser Sandbox verifiziert" vermerkt.
- **Abschnitt 13 (Plugin-System vollständig):** 21 neue Tests (`test_category_registry.py`: 7, `test_detector_registry.py`: 8, `test_rules_category_plugin_contract.py`: 6). Von Robin in seiner echten Umgebung ausgeführt und bestätigt grün (`test_detector_registry.py` 8/8 bestätigt per Screenshot; `test_rules_category_plugin_contract.py` 6/6 bestätigt; `test_category_registry.py` nach Behebung des Auslieferungsfehlers noch nicht erneut von Robin bestätigt -- offen, siehe Ausblick).
- Die zuvor in dieser Datei dokumentierten 3 vorbestehenden Fehler (`test_matcher_ssd_capacity_requirement.py`-Import, `test_sata_ssd_500gb_matcht_nicht_die_1tb_regel`, `test_search_ebay_nutzt_normalisierte_url`) treten beim aktuellen Lauf **nicht** auf -- gemäß Projektprinzip "keine unbesehenen Übernahmen aus der Doku" wird hier nur der tatsächlich in dieser Session verifizierte Zustand (356/356 grün) festgehalten; die Diskrepanz zur älteren Notiz wurde nicht weiter zurückverfolgt.
- **Historie (frühere Läufe, nicht in dieser Session erneut geprüft):** 317/317 vor Schritt A/B/C; 334 gesamt nach Schritt A/B/C (18 neue Tests: 8 SSD-Suche, 3 Log-Rotation, 7 Deals-Aufräumen).

---

## Ausblick / Mögliche nächste Schritte

Offene Punkte, unpriorisiert, keiner davon begonnen:

1. **Phase 9 – Weitere Suchquellen:** Quoka abgeschlossen (siehe Abschnitt 12) -- inkl. behobenem Test-Mock-Bug, alle Tests grün. Mit der Plugin-Registry (Abschnitt 11) kann jede weitere Quelle rein additiv ergänzt werden (Datei in `scrapers/` + `SCRAPER_NAME` + `search_<name>(search_terms, plz, radius_km, max_price)`) -- **wichtig:** bei jeder neuen Quelle müssen zusätzlich alle bestehenden End-to-End-Tests (`run_scan()`) um einen passenden Mock ergänzt werden (siehe Lehre in "Bekannte Probleme"), sonst drohen echte HTTP-Calls in der Testsuite.
   - markt.de, Facebook Marketplace, Hardwareluxx, ComputerBase: noch nicht untersucht.
2. **Gaming-PC-Preisgrenzen kalibrieren:** weiterhin explizit zurückgestellt, bis der produktive Container genug frische Daten (seit dem eBay-Dedup-Fix) gesammelt hat.
3. **SATA-SSD-Preise & `notify_max_price`-Werte gegenprüfen:** aktuell grobe Schätzwerte (siehe Abschnitt 9), noch nicht anhand echter Marktdaten kalibriert.
4. **`detect_ssd_gb()`-Wortstellungslücke (Abschnitt 10, offener Befund):** Titel der Form "…GB SATA SSD" (SATA zwischen Zahl und "SSD") werden von der strikten Adjazenzprüfung nicht erkannt -- dürfte produktiv reale SATA-SSD-Angebote als False Negative verpassen. Vorschlag: `_CONNECTOR`/Adjazenzprüfung in `storage.py` um "sata"/"sata iii" als zulässiges Zwischenwort erweitern. Eigenständiger, isolierter Schritt (nicht mit anderen Änderungen mischen).
5. ~~Detector-Registry für `categories/detectors/`~~ **Erledigt** (siehe Abschnitt 13).
6. ~~Phase 10 – Plugin-System vollständig (Kategorien als Plugins)~~ **Erledigt** (siehe Abschnitt 13).
7. **Ausstehende Bestätigung:** `test_category_registry.py` (7 Tests) noch nicht erneut von Robin bestätigt, nachdem der Auslieferungsfehler aus Abschnitt 13 (falscher Dateiinhalt am Zielpfad) behoben wurde -- kurzer, risikoarmer Nachlauf: `pytest app/tests/test_category_registry.py -v` bzw. volle Suite.
8. **Dashboard-Redesign (neu, von Robin am 02.08. vorgeschlagen, UI/UX-Feedback, unpriorisiert, keiner der Unterpunkte begonnen):** vier Hebel, jeweils eigenständig und isoliert umsetzbar (`templates/index.html`, ggf. `app.py` für Zeitstempel-Formatierung):
   - **8.1 Header & Status-Leiste:** kompakter, "Jetzt manuell scannen"-Button neben den Titel; Text "Scan läuft..." durch pulsierenden Live-Indikator (Punkt/Spinner) ersetzen.
   - **8.2 KPI-Kacheln:** dicke Rahmen entfernen, stattdessen subtile helle Hintergrundflächen ohne Rand; Top-Deals-Kachel farblich hervorheben (z.B. dezentes Gold), um sie gegenüber z.B. "Gescannt" optisch zu priorisieren.
   - **8.3 Deal-Karten:** Titel+Preis in eine Zeile (Preis fett/farblich hervorgehoben); Top-Deal-Badge standardisiert oben rechts; Plattform-Icons (eBay/Kleinanzeigen/Quoka) statt Text-Label; Zeitstempel als relative Zeit ("vor 5 Minuten"/"heute, 14:20") statt ISO-String -- Umrechnung client- oder serverseitig zu entscheiden; leere Sterne-Bewertung ausblenden statt grau anzuzeigen, solange kein Score vorliegt.
   - **8.4 Filter-Leiste:** mehr vertikaler Abstand zu den Kacheln darüber; Feldbreiten an Inhalt anpassen (z.B. "Preis bis (€)" schmaler als "Kategorie").
   - Reihenfolge/Priorisierung der vier Unterpunkte: offen, liegt bei Robin. Nahtloser Live-Refresh ohne `location.reload()` (bisheriger Punkt 7) bleibt als zusätzlicher, unabhängiger Dashboard-Punkt bestehen.

Kein Punkt ist priorisiert oder für den nächsten Schritt vorausgewählt -- Freigabe/Auswahl liegt bei Robin.
