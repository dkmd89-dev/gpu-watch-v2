"""CPU-Erkennung aus Angebotstiteln/-beschreibungen (Phase 4).

Reine, seiteneffektfreie Text-Parser -- keine Bewertungslogik, keine
hartcodierte Liste konkreter Modelle. Generation/Serie wird stattdessen
über die realen Namenskonventionen von Intel und AMD aus der Modellnummer
abgeleitet:

- Intel: bei 4-stelliger Modellnummer ist die erste Ziffer die Generation
  (z.B. i5-8400 -> Generation 8). Bei 5-stelliger Modellnummer sind es die
  ersten zwei Ziffern (z.B. i5-10400 -> Generation 10, i7-13700 -> 13).
- AMD Ryzen: die erste Ziffer der (immer 4-stelligen) Modellnummer ist die
  Serie/Generation, ausgedrückt als xxxx-Serie (z.B. Ryzen 5 3600 ->
  3000er-Serie/Zen 2, Ryzen 7 5800X -> 5000er-Serie/Zen 3).

Ob eine erkannte CPU eine Mindestanforderung erfüllt (z.B. "i5-8400 oder
besser"), wird NICHT hier entschieden -- das ist Sache der YAML-Regeln
in Phase 5. Dieses Modul liefert ausschließlich die rohe Erkennung.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Literal

Brand = Literal["Intel", "AMD"]


@dataclass(frozen=True)
class CpuMatch:
    brand: Brand
    tier: str          # z.B. "i5", "i7", "Ryzen 5", "Ryzen 7"
    model_number: int  # z.B. 8400, 3600, 5600
    generation: int     # Intel: 1-14 (Generation); AMD: 1000er-Schritte (z.B. 3000, 5000)


_INTEL_PATTERN = re.compile(
    r"\bi([3579])[\s-]?(\d{4,5})[a-z]{0,3}\b", re.IGNORECASE
)
_AMD_RYZEN_PATTERN = re.compile(
    r"\bryzen\s*([3579])\s*(\d{4})[a-z]{0,3}\b", re.IGNORECASE
)


def _intel_generation(model_number: int) -> int:
    digits = str(model_number)
    # 5-stellig (z.B. 10400, 13700) -> erste ZWEI Ziffern sind die Generation.
    # 4-stellig (z.B. 8400, 9900) -> erste EINE Ziffer ist die Generation.
    return int(digits[:2]) if len(digits) == 5 else int(digits[:1])


def _amd_generation(model_number: int) -> int:
    digits = str(model_number)
    return int(digits[0]) * 1000


def detect_cpu(text: str) -> CpuMatch | None:
    """Erkennt die erste im Text vorkommende Intel- oder AMD-Ryzen-CPU.

    Liefert None, wenn keine CPU mit vollständiger Modellnummer erkennbar
    ist (reine Marken-/Serien-Erwähnungen ohne Modellnummer, z.B. "Ryzen 5
    Serie", lösen bewusst KEINE Erkennung aus -- ohne Modellnummer lässt
    sich keine Generation ableiten).

    BEKANNTE GRENZEN: Modellnummern ohne das vorangestellte Wort "Ryzen"
    (z.B. verkürzte Schreibweisen wie "7600X3D" oder "R5600X" statt
    "Ryzen 7 7600X3D"/"Ryzen 5 5600X") werden bewusst NICHT erkannt --
    ein Muster, das auch "R" + Ziffern akzeptiert, würde zu leicht mit
    AMD-GPU-Bezeichnungen (RX 6750, RX 7600) kollidieren. Diese Fälle
    liefern None statt eines riskanten Rate-Treffers.
    """
    candidates: list[tuple[int, CpuMatch]] = []

    intel_match = _INTEL_PATTERN.search(text)
    if intel_match:
        tier_digit = intel_match.group(1)
        model_number = int(intel_match.group(2))
        candidates.append((
            intel_match.start(),
            CpuMatch(
                brand="Intel",
                tier=f"i{tier_digit}",
                model_number=model_number,
                generation=_intel_generation(model_number),
            ),
        ))

    amd_match = _AMD_RYZEN_PATTERN.search(text)
    if amd_match:
        tier_digit = amd_match.group(1)
        model_number = int(amd_match.group(2))
        candidates.append((
            amd_match.start(),
            CpuMatch(
                brand="AMD",
                tier=f"Ryzen {tier_digit}",
                model_number=model_number,
                generation=_amd_generation(model_number),
            ),
        ))

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[0])
    return candidates[0][1]
