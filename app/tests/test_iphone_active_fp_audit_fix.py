"""Regressionstest für den iphone-Fix aus dem Active-False-Positive-Audit
(docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: kein Fehltreffer über eine Ambiguität im Matching, sondern
ein leeres Verpackungs-Sammlerangebot ohne Gerät -- identisches Muster
wie bereits in handhelds.yaml gelöst ("leere box"). Real bestätigt
gegen found.json (1 Titel im vollständigen Korpus): "Titel: Leere
Originalverpackung Apple iPhone 11 - 128GB - Schwarz (Black)" (5€ --
Preis allein schon ein starkes Indiz gegen ein echtes Gerät), matchte
bisher als "iPhone 11 (≤256GB) ★ Top-Deal".

Fix: 1 neue bare-phrase exclude_category-Ergänzung ("leere
originalverpackung").

Bewusst NICHT Teil dieses Fixes (siehe Audit-Doku, P2/NO-FIX): 2 Titel
mit "Zubehörpaket" -- gegensätzliche Fälle im Korpus (einer mit
Akku-Prozentangabe, klar ein echtes Gerät mit Bonus-Zubehör; einer ganz
ohne Zustandsangabe, könnte ein reines Zubehörpaket ohne Gerät sein).
Kein sicheres Unterscheidungsmerkmal ohne Beschreibungstext, zu wenig
Evidenz (n=1 je Fall) für eine verallgemeinerbare Regel.

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


def _matches_iphone(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "iphone"


# ============================================================
# 1. Real bestätigter Fehltreffer -- muss jetzt blockiert werden.
# ============================================================

def test_leere_originalverpackung_matcht_nicht():
    assert _matches_iphone(
        "Titel: Leere Originalverpackung Apple iPhone 11 - 128GB - Schwarz (Black)",
        5.0,
    ) is False


# ============================================================
# 2. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel mit "OVP"/
#    "Verpackung" im Kontext eines echten Geräts bleiben erhalten.
# ============================================================

def test_reale_true_positives_mit_ovp_matchen_weiterhin():
    for title, price in [
        ("iPhone 12 Blau 64gb mit OVP und Ladekabel", 135.0),
        ("iPhone 11 - 64GB - Grün - Inkl. Hülle, Displayschutz & OVP", 120.0),
        ("Apple iPhone 12 mini 128 GB Schwarz in OVP", 110.0),
        ("iPhone 16 Pro 128 GB Titan Weiß | Top Zustand | OVP + Rechnung", 650.0),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "iphone", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
