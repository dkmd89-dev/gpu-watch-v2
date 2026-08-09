"""Tests für den Phase-14-Matching-Fix (PHASE14_DATA_QUALITY_REPORT.md,
Schritt 1): Zubehoer-/Ersatzteil-Fehltreffer in den Kategorien "handhelds"
(Steam Deck, ROG Ally, Lenovo Legion Go) und "konsolen_bundles" (Nintendo
Switch Lite).

Hintergrund: alle vier Regel-Paare hatten bisher eine EINSTUFIGE
require_all_of-Gruppe (nur Markenname), ohne zweite Geraete-Bestaetigung.
Anders als bei retro_konsolen (3ds/n64/ps vita -- kurze, generische
Kuerzel) sind "Steam Deck"/"ROG Ally"/"Legion Go"/"Switch Lite" bereits
eindeutige, mehrwortige Produktnamen und zugleich die Suchbegriffe der
Kategorie (search_terms) -- d.h. JEDES gescrapte Angebot (Geraet UND
Zubehoer) enthaelt den Markennamen zwangslaeufig im Titel. Eine zweite
require_all_of-Gruppe mit Positivbegriffen haette hier keine Trennschaerfe
(siehe rules/handhelds.yaml-Kommentar): sie muesste, damit ein nacktes
"Steam Deck" weiterhin matcht, die Markenbegriffe selbst enthalten -- und
waere dann bei JEDEM Zubehoer-Angebot (das den Markennamen ja ebenfalls
enthaelt) genauso erfuellt. Die tatsaechlich wirksame Korrektur ist daher
eine gezielt erweiterte Exclude-Liste (netzteil/ladekabel/kabel/
ladegerät/anleitung) -- funktional aequivalent zum retro_konsolen-Prinzip
"praezise Phrasen statt Pauschal-Exclude", nur ueber excludes statt eine
wirkungslose zweite Gruppe umgesetzt.

Alle Tests laufen gegen die ECHTEN, produktiven rules/*.yaml (load_rules()
ohne synthetische rules_cfg), analog zu
test_matcher_price_calibration_matching_fixes.py.
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
# Steam Deck (Kategorie: handhelds)
# ============================================================

def test_steam_deck_nackter_titel_matcht_weiterhin():
    r = evaluate("Steam Deck", 200.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"
    assert r.price_history_model == "handheld_steam_deck"


def test_steam_deck_mit_kapazitaet_matcht_weiterhin():
    r = evaluate("Steam Deck 256GB", 200.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "handheld_steam_deck"


def test_steam_deck_oled_matcht_weiterhin():
    r = evaluate("Steam Deck OLED", 220.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "handheld_steam_deck"


def test_steam_deck_bundle_mit_spielen_matcht_weiterhin():
    # Anforderung 6: echtes Geraet + Spiele/Zubehoer im selben Angebot
    # muss weiterhin matchen -- das globale "spiel"-Exclude greift nur
    # beim exakten Einzelwort "Spiel", nicht bei "Spiele" (Plural).
    r = evaluate("Steam Deck + 5 Spiele OVP", 220.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "handheld_steam_deck"


def test_netzteil_fuer_steam_deck_matcht_nicht_mehr():
    # Regressionsschutz fuer den urspruenglichen Bug (PHASE14-Report):
    # 15 EUR, matchte vorher als handheld_steam_deck / Top-Deal / Score 91.
    r = evaluate("Netzteil für Steam Deck 45W", 15.0, _rules_cfg())
    assert r.matched is False


def test_steam_deck_ladekabel_matcht_nicht():
    r = evaluate("Steam Deck Ladekabel USB-C original", 10.0, _rules_cfg())
    assert r.matched is False


def test_steam_deck_huelle_matcht_weiterhin_nicht():
    r = evaluate("Steam Deck Hülle Tasche schwarz", 12.0, _rules_cfg())
    assert r.matched is False


def test_steam_deck_display_ersatzteil_matcht_weiterhin_nicht():
    r = evaluate("Steam Deck Display Ersatzteil defekt", 20.0, _rules_cfg())
    assert r.matched is False


def test_anleitung_steam_deck_matcht_nicht_mehr():
    r = evaluate("Anleitung Steam Deck OVP", 5.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# ROG Ally / Lenovo Legion Go (Kategorie: handhelds)
# ============================================================

def test_rog_ally_matcht_weiterhin():
    r = evaluate("ROG Ally Z1 Extreme 512GB", 300.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "handhelds"
    assert r.price_history_model == "handheld_pc_preator"


def test_legion_go_matcht_weiterhin():
    r = evaluate("Lenovo Legion Go 512GB wie neu", 300.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "handheld_pc_preator"


def test_netzteil_fuer_rog_ally_matcht_nicht_mehr():
    r = evaluate("Netzteil für ROG Ally", 15.0, _rules_cfg())
    assert r.matched is False


def test_legion_go_ladegeraet_matcht_nicht_mehr():
    r = evaluate("Legion Go Ladegerät original", 15.0, _rules_cfg())
    assert r.matched is False


# ============================================================
# Nintendo Switch Lite (Kategorie: konsolen_bundles)
# ============================================================

def test_switch_lite_matcht_weiterhin():
    r = evaluate("Nintendo Switch Lite türkis", 80.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"
    assert r.price_history_model == "konsole_switch_lite"


def test_switch_lite_bundle_mit_spielen_matcht_weiterhin():
    r = evaluate("Nintendo Switch Lite + 3 Spiele OVP", 90.0, _rules_cfg())
    assert r.matched is True
    assert r.price_history_model == "konsole_switch_lite"


def test_ladekabel_fuer_switch_lite_matcht_nicht_mehr():
    # Regressionsschutz fuer den urspruenglichen Bug (PHASE14-Report):
    # 8 EUR, matchte vorher als konsole_switch_lite / Top-Deal / Score 88.
    r = evaluate("Ladekabel für Nintendo Switch Lite Original", 8.0, _rules_cfg())
    assert r.matched is False


def test_switch_lite_huelle_matcht_nicht():
    r = evaluate("Nintendo Switch Lite Hülle Grau", 6.0, _rules_cfg())
    assert r.matched is False
