"""Quoka-Scraper. Liefert standardisierte Listing-Dicts (siehe base.py).
Filterung/Matching/Bewertung passiert NICHT hier, sondern in matcher.py.
"""
from __future__ import annotations

import logging
import re
import time

import requests
from bs4 import BeautifulSoup

from .base import Listing

log = logging.getLogger(__name__)

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}


def _price_to_float(text: str) -> float | None:
    """Parst Quokas Preisformat zu einem float.

    Drei beobachtete Varianten (siehe Analyse gegen echte Fixture +
    Live-Verifikation gegen quoka.de, Nutzer-Meldung 2026-08-15,
    GPU-Preis-0€-Diagnose):
    - Normalpreis, dreistellig oder kleiner: "155 EUR" (Ganzzahl, kein
      Trenner).
    - Normalpreis, ab 1000: "1 050 EUR"/"1 000 EUR"/"10 000 EUR" -- hier
      ist LEERZEICHEN der Tausendertrenner (live bestaetigt: Suche nach
      "RTX 4060" auf quoka.de liefert u.a. "1 000 EUR" exakt in diesem
      Format). Bug (Root Cause der 0€-Faelle, siehe FIX-Kommentar unten):
      diese Variante fehlte bisher komplett -- die alte Regex erkannte nur
      "\\d+" (matcht dann faelschlich nur die letzten <=3 Ziffern nach dem
      letzten Leerzeichen, z.B. "1 000 EUR" -> "000" -> 0.0, "1 050 EUR"
      -> "050" -> 50.0 statt 1050.0).
    - Rabatt-Preis (`.new-price`/`.old-price`): "529.0 EUR"/"850.000 EUR"
      -- hier ist der Punkt je nach Nachkommastellen-Anzahl ENTWEDER
      Dezimaltrenner (1-2 Ziffern, "529.0 EUR" = 529,0€) ODER
      Tausendertrenner (exakt 3 Ziffern je Gruppe, deutsche Konvention,
      "1.250 EUR"/"850.000 EUR" = 1.250€/850.000€) -- live gegen
      quoka.de-Fahrzeuganzeigen verifiziert (beide Formate real
      beobachtet).

    Ggf. angehaengter Text wie "VB" (Verhandlungsbasis) wird ignoriert
    (re.search, kein Vollstring-Match).
    """
    text = text.replace("\xa0", " ")
    m = re.search(
        r"(\d{1,3}(?:\.\d{3})+|\d{1,3}(?: \d{3})+|\d+)(?:[.,](\d{1,2}))?\s*EUR",
        text,
    )
    if not m:
        return None
    whole = m.group(1).replace(".", "").replace(" ", "")
    frac = m.group(2) or "0"
    try:
        return float(f"{whole}.{frac}")
    except ValueError:
        return None


def _clean_location(text: str) -> str:
    """Normalisiert das location-Feld analog zu kleinanzeigen.py::_clean_location()
    (kollabiert Whitespace-Läufe aus mehrzeiligem HTML-Markup, z.B.
    "Booßen, Frankfurt (Oder), Brandenburg, 15232").
    """
    return re.sub(r"\s+", " ", text).strip()


# Plugin-Metadaten fuer scrapers/registry.py (Discovery statt Imports,
# Architekturplanung "Plugin-Registry"). Rein additiv, exakt nach dem
# Muster von kleinanzeigen.py/ebay.py.
SCRAPER_NAME = "quoka"


def search_quoka(
    search_terms: list[str], plz: str, radius_km: int, max_price: int
) -> list[Listing]:
    """Signatur folgt exakt dem `Scraper`-Protocol (scrapers/base.py), wie
    bereits bei search_kleinanzeigen()/search_ebay() (Plugin-Registry
    Schritt 3). `plz`/`radius_km`/`max_price` werden hier bewusst NICHT
    verwendet:

    - Die Quoka-Suchseite (`/anzeigen?q=...`) bietet zwar Ortsfilter-Felder
      (Zip/City/Area) im Formular, aber keinen verifizierten, einfachen
      Query-String-Parameter dafuer -- ohne Zugriff auf die echte Live-Seite
      wollte ich hier nichts raten (siehe Analyse-Schritt).
    - `max_price` wird generell nicht im Scraper gefiltert (Phase 3: Scraper
      liefern nur Rohdaten, Bewertung/Filterung passiert in matcher.py) --
      identisch zu search_kleinanzeigen(), das max_price ebenfalls entgegennimmt,
      aber im Funktionskoerper nicht referenziert.
    """
    listings: list[Listing] = []
    for term in search_terms:
        url = f"https://www.quoka.de/anzeigen?q={term}"
        try:
            resp = requests.get(url, headers=UA, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            log.warning("Quoka-Fehler (%s): %s", term, e)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("div.article-item"):
            title_el = item.select_one("h2.article-title a")
            price_el = item.select_one("span.article-price")
            loc_el = item.select_one("p.article-location span")
            desc_el = item.select_one("p.article-description")
            img_el = item.select_one("div.art-img img")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # Sicherheitsnetz analog kleinanzeigen.py: mindestens ein
            # Kernwort des Suchbegriffs muss im Titel vorkommen, falls
            # Quoka den Suchbegriff aus irgendeinem Grund ignoriert.
            core_words = [w for w in term.lower().split() if len(w) > 2]
            if core_words and not any(w in title.lower() for w in core_words):
                continue

            # Rabatt-Angebote verschachteln ".new-price" (aktueller Preis)
            # und ".old-price" (durchgestrichener Ursprungspreis) im selben
            # Element -- explizit den aktuellen Preis bevorzugen, statt sich
            # auf die Textreihenfolge im kombinierten get_text() zu verlassen.
            new_price_el = item.select_one("span.article-price .new-price")
            price_source = new_price_el if new_price_el else price_el
            price = _price_to_float(price_source.get_text()) if price_source else None
            href = title_el.get("href")
            if isinstance(href, list):
                href = href[0] if href else ""
            href = href or ""
            # Quoka liefert im Gegensatz zu Kleinanzeigen bereits absolute
            # URLs -- kein Domain-Prefix noetig, nur Sicherheitsnetz falls
            # doch mal eine relative URL auftaucht.
            link = "https://www.quoka.de" + href if href.startswith("/") else href

            img_src = img_el.get("src") if img_el else None
            if isinstance(img_src, list):
                img_src = img_src[0] if img_src else None
            images = [img_src] if img_src else []

            listings.append(
                {
                    "source": "Quoka",
                    "title": title,
                    "price": price,
                    "url": link,
                    "location": _clean_location(loc_el.get_text(separator=" ", strip=True)) if loc_el else "",
                    # Anders als bei Kleinanzeigen liefert Quokas Uebersichtsseite
                    # bereits einen echten Anzeigentext -- wird hier uebernommen
                    # statt bewusst leer zu bleiben.
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                    "images": images,
                }
            )
        time.sleep(2)
    return listings
