"""Tests für Schritt C: Deals-Aufräumen (found.json > DEAL_MAX_AGE_DAYS).

1. Unit-Tests direkt gegen _cleanup_old_deals()
2. Integrationstest über run_scan(): alte Einträge werden beim Scan
   automatisch entfernt, neue/junge bleiben erhalten
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.kleinanzeigen
import scrapers.ebay
import scrapers.quoka


def _load_app_module(data_dir: str, max_age_days: str = "7"):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    os.environ["DEAL_MAX_AGE_DAYS"] = max_age_days
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_cleanup", app_path)
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


# ---------- Unit-Tests: _cleanup_old_deals() ----------

def test_cleanup_entfernt_eintrag_aelter_als_max_age():
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        found = [{"title": "Alt", "found_at": old_ts}]
        kept, removed = mod._cleanup_old_deals(found, max_age_days=7)
        assert kept == []
        assert removed == 1


def test_cleanup_behaelt_eintrag_juenger_als_max_age():
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp)
        recent_ts = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        found = [{"title": "Neu", "found_at": recent_ts}]
        kept, removed = mod._cleanup_old_deals(found, max_age_days=7)
        assert len(kept) == 1
        assert removed == 0


def test_cleanup_behaelt_legacy_eintrag_ohne_found_at():
    # Rueckwaertskompatibilitaet: Eintraege aus der Zeit vor Einfuehrung
    # von found_at duerfen nicht blind geloescht werden.
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp)
        found = [{"title": "Legacy ohne Zeitstempel"}]
        kept, removed = mod._cleanup_old_deals(found, max_age_days=7)
        assert len(kept) == 1
        assert removed == 0


def test_cleanup_behaelt_eintrag_mit_kaputtem_zeitstempel():
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp)
        found = [{"title": "Kaputter Zeitstempel", "found_at": "nicht-parsebar"}]
        kept, removed = mod._cleanup_old_deals(found, max_age_days=7)
        assert len(kept) == 1
        assert removed == 0


def test_cleanup_grenzfall_genau_max_age_bleibt_erhalten():
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp)
        # Minimal juenger als die Grenze -> bleibt erhalten (>=  cutoff)
        boundary_ts = (datetime.now(timezone.utc) - timedelta(days=7) + timedelta(minutes=1)).isoformat()
        found = [{"title": "Grenzfall", "found_at": boundary_ts}]
        kept, removed = mod._cleanup_old_deals(found, max_age_days=7)
        assert len(kept) == 1
        assert removed == 0


def test_cleanup_gemischte_liste():
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        recent_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        found = [
            {"title": "Alt", "found_at": old_ts},
            {"title": "Neu", "found_at": recent_ts},
            {"title": "Legacy"},
        ]
        kept, removed = mod._cleanup_old_deals(found, max_age_days=7)
        titles = {e["title"] for e in kept}
        assert titles == {"Neu", "Legacy"}
        assert removed == 1


# ---------- Integrationstest: run_scan() räumt found.json auf ----------

def test_run_scan_entfernt_alte_deals_aus_found_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, max_age_days="7")

        # found.json manuell mit einem alten (11 Tage) und einem jungen
        # (1 Tag) Eintrag vorbelegen, BEVOR run_scan() läuft.
        old_ts = (datetime.now(timezone.utc) - timedelta(days=11)).isoformat()
        recent_ts = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        pre_existing = [
            {
                "title": "Altes Angebot", "price": 50.0, "url": "https://example.test/alt",
                "source": "kleinanzeigen", "location": "X", "found_at": old_ts,
                "category": "gpu", "deal_score": 50, "deal_stars": "★★★☆☆",
            },
            {
                "title": "Junges Angebot", "price": 50.0, "url": "https://example.test/jung",
                "source": "kleinanzeigen", "location": "X", "found_at": recent_ts,
                "category": "gpu", "deal_score": 50, "deal_stars": "★★★☆☆",
            },
        ]
        app_mod.FOUND_FILE.write_text(json.dumps(pre_existing), encoding="utf-8")
        app_mod.SEEN_FILE.write_text(json.dumps([]), encoding="utf-8")

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=[]), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy", MagicMock()):
            app_mod.run_scan()

        found_after = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        urls = {e["url"] for e in found_after}
        assert "https://example.test/jung" in urls
        assert "https://example.test/alt" not in urls


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
