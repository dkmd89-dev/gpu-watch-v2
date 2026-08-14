"""Gemeinsame, read-only Hilfsfunktionen fuer das Ruleset-Qualitaetssystem.

Kapselt ausschliesslich Importpfad-Setup und duennes Laden bestehender
Produktions-Artefakte (Regeln, found.json, price_history.jsonl) -- keine
eigene Matching-/Bewertungslogik.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
APP_DIR = REPO_ROOT / "app"
RULES_DIR = APP_DIR / "rules"
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"
TOOL_DIR = Path(__file__).resolve().parent
GENERATED_DIR = TOOL_DIR / "generated"
BASELINES_DIR = GENERATED_DIR / "baselines"
REPORTS_DIR = GENERATED_DIR / "reports"

FOUND_JSON = DATA_DIR / "found.json"
PRICE_HISTORY_JSONL = DATA_DIR / "price_history.jsonl"

if str(APP_DIR) not in sys.path:
    # matcher.py/rules_loader.py/category_validation.py/rule_analyzer.py/
    # rule_coverage.py/price_history.py liegen alle direkt in app/ und
    # importieren sich gegenseitig ueber absolute Modulnamen (z.B.
    # "from matcher import evaluate") -- app/ muss daher wie bei den
    # bestehenden Tests vorne im sys.path stehen. app.py selbst wird NICHT
    # importiert (kein DATA_DIR-Bezug noetig, siehe Modul-Docstring der
    # aufrufenden Skripte).
    sys.path.insert(0, str(APP_DIR))

from matcher import compute_ruleset_signature, evaluate, load_rules  # noqa: E402
from category_validation import is_still_valid_category  # noqa: E402
from rule_analyzer import analyze_ruleset  # noqa: E402


def load_current_rules() -> dict:
    """Laedt die aktuellen Produktivregeln aus app/rules/ (read-only)."""
    return load_rules(str(RULES_DIR))


def current_ruleset_signature(rules_cfg: dict | None = None) -> str:
    if rules_cfg is None:
        rules_cfg = load_current_rules()
    return compute_ruleset_signature(rules_cfg)


def load_found_entries() -> list[dict]:
    """Liest data/found.json read-only. Gibt eine neue Liste zurueck --
    der Aufrufer kann sie beliebig verarbeiten, ohne die Originaldatei zu
    beruehren."""
    if not FOUND_JSON.exists():
        return []
    with FOUND_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def rule_counts_by_category(rules_cfg: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in rules_cfg.get("rules", []):
        cat = rule.get("_category") or "_legacy"
        counts[cat] = counts.get(cat, 0) + 1
    return counts


__all__ = [
    "REPO_ROOT",
    "APP_DIR",
    "RULES_DIR",
    "DATA_DIR",
    "DOCS_DIR",
    "TOOL_DIR",
    "GENERATED_DIR",
    "BASELINES_DIR",
    "REPORTS_DIR",
    "FOUND_JSON",
    "PRICE_HISTORY_JSONL",
    "load_current_rules",
    "current_ruleset_signature",
    "load_found_entries",
    "rule_counts_by_category",
    "evaluate",
    "is_still_valid_category",
    "analyze_ruleset",
]
