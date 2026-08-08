# GPU-Watch v2 – Optimierungs-Roadmap

## Ausgangslage

Arbeite ausschließlich auf Basis des **aktuellen Repository-Stands**.

Repository:
`dkmd89-dev/gpu-watch-v2`

Vor jeder Änderung zwingend lesen:

* `PROJEKTSTAND_KOMPLETT.md`
* `STATUS.md`

Danach den tatsächlichen aktuellen Code und Git-Stand prüfen.

**Wichtig:** Die Dokumentation kann hinter dem tatsächlichen HEAD zurückliegen. Der tatsächliche Code- und Teststand ist maßgeblich.

Aktuell existiert bereits eine umfangreiche Architektur mit:

* modularen YAML-Kategorien
* Scraper-Registry
* Hardware-Erkennung
* Deal-Score
* Top-Deal-Logik
* Price-History
* Resale-Price-Grouping
* Profit-/Flip-Kandidaten
* Time-to-Sell
* Cross-Platform-Statistiken
* Duplicate Detection
* Presence Tracking
* Dashboard-KPIs
* ntfy Notifications

Der bestehende Teststand ist zu erhalten und nach jeder Änderung vollständig zu prüfen.

---

# Ziel

Das Projekt soll **nicht neu geschrieben**, sondern kontrolliert optimiert werden.

Prioritäten:

1. Wartbarkeit
2. Performance
3. Datenqualität
4. Zuverlässigkeit
5. Skalierbarkeit
6. erst danach neue Features

**Keine unnötigen Rewrites. Keine Breaking Changes. Keine bereits funktionierenden Systeme ohne konkreten Grund ersetzen.**

---

# PHASE 0 – Aktuellen Stand analysieren

Vor Änderungen:

1. Repository vollständig analysieren.
2. `PROJEKTSTAND_KOMPLETT.md` lesen.
3. `STATUS.md` lesen.
4. Git-Branch und HEAD prüfen.
5. tatsächlichen Teststand feststellen.
6. aktuelle Architektur mit Dokumentation vergleichen.
7. veraltete Dokumentationsabschnitte identifizieren.
8. aktuelle technische Schulden identifizieren.
9. Performance-Bottlenecks anhand des Codes bestimmen.
10. vorhandene TODO/Lücken priorisieren.

**In Phase 0 keine Codeänderungen.**

Ergebnis:

```text
AKTUELLER STAND
ARCHITEKTUR
TECHNISCHE SCHULDEN
PERFORMANCE-BOTTLENECKS
DATENQUALITÄTSRISIKEN
EMPFOHLENE REIHENFOLGE
```

---

# PHASE 1 – Dokumentation synchronisieren

`PROJEKTSTAND_KOMPLETT.md` und `STATUS.md` müssen den tatsächlichen aktuellen Repository-Stand widerspiegeln.

Insbesondere prüfen:

* aktuelle Commit-/HEAD-Situation
* aktueller Teststand
* abgeschlossene Flip-Kandidaten-Schritte
* aktuelle Resale-Price-Grouping-Implementierung
* aktuelle Top-Deal-Logik
* aktuelle Dashboard-KPIs
* aktuelle Kategorien
* offene Punkte

Keine technischen Änderungen nur zum Zweck der Dokumentation.

Danach Tests ausführen.

---

# PHASE 2 – Scan-Performance messen

Noch keine Optimierung auf Verdacht.

Zunächst messbare Scan-Metriken einführen bzw. vorhandene Metriken verbessern.

Mindestens erfassen:

```text
Scraping-Zeit je Quelle
Anzahl gescrapter Listings
Anzahl nach Deduplication
Matching-Zeit
Anzahl Matches
Deal-Score-Zeit
Price-Statistics-Zeit
Persistence-Zeit
Notification-Zeit
Gesamtdauer
```

Zusätzlich:

```text
Listings
→ dedupliziert
→ gematcht
→ Top-Deals
→ Flip-Kandidaten
→ Notifications
```

Ziel:

**Erst messen, dann optimieren.**

Bestehendes Prinzip „ein Scraping-Durchlauf pro Quelle, danach kategorieweise Matching“ erhalten.

---

# PHASE 3 – `app.py` kontrolliert modularisieren

`app.py` ist aktuell zu stark gewachsen.

Keinen Komplett-Rewrite durchführen.

Funktionalität schrittweise extrahieren, beispielsweise:

