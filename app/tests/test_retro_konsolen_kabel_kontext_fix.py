"""Regressionstests für den retro_konsolen-"kabel"-Kontext-Fix
(Nutzer-Freigabe 2026-08-15, FALSE_POSITIVES_ANALYSE Teil 1 B).

Hintergrund: "kabel" ist als Gruppe-2-Geräte-Signal bewusst erhalten
(rettet reale Bundles wie "N64 + Controller + Kabel"), reicht aber auch
für Standalone-AV-/Anschlusskabel-Angebote OHNE jedes Gerät aus (4
bestätigte Fehltreffer). Identischer Mechanismus wie der bereits
bestehende "netzteil"-Fix: blockiert "kabel" nur, wenn im GESAMTEN Titel
kein Geräte-Kontextbegriff (controller/konsole/ersatzkonsole) vorkommt.

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


def _matches_retro(title, price=20.0):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "retro_konsolen"


def test_bestaetigte_kabel_only_fehltreffer_matchen_nicht_mehr():
    for title, price in [
        ("AV Kabel - Bild Kabel für N64, SNES und Gamecube!", 5.00),
        (
            "Sony Playstation PS1 PS2 3 Original AV TV Fernseh Chinch Anschluss Kabel Stecker",
            8.95,
        ),
        ("Mad Catz Universal HD Component AV-Kabel(PS2&3, Wii, Xbox) 1,8m", 25.00),
        ("Original Sony PlayStation AV-Kabel (PS1 / PS2 / PS3)", 10.00),
    ]:
        assert _matches_retro(title, price) is False, title


def test_kabel_mit_controller_kontext_matcht_weiterhin():
    # Bereits durch test_retro_konsolen_controller_signal_fix.py abgedeckte
    # Faelle, hier zusaetzlich als Sicherheitspruefung gegen den neuen
    # Exclude: "controller" im Titel ist ein erlaubter Kontextbegriff.
    assert _matches_retro("N64 + Controller + Kabel", 50.0) is True
    assert _matches_retro("Nintendo GameCube schwarz + Controller + Kabel") is True


def test_kabel_mit_konsole_kontext_matcht_weiterhin():
    assert _matches_retro("N64 Konsole komplett mit Kabel und Controller", 45.0) is True


def test_bekannte_grenzfaelle_analyse_teil_2_werden_mitblockiert():
    # Bewusst in Kauf genommene Restluecke (siehe Analyse Teil 2, Faelle
    # #36/#39): lexikalisch nicht von den bestaetigten Kabel-FP
    # unterscheidbar, obwohl die Analyse sie tendenziell als echte
    # Verkaeufe einstuft.
    assert _matches_retro("Verkaufe Playstation 2 Mit Kabel und spiele", 85.0) is False
    assert _matches_retro("Nintendo 64 / N64 + Kabel", 50.0) is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
