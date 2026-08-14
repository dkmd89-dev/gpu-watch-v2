"""Tests fuer tools/ruleset_quality/detailed_transition.py (finale
Read-only-Revalidierung, Regression-Gate v2).

Deckt die epistemisch heikelsten Stellen ab: _derive_new_status() darf
NIEMALS ein neues TP/FP/UNCLEAR-Urteil erfinden, wenn sich der Match-
Zustand geaendert hat -- nur wenn er UNVERAENDERT ist, darf das alte
Urteil logisch zwingend uebernommen werden. _gate_findings() muss exakt
der im Auftrag vorgegebenen CRITICAL/HIGH/MEDIUM/LOW-Matrix folgen, ohne
fuer nicht-automatisch-entscheidbare Faelle (z.B. echtes "TP -> FP") ein
stillschweigendes Urteil zu faellen.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.ruleset_quality.detailed_transition import (  # noqa: E402
    NOT_AVAILABLE,
    _after_match_state,
    _derive_new_status,
    _gate_findings,
    _match_path,
)


@dataclass
class _FakeResult:
    matched: bool
    category: str | None = None
    rule_label: str | None = None
    price_history_model: str | None = None


class TestAfterMatchStateV2:
    def test_kein_treffer(self):
        assert _after_match_state(_FakeResult(matched=False), "gpu", "R") == "KEIN_TREFFER"

    def test_unveraendert(self):
        r = _FakeResult(matched=True, category="gpu", rule_label="RTX 3070")
        assert _after_match_state(r, "gpu", "RTX 3070") == "UNVERAENDERT"

    def test_regel_geaendert(self):
        r = _FakeResult(matched=True, category="gpu", rule_label="RTX 3060 Ti")
        assert _after_match_state(r, "gpu", "RTX 3070") == "REGEL_GEAENDERT"

    def test_kategorie_geaendert(self):
        r = _FakeResult(matched=True, category="office_pc", rule_label="X")
        assert _after_match_state(r, "gaming_pc", "X") == "KATEGORIE_GEAENDERT"


class TestDeriveNewStatus:
    def test_kein_treffer_ist_immer_objektiv(self):
        assert _derive_new_status("TRUE_POSITIVE", "KEIN_TREFFER") == "KEIN_TREFFER"
        assert _derive_new_status(NOT_AVAILABLE, "KEIN_TREFFER") == "KEIN_TREFFER"

    def test_unveraendert_uebernimmt_altes_urteil(self):
        # Titel/Kategorie/Regel identisch -> der bewertete Gegenstand hat
        # sich nicht geaendert, das alte Urteil gilt zwingend weiter.
        assert _derive_new_status("TRUE_POSITIVE", "UNVERAENDERT") == "TRUE_POSITIVE"
        assert _derive_new_status("FALSE_POSITIVE", "UNVERAENDERT") == "FALSE_POSITIVE"
        assert _derive_new_status("UNCLEAR", "UNVERAENDERT") == "UNCLEAR"

    def test_kein_vorheriges_label_bleibt_not_available(self):
        assert _derive_new_status(NOT_AVAILABLE, "UNVERAENDERT") == NOT_AVAILABLE
        assert _derive_new_status(NOT_AVAILABLE, "REGEL_GEAENDERT") == NOT_AVAILABLE

    def test_regel_oder_kategoriewechsel_erfordert_manuelle_pruefung(self):
        # Zentrale Anforderung: KEIN geratenes TP/FP/UNCLEAR, wenn sich
        # der Matchpfad geaendert hat.
        assert _derive_new_status("TRUE_POSITIVE", "REGEL_GEAENDERT") == "MANUELLE_PRUEFUNG_NOETIG"
        assert _derive_new_status("TRUE_POSITIVE", "KATEGORIE_GEAENDERT") == "MANUELLE_PRUEFUNG_NOETIG"
        assert _derive_new_status("FALSE_POSITIVE", "KATEGORIE_GEAENDERT") == "MANUELLE_PRUEFUNG_NOETIG"
        assert _derive_new_status("UNCLEAR", "REGEL_GEAENDERT") == "MANUELLE_PRUEFUNG_NOETIG"


class TestMatchPath:
    def test_beide_vorhanden(self):
        assert _match_path("gpu", "RTX 3070") == "gpu :: RTX 3070"

    def test_beide_fehlen(self):
        assert _match_path(None, None) == NOT_AVAILABLE


class TestGateFindingsMatrix:
    def _severities(self, findings):
        return {f["label"]: f["severity"] for f in findings}

    def test_critical_tp_kein_treffer(self):
        findings = _gate_findings("TRUE_POSITIVE", "KEIN_TREFFER", None)
        sev = self._severities(findings)
        assert sev["TRUE_POSITIVE -> kein Treffer"] == "CRITICAL"
        assert all(f["confirmed"] for f in findings)

    def test_high_tp_kategoriewechsel(self):
        findings = _gate_findings("TRUE_POSITIVE", "KATEGORIE_GEAENDERT", None)
        sev = self._severities(findings)
        assert sev["Kategoriewechsel eines TRUE_POSITIVE"] == "HIGH"

    def test_high_tp_regelwechsel_first_match_wins(self):
        findings = _gate_findings("TRUE_POSITIVE", "REGEL_GEAENDERT", None)
        sev = self._severities(findings)
        assert sev["TRUE_POSITIVE: Regelwechsel bei gleicher Kategorie (First-Match-Wins)"] == "HIGH"

    def test_high_tp_phm_wechsel_nur_wenn_bekannt(self):
        # phm_changed=None (nicht vergleichbar) darf KEIN Finding erzeugen.
        findings_none = _gate_findings("TRUE_POSITIVE", "UNVERAENDERT", None)
        assert not any("price_history_model" in f["label"] for f in findings_none)

        findings_true = _gate_findings("TRUE_POSITIVE", "REGEL_GEAENDERT", True)
        labels = [f["label"] for f in findings_true]
        assert "TRUE_POSITIVE: price_history_model geaendert" in labels

    def test_info_fp_kein_treffer(self):
        findings = _gate_findings("FALSE_POSITIVE", "KEIN_TREFFER", None)
        sev = self._severities(findings)
        assert sev["FALSE_POSITIVE -> kein Treffer"] == "INFO"

    def test_low_fp_matchpfad_geaendert_ist_kandidat_nicht_bestaetigt(self):
        findings = _gate_findings("FALSE_POSITIVE", "KATEGORIE_GEAENDERT", None)
        assert len(findings) == 1
        assert findings[0]["severity"] == "LOW"
        assert findings[0]["confirmed"] is False  # explizit KEIN automatisches Urteil

    def test_medium_unclear_kategoriewechsel(self):
        findings = _gate_findings("UNCLEAR", "KATEGORIE_GEAENDERT", None)
        sev = self._severities(findings)
        assert sev["Kategoriewechsel eines UNCLEAR"] == "MEDIUM"

    def test_unveraendert_ohne_label_erzeugt_kein_finding(self):
        assert _gate_findings(NOT_AVAILABLE, "UNVERAENDERT", None) == []

    def test_fp_unveraendert_ist_bestaetigt_kein_neues_urteil_noetig(self):
        findings = _gate_findings("FALSE_POSITIVE", "UNVERAENDERT", None)
        assert len(findings) == 1
        assert findings[0]["confirmed"] is True
        assert findings[0]["severity"] == "LOW"
