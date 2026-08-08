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


def test_migrierte_nie_gematchte_alt_url_wird_jetzt_re_evaluiert():
    """Phase 11, Punkt B (bewusste Verhaltensänderung ggü. vorher): eine
    migrierte Alt-URL (first_seen=None, NIE gematcht -- altes Listenformat
    kennt kein "category"-Feld) wird jetzt erneut evaluiert, da sie noch
    keinen last_evaluated_ruleset_hash trägt (None != aktueller Hash).
    Das ist der zentrale Fix für "seen.json darf nicht als Blockade für
    neue Kategorien wirken" -- vor Phase 11 wurde eine solche URL für
    immer übersprungen, selbst wenn eine neue/geänderte Regel sie jetzt
    korrekt matchen würde."""
    with tempfile.TemporaryDirectory() as tmpdir:
        seen_path = Path(tmpdir) / "seen.json"
        seen_path.write_text(json.dumps([_LISTING["url"]]), encoding="utf-8")

        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        # _LISTING matcht die GPU-Top-Deal-Regel (siehe api_status.py-Log:
        # "RTX 3060 12GB ★ Top-Deal") -- wird jetzt korrekt gefunden.
        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert len(found) == 1
        assert found[0]["url"] == _LISTING["url"]

        seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        # first_seen bleibt None (keine erfundene Historie), last_seen wird
        # trotzdem aktualisiert, da das Angebot in diesem Scan erneut
        # auftauchte. category ist jetzt gesetzt (frisch gematcht).
        assert seen[_LISTING["url"]]["first_seen"] is None
        assert seen[_LISTING["url"]]["last_seen"] is not None
        assert seen[_LISTING["url"]]["category"] is not None
        assert seen[_LISTING["url"]]["last_evaluated_ruleset_hash"] is not None


def test_bereits_gematchte_url_wird_nie_erneut_evaluiert():
    """Phase 11, Punkt B: die eigentliche Sicherheitsgarantie -- ein
    Angebot, das BEREITS EINMAL gematcht wurde (category gesetzt), wird
    NIE erneut evaluiert, unabhängig vom Regelwerk-Stand. Das verhindert
    doppelte Preishistorie-Einträge/Notifications für dasselbe Angebot.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        seen_path = Path(tmpdir) / "seen.json"
        # Bereits gematchter Eintrag (category gesetzt), altes/anderes
        # last_evaluated_ruleset_hash als das, was der aktuelle Scan haben
        # wird -- muss trotzdem uebersprungen werden.
        seen_path.write_text(json.dumps({
            _LISTING["url"]: {
                "first_seen": "2026-01-01T00:00:00+00:00",
                "last_seen": "2026-01-01T00:00:00+00:00",
                "missed_scans": 0,
                "delisted": False,
                "category": "gpu",
                "price_history_model": "rtx_3060_12gb",
                "last_evaluated_ruleset_hash": "veraltet-und-anders",
            }
        }), encoding="utf-8")

        app_mod = _load_app_module(tmpdir)

        _run_scan_with(app_mod, [_LISTING])

        # KEIN neuer found.json-Eintrag -- das Angebot war schon "bekannt"
        # (gematcht), evaluate() wurde für diesen Scan gar nicht erneut
        # aufgerufen.
        found = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert found == []

        seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        # last_evaluated_ruleset_hash bleibt unveraendert -- kein erneuter
        # evaluate()-Aufruf fuer bereits gematchte Eintraege.
        assert seen[_LISTING["url"]]["last_evaluated_ruleset_hash"] == "veraltet-und-anders"
        assert seen[_LISTING["url"]]["last_seen"] is not None


def test_seen_json_wird_bei_ueberschreitung_von_seen_max_items_gekappt():
    """Regressionstest (roadmap.md Phase 4, Sofort-Fix): run_scan() muss
    presence_tracking.enforce_max_size() tatsaechlich aufrufen, wenn
    len(seen) > SEEN_MAX_ITEMS. Dieser Test haette die stille Regression
    aus Commit 00bd8e8 (SEEN_MAX_ITEMS-Verdrahtung versehentlich entfernt,
    obwohl enforce_max_size() selbst unveraendert und getestet blieb)
    erkannt -- die reine Unit-Test-Abdeckung von enforce_max_size() allein
    reicht nicht, da sie den Aufruf aus app.py heraus nicht prueft.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["SEEN_MAX_ITEMS"] = "5"
        try:
            seen_path = Path(tmpdir) / "seen.json"
            # 6 vorbefuellte, aeltere Eintraege -- eine ueber der (fuer
            # diesen Test bewusst niedrig gesetzten) Grenze von 5.
            preexisting = {
                f"https://example.test/old-{i}": {
                    "first_seen": f"2026-01-0{i+1}T00:00:00+00:00",
                    "last_seen": f"2026-01-0{i+1}T00:00:00+00:00",
                    "missed_scans": 0,
                    "delisted": False,
                }
                for i in range(6)
            }
            seen_path.write_text(json.dumps(preexisting), encoding="utf-8")

            app_mod = _load_app_module(tmpdir)
            assert app_mod.SEEN_MAX_ITEMS == 5

            _run_scan_with(app_mod, [_LISTING])

            seen = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
            # 6 alte + 1 neuer Treffer aus diesem Scan = 7 vor dem Kappen ->
            # muss auf die Grenze (5) reduziert werden. Die aeltesten
            # Eintraege (old-0, old-1) fallen weg, der neue Treffer sowie
            # die juengsten alten Eintraege bleiben erhalten.
            assert len(seen) == 5
            assert _LISTING["url"] in seen
            assert "https://example.test/old-0" not in seen
            assert "https://example.test/old-1" not in seen
        finally:
            del os.environ["SEEN_MAX_ITEMS"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
