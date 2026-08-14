"""Regressionstest für den Nebenbefund aus test_gpu_rx7600_vram_fix.py
(STATUS.md Datenqualität Nr. 4, Folgeschritt 2026-08-15).

Derselbe min_vram_gb-Bug wie bei RX 7600 betraf strukturell 4 weitere
GPU-Modelle ohne eigenes min_vram_gb, deren reale VRAM-Größe unter dem
globalen Default (_global.yaml, min_vram_gb: 12) liegt:

  rtx_3060_ti  8GB   (110 historische + 12 aktuelle price_history-Punkte)
  rtx_3070     8GB   (149 historische + 16 aktuelle Punkte)
  rtx_4060     8GB   (29 historische + 4 aktuelle Punkte)
  rtx_2080_ti  11GB  (60 historische + 3 aktuelle Punkte)

Jedes Angebot mit der (weit häufigeren) Schreibweise "8GB"/"11GB" statt
"8G"/"11G" wurde durch matcher.py::_vram_gb() (Regex "(\\d{1,2})\\s*gb")
fälschlich als zu VRAM-schwach verworfen. Fix: min_vram_gb: 0 explizit je
Regel gesetzt (match-Begriffe bereits eindeutig modellspezifisch, kein
Kollisionsrisiko).

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


def test_rtx_3060_ti_mit_8gb_schreibweise_matcht_jetzt():
    for title, price in [
        ("AORUS GeForce RTX 3060 Ti Elite 8GB -- OVP", 200.0),
        ("MSI RTX 3060Ti Gaming X Trio 8GB Grafikkarte", 210.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.price_history_model == "rtx_3060_ti", title


def test_rtx_3070_mit_8gb_schreibweise_matcht_jetzt():
    r = evaluate("MSI GeForce RTX 3070 Gaming Z Trio 8GB LHR", 250.0, _rules_cfg())
    assert r.matched is True and r.price_history_model == "rtx_3070"


def test_rtx_4060_mit_8gb_schreibweise_matcht_jetzt():
    r = evaluate("Asus RTX 4060 Dual OC 8GB", 250.0, _rules_cfg())
    assert r.matched is True and r.price_history_model == "rtx_4060"


def test_rtx_2080_ti_mit_11gb_schreibweise_matcht_jetzt():
    r = evaluate("Zotac RTX 2080 Ti AMP 11GB", 250.0, _rules_cfg())
    assert r.matched is True and r.price_history_model == "rtx_2080_ti"


def test_g_schreibweise_matcht_weiterhin():
    # Bestehendes Verhalten (Schreibweise "8G" statt "8GB") darf nicht
    # regressieren.
    for title, price, expected_model in [
        ("AORUS GeForce RTX 3060 Ti Elite 8G -- OVP", 200.0, "rtx_3060_ti"),
        ("MSI GeForce RTX 3070 Gaming Z Trio 8G LHR", 250.0, "rtx_3070"),
        ("Asus RTX 4060 Dual OC 8G", 250.0, "rtx_4060"),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.price_history_model == expected_model, title


def test_benachbarte_modelle_bleiben_ueber_exclude_getrennt():
    # Kollisions-Sicherheitsnetz: die bestehenden exclude-Listen (3070 Ti,
    # 4060 Ti, 2080 Super) duerfen durch min_vram_gb: 0 nicht unterlaufen
    # werden -- diese Karten haben teils selbst < 12GB VRAM und wuerden
    # ohne funktionierenden Exclude faelschlich mitmatchen.
    for title, price in [
        ("MSI RTX 3070 Ti Gaming X Trio 8GB", 300.0),
        ("Asus RTX 4060 Ti Dual OC 8GB", 250.0),
        ("Zotac RTX 2080 Super AMP 8GB", 250.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is False, title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
