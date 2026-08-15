"""Regressionstest für den konsolen_bundles-Fix: "spiele" (Plural) unter
exclude_category_unless_also_contains, plus "panzerglas"/"displayschutz"
(Nutzer-Meldung 2026-08-15, found.json-Vollanalyse).

Hintergrund: "ovp"/"bundle"/"set"/"mit spiele" sind in der require_all_of-
Gruppe 2 bewusst erhaltene Positivsignale, reichen aber zusammen mit
"spiele" für reine Spiele-Sammlungen ohne jedes Gerät aus. Bare "spiel"
(Singular) ist bereits unbedingt ausgeschlossen, greift aber wegen
Wortgrenzen nicht bei der Pluralform "Spiele". Systematischer
Blast-Radius-Check: von 120 Titeln mit "spiele" in dieser Kategorie haben
26 KEINEN Geräte-/Modell-Marker (alle reine Spiele-Angebote), die übrigen
~94 haben jeweils mindestens einen echten Marker -- 0 Kollisionen.

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


def test_reine_spiele_angebote_matchen_nicht():
    for title, price in [
        ("3 Nintendo Switch Spiele OVP auf Module", 19.0),
        ("Nintendo Switch Spiele Bundle", 25.0),
        ("Nintendo Switch Spiele Set Asterix NEU IN FOLIE NUR KOMPLETT", 50.0),
        ("Nintendo Switch Spiele - Bundle 8 Spiele", 50.0),
        ("Nintendo Switch Spiele Auswahl z.B. Zelda, Mario, Ring Fit Adventure u.v.m. OVP", 44.0),
        ("PS4 Spiele Bundle mit zwei Controllern", 40.0),
        ("PS3 & PS4 Spiele Bundle + 2 PS4 Controller", 29.0),
        ("FIFA & F1 Spiele Paket Bundle (7 Spiele)   PlayStation 3 & 4 (PS3/PS4) | GUT", 7.99),
        ("Nintendo Switch 1 auch 2 Spiele: Cat Quest 1 und 2 und 3 neu&ovp", 40.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "konsolen_bundles"), title


def test_displayschutz_zubehoer_matcht_nicht():
    r = evaluate("Panzerglas Displayschutz Nintendo Switch Lite", 5.0, _rules_cfg())
    assert not (r.matched and r.category == "konsolen_bundles")


def test_echte_konsole_spiele_bundles_matchen_weiterhin():
    for title, price in [
        ("Sony PlayStation 4 Slim 1TB - Uncharted Edition 5 Spiele", 95.0),
        ("PS4 Slim mit 2 Spiele", 100.0),
        ("Sony PlayStation 4 500Gb CUH-1216A Schwarz + 1 Controller + 5 Spiele", 110.0),
        ("Nintendo Switch Lite Gelb + 4 Spiele + Zubehör", 90.0),
        ("Sony PlayStation 4 pro inkl. 2 Spiele", 85.0),
        ("Nintendo Switch Konsole mit Pro Controller & 5 Spielen", 130.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
