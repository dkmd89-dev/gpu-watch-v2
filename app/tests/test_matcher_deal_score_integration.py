"""Tests für die Deal-Score-Integration in matcher.evaluate() (Phase 6)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate


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


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
