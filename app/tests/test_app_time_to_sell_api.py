"""Tests für die Dashboard-Anbindung der Time-to-Sell-Statistik
(Baustein 6, Schritt 4): neue Route /api/time-to-sell + Panel im
Template. Struktur analog test_app_manufacturer_field.py.
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from time_to_sell import TimeToSellPoint, append_time_to_sell_point


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_tts_api", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_api_time_to_sell_leeres_dict_ohne_datei():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        client = app_mod.app.test_client()
        resp = client.get("/api/time-to-sell")

        assert resp.status_code == 200
        assert resp.get_json() == {}


def test_api_time_to_sell_liefert_statistik_je_kategorie():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        points = [
            TimeToSellPoint(days=1.0, first_seen="a", last_seen="b", model="m1", category="gpu", detected_at="d"),
            TimeToSellPoint(days=3.0, first_seen="c", last_seen="d", model="m2", category="gpu", detected_at="d"),
            TimeToSellPoint(days=10.0, first_seen="e", last_seen="f", model="m3", category="office_pc", detected_at="d"),
        ]
        for p in points:
            append_time_to_sell_point(app_mod.TIME_TO_SELL_FILE, p)

        client = app_mod.app.test_client()
        resp = client.get("/api/time-to-sell")
        data = resp.get_json()

        assert data["gpu"]["count"] == 2
        assert data["gpu"]["median_days"] == 2.0
        assert data["gpu"]["mean_days"] == 2.0
        assert data["office_pc"]["count"] == 1
        assert data["office_pc"]["median_days"] == 10.0


def test_dashboard_html_enthaelt_time_to_sell_panel():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        client = app_mod.app.test_client()
        resp = client.get("/")

        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'id="ttsPanel"' in html
        assert "Verweildauer (Time-to-Sell)" in html


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
