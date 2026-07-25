"""Tests für categories/detectors/psu.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.psu import detect_psu_mentioned, detect_psu_watt


# ---------- detect_psu_mentioned ----------

def test_psu_mention_netzteil():
    assert detect_psu_mentioned("Gaming PC mit 650W Netzteil 80+ Gold") is True


def test_psu_mention_psu_englisch():
    assert detect_psu_mentioned("Gaming PC PSU 650W included") is True


def test_psu_mention_keine_erwaehnung():
    assert detect_psu_mentioned("Gaming PC RTX 3060 16GB RAM") is False


def test_psu_mention_leerer_text():
    assert detect_psu_mentioned("") is False


# ---------- detect_psu_watt ----------

def test_psu_watt_mit_netzteil_kontext():
    assert detect_psu_watt("Gaming PC mit 650W Netzteil 80+ Gold") == 650


def test_psu_watt_ohne_kontext_wort():
    # Kritischer Realfall (echter Titel aus dem Projekt): Watt-Angabe
    # ganz ohne "Netzteil"/"PSU" daneben, nur Positions-Konvention.
    assert detect_psu_watt("PC i7-14700K 32GB DDR5 500GB SSD RTX 3060 Ti 1000W") == 1000


def test_psu_watt_realer_slug_artiger_titel():
    assert detect_psu_watt("i7-14700k 32gb ddr5 500ssd rtx3060ti 1000w") == 1000


def test_psu_watt_kleinerer_plausibler_wert():
    assert detect_psu_watt("Office PC 300W Netzteil i5-8500") == 300


def test_psu_watt_grosser_plausibler_wert():
    assert detect_psu_watt("High-End PC 1200W Netzteil Platinum") == 1200


def test_psu_watt_ignoriert_unplausible_kleine_werte():
    # "20W" (z.B. USB-Ladeleistung) liegt ausserhalb des plausiblen
    # Netzteil-Bereichs und soll nicht als PSU-Leistung erkannt werden.
    assert detect_psu_watt("PC mit 20W USB-C Ladegerät beigelegt") is None


def test_psu_watt_findet_plausiblen_wert_trotz_unplausiblem_davor():
    assert detect_psu_watt("PC mit 20W USB-C Ladegerät, 650W Netzteil") == 650


def test_psu_watt_kein_treffer_ohne_watt_angabe():
    assert detect_psu_watt("Gaming PC RTX 3060 16GB RAM 512GB SSD") is None


def test_psu_watt_kein_treffer_leerer_text():
    assert detect_psu_watt("") is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
