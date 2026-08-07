"""Discovery-basierte Kategorie-Registry (Plugin-Architektur, analog zu
`scrapers/registry.py`).

Hintergrund: `matcher._load_rules_from_dir()` (Phase 2) erkennt neue
Hardware-Kategorien bereits vollstaendig automatisch -- jede `*.yaml`-Datei
in `rules/` (ausser `_global.yaml`) wird eingelesen, gemergt und ausgewertet,
OHNE dass dafuer Python-Code geaendert werden muss (siehe
tests/test_rules_category_plugin_contract.py, das genau das beweist).

Seit der Matcher-Registry-Migration nutzt `matcher._load_rules_from_dir()`
dieses Modul als EINZIGE Quelle fuer die Kategorie-Discovery (welche
*.yaml-Dateien gibt es, wie heisst die Kategorie). Die anschliessende
produktive Merge-Logik (defaults, globale Ausschluesse, scoring_weights-
Fallback, category_order, Notify-Preis-Override, ...) bleibt unveraendert
in `_load_rules_from_dir()` -- nur die vorher doppelt vorhandene
Datei-Scan-/Parse-Logik wurde zusammengefuehrt.

Rueckwaertskompatibilitaet: reine Ergaenzung, keine bestehende Datei wird
veraendert.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

# Dateien im rules/-Verzeichnis, die selbst KEINE Kategorie sind, sondern
# Infrastruktur (globale Defaults) -- werden beim Discovery-Scan uebersprungen.
_NON_PLUGIN_FILES = {"_global.yaml"}


@dataclass(frozen=True)
class CategoryPlugin:
    """Ergebnis-Eintrag der Discovery: Kategorie-Name + Quelldatei + rohe Config."""

    name: str
    file: Path
    config: dict


def discover_categories(rules_dir: str | Path) -> dict[str, CategoryPlugin]:
    """Scannt ein rules/-Verzeichnis und liefert alle gefundenen Kategorie-Plugins.

    Ergebnis: {"gpu": CategoryPlugin(...), "office_pc": CategoryPlugin(...), ...}.
    Eine Datei ohne gueltigen YAML-Inhalt wird uebersprungen (mit Warnung
    geloggt), statt den gesamten Scan abzubrechen -- eine fehlerhafte
    Kategorie-Datei darf nicht alle anderen Kategorien lahmlegen (identisches
    Verhalten zu discover_scrapers()).

    `name` ist das YAML-Feld "category", falls vorhanden, sonst der
    Dateiname ohne Endung -- identisch zum Fallback in
    matcher._load_rules_from_dir(), damit beide Discovery-Wege bei
    gleichem rules/-Verzeichnis zum selben Kategorie-Namen kommen.
    """
    rules_path = Path(rules_dir)
    plugins: dict[str, CategoryPlugin] = {}

    if not rules_path.is_dir():
        return plugins

    for yaml_file in sorted(rules_path.glob("*.yaml")):
        # Identische Ausschlussregel wie matcher._load_rules_from_dir():
        # NUR "_global.yaml" ist Infrastruktur, keine pauschale
        # Unterstrich-Regel -- sonst kaemen beide Discovery-Wege bei
        # exotischen Dateinamen (z.B. Test-Fixtures) zu unterschiedlichen
        # Ergebnissen.
        if yaml_file.name in _NON_PLUGIN_FILES:
            continue

        try:
            config = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            log.warning(
                "Kategorie-Plugin '%s' konnte nicht geladen werden: %s",
                yaml_file.name, e,
            )
            continue

        category_name = config.get("category", yaml_file.stem)
        plugins[category_name] = CategoryPlugin(
            name=category_name, file=yaml_file, config=config
        )

    return plugins
