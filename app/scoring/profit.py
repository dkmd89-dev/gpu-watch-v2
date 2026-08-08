"""Profit-/Margenberechnung (Reselling-/Arbitrage-Konzept, siehe STATUS.md
Abschnitt 16): schätzt die beim Weiterverkauf eines Angebots realistisch
verbleibende Marge, unter Berücksichtigung von Plattform-/Zahlungsgebühren
sowie Versand-/Verpackungskosten (siehe rules/_global.yaml: "fees").

WICHTIGER HINWEIS zum aktuellen Stand: Dieses Modul berechnet ausschließlich
die Marge selbst (Dataclass `Profit`). Es ist in diesem Schritt bewusst NOCH
NICHT an scoring/deal_score.py oder app.py angebunden -- das ist ein
separater, noch nicht freigegebener Folgeschritt (siehe STATUS.md Abschnitt
16, "Profit-Score" als Punkt 1). Dieses Modul ist eigenständig lauffähig und
-testbar, verändert aber (noch) kein bestehendes Scoring-Verhalten.

Ausschliesslich lokal gesammelte Marktpreis-Daten als Grundlage fuer den
geschätzten Verkaufspreis (siehe price_stats.py) -- keine externen
Preis-APIs (analog zum Rest des Projekts).
"""
from __future__ import annotations

from dataclasses import dataclass

# Neutrale Default-Werte je Kostenposition, falls "fees:" in _global.yaml
# fehlt oder eine einzelne Position darin nicht gesetzt ist (z.B. ältere
# Configs vor Einführung dieses Moduls). 0 bedeutet "keine bekannte Kosten-
# information" -- die Marge wird dadurch NICHT künstlich verschlechtert,
# sondern lediglich ohne diese Kostenposition berechnet (rückwärtskompatibel,
# analog zum _PLACEHOLDER_SCORE-Prinzip in deal_score.py, hier aber additiv
# statt eines Platzhalter-Scores, da eine Marge in Euro kein 0-100-Score ist).
_FEE_DEFAULTS: dict[str, float] = {
    "platform_fee_pct": 0.0,
    "payment_fee_pct": 0.0,
    "shipping_cost": 0.0,
    "packaging_cost": 0.0,
}

# Ab welcher geschaetzten Marge (in Prozent vom Kaufpreis, siehe
# Profit.margin_pct) ein Angebot als "Flip-Kandidat" gilt (Dashboard-KPI
# "💰 Flip-Kandidaten"). Bewusst als eigene Konstante hier im Profit-Modul
# (analog zu TOP_DEAL_DISCOUNT_THRESHOLD_A/B_PCT in top_deal.py): keine
# Hardware- oder Marktdaten-Konfiguration, sondern eine Interpretationsregel
# der bereits vorhandenen compute_profit()-Ergebnisse. Wird (noch) nicht in
# diesem Modul selbst ausgewertet -- das erfolgt an der Aufrufstelle in
# app.py (Schritt "Flip-Kandidaten-KPI"), analog dazu, dass top_deal.py
# selbst auch keine deal_score-Berechnung durchfuehrt, sondern nur einen
# bereits berechneten Wert entgegennimmt.
MIN_FLIP_MARGIN_PCT = 20.0

# Bugfix (Auftrag "Flip-Kandidaten-Logik optimieren", Schritt A): Mindest-
# Kaufpreis, ab dem margin_pct ueberhaupt berechnet wird. Hintergrund: bei
# sehr niedrigen/fehlerhaften Kaufpreisen (z.B. 1€ bei Tausch-/VB-Inseraten
# ohne echten Preis) divergiert margin_pct = margin_abs / purchase_price * 100
# ins Absurde (in der Praxis beobachtet: bis zu +58.695% bei purchase_price=1€),
# obwohl margin_abs (Euro) unauffaellig bleibt. purchase_price <= 0 wurde
# bereits zuvor abgefangen (None-Ergebnis) -- dieser Guard erweitert dieselbe
# Schutzlogik auf den ganzen unplausiblen unteren Preisbereich, analog zum
# bestehenden Umgang mit purchase_price <= 0. Ueberschreibbar via
# fees["min_purchase_price_for_margin_pct"] in _global.yaml (bewusst im
# fees-Dict statt eines eigenen Ladepfads -- kleinstmoeglicher Eingriff,
# keine Aenderung an matcher.py/_load_rules_from_dir() noetig).
MIN_PURCHASE_PRICE_FOR_MARGIN_PCT = 10.0


