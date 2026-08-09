"""Tests für matcher.compute_ruleset_signature() (Phase 11, Punkt B:
sichere Re-Evaluierung bei geänderten/neuen Kategorien)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import compute_ruleset_signature


def _cfg(rules):
    return {"rules": rules}


def test_gleiches_regelwerk_liefert_gleichen_hash():
    cfg = _cfg([{"label": "A", "_category": "gpu", "max_price": 200}])
    assert compute_ruleset_signature(cfg) == compute_ruleset_signature(cfg)


def test_neue_regel_aendert_den_hash():
    cfg_alt = _cfg([{"label": "A", "_category": "gpu", "max_price": 200}])
    cfg_neu = _cfg([
        {"label": "A", "_category": "gpu", "max_price": 200},
        {"label": "B", "_category": "cpu_mainboard_bundle", "max_price": 150},
    ])
    assert compute_ruleset_signature(cfg_alt) != compute_ruleset_signature(cfg_neu)


def test_geaenderte_max_price_aendert_den_hash():
    cfg_alt = _cfg([{"label": "A", "_category": "gpu", "max_price": 200}])
    cfg_neu = _cfg([{"label": "A", "_category": "gpu", "max_price": 250}])
    assert compute_ruleset_signature(cfg_alt) != compute_ruleset_signature(cfg_neu)


def test_geaenderte_require_all_of_aendert_den_hash():
    cfg_alt = _cfg([{"label": "A", "require_all_of": [["ryzen 5 3600"]]}])
    cfg_neu = _cfg([{"label": "A", "require_all_of": [["ryzen 5 3600", "r5 3600x"]]}])
    assert compute_ruleset_signature(cfg_alt) != compute_ruleset_signature(cfg_neu)


def test_kosmetische_notify_max_price_aenderung_aendert_hash_nicht():
    # notify_max_price beeinflusst evaluate() nicht (Kategorie-Feld fürs
    # Notification-Gate, siehe app.py), gehört bewusst nicht zu den
    # matching-relevanten Feldern.
    cfg_alt = _cfg([{"label": "A", "_category": "gpu", "notify_max_price": 100}])
    cfg_neu = _cfg([{"label": "A", "_category": "gpu", "notify_max_price": 999}])
    assert compute_ruleset_signature(cfg_alt) == compute_ruleset_signature(cfg_neu)


def test_kosmetische_deal_rating_aenderung_aendert_hash_nicht():
    cfg_alt = _cfg([{"label": "A", "_category": "gpu", "deal_rating": "Top-Deal"}])
    cfg_neu = _cfg([{"label": "A", "_category": "gpu", "deal_rating": "Guter Preis"}])
    assert compute_ruleset_signature(cfg_alt) == compute_ruleset_signature(cfg_neu)


def test_leeres_regelwerk_liefert_stabilen_hash():
    h1 = compute_ruleset_signature(_cfg([]))
    h2 = compute_ruleset_signature(_cfg([]))
    assert h1 == h2
    assert isinstance(h1, str) and len(h1) > 0


def test_reihenfolge_der_regeln_aendert_den_hash():
    # Bewusst: die Prioritaetsreihenfolge der Regeln beeinflusst evaluate()
    # (first-match-wins) -- eine reine Reihenfolge-Aenderung MUSS den Hash
    # aendern, auch wenn dieselben Regeln enthalten sind.
    cfg_a = _cfg([{"label": "A", "max_price": 100}, {"label": "B", "max_price": 200}])
    cfg_b = _cfg([{"label": "B", "max_price": 200}, {"label": "A", "max_price": 100}])
    assert compute_ruleset_signature(cfg_a) != compute_ruleset_signature(cfg_b)


# ============================================================
# Phase 15 (kontrollierter Review, "Variante C"): kontextbewusster
# Exclude-Gegenpart (_category_exclude_unless_preceded_by) MUSS in die
# Signatur einfliessen -- eine Aenderung ausschliesslich an einer
# Konnektor-Liste veraendert das Match-Verhalten von evaluate() (siehe
# matcher.py::_any_conditional_exclude()), muss also erkannt werden.
# ============================================================

def test_neues_feld_exclude_unless_preceded_by_aendert_den_hash():
    # 1. Ruleset laden (hier: synthetisch aufgebaut, analog zu allen
    #    anderen Tests in dieser Datei) 2. Signature berechnen.
    cfg_ohne_feld = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {},
    }])
    hash_ohne_feld = compute_ruleset_signature(cfg_ohne_feld)

    cfg_mit_feld = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {"ladekabel": ["inkl.", "mit"]},
    }])
    hash_mit_feld = compute_ruleset_signature(cfg_mit_feld)

    assert hash_ohne_feld != hash_mit_feld


def test_ausschliesslich_konnektor_liste_veraendert_aendert_den_hash():
    # 3. AUSSCHLIESSLICH eine Konnektor-Liste veraendern (alles andere --
    #    Begriff, Regel, Kategorie -- bleibt identisch).
    cfg_alt = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {"ladekabel": ["inkl.", "mit"]},
    }])
    hash_alt = compute_ruleset_signature(cfg_alt)

    cfg_neu = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {"ladekabel": ["inkl.", "mit", "und"]},
    }])
    # 4. Signature erneut berechnen.
    hash_neu = compute_ruleset_signature(cfg_neu)

    # 5. Assertion: Signature MUSS sich aendern.
    assert hash_alt != hash_neu


def test_neuer_begriff_im_conditional_exclude_aendert_den_hash():
    cfg_alt = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {"ladekabel": ["inkl.", "mit"]},
    }])
    cfg_neu = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {
            "ladekabel": ["inkl.", "mit"], "netzteil": ["inkl.", "mit"],
        },
    }])
    assert compute_ruleset_signature(cfg_alt) != compute_ruleset_signature(cfg_neu)


def test_unveraendertes_conditional_exclude_liefert_gleichen_hash():
    cfg_a = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {"ladekabel": ["inkl.", "mit"]},
    }])
    cfg_b = _cfg([{
        "label": "A", "_category": "controller",
        "_category_exclude_unless_preceded_by": {"ladekabel": ["inkl.", "mit"]},
    }])
    assert compute_ruleset_signature(cfg_a) == compute_ruleset_signature(cfg_b)


# ============================================================
# Phase 15 (kontrollierter Folge-Review, "Gehäuse/Shell-Fix"): zweiter
# kontextbewusster Exclude-Gegenpart (_category_exclude_unless_also_
# contains) MUSS ebenfalls in die Signatur einfliessen -- eine Aenderung
# an der Kontextbegriffsliste veraendert das Match-Verhalten von
# evaluate() (siehe matcher.py::_any_conditional_exclude_presence()).
# ============================================================

def test_neues_feld_exclude_unless_also_contains_aendert_den_hash():
    cfg_ohne_feld = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {},
    }])
    hash_ohne_feld = compute_ruleset_signature(cfg_ohne_feld)

    cfg_mit_feld = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {"gehäuse": ["vergilbt", "verkratzt"]},
    }])
    hash_mit_feld = compute_ruleset_signature(cfg_mit_feld)

    assert hash_ohne_feld != hash_mit_feld


def test_ausschliesslich_kontextbegriffsliste_veraendert_aendert_den_hash():
    cfg_alt = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {"gehäuse": ["vergilbt", "verkratzt"]},
    }])
    hash_alt = compute_ruleset_signature(cfg_alt)

    cfg_neu = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {
            "gehäuse": ["vergilbt", "verkratzt", "neuwertig"],
        },
    }])
    hash_neu = compute_ruleset_signature(cfg_neu)

    assert hash_alt != hash_neu


def test_neuer_begriff_im_unless_also_contains_dict_aendert_den_hash():
    cfg_alt = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {"gehäuse": ["vergilbt"]},
    }])
    cfg_neu = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {
            "gehäuse": ["vergilbt"], "shell": ["scratched"],
        },
    }])
    assert compute_ruleset_signature(cfg_alt) != compute_ruleset_signature(cfg_neu)


def test_unveraendertes_unless_also_contains_liefert_gleichen_hash():
    cfg_a = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {"gehäuse": ["vergilbt"]},
    }])
    cfg_b = _cfg([{
        "label": "A", "_category": "handhelds",
        "_category_exclude_unless_also_contains": {"gehäuse": ["vergilbt"]},
    }])
    assert compute_ruleset_signature(cfg_a) == compute_ruleset_signature(cfg_b)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
