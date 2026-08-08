"""Tests für die erweiterten /api/status-KPIs (Auftrag "Top-Deal-Logik
optimieren", Abschnitte 11-16): top_deal_count (neue Regel), sowie neu
very_good_deals_count, flip_candidates_count, new_top_deals_count.

Alle vier KPIs werden ausschließlich aus found.json-Einträgen abgeleitet,
keine neue Persistenz. Struktur analog test_app_cross_platform_api.py.
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_status_kpis", app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_found(app_mod, entries: list[dict]) -> None:
    app_mod.FOUND_FILE.parent.mkdir(parents=True, exist_ok=True)
    app_mod.FOUND_FILE.write_text(json.dumps(entries), encoding="utf-8")


def _entry(
    *,
    is_top_deal: bool = False,
    deal_stars: str | None = None,
    estimated_margin_pct: float | None = None,
    found_at: str | None = "2026-08-01T00:00:00+00:00",
) -> dict:
    return {
        "title": "Testangebot",
        "price": 100,
        "category": "gaming_pc",
        "manufacturer": "Eigenbau",
        "is_top_deal": is_top_deal,
        "deal_stars": deal_stars,
        "estimated_margin_pct": estimated_margin_pct,
        "found_at": found_at,
    }


def test_status_kpis_leer_ohne_daten():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        client = app_mod.app.test_client()
        resp = client.get("/api/status")
        data = resp.get_json()

        assert data["top_deal_count"] == 0
        assert data["very_good_deals_count"] == 0
        assert data["flip_candidates_count"] == 0
        assert data["new_top_deals_count"] == 0


def test_top_deal_count_zaehlt_is_top_deal():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        _write_found(app_mod, [
            _entry(is_top_deal=True),
            _entry(is_top_deal=True),
            _entry(is_top_deal=False),
        ])

        client = app_mod.app.test_client()
        data = client.get("/api/status").get_json()
        assert data["top_deal_count"] == 2


def test_very_good_deals_zaehlt_nur_nicht_top_deals():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        _write_found(app_mod, [
            # Top-Deal MIT hohem Stern-Rating -> zaehlt NICHT zusaetzlich
            # als "sehr guter Deal" (keine Doppelzaehlung, Abschnitt 13).
            _entry(is_top_deal=True, deal_stars="★★★★★"),
            # Kein Top-Deal, aber gutes Rating -> sehr guter Deal.
            _entry(is_top_deal=False, deal_stars="★★★★☆"),
            _entry(is_top_deal=False, deal_stars="★★★★★"),
            # Kein Top-Deal, mittelmaessiges Rating -> zaehlt nicht.
            _entry(is_top_deal=False, deal_stars="★★★☆☆"),
            # Aeltere Eintraege ohne deal_stars -> robust ignoriert.
            _entry(is_top_deal=False, deal_stars=None),
        ])

        client = app_mod.app.test_client()
        data = client.get("/api/status").get_json()
        assert data["top_deal_count"] == 1
        assert data["very_good_deals_count"] == 2


def test_flip_candidates_ab_min_margin_und_unabhaengig_von_top_deal():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        min_margin = app_mod.MIN_FLIP_MARGIN_PCT
        _write_found(app_mod, [
            # Top-Deal UND Flip-Kandidat gleichzeitig -> ausdruecklich
            # erlaubt (Abschnitt 14), zaehlt in beiden KPIs.
            _entry(is_top_deal=True, estimated_margin_pct=min_margin + 5),
            _entry(is_top_deal=False, estimated_margin_pct=min_margin),
            _entry(is_top_deal=False, estimated_margin_pct=min_margin - 0.01),
            _entry(is_top_deal=False, estimated_margin_pct=None),
        ])

        client = app_mod.app.test_client()
        data = client.get("/api/status").get_json()
        assert data["flip_candidates_count"] == 2
        assert data["top_deal_count"] == 1


def test_new_top_deals_ist_teilmenge_seit_scan_start():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        with app_mod._status_lock:
            app_mod._scan_status["last_scan_started_at"] = "2026-08-08T10:00:00+00:00"

        _write_found(app_mod, [
            # Vor dem letzten Scan-Start gefunden -> alter Top-Deal.
            _entry(is_top_deal=True, found_at="2026-08-01T00:00:00+00:00"),
            # Waehrend/nach dem letzten Scan-Start gefunden -> neuer Top-Deal.
            _entry(is_top_deal=True, found_at="2026-08-08T10:05:00+00:00"),
            # Kein Top-Deal, aber neu -> zaehlt trotzdem nicht mit.
            _entry(is_top_deal=False, found_at="2026-08-08T10:05:00+00:00"),
        ])

        client = app_mod.app.test_client()
        data = client.get("/api/status").get_json()
        assert data["top_deal_count"] == 2
        assert data["new_top_deals_count"] == 1


def test_dashboard_html_enthaelt_neue_kpi_kacheln():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        client = app_mod.app.test_client()
        resp = client.get("/")
        html = resp.get_data(as_text=True)

        assert resp.status_code == 200
        assert 'id="cntTopDeals"' in html
        assert 'id="cntVeryGoodDeals"' in html
        assert 'id="cntFlipCandidates"' in html
        assert 'id="cntNewTopDeals"' in html


def test_dashboard_html_zeigt_top_deal_transparenz():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        _write_found(app_mod, [{
            "title": "Top-Deal-Testangebot",
            "price": 265,
            "url": "https://example.invalid/1",
            "location": "Karlsruhe",
            "source": "kleinanzeigen",
            "category": "gaming_pc",
            "manufacturer": "Eigenbau",
            "deal_score": 92,
            "deal_stars": "★★★★★",
            "is_top_deal": True,
            "top_deal_discount_pct": 22.1,
            "top_deal_market_price": 340,
            "top_deal_rule": "B",
            "found_at": "2026-08-01T00:00:00+00:00",
        }])

        client = app_mod.app.test_client()
        html = client.get("/").get_data(as_text=True)
        grid_html = html.split('id="listingsGrid"')[1].split('id="noMatchState"')[0]

        assert 'class="top-deal-detail"' in grid_html
        assert "Score 92" in grid_html
        assert "340" in grid_html
        assert "-22%" in grid_html
        assert "Regel B" in grid_html


def test_dashboard_html_ohne_top_deal_rule_keine_transparenz_zeile():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        # Aelterer found.json-Eintrag ohne top_deal_rule/top_deal_market_price
        # (vor diesem Schritt) -- darf keinen Fehler werfen, keine Zeile.
        _write_found(app_mod, [_entry(is_top_deal=False)])

        client = app_mod.app.test_client()
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        # JS-Quelltext (renderCardHtml()) enthaelt "top-deal-detail" immer
        # als String-Literal -- daher gezielt nur den serverseitig
        # gerenderten Karten-Bereich pruefen, nicht das komplette Dokument.
        grid_html = html.split('id="listingsGrid"')[1].split('id="noMatchState"')[0]
        assert 'class="top-deal-detail"' not in grid_html


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
