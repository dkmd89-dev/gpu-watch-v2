"""Datenqualitätskontrolle (roadmap.md Phase 10): erkennt automatisch,
wenn die Datenbasis für eine sinnvolle Bewertung zu dünn oder veraltet ist.

WICHTIG (roadmap.md-Vorgabe): Dieses Modul ersetzt oder verändert KEINE
bestehende Logik -- es liest ausschließlich bereits vorhandene, an
anderer Stelle berechnete Daten (price_stats.PriceStats, price_history.
PricePoint) und leitet daraus Warnungen ab. Kein Einfluss auf deal_score,
Notification-Gate, Matching oder Preisstatistik selbst.

Schritt 10a deckte die zwei Warnsignale ab, die praktisch kostenlos aus
bereits vorhandenen Feldern ableitbar sind:
- "dünne Datenbasis" -- PriceStats.confidence (Phase 5) ist bereits
  GENAU dafür gebaut, keine neue Schwelle nötig.
- "veraltete Kategorie" -- jüngster PricePoint einer Kategorie liegt zu
  lange zurück. NICHT über found.json geprüft (siehe Analyse: found.json
  wird nach DEAL_MAX_AGE_DAYS automatisch bereinigt und wäre für "seit N
  Tagen keine Treffer" bei N nahe DEAL_MAX_AGE_DAYS unzuverlässig) --
  price_history.jsonl ist append-only und dafür die verlässliche Quelle.

Schritt 10b ergänzt "Kategorie: viel gescrapt, 0 Matches"
(check_zero_match_categories()) -- nutzt Zählwerte, die run_scan() beim
Aufbau der category_buckets ohnehin schon erzeugt (len(bucket) je
Kategorie), keine neue Zählung nötig.

BEWUSST NICHT umgesetzt: "Regel: 91% ausgeschlossen" (feingranulare
Ausschlussquote je einzelner YAML-Regel). Das würde eine Instrumentierung
INNERHALB von matcher.py::evaluate()s Kernschleife voraussetzen (welche
Regel wurde warum genau verworfen: exclude_terms, Requirements, Preis?)
-- ein deutlich invasiverer Eingriff in die zentrale Matching-Logik als
die übrigen Prüfungen hier, die alle nur bereits vorhandene End-Ergebnisse
auswerten. check_zero_match_categories() liefert dafür eine erreichbare
Annäherung: eine Kategorie mit auffällig wenigen/keinen Treffern trotz
vieler gescrapter Angebote ist in der Praxis meist GENAU die Kategorie,
deren Regel zu eng gefasst ist -- ohne matcher.py anzufassen.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from price_stats import PriceStats, CONFIDENCE_LOW

WARNING_THIN_PRICE_HISTORY = "thin_price_history"
WARNING_STALE_CATEGORY = "stale_category"
WARNING_ZERO_MATCH_CATEGORY = "zero_match_category"

# Platzhalter-Schwelle mangels echter Kalibrierungsdaten, analog zu
# anderen Platzhaltern im Projekt (z.B. price_stats.py::
# _MIN_SAMPLES_FOR_HIGH_CONFIDENCE). roadmap.md nennt "7 Tage keine
# Treffer" als Beispiel -- wörtlich übernommen, kein eigener neuer Wert.
DEFAULT_STALE_CATEGORY_DAYS = 7.0

# roadmap.md nennt "500 gescrapt" nur als ILLUSTRATIVES Beispiel, keine
# feste Vorgabe -- 50 als bewusst niedrigerer Platzhalter (kleine Scans
# sollen nicht staendig false positives erzeugen, aber auch nicht erst ab
# 500 reagieren). Kalibrierung folgt nach Datensammlung, analog zu
# anderen Platzhalter-Schwellen im Projekt.
DEFAULT_MIN_SCRAPED_FOR_ZERO_MATCH_WARNING = 50


@dataclass(frozen=True)
class DataQualityWarning:
    """Eine einzelne Datenqualitäts-Warnung."""

    kind: str  # WARNING_*-Konstante oben
    subject: str  # Modellname (thin_price_history) oder Kategorie (stale_category)
    message: str  # Fertig formulierte, deutschsprachige Meldung


def check_thin_price_history(
    stats_by_model: dict[str, PriceStats],
) -> list[DataQualityWarning]:
    """Meldet alle Modelle mit LOW confidence (siehe price_stats.py::
    _confidence(), aktuell < 5 Datenpunkte) -- keine neue Schwelle, reine
    Auswertung des bereits vorhandenen Felds.

    Ergebnis-Reihenfolge folgt der Iterationsreihenfolge von
    `stats_by_model` (bei Python-Dicts: Einfügereihenfolge) -- keine
    eigene Sortierung, um keine ungetestete Annahme über die gewünschte
    Priorisierung zu treffen.
    """
    warnings = []
    for model, stats in stats_by_model.items():
        if stats is None:
            continue
        if stats.confidence == CONFIDENCE_LOW:
            warnings.append(
                DataQualityWarning(
                    kind=WARNING_THIN_PRICE_HISTORY,
                    subject=model,
                    message=(
                        f"Preishistorie für '{model}' zu dünn für eine "
                        f"belastbare Einschätzung ({stats.count} "
                        f"Datenpunkt{'e' if stats.count != 1 else ''})."
                    ),
                )
            )
    return warnings


def check_stale_categories(
    points: list,
    max_age_days: float = DEFAULT_STALE_CATEGORY_DAYS,
    now: datetime | None = None,
) -> list[DataQualityWarning]:
    """Meldet Kategorien, deren jüngster Preishistorie-Datenpunkt älter
    als `max_age_days` ist -- mögliches Anzeichen für eine zu enge Regel,
    eine tote Suchquelle oder einen ausgetrockneten Markt.

    Punkte ohne Kategorie (category is None, Legacy-Einzeldatei-Modus)
    werden übersprungen -- ohne Kategorie-Zuordnung ist keine sinnvolle
    Gruppierung möglich, kein Fehlerfall.

    `now` optional für deterministische Tests (Default: aktuelle UTC-Zeit).
    """
    reference_now = now or datetime.now(timezone.utc)

    latest_by_category: dict[str, datetime] = {}
    for point in points:
        if point.category is None:
            continue
        try:
            point_date = datetime.fromisoformat(point.date)
        except ValueError:
            continue
        current_latest = latest_by_category.get(point.category)
        if current_latest is None or point_date > current_latest:
            latest_by_category[point.category] = point_date

    warnings = []
    for category, latest_date in latest_by_category.items():
        age_days = (reference_now - latest_date).total_seconds() / 86400
        if age_days > max_age_days:
            warnings.append(
                DataQualityWarning(
                    kind=WARNING_STALE_CATEGORY,
                    subject=category,
                    message=(
                        f"Kategorie '{category}' seit {age_days:.1f} Tagen "
                        f"ohne neuen Treffer (Schwelle: {max_age_days:.0f} Tage)."
                    ),
                )
            )
    return warnings


def check_zero_match_categories(
    category_match_counts: dict[str, int],
    total_scraped: int,
    min_scraped_for_warning: int = DEFAULT_MIN_SCRAPED_FOR_ZERO_MATCH_WARNING,
) -> list[DataQualityWarning]:
    """Meldet Kategorien mit 0 Treffern in einem Scan, der insgesamt
    mindestens `min_scraped_for_warning` Angebote gescrapt hat (roadmap.md-
    Beispiel: "500 Listings gescrapt, 0 Matches").

    `total_scraped` ist bewusst der GLOBALE Scrape-Umfang (len(raw) in
    run_scan()), nicht ein kategoriespezifischer Wert -- Scraping ist ein
    einziger gemeinsamer Vorgang fuer alle Kategorien (siehe Modul-
    Docstring), ein separater "pro Kategorie gescrapt"-Zaehler existiert
    nicht und würde eine künstliche Kategorie-Zuordnung schon vor dem
    Matching erfordern.

    Bei sehr kleinen Scans (total_scraped < min_scraped_for_warning) wird
    NICHTS gemeldet -- 0 Treffer bei z.B. 5 gescrapten Angeboten ist
    statistisch nicht aussagekräftig und würde nur Rauschen erzeugen.

    category_match_counts mit 0 Kategorien (leeres Dict) -> leere Liste,
    kein Fehlerfall (z.B. ein Scan ganz ohne konfigurierte Kategorien).
    """
    if total_scraped < min_scraped_for_warning:
        return []

    warnings = []
    for category, match_count in category_match_counts.items():
        if match_count == 0:
            warnings.append(
                DataQualityWarning(
                    kind=WARNING_ZERO_MATCH_CATEGORY,
                    subject=category,
                    message=(
                        f"Kategorie '{category}': {total_scraped} Angebote "
                        f"gescrapt, 0 Treffer -- Regel möglicherweise zu eng "
                        f"gefasst."
                    ),
                )
            )
    return warnings
