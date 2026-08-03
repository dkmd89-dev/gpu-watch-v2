"""eBay-Scraper (Browse API). Liefert standardisierte Listing-Dicts (siehe base.py).
Filterung/Matching/Bewertung passiert NICHT hier, sondern in matcher.py.
"""
from __future__ import annotations

import logging
import os
import time
from urllib.parse import urlsplit, urlunsplit

import requests

from .base import Listing

log = logging.getLogger(__name__)

# Bugfix (siehe STATUS.md): search_ebay() feuerte bisher alle Suchbegriffe
# ohne jede Pause hintereinander an die eBay Browse API -- bei ~90
# Suchbegriffen pro Scan wurde dadurch Sekunden-Rate-Limit von eBay sofort
# ueberschritten (jeder einzelne Request lieferte "429 Too Many Requests",
# siehe gpu_watch.log 2026-08-03). Analog zu scrapers/kleinanzeigen.py
# (dort bereits `time.sleep(2)`), aber zusaetzlich per Env-Var konfigurierbar
# (gleiches Muster wie FOUND_MAX_ITEMS/LOG_MAX_BYTES in app.py) und mit
# gezieltem Retry-Backoff nur fuer 429, um Requests nicht unnoetig zu
# verlangsamen, wenn eBay (noch) nicht drosselt.
EBAY_REQUEST_DELAY_SECONDS = float(os.environ.get("EBAY_REQUEST_DELAY_SECONDS", "1.0"))
EBAY_MAX_RETRIES_429 = int(os.environ.get("EBAY_MAX_RETRIES_429", "3"))
EBAY_RETRY_BACKOFF_SECONDS = float(os.environ.get("EBAY_RETRY_BACKOFF_SECONDS", "2.0"))
EBAY_CIRCUIT_BREAKER_THRESHOLD = int(os.environ.get("EBAY_CIRCUIT_BREAKER_THRESHOLD", "3"))


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


# Plugin-Metadaten fuer scrapers/registry.py (Discovery statt Imports,
# Architekturplanung "Plugin-Registry").
SCRAPER_NAME = "ebay"


