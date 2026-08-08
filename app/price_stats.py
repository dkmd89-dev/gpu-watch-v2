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
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("Europe/Berlin"))

from burst_cleanup import DEFAULT_MAX_GAP_SECONDS, find_burst_duplicates
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

    market_price vs. estimated_resale_price (Reselling-/Arbitrage-Konzept,
    STATUS.md Abschnitt 16, Punkt c): beide sind Naeherungen desselben
    Preisniveaus, aber aus unterschiedlicher Perspektive berechnet -- siehe
    Docstring von _estimated_resale_price() fuer die methodische Begruendung.
    Kurzfassung: market_price ist ein ANKAUFS-Proxy (Basis: alle vom Bot
    selbst gematchten, d.h. tendenziell guenstigen Angebote), waehrend
    estimated_resale_price bewusst nur das TEURERE obere Preissegment
    derselben Datenpunkte nutzt und damit naeher an einem realistischen
    Wiederverkaufspreis liegt.
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
    # Neu (Reselling-/Arbitrage-Konzept, Punkt c). Defaults halten bestehende
    # PriceStats(...)-Konstruktionsstellen (z.B. Tests) rueckwaertskompatibel,
    # ohne dass sie diese beiden Felder kennen muessen.
    percentile_75: float = 0.0
    estimated_resale_price: float | None = None


def group_by_model(points: list[PricePoint]) -> dict[str, list[PricePoint]]:
    """Gruppiert Datenpunkte nach ihrem price_history_model-Schluessel."""
    groups: dict[str, list[PricePoint]] = {}
    for point in points:
        groups.setdefault(point.model, []).append(point)
    return groups


def group_by_resale_group(
    points: list[PricePoint], model_to_group: dict[str, str]
) -> dict[str, list[PricePoint]]:
    """Gruppiert Datenpunkte nach einer GROEBEREN Resale-Price-Gruppe statt
    nach dem exakten `price_history_model` (Option 2, "Flip-Kandidaten-Logik
    optimieren" / STATUS.md Abschnitt 33b).

    Methodisch bewusst GETRENNT von group_by_model()/compute_all_price_stats():
    jene bleiben unveraendert und liefern weiterhin market_price je EXAKTEM
    price_history_model (Deal-Score/Notification-Gate duerfen sich durch
    diese Aenderung nicht verhalten). Diese Funktion dient ausschliesslich
    als Vorstufe fuer eine groebere estimated_resale_price-Schaetzung bei
    Kategorien mit strukturell duenner Preishistorie je Modell (z.B. LEGO-
    Minifiguren, Retro-Konsolen).

    model_to_group: Mapping {price_history_model: resale_price_group}, aus
    rules_cfg["resale_price_groups"] (siehe matcher.py::_load_rules_from_dir()).
    Fehlt ein Modell im Mapping (kein `resale_price_group` in der jeweiligen
    YAML-Regel definiert), dient das Modell als eigene Gruppe (Identitaet) --
    unveraendertes Verhalten fuer alle Kategorien ohne eigene Gruppierung.
    """
    groups: dict[str, list[PricePoint]] = {}
    for point in points:
        group = model_to_group.get(point.model, point.model)
        groups.setdefault(group, []).append(point)
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


def _estimated_resale_price(
    sorted_prices: list[float], p75: float, p90: float
) -> float | None:
    """Verkaufspreis-Naeherung, methodisch GETRENNT von _market_price()
    (Reselling-/Arbitrage-Konzept, STATUS.md Abschnitt 16, Punkt c).

    Methodische Einschraenkung von market_price (siehe dortiger Docstring):
    price_history.jsonl enthaelt ausschliesslich Angebote, die der Bot
    SELBST als Treffer gematcht hat -- also Angebote, die bereits innerhalb
    der (bewusst eng kalibrierten) max_price-Grenzen einer Regel liegen.
    Der Datenpool ist dadurch strukturell nach unten verzerrt: teurere,
    aber durchaus marktuebliche Angebote oberhalb der max_price-Grenze
    tauchen in der Preishistorie gar nicht erst auf. market_price (Trimm-
    Mittelwert ueber P10-P90) uebernimmt diese Verzerrung 1:1 -- fuer die
    Frage "was zahle ich beim Einkauf" ist das gewuenscht, fuer die Frage
    "was bekomme ich beim Wiederverkauf" unterschaetzt es systematisch.

    estimated_resale_price nutzt deshalb bewusst nur das OBERE Preis-
    segment (P75-P90) derselben Datenpunkte -- die teuersten (aber noch
    nicht als Ausreisser behandelten) beobachteten Preise sind eine naeher
    an einem realistischen Verkaufspreis liegende Referenz als der von
    guenstigen Treffern dominierte Gesamt-Mittelwert.

    Bei zu wenigen Datenpunkten (< _MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE,
    derselbe Schwellwert wie bei market_price) sind Perzentile ohnehin kaum
    tragfaehig. Frueher (vor "Flip-Kandidaten-Logik optimieren", Schritt B)
    fiel estimated_resale_price hier auf max_price zurueck -- das erwies
    sich in der Praxis als strukturell zu optimistisch (max_price ist bei
    granularen Regel-Labels mit duenner Preishistorie, z.B. Lego-
    Minifiguren, iPhone, Retro-Konsolen, haeufig schon der einzige/hoechste
    beobachtete Einzelpreis und damit KEINE verlaessliche Verkaufsreferenz).
    Seit Schritt B liefert die Funktion in diesem Fall bewusst None statt
    eines Zahlenwerts: "keine belastbare Verkaufspreis-Schaetzung" statt
    einer unzuverlaessigen Naeherung. Aufrufer (siehe app.py::
    _resale_prices_from_stats(), matcher.py::evaluate()) behandeln dieses
    None NICHT als "Modell unbekannt" (das wuerde weiterhin auf
    market_price zurueckfallen und die alte Optimismus-Verzerrung ueber
    einen Umweg reproduzieren), sondern als "fuer dieses Modell aktuell
    keine Marge/kein Flip-Kandidat berechenbar" -- exakt Option 1 aus
    STATUS.md Abschnitt 33b.
    """
    if len(sorted_prices) < _MIN_SAMPLES_FOR_PERCENTILE_MARKET_PRICE:
        return None

    trimmed = [p for p in sorted_prices if p75 <= p <= p90]
    if not trimmed:
        return None  # sollte praktisch nie vorkommen, aber sicherer Fallback

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


