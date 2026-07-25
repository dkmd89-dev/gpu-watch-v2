"""Tests für categories/detectors/gpu.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.gpu import detect_dedicated_gpu, GpuMatch


# ---------- NVIDIA: Erkennung + Vorzugsliste ----------

def test_rtx_3060_erkannt_und_preferred():
    r = detect_dedicated_gpu("ASUS RTX 3060 12GB TUF Gaming")
    assert r == GpuMatch(brand="NVIDIA", model="RTX 3060", is_preferred=True)


def test_gtx_1060_erkannt_und_preferred():
    r = detect_dedicated_gpu("GTX 1060 6GB Grafikkarte gebraucht")
    assert r == GpuMatch(brand="NVIDIA", model="GTX 1060", is_preferred=True)


def test_gtx_1070_preferred():
    r = detect_dedicated_gpu("Gaming PC GTX 1070 8GB 16GB RAM")
    assert r.is_preferred is True


def test_gtx_1660_preferred():
    r = detect_dedicated_gpu("Gaming PC GTX 1660 6GB")
    assert r == GpuMatch(brand="NVIDIA", model="GTX 1660", is_preferred=True)


def test_rtx_2060_und_2070_preferred():
    assert detect_dedicated_gpu("RTX 2060 Grafikkarte").is_preferred is True
    assert detect_dedicated_gpu("RTX 2070 Grafikkarte").is_preferred is True


def test_rtx_2080ti_nicht_preferred_da_nicht_auf_liste():
    r = detect_dedicated_gpu("ASUS RTX 2080Ti DUAL Lüfter")
    assert r.brand == "NVIDIA"
    assert r.model == "RTX 2080 TI"
    assert r.is_preferred is False


def test_gtx_1650_nicht_preferred():
    r = detect_dedicated_gpu("Gaming PC GTX 1650 4GB")
    assert r.is_preferred is False


def test_ohne_leerzeichen_zwischen_marke_und_nummer():
    r = detect_dedicated_gpu("Geforce RTX3060 12GB Ventus 3x")
    assert r == GpuMatch(brand="NVIDIA", model="RTX 3060", is_preferred=True)


def test_gtx_1660_super_variante():
    r = detect_dedicated_gpu("Gaming PC GTX 1660 SUPER 6GB")
    assert r.model == "GTX 1660 SUPER"
    # SUPER-Variante ist NICHT identisch mit der Basisversion auf der
    # Vorzugsliste -- bewusst kein automatisches "mindestens gleichwertig"
    assert r.is_preferred is False


# ---------- AMD: Erkennung + Vorzugsliste ----------

def test_rx_6700_xt_erkannt_und_preferred():
    r = detect_dedicated_gpu("MSI RX 6700 XT Gaming Trio 12GB")
    assert r == GpuMatch(brand="AMD", model="RX 6700 XT", is_preferred=True)


def test_rx_6700_ohne_xt_nicht_preferred():
    # Nur "RX 6700 XT" steht auf der Liste, die Nicht-XT-Variante nicht
    r = detect_dedicated_gpu("AMD Radeon RX 6700 12GB Grafikkarte")
    assert r == GpuMatch(brand="AMD", model="RX 6700", is_preferred=False)


def test_rx_6600_preferred():
    r = detect_dedicated_gpu("Gaming PC RX 6600 8GB")
    assert r.is_preferred is True


def test_rx_ohne_leerzeichen():
    r = detect_dedicated_gpu("AMD Radeon RX6800 16GB")
    assert r == GpuMatch(brand="AMD", model="RX 6800", is_preferred=False)


# ---------- Kritische Abgrenzung: integrierte Grafik (APU) ----------

def test_apu_radeon_vega_wird_nicht_als_dedizierte_gpu_erkannt():
    # Ryzen 5600G ist eine APU mit integrierter Vega-Grafik, KEINE
    # dedizierte Grafikkarte -- klassischer Office-PC-Kandidat.
    assert detect_dedicated_gpu("Office PC Ryzen 5 5600G mit Radeon Vega Grafik 16GB RAM") is None


def test_intel_uhd_graphics_wird_nicht_erkannt():
    assert detect_dedicated_gpu("Office PC i5-10400 Intel UHD Graphics 630 8GB RAM") is None


def test_intel_iris_xe_wird_nicht_erkannt():
    assert detect_dedicated_gpu("Laptop i5-1135G7 Intel Iris Xe Graphics 16GB RAM") is None


def test_reiner_office_pc_ohne_gpu_erwaehnung():
    assert detect_dedicated_gpu("Office PC i5-8500 16GB RAM 256GB SSD") is None


# ---------- Kein Treffer ----------

def test_kein_treffer_leerer_text():
    assert detect_dedicated_gpu("") is None


def test_mehrere_gpus_erstes_vorkommen_gewinnt():
    r = detect_dedicated_gpu("Tausche RTX 3060 gegen RX 6700 XT")
    assert r.brand == "NVIDIA"
    assert r.model == "RTX 3060"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
