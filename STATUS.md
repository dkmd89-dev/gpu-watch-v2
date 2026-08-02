# status.md — Aktualisiert bis Schritt "Verhandlungs-Assistent (Abschnitt 16, Punkt d, Baustein 7): negotiation_*-YAML-Felder, matcher.py-Toleranzlogik, 🤝-Dashboard-Badge -- vollständig abgeschlossen

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
- **Dashboard-Redesign (Robins UI/UX-Vorschlag vom 02.08.):** Abgeschlossen (siehe Abschnitt 14). Alle vier Backlog-Punkte (Header/Status-Leiste, KPI-Kacheln, Deal-Karten, Filter-Leiste) sowie der zusätzliche, unabhängige Punkt "nahtloser Live-Refresh ohne `location.reload()`" umgesetzt.
- **`detect_ssd_gb()`-Wortstellungslücke (vormals Ausblick-Punkt 4):** Behoben. `_CONNECTOR`-Regex in `storage.py` erkennt jetzt eine SATA-Generationsangabe ("SATA III"/"SATA-III"/"SATA 3"/"SATA3") zwischen Größenangabe und "SSD" in beiden Wortstellungen, 7 neue Tests in `test_detector_storage.py`, volle Suite (397 Tests) grün. Rein additive Regex-Erweiterung, keine Breaking Changes.
- **SATA-SSD-Preisgrenzen kalibriert (vormals Ausblick-Punkt 3):** Abgeschlossen. `max_price`-Werte in `rules/sata_ssd.yaml` anhand realer `price_history.jsonl` (1039 Datenpunkte) neu berechnet: Top-Deal ≈ reales p10-Perzentil, Guter Preis ≈ realer Marktpreis (statt bisheriger Bauchgefühl-Werte). Veralteter Kommentar zu `gate_max_price`-Fallback in `_global.yaml` korrigiert. 397/397 Tests grün.
- **Gaming-PC-Preiskalibrierung (vormals Ausblick-Punkt 2):** Abgeschlossen, siehe Abschnitt 15. Alle 4 Schritte umgesetzt: `rules/gaming_pc.yaml` `max_price`-Werte anhand 416 realer Datenpunkte kalibriert (Top-Deal 400€→300€, Okay 750€→450€), Erfassungsfenster zurückgesetzt.
- **Reselling-/Arbitrage-Erweiterung (neues Konzept):** In Bearbeitung, siehe Abschnitt 16. Schritt 1 (fees-Konfiguration + `scoring/profit.py`) **abgeschlossen**. Schritt 2 (Anbindung `profit`-Komponente an `scoring/deal_score.py`) **abgeschlossen**. Schritt 3 (Anbindung an `app.py`/`matcher.py`) **abgeschlossen**. **Punkt b (Marge im Dashboard anzeigen) abgeschlossen** — `found.json`-Einträge enthalten jetzt `estimated_margin_eur`/`estimated_margin_pct`, Dashboard zeigt sie als 💰-Zeile (grün/rot je nach Vorzeichen). Produktives Scoring-Verhalten (deal_score/deal_stars) weiterhin unverändert (Default-Gewicht `profit` = 0 in allen Kategorien).
- **Verhandlungs-Assistent (Punkt 7 aus Abschnitt 16, Punkt d):** Abgeschlossen (siehe unten, Abschnitt 16). Neue `negotiation_*`-Felder pro Kategorie-Regel erlauben Angebote leicht über `max_price`, wenn Ausstattung/Score gut genug ist (statt komplettem Verwerfen) — testweise nur an einer GPU-Regel aktiviert. Dashboard zeigt 🤝-Badge. Punkte 3–6 aus Punkt d weiterhin offen.

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
- **Tests:** `test_category_registry.py` (8 Tests, siehe Hinweis unten), `test_detector_registry.py` (8 Tests), `test_rules_category_plugin_contract.py` (6 Tests) -- alle grün. `test_detector_registry.py` (8/8) und `test_rules_category_plugin_contract.py` (6/6) von Robin gegen die echte Umgebung bestätigt. `test_category_registry.py` war zuvor offen (Ausblick-Punkt 7) -- in dieser Sandbox erneut ausgeführt: **8/8 grün** (Datei enthält mittlerweile 8 statt der ursprünglich dokumentierten 7 Tests -- Diskrepanz nicht weiter zurückverfolgt, siehe Testabdeckung).
- **Bekannter Stolperstein dieser Session (kein Code-, sondern Auslieferungsfehler):** Zwei neu erstellte Dateien hießen beide `registry.py` (`app/categories/registry.py` und `app/categories/detectors/registry.py`) und wurden anfangs unter identischem Downloadnamen ausgeliefert -- Robin hat dadurch zweimal versehentlich die falsche Datei am falschen Pfad abgelegt (einmal fehlender Import, einmal falscher Dateiinhalt). Behoben durch eindeutig benannte Downloads (`categories_registry.py` / `detectors_registry.py`) mit expliziter Zielpfad-Tabelle. **Lehre:** bei mehreren gleichnamigen Dateien im selben Schritt künftig immer eindeutige Downloadnamen + Zielpfad-Tabelle verwenden.
- **Verifikation:** In der Sandbox (kein `pytest` installierbar, kein Netzwerkzugriff) wurde die komplette Testlogik aller drei neuen Dateien manuell per `python3`-Assertions gegen den echten Code nachvollzogen, inkl. Regressionschecks von `matcher.evaluate()` auf echten Office-PC-/Gaming-PC-Titeln. In Robins echter Umgebung zusätzlich reguläre `pytest`-Läufe bestätigt grün (siehe oben).

**Ergebnis:** Alle drei Plugin-Ebenen (Scraper, Kategorien, Detectors) sind jetzt konsistent per Discovery erfassbar. Phase 10 gilt als abgeschlossen.

---

### 14. Dashboard-Redesign: Header/Status-Leiste, KPI-Kacheln, Deal-Karten, Filter-Leiste, Live-Refresh (`app/templates/index.html`)

**Ausgangslage:** Robins UI/UX-Feedback vom 02.08. (siehe ehemals Ausblick-Punkt 8), vier Hebel + ein zusätzlicher, unabhängiger Punkt (Live-Refresh, vormals Ausblick-Punkt "7"). Alle fünf Punkte in dieser Session einzeln umgesetzt, jeweils mit eigenem Freigabe-Schritt.

