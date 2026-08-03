"""Tests für die Anbindung von presence_tracking.py in run_scan() (app.py),
STATUS.md Abschnitt 16, Baustein 6, Schritt 1.

Prüft: seen.json wird als Dict mit first_seen/last_seen geschrieben, ein
Alt-Format (reine Liste) wird beim nächsten Scan automatisch migriert, und
ein Angebot, das in zwei aufeinanderfolgenden Scans auftaucht, bekommt ein
aktualisiertes last_seen bei unverändertem first_seen.
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
    spec = importlib.util.spec_from_file_location("app_under_test_presence_tracking", app_path)
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


_LISTING = {
    "source": "Kleinanzeigen",
    "title": "ASUS RTX 3060 12GB ROG Strix",
    "price": 200.0,
    "url": "https://example.test/presence-1",
    "location": "Musterstadt",
    "description": "",
    "images": [],
}


def _run_scan_with(app_mod, listings):
    with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen", return_value=listings), \
         patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
         patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
         patch.object(app_mod, "send_ntfy", MagicMock()):
        app_mod.run_scan()


def test_seen_json_wird_als_dict_mit_first_seen_last_seen_geschrieben():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        assert isinstance(seen, dict)
        entry = seen[_LISTING["url"]]
        assert entry["first_seen"] is not None
        assert entry["last_seen"] is not None
        assert entry["first_seen"] == entry["last_seen"]


def test_erneutes_sehen_aktualisiert_last_seen_bei_gleichem_first_seen():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])
        seen_after_first = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        first_seen_1 = seen_after_first[_LISTING["url"]]["first_seen"]
        last_seen_1 = seen_after_first[_LISTING["url"]]["last_seen"]

        # Zweiter Scan, dasselbe Angebot taucht erneut in den Rohergebnissen
        # auf (bereits "seen" -> wird nicht erneut gematcht/evaluiert, aber
        # last_seen soll trotzdem aktualisiert werden).
        _run_scan_with(app_mod, [_LISTING])
        seen_after_second = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        first_seen_2 = seen_after_second[_LISTING["url"]]["first_seen"]
        last_seen_2 = seen_after_second[_LISTING["url"]]["last_seen"]

        assert first_seen_2 == first_seen_1
        assert last_seen_2 >= last_seen_1


def test_altes_listenformat_wird_beim_scan_automatisch_migriert():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Alt-Format: reine URL-Liste, wie vor diesem Schritt geschrieben.
        seen_path = Path(tmpdir) / "seen.json"
        seen_path.write_text(json.dumps(["https://example.test/legacy-url"]), encoding="utf-8")

        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        assert isinstance(seen, dict)
        # Migrierter Alt-Eintrag bleibt mit first_seen/last_seen=None erhalten
        # (keine erfundene Historie, siehe presence_tracking.py-Moduldoku).
        # missed_scans=1, da die legacy-URL in diesem Scan nicht mehr unter
        # den rohen Suchergebnissen auftaucht (Delisting-Sweep, Schritt 2) --
        # delisted bleibt False (Schwelle noch nicht erreicht).
        legacy_entry = seen["https://example.test/legacy-url"]
        assert legacy_entry["first_seen"] is None
        assert legacy_entry["last_seen"] is None
        assert legacy_entry["missed_scans"] == 1
        assert legacy_entry["delisted"] is False
        # Neuer Treffer aus diesem Scan bekommt echte Zeitstempel.
        assert seen[_LISTING["url"]]["first_seen"] is not None


def test_bereits_bekanntes_altes_angebot_wird_nicht_erneut_gematcht():
    """Rückwärtskompatibilität: eine migrierte Alt-URL (first_seen=None) mit
    exakt derselben URL wie ein aktueller Treffer darf NICHT erneut als
    neuer Fund verarbeitet werden -- die bisherige Dedup-Semantik
    (uid in seen -> skip) bleibt unveraendert erhalten."""
    with tempfile.TemporaryDirectory() as tmpdir:
        seen_path = Path(tmpdir) / "seen.json"
        seen_path.write_text(json.dumps([_LISTING["url"]]), encoding="utf-8")

        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert found == []

        seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        # first_seen bleibt None (keine erfundene Historie), last_seen wird
        # trotzdem aktualisiert, da das Angebot in diesem Scan erneut
        # auftauchte.
        assert seen[_LISTING["url"]]["first_seen"] is None
        assert seen[_LISTING["url"]]["last_seen"] is not None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
