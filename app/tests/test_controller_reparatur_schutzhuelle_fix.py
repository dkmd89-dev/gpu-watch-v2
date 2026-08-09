"""Regressionstests für den controller-"Reparatur"/"Schutzhülle"-Fix
(kontrollierter Review nach found.json-Audit, Priorität NIEDRIG,
Restlücken der bereits gemergten Phase-15-Fixes).

Hintergrund: zwei kleine, konkret in found.json gefundene Restlücken
der bereits gemergten Service/Modding- und Gehäuse/Shell-Fixes:
1. "controller reparatur" (umgekehrte Wortstellung zu "reparatur
   service") -- Reparatur-Dienstleistungsangebote wie "PS5 Controller
   Reparatur Stick Drift TMR/Hall Sticks" matchten weiterhin.
2. "schutzhülle" (Kompositum von "hülle") -- "Gummi Schutzhülle für PS5
   dualsense controller" matchte weiterhin (Wortgrenzen-Lücke).

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


def test_controller_reparatur_stick_drift_matcht_nicht():
    assert _matches_controller(
        "PS5 Controller Reparatur Stick Drift TMR/Hall Sticks", 13.0
    ) is False


def test_controller_reparatur_scuf_matcht_nicht():
    assert _matches_controller(
        "PS5 / Xbox / Scuf Controller Reparatur – Stickdrift, TMR/Hall", 15.0
    ) is False


def test_schutzhuelle_kompositum_matcht_nicht():
    assert _matches_controller(
        "Gummi Schutzhülle für PS5 dualsense controller", 5.0
    ) is False


def test_bare_huelle_bleibt_unveraendert_ausgeschlossen():
    # Bestehendes Verhalten (bare "hülle") bleibt unveraendert.
    r = evaluate("PS5 DualSense Controller Hülle schwarz", 10.0, _rules_cfg())
    assert r.matched is False


def test_drift_reparatur_kandidat_matcht_weiterhin():
    # Sicherheitsprüfung: der eigentliche Reparatur-KANDIDAT (defekter
    # Controller zum Verkauf, kein Dienstleistungsangebot) bleibt vom
    # Fix unberührt -- kein Widerspruch zu ignore_global_excludes.
    r = evaluate("PS5 DualSense Controller Stick Drift defekt", 10.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "controller_ps5_drift"


def test_regulaerer_controller_matcht_weiterhin():
    r = evaluate("PS5 DualSense Controller weiß neuwertig", 20.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"


def test_controller_mit_ladekabel_bundle_matcht_weiterhin():
    r = evaluate("Original Nintendo Switch Pro Controller mit Ladekabel", 25.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
