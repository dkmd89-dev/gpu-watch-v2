"""Zentrale Kategorievalidierung fuer bereits gespeicherte found.json-
Eintraege (Phase 14, Schritt 2 -- PHASE14_DATA_QUALITY_REPORT.md,
Abschnitt 4, Punkte 1+3).

Hintergrund: found.json wird von app.py::run_scan() zum SCAN-Zeitpunkt
geschrieben. Wird eine Matching-Regel spaeter korrigiert (z.B. Phase 14,
Schritt 1: neue Excludes fuer handhelds/konsolen_bundles), bleiben bereits
gespeicherte Alt-Treffer unveraendert in found.json stehen -- die Datei
selbst wird bewusst NICHT angefasst (keine Loeschung/Manipulation,
Auftragsvorgabe). Damit veraltete Fehltreffer trotzdem nicht mehr im
Dashboard/API/Flip-Kandidaten/Deal-Ansicht auftauchen, wird beim LESEN
jeder Eintrag erneut gegen die AKTUELLEN Regeln geprueft (matcher.evaluate(),
dieselbe Funktion, die auch beim Scan verwendet wird) -- Single Source of
Truth, keine zweite/abweichende Matching-Logik.

Architektur (siehe Report, "Scraper -> Matcher -> Kategorievalidierung ->
Dashboard/API"): dieses Modul ist die neue, zentrale dritte Stufe. Alle
Lesepfade (api/deals.py: index()/api_found(), api/status.py: api_status())
rufen ausschliesslich filter_valid_entries() auf, statt found.json roh
durchzureichen -- dadurch koennen Dashboard, API-KPIs und (ueber denselben
found-Datensatz gespeiste) Flip-Kandidaten-/Deal-Ansicht nicht mehr
auseinanderlaufen.

Bewusst NICHT angefasst: Deal-Score, Top-Deal-Flag, Flip-/Resale-Felder,
price_history_model, max_price-Schwellen -- is_still_valid_category()
prueft AUSSCHLIESSLICH, ob der Titel bei erneuter Auswertung noch derselben
Kategorie zugeordnet wird. Alle anderen gespeicherten Felder eines
Eintrags bleiben unveraendert (kein Neuberechnen von Score/Top-Deal beim
Lesen).

Hotfix (Performance, "DRINGEND -- Phase 14 Schritt 2 blockiert Dashboard"):
filter_valid_entries() lief bisher bei JEDEM Request auf /, /api/found und
/api/status vollstaendig ungecacht -- bei mehreren tausend found.json-
Eintraegen fuehrte das zu ebenso vielen matcher.evaluate()-Aufrufen PRO
Request (je einer je Route) und blockierte /api/status
(ERR_CONNECTION_ABORTED). Layer 1 dieses Hotfixes: ein In-Memory Cache
(_validity_cache), Key = (url, title, category, ruleset_hash). Der
ruleset_hash stammt aus dem bereits bestehenden
matcher.compute_ruleset_signature() (Phase 11, Punkt B, dort fuer
seen.json/presence_tracking.py genutzt) -- keine zweite Hash-Logik. Bleibt
Titel/Kategorie/Regelwerk fuer einen Eintrag unveraendert, liefert der
Cache das zuletzt berechnete Ergebnis zurueck statt erneut evaluate()
aufzurufen; aendert sich einer der vier Werte, ist es ein Miss und es wird
regulaer neu bewertet. Der Cache ist Modul-Level und wird von allen
Aufrufern von filter_valid_entries() geteilt (api/status.py UND
api/deals.py nutzen denselben Prozess-State, keine Duplikation).
is_still_valid_category() selbst bleibt fachlich unveraendert und weiterhin
direkt (ohne Cache) aufrufbar. Bewusst OHNE Regex-Caching in
matcher._contains_term() -- das ist als moegliche Folgeoptimierung (Layer 2)
vorgemerkt, damit der Effekt dieses Cache-Layers isoliert messbar bleibt.
Bewusst OHNE TTL: Invalidierung erfolgt ausschliesslich ueber den
Cache-Key (deterministisch), eine Zeitsteuerung wuerde nur unnoetige
Cache-Misses erzeugen, ohne einen Korrektheitsvorteil zu bringen.
"""
from __future__ import annotations

import logging
import threading

from matcher import evaluate, compute_ruleset_signature

logger = logging.getLogger(__name__)

