"""Deal-Score-Berechnung (Phase 6): gewichteter Score 0-100 aus mehreren
Komponenten, vollständig über YAML-Gewichte konfigurierbar.

WICHTIGER HINWEIS zum aktuellen Stand: Von den sechs im Auftrag genannten
Komponenten (Preis, Ausstattung, Hardwarequalität, Hersteller, Zustand,
Lieferumfang) haben aktuell nur "Preis" und "Hardwarequalität" eine
verlässliche Datengrundlage aus den bestehenden Detectors/Regeln.
"Hersteller", "Zustand" und "Lieferumfang" liefern bewusst einen NEUTRALEN
PLATZHALTERWERT (60/100), da es noch keine entsprechenden Detectors gibt:
- Hersteller: keine Reputations-/Qualitätsliste je Marke
- Zustand: kein Parser für Formulierungen wie "neuwertig"/"gebraucht"
- Lieferumfang: kein Erkennung von Zubehör/Rechnung/Garantie im Titel

Diese drei Komponenten sind über die YAML-Gewichte schon ansteuerbar
(z.B. auf Gewicht 0 setzbar, um sie faktisch zu deaktivieren), liefern
aber inhaltlich noch keine differenzierte Bewertung. Das ist ein bewusst
offen gelassener Folgeschritt, kein vergessener Teil.

PHASE 7, SCHRITT 7.4: "Preis" kann jetzt optional zusätzlich zum
regelbasierten max_price-Vergleich einen aus der LOKAL gesammelten
Preishistorie abgeleiteten Marktpreis einbeziehen (siehe price_stats.py).
Ohne übergebenen Marktpreis (market_price=None, der Standardfall z.B. bei
noch fehlender Preishistorie für ein Modell) verhält sich _price_score()
exakt wie zuvor -- rein rückwärtskompatibel. Details siehe _price_score().
"""
from __future__ import annotations
from dataclasses import dataclass, field

# Feste Stern-Schwellen (Bewertungsskala aus dem Auftrag: 95-100 / 80-94 /
# 60-79 / 40-59 / 0-39). Bewusst als Code-Konstante statt YAML-Wert, da es
# sich um eine feste Bewertungsskala handelt, keine Hardware- oder
# Markt-Konfiguration, die sich je Kategorie unterscheiden sollte.
_STAR_THRESHOLDS: list[tuple[int, str]] = [
    (95, "★★★★★"),
    (80, "★★★★☆"),
    (60, "★★★☆☆"),
    (40, "★★☆☆☆"),
    (0, "★☆☆☆☆"),
]

# Rang-Zuordnung (1 = wenigste Sterne, 5 = meiste) für Mindest-Vergleiche,
# z.B. "erreicht das Angebot mindestens ★★★★★?" in app.py.
_STAR_RANK: dict[str, int] = {
    label: rank for rank, (_, label) in enumerate(reversed(_STAR_THRESHOLDS), start=1)
}


def stars_meet_minimum(stars: str, min_stars: str) -> bool:
    """Prüft, ob eine Stern-Bewertung mindestens einer geforderten
    Mindest-Bewertung entspricht (z.B. für Benachrichtigungs-Schwellen).
    Unbekannte/leere Stern-Strings gelten als Rang 0 (niedrigster Rang).
    """
    return _STAR_RANK.get(stars, 0) >= _STAR_RANK.get(min_stars, 0)

# Default-Gewichte, falls eine Kategorie keine eigenen scoring_weights
# in ihrer YAML definiert. Summe ergibt 1.0, muss aber nicht -- die
# Gewichte werden in compute_deal_score() ohnehin normalisiert.
DEFAULT_WEIGHTS: dict[str, float] = {
    "price": 0.35,
    "ausstattung": 0.15,
    "hardware_qualitaet": 0.30,
    "hersteller": 0.05,
    "zustand": 0.10,
    "lieferumfang": 0.05,
}

# Neutraler Platzhalterwert für Komponenten ohne verlässliche Datengrundlage
# (siehe Modul-Docstring). 60 liegt bewusst in der "guten Mitte" (weder
# straft es Angebote unbegründet ab, noch wertet es sie unbegründet auf).
_PLACEHOLDER_SCORE = 60

