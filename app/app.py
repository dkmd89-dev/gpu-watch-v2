import os
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, render_template, jsonify

from matcher import load_rules, evaluate
from scrapers import search_kleinanzeigen, search_ebay
from notify import send_ntfy, emoji_for
from scoring.deal_score import stars_meet_minimum
from price_history import append_price_point, make_price_point, read_price_points
from price_stats import compute_all_price_stats

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
SEEN_FILE = DATA_DIR / "seen.json"
FOUND_FILE = DATA_DIR / "found.json"
LOG_FILE = DATA_DIR / "gpu_watch.log"
# Phase 7 (Schritt 7.1): append-only Zeitreihe, unabhaengig von FOUND_MAX_ITEMS-
# Rotation und vom Notification-Gate -- Grundlage fuer Marktpreis-Statistik
# (Schritt 7.2) und Top-Deal-Erkennung (Schritt 7.3).
PRICE_HISTORY_FILE = DATA_DIR / "price_history.jsonl"

# Phase-0-Befund: found.json war hart auf 200 Einträge gekappt, obwohl
# ältere Doku von 1000 sprach (Diskrepanz). Jetzt explizit konfigurierbar
# statt eines stillen Magic Numbers -- Default bleibt bei 200, da found.json
# eine reine Trefferliste fürs Dashboard ist (keine Historie; das übernimmt
# Phase 7 mit price_history.jsonl als append-only Zeitreihe).
FOUND_MAX_ITEMS = int(os.environ.get("FOUND_MAX_ITEMS", "200"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("gpu-watch")

app = Flask(__name__)

_seen_lock = threading.Lock()
_scan_running = False
_scan_lock = threading.Lock()

# Legacy-Fallback: wird NUR verwendet, falls die geladene Regel-Config
# keine eigenen search_terms mitbringt (z.B. alter Einzeldatei-Modus mit
# einer rules.yaml ohne Kategorie-Kopf). Im normalen Betrieb (Verzeichnis-
# Modus) kommen die Suchbegriffe direkt aus den Kategorie-YAMLs
# (rules/gpu.yaml: search_terms), sodass neue Kategorien automatisch
# mitgesucht werden, ohne app.py anzufassen.
SEARCH_TERMS = sorted({
    "RTX 3060 12GB",
    "RTX 3060 Ti",
    "RTX 3070",
    "RTX 4060",
    "RTX 2080 Ti",
    "RX 6700 XT",
    "RX 6750 XT",
    "RX 6800",
    "RX 7600",
    "RX 7600 XT",
})

# Legacy-Fallback: greift nur, falls die geladene Config keinen eigenen
# "notifications"-Block mitbringt (Legacy-Einzeldatei-Modus). Im normalen
# Betrieb (Verzeichnis-Modus) kommen diese Werte aus rules/_global.yaml
# (notifications: urgent_price_threshold / tags).
NOTIFY_URGENT_PRICE_THRESHOLD = 150
NOTIFY_TAGS = ["moneybag"]

# Phase 6b: Benachrichtigungs-Gate. NUR Treffer, die BEIDE Bedingungen
# erfüllen (Mindest-Sternebewertung UND Preisobergrenze), lösen eine
# ntfy-Benachrichtigung aus. Alle anderen Treffer werden weiterhin in
# found.json gespeichert und im Dashboard angezeigt, aber nicht verschickt.
# Legacy-Fallback wie oben: greift nur ohne eigenen "notifications"-Block.
NOTIFY_GATE_MIN_STARS = "★★★★★"
NOTIFY_GATE_MAX_PRICE = 150


def _load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def _save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _load_market_prices(path: Path) -> dict[str, float]:
    """Baut das {price_history_model: Marktpreis}-Mapping aus price_history.jsonl.

    Phase 7 (Schritt 7.5): einmal pro Scan aufgerufen, BEVOR die Item-Schleife
    startet -- die daraus resultierenden Marktpreise werden an evaluate()
    durchgereicht (siehe matcher.py, Schritt 7.4). Fehlt die Datei oder ist
    sie noch leer (z.B. frisch installierte Instanz ohne bisherige Treffer),
    liefert read_price_points() bereits eine leere Liste -- dann ist auch
    dieses Mapping leer und evaluate() verhält sich exakt wie vor Schritt 7.4
    (reines regelbasiertes max_price-Signal). Ein Fehler beim Statistik-Aufbau
    darf den Scan nicht abbrechen -- Marktpreise sind eine Zusatzfunktion,
    kein kritischer Pfad (analog zu append_price_point() in price_history.py).
    """
    try:
        points = read_price_points(path)
        stats_by_model = compute_all_price_stats(points)
        return {
            model: stats.market_price
            for model, stats in stats_by_model.items()
            if stats is not None
        }
    except Exception as e:
        log.error("Marktpreis-Statistik konnte nicht berechnet werden: %s", e, exc_info=True)
        return {}


def run_scan():
    global _scan_running

    with _scan_lock:
        if _scan_running:
            log.info("Scan läuft bereits, überspringe...")
            return
        _scan_running = True

    try:
        log.info("Starte Scan...")
        rules_cfg = load_rules(str(Path(__file__).parent / "rules"))
        defaults = rules_cfg["defaults"]

        # Suchbegriffe kommen aus den Kategorie-YAMLs (rules_cfg["search_terms"]).
        # Nur falls eine Config das (noch) nicht mitliefert -- z.B. Legacy-
        # Einzeldatei-Modus -- greift der hart codierte Fallback.
        search_terms = rules_cfg.get("search_terms") or SEARCH_TERMS

        # Benachrichtigungseinstellungen ebenso primär aus der Config.
        notify_cfg = rules_cfg.get("notifications") or {}
        urgent_price_threshold = notify_cfg.get(
            "urgent_price_threshold", NOTIFY_URGENT_PRICE_THRESHOLD
        )
        notify_tags = notify_cfg.get("tags", NOTIFY_TAGS)
        gate_min_stars = notify_cfg.get("gate_min_stars", NOTIFY_GATE_MIN_STARS)
        gate_max_price = notify_cfg.get("gate_max_price", NOTIFY_GATE_MAX_PRICE)

        global_max_price = max(r.get("max_price", 220) for r in rules_cfg["rules"])

        with _seen_lock:
            seen = set(_load_json(SEEN_FILE, []))
            found = _load_json(FOUND_FILE, [])

        raw = []
        raw += search_kleinanzeigen(
            search_terms, defaults["location_plz"], defaults["radius_km"], global_max_price
        )
        raw += search_ebay(search_terms, global_max_price, defaults["location_plz"])

        # Phase 7 (Schritt 7.5): Marktpreise EINMAL pro Scan aus der bisherigen
        # Preishistorie berechnen (nicht pro Item -- price_history.jsonl waechst
        # waehrend des Scans durch append_price_point() weiter unten, ein Re-Read
        # pro Item wuerde unnoetig I/O verursachen und wachsende Ergebnisse waeren
        # ohnehin fuer denselben Scan-Durchlauf nicht gewuenscht).
        market_prices = _load_market_prices(PRICE_HISTORY_FILE)

        new_hits = 0
        for item in raw:
            if item["price"] is None:
                continue
            uid = item["url"]

            with _seen_lock:
                if uid in seen:
                    continue
                seen.add(uid)
                # Sofort persistieren statt erst am Scan-Ende: verhindert,
                # dass ein Crash mitten im Scan dazu führt, dass bereits
                # verarbeitete (und ggf. schon benachrichtigte) Angebote
                # beim nächsten Lauf erneut gematcht und doppelt verschickt
                # werden (siehe Phase-0-Analyse, Befund d).
                _save_json(SEEN_FILE, list(seen))

            result = evaluate(item["title"], item["price"], rules_cfg, market_prices=market_prices)
            if not result.matched:
                continue

            entry = {
                **item,
                "rule": result.rule_label,
                "deal_score": result.deal_score,
                "deal_stars": result.deal_stars,
                "found_at": datetime.now(timezone.utc).isoformat(),
            }

            with _seen_lock:
                found.insert(0, entry)
                # Ebenfalls sofort persistieren (siehe seen.json oben): ohne
                # das würde ein Absturz nach dem seen-Save, aber vor dem
                # bisherigen Scan-Ende-Save, den Treffer endgültig verlieren
                # -- er gilt ja bereits als "seen" und würde beim nächsten
                # Lauf nicht erneut ausgewertet.
                _save_json(FOUND_FILE, found[:FOUND_MAX_ITEMS])

            new_hits += 1

            # Phase 7 (Schritt 7.1): Preishistorie-Datenpunkt fuer JEDEN
            # Treffer, unabhaengig vom Notification-Gate weiter unten (das
            # nur steuert, ob ein ntfy-Push verschickt wird -- fuer die
            # Marktpreis-Statistik zaehlt dagegen jeder gematchte Treffer).
            append_price_point(
                PRICE_HISTORY_FILE,
                make_price_point(
                    price=item["price"],
                    source=item["source"],
                    model=result.price_history_model or result.rule_label or "unbekannt",
                    category=result.category,
                    deal_score=result.deal_score,
                ),
            )

            # Phase 6b: Benachrichtigungs-Gate. Nur Treffer, die BEIDE
            # Bedingungen erfüllen, werden per ntfy verschickt -- alle
            # anderen sind bereits oben in found.json gespeichert und im
            # Dashboard sichtbar, lösen aber keinen Push aus.
            meets_star_gate = stars_meet_minimum(result.deal_stars or "", gate_min_stars)
            meets_price_gate = item["price"] <= gate_max_price

            if meets_star_gate and meets_price_gate:
                emoji = emoji_for(result.deal_rating)
                clean_title = (
                    result.rule_label.replace("[TOP]", "").replace("[GUT]", "").replace("[OK]", "").strip()
                )
                price_str = f"{item['price']:.0f} €"

                send_ntfy(
                    title=f"{emoji} {clean_title} – {price_str}",
                    message=(
                        f"{result.deal_rating or 'Fund'} · {result.deal_stars or ''}\n"
                        f"{item['title']}\n"
                        f"{price_str} · {item['source']} · {item['location']}\n"
                        f"{item['url']}"
                    ),
                    priority="urgent" if item["price"] <= urgent_price_threshold else "default",
                    tags=notify_tags,
                )
                log.info(
                    "BENACHRICHTIGT [%s/%s/%s] %s – %.0f € – %s",
                    result.rule_label, result.deal_rating, result.deal_stars,
                    item["title"], item["price"], item["url"],
                )
            else:
                log.info(
                    "GESPEICHERT (Gate nicht erfüllt: %s/%s) [%s/%s] %s – %.0f € – %s",
                    result.deal_stars, f"≤{gate_max_price}€" if meets_price_gate else f">{gate_max_price}€",
                    result.rule_label, result.deal_rating,
                    item["title"], item["price"], item["url"],
                )

        with _seen_lock:
            _save_json(SEEN_FILE, list(seen))
            _save_json(FOUND_FILE, found[:FOUND_MAX_ITEMS])

        log.info("Scan fertig: %d neue Treffer von %d Angeboten geprüft.", new_hits, len(raw))

    except Exception as e:
        log.exception(f"Fehler im Scan: {e}")
    finally:
        with _scan_lock:
            _scan_running = False


def scheduler_loop():
    interval = int(os.environ.get("SCAN_INTERVAL_MINUTES", "10")) * 60
    while True:
        try:
            run_scan()
        except Exception:
            log.exception("Fehler im Scan-Durchlauf")
        time.sleep(interval)


@app.route("/")
def index():
    found = _load_json(FOUND_FILE, [])
    return render_template("index.html", found=found)


@app.route("/api/found")
def api_found():
    return jsonify(_load_json(FOUND_FILE, []))


@app.route("/api/scan-now", methods=["POST"])
def api_scan_now():
    threading.Thread(target=run_scan, daemon=True).start()
    return jsonify({"status": "started"})


if __name__ == "__main__":
    threading.Thread(target=scheduler_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
