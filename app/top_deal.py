"""Automatische Top-Deal-Erkennung (Phase 7, Schritt 7.3): vergleicht einen
aktuellen Angebotspreis mit dem in Schritt 7.2 berechneten Marktpreis
(price_stats.PriceStats.market_price) fuer dasselbe price_history_model UND
kombiniert das Ergebnis mit dem bereits vorhandenen, gewichteten deal_score
(scoring/deal_score.py) desselben Angebots.

WICHTIG: Das ist eine ZUSAETZLICHE, datengetriebene Top-Deal-Erkennung --
unabhaengig von der bestehenden regelbasierten "deal_rating"-Einstufung
(Top-Deal/Guter Preis/Okay) aus den YAML-Regeln (siehe matcher.py). Jene
vergleicht den Preis gegen eine FEST in der YAML hinterlegte Preisgrenze
(max_price je Regel); diese hier vergleicht stattdessen gegen den aus der
LOKAL gesammelten Preishistorie abgeleiteten Marktpreis.

HISTORIE (bewusst dokumentiert, siehe Auftrag "Top-Deal-Logik optimieren"):
Bis zu diesem Schritt war die Regel ausschliesslich "Rabatt >= 15% zum
Marktpreis" -- ohne Beruecksichtigung des deal_score. Das klassifizierte in
der Praxis zu viele Angebote als Top-Deal (u.a. auch Angebote mit
mittelmaessiger Hardware-Ausstattung, aber zufaellig niedrigem Preis). Die
Deal-Score-Engine selbst (scoring/deal_score.py) bleibt davon unveraendert
-- diese Datei kombiniert lediglich zwei bereits bestehende Signale
(Marktpreis-Rabatt + deal_score) neu.

Neue Regel (siehe TopDealResult/evaluate_top_deal()):

    is_top_deal =
        (deal_score >= TOP_DEAL_SCORE_THRESHOLD_A UND
         discount_pct >= TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT)
        ODER
        (deal_score >= TOP_DEAL_SCORE_THRESHOLD_B UND
         discount_pct >= TOP_DEAL_DISCOUNT_THRESHOLD_B_PCT)
"""
from __future__ import annotations

from dataclasses import dataclass

from price_stats import PriceStats

# Mindestanzahl an Preishistorie-Datenpunkten, ab der ueberhaupt eine
# automatische Top-Deal-Aussage getroffen wird. Mit weniger Daten waere der
# Marktpreis (siehe price_stats._market_price()) noch zu instabil, um daraus
# verlaesslich "X% unter Marktpreis" abzuleiten -- die Funktion gibt dann
# ehrlich "zu wenig Datengrundlage" zurueck statt eine unsichere Aussage.
MIN_SAMPLES_FOR_TOP_DEAL_DETECTION = 3

# Regel A: niedrigere Score-Huerde, dafuer hoehere Rabatt-Huerde.
TOP_DEAL_SCORE_THRESHOLD_A = 80
TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT = 25.0

# Regel B: hoehere Score-Huerde, dafuer niedrigere Rabatt-Huerde.
TOP_DEAL_SCORE_THRESHOLD_B = 90
TOP_DEAL_DISCOUNT_THRESHOLD_B_PCT = 20.0


@dataclass(frozen=True)
class TopDealResult:
    """Ergebnis der automatischen Top-Deal-Pruefung fuer einen Einzelpreis."""

    is_top_deal: bool
    price: float
    market_price: float | None  # None, falls keine/zu wenig Datengrundlage
    discount_pct: float | None  # positiv = unter Marktpreis, negativ = darueber
    reason: str  # kurze, menschenlesbare Begruendung (z.B. fuers Dashboard/Log)
    rule: str | None = None  # "A", "B" oder None (keine Regel erfuellt/anwendbar)


def _discount_pct(price: float, market_price: float) -> float:
    return ((market_price - price) / market_price) * 100


