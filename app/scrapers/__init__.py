"""Scraper-Paket (Phase 3): eine Quelle pro Modul, gemeinsames Schema in base.py.

Re-exportiert search_kleinanzeigen/search_ebay, damit bestehender Code
(`from scrapers import search_kleinanzeigen, search_ebay`, z.B. in app.py)
unverändert weiterfunktioniert -- reine Umstrukturierung, kein API-Bruch.
"""
from .kleinanzeigen import search_kleinanzeigen
from .ebay import search_ebay
from .base import Listing, Scraper

__all__ = ["search_kleinanzeigen", "search_ebay", "Listing", "Scraper"]
