"""Tests für die in Phase 12, Schritt 5 kalibrierten Preisgrenzen
(iPhone 11 Pro Max/14 Plus/15/15 Pro/15 Pro Max/16/16 Pro/16 Pro Max,
MacBook Air M4, LEGO CMF). Prüft NUR die Preisgrenze selbst (max_price-
Verhalten an der neuen Schwelle) -- keine Änderung an Matching-Logik,
Deal-Score, Top-Deal, Flip-Kandidaten oder Notifications.

Läuft gegen die echten, produktiven rules/*.yaml (load_rules()), analog
zu test_matcher_price_calibration_matching_fixes.py.
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


# ---------- iPhone: neue Top-Deal-Grenzen ----------

def test_iphone_11_pro_max_innerhalb_neuer_grenze_ist_top_deal():
    r = evaluate("Apple iPhone 11 Pro Max 128GB", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.deal_rating == "Top-Deal"


def test_iphone_11_pro_max_ueber_neuer_grenze_ist_kein_top_deal():
    r = evaluate("Apple iPhone 11 Pro Max 128GB", 151.0, _rules_cfg())
    assert r.matched is True
    assert r.deal_rating != "Top-Deal"


def test_iphone_14_plus_neue_grenze():
    r = evaluate("Apple iPhone 14 Plus 128GB", 250.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Apple iPhone 14 Plus 128GB", 251.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_iphone_15_neue_grenze():
    r = evaluate("Apple iPhone 15 128GB", 310.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Apple iPhone 15 128GB", 311.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_iphone_15_pro_neue_grenze():
    r = evaluate("Apple iPhone 15 Pro 128GB", 380.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Apple iPhone 15 Pro 128GB", 381.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_iphone_15_pro_max_neue_grenze():
    r = evaluate("Apple iPhone 15 Pro Max 128GB", 450.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Apple iPhone 15 Pro Max 128GB", 451.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_iphone_16_neue_grenze():
    r = evaluate("Apple iPhone 16 128GB", 400.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Apple iPhone 16 128GB", 401.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_iphone_16_pro_neue_grenze():
    r = evaluate("Apple iPhone 16 Pro 128GB", 550.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Apple iPhone 16 Pro 128GB", 551.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_iphone_16_pro_max_neue_grenze():
    r = evaluate("Apple iPhone 16 Pro Max 128GB", 600.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Apple iPhone 16 Pro Max 128GB", 601.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


# ---------- MacBook Air M4: neue Top-Deal-Grenze ----------

def test_macbook_air_m4_innerhalb_neuer_grenze_ist_top_deal():
    r = evaluate("Apple MacBook Air M4 512GB", 725.0, _rules_cfg())
    assert r.matched is True
    assert r.deal_rating == "Top-Deal"


def test_macbook_air_m4_bei_altem_grenzwert_ist_jetzt_top_deal():
    # Regressionsschutz: die alte Grenze (415€) lag unter dem
    # guenstigsten real beobachteten Angebot -- bei 415€ MUSS jetzt
    # Top-Deal gelten (war vorher unmoeglich).
    r = evaluate("Apple MacBook Air M4 512GB", 415.0, _rules_cfg())
    assert r.matched is True
    assert r.deal_rating == "Top-Deal"


def test_macbook_air_m4_ueber_neuer_grenze_ist_kein_top_deal():
    r = evaluate("Apple MacBook Air M4 512GB", 726.0, _rules_cfg())
    assert r.matched is True
    assert r.deal_rating != "Top-Deal"


# ---------- LEGO CMF: alle drei neuen Preisstufen ----------

def test_lego_cmf_neue_top_deal_grenze():
    r = evaluate("LEGO CMF Sammelfigur Serie 26 selten", 5.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("LEGO CMF Sammelfigur Serie 26 selten", 6.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_lego_cmf_neue_guter_preis_grenze():
    r = evaluate("LEGO CMF Sammelfigur Serie 26 selten", 7.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Guter Preis"
    r2 = evaluate("LEGO CMF Sammelfigur Serie 26 selten", 8.0, _rules_cfg())
    assert r2.deal_rating != "Guter Preis"


def test_lego_cmf_neue_interessant_grenze():
    r = evaluate("LEGO CMF Sammelfigur Serie 26 selten", 10.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Interessant"
    r2 = evaluate("LEGO CMF Sammelfigur Serie 26 selten", 11.0, _rules_cfg())
    assert r2.matched is False


# ---------- Regressionsschutz: unveraendert gebliebene Modelle ----------

def test_crt_profi_monitor_preisgrenze_unveraendert():
    # Phase 12, Schritt 3/V2: NICHT ÄNDERN -- Grenze muss bei 80€ bleiben.
    r = evaluate("Sony PVM 740 Professional Video Monitor Broadcast", 80.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Sony PVM 740 Professional Video Monitor Broadcast", 81.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_thinkpad_modern_preisgrenze_unveraendert():
    # Phase 12, Schritt 3/V2: NICHT ÄNDERN -- Grenze muss bei 180€ bleiben.
    r = evaluate("Lenovo ThinkPad T490 i5-8365U 16GB 512GB SSD FHD", 180.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"
    r2 = evaluate("Lenovo ThinkPad T490 i5-8365U 16GB 512GB SSD FHD", 181.0, _rules_cfg())
    assert r2.deal_rating != "Top-Deal"


def test_lego_sw_rare_preisgrenze_unveraendert():
    # Phase 12, Schritt 3/V2: ZU WENIGE DATEN -- nicht kalibriert, Grenze
    # muss bei 15€ (Top-Deal) bleiben.
    r = evaluate("LEGO Star Wars Minifigur C-3PO Chrom Gold Limited Edition selten", 15.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"


def test_nintendo_retro_konsole_preisgrenze_unveraendert():
    # Phase 12, Schritt 3/V2: MANUELLE PRÜFUNG -- nicht automatisch
    # kalibriert, Grenze muss bei 40€ (Top-Deal) bleiben.
    r = evaluate("Nintendo 64 Konsole N64 schwarz", 40.0, _rules_cfg())
    assert r.matched is True and r.deal_rating == "Top-Deal"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
