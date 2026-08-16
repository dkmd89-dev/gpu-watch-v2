"""Wendet die Regel-Matrix aus rules.yaml auf einen (Titel, Preis) an."""
from __future__ import annotations
import logging
from dataclasses import dataclass

from scoring.deal_score import compute_deal_score, DEFAULT_WEIGHTS, COMPONENT_KEYS
from scoring.profit import compute_profit

# Schritt 4 der Modularisierung: PC_AUSSCHLIESSEN und die Hardware-
# Anforderungsprüfung (_ist_kompletter_pc, _*_meets_requirement,
# _evaluate_hardware_requirements) liegen jetzt in
# matcher/hardware_requirements.py. Re-Import hier fuer evaluate().
from matcher.hardware_requirements import (  # noqa: E402
    PC_AUSSCHLIESSEN,
    _ist_kompletter_pc,
    _cpu_meets_requirement,
    _ram_meets_requirement,
    _storage_meets_requirement,
    _psu_meets_requirement,
    _case_meets_requirement,
    _gpu_meets_requirement,
    _evaluate_hardware_requirements,
)

# Schritt 5 der Modularisierung: _build_score_inputs (Bruecke zu
# scoring/deal_score.py) liegt jetzt in matcher/score_bridge.py.
# Re-Import hier fuer evaluate().
from matcher.score_bridge import _build_score_inputs  # noqa: E402

logger = logging.getLogger(__name__)

# Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16): Default-
# Schwellenwert (Prozent), ab der eine im PC-Titel erkannte GPU als
# "macht den PC im Grunde nur als GPU-Verkauf lohnenswert" gilt --
# gpu_market_price / pc_price * 100 >= dieser Wert. Greift nur, falls
# _global.yaml keine eigene "part_out_detection"-Sektion definiert
# (aeltere Configs) -- analog zu duplicate_detection.py's Modulkonstanten,
# volle Rueckwaertskompatibilitaet.
DEFAULT_PART_OUT_THRESHOLD_PCT = 70.0


