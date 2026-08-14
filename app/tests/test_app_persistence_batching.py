"""Regressionstests für das Persistence-Batching (Scan-Performance-Messung
2026-08-15, docs/SCAN_PERFORMANCE_MESSUNG_2026-08-15.md, Folgeschritt zur
Scraping-Parallelisierung aus PR #36).

Vorher wurden seen.json (bis 16,7 MB) und found.json bei JEDEM einzelnen
neu gesehenen bzw. neu gematchten Angebot komplett neu geschrieben --
Persistence korrelierte mit r=0,997 zur Anzahl neuer Angebote je Scan.
Jetzt wird waehrend des Scans hoechstens alle PERSIST_BATCH_INTERVAL_SECONDS
tatsaechlich geschrieben; der finale, unbedingte Save am Scan-Ende bleibt
unveraendert bestehen -- kein Datenverlust trotz selteneren Zwischen-Saves.
"""
import sys
import os
import json
import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrapers.kleinanzeigen
import scrapers.ebay
import scrapers.quoka


def _load_app_module(data_dir: str, persist_batch_interval_seconds: str = "999"):
    import logging
    logging.root.handlers.clear()

    os.environ["DATA_DIR"] = data_dir
    os.environ["PERSIST_BATCH_INTERVAL_SECONDS"] = persist_batch_interval_seconds
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    spec = importlib.util.spec_from_file_location("app_under_test_persist_batching", app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# Reale, in dieser Session bereits gegen die produktiven Regeln bestaetigte
# TRUE_POSITIVE-Titel (controller-Kategorie) -- mehrere unterschiedliche
# URLs, damit jede einen eigenen "neuer Treffer"-Persistenz-Trigger ausloest.
_MATCHING_LISTINGS = [
    {
        "source": "kleinanzeigen", "title": "Original Xbox Controller (Xbox series x)",
        "price": 30.0, "url": f"https://example.test/xbox-controller-{i}",
        "location": "X", "description": "", "images": [],
    }
    for i in range(6)
]
# Nicht matchende, aber neue (noch nie gesehene) Angebote -- loesen den
# seen.json-Batching-Pfad aus, ohne found.json zu beruehren.
_NON_MATCHING_LISTINGS = [
    {
        "source": "kleinanzeigen", "title": f"Banale Sache ohne jeden Kategoriebezug {i}",
        "price": 5.0, "url": f"https://example.test/banal-{i}",
        "location": "X", "description": "", "images": [],
    }
    for i in range(6)
]


def _run_scan_and_count_persist_calls(app_mod):
    calls = {"seen": 0, "found": 0}
    real_save_json = app_mod._save_json

    def _counting_save_json(path, data):
        if path == app_mod.SEEN_FILE:
            calls["seen"] += 1
        elif path == app_mod.FOUND_FILE:
            calls["found"] += 1
        return real_save_json(path, data)

    with patch.object(scrapers.kleinanzeigen, "search_kleinanzeigen",
                       return_value=_MATCHING_LISTINGS + _NON_MATCHING_LISTINGS), \
         patch.object(scrapers.ebay, "search_ebay", return_value=[]), \
         patch.object(scrapers.quoka, "search_quoka", return_value=[]), \
         patch.object(app_mod, "send_ntfy", MagicMock()), \
         patch.object(app_mod, "_save_json", side_effect=_counting_save_json):
        app_mod.run_scan()

    return calls


def test_grosses_intervall_reduziert_zwischenzeitliche_schreibvorgaenge_drastisch():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, persist_batch_interval_seconds="999")
        app_mod.FOUND_FILE.write_text(json.dumps([]), encoding="utf-8")
        app_mod.SEEN_FILE.write_text(json.dumps({}), encoding="utf-8")

        calls = _run_scan_and_count_persist_calls(app_mod)

        # Vorher: 1 seen.json-Save je neu gesehenem Angebot (12) + 1
        # found.json-Save je neuem Treffer (6) + je 1 finaler Save = 13/7.
        # Mit PERSIST_BATCH_INTERVAL_SECONDS=999 darf innerhalb des Scans
        # ueberhaupt kein Zwischen-Save stattfinden -- nur der eine
        # unbedingte Save am Scan-Ende.
        assert calls["seen"] == 1, calls
        assert calls["found"] == 1, calls

        # Trotzdem: kein Datenverlust. Alle 6 echten Treffer UND alle 12
        # neu gesehenen URLs muessen im finalen Zustand vorhanden sein.
        found_after = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert len(found_after) == 6
        seen_after = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        assert len(seen_after) == 12


def test_kleines_intervall_erlaubt_zwischenzeitliches_schreiben():
    with tempfile.TemporaryDirectory() as tmpdir:
        app_mod = _load_app_module(tmpdir, persist_batch_interval_seconds="0")
        app_mod.FOUND_FILE.write_text(json.dumps([]), encoding="utf-8")
        app_mod.SEEN_FILE.write_text(json.dumps({}), encoding="utf-8")

        calls = _run_scan_and_count_persist_calls(app_mod)

        # Intervall 0 -> praktisch jeder Trigger darf sofort schreiben
        # (mehr als der eine finale Save).
        assert calls["seen"] > 1, calls
        assert calls["found"] > 1, calls

        found_after = json.loads(app_mod.FOUND_FILE.read_text(encoding="utf-8"))
        assert len(found_after) == 6
        seen_after = json.loads(app_mod.SEEN_FILE.read_text(encoding="utf-8"))
        assert len(seen_after) == 12


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
