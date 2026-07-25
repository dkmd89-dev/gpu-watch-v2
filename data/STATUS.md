# Projektstatus & Übergabe

## Statusübersicht
- **Phase 0 (Projektanalyse):** Abgeschlossen
- **Phase 1 (Architekturplanung):** Abgeschlossen
- **Phase 2 (YAML-Regelwerk-Refactoring):** Abgeschlossen
- **Phase 3 (Scraper-Entkopplung):** Abgeschlossen
- **Phase 4 (Hardware-Erkennungs-Detectors):** Abgeschlossen
- **Phase 5 (Office- & Gaming-PC-Kategorien):** Abgeschlossen
- **Phase 6 (Deal-Score & Notification-Gating):** In Arbeit (Score-Engine-Entwurf bereit)

---

## Refaktorierte Module & Bestandteile

### 1. Konfiguration & Regelwerk (`app/rules/`)
- Umstellung von Einzeldatei auf Verzeichnisstruktur (`./app/rules/`).
- `_global.yaml`: Zentrale Defaults, globale Excludes, Standortkonfiguration und Benachrichtigungsschwellen (`notifications`).
- `gpu.yaml`: 1:1 migriertes GPU-Regelwerk inkl. kategorie-spezifischem PC-Ausschluss (`exclude_category`).
- `office_pc.yaml` & `gaming_pc.yaml`: Neue Kategorien basierend auf Hardware-Anforderungen (`requirements`) statt reiner Titel-Matching-Listen.
- `docker-compose.yml`: Volume-Mount von Einzeldatei auf Verzeichnis umgestellt.

### 2. Matcher & Erkennungs-Engine (`app/matcher.py` & `app/categories/`)
- Dynamisches Laden aller YAML-Dateien aus `rules/`.
- Automatische Ableitung von `search_terms` aus den geladenen Kategorien (kein Code-Change mehr bei neuen Kategorien).
- **Hardware-Detectors (`app/categories/detectors/`):**
  - `ram.py`: Kapazität (GB) und DDR-Typ (DDR3/DDR4/DDR5) mit strikter Adjazenzprüfung.
  - `cpu.py`: Hersteller, Tier (i5, i7, Ryzen 5 etc.) und konventionsbasierte Generationserkennung.
  - `storage.py`: SSD/HDD-Größen (inkl. TB-Umrechnung) und NVMe-Erkennung.
  - `case.py`: Gehäuse-Formfaktoren mit Disambiguierung (z.B. AIO-Wasserkühlung vs. All-in-One-PC).
  - `gpu.py`: Dedizierte GPUs (GTX/RTX/RX) inklusive Abgleich mit der Vorzugsliste.
  - `psu.py`, `pcie.py`, `windows.py`: Netzteil-Leistung, PCIe-Stecker und OS-Version.
- Unterstützung für den neuen `requirements:`-Regeltyp in `matcher.py` (inkl. Bugfix für Regeln ohne `match:`-Liste).

### 3. Scraper (`app/scrapers/`)
- Aufteilung der Monolith-Datei in ein Python-Package (`scrapers/kleinanzeigen.py`, `scrapers/ebay.py`).
- Implementierung der Schema-Definition (`Listing`-TypedDict in `base.py`) zur Sicherstellung von Feldern wie `description` und `images`.
- Vollständige Abwärtskompatibilität gewahrt (`app.py` musste für das Scraper-Package nicht angepasst werden).

---

## Offene Aufgaben

1. **Phase 6 Fertigstellen (Deal-Score & Notification-Gate):**
   - Verdrahtung des berechneten Deal-Scores in `app.py`.
   - Umstellung des Notification-Gates in `notify.py` / `app.py`: Benachrichtigungen nur noch bei erfülltem Kriterium (z. B. Rating `★★★★★` UND Preis `≤ 150€`).
2. **Phase 7 (Preishistorie & Trendanalyse):**
   - Implementierung der append-only `price_history.jsonl`.
   - On-demand Berechnung von Median und Perzentilen.
3. **Phase 8 (Dashboard / Frontend):**
   - Erweiterung von `index.html` / API um Live-Filter, Statusanzeigen, Deal-Score-Darstellung und Bild-Vorschau.
4. **Kalibrierung der Preisgrenzen:**
   - Die Preisgrenzen in `office_pc.yaml` und `gaming_pc.yaml` basieren auf Schätzwerten und müssen nach den ersten Realläufen am Gebrauchtmarkt angepasst werden.

---

## Bekannte Probleme & Einschränkungen

- **Datenbasis für Deal-Score (Phase 6):** Da Scraper im Listen-Scraping aktuell keine vollständigen Beschreibungstexte oder Galeriebilder laden (um Rate-Limits und Request-Zahlen gering zu halten), fallen Teil-Scores wie „Zustand“ oder „Lieferumfang“ standardmäßig neutral aus.
- **Konservative Erkennungsgrenzen bei Detectors:**
  - *RAM:* Größen ohne expliziten Zusatz wie „RAM“ oder „Arbeitsspeicher“ (z.B. reine Positionsangaben wie `32GB 1TB RX 7800`) werden bewusst ignoriert, um Verwechslungen mit VRAM/SSD zu vermeiden.
  - *CPU:* Verkürzte AMD-Schreibweisen ohne das Wort „Ryzen“ (z.B. `7600X3D` oder `R5600X`) werden nicht gematcht, um Fehlauslösungen mit AMD-Grafikkarten (z.B. RX 6750) zu verhindern.
- **Rate-Limiting bei Kleinanzeigen:** Durch die gestiegene Anzahl an Suchbegriffen (17 Begriffe über 3 Kategorien hinweg) steigt die Anzahl der HTTP-Requests pro Scan-Lauf proportional an.

---

## Testabdeckung

- **Testsuite vorhanden:** `pytest`-Testumgebung unter `app/tests/` aufgebaut.
- **Status:** 167 Tests erfolgreich (100% grün), darunter:
  - Unit-Tests für alle 8 Hardware-Detectors.
  - Integrationstests für das Laden und Zusammenführen von Mehrfach-YAMLs.
  - Regressionstests für alle 34 GPU-Regeln (10-12 konkrete Testfälle aus reallaufenden Treffern).
  - End-to-End Tests für die Kategorie-Erkennung von GPUs, Office-PCs und Gaming-PCs.
