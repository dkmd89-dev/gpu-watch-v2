"""Tests für cross_platform_stats.py (Baustein 4 -- Cross-Platform-
Preisvergleich, STATUS.md Abschnitt 16, Schritt 1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cross_platform_stats import (
    compute_all_cross_platform_stats,
    compute_cross_platform_stats,
    group_by_source,
)
from price_history import PricePoint


def _point(price: float, source: str | None, model: str | None = "rtx_3060_12gb") -> PricePoint:
    return PricePoint(
        price=price, date="2026-08-03T00:00:00+00:00", source=source, model=model,
        category="gpu", deal_score=80,
    )


def test_group_by_source_gruppiert_korrekt():
    points = [
        _point(100.0, "kleinanzeigen"),
        _point(120.0, "ebay"),
        _point(110.0, "kleinanzeigen"),
    ]
    groups = group_by_source(points)

    assert set(groups.keys()) == {"kleinanzeigen", "ebay"}
    assert len(groups["kleinanzeigen"]) == 2
    assert len(groups["ebay"]) == 1


def test_group_by_source_ueberspringt_punkte_ohne_source():
    points = [_point(100.0, "kleinanzeigen"), _point(120.0, None), _point(90.0, "")]
    groups = group_by_source(points)

    assert groups == {"kleinanzeigen": [points[0]]}


def test_compute_cross_platform_stats_none_bei_leerer_liste():
    assert compute_cross_platform_stats("rtx_3060_12gb", []) is None


def test_compute_cross_platform_stats_none_bei_nur_einer_quelle():
    points = [_point(100.0, "kleinanzeigen"), _point(110.0, "kleinanzeigen")]
    assert compute_cross_platform_stats("rtx_3060_12gb", points) is None


def test_compute_cross_platform_stats_berechnet_spread_korrekt():
    points = [
        _point(100.0, "kleinanzeigen"),
        _point(120.0, "kleinanzeigen"),
        _point(150.0, "ebay"),
        _point(170.0, "ebay"),
    ]
    stats = compute_cross_platform_stats("rtx_3060_12gb", points)

    assert stats is not None
    assert stats.model == "rtx_3060_12gb"
    assert set(stats.by_source.keys()) == {"kleinanzeigen", "ebay"}

    kleinanzeigen = stats.by_source["kleinanzeigen"]
    assert kleinanzeigen.count == 2
    assert kleinanzeigen.mean_price == 110.0
    assert kleinanzeigen.median_price == 110.0

    ebay = stats.by_source["ebay"]
    assert ebay.count == 2
    assert ebay.mean_price == 160.0
    assert ebay.median_price == 160.0

    assert stats.cheapest_source == "kleinanzeigen"
    assert stats.priciest_source == "ebay"
    # (160 - 110) / 110 * 100
    assert round(stats.spread_pct, 4) == round((160.0 - 110.0) / 110.0 * 100, 4)


def test_compute_cross_platform_stats_drei_quellen():
    points = [
        _point(100.0, "kleinanzeigen"),
        _point(150.0, "ebay"),
        _point(200.0, "quoka"),
    ]
    stats = compute_cross_platform_stats("rtx_3060_12gb", points)

    assert stats is not None
    assert set(stats.by_source.keys()) == {"kleinanzeigen", "ebay", "quoka"}
    assert stats.cheapest_source == "kleinanzeigen"
    assert stats.priciest_source == "quoka"
    assert round(stats.spread_pct, 4) == round((200.0 - 100.0) / 100.0 * 100, 4)


def test_compute_cross_platform_stats_identische_mittelwerte_ergibt_spread_null():
    points = [_point(100.0, "kleinanzeigen"), _point(100.0, "ebay")]
    stats = compute_cross_platform_stats("rtx_3060_12gb", points)

    assert stats is not None
    assert stats.spread_pct == 0.0


def test_compute_all_cross_platform_stats_liefert_dict_je_modell():
    points = [
        _point(100.0, "kleinanzeigen", model="rtx_3060_12gb"),
        _point(150.0, "ebay", model="rtx_3060_12gb"),
        _point(50.0, "kleinanzeigen", model="rtx_2060"),
        _point(60.0, "ebay", model="rtx_2060"),
    ]
    all_stats = compute_all_cross_platform_stats(points)

    assert set(all_stats.keys()) == {"rtx_3060_12gb", "rtx_2060"}
    assert all_stats["rtx_3060_12gb"].cheapest_source == "kleinanzeigen"
    assert all_stats["rtx_2060"].priciest_source == "ebay"


def test_compute_all_cross_platform_stats_ueberspringt_modelle_mit_nur_einer_quelle():
    points = [
        _point(100.0, "kleinanzeigen", model="rtx_3060_12gb"),
        _point(150.0, "ebay", model="rtx_3060_12gb"),
        _point(50.0, "kleinanzeigen", model="rtx_2060"),
        _point(55.0, "kleinanzeigen", model="rtx_2060"),
    ]
    all_stats = compute_all_cross_platform_stats(points)

    assert set(all_stats.keys()) == {"rtx_3060_12gb"}


def test_compute_all_cross_platform_stats_leere_liste_ergibt_leeres_dict():
    assert compute_all_cross_platform_stats([]) == {}


def test_compute_all_cross_platform_stats_ignoriert_punkte_ohne_model():
    points = [
        _point(100.0, "kleinanzeigen", model=None),
        _point(150.0, "ebay", model=None),
    ]
    assert compute_all_cross_platform_stats(points) == {}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
