"""Tests für Ziel 1 (Kategorieweise Auswertung) auf run_scan()-Ebene.

Prüft:
- Treffer werden nach Kategorie gruppiert verarbeitet/geloggt (gpu VOR
  sata_ssd, entsprechend scan_priority), unabhängig von der rohen
  Scrape-Reihenfolge der Rohtreffer.
- Pro Kategorie erscheint eine "🔍 Kategorie '<name>' fertig: N Treffer"-
  Zeile, am Ende eine "✅ Scan komplett: N Treffer insgesamt"-Zeile.
- found.json/price_history/ntfy-Verhalten bleibt inhaltlich unverändert
  (nur die Verarbeitungsreihenfolge/das Logging ändert sich).
"""
import sys
import os
import json
import logging
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.kleinanzeigen
import scrapers.ebay
import scrapers.quoka


def _load_app_module(data_dir: str):
    logging.root.handlers.clear()
    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_category_grouping", app_path)
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


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def test_verarbeitung_gruppiert_nach_kategorie_gpu_vor_sata_ssd():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        capture = _CaptureHandler()
        app_mod.log.addHandler(capture)

        # Bewusst in "falscher" Reihenfolge (SATA-SSD zuerst im Rohtreffer-
        # Strom) -- die Verarbeitung/das Logging muss trotzdem GPU zuerst
        # gruppieren (scan_priority: gpu=1, sata_ssd=2).
        #
        # Titel bewusst "...SSD SATA III" (nicht "...SATA SSD"): der
        # SSD-Kapazitaets-Detector (detect_ssd_gb, categories/detectors/
        # storage.py) verlangt strikte Wort-Adjazenz zwischen Groessen-
        # angabe und "SSD" -- bei "250GB SATA SSD" stuende "SATA" dazwischen
        # und die Kapazitaet waere nicht erkennbar (siehe Matcher-Fix fuer
        # min_ssd_gb/max_ssd_gb). Fuer DIESEN Test ist nur die Kategorie-
        # Gruppierung/Reihenfolge relevant, nicht die SSD-Erkennung selbst
        # -- der Titel muss daher zuverlaessig als sata_ssd matchen.
        fake_listings = [
            {
                "source": "Kleinanzeigen",
                "title": "Kingston A400 250GB SSD SATA III 2.5",
                "price": 10.0,
                "url": "https://example.test/ssd-1",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
            {
                "source": "Kleinanzeigen",
                "title": "ASUS RTX 3060 12GB ROG Strix",
                "price": 200.0,
                "url": "https://example.test/gpu-1",
                "location": "Musterstadt",
                "description": "",
                "images": [],
            },
        ]

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=fake_listings), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
                 patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy", MagicMock()):
            app_mod.run_scan()

        app_mod.log.removeHandler(capture)

        gpu_idx = next(
            i for i, m in enumerate(capture.messages) if "Kategorie 'gpu' fertig" in m
        )
        ssd_idx = next(
            i for i, m in enumerate(capture.messages) if "Kategorie 'sata_ssd' fertig" in m
        )
        assert gpu_idx < ssd_idx, "gpu muss VOR sata_ssd fertiggemeldet werden (scan_priority)"

        assert any("1 Treffer" in m and "'gpu'" in m for m in capture.messages)
        assert any("1 Treffer" in m and "'sata_ssd'" in m for m in capture.messages)
        assert any("Scan komplett" in m and "2 Treffer insgesamt" in m for m in capture.messages)

        # found.json enthaelt weiterhin beide Treffer (Inhalt unveraendert,
        # nur die Verarbeitungsreihenfolge hat sich geaendert).
        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        urls = {e["url"] for e in found}
        assert "https://example.test/ssd-1" in urls
        assert "https://example.test/gpu-1" in urls


def test_kategorie_ohne_treffer_wird_mit_0_treffer_geloggt():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)
        capture = _CaptureHandler()
        app_mod.log.addHandler(capture)

        with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=[]), \
             patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
                 patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
             patch.object(app_mod, "send_ntfy", MagicMock()):
            app_mod.run_scan()

        app_mod.log.removeHandler(capture)
        assert any("Kategorie 'gpu' fertig: 0 Treffer" in m for m in capture.messages)
        assert any("Scan komplett: 0 Treffer insgesamt" in m for m in capture.messages)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
