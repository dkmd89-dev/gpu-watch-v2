"""Regressionstest für den retro_konsolen-Fix: "komplett"/"spiel"/"spiele"
unter exclude_category_unless_also_contains, plus "emul"-Abkürzung
(Nutzer-Meldung 2026-08-15, found.json-Vollanalyse).

Hintergrund: "komplett" ist eine require_all_of-Gruppe-2-Alternative, ist
in der Praxis aber ein Zustandsbegriff ("vollständig/CIB"), der bei
EINZELSPIELEN mindestens genauso häufig vorkommt wie bei Konsolen (z.B.
"Phantasy Star Online... - Nintendo GameCube - komplett", "FIFA Football
2003 – PS1 – deutsche PAL-Version – komplett"). Blast-Radius-Check gegen
den vollen, aktuell sichtbaren found.json-Korpus: 20 Treffer ohne jeden
stärkeren Gerätemarker (alle real bestätigte Einzelspiel-/Zubehör-
Fehltreffer), 0 Kollisionen. Kontextliste enthält "controller" (bereits
bestehende Testerwartung: "Nintendo 64 / N64 + Controller + Spiel Tetris
komplett" soll weiterhin matchen, siehe
test_retro_konsolen_controller_signal_fix.py::test_signal_komplett_positiv).

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


def test_einzelspiele_ohne_geraet_matchen_nicht():
    for title in [
        "International Tennis Pro, PS2, Sony Playstation 2, Spiel komplett",
        "Nintendo Ds Spiel - Time Hollow - Selten - Komplett",
        "6 PS2 Spiele je 3€ oder 16€ komplett Sony Playstation 2",
        'PS2 Spiel "Oben" (Disney Pixar) - Komplett in Deutsch',
        "Hybrid - Sony PlayStation 1 / PS1 Spiel (Midas PAL) - KOMPLETT MIT ANLEITUNG TOP",
        "FIFA Football 2003 – PS1 – deutsche PAL-Version – komplett",
        "Phantasy Star Online: Episode III C.A.R.D.  - Nintendo GameCube - komplett  TOP",
        "Pokémon Stadium für Nintendo 64 - Komplett mit OVP & Transfer Pak",
        "3D Lemmings für Sony Playstation 1 (PSone) - komplett",
        "Der Herr der Ringe: Die zwei Türme | GameCube | Komplett",
        "Spider-Man 2 (Sony PlayStation 1) PS1 PS One - Komplett",
        "Nintendo 64 Expansion Pak NUS-007 mit Hebel NUS-012 Original N64 komplett OVP",
        "DINO CRISIS 2 (PlayStation 1 PS1 PSX) KOMPLETT",
    ]:
        r = evaluate(title, 30.0, _rules_cfg())
        assert not (r.matched and r.category == "retro_konsolen"), title


def test_emulator_handheld_abkuerzung_matcht_nicht():
    r = evaluate(
        "R36 Ultra X handheld Konsole, snes, nes, psp, Ps1 Spiele Emul", 55.0, _rules_cfg()
    )
    assert not (r.matched and r.category == "retro_konsolen")


def test_komplett_mit_controller_kontext_matcht_weiterhin():
    # Bestehende Testerwartung (test_retro_konsolen_controller_signal_fix.py)
    # darf durch diesen Fix nicht regressieren.
    r = evaluate(
        "Nintendo 64 / N64 + Controller + Spiel Tetris komplett", 0.0, _rules_cfg()
    )
    assert r.matched is True and r.category == "retro_konsolen"


def test_echte_konsolen_matchen_weiterhin():
    for title, price in [
        ("Sony PlayStation 1 Konsole – SCPH-1002 , 1 Controller, 2 Spiele", 49.0),
        ("Nintendo 64 Konsole mit Spiel, toller Zustand", 79.99),
        ("PS1 | 2 x Controller + 1 x Memory Card", 60.0),
        ("Nintendo 64 Konsole mit 2 Controller + Kabel", 70.0),
        (
            "Sony PlayStation 2 Slim SCPH-77004 PAL schwarz + 2 Controller, Memory Card 8MB",
            59.21,
        ),
        (
            "Sony PlayStation 1 Konsole Inkl. alle Kabel 2xController, sehr gut erhalten",
            90.0,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "retro_konsolen", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
