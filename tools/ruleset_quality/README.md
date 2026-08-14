# Ruleset-Qualitätssystem (`tools/ruleset_quality/`)

Read-only Analyse-, Benchmark- und Instrumentierungswerkzeuge für die Matching-Qualität
von gpu-watch-v2. Entstanden aus Auftrag Phase 19.1–19.5.

**Kein Bestandteil der Produktionskette.** Wird von `app.py` / `matcher.py` /
`rule_analyzer.py` / `rule_coverage.py` nicht importiert. Importiert selbst ausschließlich
bereits vorhandene, produktive Funktionen — es gibt bewusst **keine zweite
Matching-/Regex-/Keyword-Engine**:

| Funktion | Herkunft |
|---|---|
| `evaluate()`, `load_rules()`, `compute_ruleset_signature()` | `app/matcher.py` |
| `is_still_valid_category()` | `app/category_validation.py` |
| `analyze_ruleset()` | `app/rule_analyzer.py` |
| `compute_rule_coverage()` | `app/rule_coverage.py` |
| `read_price_points()` | `app/price_history.py` |

Jede Kategorie-/Match-Entscheidung in diesem Package läuft ausschließlich über diese
Funktionen. Das Tooling klassifiziert und aggregiert nur, was `evaluate()` &
`is_still_valid_category()` objektiv zurückgeben.

## Schreibschutz

Schreibt/ändert **niemals**:

- `app/rules/*.yaml`
- `data/found.json`
- `data/seen.json`
- `data/price_history.jsonl`
- `app/matcher.py` oder sonstige Produktionsdateien

Alle Ausgaben landen ausschließlich unter `tools/ruleset_quality/generated/` (Baselines,
Reports, Label-Store). `historical_baseline.py` liest einen historischen Commit per
`git archive` in ein `TemporaryDirectory` — kein Checkout, kein Working-Tree-Eingriff.

## Module & Datenfluss

```
label_store.py            docs/DASHBOARD_MATCH_FORENSICS.json
   │                       → ground_truth_labels.json (URL → TP/FP/UNCLEAR)
   ▼
baseline.py                data/found.json (heutiger Korpus)
   │                       → generated/baselines/baseline_<ts>_<sig>.json
   │                         (jeder Eintrag neu bewertet über evaluate() +
   │                         is_still_valid_category(); Verdict nur für im
   │                         Label-Store abgedeckte URLs, sonst UNLABELED)
   ▼
historical_baseline.py     docs/DASHBOARD_MATCH_FORENSICS.json + git archive
   │                       → generated/baselines/historical_forensics_baseline.json
   │                         (Vor-Audit-Snapshot, Ruleset-Signatur zum
   │                         historischen Commit exakt neu berechnet)
   ▼
benchmark.py                nimmt eine Baseline, wertet sie gegen das AKTUELL
   │                        geladene Ruleset erneut aus
   │                       → generated/reports/benchmark_<baseline_id>.json
   │                         (Transition-Matrix: vorher-Verdict × nachher-
   │                         Match-Zustand → Severity/Gate-Label)
   ▼
category_report.py          kombiniert aktuellen Korpus + historischen
   │                        Regressionsvergleich pro Kategorie
   │                       → generated/reports/category_quality_current.{json,md}
   │                       → generated/reports/category_quality_historical_regression.json

price_history_revalidation.py   data/price_history.jsonl (nur lesend)
                                → generated/reports/price_history_revalidation_simulation.json
                                  (Simulation, keine Datei wird verändert)
```

`common.py` kapselt nur Importpfad-Setup (fügt `app/` vorne in `sys.path` ein, da sich die
Produktionsmodule dort gegenseitig über absolute Modulnamen importieren) und dünnes,
read-only Laden bestehender Artefakte (Regeln, `found.json`).

### `label_store.py` — Ground-Truth-Nachschlage-Store

