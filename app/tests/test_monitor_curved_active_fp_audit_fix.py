"""Regressionstests für den monitor_curved-Fix aus dem Active-False-
Positive-Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Zwei unabhängige, real bestätigte Muster im vollständigen 133-Titel-
Match-Korpus:

1. Konsolen-Bundle mit Kurzform statt ausgeschriebenem "playstation":
   "Ps4slim + curved Samsung Monitor+controller+Wandhalterung" -- der
   Monitor ist hier nur Bundle-Beilage zu einer PS4-Konsole, identisches
   Muster zum bereits bestehenden "Konsolen"-Ausschlussgrund
   (playstation/xbox/nintendo/switch), aber "playstation" allein deckt
   die verbreitete Kurzform "ps4"/"ps4slim" nicht ab. "ps4slim" als
   eigener Begriff nötig (zusammengeschriebenes Wort, kein bare "ps4"
   -Match). "ps1"-"ps5" zusätzlich ergänzt, analog zum bereits in
   gpu.yaml etablierten Muster für denselben Ausschlussgrund.

2. Fitnessgerät mit eigenem "curved"-Trainingscomputer-Display, kein
   PC-Monitor: "Klappbarer Heimtrainer F-Bike CURVED LCD-Display
   Fahrrad Top" (79€).

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


def _matches_monitor_curved(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "monitor_curved"


# ============================================================
# 1. Real bestätigte Fehltreffer -- müssen jetzt blockiert werden.
# ============================================================

def test_ps4_konsolen_bundle_matcht_nicht():
    assert _matches_monitor_curved(
        "Ps4slim + curved Samsung Monitor+controller+Wandhalterung", 110.0
    ) is False


def test_weitere_ps_kurzform_varianten_matchen_nicht():
    # Unbelegte, aber strukturell identische Kurzform-Geschwisterfälle
    # (analog zum bereits etablierten Muster in gpu.yaml).
    for title, price in [
        ("PS5 curved Monitor Bundle mit Controller", 100.0),
        ("PS3 curved Display Konsolen-Set", 60.0),
    ]:
        assert _matches_monitor_curved(title, price) is False, title


def test_heimtrainer_curved_display_matcht_nicht():
    assert _matches_monitor_curved(
        "Klappbarer Heimtrainer F‑Bike CURVED LCD-Display Fahrrad Top", 79.0
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel bleiben erhalten.
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Samsung CF396 Curved Monitor 24 Zoll", 95.0),
        ("AOC C27G42ZE 27\" Curved Gaming Monitor – 260Hz – 1ms – Full HD", 80.0),
        ("Monitor MSI Optix MAG341cq, 34 Zoll, UWQHD, Curved", 100.0),
        ("Acer Nitro ED270R 27 Zoll Curved Monitor FHD 180Hz HDMI/DP", 110.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "monitor_curved", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