```text
app/
├── app.py
├── scan/
│   ├── orchestrator.py
│   ├── processor.py
│   └── scheduler.py
├── persistence/
│   ├── found_store.py
│   ├── seen_store.py
│   └── json_store.py
├── services/
│   ├── deal_service.py
│   ├── profit_service.py
│   ├── notification_service.py
│   └── statistics_service.py
└── api/
    ├── status.py
    ├── deals.py
    └── history.py
```

Die konkrete Struktur darf angepasst werden, wenn der bestehende Code eine bessere Aufteilung nahelegt.

Regeln:

* keine unnötige Abstraktion
* keine Logik duplizieren
* Single Source of Truth erhalten
* öffentliche Schnittstellen möglichst kompatibel halten
* jeden Extraktionsschritt testen
* nach jedem Schritt vollständige Tests

---

# PHASE 4 – Persistenz analysieren und verbessern

Aktuell existieren unter anderem:

```text
seen.json
found.json
price_history.jsonl
time_to_sell.jsonl
```

JSONL für append-only Historien grundsätzlich beibehalten, sofern kein konkreter Nachteil nachgewiesen wird.

Für operative Daten insbesondere `seen.json` und `found.json` prüfen:

* Ladezeiten
* Schreibzeiten
* Dateigröße
* Speicherverbrauch
* Crash-Sicherheit
* gleichzeitige Zugriffe
* Skalierbarkeit

Danach Entscheidung:

### Option A

JSON weiterhin optimieren, wenn ausreichend performant.

### Option B

SQLite als operative Persistenz einführen.

Falls SQLite sinnvoll ist:

```text
listings
seen
matches
price_history
time_to_sell
notifications
```

Migration schrittweise durchführen.

**Keine Big-Bang-Migration.**

---

# PHASE 5 – Price-History / Resale verbessern

Die bestehende Trennung unbedingt erhalten:

```text
market_price
≠
estimated_resale_price
```

Das bestehende `resale_price_group`-Konzept weiterentwickeln.

Für Resale-Gruppen nach Möglichkeit:

```text
Samples
Median
P10
P25
P75
P90
Datenalter
Confidence
```

einführen.

Ziel:

Eine Resale-Schätzung soll erkennen können, ob ausreichend historische Daten vorhanden sind.

Beispiel:

```text
HIGH confidence
MEDIUM confidence
LOW confidence
```

Keine Resale-Schätzung auf Basis von extrem dünner Datenlage.

Die bestehende Regel „< 5 Datenpunkte → kein Flip-Kandidat“ nicht verschlechtern.

---

# PHASE 6 – Deal-Score vervollständigen

Bestehenden Deal-Score nicht neu erfinden.

Vorhandene Komponenten prüfen:

```text
Preis
Ausstattung
Hardwarequalität
Hersteller
Zustand
Lieferumfang
```

Noch nicht aktivierte Komponenten nur dann aktivieren, wenn echte zuverlässige Detektoren vorhanden sind.

Dafür ggf. implementieren:

### Zustand

Erkennen:

```text
neu
wie neu
sehr gut
gut
gebraucht
beschädigt
defekt
Bastler
```

### Lieferumfang

Positive/negative Signale:

```text
OVP
Rechnung
Originalzubehör
Netzteil
Controller
Zubehör

ohne Netzteil
nur Gerät
defekt
Ersatzteil
```

Keine Gewichtung aktivieren, solange die Erkennung nicht ausreichend zuverlässig getestet ist.

---

# PHASE 7 – Deal Intelligence

Bestehende Systeme nicht ersetzen, sondern zusammenführen.

Signale:

```text
Deal Score
Preisvorteil
Hardwarequalität
Marktpreis
Resale-Preis
estimated_margin
Time-to-Sell
```

Darauf aufbauend langfristig eine gemeinsame Deal-Bewertung ermöglichen:

```text
TOP DEAL
FLIP DEAL
VERY GOOD DEAL
WATCH
```

Beispiel:

```text
🔥 TOP DEAL
💰 Flip-Potenzial: HOCH
📈 Marktpreis: 650 €
💵 Kaufpreis: 450 €
📊 geschätzte Marge: 120 €
⏱ erwartete Verkaufsdauer: kurz
```

Bestehende Top-Deal-Regeln bleiben zunächst unverändert.

---

# PHASE 8 – Notifications optimieren

Notification-Spam reduzieren.

Priorisierung:

```text
★★★★★ + sehr großer Preisvorteil
→ sofort

★★★★☆ + sehr großer Preisvorteil
→ sofort

★★★★★ + hohes Flip-Potenzial
→ Notification

bereits gemeldetes Angebot
→ nicht erneut melden
```

