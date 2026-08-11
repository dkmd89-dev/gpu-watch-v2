"""Regressionstests für den office_pc-Fix aus dem Active-False-Positive-
Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: `office_pc.yaml` hatte bisher bewusst KEIN exclude_category
("Diese Kategorie WILL komplette PC-Systeme"). Die einzige Regel prüft
über "requirements:" (Detector-basiert, siehe matcher.py::
_evaluate_hardware_requirements()) RAM-Größe, CPU-Tier und dass das
Gehäuse NICHT als Tiny/Mini/USFF/SFF/AiO erkannt wird -- verlangt aber
nicht, dass überhaupt ein Gehäuse vorhanden ist
(matcher.py::_case_meets_requirement(): "kein erkennbares Gehäuse gilt
als ERFÜLLT"). Dadurch matchten bare Komponenten-Bundles (Mainboard +
CPU + RAM, kein Gehäuse) als vollständiges Office-PC-System.

Root-Cause-Analyse (siehe office_pc.yaml-Kommentar für Details):
1. "mainboard"/"motherboard" -- identisches, bereits in
   notebook_resell.yaml etabliertes Muster ("Lenovo ThinkPad X390
   Mainboard..." NM-B891, der ursprünglich gemeldete Kandidat).
2. "aufrüstkit"/"aufrüstbundle" -- neu identifiziert, 21+3 reale Treffer
   nach dem Muster "PC Aufrüstkit Bundle [CPU] bis [RAM] mit
   [Mainboard-Modell]", keiner davon nennt ein Gehäuse.

Verifiziert gegen den vollständigen found.json-Korpus (69 damals
matchende office_pc-Titel, echte Preise): 27 reale Fehltreffer, 0
Kollisionen mit den verbleibenden 42 echten Notebook-/Business-PC-
Treffern.

Bewusst NICHT Teil dieses Fixes (P1/P2, siehe Audit-Doku): bare
"bundle"/"kit" -- zu generisch, mehrere reale Titel ("Bundle AMD Ryzen 5
3400G...", "MSI TOMAHAWK B450...Kit", "Gaming Bundle: Ryzen 7 5800X...")
sind vom selben Root-Cause betroffen, haben aber kein eindeutiges
Signalwort und könnten bei einem bare Exclude echte Komplettsystem-
Angebote mit Zubehör-Bundle treffen.

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


def _matches_office_pc(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "office_pc"


# ============================================================
# 1. Ursprünglich gemeldeter Kandidat (identisches Muster wie
#    notebook_resell.yaml).
# ============================================================

def test_thinkpad_x390_mainboard_matcht_nicht():
    assert _matches_office_pc(
        "Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM NM-B891", 49.0
    ) is False


def test_weitere_mainboard_faelle_matchen_nicht():
    assert _matches_office_pc(
        "Mainboard-Kit: MSI B550-A Pro + Ryzen 5 5600 + 16 GB DDR4, Kühle", 300.0
    ) is False
    assert _matches_office_pc(
        "NP=450€ i5 12400f, 16gb ddr4 ram, Asrock Mainboard", 250.0
    ) is False


# ============================================================
# 2. Neu identifiziertes Muster: "Aufrüstkit"/"Aufrüstbundle" (bare
#    Komponenten-Bundle ohne Gehäuse).
# ============================================================

def test_aufruestkit_bundle_varianten_matchen_nicht():
    for title, price in [
        (
            "Aufrüstkit Bundle AMD Ryzen 5 5500 AM4, Gigabyte MB A520M K V2 u. 16 GB DDR4",
            289.95,
        ),
        (
            "PC Aufrüstkit Bundle AMD Ryzen 5 3600 bis 32GB DDR4 mit ASRock B550 Pro4",
            219.0,
        ),
        (
            "PC Aufrüstkit Bundle Intel Core i5-12400F bis 64GB DDR4 mit GIGABYTE B760M H",
            289.0,
        ),
    ]:
        assert _matches_office_pc(title, price) is False, title


def test_aufruestbundle_varianten_matchen_nicht():
    assert _matches_office_pc(
        "Aufrüstbundle AMD Ryzen 5 5600GT GA A520M KV2 16GB DDR4 3200MHz neu ungeöffnet",
        250.0,
    ) is False
    assert _matches_office_pc(
        "TOP Aufrüstbundle AMD Ryzen 5 3400G GA 520M K V2 8GB DDR4 3200MHz neu", 159.0
    ) is False


# ============================================================
# 3. Sicherheitsprüfung: reale TRUE_POSITIVE-office_pc-Treffer aus
#    found.json bleiben unverändert erhalten (echte Preise verwendet).
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        (
            "ACEMAGIC 16'' AX16Pro Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM 512GB SSD Win11P",
            289.0,
        ),
        (
            "Büro PC Fujitsu Business Computer i5 8400 16GB RAM 512GB SSD Win11 Office 2024",
            259.0,
        ),
        ("Dell Optiplex 7060 Tower PC Core i5-8500 3GHz 16GB DDR4 Ram 512GB NVMe", 179.0),
        (
            "Fujitsu Esprimo D7010 Intel Core i7-10700 16GB RAM Business Desktop-PC",
            278.0,
        ),
        ("Lenovo ThinkPad X390 | 13,3\" | i5-8365U | 8 GB RAM | 512 GB SSD", 293.0),
        ("Office PC Fujitsu Esprimo P558/E85, Core i5 9400, 16GB DDR4 RAM", 100.0),
        (
            "Terra Business PC Core i5-8500 3,0GHz 8GB RAM 250GB SSD Win 10 Pro (mk)",
            109.90,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "office_pc", title


def test_grenzfall_bare_bundle_ohne_aufruest_signal_matcht_weiterhin():
    # Grenzfall (siehe Audit-Doku, P1/P2): "Bundle"/"Kit" allein wurden
    # bewusst NICHT ausgeschlossen -- kein eindeutiges Signalwort, echte
    # Komplettsystem-Angebote könnten "Bundle" ebenfalls im Titel tragen.
    # Diese Titel bleiben daher unverändert TRUE_POSITIVE, auch wenn sie
    # strukturell demselben Root-Cause-Verdacht unterliegen könnten --
    # das ist die bewusste Grenze dieses Fixes, kein Bug.
    r = evaluate(
        "MSI TOMAHAWK B450 mit RYZEN 5 3600 und 16gb ddr4 ram Kit", 220.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "office_pc"

    r2 = evaluate(
        "Bundle AMD Ryzen 5 3400G 4,2GHz, 16-32GB DDR4, LEISE, microATX, (Windows 11 SSD)",
        169.0,
        _rules_cfg(),
    )
    assert r2.matched is True
    assert r2.category == "office_pc"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
