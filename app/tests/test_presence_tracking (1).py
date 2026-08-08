"""Tests für presence_tracking.py (Baustein 6 -- Time-to-Sell-Schätzung,
STATUS.md Abschnitt 16, Schritt 1: Datenmodell + Migration)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from presence_tracking import (
    SeenEntry, migrate_seen_data, mark_seen, mark_matched, detect_newly_delisted,
    needs_reevaluation, mark_ruleset_evaluated,
)


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
        "last_evaluated_ruleset_hash": None,
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


# ---------- needs_reevaluation() / mark_ruleset_evaluated() (Phase 11, Punkt B) ----------

def test_needs_reevaluation_true_bei_nie_gematchtem_eintrag_ohne_hash():
    entry = SeenEntry(category=None, last_evaluated_ruleset_hash=None).to_dict()
    assert needs_reevaluation(entry, "hash-a") is True


def test_needs_reevaluation_true_bei_geaendertem_ruleset():
    entry = SeenEntry(category=None, last_evaluated_ruleset_hash="hash-alt").to_dict()
    assert needs_reevaluation(entry, "hash-neu") is True


def test_needs_reevaluation_false_bei_unveraendertem_ruleset():
    entry = SeenEntry(category=None, last_evaluated_ruleset_hash="hash-a").to_dict()
    assert needs_reevaluation(entry, "hash-a") is False


def test_needs_reevaluation_false_bei_bereits_gematchtem_eintrag():
    # Zentrale Sicherheitsgarantie: category gesetzt -> NIE re-evaluieren,
    # unabhaengig vom Ruleset-Hash (sonst doppelte Preishistorie/
    # Notifications moeglich).
    entry = SeenEntry(
        category="gpu", price_history_model="rtx_3060_12gb",
        last_evaluated_ruleset_hash="voellig-anderer-hash",
    ).to_dict()
    assert needs_reevaluation(entry, "hash-neu") is False


def test_mark_ruleset_evaluated_setzt_hash():
    entries = {"https://a.test/1": SeenEntry(first_seen="t1", last_seen="t1").to_dict()}
    mark_ruleset_evaluated(entries, "https://a.test/1", "hash-x")

    assert entries["https://a.test/1"]["last_evaluated_ruleset_hash"] == "hash-x"


def test_mark_ruleset_evaluated_unbekannte_url_legt_keinen_eintrag_an():
    entries: dict[str, dict] = {}
    mark_ruleset_evaluated(entries, "https://unbekannt.test/1", "hash-x")

    assert entries == {}


def test_mark_ruleset_evaluated_ueberschreibt_alten_hash():
    entries = {
        "https://a.test/1": SeenEntry(
            first_seen="t1", last_seen="t1", last_evaluated_ruleset_hash="alt",
        ).to_dict()
    }
    mark_ruleset_evaluated(entries, "https://a.test/1", "neu")

    assert entries["https://a.test/1"]["last_evaluated_ruleset_hash"] == "neu"


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


# ============================================================
# prune_delisted_entries() -- bisher ungetestet (STATUS.md Abschnitt 28:
# Funktion wurde nachgezogen, weil sie fehlte und app.py deshalb nicht
# startete; Tests dafür fehlten seitdem). Hier nachgetragen als Teil von
# Abschnitt 31 (L5), da enforce_max_size() direkt danach im selben
# Scan-Schritt aufgerufen wird und beide zusammen verifiziert werden sollen.
# ============================================================

def test_prune_delisted_entries_entfernt_alte_delistete_eintraege():
    from datetime import datetime, timedelta, timezone
    from presence_tracking import prune_delisted_entries

    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    entries = {
        "https://a.test/1": {**SeenEntry(first_seen="t0", last_seen=old_ts).to_dict(), "delisted": True},
    }
    kept, removed = prune_delisted_entries(entries, max_age_days=3)

    assert kept == {}
    assert removed == 1


def test_prune_delisted_entries_behaelt_aktive_eintraege_unabhaengig_vom_alter():
    from datetime import datetime, timedelta, timezone
    from presence_tracking import prune_delisted_entries

    old_ts = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    entries = {
        "https://a.test/1": {**SeenEntry(first_seen="t0", last_seen=old_ts).to_dict(), "delisted": False},
    }
    kept, removed = prune_delisted_entries(entries, max_age_days=3)

    assert kept == entries
    assert removed == 0


def test_prune_delisted_entries_behaelt_junge_delistete_eintraege():
    from datetime import datetime, timedelta, timezone
    from presence_tracking import prune_delisted_entries

    recent_ts = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    entries = {
        "https://a.test/1": {**SeenEntry(first_seen="t0", last_seen=recent_ts).to_dict(), "delisted": True},
    }
    kept, removed = prune_delisted_entries(entries, max_age_days=3)

    assert "https://a.test/1" in kept
    assert removed == 0


def test_prune_delisted_entries_entfernt_migrierte_eintraege_ohne_last_seen():
    from presence_tracking import prune_delisted_entries

    entries = {
        "https://a.test/1": {**SeenEntry().to_dict(), "delisted": True},  # last_seen=None (migriert)
    }
    kept, removed = prune_delisted_entries(entries, max_age_days=3)

    assert kept == {}
    assert removed == 1


# ============================================================
# enforce_max_size() -- STATUS.md Abschnitt 31 (L5-Restlücke): harte
# Obergrenze an der Gesamtzahl seen.json-Einträge, zusätzlich zum
# alter-basierten prune_delisted_entries() oben.
# ============================================================

def test_enforce_max_size_greift_nicht_unterhalb_der_grenze():
    from presence_tracking import enforce_max_size

    entries = {
        "https://a.test/1": SeenEntry(first_seen="2026-01-01T00:00:00+00:00").to_dict(),
        "https://a.test/2": SeenEntry(first_seen="2026-01-02T00:00:00+00:00").to_dict(),
    }
    kept, removed = enforce_max_size(entries, max_items=5)

    assert kept == entries
    assert removed == 0


def test_enforce_max_size_entfernt_aelteste_eintraege_nach_first_seen():
    from presence_tracking import enforce_max_size

    entries = {
        "https://a.test/old": SeenEntry(first_seen="2026-01-01T00:00:00+00:00").to_dict(),
        "https://a.test/mid": SeenEntry(first_seen="2026-01-02T00:00:00+00:00").to_dict(),
        "https://a.test/new": SeenEntry(first_seen="2026-01-03T00:00:00+00:00").to_dict(),
    }
    kept, removed = enforce_max_size(entries, max_items=2)

    assert removed == 1
    assert set(kept.keys()) == {"https://a.test/mid", "https://a.test/new"}


def test_enforce_max_size_entfernt_migrierte_eintraege_ohne_first_seen_zuerst():
    from presence_tracking import enforce_max_size

    entries = {
        "https://a.test/migrated": SeenEntry(first_seen=None).to_dict(),
        "https://a.test/known": SeenEntry(first_seen="2026-01-01T00:00:00+00:00").to_dict(),
    }
    kept, removed = enforce_max_size(entries, max_items=1)

    assert removed == 1
    assert set(kept.keys()) == {"https://a.test/known"}


def test_enforce_max_size_gibt_neues_dict_zurueck_kein_inplace():
    from presence_tracking import enforce_max_size

    entries = {
        "https://a.test/1": SeenEntry(first_seen="2026-01-01T00:00:00+00:00").to_dict(),
        "https://a.test/2": SeenEntry(first_seen="2026-01-02T00:00:00+00:00").to_dict(),
    }
    original_len = len(entries)
    kept, removed = enforce_max_size(entries, max_items=1)

    assert len(entries) == original_len  # Original unveraendert
    assert kept is not entries
    assert len(kept) == 1


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
