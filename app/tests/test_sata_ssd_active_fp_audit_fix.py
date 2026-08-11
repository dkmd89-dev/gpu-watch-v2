"""Regressionstest für den sata_ssd-Fix aus dem Active-False-Positive-
Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: "externe festplatte"/"externes gehaeuse" deckten nur
diese beiden exakten Phrasen ab -- externe USB-SSDs mit anderer
Formulierung ("Portable SSD", "Externer Speicher") matchten weiterhin
fälschlich als interne 2.5" SATA-SSD. Real bestätigt gegen found.json
(3 Titel im vollständigen 75-Titel-Match-Korpus).

Fix: 2 neue exclude_category-Terme ("portable", "externer speicher").

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


def _matches_sata_ssd(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "sata_ssd"


# ============================================================
# 1. Real bestätigte Fehltreffer -- müssen jetzt blockiert werden.
# ============================================================

def test_externe_usb_ssds_matchen_nicht():
    for title, price in [
        ("SanDisk Portable SSD 1 TB Speicher", 65.0),
        (
            "Seagate Expansion SSD, 500GB, Portable External Solid State Drive for PC and Mac",
            54.95,
        ),
        ("SSK Pro 1TB SSD Externer Speicher USB-Stick", 70.0),
    ]:
        assert _matches_sata_ssd(title, price) is False, title


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel bleiben erhalten.
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Crucial MX500 500GB SSD 2.5\" SATA III Getestet – Einwandfrei CT500MX500SSD1", 35.99),
        ("Samsung 860 EVO 500GB SSD Festplatte", 35.0),
        ("WD Blue SATA SSD 500 GB Solid State Drive", 35.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "sata_ssd", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
