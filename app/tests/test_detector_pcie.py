"""Tests für categories/detectors/pcie.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.pcie import detect_pcie_connectors


def test_8_pin_erkannt():
    assert detect_pcie_connectors("RTX 3070 benötigt 8-Pin PCIe Stecker") == ["8-Pin"]


def test_6_pin_erkannt():
    assert detect_pcie_connectors("GTX 1660 mit 6-Pin Anschluss") == ["6-Pin"]


def test_6plus2_pin_erkannt():
    assert detect_pcie_connectors("Netzteil mit 6+2-Pin PCIe Kabel") == ["6+2-Pin"]


def test_pin_ohne_bindestrich():
    assert detect_pcie_connectors("Netzteil 8 Pin PCIe") == ["8-Pin"]


def test_mehrere_stecker_dedupliziert_in_reihenfolge():
    r = detect_pcie_connectors("Netzteil mit 2x 8-Pin und 1x 6-Pin PCIe Kabel, weiteres 8-Pin Kabel")
    assert r == ["8-Pin", "6-Pin"]


def test_kein_treffer_ohne_stecker_erwaehnung():
    assert detect_pcie_connectors("Gaming PC RTX 3060 16GB RAM 512GB SSD") == []


def test_kein_treffer_leerer_text():
    assert detect_pcie_connectors("") == []


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
