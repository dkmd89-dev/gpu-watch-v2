"""Regressionstests für den IdeaPad-Gaming-3-C1-Minimal-Recall-Fix
(2026-08-16, siehe Analysebericht "IdeaPad / IdeaPad Gaming Recall
Impact Analysis").

Root Cause: "Lenovo IdeaPad Gaming 3...GTX 1650..." erfüllte die
GPU-Gruppe der Regel "Gaming Laptop (GTX 1650)" bereits vollständig,
scheiterte aber am Gerätewort-Gate ("laptop"/"notebook") -- der Titel
enthält "gaming", das bewusst nicht als Ersatz akzeptiert wird (analoge
Design-Entscheidung wie bei der RTX3060-Regel).

Fix: das eng gefasste Zwei-Wort-Signal "ideapad gaming" als zusätzliche
OR-Alternative zur Gerätewort-Gruppe ergänzt. Bewusst als Erweiterung
DIESER bestehenden Regel statt einer separaten, generischen
"ideapad"-Marken-Regel -- Letztere hätte das Risiko geborgen, GPU-Fälle
mit der falschen (nicht GPU-kalibrierten) Preisbasis zu erfassen.

Die beiden non-Gaming IdeaPad-Fälle (IdeaPad 5, IdeaPad 5 15ARE05)
bleiben bewusst NICHT gefixt -- keine sichere Variante identifiziert
(siehe Analysebericht, Adversarial-Test zeigte 3/12 Fehlklassifikationen
für das einzig verfügbare Modellsignal "bare 5").

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
# 1. Der Ziel-Recall-Gap matcht jetzt
# ---------------------------------------------------------------

def test_ideapad_gaming3_matcht_jetzt():
    r = evaluate(
        "Lenovo IdeaPad Gaming 3 15IMH05 | i5-10300H | GTX 1650 | 8GB RAM "
        "| 512GB SSD",
        339.0,
        _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "notebook_resell"
    assert r.rule_label == "Gaming Laptop (GTX 1650)"


# ---------------------------------------------------------------
# 2. Bestehende GTX1650-Gaming-Laptop-Faelle bleiben unveraendert
# ---------------------------------------------------------------

def test_bestehende_gtx1650_faelle_bleiben_unveraendert():
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


def test_gtx1650_ti_bleibt_weiterhin_ausgeschlossen():
    r = evaluate(
        "Lenovo Legion 5 17IMH05 Gaming Laptop i5 10300H 16GB RAM 512GB "
        "SSD GTX 1650 Ti",
        395.0,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "notebook_resell")


# ---------------------------------------------------------------
# 3. Desktop-Gaming-PCs mit GTX1650 bleiben unveraendert gaming_pc
# ---------------------------------------------------------------

def test_desktop_gaming_pc_mit_gtx1650_bleibt_gaming_pc():
    for title, price in [
        (
            "Gaming PC- Ryzen 5 3400G/16GB DDR4/400GB SSD/ GTX 1650/Win 11",
            280.0,
        ),
        (
            "Gaming pc i5 8600k GeForce GTX 1650 16GB RAM Nvme Windows 11",
            329.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.category == "gaming_pc", title


# ---------------------------------------------------------------
# 4. Adversarial-Faelle bleiben unmatched
# ---------------------------------------------------------------

def test_adversarial_ideapad_zubehoer_bleibt_unmatched():
    for title, price in [
        ("IdeaPad Zubehör Ladekabel 512GB SSD extern", 30.0),
        ("IdeaPad Netzteil 65W 5 Stück Set 8GB", 20.0),
        ("IdeaPad Akku 5 Zellen 16GB Ersatz", 25.0),
        ("IdeaPad Mainboard 8GB RAM 256GB SSD", 60.0),
        ("IdeaPad Tastatur deutsch 5-polig 16GB", 15.0),
        ("IdeaPad Dockingstation USB-C 512GB", 35.0),
        ("IdeaPad Gaming Maus RGB 5 Tasten", 20.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "notebook_resell"), title


# ---------------------------------------------------------------
# 5. Die beiden normalen IdeaPad-5-Faelle bleiben unveraendert unmatched
# ---------------------------------------------------------------

def test_ideapad_5_non_gaming_faelle_bleiben_bewusst_unmatched():
    for title, price in [
        ("Lenovo IdeaPad 5 Ryzen 7 4700U 16GB RAM 500GB SSD", 180.0),
        (
            "LENOVO IDEAPAD 5 15ARE05/AMD RYZEN 5 4600U/250GB SSD NEU/16GB RAM",
            250.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "notebook_resell"), title


# ---------------------------------------------------------------
# 6. Andere A3-A7-Faelle bleiben unveraendert
# ---------------------------------------------------------------

def test_andere_a3_a7_faelle_unveraendert():
    r1 = evaluate(
        "Dell Latitude 5501 15,6\" FHD | i5-9400H | 8GB RAM | 250GB SSD",
        229.0,
        _rules_cfg(),
    )
    assert r1.matched is True and r1.rule_label == "Dell Latitude"

    r2 = evaluate(
        "ACEMAGIC 16'' FHD Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM 512GB SSD "
        "Win11 Pro",
        289.0,
        _rules_cfg(),
    )
    assert r2.matched is True and r2.rule_label == "ACEMAGIC Laptop"

    r3 = evaluate(
        "HP Laptop 17,5 Zoll – Ryzen 5 5500U – 8 GB DDR4", 100.0, _rules_cfg()
    )
    assert not (r3.matched and r3.category == "notebook_resell")

    r4 = evaluate(
        "Fujitsu Lifebook U7510 i5-10310U 2.20 GHz , 16GB DDR4, 512GB NVMe, "
        "Win 11 Pro",
        245.0,
        _rules_cfg(),
    )
    assert not (r4.matched and r4.category == "notebook_resell")

    r5 = evaluate(
        "Lenovo Laptop L480 - Core i5 8250u - 8GB DDR4 - 256 GB NVMe - WIN",
        125.0,
        _rules_cfg(),
    )
    assert r5.matched is True and r5.category == "notebook_resell"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
