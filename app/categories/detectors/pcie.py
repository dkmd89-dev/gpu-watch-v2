"""PCIe-Stromstecker-Erkennung aus Angebotstiteln (Phase 4).

Reine, seiteneffektfreie Text-Parser. Erkennt Erwähnungen von PCIe-
Stromsteckern (6-Pin, 8-Pin, 6+2-Pin), relevant um zu prüfen, ob ein
mitgeliefertes Netzteil zur Stromversorgung einer bestimmten Grafikkarte
passt.

BEKANNTE GRENZE: Es wird ausschließlich das Zahl+"Pin"-Muster geprüft,
ohne weiteren Kontext ("PCIe"/"Netzteil"/"Kabel" davor/danach). In der
Praxis der Kleinanzeigen-Titel kommt "Pin" faktisch nur im PCIe-Stecker-
Kontext vor (andere Steckertypen wie "9-Pin seriell" werden in
Gebraucht-PC-Anzeigen praktisch nie erwähnt), daher wird hier bewusst
auf eine zusätzliche Kontextprüfung verzichtet, um das Muster einfach zu
halten.
"""
from __future__ import annotations
import re

_PCIE_CONNECTOR_PATTERN = re.compile(r"\b(6\+2|8|6)[\s-]?pin\b", re.IGNORECASE)


def detect_pcie_connectors(text: str) -> list[str]:
    """Erkennt alle im Text erwähnten PCIe-Stromstecker-Typen.

    Liefert eine deduplizierte, in Erwähnungsreihenfolge sortierte Liste
    normalisierter Bezeichnungen, z.B. ["8-Pin", "6-Pin"]. Leere Liste,
    wenn keine Stecker-Angabe erkennbar ist (der häufigste Fall).
    """
    found: list[str] = []
    for match in _PCIE_CONNECTOR_PATTERN.finditer(text):
        label = f"{match.group(1)}-Pin"
        if label not in found:
            found.append(label)
    return found
