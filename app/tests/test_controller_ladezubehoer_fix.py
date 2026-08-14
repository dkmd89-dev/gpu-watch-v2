"""Regressionstest für STATUS.md Datenqualität Nr. 5 ("controller-ladekabel-
Exclude separat bewerten", Phase-15-Restlücke, 2026-08-14 final untersucht).

Ergebnis der Analyse: der bestehende exclude_category_unless_preceded_by-
Mechanismus für "ladekabel" selbst funktioniert korrekt (Standalone-Kabel
werden blockiert, echte "Controller inkl. Ladekabel"-Bundles bleiben
erhalten). Die tatsächliche Lücke betrifft einen ANDEREN Zubehör-Typ:
Lade-STATIONEN/-GERÄTE (Dock-artiges Zubehör statt Kabel), real bestätigt:
"PS5 Controller USB Dual-Charger Station", "PowerA Twin Charging Station
für PS5 Controller", "5in1 Switch Aufladegerät für 4 Joycons und 1 Pro
Controller" (Kompositum-Lücke, identisches Muster wie "Lötaufsatz").

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


def test_ladestationen_und_aufladegeraet_matchen_nicht():
    for title, price in [
        ("5in1 Switch 1 Aufladegerät für 4 Joycons und 1 Pro Controller", 9.0),
        ("PS5 Controller USB Dual-Charger Station Neu in OVP", 6.99),
        ("PowerA Twin Charging Station für PS5 Controller", 15.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "controller"), title


def test_standalone_ladekabel_matcht_weiterhin_nicht():
    # Bestehendes Verhalten (exclude_category_unless_preceded_by) darf
    # durch diesen Fix nicht regressieren.
    r = evaluate("USB-C Ladekabel für PS5 Controller 3m", 8.0, _rules_cfg())
    assert r.matched is False


def test_echtes_bundle_mit_ladekabel_matcht_weiterhin():
    r = evaluate(
        "Nintendo Switch Pro Controller schwarz inkl. Ladekabel",
        20.0,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "controller"


def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Original Xbox Controller (Xbox series x)", 30.0),
        ("Sony DualSense Wireless Controller kabellos für PS5 schwarz", 25.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "controller", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
