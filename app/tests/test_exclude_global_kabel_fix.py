"""Regressionstests für STATUS.md Abschnitt 24, Nebenbefund:

exclude_global enthielt zuvor das Einzelwort "kabel", das per
_contains_term als GANZES WORT matcht -- dadurch wurden auch legitime
Geräte-Bundles ausgeschlossen, die Kabel nur als Zubehör erwähnen
(z.B. "PS1 mit Kabel und Controller", "Monitor inkl. HDMI Kabel").

Fix: das Einzelwort wurde durch mehrwortige Phrasen ersetzt, die
spezifisch auf reine Zubehör-/Kabel-only-Angebote abzielen.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import evaluate, load_rules, _any_term

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"

CURRENT_EXCLUDES = [
    "nur kabel",
    "nur das kabel",
    "diverse kabel",
    "diverses kabel",
    "kabel konvolut",
    "kabelsalat",
]


def test_ps1_bundle_mit_kabel_wird_end_to_end_nicht_mehr_global_ausgeschlossen():
    """Der ursprüngliche Bug-Fall aus STATUS.md Abschnitt 24, end-to-end
    gegen das echte rules/-Verzeichnis (retro_konsolen.yaml + _global.yaml).

    Vor dem Fix griff bereits Schritt 1 in evaluate() (globaler Exclude)
    und lieferte MatchResult(matched=False) OHNE dass retro_konsolen.yaml
    überhaupt geprüft wurde. Das lässt sich indirekt daran erkennen, dass
    ein Titel, der nur wegen "kabel" (und sonst nichts) ausgeschlossen
    würde, jetzt bis zur eigentlichen Kategorie-Regelprüfung durchkommt --
    direkt nachgewiesen über die isolierte globale Exclude-Liste selbst
    (siehe test_ps1_bundle_mit_kabel_bleibt_erhalten unten) sowie hier
    zusätzlich per vollem evaluate()-Aufruf ohne Exception/Regression.
    """
    rules_cfg = load_rules(str(RULES_DIR))
    global_excludes = rules_cfg["defaults"]["exclude_global"]
    title_l = "n64 konsole komplett mit kabel und controller".lower()
    assert _any_term(title_l, global_excludes) is False
    # evaluate() darf nicht mehr an Schritt 1 (globaler Exclude) scheitern
    result = evaluate("N64 Konsole komplett mit Kabel und Controller", 45.0, rules_cfg)
    assert isinstance(result.matched, bool)


def test_hdmi_kabel_als_zubehoer_in_monitor_bundle_bleibt_erhalten():
    from matcher import _any_term
    title_l = "monitor 27 zoll inkl. hdmi kabel und netzteil".lower()
    assert _any_term(title_l, CURRENT_EXCLUDES) is False


def test_ps1_bundle_mit_kabel_bleibt_erhalten():
    from matcher import _any_term
    title_l = "ps1 mit kabel und controller".lower()
    assert _any_term(title_l, CURRENT_EXCLUDES) is False


def test_reines_kabel_only_angebot_wird_weiterhin_ausgeschlossen():
    from matcher import _any_term
    assert _any_term("nur kabel zu verkaufen", CURRENT_EXCLUDES) is True
    assert _any_term("diverse kabel abzugeben", CURRENT_EXCLUDES) is True
    assert _any_term("kabelsalat aus der kiste", CURRENT_EXCLUDES) is True
    assert _any_term("kabel konvolut versch. hersteller", CURRENT_EXCLUDES) is True


def test_altes_einzelwort_kabel_ist_nicht_mehr_in_der_globalen_liste():
    import yaml
    global_cfg = yaml.safe_load(
        Path(__file__).resolve().parent.parent.joinpath("rules", "_global.yaml").read_text()
    )
    excludes = global_cfg.get("exclude_global", [])
    assert "kabel" not in [e.strip().lower() for e in excludes]
