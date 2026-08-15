"""Saubere Zweiebenen-Trennung: historical_ground_truth vs. current_routing_assessment.

Reine Report-/Praesentationsschicht ueber `forensics_false_positives.py` --
enthaelt selbst KEINE eigene Matching-/Klassifikationslogik. Jeder Fall
(bestaetigter FALSE_POSITIVE oder UNCLEAR-Kandidat) wird aus
`forensics_false_positives.extract_cases()` uebernommen (das bereits die
Zwei-Ebenen-Assessment-Felder assessment_status/assessment_confidence/
assessment_evidence berechnet, siehe dortiger Moduldocstring) und in das im
Auftrag geforderte, explizit verschachtelte Schema uebersetzt:

    historical_ground_truth        -- kommt AUSSCHLIESSLICH aus dem
                                       Forensik-Snapshot, wird NIE veraendert
    current_routing_assessment     -- kommt AUSSCHLIESSLICH aus dem echten
                                       Produktionspfad (common.evaluate())
    assessment                     -- status/confidence/evidence, automatisch
                                       abgeleitet ODER (dokumentiert, siehe
                                       forensics_false_positives.
                                       _MANUAL_ASSESSMENT_OVERRIDES) manuell
                                       uebersteuert -- NIE eine erfundene
                                       Heuristik

Ein historisches FALSE_POSITIVE-Label bedeutet NICHT automatisch "aktuell
noch ein Fehltreffer" (siehe GROUND_TRUTH_CONFLICT-Faelle: Switch/Xbox-
Bundles, bei denen die aktuelle Evidenz dem historischen Label
widerspricht). Ein aktueller GLEICHE_KATEGORIE-Treffer bedeutet NICHT
automatisch "historisches Label war falsch" (Default bleibt STILL_ACTIVE,
nur ein dokumentierter manueller Override darf GROUND_TRUTH_CONFLICT
vergeben).

Schreibt/aendert NIEMALS app/rules/*.yaml, docs/DASHBOARD_MATCH_FORENSICS.json
oder sonstige Produktionsdateien. Baut KEINE zweite Matching-Engine.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from . import forensics_false_positives as ffp
from .common import REPORTS_DIR, current_ruleset_signature, load_current_rules
from .label_store import FORENSICS_SOURCE

REPORT_JSON = REPORTS_DIR / "ground_truth_routing_assessment.json"
REPORT_MD = REPORTS_DIR / "ground_truth_routing_assessment.md"

# "manual_review" in summary/categories zaehlt bewusst NUR FALSE_POSITIVE-
# Ursprungsfaelle mit assessment_status=MANUAL_REVIEW (z.B. der DS-Lite-
# Fall). Die 35 UNCLEAR-Kandidaten haben IMMER assessment_status=
# MANUAL_REVIEW (siehe forensics_false_positives.py), werden aber unter
# ihrer eigenen Kennzahl "historical_unclear" gefuehrt statt in
# "manual_review" mitgezaehlt -- sonst waere nicht mehr unterscheidbar, ob
# ein manual_review-Fall aus einem bestaetigten FP oder einem blossen
# UNCLEAR-Kandidaten stammt. Jeder einzelne UNCLEAR-Fall ist trotzdem
# vollstaendig in "cases" enthalten (case_type=unclear_candidate).


def _fp_case_to_dict(c: "ffp.FalsePositiveCase") -> dict:
    return {
        "case_type": "confirmed_false_positive",
        "listing_id": c.listing_id,
        "title": c.title,
        "price": c.price,
        "historical_ground_truth": {
            "verdict": c.ground_truth_verdict,
            "category": c.stored_category,
            "rule": c.stored_rule,
        },
        "current_routing_assessment": {
            "category": c.current_category,
            "rule": c.current_rule,
            "match_state": c.match_state,
            "routing_status": c.routing_status,
        },
        "assessment": {
            "status": c.assessment_status,
            "confidence": c.assessment_confidence,
            "evidence": c.assessment_evidence,
        },
        "root_cause": c.root_cause,
        "root_cause_confidence": c.root_cause_confidence,
        "root_cause_evidence": c.root_cause_evidence,
        "recommended_fix_type": c.recommended_fix_type,
        "regression_risk": c.regression_risk,
    }


def _candidate_to_dict(c: "ffp.FpCandidateCase") -> dict:
    return {
        "case_type": "unclear_candidate",
        "listing_id": c.listing_id,
        "title": c.title,
        "price": c.price,
        "historical_ground_truth": {
            "verdict": c.ground_truth_verdict,
            "category": c.stored_category,
            "rule": c.stored_rule,
        },
        "current_routing_assessment": {
            "category": c.current_category,
            "rule": c.current_rule,
            "match_state": c.match_state,
            "routing_status": c.routing_status,
        },
        "assessment": {
            "status": c.assessment_status,
            "confidence": c.assessment_confidence,
            "evidence": c.assessment_evidence,
        },
        "note": c.note,
    }


def _empty_category_counts() -> dict:
    return {
        "historical_fp": 0,
        "fixed": 0,
        "still_active": 0,
        "category_changed": 0,
        "manual_review": 0,
        "ground_truth_conflict": 0,
    }


_STATUS_TO_CATEGORY_FIELD = {
    ffp.ASSESSMENT_FIXED: "fixed",
    ffp.ASSESSMENT_STILL_ACTIVE: "still_active",
    ffp.ASSESSMENT_CATEGORY_CHANGED: "category_changed",
    ffp.ASSESSMENT_MANUAL_REVIEW: "manual_review",
    ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT: "ground_truth_conflict",
}


def build_report(
    input_path: Path = FORENSICS_SOURCE, rules_cfg: dict | None = None
) -> dict:
    """Baut den vollstaendigen, ungefilterten Assessment-Report (metadata/
    summary/categories/cases). Wiederverwendet ausschliesslich
    forensics_false_positives.extract_cases() -- keine eigene evaluate()-
    oder Klassifikationslogik."""
    if rules_cfg is None:
        rules_cfg = load_current_rules()

    entries = ffp.load_forensics_entries(input_path)

    verdict_counts = {"TRUE_POSITIVE": 0, "FALSE_POSITIVE": 0, "UNCLEAR": 0}
    for e in entries:
        v = e.get("verdict")
        if v in verdict_counts:
            verdict_counts[v] += 1

    confirmed, candidates = ffp.extract_cases(entries, rules_cfg, category=None)

    categories: dict[str, dict] = defaultdict(_empty_category_counts)
    for c in confirmed:
        cat_counts = categories[c.stored_category]
        cat_counts["historical_fp"] += 1
        field_name = _STATUS_TO_CATEGORY_FIELD[c.assessment_status]
        cat_counts[field_name] += 1
    categories = dict(sorted(categories.items()))

    summary = {
        "historical_tp": verdict_counts["TRUE_POSITIVE"],
        "historical_fp": verdict_counts["FALSE_POSITIVE"],
        "historical_unclear": verdict_counts["UNCLEAR"],
        "current_fixed_fp": sum(cc["fixed"] for cc in categories.values()),
        "current_active_fp": sum(cc["still_active"] for cc in categories.values()),
        "category_changed_fp": sum(
            cc["category_changed"] for cc in categories.values()
        ),
        "manual_review": sum(cc["manual_review"] for cc in categories.values()),
        "ground_truth_conflict": sum(
            cc["ground_truth_conflict"] for cc in categories.values()
        ),
    }

    cases = [_fp_case_to_dict(c) for c in confirmed] + [
        _candidate_to_dict(c) for c in candidates
    ]
    # deterministische, reproduzierbare Ausgabe (Auftrag "PERFORMANCE"):
    # nach Kategorie, dann Titel sortieren, statt Dict-Iterationsreihenfolge
    # zu verlassen.
    cases.sort(
        key=lambda d: (
            d["historical_ground_truth"]["category"] or "",
            d["title"] or "",
        )
    )

    # Auftrag "false_positive_fix_queue.json an Ground-Truth-Routing-
    # Assessment koppeln": die Fix-Queue wird HIER aus genau denselben
    # `confirmed`-Cases abgeleitet (ffp.build_fix_queue()), die auch die
    # obige assessment-Ebene liefern -- keine zweite, abweichende
    # Ableitung. Die Konsistenzpruefung stellt sicher, dass queue_category
    # ausschliesslich aus assessment.status folgt.
    fix_queue = ffp.build_fix_queue(confirmed)
    queue_consistency = ffp.validate_queue_consistency(confirmed, fix_queue)

    queue_category_counts = {
        ffp.QUEUE_CATEGORY_ALREADY_FIXED: 0,
        ffp.QUEUE_CATEGORY_ACTIVE_ROUTING_FP: 0,
        ffp.QUEUE_CATEGORY_CATEGORY_CHANGED: 0,
        ffp.QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT: 0,
        ffp.QUEUE_CATEGORY_MANUAL_REVIEW: 0,
    }
    for entry in fix_queue:
        queue_category_counts[entry.queue_category] = (
            queue_category_counts.get(entry.queue_category, 0) + entry.affected_count
        )

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ruleset_signature": current_ruleset_signature(rules_cfg),
            "source_ground_truth": str(input_path),
            "ground_truth_counts": verdict_counts,
        },
        "summary": summary,
        "categories": categories,
        "cases": cases,
        "fix_queue": [asdict(e) for e in fix_queue],
        "queue_category_counts": queue_category_counts,
        "queue_consistency": queue_consistency,
    }


def render_markdown(report: dict) -> str:
    meta = report["metadata"]
    summary = report["summary"]
    categories = report["categories"]
    cases = report["cases"]

    lines: list[str] = [
        "# Ground-Truth vs. Current-Routing-Assessment",
        "",
        "Zweiebenen-Report: trennt historische Ground Truth (aus "
        "`docs/DASHBOARD_MATCH_FORENSICS.json`, wird nie veraendert) strikt "
        "von der aktuellen Routing-Bewertung (aus `common.evaluate()`, dem "
        "echten Produktionspfad). Automatisch generiert von "
        "`tools/ruleset_quality/ground_truth_routing_assessment.py`.",
        "",
        f"- generated_at: {meta['generated_at']}",
        f"- ruleset_signature: {meta['ruleset_signature']}",
        f"- source_ground_truth: {meta['source_ground_truth']}",
        "",
        "## SUMMARY",
        "",
        f"- historical_tp: {summary['historical_tp']}",
        f"- historical_fp: {summary['historical_fp']}",
        f"- historical_unclear: {summary['historical_unclear']}",
        f"- current_fixed_fp: {summary['current_fixed_fp']}",
        f"- current_active_fp: {summary['current_active_fp']}",
        f"- category_changed_fp: {summary['category_changed_fp']}",
        f"- manual_review (FP-Ursprung, exkl. UNCLEAR): {summary['manual_review']}",
        f"- ground_truth_conflict: {summary['ground_truth_conflict']}",
        "",
        "## CATEGORIES",
        "",
        f"{'category':<20} | {'historical_fp':<13} | {'fixed':<5} | {'still_active':<12} "
        f"| {'category_changed':<17} | {'manual_review':<13} | ground_truth_conflict",
    ]
    for cat, cc in categories.items():
        lines.append(
            f"{cat:<20} | {cc['historical_fp']:<13} | {cc['fixed']:<5} | "
            f"{cc['still_active']:<12} | {cc['category_changed']:<17} | "
            f"{cc['manual_review']:<13} | {cc['ground_truth_conflict']}"
        )
    lines.append("")

    lines.append("## CASES")
    lines.append("")
    for case in cases:
        hgt = case["historical_ground_truth"]
        cra = case["current_routing_assessment"]
        a = case["assessment"]
        lines.append(f"### {case['title']}")
        lines.append("")
        lines.append(f"- listing_id: {case['listing_id']}")
        lines.append(f"- price: {case['price']}")
        lines.append(
            f"- historical_ground_truth: verdict={hgt['verdict']}, "
            f"category={hgt['category']}, rule={hgt['rule']}"
        )
        lines.append(
            f"- current_routing_assessment: category={cra['category']}, "
            f"rule={cra['rule']}, match_state={cra['match_state']}, "
            f"routing_status={cra['routing_status']}"
        )
        lines.append(f"- assessment: status={a['status']}, confidence={a['confidence']}")
        for ev in a["evidence"]:
            lines.append(f"  - {ev}")
        lines.append("")

    qc = report["queue_consistency"]
    qcc = report["queue_category_counts"]
    lines.append("## QUEUE CONSISTENCY")
    lines.append("")
    lines.append(
        "Prueft, ob jeder Assessment-Fall genau einmal in der Fix-Queue auftaucht und "
        "dort dieselbe queue_category traegt, die assessment.status vorschreibt "
        "(`tools/ruleset_quality/generated/false_positive_fix_queue.json`)."
    )
    lines.append("")
    lines.append(f"- total_cases: {qc['total_cases']}")
    lines.append(f"- matched_cases: {qc['matched_cases']}")
    lines.append(f"- missing_in_queue: {len(qc['missing_in_queue'])}")
    lines.append(f"- missing_in_assessment: {len(qc['missing_in_assessment'])}")
    lines.append(f"- duplicate_case_ids: {len(qc['duplicate_case_ids'])}")
    lines.append(f"- status_mismatches: {len(qc['status_mismatches'])}")
    lines.append(f"- consistency_ok: {qc['consistency_ok']}")
    lines.append("")
    lines.append("## QUEUE CATEGORY COUNTS")
    lines.append("")
    for qcat, n in qcc.items():
        lines.append(f"- {qcat}: {n}")

    return "\n".join(lines)


def write_outputs(report: dict) -> dict[str, Path]:
    import json

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")

    return {"json_report": REPORT_JSON, "md_report": REPORT_MD}


# Auftrag "VALIDIERUNG": die 4 explizit zu pruefenden Referenzfaelle, ueber
# ihre stabile listing_id identifiziert (nicht ueber Titel-String-Matching).
_VALIDATION_CASES = {
    "PS5-HDMI": "https://www.kleinanzeigen.de/s-anzeige/playstation-5-ps4-ps5-slim-hdmi-port-nintendo-reparatur-usb-pro/3431533294-226-3438",
    "Nintendo Switch": "https://www.ebay.de/itm/137602406753",
    "Xbox": "https://www.kleinanzeigen.de/s-anzeige/xbox-one-s-1tb-mit-spiele/3479889108-279-4400",
    "Nintendo DS Lite": "https://www.ebay.de/itm/398266334210",
}


def _print_queue_consistency_summary(report: dict) -> None:
    qc = report["queue_consistency"]
    qcc = report["queue_category_counts"]

    print("Assessment / Queue Consistency")
    print("=" * 31)
    print("Total cases:", qc["total_cases"])
    print("Matched:", qc["matched_cases"])
    print("Missing:", len(qc["missing_in_queue"]) + len(qc["missing_in_assessment"]))
    print("Duplicates:", len(qc["duplicate_case_ids"]))
    print("Status mismatches:", len(qc["status_mismatches"]))
    print("Consistency:", qc["consistency_ok"])
    print()

    print("FIXED:", qcc[ffp.QUEUE_CATEGORY_ALREADY_FIXED])
    print("ACTIVE_ROUTING_FP:", qcc[ffp.QUEUE_CATEGORY_ACTIVE_ROUTING_FP])
    print("CATEGORY_CHANGED:", qcc[ffp.QUEUE_CATEGORY_CATEGORY_CHANGED])
    print("GROUND_TRUTH_CONFLICT:", qcc[ffp.QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT])
    print("MANUAL_REVIEW:", qcc[ffp.QUEUE_CATEGORY_MANUAL_REVIEW])
    print()

    case_by_id = {c["listing_id"]: c for c in report["cases"]}
    queue_category_by_id: dict[str, str] = {}
    for entry in report["fix_queue"]:
        for listing_id in entry["case_listing_ids"]:
            queue_category_by_id[listing_id] = entry["queue_category"]

    for label, listing_id in _VALIDATION_CASES.items():
        case = case_by_id.get(listing_id)
        if case is None:
            print(f"{label}: NICHT GEFUNDEN (listing_id={listing_id})")
            continue
        assessment_status = case["assessment"]["status"]
        queue_category = queue_category_by_id.get(listing_id, "FEHLT_IN_QUEUE")
        expected = ffp._ASSESSMENT_TO_QUEUE_CATEGORY.get(assessment_status)
        consistent = queue_category == expected
        print(
            f"{label}: assessment.status={assessment_status}, "
            f"queue_category={queue_category}, consistent={consistent}"
        )
    print()


def _print_final_summary(report: dict) -> None:
    """Auftrag-ABSCHLUSS-Format: Kennzahlen + Details je nicht geloestem
    FALSE_POSITIVE-Ursprungsfall. Die 35 UNCLEAR-Kandidaten werden bewusst
    NICHT einzeln in dieser Terminal-Zusammenfassung aufgelistet (nur ihre
    Gesamtzahl via historical_unclear) -- vollstaendig einsehbar in
    ground_truth_routing_assessment.{json,md}."""
    _print_queue_consistency_summary(report)

    summary = report["summary"]
    print("Historical FP:", summary["historical_fp"])
    print("Currently active routing FP:", summary["current_active_fp"])
    print("Fixed:", summary["current_fixed_fp"])
    print("Category changed:", summary["category_changed_fp"])
    print("Ground-truth conflicts:", summary["ground_truth_conflict"])
    print(
        "Manual review:",
        summary["manual_review"],
        f"(FP-Ursprung) + {report['metadata']['ground_truth_counts']['UNCLEAR']} "
        "UNCLEAR-Kandidaten (siehe vollstaendigen Report)",
    )
    print()

    unresolved = [
        c
        for c in report["cases"]
        if c["case_type"] == "confirmed_false_positive"
        and c["assessment"]["status"] != ffp.ASSESSMENT_FIXED
    ]
    if not unresolved:
        print("Keine nicht geloesten bestaetigten FALSE_POSITIVE-Faelle.")
        return

    print(f"Nicht geloeste Faelle ({len(unresolved)}):")
    print()
    for c in unresolved:
        hgt = c["historical_ground_truth"]
        cra = c["current_routing_assessment"]
        a = c["assessment"]
        print(f"category: {hgt['category']}")
        print(f"title: {c['title']}")
        print(f"historical verdict: {hgt['verdict']}")
        print(
            f"current routing: category={cra['category']}, rule={cra['rule']}, "
            f"match_state={cra['match_state']}"
        )
        print(f"assessment: {a['status']} (confidence={a['confidence']})")
        print("evidence:")
        for ev in a["evidence"]:
            print(f"  - {ev}")
        print()


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.ruleset_quality.ground_truth_routing_assessment",
        description=(
            "Zweiebenen-Trennung historical_ground_truth vs. "
            "current_routing_assessment. Read-only -- aendert keine YAML-Regeln "
            "und niemals docs/DASHBOARD_MATCH_FORENSICS.json."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=FORENSICS_SOURCE,
        help="Pfad zum Forensik-Ground-Truth-Artefakt",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    rules_cfg = load_current_rules()
    report = build_report(input_path=args.input, rules_cfg=rules_cfg)
    written = write_outputs(report)
    for label, path in written.items():
        print(f"geschrieben ({label}): {path}")
    print()
    _print_final_summary(report)

    if not report["queue_consistency"]["consistency_ok"]:
        print("ERROR: Assessment<->Fix-Queue-Konsistenz verletzt (siehe oben).")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
