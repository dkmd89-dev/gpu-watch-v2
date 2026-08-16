"""GPU-VRAM-Parsing aus dem Angebotstitel.

Schritt 3 der Modularisierung (siehe Analysebericht): unveraendert aus
matcher/core.py extrahiert. Eigenstaendiges Modul, weil GPU-VRAM-Erkennung
funktional von den generischen Text-Matching-Primitiven
(matcher/text_matching.py) getrennt ist und Raum fuer spaetere,
GPU-spezifische Erweiterungen bietet (z.B. weitere VRAM-Notationen).
"""
from __future__ import annotations

import re


def _vram_gb(title_lower: str) -> int | None:
    m = re.search(r"(\d{1,2})\s*gb", title_lower)
    return int(m.group(1)) if m else None
