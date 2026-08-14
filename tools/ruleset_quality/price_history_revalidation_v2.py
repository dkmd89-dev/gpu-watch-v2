"""Auftrag Abschnitte 10-12: vertiefte Preishistorie-Simulation.

Erweitert price_history_revalidation.py (Phase 19) um:

  - explizite Schwellen <3 / <5 / <10 Samples nach simulierter
    Rekategorisierung (statt nur einer einzelnen <5-Schwelle)
  - alten/neuen Median + alte/neue Preis-Spanne pro betroffenem Modell
    (nur berechnet, wenn genug Datenpunkte vorhanden sind -- keine
    erfundenen Werte)
  - Kreuzreferenz mit dem Ground-Truth-Label-Store: welche PricePoints
    gehoeren (ueber denselben normalize_title()-Fingerprint wie
    price_history.jsonl selbst, Single Source of Truth, siehe
    app/duplicate_detection.py) zu einem als TRUE_POSITIVE/UNCLEAR
    gelabelten Listing, UND haben zugleich ein geaendertes
    price_history_model -- das ist der im Auftrag explizit als
    "besonders kritisch" markierte Fall.

Weiterhin rein lesend -- data/price_history.jsonl wird nicht veraendert.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from .common import APP_DIR, PRICE_HISTORY_JSONL, REPORTS_DIR, evaluate, load_current_rules
from .label_store import load_label_store

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from duplicate_detection import normalize_title  # noqa: E402
from price_history import read_price_points  # noqa: E402

THRESHOLDS = (3, 5, 10)


def _stats(prices: list[float]) -> dict | None:
    if not prices:
        return None
    return {
        "n": len(prices),
        "median": round(statistics.median(prices), 2),
        "min": round(min(prices), 2),
        "max": round(max(prices), 2),
    }


def simulate_v2(rules_cfg: dict | None = None) -> dict:
    if rules_cfg is None:
        rules_cfg = load_current_rules()

    points = read_price_points(PRICE_HISTORY_JSONL)
    labels = load_label_store()
    # Fingerprint -> staerkstes bekanntes Verdict (TRUE_POSITIVE hat Vorrang
    # vor UNCLEAR vor FALSE_POSITIVE fuer die "kritisch"-Markierung weiter
    # unten -- ein Fingerprint kann theoretisch mehrfach mit leicht
    # unterschiedlichem Titel vorkommen, daher Mehrfachzuordnung moeglich).
    fingerprint_to_verdicts: dict[str, set[str]] = defaultdict(set)
    for lbl in labels.values():
        if lbl.title:
            fingerprint_to_verdicts[normalize_title(lbl.title)].add(lbl.verdict)

    old_prices_by_model: dict[str, list[float]] = defaultdict(list)
    new_prices_by_model: dict[str, list[float]] = defaultdict(list)
    old_count_by_model: dict[str, int] = defaultdict(int)

    critical_tp_phm_change = []
    critical_unclear_phm_change = []

    for p in points:
        old_prices_by_model[p.model].append(p.price)
        old_count_by_model[p.model] += 1

        if not p.fingerprint:
            continue
        result = evaluate(p.fingerprint, 0.0, rules_cfg)
        if not result.matched or not result.price_history_model:
            continue
        new_prices_by_model[result.price_history_model].append(p.price)

        if result.price_history_model != p.model:
            verdicts = fingerprint_to_verdicts.get(p.fingerprint, set())
            if "TRUE_POSITIVE" in verdicts:
                critical_tp_phm_change.append({
                    "fingerprint": p.fingerprint, "price": p.price, "date": p.date,
                    "altes_model": p.model, "neues_model": result.price_history_model,
                    "alte_kategorie": p.category, "neue_kategorie": result.category,
                })
            elif "UNCLEAR" in verdicts:
                critical_unclear_phm_change.append({
                    "fingerprint": p.fingerprint, "price": p.price, "date": p.date,
                    "altes_model": p.model, "neues_model": result.price_history_model,
                    "alte_kategorie": p.category, "neue_kategorie": result.category,
                })

    all_models = sorted(set(old_prices_by_model) | set(new_prices_by_model))
    model_rows = []
    for model in all_models:
        old_prices = old_prices_by_model.get(model, [])
        new_prices = new_prices_by_model.get(model, [])
        old_n, new_n = len(old_prices), len(new_prices)

        warnings = []
        for threshold in THRESHOLDS:
            if old_n >= threshold > new_n:
                warnings.append(f"unterschreitet {threshold} Samples nach Revalidierung ({old_n} -> {new_n})")

        model_rows.append({
            "price_history_model": model,
            "altes_sample_count": old_n,
            "neues_sample_count": new_n,
            "delta": new_n - old_n,
            "alte_stats": _stats(old_prices),
            "neue_stats": _stats(new_prices),
            "schwellen_warnungen": warnings,
        })

    kleine_samples = [r for r in model_rows if r["schwellen_warnungen"]]

    report = {
        "meta": {
            "hinweis": (
                "Read-only Simulation, data/price_history.jsonl unveraendert. "
                "Fingerprint-Kreuzreferenz nutzt dieselbe normalize_title()-"
                "Funktion wie die Produktion (duplicate_detection.py) -- keine "
                "neue Normalisierungslogik."
            ),
            "anzahl_historische_punkte": len(points),
            "anzahl_modelle_gesamt": len(all_models),
            "anzahl_modelle_mit_schwellen_warnung": len(kleine_samples),
        },
        "modelle": model_rows,
        "kleine_samples_warnungen": kleine_samples,
        "kritisch_true_positive_mit_model_wechsel": critical_tp_phm_change,
        "kritisch_unclear_mit_model_wechsel": critical_unclear_phm_change,
    }
    return report


if __name__ == "__main__":
    report = simulate_v2()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "price_history_revalidation_v2.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report["meta"], indent=2, ensure_ascii=False))
    print(f"geschrieben nach {out}")
