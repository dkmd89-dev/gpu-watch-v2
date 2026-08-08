"""Tests für die Datenqualitäts-Verdrahtung in app.py::run_scan()
(roadmap.md Phase 10, Schritt 10b): am Scan-Ende müssen die
data_quality-Prüfungen tatsächlich aufgerufen und geloggt werden.

Struktur analog test_app_duplicate_detection.py.
"""
import sys
import os
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
    spec = importlib.util.spec_from_file_location(
        "app_under_test_data_quality", app_path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _run_scan_with(app_mod, listings):
    with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=listings), \
         patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
         patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
         patch.object(app_mod, "send_ntfy", MagicMock()):
        app_mod.run_scan()


def test_zero_match_warnung_wird_bei_ausreichend_scrape_volumen_geloggt():
    # roadmap.md-Beispiel: viele Angebote gescrapt, aber (fuer die
    # angefragten, nicht matchenden Titel) keine Treffer in einer
    # bekannten Kategorie -> Warnung wird tatsaechlich geloggt.
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        capture = _CaptureHandler()
        app_mod.log.addHandler(capture)

        # DEFAULT_MIN_SCRAPED_FOR_ZERO_MATCH_WARNING (50) Listings, die auf
        # keine Kategorie passen (voellig generischer Titel ohne jede
        # erkennbare Hardware) -> 0 Treffer in ALLEN konfigurierten
        # Kategorien bei ausreichendem Scrape-Volumen.
        listings = [
            {
                "source": "Kleinanzeigen",
                "title": f"Irgendein generischer Artikel Nr. {i}",
                "price": 10.0,
                "url": f"https://example.test/zero-match-{i}",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            }
            for i in range(60)
        ]

        _run_scan_with(app_mod, listings)

        app_mod.log.removeHandler(capture)

        assert any("Datenqualität [zero_match_category]" in m for m in capture.messages)


def test_keine_datenqualitaetswarnung_bei_kleinem_scan():
    # Unter der Mindest-Scrape-Schwelle -> keine zero_match-Warnung, auch
    # wenn 0 Treffer erzielt wurden (siehe check_zero_match_categories()).
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        capture = _CaptureHandler()
        app_mod.log.addHandler(capture)

        listings = [{
            "source": "Kleinanzeigen",
            "title": "Irgendein generischer Artikel",
            "price": 10.0,
            "url": "https://example.test/zero-match-small",
            "location": "Musterstadt",
            "description": "",
            "images": [],
        }]

        _run_scan_with(app_mod, listings)

        app_mod.log.removeHandler(capture)

        assert not any("Datenqualität [zero_match_category]" in m for m in capture.messages)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
