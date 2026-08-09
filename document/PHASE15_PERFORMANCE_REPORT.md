# Phase 15 – Performance Report (Schritt 6: Rules-Cache)

**Stand:** 2026-08-09 · **Status:** Rules-Cache implementiert, an allen drei Aufrufstellen angebunden. Keine Matcher-/Regel-Semantik verändert.

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

## 5. Nicht Teil dieses Schritts

- **Regex-Cache (Schritt 7):** noch nicht implementiert. Laut Auftrag
  erst nach eigenem Benchmark von `matcher.evaluate()` und nur bei
  messbarem Nutzen (STOP 4) — separater, noch ausstehender Schritt.
- Keine Änderung an der Matcher-Semantik, keinen YAML-Regeln, keinen
  `data/`-Dateien.
