"""Regressionstests für die Notebook-Recall-Optimierung, A3-A7 Option D,
Gerätewort-Fälle (2026-08-16): neue Marken-Regeln für Dell Latitude,
ACEMAGIC und Lenovo V330 -- ausschließlich für Titel mit explizitem
"laptop"/"notebook"-Wort im Titel (7 von 14 A3-A7-Fällen betroffen,
davon 2 HP-Fälle bewusst NICHT implementiert -- siehe unten).

Root Cause: keine der drei Marken hatte bisher eine eigene
require_all_of-Struktur in notebook_resell.yaml. Alle drei Marken kommen
im vollständigen 2306-Eintrag-Ground-Truth-Korpus AUSSCHLIESSLICH als
TRUE_POSITIVE vor (0 Zubehör-/Ersatzteil-/Desktop-Kollisionen) -- anders
als "HP", das als generische, sehr breite Marke bewusst NICHT
implementiert wurde: eine bare "hp"-Regel würde unkontrolliert auch HP
OMEN/Pavilion Gaming (bereits über eigene GPU-Regeln abgedeckt), HP
Zbook (= Cluster A10, ausdrücklich außerhalb des Scopes) sowie im
GT-Korpus nicht vertretene HP-Sublinien (EliteBook/ProBook/Envy/
Spectre) einschließen -- Cross-Category-Risiko nicht sicher
kontrollierbar (siehe Analysebericht "A3-A7 Option D").

Dell Latitude: nur 2 der 5 bekannten GT-Fälle hatten hier ursprünglich ein
Gerätewort im Titel -- die 3 übrigen (Latitude 5501/5500/7400) blieben
zunächst bewusst unmatched (Cluster "ohne Gerätewort", damals außerhalb
des Scopes dieser Phase).

UPDATE (Latitude Recall-Gap, Variante B, 2026-08-16, siehe
tools/ruleset_quality/generated/reports/latitude_recall_gap_simulation.{json,md}
und notebook_resell.yaml-Kommentar): diese 3 Fälle wurden in einer
separaten, gezielt freigegebenen Folgephase durch eine geschlossene,
korpusbelegte Modellcode-Liste ("5300"/"5401"/"5500"/"5501"/"7400" als
zusätzliche OR-Alternativen zur Geräte-Gruppe) gelöst -- siehe
test_notebook_resell_latitude_variant_b_fix.py. Der Test unten ist
entsprechend aktualisiert. ACEMAGIC/V330/HP sind von diesem Update NICHT
betroffen.

Preisgrenzen bewusst NICHT neu erfunden -- Wiederverwendung der bereits
in Cluster B belastbar kalibrierten ThinkPad-Grenzen (180€/330€).

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
# Dell Latitude -- die 2 Faelle MIT Geraetewort matchen
# ---------------------------------------------------------------

def test_dell_latitude_faelle_mit_geraetewort_matchen():
    for title, price in [
        ("Notebook Dell Latiitude 5401 i5 9400H 16GB DDR4 256GB  SSD", 150.0),
        (
            "Dell Latitude 5300 Notebook 13„ i5-8265U 8GB RAM 250GB SSD W11",
            250.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title


def test_dell_latitude_faelle_ohne_geraetewort_matchen_seit_variante_b():
    # UPDATE (Latitude Recall-Gap, Variante B, 2026-08-16): diese 3 Faelle
    # matchen seit der gezielt freigegebenen Modellcode-Erweiterung korrekt
    # -- siehe test_notebook_resell_latitude_variant_b_fix.py fuer die
    # vollstaendige Regression (inkl. Adversarial-Faelle, die weiterhin
    # NICHT matchen duerfen).
    for title, price in [
        (
            "Dell Latitude 5501 15,6\" FHD | i5-9400H | 8GB RAM | 250GB SSD",
            229.0,
        ),
        ("Dell Latitude 5500  i5-8365U 8GB Ram 250 GB SSD", 145.0),
        (
            "Dell Latitude 7400 14\" FHD i7-8665U 16GB DDR4 512GB SSD "
            "Win11 Pro FP ohne Füße",
            169.90,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title


# ---------------------------------------------------------------
# ACEMAGIC -- beide bekannten Faelle matchen
# ---------------------------------------------------------------

def test_acemagic_faelle_matchen():
    for title, price in [
        (
            "ACEMAGIC 16'' FHD Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM "
            "512GB SSD Win11 Pro",
            289.0,
        ),
        (
            "ACEMAGIC 16'' AX16Pro Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM "
            "512GB SSD Win11P",
            289.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title
        assert r.rule_label == "ACEMAGIC Laptop", title


# ---------------------------------------------------------------
# Lenovo V330 -- der bekannte Fall matcht
# ---------------------------------------------------------------

def test_lenovo_v330_matcht():
    r = evaluate(
        "Lenovo V330-15IKB Laptop i5 8250U 15,6\" 8GB DDR4 RAM 256GB SSD "
        "Win 11",
        149.95,
        _rules_cfg(),
    )
    assert r.matched is True and r.category == "notebook_resell"
    assert r.rule_label == "Lenovo V330 ★ Resell-Top"


def test_v330_ohne_lenovo_marken_gate_matcht_nicht():
    # Absicherung: "v330" allein (ohne "lenovo") darf NICHT reichen --
    # zu kurzer/generischer Code, bewusst zusaetzliches Marken-Gate.
    r = evaluate(
        "V330 Laptop i5 8250U 8GB DDR4 RAM 256GB SSD Win 11", 149.95, _rules_cfg()
    )
    assert not (r.matched and r.category == "notebook_resell")


# ---------------------------------------------------------------
# HP (generic) -- BLOCKED, bewusst nicht implementiert
# ---------------------------------------------------------------

def test_hp_generic_bleibt_bewusst_unmatched_blocked():
    for title, price in [
        ("HP Laptop 17,5 Zoll – Ryzen 5 5500U – 8 GB DDR4", 100.0),
        (
            "HP Laptop 15,6 Ryzen 5 7000er Reihe/ 16GB DDR5/  1TB SSD Win11",
            270.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "notebook_resell"), title


# ---------------------------------------------------------------
# Cross-Category-Schutz: bestehende Kategorien bleiben unberuehrt
# ---------------------------------------------------------------

def test_bestehende_thinkpad_gtx1650_faelle_bleiben_unveraendert():
    r1 = evaluate(
        "Lenovo ThinkPad T14 Gen1 i5 10310U 16GB RAM 256GB SSD 14\" FHD "
        "Win 11 Pro MwSt.",
        299.99,
        _rules_cfg(),
    )
    assert r1.matched is True and r1.category == "notebook_resell"

    r2 = evaluate(
        "HP Pavilion Gaming Laptop 15\" | i5-9300H | 8GB RAM | 512GB SSD "
        "|GTX 1650/Zubehör",
        285.0,
        _rules_cfg(),
    )
    assert r2.matched is True and r2.category == "notebook_resell"
    assert r2.rule_label == "Gaming Laptop (GTX 1650)"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
