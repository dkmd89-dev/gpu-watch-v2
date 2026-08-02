"""Discovery-basierte Detector-Registry (Plugin-Architektur, analog zu
`scrapers/registry.py` und `categories/registry.py`).

Hintergrund: `categories/detectors/` enthaelt bereits acht unabhaengige
Erkennungsmodule (cpu, ram, storage, case, gpu, psu, pcie, windows,
manufacturer -- neun tatsaechlich). Jedes exportiert per Konvention eine
oder mehrere oeffentliche `detect_<name>(text)`-Funktionen. `matcher.py`
importiert diese aktuell statisch (`from categories.detectors.cpu import
detect_cpu`, ...) und bleibt das auch weiterhin so (siehe unten) -- dieses
Modul liefert NUR die Discovery-Infrastruktur, analog zu Schritt 1 der
Scraper-Registry und zur bestehenden `categories/registry.py`.

WICHTIG (bewusst wie bei den beiden anderen Registries): `matcher.py` wird
NICHT auf diese Registry umgestellt. Die heutigen statischen Imports sind
laut Docstring der Scraper-Registry "deutlich risikoaermer", weil jede
Requirement-Pruefung in `matcher.py` genau EINEN bestimmten Detector mit
bekannter Signatur braucht (z.B. `_evaluate_hardware_requirements()` ruft
`detect_ram_gb()` und `detect_ram_type()` gezielt und in fester Reihenfolge
auf) -- eine generische "rufe alle gefundenen Detectors auf"-Schleife wuerde
hier keinen echten Mehrwert bieten und nur unnoetiges Risiko fuer den
produktiven Matching-Pfad schaffen. Diese Registry dient stattdessen als:
  - Discovery-Bestandsaufnahme ("welche Detectors gibt es aktuell?"),
  - Grundlage fuer generische Tests (z.B. "jeder Detector liefert bei
    leerem Text None/False/[] und wirft nie eine Exception"),
  - Anlaufpunkt fuer kuenftiges Plugin-Tooling.

Rueckwaertskompatibilitaet: reine Ergaenzung, keine bestehende Datei wird
veraendert.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
import re
from dataclasses import dataclass
from typing import Callable

log = logging.getLogger(__name__)

# Module im detectors-Package, die selbst KEINE Detector-Plugins sind,
# sondern Infrastruktur -- werden beim Discovery-Scan uebersprungen.
_NON_PLUGIN_MODULES = {"registry"}

# Erkennt oeffentliche Detector-Funktionen per Namenskonvention
# "detect_<name>" (z.B. detect_ram_gb, detect_dedicated_gpu). Private
# Hilfsfunktionen (_size_to_gb, _intel_generation, ...) matchen bewusst
# NICHT, da sie mit "_" beginnen.
_DETECT_FN_PATTERN = re.compile(r"^detect_(\w+)$")


@dataclass(frozen=True)
class DetectorPlugin:
    """Ergebnis-Eintrag der Discovery: Name + Modul + aufrufbare Funktion."""

    name: str
    module: str
    fn: Callable[[str], object]


def discover_detectors() -> dict[str, DetectorPlugin]:
    """Scannt das `categories.detectors`-Package und liefert alle gefundenen
    Detector-Funktionen.

    Ergebnis: {"cpu": DetectorPlugin(...), "ram_gb": DetectorPlugin(...),
    "ram_type": DetectorPlugin(...), "ssd_gb": DetectorPlugin(...), ...}.
    Module mit mehreren `detect_*`-Funktionen (z.B. `storage.py` mit
    `detect_ssd_gb`/`detect_hdd_gb`/`detect_nvme`) liefern entsprechend
    mehrere Eintraege -- anders als bei der Scraper-Registry (genau EIN
    `search_<name>` pro Modul) ist das Verhaeltnis Modul:Detector hier
    1:n statt 1:1.

    Ein Modul, das nicht importiert werden kann, wird uebersprungen (mit
    Warnung geloggt), statt den gesamten Scan abzubrechen -- ein
    fehlerhaftes Modul darf nicht alle anderen Detectors lahmlegen
    (identisches Verhalten zu discover_scrapers()/discover_categories()).
    """
    import categories.detectors as detectors_pkg

    plugins: dict[str, DetectorPlugin] = {}

    for module_info in pkgutil.iter_modules(detectors_pkg.__path__):
        mod_name = module_info.name
        if mod_name in _NON_PLUGIN_MODULES or mod_name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"categories.detectors.{mod_name}")
        except ImportError as e:
            log.warning("Detector-Modul '%s' konnte nicht geladen werden: %s", mod_name, e)
            continue

        for attr_name in dir(module):
            match = _DETECT_FN_PATTERN.match(attr_name)
            if not match:
                continue

            candidate = getattr(module, attr_name)
            if not callable(candidate):
                continue

            detector_name = match.group(1)
            plugins[detector_name] = DetectorPlugin(
                name=detector_name, module=mod_name, fn=candidate
            )

    return plugins
