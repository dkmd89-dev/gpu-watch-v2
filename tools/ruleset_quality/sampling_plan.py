"""Konkreter Stichprobenplan fuer Punkt 4 ("frische, neu gelabelte
Stichprobe vor der eigentlichen Preishistorien-Revalidierung").

Zieht eine geschichtete Stichprobe aus dem AKTUELLEN found.json (read-only)
und exportiert ein leeres Labeling-Worksheet (CSV) -- KEINE Labels werden
hier vergeben, nur die zu bewertenden Listings ausgewaehlt. Reine
Planungs-/Vorbereitungsarbeit, kein Urteil, keine Bewertung.

Schichtung:
  - pro Kategorie eine Ziel-Stichprobengroesse (kleine Kategorien:
    vollstaendig, grosse Kategorien: gedeckelt)
  - innerhalb der Kategorie nach deal_rating (Top-Deal/Guter Preis/Okay)
    gestreut, damit alle Preisstufen abgedeckt sind (siehe Roehrenfern-
    seher-Befund: Fehlklassifikationen/Randfaelle haeufen sich an
    Preisschwellen)

Deterministisch (fester Seed) fuer Reproduzierbarkeit des Plans selbst --
die eigentliche AUSWAHL sollte aber unmittelbar vor der Labeling-Sitzung
neu gezogen werden (siehe Bericht: Korpus rotiert schnell).
"""
from __future__ import annotations

import csv
import json
import random
from collections import defaultdict

from .common import FOUND_JSON, REPORTS_DIR

TARGET_PER_CATEGORY = 15
SEED = 20260814


def stratified_sample(found: list[dict], target_per_category: int = TARGET_PER_CATEGORY, seed: int = SEED) -> list[dict]:
    by_category: dict[str, list[dict]] = defaultdict(list)
    for e in found:
        cat = e.get("category")
        if cat:
            by_category[cat].append(e)

    rng = random.Random(seed)
    sample: list[dict] = []
    for cat, entries in sorted(by_category.items()):
        by_rating: dict[str, list[dict]] = defaultdict(list)
        for e in entries:
            by_rating[e.get("deal_rating") or "unbekannt"].append(e)

        n_ratings = max(len(by_rating), 1)
        per_rating_target = max(1, target_per_category // n_ratings)

        chosen: list[dict] = []
        for rating, items in sorted(by_rating.items()):
            rng.shuffle(items)
            chosen.extend(items[:per_rating_target])

        # ggf. bis Zielgroesse auffuellen (falls eine Preisstufe duenn war)
        if len(chosen) < min(target_per_category, len(entries)):
            remaining = [e for e in entries if e not in chosen]
            rng.shuffle(remaining)
            chosen.extend(remaining[: target_per_category - len(chosen)])

        sample.extend(chosen[:target_per_category])

    return sample


def write_worksheet(sample: list[dict], path) -> None:
    fieldnames = [
        "url", "title", "price", "category", "rule", "deal_rating",
        "verdict_TP_FP_UNCLEAR", "root_cause", "reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in sample:
            writer.writerow({
                "url": e.get("url"),
                "title": e.get("title"),
                "price": e.get("price"),
                "category": e.get("category"),
                "rule": e.get("rule"),
                "deal_rating": e.get("deal_rating"),
                "verdict_TP_FP_UNCLEAR": "",
                "root_cause": "",
                "reason": "",
            })


if __name__ == "__main__":
    with FOUND_JSON.open("r", encoding="utf-8") as f:
        found = json.load(f)

    sample = stratified_sample(found)

    by_cat: dict[str, int] = defaultdict(int)
    for e in sample:
        by_cat[e["category"]] += 1

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "sampling_worksheet_template.csv"
    write_worksheet(sample, out)

    print("Stichprobengroesse gesamt:", len(sample))
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat}: {n}")
    print(f"Worksheet geschrieben nach {out} (Spalten verdict/root_cause/reason leer -- bewusst kein Urteil vorgegeben)")
