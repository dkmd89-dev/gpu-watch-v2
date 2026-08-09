"""Regressionstests für den konsolen_bundles-Präzisionsphrasen-Fix
(kontrollierter Review nach found.json-Audit, Priorität HOCH).

Hintergrund: 49 von 240 sichtbaren found.json-Einträgen dieser Kategorie
waren Fehltreffer -- drei Untergruppen: reine Spiel-Angebote (21, "ovp"
als Positivsignal erfüllt), Standalone-Zubehör (22, "controller"/
"bundle" erfüllt), Touchscreen-/LCD-Ersatzteil-Reseller (5).

Auftragsvorgabe: "ovp" NICHT aus den require_all_of-Gruppen entfernen.
Stattdessen wurden die 49 Fehltreffer analysiert und präzise,
kollisionsfreie Phrasen ergänzt (jede Phrase gegen den vollständigen
sichtbaren Datensatz verifiziert: 0 Treffer in echten Konsole+Zubehör/
Spiele-Bundles). Bewusst NICHT ergänzt: bare "für" (9 Kollisionen),
"joy-con" (9 Kollisionen), "dualshock 4" (4 Kollisionen), bare
"touchscreen" (Risiko einer echten Zustands-/Funktionsprüfungs-
Beschreibung, identisches Muster wie beim Gehäuse/Shell-Fix).

Bekannte, bewusst nicht geschlossene Restlücken: individuelle
Spieltitel ohne die ergänzten Produktlinien-Phrasen (z.B. "Pokémon
Purpur", "Minecraft") sowie "Controller [Farbe] für ..." mit Wort
dazwischen (Adjazenz-Limitierung von _contains_term()).

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


def _matches_kb(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "konsolen_bundles"


# ============================================================
# 1. Gruppe 1 -- reine Spiel-Angebote: müssen jetzt blockiert werden.
# ============================================================

def test_mini_arcade_spiel_matcht_nicht():
    assert _matches_kb(
        "Nintendo Switch Mini Arcade - Mushihimesama - Limited Run - Neu & OVP", 49.95
    ) is False


def test_pro_skater_spiel_matcht_nicht():
    assert _matches_kb("PS4 Tony Hawks Pro Skater 1+2", 12.0) is False
    assert _matches_kb("Tony Hawk's Pro Skater 1+2 für PS4", 20.0) is False


def test_evolution_soccer_spiel_matcht_nicht():
    assert _matches_kb("PES 2015 Pro Evolution Soccer - PS4", 10.0) is False


def test_spiele_wahl_matcht_nicht():
    assert _matches_kb(
        "PS4 / PlayStation 4 Spiele-Wahl ALLE Spiele UNTER 10€ pro Game", 7.95
    ) is False


def test_spieleauswahl_matcht_nicht():
    assert _matches_kb(
        "Nintendo Switch riesige Spieleauswahl in OVP, Mario Kart, Minecraft, Luigi, uvm",
        73.9,
    ) is False


# ============================================================
# 2. Gruppe 2 -- Standalone-Zubehör: müssen jetzt blockiert werden.
# ============================================================

def test_zubehoer_set_matcht_nicht():
    assert _matches_kb(
        "Nintendo Switch 12-in-1 Joy-Con Zubehör-Set Schläger Schlaufe blau/rot", 70.0
    ) is False


def test_racing_wheel_matcht_nicht():
    assert _matches_kb("Drive Pro Sport Racing Wheel Lenkrad für PS4 & mehr", 55.0) is False


def test_controller_fuer_matcht_nicht():
    assert _matches_kb("2 Stück Controller für ps4 1 sony 1 suf pro", 40.0) is False
    assert _matches_kb(
        "Wireless Controller für PS4 Slim Pro PC RGB Touchpad Spinnennetz Schwarz Neu", 15.0
    ) is False


def test_dock_set_matcht_nicht():
    assert _matches_kb("Nintendo Switch Dock Set", 45.0) is False


def test_controller_defekt_matcht_nicht():
    assert _matches_kb(
        "1 x Sony PS4 DUALSHOCK 4 Schwarz Wireless Controller Defekt verbindet sich nicht",
        5.0,
    ) is False


def test_scuff_pad_matcht_nicht():
    assert _matches_kb("NEU: NACON PS4 Revolution Unlimited Pro Controller SCUFF Pad", 95.0) is False


def test_schutzhuelle_matcht_nicht():
    assert _matches_kb("NEUE Nitendo SWITCH Lite Schutzhülle - Pokemon Motiv", 4.0) is False


def test_gaming_headset_matcht_nicht():
    assert _matches_kb('Gaming Headset " NACON PS4 RIG 500 PRO"', 30.0) is False


def test_modchip_matcht_nicht():
    assert _matches_kb("Picofly Modchip Switch Lite / neu & unbenutzt", 12.0) is False


# ============================================================
# 3. Gruppe 3 -- Touchscreen-/LCD-Reseller: müssen jetzt blockiert
#    werden, OHNE bare "touchscreen" zu verwenden.
# ============================================================

def test_touchscreen_reseller_matcht_nicht():
    assert _matches_kb(
        "Nintendo Switch Lite Touchscreen grau Versand aus Deutschland", 26.09
    ) is False


def test_lcd_qualitaetskontrolle_reseller_matcht_nicht():
    assert _matches_kb(
        "Nintendo Switch Lite LCD Qualitätskontrolle & Versand aus Deutschland", 41.84
    ) is False


def test_bare_touchscreen_condition_beschreibung_bleibt_ungefaehrdet():
    # Sicherheitsprüfung: "Touchscreen" als Funktionsprüfungs-Aussage
    # eines ECHTEN Geräts (kein "Versand aus Deutschland"-Reseller-
    # Muster) darf NICHT blockiert werden -- bare "touchscreen" wurde
    # deshalb bewusst NICHT ausgeschlossen.
    r = evaluate(
        "Nintendo Switch Lite Konsole, Touchscreen reagiert einwandfrei, voll funktionsfähig",
        85.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "konsolen_bundles"


# ============================================================
# 4. Sicherheitsprüfung: echte Konsole+Zubehör/Spiele-Bundles bleiben
#    erhalten (inkl. der bewusst NICHT ausgeschlossenen Begriffe
#    "joy-con"/"dualshock 4"/"für").
# ============================================================

def test_switch_konsole_mit_joycons_matcht_weiterhin():
    r = evaluate("Nintendo Switch Konsole mit grauen Joy-Cons", 80.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_ps4_slim_mit_dualshock4_matcht_weiterhin():
    r = evaluate(
        "Sony PlayStation 4 Slim 500GB Schwarz mit DualShock 4 Controller & Headset",
        55.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_switch_konsole_mit_zubehoer_matcht_weiterhin():
    r = evaluate("Nintendo Switch Konsole OLED mit Zubehör", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_xbox_one_s_konsole_mit_controller_matcht_weiterhin():
    r = evaluate("Xbox One S Konsole mit Controller", 80.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_ovp_bleibt_positivsignal_fuer_echte_konsole():
    r = evaluate("Nintendo Switch OLED Modell - Weiß - Komplett mit OVP", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
