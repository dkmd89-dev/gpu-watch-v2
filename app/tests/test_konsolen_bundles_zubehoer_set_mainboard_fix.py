"""Regressionstest für zwei konsolen_bundles-exclude_category-Erweiterungen
(Nutzer-Meldung 2026-08-15, Live-Fehltreffer-Report):

1. "zubehör set" (mit Leerzeichen) -- nur "zubehör-set" (Bindestrich) und
   "zubehörset" (zusammengeschrieben) waren bereits gelistet, die getrennte
   Schreibweise ("12-in-1 Sport Zubehör Set für Nintendo Switch / OLED")
   griff bisher nicht durch.
2. "mainboard"/"motherboard" (bare) -- identisches, bereits in
   office_pc.yaml/gaming_pc.yaml/notebook_resell.yaml etabliertes Muster
   ("ein blosses Mainboard-Ersatzteil ist kein komplettes System"). Real
   bestätigt: "Sony Playstation 4 Pro & PS4 Mainboard Pin Buchse / Stecker
   abgerissen Reparatur" (39€, Top-Deal) -- ein defektes Ersatzteil.

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


def test_zubehoer_set_mit_leerzeichen_matcht_nicht():
    for title, price in [
        ("12-in-1 Sport Zubehör Set für Nintendo Switch / OLED - NEU OVP", 27.0),
        ("Nintendo Switch Sports Zubehör Set für Familienspaß", 20.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "konsolen_bundles"), title


def test_zubehoer_set_bestehende_schreibweisen_matchen_weiterhin_nicht():
    # Bestehendes Verhalten (Bindestrich/Zusammenschreibung) darf nicht
    # regressieren.
    for title, price in [
        ("Nintendo Switch Zubehör-Set OVP NEU", 20.0),
        ("Nintendo Switch Zubehörset OVP NEU", 20.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "konsolen_bundles"), title


def test_mainboard_ersatzteil_matcht_nicht():
    r = evaluate(
        "Sony Playstation 4 Pro & PS4 Mainboard Pin Buchse / Stecker abgerissen Reparatur",
        39.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "konsolen_bundles")


def test_motherboard_ersatzteil_matcht_nicht():
    r = evaluate("PS4 Pro Motherboard defekt Ersatzteil", 25.0, _rules_cfg())
    assert not (r.matched and r.category == "konsolen_bundles")


def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Sony PlayStation 4 Slim 500GB Konsole + Stromkabel| Top Zustand", 85.0),
        ("Nintendo Switch OLED Konsole mit Joycons", 150.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
