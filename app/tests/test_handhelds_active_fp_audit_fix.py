"""Regressionstests für den handhelds-Fix aus dem Active-False-Positive-
Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: systematischer Abgleich aller aktuell live matchenden
handhelds-Treffer gegen den echten found.json-Korpus (mit den realen
Preisen, nicht price=0.0 -- ein Test mit price=0.0 verzerrt First-Match-
Wins bei preisgedeckelten Regeln in anderen Kategorien, siehe Audit-Doku).
Von 22 aktuell matchenden handhelds-Treffern waren 10 real aktive
Standalone-Zubehör-/Ersatzteil-/Software-Fehltreffer:

- Displayschutz (Kompositum, von bare "display" nicht erfasst)
- Controller-Grip-Zubehör ("grip" existierte bereits in controller.yaml,
  fehlte aber in handhelds.yaml)
- Ersatzstift/Ersatzstifte/Touchpen/Stylus (Eingabestift-Ersatzteile)
- Schutzhülle (Kompositum, von bare "hülle" nicht erfasst)
- leere Sammler-Verpackung ("LEERE BOX", kein "OVP"-Text im Titel)
- "Spiele für X Konsole" (Software-Angebot, Pluralform zu "spiel für")
- "Controller Rechts" (einzelne, abgetrennte Legion-Go-Controller-Hälfte)
- Flash-Karte/Spielkarte (Speicherkarten-/Flashcart-Produkt)

Alle 10 Begriffe wurden gegen den vollständigen found.json-Korpus (1736
eindeutige Titel) verifiziert: jeder Begriff kommt in Kombination mit
einem Handheld-Markennamen AUSSCHLIESSLICH im jeweils identifizierten
Fehltreffer-Titel vor -- 0 Kollisionen.

Bewusst NICHT Teil dieses Fixes (siehe Audit-Doku, P1/P2/NO-FIX):
- Fanxiang M.2 2230 SSD-Ersatzteile für Steam Deck (enger Kandidat,
  eigener Review-Schritt)
- "Nintendo 2DS ... für Nintendo 3DS Plattform" (echter TRUE_POSITIVE,
  der bei einem naiven "für Plattform"-Exclude kollidieren würde --
  bräuchte den vollen Geräte-Marker-Mechanismus aus konsolen_bundles.yaml)
- USB-C-HDMI-Adapter (Kollisionsrisiko mit echten Spec-Angaben)
- "Lenovo Legion Go" bare, 15EUR (kein Zubehör-Signal im Titel, nicht
  sicher unterscheidbar)

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


def _matches_hh(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "handhelds"


# ============================================================
# 1. Reale, im Active-FP-Audit bestätigte Fehltreffer -- müssen jetzt
#    blockiert werden. Alle Titel/Preise 1:1 aus found.json.
# ============================================================

def test_displayschutz_kompositum_matcht_nicht():
    assert _matches_hh(
        "2x 9H Gehärtetes Displayschutz für Lenovo Legion Go Anti-Kratzer HD Klar", 8.90
    ) is False


def test_controller_grip_zubehoer_matcht_nicht():
    assert _matches_hh(
        "Ergonomischer Performance Controller Grip passend für Lenovo Legion Go 2 Zubehör",
        19.99,
    ) is False


def test_ersatzstifte_matcht_nicht():
    assert _matches_hh(
        "Ersatzstifte für die Konsolen Nintendo DSi XL Nintendo 2DS", 59.49
    ) is False


def test_touchpen_stylus_ersatzstift_matcht_nicht():
    assert _matches_hh(
        "Nintendo 3DS & New 3DS Touchpen Stylus Ersatzstift Eingabe Stift XL schwarz", 3.99
    ) is False
    assert _matches_hh(
        "Nintendo DS 2DS 3DS Wii U Touchpen Stylus Ersatzstift Touch New XL Lite NDSL", 3.99
    ) is False


def test_schutzhuelle_kompositum_matcht_nicht():
    assert _matches_hh("Schutzhülle für Lenovo Legion Go - Neu", 15.00) is False


def test_leere_box_matcht_nicht():
    assert _matches_hh(
        "Originalverpackung Nintendo New 2DS XL Pokeball Edition LEERE BOX mit Inlay", 85.00
    ) is False


def test_spiele_fuer_konsole_matcht_nicht():
    assert _matches_hh("Spiele für NINTENDO 3DS XL Konsole - Top", 10.00) is False


def test_controller_rechts_matcht_nicht():
    assert _matches_hh("Lenovo Legion Go Controller Rechts", 65.00) is False


def test_flash_karte_spielkarte_matcht_nicht():
    assert _matches_hh(
        "Videospiel Flash Karte 128GB SDHC Nintendo DS 3DS 2DS New 3DS Spielkarte", 41.90
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Handheld-Treffer aus
#    found.json bleiben unverändert erhalten (echte Preise verwendet,
#    nicht price=0.0 -- siehe Audit-Methodik-Hinweis).
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Asus ROG ally  z1 extream mit 512gb und mod fan konsistent peform", 310.0),
        ("Lenovo Legion Go S 8ARP1 Ryzen Z2 16GB 512GB", 220.0),
        ("New Nintendo 3DS XL OVP Schwarz – Originalverpackung", 75.0),
        ("Nintendo 2DS Konsole handheld", 30.0),
        (
            "Nintendo 3DS Schwarz Metallic Zustand Ok, Voll Funktionsfähig, nur Konsole",
            89.99,
        ),
        ("Nintendo 3DS XL Rot/Schwarz SPR-001", 95.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "handhelds", title


def test_grenzfall_fuer_plattform_mit_geraetemarker_matcht_weiterhin():
    # Kritischer Grenzfall: dieser Titel enthält "für Nintendo 3DS" (wie
    # das neue "spiele für"-Exclude, aber Singular "spielt keine Rolle" --
    # hier ist es eine reine Kompatibilitäts-/Plattform-Angabe eines
    # ECHTEN Geräts, kein Software-Angebot). Ein zu breiter "für"-Exclude
    # würde das brechen -- deshalb wurde bewusst NUR "spiele für" (die
    # exakte Software-Phrase) ergänzt, kein generischer "für"-Exclude.
    r = evaluate(
        "Nintendo 2DS Handheld-System Konsole für Nintendo 3DS Plattform Weiß/Rot",
        74.99,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "handhelds"


def test_pokemon_edition_mit_spielen_matcht_weiterhin():
    # Bereits bestehende Auftragsvorgabe (test_handhelds_zubehoer_ersatzteil_fix.py):
    # "spiele" bleibt für echte Bundles gültig, nur "spiele für" (Software-
    # Angebot ohne Gerät) wird blockiert.
    r = evaluate(
        "Nintendo 3DS XL Pokémon Edition inkl. 6 Pokémon Spielen", 0.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "handhelds"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
