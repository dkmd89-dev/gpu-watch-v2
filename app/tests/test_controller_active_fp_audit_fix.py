"""Regressionstest für den controller-Fix aus dem Active-False-
Positive-Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Fünf unabhängige, real bestätigte Muster im vollständigen 56-Titel-
Match-Korpus:

1. Controller-Halter/-Ständer und Wandhalterung (Kompositum, von bare
   "halterung" wegen fehlender Wortgrenze nicht erfasst) -- Zubehör,
   kein Controller.
2. Ersatz-Akku für einen Controller.
3. Wireless-Empfänger/-Dongle für PC ("...Adapter Empfänger Stick...").
4. Ersatzteil-Angebote ("2x Ersatz Analog Sticks..."). Bewusst NICHT
   bare "sticks" -- würde den echten TRUE_POSITIVE-Titel "TMR Sticks!
   Nintendo Switch 1 Pro Controller..." treffen.
5. Konsolen-Bundle über Speicherkapazitätsangabe ("XBOX Series S 1TB +
   2 Controller...") -- bereits im bestehenden Regel-Kommentar als
   Restrisiko dokumentiert, jetzt real bestätigt.

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


def _matches_controller(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "controller"


# ============================================================
# 1. Real bestätigte Fehltreffer -- müssen jetzt blockiert werden.
# ============================================================

def test_zubehoer_und_ersatzteil_angebote_matchen_nicht():
    for title, price in [
        ('PS5/Xbox x Controller Halter "Fight" Faust Design', 35.0),
        (
            "PS5 Wandhalterung für PS5 Controller mit Controller-Halter Kopfhörer-Aufhänger",
            23.99,
        ),
        (
            "Controller Akku für Xbox One/Xbox Series X&S,2*3600mWh Akku für Xbox One X&S",
            17.99,
        ),
        (
            "Für Wireless Xbox One Controller Adapter Empfänger Stick Windows 10 11 PC USB DE",
            18.98,
        ),
        (
            "2x Ersatz Analog Sticks für PS5 Controller DualSense - Schwarz - BLITZVERSAND",
            2.95,
        ),
    ]:
        assert _matches_controller(title, price) is False, title


def test_konsolen_bundle_ueber_speicherkapazitaet_matcht_nicht():
    assert _matches_controller(
        "XBOX Series S 1TB + 2 Controller[BITTE BESCHREIBUNG LESEN]", 1.0
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel bleiben erhalten,
#    inkl. des Grenzfalls mit "Sticks" als Verkaufsargument (kein
#    Ersatzteil-Angebot).
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Nintendo Switch Pro Controller - Schwarz", 27.0),
        ("Ps5 Controller", 35.0),
        ("Microsoft Xbox Series X Wireless Controller Black [2020]", 23.0),
        (
            "TMR Sticks! Nintendo Switch 1 Pro Controller Schwarz + OVP + Ladekabel",
            29.99,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "controller", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
