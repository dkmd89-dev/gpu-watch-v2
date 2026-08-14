"""Baut ein baseline.json-kompatibles Artefakt aus dem einzigen im Projekt
vorhandenen, tatsaechlich verifizierten Forensik-Snapshot
(docs/DASHBOARD_MATCH_FORENSICS.json, Commit 01afd5b, 2026-08-10 -- VOR dem
19-Kategorien-Active-FP-Audit).

Zweck: der Regression-Benchmark (benchmark.py) kann damit einen ECHTEN,
bereits vergangenen Ruleset-Wechsel nachvollziehen (Regeln von 01afd5b vs.
aktuelles HEAD) -- als Selbsttest/Validierung des Benchmark-Werkzeugs an
einem Fall, bei dem das erwartete Ergebnis (mehrheitlich FALSE_POSITIVE ->
kein Treffer, TRUE_POSITIVE ueberwiegend stabil) bereits aus
docs/ACTIVE_FALSE_POSITIVE_AUDIT.md bekannt ist.

Rein lesend: `git archive` extrahiert app/rules/ aus dem historischen
Commit in ein TemporaryDirectory, der aktuelle Arbeitsbaum bleibt
unangetastet.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from .common import GENERATED_DIR, REPO_ROOT, current_ruleset_signature, load_rules
from .label_store import FORENSICS_SOURCE, FORENSICS_SOURCE_COMMIT, FORENSICS_SOURCE_DATE

HISTORICAL_BASELINE_PATH = GENERATED_DIR / "baselines" / "historical_forensics_baseline.json"


def _historical_rules_cfg(commit: str = FORENSICS_SOURCE_COMMIT) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # git archive schreibt read-only aus dem Objekt-Store -- keine
        # Working-Tree-Aenderung, kein Checkout des Commits.
        proc = subprocess.run(
            ["git", "archive", commit, "app/rules"],
            cwd=REPO_ROOT, stdout=subprocess.PIPE, check=True,
        )
        subprocess.run(["tar", "-x"], input=proc.stdout, cwd=tmp_path, check=True)
        return load_rules(str(tmp_path / "app" / "rules"))


def build_historical_baseline(write: bool = True) -> dict:
    if not FORENSICS_SOURCE.exists():
        raise FileNotFoundError(f"{FORENSICS_SOURCE} nicht gefunden")

    with FORENSICS_SOURCE.open("r", encoding="utf-8") as f:
        forensics = json.load(f)

    historical_cfg = _historical_rules_cfg()
    historical_signature = current_ruleset_signature(historical_cfg)

    entries = []
    category_dist: dict[str, int] = {}
    rule_dist: dict[str, int] = {}
    verdict_dist = {"TRUE_POSITIVE": 0, "FALSE_POSITIVE": 0, "UNCLEAR": 0, "UNLABELED": 0}

    for e in forensics.get("entries", []):
        verdict = e.get("verdict")
        if verdict not in {"TRUE_POSITIVE", "FALSE_POSITIVE", "UNCLEAR"}:
            verdict = "UNLABELED"
        verdict_dist[verdict] += 1
        stored_category = e.get("category")
        stored_rule = e.get("stored_rule_label")
        if stored_category:
            category_dist[stored_category] = category_dist.get(stored_category, 0) + 1
        if stored_rule:
            rule_dist[stored_rule] = rule_dist.get(stored_rule, 0) + 1

        entries.append({
            "url": e.get("url"),
            "title": e.get("title"),
            "price": e.get("price", 0.0) or 0.0,
            "stored_category": stored_category,
            "stored_rule_label": stored_rule,
            "matched_category": e.get("matched_category"),
            "matched_rule_label": e.get("matched_rule_label"),
            "visible": True,  # forensics enthaelt nur "sichtbare Treffer"
            "ground_truth_verdict": verdict,
            "ground_truth_source": "DASHBOARD_MATCH_FORENSICS.json",
        })

    baseline = {
        "meta": {
            "baseline_id": "historical_forensics_baseline",
            "erzeugt_am": FORENSICS_SOURCE_DATE,
            "hinweis": (
                "Historische Baseline, rekonstruiert aus "
                "docs/DASHBOARD_MATCH_FORENSICS.json (Snapshot-Datum "
                f"{FORENSICS_SOURCE_DATE}, Commit {FORENSICS_SOURCE_COMMIT}) "
                "-- VOR dem 19-Kategorien-Active-FP-Audit (PR #11-#28). "
                "Ruleset-Signatur unten wurde aus den app/rules/*.yaml-"
                "Dateien exakt zu diesem Commit neu berechnet (git archive, "
                "read-only), NICHT aus der aktuellen Ruleset-Signatur "
                "uebernommen."
            ),
            "ruleset_signature": historical_signature,
            "ruleset_commit": FORENSICS_SOURCE_COMMIT,
            "rule_count": len(historical_cfg.get("rules", [])),
            "anzahl_untersuchter_eintraege": len(entries),
            "anzahl_sichtbarer_eintraege": len(entries),
            "ground_truth_verdict_distribution": verdict_dist,
            "ground_truth_abdeckung_pct": 100.0,
            "kategorieverteilung": category_dist,
            "regelverteilung": rule_dist,
        },
        "entries": entries,
    }

    if write:
        HISTORICAL_BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with HISTORICAL_BASELINE_PATH.open("w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)

    return baseline


if __name__ == "__main__":
    b = build_historical_baseline(write=True)
    print(json.dumps(b["meta"], indent=2, ensure_ascii=False))
    print(f"geschrieben nach {HISTORICAL_BASELINE_PATH}")
