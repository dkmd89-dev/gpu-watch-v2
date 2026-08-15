"""Category-False-Positive-Forensics + priorisierte Fix-Queue.

Extrahiert bestaetigte FALSE_POSITIVE-Faelle aus dem Ground-Truth-Forensik-
Snapshot (docs/DASHBOARD_MATCH_FORENSICS.json), gruppiert sie nach der
gespeicherten Kategorie, ermittelt den AKTUELLEN Match-Zustand ueber den
echten Produktionspfad und leitet daraus eine priorisierte, aber NICHT
automatisch angewendete Fix-Queue ab.

Wiederverwendet ausschliesslich vorhandene Bausteine -- baut KEINE zweite
Matching-/Bewertungslogik:

  - label_store.FORENSICS_SOURCE       Pfad zum Forensik-Rohartefakt
  - common.evaluate()/load_current_rules()   echter Produktions-Matchpfad
  - benchmark._after_match_state()      objektiver Match-Zustand "nachher"
    (KEIN_TREFFER/GLEICHE_KATEGORIE/ANDERE_KATEGORIE/ANDERE_REGEL)

Epistemische Grundregel (siehe Auftrag "KRITISCHE METHODISCHE REGEL"):
die TRUE_POSITIVE/FALSE_POSITIVE/UNCLEAR-Klassifikation kommt AUSSCHLIESSLICH
aus dem Forensik-Snapshot (menschlich/strukturiert erzeugt). Dieses Modul
erfindet niemals ein neues TP/FP-Urteil und promoviert UNCLEAR-Faelle nie
automatisch zu FALSE_POSITIVE -- sie werden getrennt als "FP-Kandidaten"
gefuehrt, nie in den confirmed-FP-Zahlen mitgezaehlt.

Root-Cause-Klassifikation: docs/DASHBOARD_MATCH_FORENSICS.json traegt pro
FALSE_POSITIVE bereits ein aus der echten Match-Instrumentierung
(require_all_of_detail, *_excludes_checked) abgeleitetes root_cause/reason-
Feld. Dieses Modul UEBERSETZT diese bereits belegte Klassifikation in die im
Auftrag geforderte Taxonomie (siehe _FORENSICS_ROOT_CAUSE_TRANSLATION) --
es bewertet nichts neu. Werte ohne Uebersetzungseintrag (z.B. "sonstiges",
wie bei allen 35 UNCLEAR-Faellen) werden bewusst NICHT geraten, sondern als
"ambiguous"/"manual_review" ausgewiesen.

Cross-Category-Routing (Auftrag Funktion 5): "FALSE_POSITIVE -> kein
Treffer" gilt als guter Fix (routing_status C). "FALSE_POSITIVE -> andere
Kategorie" gilt NICHT automatisch als Fix (routing_status B) -- das wird
in already_resolved explizit abgebildet und fliesst so in die Fix-Queue-
Priorisierung ein.

Zwei-Ebenen-Assessment (Auftrag "Saubere Trennung historical ground truth /
current routing assessment"): jeder Fall traegt SEPARAT (1) den historischen
Ground-Truth-Verdict + gespeicherte Kategorie/Regel (kommt ausschliesslich
aus dem Forensik-Snapshot, wird NIEMALS veraendert), (2) den aktuellen
Match-Zustand ueber evaluate() (kommt ausschliesslich aus dem echten
Produktionspfad) und (3) ein daraus abgeleitetes assessment.status/
confidence/evidence. Ein historisches FALSE_POSITIVE-Label bedeutet NICHT
automatisch "aktuell noch ein Fehltreffer" -- und ein aktueller
GLEICHE_KATEGORIE-Treffer bedeutet NICHT automatisch "historisches Label
war falsch". Die einzige Ausnahme von der rein automatischen Ableitung ist
_MANUAL_ASSESSMENT_OVERRIDES: ein kleines, im Code dokumentiertes,
NIEMALS heuristisch erzeugtes Lookup fuer die wenigen Faelle, in denen ein
Mensch (siehe active_fp_fix_progress.md) nach Pruefung zusaetzlicher Evidenz
explizit GROUND_TRUTH_CONFLICT oder MANUAL_REVIEW festgestellt hat --
"Keine automatische Entscheidung erfinden" gilt uneingeschraenkt.

Schreibt/aendert NIEMALS app/rules/*.yaml, docs/DASHBOARD_MATCH_FORENSICS.json
oder sonstige Produktionsdateien. Alle Ausgaben landen unter
tools/ruleset_quality/generated/.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .benchmark import _after_match_state
from .common import GENERATED_DIR, REPORTS_DIR, evaluate, load_current_rules
from .label_store import FORENSICS_SOURCE

NOT_AVAILABLE = "NOT_AVAILABLE"

FIX_QUEUE_JSON = GENERATED_DIR / "false_positive_fix_queue.json"
FIX_QUEUE_MD = GENERATED_DIR / "false_positive_fix_queue.md"

# Bekannter Referenzstand (siehe label_store.py-Docstring): 2306 Eintraege,
# TP 2252 / FP 19 / UNCLEAR 35. Wird bei jedem Lauf gegengeprueft (Auftrag
# Abschluss Punkt 7/8) -- Abweichungen werden dokumentiert, nicht verschwiegen.
KNOWN_REFERENCE_COUNTS = {"TRUE_POSITIVE": 2252, "FALSE_POSITIVE": 19, "UNCLEAR": 35}

# --- Cross-Category-Routing-Status (Auftrag Funktion 5) --------------------

ROUTING_STATUS_SAME_CATEGORY = "A_SAME_WRONG_CATEGORY"
ROUTING_STATUS_CATEGORY_CHANGED = "B_CATEGORY_CHANGED"
ROUTING_STATUS_NO_MATCH = "C_NO_LONGER_MATCHES"
ROUTING_STATUS_RULE_CHANGED = "D_RULE_CHANGED_SAME_CATEGORY"

_AFTER_STATE_TO_ROUTING_STATUS = {
    "GLEICHE_KATEGORIE": ROUTING_STATUS_SAME_CATEGORY,
    "ANDERE_KATEGORIE": ROUTING_STATUS_CATEGORY_CHANGED,
    "KEIN_TREFFER": ROUTING_STATUS_NO_MATCH,
    "ANDERE_REGEL": ROUTING_STATUS_RULE_CHANGED,
}

# Nur C zaehlt als tatsaechlich geloest -- B ist ausdruecklich KEIN
# automatischer Fix (siehe Auftrag "WICHTIGE REGRESSION-GATES").
RESOLVED_ROUTING_STATUSES = {ROUTING_STATUS_NO_MATCH}

# --- Root-Cause-Taxonomie (Auftrag Funktion 4) ------------------------------

ROOT_CAUSE_WRONG_CATEGORY = "wrong_category"
ROOT_CAUSE_ACCESSORY = "accessory_false_positive"
ROOT_CAUSE_REPLACEMENT_PART = "replacement_part_false_positive"
ROOT_CAUSE_WEAK_SIGNAL = "weak_signal"
ROOT_CAUSE_MISSING_EXCLUDE = "missing_exclude"
ROOT_CAUSE_MISSING_CONTEXT = "missing_context"
ROOT_CAUSE_RULE_COLLISION = "rule_collision"
ROOT_CAUSE_CROSS_CATEGORY_COLLISION = "cross_category_collision"
ROOT_CAUSE_AMBIGUOUS = "ambiguous"
ROOT_CAUSE_UNKNOWN = "unknown"

CONFIDENCE_CONFIRMED = "confirmed"
CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"
CONFIDENCE_MANUAL_REVIEW = "manual_review"

# Uebersetzt die im Forensik-Snapshot BEREITS vergebenen (deutschen) root_cause-
# Werte 1:1 in die Auftrags-Taxonomie. Kein Eintrag hier => keine Vermutung,
# siehe _translate_root_cause().
_FORENSICS_ROOT_CAUSE_TRANSLATION: dict[str, tuple[str, str]] = {
    "Ersatzteil statt Hauptprodukt": (
        ROOT_CAUSE_REPLACEMENT_PART,
        CONFIDENCE_CONFIRMED,
    ),
    "fehlendes Exclude": (ROOT_CAUSE_MISSING_EXCLUDE, CONFIDENCE_CONFIRMED),
    "falsches Positivsignal": (ROOT_CAUSE_WEAK_SIGNAL, CONFIDENCE_CONFIRMED),
}

_FIX_TYPE_BY_ROOT_CAUSE = {
    ROOT_CAUSE_WRONG_CATEGORY: "cross_category_precedence",
    ROOT_CAUSE_ACCESSORY: "add_accessory_guard",
    ROOT_CAUSE_REPLACEMENT_PART: "add_replacement_part_guard",
    ROOT_CAUSE_WEAK_SIGNAL: "strengthen_positive_signal",
    ROOT_CAUSE_MISSING_EXCLUDE: "add_exclude",
    ROOT_CAUSE_MISSING_CONTEXT: "add_context_requirement",
    ROOT_CAUSE_RULE_COLLISION: "add_category_conflict_rule",
    ROOT_CAUSE_CROSS_CATEGORY_COLLISION: "add_category_conflict_rule",
    ROOT_CAUSE_AMBIGUOUS: "manual_review",
    ROOT_CAUSE_UNKNOWN: "manual_review",
}

# Heuristische Default-Einschaetzung zur PRIORISIERUNG, NICHT gemessen (keine
# Datenbasis fuer eine echte Risikoquantifizierung vorhanden -- CLAUDE.md
# Regel 4 gilt sinngemaess auch hier). Ersetzt keine menschliche
# Risikoeinschaetzung vor der eigentlichen YAML-Aenderung.
_REGRESSION_RISK_BY_FIX_TYPE = {
    "add_exclude": "LOW",
    "add_replacement_part_guard": "LOW",
    "add_accessory_guard": "MEDIUM",
    "add_context_requirement": "MEDIUM",
    "strengthen_positive_signal": "HIGH",
    "weaken_keyword": "HIGH",
    "cross_category_precedence": "HIGH",
    "add_category_conflict_rule": "HIGH",
    "manual_review": "MEDIUM",
    "unknown": "MEDIUM",
}

_CONFIDENCE_WEIGHT = {
    CONFIDENCE_CONFIRMED: 2,
    CONFIDENCE_HIGH: 2,
    CONFIDENCE_MEDIUM: 1,
    CONFIDENCE_LOW: 0,
    CONFIDENCE_MANUAL_REVIEW: 0,
}

# --- Zwei-Ebenen-Assessment (Auftrag "Saubere Trennung historical ground
# truth / current routing assessment") --------------------------------------

ASSESSMENT_FIXED = "FIXED"
ASSESSMENT_STILL_ACTIVE = "STILL_ACTIVE"
ASSESSMENT_CATEGORY_CHANGED = "CATEGORY_CHANGED"
ASSESSMENT_MANUAL_REVIEW = "MANUAL_REVIEW"
ASSESSMENT_GROUND_TRUTH_CONFLICT = "GROUND_TRUTH_CONFLICT"

QUEUE_CATEGORY_ACTIVE_ROUTING_FP = "ACTIVE_ROUTING_FP"
QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT = "GROUND_TRUTH_CONFLICT"
QUEUE_CATEGORY_MANUAL_REVIEW = "MANUAL_REVIEW"
QUEUE_CATEGORY_ALREADY_FIXED = "ALREADY_FIXED"

# Manuelle, kuratierte Uebersteuerungen der automatischen Assessment-
# Ableitung -- NIEMALS heuristisch/automatisch erzeugt (Auftrag "Keine
# automatische Entscheidung erfinden"). Jeder Eintrag entspricht einer
# tatsaechlich im Chat getroffenen, dokumentierten Entscheidung (siehe
# tools/ruleset_quality/generated/reports/active_fp_fix_progress.md).
# Key = listing_id (URL). Uebersteuert NUR assessment.status/confidence/
# evidence -- historical_ground_truth und current_routing_assessment
# bleiben IMMER die tatsaechlich beobachteten Werte (Forensik-Snapshot
# bzw. evaluate()) und werden hier nie veraendert.
_MANUAL_ASSESSMENT_OVERRIDES: dict[str, tuple[str, str, list[str]]] = {
    # Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle Neon Blau/Rot mit Dock
    "https://www.ebay.de/itm/137602406753": (
        ASSESSMENT_GROUND_TRUTH_CONFLICT,
        CONFIDENCE_HIGH,
        [
            "Titel enthaelt echten Speichergroessen-Marker '32GB' (Basis-Switch-Modell) "
            "sowie ein Spiel (Mario Kart 8 Deluxe) und Zubehoer (Dock) -- liest sich als "
            "vollstaendiger Konsolenverkauf, nicht als Zubehoer-/Spiele-Angebot.",
            "Vom Nutzer am 2026-08-15 nach Vorlage der Matchpfad-Analyse explizit als "
            "korrekt gematchter TRUE_POSITIVE bestaetigt (siehe active_fp_fix_progress.md).",
            "Keine YAML-Aenderung vorgenommen -- das FALSE_POSITIVE-Label im historischen "
            "Forensik-Snapshot (Commit 01afd5b, 2026-08-10) ist vermutlich selbst fehlerhaft.",
        ],
    ),
    # Xbox One S 1TB mit Spiele
    "https://www.kleinanzeigen.de/s-anzeige/xbox-one-s-1tb-mit-spiele/3479889108-279-4400": (
        ASSESSMENT_GROUND_TRUTH_CONFLICT,
        CONFIDENCE_HIGH,
        [
            "Titel enthaelt echten Speichergroessen-Marker '1TB' (Xbox One S 1TB-Variante), "
            "keine Zubehoer-/Ersatzteil-Indikatoren.",
            "Vom Nutzer am 2026-08-15 nach Vorlage der Matchpfad-Analyse explizit als "
            "korrekt gematchter TRUE_POSITIVE bestaetigt (siehe active_fp_fix_progress.md).",
            "Keine YAML-Aenderung vorgenommen -- das FALSE_POSITIVE-Label im historischen "
            "Forensik-Snapshot ist vermutlich selbst fehlerhaft.",
        ],
    ),
    # Nintendo DS Lite Handheld-System Weiss Touchscreen inkl. 4 Spiele
    "https://www.ebay.de/itm/398266334210": (
        ASSESSMENT_MANUAL_REVIEW,
        CONFIDENCE_LOW,
        [
            "3 weitere, lexikalisch identisch formulierte 'Handheld-System'-Titel im "
            "aktuellen Korpus/Preishistorie gefunden, davon 1 selbst als UNCLEAR (nicht "
            "FALSE_POSITIVE) gelabelt -- kein lexikalisches Unterscheidungsmerkmal zwischen "
            "dem bestaetigten FP und den mutmasslich echten Treffern gefunden.",
            "Nutzerentscheidung 2026-08-15 nach Rueckfrage: nicht fixen, aber auch nicht als "
            "Ground-Truth-Konflikt einstufen -- Status bleibt unsicher (siehe "
            "active_fp_fix_progress.md).",
        ],
    ),
}


@dataclass
class FalsePositiveCase:
    listing_id: str
    title: str
    price: float
    stored_category: str
    ground_truth_verdict: str
    stored_rule: str
    current_category: str
    current_rule: str
    match_path_before: str
    match_path_after: str
    match_state: str
    routing_status: str
    already_resolved: bool
    root_cause: str
    root_cause_confidence: str
    root_cause_evidence: list[str]
    recommended_fix_type: str
    regression_risk: str
    # Zwei-Ebenen-Assessment (siehe Moduldocstring): getrennt vom rohen
    # routing_status, da routing_status ein objektiver evaluate()-Zustand
    # ist, waehrend assessment_status auch eine (dokumentierte, nie
    # automatisch erfundene) menschliche Uebersteuerung einschliessen kann.
    assessment_status: str = ASSESSMENT_STILL_ACTIVE
    assessment_confidence: str = CONFIDENCE_MANUAL_REVIEW
    assessment_evidence: list[str] = field(default_factory=list)


@dataclass
class FpCandidateCase:
    listing_id: str
    title: str
    price: float
    stored_category: str
    ground_truth_verdict: str
    stored_rule: str
    current_category: str
    current_rule: str
    match_state: str
    note: str
    # additiv, fuer ein einheitliches Zwei-Ebenen-Schema mit FalsePositiveCase
    # (siehe ground_truth_routing_assessment.py).
    routing_status: str = NOT_AVAILABLE
    # UNCLEAR-Faelle erhalten IMMER MANUAL_REVIEW -- niemals automatisch zu
    # FALSE_POSITIVE/TRUE_POSITIVE aufgeloest (Auftrag "Fall E").
    assessment_status: str = ASSESSMENT_MANUAL_REVIEW
    assessment_confidence: str = CONFIDENCE_MANUAL_REVIEW
    assessment_evidence: list[str] = field(default_factory=list)


@dataclass
class FixQueueEntry:
    priority: str
    category: str
    affected_count: int
    representative_listings: list[dict] = field(default_factory=list)
    root_cause: str = ROOT_CAUSE_UNKNOWN
    confidence: str = CONFIDENCE_MANUAL_REVIEW
    current_rule: str = NOT_AVAILABLE
    recommended_fix_type: str = "unknown"
    regression_risk: str = "MEDIUM"
    affected_categories: list[str] = field(default_factory=list)
    test_requirements: list[str] = field(default_factory=list)
    still_active_count: int = 0
    priority_score: int = 0
    # Auftrag "Fix-Queue-Anpassung": darf NICHT mehr implizieren, dass jeder
    # historische FP ein aktuell zu fixender Fall ist. Nur
    # ACTIVE_ROUTING_FP-Eintraege bekommen eine P0-P3-Prioritaet.
    queue_category: str = QUEUE_CATEGORY_MANUAL_REVIEW


def _match_path(category: str | None, rule: str | None) -> str:
    if not category and not rule:
        return NOT_AVAILABLE
    return f"{category or NOT_AVAILABLE} :: {rule or NOT_AVAILABLE}"


def load_forensics_entries(path: Path = FORENSICS_SOURCE) -> list[dict]:
    """Liest das Forensik-Rohartefakt genau einmal vollstaendig (Performance-
    Vorgabe: nicht mehrfach laden). Kein Filtern/Bewerten hier."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("entries", [])


