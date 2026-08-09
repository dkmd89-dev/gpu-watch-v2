"""Regressionstests für die handhelds-Zubehör-/Ersatzteil-Erweiterung
(kontrollierter Review nach found.json-Audit, Priorität HOCH).

Hintergrund: 24 von 38 sichtbaren found.json-Einträgen dieser Kategorie
waren Standalone-Zubehör/Ersatzteile, u.a. "Original Valve Steam Deck
Docking Station" (119,99EUR Top-Deal), "Lenovo Legion Go Gaming
Mainboard Handheld Reparatur Repair" (229EUR Top-Deal), "Kingston NV3
2TB SSD M.2 2230 NVMe PCIe 4.0 - Steam Deck, ROG Ally, etc." (180EUR
Top-Deal).

Fix, zwei Bausteine:
1. Unbedingte exclude_category-Ergänzungen für eindeutige Fälle:
   "dockingstation"/"docking station" (Kompositum-/Wortgrenzen-Lücke
   analog "ladekabel"/"kabel"), "memory card", "microsd", "m.2 ssd",
   "mainboard", "motherboard", "for parts", "not working",
   "batterieabdeckung".
2. "joystick"/"thumbstick" (+ Pluralformen) bewusst NICHT bare
   ausgeschlossen -- Stick-Drift ist bei Steam Deck/ROG Ally ein
   bekanntes, häufig in echten Geräte-Zustandsbeschreibungen genanntes
   Merkmal (analog zum Gehäuse/Shell-Fix). Stattdessen im bereits
   bestehenden exclude_category_unless_also_contains ergänzt.

Bekannte, bewusst nicht geschlossene Restlücken (documented, siehe
rules/handhelds.yaml-Kommentar): "SSD M.2" (umgekehrte Wortreihenfolge
zu "m.2 ssd") sowie Taschen-/Etui-Zubehör (nicht Teil dieses Reviews).

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


def _matches_handhelds(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "handhelds"


# ============================================================
# 1. Neue unbedingte Excludes -- müssen jetzt blockiert werden
#    (reale found.json-Funde).
# ============================================================

def test_docking_station_matcht_nicht():
    assert _matches_handhelds("Original Valve Steam Deck Docking Station", 119.99) is False


def test_dockingstation_kompositum_matcht_nicht():
    assert _matches_handhelds(
        "Original Valve Steam Deck Dockingstation - Ohne Zubehör", 79.0
    ) is False


def test_dockingstation_mit_marken_aufzaehlung_matcht_nicht():
    assert _matches_handhelds(
        "Steam Deck Dockingstation für Steam Deck OLED/ROG Ally/Legion Go, 6-in-1 USB",
        43.99,
    ) is False


def test_mainboard_reparatur_matcht_nicht():
    assert _matches_handhelds(
        "Lenovo Legion Go Gaming Mainboard Handheld Reparatur Repair", 229.0
    ) is False


def test_motherboard_for_parts_not_working_matcht_nicht():
    assert _matches_handhelds(
        "Nintendo New 3DS LL Motherboard Red CPU-10 OEM - For Parts / Not Working", 50.0
    ) is False


def test_batterieabdeckung_matcht_nicht():
    assert _matches_handhelds(
        "Lenovo Legion Go 8APU1 (83E1) original Batterieabdeckung lila", 63.35
    ) is False


def test_microsd_matcht_nicht_mehr_als_handhelds():
    r = evaluate(
        "SanDisk GamePlay microSD Express Card 512GB Nintendo Switch ROG Ally NEU OVP",
        123.99, _rules_cfg(),
    )
    assert r.category != "handhelds"


# ============================================================
# 2. Joystick/Thumbstick: Standalone-Ersatzteil blockiert,
#    Zustandsbeschreibung eines echten Geräts bleibt erlaubt.
# ============================================================

def test_standalone_joysticks_matcht_nicht():
    assert _matches_handhelds("tmr joysticks für rog ally x von HandheldDIY", 20.0) is False


def test_standalone_thumbstick_grip_caps_matcht_nicht():
    assert _matches_handhelds(
        "ROG Ally Grip Caps Thumbstick Joystick Schutz-Kappen Analog Stick Aufsätze", 2.79
    ) is False


def test_geraet_mit_joystick_drift_zustand_matcht_weiterhin():
    r = evaluate(
        "ROG Ally X, rechter Joystick minimales Drift, ansonsten neuwertig 512GB",
        240.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "handhelds"


def test_geraet_mit_thumbstick_zustand_matcht_weiterhin():
    r = evaluate(
        "Steam Deck OLED, linker Thumbstick leicht ausgeleiert, sonst Top Zustand",
        170.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "handhelds"


# ============================================================
# 3. Sicherheitsprüfung: reguläre Geräte und Bundles (inkl. Spiele)
#    matchen weiterhin -- "spiele" wurde bewusst NICHT zusätzlich
#    ausgeschlossen (siehe Auftrag).
# ============================================================

def test_steam_deck_mit_spielen_bundle_matcht_weiterhin():
    r = evaluate("Valve Steam Deck 512GB inkl. 5 Spiele", 170.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"


def test_regulaeres_geraet_ohne_zubehoer_matcht_weiterhin():
    r = evaluate("ASUS ROG Ally Z1 Extreme", 240.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"


def test_konsole_bundle_mit_spiel_matcht_weiterhin():
    r = evaluate(
        "Nintendo 2DS Konsole Schwarz Blau Bundle & Animal Crossing New Leaf",
        90.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "handhelds"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
