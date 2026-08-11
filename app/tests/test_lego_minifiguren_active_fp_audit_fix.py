"""Regressionstest für den lego_minifiguren-Fix aus dem Active-False-
Positive-Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: Die require_all_of-Gruppen dieser Kategorie prüfen nur, ob
das WORT "figur"/"figuren"/"minifigur" im Titel vorkommt -- eine
vorangestellte Negation ("Ohne Figuren") wird nicht erkannt, da
"figuren" als Teilstring von "Ohne Figuren" trotzdem matcht. Real
bestätigt gegen found.json (1 Titel im vollständigen 1750-Titel-Korpus):
"Lego Star Wars Sammlung, 75082,7959,9488, Komplett Ohne Figuren" -- ein
reines Set-/Fahrzeug-Konvolut OHNE Minifiguren, matchte bisher als
"LEGO Minifiguren-Sammlung".

Fix: vier neue bare exclude_category-Phrasen ("ohne figur"/"ohne
figuren"/"ohne minifigur"/"ohne minifiguren", Singular+Plural beider
Wortformen analog zum handhelds.yaml-Muster "ersatzstift"/"ersatzstifte").
Bewusst NICHT ergänzt: andere Negationswörter ("keine"/"kein") -- kein
Beleg im Korpus.

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


def _matches_lego(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "lego_minifiguren"


# ============================================================
# 1. Real bestätigter Fehltreffer -- muss jetzt blockiert werden.
# ============================================================

def test_ohne_figuren_matcht_nicht():
    assert _matches_lego(
        "Lego Star Wars Sammlung, 75082,7959,9488, Komplett Ohne Figuren", 34.99
    ) is False


def test_weitere_negations_varianten_matchen_nicht():
    # Singular/Plural-Geschwisterformen des real bestätigten Musters
    # (kein eigener Korpusbeleg, aber identisches strukturelles Muster --
    # analog zum bereits etablierten Singular/Plural-Fix in handhelds.yaml).
    for title, price in [
        ("LEGO Star Wars Set 75082 Komplett Ohne Figur", 30.0),
        ("LEGO Ninjago Set Komplett Ohne Minifiguren", 25.0),
        ("LEGO Castle Set Ohne Minifigur, nur Bausteine", 20.0),
    ]:
        assert _matches_lego(title, price) is False, title


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Treffer bleiben unverändert
#    erhalten (echte Preise aus found.json).
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("LEGO Konvolut: 9 Minifiguren und 6 Briefkästen", 20.0),
        ("LEGO Star Wars Clone Trooper Minifigur Commander Cody", 35.0),
        ("LEGO Ninjago Minifiguren Konvolut 12×Lego Minifiguren.", 20.0),
        ("Lego Star Wars Sammlung, 75082,7959,9488, Komplett Ohne Figuren".replace(
            "Ohne Figuren", "Mit Figuren"
        ), 34.99),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "lego_minifiguren", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
