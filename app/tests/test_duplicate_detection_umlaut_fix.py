"""Regressionstests für den Umlaut-Fix in duplicate_detection.normalize_title()
(STATUS.md Datenqualität Nr. 11, Ruleset-Qualitätssystem, 2026-08-14).

Hintergrund: `_NON_ALNUM_RE` ersetzte deutsche Umlaute (ä/ö/ü/ß) durch ein
Leerzeichen statt sie zu erhalten -- "Röhrenfernseher" wurde zu
"r hrenfernseher". Jede fingerprint-basierte matcher.evaluate()-
Revalidierung (u.a. app/rule_coverage.py::_is_still_valid()) konnte dadurch
nie mehr gegen Umlaut-haltige match/require_all_of-Begriffe matchen, egal
ob der Titel inhaltlich passen würde (19 von 355 Regeln in 4 Kategorien
betroffen). Fix: Umlaute bleiben erhalten (erlaubte Zeichenklasse erweitert),
matcher.evaluate() wendet ohnehin nur title.lower() an und verändert Umlaute
nie -- der Fingerprint muss daher exakt in diesem Format vorliegen."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from duplicate_detection import normalize_title, find_duplicate
from matcher import load_rules, evaluate
from price_history import make_price_point

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


def test_umlaute_bleiben_im_fingerprint_erhalten():
    assert normalize_title("Röhrenfernseher Grundig 51cm") == "röhrenfernseher grundig 51cm"
    assert normalize_title("Yamaha Verstärker RX-V565") == "yamaha verstärker rx v565"
    assert normalize_title("Für Küche geeignetes Gerät") == "für küche geeignetes gerät"
    assert normalize_title("Straße 12, Preis 50€") == "straße 12 preis 50"


def test_sonderzeichen_werden_weiterhin_entfernt():
    # Bestehendes Verhalten (Ausrufezeichen, Klammern etc.) darf nicht regressieren.
    assert normalize_title("RTX 3060 12GB!! (defekt)") == "rtx 3060 12gb defekt"


def test_fingerprint_matcht_jetzt_gegen_umlauthaltige_regeln():
    # Vorher (kaputt): "r hrenfernseher..." matchte NIE gegen die
    # umlauthaltigen match-Begriffe in vintage_elektronik.yaml.
    fp = normalize_title("Röhrenfernseher Grundig 51cm gut erhalten")
    r = evaluate(fp, 20.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "vintage_elektronik"
    assert r.price_history_model == "roehrenfernseher"

    fp2 = normalize_title("Yamaha Verstärker RX-V565 AV-Receiver")
    r2 = evaluate(fp2, 50.0, _rules_cfg())
    assert r2.matched is True
    assert r2.category == "vintage_elektronik"


def test_find_duplicate_erkennt_umlauthaltige_cross_postings_weiterhin():
    # find_duplicate() vergleicht wortstellungs-unabhaengig -- muss fuer
    # Umlaut-Titel identisch funktionieren wie fuer ASCII-Titel.
    fp_a = normalize_title("Röhrenfernseher Grundig 51cm")
    fp_b = normalize_title("Grundig 51cm Röhrenfernseher")
    existing = [make_price_point(price=20.0, source="ebay", model="roehrenfernseher", fingerprint=fp_a)]
    dup = find_duplicate(model="roehrenfernseher", price=20.0, fingerprint=fp_b, existing_points=existing)
    assert dup is not None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
