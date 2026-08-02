"""Tests für die GPU-Part-Out-Erkennung (STATUS.md Abschnitt 16, Baustein 3,
Schritt 2).

Nutzt zwei Test-Strategien, analog zu test_matcher_negotiation.py:
- Gegen die echte rules/-Konfiguration (gaming_pc.yaml + gpu.yaml +
  rules/mappings/component_values.yaml), da das Mapping/der Schwellenwert
  ausschliesslich dort gepflegt werden (kein synthetisches rules_cfg-Dict
  fuer die Mapping-Tabelle selbst, siehe _load_rules_from_dir()).
- Synthetische rules_cfg-Dicts fuer Edge-Cases (kein Mapping-Eintrag,
  kein Marktpreis, price=0), analog zum etablierten Muster.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules, evaluate, DEFAULT_PART_OUT_THRESHOLD_PCT

GAMING_PC_TITLE = "Gaming PC Ryzen 5 3600 16GB DDR4 RTX 3060 Tower"
OFFICE_PC_TITLE = "Office PC i5-8500 16GB DDR4 Midi-Tower"


def test_mapping_tabelle_wird_geladen():
    cfg = load_rules(RULES_DIR)
    mapping = cfg["gpu_model_to_price_history_model"]
    assert mapping["RTX 3060"] == "rtx_3060_12gb"
    assert mapping["RX 6700 XT"] == "rx_6700_xt"


def test_part_out_kandidat_bei_hoher_gpu_wert_ratio():
    cfg = load_rules(RULES_DIR)
    # GPU-Marktpreis 220€, PC-Preis 250€ -> 88% >= 70%-Schwelle (Default)
    r = evaluate(
        GAMING_PC_TITLE, 250.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    assert r.matched is True
    assert r.part_out_gpu_value == 220.0
    assert abs(r.part_out_ratio_pct - 88.0) < 0.01
    assert r.is_part_out_candidate is True


def test_kein_part_out_kandidat_unter_schwelle():
    cfg = load_rules(RULES_DIR)
    # GPU-Marktpreis 220€, PC-Preis 400€ (noch innerhalb der "Okay"-Regel,
    # max_price 450 -- Match bleibt bestehen) -> 55% < 70%-Schwelle
    r = evaluate(
        GAMING_PC_TITLE, 400.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    assert r.matched is True
    assert r.is_part_out_candidate is False
    assert r.part_out_ratio_pct is not None  # Ratio wird trotzdem berechnet
    assert abs(r.part_out_ratio_pct - 55.0) < 0.01


def test_keine_market_prices_uebergeben_bleibt_inaktiv():
    """Rueckwaertskompatibilitaet: aeltere Aufrufer, die market_prices gar
    nicht kennen, bleiben unveraendert lauffaehig (keine Exception)."""
    cfg = load_rules(RULES_DIR)
    r = evaluate(GAMING_PC_TITLE, 250.0, cfg)
    assert r.matched is True
    assert r.part_out_gpu_value is None
    assert r.part_out_ratio_pct is None
    assert r.is_part_out_candidate is False


def test_office_pc_ohne_dedizierte_gpu_bleibt_inaktiv():
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        OFFICE_PC_TITLE, 200.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    assert r.matched is True
    assert r.part_out_gpu_value is None
    assert r.is_part_out_candidate is False


def test_reine_gpu_kategorie_kein_crash_ohne_features():
    """Klassisches Titel-Matching (GPU-Kategorie selbst, requirements=None)
    hat kein "gpu"-Feature -- muss ohne Exception None/False liefern."""
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        "RTX 3060 12GB Grafikkarte", 200.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    assert r.matched is True
    assert r.part_out_gpu_value is None
    assert r.is_part_out_candidate is False


def test_kein_mapping_eintrag_fuer_erkannte_gpu_bleibt_inaktiv():
    """GPU wird erkannt, hat aber keinen Mapping-Eintrag (z.B. eine der
    dokumentierten Luecken in component_values.yaml) -> kein Crash, Signal
    bleibt inaktiv."""
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        "Gaming PC Ryzen 5 3600 16GB DDR4 GTX 1660 Tower", 250.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    assert r.matched is True
    assert r.part_out_gpu_value is None
    assert r.is_part_out_candidate is False


def test_schwellenwert_ist_ueber_global_yaml_konfigurierbar():
    cfg = load_rules(RULES_DIR)
    # Schwelle synthetisch verschaerft auf 90% -- 88% (siehe Test oben)
    # darf dann NICHT mehr als Part-Out-Kandidat gelten.
    cfg = dict(cfg)
    cfg["part_out_detection"] = {"gpu_value_ratio_threshold_pct": 90.0}
    r = evaluate(
        GAMING_PC_TITLE, 250.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    assert r.part_out_ratio_pct is not None
    assert r.part_out_ratio_pct < 90.0
    assert r.is_part_out_candidate is False


def test_fehlende_part_out_detection_sektion_faellt_auf_modulkonstante_zurueck():
    cfg = load_rules(RULES_DIR)
    cfg = dict(cfg)
    cfg["part_out_detection"] = {}  # Sektion "leer" (aeltere _global.yaml)
    r = evaluate(
        GAMING_PC_TITLE, 250.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    # 88% >= DEFAULT_PART_OUT_THRESHOLD_PCT (70.0) -> weiterhin Kandidat
    assert DEFAULT_PART_OUT_THRESHOLD_PCT == 70.0
    assert r.is_part_out_candidate is True


def test_price_null_verursacht_keinen_absturz():
    """Randfall 'zu verschenken' (price=0) darf keine ZeroDivisionError
    auslösen."""
    cfg = load_rules(RULES_DIR)
    r = evaluate(
        GAMING_PC_TITLE, 0.0, cfg,
        market_prices={"rtx_3060_12gb": 220.0},
    )
    assert r.matched is True
    assert r.part_out_gpu_value is None
    assert r.is_part_out_candidate is False
