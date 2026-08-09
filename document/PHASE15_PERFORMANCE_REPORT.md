# Phase 15 – Performance Report (Schritt 6: Rules-Cache, Schritt 7: Regex-Cache)

**Stand:** 2026-08-09 · **Status:** Beide Caches implementiert und angebunden. Keine Matcher-/Regel-Semantik verändert.

---

## 1. Baseline (vor der Optimierung, siehe auch STOP-1-Analyse)

`matcher.load_rules("rules")` parst bei jedem Aufruf alle 19 YAML-Dateien
im `rules/`-Verzeichnis komplett neu:

```
20x load_rules() direkt (ungecached): 5.447 ms gesamt, 272,35 ms/Aufruf
```

Vor diesem Schritt geschah das bei **jedem einzelnen HTTP-Request** auf
`/`, `/api/found` (`api/deals.py`) und `/api/status` (`api/status.py`)
sowie bei jedem Scan-Zyklus (`app.py::run_scan()`) — kein Caching.

---

## 2. Implementierung

`app/rules_loader.py` (neu, Phase 15 Schritt 6): cached Drop-in-Ersatz
`get_rules(path)` für `matcher.load_rules(path)`.

- **Invalidierung** über einen günstigen Datei-Fingerabdruck (Name +
  mtime_ns + Größe aller Dateien, die `load_rules()` tatsächlich liest:
  alle `*.yaml` im Wurzelverzeichnis + `mappings/component_values.yaml`)
  — kein TTL, keine stale Rules (Auftragsvorgabe Abschnitt 20).
- **`get_ruleset_hash(path)`** liefert die zuletzt berechnete
  `matcher.compute_ruleset_signature()`-Signatur aus dem Cache zurück,
  ohne sie erneut zu berechnen — keine zweite, parallele
  Hash-Implementierung (Auftragsvorgabe).
- **Thread-sicher** über ein `threading.Lock` (analog zum bestehenden
  Cache-Muster in `category_validation.py`).
- Angebunden in allen drei bisherigen `load_rules()`-Aufrufstellen:
  `api/deals.py` (`index()`, `/api/found`), `api/status.py`
  (`/api/status`), `app.py` (`run_scan()`).

## 3. Benchmark (nach der Optimierung)

```
Cold (1. Aufruf, muss parsen):        395,8 ms
Warm (20x, aus dem Cache):              3,2 ms gesamt (0,161 ms/Aufruf)

Speedup warm vs. ungecached: ~1.692x
```

Nebeneffekt-Messung: die komplette Testsuite (viele Tests instanziieren
je eine frische Flask-App gegen dasselbe echte `rules/`-Verzeichnis, z.B.
`test_category_validation_cache.py`) lief nach der Anbindung spürbar
schneller (107 s → 87 s bei identischer, sogar um 12 Tests gewachsener
Suite) — konsistent mit dem gemessenen Speedup.

## 4. Sicherheitsprüfung

- Ergebnis von `get_rules()` ist bei unverändertem Regelwerk **exakt
  identisch** zu `matcher.load_rules()` (dediziert getestet, siehe
  `test_rules_loader.py::test_ergebnis_identisch_zu_ungecachtem_load_rules`)
  — reine Performance-Optimierung, kein Verhaltensunterschied.
- Deal-Score, Top-Deal-Logik, Flip-/Resale-Berechnung, Notification-Gate,
  Price-History-Persistenz, Duplicate Detection, Presence Tracking,
  Category Validation: keine dieser Dateien wurde verändert. Nur die
  `load_rules`-Importzeile und der jeweilige Aufruf wurden in `app.py`,
  `api/deals.py`, `api/status.py` ausgetauscht (`load_rules(...)` →
  `get_rules(...)`), sonst keine Codeänderung an diesen Dateien.
- `app.py` behält den `load_rules`-Import zusätzlich bei (wird von
  `test_app_delisting.py::test_...` direkt über `app_mod.load_rules(...)`
  verwendet) — keine Testdatei musste angepasst werden.
