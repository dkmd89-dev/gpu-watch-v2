"""Tests für Schritt A (SSD-Suche verbessern/optimieren):

1. M.2-SATA-SSDs werden nicht mehr fälschlich über den generischen
   "m.2"/"m2"-Exclude in rules/sata_ssd.yaml verworfen (M.2 ist ein
   Formfaktor, kein Interface -- nur explizite NVMe-Erwähnungen sollen
   weiterhin ausgeschlossen werden).
2. Der häufige Tippfehler "SDD" (statt "SSD") wird end-to-end (Matcher-
   Ebene, nicht nur im Detector) erkannt.
3. Generische, markenlose Suchbegriffe sind in rules/sata_ssd.yaml
   hinterlegt.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules, evaluate


def test_m2_sata_ssd_wird_nicht_mehr_ausgeschlossen():
    cfg = load_rules(RULES_DIR)
    r = evaluate("Samsung 870 EVO M.2 SATA SSD 500GB 2.5", 20.0, cfg)
    assert r.matched is True
    assert r.category == "sata_ssd"


def test_explizite_nvme_erwaehnung_bleibt_ausgeschlossen():
    # Weiterhin ausgeschlossen: NVMe wird explizit genannt.
    cfg = load_rules(RULES_DIR)
    r = evaluate("Crucial P3 M.2 NVMe SSD 500GB", 20.0, cfg)
    assert r.matched is False


def test_pcie_erwaehnung_bleibt_ausgeschlossen():
    cfg = load_rules(RULES_DIR)
    r = evaluate("WD Black M.2 PCIe SSD 500GB", 20.0, cfg)
    assert r.matched is False


def test_sdd_tippfehler_matcht_end_to_end():
    cfg = load_rules(RULES_DIR)
    r = evaluate("Kingston A400 250GB SATA SDD 2.5", 10.0, cfg)
    assert r.matched is True
    assert r.category == "sata_ssd"


def test_generische_suchbegriffe_in_sata_ssd_yaml_vorhanden():
    cfg = load_rules(RULES_DIR)
    categories = cfg.get("categories", [])
    assert "sata_ssd" in categories
    assert any("SSD 500GB" in t for t in cfg["search_terms"])
    assert any("WD Blue SSD" in t for t in cfg["search_terms"])


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
