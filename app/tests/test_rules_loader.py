"""Tests für rules_loader.py (Phase 15, Schritt 6 -- Rules-Cache, siehe
PHASE15_OPTIMIERUNG.md Abschnitte 19-21).

Isolation: rules_loader._cache ist Modul-Level-State (wie
category_validation._validity_cache, siehe
test_category_validation_cache.py) -- ein autouse-Fixture leert ihn vor
UND nach jedem Test.

Läuft gegen ein temporäres, minimales Regelverzeichnis (tmp_path), nicht
gegen die echten rules/*.yaml -- Schritt 6 prüft ausschließlich das
CACHE-VERHALTEN (Hit/Miss/Invalidierung bei Dateiänderung), nicht die
fachliche Matcher-Semantik (dafür: test_matcher_*.py/test_rule_*.py)."""
import os
import sys
import time
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matcher
import rules_loader
from rules_loader import get_rules, get_ruleset_hash, invalidate


@pytest.fixture(autouse=True)
def _clear_cache():
    rules_loader.invalidate()
    yield
    rules_loader.invalidate()


def _write_minimal_ruleset(rules_dir: Path, term: str = "testterm") -> None:
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "_global.yaml").write_text(
        "defaults:\n  min_vram_gb: 0\n", encoding="utf-8"
    )
    (rules_dir / "testcat.yaml").write_text(
        f"""category: "testcat"
label: "Test Category"
rules:
  - label: "Test Rule"
    match: ["{term}"]
    price_history_model: "test_model"
    max_price: 100
""",
        encoding="utf-8",
    )


def _touch_forward(path: Path, seconds: float = 2.0) -> None:
    """Setzt mtime eindeutig in die Zukunft (verhindert Flakes durch
    Dateisystem-Aufloesung/Test-Ausfuehrungsgeschwindigkeit < 1s)."""
    st = path.stat()
    new_time = st.st_mtime + seconds
    os.utime(path, (new_time, new_time))


