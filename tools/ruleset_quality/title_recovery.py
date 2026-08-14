"""Hilfsfunktion: echte Titel zu einem price_history.jsonl-Fingerprint
zurueckgewinnen, wo moeglich.

KRITISCHER BEFUND (siehe generated/reports/PUNKTE_1_BIS_3_ABSCHLUSSBERICHT.md,
Abschnitt "Methodik-Korrektur"): `duplicate_detection.normalize_title()`
ersetzt Umlaute (ä/ö/ü/ß) durch `_NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]+")`
mit einem LEERZEICHEN, nicht durch die transliterierte Form. Aus
"Röhrenfernseher" wird so "r hrenfernseher" -- ein reiner Fingerprint-
basierter `evaluate()`-Aufruf (wie in app/rule_coverage.py::_is_still_valid()
und den fruehren Versionen von price_history_revalidation(_v2).py in dieser
Session) matcht dadurch NIE gegen Umlaut-haltige match/require_all_of-Begriffe
(z.B. "röhrenfernseher", "verstärker") -- unabhaengig davon, ob der echte
Titel inhaltlich passen wuerde. Betroffen: 19 von 355 Regeln in 4 Kategorien
(handhelds, konsolen_bundles, retro_konsolen, vintage_elektronik).

Dieses Modul rekonstruiert daher, wo moeglich, den ECHTEN Titel (statt des
Fingerprints) durch Rueckwaerts-Suche in den beiden einzigen im Repo
vorhandenen Quellen mit Klartext-Titeln:

  - data/found.json (aktueller Live-Korpus, read-only gelesen)
  - docs/DASHBOARD_MATCH_FORENSICS.json (historischer Snapshot, read-only)

Fingerprints, die in KEINER der beiden Quellen vorkommen, bleiben ehrlich
"nicht rekonstruierbar" -- es wird kein Titel erfunden.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .common import APP_DIR, DOCS_DIR, FOUND_JSON

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from duplicate_detection import normalize_title  # noqa: E402

FORENSICS_PATH = DOCS_DIR / "DASHBOARD_MATCH_FORENSICS.json"


def build_fingerprint_title_map() -> dict[str, str]:
    """fingerprint -> echter Titel, aus found.json (Prioritaet) + forensics.json."""
    fp_map: dict[str, str] = {}

    if FOUND_JSON.exists():
        with FOUND_JSON.open("r", encoding="utf-8") as f:
            found = json.load(f)
        for e in found:
            t = e.get("title")
            if t:
                fp_map[normalize_title(t)] = t

    if FORENSICS_PATH.exists():
        with FORENSICS_PATH.open("r", encoding="utf-8") as f:
            forensics = json.load(f)
        for e in forensics.get("entries", []):
            t = e.get("title")
            if t:
                fp_map.setdefault(normalize_title(t), t)

    return fp_map