def search_ebay(
    search_terms: list[str], plz: str, radius_km: int, max_price: int
) -> list[Listing]:
    """Signatur vereinheitlicht (Schritt 3/3 Plugin-Registry) auf das
    `Scraper`-Protocol aus scrapers/base.py: (search_terms, plz, radius_km,
    max_price) -- identisch zu search_kleinanzeigen(). Vorher: (search_terms,
    max_price, plz), kein radius_km.

    BREAKING CHANGE fuer Aufrufer mit POSITIONELLEN Argumenten (Reihenfolge
    von max_price/plz vertauscht sich). Alle bekannten Aufrufstellen im
    Repo nutzen bereits Keyword-Argumente (siehe tests/test_scraper_ebay.py)
    oder werden ueber die Registry per Protocol-Reihenfolge aufgerufen --
    dort war bisher explizit ein Uebergangs-Adapter (_SCRAPER_CALL_ARGS in
    app.py) noetig, der mit diesem Schritt entfaellt.

    `plz` und `radius_km` werden von der eBay Browse API aktuell NICHT
    unterstuetzt (keine Umkreissuche per PLZ in diesem Endpoint) und bleiben
    daher ungenutzte Parameter -- rein fuer Signatur-Kompatibilitaet mit dem
    Protocol/der Registry. Filterung erfolgt weiterhin nur ueber
    itemLocationCountry:DE (siehe unten).
    """
    token = _ebay_token()
    if not token:
        log.info("Kein eBay-Token (EBAY_CLIENT_ID/SECRET fehlt) -- eBay wird übersprungen.")
        return []

    listings: list[Listing] = []
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE",
    }
    # Bugfix (Fortsetzung, siehe STATUS.md Abschnitt 20): Der Retry-mit-
    # Backoff aus Abschnitt 19 geht von TRANSIENTEM Sekunden-Throttling aus.
    # In der Praxis (gpu_watch.log 03.08., 06:09 Uhr) blieben 73 von 74
    # gedrosselten Suchbegriffen trotz vollem Retry dauerhaft blockiert --
    # vermutlich ein laenger anhaltendes Kontingent-/App-Limit, kein
    # Sekunden-Throttle. Retry+Backoff fuer JEDEN der ~90 Suchbegriffe
    # einzeln durchzuziehen liess einzelne Scans dadurch auf bis zu ~26
    # Minuten anwachsen (vorher 2-6 Minuten). Circuit-Breaker: sobald
    # EBAY_CIRCUIT_BREAKER_THRESHOLD Suchbegriffe HINTEREINANDER trotz
    # voller Retry-Kette an 429 scheitern, wird der Rest der Suchbegriffe
    # fuer DIESEN Scan uebersprungen (ein Log-Eintrag statt ~70 weitere
    # sinnlose Timeouts). Naechster Scan-Durchlauf versucht es regulaer
    # wieder -- kein dauerhaftes Abschalten von eBay.
    consecutive_429_failures = 0
    for i, term in enumerate(search_terms):
        params = {
            "q": term,
            "filter": f"price:[..{max_price}],priceCurrency:EUR,itemLocationCountry:DE,"
            f"conditions:{{USED|NEW}}",
            "limit": "50",
        }

        data = None
        last_status_code = None
        for attempt in range(EBAY_MAX_RETRIES_429 + 1):
            try:
                resp = requests.get(
                    "https://api.ebay.com/buy/browse/v1/item_summary/search",
                    headers=headers,
                    params=params,
                    timeout=20,
                )
                # getattr() statt direktem Attributzugriff: bestehende Tests
                # (tests/test_scraper_ebay.py) mocken die Response bewusst
                # minimal ohne status_code/headers -- soll fuer den regulaeren
                # Erfolgsfall unveraendert funktionieren (Rueckwaertskompatibilitaet).
                status_code = getattr(resp, "status_code", None)
                last_status_code = status_code
                if status_code == 429 and attempt < EBAY_MAX_RETRIES_429:
                    # eBay drosselt -- Retry-After respektieren, falls vorhanden,
                    # sonst exponentiellen Backoff verwenden.
                    wait = EBAY_RETRY_BACKOFF_SECONDS * (2 ** attempt)
                    retry_after = getattr(resp, "headers", {}).get("Retry-After")
                    if retry_after:
                        try:
                            wait = max(wait, float(retry_after))
                        except ValueError:
                            pass
                    log.warning(
                        "eBay-Rate-Limit (%s): 429, Retry in %.1fs (Versuch %d/%d)",
                        term, wait, attempt + 1, EBAY_MAX_RETRIES_429,
                    )
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.RequestException as e:
                log.warning("eBay-Suchfehler (%s): %s", term, e)
                break

        if data is not None:
            consecutive_429_failures = 0
        elif last_status_code == 429:
            consecutive_429_failures += 1
            if consecutive_429_failures >= EBAY_CIRCUIT_BREAKER_THRESHOLD:
                skipped = len(search_terms) - (i + 1)
                log.warning(
                    "eBay scheint dauerhaft blockiert (%d Suchbegriffe in Folge trotz "
                    "Retries an 429 gescheitert) -- breche verbleibende %d Suchbegriffe "
                    "fuer diesen Scan ab. Naechster Scan versucht es wieder.",
                    consecutive_429_failures, skipped,
                )
                break
        else:
            # Andere Fehlerursache (Timeout, DNS, ...) -- kein Hinweis auf
            # anhaltende eBay-Drosselung, Zaehler bewusst nicht erhoehen.
            consecutive_429_failures = 0

        # Zwischen aufeinanderfolgenden Suchbegriffen bewusst pausieren, um
        # eBays Sekunden-Rate-Limit gar nicht erst zu erreichen (siehe
        # Kommentar zu EBAY_REQUEST_DELAY_SECONDS oben). Nicht nach dem
        # letzten Term -- unnoetige Wartezeit am Ende des Scans vermeiden.
        if i < len(search_terms) - 1 and EBAY_REQUEST_DELAY_SECONDS > 0:
            time.sleep(EBAY_REQUEST_DELAY_SECONDS)

        if data is None:
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