@dataclass
class MatchResult:
    matched: bool
    rule_label: str | None = None
    max_price: float | None = None
    deal_rating: str | None = None
    deal_score: int | None = None
    deal_stars: str | None = None
    # Phase 7 (Schritt 7.1): fuer die Preishistorie. Additive Felder mit
    # Defaults -- bestehender Code, der MatchResult per Keyword-Argumenten
    # oder nur ueber die obigen Felder erstellt/liest, bleibt unveraendert
    # lauffaehig.
    category: str | None = None  # rule._category, None im Legacy-Einzeldatei-Modus
    price_history_model: str | None = None  # stabiler Gruppierungs-Schluessel
    # Dashboard-Filter-Folgeschritt: erkannter Herstellername (siehe
    # categories/detectors/manufacturer.py), None wenn im Titel keine Marke
    # erkennbar war. Additives Feld mit Default -- bestehender Code, der
    # MatchResult ueber die bisherigen Felder erstellt/liest, bleibt
    # unveraendert lauffaehig.
    manufacturer_name: str | None = None
    # Notification-Gate-Folgeschritt: kategorie-eigenes Preislimit fuer den
    # ntfy-Push (siehe rules/*.yaml "notify_max_price"). None, wenn die
    # Kategorie keins definiert -> app.py faellt dann auf das globale
    # notifications.gate_max_price aus _global.yaml zurueck. Additives Feld
    # mit Default -- bestehender Code bleibt unveraendert lauffaehig.
    notify_max_price: float | None = None
    # Reselling-/Arbitrage-Konzept (STATUS.md Abschnitt 16, Punkt b):
    # geschätzte Marge in Euro/Prozent für die Dashboard-Anzeige --
    # unabhängig vom "profit"-Score (0-100) in compute_deal_score(), der
    # nur den GEWICHTETEN Gesamt-Score beeinflusst. Diese beiden Felder
    # transportieren die tatsächlichen, für Menschen lesbaren Rohwerte
    # (siehe scoring/profit.py::Profit). None, wenn kein estimated_resale_price
    # vorliegt (z.B. noch keine Preishistorie für dieses Modell) -- additive
    # Felder mit Default, bestehender Code bleibt unverändert lauffähig.
    estimated_margin_eur: float | None = None
    estimated_margin_pct: float | None = None
    # Phase 11, Punkt A (robuste Flip-Kandidat-Qualifikation): Confidence
    # (LOW/MEDIUM/HIGH, siehe price_stats.py) der PriceStats-Quelle, aus
    # der estimated_resale_price oben stammt -- None, wenn kein
    # price_history_model bekannt ist ODER resale_confidence gar nicht an
    # evaluate() uebergeben wurde (aeltere Aufrufer/Tests, volle
    # Rueckwaertskompatibilitaet).
    resale_confidence: str | None = None
    # Verhandlungs-Assistent (STATUS.md Abschnitt 16, Punkt 7): True, wenn
    # dieses Match NUR dank der negotiation_*-Felder der Kategorie-YAML
    # zustande kam (Preis > max_price, aber innerhalb der konfigurierten
    # Toleranz UND Mindest-Score erreicht) -- statt wie bisher komplett
    # verworfen zu werden. Additives Feld mit Default False, bestehender
    # Code bleibt unveraendert lauffaehig (regulaere Matches innerhalb von
    # max_price setzen dieses Feld nie).
    negotiation_candidate: bool = False
    # Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16): reines
    # Zusatzsignal fuer PC-Angebote (Office-/Gaming-PC o.ae.), bei denen die
    # im Titel erkannte dedizierte GPU laut bereits gesammeltem GPU-Markt-
    # preis (rules/gpu.yaml-Kategorie) einen grossen Teil des PC-Gesamtpreises
    # ausmacht -- "die GPU allein waere fast so viel wert wie der ganze PC".
    # part_out_gpu_value: nachgeschlagener GPU-Marktpreis in Euro (None, wenn
    #   keine GPU erkannt wurde ODER kein Mapping-Eintrag/Marktpreis vorliegt).
    # part_out_ratio_pct: part_out_gpu_value / Angebotspreis * 100.
    # is_part_out_candidate: True, wenn part_out_ratio_pct die konfigurierte
    #   Schwelle erreicht (siehe DEFAULT_PART_OUT_THRESHOLD_PCT/_global.yaml
    #   "part_out_detection"). KEIN Einfluss auf deal_score/deal_stars oder
    #   das Notification-Gate -- rein informatives Signal, additive Felder
    #   mit neutralen Defaults, bestehender Code bleibt unveraendert lauffaehig.
    part_out_gpu_value: float | None = None
    part_out_ratio_pct: float | None = None
    is_part_out_candidate: bool = False
    # Dashboard-Transparenz (Auftrag "Angebotswert + Marktwert + geschaetzter
    # Verkaufspreis"): der in evaluate() bereits fuer compute_profit()
    # berechnete Reselling-Schaetzwert (siehe _resale_prices_from_stats()-
    # Aufrufer unten), zusaetzlich additiv auf MatchResult mitgegeben, statt
    # wie bisher nur lokal verwendet und danach verworfen zu werden. KEINE
    # neue Berechnung -- identischer Wert, der bereits estimated_margin_eur/
    # -pct zugrunde liegt. None, wenn keine Preishistorie/Resale-Schaetzung
    # vorliegt (identische Bedingung wie bei estimated_margin_eur). Additives
    # Feld mit Default, bestehender Code bleibt unveraendert lauffaehig.
    estimated_resale_price: float | None = None


# Schritt 6 der Modularisierung: load_rules(), _load_rules_from_dir() und
# compute_ruleset_signature() liegen jetzt in matcher/rules_io.py.
# Re-Import hier, damit evaluate() und alle externen Aufrufer (app.py,
# category_validation.py, rule_analyzer.py, rule_coverage.py,
# rules_loader.py, recompute_top_deal.py, tools/ruleset_quality/common.py,
# Testsuite) unveraendert funktionieren.
from matcher.rules_io import (  # noqa: E402
    load_rules,
    _load_rules_from_dir,
    compute_ruleset_signature,
)

# Schritt 3 der Modularisierung: GPU-VRAM-Parsing liegt jetzt in
# matcher/vram.py. Re-Import hier fuer evaluate().
from matcher.vram import _vram_gb  # noqa: E402

