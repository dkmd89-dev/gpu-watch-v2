"""Tests für die Phase-12-Schritt-3-Matching-Fixes: lego_sw_rare,
crt_profi_monitor, roehrenfernseher, thinkpad_modern (echte neue Fixes)
sowie nintendo_/sony_retro_konsole (Regressionsschutz für einen bereits
zuvor umgesetzten Fix, siehe PRICE_CALIBRATION_REVIEW.md).

Alle Tests laufen gegen die ECHTEN, produktiven rules/*.yaml (load_rules()
ohne synthetische rules_cfg) -- das ist hier bewusst gewählt, weil es
genau die Konfiguration prüft, die auch produktiv läuft, nicht nur die
Matcher-Mechanik in Isolation.
"""
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


# ---------- lego_sw_rare: BUG-FIX (["lego","star wars"] als 1 Gruppe -> 2 Gruppen) ----------

def test_ninjago_limited_edition_matcht_nicht_mehr_als_lego_sw_rare():
    r = evaluate("LEGO Ninjago Limited Edition Minifigur Sawyer OVP 2018", 2.99, _rules_cfg())
    assert r.price_history_model != "lego_sw_rare"


def test_nexo_knights_limited_edition_matcht_nicht_mehr_als_lego_sw_rare():
    r = evaluate("LEGO Nexo Knights Limited Edition Minifigur Merlok 2.0 OVP", 2.49, _rules_cfg())
    assert r.price_history_model != "lego_sw_rare"


