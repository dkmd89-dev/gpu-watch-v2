# CLAUDE.md — gpu-watch-v2

Diese Datei ist die verbindliche Arbeitsanweisung für Claude Code in diesem
Repository. Sie wird bei jeder Session automatisch geladen. Bei Widerspruch
zwischen dieser Datei und einer Chat-Anweisung gilt die explizite
Chat-Anweisung des Nutzers — aber nur für den aktuellen Schritt.

**Single Source of Truth für den technischen Stand:** `TECHNISCHER_PROJEKTSTATUS.md`
**Single Source of Truth für Priorität/Status:** `STATUS.md`

Vor Beginn jeder Session: beide Dateien lesen. Sie überschreiben ggf. den
in dieser CLAUDE.md dokumentierten Stand (Commit-Hash, Testzahlen, Kategorienzahl).

---

## 1. Projekt in einem Satz

Modularer, YAML-gesteuerter Hardware-Deal-Scanner (Kleinanzeigen, eBay) mit
Matching, Scoring, Marktpreis-/Resale-Statistik, Profit-/Flip-Bewertung,
Duplicate Detection, Presence Tracking, Dashboard und ntfy-Benachrichtigung.
Produktiv im Einsatz via Docker Compose. **Kein Rewrite-Projekt — kontrollierte,
inkrementelle Weiterentwicklung.**

## 2. Nicht verhandelbare Arbeitsregeln

Diese Regeln gelten für **jede** Aufgabe, unabhängig davon wie sie formuliert ist:

1. **Kein Big-Bang-Rewrite.** Bestehender Code wird erweitert, nicht neu geschrieben.
2. **Rückwärtskompatibilität ist Pflicht.** Bestehende APIs, YAML-Felder und
   Funktionssignaturen bleiben erhalten, außer eine Änderung ist zwingend nötig
   — dann explizit ankündigen und begründen.
3. **Keine bestehenden Funktionen entfernen.**
4. **Keine Threshold-/Score-/Preisgrenzen-Änderung ohne Datenbasis.** Score-Gewichte,
   Preisgrenzen, `min_rating` etc. werden nicht "gefühlt" angepasst.
5. **Keine Tests löschen oder abschwächen**, auch nicht um eine Änderung grün zu bekommen.
6. **Keine Performance-Optimierung ohne vorherige Messung.**
7. **Keine bestehende Business-Logik duplizieren** — vorhandene Matcher-/Detector-/
   Scoring-Primitiven wiederverwenden statt Parallelstrukturen zu bauen.
8. **YAML ist die primäre Erweiterungsebene für Kategorien.** Neue Kategorien
   MÜSSEN ohne Python-Code-Änderung über `app/rules/*.yaml` möglich sein.
   Neue **Detector-Typen** erfordern dagegen weiterhin Python-Code — das ist
   kein Fehler, sondern Architekturentscheidung.
9. **Geschützte Kernsysteme** (Deal-Score, Top-Deal-Logik, Flip-/Resale-Berechnung,
   Notification-Gate, Price-History-Persistenz, Duplicate Detection, Presence
   Tracking, Category Validation) werden **nur bei nachgewiesenen Matcher-Bugs**
   gezielt angepasst — nie "nebenbei" im Rahmen einer anderen Aufgabe.
10. **Immer nur einen Schritt umsetzen.** Kein paralleles Umsetzen mehrerer großer Features.
11. **Nach jedem Schritt muss das Projekt vollständig lauffähig sein.**

## 3. Zwingender Workflow pro Aufgabe

1. Bestehenden Code zum betroffenen Bereich analysieren (nicht raten, tatsächlich lesen).
2. Kurz erläutern: Warum ist die Änderung nötig? Welche Datei(en) sind betroffen?
3. **Nur den aktuellen Schritt implementieren.** Nicht vorgreifen.
4. Nach Abschluss: **gestuft testen**, nicht reflexartig immer die volle Suite:
   - Bei Änderungen an einer Kategorie/YAML: zuerst
     `pytest app/tests/test_<kategorie>.py -v` (schnell, gibt sofortiges Feedback).
   - Danach: `pytest app/tests/ -k "<kategorie>" -v` (alle Tests mit Bezug zum Namen,
     fängt Seiteneffekte in verwandten Tests ab).
   - **Volle Suite (`pytest app/tests/`) nur** vor Abschluss eines Batches/Schritts
     mit Auswirkung über eine einzelne Kategorie hinaus (z.B. Matcher-, Scoring-,
     Persistence-Änderungen) oder wenn explizit angefragt — nicht nach jeder
     kleinen YAML-Anpassung. Im Zweifel: lieber einmal mehr die volle Suite als
     einen unbemerkten Regressionsfehler riskieren, aber nicht als Standard-Reflex.
   - 1142+ Tests müssen grün sein, bevor ein Schritt als abgeschlossen gilt.
