"""Scan-Paket (roadmap.md Phase 3, Schritt 3.5a): Scheduler-Loop,
extrahiert aus app.py.

Kleinstmoeglicher Eingriff: run_scan, status_lock und scan_status sind
Objektreferenzen (Callable bzw. mutable Objekte) -- werden per
Factory-Funktion uebergeben, keine Duplikation, kein zirkulaerer Import.
Der Scan-Intervall bleibt ueber die Umgebungsvariable SCAN_INTERVAL_MINUTES
konfigurierbar (unveraendertes Verhalten).
"""
import os
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable


def build_scheduler_loop(
    run_scan: Callable[[], None],
    status_lock,
    scan_status: dict,
    log: logging.Logger,
) -> Callable[[], None]:
    """Baut die scheduler_loop()-Funktion mit den benoetigten Referenzen im
    Closure auf. Aufruf erfolgt einmalig in app.py, z.B.:

        threading.Thread(
            target=build_scheduler_loop(run_scan, _status_lock, _scan_status, log),
            daemon=True,
        ).start()
    """

    def scheduler_loop():
        interval = int(os.environ.get("SCAN_INTERVAL_MINUTES", "10")) * 60
        while True:
            try:
                run_scan()
            except Exception:
                log.exception("Fehler im Scan-Durchlauf")

            next_at = datetime.now(timezone.utc) + timedelta(seconds=interval)
            with status_lock:
                scan_status["next_scan_at"] = next_at.isoformat()

            time.sleep(interval)

    return scheduler_loop
