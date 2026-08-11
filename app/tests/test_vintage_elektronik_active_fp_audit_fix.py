"""Regressionstests für den vintage_elektronik-Fix aus dem Active-False-
Positive-Audit (docs/ACTIVE_FALSE_POSITIVE_AUDIT.md).

Hintergrund: Die "Profi-CRT-Monitor"-Regeln (Sony PVM/BVM/Trinitron)
hatten -- anders als die "Röhrenfernseher"-Regeln direkt darunter --
keine Excludes für Ersatzteile/Fernbedienungen. Realer, sehr großer
Fehltreffer-Cluster im vollständigen 108-Titel-Match-Korpus (40 Titel
über 11 Muster), auf Kategorie-Ebene behoben (`exclude_category`) statt
dreifach pro Rating-Stufe der Profi-CRT-Regel dupliziert:

1. Ersatzteile/Zubehör für Sony PVM/BVM (Platine/Transformator/Akku/
   Ladegerät/Chip/Schutzblende/Einbauset/Netzkabel/Adapterkabel).
2. Fernbedienungen (bare + zusammengeschriebene "Ersatzfernbedienung").
3. Subwoofer-ZUBEHÖR für ein Gerät (nicht bare "subwoofer" -- das würde
   einen echten TRUE_POSITIVE-Röhrenverstärker mit Subwoofer-Ausgang
   treffen).
4. Sammler-/Merchandise-/Dokumentations-Artikel ohne Gerät ("- Altes
   Foto"/"- Foto", T-Shirt, Wandhalterung, Kippsicherung, Schulkarte,
   Funktionsbeschreibung, Werbekoffer, SCART-Cinch-Adapter-Konvolut).

Bewusst NICHT Teil dieses Fixes (P2/NO-FIX, siehe Audit-Doku): "SONY IC
VG-469 LXP-P75ST for Sony BVM-20F1 Monitor" -- bare "ic" als 2-Zeichen-
Begriff zu generisch/riskant für einen einzelnen Beleg.

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


def _matches_vintage(title, price):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "vintage_elektronik"


# ============================================================
# 1. Ersatzteile/Zubehör für Sony PVM/BVM -- müssen jetzt blockiert
#    werden.
# ============================================================

def test_pvm_bvm_ersatzteile_matchen_nicht():
    for title, price in [
        ("SONY PVM-14M4U CRT Monitor Transformer Assy Flyback NEW OVP", 199.0),
        (
            "SONY PVM-2030 20“ Zoll CRT Monitor Resistor Assy Widerstandsbaugruppe Widerstand",
            249.0,
        ),
        ("SONY PVM-9020ME CRT Monitor Mounted Circuit Board NEW OVP", 139.0),
        ("2x Li-Ion Akku 95Wh 6600mAh für Sony PVM-9040ME PVM-9042QM", 189.90),
        (
            "Charger für SONY BVM-D9,DSR-501,LMD-650,PVM-5041,PVM-6041,PVM-8040,PVM-8041Q",
            176.20,
        ),
        (
            "2x Sony BVM-2010 BVM-1410 BVM-1415 CXD8069BG Chip Semiconductor NEU NEW",
            99.0,
        ),
        (
            "SONY BKM-23M Protection Panel Schutzvorrichtung Für für Sony BVM-L30 Monitor NEU",
            199.0,
        ),
        ("Sony BVM PVM Monitor Einbauset für 9\" Monitore", 69.0),
        (
            "SCART zu BNC Breakout Adapter Kabel RGB / RGBS für SONY PVM / BVM Monitor CSYNC",
            39.90,
        ),
        (
            "Netzkabel für Sony BVM F250 Monitor Hirose 4 Pin Stecker auf Hirose 4 Pin Buchse",
            45.69,
        ),
    ]:
        assert _matches_vintage(title, price) is False, title


# ============================================================
# 2. Fernbedienungen -- müssen jetzt blockiert werden.
# ============================================================

def test_fernbedienungen_matchen_nicht():
    for title, price in [
        ("Sony Trinitron RM 694 Fernbedienung", 10.0),
        ("Super Ersatzfernbedienung passend für SONY TRINITRON", 15.88),
        ("Sony Trinitron Fernbedienung RM-883 ORIGINAL getestet.", 19.90),
        (
            "Sony PVM Monitor Fernbedienung RM668 für PVM 2130QM & PVM 2730QM *The Cube*",
            85.0,
        ),
    ]:
        assert _matches_vintage(title, price) is False, title


# ============================================================
# 3. Subwoofer-Zubehör -- muss jetzt blockiert werden, bare "subwoofer"
#    bleibt aber unangetastet (Kollisionsschutz siehe Test 5).
# ============================================================

def test_subwoofer_zubehoer_matcht_nicht():
    assert _matches_vintage(
        "Subwoofer von/für  SONY Trinitron KV-E2911A Fernseher", 49.99
    ) is False


# ============================================================
# 4. Sammler-/Merchandise-/Dokumentations-Artikel -- müssen jetzt
#    blockiert werden.
# ============================================================

def test_sammler_und_merchandise_artikel_matchen_nicht():
    for title, price in [
        ("Alter Röhrenfernseher - Stillleben Technik - Altes Foto", 8.90),
        (
            "Fernseher Fernsehsendung Loriot Zeichnung Zeichentrick  Röhrenfernseher - Foto",
            9.90,
        ),
        (
            "Testbild T-Shirt Fernseher Shirt Retro Fun Bildschirm Röhrenfernseher S-5XL",
            16.95,
        ),
        (
            "17\"- 21\" meliconi 42-55 cm TV Fernseher Röhrenfernseher Wandhalterung silber A21",
            9.99,
        ),
        (
            "TV Kippsicherung zum Verschrauben Flachbildfernseher Röhrenfernseher Kippschutz",
            11.99,
        ),
        (
            "Rollkarte Schulkarte Fernsehbildröhre Röhrenfernseher Fernseher Bildröhre",
            20.0,
        ),
        (
            "Philips Service Fernsehgeräte Funktionsbeschreibung 1964/65 Röhrenfernseher",
            25.0,
        ),
        (
            "KENWOOD HiFi Vintage Werbekoffer Aktenkoffer Vertreterkoffer schwarz rot Koffer",
            44.0,
        ),
        (
            "37x  SCART Cinch Adapter Konvolut AV Adapter Retro Gaming VHS TV CRT Fernseher",
            39.90,
        ),
    ]:
        assert _matches_vintage(title, price) is False, title


# ============================================================
# 5. Sicherheitsprüfung: reale TRUE_POSITIVE-Titel bleiben erhalten,
#    inkl. des Grenzfalls mit echtem Subwoofer-Ausgang am Verstärker.
# ============================================================

def test_reale_true_positives_matchen_weiterhin():
    for title, price in [
        ("Sony PVM 14 Zoll Röhrenmonitor Retro Gaming CRT Sammler", 150.0),
        ("SONY PVM-740 PROFESSIONAL VIDEO MONITOR Broadcast", 250.0),
        ("Röhrenfernseher SABA 20 Zoll", 20.0),
        ("Pioneer SA-970 Stereo Amplifier / Verstärker", 30.0),
        ("Kenwood KA-550 Stereo HiFi Verstärker", 40.0),
        (
            "HiFi Bluetooth Hybrid Röhren Verstärker Stereo Subwoofer Tube Power Amplifier",
            199.99,
        ),
    ]:
        r = evaluate(title, price, _rules_cfg())
        assert r.matched is True and r.category == "vintage_elektronik", title


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
