"""Tests für rule_coverage.py (Phase 15, Schritt 5 -- read-only Rule
Coverage Analysis gegen price_history.jsonl, siehe PHASE15_OPTIMIERUNG.md
Abschnitte 17-18).

Läuft gegen synthetische PricePoint-/rules_cfg-Fixtures (keine Abhängigkeit
von der echten price_history.jsonl -- die Auswertung der echten Datei
erfolgt separat, analog zu Schritt 3 beim Rule Analyzer)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from price_history import PricePoint
from rule_coverage import compute_rule_coverage, compute_rule_quality


def _point(model, category="gpu", price=100.0, date="2026-08-01T10:00:00+00:00",
           fingerprint="rtx 4070 ti 12gb"):
    return PricePoint(
        price=price, date=date, source="Kleinanzeigen",
        model=model, category=category, deal_score=50, fingerprint=fingerprint,
    )


def _rule(label, category="gpu", price_history_model=None, **kwargs):
    r = {"label": label, "_category": category}
    if price_history_model:
        r["price_history_model"] = price_history_model
    r.update(kwargs)
    return r


def _cfg(rules):
    return {"rules": rules, "defaults": {}}


# ------------------------------------------------------------------
# compute_rule_coverage
# ------------------------------------------------------------------
def test_regel_ohne_datenpunkte_hat_matches_null_und_never():
    cfg = _cfg([_rule("A", price_history_model="lego_ninjago_rare",
                       require_all_of=[["lego"], ["ninjago"]])])
    coverage = compute_rule_coverage([], cfg)
    assert len(coverage) == 1
    rc = coverage[0]
    assert rc.price_history_model == "lego_ninjago_rare"
    assert rc.matches == 0
    assert rc.valid == 0
    assert rc.sample_count == 0
    assert rc.last_seen is None
    assert rc.in_current_ruleset is True
    assert rc.false_positive_rate is None


def test_gueltiger_datenpunkt_zaehlt_als_valid():
    cfg = _cfg([_rule("A", price_history_model="rtx_4070_ti", match=["rtx 4070 ti"])])
    points = [_point("rtx_4070_ti", fingerprint="rtx 4070 ti 12gb")]
    coverage = compute_rule_coverage(points, cfg)
    rc = coverage[0]
    assert rc.matches == 1
    assert rc.sample_count == 1
    assert rc.valid == 1
    assert rc.false_positive_indicators == 0
    assert rc.false_positive_rate == 0.0


def test_nicht_mehr_matchender_datenpunkt_zaehlt_als_false_positive_indicator():
    # Simuliert eine spaeter verschaerfte Regel: der gespeicherte
    # Fingerprint matcht die AKTUELLE Regel nicht mehr.
    cfg = _cfg([_rule("A", price_history_model="rtx_4070_ti",
                       require_all_of=[["rtx 4070 ti"], ["12gb", "16gb"]])])
    points = [_point("rtx_4070_ti", fingerprint="rtx 4070 ti ohne angabe")]
    coverage = compute_rule_coverage(points, cfg)
    rc = coverage[0]
    assert rc.matches == 1
    assert rc.sample_count == 1
    assert rc.valid == 0
    assert rc.false_positive_indicators == 1
    assert rc.false_positive_rate == 1.0


def test_falsche_kategorie_bei_neubewertung_zaehlt_als_false_positive():
    # Titel matcht bei Neubewertung eine ANDERE Kategorie/Modell als
    # gespeichert -- ebenfalls ein False-Positive-Indikator.
    cfg = _cfg([
        _rule("A", category="gpu", price_history_model="rtx_4070_ti", match=["rtx 4070 ti"]),
        _rule("B", category="netzteil", price_history_model="netzteil_650w", match=["650w netzteil"]),
    ])
    points = [_point("rtx_4070_ti", category="gpu", fingerprint="650w netzteil")]
    coverage = compute_rule_coverage(points, cfg)
    rc = next(c for c in coverage if c.price_history_model == "rtx_4070_ti")
    assert rc.valid == 0
    assert rc.false_positive_indicators == 1


def test_datenpunkt_ohne_fingerprint_zaehlt_nur_in_matches():
    cfg = _cfg([_rule("A", price_history_model="rtx_4070_ti", match=["rtx 4070 ti"])])
    points = [_point("rtx_4070_ti", fingerprint=None)]
    coverage = compute_rule_coverage(points, cfg)
    rc = coverage[0]
    assert rc.matches == 1
    assert rc.sample_count == 0
    assert rc.valid == 0
    assert rc.false_positive_indicators == 0
    assert rc.false_positive_rate is None


def test_orphan_modell_ohne_aktuelle_regel_wird_markiert():
    cfg = _cfg([_rule("A", price_history_model="rtx_4070_ti", match=["rtx 4070 ti"])])
    points = [_point("alte_grafikkarte_modell", category="gpu", fingerprint="alte karte")]
    coverage = compute_rule_coverage(points, cfg)
    orphan = next(c for c in coverage if c.price_history_model == "alte_grafikkarte_modell")
    assert orphan.in_current_ruleset is False
    assert orphan.category == "gpu"
    assert orphan.matches == 1


def test_last_seen_ist_das_juengste_datum():
    cfg = _cfg([_rule("A", price_history_model="rtx_4070_ti", match=["rtx 4070 ti"])])
    points = [
        _point("rtx_4070_ti", date="2026-07-01T10:00:00+00:00"),
        _point("rtx_4070_ti", date="2026-08-05T09:00:00+00:00"),
        _point("rtx_4070_ti", date="2026-07-20T09:00:00+00:00"),
    ]
    coverage = compute_rule_coverage(points, cfg)
    assert coverage[0].last_seen == "2026-08-05"


def test_mehrere_regeln_teilen_ein_price_history_model_werden_zusammengefasst():
    # Tier-Muster (Top-Deal/Guter-Preis/...): mehrere Regeln, EIN Modell --
    # Coverage darf nicht pro Regel dupliziert werden.
    cfg = _cfg([
        _rule("Top-Deal", price_history_model="rtx_4070_ti", match=["rtx 4070 ti"], max_price=400),
        _rule("Guter Preis", price_history_model="rtx_4070_ti", match=["rtx 4070 ti"], max_price=500),
    ])
    points = [_point("rtx_4070_ti"), _point("rtx_4070_ti")]
    coverage = compute_rule_coverage(points, cfg)
    assert len(coverage) == 1
    assert coverage[0].matches == 2


# ------------------------------------------------------------------
# compute_rule_quality
# ------------------------------------------------------------------
def test_quality_score_liegt_immer_zwischen_0_und_1():
    cfg = _cfg([_rule("A", price_history_model="m", match=["x"])])
    points = [_point("m") for _ in range(30)]
    coverage = compute_rule_coverage(points, cfg)
    q = compute_rule_quality(coverage[0], reference_date_iso="2026-08-09")
    assert 0.0 <= q.overall <= 1.0
    for score in (q.match_volume_score, q.false_positive_score,
                  q.data_freshness_score, q.price_confidence_score,
                  q.rule_stability_score):
        assert 0.0 <= score <= 1.0


def test_regel_ohne_daten_hat_niedrigen_overall_score():
    cfg = _cfg([_rule("A", price_history_model="m", match=["x"])])
    coverage = compute_rule_coverage([], cfg)
    q = compute_rule_quality(coverage[0], reference_date_iso="2026-08-09")
    assert q.match_volume_score == 0.0
    assert q.price_confidence_label == "LOW"
    assert q.overall < 0.3


def test_viele_frische_valide_treffer_ergeben_hohen_overall_score():
    cfg = _cfg([_rule("A", price_history_model="m", match=["rtx 4070 ti"])])
    points = [_point("m", date="2026-08-09T10:00:00+00:00") for _ in range(20)]
    coverage = compute_rule_coverage(points, cfg)
    q = compute_rule_quality(coverage[0], reference_date_iso="2026-08-09")
    assert q.match_volume_score == 1.0
    assert q.false_positive_score == 1.0
    assert q.price_confidence_label == "HIGH"
    assert q.overall > 0.8


def test_unverifizierbare_stichprobe_gibt_neutralen_false_positive_score():
    cfg = _cfg([_rule("A", price_history_model="m", match=["x"])])
    points = [_point("m", fingerprint=None) for _ in range(5)]
    coverage = compute_rule_coverage(points, cfg)
    q = compute_rule_quality(coverage[0], reference_date_iso="2026-08-09")
    assert q.false_positive_score == 0.5


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
