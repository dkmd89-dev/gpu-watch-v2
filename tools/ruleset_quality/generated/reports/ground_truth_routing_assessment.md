# Ground-Truth vs. Current-Routing-Assessment

Zweiebenen-Report: trennt historische Ground Truth (aus `docs/DASHBOARD_MATCH_FORENSICS.json`, wird nie veraendert) strikt von der aktuellen Routing-Bewertung (aus `common.evaluate()`, dem echten Produktionspfad). Automatisch generiert von `tools/ruleset_quality/ground_truth_routing_assessment.py`.

- generated_at: 2026-08-16T06:01:32.663994+00:00
- ruleset_signature: 4f53cda18c2baa0c
- source_ground_truth: /tmp/pytest-of-robin/pytest-62/test_write_outputs_schreibt_nu0/forensics.json

## SUMMARY

- historical_tp: 0
- historical_fp: 1
- historical_unclear: 0
- current_fixed_fp: 1
- current_active_fp: 0
- category_changed_fp: 0
- manual_review (FP-Ursprung, exkl. UNCLEAR): 0
- ground_truth_conflict: 0

## CATEGORIES

category             | historical_fp | fixed | still_active | category_changed  | manual_review | ground_truth_conflict
handhelds            | 1             | 1     | 0            | 0                 | 0             | 0

## CASES

### Steam Deck Huelle Schutztasche

- listing_id: a
- price: 20.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=handhelds, rule=Valve Steam Deck * Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

## QUEUE CONSISTENCY

Prueft, ob jeder Assessment-Fall genau einmal in der Fix-Queue auftaucht und dort dieselbe queue_category traegt, die assessment.status vorschreibt (`tools/ruleset_quality/generated/false_positive_fix_queue.json`).

- total_cases: 1
- matched_cases: 1
- missing_in_queue: 0
- missing_in_assessment: 0
- duplicate_case_ids: 0
- status_mismatches: 0
- consistency_ok: True

## QUEUE CATEGORY COUNTS

- ALREADY_FIXED: 1
- ACTIVE_ROUTING_FP: 0
- CATEGORY_CHANGED: 0
- GROUND_TRUTH_CONFLICT: 0
- MANUAL_REVIEW: 0