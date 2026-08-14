"""Phase 19.4: Qualitaetsmetriken pro Kategorie + Gesamtbericht.

Kombiniert zwei Datenquellen:

1. "Aktueller Korpus" (baseline.py, heutiges found.json): TP/FP/UNCLEAR nur
   fuer den Teil, der ueber den Ground-Truth-Label-Store abgedeckt ist
   (aktuell ca. 19% Abdeckung, siehe label_store.py-Docstring) -- der Rest
   ist ausdruecklich UNLABELED, fliesst NICHT in Precision/FP-Rate ein.

2. "Historischer Regressionsvergleich" (historical_baseline.py +
   benchmark.py): alle 2306 Eintraege aus dem VOR-Audit-Snapshot, erneut
   gegen das AKTUELLE Ruleset ausgewertet -- zeigt, wie sich die
   TP/FP/UNCLEAR-Population durch den 19-Kategorien-Audit (PR #11-#28)
   tatsaechlich veraendert hat.

Formeln (siehe Auftrag Abschnitt 4):

    Precision = TRUE_POSITIVE / (TRUE_POSITIVE + FALSE_POSITIVE)
    False-Positive-Rate = FALSE_POSITIVE / (TRUE_POSITIVE + FALSE_POSITIVE)

Beide Kennzahlen werden NUR ueber die gelabelten Teilmenge berechnet
(UNCLEAR/UNLABELED fliessen nicht in den Nenner ein) -- das wird im Output
explizit mit "labeled_n" ausgewiesen, um keine falsche Praezision
vorzutaeuschen.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import REPORTS_DIR


def _labeled_precision(tp: int, fp: int) -> float | None:
    denom = tp + fp
    if denom == 0:
        return None
    return round(tp / denom, 4)


def _fp_rate(tp: int, fp: int) -> float | None:
    denom = tp + fp
    if denom == 0:
        return None
    return round(fp / denom, 4)


def current_corpus_category_stats(baseline: dict) -> dict:
    stats: dict[str, dict] = {}
    for e in baseline["entries"]:
        cat = e.get("stored_category") or "_unbekannt"
        s = stats.setdefault(cat, {
            "kategorie": cat, "getestete_eintraege": 0, "sichtbar": 0,
            "TRUE_POSITIVE": 0, "FALSE_POSITIVE": 0, "UNCLEAR": 0, "UNLABELED": 0,
        })
        s["getestete_eintraege"] += 1
        if e.get("visible"):
            s["sichtbar"] += 1
        s[e.get("ground_truth_verdict", "UNLABELED")] += 1

    for s in stats.values():
        tp, fp = s["TRUE_POSITIVE"], s["FALSE_POSITIVE"]
        s["labeled_n"] = tp + fp + s["UNCLEAR"]
        s["precision"] = _labeled_precision(tp, fp)
        s["false_positive_rate"] = _fp_rate(tp, fp)
        s["abdeckung_pct"] = round(100 * s["labeled_n"] / s["getestete_eintraege"], 1) if s["getestete_eintraege"] else None

    return stats


def historical_regression_category_stats(benchmark_report: dict) -> dict:
    stats: dict[str, dict] = {}
    for t in benchmark_report["transitions"]:
        cat = t.get("category") or "_unbekannt"
        s = stats.setdefault(cat, {
            "kategorie": cat, "getestete_eintraege": 0,
            "tp_stabil": 0, "tp_kritisch_kein_treffer": 0, "tp_anderer_matchpfad": 0,
            "fp_gefixt": 0, "fp_weiterhin_aktiv": 0,
            "unclear_kein_treffer": 0, "unclear_weiterhin": 0,
            "kategoriewechsel": 0,
        })
        s["getestete_eintraege"] += 1
        gate = t["gate_label"]
        if gate == "TRUE_POSITIVE -> TRUE_POSITIVE (stabil)":
            s["tp_stabil"] += 1
        elif gate == "TRUE_POSITIVE -> kein Treffer":
            s["tp_kritisch_kein_treffer"] += 1
        elif gate == "TRUE_POSITIVE, aber anderer Matchpfad":
            s["tp_anderer_matchpfad"] += 1
        elif gate == "FALSE_POSITIVE -> kein Treffer":
            s["fp_gefixt"] += 1
        elif gate == "FALSE_POSITIVE weiterhin aktiv":
            s["fp_weiterhin_aktiv"] += 1
        elif gate == "UNCLEAR -> kein Treffer":
            s["unclear_kein_treffer"] += 1
        elif gate == "UNCLEAR weiterhin unklar":
            s["unclear_weiterhin"] += 1
        if t["severity"] == "WARNING":
            s["kategoriewechsel"] += 1

    for s in stats.values():
        s["gewonnene_true_positive"] = s["fp_gefixt"]  # FP, das korrekt verschwunden ist
        s["verlorene_true_positive"] = s["tp_kritisch_kein_treffer"]  # zuvor TP, jetzt weg
        s["regressionen_gesamt"] = s["tp_kritisch_kein_treffer"] + s["kategoriewechsel"]

    return stats


def build_overall(stats: dict) -> dict:
    overall = {
        "kategorie": "GESAMT", "getestete_eintraege": 0, "sichtbar": 0,
        "TRUE_POSITIVE": 0, "FALSE_POSITIVE": 0, "UNCLEAR": 0, "UNLABELED": 0,
    }
    for s in stats.values():
        for k in ("getestete_eintraege", "sichtbar", "TRUE_POSITIVE", "FALSE_POSITIVE", "UNCLEAR", "UNLABELED"):
            overall[k] += s.get(k, 0)
    tp, fp = overall["TRUE_POSITIVE"], overall["FALSE_POSITIVE"]
    overall["labeled_n"] = tp + fp + overall["UNCLEAR"]
    overall["precision"] = _labeled_precision(tp, fp)
    overall["false_positive_rate"] = _fp_rate(tp, fp)
    overall["abdeckung_pct"] = round(100 * overall["labeled_n"] / overall["getestete_eintraege"], 1) if overall["getestete_eintraege"] else None
    return overall


def write_markdown_table(stats: dict, overall: dict, path: Path, columns: list[tuple[str, str]]) -> None:
    lines = ["| " + " | ".join(h for _, h in columns) + " |",
             "|" + "|".join(["---"] * len(columns)) + "|"]
    for cat in sorted(stats):
        row = stats[cat]
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    lines.append("| " + " | ".join(str(overall.get(key, "")) for key, _ in columns) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    with (REPORTS_DIR / "benchmark_historical_forensics_baseline.json").open("r", encoding="utf-8") as f:
        hist_report = json.load(f)

    current_baselines = sorted((REPORTS_DIR.parent / "baselines").glob("baseline_2*.json"))
    with current_baselines[-1].open("r", encoding="utf-8") as f:
        current_baseline = json.load(f)

    current_stats = current_corpus_category_stats(current_baseline)
    current_overall = build_overall(current_stats)
    hist_stats = historical_regression_category_stats(hist_report)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with (REPORTS_DIR / "category_quality_current.json").open("w", encoding="utf-8") as f:
        json.dump({"per_category": current_stats, "overall": current_overall}, f, indent=2, ensure_ascii=False)
    with (REPORTS_DIR / "category_quality_historical_regression.json").open("w", encoding="utf-8") as f:
        json.dump({"per_category": hist_stats}, f, indent=2, ensure_ascii=False)

    write_markdown_table(
        current_stats, current_overall,
        REPORTS_DIR / "category_quality_current.md",
        [("kategorie", "Kategorie"), ("getestete_eintraege", "Getestet"), ("sichtbar", "Sichtbar"),
         ("TRUE_POSITIVE", "TP"), ("FALSE_POSITIVE", "FP"), ("UNCLEAR", "UNCLEAR"),
         ("labeled_n", "Gelabelt (n)"), ("abdeckung_pct", "Abdeckung %"),
         ("precision", "Precision"), ("false_positive_rate", "FP-Rate")],
    )
    print("geschrieben:", REPORTS_DIR / "category_quality_current.json")
    print("geschrieben:", REPORTS_DIR / "category_quality_historical_regression.json")
    print("geschrieben:", REPORTS_DIR / "category_quality_current.md")
