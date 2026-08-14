"""Kontrollierte Preishistorien-Revalidierung v3 -- vollstaendig READ-ONLY.

Voraussetzung fuer diesen Lauf (beide jetzt erfuellt):
  1. Der Umlaut-Fingerprint-Bug (STATUS.md Datenqualitaet Nr. 11) ist
     gefixt (`duplicate_detection.normalize_title()` erhaelt Umlaute) --
     `PricePoint.fingerprint` kann daher jetzt direkt (statt nur ueber
     rekonstruierte Klartext-Titel) sinnvoll gegen `matcher.evaluate()`
     re-validiert werden, auch fuer die 19/355 zuvor betroffenen Regeln.
  2. Ein menschlich verifiziertes Label-Set fuer 251 Listings liegt vor
     (human_verified_labels_2026-08-14.json) -- wird NICHT als Ersatz fuer
     eine vollstaendige Ground Truth verwendet, sondern zur Cross-
     Validierung der fingerprint-basierten Revalidierungs-METHODIK selbst
     (wie verlaesslich ist "matcht/matcht nicht mehr per Fingerprint" als
     Proxy fuer TP/FP?).

Ausgabe: reine Analyse (Transition-Matrix, Regression-Gate, Cross-
Validierung). Schreibt NICHTS nach price_history.jsonl.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict

from .common import APP_DIR, DATA_DIR, REPORTS_DIR, GENERATED_DIR, evaluate, load_current_rules
from .title_recovery import build_fingerprint_title_map

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from price_history import read_price_points  # noqa: E402
from duplicate_detection import normalize_title  # noqa: E402

PRICE_HISTORY_JSONL = DATA_DIR / "price_history.jsonl"
HUMAN_LABELS_PATH = GENERATED_DIR / "human_verified_labels_2026-08-14.json"

SMALL_SAMPLE_THRESHOLDS = (3, 5, 10)

# Die 4 Kategorien, die vom Umlaut-Fingerprint-Bug betroffen waren (STATUS.md
# Datenqualitaet Nr. 11). Der Code-Fix (duplicate_detection.py) wirkt NUR auf
# ab jetzt neu geschriebene price_history.jsonl-Zeilen -- bereits gespeicherte
# Zeilen behalten ihr altes, fehlerhaftes Fingerprint-Format, weil der
# Rohtitel dort gar nicht persistiert wird (PricePoint hat kein title-Feld)
# und sich daher nicht nachtraeglich korrekt neu berechnen laesst. Fuer
# HISTORISCHE Punkte in diesen 4 Kategorien ist "KEIN_TREFFER per Fingerprint"
# daher NICHT zuverlaessig von "echter Regel-Drift" zu unterscheiden -- siehe
# _residual_artifact_check().
UMLAUT_BETROFFENE_KATEGORIEN = {"handhelds", "konsolen_bundles", "retro_konsolen", "vintage_elektronik"}


def _transition(point, rules_cfg) -> dict:
    r = evaluate(point.fingerprint or "", point.price, rules_cfg)
    if not r.matched:
        state = "KEIN_TREFFER"
    elif r.category != point.category:
        state = "KATEGORIE_GEAENDERT"
    elif r.price_history_model != point.model:
        state = "MODELL_GEAENDERT"
    else:
        state = "UNVERAENDERT"
    return {
        "state": state,
        "neue_kategorie": r.category if r.matched else None,
        "neues_model": r.price_history_model if r.matched else None,
    }


def full_corpus_revalidation(points, rules_cfg) -> dict:
    by_model_stats = defaultdict(lambda: defaultdict(int))
    overall = defaultdict(int)
    changed_examples = defaultdict(list)

    for p in points:
        if not p.fingerprint:
            overall["OHNE_FINGERPRINT"] += 1
            continue
        t = _transition(p, rules_cfg)
        overall[t["state"]] += 1
        by_model_stats[p.model][t["state"]] += 1
        if t["state"] != "UNVERAENDERT" and len(changed_examples[p.model]) < 5:
            changed_examples[p.model].append({
                "fingerprint": p.fingerprint, "price": p.price,
                "alte_kategorie": p.category, "altes_model": p.model,
                "neue_kategorie": t["neue_kategorie"], "neues_model": t["neues_model"],
                "state": t["state"],
            })

    per_model = {}
    for model, counts in by_model_stats.items():
        total = sum(counts.values())
        unveraendert = counts.get("UNVERAENDERT", 0)
        per_model[model] = {
            "gesamt": total,
            "unveraendert": unveraendert,
            "unveraendert_pct": round(100 * unveraendert / total, 1) if total else None,
            "kein_treffer": counts.get("KEIN_TREFFER", 0),
            "modell_geaendert": counts.get("MODELL_GEAENDERT", 0),
            "kategorie_geaendert": counts.get("KATEGORIE_GEAENDERT", 0),
            "kleine_stichprobe_warnung": {
                str(t): total < t for t in SMALL_SAMPLE_THRESHOLDS
            },
            "beispiele_veraendert": changed_examples.get(model, []),
        }

    return {
        "gesamt_punkte": len(points),
        "gesamt_verteilung": dict(overall),
        "je_modell": per_model,
    }


def cross_validate_against_human_labels(points, rules_cfg) -> dict:
    """Kreuzt price_history-Punkte mit den 251 menschlich verifizierten
    Labels ueber den (jetzt korrekten) Fingerprint des Sample-Titels --
    misst, wie gut 'matcht per Fingerprint noch unveraendert' mit dem
    tatsaechlichen TP/FP/UNCLEAR-Urteil korreliert."""
    with HUMAN_LABELS_PATH.open("r", encoding="utf-8") as f:
        human_store = json.load(f)
    human_labels = human_store["labels"]

    fp_to_human = {}
    for entry in human_labels.values():
        fp = normalize_title(entry["title"])
        fp_to_human[fp] = entry

    matched_points = []
    for p in points:
        if p.fingerprint and p.fingerprint in fp_to_human:
            matched_points.append((p, fp_to_human[p.fingerprint]))

    rows = []
    for p, human in matched_points:
        t = _transition(p, rules_cfg)
        rows.append({
            "title": human["title"],
            "price": p.price,
            "human_verdict": human["human_verdict"],
            "review_modus": human["review_modus"],
            "fingerprint_state": t["state"],
        })

    confusion = defaultdict(lambda: defaultdict(int))
    for r in rows:
        confusion[r["human_verdict"]][r["fingerprint_state"]] += 1

    return {
        "abgeglichene_punkte": len(rows),
        "hinweis": (
            f"{len(rows)} von {len(points)} price_history.jsonl-Punkten "
            "haben einen Fingerprint, der exakt einem der 251 Sample-Titel "
            "entspricht (Ueberschneidung ist klein, da die Stichprobe aus "
            "dem AKTUELLEN found.json gezogen wurde, price_history.jsonl "
            "aber den gesamten Scan-Zeitraum abdeckt)."
        ),
        "konfusionsmatrix": {k: dict(v) for k, v in confusion.items()},
        "details": rows,
    }


def residual_artifact_analysis(points, rules_cfg, fp_map) -> dict:
    """Fuer die 4 vom Umlaut-Bug betroffenen Kategorien: trennt bei den
    KEIN_TREFFER-Punkten, wo immer moeglich, 'residuales Fingerprint-
    Artefakt' (bei echtem Titel WEITERHIN gueltig) von 'echter Drift'
    (bei echtem Titel ebenfalls kein Treffer). Ehrliche Einschraenkung:
    nur fuer den kleinen, ueber found.json/forensics.json rekonstruierbaren
    Anteil moeglich -- der Rest bleibt unbeurteilbar."""
    result = {}
    for cat in sorted(UMLAUT_BETROFFENE_KATEGORIEN):
        cat_points = [p for p in points if p.category == cat and p.fingerprint]
        kein_treffer = [p for p in cat_points if not evaluate(p.fingerprint, p.price, rules_cfg).matched]

        recoverable = 0
        residual_artifact = 0
        genuine_change = 0
        for p in kein_treffer:
            title = fp_map.get(p.fingerprint)
            if not title:
                continue
            recoverable += 1
            if evaluate(title, p.price, rules_cfg).matched:
                residual_artifact += 1
            else:
                genuine_change += 1

        result[cat] = {
            "punkte_gesamt": len(cat_points),
            "kein_treffer_per_fingerprint": len(kein_treffer),
            "davon_titel_rekonstruierbar": recoverable,
            "davon_residuales_fingerprint_artefakt": residual_artifact,
            "davon_echte_aenderung_bei_titel": genuine_change,
            "davon_nicht_beurteilbar": len(kein_treffer) - recoverable,
            "hinweis": (
                "Nur der rekonstruierbare Anteil ist beurteilbar -- die "
                "'kein_treffer'-Gesamtzahl dieser Kategorie im Hauptbericht "
                "ist NICHT direkt als Datenqualitaetsproblem interpretierbar, "
                "solange der weit ueberwiegende Rest unbeurteilbar bleibt."
            ),
        }
    return result


def run() -> dict:
    rules_cfg = load_current_rules()
    points = read_price_points(PRICE_HISTORY_JSONL)
    fp_map = build_fingerprint_title_map()

    report = {
        "gesamt": full_corpus_revalidation(points, rules_cfg),
        "residual_artefakt_analyse_betroffene_kategorien": residual_artifact_analysis(points, rules_cfg, fp_map),
        "cross_validierung_human_labels": cross_validate_against_human_labels(points, rules_cfg),
    }
    return report


if __name__ == "__main__":
    report = run()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "price_history_revalidation_v3.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"geschrieben nach {out}")
    print("Gesamtverteilung:", report["gesamt"]["gesamt_verteilung"])
    print("Cross-Validierung abgeglichene Punkte:", report["cross_validierung_human_labels"]["abgeglichene_punkte"])
