"""Tests für die Part-Out-Feld-Verdrahtung in app.py (GPU-Part-Out-
Erkennung, STATUS.md Abschnitt 16, Baustein 3): found.json-Einträge
müssen "is_part_out_candidate"/"part_out_gpu_value"/"part_out_ratio_pct"
enthalten, korrekt gesetzt je nachdem, ob der GPU-Marktwert einen
Großteil des PC-Preises ausmacht.

Hintergrund: Die Badge-Anzeige (🧩, app.py + templates/index.html) war
bereits vollständig implementiert (siehe STATUS.md-Log), aber -- anders
als bei margin/negotiation (test_app_margin_field.py/test_app_
negotiation_field.py) -- fehlte bislang ein dedizierter App-Level-Test,
der das Feld end-to-end über einen echten run_scan() verifiziert
(nur test_matcher_part_out.py auf evaluate()-Ebene vorhanden). Diese
Lücke wird hiermit geschlossen; STATUS.md dokumentiert die Badge-
Anzeige nachträglich (war im Code, aber nicht im Log erfasst).

Struktur analog test_app_margin_field.py (Preishistorie vorab seeden,
frisch geladenes app.py-Modul mit isoliertem DATA_DIR, gemockte
Scraper). Nutzt die echte rules/gaming_pc.yaml + rules/gpu.yaml +
rules/mappings/component_values.yaml (max_price "Top-Deal"=300,
"Okay"=450 nach Kalibrierung, siehe STATUS.md Abschnitt 15).
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

GAMING_PC_TITLE = "Gaming PC Ryzen 5 3600 16GB DDR4 RTX 3060 Tower"


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_part_out", app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed_price_history(tmpdir: str, model: str, prices: list[float]) -> None:
    """Analog test_app_margin_field.py::_seed_price_history() -- mindestens
    5 Punkte, damit price_stats.compute_price_stats() einen market_price
    liefert (siehe _MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE)."""
    from price_history import append_price_point, make_price_point

    path = Path(tmpdir) / "price_history.jsonl"
    for price in prices:
        append_price_point(path, make_price_point(price=price, source="kleinanzeigen", model=model))


def _run_scan_for_listing(tmpdir: str, price: float, title: str = GAMING_PC_TITLE):
    app_mod = _load_app_module(tmpdir)
    fake_listings = [
        {
            "source": "Kleinanzeigen",
            "title": title,
            "price": price,
            "url": f"https://example.test/gaming-pc-part-out-{price}",
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
    return json.loads((Path(tmpdir) / "found.json").read_text())


def test_found_json_is_part_out_candidate_true_bei_hohem_gpu_wert_anteil():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 5 identische Referenzpunkte -> market_price == 220.0 fuer die
        # verbaute RTX 3060 12GB (analog test_matcher_part_out.py).
        _seed_price_history(tmpdir, "rtx_3060_12gb", [220.0] * 5)

        found_data = _run_scan_for_listing(tmpdir, 250.0)  # 220/250 = 88% >= 70%

        assert len(found_data) == 1
        entry = found_data[0]
        assert entry["is_part_out_candidate"] is True
        assert entry["part_out_gpu_value"] == 220.0
        assert entry["part_out_ratio_pct"] == 88.0


def test_found_json_is_part_out_candidate_false_unter_schwelle():
    with tempfile.TemporaryDirectory() as tmpdir:
        _seed_price_history(tmpdir, "rtx_3060_12gb", [220.0] * 5)

        found_data = _run_scan_for_listing(tmpdir, 400.0)  # 220/400 = 55% < 70%

        assert len(found_data) == 1
        entry = found_data[0]
        assert entry["is_part_out_candidate"] is False
        assert entry["part_out_ratio_pct"] == 55.0


def test_found_json_part_out_felder_none_ohne_preishistorie():
    with tempfile.TemporaryDirectory() as tmpdir:
        found_data = _run_scan_for_listing(tmpdir, 250.0)

        assert len(found_data) == 1
        entry = found_data[0]
        assert entry["is_part_out_candidate"] is False
        assert entry["part_out_gpu_value"] is None
        assert entry["part_out_ratio_pct"] is None


def test_dashboard_html_zeigt_part_out_badge_bei_kandidat():
    with tempfile.TemporaryDirectory() as tmpdir:
        _seed_price_history(tmpdir, "rtx_3060_12gb", [220.0] * 5)
        app_mod = _load_app_module(tmpdir)

        fake_listings = [{
            "source": "Kleinanzeigen",
            "title": GAMING_PC_TITLE,
            "price": 250.0,
            "url": "https://example.test/gaming-pc-part-out-badge",
            "location": "Musterstadt",
            "description": "",
            "images": [],
        }]
        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):
            app_mod.run_scan()

        client = app_mod.app.test_client()
        resp = client.get("/")

        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "badge part-out" in html
        assert "Part-Out-Kandidat" in html


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
