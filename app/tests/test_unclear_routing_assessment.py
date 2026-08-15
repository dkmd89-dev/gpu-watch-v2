"""Tests fuer tools/ruleset_quality/unclear_routing_assessment.py
(Auftrag "35 UNCLEAR-Faelle systematisch forensisch klassifizieren").

Deckt zwei Ebenen ab:

  - Schema-/Konsistenzpruefungen mit SYNTHETISCHEN Faellen (mocked
    evaluate(), mocked Forensik-Eintraege) -- unabhaengig vom echten
    Produktivdatenbestand.
  - Eine schmale Menge an Regressionstests gegen den ECHTEN Datenbestand
    (docs/DASHBOARD_MATCH_FORENSICS.json + aktuelle app/rules/*.yaml):
    exakt 35 UNCLEAR-Faelle, Konsistenz OK, und der dokumentierte DS-Lite-
    Sonderfall bleibt MANUAL_REVIEW/LOW (siehe Moduldocstring).

Isolationsmuster: analog zu test_ground_truth_routing_assessment.py --
tools/ liegt neben app/, daher Projekt-Root vorne in sys.path.
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import tools.ruleset_quality.forensics_false_positives as ffp  # noqa: E402
import tools.ruleset_quality.unclear_routing_assessment as ura  # noqa: E402
from tools.ruleset_quality.common import load_current_rules  # noqa: E402
from tools.ruleset_quality.label_store import FORENSICS_SOURCE  # noqa: E402


@dataclass
class _FakeResult:
    matched: bool
    category: str | None = None
    rule_label: str | None = None
    price_history_model: str | None = None


def _entry(**overrides) -> dict:
    base = {
        "url": "https://example.test/unclear-1",
        "title": "Nintendo Switch Irgendwas mit OVP",
        "price": 50.0,
        "category": "konsolen_bundles",
        "stored_rule_label": "Nintendo Switch (V1/V2/OLED) * Top-Deal",
        "verdict": "UNCLEAR",
        "root_cause": "sonstiges",
        "reason": "Ein require_all_of-Kriterium wurde nur ueber ein generisches Signal erfuellt.",
    }
    base.update(overrides)
    return base


def _write_forensics(tmp_path: Path, entries: list[dict]) -> Path:
    path = tmp_path / "forensics.json"
    path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return path


class TestSchema:
    def test_case_hat_alle_geforderten_felder(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry()])
        report = ura.build_report(input_path=path, rules_cfg={})
        case = report["cases"][0]
        required = {
            "case_id", "title", "historical_ground_truth", "current_routing",
            "assessment", "confidence", "evidence", "match_path", "recommended_action",
        }
        assert required <= set(case)
        assert case["historical_ground_truth"]["verdict"] == "UNCLEAR"
        assert case["assessment"]["status"] in {
            ura.STATUS_LIKELY_TRUE_POSITIVE,
            ura.STATUS_LIKELY_FALSE_POSITIVE,
            ura.STATUS_GROUND_TRUTH_CONFLICT,
            ura.STATUS_MANUAL_REVIEW,
        }
        assert case["confidence"] in {ura.CONFIDENCE_HIGH, ura.CONFIDENCE_MEDIUM, ura.CONFIDENCE_LOW}

    def test_unbekannter_fall_faellt_sicher_auf_manual_review_low_zurueck(self, monkeypatch, tmp_path):
        # Kein kuratierter Eintrag in _UNCLEAR_ASSESSMENTS fuer diese Test-URL --
        # Sicherheitsnetz greift, kein Raten (Auftrag "Bei LOW: bevorzugt MANUAL_REVIEW").
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="https://example.test/never-curated")])
        report = ura.build_report(input_path=path, rules_cfg={})
        case = report["cases"][0]
        assert case["assessment"]["status"] == ura.STATUS_MANUAL_REVIEW
        assert case["confidence"] == ura.CONFIDENCE_LOW

    def test_nur_unclear_faelle_werden_beruecksichtigt_keine_tp_fp(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [
            _entry(url="u1", verdict="UNCLEAR"),
            _entry(url="tp1", verdict="TRUE_POSITIVE"),
            _entry(url="fp1", verdict="FALSE_POSITIVE"),
        ]
        path = _write_forensics(tmp_path, entries)
        report = ura.build_report(input_path=path, rules_cfg={})
        assert report["summary"]["total_unclear"] == 1
        assert all(c["historical_ground_truth"]["verdict"] == "UNCLEAR" for c in report["cases"])


class TestRecommendedActionMapping:
    def test_feste_1_zu_1_zuordnung_gemaess_auftrag(self):
        assert ura._STATUS_TO_ACTION[ura.STATUS_LIKELY_TRUE_POSITIVE] == "regression_test"
        assert ura._STATUS_TO_ACTION[ura.STATUS_LIKELY_FALSE_POSITIVE] == "ruleset_review"
        assert ura._STATUS_TO_ACTION[ura.STATUS_GROUND_TRUTH_CONFLICT] == "ground_truth_review"
        assert ura._STATUS_TO_ACTION[ura.STATUS_MANUAL_REVIEW] == "manual_review"

    def test_alle_kuratierten_faelle_haben_konsistente_recommended_action(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        # echten Datenbestand nutzen, um alle 35 kuratierten Eintraege durchzupruefen
        rules_cfg = load_current_rules()
        report = ura.build_report(input_path=FORENSICS_SOURCE, rules_cfg=rules_cfg)
        for case in report["cases"]:
            assert case["recommended_action"] == ura._STATUS_TO_ACTION[case["assessment"]["status"]]


class TestValidateConsistency:
    def test_konsistenter_datensatz_hat_keine_fehler(self):
        candidates = [
            ffp.FpCandidateCase(
                listing_id="a", title="A", price=1.0, stored_category="x",
                ground_truth_verdict="UNCLEAR", stored_rule="r", current_category="x",
                current_rule="r", match_state="GLEICHE_KATEGORIE", note="",
            )
        ]
        cases = [
            {"case_id": "a", "assessment": {"status": ura.STATUS_MANUAL_REVIEW}},
        ]
        result = ura.validate_consistency(candidates, cases)
        assert result["missing_cases"] == []
        assert result["duplicate_cases"] == []
        # total_cases weicht vom bekannten Referenzstand (35) ab -> deshalb hier
        # bewusst NICHT consistency_ok, sondern nur die einzelnen Zaehler geprueft.
        assert result["matched_cases"] == 1
        assert result["classification_sum"] == 1

    def test_missing_case_wird_erkannt(self):
        candidates = [
            ffp.FpCandidateCase(
                listing_id="a", title="A", price=1.0, stored_category="x",
                ground_truth_verdict="UNCLEAR", stored_rule="r", current_category="x",
                current_rule="r", match_state="GLEICHE_KATEGORIE", note="",
            )
        ]
        cases: list[dict] = []  # "a" fehlt komplett in den gebauten Cases
        result = ura.validate_consistency(candidates, cases)
        assert result["missing_cases"] == ["a"]
        assert result["consistency_ok"] is False

    def test_duplicate_case_wird_erkannt(self):
        candidates = [
            ffp.FpCandidateCase(
                listing_id="a", title="A", price=1.0, stored_category="x",
                ground_truth_verdict="UNCLEAR", stored_rule="r", current_category="x",
                current_rule="r", match_state="GLEICHE_KATEGORIE", note="",
            )
        ]
        cases = [
            {"case_id": "a", "assessment": {"status": ura.STATUS_MANUAL_REVIEW}},
            {"case_id": "a", "assessment": {"status": ura.STATUS_MANUAL_REVIEW}},
        ]
        result = ura.validate_consistency(candidates, cases)
        assert result["duplicate_cases"] == ["a"]
        assert result["consistency_ok"] is False

    def test_referenzstand_abweichung_wird_erkannt(self):
        # 34 statt der bekannten 35 -- reference_notes greift, auch wenn sonst
        # alles konsistent waere.
        candidates = [
            ffp.FpCandidateCase(
                listing_id=f"u{i}", title=f"T{i}", price=1.0, stored_category="x",
                ground_truth_verdict="UNCLEAR", stored_rule="r", current_category="x",
                current_rule="r", match_state="GLEICHE_KATEGORIE", note="",
            )
            for i in range(34)
        ]
        cases = [{"case_id": f"u{i}", "assessment": {"status": ura.STATUS_MANUAL_REVIEW}} for i in range(34)]
        result = ura.validate_consistency(candidates, cases)
        assert result["reference_notes"] != []
        assert result["consistency_ok"] is False


class TestGroundTruthWirdNieVeraendert:
    def test_eingabedatei_bleibt_bytegleich(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="a"), _entry(url="b")])
        before = path.read_text(encoding="utf-8")
        report = ura.build_report(input_path=path, rules_cfg={})
        ura.render_markdown(report)
        after = path.read_text(encoding="utf-8")
        assert before == after

    def test_write_outputs_schreibt_nur_unter_generated_nie_docs(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        path = _write_forensics(tmp_path, [_entry(url="a")])
        report = ura.build_report(input_path=path, rules_cfg={})
        written = ura.write_outputs(report)
        assert "generated" in str(written["json_report"])
        assert "generated" in str(written["md_report"])
        assert "docs" not in str(written["json_report"])


class TestDeterminismus:
    def test_wiederholter_lauf_liefert_identische_reihenfolge(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ffp, "evaluate", lambda title, price, cfg: _FakeResult(matched=False))
        entries = [_entry(url=f"u{i}", title=f"Titel {i}") for i in range(5)]
        path = _write_forensics(tmp_path, entries)
        report1 = ura.build_report(input_path=path, rules_cfg={})
        report2 = ura.build_report(input_path=path, rules_cfg={})
        titles1 = [c["title"] for c in report1["cases"]]
        titles2 = [c["title"] for c in report2["cases"]]
        assert titles1 == titles2 == sorted(titles1)


class TestRealDataRegression:
    """Regressionstests gegen den ECHTEN Produktivdatenbestand -- verifiziert
    die im Auftrag geforderte Konsistenz (exakt 35 Faelle, keine fehlenden/
    doppelten, classification_sum stimmt) sowie den dokumentierten DS-Lite-
    Sonderfall (siehe Moduldocstring: lexikalisch identisch zum bereits
    bestaetigten FALSE_POSITIVE, bewusst MANUAL_REVIEW/LOW)."""

    def test_exakt_35_faelle_konsistent(self):
        rules_cfg = load_current_rules()
        report = ura.build_report(input_path=FORENSICS_SOURCE, rules_cfg=rules_cfg)
        assert report["summary"]["total_unclear"] == 35
        consistency = report["consistency"]
        assert consistency["total_cases"] == 35
        assert consistency["matched_cases"] == 35
        assert consistency["missing_cases"] == []
        assert consistency["duplicate_cases"] == []
        assert consistency["classification_sum"] == 35
        assert consistency["consistency_ok"] is True

    def test_klassifikationssumme_ergibt_summary(self):
        rules_cfg = load_current_rules()
        report = ura.build_report(input_path=FORENSICS_SOURCE, rules_cfg=rules_cfg)
        summary = report["summary"]
        total = (
            summary["likely_true_positive"]
            + summary["likely_false_positive"]
            + summary["ground_truth_conflict"]
            + summary["manual_review"]
        )
        assert total == 35 == summary["total_unclear"]

    def test_ds_lite_sonderfall_bleibt_manual_review_low(self):
        rules_cfg = load_current_rules()
        report = ura.build_report(input_path=FORENSICS_SOURCE, rules_cfg=rules_cfg)
        ds_lite = next(
            c for c in report["cases"] if c["case_id"] == "https://www.ebay.de/itm/318701631164"
        )
        assert ds_lite["assessment"]["status"] == ura.STATUS_MANUAL_REVIEW
        assert ds_lite["confidence"] == ura.CONFIDENCE_LOW

    def test_top_candidates_nur_live_aktive_likely_false_positive(self):
        rules_cfg = load_current_rules()
        report = ura.build_report(input_path=FORENSICS_SOURCE, rules_cfg=rules_cfg)
        assert len(report["top_candidates"]) > 0
        for c in report["top_candidates"]:
            assert c["assessment"]["status"] == ura.STATUS_LIKELY_FALSE_POSITIVE
            assert c["current_routing"]["routing_status"] == ffp.ROUTING_STATUS_SAME_CATEGORY

    def test_keine_ground_truth_conflict_in_diesem_batch(self):
        # Bewusste, im Moduldocstring begruendete Entscheidung: die 35
        # UNCLEAR-Faelle werden nicht als GROUND_TRUTH_CONFLICT eingestuft
        # (kein vorheriges Urteil, das widerlegt werden koennte).
        rules_cfg = load_current_rules()
        report = ura.build_report(input_path=FORENSICS_SOURCE, rules_cfg=rules_cfg)
        assert report["summary"]["ground_truth_conflict"] == 0
