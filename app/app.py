import os
import time
import logging
import logging.handlers
import threading
from pathlib import Path
from datetime import datetime, timedelta, timezone

from flask import Flask

from matcher import load_rules, evaluate
from scrapers import search_kleinanzeigen, search_ebay
from scrapers.registry import discover_scrapers
from notify import send_ntfy, emoji_for, rating_stars_for
from scoring.deal_score import stars_meet_minimum
from price_history import append_price_point, make_price_point, read_price_points
from duplicate_detection import find_duplicate, normalize_title
from presence_tracking import (
    migrate_seen_data, mark_seen, mark_matched, detect_newly_delisted,
    prune_delisted_entries, enforce_max_size, DEFAULT_DELISTING_THRESHOLD_SCANS,
)
from time_to_sell import (
    make_time_to_sell_point, append_time_to_sell_point, read_time_to_sell_points,
)
from time_to_sell_stats import compute_all_time_to_sell_stats
from deal_intelligence import classify_deal
from top_deal import evaluate_top_deal
from scoring.profit import MIN_FLIP_MARGIN_PCT
from persistence.json_store import _load_json, _save_json
from services.statistics_service import (
    _load_price_stats,
    _load_resale_stats_by_group,
    _market_prices_from_stats,
    _resale_prices_from_stats,
)
from api.history import build_history_blueprint
from api.deals import build_deals_blueprint
from api.status import build_status_blueprint
from scan.scheduler import build_scheduler_loop

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
SEEN_FILE = DATA_DIR / "seen.json"
FOUND_FILE = DATA_DIR / "found.json"
LOG_FILE = DATA_DIR / "gpu_watch.log"
# Phase 7 (Schritt 7.1): append-only Zeitreihe, unabhaengig von FOUND_MAX_ITEMS-
# Rotation und vom Notification-Gate -- Grundlage fuer Marktpreis-Statistik
# (Schritt 7.2) und Top-Deal-Erkennung (Schritt 7.3).
PRICE_HISTORY_FILE = DATA_DIR / "price_history.jsonl"
# Baustein 6 (Time-to-Sell-Schätzung, STATUS.md Abschnitt 16), Schritt 2:
# append-only Zeitreihe analog PRICE_HISTORY_FILE, aber für Verweildauern
# delisteter Angebote statt Preise (siehe time_to_sell.py).
TIME_TO_SELL_FILE = DATA_DIR / "time_to_sell.jsonl"

# Phase-0-Befund: found.json war hart auf 200 Einträge gekappt, obwohl
# ältere Doku von 1000 sprach (Diskrepanz). Jetzt explizit konfigurierbar
# statt eines stillen Magic Numbers -- Default bleibt bei 200, da found.json
# eine reine Trefferliste fürs Dashboard ist (keine Historie; das übernimmt
# Phase 7 mit price_history.jsonl als append-only Zeitreihe).
FOUND_MAX_ITEMS = int(os.environ.get("FOUND_MAX_ITEMS", "200"))

# Schritt C: Deals-Aufraeumen. found.json wurde bisher nur nach Anzahl
# (FOUND_MAX_ITEMS) gekappt, nicht nach Alter -- ein selten scannendes
# Setup oder eine Kategorie mit wenig Treffern konnte dadurch beliebig
# alte, laengst nicht mehr verfuegbare Angebote im Dashboard zeigen. Bei
# jedem Scan werden Eintraege mit found_at aelter als DEAL_MAX_AGE_DAYS
# entfernt (Default 7, per Env-Var konfigurierbar -- analog FOUND_MAX_ITEMS).
DEAL_MAX_AGE_DAYS = int(os.environ.get("DEAL_MAX_AGE_DAYS", "7"))

# Kernursache-Fix (Produktions-Vorfall: seen.json auf 9 MB angewachsen und
# korrumpiert, siehe STATUS.md Abschnitt 26): seen.json wuchs bisher
# unbegrenzt (presence_tracking.py dokumentierte das bereits als bekanntes
# Verhalten). Bei jedem Scan werden bereits DELISTETE Eintraege entfernt,
# deren last_seen aelter als SEEN_DELISTED_MAX_AGE_DAYS ist -- fuer sie
# wurde der Time-to-Sell-Datenpunkt bereits erzeugt, die Historie wird
# danach nicht mehr gebraucht (siehe prune_delisted_entries()-Docstring).
# Noch aktive (nicht delistete) Eintraege bleiben unabhaengig vom Alter
# erhalten. Kurzer Default (3 Tage) statt DEAL_MAX_AGE_DAYS-Default (7),
# da hier bereits das staerkere "delisted"-Kriterium greift, nicht nur
# das Alter allein.
SEEN_DELISTED_MAX_AGE_DAYS = int(os.environ.get("SEEN_DELISTED_MAX_AGE_DAYS", "3"))

# Sofort-Fix (roadmap.md Phase 4, Persistenz-Analyse): harte Obergrenze fuer
# AKTIVE (nicht delistete) seen.json-Eintraege, Ergaenzung zur alter-
# basierten Bereinigung oben -- siehe presence_tracking.enforce_max_size().
# 50.000 Eintraege * ca. 150-250 Byte/Eintrag ergibt ca. 7,5-12,5 MB als
# Obergrenze (Default, bereits einmal freigegeben, siehe STATUS.md
# Abschnitt 31 -- durch einen spaeteren, unabhaengigen Commit versehentlich
# aus app.py verschwunden, hier wiederhergestellt).
SEEN_MAX_ITEMS = int(os.environ.get("SEEN_MAX_ITEMS", "50000"))

