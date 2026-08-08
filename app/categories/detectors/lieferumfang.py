"""Lieferumfang-Erkennung aus Angebotstiteln (roadmap.md Phase 6, Schritt 6c).

Reine, seiteneffektfreie Text-Parser -- keine Bewertungslogik (siehe
scoring/deal_score.py, wo die "lieferumfang"-Komponente aktuell einen
neutralen Platzhalter liefert; dieses Modul liefert nur die rohe
Erkennung. Die Score-Integration UND die Aktivierung des zugehörigen
YAML-Gewichts sind bewusst separate, eigene Folgeschritte -- analog zu
condition.py/Schritt 6b, siehe dortige Moduldoku für die Begründung.

Vokabular exakt aus dem Auftrag (roadmap.md Phase 6):
- Positive Signale: OVP, Rechnung, Originalzubehör, Netzteil, Controller,
  Zubehör
- Negative Signale: ohne Netzteil, nur Gerät, defekt

ANDERS als condition.py (genau EIN Zustand pro Angebot) sind hier MEHRERE
gleichzeitige Signale der Normalfall (z.B. "OVP, Rechnung, Zubehör" in
einem Titel) -- daher keine Ein-Label-Klassifikation, sondern zwei Listen
(positive_signals/negative_signals).

NUR der Titel wird ausgewertet (gleiche Einschränkung wie condition.py --
`description` wird von matcher.py::evaluate() aktuell nicht entgegen-
genommen, siehe dortige Moduldoku für die vollständige Begründung).
"""
from __future__ import annotations
import re
from dataclasses import dataclass

SIGNAL_OVP = "OVP"
SIGNAL_RECHNUNG = "Rechnung"
SIGNAL_ORIGINALZUBEHOER = "Originalzubehör"
SIGNAL_NETZTEIL = "Netzteil"
SIGNAL_CONTROLLER = "Controller"
SIGNAL_ZUBEHOER = "Zubehör"

SIGNAL_OHNE_NETZTEIL = "ohne Netzteil"
SIGNAL_NUR_GERAET = "nur Gerät"
SIGNAL_DEFEKT = "defekt"


@dataclass(frozen=True)
class LieferumfangMatch:
    positive_signals: tuple[str, ...]  # z.B. ("OVP", "Rechnung")
    negative_signals: tuple[str, ...]  # z.B. ("ohne Netzteil",)


# Negative Muster werden VOR den positiven geprueft (siehe
# detect_lieferumfang()) -- "ohne Netzteil" darf NICHT zusaetzlich
# faelschlich das allgemeinere positive "Netzteil"-Muster ausloesen.
# Der Ausschluss erfolgt ueber ein Lookbehind direkt im Netzteil-Muster
# (siehe _POSITIVE_PATTERNS unten), nicht ueber die Pruefreihenfolge
# allein -- beide Listen werden vollstaendig durchsucht (anders als bei
# condition.py gibt es hier kein "erster Treffer gewinnt").
_NEGATIVE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(ohne|kein[e]?)\s+netzteil\b", re.IGNORECASE), SIGNAL_OHNE_NETZTEIL),
    (re.compile(r"\bnur\s+(das\s+)?ger(ä|ae)t\b", re.IGNORECASE), SIGNAL_NUR_GERAET),
    (re.compile(r"\bdefekt(er|e|es|en|em)?\b", re.IGNORECASE), SIGNAL_DEFEKT),
]

# Netzteil-Muster mit Lookbehind: matcht NICHT, wenn direkt "ohne "/"kein "/
# "keine " davorsteht (das ist bereits ueber _NEGATIVE_PATTERNS abgedeckt).
# Python-re verlangt Lookbehinds fester Laenge, daher drei einzelne
# Alternativen statt einer variablen Gruppe.
_NETZTEIL_POSITIVE = re.compile(
    r"(?<!ohne )(?<!kein )(?<!keine )\bnetzteil\b", re.IGNORECASE
)

_POSITIVE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bovp\b", re.IGNORECASE), SIGNAL_OVP),
    (re.compile(r"\brechnung\b", re.IGNORECASE), SIGNAL_RECHNUNG),
    (
        re.compile(r"\boriginal(es|e)?\s*zubeh(ö|oe)r\b", re.IGNORECASE),
        SIGNAL_ORIGINALZUBEHOER,
    ),
    (_NETZTEIL_POSITIVE, SIGNAL_NETZTEIL),
    (re.compile(r"\bcontroller\b", re.IGNORECASE), SIGNAL_CONTROLLER),
    # Lookbehind verhindert zwei Faelle:
    # 1. Doppel-Signal bei "original Zubehör" (mit Leerzeichen) -- dort
    #    matcht bereits das spezifischere Originalzubehör-Muster oben,
    #    ein zusaetzliches generisches "Zubehör"-Signal fuer denselben
    #    Text waere eine irrefuehrende doppelte Zaehlung derselben
    #    Textstelle (bei "originalzubehör" zusammengeschrieben besteht
    #    dieses Risiko ohnehin nicht, siehe Kommentar oben -- keine
    #    Wortgrenze vor "zubehör" innerhalb des zusammengesetzten Worts).
    # 2. Falsches positives Signal bei "kein Zubehör"/"ohne Zubehör" --
    #    das verneint den Lieferumfang, darf also nicht als positives
    #    Signal gezaehlt werden.
    (
        re.compile(
            r"(?<!original )(?<!originale )(?<!originales )"
            r"(?<!kein )(?<!keine )(?<!ohne )"
            r"\bzubeh(ö|oe)r\b",
            re.IGNORECASE,
        ),
        SIGNAL_ZUBEHOER,
    ),
]


def detect_lieferumfang(text: str) -> LieferumfangMatch | None:
    """Erkennt Lieferumfang-Signale (positiv wie negativ) aus einem
    Angebotstitel. Liefert None, wenn GAR KEIN Signal gefunden wurde --
    der haeufigste Fall (die meisten Titel nennen den Lieferumfang gar
    nicht explizit). Andernfalls ein LieferumfangMatch, dessen Listen
    jeweils leer sein koennen (z.B. nur positive, keine negativen
    Signale, oder umgekehrt).

    BEKANNTE GRENZEN:
    - Nur Titel, keine Beschreibung (siehe Moduldoku oben).
    - "defekt" ueberschneidet sich bewusst mit condition.py -- ein
      Angebot kann sowohl einen erkannten Zustand ("Defekt") als auch
      ein Lieferumfang-Signal ("defekt" als negatives Signal, z.B. wenn
      explizit ein Teil des Lieferumfangs als defekt beschrieben wird)
      liefern. Beide Detectors sind unabhaengig, keine gegenseitige
      Abstimmung -- das entspricht der Vokabular-Vorgabe in roadmap.md,
      die "defekt" in beiden Listen (Zustand UND Lieferumfang) fuehrt.
    """
    positive = [
        label for pattern, label in _POSITIVE_PATTERNS if pattern.search(text)
    ]
    negative = [
        label for pattern, label in _NEGATIVE_PATTERNS if pattern.search(text)
    ]

    if not positive and not negative:
        return None

    return LieferumfangMatch(
        positive_signals=tuple(positive), negative_signals=tuple(negative)
    )
