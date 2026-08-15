"""Regressionstests für den handhelds-PS-Vita-"ovp"-Kontext-Fix
(Nutzer-Freigabe 2026-08-15, FALSE_POSITIVES_ANALYSE Teil 1 C).

Hintergrund: bare "ovp" ohne jeden Geräte-Marker matchte PS-Vita-
SPIELTITEL als Konsole. Anders als bei konsolen_bundles.yaml (dort
enthält jede Regel nur EINE Plattform-Familie) bündelt handhelds.yaml
mehrere Geräte in einer Kategorie -- ein kategorieweiter bare-"ovp"-
Trigger hätte auch Steam-Deck-/ROG-Ally-/3DS-Verkäufe fälschlich
blockiert. Deshalb sind die PS-Vita-Plattformbegriffe selbst der
Trigger (nicht "ovp"), sodass der Exclude nur bei einer PS-Vita-
Erwähnung ohne Geräte-Marker greift.

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


def _matches_handhelds(title, price=30.0):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "handhelds"


def test_bestaetigte_vita_spieltitel_matchen_nicht_mehr():
    for title, price in [
        ("PS Vita uncharted ° Golden Abyss ° OVP ° Sehr guter Zustand", 30.0),
        ("PS Vita Spiele: FIFA 14 (mit OVP) + Final Fantasy X HD Remaster", 25.0),
        ("Touch My Katamari PSVita Neu & OVP", 49.95),
    ]:
        assert _matches_handhelds(title, price) is False, title


def test_grenzfall_sammlung_ohne_marker_wird_mitblockiert():
    # Analyse Teil 1, Fall #34: "nicht hundertprozentig sicher" -- ohne
    # Geräte-Marker konsistent mit den 3 bestätigten FP behandelt.
    assert _matches_handhelds("Sony PlayStation Vita Kleine SAMMLUNG OVP PAL", 22.99) is False


def test_echtes_geraet_ueber_modellcode_matcht_weiterhin():
    # PCH-Modellcode-Präfix ist Teil der Kontextliste -- rettet echte
    # Kurzverkäufe ohne "konsole"/"bundle"/"set"/"system" im Titel.
    assert _matches_handhelds(
        "Vintage Sony PS Vita PCH-1004 Schwarz OLED Top Zustand OVP", 60.0
    ) is True


def test_echtes_geraet_ueber_konsole_bundle_set_matcht_weiterhin():
    assert _matches_handhelds("PS Vita Konsole PCH-2000 mit OVP", 55.0) is True
    assert _matches_handhelds("PlayStation Vita Bundle mit OVP", 55.0) is True
    assert _matches_handhelds("PSVita Set mit OVP", 55.0) is True


def test_andere_geraetetypen_mit_ovp_bleiben_unberuehrt():
    # Sicherheitsprüfung gegen den ursprünglich zu breiten ersten Versuch
    # (bare "ovp"-Trigger hätte diese kategorieweit mitblockiert).
    assert _matches_handhelds("New Nintendo 3DS XL OVP Schwarz – Originalverpackung", 75.0) is True
    assert _matches_handhelds("Asus ROG Ally Z1 Extreme, 512GB, OVP", 0.0) is True
    assert _matches_handhelds("Steam Deck + 5 Spiele OVP", 220.0) is True


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
