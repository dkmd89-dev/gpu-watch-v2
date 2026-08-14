"""Phase 19.5: Vorbereitung der kontrollierten Preishistorie-Revalidierung.

Read-only Simulation/Bericht -- data/price_history.jsonl wird an KEINER
Stelle beschrieben oder veraendert. Baut auf app/rule_coverage.py auf
(compute_rule_coverage()/_is_still_valid(), die bereits denselben
Mechanismus -- matcher.evaluate() gegen den gespeicherten `fingerprint`,
price=0.0 -- fuer die Aggregat-Sicht implementieren) und ergaenzt eine
PER-PUNKT-Detailsicht (alte/neue Kategorie, altes/neues price_history_model),
wie im Auftrag (Abschnitt 5) gefordert.

Bekannte, im Auftrag selbst zu beachtende Einschraenkung: PricePoint
(price_history.py) speichert KEINE Regel-/rule_label-Information, nur
`category` und `model` (= price_history_model). "alte Regel"/"neue Regel"
sind daher auf Kategorie-/Modell-Ebene nachvollziehbar, nicht auf
Einzelregel-Ebene -- das wird im Report explizit ausgewiesen, nicht
stillschweigend verschwiegen.

Nur ca. 90% der price_history.jsonl-Zeilen haben ueberhaupt einen
`fingerprint` (aeltere Zeilen vor dessen Einfuehrung nicht) -- nur diese
sind rekonstruierbar/simulierbar; der Rest zaehlt separat als
"nicht rekonstruierbar", nicht als "unveraendert" (das waere eine
unbelegte Annahme).
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass

from .common import PRICE_HISTORY_JSONL, REPORTS_DIR, evaluate, load_current_rules

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent.parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from price_history import PricePoint, read_price_points  # noqa: E402
from rule_coverage import compute_rule_coverage  # noqa: E402


@dataclass
class PointRevalidation:
    fingerprint: str | None
    date: str
    price: float
    alte_kategorie: str | None
    neue_kategorie: str | None
    altes_model: str
    neues_model: str | None
    status: str  # UNVERAENDERT | KATEGORIEWECHSEL | MODELLWECHSEL | NICHT_MEHR_GUELTIG | NICHT_REKONSTRUIERBAR


def _classify_point(point: PricePoint, rules_cfg: dict) -> PointRevalidation:
    if not point.fingerprint:
        return PointRevalidation(
            fingerprint=None, date=point.date, price=point.price,
            alte_kategorie=point.category, neue_kategorie=None,
            altes_model=point.model, neues_model=None,
            status="NICHT_REKONSTRUIERBAR",
        )

    result = evaluate(point.fingerprint, 0.0, rules_cfg)
    if not result.matched:
        return PointRevalidation(
            fingerprint=point.fingerprint, date=point.date, price=point.price,
            alte_kategorie=point.category, neue_kategorie=None,
            altes_model=point.model, neues_model=None,
            status="NICHT_MEHR_GUELTIG",
        )

    if result.category != point.category:
        status = "KATEGORIEWECHSEL"
    elif result.price_history_model != point.model:
        status = "MODELLWECHSEL"
    else:
        status = "UNVERAENDERT"

    return PointRevalidation(
        fingerprint=point.fingerprint, date=point.date, price=point.price,
        alte_kategorie=point.category, neue_kategorie=result.category,
        altes_model=point.model, neues_model=result.price_history_model,
        status=status,
    )


def simulate(rules_cfg: dict | None = None) -> dict:
    if rules_cfg is None:
        rules_cfg = load_current_rules()

    points = read_price_points(PRICE_HISTORY_JSONL)
    revalidations = [_classify_point(p, rules_cfg) for p in points]

    status_counts = Counter(r.status for r in revalidations)

    # Risiko 1: Kategoriewechsel -- historische Punkte werden jetzt einer
    # ANDEREN Kategorie zugeordnet als beim Sammeln.
    kategoriewechsel = [r for r in revalidations if r.status == "KATEGORIEWECHSEL"]
    kategoriewechsel_paare = Counter(
        (r.alte_kategorie, r.neue_kategorie) for r in kategoriewechsel
    )

    # Risiko 2: Modellwechsel innerhalb derselben Kategorie -- Gefahr, dass
    # zwei vorher getrennte Modelle zusammengefuehrt werden ODER ein Modell
    # sich in mehrere aufspaltet (Sample-Groessen aendern sich).
    modellwechsel = [r for r in revalidations if r.status == "MODELLWECHSEL"]
    modellwechsel_paare = Counter(
        (r.altes_model, r.neues_model) for r in modellwechsel
    )

    # Risiko 3: Modelle mit kleinen Samples, die durch einen Wechsel
    # unbrauchbar wuerden (Schwelle 5, siehe CLAUDE.md "duenne Resale-Daten").
    altes_model_samples = Counter(r.altes_model for r in revalidations if r.fingerprint)
    betroffene_kleine_samples = sorted({
        r.altes_model for r in (kategoriewechsel + modellwechsel)
        if altes_model_samples.get(r.altes_model, 0) < 5
    })

    # Risiko 4: alte False Positives, die weiterhin in die Marktpreis-
    # Statistik einfliessen (ueber compute_rule_coverage()'s vorhandene
    # false_positive_indicators-Aggregation, Single Source of Truth,
    # keine zweite Implementierung).
    coverage = compute_rule_coverage(points, rules_cfg)
    fp_modelle = [
        {
            "category": c.category, "price_history_model": c.price_history_model,
            "sample_count": c.sample_count, "false_positive_indicators": c.false_positive_indicators,
            "false_positive_rate": c.false_positive_rate,
        }
        for c in coverage if c.false_positive_indicators
    ]

    orphan_modelle = [
        {"category": c.category, "price_history_model": c.price_history_model, "matches": c.matches}
        for c in coverage if not c.in_current_ruleset
    ]

    report = {
        "meta": {
            "hinweis": (
                "Read-only Simulation. data/price_history.jsonl wurde NICHT "
                "veraendert. 'alte Regel'/'neue Regel' sind nicht "
                "rekonstruierbar (PricePoint speichert nur category+model, "
                "kein rule_label) -- Vergleich erfolgt auf Kategorie-/"
                "Modell-Ebene."
            ),
            "anzahl_historische_eintraege": len(points),
            "davon_rekonstruierbar_mit_fingerprint": sum(1 for p in points if p.fingerprint),
            "status_counts": dict(status_counts),
        },
        "risiken": {
            "kategoriewechsel_paare": [
                {"alte_kategorie": a, "neue_kategorie": b, "anzahl": n}
                for (a, b), n in kategoriewechsel_paare.most_common()
            ],
            "modellwechsel_paare": [
                {"altes_model": a, "neues_model": b, "anzahl": n}
                for (a, b), n in modellwechsel_paare.most_common()
            ],
            "kleine_samples_betroffen_von_wechsel": betroffene_kleine_samples,
            "modelle_mit_bekannten_false_positive_indikatoren": fp_modelle,
            "orphan_modelle_ohne_aktuelle_regel": orphan_modelle,
        },
    }
    return report


if __name__ == "__main__":
    report = simulate()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "price_history_revalidation_simulation.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report["meta"], indent=2, ensure_ascii=False))
    print(f"geschrieben nach {out}")