**8.1 Header & Status-Leiste:** Redundante "Status: Scan läuft…/Bereit"-Textzeile entfernt. Live-Status läuft jetzt ausschließlich über den bereits vorhandenen pulsierenden Punkt neben dem Titel (`#statusDot`), zusätzlich mit Tooltip (`title`) + `role="status"`/`aria-live="polite"` für Barrierefreiheit. Status-Panel kompakter (Padding/Margin reduziert).

**8.2 KPI-Kacheln:** Top-Deals-Kachel bekommt eine dezent goldgetönte Hintergrundfläche (`counter-card topdeal`) zusätzlich zur bereits bestehenden goldenen Zahl. "Gescannt (letzter Lauf)"-Kachel optisch zurückgenommen (`counter-card muted`, kleinere/gedämpfte Zahl) als am wenigsten relevante Kennzahl. `.counter-card` hatte bereits keinen Rahmen (nur Hintergrundfläche) -- entsprach schon der gewünschten Optik, Fokus lag auf der Prioritäts-Abstufung.

**8.3 Deal-Karten:**
- Titel + Preis in einer Zeile (`.title-row`, Preis bleibt fett/grün, fest rechts, bricht nicht um).
- **EIN** standardisierter Badge-Slot oben rechts statt zweier potenziell gleichzeitig sichtbarer Top-Deal-Badges. Priorität: `is_top_deal` (Preishistorie/Bestpreis, Phase 7) vor regelbasiertem `deal_rating` (Phase 6) vor "Guter Preis". Beide Datenfelder bleiben im Backend unverändert -- reine Anzeige-Priorisierung.
- Plattform-Icon statt Text-Label. **Bewusste Abweichung:** zunächst neutrale Buchstaben-Kreise statt Marken-Logos (Markenrechte). Robin hat anschließend eigene, nicht-Marken-basierte SVG-Icons (`app/static/icons/{kleinanzeigen,ebay,quoka}.svg`, farbige Kreise mit Anfangsbuchstabe) bereitgestellt -- diese werden jetzt per `<img>` über Flasks Default-Static-Ordner ausgeliefert. Der ursprüngliche Buchstaben-Kreis bleibt als `onerror`-Fallback erhalten, greift automatisch für künftige Quellen (Phase 9/10-Plugins) ohne eigene SVG-Datei.
- Zeitstempel als relative Zeit ("vor 5 Minuten" / "heute, 14:20" / "gestern, …") statt ISO-String, rein clientseitig (`formatRelativeFoundAt()`), aktualisiert sich alle 60s selbst. Rohwert bleibt als `data-found-at` im DOM erhalten.
- Leere Sterne-Bewertung: war bereits über `{% if f.deal_stars %}` ausgeblendet -- kein Codeänderungsbedarf, Punkt war schon erfüllt.
- Nebenbei behoben: `found_at` wird jetzt in ein `{% if %}` gefasst -- Legacy-Einträge ohne `found_at` zeigten vorher das literale Wort "None" in der Karte.

**8.4 Filter-Leiste:** Zusätzlicher `margin-top` auf `.filter-panel` (mehr Abstand zu den KPI-Kacheln darüber, die dieselbe Panel-Optik nutzen). Neue Klasse `.filter-field.narrow` (min-width 100px/max-width 130px) am Feld "Preis bis (€)" -- schmaler als "Kategorie" & Co.

**Live-Refresh ohne `location.reload()`:** Nach Scan-Ende wird nicht mehr die komplette Seite neu geladen. `refreshListings()` holt die aktuellen Treffer über die bereits bestehende Route `/api/found` und baut nur `#listingsGrid` neu auf. Neue Funktion `renderCardHtml(f)` bildet das serverseitige Jinja-Karten-Markup 1:1 clientseitig nach (inkl. Badge-Priorität, Titel+Preis-Zeile, Icon+Fallback, relative Zeit), konsequent mit `escapeHtml()` gegen HTML-Injection über gescrapte Titel/Orte abgesichert. `initFilters()` in `populateFilterOptions()` + `fillSelectOptions()` aufgeteilt: Dropdown-Optionen werden nach jedem Refresh neu ermittelt, ohne Duplikate zu erzeugen und ohne die aktuell gewählte Filterauswahl zu verwerfen.
- **Bewusst nicht angefasst:** die Modell-Auswahl der Preisdiagramme (`initPriceCharts()`) lädt weiterhin nur einmal beim initialen Laden. Ein komplett neues `price_history_model` aus einem Scan taucht dort erst nach manuellem Neuladen auf -- war nicht Teil des benannten Backlog-Punkts ("Angebotssortierung").
- **Wartungshinweis:** Server- (Jinja) und clientseitiges (`renderCardHtml()`) Karten-Markup müssen ab jetzt synchron gepflegt werden, wenn sich die Deal-Karten-Struktur künftig ändert.

**Verifikation (kein `pytest`/Netzwerkzugriff in dieser Sandbox möglich):** Flask-Test-Client (`/` und `/api/found` rendern/antworten fehlerfrei, konsistente Datenfelder), `node --check` über den vollständigen `<script>`-Block (syntaktisch fehlerfrei), `renderCardHtml()` isoliert gegen einen DOM-Stub in Node getestet (Badge-Priorität, XSS-Schutz bei bösartigem Titel, korrekte Fallbacks bei fehlenden Feldern, "Guter Preis"-Badge + Icon-Fallback-Klasse) -- 3/3 Testfälle grün. Empfehlung: `pytest app/tests -v` sowie manuelle Browser-Prüfung (Scan auslösen, Live-Refresh ohne sichtbaren Reload beobachten, Filterauswahl bleibt erhalten) in Robins echter Umgebung nachholen.

---

### 15. Gaming-PC-Preiskalibrierung (Datensammlung erforderlich)

**Befund:** `price_history.jsonl` wird nur bei Regel-Match geschrieben (`append_price_point()` in `app.py`) -- die Statistik für `gaming_pc` (n=369) ist dadurch an den bestehenden Preisgrenzen **zensiert**: 28% der Datenpunkte im Top-Deal-Fenster (≤400€) lagen bei ≥395€, 15% aller Datenpunkte im Okay-Fenster (≤550€) lagen bei ≥545€. Median/Marktpreis aus dieser Datenbasis wären dadurch systematisch nach unten verzerrt -- eine Kalibrierung nach derselben Methode wie bei SATA-SSD (Abschnitt 9/10) wäre hier methodisch nicht belastbar, da sie nur die bestehenden Grenzen bestätigen würde.

