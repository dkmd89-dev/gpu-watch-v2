# Scan-Performance-Messung (2026-08-15)

**Charakter:** vollständig READ-ONLY — reine Analyse bereits vorhandener Produktivdaten. Kein
Code geändert, kein neuer Scan ausgelöst, keine Optimierung umgesetzt.

## Methodik

`app.py::run_scan()` protokolliert bereits seit Längerem (roadmap.md Phase 2) bei jedem Lauf eine
strukturierte `📊 Scan-Metriken`-Zeile mit Gesamtdauer + Dauer je Phase (Scraping je Quelle,
Matching+Scoring, Price-Stats, Persistence, Notification). Diese Analyse wertet **35 echte,
bereits im Produktivlog vorhandene Scan-Läufe** aus (`data/gpu_watch.log`, Zeitraum
2026-08-13 15:59 – 2026-08-14 13:37, ca. 22 Stunden durchgehender Betrieb) — kein synthetischer
Benchmark, keine neue Messung ausgelöst.

## Ergebnis: Verteilung über 35 Läufe

| Phase | Median | Mean | Min | Max | Anteil (Median) |
|---|---|---|---|---|---|
| **Gesamtdauer** | 1712,0s (28,5 min) | 1693,3s | 1517,4s | 1884,5s | 100% |
| Scraping gesamt | 1522,3s | 1528,0s | 1491,7s | 1625,1s | **88,9%** |
| davon eBay | 438,4s | 442,2s | 426,3s | 485,4s | |
| davon Kleinanzeigen | 548,2s | 549,0s | 527,4s | 602,1s | |
| davon Quoka | 535,5s | 536,8s | 532,4s | 561,5s | |
| Matching+Scoring | 5,9s | 5,3s | 0,8s | 8,8s | 0,3% |
| Price-Stats | 0,3s | 0,3s | 0,3s | 0,4s | 0,02% |
| **Persistence** | 173,6s | 157,2s | 23,6s | 267,2s | **10,1%** |
| Notification | 1,6s | 1,8s | 0,0s | 4,5s | 0,1% |

**Kontext:** `.env` konfiguriert `SCAN_INTERVAL_MINUTES=10` — die tatsächliche Scan-Dauer
(median 28,5 min) ist damit **fast 3× länger als das konfigurierte Intervall**. Der Scheduler
startet den nächsten Lauf erst nach Abschluss des vorherigen (`_scan_running`-Guard in
`run_scan()`), die reale Scan-Kadenz liegt also bei ~28-31 Minuten statt der beabsichtigten 10.

---

## Befund 1: Scraping (88,9%) läuft seriell, nicht parallel

`app.py` iteriert die drei Scraper-Plugins (eBay, Kleinanzeigen, Quoka) in einer einfachen
`for`-Schleife, jedes `plugin.search(...)` läuft vollständig ab, bevor das nächste startet:

```python
for scraper_name, plugin in scraper_plugins.items():
    _scrape_start = time.perf_counter()
    raw += plugin.search(search_terms, defaults["location_plz"], defaults["radius_km"], global_max_price)
    scrape_duration_by_source[scraper_name] = round(time.perf_counter() - _scrape_start, 3)
```

Die drei Einzeldauern summieren sich fast exakt zur Gesamt-Scraping-Zeit (438+548+536 = 1522s ≈
gemessene 1522,3s) — bestätigt: kein verstecktes Parallelisieren, echte Serialisierung. Da es sich
um I/O-gebundene HTTP-Requests an drei unabhängige, voneinander unabhängige Quellen handelt, ist
das ein klassischer Kandidat für Nebenläufigkeit (Threading/Async).

**Theoretisches Potenzial (nur Rechnung, nicht umgesetzt):** liefe das Scraping parallel statt
seriell, würde die Scraping-Zeit auf die langsamste Einzelquelle sinken (Kleinanzeigen, median
548,2s) statt der Summe aller drei (1522,3s) — eine Gesamtdauer von rechnerisch **~730s (12,2
min)** statt 1712s (28,5 min), **~57% weniger**. Das würde die reale Scan-Kadenz erstmals nah an
das konfigurierte 10-Minuten-Intervall heranbringen.

