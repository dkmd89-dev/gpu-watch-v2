"""Tests für zwei zusammengehörige Änderungen:

1. notify_max_price (matcher.py/rules/*.yaml): kategorie-eigenes Preislimit
   fürs Notification-Gate, overridet das globale notifications.gate_max_price
   aus _global.yaml. Vorher galt ein einziges globales Preislimit für ALLE
   Kategorien -- strukturell unpassend, da z.B. Gaming-PCs (200-550€) nie
   unter ein für reine GPUs gedachtes Limit fallen konnten.

2. sata_ssd.yaml min_vram_gb: 0: matcher.py hat eine generische VRAM-Check-
   Heuristik, die per Regex (\\d{1,2}\\s*gb) nach GB-Zahlen im Titel sucht.
   Kapazitätsangaben wie "500GB" wurden dabei als "0GB VRAM" fehlinterpretiert
   (Regex matcht "00gb" als Teilstring von "500gb") und der Treffer verworfen,
   obwohl es sich um eine SSD, nicht um eine Grafikkarte handelt.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")

from matcher import load_rules, evaluate, _vram_gb


def test_vram_regex_kollision_mit_ssd_kapazitaet_dokumentiert():
    # Dokumentiert die Ursache des Bugs direkt an der Regex-Hilfsfunktion:
    # "500gb" enthaelt den Teilstring "00gb", der faelschlich als "0GB VRAM"
    # erkannt wird.
    assert _vram_gb("samsung 870 evo 500gb sata ssd") == 0
    # "250gb" enthaelt "50gb" -> 50, ueber dem GPU-Default von 12 -> haette
    # zufaellig NICHT ausgeschlossen, waere aber ebenso fachlich falsch
    # (eine SSD hat kein VRAM).
    assert _vram_gb("kingston a400 250gb sata ssd") == 50


def test_sata_ssd_500gb_matcht_trotz_vram_regex_kollision():
    cfg = load_rules(RULES_DIR)
    r = evaluate("Samsung 870 EVO 500GB SATA SSD 2.5 Zoll", 20.0, cfg)
    assert r.matched is True
    assert r.category == "sata_ssd"


def test_sata_ssd_250gb_matcht():
    cfg = load_rules(RULES_DIR)
    r = evaluate("Kingston A400 250GB SATA SSD 2.5", 10.0, cfg)
    assert r.matched is True
    assert r.category == "sata_ssd"


def test_sata_ssd_sata_interface_spec_loest_keinen_fehlausschluss_aus():
    # Realistischer Titel mit SATA-III-Interface-Spezifikation ("6Gb/s"),
    # die denselben Regex-Kollisionseffekt ausloesen kann wie Kapazitaets-
    # angaben.
    cfg = load_rules(RULES_DIR)
    r = evaluate("Crucial MX500 1TB SATA SSD 6Gb/s 2.5", 35.0, cfg)
    assert r.matched is True


def test_sata_ssd_500gb_matcht_nicht_die_1tb_regel():
    # Groessen-Trennschaerfe: ein 500GB-Titel darf nicht als 1TB-Regel
    # durchgehen (und umgekehrt) -- reine Ausschluss-Konsistenzprüfung.
    cfg = load_rules(RULES_DIR)
    r = evaluate("Crucial MX500 500GB SATA SSD 2.5", 20.0, cfg)
    assert r.matched is True
    assert "500GB" in r.rule_label
    assert "1TB" not in r.rule_label


def test_notify_max_price_kategorie_override_wird_geladen():
    cfg = load_rules(RULES_DIR)
    r = evaluate("ASUS RTX 3060 12GB ROG Strix", 200.0, cfg)
    assert r.matched is True
    assert r.category == "gpu"
    assert r.notify_max_price == 250  # rules/gpu.yaml notify_max_price


def test_notify_max_price_fallback_wenn_kategorie_keins_definiert():
    # sata_ssd.yaml definiert bewusst KEIN eigenes notify_max_price ->
    # MatchResult.notify_max_price muss None sein, app.py faellt dann auf
    # das globale notifications.gate_max_price aus _global.yaml zurueck.
    cfg = load_rules(RULES_DIR)
    r = evaluate("Kingston A400 250GB SATA SSD 2.5", 10.0, cfg)
    assert r.matched is True
    assert r.notify_max_price is None


def test_notify_max_price_unterschiedlich_pro_kategorie():
    cfg = load_rules(RULES_DIR)
    gpu = evaluate("ASUS RTX 3060 12GB ROG Strix", 200.0, cfg)
    gaming = evaluate(
        "Gaming PC Ryzen 5 4500 GTX 1650 16GB RAM 512GB SSD", 300.0, cfg
    )
    office = evaluate(
        "HP ProDesk i5 9400 8GB RAM 256GB SSD", 145.0, cfg
    )
    assert gpu.notify_max_price == 250
    assert gaming.notify_max_price == 400
    assert office.notify_max_price == 200


def test_load_rules_liefert_vollstaendige_kategorie_liste():
    """Regressionstest fuer den Dashboard-Kategorie-Dropdown-Fix: load_rules()
    muss eine "categories"-Liste mit ALLEN Kategorien aus den rules/*.yaml-
    Dateien liefern -- unabhaengig davon, ob gerade Treffer dieser Kategorie
    in found.json vorhanden sind. Vorher leitete das Dashboard die Dropdown-
    Optionen NUR aus den aktuell sichtbaren Karten ab (found.json, gedeckelt
    auf FOUND_MAX_ITEMS), wodurch seltene Kategorien wie sata_ssd aus dem
    Filter verschwanden, sobald sie von haeufigeren Treffern verdraengt
    wurden (siehe app.py index()/templates/index.html SERVER_CATEGORIES).
    """
    cfg = load_rules(RULES_DIR)
    assert "categories" in cfg
    # Dynamisch aus den tatsaechlich vorhandenen rules/*.yaml-Dateien
    # abgeleitet statt hartcodiert -- eine feste Menge widerspricht dem
    # Plugin-Prinzip "neue Kategorie = nur YAML, kein Test-Update noetig"
    # und brach bereits mehrfach bei neuen Kategorien (siehe STATUS.md).
    expected_categories = {
        f.stem for f in Path(RULES_DIR).glob("*.yaml") if f.name != "_global.yaml"
    }
    assert set(cfg["categories"]) == expected_categories
    # Muss sortiert sein (Dropdown-Reihenfolge im Frontend)
    assert cfg["categories"] == sorted(cfg["categories"])


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