def _translate_root_cause(
    raw_root_cause: str | None, reason: str | None
) -> tuple[str, str, list[str]]:
    evidence: list[str] = []
    if raw_root_cause:
        evidence.append(f'Forensik-Snapshot root_cause: "{raw_root_cause}"')
    if reason:
        evidence.append(f'Forensik-Snapshot reason: "{reason}"')

    translation = (
        _FORENSICS_ROOT_CAUSE_TRANSLATION.get(raw_root_cause)
        if raw_root_cause
        else None
    )
    if translation is None:
        evidence.append(
            "Kein bekannter Uebersetzungseintrag fuer diesen Forensik-root_cause-Wert -- "
            "keine automatische Taxonomie-Zuordnung ohne Beleg."
        )
        return ROOT_CAUSE_AMBIGUOUS, CONFIDENCE_MANUAL_REVIEW, evidence

    canonical, confidence = translation
    return canonical, confidence, evidence


def _compute_fp_assessment(
    listing_id: str, routing_status: str
) -> tuple[str, str, list[str]]:
    """Leitet assessment.status/confidence/evidence rein aus dem objektiven
    routing_status ab (Faelle A-C des Auftrags) -- AUSSER es existiert ein
    dokumentierter manueller Override (Fall D des Auftrags: 'zusaetzliche
    manuelle Evidenz zeigt, dass der historische FP vermutlich eigentlich
    ein TRUE_POSITIVE war'). Erfindet nichts: ANDERE_REGEL (gleiche
    Kategorie, anderer Matchpfad) wird nie automatisch als TP/FP entschieden,
    sondern als MANUAL_REVIEW ausgewiesen (Auftrag "FALSE_POSITIVE -> OTHER_
    RULE = separat pruefen")."""
    override = _MANUAL_ASSESSMENT_OVERRIDES.get(listing_id)
    if override:
        return override

    if routing_status == ROUTING_STATUS_NO_MATCH:
        return (
            ASSESSMENT_FIXED,
            CONFIDENCE_CONFIRMED,
            [
                "aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt."
            ],
        )
    if routing_status == ROUTING_STATUS_SAME_CATEGORY:
        return (
            ASSESSMENT_STILL_ACTIVE,
            CONFIDENCE_CONFIRMED,
            [
                "aktueller Match-Zustand: GLEICHE_KATEGORIE -- Fehltreffer weiterhin "
                "unveraendert aktiv (keine dokumentierte Uebersteuerung vorhanden)."
            ],
        )
    if routing_status == ROUTING_STATUS_CATEGORY_CHANGED:
        return (
            ASSESSMENT_CATEGORY_CHANGED,
            CONFIDENCE_CONFIRMED,
            [
                "aktueller Match-Zustand: ANDERE_KATEGORIE -- gilt NICHT automatisch als "
                "Fix (Auftragsvorgabe), erfordert gesonderte Pruefung.",
            ],
        )
    if routing_status == ROUTING_STATUS_RULE_CHANGED:
        return (
            ASSESSMENT_MANUAL_REVIEW,
            CONFIDENCE_MEDIUM,
            [
                "aktueller Match-Zustand: ANDERE_REGEL (gleiche Kategorie, anderer "
                "Matchpfad) -- separat zu pruefen, kein automatisches TP/FP-Urteil moeglich.",
            ],
        )
    raise ValueError(f"unbekannter routing_status: {routing_status!r}")  # pragma: no cover


