"""Tests für _notification_priority() in app.py (roadmap.md Phase 8, Schritt 8b).

Direkte Unit-Tests gegen die reine Funktion -- kein voller run_scan()-
Durchlauf nötig, da die Funktion keine Seiteneffekte hat und alle
Eingaben (Preis, Sterne, Rabatt) frei kontrollierbar sind.
"""
import sys
import os
import importlib.util
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_app_module(data_dir: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location(
        "app_under_test_notification_priority", app_path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_bisheriges_verhalten_unveraendert_preis_unter_schwelle_ist_urgent():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        # Kein Zustand/Rabatt -> ausschliesslich der bisherige, preisbasierte
        # Fall greift (Regressionsschutz: Verhalten vor Schritt 8b).
        assert mod._notification_priority(100.0, 150.0, None, None) == "urgent"


def test_bisheriges_verhalten_unveraendert_preis_ueber_schwelle_ist_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        assert mod._notification_priority(200.0, 150.0, None, None) == "default"


def test_fuenf_sterne_und_grosser_rabatt_ueber_preisschwelle_ist_urgent():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        # Preis (200) liegt UEBER urgent_price_threshold (150) -- nur die
        # NEUE Bedingung (Sterne + Rabatt) kann hier "urgent" ausloesen.
        assert mod._notification_priority(200.0, 150.0, "★★★★★", 30.0) == "urgent"


def test_vier_sterne_und_grosser_rabatt_ueber_preisschwelle_ist_urgent():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        assert mod._notification_priority(200.0, 150.0, "★★★★☆", 30.0) == "urgent"


def test_drei_sterne_und_grosser_rabatt_bleibt_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        # Sterne-Bedingung nicht erfuellt (nur ★★★☆☆) -- trotz grossem
        # Rabatt bleibt es bei "default".
        assert mod._notification_priority(200.0, 150.0, "★★★☆☆", 30.0) == "default"


def test_fuenf_sterne_aber_kleiner_rabatt_bleibt_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        # Rabatt (10%) unter der Schwelle (25%) -- trotz ★★★★★ "default".
        assert mod._notification_priority(200.0, 150.0, "★★★★★", 10.0) == "default"


def test_fuenf_sterne_ohne_rabatt_wert_bleibt_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        # discount_pct is None (keine/zu wenig Preishistorie) -- kann die
        # neue Bedingung nie erfuellen, exakt wie vor Schritt 8b.
        assert mod._notification_priority(200.0, 150.0, "★★★★★", None) == "default"


def test_grenzwert_exakt_25_prozent_rabatt_ist_urgent():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        # TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT == 25.0, >= (nicht >) -- Grenzwert
        # selbst muss bereits ausreichen.
        assert mod._notification_priority(200.0, 150.0, "★★★★★", 25.0) == "urgent"


def test_grenzwert_knapp_unter_25_prozent_bleibt_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        assert mod._notification_priority(200.0, 150.0, "★★★★★", 24.9) == "default"


def test_beide_bedingungen_gleichzeitig_erfuellt_bleibt_urgent():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod = _load_app_module(tmpdir)
        # Preis UNTER der Schwelle UND Sterne/Rabatt erfuellt -- beide
        # Wege fuehren zu "urgent", keine widersprechen sich.
        assert mod._notification_priority(50.0, 150.0, "★★★★★", 30.0) == "urgent"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
