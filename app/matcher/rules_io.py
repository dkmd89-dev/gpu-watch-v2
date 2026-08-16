"""YAML-Regel-Laden und Ruleset-Signatur (Schritt 6 der Modularisierung).

Enthaelt load_rules(), _load_rules_from_dir() und compute_ruleset_signature() --
der groesste verbleibende Extraktionsblock aus core.py. Reine Datenladung/
-transformation, keine Matching-Logik (die bleibt in core.py::evaluate()).
"""
from __future__ import annotations

import yaml
from pathlib import Path

from categories.registry import discover_categories

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
        # Phase 15 (kontrollierter Review, generische Loesung "Variante C"):
        # optionaler, kontextbewusster Gegenpart zu exclude_category. Manche
        # Zubehoer-Begriffe (z.B. "Ladekabel") sollen eine Regel nur dann
        # blockieren, wenn sie ALLEIN stehen ("PS5 Controller Ladekabel" =
        # Standalone-Zubehoer), nicht wenn sie ein echtes Geraet-Angebot
        # mit erwaehntem Zubehoer beschreiben ("PS5 Controller inkl.
        # Ladekabel" = Bundle). {Begriff: [erlaubte Bundle-Konnektoren]} --
        # ein Begriff hier gehoert NICHT zusaetzlich in exclude_category
        # (siehe evaluate()), sonst waere die Bedingung wirkungslos (die
        # unbedingte Pruefung dort wuerde ohnehin immer greifen). Default
        # leeres Dict -> 100% identisches Verhalten zu vorher fuer
        # Kategorien, die dieses Feld nicht setzen.
        category_excludes_unless_preceded_by = cat_cfg.get(
            "exclude_category_unless_preceded_by", {}
        )
        # Phase 15 (kontrollierter Folge-Review, "Gehäuse/Shell-Fix"):
        # zweiter, andersartiger kontextbewusster Exclude-Gegenpart. Manche
        # Begriffe (z.B. "gehäuse") sind NICHT wie "ladekabel" ein reines
        # Zubehoerwort, sondern gleichzeitig eine uebliche Zustands-
        # beschreibung eines kompletten Geraets ("Gehäuse leicht
        # vergilbt/verkratzt"). Eine Adjazenz-Regel wie bei
        # "..._unless_preceded_by" (ein Konnektor unmittelbar davor) passt
        # hier nicht -- die Zustandsbeschreibung steht typischerweise NACH
        # dem Begriff und in wechselndem Abstand ("Gehäuse: leicht
        # vergilbt", "Gehäuse minimal verkratzt"). Der Begriff soll daher
        # NUR ausschliessen, wenn im GESAMTEN Titel KEIN Begriff aus einer
        # Positiv-/Kontextliste vorkommt -- {Begriff: [erlaubte Kontext-/
        # Zustandsbegriffe]}. Bewusst KEIN Adjazenz-/Abstands-Check (siehe
        # _any_conditional_exclude_presence()-Docstring fuer die Abwaegung).
        # Ein Begriff hier gehoert NICHT zusaetzlich in exclude_category
        # (siehe evaluate()), sonst waere die Bedingung wirkungslos. Default
        # leeres Dict -> 100% identisches Verhalten zu vorher fuer
        # Kategorien, die dieses Feld nicht setzen.
        category_excludes_unless_context = cat_cfg.get(
            "exclude_category_unless_also_contains", {}
        )
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
            rule["_category_exclude_unless_preceded_by"] = category_excludes_unless_preceded_by
            rule["_category_exclude_unless_also_contains"] = category_excludes_unless_context
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
def compute_ruleset_signature(rules_cfg: dict) -> str:
    """Deterministischer Fingerprint über die MATCHING-relevanten Teile von
    rules_cfg (Phase 11, Punkt B: sichere Re-Evaluierung).

    Aendert sich, sobald sich Regeln aendern/hinzukommen/wegfallen, die das
    Ergebnis von evaluate() beeinflussen koennten (Label, Kategorie,
    match/require_all_of/requirements, exclude, exclude_category_unless_
    preceded_by, price_history_model, max_price) -- NICHT bei rein
    kosmetischen YAML-Aenderungen (Kommentare, Score-Gewichte,
    notify_max_price etc.), die das Match-Ergebnis eines Titels nicht
    beeinflussen koennen.

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
            # Phase 15 (kontrollierter Review, "Variante C"): MUSS hier
            # enthalten sein -- eine Aenderung ausschliesslich an einer
            # Konnektor-Liste (z.B. "mit" ergaenzt) aendert das Match-
            # Verhalten (siehe evaluate()), muss also den Hash aendern,
            # sonst wuerde sie an presence_tracking/category_validation
            # unbemerkt vorbeigehen (Auftragsvorgabe).
            "_category_exclude_unless_preceded_by": rule.get(
                "_category_exclude_unless_preceded_by"
            ),
            # Phase 15 (kontrollierter Folge-Review, "Gehäuse/Shell-Fix"):
            # analog zum Eintrag oben -- eine Aenderung an der Kontext-
            # begriffsliste aendert das Match-Verhalten (siehe evaluate()),
            # muss also den Hash aendern.
            "_category_exclude_unless_also_contains": rule.get(
                "_category_exclude_unless_also_contains"
            ),
            "price_history_model": rule.get("price_history_model"),
            "max_price": rule.get("max_price"),
            "min_vram_gb": rule.get("min_vram_gb"),
        })
    canonical = _json.dumps(relevant, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
