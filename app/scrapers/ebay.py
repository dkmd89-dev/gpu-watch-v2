"""eBay-Scraper (Browse API). Liefert standardisierte Listing-Dicts (siehe base.py).
Filterung/Matching/Bewertung passiert NICHT hier, sondern in matcher.py.
"""
from __future__ import annotations
import os
import logging
import requests

from .base import Listing

log = logging.getLogger(__name__)


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
                "scope": "https://api.ebay.com/oauth/api_scope",
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
                    "url": it.get("itemWebUrl", ""),
                    "location": it.get("itemLocation", {}).get("city", ""),
                    # Standardisiertes Schema (Phase 3), analog zu Kleinanzeigen.
                    # Bewusst leer statt ungeprüfter Annahmen über das exakte
                    # Feldformat der Browse-API-Antwort.
                    "description": "",
                    "images": [],
                }
            )
    return listings
