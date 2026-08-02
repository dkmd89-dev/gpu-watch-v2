"""Discovery-basierte Scraper-Registry (Plugin-Architektur, Schritt 1).

Bisher (Phase 3) mussten neue Quellen an ZWEI Stellen von Hand verdrahtet
werden: `scrapers/__init__.py` (Import) und `app.py` (hartcodierter Aufruf
`raw += search_xxx(...)`). Das widerspricht Phase 9 ("Neue Quellen duerfen
ohne Aenderungen an der Kernlogik ergaenzt werden").

Dieses Modul scannt das `scrapers`-Package zur Laufzeit (statt statischer
Imports) und findet automatisch jedes Modul, das sich per Konvention als
Scraper-Plugin zu erkennen gibt:

  - Modul-Attribut `SCRAPER_NAME: str` (z.B. "kleinanzeigen", "ebay")
  - eine Funktion `search_<SCRAPER_NAME>` im selben Modul

WICHTIG (bewusst noch NICHT Teil dieses Schritts): `app.py` ruft
`search_kleinanzeigen()`/`search_ebay()` weiterhin direkt auf, wie bisher.
Diese Registry liefert nur die INFRASTRUKTUR fuer die Discovery -- die
Umstellung von app.py auf die Registry ist ein eigener, separat
freizugebender Schritt, da unterschiedliche Scraper aktuell noch
unterschiedliche Funktionssignaturen haben (siehe scrapers/base.py
Scraper-Protocol-Docstring) und ein direkter Aufruf ueber die Registry
diese Unterschiede erst einmal ueberbruecken muesste.

Rueckwaertskompatibilitaet: reine Ergaenzung. `scrapers/__init__.py` und
alle bestehenden Importe (`from scrapers import search_kleinanzeigen`)
bleiben unveraendert funktionsfaehig.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import Callable

log = logging.getLogger(__name__)

# Module, die selbst KEINE Scraper-Plugins sind, sondern Infrastruktur des
# Packages -- werden beim Discovery-Scan uebersprungen.
_NON_PLUGIN_MODULES = {"base", "registry"}


@dataclass(frozen=True)
class ScraperPlugin:
    """Ergebnis-Eintrag der Discovery: Name + aufrufbare Suchfunktion."""

    name: str
    search: Callable[..., list]


def discover_scrapers() -> dict[str, ScraperPlugin]:
    """Scannt das `scrapers`-Package und liefert alle gefundenen Plugins.

    Ergebnis: {"kleinanzeigen": ScraperPlugin(...), "ebay": ScraperPlugin(...)}.
    Ein Modul ohne `SCRAPER_NAME`-Attribut oder ohne passende
    `search_<name>`-Funktion wird uebersprungen (mit Warnung geloggt),
    statt den gesamten Scan abzubrechen -- ein fehlerhaftes Plugin darf
    nicht alle anderen Quellen lahmlegen.
    """
    import scrapers  # lokal importiert, um Zirkularitaet beim Package-Init zu vermeiden

    plugins: dict[str, ScraperPlugin] = {}

    for module_info in pkgutil.iter_modules(scrapers.__path__):
        mod_name = module_info.name
        if mod_name in _NON_PLUGIN_MODULES or mod_name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"scrapers.{mod_name}")
        except ImportError as e:
            log.warning("Scraper-Plugin '%s' konnte nicht geladen werden: %s", mod_name, e)
            continue

        scraper_name = getattr(module, "SCRAPER_NAME", None)
        if not scraper_name:
            # Kein Plugin (z.B. ein reines Hilfsmodul) -- kein Fehler, nur ueberspringen.
            continue

        search_fn = getattr(module, f"search_{scraper_name}", None)
        if not callable(search_fn):
            log.warning(
                "Scraper-Plugin '%s' definiert SCRAPER_NAME=%r, aber keine "
                "passende Funktion search_%s() -- wird uebersprungen.",
                mod_name, scraper_name, scraper_name,
            )
            continue

        plugins[scraper_name] = ScraperPlugin(name=scraper_name, search=search_fn)

    return plugins
