"""Kontrakt-Test fuer Phase 10 ("Kategorien als Plugins").

Beweist die zentrale Architektur-Anforderung des Auftrags: eine NEUE
Hardware-Kategorie darf ausschliesslich durch eine neue YAML-Datei in
rules/ entstehen -- OHNE jede Aenderung an matcher.py, app.py oder
sonstigem Python-Code.

Vorgehen: eine minimale, voellig synthetische Kategorie ("_plugin_test",
existiert nirgends im echten rules/-Verzeichnis oder in Python-Code) wird
in ein tmp_path-Verzeichnis geschrieben -- zusammen mit einer minimalen
_global.yaml, damit load_rules() unabhaengig vom echten rules/-Verzeichnis
getestet wird. Erkennt load_rules() diese Kategorie vollstaendig (Regeln,
Suchbegriffe, Label, Scan-Reihenfolge), ist der Plugin-Kontrakt erfuellt.

Reine Testergaenzung -- keine Aenderung an Produktivcode.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate

MINIMAL_GLOBAL_YAML = """
defaults:
  min_vram_gb: 12
exclude_global:
  - defekt
notifications:
  gate_min_stars: "★★★☆☆"
  gate_max_price: 150
scoring_weights:
  price: 0.7
  ausstattung: 0.15
  hardware_qualitaet: 0.15
  hersteller: 0
  zustand: 0
  lieferumfang: 0
"""

NEW_CATEGORY_YAML = """
category: "_plugin_test"
label: "Plugin-Test-Kategorie"
scan_priority: 1
notify_max_price: 42
search_terms:
  - "Plugin Test Gadget"
rules:
  - label: "Plugin-Test-Treffer"
    match:
      - "plugin test gadget"
    max_price: 100
    deal_rating: "gut"
    price_history_model: "plugin_test_gadget"
"""


def _write_minimal_rules_dir(tmp_path: Path) -> Path:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "_global.yaml").write_text(MINIMAL_GLOBAL_YAML, encoding="utf-8")
    (rules_dir / "_plugin_test.yaml").write_text(NEW_CATEGORY_YAML, encoding="utf-8")
    return rules_dir


def test_neue_kategorie_wird_allein_durch_yaml_datei_erkannt(tmp_path):
    rules_dir = _write_minimal_rules_dir(tmp_path)
    cfg = load_rules(str(rules_dir))
    assert "_plugin_test" in cfg["categories"]


def test_neue_kategorie_liefert_label_ohne_codeaenderung(tmp_path):
    rules_dir = _write_minimal_rules_dir(tmp_path)
    cfg = load_rules(str(rules_dir))
    assert cfg["category_labels"]["_plugin_test"] == "Plugin-Test-Kategorie"


def test_neue_kategorie_search_terms_werden_uebernommen(tmp_path):
    rules_dir = _write_minimal_rules_dir(tmp_path)
    cfg = load_rules(str(rules_dir))
    assert "Plugin Test Gadget" in cfg["search_terms"]


def test_neue_kategorie_scan_priority_wirkt_in_category_order(tmp_path):
    rules_dir = _write_minimal_rules_dir(tmp_path)
    cfg = load_rules(str(rules_dir))
    # scan_priority: 1 -> muss vor allen Kategorien ohne eigene Angabe stehen.
    assert cfg["category_order"][0] == "_plugin_test"


def test_neue_kategorie_treffer_wird_von_evaluate_ausgewertet(tmp_path):
    rules_dir = _write_minimal_rules_dir(tmp_path)
    cfg = load_rules(str(rules_dir))
    result = evaluate("Plugin Test Gadget", 80.0, cfg)
    assert result.matched is True
    assert result.category == "_plugin_test"
    assert result.rule_label == "Plugin-Test-Treffer"
    assert result.notify_max_price == 42


def test_neue_kategorie_ohne_treffer_ausserhalb_max_price(tmp_path):
    rules_dir = _write_minimal_rules_dir(tmp_path)
    cfg = load_rules(str(rules_dir))
    result = evaluate("Plugin Test Gadget", 150.0, cfg)
    assert result.matched is False
