"""Tests fuer categories/detectors/registry.py (Detector-Plugin-Registry).

Prueft nur die Discovery-Infrastruktur selbst -- KEINE Verhaltensaenderung
an matcher.py (siehe registry.py-Docstring: matcher.py bleibt bei
statischen Imports, analog zu den bereits bestehenden Registry-Tests).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.registry import discover_detectors, DetectorPlugin
from categories.detectors.cpu import detect_cpu
from categories.detectors.ram import detect_ram_gb, detect_ram_type
from categories.detectors.storage import detect_ssd_gb, detect_hdd_gb, detect_nvme
from categories.detectors.case import detect_case_type
from categories.detectors.gpu import detect_dedicated_gpu
from categories.detectors.psu import detect_psu_mentioned, detect_psu_watt
from categories.detectors.pcie import detect_pcie_connectors
from categories.detectors.windows import detect_windows_version
from categories.detectors.manufacturer import detect_manufacturer


def test_discover_detectors_findet_alle_bekannten_detectors():
    plugins = discover_detectors()
    erwartet = {
        "cpu", "ram_gb", "ram_type", "ssd_gb", "hdd_gb", "nvme",
        "case_type", "dedicated_gpu", "psu_mentioned", "psu_watt",
        "pcie_connectors", "windows_version", "manufacturer",
    }
    assert erwartet <= set(plugins.keys())


def test_discover_detectors_liefert_detector_plugin_instanzen():
    plugins = discover_detectors()
    for plugin in plugins.values():
        assert isinstance(plugin, DetectorPlugin)


def test_discover_detectors_ueberspringt_registry_modul_selbst():
    plugins = discover_detectors()
    assert all(p.module != "registry" for p in plugins.values())


def test_discover_detectors_name_feld_stimmt_mit_dict_key_ueberein():
    plugins = discover_detectors()
    for key, plugin in plugins.items():
        assert plugin.name == key


def test_discover_detectors_fn_ist_identisch_zur_direkt_importierten_funktion():
    # Wie bei der Scraper-Registry: keine Kopie/Wrapper, sondern exakt
    # dieselbe Funktionsreferenz wie der bestehende direkte Import.
    plugins = discover_detectors()
    assert plugins["cpu"].fn is detect_cpu
    assert plugins["ram_gb"].fn is detect_ram_gb
    assert plugins["ram_type"].fn is detect_ram_type
    assert plugins["ssd_gb"].fn is detect_ssd_gb
    assert plugins["hdd_gb"].fn is detect_hdd_gb
    assert plugins["nvme"].fn is detect_nvme
    assert plugins["case_type"].fn is detect_case_type
    assert plugins["dedicated_gpu"].fn is detect_dedicated_gpu
    assert plugins["psu_mentioned"].fn is detect_psu_mentioned
    assert plugins["psu_watt"].fn is detect_psu_watt
    assert plugins["pcie_connectors"].fn is detect_pcie_connectors
    assert plugins["windows_version"].fn is detect_windows_version
    assert plugins["manufacturer"].fn is detect_manufacturer


def test_discover_detectors_module_mit_mehreren_detectors_liefert_alle():
    # storage.py exportiert drei Detect-Funktionen -- alle drei muessen
    # als eigene Registry-Eintraege auftauchen, nicht nur die erste.
    plugins = discover_detectors()
    storage_detectors = {k for k, p in plugins.items() if p.module == "storage"}
    assert storage_detectors == {"ssd_gb", "hdd_gb", "nvme"}


def test_discover_detectors_ignoriert_private_hilfsfunktionen():
    # z.B. storage._size_to_gb / cpu._intel_generation duerfen nicht als
    # Detector auftauchen, obwohl sie im selben Modul liegen.
    plugins = discover_detectors()
    assert "size_to_gb" not in plugins
    assert "intel_generation" not in plugins
    assert "amd_generation" not in plugins


def test_alle_gefundenen_detectors_sind_robust_gegen_leeren_text():
    # Generischer Kontrakt-Check: jeder Detector muss mit leerem Text
    # umgehen koennen, ohne eine Exception zu werfen (unabhaengig vom
    # konkreten Rueckgabewert -- None/False/[] sind alle gueltig).
    plugins = discover_detectors()
    for plugin in plugins.values():
        plugin.fn("")  # darf nicht werfen
