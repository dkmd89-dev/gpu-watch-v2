"""Auftrag Abschnitt 8: Cross-Category-Routing pruefen.

Prueft NICHT nur, ob ein Listing irgendwo matcht, sondern ob es in der
"richtigen" Kategorie landet -- d.h. ob es (bei isolierter Betrachtung)
auch in einer ANDEREN Kategorie gematcht haette.

Methodik: fuer jede der 19 Kategorien wird ein auf genau diese Kategorie
gefiltertes rules_cfg gebaut (gleiche defaults/globale Excludes,
"rules": nur die Regeln dieser einen Kategorie) und `matcher.evaluate()`
UNVERAENDERT darauf angewendet -- Single Source of Truth, keine eigene
Matching-Logik, nur eine kontrollierte Teilmenge derselben Regeln.

Fuer jedes Listing wird so ermittelt, welche Kategorien (nicht nur die
tatsaechliche Gewinnerkategorie aus dem vollen First-Match-Wins-Lauf)
den Titel ebenfalls matchen wuerden. Das macht "Kategorie A ueberschattet
Kategorie B" und First-Match-Wins-Effekte sichtbar, die eine reine
Gewinner-Betrachtung uebersieht.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .common import REPORTS_DIR, evaluate, load_current_rules


def _rules_cfg_for_category(rules_cfg: dict, category: str) -> dict:
    filtered = dict(rules_cfg)
    filtered["rules"] = [r for r in rules_cfg.get("rules", []) if r.get("_category") == category]
    return filtered


def analyze(baseline_entries: list[dict], rules_cfg: dict | None = None) -> dict:
    if rules_cfg is None:
        rules_cfg = load_current_rules()

    categories = sorted({r.get("_category") for r in rules_cfg.get("rules", []) if r.get("_category")})
    per_category_cfg = {c: _rules_cfg_for_category(rules_cfg, c) for c in categories}

    multi_category_listings = []
    winner_vs_shadowed: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for e in baseline_entries:
        title = e.get("title")
        price = e.get("price", 0.0) or 0.0
        if not title:
            continue

        full_result = evaluate(title, price, rules_cfg)
        winner_category = full_result.category if full_result.matched else None

        also_matching = []
        for cat, cfg in per_category_cfg.items():
            if cat == winner_category:
                continue
            r = evaluate(title, price, cfg)
            if r.matched:
                also_matching.append({"category": cat, "rule_label": r.rule_label})

        if also_matching:
            multi_category_listings.append({
                "url": e.get("url"),
                "title": title,
                "price": price,
                "winner_category": winner_category,
                "winner_rule": full_result.rule_label if full_result.matched else None,
                "also_matching_categories": also_matching,
            })
            for m in also_matching:
                key = (winner_category or "KEIN_TREFFER", m["category"])
                winner_vs_shadowed[key] += 1
                if len(examples[key]) < 5:
                    examples[key].append({"title": title, "price": price, "shadowed_rule": m["rule_label"]})

    conflict_overview = [
        {
            "gewinner_kategorie": a, "ueberschattete_kategorie": b, "anzahl": n,
            "beispiele": examples[(a, b)],
        }
        for (a, b), n in winner_vs_shadowed.most_common()
    ]

    return {
        "meta": {
            "anzahl_untersuchter_listings": len(baseline_entries),
            "anzahl_kategorien_getestet": len(categories),
            "listings_mit_mehreren_moeglichen_kategorien": len(multi_category_listings),
        },
        "konflikt_uebersicht": conflict_overview,
        "listings_mit_mehreren_moeglichen_kategorien": multi_category_listings,
    }


if __name__ == "__main__":
    import sys
    from .common import BASELINES_DIR

    if len(sys.argv) > 1:
        baseline_path = Path(sys.argv[1])
    else:
        candidates = sorted(BASELINES_DIR.glob("baseline_2*.json"))
        baseline_path = candidates[-1]

    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)

    report = analyze(baseline["entries"])
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"cross_category_routing_{baseline_path.stem}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report["meta"], indent=2, ensure_ascii=False))
    print(f"geschrieben nach {out}")
