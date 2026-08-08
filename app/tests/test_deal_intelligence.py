"""Tests für deal_intelligence.py (roadmap.md Phase 7, Schritt 7a)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deal_intelligence import (
    classify_deal,
    DealIntelligence,
    LABEL_TOP_DEAL,
    LABEL_FLIP_DEAL,
    LABEL_VERY_GOOD_DEAL,
    LABEL_WATCH,
    EMOJI_TOP_DEAL,
    EMOJI_FLIP_DEAL,
    EMOJI_VERY_GOOD_DEAL,
    EMOJI_WATCH,
)


# ---------- Prioritätsstufe 1: TOP DEAL ----------

def test_top_deal_hat_hoechste_prioritaet():
    r = classify_deal(is_top_deal=True)
    assert r == DealIntelligence(label=LABEL_TOP_DEAL, emoji=EMOJI_TOP_DEAL)


def test_top_deal_gewinnt_auch_bei_gleichzeitig_erfuellter_flip_bedingung():
    # Regressionsschutz: "keine Doppelzaehlung" -- is_top_deal=True
    # gewinnt, selbst wenn estimated_margin_pct ebenfalls die
    # Flip-Schwelle erreicht.
    r = classify_deal(is_top_deal=True, estimated_margin_pct=50.0, deal_stars="★★★★★")
    assert r.label == LABEL_TOP_DEAL


# ---------- Prioritätsstufe 2: FLIP DEAL ----------

def test_flip_deal_ab_min_flip_margin_pct():
    r = classify_deal(is_top_deal=False, estimated_margin_pct=20.0)
    assert r == DealIntelligence(label=LABEL_FLIP_DEAL, emoji=EMOJI_FLIP_DEAL)


def test_flip_deal_knapp_unter_schwelle_faellt_durch():
    r = classify_deal(is_top_deal=False, estimated_margin_pct=19.9)
    assert r.label != LABEL_FLIP_DEAL


def test_flip_deal_ohne_margin_wert_faellt_durch():
    r = classify_deal(is_top_deal=False, estimated_margin_pct=None)
    assert r.label != LABEL_FLIP_DEAL


def test_flip_deal_gewinnt_vor_very_good_deal():
    r = classify_deal(is_top_deal=False, estimated_margin_pct=25.0, deal_stars="★★★★★")
    assert r.label == LABEL_FLIP_DEAL


# ---------- Prioritätsstufe 3: VERY GOOD DEAL ----------

def test_very_good_deal_ab_vier_sternen():
    r = classify_deal(is_top_deal=False, deal_stars="★★★★☆")
    assert r == DealIntelligence(label=LABEL_VERY_GOOD_DEAL, emoji=EMOJI_VERY_GOOD_DEAL)


def test_very_good_deal_bei_fuenf_sternen():
    r = classify_deal(is_top_deal=False, deal_stars="★★★★★")
    assert r.label == LABEL_VERY_GOOD_DEAL


def test_drei_sterne_ist_kein_very_good_deal():
    r = classify_deal(is_top_deal=False, deal_stars="★★★☆☆")
    assert r.label != LABEL_VERY_GOOD_DEAL


# ---------- Prioritätsstufe 4: WATCH (Default) ----------

def test_watch_ohne_jedes_signal():
    r = classify_deal()
    assert r == DealIntelligence(label=LABEL_WATCH, emoji=EMOJI_WATCH)


def test_watch_bei_niedrigen_sternen_und_ohne_margin():
    r = classify_deal(is_top_deal=False, estimated_margin_pct=5.0, deal_stars="★★☆☆☆")
    assert r.label == LABEL_WATCH


def test_watch_bei_fehlendem_deal_stars_feld():
    # Aeltere found.json-Eintraege ohne deal_stars-Feld (None) -- kein
    # Fehler, faellt auf WATCH zurueck (analog is-defined-Check im
    # bestehenden Dashboard-Template).
    r = classify_deal(is_top_deal=False, deal_stars=None)
    assert r.label == LABEL_WATCH


# ---------- Konsistenz mit api/status.py-KPI-Logik ----------

def test_jede_stufe_hat_genau_ein_passendes_emoji():
    for label, emoji in [
        (LABEL_TOP_DEAL, EMOJI_TOP_DEAL),
        (LABEL_FLIP_DEAL, EMOJI_FLIP_DEAL),
        (LABEL_VERY_GOOD_DEAL, EMOJI_VERY_GOOD_DEAL),
        (LABEL_WATCH, EMOJI_WATCH),
    ]:
        assert isinstance(label, str) and isinstance(emoji, str)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
