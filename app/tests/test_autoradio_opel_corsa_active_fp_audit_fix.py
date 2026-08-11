"""Regressionstest für den autoradio_opel_corsa-Fix aus dem Active-
False-Positive-Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: OEM-Werksteile (Original-Steuergerät/CD-Player-Modul mit
Opel-Teilenummer) matchten fälschlich über das generische
"multimedia"-Signalwort in Gruppe 2, obwohl es sich nicht um ein
Android-Aftermarket-Designradio handelt. Real bestätigt gegen
found.json (2 Titel im vollständigen 55-Titel-Match-Korpus): "Opel
Corsa D Radio Multimedia Steuergerät MMI 13289918", "Opel Corsa D
Radio Multimedia CP Player 13357124" -- beide ohne jede Android-/
Carplay-/Navigationsradio-Erwähnung, mit Opel-Werksteilenummer im
Titel.

Fix: 2 neue bare/phrase exclude_category-Terme ("steuergerät", "cp
player").

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


def _matches_autoradio(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "autoradio_opel_corsa"


# ============================================================
# 1. Real bestätigte Fehltreffer -- müssen jetzt blockiert werden.
# ============================================================

def test_oem_werksteile_matchen_nicht():
    for title, price in [
        ("Opel Corsa D Radio Multimedia Steuergerät MMI 13289918", 40.0),
        ("Opel Corsa D Radio Multimedia CP Player 13357124", 80.50),
    ]:
        assert _matches_autoradio(title, price) is False, title


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel bleiben erhalten.
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        (
            "7\" Für Opel Corsa D 2007-2012 Autoradio Android 15 Apple Carplay GPS NAVI 64G FM",
            134.99,
        ),
        ("A-Sure Autoradio GPS AndroidAuto/CarPlay AstraH/Corsa D", 109.0),
        (
            "ESSGOO Android Autoradio für Opel Corsa D / Astra H / Zafira – GPS, Bluetooth, D",
            69.99,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "autoradio_opel_corsa", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
