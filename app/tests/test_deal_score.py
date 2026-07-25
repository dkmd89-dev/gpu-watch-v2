"""Tests für scoring/deal_score.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring.deal_score import (
    compute_deal_score,
    _price_score,
    _hardware_qualitaet_score,
    _ausstattung_score,
    DEFAULT_WEIGHTS,
)


# ---------- _price_score ----------

def test_price_score_bei_null_euro_maximal():
    assert _price_score(0, 200) == 100


def test_price_score_bei_max_price_null():
    assert _price_score(100, 0) == 60  # Platzhalter, da kein Referenzpunkt


def test_price_score_bei_max_price_none():
    assert _price_score(100, None) == 60


def test_price_score_bei_halbem_max_price():
    assert _price_score(100, 200) == 50


def test_price_score_bei_exakt_max_price():
    assert _price_score(200, 200) == 0


def test_price_score_ueber_max_price_wird_auf_null_geklemmt():
    assert _price_score(300, 200) == 0


# ---------- _hardware_qualitaet_score ----------

def test_hardware_qualitaet_top_deal_basiswert():
    assert _hardware_qualitaet_score("Top-Deal") == 85


def test_hardware_qualitaet_guter_preis_basiswert():
    assert _hardware_qualitaet_score("Guter Preis") == 65


def test_hardware_qualitaet_okay_basiswert():
    assert _hardware_qualitaet_score("Okay") == 45


def test_hardware_qualitaet_unbekanntes_rating_platzhalter():
    assert _hardware_qualitaet_score(None) == 60
    assert _hardware_qualitaet_score("Sonstwas") == 60


def test_hardware_qualitaet_mit_cpu_und_ram_bonus():
    # Top-Deal (85) + Bonus, aber auf 100 gedeckelt
    r = _hardware_qualitaet_score("Top-Deal", cpu_headroom=5, ram_headroom_gb=16)
    assert r == 100


def test_hardware_qualitaet_bonus_gedeckelt_bei_15():
    r = _hardware_qualitaet_score("Okay", cpu_headroom=10, ram_headroom_gb=100)
    assert r == 60  # 45 + min(15, ...) = 45+15


# ---------- _ausstattung_score ----------

def test_ausstattung_score_ohne_daten_platzhalter():
    assert _ausstattung_score() == 60


def test_ausstattung_score_beide_vorhanden():
    assert _ausstattung_score(has_ssd=True, has_dedicated_gpu=True) == 100


def test_ausstattung_score_keins_vorhanden():
    assert _ausstattung_score(has_ssd=False, has_dedicated_gpu=False) == 0


def test_ausstattung_score_teilweise():
    assert _ausstattung_score(has_ssd=True, has_dedicated_gpu=False) == 50


def test_ausstattung_score_nur_ein_kriterium_bekannt():
    assert _ausstattung_score(has_ssd=True, has_dedicated_gpu=None) == 100
    assert _ausstattung_score(has_ssd=False, has_dedicated_gpu=None) == 0


# ---------- compute_deal_score: Stern-Schwellen ----------

def test_stern_schwelle_bestmoegliches_angebot_mit_default_gewichten():
    r = compute_deal_score(
        price=0, max_price=200, deal_rating="Top-Deal",
        cpu_headroom=5, ram_headroom_gb=16,
        has_ssd=True, has_dedicated_gpu=True,
    )
    # WICHTIGER BEFUND: Mit den DEFAULT_WEIGHTS ist der maximal erreichbare
    # Score aktuell 92 (4 Sterne), NICHT 100/5 Sterne -- selbst ein perfektes
    # Angebot (bester Preis, Top-Deal-Hardware, volle Ausstattung) kann die
    # 95%-Schwelle fuer 5 Sterne nicht erreichen. Grund: hersteller (5%) +
    # zustand (10%) + lieferumfang (5%) = 20% Gewicht sind beim neutralen
    # Platzhalter (60) gedeckelt, solange es dafuer keine echten Detectors
    # gibt. Das ist eine bewusst sichtbar gemachte Konsequenz der aktuellen
    # Platzhalter-Situation -- WICHTIG fuer die Benachrichtigungs-Schwelle
    # im naechsten Schritt (Phase 6b: nur ab 5 Sternen benachrichtigen).
    assert r.score == 92
    assert r.stars == "★★★★☆"


def test_stern_schwelle_5_sterne_erreichbar_wenn_platzhalter_komponenten_ausgeblendet():
    # Sobald hersteller/zustand/lieferumfang per Gewicht 0 deaktiviert
    # werden (z.B. bis echte Detectors existieren), ist 5 Sterne wieder
    # erreichbar.
    weights = {
        "price": 0.35, "ausstattung": 0.15, "hardware_qualitaet": 0.30,
        "hersteller": 0, "zustand": 0, "lieferumfang": 0,
    }
    r = compute_deal_score(
        price=0, max_price=200, deal_rating="Top-Deal",
        cpu_headroom=5, ram_headroom_gb=16,
        has_ssd=True, has_dedicated_gpu=True,
        weights=weights,
    )
    assert r.score == 100
    assert r.stars == "★★★★★"


def test_stern_schwelle_1_stern_bei_niedrigem_score():
    r = compute_deal_score(
        price=200, max_price=200, deal_rating="Okay",
        has_ssd=False, has_dedicated_gpu=False,
    )
    assert r.score < 40
    assert r.stars == "★☆☆☆☆"


def test_stern_grenzwert_exakt_95_ist_5_sterne():
    # Konstruiere ueber direkte compute_deal_score-Gewichte einen Score
    # von exakt 95, um die Grenze (>= 95) zu pruefen.
    weights = {"price": 1.0}
    r = compute_deal_score(price=10, max_price=200, deal_rating=None, weights=weights)
    assert r.score == 95
    assert r.stars == "★★★★★"


def test_stern_grenzwert_94_ist_4_sterne():
    weights = {"price": 1.0}
    r = compute_deal_score(price=12, max_price=200, deal_rating=None, weights=weights)
    assert r.score == 94
    assert r.stars == "★★★★☆"


def test_stern_grenzwert_80_ist_4_sterne():
    weights = {"price": 1.0}
    r = compute_deal_score(price=40, max_price=200, deal_rating=None, weights=weights)
    assert r.score == 80
    assert r.stars == "★★★★☆"


def test_stern_grenzwert_79_ist_3_sterne():
    weights = {"price": 1.0}
    r = compute_deal_score(price=42, max_price=200, deal_rating=None, weights=weights)
    assert r.score == 79
    assert r.stars == "★★★☆☆"


def test_stern_grenzwert_60_ist_3_sterne():
    weights = {"price": 1.0}
    r = compute_deal_score(price=80, max_price=200, deal_rating=None, weights=weights)
    assert r.score == 60
    assert r.stars == "★★★☆☆"


def test_stern_grenzwert_40_ist_2_sterne():
    weights = {"price": 1.0}
    r = compute_deal_score(price=120, max_price=200, deal_rating=None, weights=weights)
    assert r.score == 40
    assert r.stars == "★★☆☆☆"


def test_stern_grenzwert_0_ist_1_stern():
    weights = {"price": 1.0}
    r = compute_deal_score(price=200, max_price=200, deal_rating=None, weights=weights)
    assert r.score == 0
    assert r.stars == "★☆☆☆☆"


# ---------- compute_deal_score: YAML-Konfigurierbarkeit ----------

def test_weights_none_nutzt_default_weights():
    r1 = compute_deal_score(price=50, max_price=200, deal_rating="Guter Preis")
    r2 = compute_deal_score(price=50, max_price=200, deal_rating="Guter Preis", weights=DEFAULT_WEIGHTS)
    assert r1.score == r2.score


def test_weights_nur_price_ignoriert_andere_komponenten():
    weights = {"price": 1.0, "hardware_qualitaet": 0}
    r = compute_deal_score(price=0, max_price=200, deal_rating="Okay", weights=weights)
    # Bei reinem Preis-Gewicht muss der Score exakt dem price_score entsprechen,
    # unabhaengig vom (schlechten) deal_rating
    assert r.score == 100


def test_weights_komponente_auf_null_hat_keinen_einfluss():
    weights_mit_hersteller = {"price": 0.5, "hersteller": 0.5}
    weights_ohne_hersteller = {"price": 1.0, "hersteller": 0}
    r1 = compute_deal_score(price=0, max_price=200, deal_rating=None, weights=weights_mit_hersteller)
    r2 = compute_deal_score(price=0, max_price=200, deal_rating=None, weights=weights_ohne_hersteller)
    # hersteller ist immer Platzhalter 60, price bei price=0 ist 100.
    # Mit 50/50-Gewichtung: (100+60)/2 = 80. Nur price: 100.
    assert r1.score == 80
    assert r2.score == 100


def test_alle_gewichte_null_liefert_platzhalter_ohne_crash():
    r = compute_deal_score(price=50, max_price=200, deal_rating="Okay", weights={})
    assert r.score == 60  # Platzhalter, kein Crash durch Division durch Null


def test_components_dict_enthaelt_alle_sechs_schluessel():
    r = compute_deal_score(price=50, max_price=200, deal_rating="Okay")
    assert set(r.components.keys()) == {
        "price", "ausstattung", "hardware_qualitaet",
        "hersteller", "zustand", "lieferumfang",
    }


def test_score_liegt_immer_im_bereich_0_bis_100():
    for price in [-50, 0, 100, 200, 500, 10000]:
        r = compute_deal_score(price=price, max_price=200, deal_rating="Top-Deal")
        assert 0 <= r.score <= 100


# ---------- _price_score: Marktpreis-Integration (Phase 7, Schritt 7.4) ----------

def test_price_score_ohne_marktpreis_unveraendert_wie_vorher():
    # Rueckwaertskompatibilitaet: market_price=None (Default) -> exakt das
    # bisherige, rein regelbasierte Verhalten.
    assert _price_score(100, 200) == _price_score(100, 200, market_price=None)
    assert _price_score(100, 200, market_price=None) == 50


def test_price_score_bei_preis_gleich_marktpreis_ist_neutral_50():
    # ohne max_price, rein marktpreisbasiert -> Preis == Marktpreis -> 50
    assert _price_score(200, None, market_price=200) == 50


def test_price_score_deutlich_unter_marktpreis_ohne_max_price():
    # 50% unter Marktpreis -> Score 100 (obere Kappung)
    assert _price_score(100, None, market_price=200) == 100


def test_price_score_deutlich_ueber_marktpreis_ohne_max_price():
    # 50% ueber Marktpreis -> Score 0 (untere Kappung)
    assert _price_score(300, None, market_price=200) == 0


def test_price_score_marktpreis_null_faellt_auf_regelbasiert_zurueck():
    assert _price_score(100, 200, market_price=0) == _price_score(100, 200)


def test_price_score_marktpreis_negativ_faellt_auf_regelbasiert_zurueck():
    assert _price_score(100, 200, market_price=-10) == _price_score(100, 200)


def test_price_score_beide_signale_werden_gewichtet_gemittelt():
    # regelbasiert (price=100, max_price=200): 50
    # marktpreisbasiert (price=100, market_price=150, +33.3% unter Markt): 83
    # blended = 0.6*83 + 0.4*50 = 69.8 -> 70
    rule_based = _price_score(100, 200)
    market_based = _price_score(100, None, market_price=150)
    blended = _price_score(100, 200, market_price=150)
    assert rule_based == 50
    assert blended != rule_based
    assert blended != market_based
    assert min(rule_based, market_based) <= blended <= max(rule_based, market_based)


def test_compute_deal_score_gibt_market_price_an_price_score_weiter():
    r_ohne_markt = compute_deal_score(
        price=100, max_price=200, deal_rating="Okay", weights={"price": 1.0}
    )
    r_mit_markt = compute_deal_score(
        price=100, max_price=200, deal_rating="Okay", weights={"price": 1.0},
        market_price=150,  # 33% unter Marktpreis -> anderer Wert als rein regelbasiert
    )
    assert r_ohne_markt.score == 50  # rein regelbasiert (max_price=200)
    assert r_mit_markt.components["price"] != r_ohne_markt.components["price"]


def test_compute_deal_score_ohne_market_price_unveraendert():
    # Bestehendes Verhalten (siehe aeltere Sterne-Schwellen-Tests oben)
    # darf durch den neuen optionalen Parameter nicht beeinflusst werden.
    r = compute_deal_score(price=10, max_price=200, deal_rating=None, weights={"price": 1.0})
    assert r.score == 95
    assert r.stars == "★★★★★"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
