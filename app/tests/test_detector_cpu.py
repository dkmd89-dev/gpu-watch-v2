"""Tests für categories/detectors/cpu.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.cpu import detect_cpu, CpuMatch


# ---------- Intel: Modellnummer + Generation ----------

def test_intel_i5_8400_office_pc():
    r = detect_cpu("Office PC Intel Core i5-8400 16GB RAM 256GB SSD")
    assert r == CpuMatch(brand="Intel", tier="i5", model_number=8400, generation=8)


def test_intel_i7_10700f_gaming_pc():
    r = detect_cpu("Gaming PC i7-10700F RTX 3070 32GB RAM")
    assert r == CpuMatch(brand="Intel", tier="i7", model_number=10700, generation=10)


def test_intel_i9_9900k():
    r = detect_cpu("High-End PC Intel i9-9900K Wasserkühlung")
    assert r == CpuMatch(brand="Intel", tier="i9", model_number=9900, generation=9)


def test_intel_i5_13700_5stellig_generation_13():
    r = detect_cpu("Gaming PC i7-13700K RTX 4070")
    assert r.generation == 13


def test_intel_ohne_bindestrich_mit_leerzeichen():
    r = detect_cpu("Office PC i5 8500 gebraucht")
    assert r == CpuMatch(brand="Intel", tier="i5", model_number=8500, generation=8)


def test_intel_laptop_cpu_mit_buchstaben_suffix():
    r = detect_cpu("Laptop i5-8265U 8GB RAM")
    assert r == CpuMatch(brand="Intel", tier="i5", model_number=8265, generation=8)


def test_intel_i3_erkennung():
    r = detect_cpu("Büro PC Intel i3-8100 8GB RAM")
    assert r.tier == "i3"
    assert r.generation == 8


# ---------- AMD Ryzen: Modellnummer + Serie ----------

def test_amd_ryzen5_3600_gaming_pc():
    r = detect_cpu("Gaming PC AMD Ryzen 5 3600 RTX 3060 16GB RAM")
    assert r == CpuMatch(brand="AMD", tier="Ryzen 5", model_number=3600, generation=3000)


def test_amd_ryzen7_5800x_mit_suffix():
    r = detect_cpu("Gaming PC Ryzen 7 5800X 32GB RAM RTX 3070")
    assert r == CpuMatch(brand="AMD", tier="Ryzen 7", model_number=5800, generation=5000)


def test_amd_ryzen5_5600_office_test():
    r = detect_cpu("Office/Gaming PC Ryzen 5 5600 16GB DDR4")
    assert r == CpuMatch(brand="AMD", tier="Ryzen 5", model_number=5600, generation=5000)


def test_amd_ryzen9_laptop_hx_suffix():
    r = detect_cpu("Gaming Laptop Ryzen 9 5900HX RTX 3060")
    assert r == CpuMatch(brand="AMD", tier="Ryzen 9", model_number=5900, generation=5000)


def test_amd_ryzen5_2600_aeltere_generation():
    r = detect_cpu("Office PC Ryzen 5 2600 16GB RAM")
    assert r.generation == 2000


# ---------- Kein Treffer / Grenzfälle ----------

def test_kein_treffer_reine_gpu_anzeige():
    assert detect_cpu("ASUS RTX 3060 12GB TUF Gaming Grafikkarte") is None


def test_kein_treffer_marke_ohne_modellnummer():
    # Reine Serien-Erwähnung ohne Modellnummer -> bewusst kein Treffer
    assert detect_cpu("Gaming PC mit Ryzen 5 Prozessor, Marke egal") is None


def test_kein_treffer_leerer_text():
    assert detect_cpu("") is None


def test_kein_treffer_ohne_cpu_erwaehnung():
    assert detect_cpu("Gaming PC 16GB RAM 512GB SSD RTX 3060") is None


def test_intel_und_amd_im_gleichen_text_erstes_vorkommen_gewinnt():
    # Vergleichsanzeige/Textmüll mit beiden Marken -- das zuerst im Text
    # vorkommende CPU-Modell soll erkannt werden.
    r = detect_cpu("Tausche Ryzen 5 3600 PC gegen Intel i5-8400 PC")
    assert r.brand == "AMD"
    assert r.model_number == 3600


def test_gpu_modellnummer_wird_nicht_als_cpu_missverstanden():
    # "3070" alleine (GPU) darf nicht als CPU-Modellnummer durchgehen,
    # da kein "i3/i5/i7/i9"- oder "ryzen"-Präfix davorsteht.
    assert detect_cpu("RTX 3070 Grafikkarte 8GB GDDR6") is None


def test_bekannte_grenze_verkuerzte_amd_schreibweise_ohne_ryzen():
    # "7600X3D" ohne vorangestelltes "Ryzen" -- bewusst kein Treffer,
    # da sonst AMD-GPU-Bezeichnungen (RX 6750 etc.) faelschlich matchen
    # koennten.
    assert detect_cpu("High-End Gaming-PC 7600X3D RX 6800 16GB DDR5") is None


def test_bekannte_grenze_r_kurzform_ohne_ryzen():
    assert detect_cpu("PC R5600X u. RX6750XT TOP") is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
