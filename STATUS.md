# STATUS — Aktueller technischer Projektstatus

> **Stand:** 2026-08-10  
> **Repository:** `dkmd89-dev/gpu-watch-v2`  
> **Branch:** `main`  
> **HEAD:** `fa218a0826f3b8ae6868c0228c1267a5cd861265`  
> **Technische Referenz:** `TECHNISCHER_PROJEKTSTATUS.md`

## Gesamtstatus

**Stabil / aktiv weiterentwickelbar.** Die zentralen Architekturbausteine sind vorhanden und durch eine umfangreiche Testsuite abgesichert. Der aktuelle Schwerpunkt liegt auf Precision, Datenqualität, Performance-Messung und kontrollierter Modularisierung – nicht auf einem Rewrite.

## Verifiziert dokumentierter Stand

```text
main: fa218a0
fix: reduce false positives across five categories

Vergleich d2effe7...main: 61 Commits ahead, 0 behind

Letzter im Repository dokumentierter vollständiger Testlauf:
1142 passed, 0 failed

Rule Analyzer:
355 Regeln
19 Kategorien
0 Findings
```

Der Teststand 1142/0 stammt aus dem gemergten PR #6. In dieser Dokumentationssession wurde kein lokaler `pytest`-Lauf behauptet, weil kein Repository-Checkout im Ausführungscontainer verfügbar war.

## Abgeschlossen

- ursprüngliche Phasen 0–10
- YAML-Regelwerk und dynamische Kategorie-Discovery
- Scraper- und Detector-Registry
- Deal Score und Notification-Gating
- Price History / Marktpreisstatistik
- separates Resale-Price-Grouping
- Profit-/Flip-Kandidaten mit Margin-Feldern
- Top-Deal-Logik und Dashboard-KPIs
- Duplicate Detection und Presence Tracking
- Kategorie-Revalidierung und Data-Quality-Bausteine
- Rule Analyzer und Rule Coverage
- Rules-/Entry-/Regex-Caching
- Condition-/Lieferumfang-Detektoren
- mehrere neue Kategorien ohne Python-Code
- Phase-15-Performance-Optimierungen
- False-Positive-Audit für `notebook_resell`, `retro_konsolen`, `handhelds`, `konsolen_bundles` und `controller`

## Aktuelle Systemkette

```text
Scraper
  → Dedup / Presence
  → YAML Rules
  → Matcher + Detectoren
  → Deal Score
  → Marktpreis / Resale
  → Profit / Flip
  → Top-Deal / KPIs
  → Notifications
  → Dashboard / API / Statistics
```

Wichtige Architekturregeln:

- `market_price` und `estimated_resale_price` bleiben getrennt.
- Dünne Resale-Daten dürfen keinen künstlich optimistischen Flip-Kandidaten erzeugen.
- YAML bleibt die primäre Erweiterungsebene für Kategorien.
- Neue Detector-Typen benötigen weiterhin Python-Code.
- Die letzten False-Positive-Fixes verwenden bestehende YAML-/Matcher-Primitive statt eines neuen generischen Matcher-Systems.

## Datenqualität / offene Punkte

1. Coverage-/False-Positive-Rate nach ausreichender neuer Datensammlung erneut messen.
2. 22 historische Regelgruppen ohne Produktivdaten beobachten.
3. 663 historische Orphan-Datenpunkte aus der entfernten `spielzeug_bundles`-Kategorie nicht ohne separaten Auftrag löschen.
4. dokumentierte `RX 7600 XT`/`RX 7600`-Überlappung separat bewerten.
5. `controller`-`ladekabel`-Exclude separat bewerten.
6. Resale-Confidence (`HIGH/MEDIUM/LOW`) ist eine mögliche nächste Qualitätsstufe.
7. automatische Data-Quality-Warnungen weiterentwickeln.

## Nächste Prioritäten

### P0 — messen und verifizieren

- echten End-to-End-Scan messen
- Scraping-, Dedup-, Matching-, Scoring-, Statistik-, Persistence- und Notification-Zeiten erfassen
- False-Positive-/Coverage-Rate mit überwiegend Post-Fix-Daten erneut bestimmen

### P1 — Datenqualität

- Resale-Confidence ausbauen
- Datenqualitätsdiagnosen automatisieren
- historische Alt-/Neu-Daten methodisch sauber trennen

### P2 — Wartbarkeit

- `app.py` nur schrittweise weiter modularisieren, wenn konkreter Änderungsdruck besteht
- keine Komplett-Refaktorierung

### P3 — Features

Neue Kategorien oder weitere Deal-Intelligence erst nach den Stabilitäts-/Qualitätsschritten priorisieren.

## Arbeitsregeln

- Kein Big-Bang-Rewrite.
- Keine Threshold-Änderungen ohne Datenbasis.
- Keine Tests löschen oder abschwächen.
- Keine Performance-Optimierung ohne Messung.
- Keine bestehende Business-Logik duplizieren.
- Nach technischen Änderungen vollständige Testsuite ausführen.
- `TECHNISCHER_PROJEKTSTATUS.md` und `STATUS.md` nach abgeschlossenen Änderungen synchron halten.

## Dokumentationsregel

`TECHNISCHER_PROJEKTSTATUS.md` ist die aktuelle technische Referenz. Historische Phase-/Completion-Reports bleiben als Entscheidungs- und Messnachweise erhalten, gelten aber nicht als aktueller HEAD- oder Teststand.