Geplantes Vorgehen (4 Teilschritte):

1. **Erfassungsfenster öffnen** — ✅ Umgesetzt. `max_price` der "Okay"-Regel in `rules/gaming_pc.yaml` von 550€ auf 750€ angehoben, um für die Sammelphase unzensierte Daten zu erfassen. `notify_max_price` bewusst unverändert bei 400€ (keine Auswirkung auf ntfy-Benachrichtigungen, nur auf die geloggte Preishistorie).
2. **Datensammlung laufen lassen** — ✅ Abgeschlossen. 416 `gaming_pc`-Datenpunkte gesammelt (02.08.2026), nur 3 davon ≥700€ — keine Häufung mehr an der 750€-Deckelung, Verteilung sauber glockenförmig (Median 450€, p10 300€, p90 550€).
3. **Echte Kalibrierung** — ✅ Abgeschlossen. `price_stats.compute_price_stats()` auf die 416 Punkte angewendet: p10 = 300€, Marktpreis (getrimmter Mittelwert p10-p90) = 452€ (Median 450€). `rules/gaming_pc.yaml`: Top-Deal-Regel `max_price` 400€ → **300€**, Okay-Regel `max_price` 750€ → **450€** (analog Methodik SATA-SSD, Abschnitt 9/10).
4. **Erfassungsfenster zurücksetzen** — ✅ Abgeschlossen (zusammen mit Schritt 3, da derselbe Wert betroffen ist). 750€-Deckelung durch den kalibrierten 450€-Wert ersetzt.

**Testanpassungen (bewusste, erwartete Anpassung, kein Bugfix):** 2 bestehende Tests referenzierten die alten, unkalibrierten Preisgrenzen als Fixture-Werte:
- `test_matcher_deal_score_integration.py::test_evaluate_niedriger_score_bei_hohem_preis`: Testpreis 399€ (nahe alter 400€-Grenze) → 299€ (nahe neuer 300€-Grenze).
- `test_matcher_price_history_model.py::test_gaming_pc_beide_rating_stufen_teilen_price_history_model`: Okay-Tier-Testpreis 500€ (läge über der neuen 450€-Grenze) → 420€; Top-Deal-Testpreis 350€ (läge über der neuen 300€-Grenze, hätte den Test unbemerkt in die Okay-Regel fallen lassen) → 280€, damit die Variable `top_deal` auch tatsächlich die Top-Deal-Regel trifft.
- Volle Suite: **452/452 grün**, keine Regression.

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
- **Abschnitt 13 (Plugin-System vollständig):** 21 neue Tests (`test_category_registry.py`: 8, `test_detector_registry.py`: 8, `test_rules_category_plugin_contract.py`: 6). Von Robin in seiner echten Umgebung ausgeführt und bestätigt grün (`test_detector_registry.py` 8/8 bestätigt per Screenshot; `test_rules_category_plugin_contract.py` 6/6 bestätigt). `test_category_registry.py` war nach Behebung des Auslieferungsfehlers zunächst offen -- **jetzt in dieser Sandbox nachgeholt: 8/8 grün** (siehe Ausblick-Punkt 7, erledigt).
- Die zuvor in dieser Datei dokumentierten 3 vorbestehenden Fehler (`test_matcher_ssd_capacity_requirement.py`-Import, `test_sata_ssd_500gb_matcht_nicht_die_1tb_regel`, `test_search_ebay_nutzt_normalisierte_url`) treten beim aktuellen Lauf **nicht** auf -- gemäß Projektprinzip "keine unbesehenen Übernahmen aus der Doku" wird hier nur der tatsächlich in dieser Session verifizierte Zustand (356/356 grün) festgehalten; die Diskrepanz zur älteren Notiz wurde nicht weiter zurückverfolgt.
- **Historie (frühere Läufe, nicht in dieser Session erneut geprüft):** 317/317 vor Schritt A/B/C; 334 gesamt nach Schritt A/B/C (18 neue Tests: 8 SSD-Suche, 3 Log-Rotation, 7 Deals-Aufräumen).

---

## Ausblick / Mögliche nächste Schritte

Offene Punkte, unpriorisiert, keiner davon begonnen:

1. **Phase 9 – Weitere Suchquellen:** Quoka abgeschlossen (siehe Abschnitt 12) -- inkl. behobenem Test-Mock-Bug, alle Tests grün. Mit der Plugin-Registry (Abschnitt 11) kann jede weitere Quelle rein additiv ergänzt werden (Datei in `scrapers/` + `SCRAPER_NAME` + `search_<name>(search_terms, plz, radius_km, max_price)`) -- **wichtig:** bei jeder neuen Quelle müssen zusätzlich alle bestehenden End-to-End-Tests (`run_scan()`) um einen passenden Mock ergänzt werden (siehe Lehre in "Bekannte Probleme"), sonst drohen echte HTTP-Calls in der Testsuite.
   - markt.de, Facebook Marketplace, Hardwareluxx, ComputerBase: noch nicht untersucht.
2. ~~Gaming-PC-Preisgrenzen kalibrieren~~ **In Bearbeitung, siehe Abschnitt 15** — Schritt 1 (Erfassungsfenster öffnen) umgesetzt, Schritt 2–4 wartet auf Datensammlung.
3. ~~SATA-SSD-Preise & `notify_max_price`-Werte gegenprüfen~~ **Erledigt**, siehe Statusübersicht ("SATA-SSD-Preisgrenzen kalibriert") — Top-Deal/Guter-Preis-Werte anhand echter Marktdaten (1039 Datenpunkte) neu berechnet.
4. ~~`detect_ssd_gb()`-Wortstellungslücke~~ **Erledigt**, siehe Statusübersicht — `_CONNECTOR`-Regex in `storage.py` erkennt SATA-Generationsangaben zwischen Größe und "SSD", 7 neue Tests grün.
5. ~~Detector-Registry für `categories/detectors/`~~ **Erledigt** (siehe Abschnitt 13).
6. ~~Phase 10 – Plugin-System vollständig (Kategorien als Plugins)~~ **Erledigt** (siehe Abschnitt 13).
7. ~~Ausstehende Bestätigung: `test_category_registry.py` noch nicht erneut von Robin bestätigt~~ **Erledigt.** In dieser Sandbox erneut ausgeführt: 8/8 grün (Datei enthält mittlerweile 8 statt der ursprünglich dokumentierten 7 Tests -- Diskrepanz nicht weiter zurückverfolgt, siehe Statusübersicht/Abschnitt 13).
8. ~~Dashboard-Redesign (Robins Vorschlag vom 02.08.: Header/Status-Leiste, KPI-Kacheln, Deal-Karten, Filter-Leiste) inkl. nahtloser Live-Refresh ohne `location.reload()`~~ **Erledigt** (siehe Abschnitt 14).

