"""Brücke zwischen Hardware-/Zustands-Detektoren und scoring/deal_score.py.

Schritt 5 der Modularisierung (siehe Analysebericht): unveraendert aus
matcher/core.py extrahiert. Bereitet die von den Detectors erkannten
Rohwerte so auf, dass compute_deal_score() sie direkt als Score-Inputs
verwenden kann, ohne Detectors ein zweites Mal aufzurufen.
"""
from __future__ import annotations

from categories.detectors.storage import detect_ssd_gb
from categories.detectors.manufacturer import detect_manufacturer
from categories.detectors.condition import detect_condition
from categories.detectors.lieferumfang import detect_lieferumfang


def _build_score_inputs(title_lower: str, requirements: dict | None, features: dict) -> dict:
    """Bereitet die Zusatzinformationen für compute_deal_score() auf.

    Nutzt die während der Requirement-Prüfung bereits gesammelten
    Detector-Ergebnisse (features) weiter, statt sie erneut zu berechnen.
    Für klassische Titel-Matching-Regeln (requirements is None, z.B. GPU-
    Kategorie) bleiben cpu_headroom/ram_headroom_gb bei 0 und
    has_dedicated_gpu bei None (nicht anwendbar) -- compute_deal_score()
    behandelt das über den neutralen Platzhalter in _ausstattung_score().
    """
    cpu_headroom = 0
    ram_headroom_gb = 0
    has_dedicated_gpu = None

    if requirements is not None:
        cpu = features.get("cpu")
        if cpu is not None:
            brand_req = requirements.get("min_cpu", {}).get(cpu.brand.lower(), {})
            min_generation = brand_req.get("min_generation") or 0
            cpu_headroom = max(0, cpu.generation - min_generation)

        ram_gb = features.get("ram_gb")
        min_ram_gb = requirements.get("min_ram_gb")
        if ram_gb is not None and min_ram_gb is not None:
            ram_headroom_gb = max(0, ram_gb - min_ram_gb)

        if "gpu" in features:
            has_dedicated_gpu = features["gpu"] is not None

    # SSD-Erkennung ist nur bei Hardware-Requirement-Kategorien (Office-/
    # Gaming-PC) als "Ausstattung" aussagekräftig. Bei klassischen Titel-
    # Matching-Regeln (GPU-Kategorie: das Angebot IST die Grafikkarte,
    # kein "System") ist "hat SSD?" keine sinnvolle Frage -- None (nicht
    # anwendbar) statt fälschlich False, sonst würde jede reine GPU-Anzeige
    # unfair abgewertet, nur weil sie (folgerichtig) keine SSD erwähnt.
    has_ssd = detect_ssd_gb(title_lower) is not None if requirements is not None else None

    # Hersteller-Erkennung (Detector-Folgeschritt): anders als bei SSD gilt
    # HIER keine Kategorie-Einschränkung -- die erkannten Marken umfassen
    # sowohl PC-OEMs (Dell, Lenovo, ...) als auch GPU-AIB-Partner (Asus,
    # MSI, ...), daher ist "Hersteller erkannt?" auch bei der klassischen
    # GPU-Kategorie eine sinnvolle Frage (siehe categories/detectors/
    # manufacturer.py). None bleibt der korrekte Wert, wenn im Titel gar
    # keine Marke genannt wird -- die Score-Komponente behandelt das als
    # neutralen Platzhalter (siehe scoring/deal_score._hersteller_score()).
    manufacturer = detect_manufacturer(title_lower)
    manufacturer_name = manufacturer.name if manufacturer is not None else None

    # Zustand-/Lieferumfang-Detector-Verdrahtung (roadmap.md Phase 6,
    # Schritt 6d): wie bei manufacturer oben KEINE Kategorie-Einschraenkung
    # -- Zustands-/Lieferumfangsangaben koennen bei jeder Angebotsart im
    # Titel stehen. None (condition) bzw. leere Tupel (lieferumfang)
    # bleiben der korrekte Wert, wenn der Titel nichts Erkennbares enthaelt
    # -- die jeweilige Score-Komponente behandelt das als neutralen
    # Platzhalter (siehe scoring/deal_score.py::_zustand_score()/
    # _lieferumfang_score()).
    condition_match = detect_condition(title_lower)
    condition_label = condition_match.condition if condition_match is not None else None

    lieferumfang_match = detect_lieferumfang(title_lower)
    if lieferumfang_match is not None:
        lieferumfang_positive_signals = lieferumfang_match.positive_signals
        lieferumfang_negative_signals = lieferumfang_match.negative_signals
    else:
        lieferumfang_positive_signals = ()
        lieferumfang_negative_signals = ()

    return {
        "cpu_headroom": cpu_headroom,
        "ram_headroom_gb": ram_headroom_gb,
        "has_ssd": has_ssd,
        "has_dedicated_gpu": has_dedicated_gpu,
        "manufacturer_name": manufacturer_name,
        "condition_label": condition_label,
        "lieferumfang_positive_signals": lieferumfang_positive_signals,
        "lieferumfang_negative_signals": lieferumfang_negative_signals,
    }
