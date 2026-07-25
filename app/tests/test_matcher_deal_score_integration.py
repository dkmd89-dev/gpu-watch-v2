"""Tests für die Deal-Score-Integration in matcher.evaluate() (Phase 6)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate, _build_score_inputs


def test_evaluate_liefert_deal_score_und_stars_bei_treffer():
    cfg = load_rules("rules")
    r = evaluate("ASUS RTX 2080Ti DUAL Lüfter", 15.0, cfg)
    assert r.matched is True
    assert r.deal_score is not None
    assert 0 <= r.deal_score <= 100
    assert r.deal_stars is not None
    assert r.deal_stars in {"★★★★★", "★★★★☆", "★★★☆☆", "★★☆☆☆", "★☆☆☆☆"}


def test_evaluate_kein_treffer_hat_keinen_score():
    cfg = load_rules("rules")
    r = evaluate("RTX 3060 Ti defekt", 50.0, cfg)
    assert r.matched is False
    assert r.deal_score is None
    assert r.deal_stars is None


def test_evaluate_5_sterne_bei_optimalem_gaming_pc():
    cfg = load_rules("rules")
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
    cfg = load_rules("rules")
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
    cfg = load_rules("rules")
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
    cfg = load_rules("rules")
    r = evaluate("Dell OptiPlex i5-8500 16GB RAM 512GB SSD Tower", 150.0, cfg)
    assert r.matched is True
    assert r.manufacturer_name == "Dell"


def test_evaluate_manufacturer_name_none_ohne_erkennbare_marke():
    cfg = load_rules("rules")
    r = evaluate("Office PC i5-8500 16GB RAM 512GB SSD Tower", 150.0, cfg)
    assert r.matched is True
    assert r.manufacturer_name is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
