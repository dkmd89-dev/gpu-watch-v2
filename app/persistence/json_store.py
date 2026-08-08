"""Persistenz-Paket (roadmap.md Phase 3, Schritt 3.1): reine JSON-/Log-I/O-
Helfer ohne fachliche Logik, extrahiert aus app.py.

1:1 uebernommen -- kein Verhalten geaendert. app.py importiert diese
Funktionen re-exportartig, damit alle bestehenden Aufrufstellen und Tests
unveraendert weiterfunktionieren.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger("gpu-watch")


def _load_json(path: Path, default):
    """Laedt JSON aus path. Bei fehlender Datei: default. Bei korrupter
    (z.B. durch einen Absturz waehrend eines fruehen, nicht-atomaren
    Schreibvorgangs abgeschnittenen) Datei: die korrupte Datei wird als
    '<name>.corrupt-<timestamp>' gesichert, eine Warnung geloggt und
    default zurueckgegeben, statt die Anwendung abstuerzen zu lassen."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.corrupt-{timestamp}")
        try:
            path.rename(backup_path)
        except OSError:
            backup_path = None
        log.error(
            "Korrupte JSON-Datei %s konnte nicht gelesen werden (%s) -- "
            "als %s gesichert, starte mit Standardwert neu.",
            path, exc, backup_path,
        )
        return default


def _save_json(path: Path, data) -> None:
    """Schreibt data als JSON nach path -- atomar ueber eine Temp-Datei
    im selben Verzeichnis + os.replace(), damit ein Absturz/Kill mitten
    im Schreibvorgang (z.B. Container-Stop) niemals eine abgeschnittene/
    korrupte Zieldatei hinterlaesst: entweder der alte oder der neue
    vollstaendige Inhalt ist vorhanden, nie ein Zwischenzustand."""
    tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def _tail_log(path: Path, n: int) -> list[str]:
    """Liest die letzten `n` Zeilen aus der Log-Datei fürs Dashboard.

    Fehlt die Datei (z.B. ganz frischer Container-Start) -> leere Liste,
    kein Fehler. Ein Lesefehler wird geloggt statt die Status-Route zum
    Absturz zu bringen (Dashboard-Zusatzinfo, kein kritischer Pfad).
    """
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-n:]
    except OSError as e:
        log.error("Scan-Log konnte nicht gelesen werden: %s", e, exc_info=True)
        return []
