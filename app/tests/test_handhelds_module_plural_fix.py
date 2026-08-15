"""Regressionstest für die handhelds-exclude_category-Erweiterung um die
Pluralform "module" (Nutzer-Meldung 2026-08-15, Live-Fehltreffer-Report).

Hintergrund: der bestehende Exclude "modul" (Singular) wird von
matcher.py::_contains_term() als ganzes Wort geprüft und erfasst daher
NICHT die Pluralform "Module" in Titeln wie "Nintendo DS und 3DS Spiele
(AUSWAHL) Module - Sammlung Konvolut - 2DS DSi XL" -- ein reines
Spielemodul-Konvolut ohne Konsole, aktuell live als Top-Deal sichtbar
gewesen. Bewusst NICHT "spiele" (Plural von "spiel") ergänzt: Blast-Radius-
Check gegen found.json zeigt 5 echte Konsole+Spiele-Bundles ("Nintendo 3DS
XL ... mit Spielen"/"... SPIELE ZUSÄTZLICH"), die dadurch fälschlich
ausgeschlossen würden.

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


def test_module_plural_matcht_nicht():
    r = evaluate(
        "Nintendo DS und 3DS Spiele (AUSWAHL) Module - Sammlung Konvolut - 2DS DSi XL",
        39.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "handhelds")


def test_modul_singular_matcht_weiterhin_nicht():
    # Bestehendes Verhalten (Singular-Exclude) darf nicht regressieren.
    r = evaluate("Nintendo 3DS Modul Zelda", 15.0, _rules_cfg())
    assert not (r.matched and r.category == "handhelds")


def test_reale_konsole_mit_spielen_bundles_matchen_weiterhin():
    # Kollisionsschutz: "spiele" (Plural) wurde bewusst NICHT ergänzt,
    # weil diese echten Konsole+Spiele-Bundles sonst faelschlich
    # ausgeschlossen würden.
    for title, price in [
        ("NINTENDO 3DS XL SCHWARZ  SPIELE ZUSÄTZLICH", 95.0),
        ("Nintendo 3DS XL mit Spielen !ABHOLUNG!", 90.0),
        ("NINTENDO 3DS XL SCHWARZ MIT  SPEICHERKARTE SPIELE ZUSÄTZLICH", 95.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "handhelds", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
