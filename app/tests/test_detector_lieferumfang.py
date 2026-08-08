"""Tests für categories/detectors/lieferumfang.py (roadmap.md Phase 6, Schritt 6c)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from categories.detectors.lieferumfang import (
    detect_lieferumfang,
    LieferumfangMatch,
    SIGNAL_OVP,
    SIGNAL_RECHNUNG,
    SIGNAL_ORIGINALZUBEHOER,
    SIGNAL_NETZTEIL,
    SIGNAL_CONTROLLER,
    SIGNAL_ZUBEHOER,
    SIGNAL_OHNE_NETZTEIL,
    SIGNAL_NUR_GERAET,
    SIGNAL_DEFEKT,
)


# ---------- Positive Signale ----------

def test_ovp_erkannt():
    r = detect_lieferumfang("RTX 3060 OVP")
    assert r.positive_signals == (SIGNAL_OVP,)
    assert r.negative_signals == ()


def test_rechnung_erkannt():
    r = detect_lieferumfang("Grafikkarte mit Rechnung")
    assert SIGNAL_RECHNUNG in r.positive_signals


def test_mehrere_positive_signale_gleichzeitig():
    r = detect_lieferumfang("RTX 3060 OVP, Rechnung vorhanden")
    assert set(r.positive_signals) == {SIGNAL_OVP, SIGNAL_RECHNUNG}
    assert r.negative_signals == ()


def test_originalzubehoer_zusammengeschrieben_erkannt():
    r = detect_lieferumfang("Laptop mit Originalzubehör")
    assert r.positive_signals == (SIGNAL_ORIGINALZUBEHOER,)


def test_original_zubehoer_mit_leerzeichen_erkannt():
    r = detect_lieferumfang("Laptop mit original Zubehör")
    assert r.positive_signals == (SIGNAL_ORIGINALZUBEHOER,)


def test_original_zubehoer_zaehlt_nicht_doppelt_als_generisches_zubehoer():
    # Regressionsschutz: "original Zubehör" darf NICHT zusaetzlich das
    # generische Zubehör-Signal fuer dieselbe Textstelle ausloesen.
    r = detect_lieferumfang("PC mit original Zubehör")
    assert SIGNAL_ZUBEHOER not in r.positive_signals


def test_generisches_zubehoer_ohne_original_erkannt():
    r = detect_lieferumfang("PC mit Zubehör")
    assert r.positive_signals == (SIGNAL_ZUBEHOER,)


def test_netzteil_als_positives_signal_erkannt():
    r = detect_lieferumfang("Gaming PC inkl. Netzteil")
    assert r.positive_signals == (SIGNAL_NETZTEIL,)
    assert r.negative_signals == ()


def test_controller_erkannt():
    r = detect_lieferumfang("PS4 mit Controller, OVP")
    assert set(r.positive_signals) == {SIGNAL_CONTROLLER, SIGNAL_OVP}


# ---------- Negative Signale ----------

def test_ohne_netzteil_erkannt():
    r = detect_lieferumfang("PC ohne Netzteil, sonst komplett")
    assert r.negative_signals == (SIGNAL_OHNE_NETZTEIL,)
    assert r.positive_signals == ()


def test_kein_netzteil_synonym_erkannt():
    r = detect_lieferumfang("Laptop kein Netzteil dabei")
    assert r.negative_signals == (SIGNAL_OHNE_NETZTEIL,)


def test_ohne_netzteil_loest_nicht_zusaetzlich_positives_netzteil_signal_aus():
    # Regressionsschutz: "ohne Netzteil" darf NICHT zusaetzlich das
    # positive Netzteil-Signal fuer dieselbe Textstelle ausloesen.
    r = detect_lieferumfang("PC ohne Netzteil")
    assert SIGNAL_NETZTEIL not in r.positive_signals


def test_nur_geraet_erkannt():
    r = detect_lieferumfang("Grafikkarte ohne alles, nur Gerät")
    assert r.negative_signals == (SIGNAL_NUR_GERAET,)


def test_nur_das_geraet_erkannt():
    r = detect_lieferumfang("Nur das Gerät, kein Zubehör")
    assert SIGNAL_NUR_GERAET in r.negative_signals


def test_kein_zubehoer_loest_kein_positives_zubehoer_signal_aus():
    # Regressionsschutz: "kein Zubehör" negiert den Lieferumfang, darf
    # also NICHT als positives Zubehör-Signal gezaehlt werden.
    r = detect_lieferumfang("Nur Gerät, kein Zubehör")
    assert SIGNAL_ZUBEHOER not in r.positive_signals


def test_ohne_zubehoer_liefert_kein_positives_signal():
    r = detect_lieferumfang("Handy ohne Zubehör")
    assert r is None


def test_defekt_als_negatives_lieferumfang_signal_erkannt():
    r = detect_lieferumfang("Netzteil defekt, Rest funktioniert")
    assert SIGNAL_DEFEKT in r.negative_signals
    # Netzteil selbst ist trotzdem als positives Signal vorhanden (das
    # Netzteil IST im Lieferumfang, auch wenn es laut Titel defekt ist --
    # zwei unabhaengige Aussagen ueber denselben Titel).
    assert SIGNAL_NETZTEIL in r.positive_signals


def test_defekt_flexionsform_erkannt():
    r = detect_lieferumfang("Ersatzteile, ein Controller defektes Exemplar")
    assert SIGNAL_DEFEKT in r.negative_signals


# ---------- Gemischt / kein Treffer ----------

def test_positive_und_negative_signale_gleichzeitig():
    r = detect_lieferumfang("Gaming PC OVP, Rechnung, aber ohne Netzteil")
    assert set(r.positive_signals) == {SIGNAL_OVP, SIGNAL_RECHNUNG}
    assert r.negative_signals == (SIGNAL_OHNE_NETZTEIL,)


def test_kein_signal_im_titel_liefert_none():
    assert detect_lieferumfang("Einfach nur ein Titel ohne Lieferumfangsangabe") is None


def test_leerer_text_liefert_none():
    assert detect_lieferumfang("") is None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
