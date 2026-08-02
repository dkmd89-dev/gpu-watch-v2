"""Tests fuer scoring/profit.py (Reselling-/Arbitrage-Konzept)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring.profit import Profit, compute_profit


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
