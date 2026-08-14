"""Baut pro Zeile des 251-Listing-Worksheets eine Match-Diagnose (welche
require_all_of-Gruppe wodurch erfuellt wurde, welche Excludes greifen
wuerden) als Lesehilfe fuer die anschliessende Bewertung (TP/FP/UNCLEAR).

Vollstaendig read-only: nutzt evaluate() + die geladenen Regel-Dicts nur
lesend, aendert nichts. Kein Ersatz fuer evaluate() -- reine Erklaerungs-
schicht obendrauf, analog zu den bereits in DASHBOARD_MATCH_FORENSICS.json
vorhandenen Feldern (match_terms_hit / global_excludes_checked), die im
Repo sonst nirgends als wiederverwendbares Skript vorliegen.
"""
from __future__ import annotations

import csv
import json

from .common import REPORTS_DIR, evaluate, load_current_rules

WORKSHEET = REPORTS_DIR / "sampling_worksheet_template.csv"
OUT = REPORTS_DIR / "worksheet_diagnostics.json"


def _find_rule(rules_cfg, category, label):
    for r in rules_cfg["rules"]:
        if r.get("_category") == category and r.get("label") == label:
            return r
    return None


def _group_hits(title_lower: str, group: list[str]) -> list[str]:
    return [t for t in group if t.lower() in title_lower]


def build() -> list[dict]:
    rules_cfg = load_current_rules()
    out = []
    with WORKSHEET.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            title = row["title"]
            price = float(row["price"]) if row["price"] else 0.0
            category = row["category"]
            rule_label = row["rule"]
            title_lower = title.lower()

            r = evaluate(title, price, rules_cfg)
            rule_def = _find_rule(rules_cfg, category, rule_label)

            group_diag = []
            if rule_def:
                for group in rule_def.get("require_all_of", []):
                    hits = _group_hits(title_lower, group)
                    group_diag.append({
                        "group": group,
                        "hits": hits,
                        "nur_generischstes_signal": len(hits) == 1 and hits[0] == group[-1] and len(group) > 1,
                    })

            excl = rule_def.get("exclude", []) if rule_def else []
            cat_excl = rule_def.get("_category_exclude_terms", []) if rule_def else []
            excl_present = [e for e in excl if e.lower() in title_lower]
            cat_excl_present = [e for e in cat_excl if e.lower() in title_lower]

            out.append({
                "url": row["url"],
                "title": title,
                "price": price,
                "category": category,
                "rule": rule_label,
                "deal_rating": row["deal_rating"],
                "reevaluiert_matched": r.matched,
                "reevaluiert_category": r.category,
                "reevaluiert_rule_label": r.rule_label,
                "reevaluiert_stimmt_mit_worksheet_ueberein": (
                    r.matched and r.category == category and r.rule_label == rule_label
                ),
                "require_all_of_diagnose": group_diag,
                "rule_excludes_im_titel": excl_present,
                "category_excludes_im_titel": cat_excl_present,
            })
    return out


if __name__ == "__main__":
    data = build()
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    n_mismatch = sum(1 for d in data if not d["reevaluiert_stimmt_mit_worksheet_ueberein"])
    print(f"geschrieben nach {OUT}, {len(data)} Zeilen, {n_mismatch} Abweichungen ggue. Worksheet-Snapshot")
