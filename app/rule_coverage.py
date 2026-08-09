"""Rule Coverage Analysis (Phase 15, Schritt 5 -- PHASE15_OPTIMIERUNG.md,
Abschnitte 17-18).

Ermittelt, welche Regeln (genauer: welche price_history_model-Gruppen,
der stabile Gruppierungs-Schluessel ueber Regel-/Preisstufen-Grenzen
hinweg, siehe price_history.py::PricePoint-Docstring) tatsaechlich
produktive Daten erhalten haben.

Datenquelle AUSSCHLIESSLICH price_history.jsonl, rein lesend (Auftrag,
Abschnitt 2.4/17) -- kein Schreiben, kein Loeschen, keine Manipulation.
Dieses Modul importiert price_history.read_price_points() (Single Source
of Truth fuers Parsen der JSONL-Datei) statt eine zweite Leselogik zu
bauen.

Architektur
-----------
    compute_rule_coverage(points, rules_cfg) -> list[RuleCoverage]
        Eine Zeile pro (category, price_history_model)-Paar, das ENTWEDER
        in den aktuellen Regeln existiert ODER in den Daten vorkommt
        (Orphans -- Modelle aus entfernten/umbenannten Regeln -- werden
        separat markiert, nicht stillschweigend fallengelassen).

    compute_rule_quality(coverage) -> RuleQualityScore
        Nur EIN Vorschlag (Auftrag, Abschnitt 18: "darf in Phase 15
        zunaechst nur als Vorschlag behandelt werden") -- kein finaler
        Ersatz fuer/Bestandteil von scoring/deal_score.py.

Validitaets-Pruefung ("valid"/"false-positive indicators"): fuer jeden
Datenpunkt mit vorhandenem `fingerprint` (normalisierter Titel, siehe
duplicate_detection.py::normalize_title() -- Wortreihenfolge bleibt
erhalten, nur Kleinschreibung/Sonderzeichen/Fuellwoerter entfernt) wird
matcher.evaluate() erneut gegen die AKTUELLEN Regeln aufgerufen (dieselbe
Funktion wie beim Scan und in category_validation.py -- Single Source of
Truth, keine zweite Matching-Logik). Stimmen Kategorie UND
price_history_model noch mit dem gespeicherten Wert ueberein, gilt der
Punkt als "valid", sonst als False-Positive-Indikator. Punkte OHNE
fingerprint (aeltere price_history.jsonl-Zeilen vor dessen Einfuehrung)
sind nicht rekonstruierbar und zaehlen weder als valid noch als
False-Positive -- sie fliessen nur in `matches` (Rohanzahl) ein, nicht in
`sample_count` (verifizierbare Teilmenge).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from matcher import evaluate
from price_history import PricePoint, read_price_points
from price_stats import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    _confidence,
)


@dataclass
class RuleCoverage:
    category: str | None
    price_history_model: str
    matches: int
    sample_count: int  # Teilmenge von matches mit vorhandenem fingerprint
    valid: int  # Teilmenge von sample_count, die noch matcht (Kategorie+Modell)
    false_positive_indicators: int  # sample_count - valid
    last_seen: str | None  # ISO-Datum (nur Datumsteil) oder None ("never")
    in_current_ruleset: bool  # False = Orphan (Modell existiert in Regeln nicht mehr)

    @property
    def false_positive_rate(self) -> float | None:
        """None, wenn keine verifizierbare Stichprobe vorhanden ist (nicht
        0.0 -- 0 verifizierbare Punkte bedeutet 'unbekannt', nicht 'perfekt')."""
        if self.sample_count == 0:
            return None
        return self.false_positive_indicators / self.sample_count


def _last_seen_date(points: list[PricePoint]) -> str | None:
    if not points:
        return None
    return max(p.date for p in points)[:10]


def _is_still_valid(point: PricePoint, rules_cfg: dict) -> bool | None:
    """True/False bei vorhandenem fingerprint, None wenn nicht verifizierbar
    (kein fingerprint -- aeltere Datenpunkte, siehe Moduldocstring).

    Bewusst mit price=0.0 statt point.price ausgewertet: diese Analyse
    prueft NUR, ob der Titel weiterhin derselben Kategorie/demselben
    price_history_model zugeordnet wuerde (Matcher-/Regel-Qualitaet,
    Auftrag Abschnitt 34), nicht ob der historische Preis die AKTUELLE
    max_price-Schwelle noch unterschreitet. Phase 15 ist ausdruecklich
    keine Preiskalibrierungsphase (Auftrag, Abschnitt 3/2.3) -- wuerde
    hier mit point.price geprueft, wuerden Punkte, die nur wegen einer
    spaeteren, legitimen max_price-Verschaerfung (z.B. Phase 12, Schritt
    5) nicht mehr durchkommen, faelschlich als Matcher-Fehltreffer
    gezaehlt, obwohl die Titel-/Kategoriezuordnung nach wie vor korrekt
    ist. Keine Regel in diesem Projekt nutzt eine Mindestpreis-Schwelle
    (verifiziert: kein "min_price"-Feld in matcher.py/rules/*.yaml), daher
    kann price=0.0 die max_price-Pruefung risikofrei umgehen, ohne
    sonstiges evaluate()-Verhalten zu veraendern."""
    if not point.fingerprint:
        return None
    result = evaluate(point.fingerprint, 0.0, rules_cfg)
    if not result.matched:
        return False
    return (
        result.category == point.category
        and result.price_history_model == point.model
    )


def compute_rule_coverage(
    points: list[PricePoint], rules_cfg: dict
) -> list[RuleCoverage]:
    """Baut eine RuleCoverage-Zeile pro (category, price_history_model).

    Enthaelt sowohl Regeln OHNE jeden Datenpunkt (matches=0, siehe
    Auftrags-Beispiel "lego_ninjago_rare: matches: 0, never") als auch
    Modelle, die in den Daten vorkommen, aber in den AKTUELLEN Regeln
    nicht mehr existieren (in_current_ruleset=False -- z.B. nach einer
    Regel-Umbenennung/-Entfernung)."""
    known_models: dict[str, str | None] = {}
    for rule in rules_cfg.get("rules", []):
        model = rule.get("price_history_model") or rule.get("label")
        if model:
            known_models.setdefault(model, rule.get("_category"))

    points_by_model: dict[str, list[PricePoint]] = {}
    for p in points:
        points_by_model.setdefault(p.model, []).append(p)

    all_models = set(known_models) | set(points_by_model)

    coverage: list[RuleCoverage] = []
    for model in sorted(all_models):
        model_points = points_by_model.get(model, [])
        category = known_models.get(model)
        if category is None and model_points:
            category = model_points[0].category

        validities = [_is_still_valid(p, rules_cfg) for p in model_points]
        sample_count = sum(1 for v in validities if v is not None)
        valid = sum(1 for v in validities if v is True)
        false_positive_indicators = sum(1 for v in validities if v is False)

        coverage.append(RuleCoverage(
            category=category,
            price_history_model=model,
            matches=len(model_points),
            sample_count=sample_count,
            valid=valid,
            false_positive_indicators=false_positive_indicators,
            last_seen=_last_seen_date(model_points),
            in_current_ruleset=model in known_models,
        ))

    return coverage


def load_coverage(rules_cfg: dict, price_history_path: Path) -> list[RuleCoverage]:
    """Convenience-Wrapper: liest price_history.jsonl (read-only) und
    berechnet die Coverage in einem Aufruf."""
    points = read_price_points(price_history_path)
    return compute_rule_coverage(points, rules_cfg)


# ------------------------------------------------------------------
# Rule Quality (Abschnitt 18) -- NUR EIN VORSCHLAG, keine finale Bewertung.
# ------------------------------------------------------------------

# Gewichtung laut Auftrags-Beispiel (Abschnitt 18). Ausdruecklich als
# Vorschlag markiert -- darf in Phase 15 nicht als beschlossene
# Deal-Score-Erweiterung missverstanden werden.
QUALITY_WEIGHTS = {
    "match_volume": 0.30,
    "false_positive_rate": 0.30,
    "data_freshness": 0.15,
    "price_confidence": 0.15,
    "rule_stability": 0.10,
}

# Referenzgroesse fuer "volle Punktzahl" bei match_volume -- bewusst am
# HIGH-Schwellenwert der bestehenden Confidence-Klassifizierung
# orientiert (price_stats.py::_confidence()), keine neue Zahl erfunden.
_MATCH_VOLUME_FULL_SCORE_AT = 15


@dataclass
class RuleQualityScore:
    price_history_model: str
    match_volume_score: float  # 0..1
    false_positive_score: float  # 0..1 (1 = keine bekannten Fehltreffer)
    data_freshness_score: float  # 0..1
    price_confidence_score: float  # 0..1
    rule_stability_score: float  # 0..1
    overall: float  # 0..1, gewichtete Summe der obigen Komponenten
    price_confidence_label: str  # LOW/MEDIUM/HIGH (price_stats._confidence())


def compute_rule_quality(
    rc: RuleCoverage, reference_date_iso: str | None = None
) -> RuleQualityScore:
    """Berechnet die 5 Komponenten aus Abschnitt 18 fuer EINE Regel-Gruppe.

    reference_date_iso: "heutiges" Datum (ISO, nur Datumsteil) fuer die
    data_freshness-Berechnung. None -> das juengste last_seen aller
    Regeln waere noetig, um relativ zu rechnen; hier bewusst absolut
    gegen einen uebergebenen Referenzpunkt (Aufrufer entscheidet "heute"),
    damit diese Funktion selbst keine Systemzeit liest (einfacher testbar,
    deterministisch)."""
    match_volume_score = min(1.0, rc.matches / _MATCH_VOLUME_FULL_SCORE_AT)

    fp_rate = rc.false_positive_rate
    # Keine verifizierbare Stichprobe -> neutraler Mittelwert (weder
    # bestraft noch belohnt), NICHT automatisch 1.0 ("makellos").
    false_positive_score = 0.5 if fp_rate is None else max(0.0, 1.0 - fp_rate)

    if reference_date_iso and rc.last_seen:
        days_since = _days_between(rc.last_seen, reference_date_iso)
        # Linear abfallend: 1.0 am selben Tag, 0.0 ab 90 Tagen alt.
        data_freshness_score = max(0.0, 1.0 - days_since / 90)
    else:
        data_freshness_score = 0.0 if rc.matches == 0 else 0.5

    confidence_label = _confidence(rc.matches)
    price_confidence_score = {
        CONFIDENCE_LOW: 0.2,
        CONFIDENCE_MEDIUM: 0.6,
        CONFIDENCE_HIGH: 1.0,
    }[confidence_label]

    # Rule-Stability: Platzhalter-Proxy anhand der aktuell verfuegbaren
    # Coverage-Daten -- ohne eine historische Regel-Aenderungs-Zeitreihe
    # (nicht Teil dieses Moduls) ist "Stabilitaet" hier nur ueber die
    # False-Positive-Rate der VERIFIZIERBAREN Stichprobe approximierbar:
    # eine Regel, die bei Neubewertung durchgaengig noch matcht, war seit
    # dem letzten Datenpunkt vermutlich nicht destabilisierend veraendert.
    rule_stability_score = false_positive_score

    overall = (
        QUALITY_WEIGHTS["match_volume"] * match_volume_score
        + QUALITY_WEIGHTS["false_positive_rate"] * false_positive_score
        + QUALITY_WEIGHTS["data_freshness"] * data_freshness_score
        + QUALITY_WEIGHTS["price_confidence"] * price_confidence_score
        + QUALITY_WEIGHTS["rule_stability"] * rule_stability_score
    )

    return RuleQualityScore(
        price_history_model=rc.price_history_model,
        match_volume_score=round(match_volume_score, 3),
        false_positive_score=round(false_positive_score, 3),
        data_freshness_score=round(data_freshness_score, 3),
        price_confidence_score=round(price_confidence_score, 3),
        rule_stability_score=round(rule_stability_score, 3),
        overall=round(overall, 3),
        price_confidence_label=confidence_label,
    )


def _days_between(iso_date_a: str, iso_date_b: str) -> int:
    from datetime import date
    a = date.fromisoformat(iso_date_a[:10])
    b = date.fromisoformat(iso_date_b[:10])
    return abs((b - a).days)
