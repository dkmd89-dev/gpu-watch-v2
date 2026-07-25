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
    """Zielvertrag, den jede Scraper-Quelle erfüllen soll.

    HINWEIS (Stand dieses Schritts): search_kleinanzeigen() und
    search_ebay() haben aktuell noch unterschiedliche Parameter-
    reihenfolgen (historisch gewachsen) und erfüllen dieses Protocol
    daher noch nicht exakt. Das Protocol beschreibt die Zielform für
    neue Quellen (Phase 9/10); eine Vereinheitlichung der bestehenden
    zwei Funktionssignaturen ist ein separater, bewusst noch nicht
    umgesetzter Schritt, um hier nicht mehrere Dinge gleichzeitig zu
    ändern. Da Python Protocols strukturell und nicht nominal geprüft
    werden, wird nichts erzwungen -- rein dokumentarisch.
    """

    def __call__(
        self,
        search_terms: list[str],
        plz: str,
        radius_km: int,
        max_price: float,
    ) -> list[Listing]:
        ...