_COMPONENT_KEYS = (
    "price",
    "ausstattung",
    "hardware_qualitaet",
    "hersteller",
    "zustand",
    "lieferumfang",
)


@dataclass(frozen=True)
class DealScoreResult:
    score: int                  # 0-100, gerundet
    stars: str                  # z.B. "★★★★☆"
    components: dict[str, int]  # Einzelscores je Komponente (0-100)


# Gewichtung des marktpreisbasierten Signals gegenüber dem regelbasierten
# max_price-Signal, WENN ein Marktpreis vorliegt (siehe _price_score()).
# 0.6 bedeutet: der tatsächlich am Markt beobachtete Preis zählt stärker
# als die (manuell in der YAML kalibrierte) Preisgrenze der Regel, die
# aber nicht komplett verdrängt wird -- bei duennen/verzerrten
# Preishistorien bleibt so ein stabiler Anker erhalten.
_MARKET_PRICE_WEIGHT = 0.6


def _rule_based_price_score(price: float, max_price: float | None) -> int | None:
    """Preis-Score relativ zur Preisobergrenze der gematchten Regel.

    None, wenn keine max_price vorliegt -- unterscheidet sich bewusst vom
    alten Rückgabewert _PLACEHOLDER_SCORE, da _price_score() jetzt einen
    zweiten (marktpreisbasierten) Signalpfad hat, der auch ohne max_price
    greifen kann (siehe _price_score()).
    """
    if not max_price or max_price <= 0:
        return None
    ratio = max(0.0, min(1.0, price / max_price))
    return round((1 - ratio) * 100)


def _market_based_price_score(price: float, market_price: float) -> int:
    """Preis-Score relativ zum aus der Preishistorie abgeleiteten Marktpreis
    (siehe price_stats.PriceStats.market_price).

    Symmetrisch um den Marktpreis: Preis == Marktpreis -> 50 (neutrale
    Mitte), günstiger -> höher (bis 100 bei -50% oder mehr), teurer ->
    niedriger (bis 0 bei +50% oder mehr). Nutzt dieselbe Rabatt-Prozent-
    Kennzahl wie top_deal.py, hier aber als kontinuierlichen Score statt
    einer binären Top-Deal-Entscheidung.
    """
    discount_pct = ((market_price - price) / market_price) * 100
    return max(0, min(100, round(50 + discount_pct)))


def _price_score(
    price: float,
    max_price: float | None,
    market_price: float | None = None,
) -> int:
    """Preis-Score (0-100): je niedriger der Preis, desto höher der Score.

    Kombiniert zwei mögliche Signale:
    - regelbasiert: Preis relativ zur max_price der gematchten YAML-Regel
      (wie bisher, siehe _rule_based_price_score()).
    - marktpreisbasiert (Phase 7, Schritt 7.4): Preis relativ zum aus der
      LOKAL gesammelten Preishistorie abgeleiteten Marktpreis (siehe
      price_stats.py), NUR wenn `market_price` übergeben wird.

    Liegt kein Marktpreis vor (market_price=None oder <= 0 -- der
    Standardfall, z.B. noch keine Preishistorie für dieses Modell
    gesammelt), verhält sich diese Funktion EXAKT wie vor Schritt 7.4
    (reines max_price-Signal, Platzhalter 60 ohne max_price) -- volle
    Rückwärtskompatibilität.

    Liegen BEIDE Signale vor, werden sie gewichtet gemittelt
    (_MARKET_PRICE_WEIGHT), damit ein einzelner, ggf. noch dünn belegter
    Marktpreis das etablierte max_price-Signal nicht vollständig verdrängt.
    """
    rule_based = _rule_based_price_score(price, max_price)

    if market_price is None or market_price <= 0:
        return rule_based if rule_based is not None else _PLACEHOLDER_SCORE

    market_based = _market_based_price_score(price, market_price)

    if rule_based is None:
        return market_based

    blended = _MARKET_PRICE_WEIGHT * market_based + (1 - _MARKET_PRICE_WEIGHT) * rule_based
    return round(max(0.0, min(100.0, blended)))