def evaluate_top_deal(
    price: float,
    stats: PriceStats | None,
    deal_score: int | None = None,
    *,
    min_samples: int = MIN_SAMPLES_FOR_TOP_DEAL_DETECTION,
    score_threshold_a: int = TOP_DEAL_SCORE_THRESHOLD_A,
    discount_threshold_a_pct: float = TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT,
    score_threshold_b: int = TOP_DEAL_SCORE_THRESHOLD_B,
    discount_threshold_b_pct: float = TOP_DEAL_DISCOUNT_THRESHOLD_B_PCT,
) -> TopDealResult:
    """Prueft, ob `price` angesichts der Marktpreis-Statistik `stats` UND des
    bereits berechneten `deal_score` ein automatisch erkannter Top-Deal ist.

    `stats` ist typischerweise das Ergebnis von
    price_stats.compute_price_stats() fuer das passende price_history_model
    des Angebots. None bedeutet "noch keine Preishistorie fuer dieses
    Modell vorhanden" (z.B. allererster Treffer).

    `deal_score` ist der bereits an anderer Stelle (scoring/deal_score.py)
    berechnete, gewichtete 0-100-Score desselben Angebots (matcher.py ->
    MatchResult.deal_score). None (Default) bedeutet "kein Score bekannt"
    -- ein Angebot kann dann NIE Top-Deal sein, da beide Regeln zwingend
    einen Mindest-Score voraussetzen (siehe Modul-Docstring). Das ist die
    bewusst sichere Default-Haltung fuer Aufrufstellen, die (noch) keinen
    deal_score uebergeben.

    Regel A: deal_score >= score_threshold_a UND discount_pct >= discount_threshold_a_pct
    Regel B: deal_score >= score_threshold_b UND discount_pct >= discount_threshold_b_pct
    """
    if stats is None or stats.count < min_samples:
        count = stats.count if stats is not None else 0
        return TopDealResult(
            is_top_deal=False,
            price=price,
            market_price=stats.market_price if stats is not None else None,
            discount_pct=None,
            reason=(
                f"Zu wenig Datengrundlage ({count} Preispunkt(e), "
                f"mindestens {min_samples} noetig)"
            ),
        )

    if stats.market_price <= 0:
        # Sollte praktisch nicht vorkommen (Preise sind >= 0), aber schuetzt
        # vor einer irrefuehrenden Prozent-Aussage bei Division durch ~0.
        return TopDealResult(
            is_top_deal=False,
            price=price,
            market_price=stats.market_price,
            discount_pct=None,
            reason="Marktpreis nicht aussagekräftig (0€ oder weniger)",
        )

    discount_pct = _discount_pct(price, stats.market_price)
    richtung = "unter" if discount_pct >= 0 else "über"
    basis_reason = (
        f"{abs(discount_pct):.1f}% {richtung} Marktpreis "
        f"({price:.0f}€ vs. {stats.market_price:.0f}€ Marktpreis)"
    )

    if deal_score is None or price <= 0 or price >= stats.market_price or discount_pct < 0:
        # Kein Score bekannt, Preis nicht (mehr) positiv, oder Preis auf/ueber
        # Marktwert -- unter keinen Umstaenden ein Top-Deal (siehe Auftrag
        # Abschnitt 4/8).
        return TopDealResult(
            is_top_deal=False,
            price=price,
            market_price=stats.market_price,
            discount_pct=discount_pct,
            reason=basis_reason if deal_score is not None else (
                basis_reason + " (kein deal_score vorhanden)"
            ),
        )

    rule_a = deal_score >= score_threshold_a and discount_pct >= discount_threshold_a_pct
    rule_b = deal_score >= score_threshold_b and discount_pct >= discount_threshold_b_pct
    is_top_deal = rule_a or rule_b
    rule = "B" if rule_b else ("A" if rule_a else None)

    if is_top_deal:
        reason = f"{basis_reason} · Score {deal_score} · Regel {rule}"
    else:
        reason = f"{basis_reason} · Score {deal_score} (keine Top-Deal-Regel erfuellt)"

    return TopDealResult(
        is_top_deal=is_top_deal,
        price=price,
        market_price=stats.market_price,
        discount_pct=discount_pct,
        reason=reason,
        rule=rule,
    )
