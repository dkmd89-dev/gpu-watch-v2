"""Regressionstest für die handhelds-exclude_category-Erweiterung um die
Pluralform "sd karten" (Ruleset-Qualitätssystem, 251-Listing-Stichprobe
2026-08-14).

Hintergrund: der bestehende Exclude "sd karte" (Singular) wird von
matcher.py::_contains_term() als ganzes Wort geprüft und erfasst daher
NICHT die Pluralform "Karten" in Titeln wie "Modded SD Karten für 3ds/3ds
xl/" -- reines Speicherkarten-Zubehör, keine Konsole. Blast Radius
gemessen: 2 aktuelle found.json- + 3 historische price_history.jsonl-
Treffer, alle eindeutig reine SD-Karten-/Adapter-Angebote.

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


def test_sd_karten_plural_matcht_nicht():
    for title, price in [
        ("Modded SD Karten für 3ds/3ds xl/", 30.0),
        ("Gemoddete SD Karten Nintendo 3ds/ 3 ds xl", 25.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "handhelds"), title


def test_sd_karte_singular_matcht_weiterhin_nicht():
    # Bestehendes Verhalten (Singular-Exclude) darf nicht regressieren.
    r = evaluate("SD Karte für Nintendo 3DS XL 32GB", 15.0, _rules_cfg())
    assert not (r.matched and r.category == "handhelds")


def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Nintendo 3DS XL mit Spielen !ABHOLUNG!", 90.0),
        ("ASUS ROG Ally Z1 Extreme 16GB / 512GB neuwertig", 300.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "handhelds", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
