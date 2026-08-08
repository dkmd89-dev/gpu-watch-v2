"""Tests fuer top_deal.py (Phase 7, Schritt 7.3; neue Score+Discount-Regel
siehe Auftrag "Top-Deal-Logik optimieren").

Die alte, ausschliesslich auf Rabatt basierende 15%-Regel wurde bewusst
ersetzt (siehe top_deal.py Modul-Docstring "HISTORIE"). Diese Tests decken
die neue Kombination aus deal_score und Marktpreis-Rabatt ab, inkl. aller im
Auftrag (Abschnitt 8) vorgegebenen Grenzfaelle.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_stats import PriceStats
from top_deal import (
    MIN_SAMPLES_FOR_TOP_DEAL_DETECTION,
    TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT,
    TOP_DEAL_DISCOUNT_THRESHOLD_B_PCT,
    TOP_DEAL_SCORE_THRESHOLD_A,
    TOP_DEAL_SCORE_THRESHOLD_B,
    evaluate_top_deal,
)


def _stats(market_price: float, count: int = 10) -> PriceStats:
    """Minimal befuellte PriceStats-Fixture -- top_deal.py interessiert sich
    nur fuer .count und .market_price, der Rest ist fuer diese Tests egal."""
    return PriceStats(
        model="rtx_3060_12gb",
        count=count,
        min_price=market_price * 0.5,
        max_price=market_price * 2,
        mean_price=market_price,
        median_price=market_price,
        percentile_5=market_price * 0.6,
        percentile_10=market_price * 0.7,
        market_price=market_price,
        trend="stabil",
        trend_change_pct=0.0,
    )


def _price_for_discount(market_price: float, discount_pct: float) -> float:
    return market_price * (1 - discount_pct / 100)


# ---------------------------------------------------------------------
# Datengrundlage / Marktpreis-Edge-Cases (unveraendert gegenueber vorher)
# ---------------------------------------------------------------------

def test_keine_statistik_ist_kein_top_deal():
    result = evaluate_top_deal(150.0, None, deal_score=95)
    assert result.is_top_deal is False
    assert result.market_price is None
    assert result.discount_pct is None
    assert "zu wenig" in result.reason.lower() or "wenig datengrundlage" in result.reason.lower()


def test_zu_wenig_datenpunkte_ist_kein_top_deal():
    stats = _stats(market_price=200.0, count=MIN_SAMPLES_FOR_TOP_DEAL_DETECTION - 1)
    result = evaluate_top_deal(100.0, stats, deal_score=95)  # objektiv guenstig, aber zu wenig Daten
    assert result.is_top_deal is False
    assert result.discount_pct is None


def test_marktpreis_null_liefert_keine_prozent_aussage():
    stats = _stats(market_price=0.0)
    result = evaluate_top_deal(0.0, stats, deal_score=95)
    assert result.is_top_deal is False
    assert result.discount_pct is None


def test_preis_ueber_marktpreis_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    result = evaluate_top_deal(250.0, stats, deal_score=100)
    assert result.is_top_deal is False
    assert result.discount_pct == -25.0
    assert "über" in result.reason


def test_preis_gleich_marktpreis_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    result = evaluate_top_deal(200.0, stats, deal_score=100)
    assert result.is_top_deal is False
    assert result.discount_pct == 0.0


def test_preis_kleiner_gleich_null_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    result = evaluate_top_deal(0.0, stats, deal_score=100)
    assert result.is_top_deal is False


def test_fehlender_deal_score_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    result = evaluate_top_deal(100.0, stats, deal_score=None)  # 50% Rabatt, aber kein Score
    assert result.is_top_deal is False
    assert result.discount_pct == 50.0


# ---------------------------------------------------------------------
# Neue Score+Discount-Regel: exakte Grenzfaelle aus dem Auftrag (Abschnitt 8)
# ---------------------------------------------------------------------

def test_score_80_discount_25_ist_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 25.0)
    result = evaluate_top_deal(price, stats, deal_score=80)
    assert result.is_top_deal is True
    assert result.rule == "A"


def test_score_80_discount_24_99_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 24.99)
    result = evaluate_top_deal(price, stats, deal_score=80)
    assert result.is_top_deal is False


def test_score_79_discount_50_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 50.0)
    result = evaluate_top_deal(price, stats, deal_score=79)
    assert result.is_top_deal is False


def test_score_89_discount_24_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 24.0)
    result = evaluate_top_deal(price, stats, deal_score=89)
    assert result.is_top_deal is False


def test_score_90_discount_20_ist_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 20.0)
    result = evaluate_top_deal(price, stats, deal_score=90)
    assert result.is_top_deal is True
    assert result.rule == "B"


def test_score_90_discount_19_99_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 19.99)
    result = evaluate_top_deal(price, stats, deal_score=90)
    assert result.is_top_deal is False


def test_score_95_discount_21_ist_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 21.0)
    result = evaluate_top_deal(price, stats, deal_score=95)
    assert result.is_top_deal is True
    assert result.rule == "B"


def test_score_100_discount_50_ist_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 50.0)
    result = evaluate_top_deal(price, stats, deal_score=100)
    assert result.is_top_deal is True
    assert result.rule == "B"


def test_score_75_discount_40_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    price = _price_for_discount(200.0, 40.0)
    result = evaluate_top_deal(price, stats, deal_score=75)
    assert result.is_top_deal is False


def test_konstanten_stimmen_mit_auftrag_ueberein():
    assert TOP_DEAL_SCORE_THRESHOLD_A == 80
    assert TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT == 25.0
    assert TOP_DEAL_SCORE_THRESHOLD_B == 90
    assert TOP_DEAL_DISCOUNT_THRESHOLD_B_PCT == 20.0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
