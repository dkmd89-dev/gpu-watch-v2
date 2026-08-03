"""Cross-Platform-Preisvergleich (Reselling-/Arbitrage-Konzept, STATUS.md
Abschnitt 16, Baustein 4, Schritt 1): On-demand Berechnung aus bereits
vorhandenen price_history.jsonl-Datenpunkten -- KEINE Persistenz der
Statistik selbst, analog zu price_stats.py::compute_price_stats() und
time_to_sell_stats.py::compute_time_to_sell_stats().

Datengrundlage existiert bereits vollstaendig: jeder PricePoint traegt
schon ein `source`-Feld (z.B. "kleinanzeigen", "ebay", "quoka", siehe
scrapers/registry.py). price_stats.py gruppiert bisher nur nach `model`,
nicht zusaetzlich nach `source` -- dieses Modul schliesst genau diese
Luecke, ohne price_stats.py selbst anzufassen. Keine neuen Scraper/Daten
noetig, reine Auswertungslogik.

Gruppierung bewusst nach MODEL (price_history_model), nicht nach
Kategorie (anders als time_to_sell_stats.py): ein Preis-Spread ist nur
zwischen identischen Produkten sinnvoll vergleichbar (z.B. "rtx_3060_12gb"
auf Kleinanzeigen vs. eBay) -- ein Kategorie-weiter Vergleich wuerde
Aepfel mit Birnen vergleichen (unterschiedliche Modelle je Quelle).

Bewusst KEIN Mindest-Stichprobenumfang pro Quelle in diesem ersten
Schritt (anders als price_stats.py::_MIN_SAMPLES_FOR_PERCENTILE_MARKET_
PRICE): schon 1 Datenpunkt pro Quelle liefert einen Vergleichswert, auch
wenn er statistisch schwach ist -- das Signal ist rein informativ, kein
score-relevanter Wert (siehe Designentscheidung "Schritt 1" in STATUS.md).

Noch KEINE Anbindung an app.py/Dashboard/Deal-Score in diesem Schritt --
folgt dem etablierten Vorgehen (erst Berechnungslogik + Tests, dann
separate Verdrahtung, analog profit.py/price_stats.py/time_to_sell_stats.py).
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from price_history import PricePoint


@dataclass(frozen=True)
class SourceStats:
    """Statistik-Zusammenfassung für EINE Quelle (z.B. "kleinanzeigen",
    "ebay") innerhalb eines Modells."""

    source: str
    count: int
    mean_price: float
    median_price: float


@dataclass(frozen=True)
class CrossPlatformStats:
    """Preisvergleich über alle Quellen hinweg für EIN Modell
    (price_history_model, z.B. "rtx_3060_12gb").

    spread_pct: prozentualer Abstand zwischen der teuersten und der
        günstigsten Quelle, relativ zur günstigsten Quelle:
        (teuerste_quelle.mean_price - guenstigste_quelle.mean_price)
        / guenstigste_quelle.mean_price * 100.
        0.0, falls günstigste und teuerste Quelle identisch sind
        (gleicher mean_price) -- kein Spread vorhanden.
    """

    model: str
    by_source: dict[str, SourceStats]
    cheapest_source: str
    priciest_source: str
    spread_pct: float


def group_by_source(points: list[PricePoint]) -> dict[str, list[PricePoint]]:
    """Gruppiert Datenpunkte (bereits auf EIN Modell vorgefiltert) nach
    ihrer source.

    Punkte mit source=None/leer werden übersprungen -- PricePoint.source
    ist zwar als str (nicht optional) deklariert, aber ältere/kaputte
    Zeilen könnten theoretisch einen leeren String enthalten; ohne Quelle
    ist keine sinnvolle Gruppierung möglich (analog zu group_by_category()
    in time_to_sell_stats.py, das category=None ebenso überspringt).
    """
    groups: dict[str, list[PricePoint]] = {}
    for point in points:
        if not point.source:
            continue
        groups.setdefault(point.source, []).append(point)
    return groups


def compute_cross_platform_stats(model: str, points: list[PricePoint]) -> CrossPlatformStats | None:
    """Berechnet den Cross-Platform-Preisvergleich für EIN Modell.

    `points` sollte bereits auf dieses `model` gefiltert sein (analog zum
    Aufrufmuster von price_stats.compute_price_stats()).

    Gibt None zurück, wenn Datenpunkte aus WENIGER als 2 verschiedenen
    Quellen vorliegen -- kein Vergleich möglich (auch wenn `points` selbst
    nicht leer ist, z.B. nur Kleinanzeigen-Daten für dieses Modell).
    """
    by_source_points = group_by_source(points)
    if len(by_source_points) < 2:
        return None

    by_source: dict[str, SourceStats] = {}
    for source, source_points in by_source_points.items():
        prices = [p.price for p in source_points]
        by_source[source] = SourceStats(
            source=source,
            count=len(prices),
            mean_price=statistics.fmean(prices),
            median_price=statistics.median(prices),
        )

    cheapest_source = min(by_source, key=lambda s: by_source[s].mean_price)
    priciest_source = max(by_source, key=lambda s: by_source[s].mean_price)

    cheapest_mean = by_source[cheapest_source].mean_price
    priciest_mean = by_source[priciest_source].mean_price
    spread_pct = (
        0.0
        if cheapest_mean == 0
        else (priciest_mean - cheapest_mean) / cheapest_mean * 100
    )

    return CrossPlatformStats(
        model=model,
        by_source=by_source,
        cheapest_source=cheapest_source,
        priciest_source=priciest_source,
        spread_pct=spread_pct,
    )


def compute_all_cross_platform_stats(points: list[PricePoint]) -> dict[str, CrossPlatformStats]:
    """Berechnet den Cross-Platform-Vergleich für ALLE in `points`
    vorkommenden Modelle in einem Rutsch (analog compute_all_time_to_
    sell_stats() / dem Aufrufmuster von price_stats.py in
    app.py::_load_price_stats()).

    Punkte mit model=None werden übersprungen (price_history_model ist
    optional bei der Regel-Definition, siehe price_history.py-Docstring).
    """
    by_model: dict[str, list[PricePoint]] = {}
    for point in points:
        if not point.model:
            continue
        by_model.setdefault(point.model, []).append(point)

    stats: dict[str, CrossPlatformStats] = {}
    for model, model_points in by_model.items():
        result = compute_cross_platform_stats(model, model_points)
        if result is not None:
            stats[model] = result
    return stats
