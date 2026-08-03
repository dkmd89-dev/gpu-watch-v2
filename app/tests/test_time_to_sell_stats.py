"""Tests für time_to_sell_stats.py (Baustein 6 -- Time-to-Sell-Schätzung,
STATUS.md Abschnitt 16, Schritt 3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from time_to_sell import TimeToSellPoint
from time_to_sell_stats import (
    compute_all_time_to_sell_stats,
    compute_time_to_sell_stats,
    group_by_category,
)


def _point(days: float, category: str | None, model: str = "m1") -> TimeToSellPoint:
    return TimeToSellPoint(
        days=days, first_seen="a", last_seen="b", model=model, category=category, detected_at="d",
    )


def test_group_by_category_gruppiert_korrekt():
    points = [
        _point(1.0, "gpu"),
        _point(2.0, "office_pc"),
        _point(3.0, "gpu"),
    ]
    groups = group_by_category(points)

    assert set(groups.keys()) == {"gpu", "office_pc"}
    assert len(groups["gpu"]) == 2
    assert len(groups["office_pc"]) == 1


def test_group_by_category_ueberspringt_punkte_ohne_kategorie():
    points = [_point(1.0, "gpu"), _point(2.0, None)]
    groups = group_by_category(points)

    assert groups == {"gpu": [points[0]]}


def test_compute_time_to_sell_stats_none_bei_leerer_liste():
    assert compute_time_to_sell_stats("gpu", []) is None


def test_compute_time_to_sell_stats_berechnet_min_max_mean_median():
    points = [_point(1.0, "gpu"), _point(3.0, "gpu"), _point(5.0, "gpu")]
    stats = compute_time_to_sell_stats("gpu", points)

    assert stats is not None
    assert stats.category == "gpu"
    assert stats.count == 3
    assert stats.min_days == 1.0
    assert stats.max_days == 5.0
    assert stats.mean_days == 3.0
    assert stats.median_days == 3.0


def test_compute_time_to_sell_stats_einzelner_datenpunkt():
    stats = compute_time_to_sell_stats("gpu", [_point(2.5, "gpu")])

    assert stats.count == 1
    assert stats.min_days == stats.max_days == stats.mean_days == stats.median_days == 2.5


def test_compute_all_time_to_sell_stats_liefert_dict_je_kategorie():
    points = [
        _point(1.0, "gpu"), _point(3.0, "gpu"),
        _point(10.0, "office_pc"),
    ]
    all_stats = compute_all_time_to_sell_stats(points)

    assert set(all_stats.keys()) == {"gpu", "office_pc"}
    assert all_stats["gpu"].count == 2
    assert all_stats["gpu"].mean_days == 2.0
    assert all_stats["office_pc"].count == 1
    assert all_stats["office_pc"].mean_days == 10.0


def test_compute_all_time_to_sell_stats_leere_liste_ergibt_leeres_dict():
    assert compute_all_time_to_sell_stats([]) == {}


def test_compute_all_time_to_sell_stats_ignoriert_punkte_ohne_kategorie():
    all_stats = compute_all_time_to_sell_stats([_point(1.0, None)])
    assert all_stats == {}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
