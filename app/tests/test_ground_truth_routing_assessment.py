"""Tests fuer tools/ruleset_quality/ground_truth_routing_assessment.py
(Auftrag "Saubere Trennung historical ground truth / current routing
assessment").

Deckt die reine Report-/Schema-Ebene ab (das Modul selbst enthaelt keine
eigene Matching-/Klassifikationslogik -- die wird bereits in
test_forensics_false_positives.py::TestZweiEbenenAssessment getestet):

  - jeder Fall traegt historical_ground_truth/current_routing_assessment/
    assessment als getrennte, verschachtelte Objekte
  - summary/categories bleiben rechnerisch konsistent
  - UNCLEAR-Kandidaten sind vollstaendig in "cases" enthalten, aber NICHT
    in summary.manual_review mitgezaehlt (nur FP-Ursprung, siehe
    Moduldocstring)
  - GROUND_TRUTH_CONFLICT zaehlt nie als current_fixed_fp/current_active_fp
  - docs/DASHBOARD_MATCH_FORENSICS.json (bzw. die Eingabedatei) wird nie
    veraendert

Isolationsmuster: analog zu test_forensics_false_positives.py -- tools/
liegt neben app/, daher Projekt-Root vorne in sys.path.
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import tools.ruleset_quality.forensics_false_positives as ffp  # noqa: E402
import tools.ruleset_quality.ground_truth_routing_assessment as gtra  # noqa: E402


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


def _write_forensics(tmp_path: Path, entries: list[dict]) -> Path:
    path = tmp_path / "forensics.json"
    path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return path


class TestZweiEbenenSchema:
    def test_case_enthaelt_beide_ebenen_strikt_getrennt(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="a")])
        report = gtra.build_report(input_path=path, rules_cfg={})
        case = report["cases"][0]
        assert set(case) >= {"historical_ground_truth", "current_routing_assessment", "assessment"}
        assert case["historical_ground_truth"]["verdict"] == "FALSE_POSITIVE"
        assert case["historical_ground_truth"]["category"] == "handhelds"
        assert case["current_routing_assessment"]["match_state"] == "KEIN_TREFFER"
        assert case["assessment"]["status"] == "FIXED"

    def test_historisches_label_impliziert_nicht_aktuellen_status(self, monkeypatch, tmp_path):
        # Kernanforderung: ein historisches FALSE_POSITIVE-Label darf NICHT
        # automatisch "current routing = FALSE_POSITIVE" bedeuten -- die
        # current_routing_assessment-Ebene ist unabhaengig auslesbar.
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Valve Steam Deck * Top-Deal"),
        )
        path = _write_forensics(tmp_path, [_entry(url="b")])
        report = gtra.build_report(input_path=path, rules_cfg={})
        case = report["cases"][0]
        assert case["historical_ground_truth"]["verdict"] == "FALSE_POSITIVE"
        assert case["current_routing_assessment"]["category"] == "handhelds"
        assert case["current_routing_assessment"]["match_state"] == "GLEICHE_KATEGORIE"
        # assessment.status ist ein DRITTES, eigenstaendiges Feld -- nicht
        # einfach eine Kopie des historischen Verdicts.
        assert case["assessment"]["status"] == "STILL_ACTIVE"

    def test_unclear_case_hat_case_type_unclear_candidate_und_manual_review(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="c", verdict="UNCLEAR", root_cause="sonstiges")])
        report = gtra.build_report(input_path=path, rules_cfg={})
        case = report["cases"][0]
        assert case["case_type"] == "unclear_candidate"
        assert case["historical_ground_truth"]["verdict"] == "UNCLEAR"
        assert case["assessment"]["status"] == "MANUAL_REVIEW"


class TestSummaryUndCategoriesKonsistenz:
    def test_summary_zaehlt_fp_und_unclear_getrennt(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [
            _entry(url="fixed"),
            _entry(url="unclear", verdict="UNCLEAR", root_cause="sonstiges"),
        ]
        path = _write_forensics(tmp_path, entries)
        report = gtra.build_report(input_path=path, rules_cfg={})
        assert report["summary"]["historical_fp"] == 1
        assert report["summary"]["historical_unclear"] == 1
        assert report["summary"]["current_fixed_fp"] == 1
        # UNCLEAR-Kandidaten zaehlen NICHT in summary.manual_review (nur
        # FP-Ursprungsfaelle, siehe Moduldocstring) -- sonst waere nicht
        # mehr unterscheidbar, woher ein manual_review-Fall stammt.
        assert report["summary"]["manual_review"] == 0

    def test_kategorien_rollup_summiert_exakt_zu_summary(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [
            _entry(url="a", category="handhelds"),
            _entry(url="b", category="gaming_pc"),
            _entry(url="c", category="handhelds"),
        ]
        path = _write_forensics(tmp_path, entries)
        report = gtra.build_report(input_path=path, rules_cfg={})
        total_fixed = sum(c["fixed"] for c in report["categories"].values())
        total_historical = sum(c["historical_fp"] for c in report["categories"].values())
        assert total_fixed == report["summary"]["current_fixed_fp"]
        assert total_historical == report["summary"]["historical_fp"] == 3
        assert report["categories"]["handhelds"]["historical_fp"] == 2
        assert report["categories"]["gaming_pc"]["historical_fp"] == 1

    def test_ground_truth_conflict_zaehlt_getrennt_von_fixed_und_active(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Valve Steam Deck * Top-Deal"),
        )
        monkeypatch.setitem(
            ffp._MANUAL_ASSESSMENT_OVERRIDES,
            "https://example.test/conflict",
            (ffp.ASSESSMENT_GROUND_TRUTH_CONFLICT, ffp.CONFIDENCE_HIGH, ["Testevidenz"]),
        )
        path = _write_forensics(tmp_path, [_entry(url="https://example.test/conflict")])
        report = gtra.build_report(input_path=path, rules_cfg={})
        assert report["summary"]["ground_truth_conflict"] == 1
        assert report["summary"]["current_fixed_fp"] == 0
        assert report["summary"]["current_active_fp"] == 0
        assert report["categories"]["handhelds"]["ground_truth_conflict"] == 1


class TestGroundTruthWirdNieVeraendert:
    def test_eingabedatei_bleibt_bytegleich(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="a"), _entry(url="b", verdict="UNCLEAR", root_cause="x")])
        before = path.read_text(encoding="utf-8")
        gtra.build_report(input_path=path, rules_cfg={})
        gtra.render_markdown(gtra.build_report(input_path=path, rules_cfg={}))
        after = path.read_text(encoding="utf-8")
        assert before == after

    def test_write_outputs_schreibt_nur_unter_generated_nie_docs(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="a")])
        report = gtra.build_report(input_path=path, rules_cfg={})
        written = gtra.write_outputs(report)
        assert "generated" in str(written["json_report"])
        assert "generated" in str(written["md_report"])
        assert "docs" not in str(written["json_report"])


class TestFixQueueKopplung:
    """Auftrag "false_positive_fix_queue.json an Ground-Truth-Routing-
    Assessment koppeln": build_report() liefert Fix-Queue + Konsistenz-
    pruefung, abgeleitet aus denselben Cases wie die Assessment-Ebene."""

    def test_fix_queue_und_consistency_sind_im_report_enthalten(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="a")])
        report = gtra.build_report(input_path=path, rules_cfg={})
        assert "fix_queue" in report
        assert "queue_consistency" in report
        assert "queue_category_counts" in report
        assert report["queue_consistency"]["consistency_ok"] is True

    def test_konsistenter_report_hat_keine_status_mismatches(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            ffp, "evaluate",
            lambda title, price, cfg: _FakeResult(matched=True, category="handhelds", rule_label="Valve Steam Deck * Top-Deal"),
        )
        entries = [
            _entry(url="a", category="handhelds"),
            _entry(url="b", category="gaming_pc"),
        ]
        path = _write_forensics(tmp_path, entries)
        report = gtra.build_report(input_path=path, rules_cfg={})
        assert report["queue_consistency"]["status_mismatches"] == []
        assert report["queue_consistency"]["consistency_ok"] is True

    def test_queue_category_counts_summieren_zu_historical_fp(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [_entry(url=f"u{i}") for i in range(4)]
        path = _write_forensics(tmp_path, entries)
        report = gtra.build_report(input_path=path, rules_cfg={})
        assert sum(report["queue_category_counts"].values()) == report["summary"]["historical_fp"] == 4


class TestDeterminismus:
    def test_wiederholter_lauf_liefert_identische_cases_reihenfolge(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [_entry(url=f"url-{i}", title=f"Titel {i}", category="handhelds") for i in range(5)]
        path = _write_forensics(tmp_path, entries)
        report1 = gtra.build_report(input_path=path, rules_cfg={})
        report2 = gtra.build_report(input_path=path, rules_cfg={})
        titles1 = [c["title"] for c in report1["cases"]]
        titles2 = [c["title"] for c in report2["cases"]]
        assert titles1 == titles2 == sorted(titles1)
