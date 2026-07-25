"""Erkennung dedizierter Grafikkarten aus Angebotstiteln (Phase 4).

Reine, seiteneffektfreie Text-Parser. Erkennt NVIDIA (GTX/RTX) und AMD
(RX) Modellbezeichnungen. Bewusst KEIN Abgleich gegen eine Ausschlussliste
für integrierte Grafik (AMD "Vega", Intel "UHD"/"Iris Graphics") --
stattdessen wird ausschließlich nach den positiven GTX/RTX/RX-Mustern
gesucht. Das hat denselben Effekt (integrierte Grafik wird nie erkannt),
ist aber robuster: eine Ausschlussliste müsste ständig um neue Intel-/
AMD-Generationen ergänzt werden, das positive Muster nicht.

Beispiel: "Ryzen 5 5600G mit Radeon Vega Grafik" enthält KEIN "RX"-
gefolgt-von-Modellnummer-Muster und wird deshalb korrekt als "keine
dedizierte GPU" (None) erkannt -- der 5600G ist eine APU mit integrierter
Grafik, kein Gaming-PC-Kandidat.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Literal

Brand = Literal["NVIDIA", "AMD"]

# Aus Phase 5: bevorzugte Grafikkarten für die Gaming-PC-Kategorie.
# Dies ist eine einfache Mitgliedschaftspruefung gegen die im Auftrag
# genannte Liste -- KEIN "mindestens gleichwertig"-Vergleich (z.B. wird
# eine RTX 3070 hier NICHT automatisch als "preferred" gewertet, obwohl
# sie besser als eine RTX 3060 ist). Ein "erfuellt Mindestanforderung X
# oder besser"-Vergleich ist Sache der YAML-Regeln in Phase 5.
_PREFERRED_MODELS: set[tuple[Brand, str]] = {
    ("NVIDIA", "GTX 1060"),
    ("NVIDIA", "GTX 1070"),
    ("NVIDIA", "GTX 1660"),
    ("NVIDIA", "RTX 2060"),
    ("NVIDIA", "RTX 2070"),
    ("NVIDIA", "RTX 3060"),
    ("AMD", "RX 6600"),
    ("AMD", "RX 6700 XT"),
}


@dataclass(frozen=True)
class GpuMatch:
    brand: Brand
    model: str          # normalisiert, z.B. "RTX 3060", "GTX 1660 SUPER", "RX 6700 XT"
    is_preferred: bool  # exakte Mitgliedschaft in der Phase-5-Vorzugsliste


_NVIDIA_PATTERN = re.compile(
    r"\b(gtx|rtx)[\s-]?(\d{3,4})\s?(ti|super)?\b", re.IGNORECASE
)
_AMD_PATTERN = re.compile(
    r"\brx[\s-]?(\d{4})\s?(xt)?\b", re.IGNORECASE
)


def detect_dedicated_gpu(text: str) -> GpuMatch | None:
    """Erkennt die erste im Text vorkommende dedizierte Grafikkarte.

    Liefert None bei integrierter Grafik (Vega/UHD/Iris -- kein GTX/RTX/
    RX-Muster vorhanden) oder wenn keine GPU erwähnt wird.
    """
    candidates: list[tuple[int, GpuMatch]] = []

    nvidia_match = _NVIDIA_PATTERN.search(text)
    if nvidia_match:
        tier = nvidia_match.group(1).upper()
        number = nvidia_match.group(2)
        suffix = nvidia_match.group(3)
        model = f"{tier} {number}"
        if suffix:
            model += f" {suffix.upper()}"
        candidates.append((
            nvidia_match.start(),
            GpuMatch(brand="NVIDIA", model=model, is_preferred=("NVIDIA", model) in _PREFERRED_MODELS),
        ))

    amd_match = _AMD_PATTERN.search(text)
    if amd_match:
        number = amd_match.group(1)
        suffix = amd_match.group(2)
        model = f"RX {number}"
        if suffix:
            model += f" {suffix.upper()}"
        candidates.append((
            amd_match.start(),
            GpuMatch(brand="AMD", model=model, is_preferred=("AMD", model) in _PREFERRED_MODELS),
        ))

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[0])
    return candidates[0][1]
