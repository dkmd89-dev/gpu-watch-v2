PHASE 15 – Matcher & Rule Quality Optimization

Projekt: GPU-Watch v2
Phase: 15
Status: GEPLANT
Ziel: Matcher- und Regelqualität systematisch verbessern, bevor weitere Kategorien oder größere Features implementiert werden.

---

1. Ziel der Phase

Phase 15 konzentriert sich ausschließlich auf die Qualität, Robustheit und Wartbarkeit des Matcher-/Rules-Systems.

Das Projekt besitzt inzwischen:

- mehrere hundert YAML-Regeln
- zahlreiche Kategorien
- "require_all_of"
- "require_any_of"
- "exclude"
- "exclude_category"
- globale Excludes
- "ignore_global_excludes"
- Price-History-Modelle
- Kategorie-Revalidierung
- Deal-Score
- Top-Deal-Logik
- Flip-/Resale-Logik
- 899+ Tests

Die bisherigen Preis-Kalibrierungen haben gezeigt, dass Fehler im Matching erhebliche Auswirkungen auf:

- Price History
- Marktpreise
- Deal Score
- Top Deals
- Flip Candidates
- Resale Confidence
- Dashboard-KPIs

haben können.

Deshalb gilt:

«Vor einer weiteren Ausweitung des Regelwerks muss die vorhandene Matcher-/Rule-Architektur systematisch validiert werden.»

---

2. WICHTIGE Arbeitsregeln für Claude

2.1 Keine Änderungen ohne vorherige Analyse

Claude darf nicht direkt mit Codeänderungen beginnen.

Zuerst:

1. Repository vollständig analysieren
2. aktuelle Architektur verstehen
3. vorhandene Tests untersuchen
4. Matcher-Semantik nachvollziehen
5. Rules-Struktur analysieren
6. bestehende Reports lesen
7. aktuelle Testanzahl feststellen
8. aktuelle Performance messen

Erst danach darf ein Implementierungsvorschlag erstellt werden.

---

2.2 Keine bestehenden Funktionen unnötig verändern

Besonders geschützt:

- Deal-Score
- Top-Deal-Logik
- Flip-Logik
- Resale-Berechnung
- Notification-Gate
- Price-History-Persistenz
- Duplicate Detection
- Presence Tracking
- Category Validation

Diese Systeme dürfen nur verändert werden, wenn Phase 15 einen nachweisbaren Matcher-/Rule-Bug identifiziert.

---

2.3 Keine Preisgrenzen verändern

Phase 15 ist keine Preis-Kalibrierungsphase.

Keine Änderungen an:

max_price
Top-Deal-Grenzen
Guter-Preis-Grenzen
Interessant-Grenzen
Price-History-Modelle

Preisänderungen gehören in eine spätere, separat dokumentierte Phase.

---

2.4 Keine Daten löschen

Nicht löschen oder manipulieren:

data/price_history.jsonl
data/found.json
data/seen.json

Historische Daten dürfen ausschließlich lesend für Analysen verwendet werden.

---

3. Ausgangszustand feststellen

Vor Beginn muss Claude den tatsächlichen aktuellen Zustand des Repositorys dokumentieren.

Ausführen:

git status
git branch --show-current
git log --oneline -10
pytest app/tests/

Zusätzlich prüfen:

git diff
git diff --cached

Der aktuelle Git-Stand darf nicht aus "PROJEKTSTAND_KOMPLETT.md" angenommen werden.

Repository-Zustand ist die Wahrheit.

---

4. Dokumentationsabgleich

Folgende Dokumente lesen:

PROJEKTSTAND_KOMPLETT.md
STATUS.md
PHASE13_VALIDATION_REPORT.md
PHASE14_DATA_QUALITY_REPORT.md
PRICE_CALIBRATION_REPORT.md
PRICE_CALIBRATION_REVIEW.md
PRICE_CALIBRATION_REVIEW_V2.md
PRICE_CALIBRATION_APPLIED.md

Falls einzelne Dateien nicht existieren:

- nicht erfinden
- Existenz dokumentieren
- Analyse mit den vorhandenen Dokumenten fortsetzen

---

5. Phase 15 – Schritt 1

Vollständiger Matcher-Semantik-Audit

Ziel

Die tatsächliche Semantik von "matcher.py" vollständig dokumentieren.

