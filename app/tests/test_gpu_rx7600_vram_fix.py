"""Regressionstest für STATUS.md Datenqualität Nr. 4 ("RX 7600 XT/RX 7600-
Überlappung", 2026-08-15 final untersucht).

Die ursprüngliche Match-Präzedenz-Überlappung ("rx 7600" fälschlich als
match-Begriff der XT-Regel) war bereits in einer früheren Phase-15-Session
gefixt (siehe Kommentar bei "RX 7600 XT" in gpu.yaml). Die verbleibende,
jetzt gefundene Ursache für die weiterhin sehr dünne rx_7600-Datenlage
(price_history.jsonl: nur 1 Punkt) ist ein ANDERER, eigenständiger Bug:
Ohne eigenes `min_vram_gb` fielen die beiden RX-7600-Regeln auf den
globalen Default zurück (_global.yaml, min_vram_gb: 12) -- die RX 7600 hat
aber nur 8GB VRAM. matcher.py::_vram_gb() erkennt "8GB" im Titel (Regex
"(\\d{1,2})\\s*gb"), aber NICHT "8G" -- jedes Angebot mit der (weit
häufigeren) Schreibweise "8GB" wurde dadurch fälschlich verworfen.

Wichtiger Nebenbefund: derselbe Bug betraf strukturell auch rtx_3060_ti,
rtx_3070, rtx_4060 und rtx_2080_ti (alle VRAM < 12GB, kein eigenes
min_vram_gb) -- direkt im Anschluss ebenfalls gefixt, siehe
test_gpu_low_vram_models_fix.py.

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


def test_rx_7600_mit_8gb_schreibweise_matcht_jetzt():
    for title, price in [
        ("AMD Radeon MSI RX 7600 MECH 2X CLASSIC 8GB OC | OVP", 180.0),
        ("Sapphire Pulse RX 7600 8GB Grafikkarte", 150.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.price_history_model == "rx_7600", title


def test_rx_7600_mit_8g_schreibweise_matcht_weiterhin():
    r = evaluate(
        "AMD Radeon MSI RX 7600 MECH 2X CLASSIC 8G OC | OVP", 180.0, _rules_cfg()
    )
    assert r.matched is True and r.price_history_model == "rx_7600"


def test_rx_7600_xt_matcht_weiterhin_korrekt_als_xt():
    for title, price in [
        ("MSI RX 7600 XT Gaming", 150.0),
        ("AMD Radeon RX 7600XT 16GB Steel Legend Edition Grafikkarte", 230.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.price_history_model == "rx_7600_xt", title


def test_rx_7600_non_xt_matcht_nicht_als_xt():
    # Kollisions-Sicherheitsnetz: die urspruengliche Match-Praezedenz-
    # Ueberlappung (bereits vor dieser Session gefixt) darf nicht
    # zurueckkehren.
    r = evaluate("Sapphire Pulse RX 7600 8GB Grafikkarte", 150.0, _rules_cfg())
    assert r.price_history_model != "rx_7600_xt"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
