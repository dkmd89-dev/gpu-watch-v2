"""Tests für categories/detectors/condition.py (roadmap.md Phase 6, Schritt 6b)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.condition import (
    detect_condition,
    ConditionMatch,
    CONDITION_NEU,
    CONDITION_WIE_NEU,
    CONDITION_SEHR_GUT,
    CONDITION_GUT,
    CONDITION_GEBRAUCHT,
    CONDITION_BESCHAEDIGT,
    CONDITION_DEFEKT,
    CONDITION_BASTLER,
)


# ---------- Wie neu ----------

def test_wie_neu_erkannt():
    r = detect_condition("RTX 3060 12GB, wie neu, OVP")
    assert r == ConditionMatch(condition=CONDITION_WIE_NEU)


def test_neuwertig_als_wie_neu_erkannt():
    r = detect_condition("Gaming PC neuwertig kaum genutzt")
    assert r == ConditionMatch(condition=CONDITION_WIE_NEU)


def test_wie_neu_wird_nicht_als_neu_erkannt():
    # Regressionsschutz: "wie neu" enthaelt das Wort "neu" als Teilstring --
    # muss trotzdem als CONDITION_WIE_NEU, nicht als CONDITION_NEU erkannt
    # werden (Reihenfolge der Patterns).
    r = detect_condition("Mainboard wie neu")
    assert r.condition == CONDITION_WIE_NEU


# ---------- Sehr gut ----------

def test_sehr_guter_zustand_erkannt():
    r = detect_condition("RTX 3070 sehr guter Zustand")
    assert r == ConditionMatch(condition=CONDITION_SEHR_GUT)


def test_sehr_gut_ohne_zustand_wort_erkannt():
    r = detect_condition("CPU sehr gut erhalten")
    assert r == ConditionMatch(condition=CONDITION_SEHR_GUT)


def test_sehr_gut_wird_nicht_als_gut_erkannt():
    # Regressionsschutz: "sehr gut" enthaelt "gut" als Teilstring.
    r = detect_condition("Netzteil sehr gut")
    assert r.condition == CONDITION_SEHR_GUT


# ---------- Gut ----------

def test_guter_zustand_erkannt():
    r = detect_condition("RAM Riegel guter Zustand")
    assert r == ConditionMatch(condition=CONDITION_GUT)


def test_gutem_zustand_dativ_erkannt():
    r = detect_condition("PC in gutem Zustand")
    assert r == ConditionMatch(condition=CONDITION_GUT)


# ---------- Neu ----------

def test_neu_erkannt():
    r = detect_condition("Mainboard neu, ungeöffnet")
    assert r == ConditionMatch(condition=CONDITION_NEU)


def test_neuwertig_nicht_zusaetzlich_als_neu_erkannt():
    # "neuwertig" darf NICHT ueber das allgemeinere \bneu\b-Muster erneut
    # (und diesmal falsch als CONDITION_NEU) matchen.
    r = detect_condition("SSD neuwertig")
    assert r.condition == CONDITION_WIE_NEU


# ---------- Gebraucht ----------

def test_gebraucht_erkannt():
    r = detect_condition("Netzteil gebraucht, funktioniert")
    assert r == ConditionMatch(condition=CONDITION_GEBRAUCHT)


def test_gebrauchter_flexionsform_erkannt():
    r = detect_condition("SSD gebrauchter Zustand")
    assert r == ConditionMatch(condition=CONDITION_GEBRAUCHT)


def test_gebrauchtem_dativ_erkannt():
    r = detect_condition("Kabel in gebrauchtem Zustand")
    assert r == ConditionMatch(condition=CONDITION_GEBRAUCHT)


# ---------- Beschädigt ----------

def test_beschaedigt_erkannt():
    r = detect_condition("Gehäuse leicht beschädigt, Kratzer")
    assert r == ConditionMatch(condition=CONDITION_BESCHAEDIGT)


def test_beschaedigtes_flexionsform_erkannt():
    r = detect_condition("Laptop beschädigtes Display")
    assert r == ConditionMatch(condition=CONDITION_BESCHAEDIGT)


# ---------- Defekt ----------

def test_defekt_erkannt():
    r = detect_condition("Grafikkarte DEFEKT, kein Bild")
    assert r == ConditionMatch(condition=CONDITION_DEFEKT)


def test_defektes_flexionsform_erkannt():
    r = detect_condition("Netzteil defektes Gerät zum Ausschlachten")
    assert r == ConditionMatch(condition=CONDITION_DEFEKT)


def test_kaputt_als_defekt_erkannt():
    r = detect_condition("Board kaputt, Ersatzteilspender")
    assert r == ConditionMatch(condition=CONDITION_DEFEKT)


# ---------- Bastler ----------

def test_bastler_erkannt():
    r = detect_condition("Office PC Bastlergerät, Board tot")
    assert r == ConditionMatch(condition=CONDITION_BASTLER)


def test_bastler_geht_defekt_vor():
    # "Bastler" ist das staerkere/spezifischere Signal und muss VOR dem
    # allgemeineren "defekt" im selben Titel erkannt werden.
    r = detect_condition("GPU defekt, nur an Bastler")
    assert r.condition == CONDITION_BASTLER


# ---------- Kein Treffer ----------

def test_kein_zustand_im_titel_liefert_none():
    assert detect_condition("Einfach nur ein Titel ohne Zustand") is None


def test_generischer_qualitaetsbegriff_ohne_bezug_liefert_none():
    # "TOP Zustand" nutzt kein Wort aus dem definierten Vokabular
    # (roadmap.md Phase 6) -- bewusst nicht erkannt, keine Interpretation
    # ueber die vorgegebene Liste hinaus.
    assert detect_condition("RTX 3060 TOP Zustand") is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
