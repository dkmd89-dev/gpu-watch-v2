"""Automatische Top-Deal-Erkennung (Phase 7, Schritt 7.3): vergleicht einen
aktuellen Angebotspreis mit dem in Schritt 7.2 berechneten Marktpreis
(price_stats.PriceStats.market_price) fuer dasselbe price_history_model.

WICHTIG: Das ist eine ZUSAETZLICHE, datengetriebene Top-Deal-Erkennung --
unabhaengig von der bestehenden regelbasierten "deal_rating"-Einstufung
(Top-Deal/Guter Preis/Okay) aus den YAML-Regeln (siehe matcher.py). Jene
vergleicht den Preis gegen eine FEST in der YAML hinterlegte Preisgrenze
(max_price je Regel); diese hier vergleicht stattdessen gegen den aus der
LOKAL gesammelten Preishistorie abgeleiteten Marktpreis. Beide Signale
koennen sich spaeter ergaenzen (siehe Schritt 7.4: Marktpreis-Integration
in scoring/deal_score.py::_price_score()), sind aber bewusst getrennt
gehalten, solange das noch nicht verdrahtet ist.
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

# Ab wie viel Prozent UNTER dem Marktpreis ein Angebot als automatisch
# erkannter Top-Deal gilt. Bewusst als eigene Konstante (keine Hardware-
# oder Marktdaten-Konfiguration, sondern eine Interpretationsregel dieser
# Erkennungslogik selbst -- analog zu _TREND_THRESHOLD_PCT in price_stats.py).
TOP_DEAL_DISCOUNT_THRESHOLD_PCT = 15.0


@dataclass(frozen=True)
class TopDealResult:
    """Ergebnis der automatischen Top-Deal-Pruefung fuer einen Einzelpreis."""

    is_top_deal: bool
    price: float
    market_price: float | None  # None, falls keine/zu wenig Datengrundlage
    discount_pct: float | None  # positiv = unter Marktpreis, negativ = darueber
    reason: str  # kurze, menschenlesbare Begruendung (z.B. fuers Dashboard/Log)


def evaluate_top_deal(
    price: float,
    stats: PriceStats | None,
    *,
    min_samples: int = MIN_SAMPLES_FOR_TOP_DEAL_DETECTION,
    discount_threshold_pct: float = TOP_DEAL_DISCOUNT_THRESHOLD_PCT,
) -> TopDealResult:
    """Prueft, ob `price` angesichts der Marktpreis-Statistik `stats` ein
    automatisch erkannter Top-Deal ist.

    `stats` ist typischerweise das Ergebnis von
    price_stats.compute_price_stats() fuer das passende price_history_model
    des Angebots. None bedeutet "noch keine Preishistorie fuer dieses
    Modell vorhanden" (z.B. allererster Treffer).
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

    discount_pct = ((stats.market_price - price) / stats.market_price) * 100
    is_top_deal = discount_pct >= discount_threshold_pct
    richtung = "unter" if discount_pct >= 0 else "über"

    return TopDealResult(
        is_top_deal=is_top_deal,
        price=price,
        market_price=stats.market_price,
        discount_pct=discount_pct,
        reason=(
            f"{abs(discount_pct):.1f}% {richtung} Marktpreis "
            f"({price:.0f}€ vs. {stats.market_price:.0f}€ Marktpreis)"
        ),
    )
