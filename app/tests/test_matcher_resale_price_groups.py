"""Tests fuer das resale_price_groups-Mapping (Option 2, "Flip-Kandidaten-
Logik optimieren", STATUS.md Abschnitt 33b).

Analog zu test_matcher_part_out.py::test_mapping_tabelle_wird_geladen --
prueft gegen die echte rules/-Konfiguration, da das Mapping ausschliesslich
dort (in den einzelnen Kategorie-YAMLs ueber den optionalen Key
"resale_price_group") gepflegt wird.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules


def test_resale_price_groups_key_vorhanden():
    cfg = load_rules(RULES_DIR)
    assert "resale_price_groups" in cfg
    assert isinstance(cfg["resale_price_groups"], dict)


def test_lego_regeln_ohne_eigene_gruppe_bilden_sich_selbst_ab():
    cfg = load_rules(RULES_DIR)
    mapping = cfg["resale_price_groups"]
    # lego_sw_rare/lego_cmf haben bewusst KEINEN resale_price_group
    # (siehe rules/lego_minifiguren.yaml-Kommentar) -> Identitaet.
    assert mapping["lego_sw_rare"] == "lego_sw_rare"
    assert mapping["lego_cmf"] == "lego_cmf"


def test_lego_rare_minifig_regeln_teilen_sich_gemeinsame_gruppe():
    cfg = load_rules(RULES_DIR)
    mapping = cfg["resale_price_groups"]
    for model in (
        "lego_sw_clone", "lego_ninjago_rare", "lego_promo",
        "lego_superhero_rare", "lego_fantasy_rare", "lego_retro_rare",
        "lego_collector_generic",
    ):
        assert mapping[model] == "lego_rare_minifig_common"


def test_lego_bundle_regeln_teilen_sich_gemeinsame_gruppe():
    cfg = load_rules(RULES_DIR)
    mapping = cfg["resale_price_groups"]
    assert mapping["lego_ninjago_bundle"] == "lego_bundle_common"
    assert mapping["lego_minifig_bundle"] == "lego_bundle_common"


def test_retro_konsolen_einzelgeraete_teilen_sich_gemeinsame_gruppe():
    cfg = load_rules(RULES_DIR)
    mapping = cfg["resale_price_groups"]
    assert mapping["nintendo_retro_konsole"] == "retro_konsole_single"
    assert mapping["sony_retro_konsole"] == "retro_konsole_single"
    # Konvolut bewusst NICHT einbezogen (siehe rules/retro_konsolen.yaml).
    assert mapping["retro_konvolut"] == "retro_konvolut"


def test_gpu_regeln_ohne_resale_price_group_bilden_sich_selbst_ab():
    # Regressionsschutz: Kategorien, die den neuen Key gar nicht kennen
    # (z.B. gpu.yaml), bleiben unveraendert -- jede Regel bildet weiterhin
    # nur sich selbst ab.
    cfg = load_rules(RULES_DIR)
    mapping = cfg["resale_price_groups"]
    assert mapping["rtx_3060_12gb"] == "rtx_3060_12gb"
