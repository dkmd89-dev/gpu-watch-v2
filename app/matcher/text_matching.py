"""Term-/Regex-Matching-Primitive und kontextbewusste Exclude-Logik.

Schritt 2 der Modularisierung (siehe Analysebericht): unveraendert aus
matcher/core.py extrahiert. Reine, zustandslose Textpruefungen ohne
Abhaengigkeit auf andere matcher-Untermodule -- daher als erster
inhaltlicher Extraktionsschritt gewaehlt (niedrigstes Risiko).
"""
from __future__ import annotations

import functools
import re

# ============================================================
# Basis-Term-Matching (Ganzwort-Suche via Lookaround statt \b, siehe
# core.py-Kommentar zur Performance-Messung: 21,8% der Matcher-Laufzeit in
# re._compile(), 19,0% in _contains_term() -- daher functools.lru_cache
# auf den kompilierten Patterns. lru_cache ist laut Python-Doku
# thread-safe (interne Sperre), keine zusaetzliche Synchronisation noetig.
# Keine Aenderung der Matcher-Semantik gegenueber dem Vorzustand: identisches
# Pattern, identische re.UNICODE-Flag, nur die Kompilierung wird
# wiederverwendet statt bei jedem Aufruf neu zu erfolgen.
# ============================================================
@functools.lru_cache(maxsize=4096)
def _compiled_term_pattern(term_lower: str) -> re.Pattern[str]:
    return re.compile(r"(?<!\w)" + re.escape(term_lower) + r"(?!\w)", re.UNICODE)


def _contains_term(text: str, term: str) -> bool:
    """Prüft, ob `term` als GANZES WORT (bzw. ganze Wortfolge) in `text` vorkommt.

    Verhindert False-Positives durch Teilstring-Treffer, z.B. dass der
    Ausschluss-Begriff "system" auch in "Betriebssystem" oder "Kühlsystem"
    anschlägt. re.escape() macht auch Terme mit Leerzeichen ("gaming pc")
    oder Sonderzeichen ("nitro+") sicher nutzbar.
    """
    return _compiled_term_pattern(term.lower()).search(text) is not None


def _any_term(text: str, terms: list[str]) -> bool:
    return any(_contains_term(text, t) for t in terms)


# ============================================================
# Kontextbewusster Exclude (Phase 15, kontrollierter Review, "Variante C")
# ============================================================
# Ziel: ein Zubehoer-Begriff wie "ladekabel" soll eine Regel nur dann
# blockieren, wenn er ALLEIN steht ("PS5 Controller Ladekabel" ->
# Standalone-Zubehoer), NICHT wenn er ein echtes Geraet mit erwaehntem
# Zubehoer beschreibt ("PS5 Controller inkl. Ladekabel" -> Bundle).
# exclude/exclude_category koennen das nicht (reine, kontextfreie
# Wort-Praesenz-Pruefung, siehe _contains_term()-Docstring) -- dieser
# Abschnitt ergaenzt eine GENERISCHE, optionale Alternative, die JEDE
# Kategorie ueber das YAML-Feld "exclude_category_unless_preceded_by"
# nutzen kann (kein "if category == ...", siehe evaluate()).
#
# Technik: Negative Lookbehinds, ein Pattern-Fragment pro erlaubtem
# "Bundle-Konnektor" (z.B. "inkl.", "mit", "+"). Identisches Prinzip wie
# bereits produktiv in categories/detectors/lieferumfang.py
# (_NETZTEIL_POSITIVE: "netzteil" gilt nur als positives Lieferumfang-
# Signal, wenn NICHT "ohne "/"kein "/"keine " davorsteht) -- hier nur mit
# umgekehrter Wortliste (Inklusions- statt Negationswoerter) und einem
# anderen Verwendungszweck (Match-/Exclude-Entscheidung statt Deal-Score-
# Signal). Bewusst KEINE zweite, andersartige Kontextlogik erfunden.
#
# Python re verlangt Lookbehinds fester Laenge (kein "(?<!(?:a|b|c)\\s)"
# mit unterschiedlich langen Alternativen) -- daher, identisch zum
# lieferumfang.py-Vorbild, ein eigenes Lookbehind-Fragment pro Konnektor
# statt einer gemeinsamen Gruppe.
@functools.lru_cache(maxsize=4096)
def _compiled_unless_preceded_pattern(
    term_lower: str, connectors_lower: tuple[str, ...]
) -> re.Pattern[str]:
    lookbehinds = "".join(
        rf"(?<!{re.escape(c)}\s)" for c in connectors_lower
    )
    return re.compile(
        lookbehinds + r"(?<!\w)" + re.escape(term_lower) + r"(?!\w)", re.UNICODE
    )