9. **Reselling-/Arbitrage-Erweiterung (neues Konzept, siehe Abschnitt 16):** Noch nicht begonnen. Nächster Schritt: Phase-0-Analyse (`scoring/deal_score.py`, `price_stats.py`, `rules/`) im Hinblick auf Profit-Score + Gebührenmodell.

Kein weiterer Punkt ist priorisiert oder für den nächsten Schritt vorausgewählt -- Freigabe/Auswahl liegt bei Robin.

---

## 16. Nächstes Konzept: Reselling-/Arbitrage-Erweiterung (geplant, nicht begonnen)

**Ziel:** Über den bestehenden Deal-Score hinaus soll der Bot künftig gezielt Angebote erkennen, die sich günstig einkaufen und mit Marge weiterverkaufen lassen ("billig rein, teurer raus"), statt nur "günstig für den Eigenbedarf" zu bewerten.

**Bausteine (priorisiert, unpriorisiert innerhalb der Liste = Reihenfolge ist Vorschlag, keine Festlegung):**

1. **Profit-Score** (höchste Priorität, geringster Architektur-Eingriff): neue Score-Komponente in `scoring/deal_score.py`, die `geschätzter Verkaufspreis (aus PriceStats.market_price/median) − Kaufpreis − Gebühren − Versand = Marge` berechnet. Baut direkt auf der bereits vorhandenen `price_stats.compute_price_stats()`-Infrastruktur auf (Abschnitt "Marktpreis-Statistik", Phase 7).
2. **Gebühren-/Kostenmodell** (neue `rules/fees.yaml` oder Erweiterung von `_global.yaml`): Verkaufsgebühren (eBay %, PayPal), Versandpauschalen, Verpackung. Notwendig, damit Punkt 1 nicht die Marge überschätzt.
3. **Bundle-/Part-Out-Erkennung:** Summe der Einzelkomponenten-Marktpreise (via bestehende Detectors: GPU/CPU/RAM) vs. Angebotspreis bei Komplett-PCs.
4. **Cross-Platform-Preisvergleich:** Preis-Spread desselben Modells zwischen Kleinanzeigen/eBay (setzt weitere Scraper aus Phase 9 voraus, Matcher-Logik bleibt unverändert).
5. **Duplicate-/Cross-Posting-Erkennung:** verhindert Verzerrung der Marktpreis-Statistik durch mehrfach geposteter identischer Angebote.
6. **Time-to-Sell-Schätzung:** Liquiditäts-Proxy aus historischer Verweildauer je Kategorie.
7. **Verhandlungs-Assistent:** Flag für Angebote über Marktpreis, aber mit guter Ausstattung, statt kompletter Verwerfung.

**Empfohlener erster Schritt:** Punkt 1 + 2 gemeinsam (Profit-Score + Gebührenmodell), da beide direkt auf `price_stats.py`/`deal_score.py` aufbauen und ohne neue Scraper/Detectors auskommen. Alle weiteren Punkte setzen mehr Datenbasis bzw. Phase 9 voraus.

**Status:** Phase 0 (Analyse) und Phase 1 (Architekturplanung) abgeschlossen. **Phase 2, Schritt 1 umgesetzt:**
- `rules/_global.yaml`: neue Sektion `fees` (`platform_fee_pct`, `payment_fee_pct`, `shipping_cost`, `packaging_cost`), Default-Werte 10.0 / 2.5 / 6.0 / 1.5.
- `matcher.py::_load_rules_from_dir()`: extrahiert `fees` aus `_global.yaml` analog zu `manufacturer_reputation`, gibt es additiv im Config-Dict zurück (`cfg["fees"]`). Legacy-Einzeldatei-Modus unverändert (kein Crash, `fees`-Key dort schlicht nicht vorhanden).
- `scoring/profit.py` (neu): `Profit`-Dataclass + `compute_profit(purchase_price, estimated_resale_price, fees)`. Nutzt `estimated_resale_price` bewusst noch als Platzhalter (= zukünftig `PriceStats.market_price`) -- methodische Einschränkung (Ankaufs- vs. Verkaufsperspektive) im Modul-Docstring dokumentiert.
- **Noch NICHT umgesetzt (nächste Schritte):** Anbindung an `scoring/deal_score.py` (neue Komponente `"profit"`) und `app.py` (Berechnung von `estimated_resale_price` aus vorhandenem `market_prices`-Dict, Übergabe an `compute_deal_score()`). Aktuell verändert diese Erweiterung das produktive Scoring-Verhalten **nicht**.
- Tests: `tests/test_profit.py` (9 Tests), `tests/test_matcher_fees_loading.py` (3 Tests). Volle Suite: 412/412 grün (Quoka-Netzwerktests in dieser Sandbox ausgenommen, siehe "Bekannte Probleme").