def build_case(entry: dict, rules_cfg: dict) -> FalsePositiveCase:
    title = entry.get("title")
    price = entry.get("price", 0.0) or 0.0
    url = entry.get("url") or NOT_AVAILABLE
    stored_category = entry.get("category") or NOT_AVAILABLE
    stored_rule = entry.get("stored_rule_label") or NOT_AVAILABLE

    result = evaluate(title, price, rules_cfg) if title else None
    after_state = _after_match_state(
        result, entry.get("category"), entry.get("stored_rule_label")
    )
    routing_status = _AFTER_STATE_TO_ROUTING_STATUS[after_state]

    matched = bool(result and result.matched)
    current_category = result.category if matched else "KEIN_TREFFER"
    current_rule = result.rule_label if matched else "KEIN_TREFFER"

    root_cause, confidence, evidence = _translate_root_cause(
        entry.get("root_cause"), entry.get("reason")
    )
    evidence.append(
        f"aktueller Match-Zustand: {after_state} (routing_status={routing_status})"
    )

    fix_type = _FIX_TYPE_BY_ROOT_CAUSE.get(root_cause, "unknown")
    risk = _REGRESSION_RISK_BY_FIX_TYPE.get(fix_type, "MEDIUM")

    assessment_status, assessment_confidence, assessment_evidence = (
        _compute_fp_assessment(url, routing_status)
    )

    return FalsePositiveCase(
        listing_id=url,
        title=title or NOT_AVAILABLE,
        price=price,
        stored_category=stored_category,
        ground_truth_verdict=entry.get("verdict") or NOT_AVAILABLE,
        stored_rule=stored_rule,
        current_category=current_category,
        current_rule=current_rule,
        match_path_before=_match_path(
            entry.get("category"), entry.get("stored_rule_label")
        ),
        match_path_after=_match_path(result.category, result.rule_label)
        if matched
        else "KEIN_TREFFER",
        match_state=after_state,
        routing_status=routing_status,
        already_resolved=routing_status in RESOLVED_ROUTING_STATUSES,
        root_cause=root_cause,
        root_cause_confidence=confidence,
        root_cause_evidence=evidence,
        recommended_fix_type=fix_type,
        regression_risk=risk,
        assessment_status=assessment_status,
        assessment_confidence=assessment_confidence,
        assessment_evidence=assessment_evidence,
    )


