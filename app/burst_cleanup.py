"""Bereinigung von Alt-Daten-Bursts in price_history.jsonl (Cluster-Problem,
siehe STATUS.md Abschnitt 17.2 / Ausblick, Fund "SATA-SSD-500GB-Burst-Cluster").

Hintergrund: Vor Einfuehrung des `fingerprint`-Feldes (siehe PricePoint in
price_history.py, duplicate_detection.py) wurden Cross-Postings/Mehrfach-
Listings desselben Angebots beim Schreiben nicht erkannt. Dadurch koennen in
Alt-Daten (Punkte OHNE fingerprint) kurze, dichte Haeufungen exakt gleicher
(model, price, source)-Kombinationen auftreten, die die Marktpreis-Statistik
verzerren (Fund: sata_ssd_500gb @ 71,50 EUR, 33 Punkte in drei ~Sekunden-
bis Millisekunden-Bursts).

Bewusst getrennt von duplicate_detection.py: dieses Modul arbeitet NICHT auf
Basis von Titel-Fingerprints (die es fuer Alt-Daten nicht gibt, da der
Originaltitel in PricePoint nicht persistiert wird -- Datenmodell-Grenze),
sondern rein zeitbasiert. Eine Kette von Punkten mit identischem
model/price/source, bei der aufeinanderfolgende Punkte nie mehr als
`max_gap_seconds` auseinanderliegen, gilt als EIN Scan-Ereignis (typisch:
derselbe Suchlauf traf denselben Listing-Titel ueber mehrere Suchbegriffe
oder eine kurze Serie von API-Calls). Nur der AELTESTE Punkt jeder Kette
bleibt erhalten.

Nur Punkte OHNE fingerprint sind Kandidaten. Punkte MIT fingerprint sind
bereits zur Schreibzeit durch duplicate_detection.find_duplicate() vor
genau diesem Muster geschuetzt und werden hier unveraendert durchgereicht
(keine doppelte Logik, kein Risiko fuer aktuelle/zukuenftige Daten).
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from price_history import PricePoint, read_price_points

log = logging.getLogger(__name__)

# Maximale Luecke zwischen zwei aufeinanderfolgenden Punkten derselben
# (model, price, source)-Gruppe, damit sie noch als EIN Scan-Ereignis
# gelten. 60s deckt sowohl Millisekunden-Bursts innerhalb eines einzelnen
# Suchlaufs als auch kurze Verzoegerungen zwischen einzelnen API-Calls ab,
# trennt aber sauber von eigenstaendigen, spaeteren Scan-Laeufen (der
# konfigurierte Scan-Intervall liegt im Minutenbereich).
DEFAULT_MAX_GAP_SECONDS = 60.0


@dataclass(frozen=True)
class BurstCleanupResult:
    """Ergebnis einer Bereinigung: welche Punkte behalten/entfernt wuerden."""

    kept: list[PricePoint]
    removed: list[PricePoint]

    @property
    def removed_count(self) -> int:
        return len(self.removed)


def find_burst_duplicates(
    points: list[PricePoint],
    max_gap_seconds: float = DEFAULT_MAX_GAP_SECONDS,
) -> BurstCleanupResult:
    """Erkennt zeitbasierte Alt-Daten-Bursts (siehe Modul-Docstring).

    Reine Funktion (keine Datei-I/O) -- gut testbar, `apply_and_rewrite()`
    unten uebernimmt das eigentliche Schreiben.
    """
    protected = [p for p in points if p.fingerprint is not None]
    candidates = [p for p in points if p.fingerprint is None]

    groups: dict[tuple[str, float, str], list[PricePoint]] = {}
    for p in candidates:
        groups.setdefault((p.model, p.price, p.source), []).append(p)

    kept: list[PricePoint] = list(protected)
    removed: list[PricePoint] = []

    for group_points in groups.values():
        parsed: list[tuple[datetime, PricePoint]] = []
        for p in group_points:
            try:
                parsed.append((datetime.fromisoformat(p.date), p))
            except ValueError:
                # Kaputtes Datum: nicht anfassen, lieber behalten als
                # faelschlich loeschen (robustes Verhalten, analog
                # price_stats.py/duplicate_detection.py).
                kept.append(p)
        parsed.sort(key=lambda t: t[0])

        chain_start_idx = 0
        for i in range(1, len(parsed)):
            gap = (parsed[i][0] - parsed[i - 1][0]).total_seconds()
            if gap > max_gap_seconds:
                kept.append(parsed[chain_start_idx][1])
                removed.extend(p for _, p in parsed[chain_start_idx + 1:i])
                chain_start_idx = i
        if parsed:
            kept.append(parsed[chain_start_idx][1])
            removed.extend(p for _, p in parsed[chain_start_idx + 1:])

    return BurstCleanupResult(kept=kept, removed=removed)


def apply_and_rewrite(path: Path, kept: list[PricePoint], *, backup: bool = True) -> Path | None:
    """Schreibt `kept` als neue price_history.jsonl (sortiert nach date).

    Legt vorher ein Backup an (Standard: an), damit die Bereinigung
    jederzeit rueckgaengig gemacht werden kann. Gibt den Backup-Pfad
    zurueck (oder None, wenn backup=False).
    """
    backup_path = None
    if backup and path.exists():
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup_path = path.with_name(path.name + f".bak-{timestamp}")
        shutil.copy2(path, backup_path)

    ordered = sorted(kept, key=lambda p: p.date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for p in ordered:
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
    return backup_path


def _print_report(points: list[PricePoint], result: BurstCleanupResult) -> None:
    print(f"Gelesen: {len(points)} Punkte")
    print(f"Erkannt als Alt-Daten-Burst-Duplikate: {result.removed_count} Punkte")
    by_group: dict[tuple[str, float, str], int] = {}
    for p in result.removed:
        key = (p.model, p.price, p.source)
        by_group[key] = by_group.get(key, 0) + 1
    for (model, price, source), count in sorted(by_group.items(), key=lambda kv: -kv[1]):
        print(f"  {model} @ {price} EUR ({source}): {count} entfernt")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", default="data/price_history.jsonl",
        help="Pfad zu price_history.jsonl (Default: data/price_history.jsonl)",
    )
    parser.add_argument(
        "--max-gap-seconds", type=float, default=DEFAULT_MAX_GAP_SECONDS,
        help=f"Max. Luecke innerhalb eines Bursts in Sekunden (Default: {DEFAULT_MAX_GAP_SECONDS})",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Aenderungen tatsaechlich schreiben (ohne diesen Schalter: nur Dry-Run/Report).",
    )
    args = parser.parse_args()

    path = Path(args.file)
    points = read_price_points(path)
    result = find_burst_duplicates(points, max_gap_seconds=args.max_gap_seconds)
    _print_report(points, result)

    if not args.apply:
        print("\nDry-Run -- keine Datei veraendert. Mit --apply tatsaechlich schreiben.")
        return

    backup_path = apply_and_rewrite(path, result.kept)
    print(f"\nGeschrieben: {len(result.kept)} Punkte nach {path}")
    print(f"Backup: {backup_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
