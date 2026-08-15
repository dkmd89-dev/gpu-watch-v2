"""Regressionstest für das Xenoblade-Spieltitel-Problem in handhelds.yaml
(Nutzer-Meldung 2026-08-15, Live-Fehltreffer-Report).

Hintergrund: "[Spieltitel] für Nintendo [New] 3DS" ist ein Software-
Angebot, kein Gerät -- die require_all_of-Gruppe 2 dieser Kategorie hat
für 3DS/2DS kein generisches, plattformunabhängiges Signalwort (anders
als retro_konsolen: "konsole"/"gerät"/"system" dort), sondern matcht
bereits über den reinen Plattformnamen ("new 3ds"/"xl"). Real bestätigt,
aktuell live sichtbar: "Xenoblade Chronicles für Nintendo New 3DS OVP"
(18€), "Super Mario 3D Land für Nintendo 3DS 3DS XL" (5€,
price_history.jsonl) -- beide ohne jedes generische Spiel-Signalwort
("spiel"/"modul"). Fix: neuer exclude_category_unless_also_contains-
Eintrag, identisches Prinzip wie die "für [Plattform]"-Kontextprüfung in
konsolen_bundles.yaml, hier erstmalig für handhelds.yaml eingeführt.

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


def test_spieltitel_fuer_3ds_matcht_nicht():
    for title, price in [
        ("Xenoblade Chronicles für Nintendo New 3DS OVP", 18.0),
        ("Super Mario 3D Land für Nintendo 3DS 3DS XL", 5.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "handhelds"), title


def test_echtes_geraet_mit_konsole_kontext_matcht_weiterhin():
    # Kollisionsschutz: enthält "für nintendo 3ds", aber auch
    # "system"/"konsole" -- muss trotz der neuen Regel weiterhin matchen.
    r = evaluate(
        "Nintendo 2DS Handheld System Konsole für Nintendo 3DS Plattform weiß rot",
        74.99,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "handhelds"


def test_reale_true_positives_ohne_fuer_phrase_matchen_weiterhin():
    for title, price in [
        ("Nintendo 3DS XL mit Spielen !ABHOLUNG!", 90.0),
        ("ASUS ROG Ally Z1 Extreme 16GB / 512GB neuwertig", 300.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "handhelds", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
