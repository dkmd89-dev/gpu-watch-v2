"""Tests für rule_analyzer.py (Phase 15, Schritt 2 -- read-only
Regelwerk-Diagnose, siehe PHASE15_OPTIMIERUNG.md Abschnitte 6-12).

Jede Prüfung wird isoliert gegen kleine, synthetische rules_cfg-Fixtures
getestet (keine Abhängigkeit von den echten rules/*.yaml -- das folgt
in Schritt 3, wenn der Analyzer gegen das komplette Ruleset läuft)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rule_analyzer import (
    analyze_ruleset,
    check_duplicates,
    check_exclude_conflicts,
    check_overlaps,
    check_shadowed,
    check_structure,
    check_suspicious_require_all_of,
    check_unreachable,
)


def _cfg(rules, defaults=None):
    return {"rules": rules, "defaults": defaults or {}}


def _rule(label, category="gpu", **kwargs):
    r = {"label": label, "_category": category}
    r.update(kwargs)
    return r


# ------------------------------------------------------------------
# 7.1 Strukturprüfung
# ------------------------------------------------------------------
def test_regel_ohne_label_ist_error():
    cfg = _cfg([{"match": ["rtx 4070"], "_category": "gpu"}])
    findings = check_structure(cfg)
    assert any(f.severity == "ERROR" and f.check == "structure" for f in findings)


def test_leere_regel_ohne_match_require_requirements_ist_error():
    cfg = _cfg([_rule("A")])
    findings = check_structure(cfg)
    assert any(
        f.severity == "ERROR" and "matcht" in f.message and "JEDEN Titel" in f.message
        for f in findings
    )


def test_require_all_of_als_flacher_string_ist_error():
    cfg = _cfg([_rule("A", require_all_of="lego")])
    findings = check_structure(cfg)
    assert any(
        f.severity == "ERROR" and "require_all_of" in f.message and "list" in f.message
        for f in findings
    )


def test_require_all_of_gruppe_als_string_statt_liste_ist_error():
    cfg = _cfg([_rule("A", require_all_of=["lego"])])
    findings = check_structure(cfg)
    assert any(f.severity == "ERROR" and "Zeichenfolge" in f.message for f in findings)


def test_leere_require_all_of_gruppe_ist_error():
    cfg = _cfg([_rule("A", require_all_of=[["lego"], []])])
    findings = check_structure(cfg)
    assert any(f.severity == "ERROR" and "leere Gruppe" in f.message for f in findings)


def test_negativer_max_price_ist_error():
    cfg = _cfg([_rule("A", match=["gpu"], max_price=-10)])
    findings = check_structure(cfg)
    assert any(f.severity == "ERROR" and "max_price" in f.message for f in findings)


def test_gueltige_regel_hat_keine_structure_findings():
    cfg = _cfg([_rule("A", match=["rtx 4070"], max_price=200)])
    assert check_structure(cfg) == []


def test_unbekanntes_regelfeld_ist_warning():
    cfg = _cfg([_rule("A", match=["x"], require_any_of=[["y"]])])
    findings = check_structure(cfg)
    assert any(
        f.severity == "WARNING" and "require_any_of" in f.message for f in findings
    )


def test_unbekanntes_requirements_feld_ist_warning():
    cfg = _cfg([_rule("A", requirements={"min_ram_gb": 16, "foo": 1})])
    findings = check_structure(cfg)
    assert any(f.severity == "WARNING" and "foo" in f.message for f in findings)


def test_bekanntes_requirements_feld_erzeugt_keinen_warning():
    cfg = _cfg([_rule("A", requirements={"min_ram_gb": 16, "requires_dedicated_gpu": True})])
    findings = check_structure(cfg)
    assert not any(f.check == "structure" and f.severity == "WARNING" for f in findings)


# ------------------------------------------------------------------
# 7.2 Duplicate Detection
# ------------------------------------------------------------------
def test_identische_regeln_werden_als_duplicate_gemeldet():
    cfg = _cfg([
        _rule("A", match=["ps5"], max_price=100),
        _rule("B", match=["ps5"], max_price=100),
    ])
    findings = check_duplicates(cfg)
    assert any(f.check == "duplicate" and f.severity == "WARNING" for f in findings)


def test_gleiche_bedingung_unterschiedlicher_max_price_ist_kein_duplicate():
    cfg = _cfg([
        _rule("Top-Deal", match=["ps5"], max_price=100, price_history_model="ps5"),
        _rule("Guter-Preis", match=["ps5"], max_price=150, price_history_model="ps5"),
    ])
    findings = check_duplicates(cfg)
    assert findings == []


def test_geteiltes_price_history_model_ueber_kategorien_ist_warning():
    cfg = _cfg([
        _rule("A", category="gpu", match=["x"], price_history_model="shared_model"),
        _rule("B", category="netzteil", match=["y"], price_history_model="shared_model"),
    ])
    findings = check_duplicates(cfg)
    assert any(
        f.check == "duplicate" and "geteilt" in f.message for f in findings
    )


# ------------------------------------------------------------------
# 8. Overlap Detection
# ------------------------------------------------------------------
def test_geteilte_begriffe_gleiche_kategorie_anderes_modell_ist_info():
    cfg = _cfg([
        _rule("A", category="lego_minifiguren", match=["lego ninjago", "ninjago figur"], price_history_model="m1"),
        _rule("B", category="lego_minifiguren", match=["lego ninjago", "star wars"], price_history_model="m2"),
    ])
    findings = check_overlaps(cfg)
    assert any(f.severity == "INFO" and f.check == "overlap" for f in findings)


def test_einwort_begriffe_werden_bei_overlap_ignoriert():
    # Einzelne generische Woerter ("controller", "defekt") kommen in vielen
    # unabhaengigen Regeln vor -- Ueberschneidung nur bei Mehrwort-Phrasen
    # relevant (siehe Docstring check_overlaps()).
    cfg = _cfg([
        _rule("A", category="controller", match=["controller"]),
        _rule("B", category="retro_konsolen", match=["controller"]),
    ])
    assert check_overlaps(cfg) == []


def test_geteilte_begriffe_unterschiedliche_kategorie_ist_warning():
    cfg = _cfg([
        _rule("A", category="controller", match=["ps5 controller"]),
        _rule("B", category="konsolen_bundles", match=["ps5 controller"]),
    ])
    findings = check_overlaps(cfg)
    assert any(f.severity == "WARNING" and f.check == "overlap" for f in findings)


def test_tier_muster_gleiche_kategorie_gleiches_modell_kein_overlap_finding():
    cfg = _cfg([
        _rule("Top-Deal", match=["iphone 15"], price_history_model="iphone_15"),
        _rule("Guter-Preis", match=["iphone 15"], price_history_model="iphone_15"),
    ])
    assert check_overlaps(cfg) == []


def test_keine_geteilten_begriffe_kein_finding():
    cfg = _cfg([
        _rule("A", match=["gpu"]),
        _rule("B", match=["cpu"]),
    ])
    assert check_overlaps(cfg) == []


# ------------------------------------------------------------------
# 9. Shadowed Rules
# ------------------------------------------------------------------
def test_generische_regel_vor_spezifischer_regel_ist_shadow_warning():
    # Beispiel aus dem Auftrag (Abschnitt 9): "iphone" vor "iphone 15".
    cfg = _cfg([
        _rule("iphone_generic", category="iphone", match=["iphone"]),
        _rule("iphone_15", category="iphone", match=["iphone 15"]),
    ])
    findings = check_shadowed(cfg)
    assert len(findings) == 1
    f = findings[0]
    assert f.severity == "WARNING"
    assert f.rule_label == "iphone_15"
    assert f.details["earlier_rule"] == "iphone_generic"


def test_spezifische_regel_vor_generischer_regel_kein_shadow():
    cfg = _cfg([
        _rule("iphone_15", category="iphone", match=["iphone 15"]),
        _rule("iphone_generic", category="iphone", match=["iphone"]),
    ])
    assert check_shadowed(cfg) == []


def test_engeres_preisfenster_der_frueheren_regel_verhindert_shadow():
    # Die generische Regel deckt zwar den Titelraum ab, aber ihr max_price
    # ist enger als die spezifische Regel -- teurere Titel fallen bei ihr
    # regulaer durch (kein echtes Shadowing).
    cfg = _cfg([
        _rule("iphone_generic", category="iphone", match=["iphone"], max_price=50),
        _rule("iphone_15", category="iphone", match=["iphone 15"], max_price=500),
    ])
    assert check_shadowed(cfg) == []


def test_unterschiedliche_kategorien_kein_shadow():
    cfg = _cfg([
        _rule("A", category="iphone", match=["iphone"]),
        _rule("B", category="macbook", match=["iphone 15"]),
    ])
    assert check_shadowed(cfg) == []


def test_require_all_of_regeln_werden_von_shadow_check_uebersprungen():
    cfg = _cfg([
        _rule("A", category="gpu", require_all_of=[["gpu"]]),
        _rule("B", category="gpu", require_all_of=[["gpu"], ["rtx"]]),
    ])
    assert check_shadowed(cfg) == []


# ------------------------------------------------------------------
# 10. require_all_of Suspicion Detection
# ------------------------------------------------------------------
def _lego_category_siblings(n=6):
    """n Regeln, die "lego" als eigene, standalone require_all_of-Gruppe
    nutzen -- macht "lego" in dieser Kategorie ubiquitaer (>= 40% der
    Regeln, siehe UBIQUITOUS_MIN_SHARE), analog zur echten
    lego_minifiguren.yaml (44 "lego"-Erwaehnungen in 36 Regeln)."""
    return [
        _rule(f"Lego-Sibling-{i}", category="lego_minifiguren",
              require_all_of=[["lego"], [f"figur-{i}"]])
        for i in range(n)
    ]


def test_lego_star_wars_ein_gruppe_wird_als_suspicious_erkannt():
    # Der historische Phase-12-Bug: ["lego", "star wars"] als EINE Gruppe.
    # "lego" ist dank der Sibling-Regeln ubiquitaer in der Kategorie,
    # "star wars" nicht -- genau das Muster, das den echten Bug ausmachte.
    cfg = _cfg(_lego_category_siblings() + [
        _rule(
            "LEGO Star Wars Darth Revan",
            category="lego_minifiguren",
            require_all_of=[["lego", "star wars"]],
            price_history_model="lego_sw_rare",
        )
    ])
    findings = check_suspicious_require_all_of(cfg)
    assert len(findings) == 1
    assert findings[0].severity == "WARNING"
    assert findings[0].details["ubiquitous_terms"] == ["lego"]
    assert findings[0].details["specific_terms"] == ["star wars"]


def test_korrekt_getrennte_gruppen_kein_suspicious_finding():
    cfg = _cfg(_lego_category_siblings() + [
        _rule(
            "LEGO Star Wars Darth Revan",
            category="lego_minifiguren",
            require_all_of=[["lego"], ["star wars"], ["darth revan", "revan"]],
        )
    ])
    assert check_suspicious_require_all_of(cfg) == []


def test_zwei_gleichrangige_alternativbegriffe_kein_finding():
    # Echtes Ruleset-Muster (handhelds.yaml): "rog ally"/"legion go" sind
    # zwei unterschiedliche, aber gleich SELTENE Geraete, bewusst als
    # Alternative in einer Gruppe -- keiner von beiden ist ubiquitaer,
    # also kein Hinweis auf einen verungueckten UND-Fall.
    cfg = _cfg(_lego_category_siblings() + [
        _rule(
            "Asus ROG Ally / Lenovo Legion Go",
            category="lego_minifiguren",
            require_all_of=[["rog ally", "legion go"]],
        )
    ])
    findings = check_suspicious_require_all_of(cfg)
    assert findings == []


def test_kleine_kategorie_unter_mindestgroesse_kein_finding():
    # UBIQUITOUS_MIN_RULES: unter 5 Regeln zu wenig Signal fuer eine
    # verlaessliche Haeufigkeitsaussage.
    cfg = _cfg([
        _rule("A", category="autoradio_opel_corsa", require_all_of=[["lego"], ["x"]]),
        _rule(
            "B", category="autoradio_opel_corsa",
            require_all_of=[["lego", "star wars"]],
        ),
    ])
    assert check_suspicious_require_all_of(cfg) == []


def test_mehrere_gruppen_werden_nicht_als_suspicious_gemeldet():
    cfg = _cfg(_lego_category_siblings() + [
        _rule(
            "LEGO Star Wars",
            category="lego_minifiguren",
            require_all_of=[["lego", "star wars"], ["darth revan"]],
        )
    ])
    assert check_suspicious_require_all_of(cfg) == []


# ------------------------------------------------------------------
# 11. Exclude Conflicts
# ------------------------------------------------------------------
def test_einziger_match_begriff_gleich_exclude_ist_error():
    cfg = _cfg([_rule("A", match=["xbox"], exclude=["xbox"])])
    findings = check_exclude_conflicts(cfg)
    assert any(f.severity == "ERROR" for f in findings)


def test_ein_match_begriff_unter_mehreren_gleich_exclude_ist_warning():
    cfg = _cfg([_rule("A", match=["xbox", "playstation"], exclude=["xbox"])])
    findings = check_exclude_conflicts(cfg)
    assert findings and all(f.severity == "WARNING" for f in findings)


def test_require_all_of_einzelgruppe_gleich_exclude_ist_error():
    cfg = _cfg([_rule("A", require_all_of=[["defekt"]], exclude=["defekt"])])
    findings = check_exclude_conflicts(cfg)
    assert any(f.severity == "ERROR" for f in findings)


def test_kategorie_exclude_erzeugt_ebenfalls_conflict():
    cfg = _cfg([
        {
            "label": "A", "_category": "handhelds", "match": ["steam deck"],
            "_category_exclude_terms": ["steam deck"], "_ignore_global_excludes": [],
        }
    ])
    findings = check_exclude_conflicts(cfg)
    assert any(f.severity == "ERROR" for f in findings)


def test_kein_conflict_ohne_ueberschneidung():
    cfg = _cfg([_rule("A", match=["xbox"], exclude=["defekt"])])
    assert check_exclude_conflicts(cfg) == []


# ------------------------------------------------------------------
# 12. Unreachable Rules
# ------------------------------------------------------------------
def test_leere_require_all_of_gruppe_landet_in_unreachable():
    cfg = _cfg([_rule("A", require_all_of=[[]])])
    findings = check_unreachable(cfg)
    assert any(f.check == "unreachable" and f.severity == "ERROR" for f in findings)


def test_exclude_conflict_error_landet_in_unreachable():
    cfg = _cfg([_rule("A", match=["xbox"], exclude=["xbox"])])
    findings = check_unreachable(cfg)
    assert any(f.check == "unreachable" and f.severity == "ERROR" for f in findings)


def test_warning_level_exclude_conflict_landet_nicht_in_unreachable():
    cfg = _cfg([_rule("A", match=["xbox", "playstation"], exclude=["xbox"])])
    findings = check_unreachable(cfg)
    assert findings == []


# ------------------------------------------------------------------
# Sammel-Report
# ------------------------------------------------------------------
def test_analyze_ruleset_aggregiert_alle_checks():
    cfg = _cfg([
        _rule("A", match=["xbox"], exclude=["xbox"]),  # exclude_conflict + unreachable
        _rule("B"),  # leere Regel -> structure error
    ])
    report = analyze_ruleset(cfg)
    assert report.rule_count == 2
    assert report.category_count == 1
    checks = {f.check for f in report.findings}
    assert "exclude_conflict" in checks
    assert "unreachable" in checks
    assert "structure" in checks
    assert len(report.errors) > 0


def test_analyze_ruleset_read_only_mutiert_rules_cfg_nicht():
    cfg = _cfg([_rule("A", match=["gpu"], max_price=200)])
    import copy
    snapshot = copy.deepcopy(cfg)
    analyze_ruleset(cfg)
    assert cfg == snapshot


def test_sauberes_regelwerk_hat_keine_findings():
    cfg = _cfg([
        _rule("A", category="gpu", match=["rtx 4070"], max_price=500),
        _rule("B", category="netzteil", match=["be quiet 750w"], max_price=80),
    ])
    report = analyze_ruleset(cfg)
    assert report.findings == []


def test_finding_ungueltiger_schweregrad_wirft_error():
    from rule_analyzer import Finding
    import pytest
    with pytest.raises(ValueError):
        Finding("CRITICAL", "structure", "x")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
