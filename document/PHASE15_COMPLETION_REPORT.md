# PHASE 15 COMPLETION REPORT

**Stand:** 2026-08-09 · Branch `claude/phase-15-optimierung-i1jncg` ·
PR [dkmd89-dev/gpu-watch-v2#1](https://github.com/dkmd89-dev/gpu-watch-v2/pull/1) (Draft)

Format gemäß `PHASE15_OPTIMIERUNG.md`, Abschnitt 33.

---

## Matcher

- **Rules geprüft:** 355 Regeln über 19 Kategorien (`app/rules/*.yaml`)
- **Matcher-Bugs:** 0 neu gefunden. Der historische Phase-12-Bug
  (`require_all_of` als eine OR-Gruppe statt zweier AND-Gruppen) war zu
  Sessionbeginn bereits gefixt und bereits regressionsgetestet. Zwei
  Beobachtungsfunde ohne Codeänderung dokumentiert (kein bewiesener
  Bug, sondern ein strukturelles Risiko bzw. eine Exclude-Lücke):
  1. `gpu.yaml`: `RX 7600 XT`-Regel enthält `"rx 7600"` als eigenen
     match-Begriff und steht vor den `RX 7600`-Regeln — mit einem
     echten Produktivdatenpunkt bestätigt (ein Nicht-XT-Angebot wurde
     als `rx_7600_xt` gespeichert).
  2. `controller.yaml`: `exclude_category` enthält nur `"kabel"`, nicht
     `"ladekabel"` (anders als `handhelds`/`konsolen_bundles`).
- **Regression Tests:** 38 neue, zentral gebündelte Tests
  (`app/tests/test_rule_regressions.py`) gegen die echten
  `rules/*.yaml`, zusätzlich zu den bereits bestehenden
  `test_matcher_price_calibration_matching_fixes.py` und
  `test_matcher_handheld_false_positives.py`.

## Rule Analyzer

(`app/rule_analyzer.py`, neu — Lauf gegen das komplette Produktiv-Ruleset,
siehe `document/PHASE15_RULE_ANALYSIS_REPORT.md`)

- **Rules:** 355
- **Errors:** 0
- **Warnings:** 0
- **Infos:** 2
- **Shadowed:** 0
- **Overlaps:** 2 (beide `RX 7600 XT` vs. `RX 7600`, siehe oben)
- **Duplicates:** 0

## Data Quality

(`app/rule_coverage.py`, neu — Lauf gegen `price_history.jsonl`, 9.753
Datenpunkte, siehe `document/PHASE15_RULE_COVERAGE_REPORT.md`)

- **Produktive Regeln:** 113 von 135 aktiven `price_history_model`-Gruppen
  haben mindestens einen Datenpunkt.
- **Regeln ohne Daten:** 22 (größtenteils plausibel seltene High-End-
  Varianten wie 512GB/1TB-iPhone/MacBook-SKUs, Nischen-Autoradio-Modelle;
  Ausnahme `gpu/rx_7600` — strukturell erklärt, siehe Matcher-Abschnitt).
  Zusätzlich 3 Orphan-Modelle (`lego_bundle`/`playmobil_bundle`/
  `spielzeug_bundle_sonstige`, Kategorie `spielzeug_bundles` existiert
  nicht mehr, 663 Datenpunkte ohne aktuelle Regel).
- **Auffällige Kategorien:** `retro_konsolen`, `lego_sw_rare`/
  `lego_sw_clone`, `vintage_elektronik` zeigen hohe False-Positive-Raten
  (38–94 %) bei der Re-Validierung gegen aktuelle Regeln — plausibel
  größtenteils Alt-Kontamination aus der Zeit vor den am selben Tag
  committeten Phase-12-Fixes, keine gesicherte Entwarnung (siehe Coverage
  Report Abschnitt 7 für die methodische Einschränkung).

## Performance

- **load_rules() vorher:** 272,35 ms/Aufruf (ungecached, jeder API-Request)
- **load_rules() nachher:** 0,161 ms/Aufruf warm (cold: 395,8 ms einmalig)
  — Rules-Cache (`app/rules_loader.py`), ~1.700x Speedup warm
- **/api/status vorher:** 327,4 ms Median (10 Requests, Cache-Zustand
  simuliert wie vor Schritt 6)
- **/api/status nachher:** 3,0 ms Median (10 Requests, warmer Cache)
  — ~109x Speedup end-to-end
- **Regex (evaluate()) vorher:** 7,558 ms/Aufruf (3.000 Aufrufe, 15
  realistische Titel); cProfile: 83,5 % der Zeit in `_contains_term()`,
  davon ~41 % reines Compile/Escape
- **Regex (evaluate()) nachher:** 3,625 ms/Aufruf — Regex-Cache
  (`matcher.py::_compiled_term_pattern()`), ~2,1x Speedup

## Tests

- **vorher:** 868 passed
- **nachher:** 979 passed
- **failed:** 0

## Geänderte Dateien

Neu:
```
app/rule_analyzer.py
app/rule_coverage.py
app/rules_loader.py
app/tests/test_matcher_regex_cache.py
app/tests/test_rule_analyzer.py
app/tests/test_rule_coverage.py
app/tests/test_rule_regressions.py
app/tests/test_rules_loader.py
document/PHASE15_PERFORMANCE_REPORT.md
document/PHASE15_RULE_ANALYSIS_REPORT.md
document/PHASE15_RULE_COVERAGE_REPORT.md
document/PHASE15_COMPLETION_REPORT.md  (dieser Bericht)
```

Verändert (minimal, verifiziert per `git diff main...claude/phase-15-optimierung-i1jncg`):
```
app/app.py            (+5/-3   — get_rules() statt load_rules() in run_scan())
app/api/deals.py       (+8/-6   — get_rules() statt load_rules(), 2 Stellen)
app/api/status.py      (+6/-4   — get_rules() statt load_rules(), 1 Stelle)
app/matcher.py         (+43/-2  — _compiled_term_pattern()-Cache in _contains_term())
PROJEKTSTAND_KOMPLETT.md  (Abschnitt 25 ergänzt)
STATUS.md                 (Abschnitt 34 ergänzt)
```

Nicht verändert: alle YAML-Regeln, `data/price_history.jsonl`,
`data/found.json`, `data/seen.json`, `scoring/deal_score.py`,
`top_deal.py`, `scoring/profit.py`, `notify.py`, `price_history.py`,
`duplicate_detection.py`, `presence_tracking.py`, `category_validation.py`.

## Nicht umgesetzt

- **`RX 7600 XT`-YAML-Fix** (`"rx 7600"` aus der XT-Regel entfernen):
  dokumentiert (Rule Analyzer + Coverage Report), nicht umgesetzt — STOP 3
  des Auftrags, separate Freigabe für YAML-Änderungen nötig.
- **`controller.yaml`-Exclude-Ergänzung** (`"ladekabel"` analog zu
  `handhelds`/`konsolen_bundles`): dokumentiert, nicht umgesetzt —
  ebenfalls STOP 3.
- **`run_scan()`-Extraktion:** keine sichere, kleine Kandidatin gefunden
  (Schritt 8) — bewusst kein Refactoring.
- **Rule-Quality-Score-Anbindung** an Dashboard/`scoring/deal_score.py`:
  `compute_rule_quality()` ist ausdrücklich nur ein Vorschlag (Auftrag
  Abschnitt 18), keine Integration in diesem Schritt.

## Offene Punkte

1. Die 17,2 % Gesamt-False-Positive-Rate der Coverage-Analyse sollte in
   1–2 Wochen erneut geprüft werden, sobald `price_history.jsonl`
   überwiegend Post-Phase-12-Fix-Daten enthält — aktuell ist eine saubere
   Vorher/Nachher-Trennung anhand der Zeitstempel allein nicht möglich
   (Daten- und Fix-Commit-Zeitstempel fallen auf denselben Tag).
2. Die zwei dokumentierten, aber nicht umgesetzten YAML-Korrekturen
   (`rx_7600_xt`, `controller.yaml`) warten auf STOP-3-Freigabe.
3. 22 Regeln ohne jegliche Produktivdaten weiter beobachten (größtenteils
   plausibel selten, aber nicht abschließend geklärt).
4. Die 3 Orphan-Modelle (663 Datenpunkte, Kategorie `spielzeug_bundles`)
   bleiben unangetastet in `price_history.jsonl` — keine Bereinigung
   ohne expliziten Auftrag (Abschnitt 2.4).