# Schritt B: Log-Rotation. Ohne Rotation wuchs gpu_watch.log unbegrenzt
# (ein Long-Running-Container ohne Log-Limit ist ein bekanntes Betriebs-
# risiko -- volle Disk faengt irgendwann den ganzen Container ein). Grenzen
# per Env-Var konfigurierbar, Defaults wie angefordert: 1MB pro Datei,
# 5 Backups (gpu_watch.log.1 .. .log.5). Rueckwaertskompatibel: derselbe
# LOG_FILE-Pfad, dasselbe Format, StreamHandler unveraendert -- nur der
# FileHandler wird durch die rotierende Variante ersetzt.
LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", str(1_000_000)))
LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("gpu-watch")


class _SuppressStatusPollingFilter(logging.Filter):
    """Log-Aufraeumen (Ziel 2): unterdrueckt die wiederkehrenden Dashboard-
    Polling-Zugriffe auf /api/status im werkzeug-Access-Log (Frontend fragt
    das alle 5 Sekunden ab -- ohne Informationswert, blaeht das Log aber
    stark auf, siehe gpu_watch.txt). Andere Requests (z.B. POST
    /api/scan-now, GET /, GET /api/price-history) bleiben weiterhin
    sichtbar -- nur diese eine, hochfrequente Polling-Route wird gefiltert.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "/api/status" not in record.getMessage()


# werkzeug ist der Logger-Name, unter dem Flasks Dev-Server jeden Request
# loggt (siehe die "GET ... HTTP/1.1 200 -"-Zeilen). Filter NUR dort
# registrieren, nicht global -- unser eigener "gpu-watch"-Logger bleibt
# unberuehrt.
logging.getLogger("werkzeug").addFilter(_SuppressStatusPollingFilter())

app = Flask(__name__)
app.register_blueprint(build_history_blueprint(PRICE_HISTORY_FILE, TIME_TO_SELL_FILE))

_seen_lock = threading.Lock()
_scan_running = False
_scan_lock = threading.Lock()

# Phase 8 (Schritt 8.1): separater Status-State fürs Dashboard (/api/status).
# Bewusst NICHT mit _scan_running/_scan_lock oben zusammengelegt -- jene
# beiden steuern ausschließlich die "kein doppelter Scan"-Sperre und sollen
# durch die Dashboard-Anbindung nicht mit zusätzlicher Verantwortung
# (Fortschritts-/Zeitstempel-Tracking) belastet werden. Ein eigener Lock
# hält beide Belange unabhängig voneinander änderbar.
_status_lock = threading.Lock()
_scan_status: dict = {
    "scan_running": False,
    "last_scan_started_at": None,
    "last_scan_finished_at": None,
    "last_scan_error": None,
    "next_scan_at": None,
    "scan_progress_current": 0,
    "scan_progress_total": 0,
    "scanned_count_last_scan": 0,
    "new_hits_last_scan": 0,
    # roadmap.md Phase 2 (Scan-Performance-Metriken): rein additive Felder,
    # zunaechst nur "gemessen" -- keine Optimierung, siehe run_scan()-
    # Metrik-Erfassung unten. Alle *_sec-Werte sind Sekunden (float),
    # None solange kein Scan gelaufen ist.
    "scan_duration_last_scan_sec": None,
    "scrape_duration_by_source_sec": {},
    "deduplicated_count_last_scan": 0,
    # Hinweis: matcher.evaluate() berechnet Matching UND Deal-Score in
    # einem Aufruf (nicht getrennt aufrufbar ohne matcher.py anzufassen,
    # was ausserhalb des Phase-2-Scopes liegt -- siehe Begruendung im
    # zugehoerigen Schritt-Report). Diese Zeit deckt daher beides ab.
    "matching_and_scoring_duration_sec": None,
    "price_stats_duration_sec": None,
    "persistence_duration_sec": None,
    "notification_duration_sec": None,
}

# Suchquellen-Übersicht fürs Dashboard. Statisch, da app.py aktuell fest
# search_kleinanzeigen()/search_ebay() aufruft (siehe unten) -- wird erst mit
# dem Scraper-Plugin-System (Phase 9/10) dynamisch aus den geladenen Plugins
# abgeleitet.
SOURCES = ["kleinanzeigen", "ebay"]
app.register_blueprint(build_status_blueprint(
    FOUND_FILE, LOG_FILE, _scan_status, _status_lock, SOURCES,
))

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
NOTIFY_GATE_MIN_STARS = "★★☆☆☆"
NOTIFY_GATE_MAX_PRICE = 150


def _cleanup_old_deals(found: list[dict], max_age_days: int) -> tuple[list[dict], int]:
    """Entfernt Einträge aus `found`, deren `found_at` älter als max_age_days ist.

    Schritt C: Bei jedem Scan aufgerufen, damit found.json nicht auf
    Anzahl (FOUND_MAX_ITEMS) beschränkt bleibt, sondern auch veraltete
    Angebote (typischerweise längst nicht mehr verfügbar) automatisch
    verschwinden.

    Rückwärtskompatibel: Legacy-Einträge OHNE `found_at`-Feld (aus der
    Zeit vor dessen Einführung in Phase 8) werden bewusst NICHT entfernt
    -- ohne Zeitstempel lässt sich ihr Alter nicht bestimmen, ein
    Entfernen wäre eine Vermutung statt einer Tatsache (analog zum
    dokumentierten Jinja `is defined`-Bugfix für fehlendes deal_score).

    Gibt (bereinigte Liste, Anzahl entfernter Einträge) zurück.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    kept = []
    removed = 0
    for entry in found:
        found_at = entry.get("found_at")
        if not found_at:
            kept.append(entry)
            continue
        try:
            found_dt = datetime.fromisoformat(found_at)
        except (ValueError, TypeError):
            # Nicht parsebarer Zeitstempel -> konservativ behalten statt
            # einen evtl. gültigen Deal versehentlich zu loeschen.
            kept.append(entry)
            continue
        if found_dt >= cutoff:
            kept.append(entry)
        else:
            removed += 1
    return kept, removed