def build_candidate(entry: dict, rules_cfg: dict) -> FpCandidateCase:
    title = entry.get("title")
    price = entry.get("price", 0.0) or 0.0

    result = evaluate(title, price, rules_cfg) if title else None
    after_state = _after_match_state(
        result, entry.get("category"), entry.get("stored_rule_label")
    )
    matched = bool(result and result.matched)
    routing_status = _AFTER_STATE_TO_ROUTING_STATUS[after_state]

    return FpCandidateCase(
        listing_id=entry.get("url") or NOT_AVAILABLE,
        title=title or NOT_AVAILABLE,
        price=price,
        stored_category=entry.get("category") or NOT_AVAILABLE,
        ground_truth_verdict=entry.get("verdict") or NOT_AVAILABLE,
        stored_rule=entry.get("stored_rule_label") or NOT_AVAILABLE,
        current_category=result.category if matched else "KEIN_TREFFER",
        current_rule=result.rule_label if matched else "KEIN_TREFFER",
        match_state=after_state,
        routing_status=routing_status,
        note=(
            "FP-Kandidat (Ground-Truth-Verdict UNCLEAR) -- kein bestaetigter "
            "Fehltreffer, daher KEINE Root-Cause-Klassifikation ohne Beleg."
        ),
        assessment_evidence=[
            "historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird "
            "gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder "
            "TRUE_POSITIVE aufgeloest.",
            f"aktueller Match-Zustand: {after_state}",
        ],
    )


