"""Regressionstest für den ram-Fix aus dem Active-False-Positive-Audit
(docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Zwei unabhängige Wortgrenzen-/Schreibweisen-Lücken im vollständigen
81-Titel-Match-Korpus:

1. Pluralform "Laptops" wird von bare "laptop" wegen fehlender
   Wortgrenze nicht erfasst (siehe matcher.py::_contains_term()) --
   "Samsung 8GB DDR4 RAM Riegel für Laptops" (SODIMM-Formfaktor)
   matchte bisher als Desktop-RAM.
2. "SO- DIMM" (Bindestrich+Leerzeichen-Variante) wird weder von
   "so-dimm" noch "so dimm" exakt erfasst -- "SK hynix...DDR4 SO- DIMM
   1Rx8..." matchte bisher als Desktop-RAM.

Läuft gegen die echten, produktiven rules/*.yaml."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


def _matches_ram(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "ram"


# ============================================================
# 1. Real bestätigte Fehltreffer -- müssen jetzt blockiert werden.
# ============================================================

def test_laptops_plural_matcht_nicht():
    assert _matches_ram("Samsung 8GB DDR4 RAM Riegel für Laptops", 20.0) is False


def test_so_dimm_bindestrich_leerzeichen_variante_matcht_nicht():
    assert _matches_ram(
        "SK hynix16GB(2x8GB) DDR4 SO- DIMM 1Rx8 PC4-3200AA-SA2-11", 45.0
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel bleiben erhalten.
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Corsair Vengeance LPX DDR4 3000 MHz RAM 16GB", 40.0),
        ("Samsung 8GB DDR4-2400 RAM – PC4-2400T – Desktop Arbeitsspeicher", 10.0),
        ("Corsair Vengeance LPX 32GB DDR4 3200MHz RAM", 95.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "ram", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
