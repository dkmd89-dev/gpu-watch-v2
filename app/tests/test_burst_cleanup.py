"""Tests fuer burst_cleanup.py (Alt-Daten-Burst-Bereinigung, siehe
STATUS.md Ausblick "SATA-SSD-500GB-Burst-Cluster")."""
import json
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from burst_cleanup import apply_and_rewrite, find_burst_duplicates
from price_history import make_price_point, read_price_points


def _point_at(dt: datetime, price: float = 71.5, model: str = "sata_ssd_500gb",
              source: str = "eBay", fingerprint: str | None = None):
    p = make_price_point(price=price, source=source, model=model, fingerprint=fingerprint)
    # make_price_point() setzt date auf "jetzt" -- fuer die Tests brauchen
    # wir feste, kontrollierbare Zeitstempel, daher per _replace nachtraeglich.
    return p.__class__(**{**p.__dict__, "date": dt.isoformat()})


def test_dichter_burst_ohne_fingerprint_wird_auf_ersten_punkt_reduziert():
    base = datetime(2026, 8, 1, 23, 56, 35, tzinfo=timezone.utc)
    points = [_point_at(base + timedelta(milliseconds=250 * i)) for i in range(18)]

    result = find_burst_duplicates(points)

    assert len(result.kept) == 1
    assert result.kept[0].date == points[0].date
    assert result.removed_count == 17


def test_mehrere_getrennte_bursts_bleiben_getrennt_erhalten():
    base = datetime(2026, 8, 1, 23, 56, 35, tzinfo=timezone.utc)
    burst1 = [_point_at(base + timedelta(milliseconds=100 * i)) for i in range(5)]
    burst2_start = base + timedelta(minutes=12)
    burst2 = [_point_at(burst2_start + timedelta(milliseconds=100 * i)) for i in range(4)]

    result = find_burst_duplicates(burst1 + burst2)

    assert len(result.kept) == 2
    kept_dates = {p.date for p in result.kept}
    assert kept_dates == {burst1[0].date, burst2[0].date}
    assert result.removed_count == 7


def test_punkte_mit_fingerprint_werden_nicht_angefasst():
    base = datetime(2026, 8, 2, 23, 0, 0, tzinfo=timezone.utc)
    points = [
        _point_at(base + timedelta(milliseconds=10 * i), fingerprint="rtx 3060 12gb")
        for i in range(10)
    ]

    result = find_burst_duplicates(points)

    assert result.removed_count == 0
    assert len(result.kept) == 10


def test_verschiedene_preise_bilden_getrennte_gruppen():
    base = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    points = [
        _point_at(base, price=71.5),
        _point_at(base + timedelta(seconds=1), price=75.0),
    ]

    result = find_burst_duplicates(points)

    assert result.removed_count == 0
    assert len(result.kept) == 2


def test_weit_auseinanderliegende_punkte_gelten_nicht_als_burst():
    base = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
    points = [_point_at(base + timedelta(days=i)) for i in range(5)]

    result = find_burst_duplicates(points)

    assert result.removed_count == 0
    assert len(result.kept) == 5


def test_kaputtes_datum_wird_behalten_statt_geloescht():
    p = make_price_point(price=71.5, source="eBay", model="sata_ssd_500gb")
    broken = p.__class__(**{**p.__dict__, "date": "kein-datum"})

    result = find_burst_duplicates([broken])

    assert result.removed_count == 0
    assert broken in result.kept


def test_apply_and_rewrite_schreibt_datei_und_legt_backup_an(tmp_path):
    path = tmp_path / "price_history.jsonl"
    base = datetime(2026, 8, 1, 23, 56, 35, tzinfo=timezone.utc)
    original = [_point_at(base + timedelta(milliseconds=100 * i)) for i in range(5)]
    path.write_text(
        "\n".join(json.dumps(asdict(p), ensure_ascii=False) for p in original) + "\n",
        encoding="utf-8",
    )

    points = read_price_points(path)
    result = find_burst_duplicates(points)
    backup_path = apply_and_rewrite(path, result.kept)

    assert backup_path is not None
    assert backup_path.exists()
    new_points = read_price_points(path)
    assert len(new_points) == 1
    assert new_points[0].date == original[0].date
