"""Regressionstests für den handhelds-Zubehör/Ersatzteil-Fix
(kontrollierter Review, freigegeben nach DASHBOARD_MATCH_FORENSICS.md).

Hintergrund: Steam Deck / ROG Ally / Lenovo Legion Go-Regeln bestehen
jeweils nur aus EINER require_all_of-Gruppe (der Markenname selbst --
siehe handhelds.yaml-Begründung: diese Produktnamen sind eindeutige,
mehrwortige Markennamen ohne generisches Kurzwort, eine zweite
Positiv-Gruppe wäre wirkungslos, da auch Zubehör-Anzeigen den
Markennamen enthalten). Dadurch matchte jedes Angebot -- Gerät ODER
Zubehör --, das den Markennamen nennt. Vier im Forensik-Audit bestätigte
Fehltreffer-Muster waren bisher nicht durch exclude_category abgedeckt:
"hub" (USB-C-Hub), "skin"/"faceplate"/"vinyl" (Skins/Faceplates,
Aufkleber-Zubehör), "ladeadapter" (Adapter-Zubehör), "reisetasche"
(Kompositum von "tasche", von der Wortgrenzen-Prüfung nicht erfasst).

Fix: sechs weitere bare exclude_category-Einträge in handhelds.yaml
("hub", "skin", "faceplate", "vinyl", "klebefolie", "aufkleber",
"ladeadapter", "reisetasche") -- eindeutige Zubehör-Produktbezeichnungen
ohne Doppeldeutigkeit (anders als "gehäuse"/"joystick"), daher bare
Excludes statt des kontextbewussten Mechanismus. Verifiziert gegen alle
22 damals sichtbaren TRUE_POSITIVE-Treffer dieser Kategorie: 0
Kollisionen.

Auftragsvorgabe: KEIN pauschaler Ausschluss von "pokemon"/"spiele" --
"Nintendo 3DS XL Pokémon Edition inkl. 6 Pokémon Spielen" ist ein
legitimer Handheld-Treffer und muss weiterhin matchen. Nur klar belegte
Zubehör-/Ersatzteilmuster ausgeschlossen, bestehender Mechanismus
(exclude_category), kein neuer Matcher-Code.

Läuft gegen die echten, produktiven rules/*.yaml."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


def _matches_hh(title, price=0.0):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "handhelds"


# ============================================================
# 1. Die beiden im Auftrag explizit genannten Fehltreffer.
# ============================================================

def test_usb_c_hub_fuer_steam_deck_matcht_nicht():
    assert _matches_hh("USB-C HUB für Steam Deck HDMI 4k 60Hz USB 3.0 PD") is False


def test_steam_deck_skin_faceplate_matcht_nicht():
    assert _matches_hh(
        "Steam Deck Skin Faceplate Schutz Klebefolie Design Vinyl Aufkleber Skins OLED"
    ) is False


# ============================================================
# 2. Dokumentierte verwandte Zubehör-/Ersatzteilfälle.
# ============================================================

def test_ladeadapter_matcht_nicht():
    assert _matches_hh(
        "VITURE USB-C an Brille, Ladeadapter, Laden und Spielen für Switch, Steam Deck"
    ) is False


def test_reisetasche_kompositum_matcht_nicht():
    assert _matches_hh(
        "JSAUX Slim-Reisetasche Für Lenovo Legion Go/Go S/Go 2, Hartschalenbeutel"
    ) is False


def test_weitere_hub_skin_varianten_matchen_nicht():
    assert _matches_hh("USB-C Hub Adapter für ROG Ally, 6-in-1") is False
    assert _matches_hh("Skin Aufkleber für Nintendo Switch Lite, mehrere Designs") is False


# ============================================================
# 3. Kritische Sicherheitsprüfung: legitime Handheld-Treffer dürfen
#    NICHT durch einen pauschalen Ausschluss von "pokemon"/"spiele"
#    verloren gehen (explizite Auftragsvorgabe).
# ============================================================

def test_3ds_pokemon_edition_mit_spielen_matcht_weiterhin():
    r = evaluate(
        "Nintendo 3DS XL Pokémon Edition inkl. 6 Pokémon Spielen", 0.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "handhelds"


def test_steam_deck_bundle_mit_zubehoer_matcht_weiterhin():
    r = evaluate("Valve Steam Deck OLED 1TB, neuwertig", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"


def test_rog_ally_ovp_matcht_weiterhin():
    r = evaluate("Asus ROG Ally Z1 Extreme, 512GB, OVP", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"


def test_legion_go_matcht_weiterhin():
    r = evaluate('Lenovo Legion Go 8" 144Hz, wie neu', 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