def extract_cases(
    entries: list[dict], rules_cfg: dict, category: str | None = None
) -> tuple[list[FalsePositiveCase], list[FpCandidateCase]]:
    """Trennt bestaetigte FALSE_POSITIVE-Faelle von blossen UNCLEAR-Kandidaten
    (Auftrag "KRITISCHE METHODISCHE REGEL": nie vermischen)."""
    confirmed: list[FalsePositiveCase] = []
    candidates: list[FpCandidateCase] = []
    for entry in entries:
        verdict = entry.get("verdict")
        if verdict not in ("FALSE_POSITIVE", "UNCLEAR"):
            continue
        if category and entry.get("category") != category:
            continue
        if verdict == "FALSE_POSITIVE":
            confirmed.append(build_case(entry, rules_cfg))
        else:
            candidates.append(build_candidate(entry, rules_cfg))
    return confirmed, candidates


def group_by_category(cases: list) -> dict[str, list]:
    grouped: dict[str, list] = defaultdict(list)
    for c in cases:
        grouped[c.stored_category].append(c)
    return dict(sorted(grouped.items()))


def _priority_score(bucket_cases: list[FalsePositiveCase]) -> int:
    still_active = sum(1 for c in bucket_cases if not c.already_resolved)
    confidence = bucket_cases[0].root_cause_confidence
    risk = bucket_cases[0].regression_risk
    cross_category = any(
        c.routing_status
        in (ROUTING_STATUS_CATEGORY_CHANGED, ROUTING_STATUS_RULE_CHANGED)
        for c in bucket_cases
    )
    score = 2 * still_active + _CONFIDENCE_WEIGHT.get(confidence, 0)
    if cross_category:
        score += 1
    if risk == "HIGH":
        score -= 1
    return score


def _priority_tier(score: int) -> str:
    if score >= 4:
        return "P0"
    if score >= 2:
        return "P1"
    if score >= 1:
        return "P2"
    return "P3"


# Praezedenz, wenn ein Bucket (Kategorie+Regel+root_cause) Faelle mit
# unterschiedlichem assessment_status mischt (in der aktuellen Datenlage
# nicht der Fall, aber nicht ausgeschlossen): der "dringendste" Status
# bestimmt die queue_category des gesamten Buckets.
_ASSESSMENT_TO_QUEUE_CATEGORY = {
    ASSESSMENT_STILL_ACTIVE: QUEUE_CATEGORY_ACTIVE_ROUTING_FP,
    ASSESSMENT_CATEGORY_CHANGED: QUEUE_CATEGORY_ACTIVE_ROUTING_FP,
    ASSESSMENT_MANUAL_REVIEW: QUEUE_CATEGORY_MANUAL_REVIEW,
    ASSESSMENT_GROUND_TRUTH_CONFLICT: QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT,
    ASSESSMENT_FIXED: QUEUE_CATEGORY_ALREADY_FIXED,
}
_QUEUE_CATEGORY_PRECEDENCE = [
    QUEUE_CATEGORY_ACTIVE_ROUTING_FP,
    QUEUE_CATEGORY_MANUAL_REVIEW,
    QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT,
    QUEUE_CATEGORY_ALREADY_FIXED,
]


