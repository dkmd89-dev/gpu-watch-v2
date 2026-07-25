"""Tests für _clean_location() im Kleinanzeigen-Scraper (Phase-0-Befund k:
location-Feld enthielt rohes Whitespace-/Newline-Rauschen aus dem HTML)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers.kleinanzeigen import _clean_location


def test_clean_location_entfernt_internen_zeilenumbruch():
    # Reales Beispiel aus dem Phase-0-Log: ein einzelner Textknoten mit
    # eingebettetem Zeilenumbruch zwischen Ort und Entfernungsangabe.
    roh = "94539 Grafling\n                    (349 km)"
    assert _clean_location(roh) == "94539 Grafling (349 km)"


def test_clean_location_kollabiert_mehrfach_whitespace():
    roh = "76477   Karlsruhe   \t\n  (12 km)"
    assert _clean_location(roh) == "76477 Karlsruhe (12 km)"


def test_clean_location_leerer_string_bleibt_leer():
    assert _clean_location("") == ""


def test_clean_location_bereits_sauberer_text_unveraendert():
    assert _clean_location("76477 Karlsruhe (0 km)") == "76477 Karlsruhe (0 km)"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
