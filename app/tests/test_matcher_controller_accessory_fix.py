"""Regressionstests für den Controller-Zubehör-Fix (Phase 15, kontrollierter
Review nach dem False-Positive-Regression-Suite-Fund).

Hintergrund: controller.yaml führte in exclude_category nur das
eigenständige Wort "kabel". Wortgrenzen-Matching
(matcher.py::_contains_term(), Pattern "(?<!\\w)term(?!\\w)") erkennt
"kabel" NICHT als Teil des zusammengesetzten Worts "Ladekabel" -- ebenso
fehlten "netzteil"/"ladegerät"/"anleitung" komplett. Zubehör-Angebote wie
"PS5 Controller Ladekabel USB-C" matchten dadurch als vollständiger
Controller (verifiziert: 5 EUR -> Top-Deal, Score 81, ★★★★☆).

Fix: "ladekabel"/"netzteil"/"ladegerät"/"anleitung" zu exclude_category
ergänzt (siehe rules/controller.yaml) -- analog zum bereits bestehenden
Muster in handhelds.yaml/konsolen_bundles.yaml (Phase 14).

Bekannte, bewusst in Kauf genommene Einschränkung (identisch zum
Phase-14-Präzedenzfall): ein echter Controller, dessen Titel das
mitgelieferte Zubehör nennt (z.B. "PS5 Controller inkl. Ladekabel"),
matcht dadurch ebenfalls nicht mehr -- eine kategorieweite Exclude-Liste
kann nicht zwischen "nur Zubehör" und "Gerät inkl. Zubehör" unterscheiden.

Läuft gegen die echten, produktiven rules/*.yaml, analog zu
test_matcher_handheld_false_positives.py."""
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


def test_ps5_dualsense_controller_matcht():
    r = evaluate("PS5 DualSense Controller weiß neuwertig", 20.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"


def test_xbox_controller_matcht():
    r = evaluate("Xbox Series Wireless Controller schwarz", 18.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"


def test_ps5_ladekabel_matcht_nicht_mehr():
    # Regressionsschutz: 5 EUR, matchte vorher fälschlich als
    # controller_ps5_dualsense / Top-Deal / Score 81.
    r = evaluate("PS5 Controller Ladekabel USB-C 3m", 5.0, _rules_cfg())
    assert r.matched is False


def test_ps5_ladegeraet_matcht_nicht_mehr():
    r = evaluate("PS5 DualSense Controller Ladegerät 2m", 6.0, _rules_cfg())
    assert r.matched is False


def test_ps5_netzteil_matcht_nicht_mehr():
    r = evaluate("PS5 Controller Netzteil original", 5.0, _rules_cfg())
    assert r.matched is False


def test_ps5_anleitung_matcht_nicht_mehr():
    r = evaluate("PS5 Controller Anleitung", 2.0, _rules_cfg())
    assert r.matched is False


def test_xbox_ladekabel_matcht_nicht_mehr():
    r = evaluate("Xbox Series Controller Ladekabel", 5.0, _rules_cfg())
    assert r.matched is False


def test_bare_kabel_weiterhin_ausgeschlossen():
    # Bestehendes Verhalten (bare "kabel") bleibt unverändert.
    r = evaluate("PS5 Controller Kabel USB-C 3m", 5.0, _rules_cfg())
    assert r.matched is False


def test_ps5_dualsense_drift_regel_bleibt_unveraendert():
    # Sicherheitsprüfung: die Bastler-/Reparatur-Regeln (require_all_of
    # verlangt "defekt"/"drift" etc.) dürfen vom Exclude-Zusatz nicht
    # betroffen sein -- exclude_category gilt zusätzlich zu, nicht statt
    # der Regel-eigenen Logik.
    r = evaluate("PS5 DualSense Controller Stick Drift defekt", 10.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "controller_ps5_drift"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
