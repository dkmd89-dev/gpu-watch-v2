"""Tests für categories/detectors/manufacturer.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.manufacturer import detect_manufacturer, ManufacturerMatch


# ---------- OEM-Marken ----------

def test_dell_erkannt():
    r = detect_manufacturer("Dell OptiPlex 7040 i5-6500 8GB RAM")
    assert r == ManufacturerMatch(name="Dell", category="oem")


def test_lenovo_erkannt():
    r = detect_manufacturer("Lenovo ThinkCentre M920 i5-8500 16GB")
    assert r == ManufacturerMatch(name="Lenovo", category="oem")


def test_hp_kurzform_erkannt():
    r = detect_manufacturer("HP EliteDesk 800 G4 i5-8500")
    assert r == ManufacturerMatch(name="HP", category="oem")


def test_hp_langform_erkannt():
    r = detect_manufacturer("Hewlett-Packard ProDesk 600 i5-8500")
    assert r == ManufacturerMatch(name="HP", category="oem")


def test_fujitsu_erkannt():
    r = detect_manufacturer("Fujitsu Esprimo P957 i5-6500")
    assert r == ManufacturerMatch(name="Fujitsu", category="oem")


def test_acer_erkannt():
    r = detect_manufacturer("Acer Aspire TC i5-8500 8GB")
    assert r == ManufacturerMatch(name="Acer", category="oem")


def test_asus_erkannt():
    r = detect_manufacturer("Asus ROG Gaming PC RTX 3060")
    assert r == ManufacturerMatch(name="Asus", category="oem")


def test_msi_erkannt():
    r = detect_manufacturer("MSI Gaming PC RTX 2060 Ryzen 5 3600")
    assert r == ManufacturerMatch(name="MSI", category="oem")


def test_medion_erkannt():
    r = detect_manufacturer("Medion Akoya PC i5-8500 8GB")
    assert r == ManufacturerMatch(name="Medion", category="oem")


def test_apple_erkannt():
    r = detect_manufacturer("Apple iMac 27 Zoll")
    assert r == ManufacturerMatch(name="Apple", category="oem")


def test_captiva_erkannt():
    r = detect_manufacturer("Captiva Gaming PC RTX 3060")
    assert r == ManufacturerMatch(name="Captiva", category="oem")


def test_schenker_erkannt():
    r = detect_manufacturer("Schenker Gaming PC RTX 3060")
    assert r == ManufacturerMatch(name="Schenker", category="oem")


def test_terra_erkannt():
    r = detect_manufacturer("Terra PC-Business i5-8500")
    assert r == ManufacturerMatch(name="Terra", category="oem")


# ---------- Eigenbau ----------

def test_eigenbau_erkannt():
    r = detect_manufacturer("Eigenbau Gaming PC RTX 3060 Ryzen 5 3600")
    assert r == ManufacturerMatch(name="Eigenbau", category="custom")


def test_selbstbau_erkannt():
    r = detect_manufacturer("Selbstbau PC i5-8500 16GB")
    assert r == ManufacturerMatch(name="Eigenbau", category="custom")


def test_selbst_zusammengestellt_erkannt():
    r = detect_manufacturer("Gaming PC, selbst zusammengestellt, RTX 3060")
    assert r == ManufacturerMatch(name="Eigenbau", category="custom")


def test_selbst_gebaut_erkannt():
    r = detect_manufacturer("PC selbst gebaut mit Ryzen 5 3600")
    assert r == ManufacturerMatch(name="Eigenbau", category="custom")


# ---------- Kein Treffer ----------

def test_keine_marke_kein_treffer():
    r = detect_manufacturer("Gaming PC Ryzen 5 3600 RTX 3060 16GB RAM")
    assert r is None


def test_reine_komponentenliste_kein_treffer():
    r = detect_manufacturer("i5-8500 16GB DDR4 512GB SSD Midi-Tower")
    assert r is None


def test_custom_pc_wird_nicht_als_eigenbau_gewertet():
    # "Custom" wird bewusst NICHT als Eigenbau-Signal gewertet, da es am
    # Gebrauchtmarkt auch für individuell konfigurierte OEM-Systeme steht
    # (siehe Docstring in manufacturer.py) -- ohne Marken-Erwähnung also
    # kein Treffer.
    r = detect_manufacturer("Custom Gaming PC RTX 3060")
    assert r is None


# ---------- Priorität OEM vor Eigenbau ----------

def test_marke_hat_vorrang_vor_eigenbau_hinweis():
    r = detect_manufacturer("Dell Gehäuse, Eigenbau-Innenleben, i5-8500")
    assert r == ManufacturerMatch(name="Dell", category="oem")
