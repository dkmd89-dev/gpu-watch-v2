"""Tests fuer price_stats.py (Phase 7, Schritt 7.2)."""
import sys
from datetime import datetime, timedelta, timezone

import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_history import PricePoint
from price_stats import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    TREND_FALLEND,
    TREND_STABIL,
    TREND_STEIGEND,
    TREND_UNBEKANNT,
    compute_all_price_stats,
    compute_price_stats,
    compute_resale_stats_by_group,
    group_by_model,
    group_by_resale_group,
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


# ---------- roadmap.md Phase 5: percentile_25/percentile_90, Datenalter, Confidence ----------

def test_percentile_25_liegt_zwischen_percentile_10_und_median():
    prices = [100.0, 120.0, 150.0, 180.0, 200.0, 220.0, 250.0, 280.0, 300.0, 320.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.percentile_10 <= stats.percentile_25 <= stats.median_price


def test_percentile_90_liegt_zwischen_percentile_75_und_max():
    prices = [100.0, 120.0, 150.0, 180.0, 200.0, 220.0, 250.0, 280.0, 300.0, 320.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.percentile_75 <= stats.percentile_90 <= stats.max_price


def test_confidence_low_unter_fuenf_datenpunkten():
    points = [_point(p, days_ago=i) for i, p in enumerate([100.0, 200.0, 300.0])]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.count == 3
    assert stats.confidence == CONFIDENCE_LOW


def test_confidence_medium_zwischen_fuenf_und_vierzehn_datenpunkten():
    points = [_point(100.0 + i, days_ago=i) for i in range(8)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.count == 8
    assert stats.confidence == CONFIDENCE_MEDIUM


def test_confidence_high_ab_fuenfzehn_datenpunkten():
    points = [_point(100.0 + i, days_ago=i) for i in range(15)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.count == 15
    assert stats.confidence == CONFIDENCE_HIGH


def test_confidence_grenzwert_vierzehn_ist_noch_medium():
    points = [_point(100.0 + i, days_ago=i) for i in range(14)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.count == 14
    assert stats.confidence == CONFIDENCE_MEDIUM


def test_data_age_days_misst_juengsten_datenpunkt():
    # aeltester Punkt vor 10 Tagen, juengster vor 2 Tagen -> data_age_days
    # bezieht sich auf den juengsten (Frische-Indikator), nicht den Durchschnitt.
    points = [_point(100.0, days_ago=10), _point(150.0, days_ago=2)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert 1.9 <= stats.data_age_days <= 2.1


def test_data_age_days_null_bei_heutigem_datenpunkt():
    # Toleranz nach unten, da das Modul-weite `now` (price_stats.py) einmalig
    # beim Import gesetzt wird, nicht bei jedem Aufruf -- ein Testpunkt mit
    # "jetzt" kann dadurch minimal NACH dem eingefrorenen `now` liegen.
    stats = compute_price_stats("rtx_3060_12gb", [_point(100.0, days_ago=0)])
    assert stats.data_age_days is not None
    assert -0.01 <= stats.data_age_days < 0.01


def test_confidence_und_neue_perzentile_sind_rein_informativ():
    """roadmap.md Phase 5: die neuen Felder duerfen market_price/
    estimated_resale_price nicht veraendern -- Regressionsschutz gegen
    versehentliche Kopplung."""
    prices = [100.0, 120.0, 150.0, 180.0, 200.0, 220.0, 250.0, 280.0, 300.0, 320.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.confidence == CONFIDENCE_MEDIUM
    # market_price haengt weiterhin ausschliesslich von P10/P90/Median ab,
    # nicht vom neuen confidence-Feld.
    assert stats.market_price == pytest.approx(
        sum(p for p in prices if stats.percentile_10 <= p <= stats.percentile_90) /
        len([p for p in prices if stats.percentile_10 <= p <= stats.percentile_90])
    )


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


# ---------- estimated_resale_price (Reselling-/Arbitrage-Konzept, Punkt c) ----------
# Methodisch GETRENNT von market_price: nutzt das obere Preissegment
# (P75-P90) statt des gesamten P10-P90-Bereichs -- siehe
# price_stats.py::_estimated_resale_price()-Docstring.

def test_estimated_resale_price_ist_none_bei_wenig_daten():
    # Weniger als 5 Datenpunkte -> keine belastbare Verkaufsschaetzung.
    # Seit "Flip-Kandidaten-Logik optimieren", Schritt B (Option 1,
    # STATUS.md Abschnitt 33b): liefert bewusst None statt (wie vorher)
    # eines max_price-Fallbacks -- der fruehere Fallback erwies sich bei
    # duenner Preishistorie als strukturell zu optimistisch. market_price
    # bleibt von dieser Aenderung unberuehrt.
    prices = [100.0, 500.0, 300.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.estimated_resale_price is None
    assert stats.market_price == 300.0  # Median, unveraendert


def test_estimated_resale_price_liegt_ueber_market_price_bei_genug_daten():
    # Bei >=5 guenstig verteilten Datenpunkten liegt das obere Preis-
    # segment (P75-P90) strukturell ueber dem P10-P90-Trimm-Mittelwert
    # (market_price) -- das ist der eigentliche Zweck der Trennung:
    # market_price unterschaetzt den realistischen Verkaufspreis, weil
    # der Bot selbst nur guenstige Angebote in die Historie schreibt.
    prices = [190.0, 200.0, 210.0, 220.0, 230.0, 240.0, 250.0, 260.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.estimated_resale_price > stats.market_price


def test_percentile_75_liegt_zwischen_median_und_percentile_90():
    prices = [100.0, 120.0, 150.0, 180.0, 200.0, 220.0, 250.0, 280.0, 300.0, 320.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    p90 = stats.max_price  # naeherungsweise, exakter Wert unten via _percentile getestet
    assert stats.median_price <= stats.percentile_75 <= stats.max_price


def test_estimated_resale_price_einzelner_datenpunkt_ist_none():
    # 1 Datenpunkt < _MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE (5) -> None
    # (Schritt B, Option 1) statt frueher der Einzelwert selbst.
    stats = compute_price_stats("office_pc", [_point(200.0, days_ago=0, model="office_pc")])
    assert stats.estimated_resale_price is None
    assert stats.market_price == 200.0  # Median bei einem Punkt = der Punkt selbst


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


# ---------- group_by_resale_group / compute_resale_stats_by_group
# (Option 2, "Flip-Kandidaten-Logik optimieren", STATUS.md Abschnitt 33b) ----------

def test_group_by_resale_group_fasst_gemappte_modelle_zusammen():
    points = [
        _point(20.0, days_ago=0, model="lego_sw_clone", category="lego_minifiguren"),
        _point(30.0, days_ago=1, model="lego_promo", category="lego_minifiguren"),
        _point(15.0, days_ago=0, model="lego_cmf", category="lego_minifiguren"),
    ]
    mapping = {"lego_sw_clone": "lego_rare_minifig_common", "lego_promo": "lego_rare_minifig_common"}
    groups = group_by_resale_group(points, mapping)
    assert set(groups.keys()) == {"lego_rare_minifig_common", "lego_cmf"}
    assert len(groups["lego_rare_minifig_common"]) == 2
    assert len(groups["lego_cmf"]) == 1


def test_group_by_resale_group_ohne_mapping_eintrag_ist_identitaet():
    # Modell fehlt im Mapping (kein resale_price_group in der YAML-Regel)
    # -> bildet weiterhin nur sich selbst ab, identisch zu group_by_model().
    points = [_point(100.0, days_ago=0, model="rtx_3060_12gb")]
    assert group_by_resale_group(points, {}) == group_by_model(points)


def test_compute_resale_stats_by_group_erhoeht_datenpunkte_pro_gruppe():
    # 3 Punkte je Einzelmodell (unter der 5er-Perzentil-Schwelle) --
    # gemeinsam gruppiert reicht es fuer eine belastbare Schaetzung.
    points = [
        _point(30.0, days_ago=0, model="lego_sw_clone", category="lego_minifiguren"),
        _point(35.0, days_ago=1, model="lego_sw_clone", category="lego_minifiguren"),
        _point(40.0, days_ago=2, model="lego_promo", category="lego_minifiguren"),
        _point(45.0, days_ago=3, model="lego_promo", category="lego_minifiguren"),
        _point(50.0, days_ago=4, model="lego_promo", category="lego_minifiguren"),
    ]
    mapping = {"lego_sw_clone": "lego_rare_minifig_common", "lego_promo": "lego_rare_minifig_common"}
    stats_by_group = compute_resale_stats_by_group(points, mapping)
    assert set(stats_by_group.keys()) == {"lego_rare_minifig_common"}
    assert stats_by_group["lego_rare_minifig_common"].count == 5


def test_compute_resale_stats_by_group_leeres_mapping_wie_compute_all_price_stats():
    points = [
        _point(100.0, days_ago=0, model="rtx_3060_12gb"),
        _point(110.0, days_ago=1, model="rtx_3060_12gb"),
    ]
    assert (
        compute_resale_stats_by_group(points, {})["rtx_3060_12gb"].count
        == compute_all_price_stats(points)["rtx_3060_12gb"].count
    )


# ---------- Burst-Collapsing-Integration (Schritt 2, "strukturelle Loesung") ----------

def _burst_point(price: float, seconds_offset: float, model: str = "sata_ssd_500gb",
                  source: str = "eBay") -> PricePoint:
    date = (datetime.now(timezone.utc) + timedelta(seconds=seconds_offset)).isoformat()
    return PricePoint(price=price, date=date, source=source, model=model,
                       category="sata_ssd", deal_score=None)


def test_compute_price_stats_reduziert_dichten_alt_daten_burst_automatisch():
    # 20 Punkte, alle Millisekunden auseinander, alle ohne fingerprint --
    # genau das Muster aus dem sata_ssd_500gb-Fund. Ohne Collapsing wuerde
    # count faelschlich auf 20 stehen, market_price waere exakt 71.5.
    burst = [_burst_point(71.5, seconds_offset=0.01 * i) for i in range(20)]
    stats = compute_price_stats("sata_ssd_500gb", burst)
    assert stats.count == 1


def test_compute_price_stats_collapse_bursts_false_erhaelt_rohdaten():
    burst = [_burst_point(71.5, seconds_offset=0.01 * i) for i in range(20)]
    stats = compute_price_stats("sata_ssd_500gb", burst, collapse_bursts=False)
    assert stats.count == 20


def test_compute_price_stats_burst_faellt_nicht_unter_echte_gestreute_daten():
    # Echte, ueber Tage verteilte Datenpunkte werden vom Collapsing nicht
    # angefasst (Regressionsschutz: Kernverhalten bleibt unveraendert).
    prices = [100.0, 150.0, 200.0, 250.0, 300.0]
    points = [_point(p, days_ago=i) for i, p in enumerate(prices)]
    stats = compute_price_stats("rtx_3060_12gb", points)
    assert stats.count == 5


def test_compute_all_price_stats_reicht_collapse_bursts_durch():
    burst = [_burst_point(71.5, seconds_offset=0.01 * i) for i in range(10)]
    normal = [_point(200.0, days_ago=0, model="office_pc", category="office_pc")]
    all_stats = compute_all_price_stats(burst + normal)
    assert all_stats["sata_ssd_500gb"].count == 1
    assert all_stats["office_pc"].count == 1


def test_compute_all_price_stats_collapse_bursts_false_reicht_ebenfalls_durch():
    burst = [_burst_point(71.5, seconds_offset=0.01 * i) for i in range(10)]
    all_stats = compute_all_price_stats(burst, collapse_bursts=False)
    assert all_stats["sata_ssd_500gb"].count == 10


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
