"""Tests für die negotiation_candidate-Feld-Verdrahtung in app.py
(Verhandlungs-Assistent, STATUS.md Abschnitt 16, Punkt 7): found.json-
Einträge müssen "negotiation_candidate" enthalten, korrekt gesetzt je
nachdem, ob ein Match nur dank der negotiation_*-Toleranz zustande kam.

Struktur analog test_app_margin_field.py (frisch geladenes app.py-Modul
mit isoliertem DATA_DIR, gemockte Scraper). Nutzt die echte rules/gpu.yaml
(Regel "RTX 3060 12GB ★ Top-Deal": max_price=220, negotiation_tolerance_pct
=15.0 -> Toleranzgrenze 253€, negotiation_min_score=70 auf
hardware_qualitaet, Top-Deal-Basis-Score=85).
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


def _run_scan_for_listing(tmpdir: str, price: float):
    app_mod = _load_app_module(tmpdir)
    fake_listings = [
        {
            "source": "Kleinanzeigen",
            "title": "RTX 3060 12GB Grafikkarte",
            "price": price,
            "url": f"https://example.test/rtx3060-negotiation-{price}",
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


def test_found_json_negotiation_candidate_true_bei_toleranz_und_score():
    with tempfile.TemporaryDirectory() as tmpdir:
        found_data = _run_scan_for_listing(tmpdir, 240.0)  # > 220, <= 253
        assert len(found_data) == 1
        assert found_data[0]["negotiation_candidate"] is True


def test_found_json_negotiation_candidate_false_bei_regulaerem_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        found_data = _run_scan_for_listing(tmpdir, 200.0)  # <= 220
        assert len(found_data) == 1
        assert found_data[0]["negotiation_candidate"] is False
