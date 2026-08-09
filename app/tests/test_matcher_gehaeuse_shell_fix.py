"""Regressionstests für den Gehäuse/Shell-Fix (Phase 15, kontrollierter
Folge-Review nach dem Service/Modding-Fix).

Hintergrund: "Gehäuse" ist im Gegensatz zu "ladekabel" (Variante C) oder
"modding service" ZWEIDEUTIG -- es bezeichnet sowohl lose Standalone-
Ersatzschalen ("Nintendo 3DS XL Gehäuse Blau", "Modulares Steam Deck
Gehäuse mit Kühlventilator und Zubehör") als auch die übliche
Zustandsbeschreibung eines kompletten Geräts ("Gehäuse leicht
vergilbt/verkratzt"). Ein bare exclude_category-Eintrag würde daher
nachweislich echte Geräteangebote fälschlich blockieren.

Fix: zwei Bausteine pro betroffener Kategorie (handhelds, controller,
konsolen_bundles, retro_konsolen, iphone, macbook):

1. Neuer kontextbewusster Matcher-Mechanismus
   "exclude_category_unless_also_contains" (matcher.py::
   _any_conditional_exclude_presence()): schließt einen Begriff NUR aus,
   wenn im GESAMTEN Titel kein Begriff aus einer Kontext-/Zustandsliste
   vorkommt -- bewusst eine titelweite Präsenzprüfung statt einer
   Adjazenzregel wie bei Variante C, weil Zustandsbeschreibungen in
   wechselndem Abstand zum Begriff stehen ("Gehäuse: leicht vergilbt" vs.
   "... Gehäuse hat leichte Kratzer").
2. Unbedingte exclude_category-Ergänzungen für zusammengesetzte Wörter
   ("ersatzgehäuse" -- enthält "gehäuse" NICHT als eigenes Wort, siehe
   _contains_term()-Wortgrenzen) und englische Begriffe ("replacement
   shell", "backplate", ...), die "gehäuse" gar nicht enthalten.

Läuft gegen die echten, produktiven rules/*.yaml, analog zu
test_rule_service_modding_fix.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import (
    _any_conditional_exclude_presence,
    load_rules,
    evaluate,
)

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


CONDITION_WORDS = ["vergilbt", "verkratzt", "zerkratzt", "beschädigt", "neuwertig"]


# ============================================================
# 1. Unit-Tests: _any_conditional_exclude_presence() direkt
# ============================================================

def test_standalone_ohne_kontextbegriff_wird_ausgeschlossen():
    cond = {"gehäuse": CONDITION_WORDS}
    assert _any_conditional_exclude_presence(
        "nintendo 3ds xl gehäuse blau - japan", cond
    ) is True


def test_kontextbegriff_direkt_danach_verhindert_exclude():
    cond = {"gehäuse": CONDITION_WORDS}
    assert _any_conditional_exclude_presence(
        "n64 konsole gehäuse leicht vergilbt sonst neuwertig", cond
    ) is False


def test_kontextbegriff_mit_abstand_verhindert_exclude():
    # Der Kontextbegriff steht NICHT unmittelbar neben "gehäuse" -- anders
    # als Variante C ist das hier bewusst erlaubt (titelweite Prüfung,
    # keine Adjazenzregel).
    assert _any_conditional_exclude_presence(
        "iphone 11 64gb, display neuwertig, gehäuse hat leichte kratzer",
        {"gehäuse": CONDITION_WORDS},
    ) is False


def test_kontextbegriff_vor_dem_begriff_verhindert_ebenfalls_exclude():
    assert _any_conditional_exclude_presence(
        "macbook air, gehäuse und tastatur neuwertig",
        {"gehäuse": CONDITION_WORDS},
    ) is False


def test_ohne_den_geprueften_begriff_nie_exclude():
    assert _any_conditional_exclude_presence(
        "ps5 dualsense controller weiß neuwertig", {"gehäuse": CONDITION_WORDS}
    ) is False


def test_leeres_dict_greift_nie():
    assert _any_conditional_exclude_presence("gehäuse blau", {}) is False


def test_or_verknuepfung_mehrerer_begriffe():
    cond = {"gehäuse": CONDITION_WORDS, "shell": ["scratched", "used"]}
    assert _any_conditional_exclude_presence("steam deck back replacement shell", cond) is True
    assert _any_conditional_exclude_presence("steam deck, shell slightly scratched", cond) is False
    assert _any_conditional_exclude_presence("steam deck 256gb", cond) is False


# ============================================================
# 2. Integrationstests gegen die echten rules/*.yaml -- pro Kategorie:
#    a) die drei Original-Funde (soweit zutreffend) + Varianten müssen
#       blockiert werden, b) ein Gerät MIT Zustandsbeschreibung muss
#       weiterhin matchen.
# ============================================================

def test_handhelds_standalone_gehaeuse_matcht_nicht():
    # Ursprünglicher Dashboard-Fund.
    r = evaluate("Nintendo 3DS XL Gehäuse Blau - Japan", 5.0, _rules_cfg())
    assert r.matched is False


def test_handhelds_steam_deck_replacement_shell_matcht_nicht():
    r = evaluate("Steam Deck Back Replacement Shell", 15.0, _rules_cfg())
    assert r.matched is False


def test_handhelds_modulares_steam_deck_gehaeuse_matcht_nicht():
    r = evaluate(
        "Modulares Steam Deck Gehäuse mit Kühlventilator und Zubehör",
        45.0, _rules_cfg(),
    )
    assert r.matched is False


def test_handhelds_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "Nintendo 3DS XL Konsole neuwertig, Gehäuse leicht vergilbt",
        40.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "handhelds"


def test_handhelds_steam_deck_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "Valve Steam Deck 256GB, Gehäuse minimal verkratzt sonst top",
        150.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "handhelds"


def test_controller_ersatzgehaeuse_matcht_nicht():
    r = evaluate("PS5 Controller Ersatzgehäuse schwarz", 8.0, _rules_cfg())
    assert r.matched is False


def test_controller_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "PS5 DualSense Controller weiß neuwertig, Gehäuse minimal verkratzt",
        20.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "controller"


def test_konsolen_bundles_leergehaeuse_matcht_nicht():
    r = evaluate(
        "Nintendo Switch OLED Leergehäuse ohne Elektronik", 15.0, _rules_cfg()
    )
    assert r.matched is False


def test_konsolen_bundles_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "Nintendo Switch OLED Konsole, Gehäuse leicht zerkratzt sonst top",
        130.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_retro_konsolen_standalone_gehaeuse_matcht_nicht():
    r = evaluate("N64 Gehäuse gelb ohne Platine", 10.0, _rules_cfg())
    assert r.matched is False


def test_retro_konsolen_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    # Retro-Konsolen: "vergilbtes Gehäuse" ist ein besonders häufiges,
    # legitimes Zustandsmerkmal (UV-Vergilbung alter Kunststoffgehäuse).
    r = evaluate(
        "N64 Konsole Gehäuse leicht vergilbt sonst neuwertig", 30.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "retro_konsolen"


def test_iphone_ersatzgehaeuse_matcht_nicht():
    r = evaluate("iPhone 12 Ersatzgehäuse Backcover", 12.0, _rules_cfg())
    assert r.matched is False


def test_iphone_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "iPhone 11 64GB space grau, Gehäuse minimal verkratzt Akku 89%",
        65.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "iphone"


def test_macbook_wechselgehaeuse_matcht_nicht():
    r = evaluate("MacBook Pro Wechselgehäuse Oberschale silber", 25.0, _rules_cfg())
    assert r.matched is False


def test_macbook_geraet_mit_gehaeuse_zustand_matcht_weiterhin():
    r = evaluate(
        "MacBook Air Intel i5 256GB, Gehäuse leicht verkratzt", 130.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "macbook"


# ============================================================
# 3. Sicherheitsprüfung: bestehendes Verhalten (Service/Modding-Fix,
#    Variante C, reguläre Geräteangebote) bleibt unberührt.
# ============================================================

def test_service_modding_fix_bleibt_unveraendert():
    r = evaluate(
        "Modding Service für alle Nintendo Modelle / New 3DS / 2DS XL",
        25.0, _rules_cfg(),
    )
    assert r.matched is False


def test_controller_ladekabel_variante_c_bleibt_unveraendert():
    r = evaluate("PS5 Controller Ladekabel USB-C 3m", 5.0, _rules_cfg())
    assert r.matched is False
    r_bundle = evaluate(
        "PS5 DualSense Controller inkl. Ladekabel", 20.0, _rules_cfg()
    )
    assert r_bundle.matched is True


def test_regulaeres_geraet_ohne_gehaeuse_erwaehnung_matcht_weiterhin():
    r = evaluate("Xbox Series Wireless Controller schwarz", 18.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
