"""Regressionstests für die Notebook-Recall-Optimierung, Cluster A1+A2+A8
(2026-08-16): Modellcode-Erweiterung (Wortgrenzen-Bug + fehlende
ThinkPad-Serien) und neue GTX-1650-Gaming-Laptop-Regel.

Cluster A1 (Wortgrenzen-/Kompositum-Bug, KEIN neues Modell): "T490s"/
"T14s" matchten trotz vollständig erfüllter Signale nicht, weil
matcher.py::_contains_term() prüft `(?<!\\w)term(?!\\w)` -- das
angehängte "s" verhindert den Wortgrenzen-Treffer von bare "t490"/"t14".
Identisches Muster wie bereits dokumentierte Kompositum-Probleme
(teildefekt/defekt, ps4slim/ps4). Fix: "t490s"/"t14s" als eigene
Begriffe ergänzt (lokal, keine Änderung an _contains_term() selbst).

Cluster A2 (echte Whitelist-Lücke): "L480"/"L590"/"E15" als weitere
ThinkPad-Serien ergänzt. WICHTIG: nur die "ThinkPad E15"-Fälle sind
mit diesem minimalen Fix lösbar -- "L480"/"L590"-Titel im GT-Korpus
enthalten das Wort "ThinkPad" nicht wörtlich (nur "Lenovo Laptop
L480"/"Notebook Lenovo L590") und scheitern daher weiterhin an der
Marken-Gate-Gruppe (["thinkpad", "think pad"]) -- eine Lockerung dieser
Gruppe wäre eine Architekturänderung außerhalb des Scopes dieser Phase
(siehe Analysebericht "Notebook Recall Optimization – A1/A2/A8/A9 +
A3-A7", Abschnitt 3/14) und wurde bewusst NICHT umgesetzt.

Cluster A8 (GPU-Tier-Lücke, GTX 1650 ohne "Ti"): 3 GT-Fälle, aber nur
2 real matchbar -- "Lenovo IdeaPad Gaming 3...GTX 1650" enthält kein
"laptop"/"notebook"-Wort (identisches Gerätewort-Problem wie A2).
"GTX 1650 Ti"/"RTX 2060"/"RTX 4070" bewusst NICHT ergänzt (je nur 1
GT-Fall, keine belastbare Preisverteilung, siehe
PROPOSED_PRICE_CALIBRATION im Analysebericht).

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
# Cluster A1 -- T490s / T14s matchen jetzt
# ---------------------------------------------------------------

def test_cluster_a1_t490s_varianten_matchen():
    for title, price in [
        ("Lenovo ThinkPad T490s i5 8265U 8gb RAM 512gb SSD", 110.0),
        ("Lenovo Thinkpad T490s, i7 8565u, 16GB Ram, 512GB NVMe, Win11", 225.0),
        (
            "Lenovo ThinkPad T490s 14FHD i7 8665U 16GB-RAM 256SSD WINDOWS-11 "
            "LTE DE-BACKLIT",
            275.0,
        ),
        (
            "Laptop Lenovo ThinkPad T490s Intel I5-8265U 8GB RAM 256GB NVMe "
            "Win11 Pro",
            149.99,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title


def test_cluster_a1_t14s_varianten_matchen():
    for title, price in [
        (
            "Laptop Lenovo ThinkPad T14s Gen 1 14\" Full HD 256GB SSD "
            "i5-10210U 8 GB RAM",
            195.0,
        ),
        (
            "Lenovo Thinkpad T14s G1 Notebook 14\"  i5-10310U 16 GB RAM "
            "256 GB SSD Win 11 Pro",
            249.89,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title


def test_cluster_a1_mainboard_kollisionsfall_bleibt_geblockt():
    # Der einzige im Blast-Radius-Scan gefundene FALSE_POSITIVE-Kandidat:
    # ein reines T490s-Mainboard-Einzelteil. Muss durch den bereits
    # bestehenden bare "mainboard"-Exclude weiterhin geblockt bleiben.
    r = evaluate(
        "Lenovo ThinkPad T490s Mainboard nm-b891 Intel i5-8365U / i5-8265U",
        69.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


# ---------------------------------------------------------------
# Cluster A2 -- ThinkPad E15 matcht, L480/L590 (kein "ThinkPad"-Wort
# im Titel) bleiben bewusst unmatched (siehe Moduldocstring)
# ---------------------------------------------------------------

def test_cluster_a2_thinkpad_e15_matcht():
    r = evaluate(
        "Lenovo ThinkPad E15 15,6\" i5-10210U 16GB RAM 500GB SSD Win11 Pro",
        250.0,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "notebook_resell"


def test_cluster_a2_l480_l590_ohne_thinkpad_wort_bleiben_unmatched():
    # Bewusst NICHT gefixt in dieser Phase: fehlendes Marken-Gate-Signal
    # ("thinkpad"/"think pad" nicht im Titel), keine Architekturänderung
    # ohne separate Freigabe.
    for title, price in [
        ("Lenovo Laptop L480 - Core i5 8250u - 8GB DDR4 - 256 GB NVMe - WIN", 125.0),
        (
            "Notebook Lenovo L590 16GB RAM, 500GB SSD, Win11 Pro Core i5 8265u",
            150.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "notebook_resell"), title


# ---------------------------------------------------------------
# Cluster A8 -- GTX 1650 (ohne Ti) matcht, GTX 1650 Ti bleibt
# ausgeschlossen (keine Preisbasis), IdeaPad Gaming 3 bleibt trotz
# GPU-Signal unmatched (fehlendes Gerätewort)
# ---------------------------------------------------------------

def test_cluster_a8_gtx1650_faelle_matchen():
    for title, price in [
        (
            "MSI GF63 Thin Gaming Laptop | i5-10500H |16GB RAM | 512GB SSD"
            "| GTX 1650 |Aku NEU",
            349.0,
        ),
        (
            "HP Pavilion Gaming Laptop 15\" | i5-9300H | 8GB RAM | 512GB SSD "
            "|GTX 1650/Zubehör",
            285.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title
        assert r.rule_label == "Gaming Laptop (GTX 1650)", title


def test_cluster_a8_gtx1650ti_bleibt_ausgeschlossen():
    # Keine Preisbasis (nur 1 GT-Fall) -- bewusst nicht implementiert.
    r = evaluate(
        "Lenovo Legion 5 17IMH05 Gaming Laptop i5 10300H 16GB RAM 512GB "
        "SSD GTX 1650 Ti",
        395.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


def test_cluster_a8_ideapad_gaming3_bleibt_unmatched_fehlendes_geraetewort():
    r = evaluate(
        "Lenovo IdeaPad Gaming 3 15IMH05 | i5-10300H | GTX 1650 | 8GB RAM "
        "| 512GB SSD",
        339.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


def test_cluster_a8_grenzfall_350_euro_matcht_351_nicht():
    r1 = evaluate(
        "MSI Gaming Laptop i5 16GB RAM 512GB SSD GTX 1650", 350.00, _rules_cfg()
    )
    r2 = evaluate(
        "MSI Gaming Laptop i5 16GB RAM 512GB SSD GTX 1650", 350.01, _rules_cfg()
    )
    assert r1.matched is True and r1.category == "notebook_resell"
    assert not (r2.matched and r2.category == "notebook_resell")


# ---------------------------------------------------------------
# Cross-Category: Desktop-Gaming-PCs mit identischer GPU bleiben
# gaming_pc, nicht notebook_resell
# ---------------------------------------------------------------

def test_desktop_gaming_pc_mit_gtx1650_bleibt_gaming_pc():
    for title, price in [
        (
            "Gaming PC- Ryzen 5 3400G/16GB DDR4/400GB SSD/ GTX 1650/Win 11",
            280.0,
        ),
        (
            "Gaming PC Ryzen 5 2600 16GB DDR4 RAM GTX 1650 Super M2 SSD "
            "500GB",
            330.0,
        ),
        (
            "HP Pavilion Gaming | i5-10300H | 32GB RAM | GTX 1650 4gb| "
            "1.4 TB",
            400.0,
        ),
        (
            "Gaming pc i5 8600k GeForce GTX 1650 16GB RAM Nvme Windows 11",
            329.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.category == "gaming_pc", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
