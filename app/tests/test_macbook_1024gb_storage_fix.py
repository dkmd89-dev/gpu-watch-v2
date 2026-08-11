"""Regressionstests für den macbook-"1024GB"-Speichergrößen-Fix
(Cross-Category Routing Audit, docs/CROSS_CATEGORY_ROUTING_AUDIT.md,
Abschnitt 5.2).

Hintergrund: die ≥1TB-`require_all_of`-Gruppe in `macbook.yaml` kannte
bisher nur "1tb"/"1 tb"/"2tb"/"2 tb" als Speichergrößen-Signal -- nicht
aber die (v.a. bei "About This Mac"/Finder-Anzeigen übliche)
"1024GB"-Schreibweise für exakt dieselbe 1TB-Speichergröße. Ein realer
Titel ("Apple MacBook Pro 16.1 | i9-9880H | 16GB RAM 1024GB SSD OHNE OS
QWERTY | Nr. 1", 299€) fiel dadurch durch ALLE macbook-Regeln (Marke +
Chip erkannt, Speichergröße nicht) und landete zuvor fälschlich in
`office_pc` (dort mittlerweile durch den Notebook-Exclude behoben,
siehe test_office_pc_notebook_cross_category_fix.py) statt in der
eigens dafür vorhandenen `macbook`-Kategorie.

Fix: "1024gb"/"1024 gb" als Schreibweisen-Synonym zu "1tb"/"2tb" in
allen 30 betroffenen ≥1TB-Regeln ergänzt (Air+Pro, Intel/M1-M4, je drei
Preisstufen) -- reine Vervollständigung derselben physischen
Speichergröße, kein neues Konzept (identisches Vorgehen wie
ram.yaml "SO- DIMM"/"Laptops"-Fix).

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


# ============================================================
# 1. Realer Fehltreffer-Fall: 1024GB-Schreibweise matcht jetzt macbook.
# ============================================================

def test_macbook_pro_intel_1024gb_matcht_jetzt_macbook():
    r = evaluate(
        "Apple MacBook Pro 16.1 | i9-9880H | 16GB RAM 1024GB SSD  OHNE OS  QWERTY | Nr. 1",
        299.0,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "macbook"
    assert r.rule_label == "MacBook Pro Intel (≥1TB) ★ Top-Deal"


def test_1024_gb_mit_leerzeichen_matcht_ebenfalls():
    r = evaluate(
        "MacBook Air M2 1024 GB SSD 16GB RAM Space Grau",
        550.0,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "macbook"


def test_macbook_pro_m3_1024gb_matcht():
    r = evaluate(
        "MacBook Pro M3 1024GB SSD 18GB RAM 14 Zoll Space Schwarz",
        750.0,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "macbook"


# ============================================================
# 2. Sicherheitsprüfung: bestehende 1tb/2tb/512gb-Schreibweisen bleiben
#    unverändert funktionsfähig (kein Kollisionsschaden am Fix).
# ============================================================

def test_bestehende_1tb_schreibweise_matcht_weiterhin():
    r = evaluate(
        "MacBook Pro M2 1TB SSD 16GB RAM 14 Zoll Space Grau",
        480.0,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "macbook"


def test_bestehende_512gb_schreibweise_matcht_weiterhin():
    r = evaluate(
        "MacBook Air M1 512GB SSD 8GB RAM Gold",
        320.0,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "macbook"


def test_2tb_schreibweise_matcht_weiterhin():
    r = evaluate(
        "MacBook Pro M4 2TB SSD 24GB RAM 16 Zoll",
        1200.0,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "macbook"


# ============================================================
# 3. Grenzfälle.
# ============================================================

def test_reine_ram_angabe_1024mb_kollidiert_nicht():
    # Grenzfall: "1024" allein (z.B. als RAM- oder sonstige Zahl ohne
    # "gb"/"gb"-Einheit direkt danach) darf NICHT als Speichergrößen-
    # Signal fehlinterpretiert werden -- _contains_term() verlangt "gb"
    # direkt angehängt, ein bare "1024" ohne Einheit matcht daher nicht.
    r = evaluate(
        "MacBook Pro M3 512GB SSD, Modellnummer A1024, 16GB RAM",
        700.0,
        _rules_cfg(),
    )
    # Matcht ueber die bereits vorhandene 512gb-Alternative -- die
    # zusaetzliche "1024" in der Modellnummer darf daran nichts aendern.
    assert r.matched is True
    assert r.category == "macbook"
    assert r.rule_label == "MacBook Pro M3 (≤512GB) 👍 Guter Preis"


def test_1024gb_ohne_chip_angabe_matcht_weiterhin_nicht():
    # Grenzfall: Speichergroesse allein reicht nicht -- Chip/Generation
    # (intel/i5-i9 oder m1-m4) muss weiterhin vorhanden sein.
    r = evaluate(
        "MacBook Pro 1024GB SSD 16GB RAM OHNE OS",
        299.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "macbook")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
