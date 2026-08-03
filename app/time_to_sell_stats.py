"""Time-to-Sell-Statistik je Kategorie (Reselling-/Arbitrage-Konzept,
STATUS.md Abschnitt 16, Baustein 6, Schritt 3): On-demand Berechnung aus
time_to_sell.jsonl -- KEINE Persistenz der Statistik selbst, analog zu
price_stats.py::compute_price_stats().

Gruppierung bewusst nach KATEGORIE statt nach price_history_model (anders
als price_stats.py): das Konzept (STATUS.md Abschnitt 16, Baustein 6)
verlangt einen "Liquiditäts-Proxy je Kategorie". Einzelne Modelle liefern
in der Praxis zu wenige Delisting-Ereignisse für eine belastbare Statistik
(ein Delisting-Datenpunkt entsteht erst nach mehreren aufeinanderfolgenden
Scans ohne erneutes Sichten, siehe presence_tracking.py) -- eine
Kategorie (z.B. "gpu", "office_pc") sammelt diese Ereignisse über alle
ihre Modelle hinweg und kommt so schneller zu einer aussagekräftigen
Stichprobengröße.

Bewusst schlanker als price_stats.py: kein Trend, keine Perzentile/
Marktpreis-Näherung -- das Konzept verlangt für diesen Baustein
ausdrücklich nur "Median/Mittelwert Time-to-Sell je Kategorie" (STATUS.md,
Punkt d, Baustein 6). Perzentile/Trend können bei Bedarf als eigener
Folgeschritt ergänzt werden, ohne diese Funktionen zu brechen.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from time_to_sell import TimeToSellPoint


@dataclass(frozen=True)
class TimeToSellStats:
    """Statistik-Zusammenfassung für EINE Kategorie (z.B. "gpu",
    "office_pc") über alle bisher erkannten Delisting-Ereignisse.

    Tage-Werte sind, wie in TimeToSellPoint, Fließkommazahlen (können
    Bruchteile enthalten) -- Rundung erfolgt erst bei der Anzeige
    (Dashboard, Folgeschritt), nicht hier.
    """

    category: str
    count: int
    min_days: float
    max_days: float
    mean_days: float
    median_days: float


def group_by_category(points: list[TimeToSellPoint]) -> dict[str, list[TimeToSellPoint]]:
    """Gruppiert Datenpunkte nach ihrer category.

    Punkte mit category=None werden übersprungen (sollte praktisch nicht
    vorkommen -- make_time_to_sell_point() erlaubt zwar category=None,
    aber ohne Kategorie ist keine sinnvolle Gruppierung möglich; ein
    fehlendes category-Feld ist kein Grund, den kompletten Datenpunkt zu
    verwerfen, aber er kann in dieser Statistik keiner Gruppe zugeordnet
    werden).
    """
    groups: dict[str, list[TimeToSellPoint]] = {}
    for point in points:
        if point.category is None:
            continue
        groups.setdefault(point.category, []).append(point)
    return groups


def compute_time_to_sell_stats(category: str, points: list[TimeToSellPoint]) -> TimeToSellStats | None:
    """Berechnet die Statistik für EINE Kategorie.

    Gibt None zurück, wenn `points` leer ist (keine Datengrundlage) --
    absichtlich kein Platzhalter-Objekt mit Nullen, analog
    price_stats.compute_price_stats() (leicht mit einer echten
    "0 Tage"-Statistik verwechselbar).
    """
    if not points:
        return None

    days = [p.days for p in points]

    return TimeToSellStats(
        category=category,
        count=len(days),
        min_days=min(days),
        max_days=max(days),
        mean_days=statistics.fmean(days),
        median_days=statistics.median(days),
    )


def compute_all_time_to_sell_stats(points: list[TimeToSellPoint]) -> dict[str, TimeToSellStats]:
    """Berechnet die Statistik für ALLE in `points` vorkommenden Kategorien
    in einem Rutsch (analog zum Aufrufmuster von price_stats.py in
    app.py::_load_price_stats(), das ebenfalls "einmal pro Scan über alle
    Modelle" berechnet statt pro Kategorie einzeln aufgerufen zu werden).
    """
    stats: dict[str, TimeToSellStats] = {}
    for category, category_points in group_by_category(points).items():
        result = compute_time_to_sell_stats(category, category_points)
        if result is not None:
            stats[category] = result
    return stats
