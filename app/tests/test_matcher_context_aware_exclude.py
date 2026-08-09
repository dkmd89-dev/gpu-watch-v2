"""Tests für die generische, kontextbewusste Exclude-Logik "Variante C"
(Phase 15, kontrollierter Review nach dem Robustheitscheck des
controller.yaml-Fixes).

Ziel: ein Exclude-Begriff (z.B. "ladekabel") soll eine Regel nur dann
blockieren, wenn er ALLEIN steht ("PS5 Controller Ladekabel" ->
Standalone-Zubehör), NICHT wenn ein erlaubter Bundle-Konnektor
unmittelbar davorsteht ("PS5 Controller inkl. Ladekabel" -> Bundle).

Technik: Negative Lookbehinds, identisches Prinzip wie bereits produktiv
in categories/detectors/lieferumfang.py (_NETZTEIL_POSITIVE), hier mit
umgekehrter Wortliste (Inklusions- statt Negationswörter) und für die
Match-/Exclude-Entscheidung statt eines Deal-Score-Signals.

Neues, optionales YAML-Feld: "exclude_category_unless_preceded_by"
({Begriff: [Konnektoren]}) -- generisch für jede Kategorie nutzbar, kein
"if category == ...". Bestehende "exclude"/"exclude_category"-Semantik
bleibt für alle Kategorien, die das neue Feld nicht setzen, unverändert.

Zwei Ebenen:
1. Unit-Tests gegen die neuen matcher.py-Hilfsfunktionen direkt
   (_contains_term_unless_preceded_by, _any_conditional_exclude) mit
   synthetischen Fällen -- deckt die vollständige Konnektor-/Edge-Case-
   Matrix ab, unabhängig von den echten Regeln.
2. Integrationstests gegen die echten rules/controller.yaml (analog zu
   test_matcher_controller_accessory_fix.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import (
    _any_conditional_exclude,
    _contains_term_unless_preceded_by,
    load_rules,
    evaluate,
)

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


CONNECTORS = ["inkl.", "inkl", "mit", "+", "und", "sowie"]


# ============================================================
# 1. Unit-Tests: _contains_term_unless_preceded_by() / _any_conditional_exclude()
# ============================================================

# --- STANDALONE: muss True liefern (Exclude greift) ---

def test_standalone_ps5_controller_ladekabel():
    assert _contains_term_unless_preceded_by(
        "ps5 controller ladekabel", "ladekabel", CONNECTORS
    ) is True


def test_standalone_ps5_controller_ladekabel_usb_c():
    assert _contains_term_unless_preceded_by(
        "ps5 controller ladekabel usb-c 3m", "ladekabel", CONNECTORS
    ) is True


def test_standalone_ps5_ladekabel():
    assert _contains_term_unless_preceded_by(
        "ps5 ladekabel", "ladekabel", CONNECTORS
    ) is True


def test_standalone_ps5_controller_ladekabel_ersatz():
    assert _contains_term_unless_preceded_by(
        "ps5 controller ladekabel ersatz", "ladekabel", CONNECTORS
    ) is True


def test_standalone_ps5_ladekabel_original():
    assert _contains_term_unless_preceded_by(
        "ps5 ladekabel original", "ladekabel", CONNECTORS
    ) is True


def test_begriff_am_titelanfang_ist_standalone():
    # Kein Wort davor -> kein Konnektor kann gefunden werden -> Exclude
    # greift (konservativ, wie ohne jeden Kontext).
    assert _contains_term_unless_preceded_by(
        "ladekabel für ps5 controller", "ladekabel", CONNECTORS
    ) is True


def test_begriff_ohne_jeden_konnektor_ist_standalone():
    assert _contains_term_unless_preceded_by(
        "ps5 dualsense controller ladekabel schwarz", "ladekabel", CONNECTORS
    ) is True


# --- BUNDLE: muss False liefern (Exclude greift NICHT) ---

def test_bundle_inkl_punkt():
    assert _contains_term_unless_preceded_by(
        "ps5 dualsense controller inkl. ladekabel", "ladekabel", CONNECTORS
    ) is False


def test_bundle_inkl_ohne_punkt():
    assert _contains_term_unless_preceded_by(
        "ps5 dualsense controller inkl ladekabel", "ladekabel", CONNECTORS
    ) is False


def test_bundle_mit():
    assert _contains_term_unless_preceded_by(
        "ps5 dualsense wireless controller mit ladekabel", "ladekabel", CONNECTORS
    ) is False


def test_bundle_plus():
    assert _contains_term_unless_preceded_by(
        "dualsense controller + ladekabel", "ladekabel", CONNECTORS
    ) is False


def test_bundle_und():
    assert _contains_term_unless_preceded_by(
        "ps5 dualsense controller und ladekabel", "ladekabel", CONNECTORS
    ) is False


def test_bundle_sowie():
    assert _contains_term_unless_preceded_by(
        "ps5 dualsense controller sowie ladekabel", "ladekabel", CONNECTORS
    ) is False


def test_bundle_gross_kleinschreibung_konnektor():
    # Titel wird von evaluate() bereits lowercased uebergeben, die
    # Funktion selbst muss aber auch bei direktem Grossbuchstaben-Aufruf
    # (z.B. isolierter Unit-Test) case-insensitive bleiben.
    assert _contains_term_unless_preceded_by(
        "PS5 Controller INKL. Ladekabel".lower(), "LADEKABEL", CONNECTORS
    ) is False


def test_bundle_gross_kleinschreibung_begriff():
    assert _contains_term_unless_preceded_by(
        "ps5 controller mit LADEKABEL".lower(), "Ladekabel", CONNECTORS
    ) is False


# --- _any_conditional_exclude(): OR-Verknuepfung mehrerer Begriffe ---

def test_any_conditional_exclude_erkennt_jeden_konfigurierten_begriff():
    conditional = {"ladekabel": CONNECTORS, "netzteil": CONNECTORS}
    assert _any_conditional_exclude("ps5 controller ladekabel", conditional) is True
    assert _any_conditional_exclude("ps5 controller netzteil", conditional) is True
    assert _any_conditional_exclude("ps5 controller inkl. ladekabel", conditional) is False
    assert _any_conditional_exclude("ps5 dualsense controller", conditional) is False


def test_any_conditional_exclude_leeres_dict_greift_nie():
    assert _any_conditional_exclude("ps5 controller ladekabel", {}) is False


# ============================================================
# 2. Integrationstests gegen die echten rules/controller.yaml
# ============================================================

def test_integration_standalone_faelle_matchen_nicht():
    titles = [
        "PS5 Controller Ladekabel",
        "PS5 Controller Ladekabel USB-C 3m",
        "PS5 Ladekabel",
        "PS5 Controller Ladekabel Ersatz",
        "PS5 Ladekabel Original",
    ]
    for title in titles:
        r = evaluate(title, 5.0, _rules_cfg())
        assert r.matched is False, f"{title!r} haette NICHT matchen duerfen"


def test_integration_bundle_faelle_matchen():
    titles = [
        "PS5 DualSense Controller inkl. Ladekabel",
        "PS5 DualSense Wireless Controller mit Ladekabel",
        "DualSense Controller + Ladekabel",
    ]
    for title in titles:
        r = evaluate(title, 20.0, _rules_cfg())
        assert r.matched is True, f"{title!r} haette matchen muessen"
        assert r.category == "controller"


def test_integration_urspruenglicher_bug_bleibt_abgesichert():
    # Der Titel aus dem urspruenglichen False-Positive-Fund (5 EUR,
    # matchte vor jedem Fix als controller_ps5_dualsense Top-Deal).
    r = evaluate("PS5 Controller Ladekabel USB-C 3m", 5.0, _rules_cfg())
    assert r.matched is False


def test_integration_reiner_controller_matcht_weiterhin():
    r = evaluate("PS5 DualSense Controller weiß neuwertig", 20.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "controller"


def test_integration_bare_kabel_exclude_unveraendert():
    # exclude_category "kabel" (bare, unveraendert -- nicht Teil der neuen
    # kontextbewussten Logik) blockiert weiterhin unbedingt.
    r = evaluate("PS5 Controller Kabel USB-C 3m", 5.0, _rules_cfg())
    assert r.matched is False


def test_integration_netzteil_ladegeraet_anleitung_analog_zu_ladekabel():
    standalone = [
        "PS5 Controller Netzteil original",
        "PS5 DualSense Controller Ladegerät 2m",
        "PS5 Controller Anleitung",
    ]
    for title in standalone:
        r = evaluate(title, 5.0, _rules_cfg())
        assert r.matched is False, f"{title!r} haette NICHT matchen duerfen"

    bundle = [
        "PS5 DualSense Controller inkl. Netzteil",
        "PS5 DualSense Controller mit Ladegerät",
        "PS5 DualSense Controller + Anleitung",
    ]
    for title in bundle:
        r = evaluate(title, 20.0, _rules_cfg())
        assert r.matched is True, f"{title!r} haette matchen muessen"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
