"""Tests fuer MatchResult.estimated_resale_price (Auftrag "Angebotswert +
Marktwert + geschaetzter Verkaufspreis auf Deal-Karten"): der in evaluate()
intern bereits fuer compute_profit()/compute_deal_score() berechnete
Reselling-Schaetzwert muss zusaetzlich additiv auf MatchResult mitgegeben
werden -- KEINE neue Berechnung, identischer Wert wie estimated_margin_eur/
-pct zugrunde liegt.

Struktur analog test_matcher_price_history_model.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules, evaluate


def test_estimated_resale_price_gesetzt_wenn_resale_prices_vorliegen():
    """Vollstaendige Daten: resale_prices fuer das Modell vorhanden ->
    MatchResult.estimated_resale_price muss exakt diesem Wert entsprechen
    (identisch zu dem, was bereits estimated_margin_eur/-pct zugrunde
    liegt -- keine zweite/abweichende Berechnung)."""
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        "ASUS RTX 3060 12GB ROG Strix",
        100.0,
        cfg,
        market_prices={"rtx_3060_12gb": 250.0},
        resale_prices={"rtx_3060_12gb": 280.0},
    )
    assert r.matched is True
    assert r.estimated_resale_price == 280.0
    # Muss weiterhin die bestehende Marge zugrunde legen -- keine
    # Parallel-Berechnung, beide Felder muessen konsistent sein.
    assert r.estimated_margin_eur is not None


def test_estimated_resale_price_none_ohne_preishistorie():
    """Kein resale_prices-Eintrag fuer das Modell (Standardfall ohne
    market_prices/resale_prices-Uebergabe) -> sauberer Fallback auf None,
    kein erfundener Wert."""
    cfg = load_rules(RULES_DIR)
    r = evaluate("ASUS RTX 3060 12GB ROG Strix", 100.0, cfg)
    assert r.matched is True
    assert r.estimated_resale_price is None
    assert r.estimated_margin_eur is None


def test_estimated_resale_price_none_bei_explizitem_none_wert():
    """Schritt B/Option 1 (dokumentiert in price_stats.py/matcher.py): der
    Modell-Key ist vorhanden, sein Wert aber explizit None (zu duenne
    Preishistorie fuer eine belastbare Schaetzung) -> BEWUSST kein Fallback
    auf market_price, estimated_resale_price bleibt None."""
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        "ASUS RTX 3060 12GB ROG Strix",
        100.0,
        cfg,
        market_prices={"rtx_3060_12gb": 250.0},
        resale_prices={"rtx_3060_12gb": None},
    )
    assert r.matched is True
    assert r.estimated_resale_price is None


def test_kein_match_liefert_default_match_result_ohne_resale_price():
    """Regressionsschutz: MatchResult(matched=False) (kein Treffer) darf
    durch das neue Feld nicht brechen -- Default bleibt None."""
    cfg = load_rules(RULES_DIR)
    r = evaluate("Voellig unpassender Titel ohne jede Kategorie xyz123", 5.0, cfg)
    assert r.matched is False
    assert r.estimated_resale_price is None
