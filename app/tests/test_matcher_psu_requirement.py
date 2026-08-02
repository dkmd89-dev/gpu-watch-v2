"""Tests für die neue PSU-Watt-Requirement-Logik in matcher.py.

Neue eigenständige Kategorie "netzteil" (rules/netzteil.yaml, analog zu
sata_ssd.yaml): min_psu_watt/max_psu_watt als neuer Requirement-Typ,
verdrahtet mit dem bereits vorhandenen, bisher ungenutzten Detector
categories.detectors.psu.detect_psu_watt() (Phase 4). Struktur/Tests
1:1 nach dem Vorbild von test_matcher_ssd_capacity_requirement.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import (
    _psu_meets_requirement,
    _evaluate_hardware_requirements,
    load_rules,
    evaluate,
)


# ---------- _psu_meets_requirement (Unit) ----------

def test_psu_innerhalb_des_bereichs_erfuellt_anforderung():
    assert _psu_meets_requirement(600, {"min_psu_watt": 550, "max_psu_watt": 649}) is True


def test_psu_am_unteren_rand_erfuellt_anforderung():
    assert _psu_meets_requirement(550, {"min_psu_watt": 550, "max_psu_watt": 649}) is True


def test_psu_am_oberen_rand_erfuellt_anforderung():
    assert _psu_meets_requirement(649, {"min_psu_watt": 550, "max_psu_watt": 649}) is True


def test_psu_zu_schwach_erfuellt_anforderung_nicht():
    assert _psu_meets_requirement(450, {"min_psu_watt": 550, "max_psu_watt": 649}) is False


def test_psu_zu_stark_erfuellt_anforderung_nicht():
    assert _psu_meets_requirement(750, {"min_psu_watt": 550, "max_psu_watt": 649}) is False


def test_keine_erkennbare_psu_leistung_erfuellt_anforderung_nicht():
    # Analog zu _storage_meets_requirement: ohne erkennbare Watt-Zahl
    # kann eine Leistungs-Anforderung nicht bestätigt werden.
    assert _psu_meets_requirement(None, {"min_psu_watt": 550}) is False


def test_nur_min_ohne_max_ist_gueltig():
    assert _psu_meets_requirement(1200, {"min_psu_watt": 550}) is True


def test_nur_max_ohne_min_ist_gueltig():
    assert _psu_meets_requirement(400, {"max_psu_watt": 649}) is True


# ---------- Integration über _evaluate_hardware_requirements ----------

def test_requirements_mit_psu_range_matcht_realen_titel():
    ok, features = _evaluate_hardware_requirements(
        "be quiet straight power 11 650w netzteil 80 plus gold",
        {"min_psu_watt": 550, "max_psu_watt": 749},
    )
    assert ok is True
    assert features["psu_watt"] == 650


def test_requirements_mit_psu_range_lehnt_zu_schwaches_netzteil_ab():
    ok, _ = _evaluate_hardware_requirements(
        "corsair cv350 350w netzteil",
        {"min_psu_watt": 550},
    )
    assert ok is False


# ---------- End-to-End über evaluate() + echte rules/netzteil.yaml ----------

def _load_cfg():
    return load_rules(str(Path(__file__).resolve().parent.parent / "rules"))


def test_e2e_550w_netzteil_matcht_netzteil_kategorie():
    cfg = _load_cfg()
    r = evaluate("be quiet Pure Power 11 550W Netzteil 80 Plus Gold", 35, cfg)
    assert r.matched is True
    assert r.category == "netzteil"
    assert r.price_history_model == "netzteil_550w"


def test_e2e_750w_netzteil_faellt_in_750w_plus_bucket():
    cfg = _load_cfg()
    r = evaluate("Corsair RM750 750W Netzteil modular", 55, cfg)
    assert r.matched is True
    assert r.category == "netzteil"
    assert r.price_history_model == "netzteil_750w_plus"


def test_e2e_zu_schwaches_netzteil_matcht_nicht():
    # Unter der RTX-3060-Mindestanforderung von 550W (siehe Auftrag).
    cfg = _load_cfg()
    r = evaluate("Netzteil 450W ATX gebraucht", 15, cfg)
    assert r.matched is False


def test_e2e_kompletter_gaming_pc_mit_watt_angabe_faellt_nicht_in_netzteil():
    # Regressionsschutz: ein komplettes System, das nebenbei sein
    # verbautes Netzteil in Watt nennt, darf weiterhin als gaming_pc
    # matchen, nicht als eigenständiges netzteil-Angebot.
    cfg = _load_cfg()
    r = evaluate(
        "Gaming PC Ryzen 5 3600 16GB RAM 500GB SSD RTX 2060 650W Netzteil", 420, cfg
    )
    assert r.matched is True
    assert r.category == "gaming_pc"


def test_e2e_laptop_mit_plausibler_watt_angabe_faellt_nicht_in_netzteil():
    # Regressionsschutz: ein Laptop-Angebot soll auch bei einer (unüblich
    # hohen, aber innerhalb des Detector-Plausibilitätsbereichs liegenden)
    # Watt-Zahl im Titel nicht als eigenständiges "netzteil"-Angebot
    # matchen -- die exclude_category-Liste greift.
    cfg = _load_cfg()
    r = evaluate("Dell Latitude Laptop i5 8GB RAM 256GB SSD 550W Netzteil", 150, cfg)
    assert r.matched is False
