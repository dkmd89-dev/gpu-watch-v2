"""Tests für categories/detectors/case.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.case import detect_case_type, CaseMatch


# ---------- Erlaubte Formfaktoren ----------

def test_tower_erkannt():
    r = detect_case_type("Gaming PC Tower Ryzen 5 RTX 3060")
    assert r == CaseMatch(case_type="Tower", category="allowed")


def test_midi_tower_erkannt():
    r = detect_case_type("Office PC Midi-Tower i5-8500")
    assert r == CaseMatch(case_type="Midi-Tower", category="allowed")


def test_midi_tower_mit_leerzeichen():
    r = detect_case_type("Office PC Midi Tower i5-8500")
    assert r == CaseMatch(case_type="Midi-Tower", category="allowed")


def test_micro_atx_erkannt():
    r = detect_case_type("Gaming PC Micro-ATX Gehäuse RTX 3060")
    assert r == CaseMatch(case_type="Micro-ATX", category="allowed")


def test_micro_atx_ohne_bindestrich():
    r = detect_case_type("Gaming PC MicroATX Gehäuse RTX 3060")
    assert r == CaseMatch(case_type="Micro-ATX", category="allowed")


# ---------- Ausgeschlossene Formfaktoren ----------

def test_tiny_ausgeschlossen():
    r = detect_case_type("HP Tiny PC i5-8500 8GB RAM")
    assert r == CaseMatch(case_type="Tiny", category="excluded")


def test_mini_pc_ausgeschlossen():
    r = detect_case_type("Mini PC HP EliteDesk i5 8GB RAM")
    assert r == CaseMatch(case_type="Mini-PC", category="excluded")


def test_mini_pc_mit_bindestrich():
    r = detect_case_type("Mini-PC Lenovo ThinkCentre i5")
    assert r == CaseMatch(case_type="Mini-PC", category="excluded")


def test_usff_ausgeschlossen():
    r = detect_case_type("Dell OptiPlex USFF i5-8500 8GB RAM")
    assert r == CaseMatch(case_type="USFF", category="excluded")


def test_sff_ausgeschlossen():
    r = detect_case_type("HP SFF PC i5-8500 256GB SSD")
    assert r == CaseMatch(case_type="SFF", category="excluded")


def test_small_form_factor_ausgeschrieben():
    r = detect_case_type("Office PC Small Form Factor i5-8500")
    assert r == CaseMatch(case_type="Small-Form-Factor", category="excluded")


def test_all_in_one_ausgeschrieben():
    r = detect_case_type("HP All-in-One PC 24 Zoll i5-8500")
    assert r == CaseMatch(case_type="All-in-One", category="excluded")


def test_all_in_one_mit_leerzeichen():
    r = detect_case_type("Lenovo All in One PC i5-8500")
    assert r == CaseMatch(case_type="All-in-One", category="excluded")


def test_generisches_mini_ausgeschlossen():
    r = detect_case_type("Mini Rechner HP i5 8GB RAM")
    assert r == CaseMatch(case_type="Mini", category="excluded")


# ---------- Kritische Disambiguierung: AIO-Kühler vs. All-in-One-PC ----------

def test_aio_wasserkuehlung_wird_nicht_als_all_in_one_pc_erkannt():
    # "AIO" alleine ist im Gebrauchtmarkt fast immer eine Wasserkühlung,
    # NICHT ein All-in-One-PC. Ein Gaming-PC im Tower mit AIO-Kühler
    # darf nicht faelschlich ausgeschlossen werden.
    r = detect_case_type("Gaming PC Tower Ryzen 7 RTX 3070 AIO Wasserkühlung 240mm")
    assert r == CaseMatch(case_type="Tower", category="allowed")


def test_aio_alleine_ohne_tower_kontext_liefert_keinen_ausschluss():
    r = detect_case_type("Gaming PC AIO Wasserkühlung 32GB RAM RTX 3070")
    assert r is None or r.category != "excluded"


def test_ausgeschriebenes_all_in_one_wird_weiterhin_erkannt():
    # Kontrolltest: der ausgeschriebene Begriff funktioniert weiterhin,
    # nur die Abkuerzung "AIO" wird bewusst nicht als All-in-One gewertet.
    r = detect_case_type("All-in-One PC ohne Tower, integrierter Monitor")
    assert r.case_type == "All-in-One"
    assert r.category == "excluded"


# ---------- Priorität: Ausschluss vor Zulassung ----------

def test_ausschluss_hat_prioritaet_vor_zulassung():
    # Falls ein Titel widerspruechlich sowohl "Tower" als auch "Mini-PC"
    # enthaelt (z.B. Vergleichs-/Bündelangebot), gewinnt der Ausschluss.
    r = detect_case_type("Tower Gehäuse gegen Mini-PC eintauschen")
    assert r.category == "excluded"


# ---------- Kein Treffer ----------

def test_kein_treffer_ohne_gehaeuse_angabe():
    assert detect_case_type("Gaming PC Ryzen 5 3600 RTX 3060 16GB RAM") is None


def test_kein_treffer_leerer_text():
    assert detect_case_type("") is None


def test_bekannte_grenze_mini_itx_mainboard_format():
    # BEKANNTE GRENZE (siehe Docstring): "Mini-ITX" ist ein Mainboard-
    # Formfaktor, kein Gehaeuse-Formfaktor -- wird hier dennoch als
    # "Mini" (ausgeschlossen) erkannt, da das Wort "mini" matcht.
    r = detect_case_type("Gaming PC Mini-ITX Mainboard RTX 3060 im Tower")
    assert r.case_type == "Mini"
    assert r.category == "excluded"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
