"""Phase 19.2: 2.500er-found.json-Korpus als Baseline einfrieren.

Erzeugt ein unveraenderliches Diagnoseartefakt (JSON-Datei unter
generated/baselines/) aus dem AKTUELLEN Stand von data/found.json --
OHNE found.json selbst zu veraendern (reines Lesen). Jeder Eintrag wird
ueber den echten Produktionspfad neu bewertet:

  - matcher.evaluate(title, price, rules_cfg)  -> matched_category/rule
  - category_validation.is_still_valid_category(entry, rules_cfg) -> visible

Die TP/FP/UNCLEAR-Klassifikation kommt AUSSCHLIESSLICH aus dem
Ground-Truth-Label-Store (siehe label_store.py) -- fuer URLs ohne
Ground-Truth-Label ist der Status ausdruecklich UNLABELED, keine Annahme.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from .common import (
    BASELINES_DIR,
    current_ruleset_signature,
    evaluate,
    is_still_valid_category,
    load_current_rules,
    load_found_entries,
    rule_counts_by_category,
)
from .label_store import load_label_store


def freeze_baseline(baseline_id: str | None = None) -> dict:
    rules_cfg = load_current_rules()
    signature = current_ruleset_signature(rules_cfg)
    found = load_found_entries()
    labels = load_label_store()

    now = datetime.now(timezone.utc)
    if baseline_id is None:
        baseline_id = f"baseline_{now.strftime('%Y%m%dT%H%M%SZ')}_{signature}"

    entries = []
    category_dist: dict[str, int] = {}
    rule_dist: dict[str, int] = {}
    verdict_dist = {"TRUE_POSITIVE": 0, "FALSE_POSITIVE": 0, "UNCLEAR": 0, "UNLABELED": 0}
    visible_count = 0

    for item in found:
        title = item.get("title")
        price = item.get("price", 0.0) or 0.0
        url = item.get("url")
        stored_category = item.get("category")
        stored_rule = item.get("rule")

        result = evaluate(title, price, rules_cfg) if title else None
        visible = is_still_valid_category(item, rules_cfg)
        if visible:
            visible_count += 1

        label = labels.get(url)
        verdict = label.verdict if label else "UNLABELED"
        verdict_dist[verdict] += 1

        if stored_category:
            category_dist[stored_category] = category_dist.get(stored_category, 0) + 1
        if stored_rule:
            rule_dist[stored_rule] = rule_dist.get(stored_rule, 0) + 1

        entries.append({
            "url": url,
            "title": title,
            "price": price,
            "stored_category": stored_category,
            "stored_rule_label": stored_rule,
            "matched_category": result.category if result else None,
            "matched_rule_label": result.rule_label if result else None,
            "visible": visible,
            "ground_truth_verdict": verdict,
            "ground_truth_source": label.source if label else None,
        })

    baseline = {
        "meta": {
            "baseline_id": baseline_id,
            "erzeugt_am": now.isoformat(),
            "ruleset_signature": signature,
            "rule_count": len(rules_cfg.get("rules", [])),
            "category_count": len(rule_counts_by_category(rules_cfg)),
            "anzahl_untersuchter_eintraege": len(found),
            "anzahl_sichtbarer_eintraege": visible_count,
            "ground_truth_verdict_distribution": verdict_dist,
            "ground_truth_abdeckung_pct": (
                round(100 * (len(found) - verdict_dist["UNLABELED"]) / len(found), 1)
                if found else None
            ),
            "kategorieverteilung": category_dist,
            "regelverteilung": rule_dist,
        },
        "entries": entries,
    }

    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BASELINES_DIR / f"{baseline_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    baseline["_written_to"] = str(out_path)
    return baseline


if __name__ == "__main__":
    result = freeze_baseline()
    print(json.dumps(result["meta"], indent=2, ensure_ascii=False))
    print(f"geschrieben nach {result['_written_to']}")
