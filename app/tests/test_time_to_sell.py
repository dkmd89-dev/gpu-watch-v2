"""Tests für time_to_sell.py (Baustein 6 -- Time-to-Sell-Schätzung,
STATUS.md Abschnitt 16, Schritt 2)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from time_to_sell import TimeToSellPoint, append_time_to_sell_point, make_time_to_sell_point


def test_make_time_to_sell_point_berechnet_tage_korrekt():
    point = make_time_to_sell_point(
        first_seen="2026-01-01T00:00:00+00:00",
        last_seen="2026-01-03T12:00:00+00:00",
        model="rtx_3060_12gb",
        category="gpu",
    )
    assert point is not None
    assert point.days == 2.5
    assert point.model == "rtx_3060_12gb"
    assert point.category == "gpu"
    assert point.detected_at  # ISO-Zeitstempel wurde gesetzt


def test_make_time_to_sell_point_none_bei_fehlendem_first_seen():
    point = make_time_to_sell_point(
        first_seen=None, last_seen="2026-01-03T00:00:00+00:00",
        model="rtx_3060_12gb", category="gpu",
    )
    assert point is None


def test_make_time_to_sell_point_none_bei_fehlendem_last_seen():
    point = make_time_to_sell_point(
        first_seen="2026-01-01T00:00:00+00:00", last_seen=None,
        model="rtx_3060_12gb", category="gpu",
    )
    assert point is None


def test_make_time_to_sell_point_none_bei_fehlendem_model():
    """Nie gematchte (nur rohe) Angebote haben kein price_history_model --
    gehoeren konzeptionell nicht zur Time-to-Sell-Statistik."""
    point = make_time_to_sell_point(
        first_seen="2026-01-01T00:00:00+00:00", last_seen="2026-01-02T00:00:00+00:00",
        model=None, category="gpu",
    )
    assert point is None


def test_make_time_to_sell_point_none_bei_nicht_parsbarem_zeitstempel():
    point = make_time_to_sell_point(
        first_seen="kaputt", last_seen="2026-01-02T00:00:00+00:00",
        model="rtx_3060_12gb", category="gpu",
    )
    assert point is None


def test_make_time_to_sell_point_none_bei_negativer_dauer():
    point = make_time_to_sell_point(
        first_seen="2026-01-05T00:00:00+00:00", last_seen="2026-01-01T00:00:00+00:00",
        model="rtx_3060_12gb", category="gpu",
    )
    assert point is None


def test_append_time_to_sell_point_schreibt_jsonl_zeile(tmp_path):
    path = tmp_path / "time_to_sell.jsonl"
    point = make_time_to_sell_point(
        first_seen="2026-01-01T00:00:00+00:00", last_seen="2026-01-04T00:00:00+00:00",
        model="office_pc", category="office_pc",
    )
    assert point is not None

    append_time_to_sell_point(path, point)

    assert path.exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["days"] == 3.0
    assert data["model"] == "office_pc"
    assert data["category"] == "office_pc"


def test_append_time_to_sell_point_haengt_mehrere_zeilen_an(tmp_path):
    path = tmp_path / "time_to_sell.jsonl"
    p1 = TimeToSellPoint(days=1.0, first_seen="a", last_seen="b", model="m1", category="gpu", detected_at="d1")
    p2 = TimeToSellPoint(days=2.0, first_seen="c", last_seen="d", model="m2", category="gpu", detected_at="d2")

    append_time_to_sell_point(path, p1)
    append_time_to_sell_point(path, p2)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_append_time_to_sell_point_wirft_bei_schreibfehler_nicht(tmp_path, monkeypatch):
    """Analog price_history.append_price_point(): ein Schreibfehler darf
    den Scan nicht abbrechen (Zusatzfunktion, kein kritischer Pfad)."""
    path = tmp_path / "nicht_beschreibbar" / "time_to_sell.jsonl"
    point = TimeToSellPoint(days=1.0, first_seen="a", last_seen="b", model="m1", category="gpu", detected_at="d1")

    def boom(*args, **kwargs):
        raise OSError("simulierter Schreibfehler")

    monkeypatch.setattr(Path, "mkdir", boom)

    append_time_to_sell_point(path, point)  # darf keine Exception werfen


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
