"""Regressionstest für die retro_konsolen-Erweiterung von
exclude_category_unless_also_contains um "system" (Claude-Session
2026-08-15, found.json-Vollanalyse Blast-Radius-Check).

Hintergrund: "system" ist als require_all_of-Gruppe-2-Signal bewusst
erhalten (rettet reale Bundles wie "Nintendo DS Handheld-System grün
(PAL) Touchscreen, Mikrofon, Kopfhöreranschluss", die über kein anderes
Gruppe-2-Wort verfügen), reicht aber auch zufällig, wenn "System" Teil
eines Spiel-UNTERTITELS ist (real bestätigt: "Metal Arms-Glitch in The
System (Sony PlayStation 2) PS2 Gebraucht", 10,99€, Top-Deal --
Einzelspiel, kein Gerät).

Systematischer Blast-Radius-Check gegen den vollen 2.474-Titel-Korpus
(found.json): von 3 Titeln, die AUSSCHLIESSLICH über "system" matchen
(kein anderes Gruppe-2-Wort), sind 2 echte Handheld-System-Konsolen
(beide enthalten "handheld") und genau der obige 1 Fehltreffer (enthält
kein "handheld"). 0 Kollisionen. Fix: identisches, bereits produktives
Muster wie "memory card"/"netzteil" in derselben Datei
(exclude_category_unless_also_contains), Kontextliste = bestehende
Gruppe-2-Marker plus "handheld".

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


def _matches_retro(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "retro_konsolen"


# ============================================================
# 1. Bekannter realer Fehltreffer -- muss jetzt blockiert werden.
# ============================================================

def test_bekannter_fehltreffer_metal_arms_matcht_nicht():
    assert _matches_retro(
        "Metal Arms-Glitch in The System (Sony PlayStation 2) PS2 Gebraucht", 10.99
    ) is False


# ============================================================
# 2. Weitere Varianten desselben Musters (Spieltitel mit "System" im
#    Untertitel/Titel, andere Plattformen) -- müssen ebenfalls blockiert
#    werden, obwohl sie nicht real im Korpus bestätigt sind (synthetische
#    Absicherung gegen dasselbe Muster).
# ============================================================

def test_weitere_varianten_desselben_musters_matchen_nicht():
    for title, price in [
        ("Beyond Good & Evil - Sony PlayStation 2 - System Shock Bundle", 15.0),
        ("Deus Ex: Invisible War - System Wars Edition - PS2", 12.0),
        ("Nintendo GameCube - Star Wars: Battle for Naboo - System Requirements PAL", 20.0),
    ]:
        assert _matches_retro(title, price) is False, title


# ============================================================
# 3. Echte Konsolentitel (Handheld-System) -- müssen weiterhin matchen.
# ============================================================

def test_echte_handheld_system_konsolen_matchen_weiterhin():
    for title, price in [
        (
            "Nintendo DS Handheld-System grün (PAL) Touchscreen, Mikrofon, Kopfhöreranschluss",
            40.0,
        ),
        (
            "Nintendo DS Lite Konvolut 3xHandheld-System USG-001 (2xSilber, 1x Grün)",
            105.99,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "retro_konsolen", title


# ============================================================
# 4. Echtes Bundle: "system" zusammen mit einem weiteren, unabhängigen
#    Gruppe-2-Marker -- darf durch den neuen Kontext-Mechanismus nicht
#    zerstört werden.
# ============================================================

def test_system_mit_zusaetzlichem_geraetekontext_matcht_weiterhin():
    r = evaluate(
        "Nintendo 64 Handheld-System Konsole mit Controller und Kabel", 60.0, _rules_cfg()
    )
    assert r.matched is True and r.category == "retro_konsolen"


# ============================================================
# 5. Grenzfall: "system" als Teilstring in einem zusammengesetzten Wort
#    (z.B. "Betriebssystem") darf ohnehin nie als eigenständiger Treffer
#    zählen (Wortgrenzen-Prüfung in _contains_term()) -- reine
#    Sicherheitsprüfung, kein neues Verhalten durch diesen Fix.
# ============================================================

def test_system_als_teilstring_in_zusammengesetztem_wort_kein_treffer():
    r = evaluate(
        "Nintendo 64 Konsole mit Ersatzbetriebssystem-Chip und Controller", 60.0, _rules_cfg()
    )
    assert r.matched is True and r.category == "retro_konsolen"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