Insbesondere untersuchen:

require_all_of
require_any_of
exclude
exclude_category
exclude_global
ignore_global_excludes
search_terms

Für jede Bedingungsart muss geklärt werden:

- AND oder OR?
- Verhalten bei mehreren Gruppen?
- Verhalten bei leerer Gruppe?
- Verhalten bei fehlenden Feldern?
- Groß-/Kleinschreibung?
- Regex-Verhalten?
- Normalisierung?
- Tokenisierung?
- Sonderzeichen?
- Wortgrenzen?
- Teilstring-Matches?

---

5.1 Kritischer Punkt: require_all_of

Der in Phase 12 entdeckte Fehler muss ausdrücklich als Regression abgesichert werden.

Beispiel:

require_all_of:
  - ["lego", "star wars"]

Die tatsächliche Matcher-Semantik muss anhand des Codes und der bestehenden Tests eindeutig bestimmt werden.

Falls diese Struktur OR bedeutet, darf sie nicht als AND interpretiert werden.

Tests müssen mindestens enthalten:

LEGO Star Wars → Match
LEGO Marvel → kein Star-Wars-Match
Star Wars → kein LEGO-Match
LEGO Harry Potter → kein Star-Wars-Match

---

6. Phase 15 – Schritt 2

Automatischer Rule Analyzer

Es soll ein neues Analysemodul entstehen.

Bevor Code geschrieben wird:

«Architektur und API des Rule Analyzers entwerfen und dokumentieren.»

Empfohlene Datei:

app/rule_analyzer.py

und Tests:

app/tests/test_rule_analyzer.py

Der Analyzer soll zunächst read-only arbeiten.

Er darf keine YAML-Dateien automatisch verändern.

---

7. Rule Analyzer – Prüfungen

7.1 Strukturprüfung

Erkennen:

fehlende Pflichtfelder
ungültige Datentypen
leere Regeln
ungültige require_all_of-Strukturen
ungültige require_any_of-Strukturen
ungültige exclude-Strukturen
ungültige Preiswerte

---

7.2 Duplicate Detection

Erkennen:

identische Regeln
identische Suchbegriffe
identische Matcher-Bedingungen
identische Price-History-Modelle

Beispiel:

WARNING:
rule_A == rule_B

---

8. Rule Analyzer – Overlap Detection

Ermitteln, welche Regeln denselben Titelraum abdecken könnten.

Beispiel:

iphone_15
iphone_15_pro
iphone_15_pro_max

Der Analyzer soll verdächtige Überschneidungen melden.

Wichtig:

«Overlap ist nicht automatisch ein Fehler.»

Deshalb:

INFO
WARNING
ERROR

unterscheiden.

---

9. Rule Analyzer – Shadowed Rules

Ermitteln, ob eine Regel durch eine vorhergehende Regel praktisch nicht mehr erreichbar ist.

Beispiel:

Rule A
  search_terms: ["iphone"]

Rule B
  search_terms: ["iphone 15"]

Wenn die Matcher-Reihenfolge dazu führt, dass Rule B nie erreicht wird, muss das gemeldet werden.

Ausgabe beispielsweise:

WARNING:
Rule B may be shadowed by Rule A

Category:
iphone

Earlier rule:
iphone_generic

Potentially shadowed rule:
iphone_15

---

10. Rule Analyzer – "require_all_of" Suspicion Detection

Automatisch verdächtige Konstruktionen erkennen.

Beispiel:

require_all_of:
  - ["lego", "star wars"]

Wenn laut Matcher-Semantik eine Gruppe OR bedeutet, soll der Analyzer warnen:

WARNING:
Suspicious require_all_of group

Rule:
lego_sw_clone

Group:
["lego", "star wars"]

Reason:
Multiple terms inside one group are evaluated as OR.

Das ist eine der wichtigsten Prüfungen von Phase 15.

---

11. Rule Analyzer – Exclude Conflicts

Erkennen:

search term
+
exclude term

Beispiel:

search_terms:
  - xbox

exclude:
  - xbox

oder:

Rule benötigt Begriff X
Rule schließt X gleichzeitig aus

Solche Regeln sollen mindestens als:

WARNING

erscheinen.

---

12. Rule Analyzer – Unreachable Rules

