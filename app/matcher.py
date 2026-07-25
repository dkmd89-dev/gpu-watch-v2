"""Wendet die Regel-Matrix aus rules.yaml auf einen (Titel, Preis) an."""
from __future__ import annotations
import re
import yaml
from pathlib import Path
from dataclasses import dataclass

from categories.detectors.cpu import detect_cpu, CpuMatch
from categories.detectors.ram import detect_ram_gb, detect_ram_type
from categories.detectors.case import detect_case_type
from categories.detectors.gpu import detect_dedicated_gpu
from categories.detectors.storage import detect_ssd_gb
from categories.detectors.manufacturer import detect_manufacturer
from scoring.deal_score import compute_deal_score, DEFAULT_WEIGHTS

# Legacy-Fallback: wird NUR noch verwendet, wenn load_rules() im alten
# Einzeldatei-Modus (eine rules.yaml ohne Kategorie-Kontext) aufgerufen wird.
# Im neuen Verzeichnis-Modus liegt die Liste stattdessen in der jeweiligen
# Kategorie-YAML unter "exclude_category" (siehe rules/gpu.yaml) und wird
# NUR für die Regeln dieser einen Kategorie angewendet -- andere Kategorien
# (z.B. künftig "office_pc", "gaming_pc") definieren dort bewusst eine
# andere oder leere Liste, da bei ihnen komplette PC-Systeme ja genau das
# gewünschte Ergebnis sind.
PC_AUSSCHLIESSEN = [
    "gaming pc", "gaming-pc", "gamer pc", "spiele pc",
    "setup", "komplett pc", "fertig pc", "pc komplett",
    "system", "computer", "rechner", "workstation",
    "monitor", "monitore", "bildschirm", "tastatur", "maus",
    "mit monitor", "mit bildschirm",
    "komplettsystem", "komplett-system",
]


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


