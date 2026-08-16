"""Regressionstests für den Latitude-Recall-Gap-Fix, Variante B
(2026-08-16, siehe
tools/ruleset_quality/generated/reports/latitude_recall_gap_simulation.{json,md}).

3 TRUE_POSITIVE-Recall-Gaps (Dell Latitude 5501/5500/7400) blieben trotz
bestehender "Dell Latitude"-Regel in notebook_resell.yaml unmatched, weil
ihre Titel kein "laptop"/"notebook"-Wort enthalten. Fix: die Geräte-Gruppe
wurde um die 5 im gesamten Ground-Truth-Korpus (2306 Einträge) tatsächlich
beobachteten Latitude-Modellcodes ("5300","5401","5500","5501","7400") als
zusätzliche OR-Alternativen ergänzt -- eine geschlossene, korpusbelegte
Liste (Variante B), keine generische Zahlen-/Regex-Erkennung (Varianten A/C
wurden im Simulationsbericht als NICHT sicher verworfen: beide matchten
mindestens einen von zwei synthetischen Zubehör-/Ladegerät-Adversarial-
Fällen fälschlich).

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


# ---------------------------------------------------------------
# Die 3 Ziel-Recall-Gaps matchen jetzt
# ---------------------------------------------------------------

def test_latitude_5501_matcht_jetzt():
    r = evaluate(
        "Dell Latitude 5501 15,6\" FHD | i5-9400H | 8GB RAM | 250GB SSD",
        229.0,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "notebook_resell"


def test_latitude_5500_matcht_jetzt():
    r = evaluate(
        "Dell Latitude 5500  i5-8365U 8GB Ram 250 GB SSD", 145.0, _rules_cfg()
    )
    assert r.matched is True and r.category == "notebook_resell"


def test_latitude_7400_matcht_jetzt():
    r = evaluate(
        "Dell Latitude 7400\xa014\" FHD i7-8665U\xa016GB\xa0DDR4\xa0512GB\xa0SSD "
        "Win11 Pro FP ohne Füße",
        169.90,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "notebook_resell"


# ---------------------------------------------------------------
# Adversarial-Faelle aus der Simulation duerfen weiterhin NICHT matchen
# ---------------------------------------------------------------

def test_adversarial_ladegeraet_mit_unrelated_zahl_matcht_nicht():
    r = evaluate(
        "Dell Latitude Netzteil 65W Ladegeraet 512GB externe SSD Festplatte "
        "Modell 5820 Ersatzteil",
        50.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


def test_adversarial_ladegeraet_mit_zahl_direkt_nach_latitude_matcht_nicht():
    r = evaluate(
        "Dell Latitude 5410 Netzteil Ladegeraet 65W Ersatzteil 512GB SSD extern",
        50.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


# ---------------------------------------------------------------
# Bereits vorher (mit Geraetewort) gematchte Faelle bleiben unveraendert
# ---------------------------------------------------------------

def test_bestehende_latitude_faelle_mit_geraetewort_bleiben_unveraendert():
    for title, price, expected_rule in [
        (
            "Notebook Dell Latiitude 5401 i5 9400H 16GB DDR4 256GB  SSD",
            150.0,
            "Dell Latitude ★ Resell-Top",
        ),
        (
            "Dell Latitude 5300 Notebook 13„ i5-8265U 8GB RAM 250GB SSD W11",
            250.0,
            "Dell Latitude",
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title
        assert r.rule_label == expected_rule, title


# ---------------------------------------------------------------
# Grenzfaelle: Modellcode allein reicht nicht ohne Marke bzw. ohne Groesse
# ---------------------------------------------------------------

def test_modellcode_ohne_groessenangabe_matcht_nicht():
    r = evaluate("Latitude 5501 Laptop-Ersatzteil", 50.0, _rules_cfg())
    assert not (r.matched and r.category == "notebook_resell")


def test_modellcode_ohne_marke_matcht_nicht():
    r = evaluate("Dell 5501 8GB RAM SSD", 100.0, _rules_cfg())
    assert not (r.matched and r.category == "notebook_resell")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
