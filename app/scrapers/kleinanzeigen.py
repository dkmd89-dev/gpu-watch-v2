"""Kleinanzeigen-Scraper. Liefert standardisierte Listing-Dicts (siehe base.py).
Filterung/Matching/Bewertung passiert NICHT hier, sondern in matcher.py.
"""
from __future__ import annotations
import re
import time
import logging
import requests
from bs4 import BeautifulSoup

from .base import Listing

log = logging.getLogger(__name__)

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}


def _price_to_float(text: str) -> float | None:
    m = re.search(r"(\d[\d.]*),?(\d{0,2})\s*€", text.replace("\xa0", " "))
    if not m:
        return None
    whole = m.group(1).replace(".", "")
    frac = m.group(2) or "0"
    try:
        return float(f"{whole}.{frac}")
    except ValueError:
        return None


def _clean_location(text: str) -> str:
    """Normalisiert das location-Feld (Phase-0-Befund k).

    get_text(strip=True) entfernt nur führende/nachfolgende Leerzeichen PRO
    Textknoten -- interne Zeilenumbrüche/Mehrfach-Whitespace innerhalb eines
    einzelnen Textknotens (z.B. zwischen PLZ/Ort und der Entfernungsangabe
    "94539 Grafling\\n ... (349 km)") bleiben dabei erhalten. Hier werden
    daher zusätzlich alle Whitespace-Läufe (Leerzeichen, Tabs, Zeilenumbrüche)
    zu einem einzelnen Leerzeichen kollabiert. Eine strukturierte Aufteilung
    in PLZ/Ort/Entfernung als getrennte Felder ist bewusst nicht Teil dieses
    Schritts -- das ist für das Dashboard/Filter in Phase 8 vorgesehen.
    """
    return re.sub(r"\s+", " ", text).strip()


def search_kleinanzeigen(
    search_terms: list[str], plz: str, radius_km: int, max_price: int
) -> list[Listing]:
    listings: list[Listing] = []
    for term in search_terms:
        query = term.replace(" ", "-").lower()
        url = (
            f"https://www.kleinanzeigen.de/s-{query}/k0"
            f"?locationStr={plz}&radius={radius_km}&sortingField=SORTING_DATE"
        )
        try:
            resp = requests.get(url, headers=UA, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            log.warning("Kleinanzeigen-Fehler (%s): %s", term, e)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("article.aditem"):
            title_el = item.select_one("a.ellipsis")
            price_el = item.select_one(".aditem-main--middle--price-shipping--price")
            loc_el = item.select_one(".aditem-main--top--left")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # Sicherheitsnetz: falls Kleinanzeigen den Suchbegriff aus irgendeinem
            # Grund ignoriert (z.B. durch fehlerhafte URL-Filter), tauchen sonst
            # völlig themenfremde Anzeigen auf. Grobe Plausibilitätsprüfung:
            # mindestens eines der Kernwörter aus dem Suchbegriff muss im Titel stehen.
            core_words = [w for w in term.lower().split() if len(w) > 2]
            if core_words and not any(w in title.lower() for w in core_words):
                continue
            price = _price_to_float(price_el.get_text()) if price_el else None
            href = title_el.get("href", "")
            link = "https://www.kleinanzeigen.de" + href if href.startswith("/") else href
            listings.append(
                {
                    "source": "Kleinanzeigen",
                    "title": title,
                    "price": price,
                    "url": link,
                    "location": _clean_location(loc_el.get_text(separator=" ", strip=True)) if loc_el else "",
                    # Standardisiertes Schema (Phase 3): description/images sind
                    # bewusst leer -- die Übersichtsseite liefert dazu keine
                    # zuverlässigen Daten. Ein Nachladen der Detailseite pro
                    # Angebot würde die Requests pro Scan vervielfachen und ist
                    # ein separater, bewusst noch nicht umgesetzter Schritt.
                    "description": "",
                    "images": [],
                }
            )
        time.sleep(2)
    return listings
