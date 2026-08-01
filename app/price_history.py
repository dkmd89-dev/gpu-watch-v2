"""Preishistorie (Phase 7, Schritt 7.1): append-only JSONL-Log aller Treffer.

Schreibt bei JEDEM Match (unabhaengig vom Notification-Gate, siehe app.py)
einen Datenpunkt weg. Grundlage fuer spaetere Schritte:
- 7.2: On-demand Statistik (Min/Max/Durchschnitt/Median/Perzentile/Trend)
- 7.3: automatische Top-Deal-Erkennung (Preis vs. errechneter Marktpreis)
- 7.4: Ruecksppeisung des Marktpreises in scoring/deal_score.py::_price_score()

Bewusst nur Schreiben + Datenmodell in diesem Schritt -- KEINE Auswertung,
keine Statistik-Berechnung (folgt in 7.2). Ausschliesslich lokal gesammelte
Daten, keine externen Preis-APIs (siehe Auftrag).
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PricePoint:
    """Ein einzelner Preishistorie-Datenpunkt (eine Zeile in price_history.jsonl).

    model: stabiler Gruppierungs-Schluessel fuer Markt-Statistik -- kommt aus
        dem optionalen YAML-Feld "price_history_model" der gematchten Regel
        (siehe matcher.MatchResult.price_history_model), NICHT aus dem
        Angebotstitel. Mehrere Regeln (z.B. verschiedene Marken/Rating-Stufen
        derselben Grafikkarte) koennen so auf denselben Modell-Schluessel
        einzahlen, statt die Preishistorie ueber viele Einzelregeln zu
        fragmentieren.
    category: z.B. "gpu", "office_pc", "gaming_pc" (rule._category aus dem
        Verzeichnis-Modus). None im Legacy-Einzeldatei-Modus.
    """

    price: float
    date: str  # ISO-8601 UTC, z.B. "2026-07-25T12:34:56.789012+00:00"
    source: str  # z.B. "kleinanzeigen", "ebay"
    model: str
    category: str | None
    deal_score: int | None


def make_price_point(
    price: float,
    source: str,
    model: str,
    category: str | None = None,
    deal_score: int | None = None,
) -> PricePoint:
    """Baut einen PricePoint mit aktuellem UTC-Zeitstempel."""
    return PricePoint(
        price=price,
        date=datetime.now(timezone.utc).isoformat(),
        source=source,
        model=model,
        category=category,
        deal_score=deal_score,
    )


def append_price_point(path: Path, point: PricePoint) -> None:
    """Haengt einen Datenpunkt als JSON-Zeile an `path` an (append-only).

    Legt Datei/Elternverzeichnis bei Bedarf an. Ein Schreibfehler darf den
    Scan nicht abbrechen -- Preishistorie ist eine Zusatzfunktion, kein
    kritischer Pfad (analog zu send_ntfy() in notify.py: Fehler werden
    geloggt, nicht nach oben geworfen).
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(point), ensure_ascii=False) + "\n")
    except Exception:
        log.exception("Preishistorie konnte nicht geschrieben werden")


def read_price_points(path: Path) -> list[PricePoint]:
    """Liest alle Datenpunkte aus `path` (eine Zeile = ein PricePoint).

    Fehlende Datei -> leere Liste (noch kein Scan mit Treffern gelaufen).
    Einzelne kaputte Zeilen werden uebersprungen und geloggt statt den
    kompletten Lesevorgang abzubrechen (robuste Auswertung fuer 7.2/7.3).
    """
    if not path.exists():
        return []

    points: list[PricePoint] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                points.append(PricePoint(**data))
            except (json.JSONDecodeError, TypeError) as e:
                log.warning(
                    "Ueberspringe kaputte Preishistorie-Zeile %d in %s: %s",
                    line_no, path, e,
                )
    return points
