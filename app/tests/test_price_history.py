"""Tests fuer price_history.py (Phase 7, Schritt 7.1)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_history import PricePoint, append_price_point, make_price_point, read_price_points


def test_make_price_point_setzt_alle_felder():
    point = make_price_point(price=199.0, source="kleinanzeigen", model="rtx_3060_12gb",
                              category="gpu", deal_score=87)
    assert point.price == 199.0
    assert point.source == "kleinanzeigen"
    assert point.model == "rtx_3060_12gb"
    assert point.category == "gpu"
    assert point.deal_score == 87
    assert point.date  # ISO-Zeitstempel wurde gesetzt (nicht leer)


def test_make_price_point_optionale_felder_haben_defaults():
    point = make_price_point(price=100.0, source="ebay", model="office_pc")
    assert point.category is None
    assert point.deal_score is None


def test_append_price_point_schreibt_jsonl_zeile(tmp_path):
    path = tmp_path / "price_history.jsonl"
    point = make_price_point(price=150.0, source="kleinanzeigen", model="office_pc", category="office_pc")

    append_price_point(path, point)

    assert path.exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["price"] == 150.0
    assert data["model"] == "office_pc"


def test_append_price_point_ist_append_only(tmp_path):
    path = tmp_path / "price_history.jsonl"
    append_price_point(path, make_price_point(price=100.0, source="ebay", model="rx_6700_xt"))
    append_price_point(path, make_price_point(price=110.0, source="kleinanzeigen", model="rx_6700_xt"))

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["price"] == 100.0
    assert json.loads(lines[1])["price"] == 110.0


def test_append_price_point_legt_elternverzeichnis_an(tmp_path):
    path = tmp_path / "nested" / "dir" / "price_history.jsonl"
    append_price_point(path, make_price_point(price=50.0, source="ebay", model="rx_7600"))
    assert path.exists()


def test_read_price_points_leere_liste_wenn_datei_fehlt(tmp_path):
    path = tmp_path / "does_not_exist.jsonl"
    assert read_price_points(path) == []


def test_read_price_points_liefert_geschriebene_punkte_zurueck(tmp_path):
    path = tmp_path / "price_history.jsonl"
    p1 = make_price_point(price=199.0, source="kleinanzeigen", model="rtx_3060_12gb", category="gpu", deal_score=90)
    p2 = make_price_point(price=210.0, source="ebay", model="rtx_3060_12gb", category="gpu", deal_score=70)
    append_price_point(path, p1)
    append_price_point(path, p2)

    points = read_price_points(path)

    assert len(points) == 2
    assert all(isinstance(p, PricePoint) for p in points)
    assert points[0].price == 199.0
    assert points[1].price == 210.0


def test_read_price_points_ueberspringt_kaputte_zeilen(tmp_path):
    path = tmp_path / "price_history.jsonl"
    good = make_price_point(price=100.0, source="ebay", model="rx_7600")
    append_price_point(path, good)
    with path.open("a", encoding="utf-8") as f:
        f.write("{kaputtes json\n")
        f.write("\n")  # leere Zeile soll ebenfalls ignoriert werden

    points = read_price_points(path)

    assert len(points) == 1
    assert points[0].price == 100.0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
