"""Tests für den Verhandlungs-Assistenten (STATUS.md Abschnitt 16, Punkt 7).

Nutzt zwei Test-Strategien:
- Gegen die echte rules/gpu.yaml (Regel "RTX 3060 12GB ★ Top-Deal", einzige
  Regel mit allen drei negotiation_*-Feldern, siehe Kommentar dort):
  max_price=220, negotiation_tolerance_pct=15.0 (Grenze 253€),
  negotiation_min_score=70, negotiation_score_component="hardware_qualitaet"
  (Top-Deal-Basis-Score 85, siehe _hardware_qualitaet_score()).
- Synthetische rules_cfg-Dicts für Edge-Cases (fehlende Felder, ungültige
  Komponente), analog zum Muster in test_matcher_deal_score_integration.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules, evaluate

TITLE = "RTX 3060 12GB Grafikkarte"


def _synthetic_cfg(rule_overrides: dict) -> dict:
    base_rule = {
        "label": "Test-GPU",
        "match": ["testgpu"],
        "max_price": 100,
        "deal_rating": "Top-Deal",
    }
    base_rule.update(rule_overrides)
    return {
        "defaults": {"min_vram_gb": 0},
        "rules": [base_rule],
        "scoring_weights": {"hardware_qualitaet": 1.0},
    }


def test_negotiation_candidate_bei_toleranz_und_score_erfuellt():
    cfg = load_rules(RULES_DIR)
    r = evaluate(TITLE, 240.0, cfg)  # > 220, aber <= 253 (Toleranzgrenze)
    assert r.matched is True
    assert r.negotiation_candidate is True
    assert r.deal_score is not None


def test_kein_negotiation_ausserhalb_der_toleranz():
    cfg = load_rules(RULES_DIR)
    # 285€: ueber der Top-Deal-Toleranzgrenze (253€) UND ueber max_price
    # der nachfolgenden "RTX 3060 12GB"-Regel (280€, ohne negotiation_*-
    # Felder) -- damit greift keine der beiden Regeln.
    r = evaluate(TITLE, 285.0, cfg)
    assert r.matched is False


def test_regulaerer_match_innerhalb_max_price_ohne_flag():
    cfg = load_rules(RULES_DIR)
    r = evaluate(TITLE, 200.0, cfg)  # <= 220, regulaerer Top-Deal-Match
    assert r.matched is True
    assert r.negotiation_candidate is False


def test_feature_inaktiv_ohne_alle_drei_felder():
    cfg = _synthetic_cfg({"negotiation_tolerance_pct": 15.0})  # nur 1 von 3
    r = evaluate("testgpu", 110.0, cfg)  # > max_price 100
    assert r.matched is False


def test_negotiation_greift_bei_synthetischer_konfiguration():
    cfg = _synthetic_cfg(
        {
            "negotiation_tolerance_pct": 20.0,
            "negotiation_min_score": 80,
            "negotiation_score_component": "hardware_qualitaet",
        }
    )
    r = evaluate("testgpu", 115.0, cfg)  # 100 < 115 <= 120 (Toleranz)
    assert r.matched is True
    assert r.negotiation_candidate is True


def test_ablehnung_bei_score_unter_mindestwert():
    cfg = _synthetic_cfg(
        {
            "deal_rating": "Okay",  # Basis-Score 45, deutlich unter 80
            "negotiation_tolerance_pct": 20.0,
            "negotiation_min_score": 80,
            "negotiation_score_component": "hardware_qualitaet",
        }
    )
    r = evaluate("testgpu", 115.0, cfg)
    assert r.matched is False


def test_ungueltige_score_component_deaktiviert_feature():
    cfg = _synthetic_cfg(
        {
            "negotiation_tolerance_pct": 20.0,
            "negotiation_min_score": 10,
            "negotiation_score_component": "does_not_exist",
        }
    )
    r = evaluate("testgpu", 115.0, cfg)
    assert r.matched is False
