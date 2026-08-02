"""Tests für presence_tracking.py (Baustein 6 -- Time-to-Sell-Schätzung,
STATUS.md Abschnitt 16, Schritt 1: Datenmodell + Migration)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from presence_tracking import SeenEntry, migrate_seen_data, mark_seen, mark_matched, detect_newly_delisted


def test_migrate_altes_listenformat_zu_dict_mit_none_zeitstempeln():
    raw = ["https://a.test/1", "https://b.test/2"]
    migrated = migrate_seen_data(raw)

    # Seit Schritt 2 liefert SeenEntry() zusätzlich die Defaults
    # missed_scans=0/delisted=False/category=None/price_history_model=None
    # (erwartete Anpassung, kein Bugfix -- siehe presence_tracking.py).
    assert migrated == {
        "https://a.test/1": SeenEntry().to_dict(),
        "https://b.test/2": SeenEntry().to_dict(),
    }


def test_migrate_leere_liste_ergibt_leeres_dict():
    assert migrate_seen_data([]) == {}


def test_migrate_bereits_neues_format_bleibt_unveraendert():
    already_migrated = {
        "https://a.test/1": {"first_seen": "2026-01-01T00:00:00+00:00", "last_seen": "2026-01-02T00:00:00+00:00"},
    }
    result = migrate_seen_data(already_migrated)

    assert result is already_migrated
    assert result == already_migrated


def test_migrate_ist_idempotent_bei_zweifachem_aufruf():
    raw = ["https://a.test/1"]
    once = migrate_seen_data(raw)
    twice = migrate_seen_data(once)

    assert once == twice


def test_migrate_unbekannter_typ_ergibt_leeres_dict_statt_crash():
    assert migrate_seen_data(None) == {}
    assert migrate_seen_data("kaputte-datei") == {}
    assert migrate_seen_data(42) == {}


def test_mark_seen_neue_url_setzt_first_seen_gleich_last_seen():
    entries: dict[str, dict] = {}
    mark_seen(entries, "https://a.test/1", "2026-02-01T10:00:00+00:00")

    assert entries == {
        "https://a.test/1": SeenEntry(
            first_seen="2026-02-01T10:00:00+00:00",
            last_seen="2026-02-01T10:00:00+00:00",
        ).to_dict()
    }


def test_mark_seen_bekannte_url_aktualisiert_nur_last_seen():
    entries = {"https://a.test/1": {"first_seen": "2026-01-01T00:00:00+00:00", "last_seen": "2026-01-01T00:00:00+00:00"}}
    mark_seen(entries, "https://a.test/1", "2026-02-01T10:00:00+00:00")

    assert entries["https://a.test/1"]["first_seen"] == "2026-01-01T00:00:00+00:00"
    assert entries["https://a.test/1"]["last_seen"] == "2026-02-01T10:00:00+00:00"


def test_mark_seen_bekannte_url_mit_none_first_seen_bleibt_none():
    """Migrierte Alt-Einträge haben first_seen=None -- mark_seen() darf das
    NICHT nachtraeglich mit einem erfundenen Zeitstempel ueberschreiben
    (siehe Moduldoku: keine erfundene Historie)."""
    entries = {"https://a.test/1": {"first_seen": None, "last_seen": None}}
    mark_seen(entries, "https://a.test/1", "2026-02-01T10:00:00+00:00")

    assert entries["https://a.test/1"]["first_seen"] is None
    assert entries["https://a.test/1"]["last_seen"] == "2026-02-01T10:00:00+00:00"


def test_seen_entry_to_dict():
    entry = SeenEntry(first_seen="2026-01-01T00:00:00+00:00", last_seen="2026-01-02T00:00:00+00:00")
    assert entry.to_dict() == {
        "first_seen": "2026-01-01T00:00:00+00:00",
        "last_seen": "2026-01-02T00:00:00+00:00",
        "missed_scans": 0,
        "delisted": False,
        "category": None,
        "price_history_model": None,
    }


def test_seen_entry_defaults_sind_none():
    entry = SeenEntry()
    assert entry.first_seen is None
    assert entry.last_seen is None


def test_mark_matched_setzt_category_und_price_history_model():
    entries = {"https://a.test/1": SeenEntry(first_seen="t1", last_seen="t1").to_dict()}
    mark_matched(entries, "https://a.test/1", "gpu", "rtx_3060_12gb")

    assert entries["https://a.test/1"]["category"] == "gpu"
    assert entries["https://a.test/1"]["price_history_model"] == "rtx_3060_12gb"


def test_mark_matched_unbekannte_url_legt_keinen_eintrag_an():
    entries: dict[str, dict] = {}
    mark_matched(entries, "https://unbekannt.test/1", "gpu", "rtx_3060_12gb")

    assert entries == {}


def test_detect_newly_delisted_erhoeht_missed_scans_bei_fehlender_url():
    entries = {"https://a.test/1": SeenEntry(first_seen="t1", last_seen="t1").to_dict()}
    newly_delisted = detect_newly_delisted(entries, currently_seen_urls=set(), threshold=3)

    assert entries["https://a.test/1"]["missed_scans"] == 1
    assert entries["https://a.test/1"]["delisted"] is False
    assert newly_delisted == []


def test_detect_newly_delisted_setzt_zaehler_bei_erneutem_sehen_zurueck():
    entries = {"https://a.test/1": {**SeenEntry(first_seen="t1", last_seen="t1").to_dict(), "missed_scans": 2}}
    detect_newly_delisted(entries, currently_seen_urls={"https://a.test/1"}, threshold=3)

    assert entries["https://a.test/1"]["missed_scans"] == 0


def test_detect_newly_delisted_markiert_bei_erreichter_schwelle():
    entries = {"https://a.test/1": {**SeenEntry(first_seen="t1", last_seen="t1").to_dict(), "missed_scans": 2}}
    newly_delisted = detect_newly_delisted(entries, currently_seen_urls=set(), threshold=3)

    assert entries["https://a.test/1"]["missed_scans"] == 3
    assert entries["https://a.test/1"]["delisted"] is True
    assert newly_delisted == ["https://a.test/1"]


def test_detect_newly_delisted_ueberspringt_bereits_delistete_urls():
    entries = {
        "https://a.test/1": {**SeenEntry(first_seen="t1", last_seen="t1").to_dict(), "missed_scans": 5, "delisted": True},
    }
    newly_delisted = detect_newly_delisted(entries, currently_seen_urls=set(), threshold=3)

    # Weder Zaehler noch Flag veraendert, kein erneuter Time-to-Sell-Punkt.
    assert entries["https://a.test/1"]["missed_scans"] == 5
    assert newly_delisted == []


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
