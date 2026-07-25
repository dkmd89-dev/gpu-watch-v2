"""RAM-Erkennung aus Angebotstiteln/-beschreibungen (Phase 4).

Reine, seiteneffektfreie Text-Parser -- keine Bewertungslogik, kein
Zugriff auf rules.yaml/Kategorien. Werden erst in einem späteren Schritt
(Phase 5) vom Matcher tatsächlich verwendet.

Die größte Fehlerquelle bei PC-Angeboten: ein Titel enthält oft MEHRERE
"XGB"-Angaben gleichzeitig (RAM, SSD-Größe, GPU-VRAM), z.B.
"Ryzen 5 16GB DDR4 RAM 512GB SSD RTX 3060 12GB". Ein naiver Regex, der
einfach die erste/größte Zahl vor "GB" nimmt, würde hier je nach Titel
die falsche Zahl als RAM-Größe erkennen. Deshalb wird nur eine "XGB"-
Angabe akzeptiert, die UNMITTELBAR (nur durch wenige Trennzeichen
getrennt) neben einem RAM-Schlüsselwort steht -- keine große
Kontext-Fenster-Suche über den ganzen Titel.
"""
from __future__ import annotations
import re
from typing import Literal

RamType = Literal["DDR3", "DDR4", "DDR5"]

# Erlaubte "Verbindungszeichen" zwischen der GB-Zahl und dem RAM-Schlüsselwort
# (Leerzeichen, Komma, Bindestrich, Slash, Klammern) -- bewusst KEIN "\w",
# damit z.B. "SSD" zwischen "512GB" und einem folgenden "RAM" die Erkennung
# nicht faelschlich ueberbrueckt.
_CONNECTOR = r"[\s,:/\-()]*"

# "16GB RAM", "16GB DDR4", "16 GB Arbeitsspeicher"
_PATTERN_GB_THEN_RAM = re.compile(
    r"(\d{1,3})\s*gb" + _CONNECTOR + r"(?:ram|arbeitsspeicher|ddr\s?[345])",
    re.IGNORECASE,
)
# "RAM 16GB", "DDR4 16GB", "Arbeitsspeicher: 16GB"
_PATTERN_RAM_THEN_GB = re.compile(
    r"(?:ram|arbeitsspeicher|ddr\s?[345])" + _CONNECTOR + r"(\d{1,3})\s*gb",
    re.IGNORECASE,
)

_PATTERN_DDR_TYPE = re.compile(r"\bddr\s?([345])\b", re.IGNORECASE)


def detect_ram_gb(text: str) -> int | None:
    """Erkennt die System-RAM-Größe in GB aus einem Angebotstitel.

    Gibt None zurück, wenn keine eindeutig als RAM erkennbare GB-Angabe
    gefunden wird (z.B. bei reinen GPU- oder SSD-Angeboten).

    BEKANNTE GRENZE: Manche Anzeigen nennen die RAM-Größe ohne das Wort
    "RAM"/"Arbeitsspeicher"/"DDRx" direkt daneben (z.B. "... 32GB 1TB
    RX 7800 XT ...", RAM-Größe rein durch Position vor SSD/GPU impliziert).
    Solche Fälle liefern bewusst None statt eines geratenen Werts -- eine
    falsche RAM-Erkennung wäre riskanter als eine fehlende, da sie später
    in Mindestanforderungen/Deal-Score einfließt.
    """
    match = _PATTERN_GB_THEN_RAM.search(text) or _PATTERN_RAM_THEN_GB.search(text)
    if match:
        return int(match.group(1))
    return None


def detect_ram_type(text: str) -> RamType | None:
    """Erkennt den RAM-Typ (DDR3/DDR4/DDR5) aus einem Angebotstitel."""
    match = _PATTERN_DDR_TYPE.search(text)
    if match:
        return f"DDR{match.group(1)}"  # type: ignore[return-value]
    return None
