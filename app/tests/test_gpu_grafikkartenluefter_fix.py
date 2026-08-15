"""Regressionstest für den gpu-Fix: "grafikkartenlüfter" als bare Exclude
(Nutzer-Meldung 2026-08-15, found.json-Vollanalyse).

Hintergrund: "Grafikkartenlüfter" ist ein Lüfter-Zubehörteil FÜR eine
Grafikkarte, keine Grafikkarte selbst -- real bestätigt: "Grafikkartenlüfter
für MSI RTX 3060 TI GAMING X, RX 6700 XT GAMING-X" (25,95€, Top-Deal).
Bare "lüfter" bewusst NICHT ergänzt -- würde echte Karten mit eigener
Dual-/Custom-Lüfter-Beschreibung fälschlich blockieren.

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


def test_grafikkartenluefter_zubehoer_matcht_nicht():
    r = evaluate(
        "Grafikkartenlüfter für MSI RTX 3060 TI GAMING X, RX 6700 XT GAMING-X",
        25.95,
        _rules_cfg(),
    )
    assert not (r.matched and r.category == "gpu")


def test_echte_karte_mit_eigener_luefter_beschreibung_matcht_weiterhin():
    for title, price in [
        ("Palit RTX 3070 JetStream - Custom Lüfter oder Serie", 299.0),
        ("ZOTAC NVIDIA GeForce RTX 3060 TI Grafikkarte Dual-Lüfter", 201.19),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "gpu", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
