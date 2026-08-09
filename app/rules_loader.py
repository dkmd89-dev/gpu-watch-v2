"""Rules-Cache (Phase 15, Schritt 6 -- PHASE15_OPTIMIERUNG.md, Abschnitte
19-21): verhindert, dass `matcher.load_rules()` (YAML-Parsing aller
Kategorie-Dateien) bei JEDEM API-Request neu ausgefuehrt wird.

Baseline (Phase 15, STOP 1, gemessen gegen das echte rules/-Verzeichnis,
19 YAML-Dateien): `load_rules()` kostet ~310ms pro Aufruf (cold und warm
nahezu identisch, da reines YAML-Parsing ohne eigenes Caching). Aktuell
(vor diesem Modul) wird das bei JEDEM Request auf "/", "/api/found" UND
"/api/status" erneut ausgefuehrt (siehe api/deals.py, api/status.py) --
d.h. ~310ms YAML-Parsing-Overhead pro Dashboard-Aufruf.

Architektur
-----------
`get_rules(path)` ist ein Drop-in-Ersatz fuer `matcher.load_rules(path)`
mit Cache. Invalidierung NICHT ueber TTL (Auftrag: "keine stale Rules
dauerhaft verwenden", aber auch "kein unnoetiges Neuladen") und NICHT
ueber Neu-Parsen+Hash-Vergleich bei jedem Aufruf (das waere derselbe
Kostenpunkt, den der Cache gerade vermeiden soll), sondern ueber einen
GUENSTIGEN Datei-Fingerabdruck (Name+mtime_ns+Groesse aller Dateien, die
load_rules() tatsaechlich liest -- siehe `_fs_fingerprint()`): nur wenn
sich DAS aendert, wird tatsaechlich neu geparst.

`compute_ruleset_signature()` (matcher.py, bereits bestehend fuer Phase
11/Punkt B) wird NICHT dupliziert, sondern als Ruleset-Signatur ueber die
bereits geparsten Regeln weiterverwendet -- siehe `get_ruleset_hash()`,
das den zuletzt berechneten Hash aus dem Cache zurueckgibt statt ihn
erneut zu berechnen. Faellt der Datei-Fingerabdruck auseinander (Datei
beruehrt, aber Inhalt unveraendert), wird zwar neu geparst, der dabei neu
berechnete `compute_ruleset_signature()`-Wert bleibt aber identisch --
Aufrufer, die NUR den Hash zum Vergleich nutzen (z.B. presence_tracking/
category_validation), sehen dadurch korrekt "kein inhaltlicher Wechsel".

Thread-Sicherheit: ein `threading.Lock` schuetzt Lesen+Schreiben des
Cache-Eintrags (analog zu category_validation.py::_cache_lock). Bewusst
EIN Lock ueber den gesamten Cache (nicht pro Pfad) -- die Anwendung nutzt
in der Praxis exakt einen rules_dir-Pfad (siehe app.py::RULES_DIR), ein
Mehrpfad-Betrieb ist nicht vorgesehen; die Cache-Struktur unterstuetzt es
dennoch (Dict-Key = Pfad), um Tests mit isolierten Verzeichnissen nicht
gegenseitig zu beeinflussen.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from matcher import compute_ruleset_signature, load_rules

# Dateiname der Komponentenwert-Zuordnungstabelle, die load_rules()
# zusaetzlich zum *.yaml-Glob im rules/-Wurzelverzeichnis liest (siehe
# matcher.py::_load_rules_from_dir()-Kommentar zu component_values.yaml).
_MAPPINGS_SUBPATH = Path("mappings") / "component_values.yaml"


@dataclass
class _CacheEntry:
    cfg: dict
    fs_fingerprint: tuple
    ruleset_hash: str


_cache: dict[str, _CacheEntry] = {}
_cache_lock = threading.Lock()


def _fs_fingerprint(path: Path) -> tuple:
    """Guenstiger Fingerabdruck aller Dateien, die load_rules() fuer
    diesen Pfad tatsaechlich liest -- (Name, mtime_ns, Groesse) je Datei,
    sortiert. Liest KEINE Dateiinhalte (kein YAML-Parsing), nur
    Verzeichnis-/Datei-Metadaten -- das ist der guenstige Teil, der den
    teuren Reparse-Schritt unnoetig macht, solange sich nichts geaendert
    hat.
    """
    if path.is_file():
        try:
            st = path.stat()
        except FileNotFoundError:
            return ()
        return ((str(path), st.st_mtime_ns, st.st_size),)

    entries = []
    if path.is_dir():
        for yaml_file in sorted(path.glob("*.yaml")):
            st = yaml_file.stat()
            entries.append((yaml_file.name, st.st_mtime_ns, st.st_size))

        mappings_file = path / _MAPPINGS_SUBPATH
        if mappings_file.exists():
            st = mappings_file.stat()
            entries.append((str(_MAPPINGS_SUBPATH), st.st_mtime_ns, st.st_size))

    return tuple(entries)


def get_rules(path: str) -> dict:
    """Cached Drop-in-Ersatz fuer matcher.load_rules(path).

    Erster Aufruf (oder nach einer erkannten Aenderung): parst YAML neu
    (teuer, ~310ms bei 19 Dateien laut Baseline) und aktualisiert den
    Cache. Unveraenderter Datei-Fingerabdruck: liefert die gecachte
    rules_cfg zurueck, OHNE erneut zu parsen (schneller Pfad, <1ms).
    """
    fingerprint = _fs_fingerprint(Path(path))

    with _cache_lock:
        entry = _cache.get(path)
        if entry is not None and entry.fs_fingerprint == fingerprint:
            return entry.cfg

    # Ausserhalb des Locks neu laden (load_rules() ist reines Lesen ohne
    # Seiteneffekte -- ein kurzzeitig doppelter Reload bei einer seltenen
    # Race zwischen zwei Threads ist unschaedlich, blockiert aber nicht
    # alle anderen Requests waehrend der ~310ms Parse-Zeit).
    cfg = load_rules(path)
    ruleset_hash = compute_ruleset_signature(cfg)

    with _cache_lock:
        _cache[path] = _CacheEntry(
            cfg=cfg, fs_fingerprint=fingerprint, ruleset_hash=ruleset_hash,
        )
        return _cache[path].cfg


def get_ruleset_hash(path: str) -> str:
    """Ruleset-Signatur der aktuell gecachten rules_cfg fuer `path`.

    Ruft bei Bedarf get_rules() auf (stellt sicher, dass ein Cache-Eintrag
    existiert), gibt dann den bereits bei der letzten (Neu-)Ladung
    berechneten compute_ruleset_signature()-Wert zurueck -- keine erneute
    Hash-Berechnung, keine zweite Hash-Implementierung (Auftragsvorgabe,
    Abschnitt 20)."""
    get_rules(path)
    with _cache_lock:
        return _cache[path].ruleset_hash


def invalidate(path: str | None = None) -> None:
    """Entfernt einen (oder bei path=None: alle) Cache-Eintraege.

    Fuer Tests sowie fuer einen moeglichen spaeteren expliziten
    Invalidierungs-Trigger (z.B. Admin-Endpoint) -- im Normalbetrieb
    reicht die automatische Datei-Fingerabdruck-Erkennung in get_rules(),
    dieser Aufruf ist nicht Teil des regulaeren Request-Pfads."""
    with _cache_lock:
        if path is None:
            _cache.clear()
        else:
            _cache.pop(path, None)