**Phase 2, Schritt 2 umgesetzt (Anbindung an `scoring/deal_score.py`):**
- Neue siebte Komponente `"profit"` in `_COMPONENT_KEYS` und `DEFAULT_WEIGHTS` (Default-Gewicht **0.0** — bewusst, damit bestehende Kategorien unverändert bleiben, analog zum bisherigen Umgang mit `hersteller`/`zustand`/`lieferumfang`).
- Neue Funktion `_profit_score()`: symmetrisch um `margin_pct == 0` (Score 50 = kostendeckend), gekappt bei ±50% Marge (`_PROFIT_MARGIN_CAP_PCT`), `None`-Fallback auf `_PLACEHOLDER_SCORE` (60) — analog zu `_hersteller_score()`.
- `compute_deal_score()`: zwei neue optionale Parameter `estimated_resale_price` und `fees`, ruft intern `profit.compute_profit()` auf und speist das Ergebnis in `_profit_score()` ein.
- **Noch NICHT umgesetzt:** `app.py` berechnet aktuell keinen `estimated_resale_price` und übergibt ihn nicht an `evaluate()`/`compute_deal_score()` — die neue Komponente ist technisch nutzbar, aber im produktiven Scan-Lauf inaktiv (Default-Gewicht 0 UND kein Wert übergeben). Ebenfalls offen: kein `notify_max_price`-/Gate-Bezug zu Marge, keine Dashboard-Anzeige.
- Ein bestehender Test (`test_components_dict_enthaelt_alle_sechs_schluessel`) musste angepasst werden (jetzt 7 statt 6 Schlüssel) — bewusste, erwartete Anpassung, kein Bugfix.
- 5 neue Tests in `tests/test_deal_score.py` (Platzhalter-Verhalten, Score-Neutralität bei Gewicht 0, Score-Anstieg/-Abfall bei aktivem Gewicht, Gebühren-Einfluss). Volle Suite: **417/417 grün** (Quoka-Netzwerktests in dieser Sandbox ausgenommen).

**Phase 2, Schritt 3 umgesetzt (Anbindung an `app.py`):**
- **Befund:** `app.py` reicht `rules_cfg` (das bereits `fees` enthält, siehe Schritt 1) unverändert an `matcher.evaluate()` durch — eine Änderung an `app.py` selbst war dafür nicht nötig. Die eigentliche Verdrahtung fand ausschließlich in `matcher.py::evaluate()` statt.
- `evaluate()`: `compute_deal_score()`-Aufruf um `estimated_resale_price=market_price` (derselbe bereits vorhandene `market_price`-Lookup aus `market_prices`, siehe Phase-1-Entscheidung: Platzhalter = `market_price`, keine separate Verkaufspreis-Schätzung in diesem Schritt) und `fees=rules_cfg.get("fees") or None` ergänzt.
- Damit ist die Kette `price_history.jsonl` → `price_stats.compute_price_stats()` → `market_prices`-Dict (app.py) → `evaluate()` → `compute_deal_score()` → `_profit_score()` vollständig durchgängig, **technisch produktiv aktiv** (kein Code-Pfad mehr fehlt), aber **ohne Auswirkung auf den finalen Score**, solange keine Kategorie-YAML ein `profit`-Gewicht > 0 setzt.
- 3 neue Tests in `tests/test_matcher_deal_score_integration.py`: Durchreichung `market_price` → `estimated_resale_price`, Gebühren-Einfluss über `rules_cfg["fees"]`, Score-Neutralität ohne `market_prices`. Volle Suite: **420/420 grün** (Quoka-Netzwerktests in dieser Sandbox ausgenommen).
- **Damit ist die technische Grundlage des Profit-Scores vollständig (Punkt 1+2 aus der ursprünglichen Konzept-Liste).** Noch offen für eine spätere, separate Freigabe: (a) bewusste Aktivierung (`profit`-Gewicht > 0 in einer Kategorie-YAML, z.B. testweise bei `gpu.yaml`), (b) Dashboard-Anzeige der Marge, (c) methodische Verfeinerung `estimated_resale_price` (getrennt von `market_price`, siehe dokumentierte Einschränkung), (d) Punkte 3–7 aus dem Konzept (Bundle-Erkennung, Cross-Platform, Duplicate-Erkennung, Time-to-Sell, Verhandlungs-Assistent).

**Punkt a umgesetzt (profit-Gewicht testweise in `gpu.yaml` aktiviert):**
- `rules/gpu.yaml`: `scoring_weights` um `profit: 0.2` erweitert, `price` von 0.9 auf 0.7 reduziert (`hardware_qualitaet` unverändert bei 0.1). Einzige Kategorie mit `profit`-Gewicht > 0 -- alle anderen Kategorien bleiben unangetastet auf dem globalen Default 0.0 (`scoring/deal_score.py::DEFAULT_WEIGHTS`).
- Ohne Preishistorie für ein Modell bleibt `profit` weiterhin beim neutralen Platzhalter (60) -- kein Absturz, aber auch (noch) kein Signal.
- `tests/test_app_notification_gate.py::test_notification_gate_end_to_end`: hartcodierte Erwartung basierend auf den alten 90/10-Gewichten musste angepasst werden -- ohne Preishistorie wäre ★★★★★ mit den neuen Gewichten rechnerisch nicht mehr erreichbar (Platzhalter 60 deckelt den Score auf ~91). Test seedet jetzt VOR dem Scan einen `PricePoint` für `rtx_2080_ti` (260€) über `price_history.append_price_point()`, sodass `profit` einen echten Wert liefert -- entspricht dem eigentlichen Einsatzzweck der Komponente.

