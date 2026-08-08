"""API-Blueprint (roadmap.md Phase 3, Schritt 3.3): reine Lesepfade fuer
Preishistorie-/Time-to-Sell-/Cross-Platform-Statistik, extrahiert aus app.py.

Bewusst NUR die zustandslosen GET-Routen ohne Abhaengigkeit von
_scan_status/_status_lock/run_scan() -- die verbleibenden Routen (index,
api_found, api_status, api_scan_now) bleiben vorerst in app.py, da sie an
den noch nicht extrahierten Scan-Status bzw. run_scan() gekoppelt sind
(folgt in einem spaeteren, eigenen Schritt). Kleinstmoeglicher Eingriff:
Dateipfade werden ueber eine Factory-Funktion uebergeben statt die
DATA_DIR-Konstanten aus app.py zu duplizieren oder zirkulaer zu importieren
-- app.py bleibt einzige Quelle der Wahrheit fuer die Pfade.

URL-Pfade unveraendert (Frontend ruft sie per fest kodiertem fetch()-Pfad
auf, nicht ueber url_for()) -- kein Breaking Change.
"""
from dataclasses import asdict
from pathlib import Path

from flask import Blueprint, jsonify

from price_history import read_price_points
from price_stats import compute_all_price_stats, compute_price_stats
from time_to_sell import read_time_to_sell_points
from time_to_sell_stats import compute_all_time_to_sell_stats
from cross_platform_stats import compute_all_cross_platform_stats


def build_history_blueprint(price_history_file: Path, time_to_sell_file: Path) -> Blueprint:
    """Baut den Blueprint mit den benoetigten Datenpfaden im Closure auf.
    Aufruf erfolgt einmalig beim App-Start in app.py, z.B.:

        app.register_blueprint(
            build_history_blueprint(PRICE_HISTORY_FILE, TIME_TO_SELL_FILE)
        )
    """
    bp = Blueprint("history", __name__)

    @bp.route("/api/price-history")
    def api_price_history_index():
        """Kurz-Übersicht aller price_history_model-Schlüssel mit Statistik,
        aber OHNE Zeitreihe (Schritt 8.3) -- fürs Dashboard, um zu ermitteln,
        für welche Modelle überhaupt Preishistorie/Diagramme verfügbar sind.
        Für die volle Zeitreihe eines einzelnen Modells siehe
        /api/price-history/<model>.
        """
        points = read_price_points(price_history_file)
        stats_by_model = compute_all_price_stats(points)
        return jsonify({
            model: asdict(stats)
            for model, stats in stats_by_model.items()
            if stats is not None
        })

    @bp.route("/api/price-history/<model>")
    def api_price_history_detail(model):
        """Aggregierte Statistik + chronologische Zeitreihe für EIN
        price_history_model (Schritt 8.3), z.B. fürs Preisdiagramm im
        Dashboard.

        Unbekanntes/noch nie gesehenes model -> KEIN 404, sondern stats=null
        und series=[] (analog zum fail-soft-Verhalten von read_price_points()
        bei fehlender Datei) -- ein neu angelegtes Kategorie-/Hardware-Modell
        ohne bisherige Treffer ist kein Fehlerfall, sondern der Normalzustand
        direkt nach dem Anlegen einer neuen YAML-Regel.
        """
        points = read_price_points(price_history_file)
        model_points = sorted(
            (p for p in points if p.model == model), key=lambda p: p.date
        )
        stats = compute_price_stats(model, model_points)

        return jsonify({
            "model": model,
            "stats": asdict(stats) if stats is not None else None,
            "series": [
                {
                    "price": p.price,
                    "date": p.date,
                    "source": p.source,
                    "deal_score": p.deal_score,
                }
                for p in model_points
            ],
        })

    @bp.route("/api/time-to-sell")
    def api_time_to_sell():
        """Time-to-Sell-Statistik je Kategorie fürs Dashboard (Baustein 6,
        Schritt 4) -- nutzt ausschließlich die bestehenden Funktionen aus
        Schritt 3 (time_to_sell.read_time_to_sell_points(),
        time_to_sell_stats.compute_all_time_to_sell_stats()), kein neuer
        Berechnungscode. Analog zu /api/price-history: leeres Dict, solange
        noch kein Delisting erkannt wurde (kein Fehlerfall, siehe
        read_time_to_sell_points()-Docstring).
        """
        points = read_time_to_sell_points(time_to_sell_file)
        stats_by_category = compute_all_time_to_sell_stats(points)
        return jsonify({
            category: asdict(stats)
            for category, stats in stats_by_category.items()
        })

    @bp.route("/api/cross-platform")
    def api_cross_platform():
        """Cross-Platform-Preisvergleich je price_history_model fürs Dashboard
        (Baustein 4, Schritt 2) -- nutzt ausschließlich die bestehenden
        Funktionen aus Schritt 1 (price_history.read_price_points(),
        cross_platform_stats.compute_all_cross_platform_stats()), kein neuer
        Berechnungscode. Analog zu /api/time-to-sell: leeres Dict, solange
        für kein Modell Datenpunkte aus mindestens 2 verschiedenen Quellen
        vorliegen (kein Fehlerfall, siehe compute_cross_platform_stats()-
        Docstring).

        by_source ist ein verschachteltes Dict je Quelle (SourceStats) --
        asdict() serialisiert dataclasses rekursiv, kein manuelles Flatten
        nötig.
        """
        points = read_price_points(price_history_file)
        stats_by_model = compute_all_cross_platform_stats(points)
        return jsonify({
            model: asdict(stats)
            for model, stats in stats_by_model.items()
        })

    return bp
