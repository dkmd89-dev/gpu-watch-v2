"""Regressionstests für die exclude_global-Erweiterung um die deklinierten
"defekt"-Formen ("defekte"/"defekter"/"defektes"/"defekten") in
app/rules/_global.yaml (Ruleset-Qualitätssystem, 251-Listing-Stichprobe
2026-08-14).

Hintergrund: matcher.py::_contains_term() prüft Excludes als GANZES WORT
(Regex-Wortgrenzen) -- der Wortstamm "defekt" erfasst daher keine
deklinierten Formen ("Defekte Asus ROG Ally", "PS2 Slim mit defekten
Laser"). Blast Radius gemessen: 4 aktuelle found.json- + 19 historische
price_history.jsonl-Treffer, alle eindeutig echte Defekt-Kontexte, keine
Negationsfälle ("ohne Defekte" o.ä.) im gesamten Korpus gefunden. "tausch"
bewusst NICHT um "tausche" erweitert -- Risiko harmloser
Wartungsformulierungen ("Akku tauschen").

Läuft gegen die echten, produktiven rules/*.yaml -- prüft mehrere
Kategorien, da exclude_global kategorieübergreifend wirkt."""
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


def test_defekt_flexionsformen_matchen_nicht_mehr():
    for title, price in [
        ("Defekte Asus ROG Ally Z1 Extreme 1TB", 200.0),
        ("PS2 Slim mit defekten Laser", 15.0),
        ("PlayStation 4 Slim 500GB - Defekte HDMI-Buchse", 50.0),
        ("Defekter Samsung Curved Monitor Ultrawide Odyssey G5 34\"", 60.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is False, title


def test_defekt_grundform_matcht_weiterhin_nicht():
    # Bestehendes Verhalten (Grundform-Exclude) darf nicht regressieren.
    r = evaluate("Nintendo Switch Pro Controller defekt", 15.0, _rules_cfg())
    assert r.matched is False


def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("ASUS ROG Ally Z1 Extreme 16GB / 512GB neuwertig", 300.0),
        ("Sony PlayStation 2 Konsole (PS2) mit Mod-Chip", 80.0),
        ("Samsung S27D364GAU 27 Zoll Curved Gaming Monitor Full HD", 80.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True, title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
