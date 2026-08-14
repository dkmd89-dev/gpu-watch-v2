"""Ground-Truth-Label-Store fuer TRUE_POSITIVE/FALSE_POSITIVE/UNCLEAR.

WICHTIGER BEFUND (siehe docs/DASHBOARD_MATCH_FORENSICS.json und
tools/ruleset_quality/generated/reports/label_store_report.md):

docs/DASHBOARD_MATCH_FORENSICS.json ist ein bereits im Repo vorhandenes,
per-Titel klassifiziertes Forensik-Artefakt (2306 Eintraege, TP 2252 /
FP 19 / UNCLEAR 35 -- exakt die im Auftrag genannten "bekannten
Referenzstand"-Zahlen). Es wurde bei Commit 01afd5b (2026-08-10) erzeugt,
also VOR dem systematischen 19-Kategorien-Active-False-Positive-Audit
(PR #11-#28, 113 seither gefixte Fehltreffer). Es ist damit die einzige im
Projekt vorhandene MENSCHLICH/strukturiert verifizierte Ground Truth,
aber KEIN aktueller Datensatz -- weder die Regeln noch der found.json-
Korpus sind identisch mit dem heutigen Stand (siehe Deckungsanalyse in
build_label_store()).

Dieses Modul baut daraus KEINE neue Matching-Logik, sondern ausschliesslich
einen Nachschlage-Store: URL -> historisch vergebenes verdict (TP/FP/
UNCLEAR) + Metadaten. Fuer Eintraege ohne Eintrag in diesem Store ist die
Klassifikation ausdruecklich UNLABELED -- es wird NICHT geraten oder
automatisch auf TP gemappt (das waere eine unbelegte Behauptung).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .common import DOCS_DIR, GENERATED_DIR

FORENSICS_SOURCE = DOCS_DIR / "DASHBOARD_MATCH_FORENSICS.json"
FORENSICS_SOURCE_COMMIT = "01afd5b"  # siehe `git log -- docs/DASHBOARD_MATCH_FORENSICS.json`
FORENSICS_SOURCE_DATE = "2026-08-10T20:50:17+02:00"

LABEL_STORE_PATH = GENERATED_DIR / "ground_truth_labels.json"

VALID_VERDICTS = {"TRUE_POSITIVE", "FALSE_POSITIVE", "UNCLEAR"}


@dataclass
class Label:
    url: str
    verdict: str  # TRUE_POSITIVE | FALSE_POSITIVE | UNCLEAR
    category: str | None
    rule_label: str | None
    price_history_model: str | None
    root_cause: str | None
    reason: str | None
    source: str
    source_commit: str
    source_date: str


def parse_forensics(path: Path = FORENSICS_SOURCE) -> dict[str, Label]:
    """Liest docs/DASHBOARD_MATCH_FORENSICS.json (read-only) und baut ein
    URL->Label Mapping. Wirft keine Exception bei fehlender Datei -- gibt
    dann ein leeres Dict zurueck (Aufrufer entscheidet, wie kritisch das ist).
    """
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    labels: dict[str, Label] = {}
    for entry in data.get("entries", []):
        url = entry.get("url")
        verdict = entry.get("verdict")
        if not url or verdict not in VALID_VERDICTS:
            continue
        labels[url] = Label(
            url=url,
            verdict=verdict,
            category=entry.get("category"),
            rule_label=entry.get("stored_rule_label"),
            price_history_model=entry.get("price_history_model"),
            root_cause=entry.get("root_cause"),
            reason=entry.get("reason"),
            source="DASHBOARD_MATCH_FORENSICS.json",
            source_commit=FORENSICS_SOURCE_COMMIT,
            source_date=FORENSICS_SOURCE_DATE,
        )
    return labels


def build_label_store(write: bool = True) -> dict:
    """Baut den Ground-Truth-Label-Store und schreibt ihn (falls write=True)
    als Diagnoseartefakt nach LABEL_STORE_PATH. Gibt zusaetzlich ein
    Deckungs-/Herkunfts-Metadatenobjekt zurueck (WICHTIG fuer den
    Abschlussbericht: die Zahlen sind nur fuer die abgedeckten URLs
    belastbar, nicht fuer den kompletten aktuellen Korpus)."""
    labels = parse_forensics()

    by_verdict = {"TRUE_POSITIVE": 0, "FALSE_POSITIVE": 0, "UNCLEAR": 0}
    for lbl in labels.values():
        by_verdict[lbl.verdict] += 1

    store = {
        "meta": {
            "beschreibung": (
                "Ground-Truth-Label-Store, ausschliesslich aus "
                "docs/DASHBOARD_MATCH_FORENSICS.json abgeleitet. Deckt NUR "
                "die dort enthaltenen 2306 URLs ab (Snapshot vom "
                f"{FORENSICS_SOURCE_DATE}, Commit {FORENSICS_SOURCE_COMMIT}, "
                "VOR dem 19-Kategorien-Active-FP-Audit PR #11-#28). Jede "
                "URL, die dort nicht vorkommt, ist UNLABELED -- kein "
                "Ratewert, keine Heuristik."
            ),
            "source_file": str(FORENSICS_SOURCE.relative_to(GENERATED_DIR.parent.parent.parent)),
            "source_commit": FORENSICS_SOURCE_COMMIT,
            "source_date": FORENSICS_SOURCE_DATE,
            "label_count": len(labels),
            "by_verdict": by_verdict,
        },
        "labels": {url: asdict(lbl) for url, lbl in labels.items()},
    }

    if write:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        with LABEL_STORE_PATH.open("w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)

    return store


def load_label_store() -> dict[str, Label]:
    """Laedt den zuvor gebauten Label-Store; baut ihn bei Bedarf neu."""
    if not LABEL_STORE_PATH.exists():
        store = build_label_store(write=True)
    else:
        with LABEL_STORE_PATH.open("r", encoding="utf-8") as f:
            store = json.load(f)
    return {url: Label(**data) for url, data in store["labels"].items()}


if __name__ == "__main__":
    store = build_label_store(write=True)
    print(json.dumps(store["meta"], indent=2, ensure_ascii=False))
    print(f"geschrieben nach {LABEL_STORE_PATH}")
