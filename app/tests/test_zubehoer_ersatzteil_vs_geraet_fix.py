"""Regressionstests für die 4 Zubehör/Ersatzteil-vs-Gerät-Fixes aus der
251-Listing-Stichprobe (STATUS.md Datenqualität Nr. 14, 2026-08-14).

Vier unabhängige Lücken in vier Kategorien:
1. controller: Kompositum-Lücke ("Lötaufsatz" enthält "aufsatz" nicht als
   eigenes Wort, siehe matcher.py::_contains_term()-Wortgrenzen).
2. handhelds: fehlende bare Excludes "ssd"/"festplatte"/"headset"/
   "kopfhörer"/"in-ear" (kein Handheld-GERÄT wird selbst so beworben).
3. netzteil: fehlender Exclude "kabelset" (PSU-Zubehör, nicht das
   Netzteil selbst -- diese Regel matcht nur über den Watt-Detector).
4. konsolen_bundles: "joy-con" kontextbewusst (exclude_category_unless_
   also_contains) statt bare -- ein bare Exclude wurde in einer früheren
   Session wegen 9 verifizierten Kollisionen mit echten Konsole+Joy-Con-
   Bundles bewusst verworfen; die neue Marker-Liste ergänzt "konsole"
   (fehlte in der bestehenden &plattform_geraete_marker-Liste).

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


def test_loetaufsatz_matcht_nicht():
    r = evaluate(
        "Lötaufsatz / Lötspitze für Xbox Series X & PS5 Controller T900",
        16.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "controller")


def test_handhelds_ssd_und_headset_matchen_nicht():
    for title, price in [
        ("WD SN770 - Crucial P310 - SSD 2TB - 2230 - für Steam Deck etc.", 220.0),
        ("Fikwot M.2 2230 SSD PCIe Gen4 Interne SSD 1TB 2TB Festplatte For Steam Deck ASUS", 149.99),
        ("Sony PS Vita In-Ear Headset Original PCH-ZHS1 OVP | Neuwertig | Rarität Zubehör", 39.9),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "handhelds"), title


def test_netzteil_kabelset_matcht_nicht():
    r = evaluate(
        "Kabelset für be quiet! Dark Power Pro 10 850W Netzteil",
        20.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "netzteil")


def test_standalone_joy_con_sets_matchen_nicht():
    for title, price in [
        ("SW - Original Nintendo Switch Joy-Con 2er-Set Grau", 50.0),
        ("Nintendo Switch Joy-Con Controller Set lila & orange", 45.0),
        ("Original Nintendo Switch Joy-Con 2er Set Controller Neon-Lila/Neon-Orange Gut", 55.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "konsolen_bundles"), title


def test_konsole_mit_joy_con_matcht_weiterhin():
    # Kollisions-Sicherheitsnetz: echte Konsole+Joy-Con-Bundles duerfen
    # durch die neue kontextbewusste Exclude-Regel NICHT blockiert werden.
    for title, price in [
        ("Nintendo Switch Konsole mit Joy-Con - Neon-Rot/Neon-Blau/Grau", 99.0),
        ("Nintendo Switch Konsole 32GB Schwarz inkl. Dock Joy-Con Blau/Rot", 130.0),
        ("Nintendo Switch Konsole mit speziellen Joy-Cons + 64GB Karte", 140.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


def test_reale_true_positives_matchen_weiterhin():
    for title, price, expected_category in [
        ("Original Xbox Controller (Xbox series x)", 30.0, "controller"),
        ("ASUS ROG Ally Z1 Extreme 16GB / 512GB neuwertig", 300.0, "handhelds"),
        ("Corsair CX750M Computer ATX Netzteil 750W", 49.99, "netzteil"),
        ("Nintendo Switch Lite (Koralle)", 90.0, "konsolen_bundles"),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == expected_category, title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
