"""Tests für den In-Memory Entry+Ruleset-Cache in category_validation.py
(Hotfix "DRINGEND -- Phase 14 Schritt 2 blockiert Dashboard").

Prüft ausschließlich das CACHE-VERHALTEN (Hit/Miss/Invalidierung,
gemeinsame Nutzung durch api/status.py und api/deals.py). Die fachliche
Kategorievalidierung selbst (Steam Deck/Switch-Lite-Regressionen etc.)
ist bereits in tests/test_category_validation.py abgedeckt und bleibt dort
unverändert grün (siehe Testlauf im Auftrag).

Isolation: _validity_cache ist Modul-Level-State und wird von JEDEM Test
geteilt (auch aus anderen Testdateien, die category_validation importieren,
z.B. test_category_validation.py und die Integrationstests in dieser
Datei). Ein autouse-Fixture leert den Cache daher vor JEDEM Test.
"""
import sys
import os
import json
import importlib.util
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, compute_ruleset_signature
import category_validation
from category_validation import (
    is_still_valid_category,
    filter_valid_entries,
    _cached_is_still_valid_category,
)

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


@pytest.fixture(autouse=True)
def _clear_cache():
    category_validation._validity_cache.clear()
    yield
    category_validation._validity_cache.clear()


def _count_evaluate_calls(monkeypatch):
    """Zaehlt evaluate()-Aufrufe, ohne das fachliche Verhalten zu aendern
    (wraps die echte matcher.evaluate, ruft sie unveraendert auf)."""
    calls = {"n": 0}
    original_evaluate = category_validation.evaluate

    def counting_evaluate(*args, **kwargs):
        calls["n"] += 1
        return original_evaluate(*args, **kwargs)

    monkeypatch.setattr(category_validation, "evaluate", counting_evaluate)
    return calls


# ============================================================
# Cache Hit / Miss
# ============================================================

def test_cache_hit_gleicher_entry_gleicher_ruleset_hash(monkeypatch):
    calls = _count_evaluate_calls(monkeypatch)
    entry = {"title": "Steam Deck 256GB", "price": 200, "category": "handhelds"}
    ruleset_hash = compute_ruleset_signature(_rules_cfg())

    r1 = _cached_is_still_valid_category(entry, _rules_cfg(), ruleset_hash)
    r2 = _cached_is_still_valid_category(entry, _rules_cfg(), ruleset_hash)

    assert r1 is True
    assert r2 is True
    assert calls["n"] == 1  # zweiter Aufruf kam aus dem Cache


def test_cache_miss_neuer_entry(monkeypatch):
    calls = _count_evaluate_calls(monkeypatch)
    ruleset_hash = compute_ruleset_signature(_rules_cfg())
    entry_a = {"title": "Steam Deck 256GB", "price": 200, "category": "handhelds"}
    entry_b = {"title": "Steam Deck OLED 512GB", "price": 350, "category": "handhelds"}

    _cached_is_still_valid_category(entry_a, _rules_cfg(), ruleset_hash)
    _cached_is_still_valid_category(entry_b, _rules_cfg(), ruleset_hash)

    assert calls["n"] == 2  # unterschiedliche url/title -> beides Misses


def test_cache_miss_geaenderter_titel(monkeypatch):
    calls = _count_evaluate_calls(monkeypatch)
    ruleset_hash = compute_ruleset_signature(_rules_cfg())
    entry = {
        "url": "https://example.invalid/x",
        "title": "Steam Deck 256GB",
        "price": 200,
        "category": "handhelds",
    }
    _cached_is_still_valid_category(entry, _rules_cfg(), ruleset_hash)

    entry_geaendert = dict(entry, title="Steam Deck 256GB (Titel korrigiert)")
    _cached_is_still_valid_category(entry_geaendert, _rules_cfg(), ruleset_hash)

    assert calls["n"] == 2


