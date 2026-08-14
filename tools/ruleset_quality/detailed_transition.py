"""Finale Read-only-Revalidierung: detaillierter Vorher/Nachher-Vergleich
pro Listing (Auftrag Abschnitt 3-9) + Regression-Gate v2 (Abschnitt 6).

Baut auf denselben Bausteinen wie benchmark.py (Phase 19) auf, erweitert
das Transition-Schema aber um:

  - price_history_model (alt/neu, NOT_AVAILABLE wenn nicht rekonstruierbar
    -- found.json speichert dieses Feld nicht, siehe baseline.py)
  - match_path_before/match_path_after (= rule_label, explizit benannt)
  - eine zweite, striktere Gate-Klassifikation (classify_gate_v2()), die
    EXAKT der im Auftrag vorgegebenen CRITICAL/HIGH/MEDIUM/LOW-Matrix folgt

WICHTIGE EPISTEMISCHE EINSCHRAENKUNG (nicht verschweigen, siehe
Abschlussbericht): "TRUE_POSITIVE -> FALSE_POSITIVE" (und jede andere
Transition, die ein NEUES TP/FP/UNCLEAR-Urteil verlangt, ohne dass sich
der Match-Zustand selbst aendert) ist aus evaluate()/is_still_valid_
category() allein NICHT objektiv ableitbar -- das waere eine neue
Bewertungslogik, kein Regressionscheck. Wo der Auftrag genau das verlangt,
wird ein klar als "Kandidat, manuelle Pruefung noetig" markierter Fund
erzeugt, NIE eine stillschweigende Automatik-Entscheidung.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .common import REPORTS_DIR, evaluate, load_current_rules, current_ruleset_signature

NOT_AVAILABLE = "NOT_AVAILABLE"


@dataclass
class ListingTransition:
    listing_id: str
    title: str
    price: float

    stored_category: str | None
    new_category: str | None

    stored_rule: str | None
    new_rule: str | None

    stored_price_history_model: str
    new_price_history_model: str

    stored_status: str  # TRUE_POSITIVE | FALSE_POSITIVE | UNCLEAR | NOT_AVAILABLE
    new_status: str  # dito, ODER "UNVERAENDERT_ANGENOMMEN" (siehe Docstring) / "MANUELLE_PRUEFUNG_NOETIG"

    match_path_before: str
    match_path_after: str

    after_match_state: str  # KEIN_TREFFER | UNVERAENDERT | REGEL_GEAENDERT | KATEGORIE_GEAENDERT

    findings: list[dict] = field(default_factory=list)


def _match_path(category: str | None, rule: str | None) -> str:
    if not category and not rule:
        return NOT_AVAILABLE
    return f"{category or NOT_AVAILABLE} :: {rule or NOT_AVAILABLE}"


def _after_match_state(result, stored_category: str | None, stored_rule: str | None) -> str:
    if not result or not result.matched:
        return "KEIN_TREFFER"
    if result.category != stored_category:
        return "KATEGORIE_GEAENDERT"
    if stored_rule is not None and result.rule_label != stored_rule:
        return "REGEL_GEAENDERT"
    return "UNVERAENDERT"


def _derive_new_status(stored_status: str, after_state: str) -> str:
    """Nur dort ein neues TP/FP/UNCLEAR-Urteil ausgeben, wo es sich
    LOGISCH zwingend aus dem unveraenderten Match-Zustand ergibt (siehe
    Moduldocstring) -- sonst MANUELLE_PRUEFUNG_NOETIG statt Raten."""
    if after_state == "KEIN_TREFFER":
        return "KEIN_TREFFER"
    if after_state == "UNVERAENDERT" and stored_status != NOT_AVAILABLE:
        # Titel/Preis/Kategorie/Regel identisch zum Bewertungszeitpunkt ->
        # der Gegenstand der damaligen Bewertung hat sich nicht geaendert.
        return stored_status
    if stored_status == NOT_AVAILABLE:
        return NOT_AVAILABLE
    return "MANUELLE_PRUEFUNG_NOETIG"


def _gate_findings(stored_status: str, after_state: str, phm_changed: bool | None) -> list[dict]:
    """Implementiert die Auftrags-Matrix (Abschnitt 6) so praezise wie mit
    evaluate() objektiv moeglich. `phm_changed` ist None, wenn
    stored_price_history_model NOT_AVAILABLE ist (found.json-Korpus) --
    dann werden die price_history_model-Faelle uebersprungen, NICHT als
    "unveraendert" angenommen."""
    findings: list[dict] = []

    def add(severity: str, label: str, confirmed: bool, explanation: str):
        findings.append({
            "severity": severity, "label": label, "confirmed": confirmed,
            "explanation": explanation,
        })

    if stored_status == "TRUE_POSITIVE":
        if after_state == "KEIN_TREFFER":
            add("CRITICAL", "TRUE_POSITIVE -> kein Treffer", True,
                "Objektiv bestaetigt: evaluate() liefert keinen Treffer mehr.")
        elif after_state == "KATEGORIE_GEAENDERT":
            add("HIGH", "Kategoriewechsel eines TRUE_POSITIVE", True,
                "Objektiv bestaetigt: neue Kategorie != gespeicherte Kategorie. "
                "Ob das neue Ergebnis TRUE_POSITIVE/FALSE_POSITIVE/UNCLEAR ist, "
                "erfordert eine neue menschliche Bewertung (nicht automatisch ableitbar).")
        elif after_state == "REGEL_GEAENDERT":
            add("HIGH", "TRUE_POSITIVE: Regelwechsel bei gleicher Kategorie (First-Match-Wins)", True,
                "Objektiv bestaetigt: gleiche Kategorie, aber anderer Matchpfad (siehe Abschnitt 9). "
                "'TRUE_POSITIVE -> FALSE_POSITIVE'/'-> UNCLEAR' im engeren Sinn ist daraus NICHT "
                "automatisch ableitbar -- Kandidat fuer manuelle Pruefung.")
        if phm_changed is True and after_state != "KEIN_TREFFER":
            add("HIGH", "TRUE_POSITIVE: price_history_model geaendert", True,
                "Objektiv bestaetigt ueber gespeichertes vs. neu ermitteltes price_history_model.")

    elif stored_status == "FALSE_POSITIVE":
        if after_state == "KEIN_TREFFER":
            add("INFO", "FALSE_POSITIVE -> kein Treffer", True,
                "Fix wirkt wie erwartet -- bekannter Fehltreffer matcht nicht mehr.")
        elif after_state in ("KATEGORIE_GEAENDERT", "REGEL_GEAENDERT"):
            add("LOW", "FALSE_POSITIVE: Matchpfad geaendert, weiterhin ein Treffer", False,
                "Kandidat fuer 'FALSE_POSITIVE -> TRUE_POSITIVE/UNCLEAR' -- nicht automatisch "
                "entscheidbar, manuelle Pruefung noetig.")
        else:
            add("LOW", "FALSE_POSITIVE weiterhin unveraendert aktiv", True,
                "Bekannter Fehltreffer weiterhin identisch aktiv -- kein neues Urteil noetig, "
                "der bewertete Gegenstand hat sich nicht geaendert.")

    elif stored_status == "UNCLEAR":
        if after_state == "KEIN_TREFFER":
            add("INFO", "UNCLEAR -> kein Treffer", True, "Ehemals unklarer Fall matcht nicht mehr.")
        elif after_state == "KATEGORIE_GEAENDERT":
            add("MEDIUM", "Kategoriewechsel eines UNCLEAR", True,
                "Objektiv bestaetigt. 'UNCLEAR -> FALSE_POSITIVE' im engeren Sinn nicht automatisch "
                "ableitbar -- manuelle Pruefung noetig.")
        elif after_state == "REGEL_GEAENDERT":
            add("MEDIUM", "UNCLEAR: Regelwechsel bei gleicher Kategorie", True,
                "Objektiv bestaetigt -- manuelle Pruefung noetig, ob sich die Unklarheit aufloest.")
        if phm_changed is True and after_state != "KEIN_TREFFER":
            add("MEDIUM", "UNCLEAR: price_history_model geaendert", True,
                "Objektiv bestaetigt ueber gespeichertes vs. neu ermitteltes price_history_model.")

    return findings


def build_detailed_transitions(baseline: dict, rules_cfg: dict | None = None) -> list[ListingTransition]:
    if rules_cfg is None:
        rules_cfg = load_current_rules()

    transitions: list[ListingTransition] = []
    for e in baseline["entries"]:
        title = e.get("title")
        price = e.get("price", 0.0) or 0.0
        stored_category = e.get("stored_category")
        stored_rule = e.get("stored_rule_label")
        stored_phm = e.get("stored_price_history_model", NOT_AVAILABLE)
        stored_status = e.get("ground_truth_verdict", NOT_AVAILABLE)
        if stored_status == "UNLABELED":
            stored_status = NOT_AVAILABLE

        result = evaluate(title, price, rules_cfg) if title else None
        after_state = _after_match_state(result, stored_category, stored_rule)
        new_category = result.category if result and result.matched else None
        new_rule = result.rule_label if result and result.matched else None
        new_phm = (result.price_history_model if result and result.matched else None) or NOT_AVAILABLE

        phm_changed: bool | None
        if stored_phm == NOT_AVAILABLE or new_phm == NOT_AVAILABLE:
            phm_changed = None
        else:
            phm_changed = stored_phm != new_phm

        new_status = _derive_new_status(stored_status, after_state)
        findings = _gate_findings(stored_status, after_state, phm_changed)

        transitions.append(ListingTransition(
            listing_id=e.get("url") or NOT_AVAILABLE,
            title=title or NOT_AVAILABLE,
            price=price,
            stored_category=stored_category or NOT_AVAILABLE,
            new_category=new_category or "KEIN_TREFFER",
            stored_rule=stored_rule or NOT_AVAILABLE,
            new_rule=new_rule or "KEIN_TREFFER",
            stored_price_history_model=stored_phm,
            new_price_history_model=new_phm,
            stored_status=stored_status,
            new_status=new_status,
            match_path_before=_match_path(stored_category, stored_rule),
            match_path_after=_match_path(new_category, new_rule) if result and result.matched else "KEIN_TREFFER",
            after_match_state=after_state,
            findings=findings,
        ))
    return transitions


def summarize(transitions: list[ListingTransition]) -> dict:
    severity_counts: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    confirmed_counts: dict[str, int] = {}
    for t in transitions:
        for f in t.findings:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1
            label_counts[f["label"]] = label_counts.get(f["label"], 0) + 1
            key = f"{f['severity']}::confirmed" if f["confirmed"] else f"{f['severity']}::kandidat_manuelle_pruefung"
            confirmed_counts[key] = confirmed_counts.get(key, 0) + 1
    return {
        "anzahl_eintraege": len(transitions),
        "severity_counts": severity_counts,
        "label_counts": label_counts,
        "confirmed_vs_kandidat": confirmed_counts,
    }


def run(baseline_path: Path, out_name: str) -> dict:
    with baseline_path.open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    rules_cfg = load_current_rules()
    transitions = build_detailed_transitions(baseline, rules_cfg)
    report = {
        "meta": {
            "baseline_id": baseline["meta"].get("baseline_id"),
            "baseline_ruleset_signature": baseline["meta"].get("ruleset_signature"),
            "current_ruleset_signature": current_ruleset_signature(rules_cfg),
            **summarize(transitions),
        },
        "transitions": [asdict(t) for t in transitions],
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / out_name
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report


if __name__ == "__main__":
    import sys
    from .common import BASELINES_DIR

    if len(sys.argv) > 1:
        baseline_path = Path(sys.argv[1])
    else:
        candidates = sorted(BASELINES_DIR.glob("baseline_2*.json"))
        baseline_path = candidates[-1]

    report = run(baseline_path, f"detailed_transitions_{baseline_path.stem}.json")
    print(json.dumps(report["meta"], indent=2, ensure_ascii=False))
