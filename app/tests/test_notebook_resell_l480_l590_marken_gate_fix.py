"""Regressionstests für den L480/L590-Marken-Gate-Fix, Variante A
(2026-08-16, siehe Analysebericht "L480/L590 Marken-Gate Impact
Analysis").

Root Cause: "Lenovo Laptop L480..." und "Notebook Lenovo L590..." waren
trotz bereits vollständig erfüllter Modellcode- und Größen-Gruppe
(Gruppe 2/3 der ThinkPad-Regel, siehe Batch A1/A2) weiterhin unmatched,
weil die Marken-Gate-Gruppe (Gruppe 1) zwingend "thinkpad"/"think pad"
verlangte und beide Titel dieses Wort nicht enthalten.

Fix: "l480"/"l590" zusätzlich als Marken-Alternative in Gruppe 1 beider
ThinkPad-Preisstufen ergänzt (additiv, bestehende Struktur unverändert).
Gegen eine separate "Lenovo"+Modellcode-Regel (Variante B) abgewogen und
bevorzugt: bleibt konsistent mit der bestehenden Ein-Regel-Struktur und
deckt zusätzlich reale Titel wie "ThinkPad L480 ..." (ohne das Wort
"Lenovo") ab.

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


# ---------------------------------------------------------------
# Die beiden Ziel-Recall-Gaps matchen jetzt
# ---------------------------------------------------------------

def test_l480_matcht_jetzt():
    r = evaluate(
        "Lenovo Laptop L480 - Core i5 8250u - 8GB DDR4 - 256 GB NVMe - WIN",
        125.0,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "notebook_resell"
    assert r.rule_label == "ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top"


def test_l590_matcht_jetzt():
    r = evaluate(
        "Notebook Lenovo L590 16GB RAM, 500GB SSD, Win11 Pro Core i5 8265u",
        150.0,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "notebook_resell"
    assert r.rule_label == "ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top"


def test_thinkpad_l480_ohne_lenovo_wort_matcht_ebenfalls():
    # Zusaetzlicher, von Variante A (nicht von Variante B) abgedeckter
    # realistischer Fall: "ThinkPad L480" ohne das Wort "Lenovo".
    r = evaluate(
        "ThinkPad L480 14 Zoll i5-8250U 8GB RAM 256GB SSD Win11", 150.0, _rules_cfg()
    )
    assert r.matched is True and r.category == "notebook_resell"


# ---------------------------------------------------------------
# Bestehende ThinkPad-Titel bleiben unveraendert
# ---------------------------------------------------------------

def test_bestehende_thinkpad_titel_bleiben_unveraendert():
    for title, price, expected_rule in [
        (
            "Lenovo ThinkPad T14 Gen1 i5 10310U 16GB RAM 256GB SSD 14\" FHD "
            "Win 11 Pro MwSt.",
            299.99,
            "ThinkPad T14/X13 (Ryzen/Modern)",
        ),
        (
            "Lenovo ThinkPad E15 15,6\" i5-10210U 16GB RAM 500GB SSD Win11 Pro",
            250.0,
            "ThinkPad T14/X13 (Ryzen/Modern)",
        ),
        (
            "Lenovo ThinkPad T14 Gen 1 i5-10310U 16GB RAM 512GB SSD", 180.0,
            "ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top",
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title
        assert r.rule_label == expected_rule, title


def test_thinkpad_exclude_modelle_bleiben_ausgeschlossen():
    r = evaluate("ThinkPad T430 i5 8GB RAM 256GB SSD", 100.0, _rules_cfg())
    assert not (r.matched and r.category == "notebook_resell")


# ---------------------------------------------------------------
# Zubehoer-/Komponenten-Faelle bleiben ausgeschlossen
# ---------------------------------------------------------------

def test_l480_l590_zubehoer_ohne_groessenangabe_matcht_nicht():
    for title in [
        "Lenovo L480 Laptop",
        "Lenovo L590 Notebook",
        "Lenovo L480 Akku",
        "Lenovo L590 Netzteil",
        "Lenovo L480 Tastatur deutsch QWERTZ",
        "Lenovo L590 Dockingstation",
    ]:
        r = evaluate(title, 100.0, _rules_cfg())
        assert not (r.matched and r.category == "notebook_resell"), title


def test_l480_l590_mainboard_bleibt_geblockt():
    for title in [
        "Lenovo L480 Mainboard 8GB RAM",
        "Lenovo L590 Mainboard 16GB RAM 256GB SSD",
    ]:
        r = evaluate(title, 100.0, _rules_cfg())
        assert not (r.matched and r.category == "notebook_resell"), title


# ---------------------------------------------------------------
# Cross-Category: andere A3-A7-Zielgruppen unveraendert
# ---------------------------------------------------------------

def test_andere_a3_a7_marken_unveraendert():
    r1 = evaluate(
        "Dell Latitude 5501 15,6\" FHD | i5-9400H | 8GB RAM | 250GB SSD",
        229.0,
        _rules_cfg(),
    )
    assert r1.matched is True and r1.rule_label == "Dell Latitude"

    r2 = evaluate(
        "ACEMAGIC 16'' FHD Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM 512GB SSD "
        "Win11 Pro",
        289.0,
        _rules_cfg(),
    )
    assert r2.matched is True and r2.rule_label == "ACEMAGIC Laptop"

    r3 = evaluate(
        "HP Laptop 17,5 Zoll – Ryzen 5 5500U – 8 GB DDR4", 100.0, _rules_cfg()
    )
    assert not (r3.matched and r3.category == "notebook_resell")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
