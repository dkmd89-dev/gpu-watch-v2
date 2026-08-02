"""Tests fuer scrapers/registry.py (Plugin-Registry, Schritt 1: Discovery).

Prueft nur die Discovery-Infrastruktur selbst -- KEINE Verhaltensaenderung
an app.py oder den bestehenden Scraper-Funktionen (siehe registry.py-Docstring).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scrapers.registry import discover_scrapers, ScraperPlugin
from scrapers import search_kleinanzeigen, search_ebay


def test_discover_scrapers_findet_kleinanzeigen_und_ebay():
    plugins = discover_scrapers()
    assert set(plugins.keys()) == {"kleinanzeigen", "ebay"}


def test_discover_scrapers_liefert_scraper_plugin_instanzen():
    plugins = discover_scrapers()
    for plugin in plugins.values():
        assert isinstance(plugin, ScraperPlugin)


def test_discover_scrapers_search_funktion_ist_identisch_zur_direkt_importierten():
    # Die Registry darf keine Kopie/Wrapper liefern, sondern muss exakt
    # dieselbe Funktion referenzieren wie der bestehende direkte Import --
    # sonst koennten Registry und direkter Import auseinanderlaufen.
    plugins = discover_scrapers()
    assert plugins["kleinanzeigen"].search is search_kleinanzeigen
    assert plugins["ebay"].search is search_ebay


def test_discover_scrapers_name_feld_stimmt_mit_dict_key_ueberein():
    plugins = discover_scrapers()
    for key, plugin in plugins.items():
        assert plugin.name == key


def test_discover_scrapers_ueberspringt_base_und_registry_modul():
    plugins = discover_scrapers()
    assert "base" not in plugins
    assert "registry" not in plugins
