"""Tests fuer das neue, read-only Ruleset-Qualitaetssystem
(tools/ruleset_quality/, Auftrag Phase 19.1-19.5).

Deckt die reinen Klassifikations-/Parsing-Bausteine ab, die KEINE eigene
Matching-Entscheidung treffen (das bleibt matcher.evaluate() vorbehalten),
sondern nur bereits vorhandene evaluate()-Ergebnisse in Transition-/
Gate-Kategorien einordnen bzw. das vorhandene Forensik-Artefakt parsen.

Isolationsmuster: analog zu den bestehenden matcher-Tests (kein DATA_DIR-
Bezug noetig, siehe test_handhelds_active_fp_audit_fix.py) -- tools/ liegt
neben app/, daher wird der Projekt-Root vorne in sys.path eingefuegt.
"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.ruleset_quality.benchmark import _after_match_state, classify_gate  # noqa: E402
from tools.ruleset_quality.label_store import parse_forensics  # noqa: E402


@dataclass
class _FakeResult:
    matched: bool
    category: str | None = None
    rule_label: str | None = None


class TestAfterMatchState:
    def test_kein_treffer_wenn_nicht_matched(self):
        assert _after_match_state(_FakeResult(matched=False), "gpu", "GPU-Regel") == "KEIN_TREFFER"

    def test_kein_treffer_wenn_result_none(self):
        assert _after_match_state(None, "gpu", "GPU-Regel") == "KEIN_TREFFER"

    def test_andere_kategorie(self):
        result = _FakeResult(matched=True, category="office_pc", rule_label="X")
        assert _after_match_state(result, "gaming_pc", "X") == "ANDERE_KATEGORIE"

    def test_andere_regel_bei_gleicher_kategorie(self):
        result = _FakeResult(matched=True, category="gpu", rule_label="RTX 3060 Ti")
        assert _after_match_state(result, "gpu", "RTX 3070") == "ANDERE_REGEL"

    def test_gleiche_kategorie_und_regel(self):
        result = _FakeResult(matched=True, category="gpu", rule_label="RTX 3070")
        assert _after_match_state(result, "gpu", "RTX 3070") == "GLEICHE_KATEGORIE"

    def test_stored_rule_none_und_kategorie_gleich_ist_kein_regelwechsel(self):
        # Aeltere/synthetische Eintraege ohne gespeicherte Regel duerfen
        # nicht faelschlich als "ANDERE_REGEL" markiert werden.
        result = _FakeResult(matched=True, category="gpu", rule_label="RTX 3070")
        assert _after_match_state(result, "gpu", None) == "GLEICHE_KATEGORIE"


class TestClassifyGate:
    def test_critical_tp_verschwindet(self):
        severity, label, _ = classify_gate("TRUE_POSITIVE", "KEIN_TREFFER")
        assert severity == "CRITICAL"
        assert "kein Treffer" in label

    def test_neutral_tp_stabil(self):
        severity, _, _ = classify_gate("TRUE_POSITIVE", "GLEICHE_KATEGORIE")
        assert severity == "NEUTRAL"

    def test_warning_kategoriewechsel_bei_tp(self):
        severity, label, _ = classify_gate("TRUE_POSITIVE", "ANDERE_KATEGORIE")
        assert severity == "WARNING"
        assert "Kategoriewechsel" in label

    def test_high_candidate_tp_anderer_matchpfad(self):
        severity, _, _ = classify_gate("TRUE_POSITIVE", "ANDERE_REGEL")
        assert severity == "HIGH_CANDIDATE"

    def test_info_fp_gefixt(self):
        severity, label, _ = classify_gate("FALSE_POSITIVE", "KEIN_TREFFER")
        assert severity == "INFO"
        assert "kein Treffer" in label

    def test_high_candidate_fp_weiterhin_aktiv(self):
        severity, label, _ = classify_gate("FALSE_POSITIVE", "GLEICHE_KATEGORIE")
        assert severity == "HIGH_CANDIDATE"
        assert "weiterhin aktiv" in label

    def test_warning_fp_kategoriewechsel(self):
        severity, _, _ = classify_gate("FALSE_POSITIVE", "ANDERE_KATEGORIE")
        assert severity == "WARNING"

    def test_unclear_bleibt_unclear_ohne_autopromotion(self):
        # Zentrale Anforderung: UNCLEAR darf NIE automatisch zu TP/FP
        # "aufgeloest" werden, auch wenn es weiterhin matcht.
        severity, label, _ = classify_gate("UNCLEAR", "GLEICHE_KATEGORIE")
        assert severity == "INFO"
        assert "UNCLEAR" in label or "unklar" in label.lower()

    def test_unlabeled_ohne_kategoriewechsel_ist_neutral(self):
        severity, _, _ = classify_gate("UNLABELED", "GLEICHE_KATEGORIE")
        assert severity == "NEUTRAL"

    def test_unlabeled_mit_kategoriewechsel_ist_warning(self):
        severity, _, _ = classify_gate("UNLABELED", "ANDERE_KATEGORIE")
        assert severity == "WARNING"


class TestParseForensics:
    def test_parst_nur_bekannte_verdicts(self, tmp_path):
        data = {
            "entries": [
                {"url": "u1", "verdict": "TRUE_POSITIVE", "category": "gpu",
                 "stored_rule_label": "RTX 3070", "title": "RTX 3070 8GB"},
                {"url": "u2", "verdict": "FALSE_POSITIVE", "category": "gpu",
                 "stored_rule_label": "RTX 3070", "title": "RTX 3070 Wasserkuehler"},
                {"url": "u3", "verdict": "SOMETHING_UNEXPECTED", "category": "gpu"},
                {"url": "u4", "category": "gpu"},  # kein verdict-Feld
            ]
        }
        path = tmp_path / "forensics.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        labels = parse_forensics(path)

        assert set(labels) == {"u1", "u2"}
        assert labels["u1"].verdict == "TRUE_POSITIVE"
        assert labels["u2"].verdict == "FALSE_POSITIVE"
        assert labels["u1"].source == "DASHBOARD_MATCH_FORENSICS.json"

    def test_fehlende_datei_gibt_leeres_dict(self, tmp_path):
        assert parse_forensics(tmp_path / "nicht_vorhanden.json") == {}

    def test_fehlende_url_wird_uebersprungen(self, tmp_path):
        data = {"entries": [{"verdict": "TRUE_POSITIVE", "category": "gpu"}]}
        path = tmp_path / "forensics.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        assert parse_forensics(path) == {}


class TestRulesetSignatureDeterminism:
    def test_signatur_ist_deterministisch_und_reagiert_auf_matching_relevante_aenderung(self):
        from tools.ruleset_quality.common import current_ruleset_signature

        cfg_a = {"rules": [{"label": "X", "_category": "gpu", "match": ["rtx 3070"]}]}
        cfg_b = {"rules": [{"label": "X", "_category": "gpu", "match": ["rtx 3070"]}]}
        cfg_c = {"rules": [{"label": "X", "_category": "gpu", "match": ["rtx 3080"]}]}

        assert current_ruleset_signature(cfg_a) == current_ruleset_signature(cfg_b)
        assert current_ruleset_signature(cfg_a) != current_ruleset_signature(cfg_c)