# Schritt 2 der Modularisierung: Term-/Regex-Matching-Primitive und
# kontextbewusste Exclude-Logik liegen jetzt in matcher/text_matching.py.
# Re-Import hier, damit alle Aufrufer innerhalb dieser Datei (evaluate(),
# _ist_kompletter_pc() usw.) unveraendert funktionieren.
from matcher.text_matching import (  # noqa: E402
    _compiled_term_pattern,
    _contains_term,
    _any_term,
    _compiled_unless_preceded_pattern,
    _contains_term_unless_preceded_by,
    _any_conditional_exclude,
    _any_conditional_exclude_presence,
)


def evaluate(
    title: str,
    price: float,
    rules_cfg: dict,
    market_prices: dict[str, float] | None = None,
    resale_prices: dict[str, float] | None = None,
    resale_confidence: dict[str, str] | None = None,
) -> MatchResult:
    """Wertet Titel/Preis gegen die Regel-Matrix aus.

    market_prices (Phase 7, Schritt 7.4): optionales Mapping
    {price_history_model: Marktpreis}, typischerweise gebaut aus
    price_stats.compute_all_price_stats() ueber die gesammelte
    Preishistorie (siehe price_history.py). evaluate() liest dabei
    selbst KEINE Dateien -- der Aufrufer (app.py) uebergibt die bereits
    berechneten Marktpreise, damit matcher.py weiterhin frei von I/O und
    einfach testbar bleibt. None (Standard) -> unveraendertes Verhalten
    wie vor Schritt 7.4 (reines max_price-Signal im Deal-Score).

    resale_prices (Reselling-/Arbitrage-Konzept, STATUS.md Abschnitt 16,
    Punkt c): optionales Mapping {price_history_model: geschaetzter
    Verkaufspreis oder None}, typischerweise gebaut aus
    app._resale_prices_from_stats() (PriceStats.estimated_resale_price --
    methodisch von market_price getrennt, siehe price_stats.py-Docstring).
    Fehlt der Modell-Key komplett in resale_prices (oder wird resale_prices
    gar nicht uebergeben, z.B. aeltere Aufrufer/Tests), faellt die Marge-
    Berechnung fuer dieses Modell auf market_prices zurueck -- volle
    Rueckwaertskompatibilitaet zum bisherigen Verhalten (Phase-1-
    Platzhalter-Entscheidung: estimated_resale_price == market_price).
    Ist der Modell-Key dagegen VORHANDEN, aber sein Wert None ("Flip-
    Kandidaten-Logik optimieren", Schritt B, Option 1: zu duenne
    Preishistorie fuer eine belastbare Schaetzung), erfolgt bewusst KEIN
    Fallback auf market_price -- estimated_resale_price bleibt None,
    wodurch fuer dieses Angebot keine Marge/kein Flip-Kandidat berechnet
    wird (siehe compute_profit()).

    resale_confidence (Phase 11, Punkt A): optionales Mapping
    {price_history_model: Confidence-Label ("LOW"/"MEDIUM"/"HIGH")},
    typischerweise gebaut aus app._resale_confidence_from_stats() --
    MUSS aus derselben PriceStats-Quelle stammen wie resale_prices oben
    (sonst inkonsistent). Fehlt der Modell-Key oder wird resale_confidence
    gar nicht uebergeben -> MatchResult.resale_confidence bleibt None
    (volle Rueckwaertskompatibilitaet).

    Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16,
    Schritt 2): nutzt DIESELBEN market_prices wie oben (kein zusaetzlicher
    Parameter) -- fuer PC-Angebote mit erkannter dedizierter GPU wird
    geprueft, ob der GPU-Marktpreis (ueber rules_cfg["gpu_model_to_price_
    history_model"], siehe rules/mappings/component_values.yaml) einen
    grossen Anteil des PC-Gesamtpreises ausmacht (siehe MatchResult.
    part_out_gpu_value/part_out_ratio_pct/is_part_out_candidate). Reines
    Zusatzsignal, kein Einfluss auf deal_score/Notification-Gate.
    """
    title_l = title.lower()
    defaults = rules_cfg.get("defaults", {})
    global_excludes = defaults.get("exclude_global", [])
    directory_mode = rules_cfg.get("_directory_mode", False)
    # Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16,
    # Schritt 2): einmalig vor der Regel-Schleife gelesen, analog zu
    # global_excludes oben -- vermeidet wiederholte dict-Lookups pro Regel.
    gpu_model_mapping = rules_cfg.get("gpu_model_to_price_history_model") or {}
    part_out_threshold_pct = (rules_cfg.get("part_out_detection") or {}).get(
        "gpu_value_ratio_threshold_pct", DEFAULT_PART_OUT_THRESHOLD_PCT
    )

    # 1. Globaler Ausschluss (defekt, bastler, etc.) -- gilt für ALLE Kategorien,
    #    AUSSER eine Kategorie hat den jeweiligen Begriff explizit über
    #    "ignore_global_excludes" freigegeben (siehe load_rules()-Kommentar).
    #    Schnellpfad unverändert: trifft KEIN globaler Ausschlussbegriff zu,
    #    ist das Verhalten exakt wie vorher (kein Term-Match -> leere Liste
    #    -> die Prüfung pro Regel unten greift nirgends, identisch zum alten
    #    Verhalten inkl. Legacy-Einzeldatei-Modus, siehe Schritt 2 unten).
    matched_global_excludes = [t for t in global_excludes if _contains_term(title_l, t)]

    # 2. Legacy-Einzeldatei-Modus (keine Kategorie-Information vorhanden):
    #    komplette PCs weiterhin unconditional ausschließen, exakt wie
    #    im ursprünglichen Verhalten vor der Kategorie-Aufteilung. Auch hier
    #    ändert sich nichts: ignore_global_excludes ist ein Kategorie-Feature
    #    und existiert im Einzeldatei-Modus nicht.
    if not directory_mode:
        if matched_global_excludes:
            return MatchResult(matched=False)
        if _ist_kompletter_pc(title_l):
            return MatchResult(matched=False)

    # 3. Regeln durchgehen
    for rule in rules_cfg.get("rules", []):
        # match-Stichwortliste ist OPTIONAL: Hardware-Spec-Regeln (Phase 5,
        # z.B. Office-PC) brauchen keine Titel-Stichwörter, da sie über
        # "requirements:" (Detector-basiert) statt Titel-Matching laufen.
        # Ist "match" angegeben, muss weiterhin mind. ein Begriff treffen.
        match_terms = rule.get("match", [])
        if match_terms and not _any_term(title_l, match_terms):
            continue

        # Globaler Ausschluss (siehe oben) -- nur relevant, wenn Schritt 1
        # überhaupt Treffer hatte. Eine Regel kommt nur dann trotz globalem
        # Treffer weiter, wenn IHRE Kategorie ALLE getroffenen globalen
        # Begriffe explizit via ignore_global_excludes freigegeben hat.
        # Kategorien ohne diesen Key (Default: leere Liste) verhalten sich
        # exakt wie vor dieser Änderung.
        if matched_global_excludes:
            rule_ignore = rule.get("_ignore_global_excludes", [])
            if not set(matched_global_excludes).issubset(set(rule_ignore)):
                continue

        # Kategorie-spezifischer Ausschluss (nur im Verzeichnis-Modus, z.B.
        # "kein komplettes PC-System" bei GPUs). Jede Kategorie bringt ihre
        # eigene Liste mit -- Kategorien, die keine definieren, schließen
        # nichts zusätzlich aus.
        if directory_mode:
            category_excludes = rule.get("_category_exclude_terms", [])
            if category_excludes and _any_term(title_l, category_excludes):
                continue
            # Phase 15 (kontrollierter Review, "Variante C"): kontextbewusster
            # Gegenpart zu category_excludes oben -- blockiert einen Begriff
            # NUR, wenn er als Standalone-Vorkommen auftritt (siehe
            # _any_conditional_exclude()-Docstring), nicht wenn ein erlaubter
            # Bundle-Konnektor unmittelbar davorsteht. Default leeres Dict ->
            # identisches Verhalten zu vorher fuer Kategorien ohne dieses Feld.
            category_excludes_conditional = rule.get(
                "_category_exclude_unless_preceded_by", {}
            )
            if category_excludes_conditional and _any_conditional_exclude(
                title_l, category_excludes_conditional
            ):
                continue
            # Phase 15 (kontrollierter Folge-Review, "Gehäuse/Shell-Fix"):
            # zweiter kontextbewusster Gegenpart -- blockiert einen Begriff
            # NUR, wenn im GESAMTEN Titel kein erlaubter Kontext-/
            # Zustandsbegriff vorkommt (siehe
            # _any_conditional_exclude_presence()-Docstring). Default leeres
            # Dict -> identisches Verhalten zu vorher fuer Kategorien ohne
            # dieses Feld.
            category_excludes_unless_context = rule.get(
                "_category_exclude_unless_also_contains", {}
            )
            if category_excludes_unless_context and _any_conditional_exclude_presence(
                title_l, category_excludes_unless_context
            ):
                continue

        # exclude-Begriffe pro Regel
        excludes = rule.get("exclude", [])
        if _any_term(title_l, excludes):
            continue

        requirements = rule.get("requirements")
        features: dict = {}
        if requirements is not None:
            # Hardware-Spec-Regel (Phase 5): Detector-basierte Prüfung
            # statt Titel-Stichwort-Matching.
            ok, features = _evaluate_hardware_requirements(title_l, requirements)
            if not ok:
                continue
        else:
            # require_all_of: Liste von Gruppen, aus JEDER Gruppe muss min. 1 Wort matchen.
            # Wichtig: jede Untergruppe steht für eine eigene Bedingung (z.B. Marke UND
            # Modellreihe getrennt) -- eine einzelne Gruppe mit mehreren Begriffen ist
            # dagegen eine ODER-Verknüpfung und macht die Regel zu unscharf.
            require_all_of = rule.get("require_all_of")
            if require_all_of:
                ok = all(_any_term(title_l, group) for group in require_all_of)
                if not ok:
                    continue

            # VRAM-Check (nur für klassische Titel-Matching-Regeln relevant)
            min_vram = rule.get("min_vram_gb", defaults.get("min_vram_gb", 12))
            vram = _vram_gb(title_l)
            if vram is not None and vram < min_vram:
                continue

        # Preis-Check (gilt für beide Regel-Arten gleichermaßen)
        max_price = rule.get("max_price")
        price_exceeds_max = max_price is not None and price > max_price

        # Verhandlungs-Assistent (STATUS.md Abschnitt 16, Punkt 7): ein
        # Angebot über max_price wird nicht mehr zwingend sofort verworfen,
        # sondern kann als Verhandlungskandidat markiert werden, WENN die
        # Kategorie-YAML alle drei negotiation_*-Felder definiert. Fehlt
        # auch nur eines davon -> Feature fuer diese Kategorie inaktiv,
        # bisheriges Verhalten (sofortiges Verwerfen) bleibt unveraendert.
        # Bewusst KEIN globaler Fallback in _global.yaml (siehe Auftrag).
        negotiation_tolerance_pct = rule.get("negotiation_tolerance_pct")
        negotiation_min_score = rule.get("negotiation_min_score")
        negotiation_score_component = rule.get("negotiation_score_component")
        negotiation_configured = (
            negotiation_tolerance_pct is not None
            and negotiation_min_score is not None
            and negotiation_score_component is not None
        )

        if price_exceeds_max:
            if not negotiation_configured:
                continue
            tolerance_limit = max_price * (1 + negotiation_tolerance_pct / 100)
            if price > tolerance_limit:
                continue
            if negotiation_score_component not in COMPONENT_KEYS:
                logger.warning(
                    "Ungueltiger negotiation_score_component '%s' in Regel "
                    "'%s' -- Verhandlungs-Assistent fuer dieses Match "
                    "deaktiviert.",
                    negotiation_score_component,
                    rule.get("label", "?"),
                )
                continue

        # Deal-Score (Phase 6): nutzt die bereits gesammelten Detector-
        # Ergebnisse weiter, keine doppelten Detector-Aufrufe.
        score_inputs = _build_score_inputs(title_l, requirements, features)
        scoring_weights = (
            rule.get("_scoring_weights")
            or rules_cfg.get("scoring_weights")
            or DEFAULT_WEIGHTS
        )
        rule_label = rule.get("label", "?")
        # price_history_model bestimmt sowohl den Gruppierungs-Schluessel
        # fuer die Preishistorie (siehe MatchResult unten) als auch den
        # Lookup-Key fuer einen ggf. vorab berechneten Marktpreis (Schritt 7.4).
        price_history_model = rule.get("price_history_model", rule_label)
        market_price = (market_prices or {}).get(price_history_model)
        # Reselling-/Arbitrage-Konzept (STATUS.md Abschnitt 16, Punkt c):
        # estimated_resale_price kommt jetzt bevorzugt aus resale_prices
        # (PriceStats.estimated_resale_price, P75-P90-Segment -- siehe
        # price_stats.py-Docstring), NICHT mehr aus market_price. Fehlt der
        # Modell-Key komplett (noch keine Preishistorie fuer dieses Modell,
        # oder resale_prices gar nicht uebergeben), Fallback auf
        # market_price -- exakt das bisherige Phase-1-Platzhalter-Verhalten,
        # volle Rueckwaertskompatibilitaet fuer aeltere Aufrufer/Tests.
        #
        # "Flip-Kandidaten-Logik optimieren", Schritt B (Option 1,
        # STATUS.md Abschnitt 33b): ist der Modell-Key VORHANDEN, aber sein
        # Wert None (app.py::_resale_prices_from_stats() -- zu duenne
        # Preishistorie fuer eine belastbare P75-P90-Schaetzung), erfolgt
        # BEWUSST KEIN Fallback auf market_price. estimated_resale_price
        # bleibt None -> compute_profit() liefert kein Profit-Objekt ->
        # estimated_margin_pct bleibt None -> kein Flip-Kandidat (siehe
        # app.py::flip_candidates_count). market_price selbst ist davon
        # unberuehrt und fliesst weiterhin unveraendert in die "price"-
        # Score-Komponente ein.
        if resale_prices is not None and price_history_model in resale_prices:
            estimated_resale_price = resale_prices[price_history_model]
        else:
            estimated_resale_price = market_price
        # Phase 11, Punkt A: Confidence-Label fuer denselben Modell-Key --
        # bewusst OHNE Fallback auf market_price-Aehnliches Verhalten (im
        # Unterschied zu estimated_resale_price oben), da es fuer
        # market_price keine eigene Confidence gibt. Fehlt der Modell-Key
        # in resale_confidence -> None (analog zu "kein price_history_model
        # bekannt").
        resale_confidence_label = (resale_confidence or {}).get(price_history_model)
        # Reselling-/Arbitrage-Konzept (STATUS.md Abschnitt 16, Punkt b):
        # separater compute_profit()-Aufruf fuer die Dashboard-Rohwerte
        # (Euro/Prozent). compute_deal_score() ruft intern denselben
        # estimated_resale_price/fees-Input ebenfalls in compute_profit()
        # ein (fuer den 0-100 "profit"-Score) -- die doppelte Berechnung
        # ist bewusst in Kauf genommen (billige, reine Funktion ohne
        # Seiteneffekte), um compute_deal_score()s Rueckgabewert
        # (DealScoreResult) nicht um ein Profit-Objekt erweitern zu
        # muessen (kein Bruch der bestehenden Signatur/des bestehenden
        # Rueckgabewerts).
        fees_cfg = rules_cfg.get("fees") or None
        profit = compute_profit(price, estimated_resale_price, fees_cfg)
        score_result = compute_deal_score(
            price=price,
            max_price=max_price,
            deal_rating=rule.get("deal_rating"),
            weights=scoring_weights,
            market_price=market_price,
            manufacturer_reputation=rules_cfg.get("manufacturer_reputation") or None,
            # roadmap.md Phase 6, Schritt 6d: analog zu manufacturer_
            # reputation oben -- None statt leerem Dict, falls _global.yaml
            # keine eigene Sektion definiert (volle Rueckwaertskompatibilitaet,
            # siehe _zustand_score()/_lieferumfang_score()-Docstrings).
            condition_scores=rules_cfg.get("condition_scores") or None,
            lieferumfang_signal_scores=rules_cfg.get("lieferumfang_signal_scores") or None,
            # estimated_resale_price kommt jetzt aus resale_prices (siehe
            # oben), NICHT mehr 1:1 aus market_price -- die im Phase-1-
            # Architekturentscheid dokumentierte methodische Trennung
            # Ankauf (market_price, fliesst weiterhin in "price" ueber
            # _price_score() ein) vs. Verkauf (estimated_resale_price,
            # fliesst in die "profit"-Komponente ein) ist damit umgesetzt.
            # fees kommt aus rules_cfg["fees"] (siehe _load_rules_from_dir()),
            # leeres/fehlendes Dict -> neutrale 0-Defaults in
            # compute_profit(), kein Crash.
            estimated_resale_price=estimated_resale_price,
            fees=fees_cfg,
            **score_inputs,
        )

        # Verhandlungs-Assistent (STATUS.md Abschnitt 16, Punkt 7): finale
        # Entscheidung erst jetzt möglich, da erst hier score_result.components
        # vorliegt. Toleranz wurde oben bereits geprüft (sonst waere hier
        # längst "continue" ausgeloest worden) -- fehlt nur noch die
        # Mindest-Score-Pruefung der konfigurierten Komponente.
        negotiation_candidate = False
        if price_exceeds_max and negotiation_configured:
            component_score = score_result.components.get(
                negotiation_score_component, 0
            )
            if component_score < negotiation_min_score:
                continue
            negotiation_candidate = True

        # Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16,
        # Schritt 2): reines Zusatzsignal, KEIN Einfluss auf score_result/
        # deal_score/Notification-Gate (siehe MatchResult-Docstring oben).
        # Bewusst OHNE Kategorie-Namen-Hardcoding (kein "if category ==
        # 'gaming_pc'") -- die Pruefung greift generisch ueberall dort, wo
        # eine Hardware-Requirement-Regel tatsaechlich eine dedizierte GPU
        # erkannt hat (features["gpu"], siehe _evaluate_hardware_
        # requirements()) UND fuer deren Modell sowohl ein Mapping-Eintrag
        # (rules/mappings/component_values.yaml, Schritt 1) als auch ein
        # bereits gesammelter GPU-Marktpreis (market_prices) vorliegen.
        # Neue PC-Kategorien profitieren dadurch automatisch, ohne
        # matcher.py anzufassen -- konsistent mit dem Architekturprinzip
        # "neue Hardware nur ueber YAML" (Entwicklungsauftrag Phase 2).
        part_out_gpu_value: float | None = None
        part_out_ratio_pct: float | None = None
        is_part_out_candidate = False
        gpu_match = features.get("gpu")
        if gpu_match is not None:
            gpu_price_history_model = gpu_model_mapping.get(gpu_match.model)
            if gpu_price_history_model is not None:
                gpu_market_price = (market_prices or {}).get(gpu_price_history_model)
                # price > 0 verhindert ZeroDivisionError bei "zu verschenken"-
                # Angeboten (Randfall, in der Praxis kaum relevant, aber
                # evaluate() darf hierbei nie abstuerzen).
                if gpu_market_price is not None and price > 0:
                    part_out_gpu_value = gpu_market_price
                    part_out_ratio_pct = (gpu_market_price / price) * 100
                    is_part_out_candidate = part_out_ratio_pct >= part_out_threshold_pct

        return MatchResult(
            matched=True,
            rule_label=rule_label,
            max_price=max_price,
            deal_rating=rule.get("deal_rating"),
            deal_score=score_result.score,
            deal_stars=score_result.stars,
            category=rule.get("_category"),
            # price_history_model ist optional in der YAML (siehe rules/*.yaml).
            # Fehlt es (z.B. Legacy-Einzeldatei-Modus, noch nicht migrierte
            # Kategorie-YAML), fällt es auf das Regel-Label zurück, damit
            # Phase 7 auch ohne YAML-Änderung sofort nutzbar ist -- separate
            # Rating-Stufen/Marken derselben Hardware werden dann allerdings
            # NICHT zusammengefasst (siehe Docstring in price_history.py).
            price_history_model=price_history_model,
            manufacturer_name=score_inputs.get("manufacturer_name"),
            notify_max_price=rule.get("_notify_max_price"),
            estimated_margin_eur=profit.margin_abs if profit else None,
            estimated_margin_pct=profit.margin_pct if profit else None,
            resale_confidence=resale_confidence_label,
            negotiation_candidate=negotiation_candidate,
            part_out_gpu_value=part_out_gpu_value,
            part_out_ratio_pct=part_out_ratio_pct,
            is_part_out_candidate=is_part_out_candidate,
            # Dashboard-Transparenz: derselbe Wert, der oben bereits an
            # compute_profit()/compute_deal_score() uebergeben wurde (siehe
            # estimated_resale_price weiter oben in dieser Funktion) --
            # KEINE neue Berechnung, nur additive Durchreichung.
            estimated_resale_price=estimated_resale_price,
        )

    return MatchResult(matched=False)
