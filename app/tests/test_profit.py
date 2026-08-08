"""Tests fuer scoring/profit.py (Reselling-/Arbitrage-Konzept)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring.profit import (
    Profit, compute_profit, is_robust_flip_candidate,
    MIN_FLIP_MARGIN_PCT, MIN_FLIP_MARGIN_EUR, MIN_FLIP_DEAL_SCORE,
)


# ---------- Grundfälle ----------

def test_kein_resale_price_liefert_none():
    assert compute_profit(100.0, None) is None


def test_resale_price_null_liefert_none():
    assert compute_profit(100.0, 0.0) is None


def test_resale_price_negativ_liefert_none():
    assert compute_profit(100.0, -10.0) is None


# ---------- Ohne fees-Konfiguration (neutrale Defaults) ----------

def test_ohne_fees_config_reine_preisdifferenz():
    result = compute_profit(100.0, 150.0)
    assert isinstance(result, Profit)
    assert result.fees_total == 0.0
    assert result.margin_abs == 50.0
    assert result.margin_pct == 50.0


def test_leeres_fees_dict_wie_ohne_config():
    result = compute_profit(100.0, 150.0, fees={})
    assert result.fees_total == 0.0
    assert result.margin_abs == 50.0


# ---------- Mit vollständiger fees-Konfiguration ----------

def test_mit_vollstaendigen_fees():
    fees = {
        "platform_fee_pct": 10.0,
        "payment_fee_pct": 2.5,
        "shipping_cost": 6.0,
        "packaging_cost": 1.5,
    }
    result = compute_profit(100.0, 150.0, fees=fees)
    # 150 * 0.10 = 15.0 (platform) + 150 * 0.025 = 3.75 (payment)
    # + 6.0 (shipping) + 1.5 (packaging) = 26.25
    assert result.fees_total == 26.25
    assert result.margin_abs == 150.0 - 100.0 - 26.25
    assert result.margin_pct == round((result.margin_abs / 100.0) * 100, 2)


def test_teilweise_fees_nutzt_defaults_fuer_fehlende_keys():
    result = compute_profit(100.0, 150.0, fees={"shipping_cost": 5.0})
    # nur shipping_cost gesetzt, Rest bleibt 0 (Default)
    assert result.fees_total == 5.0


# ---------- Negative Marge (Verlustgeschäft) ----------

def test_negative_marge_bei_hohem_kaufpreis():
    result = compute_profit(200.0, 150.0)
    assert result.margin_abs == -50.0
    assert result.margin_pct == -25.0


# ---------- margin_pct bei purchase_price == 0 ----------

def test_margin_pct_none_bei_kaufpreis_null():
    result = compute_profit(0.0, 150.0)
    assert result.margin_pct is None
    assert result.margin_abs == 150.0


# ---------- margin_pct-Guard bei Mini-Kaufpreisen (Bugfix Schritt A) ----------

def test_margin_pct_none_bei_kaufpreis_unter_mindestschwelle():
    # purchase_price=1€ (z.B. Tausch-/VB-Inserat ohne echten Preis) darf
    # keine absurde Prozentzahl mehr liefern, margin_abs bleibt gesetzt.
    result = compute_profit(1.0, 150.0)
    assert result.margin_pct is None
    assert result.margin_abs == 149.0


def test_margin_pct_gesetzt_ab_mindestschwelle():
    # Exakt an der Schwelle (Default 10.0) wird margin_pct noch berechnet.
    result = compute_profit(10.0, 150.0)
    assert result.margin_pct == 1400.0
    result_knapp_drunter = compute_profit(9.99, 150.0)
    assert result_knapp_drunter.margin_pct is None


def test_margin_pct_mindestschwelle_ueberschreibbar_via_fees():
    fees = {"min_purchase_price_for_margin_pct": 0.0}
    result = compute_profit(1.0, 150.0, fees=fees)
    assert result.margin_pct == 14900.0


# ---------- is_robust_flip_candidate() (Phase 11, Punkt A) ----------

def test_robust_flip_candidate_wenn_alle_vier_faktoren_erfuellt():
    assert is_robust_flip_candidate(
        margin_pct=MIN_FLIP_MARGIN_PCT, margin_eur=MIN_FLIP_MARGIN_EUR,
        deal_score=MIN_FLIP_DEAL_SCORE, resale_confidence="MEDIUM",
    ) is True


def test_robust_flip_candidate_mit_high_confidence_auch_erfuellt():
    assert is_robust_flip_candidate(
        margin_pct=30.0, margin_eur=100.0, deal_score=90,
        resale_confidence="HIGH",
    ) is True


def test_kein_flip_candidate_bei_low_confidence():
    assert is_robust_flip_candidate(
        margin_pct=30.0, margin_eur=100.0, deal_score=90,
        resale_confidence="LOW",
    ) is False


def test_kein_flip_candidate_bei_zu_geringer_margin_pct():
    assert is_robust_flip_candidate(
        margin_pct=MIN_FLIP_MARGIN_PCT - 0.01, margin_eur=100.0,
        deal_score=90, resale_confidence="HIGH",
    ) is False


def test_kein_flip_candidate_bei_zu_geringer_margin_eur():
    # Regressionsschutz: genau der Fall, der die urspruengliche
    # Ueberzaehlung verursachte -- hohe Prozent-Marge, aber winziger
    # absoluter Gewinn.
    assert is_robust_flip_candidate(
        margin_pct=50.0, margin_eur=MIN_FLIP_MARGIN_EUR - 0.01,
        deal_score=90, resale_confidence="HIGH",
    ) is False


def test_kein_flip_candidate_bei_zu_niedrigem_deal_score():
    assert is_robust_flip_candidate(
        margin_pct=30.0, margin_eur=100.0,
        deal_score=MIN_FLIP_DEAL_SCORE - 1, resale_confidence="HIGH",
    ) is False


def test_kein_flip_candidate_bei_fehlendem_wert():
    assert is_robust_flip_candidate(None, 100.0, 90, "HIGH") is False
    assert is_robust_flip_candidate(30.0, None, 90, "HIGH") is False
    assert is_robust_flip_candidate(30.0, 100.0, None, "HIGH") is False
    assert is_robust_flip_candidate(30.0, 100.0, 90, None) is False


def test_kein_flip_candidate_ganz_ohne_werte():
    assert is_robust_flip_candidate(None, None, None, None) is False
