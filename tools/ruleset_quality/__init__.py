"""Ruleset-Qualitaetssystem (Auftrag Phase 19.1-19.5).

Read-only Analyse-/Benchmark-/Instrumentierungswerkzeuge fuer die
Matching-Qualitaet von gpu-watch-v2. Kein Bestandteil der Produktionskette
-- wird von app.py/matcher.py/rule_analyzer.py/rule_coverage.py NICHT
importiert, sondern importiert selbst nur die dort bereits vorhandenen
Funktionen (matcher.evaluate(), matcher.compute_ruleset_signature(),
category_validation.is_still_valid_category()/filter_valid_entries(),
rule_analyzer.analyze_ruleset(), rule_coverage.compute_rule_coverage()).

Es wird bewusst KEINE zweite Matching-/Regex-/Keyword-Engine gebaut --
jede Kategorie-/Match-Entscheidung in diesem Package laeuft ausschliesslich
ueber die oben genannten, bereits produktiven Funktionen.

Schreibt/aendert NIEMALS: app/rules/*.yaml, data/found.json, data/seen.json,
data/price_history.jsonl, app/matcher.py oder sonstige Produktionsdateien.
Alle Ausgaben landen unter tools/ruleset_quality/generated/.
"""