def test_cache_miss_geaenderte_kategorie(monkeypatch):
    calls = _count_evaluate_calls(monkeypatch)
    ruleset_hash = compute_ruleset_signature(_rules_cfg())
    entry = {
        "url": "https://example.invalid/y",
        "title": "Steam Deck 256GB",
        "price": 200,
        "category": "handhelds",
    }
    _cached_is_still_valid_category(entry, _rules_cfg(), ruleset_hash)

    entry_andere_kategorie = dict(entry, category="konsolen_bundles")
    _cached_is_still_valid_category(entry_andere_kategorie, _rules_cfg(), ruleset_hash)

    assert calls["n"] == 2


def test_cache_miss_geaendertes_ruleset(monkeypatch):
    calls = _count_evaluate_calls(monkeypatch)
    entry = {
        "url": "https://example.invalid/z",
        "title": "Steam Deck 256GB",
        "price": 200,
        "category": "handhelds",
    }
    hash_alt = compute_ruleset_signature(_rules_cfg())
    _cached_is_still_valid_category(entry, _rules_cfg(), hash_alt)

    # Simuliertes geaendertes Regelwerk -> anderer Hash -> Miss, obwohl
    # url/title/category identisch sind.
    hash_neu = hash_alt + "-geaendert"
    _cached_is_still_valid_category(entry, _rules_cfg(), hash_neu)

    assert calls["n"] == 2


def test_cache_hit_ueber_filter_valid_entries_bei_wiederholtem_aufruf(monkeypatch):
    """filter_valid_entries() berechnet den ruleset_hash selbst -- bei
    zwei Aufrufen mit unveraendertem rules_cfg muss der zweite Durchlauf
    vollstaendig aus dem Cache bedient werden."""
    calls = _count_evaluate_calls(monkeypatch)
    found = [
        {"url": "https://example.invalid/a", "title": "Steam Deck 256GB", "price": 200, "category": "handhelds"},
        {"url": "https://example.invalid/b", "title": "Netzteil für Steam Deck 45W", "price": 15, "category": "handhelds"},
    ]

    r1 = filter_valid_entries(found, _rules_cfg())
    assert calls["n"] == 2  # cold: beide Eintraege evaluiert

    r2 = filter_valid_entries(found, _rules_cfg())
    assert calls["n"] == 2  # warm: keine weiteren evaluate()-Aufrufe

    assert len(r1) == len(r2) == 1
    assert r1[0]["title"] == r2[0]["title"] == "Steam Deck 256GB"


def test_is_still_valid_category_bleibt_ohne_cache_direkt_aufrufbar():
    """Fachliche Pruefung unveraendert direkt (ohne Cache-Wrapper)
    aufrufbar -- wichtig fuer bestehende Tests/Aufrufer."""
    entry = {"title": "Steam Deck 256GB", "price": 200, "category": "handhelds"}
    assert is_still_valid_category(entry, _rules_cfg()) is True


# ============================================================
# Integrationstests: /api/status und /api/deals (/api/found) teilen sich
# denselben Cache
# ============================================================

def _load_app_module(data_dir: str, module_name: str):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_ENTRY_1 = {
    "title": "Steam Deck 256GB LCD wie neu",
    "price": 170,
    "url": "https://example.invalid/steamdeck-cache-test",
    "location": "Karlsruhe",
    "source": "kleinanzeigen",
    "category": "handhelds",
    "manufacturer": "Valve",
    "deal_score": 85,
    "deal_stars": "★★★★☆",
    "is_top_deal": False,
}

_ENTRY_2 = {
    "title": "Nintendo Switch Lite türkis",
    "price": 80,
    "url": "https://example.invalid/switchlite-cache-test",
    "location": "Karlsruhe",
    "source": "kleinanzeigen",
    "category": "konsolen_bundles",
    "manufacturer": "Nintendo",
    "deal_score": 70,
    "deal_stars": "★★★☆☆",
    "is_top_deal": False,
}