@dataclass(frozen=True)
class Profit:
    """Ergebnis einer Margenberechnung für ein einzelnes Angebot.

    purchase_price: Kaufpreis des Angebots (price aus dem Listing).
    estimated_resale_price: geschätzter Wiederverkaufspreis (aktuell i.d.R.
        PriceStats.market_price desselben price_history_model -- siehe
        Docstring-Hinweis in compute_profit() zur methodischen Einschränkung).
    fees_total: Summe aller Kostenpositionen (prozentual + fix, siehe
        _resolve_fees()).
    margin_abs: geschätzte Marge in Euro (estimated_resale_price -
        purchase_price - fees_total). Kann negativ sein (Verlustgeschäft).
    margin_pct: margin_abs relativ zum Kaufpreis, in Prozent. None, falls
        purchase_price <= 0 (Division durch Null vermieden) ODER
        purchase_price < MIN_PURCHASE_PRICE_FOR_MARGIN_PCT (Bugfix: bei
        Mini-Kaufpreisen ist die Prozent-Kennzahl strukturell irrefuehrend,
        siehe Konstanten-Docstring oben). margin_abs bleibt in beiden
        Faellen weiterhin gesetzt.
    """

    purchase_price: float
    estimated_resale_price: float
    fees_total: float
    margin_abs: float
    margin_pct: float | None


def _resolve_fees(fees: dict | None) -> dict[str, float]:
    """Merged eine (ggf. unvollständige oder leere) fees-Konfiguration mit
    den neutralen Defaults. Fehlende/None -> vollständig neutrale Kosten
    (alle Positionen 0), analog zum Umgang mit manufacturer_reputation in
    deal_score.py::_hersteller_score().
    """
    if not fees:
        return dict(_FEE_DEFAULTS)
    return {key: fees.get(key, default) for key, default in _FEE_DEFAULTS.items()}


def compute_profit(
    purchase_price: float,
    estimated_resale_price: float | None,
    fees: dict | None = None,
) -> Profit | None:
    """Berechnet die geschätzte Marge für ein Angebot.

    estimated_resale_price: aktuell i.d.R. identisch zu PriceStats.market_price
        (siehe price_stats.py) desselben price_history_model -- das ist eine
        bewusste, dokumentierte methodische Vereinfachung in diesem Schritt:
        market_price basiert auf Preisen von Angeboten, die der Bot selbst
        als "günstig" einstuft (Ankaufsperspektive), und dürfte den echten
        Wiederverkaufspreis (Verkaufsperspektive) daher eher unterschätzen.
        Eine differenziertere Verkaufspreis-Schätzung ist ein bewusst offen
        gelassener Folgeschritt (siehe STATUS.md Abschnitt 16).

    Gibt None zurück, wenn kein estimated_resale_price vorliegt (z.B. noch
    keine Preishistorie für dieses Modell) -- analog zu
    price_stats.compute_price_stats(), das bei leeren Datenpunkten ebenfalls
    None statt eines Platzhalter-Objekts liefert, um keine falsche 0€-Marge
    vorzutäuschen.

    margin_pct-Guard (Bugfix, siehe MIN_PURCHASE_PRICE_FOR_MARGIN_PCT-
    Docstring): bei purchase_price unterhalb der Mindestschwelle wird
    margin_pct auf None gesetzt statt einer irrefuehrenden Prozentzahl --
    margin_abs (Euro) ist davon nicht betroffen und bleibt immer gesetzt.
    """
    if estimated_resale_price is None or estimated_resale_price <= 0:
        return None

    resolved = _resolve_fees(fees)
    fees_total = (
        estimated_resale_price * (resolved["platform_fee_pct"] / 100)
        + estimated_resale_price * (resolved["payment_fee_pct"] / 100)
        + resolved["shipping_cost"]
        + resolved["packaging_cost"]
    )

    margin_abs = estimated_resale_price - purchase_price - fees_total

    # min_purchase_price_for_margin_pct: bewusst NICHT Teil von _FEE_DEFAULTS/
    # _resolve_fees() (keine Kostenposition, sondern ein Plausibilitaets-
    # Guard) -- eigener, direkter Lookup im rohen fees-Dict mit demselben
    # "fehlt -> Default"-Verhalten wie die uebrigen fees-Werte.
    min_purchase_price_for_pct = (fees or {}).get(
        "min_purchase_price_for_margin_pct", MIN_PURCHASE_PRICE_FOR_MARGIN_PCT
    )
    margin_pct = (
        (margin_abs / purchase_price * 100)
        if purchase_price >= min_purchase_price_for_pct
        else None
    )

    return Profit(
        purchase_price=purchase_price,
        estimated_resale_price=estimated_resale_price,
        fees_total=round(fees_total, 2),
        margin_abs=round(margin_abs, 2),
        margin_pct=round(margin_pct, 2) if margin_pct is not None else None,
    )
