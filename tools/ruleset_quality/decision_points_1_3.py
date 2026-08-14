"""Auftrag "Offene Entscheidungen 1-3 klaeren": read-only Tiefenanalyse fuer

  1. price_history_model "roehrenfernseher"
  2. die 3 Orphan-Modelle aus der entfernten Kategorie spielzeug_bundles
  3. alle UNCLEAR-gelabelten Faelle mit Kategorie-/Modelldrift

WICHTIGE METHODEN-KORREKTUR ggue. der vorherigen Session: die bisherigen
price_history_revalidation(_v2).py-Module werteten `PricePoint.fingerprint`
(erzeugt von `duplicate_detection.normalize_title()`) erneut per
`matcher.evaluate()` aus. `normalize_title()` ersetzt Umlaute (ä/ö/ü/ß)
durch ein LEERZEICHEN (`_NON_ALNUM_RE`), z.B. "Röhrenfernseher" ->
"r hrenfernseher". Das bricht jeden Abgleich gegen Umlaut-haltige
match/require_all_of-Begriffe systematisch (19 von 355 Regeln in 4
Kategorien betroffen: handhelds, konsolen_bundles, retro_konsolen,
vintage_elektronik) UND gegen preisschwellenabhaengige Regeln, wenn
zusaetzlich price=0.0 statt des echten Preises verwendet wird (siehe
switch_pro_controller-Faelle unten).

Dieses Modul nutzt daher, wo immer moeglich, ECHTE Titel (aus dem
Ground-Truth-Label-Store, der bereits Klartext-Titel speichert -- keine
Fingerprint-Rekonstruktion noetig) statt Fingerprints.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from .common import APP_DIR, DATA_DIR, REPORTS_DIR, evaluate, load_current_rules
from .label_store import load_label_store
from .title_recovery import build_fingerprint_title_map

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from price_history import read_price_points  # noqa: E402

PRICE_HISTORY_JSONL = DATA_DIR / "price_history.jsonl"


def _price_stats(prices: list[float]) -> dict:
    if not prices:
        return {}
    d = {"n": len(prices), "median": round(statistics.median(prices), 2),
         "min": round(min(prices), 2), "max": round(max(prices), 2)}
    if len(prices) >= 4:
        q = statistics.quantiles(prices, n=4)
        d["q25"], d["q75"] = round(q[0], 2), round(q[2], 2)
    return d


def analyze_model(model: str, points, rules_cfg, fp_map) -> dict:
    pts = [p for p in points if p.model == model]
    dates = sorted(p.date for p in pts)
    prices = [p.price for p in pts]

    recoverable = [(p, fp_map.get(p.fingerprint)) for p in pts]
    n_recoverable = sum(1 for _, t in recoverable if t)
    valid, invalid = 0, 0
    invalid_examples, valid_examples = [], []
    for p, title in recoverable:
        if not title:
            continue
        r = evaluate(title, p.price, rules_cfg)
        ok = r.matched and r.price_history_model == model
        if ok:
            valid += 1
            valid_examples.append({"title": title, "price": p.price})
        else:
            invalid += 1
            invalid_examples.append({
                "title": title, "price": p.price, "matched": r.matched,
                "new_category": r.category, "new_price_history_model": r.price_history_model,
            })

    return {
        "model": model,
        "anzahl_punkte": len(pts),
        "zeitraum": [dates[0][:10], dates[-1][:10]] if dates else None,
        "preisverteilung": _price_stats(prices),
        "distinkte_fingerprints": len(set(p.fingerprint for p in pts)),
        "gespeicherte_kategorien": sorted({p.category for p in pts if p.category}),
        "titel_rekonstruierbar": n_recoverable,
        "titel_rekonstruierbar_pct": round(100 * n_recoverable / len(pts), 1) if pts else None,
        "davon_valide_bei_neubewertung": valid,
        "davon_invalide_bei_neubewertung": invalid,
        "valide_beispiele": valid_examples[:10],
        "invalide_beispiele": invalid_examples,
    }


def analyze_unclear_drift(rules_cfg) -> dict:
    labels = load_label_store()
    stable, changed = [], []
    for lbl in labels.values():
        if lbl.verdict != "UNCLEAR" or not lbl.title:
            continue
        r = evaluate(lbl.title, 0.0, rules_cfg)
        if r.matched and r.price_history_model == lbl.price_history_model:
            stable.append({"title": lbl.title, "price_history_model": lbl.price_history_model})
        else:
            changed.append({
                "title": lbl.title,
                "alte_kategorie": lbl.category, "alte_regel": lbl.rule_label,
                "altes_price_history_model": lbl.price_history_model,
                "neue_kategorie": r.category if r.matched else None,
                "neues_price_history_model": r.price_history_model if r.matched else None,
                "matched": r.matched,
            })
    return {"anzahl_gesamt": len(stable) + len(changed), "stabil": stable, "veraendert": changed}


def run() -> dict:
    rules_cfg = load_current_rules()
    points = read_price_points(PRICE_HISTORY_JSONL)
    fp_map = build_fingerprint_title_map()

    report = {
        "roehrenfernseher": analyze_model("roehrenfernseher", points, rules_cfg, fp_map),
        "crt_profi_monitor_vergleich": analyze_model("crt_profi_monitor", points, rules_cfg, fp_map),
        "orphan_lego_bundle": analyze_model("lego_bundle", points, rules_cfg, fp_map),
        "orphan_playmobil_bundle": analyze_model("playmobil_bundle", points, rules_cfg, fp_map),
        "orphan_spielzeug_bundle_sonstige": analyze_model("spielzeug_bundle_sonstige", points, rules_cfg, fp_map),
        "unclear_drift": analyze_unclear_drift(rules_cfg),
    }
    return report


if __name__ == "__main__":
    report = run()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "decision_points_1_3.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"geschrieben nach {out}")
    print("roehrenfernseher:", report["roehrenfernseher"]["anzahl_punkte"], "Punkte,",
          report["roehrenfernseher"]["davon_valide_bei_neubewertung"], "valide (von",
          report["roehrenfernseher"]["titel_rekonstruierbar"], "rekonstruierbaren Titeln)")
    print("UNCLEAR gesamt:", report["unclear_drift"]["anzahl_gesamt"],
          "davon veraendert:", len(report["unclear_drift"]["veraendert"]))
