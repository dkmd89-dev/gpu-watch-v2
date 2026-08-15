"""Regressionstest für die retro_konsolen-Erweiterung von
exclude_category_unless_also_contains um "netzteil" (Nutzer-Meldung
2026-08-15, Live-Fehltreffer-Report).

Hintergrund: "netzteil" ist als require_all_of-Gruppe-2-Signal bewusst
erhalten (rettet reale Bundles wie "Nintendo N64 Control Deck 2 Original
Controller Netzteil Erweiterungskarte", die über kein anderes Gruppe-2-
Wort verfügen), reichte aber bislang auch für Standalone-Netzteil-/
Ladegerät-Angebote ohne jedes Gerät aus. Systematischer Blast-Radius-Check
gegen den vollen found.json+price_history.jsonl-Korpus: von 24 Titeln, die
AUSSCHLIESSLICH über "netzteil" matchen, hat genau 1 (der Control-Deck-
Fall) "controller" im Titel -- alle anderen 23 sind Standalone-Angebote.
Identisches, bereits produktives Muster wie "memory card" in derselben
Datei (exclude_category_unless_also_contains).

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


def test_standalone_netzteil_matcht_nicht():
    for title, price in [
        ("⚡ PS2 Netzteil Original Playstation 2 Slim 8,5V Stromkabel Netzkabel Getestet⚡", 17.95),
        ("Nintendo 64 Netzteil", 30.0),
        ("Sony PS2 Netzteil / Ladekabel", 10.0),
        ("N64 USB C Netzteil für Nintendo 64 Ersatznetzteil", 30.0),
        ("Sony PlayStation 2 Original Netzteil Videokabel Memorycard", 50.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "retro_konsolen"), title


def test_netzteil_mit_controller_kontext_matcht_weiterhin():
    # Der einzige der 24 real geprüften Fälle mit "controller" im Titel --
    # muss erhalten bleiben (Kollisionsschutz).
    r = evaluate(
        "Nintendo N64 Control Deck 2 Original Controller Netzteil Erweiterungskarte",
        99.0,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "retro_konsolen"


def test_netzteil_mit_konsole_kontext_matcht_weiterhin():
    for title, price in [
        ("Nintendo DS Lite Konsole Schwarz mit Netzteil, Tasche & Spiele inkl. Zubehör", 45.0),
        ("Sony Playstation 2 Konsole mit Netzteil inkl Spiele", 30.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "retro_konsolen", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
