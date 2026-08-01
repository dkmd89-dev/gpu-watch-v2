"""Tests für die SSD-Kapazitäts-Requirement-Logik in matcher.py.

Ablösung des starren Titel-Substring-Matchings in rules/sata_ssd.yaml
(vorher: feste Strings wie "250gb sata", die reale, nicht-runde
Kapazitäten wie 240GB/480GB/960GB nie trafen) durch eine Detector-
basierte Requirement-Prüfung (min_ssd_gb/max_ssd_gb), analog zu den
bestehenden office_pc/gaming_pc-Requirements.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import (
    _storage_meets_requirement,
    _evaluate_hardware_requirements,
    load_rules,
    evaluate,
)


# ---------- _storage_meets_requirement (Unit) ----------

def test_ssd_innerhalb_des_bereichs_erfuellt_anforderung():
    assert _storage_meets_requirement(500, {"min_ssd_gb": 320, "max_ssd_gb": 639}) is True


def test_ssd_am_unteren_rand_erfuellt_anforderung():
    assert _storage_meets_requirement(320, {"min_ssd_gb": 320, "max_ssd_gb": 639}) is True


def test_ssd_am_oberen_rand_erfuellt_anforderung():
    assert _storage_meets_requirement(639, {"min_ssd_gb": 320, "max_ssd_gb": 639}) is True


def test_ssd_zu_klein_erfuellt_anforderung_nicht():
    assert _storage_meets_requirement(120, {"min_ssd_gb": 320, "max_ssd_gb": 639}) is False


def test_ssd_zu_gross_erfuellt_anforderung_nicht():
    assert _storage_meets_requirement(1000, {"min_ssd_gb": 320, "max_ssd_gb": 639}) is False


def test_keine_erkennbare_ssd_groesse_erfuellt_anforderung_nicht():
    # Analog zu _ram_meets_requirement: ohne erkennbare Kapazität kann
    # eine Kapazitäts-Anforderung nicht bestätigt werden.
    assert _storage_meets_requirement(None, {"min_ssd_gb": 320, "max_ssd_gb": 639}) is False


def test_nur_min_ohne_max_ist_gueltig():
    assert _storage_meets_requirement(5000, {"min_ssd_gb": 320}) is True


def test_nur_max_ohne_min_ist_gueltig():
    assert _storage_meets_requirement(50, {"max_ssd_gb": 639}) is True


# ---------- Integration über _evaluate_hardware_requirements ----------

def test_requirements_mit_ssd_range_matcht_realen_titel():
    ok, features = _evaluate_hardware_requirements(
        "crucial mx500 500gb ssd 2.5 zoll sata",
        {"min_ssd_gb": 320, "max_ssd_gb": 639},
    )
    assert ok is True
    assert features["ssd_gb"] == 500


def test_requirements_mit_ssd_range_lehnt_zu_kleine_kapazitaet_ab():
    ok, _ = _evaluate_hardware_requirements(
        "kingston a400 120gb ssd 2.5 zoll",
        {"min_ssd_gb": 320, "max_ssd_gb": 639},
    )
    assert ok is False


# ---------- End-to-End über evaluate() + echte rules/sata_ssd.yaml ----------

def _load_cfg():
    return load_rules(str(Path(__file__).resolve().parent.parent / "rules"))


def test_e2e_nicht_rundes_500gb_derivat_matcht_sata_ssd_kategorie():
    # Vorher (Titel-Substring-Matching) traf NICHTS aus dieser Liste --
    # das war der eigentliche Grund für 0 Treffer in der Kategorie.
    cfg = _load_cfg()
    r = evaluate("Samsung 870 EVO 500GB SSD", 22, cfg)
    assert r.matched is True
    assert r.category == "sata_ssd"


def test_e2e_240gb_matcht_250gb_bucket():
    cfg = _load_cfg()
    r = evaluate("Kingston A400 240GB SSD SATA III", 12, cfg)
    assert r.matched is True
    assert r.category == "sata_ssd"
    assert r.price_history_model == "sata_ssd_250gb"


def test_e2e_nvme_wird_weiterhin_ausgeschlossen():
    cfg = _load_cfg()
    r = evaluate("Samsung 970 EVO 500GB NVMe M.2 SSD", 30, cfg)
    assert r.matched is False


def test_e2e_externe_ssd_wird_weiterhin_ausgeschlossen():
    cfg = _load_cfg()
    r = evaluate("Externe Festplatte 1TB SSD USB", 20, cfg)
    assert r.matched is False


def test_e2e_kompletter_gaming_pc_mit_ssd_im_titel_faellt_nicht_in_sata_ssd():
    # Regressionsschutz: ein komplettes System mit "SSD" im Titel darf
    # weiterhin als gaming_pc/office_pc matchen, nicht als sata_ssd.
    cfg = _load_cfg()
    r = evaluate(
        "Gaming PC Ryzen 5 3600 16GB RAM 500GB SSD RTX 2060", 400, cfg
    )
    assert r.matched is True
    assert r.category == "gaming_pc"
