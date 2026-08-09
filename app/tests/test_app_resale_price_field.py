"""Tests für die found.json-/API-/Dashboard-Verdrahtung von
estimated_resale_price (Auftrag "Angebotswert + Marktwert + geschaetzter
Verkaufspreis auf Deal-Karten"): das bereits in matcher.evaluate()
berechnete Feld muss additiv in found.json landen, ueber /api/found
verfuegbar sein und auf der Deal-Karte (Server-Jinja) korrekt inkl.
Fallback gerendert werden -- ohne bestehende Felder (deal_score, margin,
market_price, ...) zu veraendern.

Struktur analog test_app_margin_field.py / test_app_cross_platform_api.py.
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


def _load_app_module(data_dir: str, mod_name: str = "app_under_test_resale"):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location(mod_name, app_path)
    mod = importlib.util.module_from_spec(spec)
    # Bugfix: Modul VOR exec_module in sys.modules registrieren -- siehe
    # test_app_margin_field.py fuer die vollstaendige Begruendung.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _seed_price_history(tmpdir: str, model: str, prices: list[float]) -> None:
    """Siehe test_app_margin_field.py::_seed_price_history -- jeder Punkt
    bekommt einen eigenen fingerprint, damit burst_cleanup.py die Punkte
    nicht faelschlich zu einem einzigen Datenpunkt kollabiert."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from price_history import append_price_point, make_price_point

    path = Path(tmpdir) / "price_history.jsonl"
    for i, price in enumerate(prices):
        append_price_point(
            path,
            make_price_point(
                price=price, source="kleinanzeigen", model=model,
                fingerprint=f"{model}-resaletest-{i}",
            ),
        )


def _fake_listing(url_suffix: str, price: float = 100.0) -> dict:
    return {
        "source": "Kleinanzeigen",
        "title": "ASUS RTX 3060 12GB Grafikkarte",
        "price": price,
        "url": f"https://example.test/rtx3060-{url_suffix}",
        "location": "Musterstadt",
        "description": "",
        "images": [],
    }


def test_found_json_enthaelt_estimated_resale_price_bei_vorhandener_preishistorie():
    """1. Vollstaendige Daten -> alle Werte (inkl. estimated_resale_price)
    landen in found.json, bestehende Felder (margin, deal_score) bleiben
    unveraendert vorhanden."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _seed_price_history(tmpdir, "rtx_3060_12gb", [250.0] * 5)
        app_mod = _load_app_module(tmpdir, "app_under_test_resale_full")

        fake_listings = [_fake_listing("vollstaendig")]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

            found_data = json.loads((Path(tmpdir) / "found.json").read_text())
            assert len(found_data) == 1
            entry = found_data[0]

            # Neues Feld vorhanden und korrekt (identisch zur Grundlage von
            # estimated_margin_eur -- keine zweite Berechnung).
            assert entry["estimated_resale_price"] is not None
            assert entry["estimated_resale_price"] == 250.0

            # Bestehende Felder unveraendert vorhanden (Regressionsschutz).
            assert entry["estimated_margin_eur"] is not None
            assert entry["estimated_margin_pct"] is not None
            assert entry["deal_score"] is not None
            assert "deal_stars" in entry


def test_found_json_estimated_resale_price_none_ohne_preishistorie():
    """2. Keine Preishistorie -> sauberer None-Fallback, kein erfundener
    Wert. 3. Keine Marge berechenbar -> kein falscher Gewinnwert
    (bestehendes Verhalten bleibt erhalten)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_resale_none")

        fake_listings = [_fake_listing("ohne-historie")]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

            found_data = json.loads((Path(tmpdir) / "found.json").read_text())
            assert len(found_data) == 1
            entry = found_data[0]

            assert entry["estimated_resale_price"] is None
            # Kein falscher/erfundener Gewinnwert, wenn resale_price fehlt.
            assert entry["estimated_margin_eur"] is None
            assert entry["estimated_margin_pct"] is None


def test_api_found_liefert_estimated_resale_price_1_zu_1():
    """5. /api/found liefert das vorhandene Resale-Feld korrekt (reines
    Durchreichen aus found.json, keine erneute Berechnung in der API)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _seed_price_history(tmpdir, "rtx_3060_12gb", [250.0] * 5)
        app_mod = _load_app_module(tmpdir, "app_under_test_resale_api")

        fake_listings = [_fake_listing("api")]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

        client = app_mod.app.test_client()
        resp = client.get("/api/found")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["estimated_resale_price"] == 250.0


def test_dashboard_zeigt_verkaufspreis_zeile_bei_vorhandenem_wert():
    """1. Vollstaendige Daten -> Verkaufspreis-Zeile mit Wert auf der
    Deal-Karte (Server-Jinja) sichtbar."""
    with tempfile.TemporaryDirectory() as tmpdir:
        _seed_price_history(tmpdir, "rtx_3060_12gb", [250.0] * 5)
        app_mod = _load_app_module(tmpdir, "app_under_test_resale_dashboard_full")

        fake_listings = [_fake_listing("dashboard-voll")]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

        client = app_mod.app.test_client()
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        assert "Verkaufspreis geschätzt: 250 €" in html
        # Bestehende Marge-Darstellung bleibt unveraendert vorhanden.
        assert "geschätzte Marge" in html
        # Deal-Score-Zeile neu vorhanden.
        assert "Deal Score:" in html


def test_dashboard_zeigt_fallback_ohne_estimated_resale_price():
    """2. Kein estimated_resale_price -> Dashboard zeigt "nicht verfügbar"
    statt einen erfundenen Wert oder die Zeile komplett auszublenden. 4.
    Bestehende Deal-Karte (Titel, Preis, Meta) bleibt funktionsfaehig."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_resale_dashboard_none")

        fake_listings = [_fake_listing("dashboard-fallback")]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy"):

            app_mod.run_scan()

        client = app_mod.app.test_client()
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)

        assert "Verkaufspreis geschätzt: nicht verfügbar" in html
        # Grundfunktion der Deal-Karte bleibt intakt.
        assert "ASUS RTX 3060 12GB Grafikkarte" in html
        assert "100 €" in html
