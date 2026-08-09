"""Wendet die Regel-Matrix aus rules.yaml auf einen (Titel, Preis) an."""
from __future__ import annotations
import logging
import re
import yaml
from pathlib import Path
from dataclasses import dataclass

from categories.registry import discover_categories
from categories.detectors.cpu import detect_cpu, CpuMatch
from categories.detectors.ram import detect_ram_gb, detect_ram_type
from categories.detectors.case import detect_case_type
from categories.detectors.gpu import detect_dedicated_gpu
from categories.detectors.storage import detect_ssd_gb
from categories.detectors.psu import detect_psu_watt
from categories.detectors.manufacturer import detect_manufacturer
from categories.detectors.condition import detect_condition
from categories.detectors.lieferumfang import detect_lieferumfang
from scoring.deal_score import compute_deal_score, DEFAULT_WEIGHTS, COMPONENT_KEYS
from scoring.profit import compute_profit

logger = logging.getLogger(__name__)

# Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16): Default-
# Schwellenwert (Prozent), ab der eine im PC-Titel erkannte GPU als
# "macht den PC im Grunde nur als GPU-Verkauf lohnenswert" gilt --
# gpu_market_price / pc_price * 100 >= dieser Wert. Greift nur, falls
# _global.yaml keine eigene "part_out_detection"-Sektion definiert
# (aeltere Configs) -- analog zu duplicate_detection.py's Modulkonstanten,
# volle Rueckwaertskompatibilitaet.
DEFAULT_PART_OUT_THRESHOLD_PCT = 70.0

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
    condition_scores = {}
    lieferumfang_signal_scores = {}
    fees = {}
    duplicate_detection_cfg = {}
    part_out_detection_cfg = {}
    if global_file.exists():
        global_cfg = yaml.safe_load(global_file.read_text(encoding="utf-8")) or {}
        defaults = dict(global_cfg.get("defaults", {}))
        # Bugfix: "exclude_global:" liegt in _global.yaml als eigener
        # Top-Level-Key (Geschwister von "defaults:"), NICHT darunter
        # verschachtelt. evaluate() erwartet die Liste aber unter
        # defaults["exclude_global"] (identisch zum alten Einzeldatei-
        # Modus, siehe tests/fixtures/legacy_single_file_rules.yaml, wo
        # exclude_global tatsaechlich UNTER defaults: steht). Ohne diese
        # Zeile wurde exclude_global im Verzeichnis-Modus nie extrahiert
        # -> global_excludes war in evaluate() immer [] -> der globale
        # Ausschluss (defekt/kaputt/bastler/tausch/...) griff bei KEINER
        # Kategorie mehr. dict(...) oben kopiert defaults, damit dieses
        # Zuweisen das Original-YAML-Objekt nicht mutiert.
        defaults["exclude_global"] = global_cfg.get("exclude_global", [])
        notifications = global_cfg.get("notifications", {})
        scoring_weights = global_cfg.get("scoring_weights", {})
        # Hersteller-Detector-Folgeschritt: YAML-Reputationstabelle fuer die
        # "hersteller"-Score-Komponente (siehe scoring/deal_score.py). Ohne
        # Eintrag in _global.yaml bleibt dies ein leeres Dict -> die
        # Komponente faellt weiterhin auf den neutralen Platzhalter zurueck
        # (volle Rueckwaertskompatibilitaet, siehe _hersteller_score()).
        manufacturer_reputation = global_cfg.get("manufacturer_reputation", {})
        # roadmap.md Phase 6, Schritt 6d: analog zu manufacturer_reputation
        # oben -- leere Dicts, falls _global.yaml keine "condition_scores"-/
        # "lieferumfang_signal_scores"-Sektion definiert (aeltere Configs,
        # oder bewusst noch nicht kalibriert) -> beide Komponenten fallen
        # dann weiterhin auf den neutralen Platzhalter zurueck (siehe
        # scoring/deal_score.py::_zustand_score()/_lieferumfang_score()).
        condition_scores = global_cfg.get("condition_scores", {})
        lieferumfang_signal_scores = global_cfg.get("lieferumfang_signal_scores", {})
        # Reselling-/Arbitrage-Konzept (STATUS.md Abschnitt 16): Gebühren-
        # modell fuer scoring/profit.py::compute_profit(). Analog zu
        # manufacturer_reputation oben -- leeres Dict, falls _global.yaml
        # keine "fees:"-Sektion definiert (aeltere Configs) -> profit.py
        # faellt dann auf neutrale 0-Defaults je Kostenposition zurueck,
        # kein Crash (volle Rueckwaertskompatibilitaet).
        fees = global_cfg.get("fees", {})
        # Baustein 5 (Duplicate-/Cross-Posting-Erkennung, STATUS.md
        # Abschnitt 16): additiver Key analog zu fees/manufacturer_reputation
        # -- leeres Dict, falls _global.yaml keine "duplicate_detection:"-
        # Sektion definiert (aeltere Configs). app.py faellt dann auf die
        # Modulkonstanten in duplicate_detection.py zurueck (kein Crash,
        # volle Rueckwaertskompatibilitaet).
        duplicate_detection_cfg = global_cfg.get("duplicate_detection", {})
        # Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16):
        # additiver Key analog zu duplicate_detection -- leeres Dict, falls
        # _global.yaml keine "part_out_detection:"-Sektion definiert
        # (aeltere Configs). evaluate() faellt dann auf
        # DEFAULT_PART_OUT_THRESHOLD_PCT zurueck (kein Crash, volle
        # Rueckwaertskompatibilitaet).
        part_out_detection_cfg = global_cfg.get("part_out_detection", {})

    # Baustein 3, Schritt 1: Mapping-Tabelle GPU-Detector-Modellname ->
    # price_history_model (siehe rules/mappings/component_values.yaml).
    # Bewusst NICHT ueber den category_files-Glob unten geladen (siehe
    # Kommentar in component_values.yaml: eine *.yaml direkt in rules/
    # wuerde faelschlich als leere Kategorie eingelesen) -- eigener,
    # expliziter Ladepfad in einem Unterverzeichnis. Fehlt die Datei
    # (aeltere Installationen ohne Baustein 3) -> leeres Dict, Part-Out-
    # Erkennung bleibt in evaluate() fuer alle Modelle inaktiv (kein Crash).
    gpu_model_to_price_history_model: dict[str, str] = {}
    component_values_file = rules_dir / "mappings" / "component_values.yaml"
    if component_values_file.exists():
        component_values_cfg = yaml.safe_load(
            component_values_file.read_text(encoding="utf-8")
        ) or {}
        gpu_model_to_price_history_model = component_values_cfg.get(
            "gpu_model_to_price_history_model", {}
        )

    merged_rules: list[dict] = []
    all_search_terms: set[str] = set()
    all_categories: set[str] = set()
    # Kategorieweise-Auswertung-Auftrag: Reihenfolge, in der app.py die
    # Treffer NACH dem Scan gruppiert auswertet/loggt (siehe run_scan()).
    # Niedrigere Zahl = zuerst. Kategorien ohne eigene Angabe laufen danach,
    # untereinander alphabetisch (Fallback-Wert +inf sorgt dafuer, dass sie
    # in der finalen Sortierung ans Ende rutschen).
    category_priorities: dict[str, float] = {}
    # Dashboard-Kachel-Folgeschritt: Anzeigename je Kategorie (YAML-Feld
    # "label", z.B. "Gaming-PC" statt des internen Schluessels "gaming_pc").
    # Faellt auf den internen Schluessel zurueck, falls eine Kategorie kein
    # "label" definiert -- volle Rueckwaertskompatibilitaet.
    category_labels: dict[str, str] = {}
    # Option 2 ("Flip-Kandidaten-Logik optimieren", STATUS.md Abschnitt 33b):
    # Mapping {price_history_model: resale_price_group}. Ermoeglicht einer
    # YAML-Regel, fuer die estimated_resale_price-Schaetzung eine groebere
    # Gruppe als ihr eigenes price_history_model zu nutzen (optionaler Key
    # "resale_price_group" je Regel) -- OHNE market_price/deal_score/
    # Notification-Gate zu beeinflussen, die weiterhin exakt nach
    # price_history_model gruppieren (siehe price_stats.py::
    # group_by_resale_group()). Regeln ohne eigenen "resale_price_group"
    # bilden weiterhin nur sich selbst ab (volle Rueckwaertskompatibilitaet).
    resale_price_groups: dict[str, str] = {}
    # Migration auf die Plugin-Registry (categories/registry.py): liefert
    # dieselbe Datei-Menge/Reihenfolge wie der vorherige manuelle Glob hier
    # (identischer Ausschluss "_global.yaml", identischer Namens-Fallback
    # "category"-Feld -> Dateiname), zusaetzlich robust gegen einzelne
    # defekte YAML-Dateien (Warnung + Skip statt Absturz der gesamten
    # Rule-Ladung, siehe discover_categories()-Docstring). Ersetzt die
    # bisherige Duplizierung derselben Discovery-Logik an zwei Stellen.
    for plugin in discover_categories(rules_dir).values():
        cat_cfg = plugin.config
        category_name = plugin.name
        all_categories.add(category_name)
        category_priorities[category_name] = cat_cfg.get("scan_priority", float("inf"))
        category_labels[category_name] = cat_cfg.get("label", category_name)
        # Jede Kategorie kann eigene, kategorie-weite Ausschlussbegriffe
        # definieren (z.B. "kein komplettes PC-System" bei GPUs). Diese
        # gelten -- anders als die exclude_global-Liste -- nur für Regeln
        # dieser einen Kategorie und werden hier an jede ihrer Regeln
        # angehängt, damit evaluate() sie ohne zusätzlichen Kategorie-
        # Lookup prüfen kann.
        category_excludes = cat_cfg.get("exclude_category", [])
        # Optionaler Gegenpart zu exclude_global (_global.yaml): manche
        # Kategorien bilden ausdrücklich Bastler-/Reparatur-Angebote ab
        # (z.B. "PS5 Controller mit Stick Drift" als eigene, günstigere
        # Deal-Klasse) und sollen dafür NICHT durch den globalen
        # "defekt"/"bastler"-Ausschluss blockiert werden. exclude_global
        # gilt weiterhin für ALLE Kategorien, die diesen Key nicht setzen
        # (Default: leere Liste -> 100% identisches Verhalten zu vorher).
        # Nur die hier explizit gelisteten Begriffe werden für diese
        # Kategorie von der globalen Sperre ausgenommen -- alle anderen
        # globalen Ausschlüsse (z.B. "tausch") greifen unverändert weiter.
        category_ignore_global_excludes = cat_cfg.get("ignore_global_excludes", [])
        # Kategorie-eigene Deal-Score-Gewichte (optional). Manche Kategorien
        # (z.B. reine GPU-Angebote) haben strukturell andere Score-Komponenten
        # zur Verfügung als komplette PC-Systeme (siehe gpu.yaml-Kommentar) --
        # daher pro Kategorie überschreibbar statt nur global in _global.yaml.
        # None, falls die Kategorie keine eigenen Gewichte definiert -> Fallback
        # auf die globalen scoring_weights (siehe evaluate()).
        category_scoring_weights = cat_cfg.get("scoring_weights")
        # Notification-Gate-Folgeschritt: kategorie-eigenes Preislimit fuer
        # den ntfy-Push (optional). Grund: das globale gate_max_price aus
        # _global.yaml gilt sonst pauschal fuer ALLE Kategorien -- bei
        # Gaming-PCs (typisch 200-550€) und Office-PCs (typisch 130-300€)
        # unterschreitet aber praktisch kein Treffer ein einheitliches,
        # fuer reine GPUs gedachtes Preislimit. None, falls die Kategorie
        # keins definiert -> Fallback auf das globale gate_max_price
        # (siehe evaluate()/app.py, volle Rueckwaertskompatibilitaet).
        category_notify_max_price = cat_cfg.get("notify_max_price")
        for rule in cat_cfg.get("rules", []):
            rule = dict(rule)  # Kopie, um das Original-YAML-Objekt nicht zu mutieren
            rule["_category"] = category_name
            rule["_category_exclude_terms"] = category_excludes
            rule["_ignore_global_excludes"] = category_ignore_global_excludes
            rule["_scoring_weights"] = category_scoring_weights
            rule["_notify_max_price"] = category_notify_max_price
            merged_rules.append(rule)

            # Option 2: siehe Kommentar bei resale_price_groups oben.
            # Gleiche price_history_model-Herleitung wie in evaluate()
            # (rule.get("price_history_model", rule_label)), damit der
            # Lookup-Key identisch zu dem ist, den evaluate() spaeter
            # tatsaechlich verwendet.
            _rule_label = rule.get("label", "?")
            _phm = rule.get("price_history_model", _rule_label)
            resale_price_groups[_phm] = rule.get("resale_price_group", _phm)

        # Suchbegriffe aus der Kategorie übernehmen, damit neue Kategorien
        # automatisch mitgesucht werden -- ohne Änderung an app.py.
        all_search_terms.update(cat_cfg.get("search_terms", []))

    # Markiert, dass diese Config aus dem neuen Verzeichnis-Modus stammt --
    # nur dann greifen kategorie-spezifische Ausschlusslisten in evaluate().
    return {
        "defaults": defaults,
        "rules": merged_rules,
        "search_terms": sorted(all_search_terms),
        # Dashboard-Folgeschritt (Kategorie-Dropdown-Fix): VOLLSTAENDIGE
        # Liste aller bekannten Kategorien aus den Rules -- unabhaengig
        # davon, ob gerade Treffer dieser Kategorie in found.json vorhanden
        # sind. Grund: das Dashboard leitete das Kategorie-Dropdown bisher
        # NUR aus den aktuell sichtbaren Karten ab (found.json, gedeckelt
        # auf FOUND_MAX_ITEMS=200) -- seltene Kategorien wie sata_ssd
        # verschwanden dadurch aus dem Filter, sobald sie durch haeufigere
        # Treffer (gpu/gaming_pc/office_pc) aus dem Fenster verdraengt
        # wurden, obwohl real weiterhin Treffer dieser Kategorie existieren
        # (siehe price_history.jsonl/gpu_watch.log).
        "categories": sorted(all_categories),
        # Dashboard-Kachel-Folgeschritt: Anzeigename je Kategorie, damit
        # templates/index.html die KPI-Kacheln generisch (ohne Kategorie-
        # Namen im HTML/JS hart zu codieren) rendern kann. Additiver Key --
        # Aufrufer, die ihn nicht kennen (aeltere app.py-Version, Legacy-
        # Einzeldatei-Modus ohne diesen Key), bleiben unveraendert lauffaehig.
        "category_labels": category_labels,
        # Kategorieweise-Auswertung-Auftrag: Scan-Reihenfolge fuer app.py.
        # Sortiert nach scan_priority (aufsteigend), Kategorien ohne eigene
        # Angabe (Prioritaet +inf) alphabetisch dahinter.
        "category_order": sorted(all_categories, key=lambda c: (category_priorities.get(c, float("inf")), c)),
        "notifications": notifications,
        "scoring_weights": scoring_weights,
        "manufacturer_reputation": manufacturer_reputation,
        # roadmap.md Phase 6, Schritt 6d: additive Keys, analog zu
        # manufacturer_reputation oben -- Aufrufer, die sie nicht kennen
        # (aeltere app.py-Version, Legacy-Einzeldatei-Modus), bleiben
        # unveraendert lauffaehig.
        "condition_scores": condition_scores,
        "lieferumfang_signal_scores": lieferumfang_signal_scores,
        # Reselling-/Arbitrage-Konzept (STATUS.md Abschnitt 16): additiver
        # Key, analog zu manufacturer_reputation -- Aufrufer, die ihn nicht
        # kennen (aeltere app.py-Version, Legacy-Einzeldatei-Modus), bleiben
        # unveraendert lauffaehig, da dort schlicht nicht darauf zugegriffen
        # wird. In diesem Schritt noch NICHT an evaluate()/deal_score.py
        # angebunden (folgt in einem separaten Schritt, siehe STATUS.md).
        "fees": fees,
        # Baustein 5 (Duplicate-/Cross-Posting-Erkennung, STATUS.md
        # Abschnitt 16): additiver Key, analog zu fees oben -- Aufrufer, die
        # ihn nicht kennen (aeltere app.py-Version, Legacy-Einzeldatei-Modus),
        # bleiben unveraendert lauffaehig.
        "duplicate_detection": duplicate_detection_cfg,
        # Baustein 3 (Bundle-/Part-Out-Erkennung, STATUS.md Abschnitt 16,
        # Schritt 1+2): additive Keys, analog zu duplicate_detection oben --
        # Aufrufer, die sie nicht kennen (aeltere app.py-Version, Legacy-
        # Einzeldatei-Modus), bleiben unveraendert lauffaehig.
        "gpu_model_to_price_history_model": gpu_model_to_price_history_model,
        "part_out_detection": part_out_detection_cfg,
        # Option 2 ("Flip-Kandidaten-Logik optimieren", STATUS.md Abschnitt
        # 33b): additiver Key, analog zu gpu_model_to_price_history_model
        # oben -- Aufrufer, die ihn nicht kennen (aeltere app.py-Version,
        # Legacy-Einzeldatei-Modus), bleiben unveraendert lauffaehig.
        "resale_price_groups": resale_price_groups,
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


def _storage_meets_requirement(ssd_gb: int | None, requirement: dict) -> bool:
    """Prüft die erkannte SSD-Kapazität gegen eine Mindest-/Höchstgrenze.

    requirement-Format: {"min_ssd_gb": 320, "max_ssd_gb": 639} (beide
    Grenzen optional, mind. eine muss gesetzt sein, damit der Aufrufer
    diese Prüfung überhaupt anstößt -- siehe _evaluate_hardware_requirements).

    Fehlende Kapazitätserkennung (ssd_gb is None) gilt als NICHT erfüllt,
    analog zu _ram_meets_requirement: ohne erkennbare Größe im Titel kann
    eine Kapazitäts-Anforderung nicht bestätigt werden.
    """
    if ssd_gb is None:
        return False

    min_gb = requirement.get("min_ssd_gb")
    if min_gb is not None and ssd_gb < min_gb:
        return False

    max_gb = requirement.get("max_ssd_gb")
    if max_gb is not None and ssd_gb > max_gb:
        return False

    return True


def _psu_meets_requirement(psu_watt: int | None, requirement: dict) -> bool:
    """Prüft die erkannte Netzteilleistung (Watt) gegen eine Mindest-/
    Höchstgrenze.

    requirement-Format: {"min_psu_watt": 550, "max_psu_watt": 1200} (beide
    Grenzen optional, mind. eine muss gesetzt sein, damit der Aufrufer
    diese Prüfung überhaupt anstößt -- siehe _evaluate_hardware_requirements).
    Analog zu _storage_meets_requirement(), inkl. gleicher Begründung für
    "keine Erkennung -> nicht erfüllt": ohne erkennbare Watt-Zahl im Titel
    kann eine Leistungs-Anforderung nicht bestätigt werden.
    """
    if psu_watt is None:
        return False

    min_watt = requirement.get("min_psu_watt")
    if min_watt is not None and psu_watt < min_watt:
        return False

    max_watt = requirement.get("max_psu_watt")
    if max_watt is not None and psu_watt > max_watt:
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
    (ram_gb, ram_type, ssd_gb, psu_watt, cpu, case, gpu -- je nachdem,
    was tatsächlich geprüft wurde), damit compute_deal_score() diese
    Werte für die Score-Berechnung weiterverwenden kann, ohne dieselben
    Detectors ein zweites Mal aufzurufen.
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

    if "min_ssd_gb" in requirements or "max_ssd_gb" in requirements:
        ssd_gb = detect_ssd_gb(title_lower)
        features["ssd_gb"] = ssd_gb
        storage_requirement = {
            "min_ssd_gb": requirements.get("min_ssd_gb"),
            "max_ssd_gb": requirements.get("max_ssd_gb"),
        }
        if not _storage_meets_requirement(ssd_gb, storage_requirement):
            return False, features

    if "min_psu_watt" in requirements or "max_psu_watt" in requirements:
        psu_watt = detect_psu_watt(title_lower)
        features["psu_watt"] = psu_watt
        psu_requirement = {
            "min_psu_watt": requirements.get("min_psu_watt"),
            "max_psu_watt": requirements.get("max_psu_watt"),
        }
        if not _psu_meets_requirement(psu_watt, psu_requirement):
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


def compute_ruleset_signature(rules_cfg: dict) -> str:
    """Deterministischer Fingerprint über die MATCHING-relevanten Teile von
    rules_cfg (Phase 11, Punkt B: sichere Re-Evaluierung).

    Aendert sich, sobald sich Regeln aendern/hinzukommen/wegfallen, die das
    Ergebnis von evaluate() beeinflussen koennten (Label, Kategorie,
    match/require_all_of/requirements, exclude, price_history_model,
    max_price) -- NICHT bei rein kosmetischen YAML-Aenderungen
    (Kommentare, Score-Gewichte, notify_max_price etc.), die das
    Match-Ergebnis eines Titels nicht beeinflussen koennen.

    BEWUSST EIN GLOBALER Hash ueber die GESAMTE Regel-Liste, kein
    Hash pro Kategorie: evaluate() iteriert bereits heute linear durch
    ALLE Regeln aller Kategorien in EINEM Durchlauf (erste passende Regel
    gewinnt, siehe evaluate()-Docstring) -- es gibt in der bestehenden
    Architektur keine Vorstellung von "nur Kategorie X pruefen", ohne
    evaluate() selbst umzubauen. Ein Hash pro Kategorie wuerde denselben
    vollstaendigen Durchlauf erzwingen wie ein globaler Hash (jede
    Neubewertung eines bisher ungematchten Angebots muss ohnehin die
    komplette, aktuelle Regel-Liste in der richtigen Prioritaetsreihenfolge
    durchlaufen) -- ohne Verhaltensunterschied, nur mit mehr Zustand pro
    seen.json-Eintrag. Kleinstmoegliche, architektur-konforme Loesung
    (siehe Auftrag: "keine unnoetige Neugestaltung des Presence-Systems").
    """
    import hashlib
    import json as _json

    relevant = []
    for rule in rules_cfg.get("rules", []):
        relevant.append({
            "label": rule.get("label"),
            "_category": rule.get("_category"),
            "match": rule.get("match"),
            "require_all_of": rule.get("require_all_of"),
            "requirements": rule.get("requirements"),
            "exclude": rule.get("exclude"),
            "_category_exclude_terms": rule.get("_category_exclude_terms"),
            "price_history_model": rule.get("price_history_model"),
            "max_price": rule.get("max_price"),
            "min_vram_gb": rule.get("min_vram_gb"),
        })
    canonical = _json.dumps(relevant, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


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
