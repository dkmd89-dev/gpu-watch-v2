"""Tests fuer top_deal.py (Phase 7, Schritt 7.3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_stats import PriceStats
from top_deal import (
    MIN_SAMPLES_FOR_TOP_DEAL_DETECTION,
    TOP_DEAL_DISCOUNT_THRESHOLD_PCT,
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


def test_keine_statistik_ist_kein_top_deal():
    result = evaluate_top_deal(150.0, None)
    assert result.is_top_deal is False
    assert result.market_price is None
    assert result.discount_pct is None
    assert "zu wenig" in result.reason.lower() or "wenig datengrundlage" in result.reason.lower()


def test_zu_wenig_datenpunkte_ist_kein_top_deal():
    stats = _stats(market_price=200.0, count=MIN_SAMPLES_FOR_TOP_DEAL_DETECTION - 1)
    result = evaluate_top_deal(100.0, stats)  # objektiv sehr guenstig, aber zu wenig Daten
    assert result.is_top_deal is False
    assert result.discount_pct is None


def test_genug_datenpunkte_grenzwert_wird_geprueft():
    stats = _stats(market_price=200.0, count=MIN_SAMPLES_FOR_TOP_DEAL_DETECTION)
    # deutlich unter Marktpreis -> sollte jetzt (mit genug Daten) auswertbar sein
    result = evaluate_top_deal(100.0, stats)
    assert result.discount_pct is not None
    assert result.is_top_deal is True


def test_preis_deutlich_unter_marktpreis_ist_top_deal():
    stats = _stats(market_price=200.0)
    result = evaluate_top_deal(150.0, stats)  # 25% unter Marktpreis
    assert result.is_top_deal is True
    assert result.discount_pct == 25.0


def test_preis_knapp_unter_schwelle_ist_top_deal():
    stats = _stats(market_price=200.0)
    price = 200.0 * (1 - TOP_DEAL_DISCOUNT_THRESHOLD_PCT / 100)  # exakt an der Schwelle
    result = evaluate_top_deal(price, stats)
    assert result.is_top_deal is True  # ">=" Schwelle zaehlt noch als Top-Deal


def test_preis_knapp_ueber_schwelle_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    price = 200.0 * (1 - (TOP_DEAL_DISCOUNT_THRESHOLD_PCT - 1) / 100)  # 1%-Punkt zu wenig Rabatt
    result = evaluate_top_deal(price, stats)
    assert result.is_top_deal is False


def test_preis_ueber_marktpreis_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    result = evaluate_top_deal(250.0, stats)
    assert result.is_top_deal is False
    assert result.discount_pct == -25.0
    assert "über" in result.reason


def test_preis_gleich_marktpreis_ist_kein_top_deal():
    stats = _stats(market_price=200.0)
    result = evaluate_top_deal(200.0, stats)
    assert result.is_top_deal is False
    assert result.discount_pct == 0.0


def test_marktpreis_null_liefert_keine_prozent_aussage():
    stats = _stats(market_price=0.0)
    result = evaluate_top_deal(0.0, stats)
    assert result.is_top_deal is False
    assert result.discount_pct is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
