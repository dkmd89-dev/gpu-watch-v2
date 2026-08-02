"""Tests für die Hersteller-Feld-Verdrahtung in app.py (Dashboard-Filter-
Folgeschritt): found.json-Einträge müssen ein "manufacturer"-Feld
enthalten, /api/status muss "manufacturer_counts" liefern.

Struktur analog test_app_notification_gate.py (frisch geladenes app.py-
Modul mit isoliertem DATA_DIR, gemockte Scraper).
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.kleinanzeigen
import scrapers.ebay


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_found_json_enthaelt_manufacturer_feld_bei_erkannter_marke():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "Dell OptiPlex 7040 i5-8500 16GB RAM 512GB SSD Tower",
                "price": 150.0,
                "url": "https://example.test/dell-1",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

            found_data = json.loads((Path(tmpdir) / "found.json").read_text())
            assert len(found_data) == 1
            assert found_data[0]["manufacturer"] == "Dell"


def test_found_json_manufacturer_none_ohne_erkennbare_marke():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "Office PC i5-8500 16GB RAM 512GB SSD Tower",
                "price": 150.0,
                "url": "https://example.test/keine-marke-1",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

            found_data = json.loads((Path(tmpdir) / "found.json").read_text())
            assert len(found_data) == 1
            assert found_data[0]["manufacturer"] is None


def test_api_status_liefert_manufacturer_counts():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "Dell OptiPlex 7040 i5-8500 16GB RAM 512GB SSD Tower",
                "price": 150.0,
                "url": "https://example.test/dell-2",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
            {
                "source": "Kleinanzeigen",
                "title": "Lenovo ThinkCentre M920 i5-8500 16GB RAM 512GB SSD Tower",
                "price": 160.0,
                "url": "https://example.test/lenovo-1",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
            {
                "source": "Kleinanzeigen",
                "title": "Office PC i5-8500 16GB RAM 512GB SSD Tower",
                "price": 150.0,
                "url": "https://example.test/keine-marke-2",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

            client = app_mod.app.test_client()
            resp = client.get("/api/status")
            data = resp.get_json()

            assert data["manufacturer_counts"]["Dell"] == 1
            assert data["manufacturer_counts"]["Lenovo"] == 1
            assert data["manufacturer_counts"]["unbekannt"] == 1


def test_api_status_manufacturer_counts_robust_bei_fehlendem_feld():
    # Alte found.json-Eintraege (vor diesem Schritt) haben kein
    # "manufacturer"-Feld -- /api/status darf dabei nicht crashen und muss
    # sie unter "unbekannt" gruppieren (kein KeyError).
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        legacy_entry = {
            "title": "RTX 3060 12GB", "price": 200.0, "url": "https://example.test/legacy-1",
            "location": "Musterstadt", "source": "kleinanzeigen", "rule": "RTX 3060 12GB",
            "category": "gpu", "deal_score": 70, "deal_stars": "★★★☆☆",
            "is_top_deal": False, "top_deal_discount_pct": None,
            "found_at": "2026-01-01T00:00:00+00:00",
            # bewusst KEIN "manufacturer"-Schluessel
        }
        (Path(tmpdir) / "found.json").write_text(json.dumps([legacy_entry]))

        client = app_mod.app.test_client()
        resp = client.get("/api/status")
        data = resp.get_json()

        assert data["manufacturer_counts"]["unbekannt"] == 1


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
