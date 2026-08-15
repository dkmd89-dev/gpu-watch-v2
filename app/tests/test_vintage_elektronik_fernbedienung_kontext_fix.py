"""Regressionstest für den vintage_elektronik-Fix: "fernbedienung" von
bare exclude_category auf exclude_category_unless_preceded_by umgestellt
(Ruleset-Qualitätssystem, Regression-Benchmark gegen historischen
Vor-Audit-Snapshot, 2026-08-15).

Hintergrund: bare "fernbedienung" (Kategorie- UND Regel-Ebene bei den
Röhrenfernseher-Regeln) blockierte auch echte Markenverstärker/-Receiver/
-Fernseher, die ihre mitgelieferte Fernbedienung als Ausstattungsmerkmal
nennen ("Pioneer Stereo Verstärker mit Fernbedienung"). Fix nutzt
denselben, bereits in controller.yaml/ladekabel etablierten Mechanismus:
"fernbedienung" bleibt für Standalone-Zubehörangebote ausgeschlossen,
matcht aber wieder, wenn ein Bundle-Konnektor ("mit"/"inkl."/"+"/"und"/
"sowie") unmittelbar davorsteht.

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


def test_markengeraet_mit_fernbedienung_matcht_wieder():
    for title, price in [
        ("Pioneer Stereo Verstärker mit Fernbedienung", 50.0),
        ("Onkyo A-9155 Stereo Verstärker mit Fernbedienung", 90.0),
        ("Marantz PM 66SE Special Edition Verstärker mit Fernbedienung", 150.0),
        ("Yamaha AV Receiver RX-V367 mit Fernbedienung", 70.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "vintage_elektronik", title


def test_roehrenfernseher_mit_fernbedienung_matcht_wieder():
    for title, price in [
        ("Grundig Röhrenfernseher inkl Fernbedienung", 20.0),
        ("Technisat Röhrenfernseher silber mit Fernbedienung", 15.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "vintage_elektronik", title


def test_standalone_fernbedienung_matcht_weiterhin_nicht():
    for title, price in [
        ("Sony Trinitron RM 694 Fernbedienung", 15.0),
        ("Sony PVM Monitor Fernbedienung RM668", 20.0),
        ("Ersatz Fernbedienung passend für Sony Trinitron TV", 10.0),
        ("Hanseatic Fernbedienung voll funktionsfähig 80er Jahre für Röhrenfernseher", 8.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "vintage_elektronik"), title


def test_ersatzfernbedienung_kompositum_matcht_weiterhin_nicht():
    # "ersatzfernbedienung" bleibt unveraendert bare -- kein legitimer
    # Bundle-Fall bekannt.
    r = evaluate("Original Ersatzfernbedienung für Sony Trinitron", 12.0, _rules_cfg())
    assert not (r.matched and r.category == "vintage_elektronik")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
