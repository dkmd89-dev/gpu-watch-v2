"""Tests fuer die fees-Extraktion in matcher.load_rules() (Reselling-/
Arbitrage-Konzept, siehe STATUS.md Abschnitt 16). Analog zu den bestehenden
manufacturer_reputation-Tests in test_matcher_deal_score_integration.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules


def test_load_rules_liest_fees_aus_global_yaml():
    cfg = load_rules(RULES_DIR)
    assert "fees" in cfg
    assert cfg["fees"]["platform_fee_pct"] == 10.0
    assert cfg["fees"]["payment_fee_pct"] == 2.5
    assert cfg["fees"]["shipping_cost"] == 6.0
    assert cfg["fees"]["packaging_cost"] == 1.5


def test_load_rules_ohne_fees_sektion_liefert_leeres_dict(tmp_path):
    (tmp_path / "_global.yaml").write_text(
        "defaults:\n  min_vram_gb: 12\n", encoding="utf-8"
    )
    (tmp_path / "dummy.yaml").write_text(
        "category: dummy\nrules: []\n", encoding="utf-8"
    )
    cfg = load_rules(str(tmp_path))
    assert cfg["fees"] == {}


def test_load_rules_legacy_einzeldatei_modus_kein_fees_crash():
    fixture = str(
        Path(__file__).resolve().parent / "fixtures" / "legacy_single_file_rules.yaml"
    )
    cfg = load_rules(fixture)
    # Legacy-Modus extrahiert "fees" nicht explizit (kein _load_rules_from_dir-
    # Pfad) -- der Key ist hier schlicht nicht vorhanden. Wichtig ist nur,
    # dass das Laden nicht crasht (Rueckwaertskompatibilitaet).
    assert isinstance(cfg, dict)
