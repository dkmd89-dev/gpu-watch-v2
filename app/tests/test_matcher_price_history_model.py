"""Tests fuer MatchResult.category/price_history_model in matcher.evaluate()
(Phase 7, Schritt 7.1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules, evaluate


def test_gpu_treffer_liefert_kategorie_und_price_history_model():
    cfg = load_rules(RULES_DIR)
    r = evaluate("ASUS RTX 3060 12GB ROG Strix", 185.0, cfg)
    assert r.matched is True
    assert r.category == "gpu"
    assert r.price_history_model == "rtx_3060_12gb"


def test_verschiedene_marken_desselben_modells_teilen_price_history_model():
    # Zwei unterschiedliche Regeln (verschiedene Marken/Preisgrenzen), aber
    # dieselbe Grafikkarte -- muss auf denselben Preishistorie-Schluessel
    # gruppiert werden, sonst waere die Marktpreis-Statistik (Schritt 7.2)
    # ueber viele Einzelregeln fragmentiert.
    cfg = load_rules(RULES_DIR)
    r_asus = evaluate("ASUS RTX 3060 12GB ROG Strix", 185.0, cfg)
    r_msi = evaluate("MSI RTX 3060 12GB Gaming X", 185.0, cfg)
    assert r_asus.price_history_model == r_msi.price_history_model == "rtx_3060_12gb"


def test_office_pc_treffer_liefert_kategorie_und_price_history_model():
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        "Office PC Intel Core i5-8500 16GB DDR4 RAM 256GB SSD Tower", 250.0, cfg
    )
    assert r.matched is True
    assert r.category == "office_pc"
    assert r.price_history_model == "office_pc"


def test_gaming_pc_beide_rating_stufen_teilen_price_history_model():
    cfg = load_rules(RULES_DIR)
    top_deal = evaluate(
        "Gaming PC Intel Core i5-8500 16GB DDR4 RAM RTX 3060 Tower", 280.0, cfg
    )
    okay = evaluate(
        # 420€: innerhalb der kalibrierten Okay-Grenze (450€, siehe
        # Abschnitt 15) -- vorher 500€, das nach der Kalibrierung ueber der
        # neuen Grenze gelegen haette.
        "Gaming PC Intel Core i5-8500 16GB DDR4 RAM RTX 4060 Tower", 420.0, cfg
    )
    assert top_deal.matched is True and okay.matched is True
    assert top_deal.category == okay.category == "gaming_pc"
    assert top_deal.price_history_model == okay.price_history_model == "gaming_pc"


def test_kein_treffer_hat_keine_kategorie_und_kein_model():
    cfg = load_rules(RULES_DIR)
    r = evaluate("RTX 3060 defekt", 50.0, cfg)
    assert r.matched is False
    assert r.category is None
    assert r.price_history_model is None


def test_legacy_einzeldatei_modus_faellt_auf_rule_label_zurueck():
    # Legacy-Fixture hat kein price_history_model-Feld in der YAML -> Fallback
    # auf rule_label (siehe matcher.evaluate()-Kommentar), keine _category.
    fixture = str(Path(__file__).resolve().parent / "fixtures" / "legacy_single_file_rules.yaml")
    cfg = load_rules(fixture)
    r = evaluate("ASUS RTX 2080Ti DUAL Lüfter", 15.0, cfg)
    assert r.matched is True
    assert r.category is None
    assert r.price_history_model == r.rule_label


# ---------- market_prices-Parameter (Phase 7, Schritt 7.4) ----------

def test_evaluate_ohne_market_prices_unveraendert():
    # Rueckwaertskompatibilitaet: kein market_prices-Argument (Default None)
    # -> identisches Ergebnis wie vor Schritt 7.4.
    cfg = load_rules(RULES_DIR)
    r_ohne_arg = evaluate("ASUS RTX 3060 12GB ROG Strix", 185.0, cfg)
    r_mit_none = evaluate("ASUS RTX 3060 12GB ROG Strix", 185.0, cfg, market_prices=None)
    assert r_ohne_arg.deal_score == r_mit_none.deal_score


def test_evaluate_nutzt_marktpreis_fuer_passendes_model():
    cfg = load_rules(RULES_DIR)
    market_prices = {"rtx_3060_12gb": 185.0}  # Marktpreis == Angebotspreis -> neutral

    r_ohne_markt = evaluate("ASUS RTX 3060 12GB ROG Strix", 185.0, cfg)
    r_mit_markt = evaluate("ASUS RTX 3060 12GB ROG Strix", 185.0, cfg, market_prices=market_prices)

    assert r_mit_markt.deal_score != r_ohne_markt.deal_score


def test_evaluate_ignoriert_marktpreis_fuer_anderes_model():
    # market_prices enthaelt nur einen Eintrag fuer ein ANDERES Modell ->
    # darf das Ergebnis fuer die RTX-3060-Regel nicht beeinflussen.
    cfg = load_rules(RULES_DIR)
    market_prices = {"office_pc": 999.0}

    r_ohne_markt = evaluate("ASUS RTX 3060 12GB ROG Strix", 185.0, cfg)
    r_mit_fremdem_markt = evaluate(
        "ASUS RTX 3060 12GB ROG Strix", 185.0, cfg, market_prices=market_prices
    )

    assert r_ohne_markt.deal_score == r_mit_fremdem_markt.deal_score


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
