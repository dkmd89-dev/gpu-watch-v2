"""API-Blueprint (roadmap.md Phase 3, Schritt 3.3 Fortsetzung): Live-Status
fürs Dashboard, extrahiert aus app.py.

Kleinstmoeglicher Eingriff: der mutable Scan-Status (_scan_status-Dict +
_status_lock) bleibt EINZIGE Quelle der Wahrheit in app.py (dort auch von
run_scan() geschrieben) und wird der Route hier nur als Referenz per
Factory-Funktion uebergeben -- kein Kopieren, keine Duplikation des State,
kein zirkulaerer Import.
"""
import threading
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify

from persistence.json_store import _load_json, _tail_log
from scoring.deal_score import stars_meet_minimum
from scoring.profit import MIN_FLIP_MARGIN_PCT


def build_status_blueprint(
    found_file: Path,
    log_file: Path,
    scan_status: dict,
    status_lock: threading.Lock,
    sources: list[str],
) -> Blueprint:
    """Baut den Blueprint mit den benoetigten Referenzen im Closure auf.
    Aufruf erfolgt einmalig beim App-Start in app.py, z.B.:

        app.register_blueprint(build_status_blueprint(
            FOUND_FILE, LOG_FILE, _scan_status, _status_lock, SOURCES,
        ))
    """
    bp = Blueprint("status", __name__)

    @bp.route("/api/status")
    def api_status():
        """Live-Status fürs Dashboard (Phase 8, Schritt 8.1 + 8.2).

        Rein lesend, aggregiert bestehende Daten (found.json + In-Memory-
        Status-State) -- keine neue Persistenz, kein Einfluss auf run_scan().

        top_deal_count zählt Einträge mit is_top_deal=True (Schritt 8.2, jetzt
        neue Score+Discount-Regel siehe top_deal.py).

        Zusätzlich (Auftrag "Top-Deal-Logik optimieren", Abschnitte 11-15) drei
        weitere KPIs, ALLE ausschließlich aus bereits vorhandenen found.json-
        Feldern abgeleitet -- keine neue Persistenz, keine neue Rating-Engine:

        - very_good_deals_count: gute Angebote (deal_stars >= ★★★★☆, also
          deal_score >= 80, dieselbe Skala wie top_deal.TOP_DEAL_SCORE_THRESHOLD_A),
          die aber NICHT zusätzlich Top-Deal sind (Abschnitt 13: keine
          Doppelzählung).
        - flip_candidates_count: Angebote mit estimated_margin_pct >=
          MIN_FLIP_MARGIN_PCT (siehe scoring/profit.py) -- nutzt die bestehende
          Reselling-/Margin-Berechnung, kann sich mit Top-Deal überschneiden
          (Abschnitt 14, ausdrücklich erlaubt).
        - new_top_deals_count: Top-Deals, deren found_at im aktuell laufenden
          bzw. zuletzt gestarteten Scan liegt (Abschnitt 15) -- echte Teilmenge
          von top_deal_count, nutzt das bereits vorhandene found_at-Feld statt
          neuer Zeitstempel-Logik.

        Ältere found.json-Einträge ohne die jeweiligen Felder (is_top_deal,
        deal_stars, estimated_margin_pct, found_at) werden über .get() robust
        als "nicht zutreffend" behandelt statt KeyError.
        """
        found = _load_json(found_file, [])

        with status_lock:
            status_snapshot = dict(scan_status)

        last_scan_started_at = status_snapshot["last_scan_started_at"]
        scan_start_dt = None
        if last_scan_started_at:
            try:
                scan_start_dt = datetime.fromisoformat(last_scan_started_at)
            except ValueError:
                scan_start_dt = None

        category_counts: dict[str, int] = {}
        manufacturer_counts: dict[str, int] = {}
        top_deal_count = 0
        very_good_deals_count = 0
        flip_candidates_count = 0
        new_top_deals_count = 0
        for f in found:
            cat = f.get("category") or "unbekannt"
            category_counts[cat] = category_counts.get(cat, 0) + 1
            # Aeltere found.json-Eintraege aus der Zeit vor dem Hersteller-
            # Detector haben dieses Feld noch nicht -- .get() liefert dafuer
            # robust None statt eines KeyError, "unbekannt" gruppiert sie mit
            # Treffern, bei denen im Titel schlicht keine Marke erkennbar war.
            manufacturer = f.get("manufacturer") or "unbekannt"
            manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1

            is_top_deal = bool(f.get("is_top_deal"))
            if is_top_deal:
                top_deal_count += 1

                found_at = f.get("found_at")
                if scan_start_dt is not None and found_at:
                    try:
                        if datetime.fromisoformat(found_at) >= scan_start_dt:
                            new_top_deals_count += 1
                    except ValueError:
                        pass
            elif stars_meet_minimum(f.get("deal_stars") or "", "★★★★☆"):
                # NICHT is_top_deal (siehe Abschnitt 13: keine Doppelzaehlung).
                very_good_deals_count += 1

            margin_pct = f.get("estimated_margin_pct")
            if margin_pct is not None and margin_pct >= MIN_FLIP_MARGIN_PCT:
                flip_candidates_count += 1

        return jsonify({
            "scan_running": status_snapshot["scan_running"],
            "last_scan_started_at": status_snapshot["last_scan_started_at"],
            "last_scan_finished_at": status_snapshot["last_scan_finished_at"],
            "last_scan_error": status_snapshot["last_scan_error"],
            "next_scan_at": status_snapshot["next_scan_at"],
            "scan_progress": {
                "current": status_snapshot["scan_progress_current"],
                "total": status_snapshot["scan_progress_total"],
            },
            "scanned_count_last_scan": status_snapshot["scanned_count_last_scan"],
            "new_hits_last_scan": status_snapshot["new_hits_last_scan"],
            "saved_count": len(found),
            "category_counts": category_counts,
            "manufacturer_counts": manufacturer_counts,
            "top_deal_count": top_deal_count,
            "very_good_deals_count": very_good_deals_count,
            "flip_candidates_count": flip_candidates_count,
            "new_top_deals_count": new_top_deals_count,
            "sources": sources,
            "scan_log_tail": _tail_log(log_file, 20),
        })

    return bp
