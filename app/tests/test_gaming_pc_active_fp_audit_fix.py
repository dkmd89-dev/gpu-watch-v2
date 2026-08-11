"""Regressionstest für den gaming_pc-Fix aus dem Active-False-Positive-
Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: `gaming_pc.yaml` hatte bisher bewusst KEIN
exclude_category ("Diese Kategorie WILL komplette PC-Systeme" --
identische Begründung wie ursprünglich bei office_pc.yaml, dort real
widerlegt, siehe PR #12). Real bestätigt gegen found.json (6 Titel im
vollständigen 18-Titel-Match-Korpus):

1. Gaming-LAPTOPS ("Gaming Notebook Ryzen 7 4800H...", "Lenovo Legion
   5...Gaming Laptop...", "MSI GF63 Thin Gaming Laptop...", "HP OMEN
   15-dc1003ng Gaming Notebook...") -- ein funktionsfähiges Notebook
   ist kein Desktop-Gaming-PC-System.
2. "Lenovo IdeaPad Gaming 3 15IMH05..." -- Lenovo-Laptop-Produktlinie
   ohne "laptop"/"notebook" im Titel.
3. "Bundle Mainboard B760 + CPU i5-13400F + Lüfter + RAM 16GB (extra
   RTX 3060 Ti)" -- bares Komponenten-Bundle ohne Gehäuse, identisches
   Muster wie office_pc.yaml/notebook_resell.yaml (matcher.py::
   _case_meets_requirement() wertet "kein erkennbares Gehäuse" als
   erfüllt).

Fix: 4 neue bare exclude_category-Terme (laptop, notebook, ideapad,
mainboard).

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


def _matches_gaming_pc(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "gaming_pc"


# ============================================================
# 1. Real bestätigte Fehltreffer -- müssen jetzt blockiert werden.
# ============================================================

def test_gaming_laptops_matchen_nicht():
    for title, price in [
        (
            "Lenovo Legion 5 17IMH05 Gaming Laptop i5 10300H 16GB RAM 512GB SSD GTX 1650 Ti",
            379.0,
        ),
        (
            "MSI GF63 Thin Gaming Laptop | i5-10500H |16GB RAM | 512GB SSD| GTX 1650 |Aku NEU",
            349.0,
        ),
        (
            "Gaming Notebook Ryzen 7 4800H 16GB RAM 512GB SSD 1TB FP GTX1650Ti",
            350.0,
        ),
        (
            "HP OMEN 15-dc1003ng Gaming Notebook – i7-8750H, RTX 2060 Q-Max, 16GB RAM, 1TB",
            375.0,
        ),
        (
            "Lenovo IdeaPad Gaming 3 15IMH05 | i5-10300H | GTX 1650 | 8GB RAM | 512GB SSD",
            339.0,
        ),
    ]:
        assert _matches_gaming_pc(title, price) is False, title


def test_bares_mainboard_bundle_matcht_nicht():
    assert _matches_gaming_pc(
        "Bundle Mainboard B760 + CPU i5-13400F + Lüfter + RAM 16GB (extra RTX 3060 Ti)",
        315.0,
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Desktop-Gaming-PCs
#    bleiben unverändert erhalten.
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("HP Pavilion Gaming PC i7-8700 GTX 1060 16GB RAM SSD/HDD", 380.0),
        ("Gaming-PC - Ryzen 7 2700X - RTX 2060 - 32GB DDR4", 450.0),
        (
            "GAMING FUJITSU ESPRIMO P758 KOMPLETT PC i5 9400 16GB RAM 512GB SSD RTX 2060 W11",
            321.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "gaming_pc", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
