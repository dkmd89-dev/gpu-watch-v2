"""Phase 19.3: Automatischer Regression-Benchmark.

Nimmt eine zuvor eingefrorene Baseline (baseline.py oder
historical_baseline.py) und wertet JEDEN Eintrag erneut ueber den echten
Produktionspfad aus (matcher.evaluate() + category_validation.
is_still_valid_category()) -- gegen das AKTUELL geladene Ruleset. Schreibt
NICHTS in Produktionsdateien.

Wichtige methodische Einschraenkung (bewusst so belassen, keine
Ueberinterpretation):

Die Baseline traegt pro Eintrag ein "vorher"-Ground-Truth-Verdict
(TRUE_POSITIVE/FALSE_POSITIVE/UNCLEAR/UNLABELED), das aus einer FRUEHEREN
menschlichen/strukturierten Bewertung stammt (siehe label_store.py). Der
Benchmark selbst kann KEIN neues TRUE_POSITIVE/FALSE_POSITIVE-Urteil
"nachher" faellen -- das waere identisch mit einer zweiten,
selbstgebauten Bewertungslogik. Was er stattdessen objektiv aus
evaluate()/is_still_valid_category() ableiten kann, ist der reine
MATCH-ZUSTAND "nachher":

    KEIN_TREFFER        -- evaluate() liefert matched=False
    GLEICHE_KATEGORIE    -- matched=True, category == stored_category
    ANDERE_KATEGORIE     -- matched=True, category != stored_category
    ANDERE_REGEL          -- matched=True, gleiche Kategorie, aber
                            rule_label != stored_rule_label

Das Gate (siehe classify_gate()) kombiniert "vorher"-Verdict mit diesem
objektiven "nachher"-Match-Zustand und bildet damit so viel von der im
Auftrag beschriebenen Transition-Matrix ab, wie ohne eine zweite
Bewertungslogik moeglich ist. Faelle, die eine ECHTE neue TP/FP/UNCLEAR-
Neubewertung erfordern wuerden (z.B. "TRUE_POSITIVE -> FALSE_POSITIVE"
im engeren Sinn), werden als HIGH_CANDIDATE markiert und explizit als
"erfordert menschliche Nachpruefung" gekennzeichnet, nicht automatisch
entschieden.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .common import REPORTS_DIR, evaluate, is_still_valid_category, load_current_rules, current_ruleset_signature


@dataclass
class Transition:
    url: str
    title: str
    category: str | None
    before_verdict: str  # TRUE_POSITIVE | FALSE_POSITIVE | UNCLEAR | UNLABELED
    before_rule: str | None
    after_match_state: str  # KEIN_TREFFER | GLEICHE_KATEGORIE | ANDERE_KATEGORIE | ANDERE_REGEL
    after_category: str | None
    after_rule: str | None
    severity: str  # CRITICAL | HIGH_CANDIDATE | WARNING | INFO | NEUTRAL
    gate_label: str
    explanation: str


def _after_match_state(result, stored_category: str | None, stored_rule: str | None) -> str:
    if not result or not result.matched:
        return "KEIN_TREFFER"
    if result.category != stored_category:
        return "ANDERE_KATEGORIE"
    if stored_rule is not None and result.rule_label != stored_rule:
        return "ANDERE_REGEL"
    return "GLEICHE_KATEGORIE"


def classify_gate(before_verdict: str, after_state: str) -> tuple[str, str, str]:
    """Gibt (severity, gate_label, explanation) zurueck.

    Deckt die im Auftrag (Abschnitt 4.1) genannten Faelle ab, soweit
    objektiv aus dem Match-Zustand ableitbar:

        CRITICAL: TRUE_POSITIVE -> kein Treffer
        HIGH_CANDIDATE: TRUE_POSITIVE -> ANDERE_REGEL (gleiche Kategorie,
            aber anderer Matchpfad) ODER FALSE_POSITIVE -> GLEICHE_KATEGORIE
            (Fehltreffer weiterhin unveraendert aktiv) -- beides erfordert
            menschliche Nachpruefung, um sicher als "TP -> FP" bzw.
            "FP weiterhin FP" zu gelten.
        WARNING: Kategoriewechsel (A -> B) unabhaengig vom vorherigen Verdict
        INFO: FALSE_POSITIVE -> kein Treffer (Fix wirkt wie erwartet) sowie
            UNCLEAR -> irgendein neuer Zustand (weiterhin nicht automatisch
            aufloesbar)
        NEUTRAL: TRUE_POSITIVE -> GLEICHE_KATEGORIE (unveraendert stabil),
            UNLABELED (keine Vorher-Aussage moeglich)
    """
    if before_verdict == "TRUE_POSITIVE":
        if after_state == "KEIN_TREFFER":
            return ("CRITICAL", "TRUE_POSITIVE -> kein Treffer",
                    "Ein zuvor menschlich bestaetigter echter Treffer matcht jetzt gar nicht mehr.")
        if after_state == "ANDERE_KATEGORIE":
            return ("WARNING", "Kategoriewechsel (vorher TRUE_POSITIVE)",
                    "Ein zuvor bestaetigter Treffer landet jetzt in einer anderen Kategorie.")
        if after_state == "ANDERE_REGEL":
            return ("HIGH_CANDIDATE", "TRUE_POSITIVE, aber anderer Matchpfad",
                    "Gleiche Kategorie, aber andere Regel/anderer Preisschwellen-Bucket -- "
                    "manuell pruefen, ob weiterhin korrekt.")
        return ("NEUTRAL", "TRUE_POSITIVE -> TRUE_POSITIVE (stabil)", "Unveraendert.")

    if before_verdict == "FALSE_POSITIVE":
        if after_state == "KEIN_TREFFER":
            return ("INFO", "FALSE_POSITIVE -> kein Treffer",
                    "Bekannter Fehltreffer matcht jetzt nicht mehr (Fix wirkt wie erwartet).")
        if after_state == "ANDERE_KATEGORIE":
            return ("WARNING", "Kategoriewechsel (vorher FALSE_POSITIVE)",
                    "Bekannter Fehltreffer landet jetzt in einer anderen Kategorie statt zu verschwinden.")
        return ("HIGH_CANDIDATE", "FALSE_POSITIVE weiterhin aktiv",
                "Bekannter Fehltreffer matcht weiterhin unveraendert dieselbe Kategorie/Regel -- nicht gefixt.")

    if before_verdict == "UNCLEAR":
        if after_state == "KEIN_TREFFER":
            return ("INFO", "UNCLEAR -> kein Treffer", "Ehemals unklarer Fall matcht jetzt nicht mehr.")
        if after_state == "ANDERE_KATEGORIE":
            return ("WARNING", "Kategoriewechsel (vorher UNCLEAR)", "Ehemals unklarer Fall wechselt die Kategorie.")
        return ("INFO", "UNCLEAR weiterhin unklar",
                "Weiterhin kein automatisches Urteil moeglich -- menschliche Bewertung noetig.")

    # UNLABELED
    if after_state == "ANDERE_KATEGORIE":
        return ("WARNING", "Kategoriewechsel (kein Vorher-Label)",
                "Kein Ground-Truth-Verdict vorhanden, aber Kategorie hat sich seit Fund geaendert.")
    return ("NEUTRAL", "UNLABELED", "Kein Ground-Truth-Verdict vorhanden -- keine Regressionsaussage moeglich.")


def run_benchmark(baseline: dict, rules_cfg: dict | None = None) -> dict:
    if rules_cfg is None:
        rules_cfg = load_current_rules()
    current_signature = current_ruleset_signature(rules_cfg)
    baseline_signature = baseline["meta"].get("ruleset_signature")

    transitions: list[Transition] = []
    for e in baseline["entries"]:
        title = e.get("title")
        price = e.get("price", 0.0) or 0.0
        stored_category = e.get("stored_category")
        stored_rule = e.get("stored_rule_label")
        before_verdict = e.get("ground_truth_verdict", "UNLABELED")

        result = evaluate(title, price, rules_cfg) if title else None
        after_state = _after_match_state(result, stored_category, stored_rule)
        severity, gate_label, explanation = classify_gate(before_verdict, after_state)

        transitions.append(Transition(
            url=e.get("url"),
            title=title,
            category=stored_category,
            before_verdict=before_verdict,
            before_rule=stored_rule,
            after_match_state=after_state,
            after_category=result.category if result else None,
            after_rule=result.rule_label if result else None,
            severity=severity,
            gate_label=gate_label,
            explanation=explanation,
        ))

    severity_counts: dict[str, int] = {}
    gate_counts: dict[str, int] = {}
    for t in transitions:
        severity_counts[t.severity] = severity_counts.get(t.severity, 0) + 1
        gate_counts[t.gate_label] = gate_counts.get(t.gate_label, 0) + 1

    report = {
        "meta": {
            "baseline_id": baseline["meta"].get("baseline_id"),
            "baseline_ruleset_signature": baseline_signature,
            "current_ruleset_signature": current_signature,
            "ruleset_unveraendert": baseline_signature == current_signature,
            "anzahl_eintraege": len(transitions),
            "severity_counts": severity_counts,
            "gate_label_counts": gate_counts,
        },
        "transitions": [asdict(t) for t in transitions],
    }
    return report


def notable_findings(report: dict, severities: tuple[str, ...] = ("CRITICAL", "HIGH_CANDIDATE", "WARNING")) -> list[dict]:
    return [t for t in report["transitions"] if t["severity"] in severities]


def write_report(report: dict, name: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / name
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return out_path


if __name__ == "__main__":
    import sys
    from .baseline import BASELINES_DIR

    if len(sys.argv) > 1:
        baseline_path = Path(sys.argv[1])
    else:
        candidates = sorted(BASELINES_DIR.glob("baseline_*.json"))
        if not candidates:
            raise SystemExit("Keine Baseline gefunden -- zuerst baseline.py ausfuehren.")
        baseline_path = candidates[-1]

    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)

    report = run_benchmark(baseline)
    print(json.dumps(report["meta"], indent=2, ensure_ascii=False))
    out = write_report(report, f"benchmark_{baseline['meta']['baseline_id']}.json")
    print(f"geschrieben nach {out}")
