"""Regressionstests für den notebook_resell-"gaming"-Fix (kontrollierter
Review nach found.json-Audit, Priorität HOCH).

Hintergrund: Die Regeln "Gaming Laptop (RTX 3060/4060)" verlangten in
Gruppe 2 ["laptop", "notebook", "gaming"] -- "gaming" als Alternative
war zu generisch, da fast jede Grafikkarte "Gaming" im Produktnamen
trägt (ASUS TUF Gaming, MSI Gaming X Trio, Gigabyte GAMING OC, Zotac
Gaming). Dadurch matchten reine Standalone-Grafikkarten und Desktop-
Gaming-PCs als Notebook (found.json-Audit: 32 von 120 sichtbaren
Einträgen dieser Kategorie, u.a. "MSI GeForce RTX 4060 Ti Gaming X Trio
8GB Top Zustand + OVP" für 300EUR als Top-Deal).

Fix: "gaming" aus Gruppe 2 entfernt, nur noch ["laptop", "notebook"].

Läuft gegen die echten, produktiven rules/*.yaml, analog zu
test_rule_service_modding_fix.py."""
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
# 1. Reine Grafikkarten/Desktop-Gaming-PCs (found.json-Funde) matchen
#    NICHT mehr als notebook_resell.
# ============================================================

def test_msi_rtx4060_gaming_x_trio_matcht_nicht():
    r = evaluate(
        "MSI GeForce RTX 4060 Ti Gaming X Trio 8GB Top Zustand + OVP",
        300.0, _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


def test_gaming_pc_rtx3060_matcht_nicht():
    r = evaluate("Gaming PC rtx 3060", 380.0, _rules_cfg())
    assert not (r.matched and r.category == "notebook_resell")


def test_zotac_gaming_rtx4060_grafikkarte_matcht_nicht():
    r = evaluate(
        "ZOTAC GAMING NVIDIA GeForce RTX 4060 Ti Twin Edge Grafikkarte 8 GB",
        523.96, _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


def test_asus_tuf_gaming_rtx3060_grafikkarte_matcht_nicht():
    r = evaluate(
        "ASUS TUF Gaming GeForce RTX 4060 Ti OC 8GB GDDR6 Grafikkarte",
        360.0, _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


def test_gigabyte_gaming_oc_rtx3060_grafikkarte_matcht_nicht():
    r = evaluate(
        "GIGABYTE GeForce RTX 3060 Ti GAMING OC 8G (rev. 2.0) 8GB GDDR6 Grafikkarte",
        299.0, _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


def test_desktop_gaming_pc_bundle_matcht_nicht():
    r = evaluate(
        "Gaming PC - RTX 4060 Ti | AMD Ryzen 5 5500 | 1TB SSD", 490.0, _rules_cfg()
    )
    assert not (r.matched and r.category == "notebook_resell")


# ============================================================
# 2. Echte Gaming-Notebooks matchen weiterhin.
# ============================================================

def test_hp_omen_gaming_notebook_rtx_matcht_weiterhin():
    r = evaluate(
        "HP OMEN 15 Gaming Notebook RTX 3060 16GB RAM 512GB SSD", 450.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "notebook_resell"
    assert r.price_history_model == "gaming_laptop_rtx3060"


def test_lenovo_legion_gaming_laptop_rtx3060_matcht_weiterhin():
    r = evaluate(
        "Lenovo Legion 5 Gaming Laptop RTX 3060 16GB RAM 512GB SSD", 480.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "notebook_resell"


def test_gaming_laptop_rtx4060_matcht_weiterhin():
    r = evaluate(
        "MSI GF63 Gaming Laptop RTX 4060 16GB RAM 512GB SSD", 500.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "notebook_resell"
    assert r.price_history_model == "gaming_laptop_rtx4060"


def test_notebook_ohne_gaming_wort_matcht_weiterhin():
    # "notebook" allein (ohne "gaming") reicht weiterhin als Geraete-
    # Indikator -- die Gruppe verlangt "laptop" ODER "notebook", nicht
    # zwingend beide.
    r = evaluate("Asus Notebook RTX 3060 16GB RAM 512GB SSD", 450.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "notebook_resell"


# ============================================================
# 3. Sicherheitsprüfung: ThinkPad-Regeln (eigene require_all_of-Gruppen,
#    von diesem Fix nicht betroffen) bleiben unverändert.
# ============================================================

def test_thinkpad_t14_bleibt_unveraendert():
    r = evaluate("Lenovo ThinkPad T14 16GB RAM 512GB SSD", 150.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "notebook_resell"
    assert r.price_history_model == "thinkpad_modern"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
