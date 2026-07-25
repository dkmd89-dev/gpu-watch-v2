"""Tests fuer price_stats.py (Phase 7, Schritt 7.2)."""
import sys
from datetime import datetime, timedelta, timezone

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_history import PricePoint
from price_stats import (
    TREND_FALLEND,
    TREND_STABIL,
    TREND_STEIGEND,
    TREND_UNBEKANNT,
    compute_all_price_stats,
    compute_price_stats,
    group_by_model,
)


def _point(price: float, days_ago: int, model: str = "rtx_3060_12gb", category: str = "gpu") -> PricePoint:
    date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return PricePoint(price=price, date=date, source="kleinanzeigen", model=model,
                       category=category, deal_score=None)


# ---------- compute_price_stats: Basiswerte ----------

def test_leere_liste_liefert_none():
    assert compute_price_stats("rtx_3060_12gb", []) is None


def test_einzelner_datenpunkt():
    stats = compute_price_stats("office_pc", [_point(200.0, days_ago=0, model="office_pc")])
    assert stats.count == 1
    assert stats.min_price == stats.max_price == stats.mean_price == stats.median_price == 200.0
    assert stats.percentile_5 == stats.percentile_10 == 200.0
    assert stats.market_price == 200.0
    assert stats.trend == TREND_UNBEKANNT
    assert stats.trend_change_pct is None


def test_min_max_mean_median_korrekt():
    prices = [100.0, 150.0, 200.0, 250.0, 300.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.count == 5
    assert stats.min_price == 100.0
    assert stats.max_price == 300.0
    assert stats.mean_price == 200.0
    assert stats.median_price == 200.0


def test_perzentile_liegen_zwischen_min_und_median():
    prices = [100.0, 120.0, 150.0, 180.0, 200.0, 220.0, 250.0, 280.0, 300.0, 320.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.min_price <= stats.percentile_5 <= stats.percentile_10 <= stats.median_price


def test_market_price_faellt_bei_wenig_daten_auf_median_zurueck():
    # Weniger als 5 Datenpunkte -> Marktpreis == Median (siehe Docstring
    # _market_price(): Perzentile sind darunter nicht tragfaehig genug).
    prices = [100.0, 500.0, 300.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.market_price == stats.median_price


def test_market_price_schliesst_ausreisser_bei_genug_daten_aus():
    # 1 extremer Ausreisser nach oben unter >=5 Datenpunkten -- Marktpreis
    # (getrimmter Durchschnitt zwischen 10%/90%-Perzentil) soll deutlich
    # naeher am Gros der Preise liegen als der normale Mittelwert.
    prices = [190.0, 195.0, 200.0, 205.0, 210.0, 5000.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.mean_price > 900  # der Ausreisser zieht den Mittelwert stark hoch
    assert stats.market_price < 250  # der Marktpreis bleibt beim Gros der Preise


# ---------- Trend ----------

def test_trend_unbekannt_bei_zu_wenig_daten():
    points = [_point(100.0, days_ago=0), _point(110.0, days_ago=1), _point(120.0, days_ago=2)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.trend == TREND_UNBEKANNT
    assert stats.trend_change_pct is None


def test_trend_steigend_wenn_neuere_preise_deutlich_hoeher():
    # aeltere Haelfte (weiter in der Vergangenheit) guenstig, neuere Haelfte
    # (naeher an heute) deutlich teurer -> Preis steigt im Zeitverlauf.
    old = [_point(100.0, days_ago=d) for d in (30, 25, 20)]
    new = [_point(150.0, days_ago=d) for d in (10, 5, 0)]
    stats = compute_price_stats("rtx_3060_12gb", old + new)
    assert stats.trend == TREND_STEIGEND
    assert stats.trend_change_pct > 5.0


def test_trend_fallend_wenn_neuere_preise_deutlich_niedriger():
    old = [_point(300.0, days_ago=d) for d in (30, 25, 20)]
    new = [_point(200.0, days_ago=d) for d in (10, 5, 0)]
    stats = compute_price_stats("rtx_3060_12gb", old + new)
    assert stats.trend == TREND_FALLEND
    assert stats.trend_change_pct < -5.0


def test_trend_stabil_bei_geringer_abweichung():
    old = [_point(200.0, days_ago=d) for d in (30, 25, 20)]
    new = [_point(202.0, days_ago=d) for d in (10, 5, 0)]
    stats = compute_price_stats("rtx_3060_12gb", old + new)
    assert stats.trend == TREND_STABIL


# ---------- group_by_model / compute_all_price_stats ----------

def test_group_by_model_trennt_korrekt():
    points = [
        _point(100.0, days_ago=0, model="rtx_3060_12gb"),
        _point(200.0, days_ago=0, model="office_pc", category="office_pc"),
        _point(110.0, days_ago=1, model="rtx_3060_12gb"),
    ]
    groups = group_by_model(points)
    assert set(groups.keys()) == {"rtx_3060_12gb", "office_pc"}
    assert len(groups["rtx_3060_12gb"]) == 2
    assert len(groups["office_pc"]) == 1


def test_compute_all_price_stats_liefert_eine_statistik_pro_modell():
    points = [
        _point(100.0, days_ago=0, model="rtx_3060_12gb"),
        _point(110.0, days_ago=1, model="rtx_3060_12gb"),
        _point(250.0, days_ago=0, model="office_pc", category="office_pc"),
    ]
    all_stats = compute_all_price_stats(points)
    assert set(all_stats.keys()) == {"rtx_3060_12gb", "office_pc"}
    assert all_stats["rtx_3060_12gb"].count == 2
    assert all_stats["office_pc"].count == 1


def test_compute_all_price_stats_leere_eingabe_liefert_leeres_dict():
    assert compute_all_price_stats([]) == {}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
