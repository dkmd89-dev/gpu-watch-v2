"""Tests fuer categories/registry.py (Kategorie-Plugin-Registry, Phase 10).

Prueft nur die Discovery-Infrastruktur selbst -- KEINE Verhaltensaenderung
an matcher.py (siehe registry.py-Docstring, analog zu
tests/test_scraper_registry.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.registry import discover_categories, CategoryPlugin

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"


def test_discover_categories_findet_alle_bekannten_kategorien():
    plugins = discover_categories(RULES_DIR)
    assert {"gpu", "office_pc", "gaming_pc", "sata_ssd"} <= set(plugins.keys())


def test_discover_categories_liefert_category_plugin_instanzen():
    plugins = discover_categories(RULES_DIR)
    for plugin in plugins.values():
        assert isinstance(plugin, CategoryPlugin)


def test_discover_categories_ueberspringt_global_yaml():
    plugins = discover_categories(RULES_DIR)
    assert "_global" not in plugins


def test_discover_categories_name_feld_stimmt_mit_dict_key_ueberein():
    plugins = discover_categories(RULES_DIR)
    for key, plugin in plugins.items():
        assert plugin.name == key


def test_discover_categories_config_enthaelt_rohe_yaml_daten():
    plugins = discover_categories(RULES_DIR)
    office = plugins["office_pc"]
    assert office.config.get("label") == "Office-PC"
    assert "rules" in office.config


def test_discover_categories_leeres_verzeichnis_liefert_leeres_dict(tmp_path):
    assert discover_categories(tmp_path) == {}


def test_discover_categories_nicht_existierendes_verzeichnis_liefert_leeres_dict(tmp_path):
    assert discover_categories(tmp_path / "does_not_exist") == {}


def test_discover_categories_findet_neue_yaml_only_kategorie(tmp_path):
    # Beweist dieselbe Plugin-Eigenschaft wie
    # test_rules_category_plugin_contract.py, hier aus Sicht der Registry:
    # eine neue Kategorie-Datei wird ohne Codeaenderung erkannt.
    (tmp_path / "_global.yaml").write_text("defaults: {}\n", encoding="utf-8")
    (tmp_path / "brandneu.yaml").write_text(
        'category: "brandneu"\nlabel: "Brandneu"\nrules: []\n', encoding="utf-8"
    )
    plugins = discover_categories(tmp_path)
    assert set(plugins.keys()) == {"brandneu"}
    assert plugins["brandneu"].config["label"] == "Brandneu"
