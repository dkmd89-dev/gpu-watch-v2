"""Tests für den Quoka-Scraper.

Die HTML-Fixture (tests/fixtures/quoka_search_rtx_3060.html) ist eine reale,
von Robin bereitgestellte Quoka-Suchergebnisseite ("RTX 3060", 12 Treffer,
per `search-result-total-items`-Meta-Tag bestätigt). Kein Netzwerkzugriff
auf quoka.de in dieser Umgebung möglich/nötig -- Verifikation erfolgt
offline gegen diese Fixture, analog zu test_scraper_kleinanzeigen.py und
test_scraper_ebay.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers.quoka import _clean_location, _price_to_float, search_quoka

FIXTURE = Path(__file__).parent / "fixtures" / "quoka_search_rtx_3060.html"


# --- _price_to_float() -------------------------------------------------

def test_price_to_float_einfacher_preis():
    assert _price_to_float("155 EUR") == 155.0


def test_price_to_float_mit_tausenderpunkt():
    assert _price_to_float("1.250 EUR") == 1250.0


def test_price_to_float_dezimalpunkt_wird_nicht_als_tausenderpunkt_missverstanden():
    # Realer Fall aus der Fixture (Rabatt-Preisfeld ".new-price"): "529.0 EUR"
    # bedeutet 529 Euro, NICHT 5290 -- der Punkt hat hier nur eine
    # Nachkommastelle, ist also kein Tausendertrenner.
    assert _price_to_float("529.0 EUR") == 529.0


def test_price_to_float_mit_vb_zusatz():
    # Verhandlungsbasis -- Preis muss trotz Zusatztext erkannt werden.
    assert _price_to_float("500 EUR VB") == 500.0


def test_price_to_float_ohne_treffer_liefert_none():
    assert _price_to_float("Preis auf Anfrage") is None


def test_price_to_float_leerer_string_liefert_none():
    assert _price_to_float("") is None


# --- _clean_location() --------------------------------------------------

def test_clean_location_kollabiert_mehrfach_whitespace():
    roh = "\n                                        Booßen, Frankfurt (Oder), Brandenburg, 15232\n                                    "
    assert _clean_location(roh) == "Booßen, Frankfurt (Oder), Brandenburg, 15232"


def test_clean_location_leerer_string_bleibt_leer():
    assert _clean_location("") == ""


# --- search_quoka() end-to-end gegen die reale Fixture -------------------

def test_search_quoka_filtert_titel_ohne_suchbegriff_kernwort(monkeypatch):
    # Von den 12 Karten in der Fixture nennen 2 ("Laptop Asus ROG Strix G17",
    # "Dell Inspiron 5680 Gamer PC") weder "rtx" noch "3060" im TITEL (nur
    # ggf. in der Beschreibung) -- das Sicherheitsnetz (analog
    # kleinanzeigen.py) filtert sie korrekt heraus, da sonst themenfremde
    # Treffer bei einer zu groben Quoka-Volltextsuche durchrutschen könnten.
    html = FIXTURE.read_text(encoding="utf-8")

    class _FakeResponse:
        text = html

        def raise_for_status(self):
            pass

    def fake_get(*args, **kwargs):
        return _FakeResponse()

    monkeypatch.setattr("scrapers.quoka.requests.get", fake_get)
    monkeypatch.setattr("scrapers.quoka.time.sleep", lambda *_: None)

    results = search_quoka(["RTX 3060"], plz="76477", radius_km=50, max_price=999999)

    assert len(results) == 10
    titles = {r["title"] for r in results}
    assert "Laptop Asus ROG Strix G17" not in titles
    assert "Dell Inspiron 5680 Gamer PC" not in titles


def test_search_quoka_erstes_listing_hat_erwartete_felder(monkeypatch):
    html = FIXTURE.read_text(encoding="utf-8")

    class _FakeResponse:
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr("scrapers.quoka.requests.get", lambda *a, **kw: _FakeResponse())
    monkeypatch.setattr("scrapers.quoka.time.sleep", lambda *_: None)

    results = search_quoka(["RTX 3060"], plz="76477", radius_km=50, max_price=999999)
    first = results[0]

    assert first["source"] == "Quoka"
    assert first["title"] == "geforce RTX 3060 Ti 8GB"
    assert first["price"] == 155.0
    assert first["url"] == (
        "https://www.quoka.de/anzeigen/elektronik/computer/grafikkarten/"
        "anzeige/geforce-rtx-3060-ti-8gb/03e711ig8fdd7e462d4h4e26f92d4e4e.html"
    )
    assert first["location"] == "Booßen, Frankfurt (Oder), Brandenburg, 15232"
    assert "Inno3D" in first["description"]


def test_search_quoka_alle_preise_korrekt_geparst(monkeypatch):
    # Regressionsnetz gegen die konkreten Preise der 10 vom Sicherheitsnetz
    # durchgelassenen Karten (siehe Analyse-Schritt; 2 der 12 Karten in der
    # Fixture werden gefiltert, da "rtx"/"3060" nicht im Titel steht).
    # Karte "Gaming PC Komplettset RTX 3060 + Monitor + Zubehörr" ist ein
    # Rabatt-Angebot (".new-price"/".old-price") -- erwartet wird der
    # AKTUELLE Preis 529.0, nicht der durchgestrichene Ursprungspreis 650.0.
    html = FIXTURE.read_text(encoding="utf-8")

    class _FakeResponse:
        text = html

        def raise_for_status(self):
            pass

    monkeypatch.setattr("scrapers.quoka.requests.get", lambda *a, **kw: _FakeResponse())
    monkeypatch.setattr("scrapers.quoka.time.sleep", lambda *_: None)

    results = search_quoka(["RTX 3060"], plz="76477", radius_km=50, max_price=999999)
    prices = [r["price"] for r in results]

    erwartet = [155.0, 115.0, 165.0, 750.0, 529.0, 469.0, 650.0, 255.0, 500.0, 390.0]
    assert prices == erwartet


def test_search_quoka_request_fehler_wird_abgefangen(monkeypatch):
    import requests

    def fake_get(*args, **kwargs):
        raise requests.RequestException("Netzwerkfehler")

    monkeypatch.setattr("scrapers.quoka.requests.get", fake_get)
    monkeypatch.setattr("scrapers.quoka.time.sleep", lambda *_: None)

    results = search_quoka(["RTX 3060"], plz="76477", radius_km=50, max_price=999999)
    assert results == []


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