`docs/DASHBOARD_MATCH_FORENSICS.json` ist ein bereits im Repo vorhandenes, per-Titel
klassifiziertes Forensik-Artefakt (2306 Einträge, TP 2252 / FP 19 / UNCLEAR 35) aus
Commit `01afd5b` (2026-08-10), **vor** dem 19-Kategorien-Active-FP-Audit (PR #11–#28).
Es ist die einzige im Projekt vorhandene menschlich/strukturiert verifizierte Ground
Truth — aber kein aktueller Datensatz. `label_store.py` baut daraus **keine neue
Matching-Logik**, sondern nur ein `URL → Label`-Mapping. Einträge ohne Eintrag im Store
sind ausdrücklich `UNLABELED`, nie geraten oder automatisch auf TP gemappt.

### `baseline.py` — aktuellen Korpus einfrieren

Friert `data/found.json` als unveränderliches JSON-Artefakt ein. Jeder Eintrag wird über
den echten Produktionspfad neu bewertet; die TP/FP/UNCLEAR-Klassifikation kommt
ausschließlich aus dem Label-Store (aktuell ~19 % Abdeckung des Korpus, siehe Docstring).

### `historical_baseline.py` — Vor-Audit-Snapshot rekonstruieren

Baut ein zu `baseline.py` kompatibles Artefakt aus dem Forensik-Snapshot, inkl. der
historischen Ruleset-Signatur (per `git archive` aus `app/rules/` zum Snapshot-Commit
neu berechnet). Dient als Selbsttest für `benchmark.py` an einem Fall mit bekanntem
erwarteten Ergebnis (`docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`).

### `benchmark.py` — Regressions-Benchmark

Wertet jeden Eintrag einer Baseline erneut gegen das aktuell geladene Ruleset aus. Der
Benchmark fällt **kein neues** TP/FP-Urteil (das wäre eine zweite Bewertungslogik),
sondern leitet nur den objektiven Match-Zustand "nachher" ab (`KEIN_TREFFER`,
`GLEICHE_KATEGORIE`, `ANDERE_KATEGORIE`, `ANDERE_REGEL`) und kombiniert ihn mit dem
"vorher"-Verdict zu einem Severity-Gate:

| Severity | Bedeutung |
|---|---|
| `CRITICAL` | zuvor bestätigter Treffer (TP) matcht jetzt gar nicht mehr |
| `HIGH_CANDIDATE` | erfordert menschliche Nachprüfung (z. B. TP über anderen Matchpfad, oder bekannter FP weiterhin unverändert aktiv) |
| `WARNING` | Kategoriewechsel, unabhängig vom vorherigen Verdict |
| `INFO` | z. B. bekannter FP verschwindet erwartungsgemäß |
| `NEUTRAL` | unverändert stabil, oder `UNLABELED` (keine Vorher-Aussage möglich) |

### `category_report.py` — Qualitätsmetriken pro Kategorie

Kombiniert den aktuellen Korpus (Baseline) mit dem historischen Regressionsvergleich
(Benchmark über die historische Baseline) zu Precision / False-Positive-Rate pro
Kategorie. Beide Kennzahlen werden **nur über die gelabelte Teilmenge** berechnet
(`labeled_n` wird explizit ausgewiesen, `UNCLEAR`/`UNLABELED` fließen nicht in den Nenner
ein).

### `price_history_revalidation.py` — Preishistorie-Revalidierung (Simulation)

Baut auf `app/rule_coverage.py` (`compute_rule_coverage()`) auf und ergänzt eine
Per-Punkt-Detailsicht: alte/neue Kategorie, altes/neues `price_history_model` pro
historischem Preispunkt. Nur Punkte mit `fingerprint` (~90 % der Zeilen) sind
rekonstruierbar; der Rest zählt separat als `NICHT_REKONSTRUIERBAR`, nicht als
unverändert. Rein lesende Simulation — `data/price_history.jsonl` bleibt unangetastet.

## Ausführung

Alle Module sind sowohl als Bibliothek importierbar als auch einzeln über ihren
`if __name__ == "__main__":`-Block ausführbar. Als Package-Module ausführen (nicht als
Skript-Pfad), damit die relativen Imports innerhalb von `tools/ruleset_quality/`
auflösen:

```bash
cd <repo-root>

# 1. Ground-Truth-Label-Store bauen (wird bei Bedarf auch automatisch erzeugt)
python -m tools.ruleset_quality.label_store

# 2. Aktuellen Korpus einfrieren
python -m tools.ruleset_quality.baseline

# 3. Historischen Vor-Audit-Snapshot rekonstruieren (einmalig / bei Bedarf)
python -m tools.ruleset_quality.historical_baseline

# 4. Benchmark gegen die zuletzt erzeugte Baseline laufen lassen
#    (optional: Pfad zu einer konkreten Baseline-Datei als Argument)
python -m tools.ruleset_quality.benchmark
python -m tools.ruleset_quality.benchmark generated/baselines/historical_forensics_baseline.json

# 5. Kategorie-Qualitätsbericht erzeugen
#    (erwartet vorhandene benchmark_historical_forensics_baseline.json + aktuelle Baseline)
python -m tools.ruleset_quality.category_report

# 6. Preishistorie-Revalidierung simulieren
python -m tools.ruleset_quality.price_history_revalidation
```

Empfohlene Reihenfolge bei einem kompletten Lauf: 1 → 2 → 3 → 4 (für beide Baselines)
→ 5 → 6.

## Erzeugte Artefakte (`generated/`)

```
generated/
├── ground_truth_labels.json                  Label-Store (label_store.py)
├── baselines/
│   ├── baseline_<timestamp>_<signatur>.json   aktueller Korpus (baseline.py)
│   └── historical_forensics_baseline.json     Vor-Audit-Snapshot (historical_baseline.py)
└── reports/
    ├── benchmark_<baseline_id>.json           Transition-Matrix (benchmark.py)
    ├── category_quality_current.{json,md}     Precision/FP-Rate pro Kategorie (category_report.py)
    ├── category_quality_historical_regression.json
    ├── price_history_revalidation_simulation.json
    └── ABSCHLUSSBERICHT.md                    zusammenfassender Bericht Phase 19.1–19.5
```

Alle Artefakte sind Diagnoseausgaben (JSON/Markdown), keine Konfigurationsdateien — sie
werden von der Produktionskette nicht gelesen.

## Tests

`app/tests/test_ruleset_quality_tooling.py` (20 Tests) deckt die reinen
Klassifikations-/Parsing-Bausteine ab, die keine eigene Matching-Entscheidung treffen
(`_after_match_state()`, `classify_gate()`, `parse_forensics()`). Läuft als Teil der
normalen Testsuite:

```bash
pytest app/tests/test_ruleset_quality_tooling.py -v
```

## Bekannte methodische Einschränkungen

- **Label-Store-Abdeckung:** Der Ground-Truth-Label-Store deckt nur die 2306 URLs aus dem
  Forensik-Snapshot ab (~19 % des aktuellen `found.json`-Korpus). Alles darüber hinaus ist
  `UNLABELED` — keine Annahme, keine Heuristik.
- **`benchmark.py` fällt kein neues TP/FP-Urteil.** Fälle, die eine echte Neubewertung
  erfordern würden, werden als `HIGH_CANDIDATE` markiert und explizit als "erfordert
  menschliche Nachprüfung" gekennzeichnet, nicht automatisch entschieden.
- **`price_history_revalidation.py`:** "alte Regel"/"neue Regel" sind nicht
  rekonstruierbar (`PricePoint` speichert nur `category` + `model`, kein `rule_label`) —
  Vergleich erfolgt auf Kategorie-/Modell-Ebene. Nur Punkte mit `fingerprint` (~90 %)
  sind simulierbar.
- **`data/found.json` ist eine Momentaufnahme.** Der Produktiv-Scanner verändert die
  Datei kontinuierlich; jede eingefrorene Baseline ist nur zum Erzeugungszeitpunkt
  gültig.

Details und konkrete Zahlen zum letzten vollständigen Lauf: siehe
`generated/reports/ABSCHLUSSBERICHT.md`.