Regeln identifizieren, die aufgrund ihrer Bedingungen logisch nicht erreichbar sind.

Beispiele:

required term fehlt
exclude widerspricht required term
vorherige Regel deckt vollständigen Suchraum ab

Ausgabe:

ERROR:
Potentially unreachable rule

Category:
...

Rule:
...

Reason:
...

---

13. Phase 15 – Schritt 3

Analyzer gegen komplettes Ruleset laufen lassen

Der Analyzer muss anschließend gegen alle aktuellen YAML-Regeln laufen.

Ergebnis:

RULE ANALYSIS REPORT
====================

Categories: XXX
Rules: XXX

Errors: XX
Warnings: XX
Info: XX

Potential duplicates: XX
Potential overlaps: XX
Potential shadowed rules: XX
Suspicious require_all_of: XX
Exclude conflicts: XX
Unreachable rules: XX

Neues Dokument:

PHASE15_RULE_ANALYSIS_REPORT.md

---

14. Wichtig: Keine automatische Reparatur

Der Analyzer darf in Phase 15 keine Regeln automatisch verändern.

Er soll ausschließlich feststellen:

Was ist auffällig?
Warum ist es auffällig?
Wie sicher ist die Diagnose?
Welche Regel ist betroffen?

Erst danach erfolgt eine manuelle Prüfung.

---

15. Phase 15 – Schritt 4

False-Positive Regression Suite

Auf Basis der bisherigen Erkenntnisse eine zentrale Regression-Suite aufbauen.

Datei:

app/tests/test_rule_regressions.py

Mindestens folgende Problemgruppen berücksichtigen:

LEGO Star Wars
LEGO Clone Wars
LEGO Ninjago
LEGO Bundles
CRT Monitor
Röhrenfernseher
ThinkPad
Retro-Konsolen
Handheld-Zubehör
Konsolen-Zubehör
Controller

Für jede wichtige Regel:

echtes Angebot → muss matchen

bekannter Fehltreffer → darf nicht matchen

---

16. False-Positive Test Matrix

Die Tests sollen nach Möglichkeit eine Matrix bilden:

Kategorie| Positiv| Negativ
LEGO Star Wars| echtes SW-Angebot| Marvel
LEGO Ninjago| echtes Ninjago| Harry Potter
Handheld| echtes Gerät| Ladegerät
Konsole| echte Konsole| Spiel
CRT| echter Fernseher| Bedienungsanleitung
ThinkPad| Laptop| Ersatzteil

---

17. Phase 15 – Schritt 5

Rule Coverage Analysis

Ermitteln, welche Regeln tatsächlich produktive Daten erhalten.

Datenquelle:

price_history.jsonl

Nur lesend.

Für jede Regel:

rule
matches
valid matches
false-positive indicators
sample count
last seen

Beispiel:

iphone_15_128gb
matches: 213
valid: 210
last_seen: 2026-08-09

und:

lego_ninjago_rare
matches: 0
valid: 0
last_seen: never

---

18. Regelqualität

Aus Coverage und bisherigen Daten kann ein Qualitätsindikator entstehen.

Noch keine endgültige automatische Bewertung als Deal-Score.

Nur Diagnose.

Beispiel:

Rule Quality
────────────────────
Match volume       30 %
False-positive rate 30 %
Data freshness     15 %
Price confidence   15 %
Rule stability     10 %

Diese Gewichtung darf in Phase 15 zunächst nur als Vorschlag behandelt werden.

---

19. Phase 15 – Schritt 6

"load_rules()" Performance Optimization

Erst nachdem Matcher/Rules funktional abgesichert sind.

Ziel:

YAML parsing nicht bei jedem API-Request

Implementierung eines Rules-Caches.

Empfohlen:

app/rules_loader.py

oder Erweiterung des bestehenden Loader-Moduls, falls bereits vorhanden.

---

20. Cache-Anforderungen

Der Cache muss:

- thread-safe sein
- ruleset-Änderungen erkennen
- automatisch invalidieren
- keine stale Rules dauerhaft verwenden
- Tests besitzen
- mit bestehendem "compute_ruleset_signature()" arbeiten

Keine zweite parallele Ruleset-Hash-Implementierung erstellen.

---

21. Cache Regression Tests

Tests für:

first load → YAML lesen

second load → Cache Hit

