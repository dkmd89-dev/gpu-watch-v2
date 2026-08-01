# status.md — Aktualisiert bis Schritt "exclude_global-Bugfix + Notification-Gate-Korrektur"

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
- **Dashboard-Kategorie-Dropdown-Fix:** Abgeschlossen (siehe unten). **Punkt 3 (generische KPI-Kacheln pro Kategorie) wartet noch auf Freigabe.**

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
- **Noch offen (wartet auf Freigabe):** Die vier KPI-Kacheln oben im Dashboard (Office-PCs/Gaming-PCs/Top-Deals) sind weiterhin im HTML fest nur für `office_pc`/`gaming_pc` verdrahtet -- GPU und SATA-SSD haben keine eigene Kachel, obwohl das Backend (`category_counts`) die Zahlen für alle Kategorien liefert.



- **Preisgrenzen kalibrieren (Gaming-PC, 400€/550€):** `data/price_history.jsonl` wurde geleert (Altdaten gesichert unter `data/price_history.pre-ebay-fix-backup-20260725.jsonl`), Sammlung beginnt mit dem nächsten produktiven Scan von vorn. **Kalibrierung ist bewusst noch NICHT durchgeführt** — dafür wird ein neuer, ausreichend langer Sammelzeitraum mit dem laufenden Container in Robins realer Umgebung benötigt (kein Netzwerkzugriff auf kleinanzeigen.de/ebay.com in dieser Analyse-Umgebung möglich). Empfehlung: nach einigen Tagen/Wochen produktivem Betrieb erneut mit der dann gefüllten `price_history.jsonl` anfragen.
- **SATA-SSD-Preise gegenprüfen:** die neuen 250GB/500GB-max_price-Werte (12/18€ bzw. 18/28€) sind grobe Schätzwerte, noch nicht anhand echter Marktdaten kalibriert -- nach ersten Treffern prüfen.
- **notify_max_price-Werte sind ebenfalls Schätzungen** (GPU 250€, Office-PC 200€, Gaming-PC 400€) -- nach ein paar Tagen Betrieb prüfen, ob die Benachrichtigungsfrequenz für Robin passt, und ggf. nachjustieren.
- **Optional (Polishing):** Nahtloser Live-Refresh der Angebotssortierung ohne vollen `location.reload()`.

---

## Bekannte Probleme & Einschränkungen

- **Datenbasis für Deal-Score:** Da im Listen-Scraping keine vollständigen Beschreibungstexte/Galeriebilder geladen werden, fallen Teil-Scores für Zustand oder Lieferumfang standardmäßig neutral aus.
- **Konservative Erkennungsgrenzen bei Detectors:** Strikte Adjazenzprüfungen bei RAM/CPU zur Vermeidung von False Positives.
- **`price_history.jsonl` wurde zurückgesetzt** (Backup unter `data/price_history.pre-ebay-fix-backup-20260725.jsonl`, nicht geloescht). Marktpreis-Statistik/Top-Deal-Erkennung/dynamischer Preis-Score in `deal_score.py` fallen bis zur erneuten Datensammlung auf ihre dokumentierten Fallbacks zurück (kein Marktpreis vorhanden → reines `max_price`-Signal, kein Crash, siehe `read_price_points()`/`_load_price_stats()`).

---

## Testabdeckung

- **Testsuite:** pytest unter `app/tests/`.
- **Status:** Tatsächlich ausgeführt und verifiziert: **317/317 Tests grün** (0 Fehler), inkl. 10 neuer Tests für notify_max_price, den SATA-SSD-VRAM-Kollisionsfix und den Dashboard-Kategorie-Dropdown-Fix.
