"""Tests fuer tools/ruleset_quality/forensics_false_positives.py (Auftrag
"Category False-Positive Forensics + gezielte Fix-Queue").

Deckt die epistemisch heiklen Stellen ab:

  - FALSE_POSITIVE und UNCLEAR duerfen NIE vermischt werden (Auftrag
    "KRITISCHE METHODISCHE REGEL") -- UNCLEAR bleibt immer FP-Kandidat,
    nie ein bestaetigter FP.
  - Root-Cause-Klassifikation erfindet nichts: Werte ohne Uebersetzungs-
    eintrag werden als "ambiguous"/"manual_review" ausgewiesen, nicht
    geraten.
  - FALSE_POSITIVE -> ANDERE_KATEGORIE gilt NICHT automatisch als Fix
    (already_resolved bleibt False).
  - fehlende Forensics-Felder fuehren zu NOT_AVAILABLE statt Exception.

Isolationsmuster: analog zu test_ruleset_quality_tooling.py -- tools/ liegt
neben app/, daher Projekt-Root vorne in sys.path.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import tools.ruleset_quality.forensics_false_positives as ffp  # noqa: E402
from tools.ruleset_quality.forensics_false_positives import (  # noqa: E402
    ROUTING_STATUS_CATEGORY_CHANGED,
    ROUTING_STATUS_NO_MATCH,
    ROUTING_STATUS_RULE_CHANGED,
    ROUTING_STATUS_SAME_CATEGORY,
    build_candidate,
    build_case,
    build_fix_queue,
    build_report,
    extract_cases,
    group_by_category,
)


@dataclass
class _FakeResult:
    matched: bool
    category: str | None = None
    rule_label: str | None = None
    price_history_model: str | None = None


def _entry(**overrides) -> dict:
    base = {
        "url": "https://example.test/1",
        "title": "Steam Deck Huelle Schutztasche",
        "price": 20.0,
        "category": "handhelds",
        "stored_rule_label": "Valve Steam Deck * Top-Deal",
        "verdict": "FALSE_POSITIVE",
        "root_cause": "fehlendes Exclude",
        "reason": "Nur 1 unabhaengiges Positiv-Kriterium, kein Exclude-Schutz.",
    }
    base.update(overrides)
    return base


class TestExtractCasesTrenntFpUndKandidaten:
    """1. FP wird korrekt extrahiert / 11. mehrere Kategorien korrekt gruppiert."""

    def test_nur_false_positive_und_unclear_werden_beruecksichtigt(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [
            _entry(url="fp1", verdict="FALSE_POSITIVE"),
            _entry(url="tp1", verdict="TRUE_POSITIVE"),
            _entry(url="uc1", verdict="UNCLEAR", root_cause="sonstiges"),
        ]
        confirmed, candidates = extract_cases(entries, rules_cfg={})
        assert [c.listing_id for c in confirmed] == ["fp1"]
        assert [c.listing_id for c in candidates] == ["uc1"]

    def test_unclear_landet_niemals_bei_confirmed(self, monkeypatch):
        # Zentrale Anforderung: kein FP wird aus einer blossen Heuristik
        # "bestaetigt".
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [_entry(url="uc1", verdict="UNCLEAR", root_cause="sonstiges")]
        confirmed, candidates = extract_cases(entries, rules_cfg={})
        assert confirmed == []
        assert len(candidates) == 1

    def test_mehrere_kategorien_werden_korrekt_gruppiert(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [
            _entry(url="a", category="handhelds"),
            _entry(url="b", category="gaming_pc"),
            _entry(url="c", category="handhelds"),
        ]
        confirmed, _ = extract_cases(entries, rules_cfg={})
        grouped = group_by_category(confirmed)
        assert set(grouped) == {"handhelds", "gaming_pc"}
        assert len(grouped["handhelds"]) == 2
        assert len(grouped["gaming_pc"]) == 1

    def test_category_filter_wirkt(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [_entry(url="a", category="handhelds"), _entry(url="b", category="gaming_pc")]
        confirmed, _ = extract_cases(entries, rules_cfg={}, category="handhelds")
        assert [c.listing_id for c in confirmed] == ["a"]


class TestBuildCaseKategorieUndRegel:
    """2/3/4. Kategorie/current_category/current_rule werden korrekt uebernommen."""

    def test_stored_category_und_regel_werden_uebernommen(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={})
        assert case.stored_category == "handhelds"
        assert case.stored_rule == "Steam Deck"

    def test_current_category_und_regel_aus_evaluate(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="notebook_resell", rule_label="Notebook X"),
        )
        case = build_case(_entry(category="office_pc", stored_rule_label="Office-PC"), rules_cfg={})
        assert case.current_category == "notebook_resell"
        assert case.current_rule == "Notebook X"


class TestRoutingStatusABCD:
    """5/6/7. KEIN_TREFFER / KATEGORIE_GEAENDERT / weiterhin aktiv korrekt erkannt."""

    def test_c_kein_treffer_mehr(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(), rules_cfg={})
        assert case.routing_status == ROUTING_STATUS_NO_MATCH
        assert case.already_resolved is True

    def test_b_andere_kategorie(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="controller", rule_label="X"),
        )
        case = build_case(_entry(category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={})
        assert case.routing_status == ROUTING_STATUS_CATEGORY_CHANGED
        assert case.current_category == "controller"

    def test_a_weiterhin_gleiche_kategorie_und_regel_aktiv(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        case = build_case(_entry(category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={})
        assert case.routing_status == ROUTING_STATUS_SAME_CATEGORY
        assert case.already_resolved is False

    def test_d_gleiche_kategorie_aber_andere_regel(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Andere Regel"),
        )
        case = build_case(_entry(category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={})
        assert case.routing_status == ROUTING_STATUS_RULE_CHANGED
        assert case.already_resolved is False


class TestKategorieWechselIstKeinAutomatischerFix:
    """8. FP -> andere Kategorie wird NICHT als Fix gewertet."""

    def test_andere_kategorie_bleibt_ungeloest(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="notebook_resell", rule_label="Y"),
        )
        case = build_case(_entry(category="office_pc"), rules_cfg={})
        assert case.already_resolved is False
        assert ROUTING_STATUS_CATEGORY_CHANGED not in ffp.RESOLVED_ROUTING_STATUSES

    def test_fix_queue_zaehlt_kategoriewechsel_als_weiterhin_aktiv(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="notebook_resell", rule_label="Y"),
        )
        case = build_case(_entry(category="office_pc", stored_rule_label="R"), rules_cfg={})
        queue = build_fix_queue([case])
        assert queue[0].still_active_count == 1


class TestRootCauseErfindetNichts:
    """9. Root-Cause-Klassifikation erfindet keine nicht belegten Informationen."""

    def test_bekannter_root_cause_wird_uebersetzt_mit_confirmed(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(root_cause="Ersatzteil statt Hauptprodukt"), rules_cfg={})
        assert case.root_cause == ffp.ROOT_CAUSE_REPLACEMENT_PART
        assert case.root_cause_confidence == ffp.CONFIDENCE_CONFIRMED

    def test_unbekannter_root_cause_wird_nicht_geraten(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(root_cause="sonstiges"), rules_cfg={})
        assert case.root_cause == ffp.ROOT_CAUSE_AMBIGUOUS
        assert case.root_cause_confidence == ffp.CONFIDENCE_MANUAL_REVIEW

    def test_fehlender_root_cause_wird_nicht_geraten(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(root_cause=None), rules_cfg={})
        assert case.root_cause == ffp.ROOT_CAUSE_AMBIGUOUS
        assert case.root_cause_confidence == ffp.CONFIDENCE_MANUAL_REVIEW

    def test_evidence_enthaelt_original_beleg_nicht_nur_behauptung(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(root_cause="fehlendes Exclude", reason="Beispielbegruendung"), rules_cfg={})
        assert any("fehlendes Exclude" in e for e in case.root_cause_evidence)
        assert any("Beispielbegruendung" in e for e in case.root_cause_evidence)


class TestFehlendeFelderWerdenNichtErfunden:
    """10. fehlende Forensics-Felder fuehren zu NOT_AVAILABLE/null statt Fehler."""

    def test_fehlende_url_wird_not_available(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entry = _entry()
        del entry["url"]
        case = build_case(entry, rules_cfg={})
        assert case.listing_id == "NOT_AVAILABLE"

    def test_fehlende_stored_rule_label_wird_not_available(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entry = _entry()
        del entry["stored_rule_label"]
        case = build_case(entry, rules_cfg={})
        assert case.stored_rule == "NOT_AVAILABLE"

    def test_fehlende_category_wird_not_available_und_wirft_nicht(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entry = _entry()
        del entry["category"]
        case = build_case(entry, rules_cfg={})
        assert case.stored_category == "NOT_AVAILABLE"

    def test_fehlende_felder_bei_candidate_werfen_nicht(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entry = {"verdict": "UNCLEAR", "title": "X"}
        candidate = build_candidate(entry, rules_cfg={})
        assert candidate.listing_id == "NOT_AVAILABLE"
        assert candidate.stored_category == "NOT_AVAILABLE"


class TestBuildReportKonsistenzUndFilter:
    """12. Zusammenspiel/Report-Ebene: Filter, Konsistenzpruefung, Fix-Queue bleibt kanonisch."""

    def test_only_fp_blendet_kandidaten_aus(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        data_path = tmp_path / "forensics.json"
        import json

        data_path.write_text(
            json.dumps({"entries": [_entry(url="fp1"), _entry(url="uc1", verdict="UNCLEAR", root_cause="sonstiges")]}),
            encoding="utf-8",
        )
        report = build_report(input_path=data_path, only_fp=True, rules_cfg={})
        assert report["candidates_by_category"] == {}
        assert report["meta"]["confirmed_fp_count_total"] == 1

    def test_fix_queue_bleibt_kanonisch_trotz_category_filter(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        import json

        data_path = tmp_path / "forensics.json"
        data_path.write_text(
            json.dumps(
                {
                    "entries": [
                        _entry(url="a", category="handhelds"),
                        _entry(url="b", category="gaming_pc"),
                    ]
                }
            ),
            encoding="utf-8",
        )
        report = build_report(input_path=data_path, category="handhelds", rules_cfg={})
        assert {e.category for e in report["fix_queue_canonical"]} == {"handhelds", "gaming_pc"}
        assert {e.category for e in report["fix_queue_view"]} == {"handhelds"}

    def test_konsistenzpruefung_meldet_abweichung_statt_zu_schoenrechnen(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        import json

        data_path = tmp_path / "forensics.json"
        data_path.write_text(json.dumps({"entries": [_entry(url="fp1")]}), encoding="utf-8")
        report = build_report(input_path=data_path, rules_cfg={})
        notes = report["meta"]["consistency_notes"]
        assert any("FALSE_POSITIVE" in n for n in notes)

    def test_fehlende_input_datei_gibt_leeren_report_statt_fehler(self, tmp_path):
        report = build_report(input_path=tmp_path / "nicht_vorhanden.json", rules_cfg={})
        assert report["meta"]["total_entries_in_source"] == 0
        assert report["confirmed_by_category"] == {}


class TestZweiEbenenAssessment:
    """Auftrag "Saubere Trennung historical ground truth / current routing
    assessment": historical_ground_truth und current_routing_assessment
    werden getrennt gespeichert, assessment.status wird daraus abgeleitet
    -- AUSSER ein dokumentierter manueller Override greift (nie eine
    erfundene Heuristik). Deckt die 6 im Auftrag geforderten Faelle ab."""

    def test_1_historische_fp_kein_treffer_ist_fixed(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(url="szenario-1"), rules_cfg={})
        assert case.assessment_status == ffp.ASSESSMENT_FIXED
        assert case.assessment_confidence == ffp.CONFIDENCE_CONFIRMED

    def test_2_historische_fp_gleiche_kategorie_ist_still_active(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        case = build_case(
            _entry(url="szenario-2", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        assert case.assessment_status == ffp.ASSESSMENT_STILL_ACTIVE

    def test_3_historische_fp_andere_kategorie_ist_category_changed(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="notebook_resell", rule_label="Y"),
        )
        case = build_case(_entry(url="szenario-3", category="office_pc"), rules_cfg={})
        assert case.assessment_status == ffp.ASSESSMENT_CATEGORY_CHANGED
        # explizit NICHT als FIXED/STILL_ACTIVE fehlinterpretiert:
        assert case.assessment_status not in (ffp.ASSESSMENT_FIXED, ffp.ASSESSMENT_STILL_ACTIVE)

    def test_4_historische_unclear_ist_immer_manual_review(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        candidate = build_candidate(
            _entry(url="szenario-4", verdict="UNCLEAR", root_cause="sonstiges"), rules_cfg={}
        )
        assert candidate.assessment_status == ffp.ASSESSMENT_MANUAL_REVIEW
        assert candidate.assessment_confidence == ffp.CONFIDENCE_MANUAL_REVIEW

    def test_5_dokumentierter_override_ergibt_ground_truth_conflict(self, monkeypatch):
        # Testet den Override-MECHANISMUS generisch (nicht die konkreten
        # Produktions-URLs aus _MANUAL_ASSESSMENT_OVERRIDES) -- die
        # Uebersteuerung darf NUR ueber einen expliziten, dokumentierten
        # Eintrag erfolgen, nie automatisch aus evaluate() abgeleitet werden.
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        monkeypatch.setitem(
            ffp._MANUAL_ASSESSMENT_OVERRIDES,
            "szenario-5-url",
            (ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT, ffp.CONFIDENCE_HIGH, ["kuratierte Testevidenz"]),
        )
        case = build_case(
            _entry(url="szenario-5-url", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        assert case.assessment_status == ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT
        assert case.assessment_confidence == ffp.CONFIDENCE_HIGH
        assert case.assessment_evidence == ["kuratierte Testevidenz"]

    def test_5b_ohne_override_bleibt_gleiche_kategorie_still_active(self, monkeypatch):
        # Gegenprobe zu Fall 5: OHNE registrierten Override darf GLEICHE_
        # KATEGORIE NIEMALS automatisch zu GROUND_TRUTH_CONFLICT werden.
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        case = build_case(
            _entry(url="szenario-5b-kein-override", category="handhelds", stored_rule_label="Steam Deck"),
            rules_cfg={},
        )
        assert case.assessment_status == ffp.ASSESSMENT_STILL_ACTIVE
        assert case.assessment_status != ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT

    def test_6_ground_truth_datei_wird_niemals_veraendert(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        import json

        data_path = tmp_path / "forensics.json"
        original_content = json.dumps({"entries": [_entry(url="szenario-6")]})
        data_path.write_text(original_content, encoding="utf-8")

        build_report(input_path=data_path, rules_cfg={})
        build_case(_entry(url="szenario-6"), rules_cfg={})

        assert data_path.read_text(encoding="utf-8") == original_content

    def test_andere_regel_gleiche_kategorie_ist_manual_review(self, monkeypatch):
        # ANDERE_REGEL (Auftrag "FALSE_POSITIVE -> OTHER_RULE = separat
        # pruefen") wird nie automatisch zu TP/FP entschieden.
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Andere Regel"),
        )
        case = build_case(
            _entry(url="szenario-regel", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        assert case.assessment_status == ffp.ASSESSMENT_MANUAL_REVIEW

    def test_queue_category_ground_truth_conflict_bekommt_keine_prioritaet(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        monkeypatch.setitem(
            ffp._MANUAL_ASSESSMENT_OVERRIDES,
            "szenario-queue-url",
            (ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT, ffp.CONFIDENCE_HIGH, ["Testevidenz"]),
        )
        case = build_case(
            _entry(url="szenario-queue-url", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        queue = build_fix_queue([case])
        assert queue[0].queue_category == ffp.QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT
        assert queue[0].priority == "N/A"

    def test_queue_category_still_active_wird_priorisiert(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        case = build_case(
            _entry(url="szenario-active-queue", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        queue = build_fix_queue([case])
        assert queue[0].queue_category == ffp.QUEUE_CATEGORY_ACTIVE_ROUTING_FP
        assert queue[0].priority in ("P0", "P1", "P2", "P3")

    def test_queue_category_fixed_wird_als_already_fixed_gefuehrt(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(url="szenario-fixed-queue"), rules_cfg={})
        queue = build_fix_queue([case])
        assert queue[0].queue_category == ffp.QUEUE_CATEGORY_ALREADY_FIXED
        assert queue[0].priority == "N/A"


class TestQueueCategoryMapping:
    """Auftrag "false_positive_fix_queue.json an Ground-Truth-Routing-
    Assessment koppeln": strikte 1:1-Ableitung assessment.status ->
    queue_category, NIEMALS ueber still_active_count. Deckt alle 10 im
    Auftrag geforderten Mapping-Faelle ab (1-2/4 bereits oben abgedeckt,
    hier die restlichen + die expliziten Negativ-Pruefungen)."""

    def test_3_category_changed_ergibt_queue_category_category_changed(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="notebook_resell", rule_label="Y"),
        )
        case = build_case(_entry(url="mapping-3", category="office_pc"), rules_cfg={})
        assert case.assessment_status == ffp.ASSESSMENT_CATEGORY_CHANGED
        queue = build_fix_queue([case])
        assert queue[0].queue_category == ffp.QUEUE_CATEGORY_CATEGORY_CHANGED
        assert queue[0].priority == "N/A"

    def test_5_manual_review_ergibt_queue_category_manual_review(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Andere Regel"),
        )
        case = build_case(
            _entry(url="mapping-5", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        assert case.assessment_status == ffp.ASSESSMENT_MANUAL_REVIEW
        queue = build_fix_queue([case])
        assert queue[0].queue_category == ffp.QUEUE_CATEGORY_MANUAL_REVIEW

    def test_6_manual_review_ist_niemals_already_fixed(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Andere Regel"),
        )
        case = build_case(
            _entry(url="mapping-6", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        queue = build_fix_queue([case])
        assert queue[0].queue_category != ffp.QUEUE_CATEGORY_ALREADY_FIXED

    def test_7_ground_truth_conflict_ist_niemals_already_fixed(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        monkeypatch.setitem(
            ffp._MANUAL_ASSESSMENT_OVERRIDES,
            "mapping-7",
            (ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT, ffp.CONFIDENCE_HIGH, ["Testevidenz"]),
        )
        case = build_case(
            _entry(url="mapping-7", category="handhelds", stored_rule_label="Steam Deck"), rules_cfg={}
        )
        queue = build_fix_queue([case])
        assert queue[0].queue_category != ffp.QUEUE_CATEGORY_ALREADY_FIXED
        assert queue[0].queue_category == ffp.QUEUE_CATEGORY_GROUND_TRUTH_CONFLICT

    def test_8_category_changed_ist_weder_fixed_noch_already_fixed(self, monkeypatch):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="notebook_resell", rule_label="Y"),
        )
        case = build_case(_entry(url="mapping-8", category="office_pc"), rules_cfg={})
        queue = build_fix_queue([case])
        assert case.assessment_status != ffp.ASSESSMENT_FIXED
        assert queue[0].queue_category != ffp.QUEUE_CATEGORY_ALREADY_FIXED

    def test_9_still_active_count_null_erzeugt_nicht_automatisch_already_fixed(self, monkeypatch):
        # DAS konkrete Regressionsbeispiel aus dem Auftrag ("Ein Fall kann
        # aktuell KEIN_TREFFER sein, aber trotzdem MANUAL_REVIEW
        # benoetigen"): routing_status=KEIN_TREFFER wuerde OHNE Override
        # zu FIXED/still_active_count=0 fuehren -- der dokumentierte
        # Override zeigt, dass MANUAL_REVIEW trotzdem Vorrang hat und
        # sich NICHT von still_active_count=0 in ALREADY_FIXED verwandelt.
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        monkeypatch.setitem(
            ffp._MANUAL_ASSESSMENT_OVERRIDES,
            "mapping-9",
            (ffp.ASSESSMENT_MANUAL_REVIEW, ffp.CONFIDENCE_LOW, ["Trotz KEIN_TREFFER weiterhin unsicher."]),
        )
        case = build_case(_entry(url="mapping-9"), rules_cfg={})
        assert case.routing_status == ffp.ROUTING_STATUS_NO_MATCH
        assert case.assessment_status == ffp.ASSESSMENT_MANUAL_REVIEW

        queue = build_fix_queue([case])
        assert queue[0].still_active_count == 1  # Metrik-Spalte, NICHT die Entscheidung
        assert queue[0].queue_category == ffp.QUEUE_CATEGORY_MANUAL_REVIEW
        assert queue[0].queue_category != ffp.QUEUE_CATEGORY_ALREADY_FIXED

    def test_10_ground_truth_bleibt_unveraendert_auch_bei_conflict(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Steam Deck"),
        )
        monkeypatch.setitem(
            ffp._MANUAL_ASSESSMENT_OVERRIDES,
            "mapping-10",
            (ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT, ffp.CONFIDENCE_HIGH, ["Testevidenz"]),
        )
        import json

        data_path = tmp_path / "forensics.json"
        original_content = json.dumps({"entries": [_entry(url="mapping-10", category="handhelds")]})
        data_path.write_text(original_content, encoding="utf-8")

        build_report(input_path=data_path, rules_cfg={})

        assert data_path.read_text(encoding="utf-8") == original_content


class TestValidateQueueConsistency:
    """Auftrag "NEUER VALIDIERUNGSSCHRITT": prueft assessment.status <->
    queue_category ueber stabile Case-IDs (listing_id), nicht ueber
    Titel-String oder Kategorie."""

    def test_konsistenter_fall_ist_ok(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(url="consistency-ok"), rules_cfg={})
        queue = build_fix_queue([case])
        result = ffp.validate_queue_consistency([case], queue)
        assert result["consistency_ok"] is True
        assert result["total_cases"] == 1
        assert result["matched_cases"] == 1
        assert result["missing_in_queue"] == []
        assert result["missing_in_assessment"] == []
        assert result["duplicate_case_ids"] == []
        assert result["status_mismatches"] == []

    def test_fehlender_fall_in_queue_wird_gemeldet(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(url="consistency-missing"), rules_cfg={})
        result = ffp.validate_queue_consistency([case], [])  # leere Queue
        assert result["consistency_ok"] is False
        assert result["missing_in_queue"] == ["consistency-missing"]

    def test_status_mismatch_manual_review_als_already_fixed_ist_error(self):
        # Auftrags-Beispiel: assessment=MANUAL_REVIEW, queue=ALREADY_FIXED -> ERROR
        case = ffp.FalsePositiveCase(
            listing_id="mismatch-1", title="X", price=1.0, stored_category="handhelds",
            ground_truth_verdict="FALSE_POSITIVE", stored_rule="R", current_category="KEIN_TREFFER",
            current_rule="KEIN_TREFFER", match_path_before="x", match_path_after="x",
            match_state="KEIN_TREFFER", routing_status=ffp.ROUTING_STATUS_NO_MATCH,
            already_resolved=True, root_cause="ambiguous", root_cause_confidence="manual_review",
            root_cause_evidence=[], recommended_fix_type="manual_review", regression_risk="MEDIUM",
            assessment_status=ffp.ASSESSMENT_MANUAL_REVIEW, assessment_confidence="low", assessment_evidence=[],
        )
        broken_entry = ffp.FixQueueEntry(
            priority="N/A", category="handhelds", affected_count=1,
            queue_category=ffp.QUEUE_CATEGORY_ALREADY_FIXED,  # bewusst falsch
            case_listing_ids=["mismatch-1"],
        )
        result = ffp.validate_queue_consistency([case], [broken_entry])
        assert result["consistency_ok"] is False
        assert len(result["status_mismatches"]) == 1
        assert result["status_mismatches"][0]["assessment_status"] == ffp.ASSESSMENT_MANUAL_REVIEW
        assert result["status_mismatches"][0]["actual_queue_category"] == ffp.QUEUE_CATEGORY_ALREADY_FIXED

    def test_status_mismatch_ground_truth_conflict_als_already_fixed_ist_error(self):
        # Auftrags-Beispiel: assessment=GROUND_TRUTH_CONFLICT, queue=ALREADY_FIXED -> ERROR
        case = ffp.FalsePositiveCase(
            listing_id="mismatch-2", title="X", price=1.0, stored_category="handhelds",
            ground_truth_verdict="FALSE_POSITIVE", stored_rule="R", current_category="handhelds",
            current_rule="R", match_path_before="x", match_path_after="x",
            match_state="GLEICHE_KATEGORIE", routing_status=ffp.ROUTING_STATUS_SAME_CATEGORY,
            already_resolved=False, root_cause="weak_signal", root_cause_confidence="confirmed",
            root_cause_evidence=[], recommended_fix_type="strengthen_positive_signal", regression_risk="HIGH",
            assessment_status=ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT, assessment_confidence="high", assessment_evidence=[],
        )
        broken_entry = ffp.FixQueueEntry(
            priority="N/A", category="handhelds", affected_count=1,
            queue_category=ffp.QUEUE_CATEGORY_ALREADY_FIXED,  # bewusst falsch
            case_listing_ids=["mismatch-2"],
        )
        result = ffp.validate_queue_consistency([case], [broken_entry])
        assert result["consistency_ok"] is False
        assert len(result["status_mismatches"]) == 1

    def test_fixed_als_already_fixed_ist_ok(self, monkeypatch):
        # Auftrags-Beispiel: assessment=FIXED, queue=ALREADY_FIXED -> OK
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(url="mismatch-3"), rules_cfg={})
        assert case.assessment_status == ffp.ASSESSMENT_FIXED
        queue = build_fix_queue([case])
        result = ffp.validate_queue_consistency([case], queue)
        assert result["consistency_ok"] is True

    def test_duplicate_case_id_wird_gemeldet(self, monkeypatch):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        case = build_case(_entry(url="dup-1"), rules_cfg={})
        entry_a = ffp.FixQueueEntry(
            priority="N/A", category="handhelds", affected_count=1,
            queue_category=ffp.QUEUE_CATEGORY_ALREADY_FIXED, case_listing_ids=["dup-1"],
        )
        entry_b = ffp.FixQueueEntry(
            priority="N/A", category="handhelds", affected_count=1,
            queue_category=ffp.QUEUE_CATEGORY_MANUAL_REVIEW, case_listing_ids=["dup-1"],
        )
        result = ffp.validate_queue_consistency([case], [entry_a, entry_b])
        assert result["consistency_ok"] is False
        assert result["duplicate_case_ids"] == ["dup-1"]
