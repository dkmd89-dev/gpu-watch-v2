"""Tests fuer die Resale-Price-Gruppierung in app.py (Option 2,
"Flip-Kandidaten-Logik optimieren", STATUS.md Abschnitt 33b):
_load_resale_stats_by_group() und die erweiterte _resale_prices_from_stats().

Struktur analog test_app_margin_field.py (frisch geladenes app.py-Modul
mit isoliertem DATA_DIR).
"""
import sys
import importlib.util
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_stats import PriceStats


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_resale_groups", app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _stats(model: str, resale_price: float | None) -> PriceStats:
    return PriceStats(
        model=model, count=5, min_price=10.0, max_price=50.0, mean_price=30.0,
        median_price=30.0, percentile_5=10.0, percentile_10=12.0, market_price=25.0,
        trend="unbekannt", trend_change_pct=None,
        percentile_75=45.0, estimated_resale_price=resale_price,
    )


def test_resale_prices_ohne_mapping_unveraendert_wie_vorher():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        stats_by_model = {"rtx_3060_12gb": _stats("rtx_3060_12gb", 220.0)}
        # Alte Aufrufsignatur (nur 1 Argument) muss weiterhin funktionieren.
        result = app_mod._resale_prices_from_stats(stats_by_model)
        assert result == {"rtx_3060_12gb": 220.0}


def test_resale_prices_nutzt_groebere_gruppe_wenn_gemappt():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        # lego_sw_clone hat selbst zu duenne Historie (None), die
        # gemeinsame Gruppe "lego_rare_minifig_common" hat aber genug
        # Datenpunkte fuer eine belastbare Schaetzung.
        stats_by_model = {"lego_sw_clone": _stats("lego_sw_clone", None)}
        stats_by_group = {"lego_rare_minifig_common": _stats("lego_rare_minifig_common", 38.0)}
        model_to_group = {"lego_sw_clone": "lego_rare_minifig_common"}

        result = app_mod._resale_prices_from_stats(stats_by_model, stats_by_group, model_to_group)
        assert result == {"lego_sw_clone": 38.0}


def test_resale_prices_gruppe_fehlt_liefert_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        stats_by_model = {"lego_sw_clone": _stats("lego_sw_clone", None)}
        model_to_group = {"lego_sw_clone": "lego_rare_minifig_common"}

        result = app_mod._resale_prices_from_stats(stats_by_model, {}, model_to_group)
        # leeres stats_by_group -> Fallback auf altes Verhalten (kein Mapping
        # angewendet, da "if not stats_by_resale_group" greift).
        assert result == {"lego_sw_clone": None}


def test_market_price_unveraendert_durch_resale_gruppierung():
    # Regressionsschutz: _market_prices_from_stats() nutzt weiterhin
    # ausschliesslich stats_by_model (exaktes price_history_model), nie
    # die Resale-Gruppe.
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        stats_by_model = {"lego_sw_clone": _stats("lego_sw_clone", None)}
        result = app_mod._market_prices_from_stats(stats_by_model)
        assert result == {"lego_sw_clone": 25.0}


def test_load_resale_stats_by_group_fasst_price_history_zusammen():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        from price_history import append_price_point, make_price_point

        path = Path(tmpdir) / "price_history.jsonl"
        for price in (20.0, 25.0, 30.0):
            append_price_point(path, make_price_point(price=price, source="kleinanzeigen", model="lego_sw_clone"))
        for price in (40.0, 45.0):
            append_price_point(path, make_price_point(price=price, source="kleinanzeigen", model="lego_promo"))

        mapping = {"lego_sw_clone": "lego_rare_minifig_common", "lego_promo": "lego_rare_minifig_common"}
        stats_by_group = app_mod._load_resale_stats_by_group(path, mapping)

        assert set(stats_by_group.keys()) == {"lego_rare_minifig_common"}
        assert stats_by_group["lego_rare_minifig_common"].count == 5
