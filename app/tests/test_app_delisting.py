"""Tests für die Delisting-Erkennung + Time-to-Sell-Anbindung in run_scan()
(app.py), STATUS.md Abschnitt 16, Baustein 6, Schritt 2.

Prüft End-to-End (mehrere echte run_scan()-Läufe): ein zuvor gematchtes
Angebot, das anschließend delisting_threshold_scans (Default 3, siehe
rules/_global.yaml) aufeinanderfolgende Scans NICHT mehr in den rohen
Suchergebnissen auftaucht, wird als delisted markiert und erzeugt genau
einen time_to_sell.jsonl-Eintrag.
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
    spec = importlib.util.spec_from_file_location("app_under_test_delisting", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_LISTING = {
    "source": "Kleinanzeigen",
    "title": "ASUS RTX 3060 12GB ROG Strix",
    "price": 200.0,
    "url": "https://example.test/delisting-1",
    "location": "Musterstadt",
    "description": "",
    "images": [],
}


def _run_scan_with(app_mod, listings):
    with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=listings), \
         patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
         patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
         patch.object(app_mod, "send_ntfy", MagicMock()):
        app_mod.run_scan()


def test_angebot_wird_nach_schwellenwert_scans_delisted_und_erzeugt_zeitpunkt():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        # Schwellenwert kommt aus der echten rules/_global.yaml
        # (presence_tracking.delisting_threshold_scans, aktuell 3).
        threshold = app_mod.load_rules(str(Path(app_mod.__file__).parent / "rules")) \
            .get("presence_tracking", {}).get("delisting_threshold_scans", 3)

        # Scan 1: Angebot taucht auf und wird gematcht (RTX 3060 -> gpu-Kategorie).
        _run_scan_with(app_mod, [_LISTING])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert len(found) == 1
        assert app_mod.TIME_TO_SELL_FILE.exists() is False

        # Folgescans: Angebot taucht NICHT mehr in den Rohergebnissen auf.
        for _ in range(threshold):
            _run_scan_with(app_mod, [])

        seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        entry = seen[_LISTING["url"]]
        assert entry["delisted"] is True
        assert entry["category"] == "gpu"
        assert entry["price_history_model"]

        assert app_mod.TIME_TO_SELL_FILE.exists()
        lines = app_mod.TIME_TO_SELL_FILE.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        point = json.loads(lines[0])
        assert point["category"] == "gpu"
        assert point["model"] == entry["price_history_model"]
        assert point["days"] >= 0

        # Weitere Scans dürfen KEINEN zweiten Datenpunkt für dasselbe,
        # bereits delistete Angebot erzeugen (siehe detect_newly_delisted()).
        _run_scan_with(app_mod, [])
        lines_after = app_mod.TIME_TO_SELL_FILE.read_text(encoding="utf-8").splitlines()
        assert len(lines_after) == 1


def test_angebot_das_weiterhin_gesehen_wird_bleibt_nicht_delisted():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])
        # Angebot taucht in jedem Folgescan weiterhin auf -> missed_scans
        # wird jedes Mal zurückgesetzt, niemals delisted.
        for _ in range(5):
            _run_scan_with(app_mod, [_LISTING])

        seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        entry = seen[_LISTING["url"]]
        assert entry["delisted"] is False
        assert entry["missed_scans"] == 0
        assert app_mod.TIME_TO_SELL_FILE.exists() is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
