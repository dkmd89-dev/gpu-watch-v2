"""Marktpreis-Statistik (Phase 7, Schritt 7.2): On-demand Berechnung aus
price_history.jsonl -- KEINE Persistenz der Statistik selbst, sie wird bei
Bedarf (z.B. spaeter im Dashboard/API, Phase 8) frisch aus den vorhandenen
PricePoint-Datenpunkten (siehe price_history.py) berechnet.

Ausschliesslich lokal gesammelte Daten (siehe Auftrag: keine externen
Preis-APIs) -- die Statistik ist also nur so gut wie die bisher gesammelte
Preishistorie fuer das jeweilige `price_history_model`.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime

from price_history import PricePoint

# Ab dieser Datenpunkt-Anzahl gelten Perzentile als statistisch tragfaehig
# genug, um den Marktpreis auf ihnen (statt nur auf dem Median) aufzubauen.
# Bei weniger Datenpunkten waeren 5%/10%-Perzentile ohnehin kaum aussagekraeftig
# (siehe _percentile()), daher faellt der Marktpreis dann auf den Median zurueck.
_MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE = 5

# Ab dieser Datenpunkt-Anzahl wird ueberhaupt ein Trend berechnet (braucht
# zwei sinnvoll grosse Haelften, siehe _compute_trend()). Darunter ist die
# Aufteilung in "alte" vs. "neue" Haelfte zu verrauscht, um einen Trend
# verlaesslich von Zufallsschwankungen zu unterscheiden.
_MIN_SAMPLES_FOR_TREND = 4

# Schwelle in Prozent, ab der eine Preisaenderung zwischen alter und neuer
# Haelfte als "steigend"/"fallend" statt "stabil" gilt. Bewusst als
# Code-Konstante (Interpretationsregel der Statistik-Berechnung selbst,
# keine Hardware- oder Marktdaten-Konfiguration wie die Gewichte in
# _global.yaml).
_TREND_THRESHOLD_PCT = 5.0

TREND_STEIGEND = "steigend"
TREND_FALLEND = "fallend"
TREND_STABIL = "stabil"
TREND_UNBEKANNT = "unbekannt"


@dataclass(frozen=True)
class PriceStats:
    """Statistik-Zusammenfassung fuer ein `price_history_model` (z.B.
    "rtx_3060_12gb", "office_pc") ueber alle bisher gesammelten Datenpunkte.
    """

    model: str
    count: int
    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    percentile_5: float
    percentile_10: float
    market_price: float
    trend: str  # "steigend" / "fallend" / "stabil" / "unbekannt"
    trend_change_pct: float | None  # None, falls trend == "unbekannt"


def group_by_model(points: list[PricePoint]) -> dict[str, list[PricePoint]]:
    """Gruppiert Datenpunkte nach ihrem price_history_model-Schluessel."""
    groups: dict[str, list[PricePoint]] = {}
    for point in points:
        groups.setdefault(point.model, []).append(point)
    return groups


def _percentile(sorted_prices: list[float], pct: float) -> float:
    """k-tes Perzentil ueber eine BEREITS sortierte Preisliste.

    Nutzt statistics.quantiles() (linear interpoliert, "inclusive"-Methode
    -- deckt 0%/100% exakt auf Min/Max ab). Bei nur einem Datenpunkt ist
    jedes Perzentil per Definition dieser Wert selbst (quantiles() verlangt
    mindestens zwei Datenpunkte und wuerde sonst einen Fehler werfen).
    """
    if len(sorted_prices) == 1:
        return sorted_prices[0]

    # n=100 liefert 99 Schnittpunkte: index 0 = 1. Perzentil, index k-1 = k-tes.
    cut_points = statistics.quantiles(sorted_prices, n=100, method="inclusive")
    index = max(0, min(len(cut_points) - 1, round(pct) - 1))
    return cut_points[index]


def _market_price(sorted_prices: list[float], p10: float, p90: float, median: float) -> float:
    """Marktpreis-Naeherung: getrimmter Durchschnitt aller Preise zwischen dem
    10%- und 90%-Perzentil (schliesst extreme Ausreisser nach oben/unten aus,
    nutzt aber -- anders als der reine Median -- mehrere Datenpunkte).

    Bei zu wenigen Datenpunkten (< _MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE)
    sind Perzentile statistisch kaum tragfaehig -- dann faellt der
    Marktpreis stattdessen auf den robusteren Median zurueck.
    """
    if len(sorted_prices) < _MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE:
        return median

    trimmed = [p for p in sorted_prices if p10 <= p <= p90]
    if not trimmed:
        return median  # sollte praktisch nie vorkommen, aber sicherer Fallback

    return statistics.fmean(trimmed)


def _compute_trend(points: list[PricePoint]) -> tuple[str, float | None]:
    """Vergleicht den Durchschnittspreis der aelteren mit der neueren Haelfte
    der (chronologisch sortierten) Datenpunkte.

    Rueckgabe: (trend_label, prozentuale_aenderung). prozentuale_aenderung
    ist None, wenn kein Trend berechnet werden konnte (zu wenig Daten oder
    aeltere Haelfte hatte Durchschnittspreis 0).
    """
    if len(points) < _MIN_SAMPLES_FOR_TREND:
        return TREND_UNBEKANNT, None

    by_date = sorted(points, key=lambda p: p.date)
    mid = len(by_date) // 2
    older_half = by_date[:mid]
    newer_half = by_date[mid:]

    older_mean = statistics.fmean(p.price for p in older_half)
    newer_mean = statistics.fmean(p.price for p in newer_half)

    if older_mean == 0:
        return TREND_UNBEKANNT, None

    change_pct = ((newer_mean - older_mean) / older_mean) * 100

    if change_pct > _TREND_THRESHOLD_PCT:
        return TREND_STEIGEND, change_pct
    if change_pct < -_TREND_THRESHOLD_PCT:
        return TREND_FALLEND, change_pct
    return TREND_STABIL, change_pct


def compute_price_stats(model: str, points: list[PricePoint]) -> PriceStats | None:
    """Berechnet die vollstaendige Statistik fuer EIN price_history_model.

    Gibt None zurueck, wenn `points` leer ist (keine Datengrundlage) --
    absichtlich kein Platzhalter-Objekt mit Nullen, da das leicht mit einer
    echten 0€-Statistik verwechselt werden koennte.
    """
    if not points:
        return None

    prices = sorted(p.price for p in points)
    p5 = _percentile(prices, 5)
    p10 = _percentile(prices, 10)
    median = statistics.median(prices)
    p90 = _percentile(prices, 90)
    trend, trend_change_pct = _compute_trend(points)

    return PriceStats(
        model=model,
        count=len(prices),
        min_price=min(prices),
        max_price=max(prices),
        mean_price=statistics.fmean(prices),
        median_price=median,
        percentile_5=p5,
        percentile_10=p10,
        market_price=_market_price(prices, p10, p90, median),
        trend=trend,
        trend_change_pct=trend_change_pct,
    )


def compute_all_price_stats(points: list[PricePoint]) -> dict[str, PriceStats]:
    """Berechnet die Statistik fuer JEDES vorkommende price_history_model.

    Nimmt bereits eingelesene Datenpunkte entgegen (z.B. aus
    price_history.read_price_points()), statt selbst die Datei zu lesen --
    haelt dieses Modul unabhaengig von Dateipfaden und leicht testbar.
    """
    return {
        model: compute_price_stats(model, model_points)
        for model, model_points in group_by_model(points).items()
    }