def test_api_status_und_api_found_teilen_denselben_cache(monkeypatch):
    calls = _count_evaluate_calls(monkeypatch)
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_catval_cache_shared")
        app_mod.FOUND_FILE.parent.mkdir(parents=True, exist_ok=True)
        app_mod.FOUND_FILE.write_text(
            json.dumps([_ENTRY_1, _ENTRY_2]), encoding="utf-8"
        )

        client = app_mod.app.test_client()

        # 1. Request (/api/status): cold -> 2 evaluate()-Aufrufe
        client.get("/api/status")
        calls_nach_status = calls["n"]
        assert calls_nach_status == 2

        # 2. Request (/api/found, andere Route): muss aus demselben
        # Modul-Cache bedient werden -- KEINE weiteren evaluate()-Aufrufe,
        # obwohl load_rules() in api/deals.py unabhaengig neu aufgerufen
        # wird (identisches rules_cfg -> identischer ruleset_hash).
        client.get("/api/found")
        assert calls["n"] == calls_nach_status

        # 3. Request (/, Dashboard): ebenfalls derselbe Cache
        client.get("/")
        assert calls["n"] == calls_nach_status


def test_api_status_kpis_unveraendert_mit_cache():
    """Fachliches Ergebnis (KPI-Zaehlung) bleibt mit Cache identisch zum
    Verhalten ohne Cache -- reine Performance-Optimierung, kein
    Verhaltensunterschied."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, "app_under_test_catval_cache_kpi")
        app_mod.FOUND_FILE.parent.mkdir(parents=True, exist_ok=True)
        app_mod.FOUND_FILE.write_text(
            json.dumps([_ENTRY_1, _ENTRY_2]), encoding="utf-8"
        )

        client = app_mod.app.test_client()
        data = client.get("/api/status").get_json()

        assert data["category_counts"].get("handhelds") == 1
        assert data["category_counts"].get("konsolen_bundles") == 1


# ============================================================
# Performance: 2500 Eintraege, cold vs. warm
# ============================================================

def test_performance_2500_eintraege_cold_vs_warm(monkeypatch):
    """Realistischer Datenbestand (2500 Eintraege, Mix aus echten
    Treffern und Alt-Fehltreffern) -- misst evaluate()-Aufrufe und
    Response-Zeit fuer cold vs. warm Cache. Kein hartes Zeitlimit (CI-
    Hardware variiert), aber warm MUSS spuerbar schneller sein und OHNE
    weitere evaluate()-Aufrufe auskommen.
    """
    calls = _count_evaluate_calls(monkeypatch)

    found = []
    for i in range(2500):
        if i % 2 == 0:
            found.append({
                "url": f"https://example.invalid/perf-{i}",
                "title": f"Steam Deck 256GB Nr {i}",
                "price": 200,
                "category": "handhelds",
            })
        else:
            found.append({
                "url": f"https://example.invalid/perf-{i}",
                "title": f"Netzteil für Steam Deck 45W Nr {i}",
                "price": 15,
                "category": "handhelds",
            })

    rules_cfg = _rules_cfg()

    t0 = time.perf_counter()
    result_cold = filter_valid_entries(found, rules_cfg)
    t_cold = time.perf_counter() - t0
    calls_cold = calls["n"]

    assert calls_cold == 2500
    assert len(result_cold) == 1250  # nur die geraden (echten) Treffer

    t0 = time.perf_counter()
    result_warm = filter_valid_entries(found, rules_cfg)
    t_warm = time.perf_counter() - t0
    calls_warm_total = calls["n"]

    assert calls_warm_total == calls_cold  # keine weiteren evaluate()-Aufrufe
    assert len(result_warm) == 1250
    assert t_warm < t_cold

    print(
        f"\n[PERF] cold: {t_cold:.4f}s / {calls_cold} evaluate()-Aufrufe | "
        f"warm: {t_warm:.4f}s / 0 weitere evaluate()-Aufrufe "
        f"(Speedup {t_cold / max(t_warm, 1e-9):.1f}x)"
    )