## Befund 2: Persistence (10,1%, bis zu 267s) korreliert nahezu perfekt mit neuen Treffern

Korrelation Persistence-Dauer ↔ Anzahl neuer Treffer (`dedupliziert`) über alle 35 Läufe:
**r = 0,997**. Root Cause: `app.py` speichert bei **jedem einzelnen neuen Treffer** während des
Scans die komplette `found.json` (aktuell `FOUND_MAX_ITEMS=2500`, 2,76 MB) neu:

```python
found.insert(0, entry)
_save_json(FOUND_FILE, found[:FOUND_MAX_ITEMS])   # bei JEDEM neuen Treffer
```

`_save_json()` (`app/persistence/json_store.py`) schreibt bewusst **atomar** (Temp-Datei +
`fsync()` + `os.replace()`) — explizit dokumentiert als Crash-Sicherheit: geht der Prozess mitten
im Scan verloren, bleibt `found.json` nie abgeschnitten/korrupt, und ein bereits als "seen"
markierter Treffer geht nicht verloren. Das ist eine **bewusste, sinnvolle Design-Entscheidung**,
keine Nachlässigkeit — der Preis dafür: bei ~600 neuen Treffern pro Scan (typischer Wert in den
35 Läufen) wird dieselbe ~2,7-MB-Datei ~600× komplett neu geschrieben und gefsynct, statt einmal
am Scan-Ende.

**Theoretisches Potenzial (nur Beobachtung, nicht umgesetzt):** ein Batching (z. B. alle N Treffer
oder alle X Sekunden statt bei jedem einzelnen) könnte die Persistence-Zeit auf einen Bruchteil
reduzieren — bei vollständigem Verzicht auf Zwischenspeicherung theoretisch auf einen einzelnen
Schreibvorgang (deutlich unter 1s), aber das würde die Crash-Sicherheits-Garantie abschwächen
(mehr potenziell verlorene Treffer bei einem Absturz zwischen zwei Batches). Ein sauberer
Kompromiss (z. B. Batching mit kleinem, konfigurierbarem Intervall) ist eine Design-Entscheidung,
keine reine Performance-Frage.

---

## Nicht auffällig

- **Matching+Scoring** (median 5,9s für ~14.200 geprüfte Angebote ≈ 0,4ms/Angebot) — konsistent
  mit der in Phase 15 gemessenen `matcher.evaluate()`-Einzelkosten (~3,6ms bei kaltem Cache,
  deutlich schneller warm) und den dortigen Caching-Maßnahmen. Kein Optimierungsbedarf erkennbar.
- **Price-Stats** (median 0,3s) und **Notification** (median 1,6s) — vernachlässigbar.

---

## Ausdrücklich keine Handlungsempfehlung/Umsetzung

Diese Analyse liefert ausschließlich die in TECHNISCHER_PROJEKTSTATUS.md geforderte
End-to-End-Scanmessung als Grundlage für eine *künftige, separat zu beauftragende*
Optimierungsentscheidung (CLAUDE.md Regel 6: keine Performance-Optimierung ohne vorherige
Messung — diese liegt jetzt vor). Es wurde **keine** Code-Änderung vorgenommen. Beide Befunde
(serielles Scraping, Per-Treffer-Persistence) sind bewusste, historisch begründete
Architekturentscheidungen (siehe Code-Kommentare) — eine Änderung sollte die jeweils zugrunde
liegenden Garantien (Rate-Limit-Schonung bei parallelem Scraping, Crash-Sicherheit bei
Persistence) explizit mit abwägen, nicht nur die reine Laufzeit.

## Bestätigung

Es wurde ausschließlich eine neue, read-only Analyse-Datei erzeugt (dieser Bericht). **Keine**
Änderung an `app/app.py`, `app/persistence/json_store.py`, `data/*` oder sonstigen
Produktionsdateien. Kein neuer Scan ausgelöst. Kein Commit, kein Push, kein Merge, kein PR.
