"""Tests für die Deal-Score-Integration in matcher.evaluate() (Phase 6)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules, evaluate, _build_score_inputs


def test_evaluate_liefert_deal_score_und_stars_bei_treffer():
    cfg = load_rules(RULES_DIR)
    r = evaluate("ASUS RTX 2080Ti DUAL Lüfter", 15.0, cfg)
    assert r.matched is True
    assert r.deal_score is not None
    assert 0 <= r.deal_score <= 100
    assert r.deal_stars is not None
    assert r.deal_stars in {"★★★★★", "★★★★☆", "★★★☆☆", "★★☆☆☆", "★☆☆☆☆"}


def test_evaluate_kein_treffer_hat_keinen_score():
    cfg = load_rules(RULES_DIR)
    r = evaluate("RTX 3060 Ti defekt", 50.0, cfg)
    assert r.matched is False
    assert r.deal_score is None
    assert r.deal_stars is None


def test_evaluate_5_sterne_bei_optimalem_gaming_pc():
    cfg = load_rules(RULES_DIR)
    # Bestmoegliches Angebot: 0 Euro, Top-Deal-GPU, SSD vorhanden
    r = evaluate(
        "Gaming PC Intel Core i5-8500 16GB RAM RTX 3060 512GB SSD Tower",
        0.0,
        cfg,
    )
    assert r.matched is True
    assert r.deal_stars == "★★★★★"
    assert r.deal_score >= 95


def test_evaluate_niedriger_score_bei_hohem_preis():
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        "Gaming PC Intel Core i5-8500 16GB RAM RTX 3060 Tower",
        399.0,  # nahe an max_price (400) der Top-Deal-Regel
        cfg,
    )
    assert r.matched is True
    assert r.deal_score < 40


def test_evaluate_legacy_einzeldatei_modus_liefert_ebenfalls_score():
    # Legacy-Modus hat keine eigenen scoring_weights -> DEFAULT_WEIGHTS-
    # Fallback muss greifen, kein Crash. Nutzt eine schlanke Test-Fixture
    # statt der früheren, im Produktivbetrieb unreferenzierten app/rules.yaml
    # (die wurde entfernt, siehe Phase-0-Bereinigung).
    fixture = str(Path(__file__).resolve().parent / "fixtures" / "legacy_single_file_rules.yaml")
    cfg = load_rules(fixture)
    r = evaluate("ASUS RTX 2080Ti DUAL Lüfter", 15.0, cfg)
    assert r.matched is True
    assert r.deal_score is not None
    assert r.deal_stars is not None


def test_evaluate_score_reproduzierbar_fuer_gleiche_eingabe():
    cfg = load_rules(RULES_DIR)
    r1 = evaluate("ASUS RTX 2080Ti DUAL Lüfter", 15.0, cfg)
    r2 = evaluate("ASUS RTX 2080Ti DUAL Lüfter", 15.0, cfg)
    assert r1.deal_score == r2.deal_score
    assert r1.deal_stars == r2.deal_stars


# ---------- Hersteller-Detector-Verdrahtung (Folgeschritt) ----------

def test_build_score_inputs_erkennt_hersteller():
    inputs = _build_score_inputs("dell optiplex 7040 i5-8500 16gb", None, {})
    assert inputs["manufacturer_name"] == "Dell"


def test_build_score_inputs_ohne_hersteller_liefert_none():
    inputs = _build_score_inputs("gaming pc ryzen 5 3600 rtx 3060", None, {})
    assert inputs["manufacturer_name"] is None


def test_evaluate_reicht_manufacturer_reputation_bis_zum_score_durch():
    # Synthetische rules_cfg mit eigenem Reputations-Eintrag und Gewicht
    # ausschliesslich auf "hersteller" -- prueft die vollstaendige Kette
    # Titel -> Detector -> compute_deal_score(), unabhaengig vom
    # produktiven Gewicht (das in _global.yaml bewusst bei 0 bleibt).
    cfg = {
        "defaults": {},
        "rules": [
            {
                "label": "Test-Office-PC",
                "requirements": {
                    "min_ram_gb": 8,
                    "min_cpu": {"intel": {"min_tier_rank": 5, "min_generation": 8}},
                },
                "max_price": 300,
                "deal_rating": "Okay",
                "_category": "office_pc",
                "_category_exclude_terms": [],
                "_scoring_weights": {"hersteller": 1.0},
            }
        ],
        "search_terms": [],
        "notifications": {},
        "scoring_weights": {},
        "manufacturer_reputation": {"Dell": 80, "_default": 60},
        "_directory_mode": True,
    }
    r = evaluate("Dell OptiPlex i5-8500 16GB RAM", 100.0, cfg)
    assert r.matched is True
    assert r.deal_score == 80


def test_evaluate_reicht_market_price_als_estimated_resale_price_durch():
    # Reselling-/Arbitrage-Konzept (STATUS.md Abschnitt 16): market_prices
    # wird laut Phase-1-Entscheidung 1:1 als estimated_resale_price genutzt.
    # Gewicht ausschliesslich auf "profit" -- prueft die vollstaendige Kette
    # market_prices -> evaluate() -> compute_deal_score() -> profit-Score.
    cfg = {
        "defaults": {},
        "rules": [
            {
                "label": "Test-GPU",
                "max_price": 300,
                "deal_rating": "Okay",
                "_category": "gpu",
                "_category_exclude_terms": [],
                "_scoring_weights": {"profit": 1.0},
                "price_history_model": "rtx_3060_12gb",
            }
        ],
        "search_terms": [],
        "notifications": {},
        "scoring_weights": {},
        "fees": {},
        "_directory_mode": True,
    }
    r = evaluate(
        "RTX 3060 12GB", 100.0, cfg,
        market_prices={"rtx_3060_12gb": 200.0},  # deutliche Marge, keine fees
    )
    assert r.matched is True
    # margin_pct = (200-100)/100*100 = 100%, gekappt bei 50 -> Score 100
    assert r.deal_score == 100


def test_evaluate_beruecksichtigt_fees_aus_rules_cfg():
    cfg = {
        "defaults": {},
        "rules": [
            {
                "label": "Test-GPU",
                "max_price": 300,
                "deal_rating": "Okay",
                "_category": "gpu",
                "_category_exclude_terms": [],
                "_scoring_weights": {"profit": 1.0},
                "price_history_model": "rtx_3060_12gb",
            }
        ],
        "search_terms": [],
        "notifications": {},
        "scoring_weights": {},
        "fees": {"platform_fee_pct": 20.0, "shipping_cost": 10.0},
        "_directory_mode": True,
    }
    r_ohne_fees = evaluate(
        "RTX 3060 12GB", 100.0, {**cfg, "fees": {}},
        market_prices={"rtx_3060_12gb": 150.0},
    )
    r_mit_fees = evaluate(
        "RTX 3060 12GB", 100.0, cfg,
        market_prices={"rtx_3060_12gb": 150.0},
    )
    assert r_mit_fees.deal_score < r_ohne_fees.deal_score


def test_evaluate_ohne_market_price_profit_score_ist_platzhalter_und_ohne_einfluss():
    # Default-Gewicht "profit" ist 0 (siehe DEFAULT_WEIGHTS) -- ohne
    # market_prices darf sich am produktiven Score NICHTS aendern.
    cfg = {
        "defaults": {},
        "rules": [
            {
                "label": "Test-GPU",
                "max_price": 300,
                "deal_rating": "Okay",
                "_category": "gpu",
                "_category_exclude_terms": [],
            }
        ],
        "search_terms": [],
        "notifications": {},
        "scoring_weights": {},
        "fees": {},
        "_directory_mode": True,
    }
    r_ohne = evaluate("RTX 3060 12GB", 100.0, cfg)
    r_mit_leerem_market_prices = evaluate("RTX 3060 12GB", 100.0, cfg, market_prices={})
    assert r_ohne.deal_score == r_mit_leerem_market_prices.deal_score


def test_evaluate_ohne_erkannten_hersteller_nutzt_platzhalter():
    cfg = {
        "defaults": {},
        "rules": [
            {
                "label": "Test-Office-PC",
                "requirements": {
                    "min_ram_gb": 8,
                    "min_cpu": {"intel": {"min_tier_rank": 5, "min_generation": 8}},
                },
                "max_price": 300,
                "deal_rating": "Okay",
                "_category": "office_pc",
                "_category_exclude_terms": [],
                "_scoring_weights": {"hersteller": 1.0},
            }
        ],
        "search_terms": [],
        "notifications": {},
        "scoring_weights": {},
        "manufacturer_reputation": {"Dell": 80, "_default": 60},
        "_directory_mode": True,
    }
    r = evaluate("Office PC i5-8500 16GB RAM", 100.0, cfg)
    assert r.matched is True
    assert r.deal_score == 60  # Platzhalter, keine Marke im Titel


def test_evaluate_liefert_manufacturer_name_auf_matchresult():
    cfg = load_rules(RULES_DIR)
    r = evaluate("Dell OptiPlex i5-8500 16GB RAM 512GB SSD Tower", 150.0, cfg)
    assert r.matched is True
    assert r.manufacturer_name == "Dell"


def test_evaluate_manufacturer_name_none_ohne_erkennbare_marke():
    cfg = load_rules(RULES_DIR)
    r = evaluate("Office PC i5-8500 16GB RAM 512GB SSD Tower", 150.0, cfg)
    assert r.matched is True
    assert r.manufacturer_name is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
