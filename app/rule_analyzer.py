"""Rule Analyzer (Phase 15, Schritt 2 -- PHASE15_OPTIMIERUNG.md, Abschnitte 6-12).

Read-only Diagnosewerkzeug fuer das Regelwerk (rules_cfg, wie von
matcher.load_rules() geliefert). Veraendert NIEMALS YAML-Dateien -- reine
Analyse, keine automatische Reparatur (Auftragsvorgabe, Abschnitt 14).

Architektur
-----------
Eine Regel-Signatur, sechs unabhaengige Pruefungen, ein Sammel-Report:

    analyze_ruleset(rules_cfg) -> RuleAnalysisReport
        check_structure()               Abschnitt 7.1
        check_duplicates()              Abschnitt 7.2
        check_overlaps()                Abschnitt 8
        check_shadowed()                Abschnitt 9
        check_suspicious_require_all_of()  Abschnitt 10
        check_exclude_conflicts()       Abschnitt 11
        check_unreachable()             Abschnitt 12

Jede Pruefung ist einzeln aufrufbar (nimmt dieselbe rules_cfg entgegen wie
matcher.evaluate()) und liefert eine Liste von Finding-Objekten mit
Schweregrad INFO/WARNING/ERROR. analyze_ruleset() fuehrt alle Pruefungen
aus und aggregiert das Ergebnis fuer PHASE15_RULE_ANALYSIS_REPORT.md
(Schritt 3, noch nicht Teil dieses Moduls).

Wichtig: der Analyzer nutzt matcher._contains_term()/_any_term() (Single
Source of Truth fuer Wortgrenzen-Matching, siehe matcher.py-Docstring),
statt eine zweite, moeglicherweise abweichende Matching-Logik zu bauen.

Grenzen (bewusst, siehe Auftrag Abschnitt 8 "Overlap ist nicht automatisch
ein Fehler"): Shadow-/Overlap-Erkennung basiert auf Heuristiken ueber die
Titel-Wortraeume von `match`/`require_all_of` (Substring-/Teilmengen-
Vergleiche), nicht auf einem vollstaendigen Boolean-SAT-Solver. Ergebnisse
sind Kandidaten fuer manuelle Pruefung, keine bewiesenen Tatsachen.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from itertools import combinations

from matcher import _any_term, _contains_term

# requirements:-Schluessel, die _evaluate_hardware_requirements() (matcher.py)
# tatsaechlich auswertet. Alles andere waere ein stilles No-Op.
KNOWN_REQUIREMENT_KEYS = {
    "min_ram_gb",
    "ram_type_exclude",
    "min_ssd_gb",
    "max_ssd_gb",
    "min_psu_watt",
    "max_psu_watt",
    "min_cpu",
    "case",
    "requires_dedicated_gpu",
    "preferred_gpu_only",
}

# Top-Level-Regel-Felder, die evaluate() (matcher.py) tatsaechlich liest.
# Alles andere in einer Regel wird von evaluate() ignoriert -- entweder
# bewusst (Metadaten wie "label") oder als stiller Tippfehler/totes Feld.
KNOWN_RULE_FIELDS = {
    "label",
    "match",
    "require_all_of",
    "requirements",
    "exclude",
    "price_history_model",
    "max_price",
    "min_vram_gb",
    "deal_rating",
    "resale_price_group",
    "negotiation_tolerance_pct",
    "negotiation_min_score",
    "negotiation_score_component",
    # intern von _load_rules_from_dir() angehaengt (siehe matcher.py)
    "_category",
    "_category_exclude_terms",
    # Phase 15 (kontrollierter Review, "Variante C"): kontextbewusster
    # Exclude-Gegenpart, siehe matcher.py::_any_conditional_exclude().
    "_category_exclude_unless_preceded_by",
    "_ignore_global_excludes",
    "_scoring_weights",
    "_notify_max_price",
}

SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}


@dataclass
class Finding:
    severity: str  # "ERROR" | "WARNING" | "INFO"
    check: str
    message: str
    category: str | None = None
    rule_label: str | None = None
    details: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_ORDER:
            raise ValueError(f"Ungueltiger Schweregrad: {self.severity!r}")


@dataclass
class RuleAnalysisReport:
    findings: list[Finding]
    rule_count: int
    category_count: int

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "ERROR"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "WARNING"]

    @property
    def infos(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "INFO"]

    def count_by_check(self, check: str) -> int:
        return sum(1 for f in self.findings if f.check == check)


def _rule_terms(rule: dict) -> list[str]:
    """Alle Titel-Begriffe, die ein Match dieser Regel ausloesen koennten
    (match-Liste flach + alle require_all_of-Gruppen flach). Reine
    Positivbedingungen, keine requirements:/Preis-Angaben."""
    terms: list[str] = list(rule.get("match") or [])
    for group in rule.get("require_all_of") or []:
        terms.extend(group or [])
    return terms


def _rule_excludes(rule: dict, global_excludes: list[str]) -> list[str]:
    excludes = list(rule.get("exclude") or [])
    excludes.extend(rule.get("_category_exclude_terms") or [])
    ignored = set(rule.get("_ignore_global_excludes") or [])
    excludes.extend(t for t in global_excludes if t not in ignored)
    return excludes


def _signature(rule: dict) -> str:
    """Kanonische Signatur der MATCHING-relevanten Regelfelder (analog zu
    matcher.compute_ruleset_signature(), aber pro Einzelregel und inkl.
    Preis -- zwei Regeln mit identischer Signatur sind fuer evaluate()
    tatsaechlich ununterscheidbar (bis auf label/price_history_model)."""
    payload = {
        "match": sorted(rule.get("match") or []),
        "require_all_of": sorted(
            tuple(sorted(g)) for g in (rule.get("require_all_of") or [])
        ),
        "requirements": rule.get("requirements"),
        "exclude": sorted(rule.get("exclude") or []),
        "category_exclude_terms": sorted(rule.get("_category_exclude_terms") or []),
        "max_price": rule.get("max_price"),
    }
    return json.dumps(payload, sort_keys=True, default=str)


# ------------------------------------------------------------------
# 7.1 Strukturpruefung
# ------------------------------------------------------------------
def check_structure(rules_cfg: dict) -> list[Finding]:
    findings: list[Finding] = []
    for rule in rules_cfg.get("rules", []):
        category = rule.get("_category")
        label = rule.get("label")

        if not label:
            findings.append(Finding(
                "ERROR", "structure", "Regel ohne 'label' -- Preishistorie/"
                "Deal-Score-Gruppierung faellt auf '?' zurueck.",
                category=category, rule_label=label,
            ))

        match_terms = rule.get("match")
        require_all_of = rule.get("require_all_of")
        requirements = rule.get("requirements")

        if match_terms is not None and not isinstance(match_terms, list):
            findings.append(Finding(
                "ERROR", "structure",
                f"'match' ist kein list, sondern {type(match_terms).__name__} "
                "-- evaluate() erwartet eine Liste von Strings.",
                category=category, rule_label=label,
            ))

        if require_all_of is not None:
            if not isinstance(require_all_of, list):
                findings.append(Finding(
                    "ERROR", "structure",
                    f"'require_all_of' ist kein list, sondern "
                    f"{type(require_all_of).__name__} -- evaluate() iteriert "
                    "ueber Gruppen, ein flacher String wuerde als "
                    "Zeichen-fuer-Zeichen-Liste fehlinterpretiert.",
                    category=category, rule_label=label,
                ))
            else:
                for i, group in enumerate(require_all_of):
                    if not isinstance(group, list):
                        findings.append(Finding(
                            "ERROR", "structure",
                            f"require_all_of[{i}] ist kein list, sondern "
                            f"{type(group).__name__} ('{group}') -- wird von "
                            "_any_term() als Zeichenfolge statt Begriffsliste "
                            "durchlaufen.",
                            category=category, rule_label=label,
                            details={"group_index": i},
                        ))
                    elif len(group) == 0:
                        findings.append(Finding(
                            "ERROR", "structure",
                            f"require_all_of[{i}] ist eine leere Gruppe -- "
                            "diese Bedingung kann NIE erfuellt werden "
                            "(_any_term(text, []) == False), die Regel ist "
                            "damit unerreichbar.",
                            category=category, rule_label=label,
                            details={"group_index": i},
                        ))

        if rule.get("exclude") is not None and not isinstance(rule["exclude"], list):
            findings.append(Finding(
                "ERROR", "structure",
                f"'exclude' ist kein list, sondern {type(rule['exclude']).__name__}.",
                category=category, rule_label=label,
            ))

        if requirements is not None and not isinstance(requirements, dict):
            findings.append(Finding(
                "ERROR", "structure",
                f"'requirements' ist kein dict, sondern "
                f"{type(requirements).__name__}.",
                category=category, rule_label=label,
            ))
        elif isinstance(requirements, dict):
            unknown = set(requirements) - KNOWN_REQUIREMENT_KEYS
            for key in sorted(unknown):
                findings.append(Finding(
                    "WARNING", "structure",
                    f"Unbekanntes requirements-Feld '{key}' -- wird von "
                    "_evaluate_hardware_requirements() (matcher.py) still "
                    "ignoriert, hat keinen Effekt.",
                    category=category, rule_label=label,
                ))

        max_price = rule.get("max_price")
        if max_price is not None:
            if not isinstance(max_price, (int, float)) or isinstance(max_price, bool):
                findings.append(Finding(
                    "ERROR", "structure",
                    f"'max_price' ist kein Zahlentyp: {max_price!r}.",
                    category=category, rule_label=label,
                ))
            elif max_price <= 0:
                findings.append(Finding(
                    "ERROR", "structure",
                    f"'max_price' ist <= 0: {max_price!r}.",
                    category=category, rule_label=label,
                ))

        # Leere Regel: weder Titel-Stichwoerter noch requirements ->
        # matcht (nach Preis-/Exclude-Pruefung) JEDEN Titel dieser Kategorie.
        if not match_terms and not require_all_of and requirements is None:
            findings.append(Finding(
                "ERROR", "structure",
                "Regel hat weder 'match' noch 'require_all_of' noch "
                "'requirements' -- matcht (Preis/Exclude vorausgesetzt) "
                "JEDEN Titel, der die Kategorie erreicht.",
                category=category, rule_label=label,
            ))

        unknown_fields = set(rule) - KNOWN_RULE_FIELDS
        for key in sorted(unknown_fields):
            findings.append(Finding(
                "WARNING", "structure",
                f"Unbekanntes Regelfeld '{key}' -- wird von evaluate() nicht "
                "gelesen, hat keinen Effekt auf das Matching (Tippfehler? "
                "z.B. 'require_any_of' existiert nicht als Feld, nur "
                "'require_all_of').",
                category=category, rule_label=label,
            ))

    return findings


# ------------------------------------------------------------------
# 7.2 Duplicate Detection
# ------------------------------------------------------------------
def check_duplicates(rules_cfg: dict) -> list[Finding]:
    findings: list[Finding] = []
    rules = rules_cfg.get("rules", [])

    by_signature: dict[str, list[dict]] = {}
    for rule in rules:
        by_signature.setdefault(_signature(rule), []).append(rule)

    for sig_rules in by_signature.values():
        if len(sig_rules) < 2:
            continue
        for a, b in combinations(sig_rules, 2):
            findings.append(Finding(
                "WARNING", "duplicate",
                f"Regel '{a.get('label')}' und '{b.get('label')}' haben "
                "identische Matching-Bedingungen (match/require_all_of/"
                "requirements/exclude/max_price) -- eine der beiden ist "
                "wahrscheinlich redundant (die erste in Iterationsreihenfolge "
                "gewinnt immer, die zweite ist tot).",
                category=a.get("_category"), rule_label=b.get("label"),
                details={"other_rule": a.get("label")},
            ))

    # price_history_model ueber KATEGORIE-Grenzen hinweg geteilt: fuehrt
    # Preishistorie/Marktpreis zweier fachlich unterschiedlicher Kategorien
    # ungewollt zusammen (Abschnitt 7.2: "identische Price-History-Modelle").
    model_categories: dict[str, set[str]] = {}
    for rule in rules:
        phm = rule.get("price_history_model") or rule.get("label")
        model_categories.setdefault(phm, set()).add(rule.get("_category"))
    for phm, cats in model_categories.items():
        if len(cats) > 1:
            findings.append(Finding(
                "WARNING", "duplicate",
                f"price_history_model '{phm}' wird von mehreren Kategorien "
                f"geteilt ({sorted(cats)}) -- Preishistorie/Marktpreis "
                "dieser Kategorien werden dadurch zusammengefuehrt.",
                details={"price_history_model": phm, "categories": sorted(cats)},
            ))

    return findings


# ------------------------------------------------------------------
# 8. Overlap Detection
# ------------------------------------------------------------------
def check_overlaps(rules_cfg: dict) -> list[Finding]:
    """Meldet Regelpaare, deren `match`/`require_all_of`-Begriffe sich
    woertlich ueberschneiden (gemeinsame Begriffe). Kein Fehler an sich
    (Abschnitt 8) -- INFO bei geteilten Kategorien (haeufig gewolltes
    Tier-Muster wie Top-Deal/Guter-Preis/Interessant), WARNING bei
    unterschiedlichen Kategorien (Titel koennte in zwei Kategorien
    gleichzeitig landen, abhaengig von Iterationsreihenfolge).

    Beschraenkt auf (a) reine `match`-Regeln (OR-Semantik: JEDER Begriff
    allein reicht fuer einen Treffer) und (b) MEHRWORT-Begriffe ("steam
    deck", "iphone 15"). Zwei Gruende:

    1. require_all_of-Begriffe werden bewusst NICHT einbezogen (anders als
       bei check_suspicious_require_all_of): ein Begriff aus nur EINER von
       mehreren AND-Gruppen ist eine notwendige, aber keine hinreichende
       Bedingung -- ein flacher Vergleich erzeugte in der Praxis massive
       Falsch-Funde (z.B. "128 gb" taucht sowohl in iPhone- als auch in
       MacBook-Regeln als EINE von mehreren Kapazitaets-Alternativen auf,
       obwohl sich die Titelraeume der Regeln uebergeordnet -- Marke
       "iphone" vs. "macbook" -- gar nicht ueberschneiden koennen).
    2. Einzelne generische Woerter (z.B. "defekt", "controller", "display")
       kommen in einem Ruleset dieser Groesse zwangslaeufig in vielen
       unabhaengigen Regeln als EIN Synonym unter mehreren vor.

    Beide Einschraenkungen wurden gegen das echte Ruleset validiert (Phase
    15 Schritt 2): ohne sie erzeugte der Check > 14.000 groesstenteils
    bedeutungslose Funde -- widerspricht der Prioritaet "Precision >
    Recall" (Auftrag, Abschnitt 34)."""
    findings: list[Finding] = []
    rules = rules_cfg.get("rules", [])

    for a, b in combinations(rules, 2):
        if a.get("require_all_of") or b.get("require_all_of"):
            continue
        terms_a = {t.lower() for t in (a.get("match") or []) if len(t.split()) >= 2}
        terms_b = {t.lower() for t in (b.get("match") or []) if len(t.split()) >= 2}
        if not terms_a or not terms_b:
            continue
        shared = terms_a & terms_b
        if not shared:
            continue
        if a.get("label") == b.get("label"):
            continue

        same_category = a.get("_category") == b.get("_category")
        same_model = (a.get("price_history_model") or a.get("label")) == (
            b.get("price_history_model") or b.get("label")
        )
        if same_category and same_model:
            # Erwartetes Tier-Muster (gleiche Bedingung, versch. max_price) --
            # kein eigener Finding, das ist Normalfall, kein Ueberschneidungs-
            # Risiko im Sinne von Abschnitt 8.
            continue

        severity = "INFO" if same_category else "WARNING"
        findings.append(Finding(
            severity, "overlap",
            f"Regeln '{a.get('label')}' ({a.get('_category')}) und "
            f"'{b.get('label')}' ({b.get('_category')}) teilen Begriff(e) "
            f"{sorted(shared)} -- moegliche Ueberschneidung im Titelraum.",
            category=a.get("_category"), rule_label=a.get("label"),
            details={
                "other_rule": b.get("label"),
                "other_category": b.get("_category"),
                "shared_terms": sorted(shared),
            },
        ))

    return findings


# ------------------------------------------------------------------
# 9. Shadowed Rules
# ------------------------------------------------------------------
def _term_implies(broad_term: str, narrow_term: str) -> bool:
    """True, wenn jeder Titel, der `narrow_term` als Wort(folge) enthaelt,
    zwangslaeufig auch `broad_term` enthaelt -- z.B. "iphone" wird von
    "iphone 15" impliziert (die laengere Phrase enthaelt die kuerzere als
    eigenes Wort). Rein lexikalisch, keine Semantik."""
    return _contains_term(narrow_term.lower(), broad_term.lower())


def _match_space_covers(broad: list[str], narrow: list[str]) -> bool:
    """True, wenn der Titel-Raum von `broad` (OR-Liste) eine Obermenge des
    Titel-Raums von `narrow` (OR-Liste) ist: jeder narrow-Begriff muss
    lexikalisch einen broad-Begriff implizieren."""
    if not broad or not narrow:
        return False
    return all(any(_term_implies(b, n) for b in broad) for n in narrow)


def check_shadowed(rules_cfg: dict) -> list[Finding]:
    """Heuristische Erreichbarkeitspruefung: kann eine fruehere Regel (in
    evaluate()-Iterationsreihenfolge, Abschnitt: 'erste passende Regel
    gewinnt') jeden Titel abfangen, den eine spaetere Regel DERSELBEN
    Kategorie ebenfalls matchen wuerde? Beschraenkt auf `match`-basierte
    Regeln (kein requirements:/require_all_of-Vergleich -- siehe
    Modul-Docstring, Grenzen) und auf dieselbe Kategorie (kategorieuebergreifend
    ist die Iterationsreihenfolge weniger vorhersagbar/beabsichtigt)."""
    findings: list[Finding] = []
    rules = rules_cfg.get("rules", [])

    by_category: dict[str, list[dict]] = {}
    for rule in rules:
        by_category.setdefault(rule.get("_category"), []).append(rule)

    for category, cat_rules in by_category.items():
        for i, earlier in enumerate(cat_rules):
            earlier_match = earlier.get("match")
            if not earlier_match or earlier.get("require_all_of") or earlier.get("requirements"):
                continue
            for later in cat_rules[i + 1:]:
                later_match = later.get("match")
                if not later_match or later.get("require_all_of") or later.get("requirements"):
                    continue
                if not _match_space_covers(earlier_match, later_match):
                    continue

                # Preis-Fenster der fruehen Regel muss das der spaeten
                # abdecken, sonst laesst price_exceeds_max teurere Titel
                # regulaer durchfallen (kein echtes Shadowing).
                earlier_max = earlier.get("max_price")
                later_max = later.get("max_price")
                price_covers = earlier_max is None or (
                    later_max is not None and earlier_max >= later_max
                )
                if not price_covers:
                    continue

                findings.append(Finding(
                    "WARNING", "shadowed",
                    f"Regel '{later.get('label')}' koennte durch die frueher "
                    f"iterierte Regel '{earlier.get('label')}' verdeckt sein "
                    f"(deren match-Begriffe {sorted(set(m.lower() for m in earlier_match))} "
                    "decken lexikalisch alle Titel ab, die "
                    f"'{later.get('label')}' matchen wuerde, bei "
                    "mindestens gleich weitem Preis-Fenster).",
                    category=category, rule_label=later.get("label"),
                    details={"earlier_rule": earlier.get("label")},
                ))

    return findings


# ------------------------------------------------------------------
# 10. require_all_of Suspicion Detection
# ------------------------------------------------------------------
UBIQUITOUS_MIN_RULES = 5  # Kategorie braucht Mindestgroesse, sonst zu wenig Signal
UBIQUITOUS_MIN_SHARE = 0.4  # Begriff muss in >= 40% der Kategorie-Regeln vorkommen


def _ubiquitous_terms_by_category(rules_cfg: dict) -> dict[str, set[str]]:
    """Begriffe, die innerhalb ihrer Kategorie in einem grossen Teil aller
    Regeln vorkommen (z.B. "lego" in lego_minifiguren.yaml: 44 Erwaehnungen
    in 36 Regeln) -- solche Begriffe tragen praktisch keine Trennschaerfe
    mehr, weil fast jeder Titel der Kategorie sie ohnehin enthaelt."""
    rules = rules_cfg.get("rules", [])
    by_category: dict[str, list[dict]] = {}
    for rule in rules:
        by_category.setdefault(rule.get("_category"), []).append(rule)

    result: dict[str, set[str]] = {}
    for category, cat_rules in by_category.items():
        if len(cat_rules) < UBIQUITOUS_MIN_RULES:
            continue
        term_rule_count: dict[str, int] = {}
        for rule in cat_rules:
            terms_in_rule = {t.lower() for t in _rule_terms(rule)}
            for t in terms_in_rule:
                term_rule_count[t] = term_rule_count.get(t, 0) + 1
        threshold = len(cat_rules) * UBIQUITOUS_MIN_SHARE
        result[category] = {
            t for t, n in term_rule_count.items() if n >= threshold
        }
    return result


def check_suspicious_require_all_of(rules_cfg: dict) -> list[Finding]:
    """Meldet den in Phase 12 gefundenen Bug-Musterfall: ein EINZIGES
    require_all_of mit mehreren Begriffen, von denen mindestens einer in
    der Kategorie "ubiquitaer" ist (siehe _ubiquitous_terms_by_category)
    UND mindestens einer NICHT. Ein solcher Begriff (z.B. "lego") traegt
    als ODER-Alternative nichts zur Abgrenzung bei -- die Regel matcht de
    facto bereits durch ihn allein, der eigentlich abgrenzende Begriff
    (z.B. "star wars") wird zur reinen Alternative statt zur Zusatz-
    bedingung (siehe matcher.py::evaluate()-Kommentar zu require_all_of).

    Bewusst NICHT ueber Label-Text-Abgleich (fruehere Version dieses
    Checks): zwei echte, gleichrangige Alternativbegriffe wie "rog ally"/
    "legion go" oder Synonym-Paare wie "switch lite"/"nintendo switch
    lite" werden im Label ebenfalls beide erwaehnt, sind aber KEIN Bug
    (beide sind gleich selten/spezifisch in ihrer Kategorie) -- die
    Haeufigkeits-Heuristik unterscheidet das korrekt (validiert gegen das
    echte Ruleset, Phase 15 Schritt 2)."""
    findings: list[Finding] = []
    ubiquitous_by_category = _ubiquitous_terms_by_category(rules_cfg)

    for rule in rules_cfg.get("rules", []):
        require_all_of = rule.get("require_all_of")
        if not require_all_of or len(require_all_of) != 1:
            continue
        group = require_all_of[0]
        if not isinstance(group, list) or len(group) < 2:
            continue

        ubiquitous = ubiquitous_by_category.get(rule.get("_category"), set())
        group_lower = [t.lower() for t in group]
        ubiquitous_in_group = [t for t in group_lower if t in ubiquitous]
        specific_in_group = [t for t in group_lower if t not in ubiquitous]

        if ubiquitous_in_group and specific_in_group:
            findings.append(Finding(
                "WARNING", "suspicious_require_all_of",
                f"Einzige require_all_of-Gruppe enthaelt {group!r} -- "
                "das wird als ODER ausgewertet (mind. EIN Begriff reicht). "
                f"{ubiquitous_in_group} kommt in >= "
                f"{int(UBIQUITOUS_MIN_SHARE * 100)}% der Regeln dieser "
                "Kategorie vor und traegt daher praktisch keine "
                f"Trennschaerfe bei -- die eigentliche Bedingung "
                f"{specific_in_group} wirkt dadurch nur als Alternative, "
                "nicht als Zusatzbedingung. Moeglicherweise war eine "
                "UND-Verknuepfung (zwei getrennte Gruppen) beabsichtigt.",
                category=rule.get("_category"), rule_label=rule.get("label"),
                details={
                    "group": group,
                    "ubiquitous_terms": ubiquitous_in_group,
                    "specific_terms": specific_in_group,
                },
            ))
    return findings


# ------------------------------------------------------------------
# 11. Exclude Conflicts
# ------------------------------------------------------------------
def check_exclude_conflicts(rules_cfg: dict) -> list[Finding]:
    global_excludes = (rules_cfg.get("defaults") or {}).get("exclude_global", [])

    findings: list[Finding] = []
    for rule in rules_cfg.get("rules", []):
        excludes = {t.lower() for t in _rule_excludes(rule, global_excludes)}
        if not excludes:
            continue

        match_terms = rule.get("match") or []
        if len(match_terms) == 1 and match_terms[0].lower() in excludes:
            findings.append(Finding(
                "ERROR", "exclude_conflict",
                f"'{match_terms[0]}' ist gleichzeitig der einzige match-"
                "Begriff und ein Exclude-Begriff dieser Regel -- die Regel "
                "kann NIE matchen.",
                category=rule.get("_category"), rule_label=rule.get("label"),
            ))
        elif match_terms:
            conflicting = [t for t in match_terms if t.lower() in excludes]
            for t in conflicting:
                findings.append(Finding(
                    "WARNING", "exclude_conflict",
                    f"'{t}' ist sowohl match-Begriff als auch Exclude-"
                    "Begriff -- dieser eine Pfad ist blockiert, andere "
                    "match-Begriffe koennen die Regel aber weiterhin "
                    "ausloesen.",
                    category=rule.get("_category"), rule_label=rule.get("label"),
                    details={"term": t},
                ))

        for i, group in enumerate(rule.get("require_all_of") or []):
            if not isinstance(group, list):
                continue
            if len(group) == 1 and group[0].lower() in excludes:
                findings.append(Finding(
                    "ERROR", "exclude_conflict",
                    f"require_all_of[{i}] besteht nur aus '{group[0]}', was "
                    "gleichzeitig ein Exclude-Begriff ist -- diese Gruppe "
                    "kann NIE erfuellt werden, die Regel ist unerreichbar.",
                    category=rule.get("_category"), rule_label=rule.get("label"),
                    details={"group_index": i},
                ))
            else:
                conflicting = [t for t in group if t.lower() in excludes]
                for t in conflicting:
                    findings.append(Finding(
                        "WARNING", "exclude_conflict",
                        f"require_all_of[{i}] enthaelt '{t}', was gleichzeitig "
                        "ein Exclude-Begriff ist -- dieser eine Alternativ-"
                        "Begriff ist blockiert, andere Begriffe der Gruppe "
                        "koennen sie aber weiterhin erfuellen.",
                        category=rule.get("_category"), rule_label=rule.get("label"),
                        details={"group_index": i, "term": t},
                    ))
    return findings


# ------------------------------------------------------------------
# 12. Unreachable Rules
# ------------------------------------------------------------------
def check_unreachable(rules_cfg: dict) -> list[Finding]:
    """Kombiniert die hoechste-Konfidenz-Faelle aus Struktur-/Exclude-/
    Shadow-Pruefung zu einer eigenen ERROR-Liste 'garantiert unerreichbar'.
    Ergaenzt (dupliziert nicht) die WARNING-Funde der anderen Checks."""
    findings: list[Finding] = []

    structural = check_structure(rules_cfg)
    for f in structural:
        if f.severity == "ERROR" and (
            "unerreichbar" in f.message or "kann NIE" in f.message
        ):
            findings.append(Finding(
                "ERROR", "unreachable", f.message,
                category=f.category, rule_label=f.rule_label, details=f.details,
            ))

    exclude_conflicts = check_exclude_conflicts(rules_cfg)
    for f in exclude_conflicts:
        if f.severity == "ERROR":
            findings.append(Finding(
                "ERROR", "unreachable", f.message,
                category=f.category, rule_label=f.rule_label, details=f.details,
            ))

    return findings


# ------------------------------------------------------------------
# Sammel-Report
# ------------------------------------------------------------------
def analyze_ruleset(rules_cfg: dict) -> RuleAnalysisReport:
    """Fuehrt alle Pruefungen aus und aggregiert das Ergebnis. Read-only --
    rules_cfg wird an keiner Stelle mutiert oder auf Platte geschrieben."""
    findings: list[Finding] = []
    findings.extend(check_structure(rules_cfg))
    findings.extend(check_duplicates(rules_cfg))
    findings.extend(check_overlaps(rules_cfg))
    findings.extend(check_shadowed(rules_cfg))
    findings.extend(check_suspicious_require_all_of(rules_cfg))
    findings.extend(check_exclude_conflicts(rules_cfg))
    findings.extend(check_unreachable(rules_cfg))

    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.check, f.category or "", f.rule_label or ""))

    rules = rules_cfg.get("rules", [])
    categories = {r.get("_category") for r in rules if r.get("_category")}

    return RuleAnalysisReport(
        findings=findings,
        rule_count=len(rules),
        category_count=len(categories) or len(rules_cfg.get("categories", [])),
    )
