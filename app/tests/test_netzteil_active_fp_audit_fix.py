"""Regressionstest für den netzteil-Fix aus dem Active-False-Positive-
Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: HiFi-Verstärker mit Watt-Angabe im Titel (z.B. "1000W
Verstärker Stereo Amplifier HIFI...") matchten bisher fälschlich als
PC-Netzteil -- der psu.py-Detector interpretiert jede Wattzahl im Titel
als PSU-Leistung, ohne zwischen "Netzteil-Watt" und
"Verstärker-Ausgangs-Watt" zu unterscheiden. Real bestätigt gegen
found.json (2 Titel im vollständigen 94-Titel-Match-Korpus).

Fix: 2 neue bare exclude_category-Terme ("verstärker", "amplifier").

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


def _matches_netzteil(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "netzteil"


# ============================================================
# 1. Real bestätigte Fehltreffer -- müssen jetzt blockiert werden.
# ============================================================

def test_hifi_verstaerker_matchen_nicht():
    for title, price in [
        (
            "1000W Verstärker Stereo Amplifier HIFI Digital Bluetooth FM USB Vollverstärker",
            26.57,
        ),
        (
            "600W Bluetooth Mini Verstärker HiFi Power Audio Stereo Bass Amplifier USB MP3 FM",
            25.99,
        ),
    ]:
        assert _matches_netzteil(title, price) is False, title


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Netzteile bleiben
#    unverändert erhalten (echte Preise aus found.json).
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Corsair RM750 (750 W, vollmodular)", 50.0),
        ("be quiet! Straight Power 11 750W modular", 50.0),
        ("LC-Power LC6650GP3 V2.3 Ozeanos 600W Netzteil", 15.0),
        ("Corsair AX860 860W PC-Netzteil 80 PLUS Platinum Vollmodular ATX", 49.99),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "netzteil", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
