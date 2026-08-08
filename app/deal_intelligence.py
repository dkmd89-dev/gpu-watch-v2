"""Deal Intelligence (roadmap.md Phase 7): führt bereits bestehende,
unabhängig berechnete Signale zu EINER gemeinsamen Einstufung pro
Angebot zusammen -- TOP DEAL / FLIP DEAL / VERY GOOD DEAL / WATCH.

WICHTIG (roadmap.md-Vorgabe wörtlich): "Bestehende Systeme nicht
ersetzen, sondern zusammenführen." Dieses Modul führt KEINE neue
Bewertungslogik, KEINE neuen Schwellenwerte und KEINE neue Berechnung
ein -- es liest ausschließlich bereits an anderer Stelle berechnete
Werte (top_deal.py::TopDealResult.is_top_deal, scoring/profit.py::
Profit.margin_pct, scoring/deal_score.py::DealScoreResult.stars) und
wendet exakt dieselbe Prioritäts-Logik an, die bereits in
api/status.py für die Dashboard-KPIs (top_deal_count/
flip_candidates_count/very_good_deals_count) verwendet wird -- siehe
dortigen Docstring. Beide Stellen nutzen bewusst dieselben importierten
Konstanten (MIN_FLIP_MARGIN_PCT, stars_meet_minimum), damit sie nicht
auseinanderlaufen können.

Reine, seiteneffektfreie Funktion -- keine Verdrahtung in app.py/
matcher.py in diesem Schritt (folgt als eigener, separater Schritt 7b).
"""
from __future__ import annotations

from dataclasses import dataclass

from scoring.deal_score import stars_meet_minimum
from scoring.profit import MIN_FLIP_MARGIN_PCT
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
    deal_stars: str | None = None,
) -> DealIntelligence:
    """Klassifiziert ein Angebot anhand bereits vorhandener Signale.

    Priorität (identisch zur bestehenden KPI-Logik in api/status.py,
    "keine Doppelzaehlung" -- jedes Angebot faellt in GENAU eine Stufe):

    1. is_top_deal (top_deal.py, Regel A/B bereits erfuellt) -> TOP DEAL
    2. sonst estimated_margin_pct >= MIN_FLIP_MARGIN_PCT (scoring/
       profit.py, 20%) -> FLIP DEAL
    3. sonst deal_stars >= ★★★★☆ (entspricht deal_score >= 80,
       scoring/deal_score.py) -> VERY GOOD DEAL
    4. sonst -> WATCH (Default/Auffangstufe, kein "schlechtes" Angebot,
       nur keine der drei staerkeren Stufen erfuellt)

    Alle drei Eingabeparameter sind optional mit sicheren Defaults --
    ein Aufrufer, der z.B. noch keinen deal_stars-Wert hat (aeltere
    found.json-Eintraege ohne dieses Feld), bekommt WATCH statt eines
    Fehlers (analog zum is-defined-Check im bestehenden Dashboard-Template).
    """
    if is_top_deal:
        label = LABEL_TOP_DEAL
    elif estimated_margin_pct is not None and estimated_margin_pct >= MIN_FLIP_MARGIN_PCT:
        label = LABEL_FLIP_DEAL
    elif stars_meet_minimum(deal_stars or "", _VERY_GOOD_MIN_STARS):
        label = LABEL_VERY_GOOD_DEAL
    else:
        label = LABEL_WATCH

    return DealIntelligence(label=label, emoji=_EMOJI_BY_LABEL[label])
