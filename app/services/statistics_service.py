"""Services-Paket (roadmap.md Phase 3, Schritt 3.2): Preisstatistik-Helper,
extrahiert aus app.py.

1:1 uebernommen -- kein Verhalten geaendert. app.py importiert diese
Funktionen re-exportartig, damit alle bestehenden Aufrufstellen und Tests
unveraendert weiterfunktionieren.
"""
import logging
from pathlib import Path

from price_history import read_price_points
from price_stats import compute_all_price_stats, compute_resale_stats_by_group, PriceStats

log = logging.getLogger("gpu-watch")


def _load_price_stats(path: Path) -> dict[str, PriceStats]:
    """Berechnet die volle Preisstatistik je price_history_model.

    Gemeinsame Basis für zwei Verwendungszwecke:
    - Marktpreise fürs Deal-Score-Scoring (Schritt 7.5, siehe
      _market_prices_from_stats() unten)
    - Top-Deal-Erkennung (Schritt 8.2, siehe evaluate_top_deal() in run_scan())

    Ein Fehler beim Statistik-Aufbau darf den Scan nicht abbrechen --
    Preisstatistik ist eine Zusatzfunktion, kein kritischer Pfad (analog zu
    append_price_point() in price_history.py).
    """
    try:
        points = read_price_points(path)
        return compute_all_price_stats(points)
    except Exception as e:
        log.error("Preisstatistik konnte nicht berechnet werden: %s", e, exc_info=True)
        return {}


def _load_resale_stats_by_group(
    path: Path, model_to_group: dict[str, str]
) -> dict[str, PriceStats]:
    """Wie _load_price_stats(), aber gruppiert nach der groeberen Resale-
    Price-Gruppe (Option 2, STATUS.md Abschnitt 33b) statt nach dem exakten
    price_history_model. GETRENNT von _load_price_stats() -- market_prices
    und die Top-Deal-Erkennung nutzen weiterhin ausschliesslich
    _load_price_stats()/compute_all_price_stats(), unveraendert.

    model_to_group leer (aeltere Configs / Legacy-Einzeldatei-Modus ohne
    "resale_price_groups"-Key) -> jedes Modell bildet seine eigene Gruppe,
    identisches Ergebnis zu _load_price_stats() (volle Rueckwaertskompatibilitaet).

    Fehler bei der Berechnung duerfen den Scan nicht abbrechen (analog
    _load_price_stats()) -- reine Zusatzfunktion.
    """
    try:
        points = read_price_points(path)
        return compute_resale_stats_by_group(points, model_to_group)
    except Exception as e:
        log.error(
            "Resale-Gruppen-Preisstatistik konnte nicht berechnet werden: %s",
            e, exc_info=True,
        )
        return {}


def _market_prices_from_stats(stats_by_model: dict[str, PriceStats]) -> dict[str, float]:
    """Reduziert die volle Preisstatistik (siehe _load_price_stats()) auf das
    {price_history_model: Marktpreis}-Mapping, das evaluate() erwartet
    (Schritt 7.4/7.5). None (kein Modell in der Historie) -> unveraendertes
    Verhalten wie vor Schritt 7.4 (reines regelbasiertes max_price-Signal).
    """
    return {
        model: stats.market_price
        for model, stats in stats_by_model.items()
        if stats is not None
    }


def _resale_prices_from_stats(
    stats_by_model: dict[str, PriceStats],
    stats_by_resale_group: dict[str, PriceStats] | None = None,
    model_to_group: dict[str, str] | None = None,
) -> dict[str, float | None]:
    """Reduziert die volle Preisstatistik auf das
    {price_history_model: geschaetzter Verkaufspreis}-Mapping (Reselling-/
    Arbitrage-Konzept, STATUS.md Abschnitt 16, Punkt c).

    Methodisch GETRENNT von _market_prices_from_stats(): market_price ist
    ein Ankaufs-Proxy (Basis: alle vom Bot selbst gematchten, tendenziell
    guenstigen Angebote), estimated_resale_price nutzt bewusst nur das
    obere Preissegment (P75-P90) derselben Daten -- siehe
    price_stats.py::_estimated_resale_price()-Docstring fuer die
    Begruendung.

    Option 2 ("Flip-Kandidaten-Logik optimieren", STATUS.md Abschnitt 33b):
    stats_by_resale_group/model_to_group sind optional (Default None ->
    identisches Verhalten zu vorher, volle Rueckwaertskompatibilitaet fuer
    aeltere Aufrufer/Tests). Sind beide gesetzt, wird estimated_resale_price
    NICHT mehr aus stats_by_model[model] gelesen, sondern aus der
    (potenziell groeberen) Gruppe stats_by_resale_group[model_to_group[model]]
    -- nur fuer Kategorien mit eigenem "resale_price_group" je Regel macht
    das ueberhaupt einen Unterschied (Default-Gruppe == Modell selbst).
    market_price/deal_score/Notification-Gate bleiben davon unberuehrt,
    die nutzen weiterhin ausschliesslich stats_by_model.

    Fehlt ein Modell komplett in der Historie (stats is None, noch kein
    einziger Datenpunkt gesammelt), wird das Modell hier weggelassen --
    evaluate() faellt dann weiterhin auf market_price zurueck (siehe
    dortiger Docstring), unveraendertes Verhalten.

    "Flip-Kandidaten-Logik optimieren", Schritt B (Option 1, STATUS.md
    Abschnitt 33b): liegt fuer ein Modell zwar eine PriceStats-Instanz vor,
    aber estimated_resale_price ist None (zu duenne Preishistorie, siehe
    price_stats.py::_estimated_resale_price()), wird das Modell hier
    BEWUSST MIT dem Wert None ins Mapping aufgenommen, statt komplett
    weggelassen zu werden. Der Unterschied ist entscheidend: ein fehlender
    Modell-Key bedeutet fuer matcher.py "Modell unbekannt -> Fallback auf
    market_price", waehrend ein vorhandener Key mit Wert None bedeutet
    "Modell bekannt, aber Verkaufspreis-Schaetzung aktuell nicht
    belastbar genug -> keine Marge/kein Flip-Kandidat berechnen" (matcher.py
    faellt in diesem Fall NICHT auf market_price zurueck). Ohne diese
    Unterscheidung wuerde ein einfaches Weglassen die alte, zu optimistische
    max_price-Naeherung ueber den market_price-Fallback wieder einschleusen.
    """
    if not stats_by_resale_group or not model_to_group:
        return {
            model: stats.estimated_resale_price
            for model, stats in stats_by_model.items()
            if stats is not None
        }

    result: dict[str, float | None] = {}
    for model, stats in stats_by_model.items():
        if stats is None:
            continue
        group = model_to_group.get(model, model)
        group_stats = stats_by_resale_group.get(group)
        result[model] = (
            group_stats.estimated_resale_price if group_stats is not None else None
        )
    return result
