"""Regressionstest für den iphone-Fix aus der Category-False-Positive-
Forensics-Fix-Queue (tools/ruleset_quality/generated/false_positive_fix_queue.json,
P0, root_cause: replacement_part_false_positive).

Hintergrund: ein bloßes iPhone-Mainboard/-Ersatzteil wurde bisher als
komplettes Gerät gematcht. Identisches, bereits in gaming_pc.yaml/
office_pc.yaml/notebook_resell.yaml/handhelds.yaml/konsolen_bundles.yaml
etabliertes Muster (bare "mainboard"/"motherboard"-Exclude). Real
bestätigter Fehltreffer (docs/DASHBOARD_MATCH_FORENSICS.json): "Apple
iPhone 15 Pro Max 512GB Mainboard Platine mit FaceID und Kameramodul"
(400€), matchte bisher als "iPhone 15 Pro Max (≥512GB) 👍 Guter Preis".

Fix: 2 neue bare-Wort exclude_category-Ergänzungen ("mainboard",
"motherboard").

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


def _matches_iphone(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "iphone"


# ============================================================
# 1. Real bestätigter Fehltreffer -- muss jetzt blockiert werden.
# ============================================================

def test_iphone_15_pro_max_mainboard_platine_matcht_nicht():
    assert _matches_iphone(
        "Apple iPhone 15 Pro Max 512GB Mainboard Platine mit FaceID und Kameramodul",
        400.0,
    ) is False


def test_iphone_12_mini_hauptplatine_mainboard_matcht_nicht():
    # Zusaetzlicher, im aktuellen Korpus beobachteter Fall desselben
    # Musters (nicht Teil der 19 formal gelabelten historischen FP,
    # aber identischer Root Cause -- Nebeneffekt desselben Fixes).
    assert _matches_iphone(
        "Apple iPhone 12 mini 128GB Hauptplatine Mainboard Face ID Sensor",
        100.0,
    ) is False


def test_iphone_11_mainboard_ohne_sperre_matcht_nicht():
    assert _matches_iphone(
        "Mainboard für iPhone 11 ohne Sperre 64GB",
        39.99,
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel bleiben erhalten.
# ============================================================

def test_reale_true_positives_ohne_mainboard_matchen_weiterhin():
    for title, price in [
        ("iPhone 12 Blau 64gb mit OVP und Ladekabel", 135.0),
        ("iPhone 11 - 64GB - Grün - Inkl. Hülle, Displayschutz & OVP", 120.0),
        ("Apple iPhone 12 mini 128 GB Schwarz in OVP", 110.0),
        ("iPhone 16 Pro 128 GB Titan Weiß | Top Zustand | OVP + Rechnung", 650.0),
        ("Apple iPhone 15 Pro Max 512GB Titan Schwarz", 600.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "iphone", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
