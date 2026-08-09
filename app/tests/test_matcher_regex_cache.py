"""Tests für den Regex-Cache in matcher.py (Phase 15, Schritt 7 -- siehe
PHASE15_OPTIMIERUNG.md Abschnitte 22-23).

Prüft AUSSCHLIESSLICH das Cache-Verhalten (Hit/Miss, Gross-/Kleinschreibung
teilt sich einen Cache-Eintrag, Korrektheit bleibt identisch zum
unkompilierten Verhalten). Die fachliche Wortgrenzen-/Matching-Semantik
selbst ist bereits durch die gesamte bestehende Testsuite abgedeckt (jeder
evaluate()-Aufruf läuft über denselben Code-Pfad) -- dieser Schritt ändert
die Semantik ausdrücklich NICHT (Auftragsvorgabe Abschnitt 23)."""
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import _compiled_term_pattern, _contains_term


def _clear_cache():
    _compiled_term_pattern.cache_clear()


def test_erster_aufruf_ist_cache_miss():
    _clear_cache()
    _contains_term("rtx 4070 ti grafikkarte", "rtx 4070 ti")
    info = _compiled_term_pattern.cache_info()
    assert info.misses == 1
    assert info.hits == 0


def test_zweiter_aufruf_gleicher_begriff_ist_cache_hit():
    _clear_cache()
    _contains_term("rtx 4070 ti grafikkarte", "rtx 4070 ti")
    _contains_term("eine andere rtx 4070 ti karte", "rtx 4070 ti")
    info = _compiled_term_pattern.cache_info()
    assert info.misses == 1
    assert info.hits == 1


def test_gross_kleinschreibung_teilt_sich_einen_cache_eintrag():
    # _contains_term lowered den Begriff VOR dem Cache-Lookup (term.lower())
    # -- "LEGO"/"lego"/"Lego" muessen denselben Eintrag treffen.
    _clear_cache()
    _contains_term("lego star wars set", "LEGO")
    _contains_term("noch ein lego set", "lego")
    _contains_term("Lego Classic", "Lego")
    info = _compiled_term_pattern.cache_info()
    assert info.misses == 1
    assert info.hits == 2


def test_unterschiedliche_begriffe_erzeugen_unterschiedliche_cache_eintraege():
    _clear_cache()
    _contains_term("rtx 4070 ti", "rtx 4070 ti")
    _contains_term("rtx 4080", "rtx 4080")
    info = _compiled_term_pattern.cache_info()
    assert info.misses == 2
    assert info.hits == 0


# ------------------------------------------------------------------
# Korrektheit bleibt identisch zum unkompilierten Verhalten (Wortgrenzen,
# Sonderzeichen, Mehrwort-Phrasen) -- keine Semantikaenderung.
# ------------------------------------------------------------------

def test_wortgrenzen_verhindern_teilstring_treffer():
    _clear_cache()
    assert _contains_term("kühlsystem defekt", "system") is False
    assert _contains_term("system defekt", "system") is True


def test_mehrwort_phrase_matcht_nur_als_zusammenhaengende_folge():
    _clear_cache()
    assert _contains_term("gaming pc ryzen 5600", "gaming pc") is True
    assert _contains_term("pc fuer gaming geeignet", "gaming pc") is False


def test_sonderzeichen_im_begriff_werden_sicher_behandelt():
    _clear_cache()
    assert _contains_term("rx 6800 nitro+ ovp", "nitro+") is True
    assert _contains_term("rx 6800 ohne zusatz", "nitro+") is False


def test_case_insensitive_matching_bleibt_erhalten():
    # _contains_term() lowert nur den BEGRIFF selbst -- der Titel/Text wird
    # (wie im echten Aufrufpfad, siehe evaluate(): "title_l = title.lower()")
    # bereits vom Aufrufer kleingeschrieben uebergeben.
    _clear_cache()
    assert _contains_term("lego star wars set", "star wars") is True
    assert _contains_term("lego star wars set", "Star Wars") is True


# ------------------------------------------------------------------
# Thread-Sicherheit (Auftrag Abschnitt 23) -- functools.lru_cache ist laut
# Python-Doku thread-safe; dieser Test prueft nur, dass paralleler Zugriff
# mit unterschiedlichen Begriffen nicht zu falschen/inkonsistenten
# Ergebnissen fuehrt (kein Nachweis der internen lru_cache-Locking-Details,
# die sind Teil der Python-Standardbibliothek).
# ------------------------------------------------------------------

def test_parallele_zugriffe_liefern_konsistente_ergebnisse():
    _clear_cache()
    terms = [f"begriff{i}" for i in range(50)]
    texts = [f"titel mit begriff{i} drin" for i in range(50)]
    errors = []
    results = []

    def worker(term, text, expected):
        try:
            results.append(_contains_term(text, term) == expected)
        except Exception as e:  # pragma: no cover
            errors.append(e)

    threads = []
    for term, text in zip(terms, texts):
        threads.append(threading.Thread(target=worker, args=(term, text, True)))
        threads.append(threading.Thread(target=worker, args=(term, "kein treffer hier", False)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert all(results)
    assert len(results) == len(threads)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
