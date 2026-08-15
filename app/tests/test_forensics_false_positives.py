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
