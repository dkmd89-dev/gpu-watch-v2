"""Time-to-Sell-Datenpunkte (Reselling-/Arbitrage-Konzept, STATUS.md
Abschnitt 16, Baustein 6, Schritt 2): append-only JSONL-Log analog zu
price_history.py, aber für Verweildauern statt Preise.

Ein Datenpunkt entsteht genau dann, wenn presence_tracking.detect_newly_delisted()
ein zuvor gematchtes Angebot als "delisted" erkennt (siehe app.py). Grundlage
für Schritt 3 (Median/Mittelwert-Statistik je Kategorie als Liquiditäts-
Proxy) -- KEINE Auswertung in diesem Schritt.

Ausschließlich lokal gesammelte Daten (first_seen/last_seen aus seen.json),
keine externen APIs -- exakt dasselbe Prinzip wie price_history.py.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimeToSellPoint:
    """Ein einzelner Time-to-Sell-Datenpunkt (eine Zeile in time_to_sell.jsonl).

    days: Verweildauer in Tagen (last_seen - first_seen), kann Bruchteile
        enthalten (z.B. 2.5 Tage) -- Rundung erfolgt erst in der spaeteren
        Statistik-Auswertung (Schritt 3), nicht hier.
    model/category: siehe price_history.PricePoint -- gleiche Semantik
        (price_history_model bzw. result.category aus dem Match).
    detected_at: ISO-8601 UTC-Zeitstempel, WANN die Delisting-Erkennung
        stattfand (nicht zu verwechseln mit first_seen/last_seen).
    """

    days: float
    first_seen: str
    last_seen: str
    model: str | None
    category: str | None
    detected_at: str


def make_time_to_sell_point(
    first_seen: str | None,
    last_seen: str | None,
    model: str | None,
    category: str | None,
) -> TimeToSellPoint | None:
    """Baut einen TimeToSellPoint, oder None falls keine sinnvolle
    Berechnung möglich ist.

    Gibt bewusst None zurück (statt eines Platzhalter-/Nullwerts) wenn:
    - first_seen oder last_seen fehlt (None) -- migrierte Alt-Einträge aus
      presence_tracking.py Schritt 1 haben keine echte Historie; eine
      Time-to-Sell-Spanne von "0 Tagen" wäre hier schlicht erfunden.
    - model is None -- ein Angebot ohne price_history_model wurde nie
      erfolgreich gematcht (siehe presence_tracking.mark_matched()) und
      gehört konzeptionell nicht zur Time-to-Sell-Statistik ("zuvor
      GEMATCHTES Angebot", siehe STATUS.md Abschnitt 16).
    - die berechnete Dauer negativ wäre (Datenfehler/Uhrzeit-Anomalie) --
      defensiv, verhindert unsinnige Statistik-Ausreißer.
    """
    if first_seen is None or last_seen is None or model is None:
        return None

    try:
        first_dt = datetime.fromisoformat(first_seen)
        last_dt = datetime.fromisoformat(last_seen)
    except ValueError:
        log.warning(
            "Time-to-Sell: first_seen/last_seen nicht als ISO-8601 lesbar "
            "(first_seen=%r, last_seen=%r) -- übersprungen.",
            first_seen, last_seen,
        )
        return None

    days = (last_dt - first_dt).total_seconds() / 86400
    if days < 0:
        log.warning(
            "Time-to-Sell: negative Dauer berechnet (first_seen=%s, "
            "last_seen=%s) -- übersprungen.",
            first_seen, last_seen,
        )
        return None

    return TimeToSellPoint(
        days=days,
        first_seen=first_seen,
        last_seen=last_seen,
        model=model,
        category=category,
        detected_at=datetime.now(timezone.utc).isoformat(),
    )


def append_time_to_sell_point(path: Path, point: TimeToSellPoint) -> None:
    """Hängt einen Datenpunkt als JSON-Zeile an `path` an (append-only).

    Legt Datei/Elternverzeichnis bei Bedarf an. Ein Schreibfehler darf den
    Scan nicht abbrechen -- analog zu price_history.append_price_point()
    (Zusatzfunktion, kein kritischer Pfad).
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(point), ensure_ascii=False) + "\n")
    except Exception:
        log.exception("Time-to-Sell-Datenpunkt konnte nicht geschrieben werden")
