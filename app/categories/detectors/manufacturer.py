"""Hersteller-Erkennung aus Angebotstiteln (Phase 4/5-Folgeschritt).

Reine, seiteneffektfreie Text-Parser -- keine Bewertungslogik, keine
Reputations-/Qualitätswertung (siehe scoring/deal_score.py, wo die
"hersteller"-Komponente aktuell bewusst einen neutralen Platzhalter
liefert; dieses Modul liefert nur die rohe Erkennung, die spätere
Score-/Filter-Integration ist ein separater Folgeschritt).

Unterschieden werden zwei Kategorien:
- "oem": ein bekannter Marken-PC-Hersteller wird im Titel genannt
  (z.B. "Dell OptiPlex 7040", "Lenovo ThinkCentre").
- "custom": der Titel weist explizit auf einen Eigenbau/Selbstbau hin
  (z.B. "Eigenbau PC", "selbst zusammengestellt") -- kein Marken-PC,
  aber ebenfalls ein aussagekräftiges Signal (kein OEM-Support/-Garantie,
  dafür oft freiere Komponentenwahl).

Liefert None, wenn der Titel keinen der beiden Fälle erkennen lässt --
der häufigste Fall, da viele Anzeigen weder eine Marke noch "Eigenbau"
explizit nennen (z.B. reine Komponentenlisten). Das ist bewusst KEIN
Fehlerfall, sondern "nicht ermittelbar", analog zu den übrigen Detectors
(vgl. detect_case_type(), detect_dedicated_gpu()).

BEKANNTE GRENZEN: Die OEM-Markenliste ist eine feste Aufzählung
gängiger, am deutschen Gebrauchtmarkt verbreiteter PC-Hersteller.
Anders als bei CPU-/GPU-Erkennung lässt sich ein Herstellername nicht
algorithmisch aus einem Muster ableiten -- die Liste muss bei Bedarf
manuell erweitert werden (z.B. um "Schenker", "One GmbH"). Das ist
dieselbe Trade-off-Entscheidung wie bei den Formfaktor-Mustern in
case.py.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Literal

Category = Literal["oem", "custom"]


@dataclass(frozen=True)
class ManufacturerMatch:
    name: str          # normalisierte Bezeichnung, z.B. "Dell", "Lenovo"
    category: Category  # "oem" oder "custom"


# Reihenfolge nicht relevant (jede Marke hat ein eindeutiges Muster),
# aber alphabetisch sortiert für Übersichtlichkeit/Wartbarkeit.
# Wortgrenzen (\b) verhindern Teilstring-Treffer (z.B. "Acer" nicht in
# anderen Wörtern). "HP"/"Hewlett-Packard" sind bewusst zwei Muster für
# denselben normalisierten Namen, da beide Schreibweisen im Gebrauchtmarkt
# vorkommen.
_OEM_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bacer\b", re.IGNORECASE), "Acer"),
    (re.compile(r"\bapple\b", re.IGNORECASE), "Apple"),
    (re.compile(r"\basus\b", re.IGNORECASE), "Asus"),
    (re.compile(r"\bcaptiva\b", re.IGNORECASE), "Captiva"),
    (re.compile(r"\bdell\b", re.IGNORECASE), "Dell"),
    (re.compile(r"\bfujitsu\b", re.IGNORECASE), "Fujitsu"),
    (re.compile(r"\bhewlett[\s-]?packard\b", re.IGNORECASE), "HP"),
    (re.compile(r"\bhp\b", re.IGNORECASE), "HP"),
    (re.compile(r"\blenovo\b", re.IGNORECASE), "Lenovo"),
    (re.compile(r"\bmedion\b", re.IGNORECASE), "Medion"),
    (re.compile(r"\bmsi\b", re.IGNORECASE), "MSI"),
    (re.compile(r"\bschenker\b", re.IGNORECASE), "Schenker"),
    (re.compile(r"\bterra\b", re.IGNORECASE), "Terra"),
]

# Explizite Eigenbau-Hinweise. "Selbstbau"/"selbst zusammengestellt" sind
# gängige Formulierungen in Kleinanzeigen; "custom pc" bewusst NICHT
# aufgenommen, da "Custom" im Gebrauchtmarkt häufig auch für individuell
# konfigurierte OEM-Systeme verwendet wird (z.B. "Dell Custom Build") und
# damit fälschlich Marken-PCs als Eigenbau markieren würde.
_CUSTOM_PATTERNS: list[re.Pattern] = [
    re.compile(r"\beigenbau\b", re.IGNORECASE),
    re.compile(r"\bselbstbau\b", re.IGNORECASE),
    re.compile(r"\bselbst\s+zusammengestellt\b", re.IGNORECASE),
    re.compile(r"\bselbst\s+gebaut\b", re.IGNORECASE),
]


def detect_manufacturer(text: str) -> ManufacturerMatch | None:
    """Erkennt einen genannten Marken-PC-Hersteller oder einen expliziten
    Eigenbau-Hinweis im Angebotstitel.

    OEM-Marken werden VOR Eigenbau-Mustern geprüft: nennt ein Titel sowohl
    eine Marke als auch (unwahrscheinlich, aber möglich) ein Eigenbau-Wort,
    zählt die konkretere Markenangabe. Liefert None, wenn keines von
    beidem erkennbar ist.
    """
    for pattern, name in _OEM_PATTERNS:
        if pattern.search(text):
            return ManufacturerMatch(name=name, category="oem")

    for pattern in _CUSTOM_PATTERNS:
        if pattern.search(text):
            return ManufacturerMatch(name="Eigenbau", category="custom")

    return None
