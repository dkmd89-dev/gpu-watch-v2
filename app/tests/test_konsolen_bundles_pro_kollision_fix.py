"""Regressionstest für die "pro"-Kollision in konsolen_bundles.yaml
(Nutzer-Meldung 2026-08-15, Live-Fehltreffer-Report, Folgeschritt zu
test_konsolen_bundles_zubehoer_set_mainboard_fix.py).

Drei unabhängige Root Causes für dieselbe Symptomatik (bare "pro" in der
require_all_of-Gruppe 2 der PS4-Regeln matcht Produktnamen statt der
PS4-Pro-Konsole selbst):

1. "pro-controller" (Bindestrich) -- der bestehende
   exclude_category_unless_preceded_by-Eintrag "pro controller" (Leerzeichen)
   greift nicht bei Bindestrich-Schreibweise (identisches Kompositum-
   Problem wie "zubehör-set"/"zubehörset"/"zubehör set"). Fix: "pro-
   controller" als Geschwister-Eintrag mit demselben Konnektor-Anker
   ergänzt.
2. "mixamp" -- Astro MixAmp ist ein Audio-Verstärker-Produktname, kein
   Konsolen-Bundle. Bare Exclude, kein Bundle-Kollisionsrisiko.
3. "vertical stand" -- Konsolenständer-Produktname, matcht fälschlich über
   mehrere Plattform-/Modell-Kompatibilitätsangaben ("für PS4 / PS4 Slim /
   PS4 Pro"). Fix über exclude_category_unless_also_contains (titelweite
   Präsenzprüfung auf Bundle-Konnektoren) statt _unless_preceded_by, da der
   einzige echte Bundle-Kollisionsfall ("PS4 Slim inkl 1 Controller
   Vertical Stand und Lampe") den Konnektor "inkl" NICHT unmittelbar vor
   "Vertical Stand" stehen hat.

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


def test_pro_controller_bindestrich_matcht_nicht():
    r = evaluate(
        "Snakebyte PS4 Wireless Pro-Controller PC Bayern München", 52.0, _rules_cfg()
    )
    assert not (r.matched and r.category == "konsolen_bundles")


def test_mixamp_matcht_nicht():
    r = evaluate(
        "Astro MixAmp Pro TR Gen 4 für PS4/PC – Audio-Verstärker", 50.0, _rules_cfg()
    )
    assert not (r.matched and r.category == "konsolen_bundles")


def test_vertical_stand_ohne_bundle_kontext_matcht_nicht():
    r = evaluate(
        "Chin Fai The Shark Vertical Stand für PS4 / PS4 Slim / PS4 Pro",
        15.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "konsolen_bundles")


def test_vertical_stand_im_echten_bundle_matcht_weiterhin():
    # Kollisionsschutz: der Konnektor "inkl" steht hier NICHT unmittelbar
    # vor "Vertical Stand" (dazwischen "1 Controller") -- ein reiner
    # Adjazenz-Check hätte diesen echten Bundle-Treffer zerstört.
    r = evaluate(
        "PS4 Slim inkl 1 Controller Vertical Stand und Lampe", 80.0, _rules_cfg()
    )
    assert r.matched is True and r.category == "konsolen_bundles"


def test_pro_controller_leerzeichen_bleibt_unveraendert():
    # Bestehendes Verhalten (Leerzeichen-Variante) darf nicht regressieren.
    r = evaluate("Nintendo Switch Pro Controller OVP", 25.0, _rules_cfg())
    assert not (r.matched and r.category == "konsolen_bundles")


def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Nintendo Switch Konsole mit Pro Controller & 5 Spielen", 130.0),
        ("Nintendo Switch 1 Konsole + Pro Controller", 150.0),
        ("PS4 pro zum verkaufen", 12.0),
        ("playstation 4 pro", 90.0),
        ("PS4 slim 500gb", 40.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
