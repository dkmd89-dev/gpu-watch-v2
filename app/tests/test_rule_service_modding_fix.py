"""Regressionstests für den Service-/Modding-Fix (Phase 15, kontrollierter
Folge-Review nach dem "Nintendo 3DS Gehäuse/Modding Service"-Dashboard-Fund).

Hintergrund: Reparatur-/Modding-DIENSTLEISTUNGSANGEBOTE ("ich repariere/
mode Geräte für dich" -- es wechselt kein Gerät den Besitzer) matchten
bisher fälschlich als Geräteverkauf, weil keine Kategorie einen Ausschluss
für "Service"-Angebote hatte (z.B. "Modding Service für alle Nintendo
Modelle / New 3DS / 2DS XL" matchte als handhelds-Top-Deal).

Fix: die Mehrwort-Phrasen "modding service" / "reparatur service" /
"repair service" wurden exclude_category von handhelds, controller,
konsolen_bundles, retro_konsolen, iphone und macbook ergänzt.

Bewusst NICHT umgesetzt (siehe kontrollierter Review, separat
zurückgestellt): ein bare exclude_category auf "gehäuse" -- das würde auch
legitime Zustandsbeschreibungen kompletter Geräte blockieren ("Gehäuse
leicht vergilbt/verkratzt/neuwertig" ist eine sehr verbreitete Formulierung
für den Zustand des VERKAUFTEN Geräts selbst, nicht nur für Standalone-
Ersatzteil-Angebote). Bewusst als Mehrwort-Phrase statt bare "service": ein
bare Exclude wäre riskant, u.a. weil controller.yaml Reparatur-KANDIDATEN
(defekte/Drift-Controller zum Verkauf) über eigene require_all_of-Regeln
bewusst zulässt -- diese Titel enthalten "defekt"/"drift", aber nicht das
Wort "Service".

Läuft gegen die echten, produktiven rules/*.yaml, analog zu
test_matcher_controller_accessory_fix.py."""
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


# ============================================================
# 1. Service-/Modding-Angebote dürfen NICHT mehr matchen
# ============================================================

def test_handhelds_modding_service_matcht_nicht():
    # Ursprünglicher Dashboard-Fund.
    r = evaluate(
        "Modding Service für alle Nintendo Modelle / New 3DS / 2DS XL",
        25.0, _rules_cfg(),
    )
    assert r.matched is False


def test_controller_reparatur_service_matcht_nicht():
    r = evaluate(
        "Xbox Series Controller Stick Drift Reparatur Service", 15.0, _rules_cfg()
    )
    assert r.matched is False


def test_konsolen_bundles_modding_service_matcht_nicht():
    r = evaluate("PS4 Jailbreak Modding Service Chip", 30.0, _rules_cfg())
    assert r.matched is False


def test_konsolen_bundles_switch_modding_service_matcht_nicht():
    r = evaluate("Nintendo Switch OLED Modding Service Chip", 50.0, _rules_cfg())
    assert r.matched is False


def test_retro_konsolen_modding_service_matcht_nicht():
    r = evaluate("N64 Konsole Modding Service Composite Mod", 40.0, _rules_cfg())
    assert r.matched is False


def test_iphone_reparatur_service_matcht_nicht():
    r = evaluate("iPhone Display Reparatur Service alle Modelle", 25.0, _rules_cfg())
    assert r.matched is False


def test_macbook_reparatur_service_matcht_nicht():
    r = evaluate("MacBook Reparatur Service Display Tausch", 50.0, _rules_cfg())
    assert r.matched is False


def test_repair_service_englisch_matcht_nicht():
    r = evaluate("iPhone 11 Screen Repair Service alle Modelle", 25.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# 2. Echte Geräteangebote MIT Zustandsbeschreibung ("Gehäuse ...") müssen
#    weiterhin matchen -- das ist die zentrale Regressionsabsicherung
#    gegen einen zu breiten Fix (siehe Modul-Docstring).
# ============================================================

def test_handhelds_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "Nintendo 3DS XL Konsole neuwertig, Gehäuse leicht vergilbt",
        40.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "handhelds"


def test_controller_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "PS5 DualSense Controller weiß neuwertig, Gehäuse minimal verkratzt",
        20.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "controller"


def test_konsolen_bundles_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "Nintendo Switch OLED Konsole, Gehäuse leicht zerkratzt sonst top",
        130.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_retro_konsolen_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "N64 Konsole Gehäuse leicht vergilbt sonst neuwertig", 30.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "retro_konsolen"


def test_iphone_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "iPhone 11 64GB space grau, Gehäuse minimal verkratzt Akku 89%",
        65.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "iphone"


def test_macbook_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "MacBook Air Intel i5 256GB, Gehäuse leicht verkratzt", 130.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "macbook"


def test_controller_drift_reparatur_kandidat_matcht_weiterhin():
    # Reparatur-KANDIDAT (defekter Controller zum Verkauf) bleibt vom
    # Service-Fix unberührt -- kein Widerspruch zu ignore_global_excludes.
    r = evaluate("PS5 DualSense Controller Stick Drift defekt", 10.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "controller_ps5_drift"


def test_xbox_controller_ohne_service_matcht_weiterhin():
    r = evaluate("Xbox Series Wireless Controller schwarz", 18.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
