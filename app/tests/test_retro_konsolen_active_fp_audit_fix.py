"""Regressionstests für den retro_konsolen-Fix aus dem Active-False-
Positive-Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: `retro_konsolen.yaml` akzeptiert "memory card" als
Gruppe-2-Geräte-Signal (require_all_of), um echte Bundles zu retten, die
über kein anderes Signalwort verfügen (z.B. "Playstation 1 original mit
Controller, Spielen und Memory Card" -- kein "konsole"/"system"/"slim"/
"fat"/"komplett" im Titel). Dasselbe Signal reicht aber auch für
Standalone-Speicherkarten-Angebote OHNE jedes Gerät aus (6 reale
Fehltreffer in found.json, u.a. "Nintendo Gamecube Memory Card",
5EUR).

Ein einfaches Entfernen von "memory card" aus Gruppe 2 wurde geprüft und
verworfen: es hätte 2 reale TRUE_POSITIVE-Bundles zerstört
("Playstation 1 original mit Controller, Spielen und Memory Card",
"PlayStation 2 Slimline Silber - Ersatzkonsole + Memory Card -
SCPH-77004"), die ausschließlich über "memory card" ihr Gruppe-2-
Kriterium erfüllen. Ein unbedingter exclude_category-Eintrag für
"memory card" hätte dieselben beiden Titel zerstört.

Fix: kontextbewusster Exclude (exclude_category_unless_also_contains,
bereits für "gehäuse" in dieser Datei etabliert) -- blockiert "memory
card" nur, wenn im GESAMTEN Titel kein Geräte-Kontextbegriff
("controller"/"konsole"/"ersatzkonsole") vorkommt. Verifiziert: alle 6
bekannten Fehltreffer korrekt blockiert, alle bekannten TRUE_POSITIVE-
Titel mit "memory card" (auch die, die zusätzlich über andere
Gruppe-2-Wörter verfügen) bleiben unverändert erhalten.

Zusätzlich zwei neue bare exclude_category-Terme für real bestätigte
Standalone-Zubehör-Angebote: "zubehör-set" (Bindestrich-Variante, andere
Formulierung als das bereits vorhandene "zubehörpaket") und
"ersatznetzteil" (Kompositum, von bare "netzteil" -- das als
Bundle-Signal bewusst erhalten bleibt -- nicht erfasst).

Bewusst NICHT Teil dieses Fixes (siehe Audit-Doku, P1/P2/NO-FIX):
- 11 Einzelspiel-Titel, die über "komplett" matchen (z.B. "Silent Hill
  – PlayStation 1 – Komplett & in hervorragendem Zustand") -- identisches
  Muster zur bereits in einem früheren Arbeitsblock (konsolen_bundles)
  als unsicher zurückgestellten "Spieltitel-vor-Plattform"-Lücke, kein
  kollisionsfreies Substring-Muster ohne Spieltitel-Datenbank
  identifiziert.
- "Nintendo Netzteil für Nintendo DS USG-002..." -- identisches Muster
  zum bereits in konsolen_bundles gelösten "[Zubehör] für [Plattform]"-
  Fall, würde aber den vollen Geräte-Marker-Mechanismus erfordern
  (eigener, größerer Arbeitsschritt).
- "Nintendo DS ... Display LCD Bildschirm oben oder unten" (Ersatzteil,
  1 Titel) -- zu wenig Evidenz für eine verallgemeinerbare Regel.
- "Flohmarkt, Trödel Konvolut, Vtech, Konsole, Kleidung, Dvds" -- zeigt
  strukturelles Risiko der Konvolut-Regel (bare "konsole"/"nintendo" als
  Gruppe-1-Signal), aber nur 1 bestätigter Fall, Fix würde Gruppe-1-Logik
  anfassen -- eigener Arbeitsschritt.

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


def _matches_retro(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "retro_konsolen"


# ============================================================
# 1. Standalone Memory Cards -- müssen jetzt blockiert werden.
# ============================================================

def test_standalone_memory_cards_matchen_nicht():
    for title, price in [
        ("Nintendo Gamecube Memory Card", 5.0),
        ("Original Sony PS2 Memory Card 8 MB – Transparent Blau – MagicGate", 15.0),
        (
            "Playstation 1 Memory Card 1MB Speicherkarte für PS1 / PSX / PSone *NEU*",
            5.35,
        ),
        ("PS / PlayStation (PS1 / PSX) ORIGINAL Memory Card Speicherkarte 💾☑️", 24.95),
        (
            "PS2 / PlayStation 2 ORIGINAL Sony 8 MB Memory Card Speicherkarte Getestet",
            10.95,
        ),
        ("Sony Multitap  Playstation 2  PS2  Memory Card  A B C D", 10.0),
    ]:
        assert _matches_retro(title, price) is False, title


# ============================================================
# 2. Standalone Zubehör-Set / Ersatznetzteil -- müssen jetzt blockiert
#    werden.
# ============================================================

def test_zubehoer_set_matcht_nicht():
    assert _matches_retro(
        "N64 / Nintendo 64 Zubehör-Set Auswahl 🤔✅ Netzteil, Kabel, Expansion, Jumper Pak",
        69.95,
    ) is False
    assert _matches_retro(
        "PS2 / PlayStation 2 ORIGINAL Zubehör-Set Auswahl: Netzkabel Anschluss AV Kabel",
        49.95,
    ) is False


def test_ersatznetzteil_matcht_nicht():
    assert _matches_retro(
        "N64 USB-C Netzteil für Nintendo 64 Ersatznetzteil", 30.0
    ) is False


# ============================================================
# 3. Sicherheitsprüfung: reale TRUE_POSITIVE-Bundles mit "memory card"
#    bleiben unverändert erhalten -- inkl. der beiden Titel, die
#    AUSSCHLIESSLICH über "memory card" ihr Gruppe-2-Kriterium erfüllen.
# ============================================================

def test_memory_card_bundles_mit_geraetekontext_matchen_weiterhin():
    for title, price in [
        (
            "Playstation 1 original mit Controller, Spielen und Memory Card",
            79.0,
        ),
        (
            "PlayStation 2 Slimline Silber - Ersatzkonsole + Memory Card - SCPH-77004",
            39.99,
        ),
        (
            "PS2 Fat + 2 Controller + 8 MB Memory Card + Budokai Tenkaichi 3",
            75.0,
        ),
        (
            "Sony PlayStation 1 PS1 Konsole SCPH-5502 mit Controller, Kabeln und Memory Card",
            69.99,
        ),
        (
            "Sony Playstation 2 FAT  (SCPH-30004) inklusive Controller und Memory Card",
            89.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "retro_konsolen", title


def test_weitere_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Kellerfund: Nintendo 64 Konsole mit 2 Controllern und 8 Spielen", 75.0),
        ("Nintendo 64 Konsole", 30.0),
        (
            "NGC - Nintendo GameCube Konsole mit Controller + HDMI (gebrauchter Zustand)",
            84.95,
        ),
        ("Nintendo Gamecube NUR Konsole Ersatzkonsole - geprüft ", 59.99),
        ("Sony PlayStation 2 - PS2 Fat Konsole silber + 2 Controller", 85.05),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "retro_konsolen", title


def test_grenzfall_bindestrich_zwischen_marke_und_vollname_matcht_weiterhin():
    # Grenzfall: "N64 - Nintendo 64 Konsole ..." enthält einen Bindestrich
    # zwischen Markenkuerzel und Vollname (kein Spieltitel-vor-Plattform-
    # Muster) -- darf durch den neuen "memory card"-Kontext-Mechanismus
    # nicht betroffen sein (er enthaelt "memory card" gar nicht, dient
    # hier nur als generelle Bindestrich-Sicherheitspruefung).
    r = evaluate("N64 - Nintendo 64 Konsole Einzeln - NUS-001 (EUR)", 60.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "retro_konsolen"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
