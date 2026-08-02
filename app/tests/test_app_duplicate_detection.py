"""Tests für die Anbindung von duplicate_detection.py in run_scan() (app.py),
STATUS.md Abschnitt 16, Baustein 5.

Prüft: zwei mutmaßlich identische Angebote (gleiches price_history_model,
gleicher normalisierter Titel, Preis innerhalb Toleranz) über verschiedene
Quellen/URLs hinweg im selben Scan erzeugen nur EINEN Preishistorie-Eintrag,
landen aber BEIDE unverändert in found.json (kein Verlust echter Treffer).
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
    spec = importlib.util.spec_from_file_location("app_under_test_duplicate_detection", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def test_cross_posting_erzeugt_nur_einen_price_history_eintrag():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        capture = _CaptureHandler()
        app_mod.log.addHandler(capture)

        # Dasselbe physische Angebot (identischer Titel, fast identischer
        # Preis) -- einmal auf Kleinanzeigen, einmal auf eBay, unterschiedliche
        # URLs (sonst würde bereits die bestehende seen.json-URL-Dedup greifen).
        kleinanzeigen_listings = [{
            "source": "Kleinanzeigen",
            "title": "ASUS RTX 3060 12GB ROG Strix",
            "price": 200.0,
            "url": "https://example.test/gpu-kleinanzeigen",
            "location": "Musterstadt",
            "description": "",
            "images": [],
        }]
        ebay_listings = [{
            "source": "eBay",
            "title": "ASUS RTX 3060 12GB ROG Strix",
            "price": 205.0,  # < 5% Abweichung -> gilt als Duplikat
            "url": "https://example.test/gpu-ebay",
            "location": "",
            "description": "",
            "images": [],
        }]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=kleinanzeigen_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=ebay_listings), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy", MagicMock()):
            app_mod.run_scan()

        app_mod.log.removeHandler(capture)

        # Beide Treffer landen unveraendert in found.json.
        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        urls = {e["url"] for e in found}
        assert "https://example.test/gpu-kleinanzeigen" in urls
        assert "https://example.test/gpu-ebay" in urls

        # Aber nur EIN Preishistorie-Eintrag wurde geschrieben.
        lines = app_mod.PRICE_HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1

        assert any("Duplicate-/Cross-Posting-Erkennung" in m for m in capture.messages)


def test_unterschiedliche_titel_erzeugen_zwei_price_history_eintraege():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        kleinanzeigen_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "ASUS RTX 3060 12GB ROG Strix",
                "price": 200.0,
                "url": "https://example.test/gpu-a",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
            {
                "source": "Kleinanzeigen",
                "title": "MSI RTX 3060 12GB Gaming X",
                "price": 205.0,
                "url": "https://example.test/gpu-b",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=kleinanzeigen_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy", MagicMock()):
            app_mod.run_scan()

        lines = app_mod.PRICE_HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2


def test_price_history_eintrag_enthaelt_fingerprint():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        kleinanzeigen_listings = [{
            "source": "Kleinanzeigen",
            "title": "ASUS RTX 3060 12GB ROG Strix",
            "price": 200.0,
            "url": "https://example.test/gpu-fingerprint",
            "location": "Musterstadt",
            "description": "",
            "images": [],
        }]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=kleinanzeigen_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy", MagicMock()):
            app_mod.run_scan()

        line = app_mod.PRICE_HISTORY_FILE.read_text(encoding="utf-8").splitlines()[0]
        data = json.loads(line)
        assert data["fingerprint"] == "asus rtx 3060 12gb rog strix"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
