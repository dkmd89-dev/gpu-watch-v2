"""Tests für categories/detectors/windows.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.windows import detect_windows_version


def test_windows_11_ausgeschrieben():
    assert detect_windows_version("Office PC inkl. Windows 11 Lizenz") == "11"


def test_windows_10_ausgeschrieben():
    assert detect_windows_version("Gaming PC mit Windows 10 Pro") == "10"


def test_win_11_kurzform_mit_leerzeichen():
    assert detect_windows_version("Lenovo Gaming PC RTX 4060 i5 16GB RAM Win 11") == "11"


def test_win11_kurzform_ohne_leerzeichen():
    assert detect_windows_version("HP Pavilion Gaming PC RTX 3060 Ti i7-10700F 16GB RAM Win11") == "11"


def test_win10_ohne_leerzeichen():
    assert detect_windows_version("Office PC i5-8500 Win10 Pro aktiviert") == "10"


def test_windows_7_aeltere_version():
    assert detect_windows_version("Alter Büro PC mit Windows 7") == "7"


def test_kein_treffer_ohne_windows_erwaehnung():
    assert detect_windows_version("Gaming PC RTX 3060 16GB RAM 512GB SSD") is None


def test_kein_treffer_leerer_text():
    assert detect_windows_version("") is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