YAML verändert → Cache Miss

ruleset signature verändert → Reload

gleiches Ruleset → kein Reload

---

22. Phase 15 – Schritt 7

Regex Cache

Erst nach erfolgreicher Messung.

Nicht automatisch implementieren.

Benchmark durchführen:

matcher.evaluate()

mit ausreichend vielen Wiederholungen.

Vergleichen:

Baseline
vs.
Regex Cache

Nur implementieren, wenn eine relevante Verbesserung messbar ist.

---

23. Regex Cache Anforderungen

Falls implementiert:

compiled regex
+
lru_cache

oder eine gleichwertige Lösung.

Dabei beachten:

- Speicherverbrauch
- Cache-Größe
- Thread-Sicherheit
- Regex-Pattern-Normalisierung
- Ruleset-Änderungen

Keine Änderung der Matcher-Semantik.

---

24. Performance Benchmark

Vor und nach den Optimierungen messen:

load_rules()
matcher.evaluate()
filter_valid_entries()
/api/status
/api/found

Benchmark mit realistischen Größen:

100 Entries
500 Entries
1000 Entries
2500 Entries
5000 Entries

Dokumentieren:

cold
warm
median
p95

Keine Einzelmessung als endgültigen Beweis verwenden.

---

25. Phase 15 – Schritt 8

Keine "run_scan()"-Großrefaktorierung

Eine Modularisierung von "run_scan()" wird in Phase 15 nicht automatisch durchgeführt.

Grund:

"run_scan()" besitzt aktuell viele Abhängigkeiten.

Nur wenn die Analyse ergibt, dass eine kleine, sichere Extraktion sinnvoll ist, darf ein separater Vorschlag erstellt werden.

Beispielsweise:

scan_context.py

oder:

scan_persistence.py

Aber:

«Kein Big-Bang-Refactoring.»

---

26. Phase 15 – Schritt 9

Testanforderungen

Nach jeder Codeänderung:

pytest app/tests/

muss vollständig erfolgreich sein.

Ziel:

0 failed

Keine Tests löschen.

Keine Tests abschwächen.

Keine Assertions entfernen, nur um Tests grün zu bekommen.

---

27. Teststrategie

Neue Tests müssen mindestens abdecken:

Matcher-Semantik
Rule Analyzer
Duplicate Detection
Overlap Detection
Shadow Detection
require_all_of warnings
Exclude conflicts
Unreachable rules
Rule Coverage
Rules Cache
Cache invalidation
Regex Cache, falls implementiert

---

28. Sicherheitsprüfung nach jeder Änderung

Vor jedem Commit prüfen:

Deal Score unverändert?
Top Deal unverändert?
Flip unverändert?
Resale unverändert?
Notifications unverändert?
Price History unverändert?
Scraper unverändert?
Persistence unverändert?

Wenn eine dieser Komponenten unbeabsichtigt verändert wurde:

«STOPP.»

Änderung untersuchen und zurücknehmen oder ausdrücklich dokumentieren.

---

29. Was NICHT Teil von Phase 15 ist

Nicht durchführen:

❌ neue Kategorien hinzufügen
❌ Preisgrenzen kalibrieren
❌ Deal-Score-Gewichte verändern
❌ Top-Deal-Schwellen verändern
❌ Flip-Schwellen verändern
❌ Resale-Formel ändern
❌ automatische Preis-Selbstkalibrierung
❌ found.json bereinigen/löschen
❌ price_history.jsonl löschen
❌ seen.json löschen
❌ Dashboard redesignen
❌ Scraper komplett neu schreiben
❌ run_scan() komplett refactoren

---

30. Abschlusskriterien

Phase 15 darf erst als abgeschlossen gelten, wenn:

Matcher

[ ] Matcher-Semantik vollständig dokumentiert
[ ] require_all_of Regression geschützt
[ ] bestehende False-Positive-Fixes geschützt

Rule Analyzer

[ ] alle Regeln analysiert
[ ] Duplicate Detection
[ ] Overlap Detection
[ ] Shadow Detection
[ ] require_all_of Detection
[ ] Exclude Conflict Detection
[ ] Unreachable Detection

Datenqualität

[ ] Rule Coverage analysiert
[ ] produktive Regeln identifiziert
[ ] Regeln ohne Daten identifiziert

