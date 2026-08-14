"""Duplicate-/Cross-Posting-Erkennung (Reselling-/Arbitrage-Konzept,
STATUS.md Abschnitt 16, Baustein 5).

Ziel: verhindert, dass mehrfach gepostete/identische Angebote (gleicher
Verkaeufer postet dasselbe Geraet erneut, oder auf mehreren Plattformen
parallel -- Kleinanzeigen + eBay) die Marktpreis-Statistik verzerren.

Abgrenzung zur bestehenden seen.json-Dedup (app.py): seen.json verhindert
per exakter URL-Gleichheit, dass DASSELBE Listing zweimal VERARBEITET wird.
Diese Erkennung hier setzt eine Ebene tiefer an -- sie erkennt zwei
VERSCHIEDENE Listings (unterschiedliche URL, ggf. unterschiedliche Quelle),
die mutmasslich dasselbe physische Angebot sind, und verhindert nur, dass
der ZWEITE Preishistorie-Datenpunkt zusaetzlich in price_history.jsonl
landet. Das Matching/found.json/Notification-Gate bleibt komplett
unberuehrt -- jedes gematchte Angebot wird weiterhin normal angezeigt.

Kriterium (bewusst einfach gehalten, siehe Abstimmung): gleiches
price_history_model + normalisierter Titel identisch + Preis innerhalb
Toleranz + innerhalb eines Zeitfensters. Nur der Titel wird verglichen
(keine location) -- Kleinanzeigen-Ortsangaben sind oft zu ungenau/
inkonsistent ("Berlin" vs. "Berlin-Mitte" vs. keine Angabe) und wuerden
echte Duplikate eher verschleiern als bestaetigen. Bei Unsicherheit lieber
mehr Duplikate erkennen als weniger (Marktpreis-Statistik profitiert von
einem sauberen statt vollstaendigen Datenpool).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from price_history import PricePoint

# Abgestimmte Defaults (siehe STATUS.md Abschnitt 16, Baustein 5):
# 5% Preistoleranz, 30 Tage Zeitfenster. Als Modulkonstanten statt Magic
# Numbers direkt im Code -- Config-Anbindung (rules/_global.yaml) ist
# bewusst ein separater, noch nicht freigegebener Folgeschritt (siehe
# Phase-0-Analyse); bis dahin sind sie hier als benannte Defaults hinterlegt
# und ueberschreibbar per Funktionsparameter (z.B. fuer Tests).
DEFAULT_PRICE_TOLERANCE_PCT = 5.0
DEFAULT_WINDOW_DAYS = 30.0

# Fuellwoerter, die in Kleinanzeigen-Titeln haeufig vorkommen, aber keine
# Aussagekraft fuer die Identitaet des Angebots haben -- ohne Entfernung
# wuerden zwei ansonsten identische Titel ("RTX 3060 12GB" vs. "Biete RTX
# 3060 12GB") faelschlich als unterschiedlich gelten.
_TITLE_STOPWORDS = frozenset({
    "biete", "verkaufe", "zu", "verkaufen", "neu", "neuwertig", "wie", "wg",
    "tausch", "tauschen", "vb", "verhandelbar", "top", "sehr", "gut", "guter",
    "zustand",
})

_NON_ALNUM_RE = re.compile(r"[^a-z0-9äöüß ]+")
_MULTI_SPACE_RE = re.compile(r"\s+")


def _fingerprint_words(fingerprint: str) -> tuple[str, ...]:
    """Zerlegt einen normalisierten Fingerprint in eine sortierte Wort-
    Sequenz fuer einen wortstellungs-UNabhaengigen Vergleich (roadmap.md
    Phase 9).

    Grund: normalize_title() erhaelt bewusst die urspruengliche Wort-
    reihenfolge (Format-Stabilitaet fuer bereits geschriebene
    price_history.jsonl-Zeilen, keine Migration noetig) -- zwei
    Cross-Postings desselben Angebots koennen den Titel aber in
    unterschiedlicher Reihenfolge formulieren (z.B. "Asus RTX 3060 12GB"
    vs. "RTX 3060 12GB Asus"), was mit reinem String-Vergleich als
    unterschiedlich gilt und ein echtes Duplikat uebersehen wuerde.

    sorted() statt set(): behaelt Wiederholungen korrekt bei (z.B. zwei
    Vorkommen von "rtx" bleiben zwei Vorkommen) -- ein set() wuerde
    Titel mit unterschiedlicher Wort-HAEUFIGKEIT faelschlich gleichsetzen.
    Bewusst weiterhin rein deterministisch (kein Fuzzy-Matching), nur die
    Reihenfolge wird ignoriert -- alle anderen Woerter muessen weiterhin
    exakt uebereinstimmen (keine Lockerung der Erkennungsgenauigkeit,
    siehe roadmap.md-Vorgabe "keine aggressiven False-Positive-Regeln").
    """
    return tuple(sorted(fingerprint.split()))


def normalize_title(title: str) -> str:
    """Normalisiert einen Angebotstitel fuer den Duplikat-Vergleich.

    Schritte: lowercase, Sonderzeichen entfernen, Fuellwoerter strippen,
    Mehrfach-Whitespace vereinheitlichen. Bewusst simpel/deterministisch
    (kein Fuzzy-Matching/keine externe Bibliothek) -- reicht fuer den
    Zweck (offensichtliche Duplikate/Cross-Postings erkennen), bleibt aber
    leicht nachvollziehbar und testbar.

    Wortreihenfolge bleibt bewusst ERHALTEN (keine Sortierung hier) --
    der wortstellungs-unabhaengige Vergleich passiert erst in
    find_duplicate() ueber _fingerprint_words() (siehe dort), damit sich
    das gespeicherte Fingerprint-Format in price_history.jsonl durch
    diese Verbesserung NICHT aendert (keine Migration bestehender
    Zeilen noetig).

    FIX (STATUS.md Datenqualitaet Nr. 11, Ruleset-Qualitaetssystem):
    deutsche Umlaute (ä/ö/ü/ß) werden NICHT mehr entfernt/durch ein
    Leerzeichen ersetzt -- sie sind Teil der erlaubten Zeichenklasse.
    Vorher wurde z.B. "Röhrenfernseher" zu "r hrenfernseher", wodurch
    JEDE fingerprint-basierte matcher.evaluate()-Revalidierung (u.a.
    app/rule_coverage.py::_is_still_valid()) nie mehr gegen Umlaut-
    haltige match/require_all_of-Begriffe (z.B. "röhrenfernseher",
    "verstärker") matchen konnte -- unabhaengig davon, ob der Titel
    inhaltlich passen wuerde (19 von 355 Regeln in 4 Kategorien
    betroffen: handhelds, konsolen_bundles, retro_konsolen,
    vintage_elektronik). matcher.evaluate() selbst wendet nur title.lower()
    an, verändert Umlaute also nie -- der Fingerprint muss daher exakt in
    diesem Format vorliegen, damit ein Re-Match ueberhaupt moeglich ist.
    Rueckwaertskompatibel fuer die produktive Duplicate-/Cross-Posting-
    Erkennung: find_duplicate() vergleicht in app.py ausschliesslich
    Fingerprints INNERHALB desselben Scan-Laufs (price_points_this_scan),
    nie gegen historisch in price_history.jsonl gespeicherte Fingerprints
    -- die Formataenderung hat daher keine Kontinuitaets-Auswirkung auf
    bereits geschriebene Zeilen. Bereits VOR diesem Fix geschriebene
    price_history.jsonl-Zeilen mit Umlaut-Titeln behalten ihr altes,
    fehlerhaftes Fingerprint-Format (keine rueckwirkende Migration) --
    nur ab jetzt neu geschriebene Zeilen sind korrekt.
    """
    lowered = title.lower()
    cleaned = _NON_ALNUM_RE.sub(" ", lowered)
    words = [w for w in cleaned.split() if w not in _TITLE_STOPWORDS]
    return _MULTI_SPACE_RE.sub(" ", " ".join(words)).strip()


def _price_within_tolerance(price_a: float, price_b: float, tolerance_pct: float) -> bool:
    """Prueft, ob zwei Preise innerhalb der prozentualen Toleranz liegen.

    Toleranz wird relativ zum GROESSEREN der beiden Preise berechnet --
    symmetrisch (Reihenfolge der Argumente egal) und vermeidet eine
    Division durch 0, falls einer der Preise 0 ist (nur dann, wenn beide 0
    sind, gelten sie als gleich).
    """
    if price_a == price_b:
        return True
    reference = max(abs(price_a), abs(price_b))
    if reference == 0:
        return True
    diff_pct = abs(price_a - price_b) / reference * 100
    return diff_pct <= tolerance_pct


def find_duplicate(
    *,
    model: str,
    price: float,
    fingerprint: str,
    existing_points: list[PricePoint],
    price_tolerance_pct: float = DEFAULT_PRICE_TOLERANCE_PCT,
    window_days: float = DEFAULT_WINDOW_DAYS,
    now: datetime | None = None,
) -> PricePoint | None:
    """Sucht in `existing_points` nach einem mutmasslichen Duplikat.

    Gibt den ERSTEN passenden bestehenden PricePoint zurueck (fuer Logging/
    Nachvollziehbarkeit), oder None wenn kein Duplikat gefunden wurde.
    Ein Duplikat liegt vor, wenn ALLE Kriterien erfuellt sind:
    - gleiches `model` (price_history_model)
    - gleicher `fingerprint` (normalisierter Titel, siehe normalize_title() --
      Vergleich ist wortstellungs-unabhaengig, siehe _fingerprint_words())
    - Preis innerhalb `price_tolerance_pct`
    - bestehender Punkt liegt nicht laenger als `window_days` zurueck

    Punkte ohne Fingerprint (aeltere price_history.jsonl-Zeilen vor
    Einfuehrung dieses Features) werden uebersprungen -- ohne Fingerprint
    ist kein Vergleich moeglich, sie zaehlen nicht als Duplikat-Kandidat.
    Kaputte/unparsebare `date`-Werte werden ebenfalls uebersprungen statt
    einen Fehler zu werfen (robuste Auswertung, analog price_stats.py).
    """
    reference_now = now or datetime.now(timezone.utc)

    for point in existing_points:
        if point.model != model:
            continue
        if point.fingerprint is None:
            continue
        # roadmap.md Phase 9: wortstellungs-unabhaengiger Vergleich statt
        # exakter String-Gleichheit -- siehe _fingerprint_words()-Docstring.
        if _fingerprint_words(point.fingerprint) != _fingerprint_words(fingerprint):
            continue
        if not _price_within_tolerance(point.price, price, price_tolerance_pct):
            continue
        try:
            point_date = datetime.fromisoformat(point.date)
        except ValueError:
            continue
        age_days = (reference_now - point_date).total_seconds() / 86400
        if age_days < 0 or age_days > window_days:
            continue
        return point

    return None
