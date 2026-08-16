"""Regressionstests für den Profit-Matching-Root-Cause-Audit (2026-08-16):
drei unabhängige, im Resale-/Profit-Audit gefundene LIVE-Fehltreffer, die
die Margen-/Flip-Aussagekraft direkt verzerrten (margin_pct 543%-841%).

Drei technisch unabhängige Root Causes (siehe jeweiliger YAML-Kommentar):

- Cluster A (konsolen_bundles): "pro" ist sowohl require_all_of-Signal als
  auch Verstärkungsmarker des "spiele"-Kontext-Guards -- kollidiert mit der
  deutschen Präposition "pro" ("je Stück"), nicht nur mit "PS4 Pro". Fix:
  spezifische Phrase "pro stück" als bare exclude_category-Eintrag.
- Cluster B (vintage_elektronik): require_all_of unterscheidet nicht
  zwischen einem echten Verstärker und einem Zeitschriften-/Heft-Konvolut,
  das nur ÜBER Verstärker berichtet. Fix: "hefte" als bare
  exclude_category-Eintrag (identisches Muster wie die bereits
  vorhandenen Sammler-/Dokumentations-Excludes "foto"/"funktionsbeschreibung").
- Cluster C (monitor_curved): "Teildefekt" (Kompositum) wird vom globalen
  "defekt"-Exclude wegen fehlender Wortgrenze nicht erfasst. Fix: lokaler
  exclude_category-Eintrag NUR in monitor_curved.yaml (bewusst NICHT
  global in rules/_global.yaml, da "teildefekt" in 2 anderen Kategorien
  (iphone, retro_konsolen) als TRUE_POSITIVE gilt -- siehe Cross-Kategorie-
  Regressionstest unten).

Bekannter, bewusst akzeptierter Ground-Truth-Konflikt (siehe Cluster-A-
Kommentar in konsolen_bundles.yaml): 2 in docs/DASHBOARD_MATCH_FORENSICS.json
als TRUE_POSITIVE gelabelte Fälle ("Ps4 Spiele Einzelverkauf 7€ pro
Stück.", "Ps4 Spiele gebraucht 10€ pro Stück") matchen durch diesen Fix
ebenfalls nicht mehr -- inhaltlich eindeutig Spiele-Einzelverkäufe, kein
Konsolenangebot, vermutlich Label-Fehler analog zum bereits dokumentierten
Switch/Xbox-Ground-Truth-Artefakt (Batch 20b). Die Ground-Truth-Datei
selbst bleibt unverändert.

Läuft gegen die echten, produktiven rules/*.yaml."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


# ---------------------------------------------------------------
# Cluster A -- konsolen_bundles: "pro Stück"
# ---------------------------------------------------------------

def test_cluster_a_ps4_spiele_pro_stueck_matcht_nicht():
    r = evaluate("PS4 Spiele 10€ pro Stück", 10.0, _rules_cfg())
    assert not (r.matched and r.category == "konsolen_bundles")


def test_cluster_a_bekannte_ground_truth_konflikt_faelle_matchen_nicht_mehr():
    # Bewusst akzeptierter Ground-Truth-Konflikt (siehe Moduldocstring) --
    # beide Titel sind inhaltlich Spiele-Einzelverkaeufe, keine Konsole.
    for title, price in [
        ("Ps4 Spiele Einzelverkauf 7€ pro Stück.", 7.0),
        ("Ps4 Spiele gebraucht 10€ pro Stück", 10.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert not (r.matched and r.category == "konsolen_bundles"), title


def test_cluster_a_reale_ps4_pro_konsole_matcht_weiterhin():
    for title, price in [
        ("PS4 Pro 1TB Konsole mit 2 Controllern", 100.0),
        ("Sony Playstation 4 Pro 1TB inkl. Spiele", 100.0),
        ("PS4 Slim 500GB Konsole komplett", 90.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "konsolen_bundles", title


# ---------------------------------------------------------------
# Cluster B -- vintage_elektronik: "Hefte"
# ---------------------------------------------------------------

def test_cluster_b_hifi_hefte_konvolut_matcht_nicht():
    r = evaluate("Image hifi Hefte Röhrenverstärker 6 Hefte", 20.0, _rules_cfg())
    assert not (r.matched and r.category == "vintage_elektronik")


def test_cluster_b_reale_roehrenverstaerker_matchen_weiterhin():
    for title, price in [
        ("Sansui Röhrenverstärker Vintage HiFi", 80.0),
        ("Marantz Vollverstärker HiFi Receiver", 90.0),
        ("Pioneer Stereo Verstärker mit Fernbedienung", 70.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "vintage_elektronik", title


# ---------------------------------------------------------------
# Cluster C -- monitor_curved: "Teildefekt"
# ---------------------------------------------------------------

def test_cluster_c_teildefekt_monitor_matcht_nicht():
    r = evaluate(
        "Xiaomi Mi curved Gaming Monitor 34 Zoll Teildefekt", 10.0, _rules_cfg()
    )
    assert not (r.matched and r.category == "monitor_curved")


def test_cluster_c_reale_curved_monitore_matchen_weiterhin():
    for title, price in [
        ("Samsung Curved Gaming Monitor 27 Zoll", 60.0),
        ("AOC Curved Monitor 32 Zoll Full HD", 65.0),
        ("LG Curved Ultrawide Monitor 34 Zoll", 110.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "monitor_curved", title


def test_cluster_c_teildefekt_in_anderen_kategorien_bleibt_unveraendert():
    # Cross-Kategorie-Regressionsschutz: der neue exclude_category-Eintrag
    # ist LOKAL auf monitor_curved beschraenkt -- "teildefekt" gilt in
    # anderen Kategorien laut Ground Truth teils als gueltiger Treffer
    # (siehe Moduldocstring) und darf dort nicht beeinflusst werden.
    r_iphone = evaluate(
        "iPhone 14 Plus 128GB Blau Blue Akkukap.: 100% Teildefekt L83",
        250.0,
        _rules_cfg(),
    )
    assert r_iphone.matched is True and r_iphone.category == "iphone"

    r_retro = evaluate(
        "Sony Playstation 2 PS2 Slim teildefekt mit Controller ohne Kabel",
        20.0,
        _rules_cfg(),
    )
    assert r_retro.matched is True and r_retro.category == "retro_konsolen"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