Bestehendes Notification-Gate nicht unnötig ersetzen.

Neue Regeln nur mit Tests.

---

# PHASE 9 – Duplicate Detection verbessern

Bestehende Duplicate Detection weiterentwickeln.

Ziel ist eine robuste Listing Identity / Fingerprint.

Mögliche Signale:

```text
Quelle
normalisierter Titel
Seller
Location
Preis
Bilder
```

Cross-Platform-Angebote sollen perspektivisch als möglicherweise dasselbe physische Angebot erkannt werden können.

Dabei keine aggressiven False-Positive-Regeln einführen.

---

# PHASE 10 – Automatische Datenqualitätskontrolle

Das System soll langfristig erkennen, wenn Regeln oder Daten auffällig werden.

Beispiele:

```text
Price History:
nur 2 Samples

Kategorie:
500 Listings gescrapt
0 Matches

Regel:
91 % der Listings ausgeschlossen

Kategorie:
7 Tage keine Treffer

Preis:
starke Abweichung vom historischen Median
```

Daraus sollen Warnungen/Diagnoseinformationen entstehen.

Ziel:

**Das System soll Fehlkalibrierungen selbst sichtbar machen.**

---

# Dashboard

Dashboard nicht einfach mit immer mehr KPI-Kacheln erweitern.

Hauptansicht übersichtlich halten:

```text
🔥 Top Deals
💰 Flip Deals
⭐ Sehr gute Deals
🆕 Neue Deals
```

Detail-/Analysebereich für:

```text
Kategorie
Quelle
Preisverteilung
Score
Marktpreis
Resale
Marge
Time-to-Sell
```

Bestehende Top-Deal-Transparenz und KPI-Filter erhalten.

---

# Teststrategie

Nach **jeder einzelnen Phase**:

```bash
pytest -q
```

Keine Phase abschließen, wenn Tests fehlschlagen.

Zusätzlich bei relevanten Änderungen:

* Unit Tests
* Integration Tests
* Regression Tests
* reale Datenstrukturen prüfen
* JSON-/JSONL-Kompatibilität prüfen
* Migrationen mit Backup/Dry-Run

Ziel:

```text
Tests vorher: N
Tests nachher: >= N
Failures: 0
```

Tests niemals entfernen oder abschwächen, nur damit die Suite grün wird.

---

# Harte Regeln

## Nicht machen

* kein Big-Bang-Rewrite
* keine unnötige neue Architektur
* keine bestehenden funktionierenden Regeln ersetzen
* keine Thresholds ohne Datenbasis ändern
* keine Tests löschen
* keine Testfälle abschwächen
* keine Breaking Changes ohne zwingenden Grund
* keine neue Kategorie nur um „mehr Features“ zu haben
* keine Performance-Optimierung ohne Messung
* keine Duplikation bestehender Business-Logik

## Immer machen

* vorhandene Architektur zuerst verstehen
* bestehende Single Sources of Truth verwenden
* Änderungen klein halten
* Tests zuerst/parallel ergänzen
* reale Produktionsdaten berücksichtigen
* Migrationen sicher durchführen
* Dokumentation nach abgeschlossenen Änderungen aktualisieren
* Git-Diff nach jeder Phase kontrollieren

---

# Empfohlene Reihenfolge

```text
PHASE 0  Analyse
   ↓
PHASE 1  Dokumentation synchronisieren
   ↓
PHASE 2  Performance messen
   ↓
PHASE 3  app.py modularisieren
   ↓
PHASE 4  Persistenz optimieren
   ↓
PHASE 5  Price-History / Resale Confidence
   ↓
PHASE 6  Deal-Score vervollständigen
   ↓
PHASE 7  Deal Intelligence
   ↓
PHASE 8  Notifications
   ↓
PHASE 9  Duplicate Detection
   ↓
PHASE 10 Datenqualitäts-Automatisierung
```

## Wichtig

**Nicht alle Phasen automatisch in einem Durchlauf implementieren.**

Nach jeder Phase:

1. Änderung durchführen
2. Tests ausführen
3. Ergebnis dokumentieren
4. Git-Diff prüfen
5. Status aktualisieren
6. erst danach nächste Phase beginnen.

Wenn während einer Phase eine bessere oder sicherere Lösung gefunden wird, zuerst die bestehende Architektur berücksichtigen und die Abweichung begründen.

**Priorität ist nicht „möglichst viel Code ändern“, sondern das bestehende GPU-Watch-System messbar robuster, schneller, wartbarer und intelligenter zu machen.**