**Punkt c umgesetzt (`estimated_resale_price` methodisch von `market_price` getrennt):**
- `price_stats.py`: `PriceStats` um zwei neue Felder erweitert (`percentile_75`, `estimated_resale_price`, beide mit Defaults -- rückwärtskompatibel für bestehende `PriceStats(...)`-Konstruktionsstellen, z.B. `test_top_deal.py`). Neue Funktion `_estimated_resale_price()`: nutzt bewusst nur das OBERE Preissegment (P75-P90) derselben Preishistorie-Datenpunkte statt des P10-P90-Trimm-Mittelwerts von `market_price` -- Begründung (siehe Docstring): `price_history.jsonl` enthält ausschließlich vom Bot selbst gematchte, tendenziell günstige Angebote (Angebote oberhalb der `max_price`-Grenze einer Regel tauchen gar nicht erst auf), wodurch `market_price` die Ankaufsseite gut abbildet, die Verkaufsseite aber systematisch unterschätzt. Bei zu wenigen Datenpunkten (< 5) fällt `estimated_resale_price` auf `max_price` zurück (konservativste beobachtete Referenz), NICHT auf den Median wie `market_price` -- vermeidet doppelte Nutzung derselben nach-unten-verzerrten Näherung.
- `app.py`: neue Funktion `_resale_prices_from_stats()` (analog zu `_market_prices_from_stats()`), reduziert die Statistik auf `{price_history_model: estimated_resale_price}`. `run_scan()` berechnet `resale_prices` zusätzlich zu `market_prices` und übergibt beides an `evaluate()`.
- `matcher.py::evaluate()`: neuer optionaler Parameter `resale_prices`. `estimated_resale_price` kommt jetzt bevorzugt aus `resale_prices`; fehlt ein Modelleintrag (oder wird `resale_prices` gar nicht übergeben, z.B. ältere Aufrufer/Tests), Fallback auf `market_price` -- exakt das bisherige Phase-1-Platzhalter-Verhalten, volle Rückwärtskompatibilität. `market_price` bleibt unverändert Input für die `"price"`-Komponente (Ankaufsperspektive über `_price_score()`); nur die `"profit"`-Komponente nutzt jetzt den getrennten Verkaufspreis.
- Tests: 5 neue Tests in `tests/test_price_stats.py` (Fallback auf `max_price` statt Median, `estimated_resale_price > market_price` bei genug Daten, `percentile_75`-Lage, Einzeldatenpunkt-Fall), 3 neue Tests in `tests/test_matcher_deal_score_integration.py` (Nutzung von `resale_prices` statt `market_prices`, Fallback bei fehlendem Modelleintrag, Fallback ohne `resale_prices`-Parameter).
- **Keine Auswirkung auf bestehende produktive Scores außer der GPU-Kategorie** (einzige mit `profit`-Gewicht > 0, siehe Punkt a) -- und selbst dort nur, sobald für ein Modell ≥5 Preishistorie-Datenpunkte vorliegen (sonst bleibt der bisherige Platzhalter-/Fallback-Pfad aktiv).
- In dieser Sandbox (kein `pytest` installierbar, kein Netzwerkzugriff): eigener Minimal-Runner ohne pytest-Fixtures verwendet -- **422/443 grün**, alle 21 Fehlschläge weiterhin ausschließlich fehlende `tmp_path`/`monkeypatch`-Fixtures des Runners (siehe Punkt a), keine Regression. Bitte in Robins echter Umgebung mit echtem `pytest` gegenprüfen.

**Punkt b umgesetzt (Marge im Dashboard anzeigen):**
- `matcher.py::MatchResult`: zwei neue additive Felder `estimated_margin_eur`/`estimated_margin_pct`. `evaluate()` ruft dafür separat `scoring.profit.compute_profit(price, market_price, fees_cfg)` auf (bewusste doppelte Berechnung neben der bereits in `compute_deal_score()` erfolgenden — reine Funktion ohne Seiteneffekte, vermeidet eine Signaturänderung von `DealScoreResult`).
- `app.py`: `found.json`-Entry um `estimated_margin_eur`/`estimated_margin_pct` ergänzt (gerundet, `None` falls keine Preishistorie für das Modell vorliegt — additiv, ältere `found.json`-Einträge ohne dieses Feld bleiben kompatibel dank `is defined`-Jinja-Check).
- `templates/index.html`: neue 💰-Zeile auf der Deal-Karte, **in beiden Render-Pfaden** (server-seitiges Jinja UND `renderCardHtml()` für den Live-Refresh ohne `location.reload()`, siehe Abschnitt 14) — grün bei positiver, rot bei negativer Marge, nur sichtbar wenn ein Wert vorliegt.
- Tests: 2 neue app-Level-Tests (`tests/test_app_margin_field.py`, inkl. exakter Berechnung mit echten `_global.yaml`-Gebühren: `market_price=250€` → Marge `+111.25€`/`+111.2%`), 2 neue Matcher-Tests (`MatchResult`-Felder gesetzt/`None`). Zusätzlich manuell gegen einen echten Flask-`test_client()`-Request verifiziert (Status 200, Marge korrekt im gerenderten HTML sichtbar).
- Volle Suite: **424/424 grün** (Quoka-Netzwerktests in dieser Sandbox ausgenommen).