def _bucket_queue_category(bucket_cases: list[FalsePositiveCase]) -> str:
    present = {
        _ASSESSMENT_TO_QUEUE_CATEGORY[c.assessment_status] for c in bucket_cases
    }
    for qc in _QUEUE_CATEGORY_PRECEDENCE:
        if qc in present:
            return qc
    return QUEUE_CATEGORY_MANUAL_REVIEW  # pragma: no cover -- defensiver Fallback


def build_fix_queue(cases: list[FalsePositiveCase]) -> list[FixQueueEntry]:
    """Baut die priorisierte Fix-Queue (Auftrag Funktion 6/7). Ein Bucket =
    eine Kategorie + eine Regel + eine root_cause, da eine YAML-Aenderung
    typischerweise genau eine Regel adressiert. Aendert NIE selbst YAML.

    WICHTIG (Auftrag "Fix-Queue-Anpassung"): ein historischer FP impliziert
    NICHT mehr automatisch einen aktuell zu fixenden Fall. Nur Buckets mit
    queue_category=ACTIVE_ROUTING_FP bekommen eine P0-P3-Prioritaet;
    GROUND_TRUTH_CONFLICT/MANUAL_REVIEW/ALREADY_FIXED-Buckets werden nie
    als aktiver YAML-Fix priorisiert (priority="N/A")."""
    buckets: dict[tuple[str, str, str], list[FalsePositiveCase]] = defaultdict(list)
    for c in cases:
        buckets[(c.stored_category, c.stored_rule, c.root_cause)].append(c)

    entries: list[FixQueueEntry] = []
    for (category, rule, root_cause), bucket_cases in buckets.items():
        queue_category = _bucket_queue_category(bucket_cases)
        if queue_category == QUEUE_CATEGORY_ACTIVE_ROUTING_FP:
            score = _priority_score(bucket_cases)
            priority = _priority_tier(score)
        else:
            score = 0
            priority = "N/A"
        still_active = sum(
            1
            for c in bucket_cases
            if c.assessment_status
            in (ASSESSMENT_STILL_ACTIVE, ASSESSMENT_CATEGORY_CHANGED)
        )
        affected_categories = sorted(
            {category}
            | {
                c.current_category
                for c in bucket_cases
                if c.current_category not in (category, "KEIN_TREFFER")
            }
        )
        fix_type = bucket_cases[0].recommended_fix_type
        risk = bucket_cases[0].regression_risk
        confidence = bucket_cases[0].root_cause_confidence

        test_requirements = [
            f"bestehende TRUE_POSITIVE-Tests fuer Regel '{rule}' in Kategorie '{category}' "
            f"(z.B. app/tests/test_{category}.py, falls vorhanden) muessen weiterhin gruen bleiben",
            f"Regression gegen alle {len(bucket_cases)} bekannten FP-Faelle dieser Gruppe "
            "(siehe representative_listings)",
        ]
        if len(affected_categories) > 1:
            test_requirements.append(
                "Cross-Category-Check: "
                + ", ".join(a for a in affected_categories if a != category)
                + " -- sicherstellen, dass die Aenderung dort keine neuen Fehltreffer erzeugt"
            )
        test_requirements.append(
            "tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)"
        )
        if queue_category == QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT:
            test_requirements.append(
                "KEINE YAML-Aenderung geplant -- historisches FALSE_POSITIVE-Label gilt als "
                "vermutlich fehlerhaft, aktuelles Matcher-Verhalten wird als korrekt eingestuft."
            )
        elif queue_category == QUEUE_CATEGORY_MANUAL_REVIEW:
            test_requirements.append(
                "KEINE automatische YAML-Aenderung -- Status bleibt unsicher, erfordert "
                "zusaetzliche Evidenz (z.B. Beschreibungstext/Bildmaterial) vor einer Entscheidung."
            )

        entries.append(
            FixQueueEntry(
                priority=priority,
                category=category,
                affected_count=len(bucket_cases),
                representative_listings=[
                    {"listing_id": c.listing_id, "title": c.title, "price": c.price}
                    for c in bucket_cases[:3]
                ],
                root_cause=root_cause,
                confidence=confidence,
                current_rule=rule,
                recommended_fix_type=fix_type,
                regression_risk=risk,
                affected_categories=affected_categories,
                test_requirements=test_requirements,
                still_active_count=still_active,
                priority_score=score,
                queue_category=queue_category,
            )
        )

    _queue_category_order = {
        QUEUE_CATEGORY_ACTIVE_ROUTING_FP: 0,
        QUEUE_CATEGORY_MANUAL_REVIEW: 1,
        QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT: 2,
        QUEUE_CATEGORY_ALREADY_FIXED: 3,
    }
    entries.sort(
        key=lambda e: (
            _queue_category_order.get(e.queue_category, 9),
            -e.priority_score,
            e.category,
            e.current_rule,
        )
    )
    return entries