def load_rules(path: str = "rules.yaml") -> dict:
    """Lädt die Regel-Konfiguration.

    Unterstützt zwei Modi (rückwärtskompatibel):
    - `path` zeigt auf eine einzelne YAML-Datei (altes Verhalten,
      z.B. noch vorhandene Alt-Installationen mit rules.yaml).
    - `path` zeigt auf ein Verzeichnis: dann wird `_global.yaml`
      als Basis für `defaults` geladen und alle übrigen `*.yaml`
      Dateien (eine pro Kategorie) werden zusammengeführt. Das
      Ergebnis hat exakt dieselbe Struktur wie beim alten
      Einzeldatei-Modus ({"defaults": {...}, "rules": [...]}), damit
      `evaluate()` unverändert bleibt.
    """
    p = Path(path)

    if p.is_dir():
        return _load_rules_from_dir(p)

    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _load_rules_from_dir(rules_dir: Path) -> dict:
    global_file = rules_dir / "_global.yaml"
    defaults = {}
    notifications = {}
    scoring_weights = {}
    manufacturer_reputation = {}
    if global_file.exists():
        global_cfg = yaml.safe_load(global_file.read_text(encoding="utf-8")) or {}
        defaults = global_cfg.get("defaults", {})
        notifications = global_cfg.get("notifications", {})
        scoring_weights = global_cfg.get("scoring_weights", {})
        # Hersteller-Detector-Folgeschritt: YAML-Reputationstabelle fuer die
        # "hersteller"-Score-Komponente (siehe scoring/deal_score.py). Ohne
        # Eintrag in _global.yaml bleibt dies ein leeres Dict -> die
        # Komponente faellt weiterhin auf den neutralen Platzhalter zurueck
        # (volle Rueckwaertskompatibilitaet, siehe _hersteller_score()).
        manufacturer_reputation = global_cfg.get("manufacturer_reputation", {})

    merged_rules: list[dict] = []
    all_search_terms: set[str] = set()
    category_files = sorted(
        f for f in rules_dir.glob("*.yaml") if f.name != "_global.yaml"
    )
    for cat_file in category_files:
        cat_cfg = yaml.safe_load(cat_file.read_text(encoding="utf-8")) or {}
        category_name = cat_cfg.get("category", cat_file.stem)
        # Jede Kategorie kann eigene, kategorie-weite Ausschlussbegriffe
        # definieren (z.B. "kein komplettes PC-System" bei GPUs). Diese
        # gelten -- anders als die exclude_global-Liste -- nur für Regeln
        # dieser einen Kategorie und werden hier an jede ihrer Regeln
        # angehängt, damit evaluate() sie ohne zusätzlichen Kategorie-
        # Lookup prüfen kann.
        category_excludes = cat_cfg.get("exclude_category", [])
        # Kategorie-eigene Deal-Score-Gewichte (optional). Manche Kategorien
        # (z.B. reine GPU-Angebote) haben strukturell andere Score-Komponenten
        # zur Verfügung als komplette PC-Systeme (siehe gpu.yaml-Kommentar) --
        # daher pro Kategorie überschreibbar statt nur global in _global.yaml.
        # None, falls die Kategorie keine eigenen Gewichte definiert -> Fallback
        # auf die globalen scoring_weights (siehe evaluate()).
        category_scoring_weights = cat_cfg.get("scoring_weights")
        for rule in cat_cfg.get("rules", []):
            rule = dict(rule)  # Kopie, um das Original-YAML-Objekt nicht zu mutieren
            rule["_category"] = category_name
            rule["_category_exclude_terms"] = category_excludes
            rule["_scoring_weights"] = category_scoring_weights
            merged_rules.append(rule)

        # Suchbegriffe aus der Kategorie übernehmen, damit neue Kategorien
        # automatisch mitgesucht werden -- ohne Änderung an app.py.
        all_search_terms.update(cat_cfg.get("search_terms", []))

    # Markiert, dass diese Config aus dem neuen Verzeichnis-Modus stammt --
    # nur dann greifen kategorie-spezifische Ausschlusslisten in evaluate().
    return {
        "defaults": defaults,
        "rules": merged_rules,
        "search_terms": sorted(all_search_terms),
        "notifications": notifications,
        "scoring_weights": scoring_weights,
        "manufacturer_reputation": manufacturer_reputation,
        "_directory_mode": True,
    }


def _vram_gb(title_lower: str) -> int | None:
    m = re.search(r"(\d{1,2})\s*gb", title_lower)
    return int(m.group(1)) if m else None


def _contains_term(text: str, term: str) -> bool:
    """Prüft, ob `term` als GANZES WORT (bzw. ganze Wortfolge) in `text` vorkommt.

    Verhindert False-Positives durch Teilstring-Treffer, z.B. dass der
    Ausschluss-Begriff "system" auch in "Betriebssystem" oder "Kühlsystem"
    anschlägt. re.escape() macht auch Terme mit Leerzeichen ("gaming pc")
    oder Sonderzeichen ("nitro+") sicher nutzbar.
    """
    pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"
    return re.search(pattern, text, flags=re.UNICODE) is not None


def _any_term(text: str, terms: list[str]) -> bool:
    return any(_contains_term(text, t) for t in terms)


def _ist_kompletter_pc(title_lower: str) -> bool:
    """Prüft ob der Titel auf einen kompletten PC hindeutet."""
    return _any_term(title_lower, PC_AUSSCHLIESSEN)


# ============================================================
# Hardware-Anforderungsprüfung (Phase 5: Office-PC/Gaming-PC)
# ============================================================
# Diese Funktionen prüfen die Ausgabe der Detectors (categories/detectors/)
# gegen die "requirements:"-Angaben einer Kategorie-Regel. Jede Funktion
# ist bewusst eigenstständig testbar und kennt nichts von YAML-Parsing
# oder der restlichen evaluate()-Logik.