- 22 neue Tests (`test_rules_loader.py`): Cache Hit/Miss bei
  unverändertem/geändertem/neu hinzugefügtem YAML, Signatur-Konsistenz
  ("gleiches Ruleset → kein wahrgenommener Hash-Wechsel trotz
  Datei-Touch"), Thread-Sicherheit (20 parallele Zugriffe), `invalidate()`.
- Gesamtsuite: **970 passed, 0 failed** (958 vorher + 12 neue
  `test_rules_loader.py`-Tests). Keine bestehende Testdatei musste
  geändert werden.

---

# Schritt 7: Regex-Cache

Auftragsvorgabe (Abschnitt 22): erst benchmarken, nur bei messbarem
Nutzen implementieren. STOP 4: Baseline-Messung vor der Optimierung.

## 6. Benchmark VOR der Optimierung (Baseline)

`matcher.evaluate()` gegen 15 realistische Titel (Treffer verschiedener
Kategorien + 1 kompletter Nicht-Treffer), 200 Wiederholungen (3.000
`evaluate()`-Aufrufe):

```
Baseline: 3.000 Aufrufe in 22.672,9ms (7,558ms/Aufruf)
```

`cProfile`-Analyse derselben 3.000 Aufrufe zeigt, wo die Zeit hingeht:

```
_contains_term()      83,5 % der evaluate()-Gesamtzeit (12.316.200 Aufrufe)
  davon re._compile()   21,8 % der evaluate()-Gesamtzeit
  davon re.escape()     19,0 % der evaluate()-Gesamtzeit
  davon Pattern.search() 15,4 % (die eigentliche Suche -- nicht vermeidbar)
  davon re.UNICODE-Flag-Lookup (enum) ~10 %
```

**~41 % der Gesamtzeit ist reines Kompilieren/Escapen desselben, festen
Begriffs-Vokabulars** (625 verschiedene kleingeschriebene Begriffe im
aktuellen Regelwerk) bei JEDEM einzelnen Aufruf — obwohl sich die
Begriffe zwischen zwei Regel-Ladezyklen nicht ändern. Eindeutig über der
Signifikanzschwelle für einen Regex-Cache.

## 7. Implementierung

`matcher.py::_compiled_term_pattern()` (neu): `functools.lru_cache(maxsize=4096)`
um die bisherige Pattern-Bau-Logik aus `_contains_term()`. `_contains_term()`
selbst bleibt in Signatur und Semantik unverändert (Wortgrenzen, Case-
Insensitivity, Sonderzeichen-Escaping) — nur die Kompilierung wird beim
zweiten und jedem weiteren Aufruf mit demselben (kleingeschriebenen)
Begriff wiederverwendet statt neu zu erfolgen. `maxsize=4096` bewusst
begrenzt (nicht unbounded), aber großzügig über der aktuellen
Begriffsmenge (625) — Begriffe kommen ausschließlich aus den
vertrauenswürdigen YAML-Regeln, kein von außen kontrollierter Input.
Keine Invalidierung bei Ruleset-Änderungen nötig: ein kompiliertes Pattern
hängt nur vom Begriffs-String selbst ab, nicht davon, aus welcher
Regel/welchem Ruleset-Stand er stammt.

## 8. Benchmark NACH der Optimierung

Gleicher Aufbau (15 Titel, 200 Wiederholungen, 3.000 Aufrufe, nach
Cache-Warmup):

```
Mit Regex-Cache: 3.000 Aufrufe in 10.875,1ms (3,625ms/Aufruf)
Speedup: ~2,1x
```

## 9. Sicherheitsprüfung

- Diff in `matcher.py` beschränkt auf: einen neuen Import
  (`functools`), eine neue, gecachte Hilfsfunktion
  (`_compiled_term_pattern()`), und zwei geänderte Zeilen in
  `_contains_term()` (Pattern-Bau ausgelagert). Keine andere Zeile in
  `matcher.py` verändert.
- 9 neue, dedizierte Tests (`test_matcher_regex_cache.py`): Cache Hit/
  Miss, Groß-/Kleinschreibung teilt sich einen Cache-Eintrag, Wortgrenzen/
  Sonderzeichen/Mehrwort-Phrasen-Korrektheit unverändert, Thread-Sicherheit
  (parallele Zugriffe mit unterschiedlichen Begriffen).
- Gesamtsuite (alle 979 Tests, inkl. sämtlicher bestehender
  Matcher-/Regel-/Deal-Score-/Top-Deal-/Flip-/Notification-Tests): **979
  passed, 0 failed** (970 vorher + 9 neue). Kein einziger bestehender Test
  musste angepasst werden — starkes Indiz, dass die Matcher-Semantik
  tatsächlich unverändert blieb.
- Als Nebeneffekt sank die Laufzeit der Gesamtsuite weiter: 87s → 82s
  (Schritt 6) → 78s (Schritt 7, trotz 9 weiterer Tests).

## 10. Nicht Teil dieses Schritts

- Keine Änderung an der Matcher-Semantik, keinen YAML-Regeln, keinen
  `data/`-Dateien.
- Kein Big-Bang-Refactoring von `_contains_term()`/`_any_term()` — nur
  die Pattern-Kompilierung wird gecacht, die Funktionslogik/-signatur
  bleibt identisch.
