"""Gehäusetyp-Erkennung aus Angebotstiteln (Phase 4).

Reine, seiteneffektfreie Text-Parser. Unterscheidet zwischen erlaubten
Formfaktoren (Tower, Midi-Tower, Micro-ATX) und kompakten Formfaktoren,
die für Office-/Gaming-PC-Kategorien ausgeschlossen werden sollen (Phase
5: Tiny, Mini, Mini-PC, USFF, SFF, Small Form Factor, All-in-One).

WICHTIGE DISAMBIGUIERUNG: "AIO" bedeutet im Gebrauchtmarkt praktisch
immer "All-In-One-Wasserkühlung" (CPU-Kühler), NICHT "All-in-One-PC"
(Monitor-integrierter Computer). Ein Gaming-PC mit "AIO Wasserkühlung"
darf nicht faelschlich als All-in-One-PC ausgeschlossen werden. Es wird
deshalb ausschließlich der ausgeschriebene Begriff "All-in-One" erkannt,
NICHT die Abkürzung "AIO" alleine.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Literal

Category = Literal["allowed", "excluded"]


@dataclass(frozen=True)
class CaseMatch:
    case_type: str      # normalisierte Bezeichnung, z.B. "Midi-Tower", "Mini-PC"
    category: Category  # "allowed" oder "excluded"


# Reihenfolge ist wichtig: spezifischere Begriffe (z.B. "mini pc") werden
# VOR dem allgemeineren "mini" geprüft, damit sie mit ihrer eigenen,
# aussagekräftigeren Bezeichnung erkannt werden.
_EXCLUDED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\ball[\s-]?in[\s-]?one\b", re.IGNORECASE), "All-in-One"),
    (re.compile(r"\busff\b", re.IGNORECASE), "USFF"),
    (re.compile(r"\bsmall\s+form\s+factor\b", re.IGNORECASE), "Small-Form-Factor"),
    (re.compile(r"\bsff\b", re.IGNORECASE), "SFF"),
    (re.compile(r"\bmini[\s-]?pc\b", re.IGNORECASE), "Mini-PC"),
    (re.compile(r"\btiny\b", re.IGNORECASE), "Tiny"),
    (re.compile(r"\bmini\b", re.IGNORECASE), "Mini"),
]

_ALLOWED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bmidi[\s-]?tower\b", re.IGNORECASE), "Midi-Tower"),
    (re.compile(r"\bmicro[\s-]?atx\b", re.IGNORECASE), "Micro-ATX"),
    (re.compile(r"\btower\b", re.IGNORECASE), "Tower"),
]


def detect_case_type(text: str) -> CaseMatch | None:
    """Erkennt den Gehäusetyp aus einem Angebotstitel.

    Ausgeschlossene Formfaktoren werden VOR erlaubten geprüft -- eine
    explizite Kompakt-Angabe wiegt schwerer als ein zufällig auftauchendes
    "Tower" an anderer Stelle. Liefert None, wenn der Titel keine
    erkennbare Gehäuseform-Angabe enthält (der häufigste Fall, da die
    meisten Anzeigen den Formfaktor gar nicht explizit nennen).

    BEKANNTE GRENZE: "Mini-ITX" (ein Mainboard-Formfaktor, der auch in
    normal großen Towern verbaut sein kann) matcht das "Mini"-Muster und
    würde fälschlich als kompaktes Gehäuse gewertet. Eine explizite
    Sonderbehandlung für "Mini-ITX" wurde bewusst nicht ergänzt, da
    reine Mainboard-Erwähnungen ohne weiteren Gehäuse-Kontext ohnehin
    unzuverlässig sind -- siehe Testfall in tests/test_detector_case.py.
    """
    for pattern, label in _EXCLUDED_PATTERNS:
        if pattern.search(text):
            return CaseMatch(case_type=label, category="excluded")

    for pattern, label in _ALLOWED_PATTERNS:
        if pattern.search(text):
            return CaseMatch(case_type=label, category="allowed")

    return None