5. Output **immer** in diesem Schema:
   - Zusammenfassung
   - Geänderte Dateien
   - Begründung der Änderungen
   - Empfohlene Tests
   - Mögliche Nebenwirkungen
   - Commit-Nachricht
6. **Danach warten.** Nicht automatisch mit dem nächsten Schritt beginnen,
   auch wenn der nächste Schritt "offensichtlich" ist. Freigabe durch den
   Nutzer erfolgt auch durch das einzelne Wort „Freigabe".
7. `STATUS.md` / `TECHNISCHER_PROJEKTSTATUS.md` werden **nicht** nach jeder
   Einzeländerung aktualisiert, sondern an logischen Batch-Grenzen — auf
   Ansage des Nutzers.

Kommunikationsstil: kurz, direkt, präzise. Deutsch. Keine Wiederholung von
bereits bekanntem Kontext.

## 4. Architektur (Ist-Stand)

```
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

### Verzeichnisstruktur

```
app/
├── app.py                    # Flask-Einstiegspunkt, Scan-Loop, Persistenz-Orchestrierung
│                              # (bereits reduziert, aber weiterhin Kandidat für
│                              #  kontrollierte, bedarfsgetriebene Modularisierung)
├── matcher.py                 # Kern-Matching-Logik gegen YAML-Regeln
├── rules_loader.py             # YAML-Regeln laden (Rules-Cache)
├── rule_analyzer.py            # read-only Diagnose: unerreichbare Regeln, Duplikate, Exclude-Konflikte
├── rule_coverage.py            # Coverage-Messung
├── category_validation.py      # Kategorie-Revalidierung
├── data_quality.py             # Datenqualitäts-Diagnosen
├── deal_intelligence.py        # Deal-Intelligence-Layer
├── scan/
│   └── scheduler.py            # Scan-Scheduling (aus orchestrator-Refactoring hervorgegangen)
├── scrapers/                   # Kleinanzeigen-/eBay-Scraper (Plugin-Registry)
├── rules/                      # ein YAML pro Kategorie, `_global.yaml` = globale Excludes/Thresholds
├── scoring/                    # Deal-Score, Profit-/Flip-Berechnung (scoring/profit.py)
├── categories/detectors/       # Kategorie-spezifische Ausstattungs-/Zustands-/Lieferumfang-Detektoren
├── api/                        # Flask-Blueprints
│   ├── deals.py                # /api/found
│   ├── history.py              # /api/history
│   └── status.py                # /api/status
├── services/
│   └── statistics_service.py   # Marktpreis-/Resale-Statistik
├── persistence/
│   └── json_store.py           # JSON-/Log-I/O-Helfer (seen.json, found.json, price_history.jsonl)
└── tests/                       # pytest-Suite (synthetische Fixtures + echtes Produktiv-Regelwerk)
```

### Grundprinzipien (nicht aufweichen)

- YAML ist Single Source of Truth für Kategorien und viele Matching-/Scoring-Regeln.
- Scraper liefern ausschließlich standardisierte Rohdaten, keine Bewertungslogik.
- Alle Bewertung erfolgt im Matcher/Scoring, nicht im Scraper.
- `market_price` und `estimated_resale_price` bleiben strikt getrennt —
  niemals zusammenführen oder eines aus dem anderen ableiten.
- Notification-Gating ist von Preis-/Resale-Experimenten entkoppelt.
- Dünne Resale-Daten (< 5 Samples pro Resale-Gruppe) erzeugen **keine**
  künstlich optimistische Flip-Einstufung.
- Top-Deal-Regel: `(Score ≥ 80 UND Discount ≥ 25%) ODER (Score ≥ 90 UND Discount ≥ 20%)`.

## 5. Bekannte Fallstricke (vor Änderungen prüfen)

- **Testisolation:** Test-Pattern lädt `app.py` per
  `importlib.util.spec_from_file_location()` nach Setzen von `DATA_DIR` in
  `os.environ` neu. Bei weiterer Extraktion von Modulen aus `app.py` in eigene
  Dateien: `sys.modules`-Cache verursacht sonst stille Cross-Test-Kontamination
  bei Folgeläufen. Explizit gegenprüfen.
- **Neue Scraper ohne Mocks = stille echte HTTP-Calls in Tests.** Jeder neue
  Scraper via Plugin-Registry braucht passende Mocks in **allen**
  `run_scan()`-aufrufenden Tests. Pflicht-Checklistenpunkt, kein Kann.
- **`patch.object()` braucht expliziten Import.** Z.B.
  `patch.object(scrapers.quoka, ...)` schlägt fehl, wenn `import scrapers.quoka`
  im isoliert laufenden Testfile fehlt.
- **`notify_max_price` ist ausschließlich category-level**, kein Per-Rule-Feld.
- **`exclude_global` muss im Directory-Mode explizit extrahiert werden** —
  war früher still inaktiv. Bei Änderungen am Loading-Pfad erneut prüfen.
- **`profit`-Gewicht defaultet auf `0.0`.** Keine Scoring-Änderung an
  bestehenden Kategorien, solange eine Kategorie-YAML kein explizites
  Non-Zero-Gewicht setzt.
- **`estimated_resale_price` hat aktuell Purchase-Perspective-Bias**
  (== `market_price` als Platzhalter). Sell-Perspective-Anpassung ist ein
  offener, dokumentierter Punkt — nicht stillschweigend "fixen".

## 6. Aktuell offene Punkte (siehe STATUS.md für Priorität)

**P0 — Messen/Verifizieren**
- Echten End-to-End-Scan messen (Scraping, Dedup, Matching, Scoring,
  Statistik, Persistence, Notification je Zeitanteil).
- False-Positive-/Coverage-Rate erneut messen, sobald überwiegend
  Post-Fix-Daten vorliegen (letzter Wert: 17,2 %, als Alt-Beobachtungswert
  markiert, nicht belastbar).

**P1 — Datenqualität**
- Resale-Confidence (`HIGH/MEDIUM/LOW`) ausbauen.
- Datenqualitätsdiagnosen automatisieren.
- Alt-/Neu-Daten in `price_history.jsonl` methodisch trennen.

**P2 — Wartbarkeit**
- `app.py` nur bei konkretem Änderungsdruck weiter modularisieren — kein
  proaktives Refactoring ohne Anlass.

**P3 — Features**
- Neue Kategorien/Deal-Intelligence erst nach den Stabilitäts-/Qualitätsschritten.

**Explizit dokumentierte Restlücken (nicht ohne separaten Auftrag anfassen):**
- 663 historische Orphan-Datenpunkte aus entfernter Kategorie `spielzeug_bundles`
  — nicht löschen ohne separaten Auftrag.
- `RX 7600 XT` / `RX 7600`-Überlappung.
- `controller`-`ladekabel`-Exclude.
- 22 Regeln ohne Produktivdaten weiter beobachten, nicht vorschnell entfernen.

## 7. Verifizierter Repo-Stand (Stand 2026-08-10 — vor jeder Session gegen STATUS.md prüfen!)

```
Branch: main
Letzter Code-Commit: fa218a0 — "fix: reduce false positives across five categories"
Vergleich d2effe7...main: 61 Commits ahead, 0 behind
Letzter dokumentierter Testlauf: 1142 passed, 0 failed
Rule Analyzer: 355 Regeln, 19 Kategorien, 0 Findings
```

⚠️ Dieser Stand stammt aus dem gemergten PR #6 und wurde nicht in jeder
Session live gegen einen lokalen Checkout verifiziert. Vor Behauptungen über
den aktuellen Teststand: `pytest app/tests/` tatsächlich ausführen, nicht
aus der Dokumentation übernehmen.

## 8. Vor jeder Regeländerung

1. `app/rule_analyzer.py` laufen lassen (read-only: unerreichbare Regeln,
   Duplikate, Exclude-Konflikte).
2. Testsuite laufen lassen (`cd app && pytest tests/`).
3. Änderung als YAML vornehmen, nicht als Python-Sonderfall — außer es
   handelt sich nachweislich um einen neuen Detector-Typ.

## 9. Empfohlene Custom Skills

Für wiederkehrende, projektspezifische Prüfungen lohnen sich eigene Skills
(via `skill-creator`) statt der vorgefertigten Standard-Skills — diese decken
Word/PDF/Slides ab und sind für dieses Repo irrelevant. Sinnvoll für dieses
Projekt:

- **`yaml-rule-review`** — prüft neue/geänderte Kategorie-YAMLs automatisch
  gegen bekannte Fallstricke, bevor sie committet werden:
  - Feld auf korrektem Level (z.B. `notify_max_price` nur category-level,
    nicht pro Rule)
  - `exclude_category` vorhanden, wo sinnvoll
  - `require_all_of`-Gruppen korrekt strukturiert (AND-Gruppen, nicht versehentlich
    eine flache Liste)
  - Ergänzt, ersetzt aber nicht den Lauf von `app/rule_analyzer.py`.
- **`scraper-checklist`** — wird bei neuen Scrapern (Plugin-Registry) aktiv
  und erinnert verbindlich daran, Mocks in **allen** `run_scan()`-aufrufenden
  Tests zu ergänzen sowie ggf. fehlende explizite Imports
  (`import scrapers.<name>`) zu prüfen — beides bekannte Quellen für stille
  Fehler (echte HTTP-Calls in Tests bzw. `patch.object`-Fehlschläge).

Beide Skills sind optional und ersetzen keine der Regeln aus Abschnitt 2/3 —
sie automatisieren nur die Vorabprüfung.

## 10. Deployment-Hinweis

- YAML-Regeln sind volume-gemountet: Änderungen wirken sofort in Produktion,
  ohne Rebuild.
- Python-Änderungen erfordern `docker compose up --build -d`.
- Vor jedem Vorschlag mit Deployment-Implikation explizit sagen, ob ein
  Rebuild nötig ist oder nicht.
