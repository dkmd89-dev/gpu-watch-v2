# UNCLEAR Routing Assessment

Forensische Klassifikation der 35 historischen UNCLEAR-Faelle aus `docs/DASHBOARD_MATCH_FORENSICS.json` (wird nie veraendert). Betrifft AUSSCHLIESSLICH Faelle mit historischem Verdict UNCLEAR -- niemals TRUE_POSITIVE/FALSE_POSITIVE. Automatisch generiert von `tools/ruleset_quality/unclear_routing_assessment.py`.

- generated_at: 2026-08-15T22:15:11.929740+00:00
- ruleset_signature: 4f53cda18c2baa0c
- source_ground_truth: /tmp/pytest-of-robin/pytest-47/test_write_outputs_schreibt_nu1/forensics.json

## SUMMARY

- total_unclear: 1
- likely_true_positive: 0
- likely_false_positive: 0
- ground_truth_conflict: 0
- manual_review: 1

## CONFIDENCE

- high: 0
- medium: 0
- low: 1

## CATEGORIES

category           | unclear | TP    | FP    | conflict | manual_review
konsolen_bundles   | 1       | 0     | 0     | 0        | 1

## CASES

### Nintendo Switch Irgendwas mit OVP

- case_id: a
- price: 50.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) * Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: MANUAL_REVIEW (confidence=LOW)
- root_cause_pattern: unassessed
- recommended_action: manual_review
- evidence:
  - [context/weak] kein kuratiertes Assessment vorhanden: Neuer/unbekannter UNCLEAR-Fall ohne dokumentierte Bewertung -- Auftragsregel 'Bei LOW: bevorzugt MANUAL_REVIEW' greift als sicherer Default.

## CONSISTENCY

- total_cases: 1
- matched_cases: 1
- missing_cases: 0
- duplicate_cases: 0
- classification_sum: 1
- consistency_ok: False