def _cpu_meets_requirement(cpu: CpuMatch | None, requirement: dict) -> bool:
    """Prüft eine erkannte CPU gegen eine Mindestanforderung pro Hersteller.

    requirement-Format: {"intel": {"min_tier_rank": 5, "min_generation": 8},
                          "amd": {"min_tier_rank": 5, "min_generation": 2000}}
    Fehlt der erkannte Hersteller im requirement-Dict, gilt die Anforderung
    als NICHT erfüllt (z.B. eine Intel-Anforderung lässt keine AMD-CPU zu,
    außer AMD ist ebenfalls im requirement-Dict definiert).
    """
    if cpu is None:
        return False

    brand_req = requirement.get(cpu.brand.lower())
    if brand_req is None:
        return False

    tier_digit = re.search(r"\d", cpu.tier)
    tier_rank = int(tier_digit.group()) if tier_digit else 0

    min_tier_rank = brand_req.get("min_tier_rank")
    if min_tier_rank is not None and tier_rank < min_tier_rank:
        return False

    min_generation = brand_req.get("min_generation")
    if min_generation is not None and cpu.generation < min_generation:
        return False

    return True


def _ram_meets_requirement(ram_gb: int | None, ram_type: str | None, requirement: dict) -> bool:
    """Prüft erkannte RAM-Größe/-Typ gegen eine Mindestanforderung.

    Fehlende RAM-Erkennung (ram_gb is None) gilt als NICHT erfüllt, wenn
    ein min_gb gefordert ist -- ohne erkennbare RAM-Angabe im Titel kann
    die Mindestanforderung nicht bestätigt werden.
    """
    min_gb = requirement.get("min_gb")
    if min_gb is not None:
        if ram_gb is None or ram_gb < min_gb:
            return False

    type_exclude = requirement.get("type_exclude", [])
    if ram_type is not None and ram_type in type_exclude:
        return False

    return True


def _case_meets_requirement(case_match, requirement: dict) -> bool:
    """Prüft den erkannten Gehäusetyp gegen eine Ausschluss-Anforderung.

    Keine erkennbare Gehäuseform (case_match is None) gilt als ERFÜLLT --
    die meisten Anzeigen nennen den Formfaktor gar nicht explizit, das
    darf kein PC-Angebot pauschal ausschließen.
    """
    if case_match is None:
        return True

    exclude_categories = requirement.get("exclude_categories", [])
    if case_match.category in exclude_categories:
        return False

    return True


def _gpu_meets_requirement(gpu_match, requires_dedicated_gpu: bool, preferred_only: bool = False) -> bool:
    """Prüft, ob eine geforderte dedizierte GPU vorhanden ist.

    requires_dedicated_gpu=False bedeutet "nicht erforderlich", schließt
    aber Angebote MIT dedizierter GPU nicht aus (z.B. Office-PC mit
    zusätzlicher GPU ist weiterhin ein gültiger Office-PC-Treffer).

    preferred_only=True verlangt zusätzlich, dass die erkannte GPU auf
    der Phase-5-Vorzugsliste steht (siehe categories.detectors.gpu) --
    für eine höherwertige Deal-Einstufung (z.B. "Top-Deal" nur bei
    bevorzugter GPU, "Okay" bei jeder anderen dedizierten GPU).
    """
    if requires_dedicated_gpu and gpu_match is None:
        return False
    # preferred_only ist eine VERSCHÄRFUNG der GPU-Pflicht ("muss zusätzlich
    # eine Vorzugs-GPU sein") und hat daher nur eine Wirkung, wenn überhaupt
    # eine dedizierte GPU gefordert ist. Ohne requires_dedicated_gpu=True gibt
    # es keine GPU-Anforderung, an die preferred_only "verschärfen" könnte.
    if requires_dedicated_gpu and preferred_only and (gpu_match is None or not gpu_match.is_preferred):
        return False
    return True