# Cache-Key: (url, title, category, ruleset_hash). url ist laut app.py
# (uid = item["url"]) der eindeutige Identifier eines found.json-Eintrags;
# title/category sind Teil des Keys, damit eine nachtraegliche Aenderung
# dieser Felder (z.B. manuelle Korrektur) automatisch einen Cache-Miss
# erzeugt. Value: das zuletzt berechnete is_still_valid_category()-Ergebnis.
# Unbounded (keine TTL/kein Max-Size) -- siehe Docstring oben.
_validity_cache: dict[tuple[str, str, object, str], bool] = {}
_cache_lock = threading.Lock()


def is_still_valid_category(entry: dict, rules_cfg: dict) -> bool:
    """Prueft, ob ein bereits gespeicherter found.json-Eintrag bei einer
    erneuten Auswertung gegen die AKTUELLEN Regeln noch derselben
    Kategorie zugeordnet wuerde.

    Fail-open bei fehlenden/unerwarteten Daten (kein Titel, keine
    gespeicherte Kategorie, Auswertungsfehler): der Eintrag wird NICHT
    ausgeblendet. Grund: diese Funktion soll ausschliesslich bekannte
    Fehltreffer (Titel matcht bei Neupruefung nicht mehr / matcht jetzt
    einer anderen Kategorie) herausfiltern -- sie darf niemals Eintraege
    verstecken, ueber die sie mangels Daten gar kein verlaessliches Urteil
    faellen kann. Das entspricht der Auftragsvorgabe "keine historische
    Datenloeschung als Workaround": im Zweifel bleibt ein Eintrag sichtbar.
    """
    title = entry.get("title")
    stored_category = entry.get("category")
    if not title or not stored_category:
        return True

    # Aeltere found.json-Eintraege koennen ohne "price"-Feld vorliegen;
    # 0.0 als neutraler Default stellt sicher, dass die Preisgrenze der
    # Regel die Kategoriezuordnung bei der Revalidierung nicht verfaelscht
    # (es geht hier ausschliesslich um die Kategorie, nicht um die exakte
    # Deal-Einstufung -- siehe Modul-Docstring).
    price = entry.get("price", 0.0) or 0.0

    try:
        result = evaluate(title, price, rules_cfg)
    except Exception:
        logger.exception(
            "Revalidierung fehlgeschlagen fuer Eintrag %r -- Eintrag bleibt "
            "sichtbar (fail-open).", title,
        )
        return True

    if not result.matched:
        return False
    return result.category == stored_category


def _cached_is_still_valid_category(
    entry: dict, rules_cfg: dict, ruleset_hash: str
) -> bool:
    """Cache-Wrapper um is_still_valid_category() (siehe Hotfix-Abschnitt
    im Modul-Docstring). Die fachliche Pruefung selbst bleibt
    ausschliesslich in is_still_valid_category() -- dieser Wrapper
    entscheidet nur, ob sie ueberhaupt erneut ausgefuehrt werden muss.

    url fehlt bei manchen Alt-Eintraegen theoretisch nicht (siehe app.py:
    uid = item["url"], wird beim Scan immer gesetzt) -- .get("", "")
    trotzdem als defensiver Fallback, damit ein fehlendes Feld hoechstens
    zu einem (harmlosen) Cache-Miss fuehrt, nie zu einem Fehler.
    """
    url = entry.get("url") or ""
    title = entry.get("title") or ""
    category = entry.get("category")
    key = (url, title, category, ruleset_hash)

    with _cache_lock:
        cached = _validity_cache.get(key)
    if cached is not None:
        return cached

    result = is_still_valid_category(entry, rules_cfg)

    with _cache_lock:
        _validity_cache[key] = result
    return result


def filter_valid_entries(found: list[dict], rules_cfg: dict) -> list[dict]:
    """Wendet is_still_valid_category() (ueber den Cache-Wrapper, siehe
    Hotfix-Abschnitt im Modul-Docstring) auf eine ganze found.json-Liste
    an.

    ruleset_hash wird EINMAL pro Aufruf berechnet (nicht pro Eintrag) --
    compute_ruleset_signature() haengt ausschliesslich vom uebergebenen
    rules_cfg ab, ist also fuer alle Eintraege dieses Aufrufs identisch.

    Reine Filterfunktion ohne Seiteneffekte -- schreibt/loescht NICHTS auf
    Platte. found.json/seen.json/price_history.jsonl bleiben unangetastet;
    lediglich die fuer Dashboard/API zurueckgegebene LISTE wird reduziert.
    """
    ruleset_hash = compute_ruleset_signature(rules_cfg)
    return [
        e for e in found
        if _cached_is_still_valid_category(e, rules_cfg, ruleset_hash)
    ]
