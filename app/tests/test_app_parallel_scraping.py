"""Regressionstests für die Parallelisierung der Scraper-Aufrufe in
run_scan() (Scan-Performance-Messung 2026-08-15,
docs/SCAN_PERFORMANCE_MESSUNG_2026-08-15.md).

Scraping macht 88,9% der Gesamt-Scandauer aus und lief bisher rein
seriell (ThreadPoolExecutor mit einem Worker je entdecktem Scraper-Plugin
ersetzt die einfache for-Schleife, Ergebnisse werden weiterhin nur im
Hauptthread in `raw` gemergt). Zusätzlich wurde ein bestehendes
Robustheitsproblem behoben: vorher gab es keinerlei try/except um
plugin.search() -- ein Fehler in EINER Quelle riss den kompletten Scan in
den äußeren except-Block von run_scan(), die anderen beiden Quellen
wurden verworfen. Jetzt wird jede Quelle einzeln abgefangen.
"""
import sys
import os
import json
import importlib.util
import tempfile
import time
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
    spec = importlib.util.spec_from_file_location("app_under_test_parallel_scraping", app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_ergebnisse_aller_drei_quellen_werden_gemergt():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        app_mod.FOUND_FILE.write_text(json.dumps([]), encoding="utf-8")
        app_mod.SEEN_FILE.write_text(json.dumps([]), encoding="utf-8")

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=[]), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]):
            app_mod.run_scan()

        # scrape_duration_by_source_sec ist die einzige nach aussen sichtbare
        # Bestaetigung, dass ALLE drei Plugins tatsaechlich aufgerufen wurden
        # (unabhaengig von Ergebnismenge) -- Reihenfolge/Parallelitaet selbst
        # ist ein Implementierungsdetail.
        by_source = app_mod._scan_status["scrape_duration_by_source_sec"]
        assert set(by_source.keys()) == {"kleinanzeigen", "ebay", "quoka"}
        assert app_mod._scan_status["last_scan_error"] is None


def test_einzelner_scraper_fehler_blockiert_die_anderen_quellen_nicht():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        app_mod.FOUND_FILE.write_text(json.dumps([]), encoding="utf-8")
        app_mod.SEEN_FILE.write_text(json.dumps([]), encoding="utf-8")

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", side_effect=RuntimeError("boom")), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
             patch.object(scrapers.quoka, "search_quoka", return_value=[]):
            app_mod.run_scan()

        # Vor dem Fix: die RuntimeError haette den gesamten Scan abgebrochen
        # (last_scan_error waere gesetzt gewesen, scrape_duration_by_source_sec
        # haette ebay/quoka evtl. gar nicht mehr enthalten, je nach
        # Dict-Iterationsreihenfolge). Jetzt: Scan laeuft trotzdem sauber durch.
        assert app_mod._scan_status["last_scan_error"] is None
        by_source = app_mod._scan_status["scrape_duration_by_source_sec"]
        assert set(by_source.keys()) == {"kleinanzeigen", "ebay", "quoka"}


def test_scraping_laeuft_parallel_nicht_seriell():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        app_mod.FOUND_FILE.write_text(json.dumps([]), encoding="utf-8")
        app_mod.SEEN_FILE.write_text(json.dumps([]), encoding="utf-8")

        def _slow(*_args, **_kwargs):
            time.sleep(0.15)
            return []

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", side_effect=_slow), \
             patch.object(scrapers.ebay, "search_ebay", side_effect=_slow), \
             patch.object(scrapers.quoka, "search_quoka", side_effect=_slow):
            t0 = time.perf_counter()
            app_mod.run_scan()
            wall_clock = time.perf_counter() - t0

        # Seriell waeren es >= 3 * 0.15s = 0.45s allein fuers Scraping (plus
        # Overhead). Parallel bleibt die Scraping-Zeit nahe an einem
        # einzelnen 0.15s-Aufruf. Grosszuegige Grenze (0.4s) fuer
        # Ausfuehrungs-Overhead in der Sandbox, liegt aber klar unter der
        # seriellen Summe.
        assert wall_clock < 0.4, f"Scan dauerte {wall_clock:.3f}s -- Scraping scheint seriell zu laufen"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