Performance

[ ] load_rules() Benchmark
[ ] Rules Cache
[ ] Cache Invalidation
[ ] Regex Benchmark
[ ] Regex Cache nur bei messbarem Nutzen

Tests

[ ] gesamte Test-Suite grün
[ ] keine Regression
[ ] keine Tests entfernt

Dokumentation

[ ] PHASE15_RULE_ANALYSIS_REPORT.md
[ ] PROJEKTSTAND_KOMPLETT.md aktualisiert
[ ] STATUS.md aktualisiert

---

31. Empfohlene Reihenfolge

Claude soll exakt in dieser Reihenfolge arbeiten:

PHASE 15
│
├── 1. Repository analysieren
│
├── 2. Matcher-Semantik auditieren
│
├── 3. Rule Analyzer entwerfen
│
├── 4. Rule Analyzer implementieren
│
├── 5. komplettes Ruleset analysieren
│
├── 6. False-Positive Regression Tests
│
├── 7. Rule Coverage
│
├── 8. load_rules() benchmarken
│
├── 9. Rules Cache implementieren
│
├── 10. Cache benchmarken
│
├── 11. Regex benchmarken
│
├── 12. Regex Cache nur bei Nutzen
│
├── 13. vollständige Tests
│
├── 14. Sicherheitsprüfung
│
└── 15. Dokumentation aktualisieren

---

32. STOP-PUNKTE

Claude muss an folgenden Stellen stoppen und Bericht erstatten:

STOP 1

Nach vollständiger Repository- und Matcher-Analyse.

Noch keine Änderungen.

---

STOP 2

Nach dem ersten Rule-Analyzer-Lauf.

Alle gefundenen:

ERROR
WARNING
INFO

vor Implementierung von Fixes dokumentieren.

---

STOP 3

Vor Änderungen an bestehenden YAML-Regeln.

Jede Regeländerung einzeln begründen.

---

STOP 4

Vor Performance-Optimierungen.

Baseline-Messungen dokumentieren.

---

STOP 5

Vor Commit.

Vollständige Tests + Diff + Sicherheitsprüfung.

---

33. Erwartetes Abschlussformat für Claude

Nach Abschluss soll Claude einen Bericht erzeugen:

PHASE 15 COMPLETION REPORT

Matcher:
- Rules geprüft:
- Matcher-Bugs:
- Regression Tests:

Rule Analyzer:
- Rules:
- Errors:
- Warnings:
- Infos:
- Shadowed:
- Overlaps:
- Duplicates:

Data Quality:
- produktive Regeln:
- Regeln ohne Daten:
- auffällige Kategorien:

Performance:
- load_rules vorher:
- load_rules nachher:
- /api/status vorher:
- /api/status nachher:
- Regex vorher:
- Regex nachher:

Tests:
- vorher:
- nachher:
- failed:

Geänderte Dateien:
...

Nicht umgesetzt:
...

Offene Punkte:
...

---

34. Wichtigste Priorität

Die wichtigste Erkenntnis dieser Phase lautet:

«GPU-Watch soll nicht nur möglichst viele Angebote finden, sondern möglichst zuverlässig entscheiden, welche Angebote tatsächlich zur jeweiligen Kategorie gehören und wirtschaftlich relevant sind.»

Daher gilt für Phase 15:

PRECISION > RECALL

korrekter Match
>
möglichst viele Matches

Ein falscher Match kann anschließend Marktpreis, Deal Score, Resale Price und Flip-Erkennung verfälschen.

Deshalb soll jede Optimierung primär die Vertrauenswürdigkeit der Ergebnisse verbessern.

---

35. Abschluss

Phase 15 ist erfolgreich abgeschlossen, wenn das System:

1. seine eigenen Regelprobleme erkennen kann,
2. kritische Matcher-Fehler automatisch durch Tests absichert,
3. problematische Regeln transparent ausweist,
4. Regeln nicht mehr unnötig mehrfach parsen muss,
5. Performance messbar verbessert wurde,
6. keine bestehende Deal-/Resale-Logik unbeabsichtigt verändert wurde.

Keine Feature-Ausweitung während dieser Phase.

Erst nach erfolgreicher Phase 15 soll über neue Kategorien und weiterführende Deal-Intelligence-Funktionen entschieden werden.