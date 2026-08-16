"""Kompatibilitäts-Fassade für das ehemalige Einzelmodul `matcher.py`.

Schritt 1 der Modularisierung (siehe Analysebericht): `matcher.py` wurde zu
diesem Package, der komplette bisherige Inhalt liegt unveraendert in
`core.py`. Dieses `__init__.py` re-exportiert exakt die Namen, die von
`app.py`, `category_validation.py`, `recompute_top_deal.py`,
`rule_analyzer.py`, `rule_coverage.py`, `rules_loader.py`,
`tools/ruleset_quality/common.py` sowie der Testsuite importiert werden
(auch die mit `_` beginnenden, dort de facto als API genutzten Namen).

`from matcher import ...` bzw. `import matcher` funktioniert für alle
Aufrufer unveraendert -- keine Anpassung an Aufrufer-Code noetig.
"""
from __future__ import annotations

from matcher.core import (
    MatchResult,
    PC_AUSSCHLIESSEN,
    DEFAULT_PART_OUT_THRESHOLD_PCT,
    load_rules,
    evaluate,
    compute_ruleset_signature,
    _load_rules_from_dir,
    _vram_gb,
    _compiled_term_pattern,
    _contains_term,
    _any_term,
    _compiled_unless_preceded_pattern,
    _contains_term_unless_preceded_by,
    _any_conditional_exclude,
    _any_conditional_exclude_presence,
    _ist_kompletter_pc,
    _cpu_meets_requirement,
    _ram_meets_requirement,
    _storage_meets_requirement,
    _psu_meets_requirement,
    _case_meets_requirement,
    _gpu_meets_requirement,
    _evaluate_hardware_requirements,
    _build_score_inputs,
)

__all__ = [
    "MatchResult",
    "PC_AUSSCHLIESSEN",
    "DEFAULT_PART_OUT_THRESHOLD_PCT",
    "load_rules",
    "evaluate",
    "compute_ruleset_signature",
    "_load_rules_from_dir",
    "_vram_gb",
    "_compiled_term_pattern",
    "_contains_term",
    "_any_term",
    "_compiled_unless_preceded_pattern",
    "_contains_term_unless_preceded_by",
    "_any_conditional_exclude",
    "_any_conditional_exclude_presence",
    "_ist_kompletter_pc",
    "_cpu_meets_requirement",
    "_ram_meets_requirement",
    "_storage_meets_requirement",
    "_psu_meets_requirement",
    "_case_meets_requirement",
    "_gpu_meets_requirement",
    "_evaluate_hardware_requirements",
    "_build_score_inputs",
]
