# STATUS — Aktueller technischer Projektstatus

> **Stand:** 2026-08-10  
> **Repository:** `dkmd89-dev/gpu-watch-v2`  
> **Branch:** `main`  
> **HEAD:** `ca4b35be153c1982187fcae09e5c99b55fbf2b25`  
> **Letzter Code-Commit auf `main`:** `ca4b35b` (PR #8, squash-gemergt) — davor `3eed07f`  
> **Technische Referenz:** `TECHNISCHER_PROJEKTSTATUS.md`

## Gesamtstatus

**Stabil / aktiv weiterentwickelbar.** Die zentralen Architekturbausteine sind vorhanden und durch eine umfangreiche Testsuite abgesichert. Der aktuelle Schwerpunkt liegt auf Precision, Datenqualität, Performance-Messung und kontrollierter Modularisierung – nicht auf einem Rewrite.

## Verifiziert dokumentierter Stand

```text
main: ca4b35b
fix(konsolen_bundles): GameCube-Controller- und Plattform-Bindestrich-Fehltreffer ausschließen (#8)

Letzter Code-Commit davor (main): 3eed07f
fix: Plattformbegriff/Mainboard/Zubehör-Fehltreffer in drei Kategorien beheben

Vergleich d2effe7...fa218a0: 61 Commits ahead, 0 behind
fa218a0..3eed07f: 1 Code-Commit; danach 4 Doku-/Chore-Commits bis 0757580,
0757580..ca4b35b: PR #8 (squash-gemergt, 3 Commits: GameCube-Controller-Fix,
Doku-Batch, Plattform-Bindestrich-Fix)

Letzter im Repository dokumentierter vollständiger Testlauf:
1175 passed, 0 failed (aus der Commit-Message von 3eed07f; in dieser
Session nicht erneut lokal verifiziert, siehe Hinweis unten)

Rule Analyzer:
355 Regeln
19 Kategorien
0 Findings (letzte Messung: nach PR #8 in dieser Session, siehe Batch-Eintrag)
```

Der Teststand 1175/0 stammt aus der Commit-Message von `3eed07f`. In dieser Dokumentationssession war `pytest` selbst nicht ausführbar (kein PyPI-Zugriff zum Nachinstallieren von `pytest`/`flask`/`pyyaml` im Sandbox-Container); als Ersatz wurden betroffene Testdateien per direktem Funktionsaufruf ausgeführt (siehe Batch-Eintrag unten) — das ersetzt keinen vollständigen `pytest app/tests/`-Lauf.

## Zuletzt abgeschlossener Batch

**Dashboard-Match-Validierung Variante C** (PR #8, gemergt via Squash auf `main` als `ca4b35b`):

- Live-Instanz (`romajagijo.zapto.org`) über öffentliche HTTP-Endpunkte verifiziert, soweit ohne Server-Zugriff möglich (kein SSH/Docker-Zugriff auf den Host).
- Zwei `konsolen_bundles`-Match-Lücken aus `3eed07f` identifiziert und **beide geschlossen**:
  1. **"GameCube Controller" ohne "für"/"pro controller"** — `exclude_category_unless_preceded_by`, identisches Muster wie "pro controller". 0 Kollisionen gegen den vollständigen 318-Fingerprint-Korpus aus `data/price_history.jsonl`.
  2. **"Plattform + Bindestrich" ohne "für"** (z.B. "Nintendo Switch - Minecraft FRA mit OVP") — nach separater, datengetesteter Review-Runde (erst als Restlücke dokumentiert offen gelassen, dann auf Ansage des Nutzers gezielt geschlossen) über `exclude_category_unless_also_contains` mit Bindestrich/Halbgeviertstrich als Teil des Suchbegriffs (kein neuer Matcher-Mechanismus). 0 Kollisionen gegen 318-Fingerprint- und einen zusätzlich erschlossenen 186-Titel-Rohkorpus (`data/gpu_watch.log.*`, mit Interpunktion).
- Beide Fixes verwenden ausschließlich bereits produktive YAML-Primitiven, kein neuer Matcher-Code.
- **Weiterhin bewusst offen (neue, kleinere Restlücke):** Spieltitel VOR der Plattform OHNE nachfolgenden Bindestrich (z.B. "Donkey Kong Bananza Nintendo Switch 2 2025 OVP") — dafür gibt es kein Substring-Muster, das nicht auch echte Geräte-Titel träfe.

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
8. `konsolen_bundles`: "Spieltitel VOR Plattform ohne Bindestrich"-Restlücke (siehe Batch-Eintrag oben, z.B. "Donkey Kong Bananza Nintendo Switch 2 2025 OVP") — bewusst offen, kein Substring-Muster ohne Kollisionsrisiko mit echten Geräte-Titeln identifiziert.

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
