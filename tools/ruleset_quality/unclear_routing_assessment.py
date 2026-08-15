"""Forensische Klassifikation der 35 historischen UNCLEAR-Faelle.

Betrifft AUSSCHLIESSLICH Faelle mit historischem Ground-Truth-Verdict
UNCLEAR (siehe docs/DASHBOARD_MATCH_FORENSICS.json) -- niemals
TRUE_POSITIVE/FALSE_POSITIVE-Faelle (die werden bereits von
forensics_false_positives.py/ground_truth_routing_assessment.py
behandelt). Baut auf denselben Bausteinen auf:

  - forensics_false_positives.extract_cases()  liefert die 35
    FpCandidateCase-Objekte (bereits vorhandene current_routing-Ebene via
    evaluate(), dem echten Produktionspfad -- keine zweite Matching-Engine)
  - docs/DASHBOARD_MATCH_FORENSICS.json (require_all_of_detail,
    *_excludes_checked/-present) liefert die ROHEN Signal-Daten, aus denen
    die Evidenzeintraege gebaut werden

Kernproblem der 35 UNCLEAR-Faelle (siehe entry["reason"] im Forensik-
Snapshot): das automatisierte require_all_of-Kriterium wurde bei JEDEM der
35 Faelle ausschliesslich ueber ein generisches Sekundaersignal ("ovp",
"set" oder "bundle") erfuellt, ohne eine staerkere Alternative ("konsole",
"system") im selben Treffer -- die automatisierte Erkennung kann daher
nicht unterscheiden, ob der Titel tatsaechlich eine Konsole beschreibt oder
nur ein Spiel/Zubehoerteil mit generischem Verpackungshinweis ("OVP"=
Originalverpackung sagt nichts ueber den Produkttyp aus). Diese
Modul-Klassifikation liest deshalb den VOLLEN Titeltext (nicht nur das
generische Hit-Signal) und bewertet, ob der Rest des Titels ein
Konsolen-spezifisches Merkmal (Modellnummer, Speichergroesse, explizites
Wort "Konsole"/"System", Hardware-Reparaturkontext) oder ein
Spiel-/Zubehoer-Merkmal (Spieltitel als Eigenname, "Controller"/"Joy-Con"
ohne Konsolenbezug) traegt.

Epistemische Grundregel (identisch zu forensics_false_positives.py):
KEINE automatische/heuristische Klassifikation. Die Zuordnung
listing_id -> (status, confidence, pattern, evidence) in
_UNCLEAR_ASSESSMENTS ist eine kuratierte, dokumentierte Tabelle -- jeder
Eintrag stammt aus tatsaechlich im Titel/Forensik-Snapshot vorhandenem
Text, nichts wird erfunden. Ein alleiniges Keyword (z.B. "bundle") wird
NIE als hinreichende Evidenz behandelt (siehe Auftrag "WICHTIGE
SEMANTIK") -- entscheidend ist immer der volle Titelkontext.

GROUND_TRUTH_CONFLICT wird in diesem Batch bewusst NICHT vergeben: anders
als bei den 19 bestaetigten FALSE_POSITIVE-Faellen (wo ein Mensch bereits
ein Urteil gefaellt hatte, das ggf. widerlegt werden kann) war der
historische Status hier "UNCLEAR" = per Definition kein gefaelltes
Urteil, sondern eine mechanische Beschraenkung des Forensik-Tools (siehe
oben). Eine klare Titel-Lesung loest diese Beschraenkung auf -- das ist
LIKELY_TRUE_POSITIVE/LIKELY_FALSE_POSITIVE, kein Konflikt mit einem
vorherigen Urteil. GROUND_TRUTH_CONFLICT bliebe nur fuer den (hier nicht
eingetretenen) Fall reserviert, dass die aktuelle Routing-Entscheidung
selbst der Beleg waere.

Sonderfall Nintendo DS Lite (retro_konsolen, siehe _UNCLEAR_ASSESSMENTS):
lexikalisch (fast) identisch zum bereits bestaetigten FALSE_POSITIVE
"Nintendo DS Lite Handheld-System Weiss Touchscreen inkl. 4 Spiele"
(forensics_false_positives._MANUAL_ASSESSMENT_OVERRIDES, url
.../398266334210) -- genau dort wurde am 2026-08-15 dokumentiert, dass
KEIN zuverlaessiges lexikalisches Unterscheidungsmerkmal zwischen diesem
bestaetigten FP und den mutmasslich echten "Handheld-System"-Treffern
gefunden wurde. Diese Erkenntnis wird hier NICHT durch eine neue Heuristik
ueberschrieben -- bleibt MANUAL_REVIEW/LOW.

Schreibt/aendert NIEMALS app/rules/*.yaml, docs/DASHBOARD_MATCH_FORENSICS.json
oder sonstige Produktionsdateien. Baut KEINE zweite Matching-Engine.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import forensics_false_positives as ffp
from .common import REPORTS_DIR, current_ruleset_signature, load_current_rules
from .label_store import FORENSICS_SOURCE

REPORT_JSON = REPORTS_DIR / "unclear_routing_assessment.json"
REPORT_MD = REPORTS_DIR / "unclear_routing_assessment.md"

# Bekannter Referenzstand (siehe forensics_false_positives.KNOWN_REFERENCE_COUNTS):
# 35 UNCLEAR-Faelle. Wird bei jedem Lauf gegengeprueft.
KNOWN_UNCLEAR_COUNT = 35

STATUS_LIKELY_TRUE_POSITIVE = "LIKELY_TRUE_POSITIVE"
STATUS_LIKELY_FALSE_POSITIVE = "LIKELY_FALSE_POSITIVE"
STATUS_GROUND_TRUTH_CONFLICT = "GROUND_TRUTH_CONFLICT"
STATUS_MANUAL_REVIEW = "MANUAL_REVIEW"

CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"

ACTION_NO_ACTION = "no_action"
ACTION_REGRESSION_TEST = "regression_test"
ACTION_RULESET_REVIEW = "ruleset_review"
ACTION_GROUND_TRUTH_REVIEW = "ground_truth_review"
ACTION_MANUAL_REVIEW = "manual_review"

# Auftrag "RECOMMENDED_ACTION": feste 1:1-Zuordnung, keine Heuristik.
_STATUS_TO_ACTION = {
    STATUS_LIKELY_TRUE_POSITIVE: ACTION_REGRESSION_TEST,
    STATUS_LIKELY_FALSE_POSITIVE: ACTION_RULESET_REVIEW,
    STATUS_GROUND_TRUTH_CONFLICT: ACTION_GROUND_TRUTH_REVIEW,
    STATUS_MANUAL_REVIEW: ACTION_MANUAL_REVIEW,
}


def _ev(type_: str, signal: str, strength: str, interpretation: str) -> dict:
    return {
        "type": type_,
        "signal": signal,
        "strength": strength,
        "interpretation": interpretation,
    }


# Wiederkehrende Begruendungsmuster (fuer die "Root Cause"-Spalte im
# Abschlussbericht, siehe Auftrag "TOP-Kandidaten"). Rein deskriptiv, kein
# Bezug zu forensics_false_positives.ROOT_CAUSE_* (dort geht es um
# YAML-Fix-Typen, hier nur um die Titel-Lesung).
PATTERN_ACCESSORY_NO_CONSOLE = "accessory_without_console_marker"
PATTERN_GAME_TITLE_ONLY = "single_game_title_without_console_marker"
PATTERN_CONSOLE_EXPLICIT = "console_confirmed_by_explicit_model_or_keyword"
PATTERN_CONSOLE_HARDWARE_CONTEXT = "console_confirmed_by_hardware_repair_context"
PATTERN_LEXICAL_AMBIGUITY_VS_CONFIRMED_FP = "lexically_ambiguous_vs_confirmed_false_positive"

_GENERIC_HIT_CONTEXT_EVIDENCE = _ev(
    "context",
    "require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt",
    "weak",
    "Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze "
    "(kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- "
    "das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.",
)

# Kuratierte, dokumentierte Klassifikation aller 35 UNCLEAR-Faelle (Auftrag
# "35 UNCLEAR-Faelle systematisch forensisch klassifizieren"). Key =
# listing_id (stabile Case-ID, siehe Auftrag "Datenintegritaet" aus dem
# vorherigen Schritt). Jeder Eintrag: (status, confidence, pattern,
# evidence-Liste). Evidence stammt ausschliesslich aus dem tatsaechlichen
# Titeltext bzw. dem Forensik-Snapshot -- siehe Moduldocstring.
_UNCLEAR_ASSESSMENTS: dict[str, tuple[str, str, str, list[dict]]] = {
    "https://www.kleinanzeigen.de/s-anzeige/2x-nintendo-switch-2-pro-controller-neu-ovp/3480514740-279-924": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "2x ... Pro Controller", "strong",
                "Titel nennt ausschliesslich zwei Controller -- kein Konsolen-Kernprodukt."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong",
                "Weder Modellbezeichnung noch Speichergroesse noch das Wort 'Konsole'/'System' vorhanden."),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/137596202274": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Bayonetta & Vanquish 10th Anniversary Bundle", "strong",
                "Zwei genannte Spieltitel als Jubilaeums-Doppelpack -- kein Konsolen-Kernprodukt."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong",
                "'Bundle' bezieht sich hier auf die zwei Spiele, nicht auf ein Konsolenpaket."),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/298569642364": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "HORI Split Pad Pro ... Controller", "strong",
                "HORI Split Pad Pro ist ein bekanntes Dritthersteller-Controller-Zubehoer; "
                "Titel nennt explizit 'Controller', keine Konsole."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong",
                "Kein Hinweis auf ein verkauftes Konsolengehaeuse."),
            _ev("context", "current_routing_status=A_SAME_WRONG_CATEGORY", "strong",
                "Faellt unter den AKTUELLEN Produktivregeln weiterhin in dieselbe Kategorie -- "
                "live aktiver Fehltreffer-Kandidat, nicht nur historisch."),
        ],
    ),
    "https://www.ebay.de/itm/278262114576": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Metroid Prime Remastered", "strong",
                "Genannter Einzel-Spieltitel als Eigenname -- exakt das im Forensik-reason "
                "beschriebene 'Minecraft'-Beispielszenario."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/366595666798": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "1TB", "strong",
                "Speichergroessen-Marker -- typisch fuer ein Konsolenangebot, nicht fuer ein Spiel."),
            _ev("positive_signal", "Microsoft Xbox One X", "strong",
                "Hersteller+Modellname als Kernprodukt des Angebots."),
            _ev("negative_signal", "Ohne Controller", "weak",
                "Beschreibt nur fehlendes Zubehoer zur Konsole, nicht das verkaufte Hauptprodukt."),
        ],
    ),
    "https://www.ebay.de/itm/398090521820": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Nintendo Switch Pro Controller - Monster Hunter Rise Sunbreak Edition", "strong",
                "Sonderedition eines Pro Controllers -- Zubehoer, keine Konsole genannt."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/407131833744": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Pokémon Purpur", "strong", "Genannter Einzel-Spieltitel als Eigenname."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/267751986716": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Controller Joy-Con Neon-Gruen / Neon-Pink 2er", "strong",
                "Explizit zwei Joy-Con-Controller -- Zubehoer, keine Konsole."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/800482418310": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Minecraft", "strong",
                "Identisch zum im Forensik-reason genannten Beispiel -- Spieltitel als Eigenname."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/287514519935": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "1. Generation", "strong", "Modellgenerations-Angabe -- konsolenspezifisch."),
            _ev("positive_signal", "Neon Blau/Rot", "medium", "Farbangabe typisch fuer ein Konsolengehaeuse."),
            _ev("positive_signal", "Kaufbeleg", "medium",
                "Kaufbeleg-Erwaehnung passt zum Verkauf eines Geraets, nicht eines Spiels."),
        ],
    ),
    "https://www.ebay.de/itm/407120679305": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Pro Controller NSWITCH 2", "strong", "Zubehoer, keine Konsole genannt."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-2-gamecube-controller-ovp-neu/3480875199-227-2761": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "GameCube Controller", "strong",
                "Retro-Stil-Controller-Zubehoer fuer Switch 2, keine Konsole im Titel."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/407132075434": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "GameCube Controller – Nintendo Classics", "strong",
                "Identisches Muster zum Schwesterfall (siehe .../3480875199) -- Controller-Zubehoer."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/267751985916": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Controller - Joy-Con 2er-Set", "strong",
                "Explizit Joy-Con-Controller-Set -- Zubehoer, keine Konsole."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-grau-bundle-neue-sticks-kein-drift-extras-/3480736743-279-9668": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_MEDIUM,
        PATTERN_CONSOLE_HARDWARE_CONTEXT,
        [
            _ev("positive_signal", "Neue Sticks (Kein Drift)", "strong",
                "Analogstick-Drift ist ein bekanntes physisches Konsolen-/Joy-Con-Hardwareproblem -- "
                "kann sich nicht auf ein reines Spiel beziehen, setzt echte Hardware voraus."),
            _ev("positive_signal", "Bundle + Extras", "medium", "Kein einzelner Spieltitel genannt."),
            _ev("negative_signal", "kein explizites Wort 'Konsole'/'System' oder Speichergroesse", "medium",
                "Deshalb MEDIUM statt HIGH -- Hardwarekontext ist stark, aber kein direkter "
                "Konsolen-Begriff vorhanden."),
        ],
    ),
    "https://www.ebay.de/itm/188766880820": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "HAC-001(-01)", "strong", "Offizielle Nintendo-Switch-Modellnummer."),
            _ev("positive_signal", "32GB", "strong", "Speichergroessen-Marker der Basis-Switch."),
            _ev("positive_signal", "Handheld-Spielekonsole", "strong", "Explizites Wort 'Spielekonsole' im Titel."),
        ],
    ),
    "https://www.ebay.de/itm/298572812276": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_MEDIUM,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "Komplett Set", "medium",
                "Kein Spieltitel genannt -- 'Komplett Set' ohne Eigenname deutet auf ein "
                "vollstaendiges Konsolenpaket hin."),
            _ev("negative_signal", "kein explizites Wort 'Konsole'/'System' oder Speichergroesse", "medium",
                "Deshalb MEDIUM statt HIGH -- 'Set' bleibt fuer sich genommen generisch."),
        ],
    ),
    "https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-neon-bundle-neue-sticks-kein-drift-extras/3480680031-279-9668": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_MEDIUM,
        PATTERN_CONSOLE_HARDWARE_CONTEXT,
        [
            _ev("positive_signal", "Neue Sticks (Kein Drift!)", "strong",
                "Identisches Hardware-Reparatur-Signal wie beim Schwesterfall (siehe "
                ".../3480736743) -- Analogstick-Drift ist konsolenspezifisch."),
            _ev("positive_signal", "Bundle + Extras", "medium", "Kein einzelner Spieltitel genannt."),
            _ev("negative_signal", "kein explizites Wort 'Konsole'/'System' oder Speichergroesse", "medium", ""),
        ],
    ),
    "https://www.ebay.de/itm/128017856305": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_MEDIUM,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "OLED Joy-Con Set", "strong", "Explizit ein Joy-Con-Set -- Zubehoer."),
            _ev("positive_signal", "mit Handschlaufaufen", "medium", "Handschlaufen sind Joy-Con-Zubehoer."),
            _ev("negative_signal", "Pokemon Scarlet & Violet als genannter Spieltitel", "medium",
                "Zusaetzliches Spiel im Bundle, kein Konsolenhinweis."),
            _ev("context", "current_routing_status=A_SAME_WRONG_CATEGORY", "strong",
                "Faellt unter den AKTUELLEN Produktivregeln weiterhin in dieselbe Kategorie -- "
                "live aktiver Fehltreffer-Kandidat. MEDIUM statt HIGH, da 'Set' theoretisch auch "
                "ein Konsolenpaket bezeichnen koennte."),
        ],
    ),
    "https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-oled-modell-weiss-komplett-mit-ovp/3480437137-279-8400": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "OLED Modell", "strong", "Benennt explizit das Konsolenmodell."),
            _ev("positive_signal", "Komplett", "medium", "Verstaerkt den Eindruck eines vollstaendigen Geraets."),
        ],
    ),
    "https://www.ebay.de/itm/336734053355": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Pro Controller ... kaum genutzt", "strong", "Zubehoer, keine Konsole."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/318646020850": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Pro Controller Original", "strong", "Zubehoer, keine Konsole."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-pro-controller-in-ovp/3480100632-279-1186": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Pro Controller in OVP", "strong", "Zubehoer, keine Konsole."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/286899614096": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_ACCESSORY_NO_CONSOLE,
        [
            _ev("positive_signal", "Pro Controller, TOP Zustand", "strong", "Zubehoer, keine Konsole."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/188763698665": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "Spielkonsole", "strong", "Explizites Wort 'Spielkonsole' im Titel."),
        ],
    ),
    "https://www.ebay.de/itm/188763696701": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "Spielkonsole", "strong",
                "Identisches Muster zum Schwesterfall (siehe .../188763698665)."),
        ],
    ),
    "https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-sports-inkl-12-in-1-zubehoer-set/3480799134-227-2661": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Nintendo Switch Sports", "strong", "Genannter Spieltitel."),
            _ev("positive_signal", "12-in-1 Zubehör Set", "strong", "Explizit Zubehoer-Set, keine Konsole."),
        ],
    ),
    "https://www.ebay.de/itm/298572811262": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "V1", "strong", "Modellgenerations-Angabe."),
            _ev("positive_signal", "HAC-001", "strong", "Offizielle Nintendo-Switch-Modellnummer."),
            _ev("positive_signal", "Komplett", "medium", ""),
        ],
    ),
    "https://www.kleinanzeigen.de/s-anzeige/pok-mon-let-s-go-evoli-nintendo-switch-ovp-komplett/3480723859-227-3213": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_MEDIUM,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Pokémon Let's Go Evoli!", "strong", "Genannter Einzel-Spieltitel."),
            _ev("negative_signal", "'komplett' vermutlich CIB-Bezeichnung fuers Spiel, nicht Konsolenhinweis",
                "weak", "Deshalb MEDIUM statt HIGH -- Restambiguitaet durch das Wort 'komplett'."),
        ],
    ),
    "https://www.ebay.de/itm/327297670888": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Read Dead Redemption 1+2 ... Steelbook Bundle", "strong",
                "Zwei genannte Spieltitel in Steelbook-Sonderverpackung -- kein Konsolen-Kernprodukt."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _ev("context", "current_routing_status=A_SAME_WRONG_CATEGORY", "strong",
                "Faellt unter den AKTUELLEN Produktivregeln weiterhin in dieselbe Kategorie -- "
                "live aktiver Fehltreffer-Kandidat."),
        ],
    ),
    "https://www.ebay.de/itm/298566727139": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "STAR FOX", "strong", "Genannter Einzel-Spieltitel, Haendlerverkauf."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/227468705699": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Star Fox", "strong",
                "Identisches Muster zum Schwesterfall (siehe .../298566727139)."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/800481313890": (
        STATUS_LIKELY_FALSE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_GAME_TITLE_ONLY,
        [
            _ev("positive_signal", "Super Smash Bros. Ultimate", "strong", "Genannter Einzel-Spieltitel."),
            _ev("negative_signal", "kein Konsolen-/Speichergroessen-Marker im Titel", "strong", ""),
            _GENERIC_HIT_CONTEXT_EVIDENCE,
        ],
    ),
    "https://www.ebay.de/itm/377405800415": (
        STATUS_LIKELY_TRUE_POSITIVE,
        CONFIDENCE_HIGH,
        PATTERN_CONSOLE_EXPLICIT,
        [
            _ev("positive_signal", "1 TB", "strong", "Speichergroessen-Marker."),
            _ev("negative_signal", "+ 1 Controller", "weak",
                "Zubehoer-Ergaenzung zur Konsole, nicht das Hauptprodukt selbst."),
        ],
    ),
    "https://www.ebay.de/itm/318701631164": (
        STATUS_MANUAL_REVIEW,
        CONFIDENCE_LOW,
        PATTERN_LEXICAL_AMBIGUITY_VS_CONFIRMED_FP,
        [
            _ev("context", "Titelmuster 'Handheld-System'", "strong",
                "Lexikalisch (fast) identisch zum bereits bestaetigten FALSE_POSITIVE "
                "'Nintendo DS Lite Handheld-System Weiss Touchscreen inkl. 4 Spiele' "
                "(forensics_false_positives._MANUAL_ASSESSMENT_OVERRIDES, "
                "url=.../398266334210)."),
            _ev("context", "bereits dokumentierte Vorpruefung (2026-08-15)", "strong",
                "Fuer genau diesen Fall wurde bereits festgestellt: 'kein lexikalisches "
                "Unterscheidungsmerkmal zwischen dem bestaetigten FP und den mutmasslich "
                "echten Treffern gefunden' (siehe active_fp_fix_progress.md). Diese "
                "Erkenntnis wird hier NICHT durch eine neue Heuristik ueberschrieben."),
        ],
    ),
}


def _match_path(category: str | None, rule: str | None) -> str:
    return ffp._match_path(category, rule)


def build_case(candidate: "ffp.FpCandidateCase") -> dict:
    override = _UNCLEAR_ASSESSMENTS.get(candidate.listing_id)
    if override is None:  # pragma: no cover -- Sicherheitsnetz, sollte fuer die bekannten 35 nie greifen
        status, confidence, pattern, evidence = (
            STATUS_MANUAL_REVIEW,
            CONFIDENCE_LOW,
            "unassessed",
            [
                _ev(
                    "context",
                    "kein kuratiertes Assessment vorhanden",
                    "weak",
                    "Neuer/unbekannter UNCLEAR-Fall ohne dokumentierte Bewertung -- Auftragsregel "
                    "'Bei LOW: bevorzugt MANUAL_REVIEW' greift als sicherer Default.",
                )
            ],
        )
    else:
        status, confidence, pattern, evidence = override

    return {
        "case_id": candidate.listing_id,
        "title": candidate.title,
        "price": candidate.price,
        "historical_ground_truth": {
            "verdict": candidate.ground_truth_verdict,
            "category": candidate.stored_category,
            "rule": candidate.stored_rule,
        },
        "current_routing": {
            "category": candidate.current_category,
            "rule": candidate.current_rule,
            "match_state": candidate.match_state,
            "routing_status": candidate.routing_status,
        },
        "assessment": {"status": status},
        "confidence": confidence,
        "evidence": evidence,
        "root_cause_pattern": pattern,
        "match_path": f"{_match_path(candidate.stored_category, candidate.stored_rule)} -> "
        f"{_match_path(candidate.current_category, candidate.current_rule) if candidate.current_category != 'KEIN_TREFFER' else 'KEIN_TREFFER'}",
        "recommended_action": _STATUS_TO_ACTION[status],
    }


def _empty_category_counts() -> dict:
    return {
        "unclear_count": 0,
        "likely_true_positive": 0,
        "likely_false_positive": 0,
        "ground_truth_conflict": 0,
        "manual_review": 0,
    }


_STATUS_TO_CATEGORY_FIELD = {
    STATUS_LIKELY_TRUE_POSITIVE: "likely_true_positive",
    STATUS_LIKELY_FALSE_POSITIVE: "likely_false_positive",
    STATUS_GROUND_TRUTH_CONFLICT: "ground_truth_conflict",
    STATUS_MANUAL_REVIEW: "manual_review",
}


def validate_consistency(candidates: list["ffp.FpCandidateCase"], cases: list[dict]) -> dict:
    """Konsistenzpruefung (Auftrag "VALIDIERUNG"/"KONSISTENZPRUEFUNG"):
    total_cases/matched_cases/missing_cases/duplicate_cases/
    classification_sum. Reine Pruefung -- aendert nichts."""
    candidate_ids = [c.listing_id for c in candidates]
    case_ids = [c["case_id"] for c in cases]

    total_cases = len(candidate_ids)
    case_id_set = set(case_ids)
    missing_cases = sorted(set(candidate_ids) - case_id_set)
    duplicate_cases = sorted(
        {cid for cid in case_ids if case_ids.count(cid) > 1}
    )
    matched_cases = len(candidate_ids) - len(missing_cases)

    status_counts: dict[str, int] = defaultdict(int)
    for c in cases:
        status_counts[c["assessment"]["status"]] += 1
    classification_sum = sum(status_counts.values())

    reference_notes = []
    if total_cases != KNOWN_UNCLEAR_COUNT:
        reference_notes.append(
            f"Abweichung vom bekannten Referenzstand: erwartet {KNOWN_UNCLEAR_COUNT} "
            f"UNCLEAR-Faelle, tatsaechlich {total_cases}."
        )

    consistency_ok = (
        not missing_cases
        and not duplicate_cases
        and matched_cases == total_cases
        and classification_sum == total_cases
        and not reference_notes
    )

    return {
        "total_cases": total_cases,
        "matched_cases": matched_cases,
        "missing_cases": missing_cases,
        "duplicate_cases": duplicate_cases,
        "classification_sum": classification_sum,
        "status_counts": dict(status_counts),
        "reference_notes": reference_notes,
        "consistency_ok": consistency_ok,
    }


def build_report(
    input_path: Path = FORENSICS_SOURCE, rules_cfg: dict | None = None
) -> dict:
    """Baut den vollstaendigen UNCLEAR-Assessment-Report. Wiederverwendet
    ausschliesslich forensics_false_positives.extract_cases() fuer die
    current_routing-Ebene -- keine eigene evaluate()-Logik."""
    if rules_cfg is None:
        rules_cfg = load_current_rules()

    entries = ffp.load_forensics_entries(input_path)
    _confirmed, candidates = ffp.extract_cases(entries, rules_cfg, category=None)

    cases = [build_case(c) for c in candidates]
    cases.sort(
        key=lambda d: (d["historical_ground_truth"]["category"] or "", d["title"] or "")
    )

    categories: dict[str, dict] = defaultdict(_empty_category_counts)
    for case in cases:
        cat = case["historical_ground_truth"]["category"]
        cat_counts = categories[cat]
        cat_counts["unclear_count"] += 1
        field_name = _STATUS_TO_CATEGORY_FIELD[case["assessment"]["status"]]
        cat_counts[field_name] += 1
    categories = dict(sorted(categories.items()))

    summary = {
        "total_unclear": len(cases),
        "likely_true_positive": sum(cc["likely_true_positive"] for cc in categories.values()),
        "likely_false_positive": sum(cc["likely_false_positive"] for cc in categories.values()),
        "ground_truth_conflict": sum(cc["ground_truth_conflict"] for cc in categories.values()),
        "manual_review": sum(cc["manual_review"] for cc in categories.values()),
    }

    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    for case in cases:
        confidence_counts[case["confidence"].lower()] += 1

    consistency = validate_consistency(candidates, cases)

    # TOP-Kandidaten fuer einen spaeteren Ruleset-Audit (Auftrag
    # "ABSCHLUSSBERICHT"): LIKELY_FALSE_POSITIVE-Faelle, die unter den
    # AKTUELLEN Produktivregeln noch immer matchen (routing_status=
    # A_SAME_WRONG_CATEGORY) -- also live aktive Fehltreffer, nicht nur
    # historische Beobachtungen. Sortiert nach Confidence.
    _confidence_rank = {CONFIDENCE_HIGH: 0, CONFIDENCE_MEDIUM: 1, CONFIDENCE_LOW: 2}
    top_candidates = sorted(
        (
            c
            for c in cases
            if c["assessment"]["status"] == STATUS_LIKELY_FALSE_POSITIVE
            and c["current_routing"]["routing_status"] == ffp.ROUTING_STATUS_SAME_CATEGORY
        ),
        key=lambda c: (_confidence_rank.get(c["confidence"], 9), c["title"]),
    )

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ruleset_signature": current_ruleset_signature(rules_cfg),
            "source_ground_truth": str(input_path),
        },
        "summary": summary,
        "confidence": confidence_counts,
        "categories": categories,
        "cases": cases,
        "top_candidates": top_candidates,
        "consistency": consistency,
    }


def render_markdown(report: dict) -> str:
    meta = report["metadata"]
    summary = report["summary"]
    confidence = report["confidence"]
    categories = report["categories"]
    cases = report["cases"]
    consistency = report["consistency"]

    lines: list[str] = [
        "# UNCLEAR Routing Assessment",
        "",
        "Forensische Klassifikation der 35 historischen UNCLEAR-Faelle aus "
        "`docs/DASHBOARD_MATCH_FORENSICS.json` (wird nie veraendert). Betrifft "
        "AUSSCHLIESSLICH Faelle mit historischem Verdict UNCLEAR -- niemals "
        "TRUE_POSITIVE/FALSE_POSITIVE. Automatisch generiert von "
        "`tools/ruleset_quality/unclear_routing_assessment.py`.",
        "",
        f"- generated_at: {meta['generated_at']}",
        f"- ruleset_signature: {meta['ruleset_signature']}",
        f"- source_ground_truth: {meta['source_ground_truth']}",
        "",
        "## SUMMARY",
        "",
        f"- total_unclear: {summary['total_unclear']}",
        f"- likely_true_positive: {summary['likely_true_positive']}",
        f"- likely_false_positive: {summary['likely_false_positive']}",
        f"- ground_truth_conflict: {summary['ground_truth_conflict']}",
        f"- manual_review: {summary['manual_review']}",
        "",
        "## CONFIDENCE",
        "",
        f"- high: {confidence['high']}",
        f"- medium: {confidence['medium']}",
        f"- low: {confidence['low']}",
        "",
        "## CATEGORIES",
        "",
        f"{'category':<18} | {'unclear':<7} | {'TP':<5} | {'FP':<5} | {'conflict':<8} | manual_review",
    ]
    for cat, cc in categories.items():
        lines.append(
            f"{cat:<18} | {cc['unclear_count']:<7} | {cc['likely_true_positive']:<5} | "
            f"{cc['likely_false_positive']:<5} | {cc['ground_truth_conflict']:<8} | {cc['manual_review']}"
        )
    lines.append("")

    lines.append("## CASES")
    lines.append("")
    for case in cases:
        hgt = case["historical_ground_truth"]
        cra = case["current_routing"]
        lines.append(f"### {case['title']}")
        lines.append("")
        lines.append(f"- case_id: {case['case_id']}")
        lines.append(f"- price: {case['price']}")
        lines.append(f"- historical_ground_truth: verdict={hgt['verdict']}, category={hgt['category']}, rule={hgt['rule']}")
        lines.append(
            f"- current_routing: category={cra['category']}, rule={cra['rule']}, "
            f"match_state={cra['match_state']}, routing_status={cra['routing_status']}"
        )
        lines.append(f"- assessment: {case['assessment']['status']} (confidence={case['confidence']})")
        lines.append(f"- root_cause_pattern: {case['root_cause_pattern']}")
        lines.append(f"- recommended_action: {case['recommended_action']}")
        lines.append("- evidence:")
        for ev in case["evidence"]:
            lines.append(f"  - [{ev['type']}/{ev['strength']}] {ev['signal']}: {ev['interpretation']}")
        lines.append("")

    lines.append("## CONSISTENCY")
    lines.append("")
    lines.append(f"- total_cases: {consistency['total_cases']}")
    lines.append(f"- matched_cases: {consistency['matched_cases']}")
    lines.append(f"- missing_cases: {len(consistency['missing_cases'])}")
    lines.append(f"- duplicate_cases: {len(consistency['duplicate_cases'])}")
    lines.append(f"- classification_sum: {consistency['classification_sum']}")
    lines.append(f"- consistency_ok: {consistency['consistency_ok']}")

    return "\n".join(lines)


def write_outputs(report: dict) -> dict[str, Path]:
    import json

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")

    return {"json_report": REPORT_JSON, "md_report": REPORT_MD}


def _print_final_summary(report: dict) -> None:
    summary = report["summary"]
    confidence = report["confidence"]
    consistency = report["consistency"]

    print("UNCLEAR ROUTING ASSESSMENT")
    print("=" * 26)
    print()
    print("Historical UNCLEAR:")
    print(f"    {summary['total_unclear']}")
    print()
    print("Likely TRUE_POSITIVE:")
    print(f"    {summary['likely_true_positive']}")
    print()
    print("Likely FALSE_POSITIVE:")
    print(f"    {summary['likely_false_positive']}")
    print()
    print("Ground Truth Conflict:")
    print(f"    {summary['ground_truth_conflict']}")
    print()
    print("Manual Review:")
    print(f"    {summary['manual_review']}")
    print()
    print("High confidence:")
    print(f"    {confidence['high']}")
    print()
    print("Medium confidence:")
    print(f"    {confidence['medium']}")
    print()
    print("Low confidence:")
    print(f"    {confidence['low']}")
    print()
    print("Consistency:")
    print(f"    {consistency['consistency_ok']}")
    print()

    top_candidates = report["top_candidates"]
    if top_candidates:
        print(f"TOP-Kandidaten fuer spaeteren Ruleset-Audit ({len(top_candidates)}):")
        print()
        for i, c in enumerate(top_candidates, 1):
            hgt = c["historical_ground_truth"]
            print(f"{i}. Kategorie: {hgt['category']}")
            print(f"   Titel: {c['title']}")
            print(f"   Aktuelle Regel: {c['current_routing']['rule']}")
            print(f"   Root Cause: {c['root_cause_pattern']}")
            print(f"   Confidence: {c['confidence']}")
            for ev in c["evidence"]:
                print(f"   Evidence: [{ev['type']}] {ev['signal']} -- {ev['interpretation']}")
            print(f"   Recommended Action: {c['recommended_action']}")
            print()
    else:
        print("Keine live aktiven TOP-Kandidaten fuer einen Ruleset-Audit gefunden.")
        print()


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.ruleset_quality.unclear_routing_assessment",
        description=(
            "Forensische Klassifikation der 35 historischen UNCLEAR-Faelle. "
            "Read-only -- aendert keine YAML-Regeln und niemals "
            "docs/DASHBOARD_MATCH_FORENSICS.json."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=FORENSICS_SOURCE,
        help="Pfad zum Forensik-Ground-Truth-Artefakt",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    rules_cfg = load_current_rules()
    report = build_report(input_path=args.input, rules_cfg=rules_cfg)
    written = write_outputs(report)
    for label, path in written.items():
        print(f"geschrieben ({label}): {path}")
    print()
    _print_final_summary(report)

    if not report["consistency"]["consistency_ok"]:
        print("ERROR: Konsistenzpruefung fehlgeschlagen (siehe oben).")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
