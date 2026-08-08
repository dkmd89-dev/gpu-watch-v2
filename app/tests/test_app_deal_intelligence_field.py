"""Tests für die Deal-Intelligence-Feld-Verdrahtung in app.py (roadmap.md
Phase 7, Schritt 7b): found.json-Einträge müssen "deal_intelligence_label",
"deal_intelligence_emoji" und "expected_days_to_sell" enthalten.

Struktur analog test_app_manufacturer_field.py.
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.kleinanzeigen
import scrapers.ebay
import scrapers.quoka


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location(
        "app_under_test_deal_intelligence", app_path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_LISTING = {
    "source": "Kleinanzeigen",
    "title": "ASUS RTX 3060 12GB ROG Strix",
    "price": 200.0,
    "url": "https://example.test/deal-intelligence-1",
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


def test_found_json_enthaelt_deal_intelligence_felder():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert len(found) == 1
        entry = found[0]
        assert "deal_intelligence_label" in entry
        assert entry["deal_intelligence_label"] in {
            "TOP DEAL", "FLIP DEAL", "VERY GOOD DEAL", "WATCH",
        }
        assert "deal_intelligence_emoji" in entry
        assert "expected_days_to_sell" in entry


def test_expected_days_to_sell_ist_none_ohne_time_to_sell_historie():
    # Frischer Scan, keine time_to_sell.jsonl vorhanden -> fuer JEDE
    # Kategorie liegt noch keine Delisting-Historie vor (siehe
    # time_to_sell_stats.py-Docstring) -> None, kein Fehler.
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert found[0]["expected_days_to_sell"] is None


def test_deal_intelligence_label_konsistent_mit_is_top_deal_feld():
    # Regressionsschutz: das bereits bestehende is_top_deal-Feld und das
    # neue deal_intelligence_label duerfen sich nicht widersprechen --
    # is_top_deal=True MUSS deal_intelligence_label == "TOP DEAL" ergeben
    # (siehe deal_intelligence.py: TOP DEAL hat hoechste Prioritaet).
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        entry = found[0]
        if entry["is_top_deal"]:
            assert entry["deal_intelligence_label"] == "TOP DEAL"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
