"""Tests für categories/detectors/ram.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.ram import detect_ram_gb, detect_ram_type


# ---------- detect_ram_gb ----------

def test_ram_gb_direkt_nach_gb():
    assert detect_ram_gb("Gaming PC Ryzen 5 5600 16GB RAM 512GB SSD RTX 3060") == 16


def test_ram_gb_ddr_direkt_nach_gb():
    assert detect_ram_gb("Ryzen 5 5600 16GB DDR4 RAM 512GB SSD RTX 3060") == 16


def test_ram_gb_ram_vor_zahl():
    assert detect_ram_gb("Office PC Intel i5 RAM 8GB SSD 256GB") == 8


def test_ram_gb_arbeitsspeicher_deutsch():
    assert detect_ram_gb("PC mit 32GB Arbeitsspeicher und 1TB SSD") == 32


def test_ram_gb_arbeitsspeicher_vor_zahl():
    assert detect_ram_gb("PC Arbeitsspeicher: 16GB, SSD 512GB") == 16


def test_ram_gb_ssd_zuerst_dann_ram_nicht_verwechseln():
    # Kritischer Kollisionsfall: 512GB SSD steht VOR 16GB RAM.
    # Ohne strikte Adjazenz würde ein simpler "erste Zahl vor GB"-Regex
    # hier 512 statt 16 liefern.
    assert detect_ram_gb("Gaming PC 512GB SSD 16GB RAM Ryzen 5") == 16


def test_ram_gb_ram_zuerst_dann_ssd():
    assert detect_ram_gb("Gaming PC 16GB RAM 512GB SSD 1TB HDD") == 16


def test_ram_gb_mit_klammern():
    assert detect_ram_gb("Office PC (16GB RAM) i5-8500 gebraucht") == 16


def test_ram_gb_kein_ram_kontext_reine_gpu():
    # "12GB" bezieht sich hier auf VRAM einer Grafikkarte, nicht auf System-RAM
    assert detect_ram_gb("ASUS RTX 3060 12GB Grafikkarte TUF Gaming") is None


def test_ram_gb_vram_wird_nicht_als_ram_erkannt():
    # "vram" enthaelt zwar den Teilstring "ram", darf aber nicht matchen
    assert detect_ram_gb("RTX 3070 8GB VRAM GDDR6 Grafikkarte") is None


def test_ram_gb_nur_ssd_kein_ram_erwaehnt():
    assert detect_ram_gb("PC Komplettsystem 512GB SSD i5-8500") is None


def test_ram_gb_gddr_wird_nicht_als_ram_erkannt():
    assert detect_ram_gb("Gaming PC RTX 3070 8GB GDDR6 512GB SSD") is None


def test_ram_gb_kein_treffer_bei_leerem_text():
    assert detect_ram_gb("") is None


def test_ram_gb_kein_treffer_ohne_gb_angabe():
    assert detect_ram_gb("Ryzen 5 5600 RTX 3060 Gaming PC") is None


# ---------- detect_ram_type ----------

def test_ram_type_ddr4_mit_leerzeichen():
    assert detect_ram_type("16GB DDR4 RAM") == "DDR4"


def test_ram_type_ddr3():
    assert detect_ram_type("PC mit 8GB RAM (DDR3) und SSD") == "DDR3"


def test_ram_type_ddr5():
    assert detect_ram_type("Neuer Gaming PC 32GB DDR5 RAM") == "DDR5"


def test_ram_type_ddr_mit_leerzeichen_zwischen_ddr_und_zahl():
    assert detect_ram_type("16GB DDR 4 RAM 3200mhz") == "DDR4"


def test_ram_type_kein_treffer():
    assert detect_ram_type("Office PC 8GB RAM 256GB SSD") is None


def test_ram_type_gddr_wird_nicht_als_system_ddr_erkannt():
    # GDDR6 (Grafikkarten-Speicher) darf NICHT als System-RAM-Typ erkannt werden
    assert detect_ram_type("RTX 3070 8GB GDDR6 Grafikkarte") is None


def test_ram_type_kein_treffer_bei_leerem_text():
    assert detect_ram_type("") is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
