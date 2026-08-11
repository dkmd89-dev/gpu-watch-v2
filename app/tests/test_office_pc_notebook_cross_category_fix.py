"""Regressionstests für den office_pc-Notebook-Exclude aus dem
Cross-Category Routing Audit (docs/CROSS_CATEGORY_ROUTING_AUDIT.md,
Abschnitt 5.1/9.1).

Hintergrund: `office_pc.yaml` nutzt "requirements:"-Detector-Matching
(RAM/CPU/Gehäuse) statt Titel-Keywords. `matcher.py::_case_meets_requirement()`
behandelt "kein erkennbares Gehäuse" bewusst als ERFÜLLT -- ein Notebook
hat naturgemäß keine separate Gehäuse-Beschreibung und rutschte dadurch
strukturell durch dieselbe Lücke wie die bereits gefixten bare
Mainboard-Bundles (siehe test_office_pc_active_fp_audit_fix.py). 21
reale, aktuell matchende found.json-Titel bestätigt (149,95-339,00€,
ThinkPad/MacBook/Alienware/Lifebook/IdeaPad/ACEMAGIC/ASUS-TUF u.a.) --
davon 1 zusätzlich als Domino-Effekt des bereits gefixten
gaming_pc-Excludes (PR #24) neu entstanden.

Root Cause identisch zum bereits in gaming_pc.yaml gefixten Muster
(dort: "Diese Kategorie WILL komplette PC-Systeme", identische
Begründung). Alternative "notebook_resell.yaml-Preisdeckel anheben"
explizit gegen den vollen 97-Titel-ThinkPad-Realkorpus geprüft und
verworfen (89% der realen Angebote liegen bereits innerhalb der
bestehenden 180/240€-Grenzen) -- siehe Audit-Doku Abschnitt 9.1.

Fix: `exclude_category` um `laptop`, `notebook`, `thinkpad`, `macbook`,
`ideapad`, `alienware`, `lifebook` erweitert (bare Markenbegriffe statt
nur "laptop"/"notebook", weil mehrere reale Titel keines der beiden
Wörter enthalten, z.B. "Lenovo ThinkPad X390 | 13,3\" | i5-8365U...").

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


# ============================================================
# 1. Reale Fehltreffer/Routing-Fälle: Notebooks matchen office_pc nicht
#    mehr (repräsentative Auswahl über alle 7 neuen Exclude-Begriffe).
# ============================================================

def test_thinkpad_ohne_laptop_notebook_wort_matcht_nicht():
    # "thinkpad" bare -- Titel enthält weder "laptop" noch "notebook".
    for title, price in [
        ('Lenovo ThinkPad X390 | 13,3" | i5-8365U | 8 GB RAM | 512 GB SSD', 293.0),
        ("Lenovo ThinkPad X13 Gen.1 13,3\" Intel i5-10310U 1,70GHz 16GB RAM 256GB SSD Touch", 249.0),
        ("Lenovo ThinkPad T14 Gen1 i5 10310U 16GB RAM 256GB SSD 14\" FHD Win 11 Pro MwSt.", 299.99),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "office_pc"), title


def test_laptop_notebook_wort_matcht_nicht():
    for title, price in [
        ("ACEMAGIC 16'' AX16Pro Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM 512GB SSD Win11P", 289.0),
        ("ASUS TUF Gaming FX705DT Notebook 17 Zoll 16GB RAM ;AMD Ryzen 5 3550H", 290.03),
        ("Lenovo V330-15IKB Laptop i5 8250U 15,6\" 8GB DDR4 RAM 256GB SSD Win 11", 149.95),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "office_pc"), title


def test_ideapad_gaming_laptop_domino_fall_matcht_nicht():
    # Der in Abschnitt 3 des Audits dokumentierte Domino-Fall: seit dem
    # gaming_pc-Exclude (PR #24) landete dieser Titel in office_pc.
    r = evaluate(
        "Lenovo IdeaPad Gaming 3 15IMH05 | i5-10300H | GTX 1650 | 8GB RAM | 512GB SSD",
        339.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "office_pc")
    assert not (r.matched and r.category == "gaming_pc")


def test_macbook_matcht_nicht():
    r = evaluate(
        "Apple MacBook Pro 16.1 | i9-9880H | 16GB RAM 1024GB SSD  OHNE OS  QWERTY | Nr. 1",
        299.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "office_pc")


def test_alienware_lifebook_matchen_nicht():
    r = evaluate(
        "DELL [OVP] || Alienware M17 R3 | i7-10750H - 16GbDDR4 - 2TbM2 - 1660Ti+UHD630 - W11",
        50.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "office_pc")

    r2 = evaluate(
        "Fujitsu Lifebook U7510 i5-10310U 2.20 GHz , 16GB DDR4, 512GB NVMe, Win 11 Pro",
        245.0,
        _rules_cfg(),
    )
    assert not (r2.matched and r2.category == "office_pc")


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Desktop-/Tower-Titel bleiben
#    unverändert office_pc (kein neuer Kollisionsschaden).
# ============================================================

def test_reale_desktop_true_positives_matchen_weiterhin():
    for title, price in [
        ("Dell Optiplex 7060 Tower PC Core i5-8500 3GHz 16GB DDR4 Ram 512GB NVMe", 179.0),
        ("Terra Business PC Core i5-8500 3,0GHz 8GB RAM 250GB SSD Win 10 Pro (mk)", 109.90),
        ("Fujitsu Esprimo D7010 Intel Core i7-10700 16GB RAM Business Desktop-PC", 278.0),
        ("Dell Precision 3450 I7 11700 16GB DDR4 Office PC", 300.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "office_pc", title


# ============================================================
# 3. Grenzfälle.
# ============================================================

def test_ueber_240_euro_thinkpad_landet_unmatched_nicht_in_notebook_resell():
    # Grenzfall: ein ThinkPad ueber dem notebook_resell-Preisdeckel
    # (240€) matcht nach diesem Fix WEDER office_pc NOCH notebook_resell
    # -- das ist die bewusste, im Audit dokumentierte Konsequenz (siehe
    # Abschnitt 9.1: Preisdeckel-Anhebung explizit verworfen, keine
    # Datenbasis). Kein neues Fehlrouting, sondern korrektes "kein Deal".
    r = evaluate(
        "Lenovo ThinkPad L14 G1 Core i5 10310U 16 GB RAM 240 GB M.2 nVME SSD Webcam",
        279.0,
        _rules_cfg(),
    )
    assert r.matched is False


def test_thinkpad_innerhalb_preisdeckel_matcht_weiterhin_notebook_resell():
    # Grenzfall: derselbe Modellcode, aber innerhalb des
    # notebook_resell-Preisdeckels -- muss weiterhin dort matchen (der
    # office_pc-Exclude darf notebook_resell selbst nicht beeinflussen).
    r = evaluate(
        "Lenovo ThinkPad T14 Gen1 i5 10310U 16GB RAM 256GB SSD 14\" FHD Win 11 Pro MwSt.",
        230.0,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "notebook_resell"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
