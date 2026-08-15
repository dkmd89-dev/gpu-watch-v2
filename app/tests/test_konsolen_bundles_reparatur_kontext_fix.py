"""Regressionstest für den konsolen_bundles-Fix aus der Category-False-
Positive-Forensics-Fix-Queue (Manual-Review-Fall, Auftrag "Aktive False
Positives gezielt beheben", umgesetzt nach Nutzer-Vorschlag mit Korrektur
der Marker-Liste -- siehe app/rules/konsolen_bundles.yaml).

Hintergrund: bare "reparatur" wird jetzt kontextbewusst blockiert (Muster
identisch zu "spiele"/"ovp" in derselben Datei) -- nur wenn KEIN
Geräte-Marker (Speichergröße/Konsolenwort/Modellvariante/"ovp") im
gesamten Titel vorkommt. Bewusst OHNE Markennamen
("nintendo"/"playstation"/"xbox") und OHNE "slim"/"pro"/"bundle"/
"mit spiele" als Kontext -- beide waeren im bestaetigten Fehltreffer
selbst bereits vorhanden bzw. sind Teil der auslösenden Regel-eigenen
require_all_of-Gruppe und würden das Gate wirkungslos machen.

Real bestätigter Fehltreffer (docs/DASHBOARD_MATCH_FORENSICS.json):
"Playstation 5 PS4 PS5 Slim HDMI Port Nintendo Reparatur USB PRO" (50€),
matchte bisher als "PS4 Slim / Pro Bundle ★ Top-Deal" über "slim"+"pro"
(aus "PS5 Slim"/"USB PRO", nicht aus einer echten PS4-Modellvariante).

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


def _matches_kb(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "konsolen_bundles"


# ============================================================
# 1. Real bestätigter Fehltreffer -- muss jetzt blockiert werden.
# ============================================================

def test_ps5_hdmi_reparatur_matcht_nicht():
    assert _matches_kb(
        "Playstation 5 PS4 PS5 Slim HDMI Port Nintendo Reparatur USB PRO", 50.0
    ) is False


def test_ps4_reinigung_waermeleitpaste_reparatur_matcht_nicht():
    # Zusaetzlicher, im aktuellen Korpus beobachteter Fall desselben
    # Musters (nicht Teil der 19 formal gelabelten historischen FP,
    # aber identischer Root Cause -- Nebeneffekt desselben Fixes).
    assert _matches_kb(
        "PS4 & PS4 Slim – Reinigung, Wärmeleitpaste & Reparatur", 60.0
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: Marker-Liste bewusst OHNE Markennamen/
#    "slim"/"pro" -- Titel mit echtem Geräte-Marker bleiben erhalten,
#    auch wenn sie "reparatur" enthalten.
# ============================================================

def test_reparatur_mit_geraete_marker_matcht_weiterhin():
    for title, price in [
        ("Nintendo Switch 32GB Konsole, frisch repariert, neue Sticks", 130.0),
        ("PS4 Pro 1TB Reparatur durchgeführt, funktioniert einwandfrei, OVP", 100.0),
        ("Xbox One S 500GB Konsole repariert und getestet", 70.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


def test_reale_true_positives_ohne_reparatur_matchen_weiterhin():
    r = evaluate("Nintendo Switch 32GB Konsole mit Dock, Joy-Cons Neon Rot/Blau & OVP", 130.0, _rules_cfg())
    assert r.matched is True and r.category == "konsolen_bundles"
    r2 = evaluate("Xbox One S 500 GB Konsole mit Controller in OVP", 60.0, _rules_cfg())
    assert r2.matched is True and r2.category == "konsolen_bundles"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
