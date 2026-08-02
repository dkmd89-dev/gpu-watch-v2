"""Tests fuer duplicate_detection.py (STATUS.md Abschnitt 16, Baustein 5)."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from duplicate_detection import find_duplicate, normalize_title
from price_history import make_price_point


# --- normalize_title() ---

def test_normalize_title_lowercase():
    assert normalize_title("RTX 3060 12GB") == "rtx 3060 12gb"


def test_normalize_title_entfernt_sonderzeichen():
    assert normalize_title("RTX 3060 12GB!! (defekt)") == "rtx 3060 12gb defekt"


def test_normalize_title_entfernt_fuellwoerter():
    assert normalize_title("Biete RTX 3060 12GB zu verkaufen") == "rtx 3060 12gb"


def test_normalize_title_vereinheitlicht_whitespace():
    assert normalize_title("RTX   3060    12GB") == "rtx 3060 12gb"


def test_normalize_title_zwei_aequivalente_titel_liefern_gleiches_ergebnis():
    a = normalize_title("Biete RTX 3060 12GB, sehr guter Zustand!")
    b = normalize_title("RTX 3060 12GB - TOP Zustand, VB")
    assert a == b


# --- find_duplicate() ---

def _point(price, model="rtx_3060_12gb", fingerprint="rtx 3060 12gb", days_ago=0.0, now=None):
    ref = now or datetime.now(timezone.utc)
    date = (ref - timedelta(days=days_ago)).isoformat()
    p = make_price_point(price=price, source="kleinanzeigen", model=model, fingerprint=fingerprint)
    # date von make_price_point() ueberschreiben (dort immer "jetzt")
    return p.__class__(**{**p.__dict__, "date": date})


def test_find_duplicate_erkennt_gleiches_model_titel_preis_im_fenster():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, days_ago=5, now=now)]

    result = find_duplicate(
        model="rtx_3060_12gb", price=205.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, now=now,
    )

    assert result is not None
    assert result.price == 200.0


def test_find_duplicate_none_bei_unterschiedlichem_model():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, model="rtx_3070", days_ago=5, now=now)]

    result = find_duplicate(
        model="rtx_3060_12gb", price=200.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, now=now,
    )

    assert result is None


def test_find_duplicate_none_bei_unterschiedlichem_fingerprint():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, fingerprint="rtx 3070", days_ago=5, now=now)]

    result = find_duplicate(
        model="rtx_3060_12gb", price=200.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, now=now,
    )

    assert result is None


def test_find_duplicate_none_wenn_preis_ausserhalb_toleranz():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, days_ago=5, now=now)]

    # 10% Abweichung > 5% Default-Toleranz
    result = find_duplicate(
        model="rtx_3060_12gb", price=220.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, now=now,
    )

    assert result is None


def test_find_duplicate_innerhalb_toleranzgrenze_wird_erkannt():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, days_ago=5, now=now)]

    # exakt 5% Abweichung -- Grenzfall soll noch als Duplikat gelten
    result = find_duplicate(
        model="rtx_3060_12gb", price=210.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, now=now,
    )

    assert result is not None


def test_find_duplicate_none_wenn_ausserhalb_zeitfenster():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, days_ago=31, now=now)]

    result = find_duplicate(
        model="rtx_3060_12gb", price=200.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, now=now,
    )

    assert result is None


def test_find_duplicate_none_wenn_fingerprint_fehlt():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, days_ago=5, now=now)]
    existing[0] = existing[0].__class__(**{**existing[0].__dict__, "fingerprint": None})

    result = find_duplicate(
        model="rtx_3060_12gb", price=200.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, now=now,
    )

    assert result is None


def test_find_duplicate_leere_liste_liefert_none():
    result = find_duplicate(
        model="rtx_3060_12gb", price=200.0, fingerprint="rtx 3060 12gb",
        existing_points=[],
    )
    assert result is None


def test_find_duplicate_respektiert_custom_toleranz_und_fenster():
    now = datetime.now(timezone.utc)
    existing = [_point(200.0, days_ago=5, now=now)]

    # 3% Abweichung, aber Toleranz auf 1% verschaerft -> kein Duplikat
    result = find_duplicate(
        model="rtx_3060_12gb", price=206.0, fingerprint="rtx 3060 12gb",
        existing_points=existing, price_tolerance_pct=1.0, now=now,
    )
    assert result is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
