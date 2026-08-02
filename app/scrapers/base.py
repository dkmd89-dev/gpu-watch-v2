"""Formaler Vertrag für alle Scraper-Quellen (Phase 3).

Jede Quelle (Kleinanzeigen, eBay, künftig Quoka/markt.de/...) liefert
ausschließlich standardisierte Rohdaten in Form von `Listing`-Objekten.
Bewertung/Filterung/Matching findet NICHT hier statt, sondern
ausschließlich in matcher.py.

Hinweis zur Rückwärtskompatibilität: `Listing` ist ein `TypedDict`, also
zur Laufzeit ein ganz normales `dict`. Bestehender Code, der mit
`item["title"]`, `item["price"]` etc. auf Listings zugreift (app.py,
notify.py), funktioniert dadurch unverändert weiter -- TypedDict dient
hier ausschließlich der Dokumentation/Typprüfung, nicht als neue
Laufzeit-Klasse.
"""
from __future__ import annotations
from typing import Protocol, TypedDict


class Listing(TypedDict):
    """Standardisiertes Schema, das jeder Scraper pro Angebot liefert."""

    source: str
    title: str
    price: float | None
    url: str
    location: str
    description: str
    images: list[str]


class Scraper(Protocol):
    """Vertrag, den jede Scraper-Quelle erfüllt: search_<name>(search_terms,
    plz, radius_km, max_price) -> list[Listing].

    Seit Schritt 3 der Plugin-Registry erfüllen search_kleinanzeigen() UND
    search_ebay() dieses Protocol exakt (gleiche Parameterreihenfolge).
    Dadurch kann app.py jedes über scrapers/registry.py gefundene Plugin
    generisch mit denselben vier Argumenten aufrufen -- der bisherige
    Übergangs-Adapter (_SCRAPER_CALL_ARGS) entfällt. Eine neue Quelle
    (Quoka, markt.de, ...) muss dieses Protocol ebenfalls erfüllen, dann
    wird sie ohne jede Codeänderung an app.py automatisch mitgescannt.

    Da Python Protocols strukturell und nicht nominal geprüft werden, wird
    nichts zur Laufzeit erzwungen -- rein dokumentarisch/als Konvention.
    """

    def __call__(
        self,
        search_terms: list[str],
        plz: str,
        radius_km: int,
        max_price: float,
    ) -> list[Listing]:
        ...
