"""Windows-Versions-Erkennung aus Angebotstiteln (Phase 4).

Reine, seiteneffektfreie Text-Parser. Erkennt "Windows"/"Win" gefolgt
von der Versionsnummer (7/8/10/11), in beliebiger gängiger Schreibweise
("Windows 11", "Win 11", "Win11", "Windows11").
"""
from __future__ import annotations
import re

_WINDOWS_VERSION_PATTERN = re.compile(
    r"\bwin(?:dows)?\s?(7|8|10|11)\b", re.IGNORECASE
)


def detect_windows_version(text: str) -> str | None:
    """Erkennt die erwähnte Windows-Version als String ("7"/"8"/"10"/"11").

    Liefert None, wenn keine Windows-Version genannt wird (der häufigste
    Fall bei reinen Hardware-Anzeigen ohne Betriebssystem-Angabe).
    """
    match = _WINDOWS_VERSION_PATTERN.search(text)
    if match:
        return match.group(1)
    return None
