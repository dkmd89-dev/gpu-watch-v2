"""Tests für Schritt B: Log-Rotation in app.py.

Prüft:
- gpu_watch.log rotiert automatisch, sobald LOG_MAX_BYTES überschritten wird
- maximal LOG_BACKUP_COUNT alte Log-Dateien bleiben erhalten
- der eingesetzte Handler ist tatsächlich ein RotatingFileHandler (nicht
  mehr der alte, unbegrenzt wachsende FileHandler)
"""
import sys
import os
import glob
import logging
import importlib.util
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_app_module(data_dir: str, max_bytes: str = "1000000", backup_count: str = "5"):
    """Lädt app.py frisch mit isoliertem DATA_DIR + Log-Rotationsgrenzen."""
    logging.root.handlers.clear()  # sonst wirkt logging.basicConfig() nur beim ersten Testlauf

    os.environ["DATA_DIR"] = data_dir
    os.environ["LOG_MAX_BYTES"] = max_bytes
    os.environ["LOG_BACKUP_COUNT"] = backup_count
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_logrotation", app_path)
    mod = importlib.util.module_from_spec(spec)
    # Bugfix: Modul VOR exec_module in sys.modules registrieren --
    # sonst findet Flask(__name__) intern keinen Eintrag unter dem
    # Modulnamen und faellt auf os.getcwd() als root_path zurueck
    # (statt auf den echten app.py-Verzeichnispfad). Funktioniert dann nur
    # zufaellig, wenn pytest aus app/ heraus gestartet wird -- schlaegt mit
    # "TemplateNotFound: index.html" fehl, sobald z.B. aus dem Projekt-Root
    # gestartet wird (siehe Robins echter pytest-Lauf, 03.08.).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_handler_ist_rotating_file_handler():
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp)
        handlers = logging.root.handlers
        rotating = [h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(rotating) == 1
        assert rotating[0].maxBytes == 1_000_000
        assert rotating[0].backupCount == 5


def test_log_rotiert_bei_ueberschrittenem_max_bytes():
    with tempfile.TemporaryDirectory() as tmp:
        mod = _load_app_module(tmp, max_bytes="2000", backup_count="5")
        for i in range(500):
            mod.log.info("x" * 50 + str(i))

        files = sorted(glob.glob(os.path.join(tmp, "gpu_watch.log*")))
        # aktuelle Datei + mindestens 1 Backup -> Rotation hat stattgefunden
        assert len(files) > 1
        # nie mehr als backup_count Backups + aktuelle Datei
        assert len(files) <= 6


def test_default_rotationsgrenzen_ohne_env_override():
    with tempfile.TemporaryDirectory() as tmp:
        # Env-Vars aus vorherigen Tests bewusst entfernen, um Defaults zu prüfen
        os.environ.pop("LOG_MAX_BYTES", None)
        os.environ.pop("LOG_BACKUP_COUNT", None)
        logging.root.handlers.clear()
        os.environ["DATA_DIR"] = tmp
        app_path = Path(__file__).resolve().parent.parent / "app.py"
        spec = importlib.util.spec_from_file_location("app_under_test_logrotation_defaults", app_path)
        mod = importlib.util.module_from_spec(spec)
        # Bugfix: siehe Kommentar in _load_app_module() oben -- Modul muss
        # VOR exec_module in sys.modules stehen, sonst TemplateNotFound je
        # nach Start-Arbeitsverzeichnis von pytest.
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)

        rotating = [h for h in logging.root.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(rotating) == 1
        assert rotating[0].maxBytes == 1_000_000  # 1 MB Default
        assert rotating[0].backupCount == 5  # max. 5 alte Logs Default


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
