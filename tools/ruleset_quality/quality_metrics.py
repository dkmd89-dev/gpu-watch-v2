"""Auftrag Abschnitt 7: Qualitaetskennzahlen gesamt + pro Kategorie.

Liest die von detailed_transition.py erzeugten Transition-Listen (KEINE
neue Bewertung, nur Aggregation bereits berechneter, objektiver Fakten).

Precision-Definition (Auftrag, explizit dokumentiert statt einer
alternativen Definition):

    Precision = TRUE_POSITIVE / (TRUE_POSITIVE + FALSE_POSITIVE)
    False-Positive-Rate = FALSE_POSITIVE / (TRUE_POSITIVE + FALSE_POSITIVE)

Beide NUR ueber die "vorher"-Ground-Truth (stored_status), NICHT ueber ein
neu erratenes "nachher"-Urteil -- ein belastbares "nachher"-TP/FP/UNCLEAR
gibt es nur dort, wo after_match_state == UNVERAENDERT ist (siehe
detailed_transition.py::_derive_new_status()). "TP/FP/UNCLEAR gewonnen"
(im Sinn von: ein bisher UNLABELED/anderes Listing wird NEU als TP/FP/
UNCLEAR bestaetigt) ist grundsaetzlich NICHT aus evaluate() allein
ableitbar -- wird explizit als "nicht ermittelbar ohne neues Labeling"
ausgewiesen statt erfunden.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import REPORTS_DIR


def _empty_category_stats(cat: str) -> dict:
    return {
        "kategorie": cat,
        "untersuchte_listings": 0,
        "sichtbare_listings": "NOT_AVAILABLE",  # nur aus baseline.meta bekannt, hier pro Kategorie nicht getrennt erfasst
        "TRUE_POSITIVE_vorher": 0, "FALSE_POSITIVE_vorher": 0, "UNCLEAR_vorher": 0, "NOT_AVAILABLE_vorher": 0,
        "kategorie_aenderungen": 0, "regel_aenderungen": 0, "kein_treffer_mehr": 0,
        "price_history_model_aenderungen": 0, "price_history_model_nicht_vergleichbar": 0,
        "tp_verloren_bestaetigt": 0, "tp_potenziell_veraendert": 0,
        "fp_verloren_bestaetigt": 0, "fp_potenziell_veraendert": 0,
        "unclear_aufgeloest_kein_treffer": 0, "unclear_potenziell_veraendert": 0,
    }


def compute(transitions: list[dict]) -> dict:
    per_category: dict[str, dict] = {}

    for t in transitions:
        cat = t.get("stored_category") or "NOT_AVAILABLE"
        s = per_category.setdefault(cat, _empty_category_stats(cat))
        s["untersuchte_listings"] += 1

        status = t["stored_status"]
        s[f"{status}_vorher"] = s.get(f"{status}_vorher", 0) + 1

        after = t["after_match_state"]
        if after == "KATEGORIE_GEAENDERT":
            s["kategorie_aenderungen"] += 1
        elif after == "REGEL_GEAENDERT":
            s["regel_aenderungen"] += 1
        elif after == "KEIN_TREFFER":
            s["kein_treffer_mehr"] += 1

        old_phm = t["stored_price_history_model"]
        new_phm = t["new_price_history_model"]
        if old_phm == "NOT_AVAILABLE" or new_phm == "NOT_AVAILABLE":
            s["price_history_model_nicht_vergleichbar"] += 1
        elif old_phm != new_phm:
            s["price_history_model_aenderungen"] += 1

        if status == "TRUE_POSITIVE":
            if after == "KEIN_TREFFER":
                s["tp_verloren_bestaetigt"] += 1
            elif after in ("KATEGORIE_GEAENDERT", "REGEL_GEAENDERT"):
                s["tp_potenziell_veraendert"] += 1
        elif status == "FALSE_POSITIVE":
            if after == "KEIN_TREFFER":
                s["fp_verloren_bestaetigt"] += 1
            elif after in ("KATEGORIE_GEAENDERT", "REGEL_GEAENDERT"):
                s["fp_potenziell_veraendert"] += 1
        elif status == "UNCLEAR":
            if after == "KEIN_TREFFER":
                s["unclear_aufgeloest_kein_treffer"] += 1
            elif after in ("KATEGORIE_GEAENDERT", "REGEL_GEAENDERT"):
                s["unclear_potenziell_veraendert"] += 1

    for s in per_category.values():
        tp, fp = s["TRUE_POSITIVE_vorher"], s["FALSE_POSITIVE_vorher"]
        denom = tp + fp
        s["precision_vorher"] = round(tp / denom, 4) if denom else None
        s["false_positive_rate_vorher"] = round(fp / denom, 4) if denom else None
        s["tp_gewonnen"] = "NICHT_ERMITTELBAR_OHNE_NEUES_LABELING"
        s["fp_gewonnen"] = "NICHT_ERMITTELBAR_OHNE_NEUES_LABELING"
        s["unclear_gewonnen"] = "NICHT_ERMITTELBAR_OHNE_NEUES_LABELING"

    overall = _empty_category_stats("GESAMT")
    for s in per_category.values():
        for k in overall:
            if k in ("kategorie", "sichtbare_listings", "tp_gewonnen", "fp_gewonnen", "unclear_gewonnen"):
                continue
            if isinstance(s.get(k), (int, float)):
                overall[k] += s[k]
    tp, fp = overall["TRUE_POSITIVE_vorher"], overall["FALSE_POSITIVE_vorher"]
    denom = tp + fp
    overall["precision_vorher"] = round(tp / denom, 4) if denom else None
    overall["false_positive_rate_vorher"] = round(fp / denom, 4) if denom else None
    overall["tp_gewonnen"] = overall["fp_gewonnen"] = overall["unclear_gewonnen"] = "NICHT_ERMITTELBAR_OHNE_NEUES_LABELING"

    return {"per_category": per_category, "overall": overall}


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORTS_DIR / "detailed_transitions_historical.json"
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    result = compute(data["transitions"])
    out = REPORTS_DIR / f"quality_metrics_{path.stem}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(json.dumps(result["overall"], indent=2, ensure_ascii=False))
    print(f"geschrieben nach {out}")
