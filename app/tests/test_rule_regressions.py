"""False-Positive Regression Suite (Phase 15, Schritt 4 -- zentrale
Regressionssuite, siehe PHASE15_OPTIMIERUNG.md Abschnitte 15-16).

Deckt die im Auftrag genannten Problemgruppen ab: LEGO Star Wars, LEGO
Clone Wars, LEGO Ninjago, LEGO Bundles, CRT-Monitor, Röhrenfernseher,
ThinkPad, Retro-Konsolen, Handheld-Zubehör, Konsolen-Zubehör, Controller.
Für jede Gruppe mindestens ein Paar: ein echtes, positives Angebot MUSS
matchen; ein bekannter/plausibler Fehltreffer DARF NICHT (bzw. nicht als
dieselbe Regel/Kategorie) matchen.

Läuft bewusst gegen die ECHTEN, produktiven rules/*.yaml (load_rules()
ohne synthetische rules_cfg, analog zu
test_matcher_price_calibration_matching_fixes.py und
test_matcher_handheld_false_positives.py) -- eine Regression, die durch
eine spätere YAML-Änderung entsteht, muss hier real auffallen, nicht nur
gegen eine synthetische Fixture.

Die meisten der hier geprüften Fixes stammen bereits aus Phase 12/14 und
sind an anderer Stelle bereits punktuell getestet (siehe
test_matcher_price_calibration_matching_fixes.py,
test_matcher_handheld_false_positives.py). Diese Datei bündelt sie zu
EINER zentralen Suite (Auftragsvorgabe, Abschnitt 15) und ergänzt Gruppen,
die bisher nicht dediziert abgedeckt waren (CRT-Monitor, Röhrenfernseher,
ThinkPad, Konsolen-Zubehör, Controller) -- keine der bestehenden Tests
wird ersetzt oder abgeschwächt.
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


# ============================================================
# 1. LEGO Star Wars (Kategorie: lego_minifiguren, price_history_model
#    "lego_sw_rare"). Historischer Bug (Phase 12, Schritt 3):
#    require_all_of: [["lego", "star wars"]] als EINE Gruppe wertete
#    "lego" ODER "star wars" statt beide -- bereits gefixt.
# ============================================================

def test_lego_star_wars_seltene_figur_matcht():
    r = evaluate(
        "LEGO Star Wars Minifigur C-3PO Chrom Gold Limited Edition",
        12.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "lego_minifiguren"
    assert r.price_history_model == "lego_sw_rare"


def test_lego_star_wars_darth_revan_matcht():
    r = evaluate("LEGO Star Wars Darth Revan Minifigur selten", 40.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_sw_rare"


def test_lego_marvel_matcht_nicht_als_star_wars():
    # Auftrags-Matrix (Abschnitt 16): LEGO Star Wars Positiv=echtes
    # SW-Angebot, Negativ=Marvel.
    r = evaluate("LEGO Marvel Spider-Man Minifigur selten limitiert", 20.0, _rules_cfg())
    assert r.price_history_model != "lego_sw_rare"


def test_nur_lego_ohne_star_wars_matcht_nicht_als_star_wars():
    r = evaluate("LEGO Ninjago Limited Edition Minifigur Sawyer OVP", 3.0, _rules_cfg())
    assert r.price_history_model != "lego_sw_rare"


# ============================================================
# 2. LEGO Clone Wars (Kategorie: lego_minifiguren, price_history_model
#    "lego_sw_clone"). Gleiches strukturelles Bug-Muster wie Star Wars,
#    ebenfalls in Phase 12, Schritt 4 gefixt.
# ============================================================

def test_lego_clone_wars_trooper_matcht():
    r = evaluate("LEGO Star Wars Clone Trooper 501st Minifigur", 15.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_sw_clone"


def test_lego_marvel_mit_clone_im_titel_matcht_nicht_als_clone_wars():
    # "clone" allein reicht nicht -- "star wars" muss zwingend vorkommen
    # (zweite, separate require_all_of-Gruppe).
    r = evaluate("LEGO Marvel Spider-Man Minifigur Clone Sammler selten", 20.0, _rules_cfg())
    assert r.price_history_model != "lego_sw_clone"


def test_star_wars_ohne_clone_begriff_matcht_nicht_als_clone_wars():
    r = evaluate("LEGO Star Wars Minifigur C-3PO selten", 12.0, _rules_cfg())
    assert r.price_history_model != "lego_sw_clone"


# ============================================================
# 3. LEGO Ninjago (Kategorie: lego_minifiguren, price_history_model
#    "lego_ninjago_rare"/"lego_ninjago_bundle").
# ============================================================

def test_lego_ninjago_seltene_figur_matcht():
    r = evaluate("LEGO Ninjago Minifigur Kai selten limited", 15.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_ninjago_rare"


def test_lego_harry_potter_matcht_nicht_als_ninjago():
    # Auftrags-Matrix (Abschnitt 16): LEGO Ninjago Positiv=echtes
    # Ninjago-Angebot, Negativ=Harry Potter.
    r = evaluate("LEGO Harry Potter Minifigur Hermine selten limited", 20.0, _rules_cfg())
    assert r.price_history_model != "lego_ninjago_rare"
    assert r.price_history_model != "lego_ninjago_bundle"


def test_lego_star_wars_matcht_nicht_als_ninjago():
    r = evaluate("LEGO Star Wars Minifigur C-3PO selten", 12.0, _rules_cfg())
    assert r.price_history_model != "lego_ninjago_rare"


# ============================================================
# 4. LEGO Bundles (Konvolute/Sammlungen -- price_history_model
#    "lego_ninjago_bundle"/"lego_minifig_bundle"). Einzelfigur darf NICHT
#    als Bundle matchen (fehlende "sammlung"/"konvolut"/"posten"/"lot").
# ============================================================

def test_echtes_ninjago_konvolut_matcht_als_bundle():
    r = evaluate("LEGO Ninjago Minifiguren Konvolut Sammlung 20 Stück", 35.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_ninjago_bundle"


def test_allgemeine_lego_minifiguren_sammlung_matcht_als_bundle():
    r = evaluate("LEGO Minifiguren Sammlung Konvolut 15 Figuren", 12.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "lego_minifig_bundle"


def test_einzelne_ninjago_figur_matcht_nicht_als_bundle():
    r = evaluate("LEGO Ninjago Minifigur Kai selten limited", 15.0, _rules_cfg())
    assert r.price_history_model != "lego_ninjago_bundle"
    assert r.price_history_model != "lego_minifig_bundle"


# ============================================================
# 5. CRT-Monitor (Profi-CRT-Monitor, Kategorie: vintage_elektronik,
#    price_history_model "crt_profi_monitor"). Phase-12-Fix: Vintage-
#    Werbeanzeigen/Anleitungen wurden faelschlich als Geraet gematcht.
# ============================================================

def test_sony_pvm_monitor_matcht():
    r = evaluate("Sony PVM 20L5 Profi Monitor funktioniert", 70.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "vintage_elektronik"
    assert r.price_history_model == "crt_profi_monitor"


def test_sony_pvm_bedienungsanleitung_matcht_nicht():
    # Auftrags-Matrix (Abschnitt 16): CRT Positiv=echter Fernseher/
    # Monitor, Negativ=Bedienungsanleitung.
    r = evaluate("Sony PVM Bedienungsanleitung Original", 8.0, _rules_cfg())
    assert r.matched is False


def test_sony_trinitron_werbeanzeige_matcht_nicht():
    r = evaluate("Sony Trinitron Vintage Werbung Reklame 1985", 5.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# 6. Röhrenfernseher (Kategorie: vintage_elektronik, price_history_model
#    "roehrenfernseher").
# ============================================================

def test_roehrenfernseher_funktionsfaehig_matcht():
    r = evaluate("Röhrenfernseher Grundig 51cm funktioniert einwandfrei", 8.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "roehrenfernseher"


def test_roehrenfernseher_bedienungsanleitung_matcht_nicht():
    r = evaluate("Röhrenfernseher Bedienungsanleitung Original", 3.0, _rules_cfg())
    assert r.matched is False


def test_roehrenfernseher_ersatzteil_matcht_nicht():
    r = evaluate("Röhrenfernseher Ersatzteil Widerstand Platine", 4.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# 7. ThinkPad (Kategorie: notebook_resell, price_history_model
#    "thinkpad_modern"). Phase-12-Fix: fehlende dritte require_all_of-
#    Gruppe (RAM/SSD-Groesse) liess Einzelteile durch.
# ============================================================

def test_thinkpad_t14_mit_ram_ssd_matcht():
    r = evaluate("ThinkPad T14 Ryzen 16GB RAM 512GB SSD", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "notebook_resell"
    assert r.price_history_model == "thinkpad_modern"


def test_thinkpad_x13_mit_ssd_matcht():
    r = evaluate("ThinkPad X13 i5 8GB SSD sehr guter Zustand", 160.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "thinkpad_modern"


def test_thinkpad_ersatzteil_ohne_ram_angabe_matcht_nicht():
    # Auftrags-Matrix (Abschnitt 16): ThinkPad Positiv=Laptop,
    # Negativ=Ersatzteil.
    r = evaluate("ThinkPad T14 Mainboard Ersatzteil defekt", 30.0, _rules_cfg())
    assert r.matched is False


def test_thinkpad_altes_modell_matcht_nicht():
    r = evaluate("ThinkPad T420 16GB RAM 512GB SSD", 100.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# 8. Retro-Konsolen (Kategorie: retro_konsolen). Phase-12-Fix: fehlende
#    zweite require_all_of-Gruppe (Konsolen-Indikator) liess Einzelspiele
#    durch (72% Fehltreffer laut YAML-Kommentar).
# ============================================================

def test_n64_konsole_matcht():
    r = evaluate("Nintendo 64 Konsole mit 2 Controllern funktioniert", 30.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "retro_konsolen"
    assert r.price_history_model == "nintendo_retro_konsole"


def test_ps2_konsole_matcht():
    r = evaluate("PlayStation 2 Konsole mit Netzteil und Controller", 25.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "sony_retro_konsole"


def test_ps2_einzelspiel_matcht_nicht():
    # Auftrags-Matrix (Abschnitt 16): Konsole Positiv=echte Konsole,
    # Negativ=Spiel.
    r = evaluate("PS2 Spiel GTA San Andreas", 8.0, _rules_cfg())
    assert r.matched is False


def test_n64_modul_einzeln_matcht_nicht():
    r = evaluate("N64 Modul Mario Kart 64 lose", 10.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# 9. Handheld-Zubehör (Kategorie: handhelds). Phase-14-Fix: fehlende
#    Excludes fuer Netzteil/Ladekabel/Ladegeraet liessen Zubehoer als
#    komplettes Geraet durch (siehe auch
#    test_matcher_handheld_false_positives.py -- hier zentral gebündelt).
# ============================================================

def test_steam_deck_geraet_matcht():
    r = evaluate("Steam Deck 512GB OLED wie neu", 220.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"
    assert r.price_history_model == "handheld_steam_deck"


def test_ladegeraet_fuer_steam_deck_matcht_nicht():
    # Auftrags-Matrix (Abschnitt 16): Handheld Positiv=echtes Gerät,
    # Negativ=Ladegerät.
    r = evaluate("Ladegerät für Steam Deck original 45W", 15.0, _rules_cfg())
    assert r.matched is False


def test_3ds_xl_konsole_matcht():
    r = evaluate("Nintendo New 3DS XL Konsole guter Zustand", 55.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "handheld_nintendo_3ds"


# ============================================================
# 10. Konsolen-Zubehör (Kategorie: konsolen_bundles). Phase-14-Fix:
#     fehlende Excludes fuer Netzteil/Ladekabel liessen Zubehoer als
#     komplette Konsole durch (Nintendo Switch Lite).
# ============================================================

def test_nintendo_switch_oled_konsole_matcht():
    # "Spielen" (Plural), nicht "Spiel" (Singular): exclude_category
    # "spiel" ist als exaktes Einzelwort hinterlegt und schliesst nur den
    # Singular aus (analog Steam-Deck-Test in
    # test_matcher_handheld_false_positives.py) -- ein Bundle mit
    # mehreren Spielen soll weiterhin matchen, ein reines "mit Spiel"
    # (Singular, potenziell nur 1 Zubehoerspiel ohne Konsole) nicht.
    r = evaluate("Nintendo Switch OLED Konsole OVP mit 2 Spielen", 140.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"
    assert r.price_history_model == "konsole_switch_standard"


def test_switch_lite_geraet_matcht():
    r = evaluate("Nintendo Switch Lite türkis guter Zustand", 80.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "konsole_switch_lite"


def test_ladekabel_fuer_switch_lite_matcht_nicht():
    r = evaluate("Ladekabel für Nintendo Switch Lite Original", 8.0, _rules_cfg())
    assert r.matched is False


def test_switch_huelle_matcht_nicht():
    r = evaluate("Nintendo Switch Hülle Tasche schwarz", 10.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# 11. Controller (Kategorie: controller).
# ============================================================

def test_ps5_dualsense_controller_matcht():
    r = evaluate("PS5 DualSense Controller weiß neuwertig", 20.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"
    assert r.price_history_model == "controller_ps5_dualsense"


def test_xbox_wireless_controller_matcht():
    r = evaluate("Xbox Series Wireless Controller schwarz", 18.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "controller_xbox_series"


def test_ps5_controller_kabel_matcht_nicht():
    # Bewusst bare "Kabel" (nicht "Ladekabel"): controller.yaml fuehrt in
    # exclude_category nur den exakten Begriff "kabel". Wortgrenzen-Matching
    # (matcher.py::_contains_term()) erkennt "kabel" nur als eigenstaendiges
    # Wort, nicht als Teil des zusammengesetzten Worts "Ladekabel" -- ein
    # Titel wie "PS5 Controller Ladekabel USB-C" wuerde AKTUELL trotzdem
    # matchen (verifiziert). Das ist eine potenzielle Luecke analog zum
    # Phase-14-Fix bei handhelds/konsolen_bundles (dort wurde "ladekabel"
    # zusaetzlich als eigener Begriff ergaenzt) -- hier bewusst NICHT
    # nachgezogen, da Phase 15 keine YAML-Aenderungen ohne separate
    # Freigabe vornimmt (STOP 3). Dieser Test dokumentiert nur den
    # tatsaechlich abgesicherten Fall (bare "Kabel").
    r = evaluate("PS5 Controller Kabel USB-C 3m", 5.0, _rules_cfg())
    assert r.matched is False


def test_ps5_controller_huelle_matcht_nicht():
    r = evaluate("PS5 DualSense Controller Hülle Case Silikon", 6.0, _rules_cfg())
    assert r.matched is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
