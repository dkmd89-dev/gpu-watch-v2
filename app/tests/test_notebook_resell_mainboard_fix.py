"""Regressionstests für den notebook_resell-Mainboard-Fix (kontrollierter
Review, freigegeben nach DASHBOARD_MATCH_FORENSICS.md).

Hintergrund: "Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM
NM-B891" matchte fälschlich als komplettes Notebook. Ursache: die dritte
require_all_of-Gruppe der ThinkPad-Regeln (RAM-/SSD-Größenangabe,
ursprünglich gegen Einzelteil-Angebote wie Power-Button/Lautsprecher/
Gehäuse/Kühler eingeführt) wird auch von einem BLOSSEN Mainboard erfüllt,
weil dessen eigene verlötete/aufgesteckte RAM-Menge im Titel genannt wird
-- ohne dass ein komplettes Notebook angeboten wird.

Fix: "mainboard"/"motherboard" als bare exclude_category-Einträge in
notebook_resell.yaml ergänzt (Begründung: niemand bewirbt ein komplettes,
funktionierendes Notebook mit dem Wort "Mainboard"/"Motherboard").
Verifiziert gegen alle 59 damals sichtbaren TRUE_POSITIVE-Treffer dieser
Kategorie: 0 Kollisionen.

Auftragsvorgabe: KEIN pauschales Entfernen von Notebook-/ThinkPad-
Signalen -- gezielter, eng gefasster Exclude, bestehender Mechanismus
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


def _matches_nb(title, price=0.0):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "notebook_resell"


# ============================================================
# 1. Mainboard/Motherboard-Einzelteile -- müssen blockiert werden.
# ============================================================

def test_thinkpad_x390_mainboard_matcht_nicht():
    assert _matches_nb(
        "Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM NM-B891"
    ) is False


def test_thinkpad_t490s_mainboard_matcht_nicht():
    assert _matches_nb(
        "Lenovo ThinkPad T490s Mainboard nm-b891 Intel i5-8365U / i5-8265U 8GB RAM"
    ) is False


def test_weitere_mainboard_motherboard_varianten_matchen_nicht():
    assert _matches_nb("ThinkPad T14 Motherboard defekt, 16GB RAM verlötet") is False
    assert _matches_nb("ThinkPad X13 Mainboard mit 32GB RAM, funktionsfähig") is False
    assert _matches_nb("Lenovo ThinkPad L14 Motherboard NM-C871 8GB") is False


# ============================================================
# 2. Echte ThinkPad-/Notebook-Angebote -- müssen weiterhin matchen
#    (Sicherheitsprüfung gegen Overblocking).
# ============================================================

def test_echtes_thinkpad_ohne_mainboard_wort_matcht_weiterhin():
    r = evaluate("ThinkPad X13 16GB RAM 512GB SSD, guter Zustand", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "notebook_resell"


def test_echtes_thinkpad_t490_matcht_weiterhin():
    r = evaluate("ThinkPad T490 8GB 256GB SSD, guter Zustand", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "notebook_resell"


def test_gaming_laptop_matcht_weiterhin():
    r = evaluate("Lenovo Legion 5 RTX 3060 16GB Gaming Laptop", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "notebook_resell"


def test_thinkpad_mit_netzteil_und_tasche_matcht_weiterhin():
    # Sicherheitsprüfung: bestehendes, bewusst NICHT als bare-word-
    # Exclude gesetztes Zubehör ("Netzteil"/"Tasche" als Kaufargument)
    # bleibt von diesem Fix unberührt.
    r = evaluate(
        "ThinkPad X390 16GB RAM 256GB SSD inkl. Netzteil und Tasche",
        0.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "notebook_resell"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
