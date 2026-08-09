"""Regressionstests für den RX-7600/RX-7600-XT-Fix (Phase 15, kontrollierter
Review nach dem Rule-Analyzer-/Rule-Coverage-Fund).

Hintergrund: Die Regel "RX 7600 XT" (Guter Preis, price_history_model
"rx_7600_xt") führte bisher "rx 7600" als eigenen match-Begriff, obwohl
"7600 xt"/"7600xt" die XT-Variante bereits eindeutig identifizieren. Da
diese Regel VOR den "RX 7600"-Regeln (8GB, price_history_model "rx_7600")
steht und first-match-wins gilt (matcher.py::evaluate()-Docstring), ihr
max_price (230) zudem beide "RX 7600"-Preisstufen (160/210) vollständig
abdeckte, gewann sie IMMER zuerst -- "rx_7600" war dadurch strukturell
100% unerreichbar. Bestätigt anhand echter price_history.jsonl-Daten
(8/8 Datenpunkte liefen unter rx_7600_xt, mind. 1 nachweislich eine
Nicht-XT-Karte: "MSI RX 7600 MECH 2X Classic 8G OC").

Fix: "rx 7600" aus der "RX 7600 XT"-Regel entfernt (siehe rules/gpu.yaml).

Läuft gegen die echten, produktiven rules/*.yaml, analog zu
test_matcher_price_calibration_matching_fixes.py."""
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


def test_rx_7600_matcht_als_normal():
    r = evaluate("RX 7600 Grafikkarte", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "rx_7600"


def test_rx_7600_xt_matcht_als_xt():
    r = evaluate("RX 7600 XT Grafikkarte", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "rx_7600_xt"


def test_rx_7600_oc_matcht_als_normal():
    r = evaluate("RX 7600 OC Grafikkarte", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "rx_7600"


def test_rx_7600_xt_oc_matcht_als_xt():
    r = evaluate("RX 7600 XT OC Grafikkarte", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "rx_7600_xt"


def test_echte_nicht_xt_karte_matcht_nicht_mehr_als_xt():
    # Regressionsschutz fuer den urspruenglichen Bug: dieser Titel (aus
    # price_history.jsonl, 180 EUR) matchte vorher faelschlich als
    # rx_7600_xt.
    r = evaluate("MSI Radeon RX 7600 Gaming X 8G", 180.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "rx_7600"


def test_echte_xt_karte_matcht_weiterhin_als_xt():
    r = evaluate("Gigabyte Radeon RX 7600 XT Gaming", 200.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "rx_7600_xt"


def test_rx_7600_xt_niemals_als_normale_rx_7600_klassifiziert():
    # Systematischer Preis-Sweep ueber beide Preisstufen hinweg.
    for price in [50, 100, 150, 180, 200, 230]:
        r = evaluate("Sapphire RX 7600 XT Pulse 16GB", float(price), _rules_cfg())
        if r.matched:
            assert r.price_history_model == "rx_7600_xt", (
                f"Bei {price} EUR faelschlich als {r.price_history_model} "
                "statt rx_7600_xt gematcht"
            )


def test_rx_7600_niemals_als_xt_klassifiziert():
    for price in [50, 100, 150, 180, 200, 210]:
        r = evaluate("MSI Radeon RX 7600 Gaming X 8G", float(price), _rules_cfg())
        if r.matched:
            assert r.price_history_model == "rx_7600", (
                f"Bei {price} EUR faelschlich als {r.price_history_model} "
                "statt rx_7600 gematcht"
            )


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
