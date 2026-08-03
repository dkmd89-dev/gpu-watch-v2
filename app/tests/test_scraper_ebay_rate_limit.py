"""Tests für das Rate-Limit-/Retry-/Circuit-Breaker-Verhalten in scrapers/ebay.py.

Bugfix-Hintergrund (siehe gpu_watch.log, 2026-08-03, STATUS.md Abschnitt 19+20):
search_ebay() feuerte urspruenglich alle Suchbegriffe ohne jede Pause
hintereinander an die eBay Browse API -- dadurch lieferte JEDER Request "429
Too Many Requests". Pause + Retry-mit-Backoff (Abschnitt 19) behoben das fuer
transientes Sekunden-Throttling, aber in der Praxis blieb eBay laenger
anhaltend blockiert (73/74 Suchbegriffe scheiterten trotz Retry). Der
Circuit-Breaker (Abschnitt 20) bricht in diesem Fall den Rest des Scans fuer
eBay ab, statt jeden Suchbegriff einzeln mit vollem Retry durchzuprobieren.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.ebay as ebay_mod
from scrapers.ebay import search_ebay


class _FakeTokenResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"access_token": "fake-token"}


class _FakeResponse:
    """Konfigurierbarer Fake für requests.Response (status_code/headers/json)."""

    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json_data = json_data or {"itemSummaries": []}

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._json_data


def _patch_common(monkeypatch, get_responses):
    """Patcht Token-Post + eine Sequenz von GET-Antworten (eine pro Aufruf).

    Gibt (sleeps, call_counter) zurueck:
    - sleeps: Liste aller time.sleep()-Aufrufe (real nicht ausgefuehrt, nur
      gezaehlt/protokolliert -- haelt die Testsuite schnell).
    - call_counter: einelementige Liste, die bei jedem GET-Aufruf hochgezaehlt
      wird (fuer Assertions, wie oft tatsaechlich angefragt wurde, z.B. um
      den Circuit-Breaker zu pruefen).
    """
    monkeypatch.setenv("EBAY_CLIENT_ID", "id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "secret")
    monkeypatch.setattr(ebay_mod.requests, "post", lambda *a, **kw: _FakeTokenResponse())

    calls = iter(get_responses)
    call_counter = [0]

    def fake_get(*a, **kw):
        call_counter[0] += 1
        return next(calls)

    monkeypatch.setattr(ebay_mod.requests, "get", fake_get)

    sleeps: list[float] = []
    monkeypatch.setattr(ebay_mod.time, "sleep", lambda s: sleeps.append(s))
    return sleeps, call_counter


def test_429_wird_mit_backoff_wiederholt_und_liefert_dann_ergebnis(monkeypatch):
    ok_response = _FakeResponse(
        status_code=200,
        json_data={
            "itemSummaries": [
                {
                    "title": "Gaming PC RTX 3060",
                    "price": {"value": "450.0"},
                    "itemWebUrl": "https://www.ebay.de/itm/123",
                    "itemLocation": {"city": "Musterstadt"},
                }
            ]
        },
    )
    sleeps, _ = _patch_common(
        monkeypatch,
        [_FakeResponse(status_code=429), _FakeResponse(status_code=429), ok_response],
    )

    results = search_ebay(["Gaming PC"], plz="76477", radius_km=50, max_price=999)

    assert len(results) == 1
    assert results[0]["title"] == "Gaming PC RTX 3060"
    # Zwei Retry-Wartezeiten wegen der zwei 429er (kein Delay danach, da
    # letzter/einziger Suchbegriff).
    assert len(sleeps) == 2


def test_retry_after_header_wird_respektiert(monkeypatch):
    ok_response = _FakeResponse(status_code=200, json_data={"itemSummaries": []})
    sleeps, _ = _patch_common(
        monkeypatch,
        [_FakeResponse(status_code=429, headers={"Retry-After": "5"}), ok_response],
    )

    search_ebay(["GPU"], plz="76477", radius_km=50, max_price=999)

    assert sleeps[0] >= 5.0


def test_dauerhaftes_429_wird_nach_max_retries_uebersprungen_ohne_absturz(monkeypatch):
    _patch_common(
        monkeypatch,
        [_FakeResponse(status_code=429) for _ in range(ebay_mod.EBAY_MAX_RETRIES_429 + 1)],
    )

    results = search_ebay(["GPU"], plz="76477", radius_km=50, max_price=999)

    assert results == []


def test_pause_zwischen_mehreren_suchbegriffen(monkeypatch):
    ok = _FakeResponse(status_code=200, json_data={"itemSummaries": []})
    sleeps, _ = _patch_common(monkeypatch, [ok, ok, ok])

    search_ebay(["A", "B", "C"], plz="76477", radius_km=50, max_price=999)

    # 2 Pausen zwischen 3 Suchbegriffen, keine nach dem letzten.
    assert len(sleeps) == 2
    assert all(s == ebay_mod.EBAY_REQUEST_DELAY_SECONDS for s in sleeps)


def test_circuit_breaker_bricht_nach_threshold_aufeinanderfolgenden_429_ab(monkeypatch):
    """Kernfall Abschnitt 20: 73/74 Suchbegriffe blieben in der Praxis trotz
    Retry dauerhaft blockiert. Nach EBAY_CIRCUIT_BREAKER_THRESHOLD (Default 3)
    aufeinanderfolgenden vollstaendig gescheiterten Suchbegriffen soll der
    Rest der Suchbegriffe uebersprungen werden, statt jeden einzeln mit
    vollem Retry durchzuprobieren.
    """
    responses = []
    for _ in range(5):
        responses.extend([_FakeResponse(status_code=429)] * (ebay_mod.EBAY_MAX_RETRIES_429 + 1))
    _, call_counter = _patch_common(monkeypatch, responses)

    results = search_ebay(
        ["A", "B", "C", "D", "E"], plz="76477", radius_km=50, max_price=999
    )

    assert results == []
    # Nur die ersten EBAY_CIRCUIT_BREAKER_THRESHOLD Suchbegriffe wurden
    # tatsaechlich (mit vollem Retry) versucht -- danach abgebrochen.
    used_calls = ebay_mod.EBAY_CIRCUIT_BREAKER_THRESHOLD * (ebay_mod.EBAY_MAX_RETRIES_429 + 1)
    assert call_counter[0] == used_calls


def test_circuit_breaker_wird_durch_erfolg_zurueckgesetzt(monkeypatch):
    """Zwei 429-Serien mit einem erfolgreichen Suchbegriff dazwischen duerfen
    den Zaehler NICHT ueber mehrere Suchbegriffe hinweg aufaddieren."""
    ok = _FakeResponse(status_code=200, json_data={"itemSummaries": []})
    responses = (
        [_FakeResponse(status_code=429)] * (ebay_mod.EBAY_MAX_RETRIES_429 + 1)
        + [_FakeResponse(status_code=429)] * (ebay_mod.EBAY_MAX_RETRIES_429 + 1)
        + [ok]
        + [_FakeResponse(status_code=429)] * (ebay_mod.EBAY_MAX_RETRIES_429 + 1)
        + [_FakeResponse(status_code=429)] * (ebay_mod.EBAY_MAX_RETRIES_429 + 1)
    )
    _, call_counter = _patch_common(monkeypatch, responses)

    # 5 Suchbegriffe, threshold=3 -- da nach 2 Fehlschlaegen ein Erfolg den
    # Zaehler zuruecksetzt, darf der Circuit-Breaker hier NICHT greifen,
    # alle 5 Suchbegriffe werden tatsaechlich versucht.
    results = search_ebay(
        ["A", "B", "C", "D", "E"], plz="76477", radius_km=50, max_price=999
    )
    assert results == []  # der eine Erfolg lieferte 0 itemSummaries
    expected_calls = 4 * (ebay_mod.EBAY_MAX_RETRIES_429 + 1) + 1
    assert call_counter[0] == expected_calls


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