def _evaluate_hardware_requirements(title_lower: str, requirements: dict) -> tuple[bool, dict]:
    """Orchestriert die Detector-Aufrufe für eine "requirements:"-Regel.

    Ruft nur die Detectors auf, die für die jeweils angegebenen
    Anforderungen tatsächlich gebraucht werden. Gibt zusätzlich zum
    Ergebnis ein "features"-Dict mit den erkannten Rohwerten zurück
    (ram_gb, ram_type, cpu, case, gpu -- je nachdem, was tatsächlich
    geprüft wurde), damit compute_deal_score() diese Werte für die
    Score-Berechnung weiterverwenden kann, ohne dieselben Detectors
    ein zweites Mal aufzurufen.
    """
    features: dict = {}

    if "min_ram_gb" in requirements or "ram_type_exclude" in requirements:
        ram_gb = detect_ram_gb(title_lower)
        ram_type = detect_ram_type(title_lower)
        features["ram_gb"] = ram_gb
        features["ram_type"] = ram_type
        ram_requirement = {
            "min_gb": requirements.get("min_ram_gb"),
            "type_exclude": requirements.get("ram_type_exclude", []),
        }
        if not _ram_meets_requirement(ram_gb, ram_type, ram_requirement):
            return False, features

    if "min_cpu" in requirements:
        cpu = detect_cpu(title_lower)
        features["cpu"] = cpu
        if not _cpu_meets_requirement(cpu, requirements["min_cpu"]):
            return False, features

    if "case" in requirements:
        case_match = detect_case_type(title_lower)
        features["case"] = case_match
        if not _case_meets_requirement(case_match, requirements["case"]):
            return False, features

    if "requires_dedicated_gpu" in requirements or "preferred_gpu_only" in requirements:
        gpu_match = detect_dedicated_gpu(title_lower)
        features["gpu"] = gpu_match
        requires_dedicated = requirements.get("requires_dedicated_gpu", False)
        preferred_only = requirements.get("preferred_gpu_only", False)
        if not _gpu_meets_requirement(gpu_match, requires_dedicated, preferred_only):
            return False, features

    return True, features


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

    return {
        "cpu_headroom": cpu_headroom,
        "ram_headroom_gb": ram_headroom_gb,
        "has_ssd": has_ssd,
        "has_dedicated_gpu": has_dedicated_gpu,
        "manufacturer_name": manufacturer_name,
    }


def evaluate(
    title: str,
    price: float,
    rules_cfg: dict,
    market_prices: dict[str, float] | None = None,
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
    """
    title_l = title.lower()
    defaults = rules_cfg.get("defaults", {})
    global_excludes = defaults.get("exclude_global", [])
    directory_mode = rules_cfg.get("_directory_mode", False)

    # 1. Globaler Ausschluss (defekt, bastler, etc.) -- gilt für ALLE Kategorien
    if _any_term(title_l, global_excludes):
        return MatchResult(matched=False)

    # 2. Legacy-Einzeldatei-Modus (keine Kategorie-Information vorhanden):
    #    komplette PCs weiterhin unconditional ausschließen, exakt wie
    #    im ursprünglichen Verhalten vor der Kategorie-Aufteilung.
    if not directory_mode and _ist_kompletter_pc(title_l):
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

        # Kategorie-spezifischer Ausschluss (nur im Verzeichnis-Modus, z.B.
        # "kein komplettes PC-System" bei GPUs). Jede Kategorie bringt ihre
        # eigene Liste mit -- Kategorien, die keine definieren, schließen
        # nichts zusätzlich aus.
        if directory_mode:
            category_excludes = rule.get("_category_exclude_terms", [])
            if category_excludes and _any_term(title_l, category_excludes):
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
        if max_price is not None and price > max_price:
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
        score_result = compute_deal_score(
            price=price,
            max_price=max_price,
            deal_rating=rule.get("deal_rating"),
            weights=scoring_weights,
            market_price=market_price,
            manufacturer_reputation=rules_cfg.get("manufacturer_reputation") or None,
            **score_inputs,
        )

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
        )

    return MatchResult(matched=False)
