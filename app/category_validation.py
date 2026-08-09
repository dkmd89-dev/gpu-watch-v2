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
"""
from __future__ import annotations

import logging

from matcher import evaluate

logger = logging.getLogger(__name__)


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


def filter_valid_entries(found: list[dict], rules_cfg: dict) -> list[dict]:
    """Wendet is_still_valid_category() auf eine ganze found.json-Liste an.

    Reine Filterfunktion ohne Seiteneffekte -- schreibt/loescht NICHTS auf
    Platte. found.json/seen.json/price_history.jsonl bleiben unangetastet;
    lediglich die fuer Dashboard/API zurueckgegebene LISTE wird reduziert.
    """
    return [e for e in found if is_still_valid_category(e, rules_cfg)]
