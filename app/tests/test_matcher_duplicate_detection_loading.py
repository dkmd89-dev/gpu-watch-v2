"""Tests fuer die duplicate_detection-Extraktion in matcher.load_rules()
(STATUS.md Abschnitt 16, Baustein 5, Folgeschritt). Analog zu den
bestehenden fees-Tests in test_matcher_fees_loading.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules


def test_load_rules_liest_duplicate_detection_aus_global_yaml():
    cfg = load_rules(RULES_DIR)
    assert "duplicate_detection" in cfg
    assert cfg["duplicate_detection"]["price_tolerance_pct"] == 5.0
    assert cfg["duplicate_detection"]["window_days"] == 30.0


def test_load_rules_ohne_duplicate_detection_sektion_liefert_leeres_dict(tmp_path):
    (tmp_path / "_global.yaml").write_text(
        "defaults:\n  min_vram_gb: 12\n", encoding="utf-8"
    )
    (tmp_path / "dummy.yaml").write_text(
        "category: dummy\nrules: []\n", encoding="utf-8"
    )
    cfg = load_rules(str(tmp_path))
    assert cfg["duplicate_detection"] == {}


def test_load_rules_legacy_einzeldatei_modus_kein_duplicate_detection_crash():
    fixture = str(
        Path(__file__).resolve().parent / "fixtures" / "legacy_single_file_rules.yaml"
    )
    cfg = load_rules(fixture)
    # Legacy-Modus extrahiert "duplicate_detection" nicht explizit (kein
    # _load_rules_from_dir-Pfad) -- der Key ist hier schlicht nicht
    # vorhanden. Wichtig ist nur, dass das Laden nicht crasht.
    assert isinstance(cfg, dict)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
