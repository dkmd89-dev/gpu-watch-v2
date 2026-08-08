"""Zustand-Erkennung aus Angebotstiteln (roadmap.md Phase 6, Schritt 6b).

Reine, seiteneffektfreie Text-Parser -- keine Bewertungslogik (siehe
scoring/deal_score.py, wo die "zustand"-Komponente aktuell einen
neutralen Platzhalter liefert; dieses Modul liefert nur die rohe
Erkennung. Die Score-Integration UND die Aktivierung des zugehörigen
YAML-Gewichts sind bewusst separate, eigene Folgeschritte -- siehe
roadmap.md Phase 6: "Keine Gewichtung aktivieren, solange die Erkennung
nicht ausreichend zuverlässig getestet ist.").

Vokabular exakt aus dem Auftrag (roadmap.md Phase 6): neu / wie neu /
sehr gut / gut / gebraucht / beschädigt / defekt / Bastler.

NUR der Titel wird ausgewertet (analog zu allen bestehenden Detectors in
diesem Paket) -- die Beschreibung (`description`) wird von matcher.py::
evaluate() aktuell gar nicht entgegengenommen, das waere eine groessere,
eigene Erweiterung ausserhalb dieses Schritts. Bekannte Grenze: ein
Zustand, der nur in der Beschreibung (nicht im Titel) genannt wird, wird
dadurch nicht erkannt -- in der Praxis nennen viele Anzeigen den Zustand
aber bereits im Titel (z.B. "RTX 3060 12GB TOP Zustand, wie neu").

Liefert None, wenn der Titel keine erkennbare Zustandsangabe enthaelt --
der haeufigste Fall (die meisten Titel nennen gar keinen Zustand explizit).
Das ist bewusst KEIN Fehlerfall, analog zu den uebrigen Detectors.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

CONDITION_NEU = "Neu"
CONDITION_WIE_NEU = "Wie neu"
CONDITION_SEHR_GUT = "Sehr gut"
CONDITION_GUT = "Gut"
CONDITION_GEBRAUCHT = "Gebraucht"
CONDITION_BESCHAEDIGT = "Beschädigt"
CONDITION_DEFEKT = "Defekt"
CONDITION_BASTLER = "Bastler"


@dataclass(frozen=True)
class ConditionMatch:
    condition: str  # einer der CONDITION_*-Werte oben


# Reihenfolge ist entscheidend: spezifischere/laengere Formulierungen
# werden VOR den kuerzeren, allgemeineren Begriffen geprueft, die sie als
# Teilstring enthalten -- sonst wuerde z.B. "wie neu" faelschlich schon
# durch das allgemeinere \bneu\b-Muster erkannt, bevor die spezifischere
# Regel ueberhaupt zum Zug kommt (\bneu\b matcht das Wort "neu" INNERHALB
# von "wie neu" ebenso). Gleiches Prinzip wie in case.py.
#
# "Bastler" und "defekt" werden bewusst VOR "beschädigt" geprueft: ein
# als Bastlergeraet/defekt beschriebenes Angebot ist ein staerkeres,
# eindeutigeres Signal als das allgemeinere "beschädigt" (das auch nur
# kosmetische Schaeden meinen kann). "Bastler" wiederum vor "defekt",
# da eine explizite Bastler-Angabe zusaetzlich signalisiert, dass das
# Geraet nicht als funktionsfaehig verkauft wird (staerkere Aussage als
# reines "defekt", das sich z.B. auch auf ein Einzelteil beziehen kann).
#
# Adjektiv-Endungen (er/e/es/en/em) werden bewusst mit abgedeckt --
# deutsche Anzeigentexte flektieren haeufig ("gebrauchter Laptop",
# "defektes Netzteil", "in gutem Zustand"), eine reine Grundform-Suche
# wuerde diese sehr haeufigen Formulierungen verpassen.
_ADJ_ENDING = r"(er|e|es|en|em)?"
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(wie\s+neu|neuwertig)\b", re.IGNORECASE), CONDITION_WIE_NEU),
    (re.compile(r"\bbastler(gerät|geraet)?\b", re.IGNORECASE), CONDITION_BASTLER),
    (re.compile(rf"\b(defekt|kaputt){_ADJ_ENDING}\b", re.IGNORECASE), CONDITION_DEFEKT),
    (re.compile(rf"\bbesch(ä|ae)digt{_ADJ_ENDING}\b", re.IGNORECASE), CONDITION_BESCHAEDIGT),
    (re.compile(rf"\bsehr\s+gut{_ADJ_ENDING}\s*(zustand)?\b", re.IGNORECASE), CONDITION_SEHR_GUT),
    (re.compile(rf"\bneu{_ADJ_ENDING}\b", re.IGNORECASE), CONDITION_NEU),
    (re.compile(rf"\bgut{_ADJ_ENDING}\s*(zustand)?\b", re.IGNORECASE), CONDITION_GUT),
    (re.compile(rf"\bgebraucht{_ADJ_ENDING}\b", re.IGNORECASE), CONDITION_GEBRAUCHT),
]


def detect_condition(text: str) -> ConditionMatch | None:
    """Erkennt eine Zustandsangabe aus einem Angebotstitel.

    BEKANNTE GRENZEN:
    - Nur Titel, keine Beschreibung (siehe Moduldoku oben).
    - "gut"/"guter Zustand" ist ein sehr generisches Muster und kann in
      anderen Zusammenhaengen fehlklassifizieren (z.B. "guter Preis" wird
      NICHT erkannt, da "Zustand" oder ein direktes "gut"-Wort verlangt
      wird -- aber ein Titel wie "gut erhaltenes Netzteil" matcht ebenso
      auf CONDITION_GUT, was inhaltlich korrekt ist). Kein bekannter
      systematischer Fehlklassifizierungsfall, aber wie bei allen
      Text-Heuristiken keine Garantie -- siehe roadmap.md-Vorgabe, das
      zugehoerige Scoring-Gewicht erst nach Verlaesslichkeitspruefung an
      echten Daten zu aktivieren.
    """
    for pattern, label in _PATTERNS:
        if pattern.search(text):
            return ConditionMatch(condition=label)

    return None
