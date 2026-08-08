"""Deal Intelligence (roadmap.md Phase 7, erweitert in Phase 11): führt
bereits bestehende, unabhängig berechnete Signale zu EINER gemeinsamen
Einstufung pro Angebot zusammen -- TOP DEAL / FLIP DEAL / VERY GOOD DEAL
/ WATCH.

WICHTIG (roadmap.md-Vorgabe wörtlich): "Bestehende Systeme nicht
ersetzen, sondern zusammenführen." Dieses Modul führt KEINE neue
Bewertungslogik, KEINE neuen Schwellenwerte und KEINE neue Berechnung
ein -- es liest ausschließlich bereits an anderer Stelle berechnete
Werte (top_deal.py::TopDealResult.is_top_deal, scoring/deal_score.py::
DealScoreResult.stars/score) und wendet exakt dieselbe Prioritäts-Logik
an, die bereits in api/status.py für die Dashboard-KPIs (top_deal_count/
flip_candidates_count/very_good_deals_count) verwendet wird -- siehe
dortigen Docstring.

Phase 11, Punkt A: die FLIP-DEAL-Stufe nutzt jetzt scoring/profit.py::
is_robust_flip_candidate() (margin_pct UND margin_eur UND deal_score UND
resale_confidence) statt des vormaligen alleinigen margin_pct-Kriteriums
-- Single Source of Truth mit api/status.py, beide Stellen rufen
dieselbe Funktion auf, können nicht mehr auseinanderlaufen.

Reine, seiteneffektfreie Funktion -- Verdrahtung in app.py (Schritt 7b).
"""
from __future__ import annotations

from dataclasses import dataclass

from scoring.deal_score import stars_meet_minimum
from scoring.profit import is_robust_flip_candidate
from top_deal import TOP_DEAL_SCORE_THRESHOLD_A

LABEL_TOP_DEAL = "TOP DEAL"
LABEL_FLIP_DEAL = "FLIP DEAL"
LABEL_VERY_GOOD_DEAL = "VERY GOOD DEAL"
LABEL_WATCH = "WATCH"

EMOJI_TOP_DEAL = "🔥"
EMOJI_FLIP_DEAL = "💰"
EMOJI_VERY_GOOD_DEAL = "⭐"
EMOJI_WATCH = "👀"

_EMOJI_BY_LABEL = {
    LABEL_TOP_DEAL: EMOJI_TOP_DEAL,
    LABEL_FLIP_DEAL: EMOJI_FLIP_DEAL,
    LABEL_VERY_GOOD_DEAL: EMOJI_VERY_GOOD_DEAL,
    LABEL_WATCH: EMOJI_WATCH,
}

# "Sehr gut" entspricht deal_score >= TOP_DEAL_SCORE_THRESHOLD_A (80) --
# dieselbe Skala/Schwelle wie in api/status.py::api_status() (siehe
# dortiger Docstring: "dieselbe Skala wie top_deal.
# TOP_DEAL_SCORE_THRESHOLD_A"). Keine neue Zahl, nur der bereits
# bestehende Schwellenwert in Sterne-Form uebersetzt (stars_meet_minimum()
# vergleicht Rang, nicht die Rohzahl direkt).
_VERY_GOOD_MIN_STARS = "★★★★☆"


@dataclass(frozen=True)
class DealIntelligence:
    """Ergebnis der Deal-Intelligence-Einstufung fuer ein einzelnes Angebot."""

    label: str  # einer der LABEL_*-Werte oben
    emoji: str  # einer der EMOJI_*-Werte oben, passend zu label


def classify_deal(
    *,
    is_top_deal: bool = False,
    estimated_margin_pct: float | None = None,
    estimated_margin_eur: float | None = None,
    deal_score: int | None = None,
    resale_confidence: str | None = None,
    deal_stars: str | None = None,
) -> DealIntelligence:
    """Klassifiziert ein Angebot anhand bereits vorhandener Signale.

    Priorität (identisch zur bestehenden KPI-Logik in api/status.py,
    "keine Doppelzaehlung" -- jedes Angebot faellt in GENAU eine Stufe):

    1. is_top_deal (top_deal.py, Regel A/B bereits erfuellt) -> TOP DEAL
    2. sonst is_robust_flip_candidate() (scoring/profit.py, Phase 11 Punkt
       A: margin_pct UND margin_eur UND deal_score UND resale_confidence)
       -> FLIP DEAL
    3. sonst deal_stars >= ★★★★☆ (entspricht deal_score >= 80,
       scoring/deal_score.py) -> VERY GOOD DEAL
    4. sonst -> WATCH (Default/Auffangstufe, kein "schlechtes" Angebot,
       nur keine der drei staerkeren Stufen erfuellt)

    Alle Eingabeparameter sind optional mit sicheren Defaults -- ein
    Aufrufer, der z.B. noch keinen deal_stars-Wert hat (aeltere
    found.json-Eintraege ohne dieses Feld), bekommt WATCH statt eines
    Fehlers (analog zum is-defined-Check im bestehenden Dashboard-Template).
    is_robust_flip_candidate() selbst liefert bei fehlenden Werten (None)
    bereits False, kein zusaetzlicher Guard hier noetig.
    """
    if is_top_deal:
        label = LABEL_TOP_DEAL
    elif is_robust_flip_candidate(
        margin_pct=estimated_margin_pct,
        margin_eur=estimated_margin_eur,
        deal_score=deal_score,
        resale_confidence=resale_confidence,
    ):
        label = LABEL_FLIP_DEAL
    elif stars_meet_minimum(deal_stars or "", _VERY_GOOD_MIN_STARS):
        label = LABEL_VERY_GOOD_DEAL
    else:
        label = LABEL_WATCH

    return DealIntelligence(label=label, emoji=_EMOJI_BY_LABEL[label])
