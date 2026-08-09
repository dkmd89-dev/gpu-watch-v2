"""API-Blueprint (roadmap.md Phase 3, Schritt 3.3 Fortsetzung): Dashboard-
Startseite, Treffer-Rohdaten und Scan-Anstoß, extrahiert aus app.py.

Kleinstmoeglicher Eingriff: run_scan bleibt in app.py definiert (Extraktion
folgt in einem spaeteren, eigenen Schritt, siehe roadmap.md Phase 3.5) und
wird dieser Route nur als aufrufbare Referenz per Factory-Funktion
uebergeben -- kein zirkulaerer Import.
"""
from pathlib import Path
from typing import Callable

from flask import Blueprint, render_template, jsonify

from persistence.json_store import _load_json
from rules_loader import get_rules
from category_validation import filter_valid_entries
from scoring.profit import MIN_FLIP_MARGIN_PCT
from top_deal import (
    TOP_DEAL_SCORE_THRESHOLD_A,
    TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT,
    TOP_DEAL_SCORE_THRESHOLD_B,
    TOP_DEAL_DISCOUNT_THRESHOLD_B_PCT,
)


def build_deals_blueprint(
    found_file: Path, rules_dir: Path, run_scan: Callable[[], None]
) -> Blueprint:
    """Baut den Blueprint mit den benoetigten Referenzen im Closure auf.
    Aufruf erfolgt einmalig beim App-Start in app.py, NACH der run_scan()-
    Definition (run_scan wird hier nur referenziert, nicht sofort
    aufgerufen), z.B.:

        app.register_blueprint(build_deals_blueprint(
            FOUND_FILE, Path(__file__).parent / "rules", run_scan,
        ))
    """
    bp = Blueprint("deals", __name__)

    @bp.route("/")
    def index():
        found = _load_json(found_file, [])
        # Dashboard-Folgeschritt: vollstaendige Kategorie-Liste aus den Rules
        # (nicht nur aus den aktuell sichtbaren found.json-Eintraegen) fuers
        # Kategorie-Filter-Dropdown im Template -- siehe matcher.py-Kommentar
        # bei "categories". get(..., []) statt [] direkt, falls load_rules()
        # im Legacy-Einzeldatei-Modus laeuft (dort existiert der Key nicht).
        # Phase 15, Schritt 6 (rules_loader.py): gecachter Zugriff statt
        # YAML-Neuparsing bei JEDEM Request -- identisches Rueckgabeformat.
        rules_cfg = get_rules(str(rules_dir))
        # Phase 14, Schritt 2 (PHASE14_DATA_QUALITY_REPORT.md): zentrale
        # Kategorievalidierung -- Eintraege, die bei erneuter Pruefung gegen
        # die AKTUELLEN Regeln nicht mehr (oder einer anderen Kategorie)
        # zugeordnet wuerden, werden hier ausgeblendet. found.json selbst
        # bleibt unveraendert (siehe category_validation.py-Docstring).
        found = filter_valid_entries(found, rules_cfg)
        all_categories = rules_cfg.get("categories", [])
        # Dashboard-Kachel-Folgeschritt: Anzeigenamen je Kategorie (YAML-Feld
        # "label") fuers generische KPI-Kachel-Rendering im Template. get(...,
        # {}) statt {} direkt, falls load_rules() im Legacy-Einzeldatei-Modus
        # laeuft (dort existiert der Key nicht) -- Template faellt dann auf den
        # internen Kategorie-Schluessel als Anzeigename zurueck.
        category_labels = rules_cfg.get("category_labels", {})
        # Top-Deal-Transparenz (Abschnitt 19): Regel-Schwellen aus top_deal.py
        # als Template-Kontext statt hartkodierter Zahlen im HTML/JS -- damit
        # der angezeigte Regeltext nie von den tatsaechlichen Konstanten
        # abweichen kann (single source of truth bleibt top_deal.py).
        top_deal_rule_thresholds = {
            "A": {"score": TOP_DEAL_SCORE_THRESHOLD_A, "discount_pct": TOP_DEAL_DISCOUNT_THRESHOLD_A_PCT},
            "B": {"score": TOP_DEAL_SCORE_THRESHOLD_B, "discount_pct": TOP_DEAL_DISCOUNT_THRESHOLD_B_PCT},
        }
        # Filter-Erweiterung (Abschnitt 20): Schwellen fuer den neuen KPI-Filter
        # (Top-Deals / Sehr gute Deals / Flip-Kandidaten / Neue Top-Deals) im
        # Dashboard. Bewusst dieselben Konstanten wie in api_status() (siehe
        # dortiger Docstring: very_good <=> deal_score >= TOP_DEAL_SCORE_
        # THRESHOLD_A, dieselbe Skala wie stars_meet_minimum(..., "★★★★☆")) --
        # keine neue Zahl, single source of truth bleibt top_deal.py/scoring/
        # profit.py. Wird 1:1 als JS-Konstante injiziert, damit die Browser-
        # Filterlogik nie von der Backend-KPI-Zaehlung abweichen kann.
        kpi_filter_thresholds = {
            "very_good_min_score": TOP_DEAL_SCORE_THRESHOLD_A,
            "flip_min_margin_pct": MIN_FLIP_MARGIN_PCT,
        }
        return render_template(
            "index.html",
            found=found,
            all_categories=all_categories,
            category_labels=category_labels,
            top_deal_rule_thresholds=top_deal_rule_thresholds,
            kpi_filter_thresholds=kpi_filter_thresholds,
        )

    @bp.route("/api/found")
    def api_found():
        # Phase 14, Schritt 2: dieselbe zentrale Revalidierung wie index(),
        # damit /api/found (z.B. externe/mobile Clients) nicht von der
        # Dashboard-Ansicht abweicht.
        found = _load_json(found_file, [])
        rules_cfg = get_rules(str(rules_dir))
        return jsonify(filter_valid_entries(found, rules_cfg))

    @bp.route("/api/scan-now", methods=["POST"])
    def api_scan_now():
        import threading
        threading.Thread(target=run_scan, daemon=True).start()
        return jsonify({"status": "started"})

    return bp