def test_echte_star_wars_seltene_figur_matcht_weiterhin():
    r = evaluate("LEGO Star Wars Minifigur C-3PO Chrom Gold Limited Edition", 49.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_sw_rare"


def test_echter_darth_revan_matcht_weiterhin():
    r = evaluate("LEGO Star Wars Darth Revan Minifigur selten", 40.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_sw_rare"


def test_darth_revan_ohne_star_wars_erwaehnung_matcht_nicht_mehr():
    # Regressionsschutz fuer genau den urspruenglichen Bug: "revan" allein
    # (ohne "star wars" im Titel) darf nicht mehr ausreichen.
    r = evaluate("LEGO Revan Minifigur selten", 40.0, _rules_cfg())
    assert r.price_history_model != "lego_sw_rare"


# ---------- lego_sw_clone: BUG-FIX (Phase 12, Schritt 4, gleiches Muster) ----------

def test_marvel_figur_matcht_nicht_mehr_als_lego_sw_clone():
    r = evaluate("LEGO Marvel Spider-Man Minifigur Clone Sammler selten", 20.0, _rules_cfg())
    assert r.price_history_model != "lego_sw_clone"


def test_echter_clone_trooper_matcht_weiterhin():
    r = evaluate("LEGO Star Wars Clone Trooper 501st Minifigur", 25.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_sw_clone"


# ---------- lego_ninjago_rare / lego_ninjago_bundle: BUG-FIX (Phase 12, Schritt 4) ----------

def test_star_wars_konvolut_matcht_nicht_mehr_als_lego_ninjago_bundle():
    r = evaluate("LEGO Star Wars Minifiguren Konvolut Sammlung 10 Stück", 30.0, _rules_cfg())
    assert r.price_history_model != "lego_ninjago_bundle"


def test_echte_ninjago_seltene_figur_matcht_weiterhin():
    r = evaluate("LEGO Ninjago Minifigur Kai selten limited", 15.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_ninjago_rare"


def test_echtes_ninjago_konvolut_matcht_weiterhin():
    r = evaluate("LEGO Ninjago Minifiguren Konvolut Sammlung 20 Stück", 35.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_ninjago_bundle"


def test_ninjago_rare_ohne_ninjago_erwaehnung_matcht_nicht_mehr():
    # Regressionsschutz: "selten"+"minifigur"+"lego" allein (ohne
    # "ninjago") darf nicht mehr ausreichen.
    r = evaluate("LEGO Minifigur selten limited", 15.0, _rules_cfg())
    assert r.price_history_model != "lego_ninjago_rare"


# ---------- crt_profi_monitor: MATCHING-FIX (Werbung/Papierwaren ausschliessen) ----------

def test_vintage_werbeanzeige_matcht_nicht_mehr_als_monitor():
    r = evaluate(
        "1978 Sony Trinitron Plus Fernseher TV Bildröhre Vintage Advert Werbung Reklame",
        4.99, _rules_cfg(),
    )
    assert r.price_history_model != "crt_profi_monitor"


def test_anleitung_matcht_nicht_mehr_als_monitor():
    r = evaluate("Sony Trinitron Fernseher Bedienungsanleitung", 1.0, _rules_cfg())
    assert r.price_history_model != "crt_profi_monitor"


def test_echter_pvm_monitor_matcht_weiterhin():
    r = evaluate("Sony PVM 740 Professional Video Monitor Broadcast", 250.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "crt_profi_monitor"


# ---------- roehrenfernseher: MATCHING-FIX (Ersatzteile/Zubehoer ausschliessen) ----------

def test_fernbedienung_matcht_nicht_mehr_als_roehrenfernseher():
    r = evaluate(
        "Hanseatic Fernbedienung voll funktionsfähig 80er Jahre für Röhrenfernseher",
        3.50, _rules_cfg(),
    )
    assert r.price_history_model != "roehrenfernseher"


def test_netzschalter_matcht_nicht_mehr_als_roehrenfernseher():
    r = evaluate("Telefunken Netzschalter für Röhrenfernseher", 4.48, _rules_cfg())
    assert r.price_history_model != "roehrenfernseher"


def test_widerstand_set_matcht_nicht_mehr_als_roehrenfernseher():
    r = evaluate("20x 110 kOhm 5 1 Watt Widerstand für Röhrenfernseher Radio", 2.09, _rules_cfg())
    assert r.price_history_model != "roehrenfernseher"


def test_echter_roehrenfernseher_matcht_weiterhin():
    r = evaluate("Vintage Philips Röhrenfernseher 80er Jahre Retro Gaming", 45.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "roehrenfernseher"


# ---------- thinkpad_modern: MATCHING-FIX (RAM-/Speicher-Angabe erforderlich) ----------

def test_einzelner_power_button_matcht_nicht_mehr():
    r = evaluate("Lenovo ThinkPad T490 Poweron Button Einschaltknopf", 7.0, _rules_cfg())
    assert r.price_history_model != "thinkpad_modern"


def test_einzelner_luefter_matcht_nicht_mehr():
    r = evaluate("Lenovo ThinkPad X390 X395 X13 G1 Kühler Lüfter 01AW748", 14.0, _rules_cfg())
    assert r.price_history_model != "thinkpad_modern"


def test_einzelnes_gehaeuse_matcht_nicht_mehr():
    r = evaluate("Lenovo ThinkPad T490 20N3 Gehäuse Unterseite Case", 13.0, _rules_cfg())
    assert r.price_history_model != "thinkpad_modern"


def test_komplettgeraet_mit_ram_und_ssd_matcht_weiterhin():
    r = evaluate("Lenovo ThinkPad T490 i5-8365U 16GB 512GB SSD FHD", 240.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "thinkpad_modern"


def test_komplettgeraet_mit_kleinerer_ram_groesse_matcht_weiterhin():
    r = evaluate("Lenovo ThinkPad X13 Yoga i5-10210U FullHD 8GB 256GB IPS", 180.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "thinkpad_modern"


# ---------- nintendo_/sony_retro_konsole: Regressionsschutz (bereits vorher gefixt) ----------

def test_nintendo_einzelspiel_matcht_nicht():
    r = evaluate("Nintendo Gamecube Spiele", 1.0, _rules_cfg())
    assert r.price_history_model != "nintendo_retro_konsole"


def test_sony_einzelspiel_matcht_nicht():
    r = evaluate("PS1 Spiel Wer wird Millionär auch spielbar auf PS2 und PS3", 1.40, _rules_cfg())
    assert r.price_history_model != "sony_retro_konsole"


def test_sony_anleitung_matcht_nicht():
    r = evaluate("Sony Playstation 1 PS1 PSone Anleitungen deutsch PAL", 2.0, _rules_cfg())
    assert r.price_history_model != "sony_retro_konsole"


def test_markenuebergreifende_platzhalter_sammlung_matcht_nicht():
    r = evaluate(
        "PS2 PS3 PS4 Xbox Xbox360 Gamecube Sammlungsauflösung der Preis ist nur Platzhalter",
        1.0, _rules_cfg(),
    )
    assert r.price_history_model not in ("nintendo_retro_konsole", "sony_retro_konsole")


def test_echte_nintendo_konsole_matcht_weiterhin():
    r = evaluate("Nintendo 64 Konsole N64 schwarz", 40.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "nintendo_retro_konsole"


def test_echte_sony_konsole_matcht_weiterhin():
    r = evaluate("Sony PSOne Playstation 1 Konsole Slim Controller MC", 35.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "sony_retro_konsole"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