def run_scan():
    global _scan_running

    with _scan_lock:
        if _scan_running:
            log.info("Scan läuft bereits, überspringe...")
            return
        _scan_running = True

    with _status_lock:
        _scan_status["scan_running"] = True
        _scan_status["last_scan_started_at"] = datetime.now(timezone.utc).isoformat()
        _scan_status["last_scan_error"] = None
        _scan_status["scan_progress_current"] = 0
        _scan_status["scan_progress_total"] = 0

    try:
        log.info("Starte Scan...")
        # roadmap.md Phase 2: Gesamtdauer-Messung. perf_counter() statt
        # time.time(), da hier nur Differenzen (keine Wanduhrzeit) gebraucht
        # werden -- monotone, fuer Laufzeitmessung geeignete Quelle.
        _scan_start_perf = time.perf_counter()
        scrape_duration_by_source: dict[str, float] = {}
        matching_and_scoring_duration = 0.0
        persistence_duration = 0.0
        notification_duration = 0.0
        already_seen_count = 0

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

        # Baustein 5 (Duplicate-/Cross-Posting-Erkennung, STATUS.md
        # Abschnitt 16): Toleranz-%/Zeitfenster jetzt aus _global.yaml
        # konfigurierbar (analog notify_cfg oben). Fehlende einzelne Werte
        # (oder komplett fehlende Sektion -> dup_cfg == {}) fallen auf die
        # Modulkonstanten in duplicate_detection.py zurueck (find_duplicate()-
        # Parameter-Defaults) -- kein Crash, volle Rueckwaertskompatibilitaet.
        dup_cfg = rules_cfg.get("duplicate_detection") or {}
        duplicate_kwargs = {}
        if "price_tolerance_pct" in dup_cfg:
            duplicate_kwargs["price_tolerance_pct"] = dup_cfg["price_tolerance_pct"]
        if "window_days" in dup_cfg:
            duplicate_kwargs["window_days"] = dup_cfg["window_days"]

        # Baustein 6 (Time-to-Sell-Schätzung, STATUS.md Abschnitt 16),
        # Schritt 2: Delisting-Schwelle (Anzahl aufeinanderfolgender Scans
        # ohne erneutes Sichten) analog aus _global.yaml konfigurierbar,
        # gleiches Muster wie duplicate_detection oben. Fehlt der Wert/die
        # Sektion, greift presence_tracking.DEFAULT_DELISTING_THRESHOLD_SCANS.
        presence_cfg = rules_cfg.get("presence_tracking") or {}
        delisting_threshold_scans = presence_cfg.get(
            "delisting_threshold_scans", DEFAULT_DELISTING_THRESHOLD_SCANS
        )

        with _seen_lock:
            # Baustein 6 (Time-to-Sell-Schätzung, STATUS.md Abschnitt 16),
            # Schritt 1: seen.json speichert je URL jetzt zusätzlich
            # first_seen/last_seen statt nur eine flache URL-Liste zu sein.
            # migrate_seen_data() überführt ein bestehendes Alt-Format
            # automatisch (siehe presence_tracking.py-Moduldoku) --
            # rückwärtskompatibel, kein manueller Migrationsschritt nötig.
            seen = migrate_seen_data(_load_json(SEEN_FILE, []))
            found = _load_json(FOUND_FILE, [])
            # Schritt C: veraltete Deals (> DEAL_MAX_AGE_DAYS) vor dem
            # Scan entfernen, damit found.json/das Dashboard nicht auf
            # laengst nicht mehr verfuegbare Angebote hinweisen. Sofort
            # gespeichert, unabhaengig davon ob dieser Scan neue Treffer
            # findet (analog zum bisherigen seen.json/found.json-Muster).
            found, removed_count = _cleanup_old_deals(found, DEAL_MAX_AGE_DAYS)
            if removed_count:
                log.info(
                    "Deals-Aufräumen: %d Angebot(e) älter als %d Tage entfernt.",
                    removed_count, DEAL_MAX_AGE_DAYS,
                )
                _save_json(FOUND_FILE, found)

        # Hinweis: das eigentliche Scraping (raw = [...]) findet weiter unten
        # ueber die Plugin-Registry statt (siehe "Plugin-Registry (Schritt 2)"),
        # NACHDEM category_order/price_stats_by_model berechnet sind -- hier
        # nur noch Vorbereitung, kein Scraping-Aufruf mehr an dieser Stelle.
        #
        # Phase 7 (Schritt 7.5) + Phase 8 (Schritt 8.2): Preisstatistik EINMAL
        # pro Scan aus der bisherigen Preishistorie berechnen (nicht pro Item --
        # price_history.jsonl waechst waehrend des Scans durch append_price_point()
        # weiter unten, ein Re-Read pro Item wuerde unnoetig I/O verursachen und
        # wachsende Ergebnisse waeren ohnehin fuer denselben Scan-Durchlauf nicht
        # gewuenscht). Liefert die Grundlage fuer ZWEI Signale aus derselben
        # Berechnung: market_prices (Deal-Score, Schritt 7.5) und
        # price_stats_by_model (Top-Deal-Erkennung, Schritt 8.2).
        # roadmap.md Phase 2: Price-Statistics-Zeit -- deckt den gesamten
        # Block ab (Markt- UND Resale-Preisstatistik), da beide auf
        # derselben Preishistorie-Datei aufbauen und im selben Schritt
        # (einmal pro Scan) berechnet werden, siehe Kommentar oben.
        _price_stats_start = time.perf_counter()
        price_stats_by_model = _load_price_stats(PRICE_HISTORY_FILE)
        market_prices = _market_prices_from_stats(price_stats_by_model)
        # Option 2 (STATUS.md Abschnitt 33b): resale_price_groups fehlt bei
        # aelteren Configs (Legacy-Einzeldatei-Modus) -> leeres Dict ->
        # _resale_prices_from_stats() faellt auf das bisherige Verhalten
        # zurueck (siehe dortiger Docstring).
        resale_price_groups = rules_cfg.get("resale_price_groups") or {}
        resale_stats_by_group = _load_resale_stats_by_group(
            PRICE_HISTORY_FILE, resale_price_groups
        )
        resale_prices = _resale_prices_from_stats(
            price_stats_by_model, resale_stats_by_group, resale_price_groups
        )
        price_stats_duration = time.perf_counter() - _price_stats_start

        # roadmap.md Phase 7, Schritt 7b: Time-to-Sell-Statistik EINMAL pro
        # Scan berechnen (analog price_stats_by_model oben), NICHT pro
        # Treffer -- reines Kategorie-Aggregat (siehe time_to_sell_stats.py),
        # aendert sich innerhalb eines Scan-Laufs ohnehin nicht (Delisting-
        # Erkennung, die neue Datenpunkte erzeugen wuerde, laeuft an anderer
        # Stelle im selben run_scan()-Durchlauf). Rein informative
        # Zusatzangabe fuers Deal-Intelligence-Feld unten -- KEIN Einfluss
        # auf deal_score/Notification-Gate/bestehende Top-Deal-Logik.
        time_to_sell_stats_by_category = compute_all_time_to_sell_stats(
            read_time_to_sell_points(TIME_TO_SELL_FILE)
        )

        # Baustein 5 (Duplicate-/Cross-Posting-Erkennung, STATUS.md Abschnitt
        # 16): Rohdatenpunkte EINMAL pro Scan laden (analog price_stats_by_model
        # oben) statt pro Treffer neu einzulesen. Waechst waehrend des Scans
        # lokal mit (siehe Phase 2 unten) -- so werden auch Cross-Postings
        # INNERHALB desselben Scan-Laufs erkannt, nicht erst beim naechsten Lauf.
        price_points_this_scan = read_price_points(PRICE_HISTORY_FILE)

        # Kategorieweise-Auswertung-Auftrag: Reihenfolge aus matcher.py
        # (scan_priority, siehe rules/*.yaml). Fallback auf "categories"
        # (Legacy-Einzeldatei-Modus/keine eigene Priorität definiert).
        category_order = rules_cfg.get("category_order") or rules_cfg.get("categories") or []

        # Phase 1: EINMALIGES Scraping (unveraendert -- ein Requestlauf pro
        # Suchbegriff ueber ALLE Kategorien hinweg, wie bisher. KEINE
        # Aufteilung in mehrere Scraping-Runden pro Kategorie, das wuerde
        # die Anzahl der HTTP-Requests unnoetig vervielfachen).
        #
        # Plugin-Registry (Schritt 2): statt zweier hartcodierter
        # `raw += search_xxx(...)`-Zeilen wird ueber alle per Discovery
        # gefundenen Scraper-Plugins iteriert (siehe scrapers/registry.py).
        #
        # Schritt 3: search_kleinanzeigen() und search_ebay() erfuellen jetzt
        # beide exakt das Scraper-Protocol (search_terms, plz, radius_km,
        # max_price) -- siehe scrapers/base.py. Der bisherige Uebergangs-
        # Adapter (_SCRAPER_CALL_ARGS) entfaellt dadurch: jedes Plugin wird
        # generisch mit denselben vier Argumenten aufgerufen. Eine neue
        # Quelle (Phase 9), die dieses Protocol erfuellt, wird ohne jede
        # Codeaenderung an app.py automatisch mitgescannt.
        raw = []
        scraper_plugins = discover_scrapers()
        for scraper_name, plugin in scraper_plugins.items():
            # roadmap.md Phase 2: Scraping-Zeit je Quelle. Einzeln pro
            # Plugin gemessen (nicht nur gesamt), damit eine einzelne
            # langsame Quelle sichtbar wird statt in der Summe unterzugehen.
            _scrape_start = time.perf_counter()
            raw += plugin.search(
                search_terms, defaults["location_plz"], defaults["radius_km"], global_max_price,
            )
            scrape_duration_by_source[scraper_name] = round(
                time.perf_counter() - _scrape_start, 3
            )

        with _status_lock:
            _scan_status["scan_progress_total"] = len(raw)

        new_hits = 0
        # Baustein 6, Schritt 1: EIN Zeitstempel für den gesamten Scan-Lauf
        # (statt pro Item neu), analog zu "found_at" weiter unten -- ein
        # Scan gilt als ein Zeitpunkt, zu dem alle darin enthaltenen
        # Angebote "gesehen" wurden.
        now_iso = datetime.now(timezone.utc).isoformat()
        # Treffer werden hier nur gesammelt (nach Kategorie gruppiert,
        # Reihenfolge innerhalb einer Kategorie = Scrape-Reihenfolge),
        # die eigentliche Verarbeitung (found.json/price_history/ntfy)
        # passiert danach gruppiert in Phase 2.
        category_buckets: dict[str, list[tuple[dict, object]]] = {c: [] for c in category_order}

        for idx, item in enumerate(raw, start=1):
            with _status_lock:
                _scan_status["scan_progress_current"] = idx

            if item["price"] is None:
                continue
            uid = item["url"]

            with _seen_lock:
                already_seen = uid in seen
                # Baustein 6, Schritt 1: last_seen wird für JEDES erneut
                # gesehene Angebot aktualisiert (auch wenn es unten wegen
                # already_seen übersprungen wird) -- das ist die Grundlage
                # für die spätere Delisting-Erkennung (Schritt 2): ein
                # Angebot gilt dort als delisted, wenn es N Scans lang
                # NICHT mehr aktualisiert wurde. mark_seen() legt bei neuen
                # URLs zusätzlich first_seen an.
                mark_seen(seen, uid, now_iso)
                if already_seen:
                    already_seen_count += 1
                    continue
                # Sofort persistieren statt erst am Scan-Ende: verhindert,
                # dass ein Crash mitten im Scan dazu führt, dass bereits
                # verarbeitete (und ggf. schon benachrichtigte) Angebote
                # beim nächsten Lauf erneut gematcht und doppelt verschickt
                # werden (siehe Phase-0-Analyse, Befund d). Für bereits
                # bekannte URLs (nur last_seen aktualisiert) wird NICHT
                # sofort persistiert -- das wäre bei tausenden bereits
                # bekannten Angeboten pro Scan ein spürbarer I/O-Mehraufwand
                # für eine unkritische Information (last_seen); diese
                # Updates werden gesammelt am Scan-Ende geschrieben (siehe
                # unten). Kein Datenverlustrisiko: bei einem Crash bleibt
                # last_seen für diese Einträge lediglich auf dem Stand des
                # vorherigen Scans -- first_seen (sicherheitsrelevant für
                # Schritt 2) ist davon nicht betroffen.
                _persist_start = time.perf_counter()
                _save_json(SEEN_FILE, seen)
                persistence_duration += time.perf_counter() - _persist_start

            # roadmap.md Phase 2: Matching- und Deal-Score-Zeit. Beide in
            # einem Wert, da evaluate() sie intern nicht getrennt berechnet
            # (siehe Kommentar bei "matching_and_scoring_duration_sec" oben).
            _match_start = time.perf_counter()
            result = evaluate(
                item["title"], item["price"], rules_cfg,
                market_prices=market_prices, resale_prices=resale_prices,
            )
            matching_and_scoring_duration += time.perf_counter() - _match_start
            if not result.matched:
                continue

            # Baustein 6, Schritt 2: category/price_history_model direkt im
            # seen.json-Eintrag vermerken, damit die spätere Delisting-
            # Erkennung (weiter unten) sie ohne Abhängigkeit von der auf
            # FOUND_MAX_ITEMS begrenzten found.json nachschlagen kann.
            with _seen_lock:
                mark_matched(seen, uid, result.category, result.price_history_model)

            category_buckets.setdefault(result.category or "unbekannt", []).append((item, result))

        # Phase 2: kategorieweise Verarbeitung (found.json/price_history/ntfy
        # -- exakt dieselbe Logik wie zuvor, nur gruppiert statt im rohen
        # Scrape-Reihenfolge). category_order zuerst, danach evtl. weitere
        # Kategorien, die nicht in category_order auftauchen (z.B. Legacy-
        # Einzeldatei-Modus ohne "categories"/"category_order").
        remaining_categories = sorted(c for c in category_buckets if c not in category_order)
        for category_name in [*category_order, *remaining_categories]:
            bucket = category_buckets.get(category_name, [])
            for item, result in bucket:

                # Phase 8 (Schritt 8.2): datengetriebene Top-Deal-Erkennung
                # (unabhaengig von der regelbasierten deal_rating-Einstufung,
                # siehe top_deal.py-Docstring). Nutzt dieselbe, oben bereits
                # berechnete Preisstatistik -- kein zusaetzlicher Datei-Zugriff.
                top_deal_result = evaluate_top_deal(
                    item["price"], price_stats_by_model.get(result.price_history_model),
                    deal_score=result.deal_score,
                )

                # roadmap.md Phase 7, Schritt 7b: Deal-Intelligence-
                # Einstufung + Time-to-Sell-Kategorie-Lookup, beide erst
                # jetzt moeglich (brauchen top_deal_result.is_top_deal bzw.
                # result.category, die oben/vorher bereits vorliegen).
                deal_intelligence = classify_deal(
                    is_top_deal=top_deal_result.is_top_deal,
                    estimated_margin_pct=result.estimated_margin_pct,
                    deal_stars=result.deal_stars,
                )
                category_tts_stats = time_to_sell_stats_by_category.get(result.category)

                entry = {
                    **item,
                    "rule": result.rule_label,
                    "category": result.category,
                    "manufacturer": result.manufacturer_name,
                    "deal_score": result.deal_score,
                    "deal_stars": result.deal_stars,
                    "deal_rating": result.deal_rating,
                    # Dashboard-Badge (Ziel: ⭐ Top-Deal + ★★★★★ bzw.
                    # 👍 Guter Preis + ★★★☆☆) mit fester Sternezahl je
                    # regelbasiertem deal_rating -- bewusst getrennt von
                    # "deal_stars" oben, das weiterhin den vollen gewichteten
                    # deal_score (Phase 6) widerspiegelt.
                    "deal_rating_badge_stars": rating_stars_for(result.deal_rating),
                    "is_top_deal": top_deal_result.is_top_deal,
                    "top_deal_discount_pct": (
                        round(top_deal_result.discount_pct, 1)
                        if top_deal_result.discount_pct is not None
                        else None
                    ),
                    # Top-Deal-Transparenz (Auftrag "Top-Deal-Logik
                    # optimieren", Abschnitt 19): zusaetzliche, rein additive
                    # Felder, damit das Dashboard nachvollziehbar anzeigen
                    # kann, WARUM ein Angebot als Top-Deal erkannt wurde --
                    # ohne evaluate_top_deal() ein zweites Mal aufzurufen.
                    # None/None fuer aeltere found.json-Eintraege vor diesem
                    # Schritt (is-defined-Check im Template).
                    "top_deal_market_price": (
                        round(top_deal_result.market_price, 0)
                        if top_deal_result.market_price is not None
                        else None
                    ),
                    "top_deal_rule": top_deal_result.rule,
                    # Reselling-/Arbitrage-Konzept (STATUS.md Abschnitt 16,
                    # Punkt b): Rohwerte fuer die Dashboard-Anzeige. None,
                    # solange keine Preishistorie fuer dieses Modell vorliegt
                    # -- Template blendet die Anzeige dann aus (additiv, kein
                    # Bruch fuer aeltere found.json-Eintraege ohne dieses Feld).
                    "estimated_margin_eur": (
                        round(result.estimated_margin_eur, 2)
                        if result.estimated_margin_eur is not None
                        else None
                    ),
                    "estimated_margin_pct": (
                        round(result.estimated_margin_pct, 1)
                        if result.estimated_margin_pct is not None
                        else None
                    ),
                    # Verhandlungs-Assistent (STATUS.md Abschnitt 16, Punkt 7):
                    # True, wenn dieses Match nur dank negotiation_*-Feldern
                    # der Kategorie-Regel zustande kam (Preis > max_price,
                    # aber Toleranz + Mindest-Score erfuellt). Additives Feld,
                    # aeltere found.json-Eintraege ohne dieses Feld bleiben
                    # dank is-defined-Check im Template kompatibel.
                    "negotiation_candidate": result.negotiation_candidate,
                    # GPU-Part-Out-Erkennung (STATUS.md Abschnitt 16, Baustein 3,
                    # Schritt 2 in matcher.py bereits berechnet). Rein additive
                    # Felder fuer die Dashboard-Anzeige (Schritt 3) -- None/False,
                    # solange keine dedizierte GPU erkannt wurde oder kein
                    # Mapping-/Marktpreis-Eintrag vorliegt. Aeltere found.json-
                    # Eintraege ohne diese Felder bleiben dank is-defined-Check
                    # im Template kompatibel.
                    "is_part_out_candidate": result.is_part_out_candidate,
                    "part_out_gpu_value": (
                        round(result.part_out_gpu_value, 0)
                        if result.part_out_gpu_value is not None
                        else None
                    ),
                    "part_out_ratio_pct": (
                        round(result.part_out_ratio_pct, 1)
                        if result.part_out_ratio_pct is not None
                        else None
                    ),
                    # Deal Intelligence (roadmap.md Phase 7, Schritt 7b):
                    # fuehrt is_top_deal/estimated_margin_pct/deal_stars
                    # (alle oben bereits berechnet) zu EINER gemeinsamen
                    # Einstufung zusammen (TOP DEAL/FLIP DEAL/VERY GOOD
                    # DEAL/WATCH) -- siehe deal_intelligence.py-Docstring:
                    # reine Zusammenfuehrung bestehender Signale, KEINE neue
                    # Bewertungslogik, KEIN Einfluss auf deal_score/
                    # Notification-Gate. Additive Felder, aeltere found.json-
                    # Eintraege ohne diese Felder bleiben dank is-defined-
                    # Check im Template kompatibel.
                    "deal_intelligence_label": deal_intelligence.label,
                    "deal_intelligence_emoji": deal_intelligence.emoji,
                    # Rein informative Zusatzangabe (KEIN Einfluss auf die
                    # obige Einstufung): Median-Verweildauer der KATEGORIE
                    # dieses Treffers (nicht des Einzelangebots -- fuer ein
                    # noch aktives Angebot ist die tatsaechliche Verkaufs-
                    # dauer per Definition unbekannt, siehe time_to_sell_
                    # stats.py-Docstring). None, solange fuer diese Kategorie
                    # noch keine Delisting-Ereignisse erfasst wurden.
                    "expected_days_to_sell": (
                        round(category_tts_stats.median_days, 1)
                        if category_tts_stats is not None
                        else None
                    ),
                    "found_at": datetime.now(timezone.utc).isoformat(),
                }

                with _seen_lock:
                    found.insert(0, entry)
                    # Ebenfalls sofort persistieren (siehe seen.json oben): ohne
                    # das würde ein Absturz nach dem seen-Save, aber vor dem
                    # bisherigen Scan-Ende-Save, den Treffer endgültig verlieren
                    # -- er gilt ja bereits als "seen" und würde beim nächsten
                    # Lauf nicht erneut ausgewertet.
                    _persist_start = time.perf_counter()
                    _save_json(FOUND_FILE, found[:FOUND_MAX_ITEMS])
                    persistence_duration += time.perf_counter() - _persist_start

                new_hits += 1

                # Phase 7 (Schritt 7.1): Preishistorie-Datenpunkt fuer JEDEN
                # Treffer, unabhaengig vom Notification-Gate weiter unten (das
                # nur steuert, ob ein ntfy-Push verschickt wird -- fuer die
                # Marktpreis-Statistik zaehlt dagegen jeder gematchte Treffer).
                #
                # Baustein 5 (Duplicate-/Cross-Posting-Erkennung): NUR der
                # Preishistorie-Eintrag wird bei einem erkannten Duplikat
                # uebersprungen -- das Match selbst landet unveraendert in
                # found.json/Dashboard (siehe Konzept: verhindert Verzerrung
                # der Marktpreis-Statistik, nicht Verlust echter Treffer).
                price_history_model = result.price_history_model or result.rule_label or "unbekannt"
                fingerprint = normalize_title(item["title"])
                duplicate = find_duplicate(
                    model=price_history_model,
                    price=item["price"],
                    fingerprint=fingerprint,
                    existing_points=price_points_this_scan,
                    **duplicate_kwargs,
                )
                if duplicate is not None:
                    log.info(
                        "Duplicate-/Cross-Posting-Erkennung: Preishistorie-Eintrag "
                        "uebersprungen (Modell=%s, Preis=%.2f, Quelle=%s) -- "
                        "aehnlicher Datenpunkt vom %s bereits vorhanden.",
                        price_history_model, item["price"], item["source"], duplicate.date,
                    )
                else:
                    new_point = make_price_point(
                        price=item["price"],
                        source=item["source"],
                        model=price_history_model,
                        category=result.category,
                        deal_score=result.deal_score,
                        fingerprint=fingerprint,
                    )
                    append_price_point(PRICE_HISTORY_FILE, new_point)
                    price_points_this_scan.append(new_point)

                # Phase 6b: Benachrichtigungs-Gate. Nur Treffer, die BEIDE
                # Bedingungen erfüllen, werden per ntfy verschickt -- alle
                # anderen sind bereits oben in found.json gespeichert und im
                # Dashboard sichtbar, lösen aber keinen Push aus.
                meets_star_gate = stars_meet_minimum(result.deal_stars or "", gate_min_stars)
                # Kategorie-eigenes Preislimit hat Vorrang vor dem globalen
                # gate_max_price (siehe matcher.py/rules/*.yaml "notify_max_price").
                effective_gate_max_price = (
                    result.notify_max_price if result.notify_max_price is not None else gate_max_price
                )
                meets_price_gate = item["price"] <= effective_gate_max_price

                if meets_star_gate and meets_price_gate:
                    emoji = emoji_for(result.deal_rating)
                    clean_title = (
                        result.rule_label.replace("[TOP]", "").replace("[GUT]", "").replace("[OK]", "").strip()
                    )
                    price_str = f"{item['price']:.0f} €"

                    _notify_start = time.perf_counter()
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
                    notification_duration += time.perf_counter() - _notify_start
                    log.info(
                        "BENACHRICHTIGT [%s/%s/%s] %s – %.0f € – %s",
                        result.rule_label, result.deal_rating, result.deal_stars,
                        item["title"], item["price"], item["url"],
                    )
                else:
                    log.info(
                        "GESPEICHERT (Gate nicht erfüllt: %s/%s) [%s/%s] %s – %.0f € – %s",
                        result.deal_stars, f"≤{effective_gate_max_price}€" if meets_price_gate else f">{effective_gate_max_price}€",
                        result.rule_label, result.deal_rating,
                        item["title"], item["price"], item["url"],
                    )

            # Kategorieweise-Auswertung-Auftrag (Ziel 1): Kurzfazit direkt
            # nach jeder Kategorie, unabhaengig von der Trefferzahl (auch
            # "0 Treffer" ist eine hilfreiche Info -- zeigt, dass die
            # Kategorie durchsucht wurde).
            log.info("🔍 Kategorie '%s' fertig: %d Treffer", category_name, len(bucket))

        # Baustein 6 (Time-to-Sell-Schätzung), Schritt 2: Delisting-Sweep
        # EINMAL am Scan-Ende über alle bekannten URLs, nicht pro Item --
        # analog zu price_stats_by_model oben (einmal pro Scan berechnet).
        # raw_urls: exakt dieselbe Teilmenge, die auch oben im Scrape-Loop
        # via mark_seen() aktualisiert wurde (item["price"] is not None),
        # damit "aktuell gesehen" fuer Presence-Tracking und Delisting-
        # Erkennung konsistent definiert ist.
        raw_urls = {item["url"] for item in raw if item.get("price") is not None}
        with _seen_lock:
            newly_delisted_urls = detect_newly_delisted(
                seen, raw_urls, threshold=delisting_threshold_scans
            )
            for delisted_url in newly_delisted_urls:
                entry = seen.get(delisted_url, {})
                ttsp = make_time_to_sell_point(
                    first_seen=entry.get("first_seen"),
                    last_seen=entry.get("last_seen"),
                    model=entry.get("price_history_model"),
                    category=entry.get("category"),
                )
                if ttsp is None:
                    # Kein gematchtes Angebot (kein price_history_model)
                    # oder migrierter Alt-Eintrag ohne echte Historie
                    # (first_seen is None) -- siehe time_to_sell.py-
                    # Docstring. Kein Datenpunkt, aber weiterhin als
                    # delisted markiert (verhindert erneute Pruefung).
                    continue
                append_time_to_sell_point(TIME_TO_SELL_FILE, ttsp)
                log.info(
                    "Delisting erkannt: Modell=%s, Kategorie=%s, "
                    "Verweildauer=%.1f Tage (%s -> %s).",
                    ttsp.model, ttsp.category, ttsp.days, ttsp.first_seen, ttsp.last_seen,
                )

        with _seen_lock:
            seen, pruned_count = prune_delisted_entries(seen, SEEN_DELISTED_MAX_AGE_DAYS)
            if pruned_count:
                log.info(
                    "🧹 seen.json bereinigt: %d delistete Alt-Eintraege "
                    "(> %d Tage) entfernt.",
                    pruned_count, SEEN_DELISTED_MAX_AGE_DAYS,
                )
            # Sofort-Fix (roadmap.md Phase 4): haerte Obergrenze fuer AKTIVE
            # (nicht delistete) Eintraege -- prune_delisted_entries() oben
            # deckt bewusst nur delistete Eintraege ab (siehe dortiger
            # Docstring). Ohne diese Ergaenzung waechst seen.json bei
            # breiten search_terms unbegrenzt. Greift NICHT, solange die
            # Grenze nicht ueberschritten ist (Normalfall unveraendert).
            seen, size_capped_count = enforce_max_size(seen, SEEN_MAX_ITEMS)
            if size_capped_count:
                log.info(
                    "🧹 seen.json Obergrenze erreicht: %d älteste Einträge "
                    "(> %d Gesamt-Limit) entfernt.",
                    size_capped_count, SEEN_MAX_ITEMS,
                )
            _persist_start = time.perf_counter()
            _save_json(SEEN_FILE, seen)
            _save_json(FOUND_FILE, found[:FOUND_MAX_ITEMS])
            persistence_duration += time.perf_counter() - _persist_start

        scan_duration = time.perf_counter() - _scan_start_perf
        deduplicated_count = len(raw) - already_seen_count

        log.info(
            "✅ Scan komplett: %d Treffer insgesamt (von %d geprüften Angeboten).",
            new_hits, len(raw),
        )
        # roadmap.md Phase 2: strukturierte Metrik-Zusammenfassung, ein
        # Log-Eintrag pro Scan -- Grundlage fuer spaetere Auswertung, ohne
        # dafuer erst das Dashboard (Phase 8) zu brauchen.
        log.info(
            "📊 Scan-Metriken: Gesamtdauer=%.2fs, Scraping=%s, "
            "gescrapt=%d, dedupliziert=%d, Matching+Scoring=%.2fs, "
            "Price-Stats=%.2fs, Persistence=%.2fs, Notification=%.2fs",
            scan_duration, scrape_duration_by_source, len(raw),
            deduplicated_count, matching_and_scoring_duration,
            price_stats_duration, persistence_duration, notification_duration,
        )

        with _status_lock:
            _scan_status["scanned_count_last_scan"] = len(raw)
            _scan_status["new_hits_last_scan"] = new_hits
            _scan_status["scan_duration_last_scan_sec"] = round(scan_duration, 3)
            _scan_status["scrape_duration_by_source_sec"] = scrape_duration_by_source
            _scan_status["deduplicated_count_last_scan"] = deduplicated_count
            _scan_status["matching_and_scoring_duration_sec"] = round(
                matching_and_scoring_duration, 3
            )
            _scan_status["price_stats_duration_sec"] = round(price_stats_duration, 3)
            _scan_status["persistence_duration_sec"] = round(persistence_duration, 3)
            _scan_status["notification_duration_sec"] = round(notification_duration, 3)

    except Exception as e:
        log.exception(f"Fehler im Scan: {e}")
        with _status_lock:
            _scan_status["last_scan_error"] = str(e)
    finally:
        with _scan_lock:
            _scan_running = False
        with _status_lock:
            _scan_status["scan_running"] = False
            _scan_status["last_scan_finished_at"] = datetime.now(timezone.utc).isoformat()


app.register_blueprint(build_deals_blueprint(
    FOUND_FILE, Path(__file__).parent / "rules", run_scan,
))


if __name__ == "__main__":
    # Log-Aufraeumen (Ziel 3): klar erkennbares Start-Banner, damit im Log
    # sofort sichtbar ist, dass der Bot erfolgreich hochgefahren ist und
    # auf den naechsten Scan-Zyklus wartet.
    log.info("🤖 [HARDWARE_DEAL] ✅ Bot läuft und lauscht auf Nachrichten...")
    scheduler_loop = build_scheduler_loop(run_scan, _status_lock, _scan_status, log)
    threading.Thread(target=scheduler_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
