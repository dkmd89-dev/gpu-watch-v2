"""Tests für category_validation.py (Phase 14, Schritt 2 --
PHASE14_DATA_QUALITY_REPORT.md, zentrale Kategorievalidierung).

Zwei Ebenen:
1. Unit-Tests direkt gegen is_still_valid_category()/filter_valid_entries()
   mit den ECHTEN, produktiven rules/*.yaml (load_rules()).
2. Integrationstests gegen die echte Flask-App (analog
   test_app_status_kpis.py::_load_app_module): schreiben ein found.json
   mit einem Alt-Fehltreffer (Titel, der laut Phase-14-Report VOR dem
   Schritt-1-Fix gematcht hat) + einem echten Treffer, pruefen dass
   Dashboard/API/Status den Fehltreffer ausblenden, waehrend die Datei
   auf Platte unveraendert bleibt (keine Loeschung/Manipulation).
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules
from category_validation import is_still_valid_category, filter_valid_entries

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


# ============================================================
# Unit-Tests: is_still_valid_category() / filter_valid_entries()
# ============================================================

def test_echter_treffer_bleibt_gueltig():
    entry = {"title": "Steam Deck 256GB", "price": 200, "category": "handhelds"}
    assert is_still_valid_category(entry, _rules_cfg()) is True


def test_alter_fehltreffer_wird_ungueltig():
    # Titel, der laut PHASE14_DATA_QUALITY_REPORT.md VOR dem Schritt-1-Fix
    # als handheld_steam_deck gematcht hat -- nach dem Fix matcht er gar
    # nicht mehr, muss also als ungueltig erkannt werden.
    entry = {"title": "Netzteil für Steam Deck 45W", "price": 15, "category": "handhelds"}
    assert is_still_valid_category(entry, _rules_cfg()) is False


def test_alter_switch_lite_fehltreffer_wird_ungueltig():
    entry = {
        "title": "Ladekabel für Nintendo Switch Lite Original",
        "price": 8,
        "category": "konsolen_bundles",
    }
    assert is_still_valid_category(entry, _rules_cfg()) is False


def test_eintrag_ohne_titel_bleibt_sichtbar_fail_open():
    entry = {"price": 15, "category": "handhelds"}
    assert is_still_valid_category(entry, _rules_cfg()) is True


def test_eintrag_ohne_kategorie_bleibt_sichtbar_fail_open():
    entry = {"title": "Netzteil für Steam Deck 45W", "price": 15}
    assert is_still_valid_category(entry, _rules_cfg()) is True


def test_eintrag_ohne_preisfeld_wird_dennoch_korrekt_geprueft():
    # Kein "price"-Key (aeltere found.json-Eintraege) -- Default 0.0 darf
    # die Kategorie-Pruefung nicht verfaelschen, ein echter Treffer bleibt
    # gueltig.
    entry = {"title": "Steam Deck OLED", "category": "handhelds"}
    assert is_still_valid_category(entry, _rules_cfg()) is True


def test_filter_valid_entries_entfernt_nur_den_fehltreffer():
    found = [
        {"title": "Steam Deck 256GB", "price": 200, "category": "handhelds"},
        {"title": "Netzteil für Steam Deck 45W", "price": 15, "category": "handhelds"},
    ]
    result = filter_valid_entries(found, _rules_cfg())
    assert len(result) == 1
    assert result[0]["title"] == "Steam Deck 256GB"


def test_filter_valid_entries_leere_liste():
    assert filter_valid_entries([], _rules_cfg()) == []


# ============================================================
# Integrationstests: echte Flask-App, / , /api/found, /api/status
# ============================================================

def _load_app_module(data_dir: str, module_name: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_FALSE_POSITIVE_ENTRY = {
    "title": "Netzteil für Steam Deck 45W",
    "price": 15,
    "url": "https://example.invalid/netzteil",
    "location": "Karlsruhe",
    "source": "kleinanzeigen",
    "category": "handhelds",
    "manufacturer": "Valve",
    "deal_score": 91,
    "deal_stars": "★★★★☆",
    "is_top_deal": True,
}

_REAL_ENTRY = {
    "title": "Steam Deck 256GB LCD wie neu",
    "price": 170,
    "url": "https://example.invalid/steamdeck",
    "location": "Karlsruhe",
    "source": "kleinanzeigen",
    "category": "handhelds",
    "manufacturer": "Valve",
    "deal_score": 85,
    "deal_stars": "★★★★☆",
    "is_top_deal": False,
}


def test_dashboard_blendet_alten_fehltreffer_aus():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_catval_dashboard")
        app_mod.FOUND_FILE.parent.mkdir(parents=True, exist_ok=True)
        app_mod.FOUND_FILE.write_text(
            json.dumps([_FALSE_POSITIVE_ENTRY, _REAL_ENTRY]), encoding="utf-8"
        )

        client = app_mod.app.test_client()
        html = client.get("/").get_data(as_text=True)

        assert "Netzteil für Steam Deck" not in html
        assert "Steam Deck 256GB LCD wie neu" in html


def test_api_found_blendet_alten_fehltreffer_aus():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_catval_api_found")
        app_mod.FOUND_FILE.parent.mkdir(parents=True, exist_ok=True)
        app_mod.FOUND_FILE.write_text(
            json.dumps([_FALSE_POSITIVE_ENTRY, _REAL_ENTRY]), encoding="utf-8"
        )

        client = app_mod.app.test_client()
        data = client.get("/api/found").get_json()

        titles = [e["title"] for e in data]
        assert "Netzteil für Steam Deck 45W" not in titles
        assert "Steam Deck 256GB LCD wie neu" in titles


def test_api_status_kpis_zaehlen_fehltreffer_nicht_mit():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_catval_api_status")
        app_mod.FOUND_FILE.parent.mkdir(parents=True, exist_ok=True)
        app_mod.FOUND_FILE.write_text(
            json.dumps([_FALSE_POSITIVE_ENTRY, _REAL_ENTRY]), encoding="utf-8"
        )

        client = app_mod.app.test_client()
        data = client.get("/api/status").get_json()

        # Der Fehltreffer hatte is_top_deal=True/deal_stars="★★★★☆" -- ohne
        # Revalidierung wuerde er in category_counts["handhelds"] und ggf.
        # very_good_deals_count mitgezaehlt. Erwartet: nur der echte
        # Treffer zaehlt.
        assert data["category_counts"].get("handhelds") == 1


def test_found_json_auf_platte_bleibt_unveraendert():
    # Kernvorgabe des Auftrags: keine Loeschung/Manipulation von
    # found.json -- die Revalidierung wirkt AUSSCHLIESSLICH auf die vom
    # Server zurueckgegebene Liste, nicht auf die Datei.
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_catval_file_unchanged")
        app_mod.FOUND_FILE.parent.mkdir(parents=True, exist_ok=True)
        original = [_FALSE_POSITIVE_ENTRY, _REAL_ENTRY]
        app_mod.FOUND_FILE.write_text(json.dumps(original), encoding="utf-8")

        client = app_mod.app.test_client()
        client.get("/")
        client.get("/api/found")
        client.get("/api/status")

        on_disk = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert len(on_disk) == 2
        assert on_disk[0]["title"] == "Netzteil für Steam Deck 45W"