def _contains_term_unless_preceded_by(
    text: str, term: str, connectors: list[str] | tuple[str, ...]
) -> bool:
    """True, wenn `term` als eigenes Wort in `text` vorkommt UND NICHT
    unmittelbar (getrennt durch genau ein Leerzeichen) einer der
    `connectors`-Alternativen vorausgeht.

    Bekannte, vom lieferumfang.py-Vorbild geerbte Einschraenkung: nur
    GENAU EIN Leerzeichen zwischen Konnektor und Begriff wird erkannt
    (Python re erlaubt keine Lookbehinds variabler Laenge wie "\\s+") --
    unueblich formatierte Titel mit mehrfachen Leerzeichen wuerden den
    Konnektor nicht erkennen und den Begriff daher (konservativ) als
    Standalone werten.
    """
    pattern = _compiled_unless_preceded_pattern(
        term.lower(), tuple(c.lower() for c in connectors)
    )
    return pattern.search(text) is not None


def _any_conditional_exclude(text: str, conditional_excludes: dict[str, list[str]]) -> bool:
    """True, wenn MINDESTENS EIN Begriff aus `conditional_excludes` als
    Standalone-Vorkommen (siehe _contains_term_unless_preceded_by())
    in `text` gefunden wird -- OR-Verknuepfung, analog zu _any_term()."""
    return any(
        _contains_term_unless_preceded_by(text, term, connectors)
        for term, connectors in conditional_excludes.items()
    )


# ============================================================
# Kontextbewusster Exclude, Variante 2 (Phase 15, kontrollierter
# Folge-Review, "Gehäuse/Shell-Fix")
# ============================================================
# Andere Kontext-Beziehung als Variante C oben: dort geht es um einen
# Begriff, der bei BUNDLE-Erwaehnung erlaubt ist (Konnektor unmittelbar
# DAVOR). Hier geht es um einen Begriff, der bei einer GERAETE-
# Zustandsbeschreibung ueberall im Titel erlaubt ist, unabhaengig vom
# Abstand ("Gehäuse: leicht vergilbt" vs. "Gehäuse minimal verkratzt" vs.
# "... Display neuwertig, Gehäuse hat leichte Kratzer" -- der Zustandsbegriff
# kann vor, nach oder mit mehreren Woertern Abstand zum Begriff stehen).
# Eine Adjazenz-/Abstandsregel wie bei Variante C waere hier zu spezifisch
# und wuerde reale Formulierungen verfehlen -- daher bewusst eine einfache,
# TITELWEITE Praesenzpruefung statt einer weiteren Regex-Konstruktion.
# Abwaegung: dadurch werden theoretisch auch Titel nicht ausgeschlossen, in
# denen ein Zustandsbegriff UND ein Standalone-Gehäuse-Angebot unabhaengig
# voneinander vorkommen (sehr seltene Kombination in der Praxis) -- ein
# bewusst in Kauf genommener, geringer Recall-Nachteil gegenueber einem
# false-negativ bei einem echten Geraete-Angebot mit Zustandsbeschreibung
# (dessen Vermeidung der eigentliche Zweck dieser Variante ist).
def _any_conditional_exclude_presence(
    text: str, conditional_excludes: dict[str, list[str]]
) -> bool:
    """True, wenn MINDESTENS EIN Begriff aus `conditional_excludes` als
    eigenes Wort in `text` vorkommt UND KEINER der zugehoerigen erlaubten
    Kontext-/Zustandsbegriffe irgendwo im selben Titel vorkommt.

    conditional_excludes: {Begriff: [erlaubte Kontextbegriffe]}, OR-
    verknuepft ueber alle Eintraege (analog zu _any_conditional_exclude()).
    """
    for term, allowed_context_terms in conditional_excludes.items():
        if _contains_term(text, term) and not _any_term(text, allowed_context_terms):
            return True
    return False
