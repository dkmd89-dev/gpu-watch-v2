"""Regressionstest für zwei konsolen_bundles-Fixes aus dem UNCLEAR-FP-
Root-Cause-Audit (2026-08-16, Cluster C5/C7):

1. C5 THIRD_PARTY_ACCESSORY_BRAND_NAME_MARKER_COLLISION -- "HORI Split Pad
   Pro" ist ein Dritthersteller-Controller-Produktname. Der bereits
   vorhandene "pro controller"-Phrasen-Exclude greift nicht, weil "Pro" und
   "Controller" im Titel durch "Nintendo Switch" getrennt stehen; der Titel
   rutscht stattdessen über das generische Wort "pro" in der
   exclude_category_unless_also_contains-Verstärkungsliste des Keys "ovp"
   durch. Fix: "split pad pro" als neuer Eintrag in
   exclude_category_unless_preceded_by, identischer *bundle_konnektoren-
   Anker wie "pro controller"/"gamecube controller".

2. C7 JOYCON_SET_OLED_MARKER_COLLISION -- "Nintendo Switch OLED Joy-Con
   Set" matcht fälschlich, weil der "joy-con"-Kontext-Guard "oled" als
   Geräte-Verstärkungssignal akzeptiert, obwohl "OLED" hier nur die
   Joy-Con-Kompatibilitätsvariante beschreibt. Fix: "joy-con set" als neue
   bare exclude_category-Phrase, analog zu "zubehör set".

Vollkorpus-Regression (docs/DASHBOARD_MATCH_FORENSICS.json, 2306 Einträge)
bestätigt: genau 2 Routing-Änderungen (beide Zielfälle), 0 Abweichungen bei
allen 2252 TRUE_POSITIVE- und 19 FALSE_POSITIVE-Fällen sowie den übrigen 33
UNCLEAR-Fällen.

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


# ---------------------------------------------------------------
# C5 -- Split Pad Pro
# ---------------------------------------------------------------

def test_c5_split_pad_pro_standalone_matcht_nicht():
    r = evaluate(
        "HORI Split Pad Pro Nintendo Switch Controller Schwarz mit OVP",
        30.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "konsolen_bundles")


def test_c5_split_pad_pro_im_echten_bundle_matcht_weiterhin():
    # Konnektor "mit" steht unmittelbar vor "Split Pad Pro" -- geschützt
    # über denselben *bundle_konnektoren-Mechanismus wie "pro controller".
    r = evaluate("Nintendo Switch Konsole mit Split Pad Pro", 130.0, _rules_cfg())
    assert r.matched is True and r.category == "konsolen_bundles"


def test_c5_reale_switch_konsole_matcht_weiterhin():
    for title, price in [
        ("Nintendo Switch OLED Konsole Weiss OVP", 100.0),
        ("Nintendo Switch Konsole OVP", 100.0),
        ("Nintendo Switch Konsole mit Pro Controller & 5 Spielen", 130.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


def test_c5_split_pad_pro_controller_yaml_bleibt_unveraendert():
    # Kontrollfall: der TRUE_POSITIVE-Schwesterfall mit direkter
    # "Pro Controller"-Adjazenz matcht weiterhin ueber controller.yaml, nicht
    # konsolen_bundles -- von dieser Aenderung nicht betroffen.
    r = evaluate(
        "HORI Split Pad Pro Controller Schwarz für Nintendo Switch", 30.0, _rules_cfg()
    )
    assert r.matched is True and r.category == "controller"


# ---------------------------------------------------------------
# C7 -- Joy-Con Set
# ---------------------------------------------------------------

def test_c7_joycon_set_mit_spieltitel_matcht_nicht():
    r = evaluate(
        "Nintendo Switch OLED Joy-Con Set - Pokemon Scarlet & Violet mit Handschlaufaufen",
        45.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "konsolen_bundles")


def test_c7_reale_switch_oled_konsole_matcht_weiterhin():
    r = evaluate("Nintendo Switch OLED Konsole Weiss OVP", 100.0, _rules_cfg())
    assert r.matched is True and r.category == "konsolen_bundles"


def test_c7_reale_konsole_mit_joycons_matcht_weiterhin():
    # Der explizit dokumentierte Kollisionsschutz-Fall (siehe
    # "Bewusst NICHT joy-con" in konsolen_bundles.yaml) darf durch die neue
    # "joy-con set"-Phrase nicht beeintraechtigt werden.
    for title, price in [
        ("Nintendo Switch Konsole mit grauen Joy-Cons", 100.0),
        ("Nintendo Switch OLED Konsole mit grauen Joy-Cons", 100.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


def test_c7_standalone_joycon_set_bleibt_unveraendert_blockiert():
    # Bestehendes Verhalten (bereits ueber den Kontext-Guard geloest) darf
    # nicht regressieren.
    r = evaluate("SW - Original Nintendo Switch Joy-Con 2er-Set Grau", 40.0, _rules_cfg())
    assert not (r.matched and r.category == "konsolen_bundles")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
