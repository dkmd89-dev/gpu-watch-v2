"""Speicher-Erkennung (SSD/HDD/NVMe) aus Angebotstiteln (Phase 4).

Reine, seiteneffektfreie Text-Parser. Verwendet dasselbe Prinzip wie
categories.detectors.ram: strikte Adjazenz zwischen Größenangabe und
Schlüsselwort, damit z.B. "512GB SSD 16GB RAM" nicht verwechselt wird
(die 16 würde ohne Adjazenz-Prüfung fälschlich als SSD-Größe erkannt).

TB-Angaben werden in GB umgerechnet (1 TB = 1000 GB, Marktkonvention bei
Speichergrößen, nicht 1024 GB), inkl. deutscher Dezimal-Kommaschreibweise
("1,5TB").
"""
from __future__ import annotations
import re

_CONNECTOR = r"[\s,:/\-()]*(?:SATA(?:[\s-]*(?:I{1,3}|[123]))?\s*)?"

# Zahl (optional mit Dezimalpunkt/-komma) + Einheit (GB/TB)
_SIZE_UNIT = r"(\d{1,4}(?:[.,]\d{1,2})?)\s*(gb|tb)"

_PATTERN_SIZE_THEN_SSD = re.compile(
    _SIZE_UNIT + _CONNECTOR + r"(?:ssd|sdd|nvme)", re.IGNORECASE
)
_PATTERN_SSD_THEN_SIZE = re.compile(
    r"(?:ssd|sdd|nvme)" + _CONNECTOR + _SIZE_UNIT, re.IGNORECASE
)
_PATTERN_SIZE_THEN_HDD = re.compile(
    _SIZE_UNIT + _CONNECTOR + r"hdd", re.IGNORECASE
)
_PATTERN_HDD_THEN_SIZE = re.compile(
    r"hdd" + _CONNECTOR + _SIZE_UNIT, re.IGNORECASE
)
_PATTERN_NVME = re.compile(r"\bnvme\b", re.IGNORECASE)


def _size_to_gb(number_str: str, unit: str) -> int:
    value = float(number_str.replace(",", "."))
    if unit.lower() == "tb":
        value *= 1000
    return round(value)


def _first_match_gb(text: str, pattern_a: re.Pattern, pattern_b: re.Pattern) -> int | None:
    match = pattern_a.search(text) or pattern_b.search(text)
    if match:
        return _size_to_gb(match.group(1), match.group(2))
    return None


def detect_ssd_gb(text: str) -> int | None:
    """Erkennt die SSD-Größe in GB (inkl. NVMe-SSDs, TB wird umgerechnet).

    Erkennt zusätzlich den häufigen Vertipper "SDD" (statt "SSD") als
    gleichwertiges Schlüsselwort -- kommt in echten Kleinanzeigen-Titeln
    regelmäßig vor und würde sonst zu False Negatives führen.

    Erkennt außerdem eine zwischen Größe und "SSD" stehende SATA-
    Generationsangabe ("SATA", "SATA III", "SATA-III", "SATA 3", "SATA3"
    -- Groß-/Kleinschreibung und Leerzeichen/Bindestrich beliebig), z.B.
    "500GB SATA III SSD". Vormals eine bekannte Lücke (siehe STATUS.md
    Abschnitt 10): die strikte Adjazenzprüfung erkannte nur bloßes
    "SATA" zwischen Zahl und "SSD", nicht die in echten Anzeigen
    verbreitete Generationsangabe -- dadurch wurden reale SATA-SSD-
    Angebote dieser Wortstellung als False Negative verpasst.

    BEKANNTE GRENZEN:
    - Größenangaben ohne explizite Einheit (z.B. "500SSD" statt "500GB
      SSD") werden bewusst NICHT erkannt -- ohne "GB"/"TB" ist die Zahl
      nicht zuverlässig von anderen Zahlen (Preis, Modellnummer)
      unterscheidbar.
    - Dezimal-TB-Angaben werden nur mit Punkt oder Komma als Trennzeichen
      erkannt ("1,5TB"/"1.5TB"), NICHT mit Bindestrich ("1-5TB"). Solche
      Bindestrich-Schreibweisen kommen in echten Anzeigentiteln (aus
      get_text() der Seite) nicht vor -- sie entstehen nur beim
      URL-Slug-Encoding, das hier nicht als Eingabe verwendet wird. Ein
      Bindestrich zwischen zwei Ziffern wird stattdessen als Trenner
      zwischen zwei unabhängigen Zahlen interpretiert (z.B. "1-5TB SSD"
      würde fälschlich nur "5TB" erkennen) -- siehe Testfall in
      tests/test_detector_storage.py.
    """
    return _first_match_gb(text, _PATTERN_SIZE_THEN_SSD, _PATTERN_SSD_THEN_SIZE)


def detect_hdd_gb(text: str) -> int | None:
    """Erkennt die HDD-Größe in GB (TB wird umgerechnet)."""
    return _first_match_gb(text, _PATTERN_SIZE_THEN_HDD, _PATTERN_HDD_THEN_SIZE)


def detect_nvme(text: str) -> bool:
    """Prüft, ob explizit eine NVMe-Schnittstelle erwähnt wird.

    Unabhängig von detect_ssd_gb() -- eine NVMe-SSD ist auch über
    detect_ssd_gb() als SSD erkennbar, detect_nvme() liefert zusätzlich
    die Information, ob es sich um NVMe (statt SATA) handelt.
    """
    return _PATTERN_NVME.search(text) is not None
