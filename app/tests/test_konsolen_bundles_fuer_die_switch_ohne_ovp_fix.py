"""Regressionstests für zwei konsolen_bundles-Fehltreffer (Nutzer-Meldung
2026-08-15, Live-Fehltreffer-Report):

1. "für die Switch" (Artikel zwischen "für" und Plattformname eingeschoben)
   -- wird vom bestehenden "für switch"/"für nintendo switch"-Schutz
   (exclude_category_unless_also_contains) NICHT erfasst, da
   matcher.py::_contains_term() die komplette Phrase als zusammenhaengenden
   Substring prueft. Real bestaetigt: "Luigis Mansion 2 HD für die Switch,
   Switch Lite, Switch2" (35€) -- matchte bisher ueber die Switch-Lite-
   Regel, die (anders als die Standard-Switch-Regel) gar keine eigene
   Geraete-Marker-Gruppe hat.

2. "ohne OVP"/"kein OVP"/"keine OVP" -- "ovp" ist in der Switch-Standard-
   und Xbox-One-Gruppe-2 bewusst als Positivsignal erhalten, die reine
   Wort-Praesenz-Pruefung erkennt aber keine Verneinung. Real bestaetigt:
   "Hogwarts Legacy - ohne OVP - Nintendo Switch" (25€), "Ring Fit
   Adventure (Nintendo Switch) keine OVP" (23€), "POKEMON SCHILD OHNE OVP
   NINTENDO SWITCH" (22€) -- alle Einzelspiele.

Beide Fixes nutzen ausschließlich den bereits produktiven
exclude_category_unless_also_contains-Mechanismus (kein neuer
Matcher-Code). Blast-Radius-Check gegen den vollen 2.474-Titel-Korpus
(found.json): 0 Kollisionen -- beide neuen Fixes entfernen ausschließlich
die real bestätigten Fehltreffer, kein einziger vorher matchender Titel
geht zusätzlich verloren.

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


def _matches_kb(title, price=0.0):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "konsolen_bundles"


# ============================================================
# 1. "für die Switch" -- muss jetzt blockiert werden, inkl. der Switch-
#    Lite-Regel (kategorieweiter Mechanismus).
# ============================================================

def test_luigis_mansion_fuer_die_switch_matcht_nicht():
    assert _matches_kb(
        "Luigis Mansion 2 HD für die Switch, Switch Lite, Switch2", 35.0
    ) is False


def test_weitere_fuer_die_switch_varianten_matchen_nicht():
    assert _matches_kb("Mario Kart 8 Deluxe für die Nintendo Switch - OVP", 30.0) is False
    assert _matches_kb("Zelda: Tears of the Kingdom für die Switch NEU OVP", 40.0) is False


# ============================================================
# 2. "ohne/kein/keine OVP" -- muss jetzt blockiert werden.
# ============================================================

def test_hogwarts_legacy_ohne_ovp_matcht_nicht():
    assert _matches_kb("Hogwarts Legacy - ohne OVP - Nintendo Switch", 25.0) is False


def test_weitere_negierte_ovp_faelle_matchen_nicht():
    assert _matches_kb("Ring Fit Adventure (Nintendo Switch) keine OVP", 23.0) is False
    assert _matches_kb("POKEMON SCHILD OHNE OVP NINTENDO SWITCH", 22.0) is False


# ============================================================
# 3. Sicherheitsprüfung: echte Konsolen/Bundles bleiben unverändert
#    erhalten -- inkl. Switch-Lite-Standalone-Verkäufe (die KEINEN
#    Geräte-Marker im Titel haben und daher besonders empfindlich auf
#    eine zu breite "für Plattform"-Erweiterung reagieren würden).
# ============================================================

def test_echte_switch_lite_standalone_verkaeufe_matchen_weiterhin():
    for title, price in [
        ("Nintendo Switch Lite", 90.0),
        ("Nintendo Switch Lite in Türkis", 70.0),
        ("Nintendo Switch Lite Blau", 94.23),
        ("Nintendo Switch Lite Gelb + 4 Spiele + Zubehör", 90.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


def test_echte_bundles_mit_ovp_bleiben_erhalten():
    # Bare "ovp" ohne Verneinung bleibt unveraendert ein gueltiges
    # Positivsignal (Auftragsvorgabe frueherer Fixes: OVP nicht entfernen).
    r = evaluate("Nintendo Switch mit OVP", 60.0, _rules_cfg())
    assert r.matched is True and r.category == "konsolen_bundles"

    r2 = evaluate("Microsoft Xbox One X 1TB Schwarz Inkl OVP", 55.0, _rules_cfg())
    assert r2.matched is True and r2.category == "konsolen_bundles"


def test_geraet_mit_fuer_die_switch_als_spec_angabe_matcht_weiterhin():
    # Analog zur bestehenden "für Plattform"-Ausnahme: ein echtes Gerät,
    # dessen Titel "für die Switch" nur als Kompatibilitäts-/Spec-Angabe
    # nennt, bleibt über den Geräte-Marker-Anker (*plattform_geraete_marker)
    # erhalten -- der neue Exclude blockiert nur, wenn KEIN Geräte-Marker
    # im Titel vorkommt.
    r = evaluate(
        "Nintendo Switch OLED Konsole mit Adapter für die Switch geeignet",
        90.0, _rules_cfg(),
    )
    assert r.matched is True and r.category == "konsolen_bundles"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
