"""Regressionstests für die Notebook-Recall-Optimierung, Cluster B
(2026-08-16): Preisgrenzen-Kalibrierung der "ThinkPad T14/X13 (Ryzen/
Modern)"-Regel ("Guter Preis"-Stufe).

Hintergrund (99-TRUE_POSITIVE-Recall-Forensics-Audit): 11 real bestätigte
TRUE_POSITIVE-ThinkPads (T14/X13/X390/L14 Gen 1, Preis 249-329€) matchten
trotz vollständig erfüllter require_all_of-Signale (thinkpad + Modellcode +
RAM-/SSD-Größe) nicht, weil die alte max_price-Grenze der "Guter Preis"-
Stufe (240€) sie ausschloss -- ein reines Preisgrenzen-Problem, kein
Signal-Gap.

Kalibrierung: neue Grenze = höchster real bestätigter TRUE_POSITIVE-Preis
(329,00€) aufgerundet auf 330€. Blast-Radius-Prüfung gegen den
vollständigen docs/DASHBOARD_MATCH_FORENSICS.json-Korpus (2306 Einträge,
ThinkPad-Signal + Preis 240-400€): exakt diese 11 Fälle, 0 zusätzliche
Kandidaten (weder TRUE_POSITIVE noch FALSE_POSITIVE noch UNCLEAR).
Vollkorpus-Vorher/Nachher-Diff bestätigt: genau 11 Routing-Änderungen,
keine unerwarteten Nebeneffekte.

Die "Top-Deal"-Stufe (180€) bleibt unverändert -- keine Datenbasis für
eine Änderung dort.

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
# Die 11 real bestätigten Cluster-B-Fälle matchen jetzt
# (Quelle: docs/DASHBOARD_MATCH_FORENSICS.json, TRUE_POSITIVE)
# ---------------------------------------------------------------

CLUSTER_B_FAELLE = [
    ("Laptop Lenovo ThinkPad T14 Gen1/Core i7 10510U/DDR4 24Gb/SSD 512", 300.0),
    (
        "✅ Lenovo ThinkPad L14 Gen 1 | 14\" | 16/32 GB RAM | 512 GB SSD | "
        "i5-10210U | Notebook | Laptop | MwSt | Garantie | Office | Schule | "
        "Uni | Microsoft Office Paket",
        329.0,
    ),
    ("Lenovo ThinkPad X390 | 13,3\" | i5-8365U | 8 GB RAM | 512 GB SSD", 293.0),
    (
        "Lenovo ThinkPad X390 Yoga | 13,3\" | i7-8665U | 16 GB RAM | 256 GB SSD",
        314.0,
    ),
    (
        "Laptop Lenovo ThinkPad X390 Yoga 13,3\" FHD 256GB SSD i7-8565U "
        "16GB RAM QWERTZ",
        280.0,
    ),
    (
        "NOTEBOOK LENOVO THINKPAD X13 YOGA GEN 1 INTEL CORE i5-10310U 4x "
        "1.7GHz 16GB RAM",
        274.0,
    ),
    (
        "Lenovo ThinkPad X13 Gen.1 13,3\" Intel i5-10310U 1,70GHz 16GB RAM "
        "256GB SSD Touch",
        249.0,
    ),
    (
        "Lenovo ThinkPad X13 Yoga Gen 1 i5-10310U 16GB RAM 512GB SSD Touch "
        "Windows 11",
        297.5,
    ),
    (
        "Laptop 2 in 1 Lenovo ThinkPad X13 Yoga Gen 1 i7-10510U 16GB RAM "
        "SSD 512GB Win 11",
        270.0,
    ),
    (
        "Lenovo ThinkPad T14 Gen1 i5 10310U 16GB RAM 256GB SSD 14\" FHD "
        "Win 11 Pro MwSt.",
        299.99,
    ),
    (
        "Lenovo Thinkpad T14 Gen 1 Core i5-10310U 1,7Ghz 16GB Ram 512GB M.2",
        259.0,
    ),
]


def test_cluster_b_alle_11_faelle_matchen_jetzt():
    for title, price in CLUSTER_B_FAELLE:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True, title
        assert r.category == "notebook_resell", title
        assert r.deal_rating == "Guter Preis", title


# ---------------------------------------------------------------
# Grenzfall: neue Obergrenze exakt bei 330€
# ---------------------------------------------------------------

def test_cluster_b_grenzfall_330_euro_matcht():
    r = evaluate(
        "Lenovo ThinkPad T14 Gen 1 i5-10310U 16GB RAM 512GB SSD", 330.00, _rules_cfg()
    )
    assert r.matched is True
    assert r.category == "notebook_resell"


def test_cluster_b_grenzfall_330_01_euro_matcht_nicht_mehr():
    r = evaluate(
        "Lenovo ThinkPad T14 Gen 1 i5-10310U 16GB RAM 512GB SSD", 330.01, _rules_cfg()
    )
    assert not (r.matched and r.category == "notebook_resell")


# ---------------------------------------------------------------
# Top-Deal-Stufe (180€) bleibt unveraendert
# ---------------------------------------------------------------

def test_top_deal_stufe_180_euro_unveraendert():
    r = evaluate(
        "Lenovo ThinkPad T14 Gen 1 i5-10310U 16GB RAM 512GB SSD", 180.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.deal_rating == "Top-Deal"


def test_181_euro_faellt_in_guter_preis_nicht_top_deal():
    r = evaluate(
        "Lenovo ThinkPad T14 Gen 1 i5-10310U 16GB RAM 512GB SSD", 181.0, _rules_cfg()
    )
    assert r.matched is True
    assert r.deal_rating == "Guter Preis"


# ---------------------------------------------------------------
# Bestehende, bereits vor dem Fix matchende Faelle (found.json,
# 130-239€) matchen weiterhin -- keine Regression der bisherigen
# Preisspanne durch die Grenzenanhebung.
# ---------------------------------------------------------------

def test_bestehende_reale_treffer_matchen_weiterhin():
    for title, price in [
        (
            "Lenovo ThinkPad L14 Gen 1 14\" FHD Intel Core i5-10210U 8GB RAM",
            130.0,
        ),
        ("Lenovo ThinkPad T490 i5-8365U 16GB RAM 256GB SSD", 149.0),
        ("Lenovo ThinkPad X13 Gen.1 13,3\" 16GB RAM 256GB SSD", 239.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "notebook_resell", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
