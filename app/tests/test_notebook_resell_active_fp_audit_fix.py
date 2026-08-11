"""Regressionstest für den notebook_resell-Fix aus dem Active-False-
Positive-Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: Die dritte require_all_of-Gruppe der ThinkPad-Regel
akzeptiert bare "ssd"/"nvme" als Alternative zu einer konkreten
Speichergrößenangabe (siehe bestehender Regel-Kommentar in
notebook_resell.yaml) -- eine vorangestellte Negation wird nicht
erkannt, da "ssd" als Teilstring von "Ohne SSD/RAM" identisch matcht.
Real bestätigt gegen found.json (2 Titel im vollständigen 84-Titel-
Match-Korpus): "Lenovo ThinkPad L14 Gen 3 | Ryzen 5 PRO 5675U | BIOS OK
| Ohne SSD/RAM" -- ein bloßes Mainboard+CPU-Gehäuse ganz ohne RAM UND
ohne Storage, kein funktionsfähiges Notebook.

Fix: 1 neue bare-phrase exclude_category-Ergänzung ("ohne ssd/ram").

Bewusst NICHT generalisiert auf "ohne ssd" allein: 2 weitere Titel im
Korpus ("...8GB RAM OHNE SSD...") haben echtes RAM und erfüllen Gruppe
3 bereits unabhängig über die RAM-Größe -- ein bare "ohne ssd"-Exclude
würde diese echten Barebone-mit-RAM-Angebote fälschlich blockieren
(siehe Sicherheitstest unten).

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


def _matches_notebook_resell(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "notebook_resell"


# ============================================================
# 1. Real bestätigter Fehltreffer -- muss jetzt blockiert werden.
# ============================================================

def test_ohne_ssd_ram_matcht_nicht():
    for title, price in [
        (
            "Lenovo ThinkPad L14 Gen 3 | Ryzen 5 PRO 5675U | BIOS OK | Ohne SSD/RAM #TR326",
            199.99,
        ),
        (
            "Lenovo ThinkPad L14 Gen 3 | Ryzen 5 PRO 5675U | BIOS OK | Ohne SSD/RAM #TR343",
            209.99,
        ),
    ]:
        assert _matches_notebook_resell(title, price) is False, title


# ============================================================
# 2. Sicherheitsprüfung: Barebone-Angebote MIT echter RAM-Angabe (nur
#    ohne SSD) bleiben unverändert TRUE_POSITIVE -- der Fix darf nicht
#    auf bare "ohne ssd" verallgemeinert werden.
# ============================================================

def test_barebone_mit_ram_ohne_ssd_matcht_weiterhin():
    for title, price in [
        (
            "Lenovo ThinkPad X13 Gen 1 | Intel Core i5-10210U | 8GB RAM | OHNE SSD  #925",
            143.99,
        ),
        (
            "Lenovo ThinkPad T490 i5-8265U 8GB RAM  ohne SSD ohne Netzteil BIOS #960",
            149.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title


def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Lenovo ThinkPad X390 | 13,3\" | i5-8265U | 8 GB RAM | 256 GB SSD", 169.0),
        ("Lenovo ThinkPad T490 i5-8365U 16GB 256GB 14\" FHD Win11 StoreDeal #32", 229.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
