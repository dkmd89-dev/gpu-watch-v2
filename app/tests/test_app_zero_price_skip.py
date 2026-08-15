"""Test für den Preis-Mindestbetrag-Fix in run_scan() (app.py).

Hintergrund (Nutzer-Meldung 2026-08-15, GPU-Preis-Diagnose): der
Quoka-Scraper lieferte vereinzelt einen geparsten Preis von exakt 0.0
statt None (5 Punkte in price_history.jsonl, alle source="Quoka") --
ein Scraper-seitiger Preis-Parsing-Defekt, kein echtes 0€-Angebot.
run_scan() überspringt Items mit price=None bereits (Sicherheitsnetz
gegen Parsing-Fehler) -- dieser Test prüft die Erweiterung auf
price<=0, analog zum bestehenden None-Check.
"""
import sys
import os
import json
import logging
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.kleinanzeigen
import scrapers.ebay
import scrapers.quoka


def _load_app_module(data_dir: str):
    logging.root.handlers.clear()
    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_zero_price", app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_scan_with(app_mod, listings):
    with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=listings), \
         patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
         patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
         patch.object(app_mod, "send_ntfy", MagicMock()):
        app_mod.run_scan()


def _listing(url: str, price) -> dict:
    return {
        "source": "Quoka",
        "title": "ZOTAC Gaming GeForce RTX 4060 Spider-Man Edition OC 8GB GDDR6",
        "price": price,
        "url": url,
        "location": "Musterstadt",
        "description": "",
        "images": [],
    }


def test_null_preis_angebot_wird_uebersprungen():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        _run_scan_with(app_mod, [_listing("https://example.test/zero-price-1", 0.0)])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert found == []
        assert not app_mod.PRICE_HISTORY_FILE.exists() or \
            app_mod.PRICE_HISTORY_FILE.read_text(encoding="utf-8").strip() == ""


def test_negativer_preis_wird_uebersprungen():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        _run_scan_with(app_mod, [_listing("https://example.test/negative-price-1", -5.0)])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert found == []


def test_regulaerer_positiver_preis_matcht_weiterhin():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        _run_scan_with(app_mod, [_listing("https://example.test/valid-price-1", 240.0)])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert len(found) == 1
        assert found[0]["price"] == 240.0
