"""Tests für die Dashboard-Anbindung des Cross-Platform-Preisvergleichs
(Baustein 4, Schritt 2): neue Route /api/cross-platform + Panel im
Template. Struktur analog test_app_time_to_sell_api.py.
"""
import sys
import os
import importlib.util
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_history import PricePoint, append_price_point


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_cp_api", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _point(price: float, source: str, model: str) -> PricePoint:
    return PricePoint(
        price=price, date="2026-08-03T00:00:00+00:00", source=source, model=model,
        category="gpu", deal_score=80,
    )


def test_api_cross_platform_leeres_dict_ohne_datei():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        client = app_mod.app.test_client()
        resp = client.get("/api/cross-platform")

        assert resp.status_code == 200
        assert resp.get_json() == {}


def test_api_cross_platform_liefert_statistik_je_modell():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        points = [
            _point(100.0, "kleinanzeigen", "rtx_3060_12gb"),
            _point(150.0, "ebay", "rtx_3060_12gb"),
            # nur eine Quelle -> darf NICHT im Ergebnis auftauchen
            _point(50.0, "kleinanzeigen", "rtx_2060"),
        ]
        for p in points:
            append_price_point(app_mod.PRICE_HISTORY_FILE, p)

        client = app_mod.app.test_client()
        resp = client.get("/api/cross-platform")
        data = resp.get_json()

        assert set(data.keys()) == {"rtx_3060_12gb"}
        stats = data["rtx_3060_12gb"]
        assert stats["cheapest_source"] == "kleinanzeigen"
        assert stats["priciest_source"] == "ebay"
        assert stats["by_source"]["kleinanzeigen"]["mean_price"] == 100.0
        assert stats["by_source"]["ebay"]["mean_price"] == 150.0
        assert round(stats["spread_pct"], 2) == 50.0


def test_dashboard_html_enthaelt_cross_platform_panel():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        client = app_mod.app.test_client()
        resp = client.get("/")

        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'id="cpPanel"' in html
        assert "Cross-Platform-Preisvergleich" in html


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
