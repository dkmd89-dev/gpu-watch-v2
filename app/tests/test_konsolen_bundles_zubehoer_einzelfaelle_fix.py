"""Regressionstests für drei gezielte Zubehör-/Ersatzteil-Excludes in
konsolen_bundles.yaml (Nutzer-Freigabe 2026-08-15, FALSE_POSITIVES_ANALYSE
Teil 1 D).

Drei Einzelfälle, real bestätigt gegen found.json/price_history.jsonl:
- SD-Karten-Zubehör ("microsdxc"), matchte bisher über "512gb".
- PS4-Ersatzfestplatte ("interne festplatte"), matchte über "500gb"/"1tb".
- Switch-Tragetasche ("travelcase"/"tragetasche"), matchte über "system";
  das bereits vorhandene bare "tasche" greift wegen Wortgrenzen-Matching
  nicht beim Kompositum "Tragetasche".

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


def _matches_kb(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "konsolen_bundles"


def test_sd_karte_zubehoer_matcht_nicht():
    assert _matches_kb(
        "SanDisk microSDXC Extreme 512GB U3 Nintendo Switch 100MB/s Neu OVP", 78.90
    ) is False


def test_ps4_ersatzfestplatte_matcht_nicht():
    assert _matches_kb(
        "Toshiba MQ01ABD050V 2,5 Zoll, 500GB SATA III Interne Festplatte (Original PS4)",
        39.99,
    ) is False
    assert _matches_kb(
        "Toshiba MQ04ABF100 2,5 Zoll, 1TB SATA III Interne Festplatte (Original PS4 Pro)",
        45.0,
    ) is False


def test_switch_travelcase_matcht_nicht():
    assert _matches_kb("Nintendo Switch Deluxe System/Travelcase/Tragetasche", 10.00) is False


def test_reale_true_positives_bleiben_unveraendert():
    r = evaluate("Nintendo Switch 32GB Konsole mit Dock, Joy-Cons Neon Rot/Blau & OVP", 130.0, _rules_cfg())
    assert r.matched is True and r.category == "konsolen_bundles"
    r2 = evaluate("Xbox One S 500 GB Konsole mit Controller in OVP", 60.0, _rules_cfg())
    assert r2.matched is True and r2.category == "konsolen_bundles"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
