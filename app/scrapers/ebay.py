"""eBay-Scraper (Browse API). Liefert standardisierte Listing-Dicts (siehe base.py).
Filterung/Matching/Bewertung passiert NICHT hier, sondern in matcher.py.
"""
from __future__ import annotations

import logging
import os
from urllib.parse import urlsplit, urlunsplit

import requests

from .base import Listing

log = logging.getLogger(__name__)


def _stable_item_url(item_web_url: str) -> str:
    """Normalisiert eine eBay itemWebUrl auf einen stabilen, dedup-fähigen Wert.

    Bug-Hintergrund (siehe price_history.jsonl-Analyse): itemWebUrl aus der
    eBay Browse API enthält Query-Parameter wie "?hash=...&amdata=..." --
    das sind Tracking-/Session-Werte, die für DASSELBE physische Angebot
    bei unterschiedlichen API-Aufrufen unterschiedlich ausfallen können.
    Da app.py Listings ausschließlich über item["url"] dedupliziert
    (seen.json, siehe run_scan()), wurde dasselbe eBay-Angebot dadurch bei
    jedem Scan erneut als "neu" behandelt -- sichtbar als massenhafte
    Wiederholungen desselben Preises in price_history.jsonl.

    Die eigentliche Item-Identität steckt stabil im Pfad (z.B.
    "/itm/1234567890"), nicht in der Query. Wir behalten deshalb nur
    Schema, Host und Pfad -- das Ergebnis ist weiterhin eine gültige,
    funktionierende eBay-URL (ohne Tracking-Anhang), aber jetzt stabil
    über mehrere Scans hinweg identisch für dasselbe Angebot.
    """
    if not item_web_url:
        return item_web_url
    parts = urlsplit(item_web_url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _ebay_token() -> str | None:
    """OAuth2 Client-Credentials-Flow für die eBay Browse API.
    Benötigt EBAY_CLIENT_ID und EBAY_CLIENT_SECRET als Umgebungsvariablen
    (aus dem eBay Developer Portal, Production Keyset).
    """
    client_id = os.environ.get("EBAY_CLIENT_ID")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    try:
        resp = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            auth=(client_id, client_secret),
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]
    except requests.RequestException as e:
        log.warning("eBay-Token-Fehler: %s", e)
        return None


def search_ebay(search_terms: list[str], max_price: int, plz: str) -> list[Listing]:
    token = _ebay_token()
    if not token:
        log.info("Kein eBay-Token (EBAY_CLIENT_ID/SECRET fehlt) -- eBay wird übersprungen.")
        return []

    listings: list[Listing] = []
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE",
    }
    for term in search_terms:
        params = {
            "q": term,
            "filter": f"price:[..{max_price}],priceCurrency:EUR,itemLocationCountry:DE,"
            f"conditions:{{USED|NEW}}",
            "limit": "50",
        }
        try:
            resp = requests.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers=headers,
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            log.warning("eBay-Suchfehler (%s): %s", term, e)
            continue

        for it in data.get("itemSummaries", []):
            price_val = it.get("price", {}).get("value")
            listings.append(
                {
                    "source": "eBay",
                    "title": it.get("title", ""),
                    "price": float(price_val) if price_val else None,
                    "url": _stable_item_url(it.get("itemWebUrl", "")),
                    "location": it.get("itemLocation", {}).get("city", ""),
                    # Standardisiertes Schema (Phase 3), analog zu Kleinanzeigen.
                    # Bewusst leer statt ungeprüfter Annahmen über das exakte
                    # Feldformat der Browse-API-Antwort.
                    "description": "",
                    "images": [],
                }
            )
    return listings