def _count_load_rules_calls(monkeypatch):
    calls = {"n": 0}
    original = rules_loader.load_rules

    def counting_load_rules(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(rules_loader, "load_rules", counting_load_rules)
    return calls


# ============================================================
# Cache Hit / Miss (Auftrag Abschnitt 21)
# ============================================================

def test_erster_load_parst_yaml(tmp_path, monkeypatch):
    calls = _count_load_rules_calls(monkeypatch)
    _write_minimal_ruleset(tmp_path)

    cfg = get_rules(str(tmp_path))

    assert calls["n"] == 1
    assert len(cfg["rules"]) == 1
    assert cfg["rules"][0]["price_history_model"] == "test_model"


def test_zweiter_load_ist_cache_hit(tmp_path, monkeypatch):
    _write_minimal_ruleset(tmp_path)
    get_rules(str(tmp_path))  # cold

    calls = _count_load_rules_calls(monkeypatch)
    get_rules(str(tmp_path))  # sollte NICHT erneut parsen

    assert calls["n"] == 0


def test_unveraendertes_ruleset_mehrfach_hintereinander_bleibt_cache_hit(tmp_path, monkeypatch):
    _write_minimal_ruleset(tmp_path)
    get_rules(str(tmp_path))

    calls = _count_load_rules_calls(monkeypatch)
    for _ in range(10):
        get_rules(str(tmp_path))

    assert calls["n"] == 0


def test_yaml_inhaltlich_veraendert_ist_cache_miss(tmp_path, monkeypatch):
    _write_minimal_ruleset(tmp_path, term="altbegriff")
    cfg_alt = get_rules(str(tmp_path))
    assert cfg_alt["rules"][0]["match"] == ["altbegriff"]

    _write_minimal_ruleset(tmp_path, term="neubegriff")
    _touch_forward(tmp_path / "testcat.yaml")

    calls = _count_load_rules_calls(monkeypatch)
    cfg_neu = get_rules(str(tmp_path))

    assert calls["n"] == 1  # Cache Miss -- neu geparst
    assert cfg_neu["rules"][0]["match"] == ["neubegriff"]


def test_neue_yaml_datei_hinzugefuegt_ist_cache_miss(tmp_path, monkeypatch):
    _write_minimal_ruleset(tmp_path)
    get_rules(str(tmp_path))

    (tmp_path / "zweite_kategorie.yaml").write_text(
        'category: "zweite"\nlabel: "Zweite Kategorie"\nrules:\n'
        '  - label: "R2"\n    match: ["zweiterbegriff"]\n    max_price: 50\n',
        encoding="utf-8",
    )
    _touch_forward(tmp_path)  # neue Datei -> Verzeichnis-Fingerabdruck aendert sich

    calls = _count_load_rules_calls(monkeypatch)
    cfg = get_rules(str(tmp_path))

    assert calls["n"] == 1
    assert len(cfg["rules"]) == 2


# ============================================================
# Ruleset-Signatur (Auftrag: "mit compute_ruleset_signature() arbeiten,
# keine zweite Hash-Implementierung")
# ============================================================

def test_ruleset_signature_aendert_sich_bei_inhaltlicher_aenderung(tmp_path):
    _write_minimal_ruleset(tmp_path, term="altbegriff")
    hash_alt = get_ruleset_hash(str(tmp_path))

    _write_minimal_ruleset(tmp_path, term="neubegriff")
    _touch_forward(tmp_path / "testcat.yaml")
    hash_neu = get_ruleset_hash(str(tmp_path))

    assert hash_alt != hash_neu


def test_gleiches_ruleset_kein_hash_wechsel_trotz_datei_touch(tmp_path, monkeypatch):
    # "gleiches Ruleset -> kein Reload" (Auftrag Abschnitt 21): eine Datei
    # wird beruehrt (mtime aendert sich -> Cache muss neu parsen), der
    # INHALT bleibt aber identisch -- aus Sicht von Aufrufern, die nur den
    # Hash zum Vergleich nutzen (presence_tracking/category_validation),
    # aendert sich dadurch NICHTS (kein wahrgenommener Ruleset-Wechsel).
    _write_minimal_ruleset(tmp_path, term="unveraendert")
    hash_alt = get_ruleset_hash(str(tmp_path))

    _touch_forward(tmp_path / "testcat.yaml")  # nur mtime, Inhalt gleich
    calls = _count_load_rules_calls(monkeypatch)
    hash_neu = get_ruleset_hash(str(tmp_path))

    assert calls["n"] == 1  # intern wurde neu geparst (mtime-Aenderung)
    assert hash_alt == hash_neu  # aber die Signatur ist unveraendert


def test_get_ruleset_hash_nutzt_compute_ruleset_signature_ohne_neuberechnung(tmp_path, monkeypatch):
    _write_minimal_ruleset(tmp_path)
    get_rules(str(tmp_path))

    calls = {"n": 0}
    original = rules_loader.compute_ruleset_signature

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(rules_loader, "compute_ruleset_signature", counting)

    get_ruleset_hash(str(tmp_path))
    get_ruleset_hash(str(tmp_path))
    get_ruleset_hash(str(tmp_path))

    assert calls["n"] == 0  # Cache-Hit -- keine erneute Hash-Berechnung


# ============================================================
# invalidate()
# ============================================================

def test_invalidate_erzwingt_reload(tmp_path, monkeypatch):
    _write_minimal_ruleset(tmp_path)
    get_rules(str(tmp_path))

    invalidate(str(tmp_path))

    calls = _count_load_rules_calls(monkeypatch)
    get_rules(str(tmp_path))
    assert calls["n"] == 1


def test_invalidate_ohne_pfad_leert_gesamten_cache(tmp_path, monkeypatch):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    _write_minimal_ruleset(dir_a)
    _write_minimal_ruleset(dir_b)
    get_rules(str(dir_a))
    get_rules(str(dir_b))

    invalidate()

    calls = _count_load_rules_calls(monkeypatch)
    get_rules(str(dir_a))
    get_rules(str(dir_b))
    assert calls["n"] == 2


# ============================================================
# Thread-Sicherheit (Auftrag Abschnitt 20)
# ============================================================

def test_parallele_zugriffe_liefern_konsistentes_ergebnis(tmp_path):
    _write_minimal_ruleset(tmp_path)
    results = []
    errors = []

    def worker():
        try:
            results.append(get_rules(str(tmp_path)))
        except Exception as e:  # pragma: no cover
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(results) == 20
    assert all(r["rules"][0]["price_history_model"] == "test_model" for r in results)


# ============================================================
# Verhalten bleibt identisch zu ungecachtem matcher.load_rules()
# ============================================================

def test_ergebnis_identisch_zu_ungecachtem_load_rules(tmp_path):
    _write_minimal_ruleset(tmp_path)
    direct = matcher.load_rules(str(tmp_path))
    cached = get_rules(str(tmp_path))
    assert direct == cached


if __name__ == "__main__":
    import pytest as _pytest
    raise SystemExit(_pytest.main([__file__, "-v"]))
