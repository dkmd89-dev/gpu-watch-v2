"""Tests für data_quality.py (roadmap.md Phase 10, Schritt 10a)"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_quality import (
    check_thin_price_history,
    check_stale_categories,
    check_zero_match_categories,
    DataQualityWarning,
    WARNING_THIN_PRICE_HISTORY,
    WARNING_STALE_CATEGORY,
    WARNING_ZERO_MATCH_CATEGORY,
    DEFAULT_STALE_CATEGORY_DAYS,
    DEFAULT_MIN_SCRAPED_FOR_ZERO_MATCH_WARNING,
)
from price_history import PricePoint
from price_stats import compute_all_price_stats, compute_price_stats


def _point(price, model="rtx_3060_12gb", category="gpu", days_ago=0.0, now=None):
    ref = now or datetime.now(timezone.utc)
    date = (ref - timedelta(days=days_ago)).isoformat()
    return PricePoint(price=price, date=date, source="kleinanzeigen", model=model, category=category, deal_score=None)


# ---------- check_thin_price_history() ----------

def test_wenig_datenpunkte_erzeugt_warnung():
    points = [_point(100.0 + i, days_ago=i) for i in range(3)]
    stats = compute_all_price_stats(points)
    warnings = check_thin_price_history(stats)
    assert len(warnings) == 1
    assert warnings[0].kind == WARNING_THIN_PRICE_HISTORY
    assert warnings[0].subject == "rtx_3060_12gb"
    assert "3 Datenpunkte" in warnings[0].message


def test_genug_datenpunkte_erzeugt_keine_warnung():
    points = [_point(100.0 + i, days_ago=i) for i in range(10)]
    stats = compute_all_price_stats(points)
    assert check_thin_price_history(stats) == []


def test_mehrere_modelle_nur_duenne_werden_gemeldet():
    points = (
        [_point(100.0 + i, model="rtx_3060_12gb", days_ago=i) for i in range(10)]
        + [_point(200.0 + i, model="rtx_4070", days_ago=i) for i in range(2)]
    )
    stats = compute_all_price_stats(points)
    warnings = check_thin_price_history(stats)
    subjects = {w.subject for w in warnings}
    assert subjects == {"rtx_4070"}


def test_ein_datenpunkt_singular_in_meldung():
    points = [_point(100.0)]
    stats = compute_all_price_stats(points)
    warnings = check_thin_price_history(stats)
    assert "1 Datenpunkt " in warnings[0].message or warnings[0].message.endswith("1 Datenpunkt)." )


def test_leeres_stats_dict_erzeugt_keine_warnung():
    assert check_thin_price_history({}) == []


# ---------- check_stale_categories() ----------

def test_veraltete_kategorie_erzeugt_warnung():
    now = datetime.now(timezone.utc)
    points = [_point(100.0, category="office_pc", days_ago=10, now=now)]
    warnings = check_stale_categories(points, now=now)
    assert len(warnings) == 1
    assert warnings[0].kind == WARNING_STALE_CATEGORY
    assert warnings[0].subject == "office_pc"


def test_frische_kategorie_erzeugt_keine_warnung():
    now = datetime.now(timezone.utc)
    points = [_point(100.0, category="gaming_pc", days_ago=1, now=now)]
    assert check_stale_categories(points, now=now) == []


def test_genau_an_der_schwelle_erzeugt_keine_warnung():
    # > max_age_days, nicht >= -- Grenzwert selbst gilt noch nicht als
    # veraltet.
    now = datetime.now(timezone.utc)
    points = [_point(100.0, category="office_pc", days_ago=DEFAULT_STALE_CATEGORY_DAYS, now=now)]
    assert check_stale_categories(points, now=now) == []


def test_kategorie_mit_gemischt_altem_und_neuem_punkt_nutzt_juengsten():
    # Ein alter Punkt (30 Tage) und ein frischer (1 Tag) derselben
    # Kategorie -- der JUENGSTE Punkt zaehlt, keine Warnung.
    now = datetime.now(timezone.utc)
    points = [
        _point(100.0, category="office_pc", days_ago=30, now=now),
        _point(110.0, category="office_pc", days_ago=1, now=now),
    ]
    assert check_stale_categories(points, now=now) == []


def test_mehrere_kategorien_nur_veraltete_werden_gemeldet():
    now = datetime.now(timezone.utc)
    points = [
        _point(100.0, category="office_pc", days_ago=10, now=now),
        _point(200.0, category="gaming_pc", days_ago=1, now=now),
    ]
    warnings = check_stale_categories(points, now=now)
    subjects = {w.subject for w in warnings}
    assert subjects == {"office_pc"}


def test_punkte_ohne_kategorie_werden_uebersprungen():
    now = datetime.now(timezone.utc)
    points = [_point(100.0, category=None, days_ago=30, now=now)]
    assert check_stale_categories(points, now=now) == []


def test_benutzerdefinierte_schwelle_wird_respektiert():
    now = datetime.now(timezone.utc)
    points = [_point(100.0, category="office_pc", days_ago=3, now=now)]
    assert check_stale_categories(points, max_age_days=2.0, now=now) != []
    assert check_stale_categories(points, max_age_days=5.0, now=now) == []


def test_leere_punkteliste_erzeugt_keine_warnung():
    assert check_stale_categories([]) == []


def test_kategorie_mit_null_treffern_bei_ausreichend_scrape_volumen_erzeugt_warnung():
    warnings = check_zero_match_categories(
        {"office_pc": 0, "gaming_pc": 5}, total_scraped=100,
    )
    assert len(warnings) == 1
    assert warnings[0].kind == WARNING_ZERO_MATCH_CATEGORY
    assert warnings[0].subject == "office_pc"


def test_kategorie_mit_treffern_erzeugt_keine_warnung():
    warnings = check_zero_match_categories({"gaming_pc": 5}, total_scraped=100)
    assert warnings == []


def test_zu_kleines_scrape_volumen_unterdrueckt_warnung():
    # Unter der Mindest-Scrape-Schwelle -> keine Warnung, auch bei 0 Treffern
    # (statistisch nicht aussagekraeftig bei kleinen Scans).
    warnings = check_zero_match_categories(
        {"office_pc": 0}, total_scraped=10,
        min_scraped_for_warning=DEFAULT_MIN_SCRAPED_FOR_ZERO_MATCH_WARNING,
    )
    assert warnings == []


def test_grenzwert_exakt_an_der_scrape_schwelle_erzeugt_warnung():
    warnings = check_zero_match_categories(
        {"office_pc": 0}, total_scraped=DEFAULT_MIN_SCRAPED_FOR_ZERO_MATCH_WARNING,
    )
    assert len(warnings) == 1


def test_benutzerdefinierte_scrape_schwelle_wird_respektiert():
    assert check_zero_match_categories({"x": 0}, total_scraped=20, min_scraped_for_warning=50) == []
    assert check_zero_match_categories({"x": 0}, total_scraped=20, min_scraped_for_warning=10) != []


def test_leeres_match_counts_dict_erzeugt_keine_warnung():
    assert check_zero_match_categories({}, total_scraped=1000) == []


def test_mehrere_kategorien_nur_die_mit_null_treffern_werden_gemeldet():
    warnings = check_zero_match_categories(
        {"office_pc": 0, "gaming_pc": 3, "gpu": 0}, total_scraped=100,
    )
    subjects = {w.subject for w in warnings}
    assert subjects == {"office_pc", "gpu"}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
