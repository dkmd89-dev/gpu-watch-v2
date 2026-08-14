"""Regressionstests für die office_pc-exclude_category-Erweiterung um
"dynabook", "satellite pro" und "latitude" (Ruleset-Qualitätssystem,
251-Listing-Stichprobe 2026-08-14).

Hintergrund: identisches Muster wie test_office_pc_notebook_cross_category_fix.py
(bare Markenbegriffe statt "laptop"/"notebook", weil reale Titel keines der
beiden Wörter enthalten) -- zwei weitere Notebook-Marken, die durchrutschten:
"Dynabook Satellite Pro" (Toshiba/Dynabook-Businessnotebook-Linie) und
"Dell Latitude" (Dell-Businessnotebook-Linie). Blast Radius gemessen: je 1
aktueller found.json-Treffer + 1 (Dynabook) bzw. 10 (Latitude, nach Abzug
der bereits über "notebook"/"laptop" erfassten) historische
price_history.jsonl-Punkte, alle zweifelsfrei echte Notebooks.

Läuft gegen die echten, produktiven rules/*.yaml."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


def test_dynabook_satellite_pro_matcht_nicht():
    r = evaluate(
        'Dynabook Satellite Pro Intel Core 15,6" i5-8250U 1.6Ghz 8GB RAM',
        115.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "office_pc")


def test_dell_latitude_varianten_matchen_nicht():
    for title, price in [
        ('Dell Latitude 7300 - i7-8665U - 16GB RAM - 500GB SSD - 13,3" FHD - Windows 11', 179.99),
        ("Dell Latitude 5500 i5-8365U 8GB RAM 250 GB SSD", 150.0),
        ("Latitude W11 3410 Intel i5-10310U 32GB RAM 250GB SSD", 160.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "office_pc"), title


def test_reale_desktop_true_positives_matchen_weiterhin():
    for title, price in [
        ("Dell Optiplex 7060 Tower PC Core i5-8500 3GHz 16GB DDR4 Ram 512GB NVMe", 179.0),
        ("Dell Precision 3450 I7 11700 16GB DDR4 Office PC", 300.0),
        ("PC Dell 7060 MT | I5-8500 | 8GB DDR4 | 256GB SSD M.2 | WIN11 pro", 289.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "office_pc", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