def _hardware_qualitaet_score(
    deal_rating: str | None,
    cpu_headroom: int = 0,
    ram_headroom_gb: int = 0,
) -> int:
    """Basis-Score aus der bereits vorhandenen Top-Deal/Guter-Preis/Okay-
    Einstufung (Signal aus matcher.evaluate()), optional angehoben durch
    CPU-/RAM-"Überschuss" oberhalb der Mindestanforderung.

    cpu_headroom: z.B. Differenz der CPU-Generation über das Minimum hinaus.
    ram_headroom_gb: erkannte RAM-Größe minus geforderte Mindestgröße.
    """
    base = {"Top-Deal": 85, "Guter Preis": 65, "Okay": 45}.get(
        deal_rating, _PLACEHOLDER_SCORE
    )
    bonus = min(15, cpu_headroom * 3 + (ram_headroom_gb // 8) * 3)
    return max(0, min(100, base + bonus))


def _ausstattung_score(
    has_ssd: bool | None = None,
    has_dedicated_gpu: bool | None = None,
) -> int:
    """Bonus-Score für zusätzliche Ausstattung über die Mindestanforderung
    hinaus (z.B. SSD bei PC-Kategorien). None bedeutet "nicht ermittelt/
    nicht anwendbar" (z.B. bei der reinen GPU-Kategorie, wo das Konzept
    "Ausstattung eines Systems" nicht greift) -> neutraler Platzhalterwert.
    """
    checks = [flag for flag in (has_ssd, has_dedicated_gpu) if flag is not None]
    if not checks:
        return _PLACEHOLDER_SCORE
    return round((sum(checks) / len(checks)) * 100)


def compute_deal_score(
    price: float,
    max_price: float | None,
    deal_rating: str | None,
    weights: dict | None = None,
    *,
    cpu_headroom: int = 0,
    ram_headroom_gb: int = 0,
    has_ssd: bool | None = None,
    has_dedicated_gpu: bool | None = None,
    market_price: float | None = None,
) -> DealScoreResult:
    """Berechnet den gewichteten Deal-Score (0-100) und die Stern-Einstufung.

    weights: Dict mit einem Teil oder allen Schlüsseln aus _COMPONENT_KEYS.
    Fehlende Schlüssel werden mit Gewicht 0 behandelt. None -> DEFAULT_WEIGHTS.
    Die Gewichte werden intern normalisiert (müssen sich nicht zu 1.0 summieren).

    market_price (Phase 7, Schritt 7.4): optionaler, aus der lokalen
    Preishistorie abgeleiteter Marktpreis (siehe price_stats.PriceStats.
    market_price), fließt in die "price"-Komponente ein (siehe
    _price_score()). None (Standard) -> unverändertes Verhalten wie vor
    Schritt 7.4.
    """
    weights = weights if weights is not None else DEFAULT_WEIGHTS

    components: dict[str, int] = {
        "price": _price_score(price, max_price, market_price),
        "ausstattung": _ausstattung_score(has_ssd, has_dedicated_gpu),
        "hardware_qualitaet": _hardware_qualitaet_score(
            deal_rating, cpu_headroom, ram_headroom_gb
        ),
        "hersteller": _PLACEHOLDER_SCORE,
        "zustand": _PLACEHOLDER_SCORE,
        "lieferumfang": _PLACEHOLDER_SCORE,
    }

    total_weight = sum(weights.get(k, 0) for k in _COMPONENT_KEYS)
    if total_weight <= 0:
        # Kein einziges Gewicht gesetzt -- Score ist in diesem Fall nicht
        # aussagekräftig, aber wir liefern trotzdem einen validen Wert statt
        # einer Division durch Null (neutraler Mittelwert).
        score = _PLACEHOLDER_SCORE
    else:
        weighted_sum = sum(components[k] * weights.get(k, 0) for k in _COMPONENT_KEYS)
        score = round(weighted_sum / total_weight)
        score = max(0, min(100, score))

    stars = next(label for threshold, label in _STAR_THRESHOLDS if score >= threshold)

    return DealScoreResult(score=score, stars=stars, components=components)