def compute_price_stats(
    model: str,
    points: list[PricePoint],
    *,
    collapse_bursts: bool = True,
    burst_max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS,
) -> PriceStats | None:
    """Berechnet die vollstaendige Statistik fuer EIN price_history_model.

    Gibt None zurueck, wenn `points` leer ist (keine Datengrundlage) --
    absichtlich kein Platzhalter-Objekt mit Nullen, da das leicht mit einer
    echten 0€-Statistik verwechselt werden koennte.

    collapse_bursts (Default True): wendet burst_cleanup.find_burst_duplicates()
    auf `points` an, BEVOR die Statistik berechnet wird (siehe STATUS.md
    Ausblick "SATA-SSD-500GB-Burst-Cluster", burst_cleanup.py Schritt 1).
    Wirkt NUR auf diese Berechnung -- price_history.jsonl selbst bleibt
    unveraendert, das bleibt Aufgabe des expliziten burst_cleanup.py-Skripts
    fuer bereits bekannte Faelle. Hier geht es um kuenftige/noch unentdeckte
    Alt-Daten-Bursts in beliebigen Modellen: die Statistik neutralisiert sie
    automatisch bei JEDER Berechnung, ohne dass jemand manuell ein Skript
    ausfuehren muss. Abschaltbar (collapse_bursts=False) fuer Tests/Debugging,
    die bewusst die Rohdaten unveraendert sehen wollen.
    """
    if not points:
        return None

    if collapse_bursts:
        points = find_burst_duplicates(points, max_gap_seconds=burst_max_gap_seconds).kept
        if not points:
            return None

    prices = sorted(p.price for p in points)
    p5 = _percentile(prices, 5)
    p10 = _percentile(prices, 10)
    median = statistics.median(prices)
    p75 = _percentile(prices, 75)
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
        percentile_75=p75,
        estimated_resale_price=_estimated_resale_price(prices, p75, p90),
    )


def compute_all_price_stats(
    points: list[PricePoint],
    *,
    collapse_bursts: bool = True,
    burst_max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS,
) -> dict[str, PriceStats | None]:
    """Berechnet die Statistik fuer JEDES vorkommende price_history_model.

    Nimmt bereits eingelesene Datenpunkte entgegen (z.B. aus
    price_history.read_price_points()), statt selbst die Datei zu lesen --
    haelt dieses Modul unabhaengig von Dateipfaden und leicht testbar.

    collapse_bursts/burst_max_gap_seconds: siehe compute_price_stats(),
    wird 1:1 an jede Modell-Berechnung durchgereicht.
    """
    return {
        model: compute_price_stats(
            model, model_points,
            collapse_bursts=collapse_bursts,
            burst_max_gap_seconds=burst_max_gap_seconds,
        )
        for model, model_points in group_by_model(points).items()
    }


def compute_resale_stats_by_group(
    points: list[PricePoint],
    model_to_group: dict[str, str],
    *,
    collapse_bursts: bool = True,
    burst_max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS,
) -> dict[str, PriceStats | None]:
    """Wie compute_all_price_stats(), aber gruppiert nach der groeberen
    Resale-Price-Gruppe (group_by_resale_group()) statt nach dem exakten
    price_history_model. Nur zur Ableitung von estimated_resale_price
    gedacht (siehe app.py::_resale_prices_from_stats()) -- das
    zurueckgegebene market_price je Gruppe ist hier ein Nebenprodukt der
    wiederverwendeten compute_price_stats()-Berechnung und wird bewusst
    NICHT fuer Deal-Score/Notification-Gate verwendet (die nutzen weiterhin
    compute_all_price_stats()/group_by_model() unveraendert).
    """
    return {
        group: compute_price_stats(
            group, group_points,
            collapse_bursts=collapse_bursts,
            burst_max_gap_seconds=burst_max_gap_seconds,
        )
        for group, group_points in group_by_resale_group(points, model_to_group).items()
    }