def build_report(
    input_path: Path = FORENSICS_SOURCE,
    category: str | None = None,
    only_fp: bool = False,
    rules_cfg: dict | None = None,
) -> dict:
    if rules_cfg is None:
        rules_cfg = load_current_rules()

    entries = load_forensics_entries(input_path)

    verdict_counts = {"TRUE_POSITIVE": 0, "FALSE_POSITIVE": 0, "UNCLEAR": 0}
    for e in entries:
        v = e.get("verdict")
        if v in verdict_counts:
            verdict_counts[v] += 1

    consistency_notes = []
    for verdict, expected in KNOWN_REFERENCE_COUNTS.items():
        actual = verdict_counts.get(verdict, 0)
        if actual != expected:
            consistency_notes.append(
                f"Abweichung bei {verdict}: erwartet {expected} (bekannter Referenzstand, "
                f"siehe label_store.py-Docstring), tatsaechlich {actual} in {input_path}."
            )
    if not consistency_notes:
        consistency_notes.append("keine Abweichung zum bekannten Referenzstand")

    # Fix-Queue ist ein kanonisches Artefakt und wird IMMER aus dem
    # vollstaendigen, ungefilterten bestaetigten FP-Datensatz gebaut (siehe
    # Moduldocstring) -- --category/--only-fp filtern nur die Anzeige.
    confirmed_all, candidates_all = extract_cases(entries, rules_cfg, category=None)
    fix_queue_canonical = build_fix_queue(confirmed_all)

    confirmed_view, candidates_view = extract_cases(
        entries, rules_cfg, category=category
    )
    if only_fp:
        candidates_view = []

    confirmed_by_category = group_by_category(confirmed_view)
    candidates_by_category = group_by_category(candidates_view)

    fix_queue_view = (
        [e for e in fix_queue_canonical if e.category == category]
        if category
        else fix_queue_canonical
    )

    return {
        "meta": {
            "input_source": str(input_path),
            "total_entries_in_source": len(entries),
            "verdict_distribution_in_source": verdict_counts,
            "known_reference_counts": KNOWN_REFERENCE_COUNTS,
            "consistency_notes": consistency_notes,
            "filter_category": category,
            "filter_only_fp": only_fp,
            "confirmed_fp_count_total": len(confirmed_all),
            "confirmed_fp_count_filtered": len(confirmed_view),
            "fp_candidate_count_total": len(candidates_all),
            "categories_with_confirmed_fp": sorted(group_by_category(confirmed_all)),
        },
        "confirmed_by_category": confirmed_by_category,
        "candidates_by_category": candidates_by_category,
        "fix_queue_view": fix_queue_view,
        "fix_queue_canonical": fix_queue_canonical,
    }


def _serialize(report: dict) -> dict:
    return {
        "meta": report["meta"],
        "confirmed_by_category": {
            k: [asdict(c) for c in v]
            for k, v in report["confirmed_by_category"].items()
        },
        "candidates_by_category": {
            k: [asdict(c) for c in v]
            for k, v in report["candidates_by_category"].items()
        },
        "fix_queue": [asdict(e) for e in report["fix_queue_view"]],
    }


def render_text_report(report: dict) -> str:
    confirmed_by_category = report["confirmed_by_category"]
    candidates_by_category = report["candidates_by_category"]
    fix_queue = report["fix_queue_view"]

    lines: list[str] = []
    lines.append("FALSE POSITIVES BY CATEGORY")
    lines.append("=" * 28)
    lines.append("")

    if not confirmed_by_category:
        lines.append(
            "(keine bestaetigten FALSE_POSITIVE-Faelle fuer den aktuellen Filter)"
        )
        lines.append("")

    for category, cases in confirmed_by_category.items():
        lines.append(f"{category} ({len(cases)})")
        lines.append("")
        for i, c in enumerate(cases, 1):
            lines.append(f"  FP #{i}")
            lines.append(f"    title: {c.title}")
            lines.append(f"    url: {c.listing_id}")
            lines.append(f"    stored_category: {c.stored_category}")
            lines.append(f"    current_category: {c.current_category}")
            lines.append(f"    stored_rule: {c.stored_rule}")
            lines.append(f"    current_rule: {c.current_rule}")
            lines.append(
                f"    match_path: {c.match_path_before} -> {c.match_path_after}"
            )
            lines.append(
                f"    match_state: {c.match_state} (routing_status={c.routing_status})"
            )
            lines.append(f"    root_cause: {c.root_cause}")
            lines.append(f"    confidence: {c.root_cause_confidence}")
            lines.append("    evidence:")
            for ev in c.root_cause_evidence:
                lines.append(f"      - {ev}")
            lines.append(f"    recommended_fix: {c.recommended_fix_type}")
            lines.append(f"    regression_risk: {c.regression_risk}")
            lines.append(
                f"    assessment: {c.assessment_status} (confidence={c.assessment_confidence})"
            )
            for ev in c.assessment_evidence:
                lines.append(f"      - {ev}")
            lines.append("")
        lines.append("")

    if candidates_by_category:
        lines.append(
            "FP-KANDIDATEN (Ground-Truth-Verdict UNCLEAR -- KEINE bestaetigten FPs)"
        )
        lines.append("=" * 70)
        for category, cases in candidates_by_category.items():
            lines.append(f"{category} ({len(cases)})")
            for c in cases[:10]:
                lines.append(f"  - {c.title} [{c.match_state}]")
            if len(cases) > 10:
                lines.append(f"  ... und {len(cases) - 10} weitere")
            lines.append("")

    lines.append("CATEGORY SUMMARY")
    lines.append("=" * 16)
    header = f"{'category':<20} | {'confirmed FP':<12} | {'candidates':<10} | {'root causes':<45} | priority"
    lines.append(header)
    all_categories = sorted(set(confirmed_by_category) | set(candidates_by_category))
    for category in all_categories:
        confirmed_n = len(confirmed_by_category.get(category, []))
        candidate_n = len(candidates_by_category.get(category, []))
        root_causes = sorted(
            {c.root_cause for c in confirmed_by_category.get(category, [])}
        )
        cat_priorities = sorted(
            {e.priority for e in fix_queue if e.category == category}
        )
        lines.append(
            f"{category:<20} | {confirmed_n:<12} | {candidate_n:<10} | "
            f"{', '.join(root_causes) or '-':<45} | {', '.join(cat_priorities) or '-'}"
        )
    lines.append("")

    lines.append("FIX QUEUE")
    lines.append("=" * 9)
    lines.append(
        "Gruppiert nach queue_category -- nur ACTIVE_ROUTING_FP hat eine P0-P3-Prioritaet, "
        "die anderen Kategorien implizieren KEINEN offenen YAML-Fix-Bedarf."
    )
    lines.append("")
    for qc in (
        QUEUE_CATEGORY_ACTIVE_ROUTING_FP,
        QUEUE_CATEGORY_MANUAL_REVIEW,
        QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT,
        QUEUE_CATEGORY_ALREADY_FIXED,
    ):
        qc_entries = [e for e in fix_queue if e.queue_category == qc]
        if not qc_entries:
            continue
        lines.append(f"{qc}:")
        for tier in ("P0", "P1", "P2", "P3", "N/A"):
            tier_entries = [e for e in qc_entries if e.priority == tier]
            for e in tier_entries:
                prio = f"{tier}: " if tier != "N/A" else ""
                lines.append(
                    f"  {prio}[{e.category}] Regel '{e.current_rule}' -- root_cause={e.root_cause} "
                    f"(confidence={e.confidence}), {e.affected_count} Fall/Faelle "
                    f"({e.still_active_count} weiterhin aktiv) -- "
                    f"fix={e.recommended_fix_type}, risk={e.regression_risk}"
                )
        lines.append("")

    return "\n".join(lines)


