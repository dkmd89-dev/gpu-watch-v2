"""Netzteil-Erkennung aus Angebotstiteln (Phase 4).

Reine, seiteneffektfreie Text-Parser.

BESONDERHEIT bei der Watt-Erkennung: Viele echte Anzeigen nennen die
Netzteilleistung ohne das Wort "Netzteil"/"PSU" direkt daneben (reine
Positions-Konvention, meist als letzte Spezifikation vor/nach der GPU),
z.B. ein echter Titel aus diesem Projekt:
    "... RTX 3060 Ti 1000W" (ohne "Netzteil" im Text)
Die Watt-Erkennung verlangt deshalb KEINEN Kontext-Begriff, sondern
akzeptiert jede "NNNW"-Zahl in einem plausiblen Netzteil-Leistungsbereich
(300-1600 Watt). Das ist bewusst grosszuegiger als bei RAM/SSD (wo ein
Kontext-Wort noetig ist), weil bei PSU-Watt kaum eine andere GB/TB-artige
Verwechslungsgefahr besteht -- "NNNW" ist ein recht eindeutiges Muster.
"""
from __future__ import annotations
import re

_PSU_MENTION_PATTERN = re.compile(
    r"\b(?:netzteil|psu|power\s?supply)\b", re.IGNORECASE
)
_WATT_PATTERN = re.compile(r"\b(\d{3,4})\s?w\b", re.IGNORECASE)

# Plausibler Leistungsbereich handelsüblicher PC-Netzteile. Werte
# außerhalb (z.B. "20W" Ladegerät, "5W" USB) werden ignoriert.
_PLAUSIBLE_WATT_MIN = 300
_PLAUSIBLE_WATT_MAX = 1600


def detect_psu_mentioned(text: str) -> bool:
    """Prüft, ob überhaupt ein Netzteil explizit erwähnt wird."""
    return _PSU_MENTION_PATTERN.search(text) is not None


def detect_psu_watt(text: str) -> int | None:
    """Erkennt die Netzteilleistung in Watt.

    Verlangt KEIN "Netzteil"-Schlüsselwort in der Nähe (siehe Modul-
    Docstring) -- nur einen plausiblen Wertebereich (300-1600W).
    """
    for match in _WATT_PATTERN.finditer(text):
        value = int(match.group(1))
        if _PLAUSIBLE_WATT_MIN <= value <= _PLAUSIBLE_WATT_MAX:
            return value
    return None