**Punkt d, Baustein 7 umgesetzt (Verhandlungs-Assistent):**
- **Konzept:** Angebote über `max_price` werden nicht mehr zwingend verworfen, sondern können als Verhandlungskandidat markiert werden, wenn Preis und Ausstattung/Score das rechtfertigen — statt "günstig genug oder raus" jetzt auch "zu teuer, aber verhandlungswürdig".
- Neue optionale YAML-Felder **pro Kategorie-Regel** (bewusst kein globaler Fallback in `_global.yaml`, explizite Vorgabe): `negotiation_tolerance_pct`, `negotiation_min_score`, `negotiation_score_component` (muss einer der `_COMPONENT_KEYS` aus `scoring/deal_score.py` sein, dort neu als `COMPONENT_KEYS` öffentlich re-exportiert). Fehlt auch nur eines der drei Felder → Feature für diese Regel inaktiv, unverändertes Verhalten (sofortiges Verwerfen bei `price > max_price`).
- `matcher.py`: Preis-Check im Rule-Loop aufgeweicht — bei Überschreitung von `max_price` UND vollständig konfigurierten `negotiation_*`-Feldern wird zunächst die Toleranzgrenze (`max_price * (1 + negotiation_tolerance_pct/100)`) geprüft, danach (nach Berechnung von `score_result`) die Mindest-Score-Schwelle der konfigurierten Komponente. Ungültiger `negotiation_score_component`-Wert → Warn-Log, kein Crash, Match verworfen. Neues additives Feld `MatchResult.negotiation_candidate: bool = False`.
- `rules/gpu.yaml`: testweise nur an Regel „RTX 3060 12GB ★ Top-Deal" aktiviert (`negotiation_tolerance_pct: 15.0`, `negotiation_min_score: 70`, `negotiation_score_component: "hardware_qualitaet"`) — bewusst an der Top-Deal-Variante (Basis-Score 85) statt „Guter Preis" (Basis-Score max. 65, Schwelle 70 wäre dort nie erreichbar).
- `app.py`: `found.json`-Entry um `negotiation_candidate` ergänzt (additiv).
- `templates/index.html`: neues 🤝-Badge „Verhandelbar", **in beiden Render-Pfaden** (Jinja + `renderCardHtml()`), orthogonal zum bestehenden Top-Deal/Rating-Badge (kann parallel dazu erscheinen, da unabhängige Aussage). Bewusst ohne Zusatzdetail (Toleranz-%/Score) im Badge selbst — spätere Tooltip-Erweiterung als separater Folgeschritt möglich. Kein Einfluss auf das Notification-Gate (weiterhin nur ★★★★★ + Preisgrenze aus Phase 6).
- Tests: 7 neue Matcher-Tests (`tests/test_matcher_negotiation.py`: Toleranz erfüllt/überschritten, regulärer Match ohne Flag, fehlende Felder, ungültige Komponente, Score unter Schwelle), 2 neue App-Level-Tests (`tests/test_app_negotiation_field.py`). Zusätzlich manuell gegen echten Flask-`test_client()`-Request verifiziert (Status 200, Badge + CSS-Klasse im gerenderten HTML sichtbar).
- Volle Suite: **452/452 grün**.
**Punkt d, Baustein 5 umgesetzt (Duplicate-/Cross-Posting-Erkennung):**
- **Konzept:** verhindert, dass mehrfach gepostete/identische Angebote (gleicher Verkäufer postet dasselbe Gerät erneut, oder parallel auf mehreren Plattformen — Kleinanzeigen + eBay) die Marktpreis-Statistik verzerren. Abgrenzung zur bestehenden `seen.json`-Dedup: die erkennt nur exakte URL-Gleichheit (dasselbe Listing zweimal verarbeitet); dieser Baustein erkennt zwei *verschiedene* Listings, die mutmaßlich dasselbe physische Angebot sind.
- Kriterium (abgestimmt): gleiches `price_history_model` + normalisierter Titel identisch + Preis innerhalb Toleranz (**5 %**) + innerhalb Zeitfenster (**30 Tage**). Bewusst nur Titel, keine `location` (Kleinanzeigen-Ortsangaben zu ungenau/inkonsistent) — bei Unsicherheit lieber mehr Duplikate erkennen als weniger.
- `price_history.py`: `PricePoint` um optionales Feld `fingerprint: str | None = None` erweitert (Default, rückwärtskompatibel — ältere `price_history.jsonl`-Zeilen ohne dieses Feld bleiben lesbar). `make_price_point()` nimmt `fingerprint` optional entgegen.
- `duplicate_detection.py` (neu, eigenständiges Modul analog `profit.py`/`price_stats.py`): `normalize_title()` (lowercase, Sonderzeichen/Füllwörter wie „biete"/„verkaufe"/„vb" entfernen, Whitespace vereinheitlichen), `find_duplicate()` (prüft die oben genannten vier Kriterien gegen eine Liste bestehender `PricePoint`s, gibt den gefundenen Duplikat-Punkt oder `None` zurück).
- `app.py::run_scan()`: liest `price_points_this_scan` einmal pro Scan (analog `price_stats_by_model`) und lässt die Liste während des Scans mitwachsen — dadurch werden auch Cross-Postings *innerhalb* desselben Scan-Laufs erkannt, nicht erst beim nächsten. Vor jedem `append_price_point()`-Aufruf wird `find_duplicate()` geprüft: bei Treffer wird **nur der Preishistorie-Eintrag** übersprungen (+ Info-Log mit Modell/Preis/Quelle/Datum des Original-Punkts) — das Match selbst landet unverändert in `found.json`/Dashboard, kein Verlust echter Treffer, kein Einfluss auf Notification-Gate.
- **Standardverhalten wie abgestimmt: aktiv + geloggt** (kein reiner Logging-Modus) — analog zur bestehenden `seen.json`-Baseline, mit Logging zur Überwachung der Trefferquote.
- Tests: 14 neue Tests in `tests/test_duplicate_detection.py` (Titel-Normalisierung, `find_duplicate()`-Kriterien einzeln und kombiniert, Toleranz-/Zeitfenster-Grenzfälle), 3 neue App-Level-Tests in `tests/test_app_duplicate_detection.py` (Cross-Posting über zwei Quellen erzeugt nur einen Preishistorie-Eintrag + beide Treffer bleiben in `found.json`, unterschiedliche Titel erzeugen weiterhin zwei Einträge, Fingerprint wird korrekt persistiert).
- Volle Suite: **469/469 grün**.
- **Noch offen aus Punkt d:** Bausteine 3, 4, 6 (Bundle-/Part-Out-Erkennung, Cross-Platform-Preisvergleich, Time-to-Sell-Schätzung) — noch nicht begonnen, keine Freigabe für einen davon erteilt. Ebenfalls noch offen (separater möglicher Folgeschritt, nicht Teil dieser Freigabe): Toleranz-%/Zeitfenster aus `_global.yaml` statt Modulkonstanten konfigurierbar machen.

**Baustein 5, Folgeschritt umgesetzt (Toleranz-%/Zeitfenster aus `_global.yaml` konfigurierbar):**
- `rules/_global.yaml`: neue Sektion `duplicate_detection` (`price_tolerance_pct: 5.0`, `window_days: 30.0`) — identisch zu den bisherigen Modulkonstanten in `duplicate_detection.py`, jetzt aber ohne Code-Änderung anpassbar.
- `matcher.py::_load_rules_from_dir()`: extrahiert `duplicate_detection` aus `_global.yaml` additiv ins Config-Dict (`cfg["duplicate_detection"]`), exakt analog zu `fees`/`manufacturer_reputation`. Leeres Dict, falls die Sektion fehlt (ältere Configs).
- `app.py::run_scan()`: liest `dup_cfg = rules_cfg.get("duplicate_detection") or {}`, reicht nur tatsächlich gesetzte Werte (`price_tolerance_pct`/`window_days`) als Keyword-Argumente an `find_duplicate()` durch. Fehlt ein Wert (oder die ganze Sektion), greifen weiterhin die Modulkonstanten (`find_duplicate()`-Parameter-Defaults) — volle Rückwärtskompatibilität, kein Crash.
- Tests: 3 neue Tests in `tests/test_matcher_duplicate_detection_loading.py` (Extraktion aus echter `rules/`-Sektion, leeres Dict ohne Sektion, Legacy-Einzeldatei-Modus kein Crash), 1 neuer App-Level-Test in `tests/test_app_duplicate_detection.py` (verschärfte Toleranz 1 % statt 5 % aus `_global.yaml` greift real — 2,5 %-Preisunterschied wird dann NICHT mehr als Duplikat erkannt). Letzterer patcht `rules/_global.yaml` temporär und stellt den Originalinhalt in einem `finally`-Block wieder her.
- Volle Suite: **473/473 grün**.

**Punkt d, Baustein 6 umgesetzt (Time-to-Sell-Schätzung), Schritt 1 (Presence-Tracking-Datenmodell):**
- **Konzept:** Verweildauer eines Angebots (Zeitspanne "zuerst gesehen" bis "zuletzt gesehen, danach delisted") als Liquiditäts-Proxy je Kategorie. Voraussetzung: `seen.json` muss Zeitinformation statt nur einer flachen URL-Liste führen.
- `presence_tracking.py` (neu): `SeenEntry`-Dataclass (`first_seen`/`last_seen`), `migrate_seen_data()` (rückwärtskompatible Migration vom alten Listenformat -- migrierte Einträge bekommen bewusst `first_seen=last_seen=None` statt eines erfundenen Zeitstempels), `mark_seen()`.
- `app.py::run_scan()`: `seen.json` wird jetzt als Dict mit `first_seen`/`last_seen` geführt statt als reines Set von URLs, Migration erfolgt automatisch beim Laden (`migrate_seen_data(_load_json(SEEN_FILE, []))`).
- Tests: 10 neue Tests in `tests/test_presence_tracking.py`, 4 neue App-Level-Tests in `tests/test_app_presence_tracking.py`. Volle Suite: **497/497 grün**.

**Punkt d, Baustein 6 umgesetzt (Time-to-Sell-Schätzung), Schritt 2 (Delisting-Erkennung + Time-to-Sell-Datenpunkte):**
- **Konzept:** Ein zuvor gematchtes Angebot gilt als "delisted", wenn es `delisting_threshold_scans` (Default 3) aufeinanderfolgende Scans NICHT mehr in den rohen Suchergebnissen auftaucht. Daraus wird `time_to_sell = last_seen − first_seen` berechnet und in einer neuen Datei `time_to_sell.jsonl` gespeichert (Modell/Kategorie/Tage) — Grundlage für eine spätere Statistik (Schritt 3, noch offen), analog `price_history.jsonl`/`price_stats.py`.
- `presence_tracking.py` erweitert: `SeenEntry` um `missed_scans: int = 0`, `delisted: bool = False`, `category: str | None = None`, `price_history_model: str | None = None`. Neue Funktion `mark_matched()` (vermerkt `category`/`price_history_model` NUR für tatsächlich gematchte Angebote, direkt im `seen.json`-Eintrag statt in `found.json` nachzuschlagen — Begründung: `found.json` ist auf `FOUND_MAX_ITEMS` begrenzt/rotiert, ein herausrotiertes aber noch nicht delistetes Angebot wäre dort nicht mehr auffindbar; `seen.json` wächst unbegrenzt und bleibt die zuverlässigere Quelle). Neue Funktion `detect_newly_delisted()`: Sweep über alle bekannten URLs, erhöht `missed_scans` für nicht mehr gesehene URLs, setzt es bei erneutem Sehen zurück, markiert `delisted=True` bei Erreichen der Schwelle und gibt nur die *neu* delisteten URLs zurück (verhindert mehrfache Time-to-Sell-Punkte für dasselbe Angebot).
- `time_to_sell.py` (neu, analog `price_history.py`): `TimeToSellPoint`-Dataclass, `make_time_to_sell_point()` (gibt bewusst `None` zurück statt eines Platzhalters bei fehlendem `first_seen`/`last_seen`/`model` oder negativer Dauer — kein erfundener Datenpunkt), `append_time_to_sell_point()` (Schreibfehler bricht den Scan nicht ab, analog `append_price_point()`).
- `app.py::run_scan()`: `mark_matched()` wird nach jedem erfolgreichen Match aufgerufen (bevor das Ergebnis in `category_buckets` einsortiert wird). Am Scan-Ende, EINMAL pro Scan (nicht pro Item, analog `price_stats_by_model`): `detect_newly_delisted()` gegen die Menge der in diesem Scan tatsächlich gesehenen URLs (`raw_urls`, exakt dieselbe Teilmenge wie bei `mark_seen()` oben), für jede neu delistete URL wird `make_time_to_sell_point()` aufgerufen und bei Erfolg per `append_time_to_sell_point()` in `time_to_sell.jsonl` gespeichert (+ Info-Log).
- `rules/_global.yaml`: neue Sektion `presence_tracking` (`delisting_threshold_scans: 3`), analog zum `duplicate_detection`-Muster — fehlt die Sektion/der Wert, greift `presence_tracking.DEFAULT_DELISTING_THRESHOLD_SCANS` (=3) als Fallback, volle Rückwärtskompatibilität.
- **Reines Zusatzsignal:** kein Einfluss auf `deal_score`/`deal_stars`/Notification-Gate/`found.json`. Keine Dashboard-Anzeige in diesem Schritt (separater Folgeschritt, analog zu Marge/Verhandlungs-Assistent).
- **Erwartete Anpassung (kein Bugfix):** 4 Tests aus Schritt 1 (`test_presence_tracking.py`: `test_migrate_altes_listenformat_zu_dict_mit_none_zeitstempeln`, `test_mark_seen_neue_url_setzt_first_seen_gleich_last_seen`, `test_seen_entry_to_dict`; `test_app_presence_tracking.py`: `test_altes_listenformat_wird_beim_scan_automatisch_migriert`) prüften exakte Dict-Gleichheit auf Basis des alten `SeenEntry`-Formats (nur `first_seen`/`last_seen`) und mussten an die vier neuen Felder angepasst werden.
- Tests: 7 neue Unit-Tests in `tests/test_presence_tracking.py` (`mark_matched()`, `detect_newly_delisted()` inkl. Zähler-Reset/Schwellenwert/bereits-delistet-überspringen), 9 neue Tests in `tests/test_time_to_sell.py` (Tage-Berechnung, `None`-Fälle, JSONL-Schreiben, Schreibfehler-Robustheit), 2 neue End-to-End-Tests in `tests/test_app_delisting.py` (mehrere echte `run_scan()`-Läufe: Angebot verschwindet über `delisting_threshold_scans` Scans hinweg → `delisted=True` + genau ein `time_to_sell.jsonl`-Eintrag, kein zweiter Eintrag bei weiteren Scans; Angebot bleibt sichtbar → niemals delisted).
- Volle Suite: **514/514 grün**.
- **Noch offen:** Schritt 3 (Median/Mittelwert-Statistik je Kategorie aus `time_to_sell.jsonl`, analog `price_stats.py`), Schritt 4 (Dashboard-Anzeige). Ebenfalls weiterhin offen aus Punkt d: Baustein 4 (Cross-Platform-Preisvergleich).
