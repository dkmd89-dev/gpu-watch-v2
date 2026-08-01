"""Tests für _stable_item_url() im eBay-Scraper.

Bugfix-Hintergrund: itemWebUrl aus der eBay Browse API enthält volatile
Tracking-Query-Parameter (hash/amdata), die für dasselbe physische Angebot
zwischen API-Aufrufen variieren können. Da app.py ausschließlich über
item["url"] dedupliziert (seen.json), führte das dazu, dass dasselbe
eBay-Angebot bei jedem Scan erneut als "neu" galt -- sichtbar als massenhafte
Preis-Wiederholungen in price_history.jsonl (siehe STATUS.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers.ebay import _stable_item_url, search_ebay


def test_entfernt_tracking_query_parameter():
    roh = "https://www.ebay.de/itm/1234567890?hash=item1c2d3e4f5g:g:AbcAAOSw~~~"
    assert _stable_item_url(roh) == "https://www.ebay.de/itm/1234567890"


def test_dasselbe_item_liefert_bei_unterschiedlichem_tracking_dieselbe_url():
    # Kernfall des Bugs: zwei API-Antworten fuer DASSELBE physische Angebot
    # mit unterschiedlichen Tracking-Werten muessen auf dieselbe URL normalisiert
    # werden, sonst schlaegt die seen.json-Dedup in app.py fehl.
    url_scan_1 = "https://www.ebay.de/itm/1234567890?hash=aaa&amdata=xxx"
    url_scan_2 = "https://www.ebay.de/itm/1234567890?hash=bbb&amdata=yyy&_trkparms=zzz"
    assert _stable_item_url(url_scan_1) == _stable_item_url(url_scan_2)


def test_url_ohne_query_bleibt_unveraendert():
    assert _stable_item_url("https://www.ebay.de/itm/1234567890") == "https://www.ebay.de/itm/1234567890"


def test_leerer_string_bleibt_leer():
    assert _stable_item_url("") == ""


def test_unterschiedliche_items_bleiben_unterschiedlich():
    a = _stable_item_url("https://www.ebay.de/itm/1111111111?hash=aaa")
    b = _stable_item_url("https://www.ebay.de/itm/2222222222?hash=aaa")
    assert a != b


def test_search_ebay_nutzt_normalisierte_url(monkeypatch):
    # End-to-End: search_ebay() muss die Normalisierung tatsaechlich anwenden,
    # nicht nur die isolierte Hilfsfunktion.
    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"access_token": "fake-token"}

    class _FakeSearchResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "itemSummaries": [
                    {
                        "title": "Gaming PC RTX 3060",
                        "price": {"value": "450.0"},
                        "itemWebUrl": "https://www.ebay.de/itm/1234567890?hash=zzz&amdata=abc",
                        "itemLocation": {"city": "Musterstadt"},
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        return _FakeResponse()

    def fake_get(*args, **kwargs):
        return _FakeSearchResponse()

    monkeypatch.setenv("EBAY_CLIENT_ID", "id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "secret")
    monkeypatch.setattr("scrapers.ebay.requests.post", fake_post)
    monkeypatch.setattr("scrapers.ebay.requests.get", fake_get)

    results = search_ebay(["Gaming PC"], max_price=999, plz="76477")
    assert len(results) == 1
    assert results[0]["url"] == "https://www.ebay.de/itm/1234567890"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