def render_fix_queue_markdown(fix_queue: list[FixQueueEntry]) -> str:
    lines = [
        "# False-Positive Fix-Queue",
        "",
        "Automatisch generiert von `tools/ruleset_quality/forensics_false_positives.py`. "
        "Aendert KEINE YAML-Regeln -- die Entscheidung liegt beim Entwickler.",
        "",
    ]
    for qc in (
        QUEUE_CATEGORY_ACTIVE_ROUTING_FP,
        QUEUE_CATEGORY_MANUAL_REVIEW,
        QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT,
        QUEUE_CATEGORY_ALREADY_FIXED,
    ):
        qc_entries = [e for e in fix_queue if e.queue_category == qc]
        if not qc_entries:
            continue
        lines.append(f"## {qc}")
        lines.append("")
        for e in qc_entries:
            heading = (
                f"### [{e.priority}] {e.category} :: {e.current_rule}"
                if e.priority != "N/A"
                else f"### {e.category} :: {e.current_rule}"
            )
            lines.append(heading)
            lines.append("")
            lines.append(
                f"- **Problem**: {e.affected_count} bestaetigte(r) historische(r) Fehltreffer, "
                f"root_cause=`{e.root_cause}` (confidence={e.confidence}), "
                f"{e.still_active_count} davon aktuell noch als aktives Routing-Problem "
                "eingestuft."
            )
            lines.append(f"- **Vorschlag**: `{e.recommended_fix_type}`")
            lines.append(f"- **Regression-Risiko**: {e.regression_risk}")
            lines.append(
                f"- **Betroffene Kategorien**: {', '.join(e.affected_categories)}"
            )
            lines.append("- **Regressionstests**:")
            for t in e.test_requirements:
                lines.append(f"  - {t}")
            lines.append("- **Beispiel-Listings**:")
            for listing in e.representative_listings:
                lines.append(f"  - {listing['title']} ({listing['listing_id']})")
            lines.append("")
    if not any(e for e in fix_queue):
        lines.append("(keine Eintraege)")
    return "\n".join(lines)


def write_outputs(report: dict, output_path: Path | None = None) -> dict[str, Path]:
    written: dict[str, Path] = {}
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = REPORTS_DIR / "forensics_false_positives_report.md"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = render_text_report(report)
    output_path.write_text(text, encoding="utf-8")
    written["text_report"] = output_path

    json_path = output_path.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(_serialize(report), f, indent=2, ensure_ascii=False)
    written["json_report"] = json_path

    # Fix-Queue: kanonisches Artefakt an fixem Pfad (Auftrag Funktion 6),
    # IMMER aus dem vollstaendigen ungefilterten Datensatz.
    with FIX_QUEUE_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            [asdict(e) for e in report["fix_queue_canonical"]],
            f,
            indent=2,
            ensure_ascii=False,
        )
    written["fix_queue_json"] = FIX_QUEUE_JSON

    FIX_QUEUE_MD.write_text(
        render_fix_queue_markdown(report["fix_queue_canonical"]), encoding="utf-8"
    )
    written["fix_queue_md"] = FIX_QUEUE_MD

    return written


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.ruleset_quality.forensics_false_positives",
        description=(
            "Category-False-Positive-Forensics + priorisierte Fix-Queue. "
            "Read-only -- aendert keine YAML-Regeln."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=FORENSICS_SOURCE,
        help="Pfad zum Forensik-Ground-Truth-Artefakt (Default: docs/DASHBOARD_MATCH_FORENSICS.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Pfad fuer den Text-/JSON-Report (Default: generated/reports/forensics_false_positives_report.md)",
    )
    parser.add_argument(
        "--category", type=str, default=None, help="Nur diese Kategorie anzeigen"
    )
    parser.add_argument(
        "--only-fp",
        action="store_true",
        help="Nur bestaetigte FALSE_POSITIVE anzeigen, keine UNCLEAR-FP-Kandidaten",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Zusaetzliche Fortschrittsausgaben"
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)

    if args.verbose:
        print(f"Lade Forensik-Artefakt: {args.input}")

    rules_cfg = load_current_rules()
    report = build_report(
        input_path=args.input,
        category=args.category,
        only_fp=args.only_fp,
        rules_cfg=rules_cfg,
    )

    if args.verbose:
        meta = report["meta"]
        print(
            f"{meta['confirmed_fp_count_total']} bestaetigte FP insgesamt, "
            f"{meta['confirmed_fp_count_filtered']} nach Filter angezeigt."
        )
        for note in meta["consistency_notes"]:
            print(f"Konsistenz: {note}")

    print(render_text_report(report))
    print()

    written = write_outputs(report, args.output)
    for label, path in written.items():
        print(f"geschrieben ({label}): {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
