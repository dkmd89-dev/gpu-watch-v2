"""Tests für die Margen-Feld-Verdrahtung in app.py (Reselling-/Arbitrage-
Konzept, STATUS.md Abschnitt 16, Punkt b): found.json-Einträge müssen
"estimated_margin_eur"/"estimated_margin_pct" enthalten, sobald für das
jeweilige price_history_model bereits eine Preishistorie vorliegt.

Struktur analog test_app_manufacturer_field.py (frisch geladenes app.py-
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
import scrapers.quoka


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test", app_path)
    mod = importlib.util.module_from_spec(spec)
    # Bugfix: Modul VOR exec_module in sys.modules registrieren --
    # sonst findet Flask(__name__) intern keinen Eintrag unter dem
    # Modulnamen und faellt auf os.getcwd() als root_path zurueck
    # (statt auf den echten app.py-Verzeichnispfad). Funktioniert dann nur
    # zufaellig, wenn pytest aus app/ heraus gestartet wird -- schlaegt mit
    # "TemplateNotFound: index.html" fehl, sobald z.B. aus dem Projekt-Root
    # gestartet wird (siehe Robins echter pytest-Lauf, 03.08.).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _seed_price_history(tmpdir: str, model: str, prices: list[float]) -> None:
    """Schreibt vorab PricePoints in price_history.jsonl, damit
    price_stats.compute_price_stats() beim naechsten run_scan() bereits
    einen market_price fuer `model` berechnen kann (mindestens 5 Punkte,
    siehe _MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE in price_stats.py).
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from price_history import append_price_point, make_price_point

    path = Path(tmpdir) / "price_history.jsonl"
    for price in prices:
        append_price_point(path, make_price_point(price=price, source="kleinanzeigen", model=model))


def test_found_json_enthaelt_margin_bei_vorhandener_preishistorie():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 5 identische Referenzpunkte -> market_price == 250.0 (siehe
        # price_stats._market_price(): getrimmter Mittelwert p10-p90).
        _seed_price_history(tmpdir, "rtx_3060_12gb", [250.0] * 5)
        app_mod = _load_app_module(tmpdir)

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "ASUS RTX 3060 12GB Grafikkarte",
                "price": 100.0,
                "url": "https://example.test/rtx3060-margin",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
                 patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

            found_data = json.loads((Path(tmpdir) / "found.json").read_text())
            assert len(found_data) == 1
            entry = found_data[0]
            assert entry["estimated_margin_eur"] is not None
            assert entry["estimated_margin_pct"] is not None
            # market_price=250, fees aus rules/_global.yaml (platform 10%,
            # payment 2.5%, shipping 6, packaging 1.5):
            # fees_total = 250*0.10 + 250*0.025 + 6 + 1.5 = 38.75
            # margin_abs = 250 - 100 - 38.75 = 111.25
            assert entry["estimated_margin_eur"] == 111.25
            assert entry["estimated_margin_pct"] == 111.2


def test_found_json_margin_none_ohne_preishistorie():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "ASUS RTX 3060 12GB Grafikkarte",
                "price": 100.0,
                "url": "https://example.test/rtx3060-ohne-historie",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
                 patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

            found_data = json.loads((Path(tmpdir) / "found.json").read_text())
            assert len(found_data) == 1
            assert found_data[0]["estimated_margin_eur"] is None
            assert found_data[0]["estimated_margin_pct"] is None
