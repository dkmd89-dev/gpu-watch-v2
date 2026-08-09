"""Regressionstests für den retro_konsolen-"controller"-Ersatzsignale-Fix
(kontrollierter Review nach found.json-Audit, Priorität HOCH,
Option "präzise Ergänzung").

Hintergrund: "controller" stand bisher in jeder Geräte-Indikator-Gruppe
dieser Datei als eigenständig ausreichende Alternative zu "konsole"/
"gerät"/"system"/"netzteil" -- dadurch matchte jeder Standalone-
Controller-Verkauf mit Konsolen-Markennamen im Titel ebenfalls (41 von
190 sichtbaren found.json-Einträgen dieser Kategorie, u.a. "Nintendo 64
Controller" für 25EUR als Top-Deal).

Ein einfaches Entfernen von "controller" OHNE Ersatz wurde geprüft und
verworfen: es hätte zusätzlich 55 echte Konsole+Controller-Bundles ohne
das Wort "Konsole" im Titel zerstört.

Fix: "controller" entfernt, dafür die tatsächlich in den betroffenen
echten Bundle-Titeln vorkommenden Geräte-Signalwörter datenbasiert
ermittelt und ergänzt: "kabel", "slim", "fat", "komplett", "memory
card", "heimkonsole", "spielekonsole". Verifiziert gegen die realen
found.json-Titel: alle 41 bekannten Fehltreffer bleiben blockiert, 39
von 53 echten Bundles ohne "Konsole"-Wort werden gerettet (14
verbleibende, dokumentierte Restlücke, z.B. "Nintendo 64 mit
Controller" ohne weiteres Bundle-Signalwort).

Läuft gegen die echten, produktiven rules/*.yaml, analog zu
test_notebook_resell_gaming_fix.py."""
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


def _matches_retro(title, price=0.0):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "retro_konsolen"


# ============================================================
# 1. Vom Nutzer explizit vorgegebene Zielfälle
# ============================================================

def test_standalone_n64_controller_matcht_nicht():
    assert _matches_retro("Nintendo 64 Controller", 25.0) is False


def test_ps2_slim_controller_memory_card_matcht():
    assert _matches_retro("PS2 Slim + Controller + Memory Card", 50.0) is True


def test_n64_controller_kabel_matcht():
    assert _matches_retro("N64 + Controller + Kabel", 50.0) is True


def test_n64_konsole_mit_3x_controller_matcht():
    assert _matches_retro("Nintendo 64 Konsole + 3x Controller", 60.0) is True


# ============================================================
# 2. Positiv-/Negativtests pro neuem Signalwort
#    (Positiv: Signalwort vorhanden -> Bundle matcht.
#     Negativ: Signalwort UND jedes andere Signalwort fehlt -> matcht
#     weiterhin nicht, bleibt Standalone-Controller.)
# ============================================================

def test_signal_kabel_positiv():
    assert _matches_retro("Nintendo GameCube schwarz + Controller + Kabel") is True


def test_signal_kabel_negativ_ohne_jedes_signalwort():
    assert _matches_retro("Nintendo GameCube schwarz Controller") is False


def test_signal_slim_positiv():
    assert _matches_retro(
        "Sony PlayStation 2 Slim SCPH-77004 Silber PAL inkl. Controller"
    ) is True


def test_signal_slim_negativ_ohne_slim():
    assert _matches_retro("Sony PlayStation 2 SCPH-77004 Silber PAL inkl. Controller") is False


def test_signal_fat_positiv():
    assert _matches_retro(
        "Sony PlayStation 2 PS2 Fat + 2 Original Controller – funktioniert"
    ) is True


def test_signal_fat_negativ_ohne_fat():
    assert _matches_retro("Sony PlayStation 2 PS2 + 2 Original Controller") is False


def test_signal_komplett_positiv():
    assert _matches_retro(
        "Nintendo 64 / N64 + Controller + Spiel Tetris komplett"
    ) is True


def test_signal_komplett_negativ_ohne_komplett():
    assert _matches_retro("Nintendo 64 / N64 + Controller + Spiel Tetris") is False


def test_signal_memory_card_positiv():
    assert _matches_retro(
        "Sony PlayStation 2 Slim Controller Memory Card Midnight Club"
    ) is True


def test_signal_heimkonsole_positiv():
    # Kompositum-Variante von "konsole" -- bare "konsole" matcht wegen
    # Wortgrenzen ("(?<!\\w)konsole(?!\\w)") kein zusammengesetztes Wort.
    assert _matches_retro(
        "Nintendo 64 Heimkonsole schwarz, 3 Controller, AV-Kabel"
    ) is True


def test_signal_spielekonsole_positiv():
    assert _matches_retro("Sony PlayStation 1 Spielekonsole PS1 mit Controller") is True


def test_signal_spielekonsole_negativ_ohne_jedes_signalwort():
    assert _matches_retro("Sony PlayStation 1 PS1 mit Controller") is False


# ============================================================
# 3. Bekannte, verbleibende Fehltreffer bleiben blockiert
#    (Stichprobe aus den 41 verifizierten Fällen).
# ============================================================

def test_bekannte_fehltreffer_bleiben_blockiert():
    fps = [
        "Nintendo 64 Controller",
        "Playstation 2 PS2 Controller Dualshock 2 OVP",
        "ORIGINAL N64 CONTROLLER GRAU MIT OVP",
        "Gamecube Controller Schwarz",
        "2x N64 Controller",
        "Original Playstation 2 - PS2 DualShock Analog Controller - Black",
    ]
    for title in fps:
        assert _matches_retro(title, 0.0) is False, f"{title!r} haette NICHT matchen duerfen"


def test_zubehoer_paket_bleibt_blockiert():
    # Absicherung: "Zubehör Paket" bleibt auch mit den neuen
    # Geraete-Signalwoertern ausgeschlossen.
    assert _matches_retro(
        "Nintendo Konsolen Zubehör Paket Gamecube N64 Controller usw."
    ) is False


# ============================================================
# 4. Sicherheitsprüfung: reguläre Konsole+Controller-Bundles mit
#    explizitem "Konsole"-Wort (unverändertes Verhalten) matchen
#    weiterhin.
# ============================================================

def test_regulaeres_bundle_mit_konsole_wort_matcht_weiterhin():
    r = evaluate("Nintendo GameCube Konsole mit Controller und Kabeln", 60.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "retro_konsolen"


def test_reine_konsole_ohne_controller_matcht_weiterhin():
    r = evaluate("Nintendo 64 Konsole gebraucht", 60.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "retro_konsolen"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
