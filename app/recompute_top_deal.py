"""Einmaliger Offline-Recompute der Top-Deal-Klassifizierung für bereits
vorhandene found.json-Einträge (Nachtrag zum Auftrag "Top-Deal-Logik
optimieren").

HINTERGRUND: is_top_deal (top_deal.py::evaluate_top_deal()) wird in
app.py::run_scan() ausschließlich beim ERSTMALIGEN Matching eines neuen
Angebots berechnet und in found.json persistiert (siehe Aufrufstelle kurz
vor "entry = {...}"). Bereits vorhandene found.json-Einträge werden bei
erneuter Sichtung desselben Angebots NICHT neu bewertet (Dedup über
seen.json). Der Wechsel von der alten 15%-Rabattregel auf die neue
Score+Discount-Regel (siehe top_deal.py) wirkt sich dadurch nur auf NEUE
Treffer aus -- die Masse der bereits gespeicherten found.json-Einträge
trägt weiterhin den alten is_top_deal-Wert, bis sie irgendwann neu
gescannt werden (kann je nach seen.json-Rotation sehr lange dauern).

Dieses Skript schließt genau diese Lücke, OHNE einen echten Scan/
Re-Match durchzuführen:

- deal_score, category, rule (rule_label), Preis und alle sonstigen
  Felder jedes Eintrags bleiben BYTE-IDENTISCH erhalten -- kein
  Re-Matching gegen matcher.py, kein Risiko einer unbeabsichtigten
  Kategorie-/Score-Verschiebung durch inzwischen ergänzte YAML-Regeln.
- Nur die vier top_deal_*-Felder werden neu berechnet:
  is_top_deal, top_deal_discount_pct, top_deal_market_price, top_deal_rule
- price_history_model wird NICHT aus found.json gelesen (dort nicht
  gespeichert -- nur seen.json kennt es, siehe app.py::mark_matched()),
  sondern deterministisch aus (category, rule) gegen die aktuell
  geladenen rules/*.yaml nachgeschlagen: exakt dieselbe Zuordnung wie
  matcher.py::evaluate() (rule.get("price_history_model", rule_label)).
- Nutzt price_stats.py/top_deal.py 1:1 wieder (keine Duplizierung),
  identisch zum Live-Scan-Pfad in app.py::run_scan().

SICHERHEIT (analog zu burst_cleanup.py):
- Dry-Run per Default, nur --apply schreibt tatsächlich.
- Backup der found.json vor dem Schreiben (found.json.bak-<timestamp>).
- Atomarer Schreibvorgang (Temp-Datei + os.replace(), wie app.py::
  _save_json()) -- ein Abbruch mitten im Schreiben hinterlässt nie eine
  abgeschnittene/korrupte found.json (siehe STATUS.md Abschnitt 25).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from matcher import load_rules
from price_history import read_price_points
from price_stats import compute_all_price_stats, PriceStats
from top_deal import evaluate_top_deal

log = logging.getLogger(__name__)


def _build_price_history_model_lookup(rules_cfg: dict) -> dict[tuple[str | None, str | None], str]:
    """(category, rule_label) -> price_history_model.

    Exakt dieselbe Zuordnung wie matcher.py::evaluate() (Zeile ~773:
    `rule.get("price_history_model", rule_label)`), hier als reines
    Nachschlagewerk statt als Teil eines echten Matching-Durchlaufs.
    """
    lookup: dict[tuple[str | None, str | None], str] = {}
    for rule in rules_cfg.get("rules", []):
        category = rule.get("_category")
        label = rule.get("label", "?")
        model = rule.get("price_history_model", label)
        lookup[(category, label)] = model
    return lookup


@dataclass
class RecomputeReport:
    total: int = 0
    updated: int = 0
    unchanged: int = 0
    became_top_deal: int = 0
    lost_top_deal: int = 0
    skipped_no_model: int = 0
    skipped_no_score_or_price: int = 0
    before_top_deal_count: int = 0
    after_top_deal_count: int = 0
    skipped_examples: list[str] = field(default_factory=list)


def recompute_entries(
    entries: list[dict],
    price_stats_by_model: dict[str, PriceStats],
    model_lookup: dict[tuple[str | None, str | None], str],
) -> tuple[list[dict], RecomputeReport]:
    """Berechnet die vier top_deal_*-Felder für jeden Eintrag neu.

    Gibt eine NEUE Liste zurück (Originale werden nicht mutiert) plus
    einen Report für die Konsolen-Ausgabe. Einträge, für die weder
    price_history_model noch deal_score/price ermittelbar sind, werden
    unverändert durchgereicht (robust, kein Crash bei Alt-/Sonderfällen).
    """
    report = RecomputeReport(total=len(entries))
    result_entries: list[dict] = []

    for entry in entries:
        was_top_deal = bool(entry.get("is_top_deal"))
        report.before_top_deal_count += 1 if was_top_deal else 0

        category = entry.get("category")
        rule_label = entry.get("rule")
        model = model_lookup.get((category, rule_label))

        deal_score = entry.get("deal_score")
        price = entry.get("price")

        if model is None:
            report.skipped_no_model += 1
            if len(report.skipped_examples) < 10:
                report.skipped_examples.append(
                    f"kein price_history_model für category={category!r} rule={rule_label!r}"
                )
            result_entries.append(entry)
            report.after_top_deal_count += 1 if was_top_deal else 0
            continue

        if deal_score is None or price is None:
            report.skipped_no_score_or_price += 1
            result_entries.append(entry)
            report.after_top_deal_count += 1 if was_top_deal else 0
            continue

        stats = price_stats_by_model.get(model)
        top_deal_result = evaluate_top_deal(price, stats, deal_score=deal_score)

        new_entry = dict(entry)
        new_entry["is_top_deal"] = top_deal_result.is_top_deal
        new_entry["top_deal_discount_pct"] = (
            round(top_deal_result.discount_pct, 1)
            if top_deal_result.discount_pct is not None
            else None
        )
        new_entry["top_deal_market_price"] = (
            round(top_deal_result.market_price, 0)
            if top_deal_result.market_price is not None
            else None
        )
        new_entry["top_deal_rule"] = top_deal_result.rule
        result_entries.append(new_entry)

        report.after_top_deal_count += 1 if top_deal_result.is_top_deal else 0
        if top_deal_result.is_top_deal == was_top_deal:
            report.unchanged += 1
        else:
            report.updated += 1
            if top_deal_result.is_top_deal:
                report.became_top_deal += 1
            else:
                report.lost_top_deal += 1

    return result_entries, report


def _atomic_write_json(path: Path, data) -> None:
    """Identisch zu app.py::_save_json() -- Temp-Datei im selben
    Verzeichnis + os.replace(), damit ein Abbruch mitten im Schreiben nie
    eine abgeschnittene found.json hinterlässt."""
    tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def _print_report(report: RecomputeReport) -> None:
    print(f"Gelesen: {report.total} Einträge")
    print(f"Aktualisiert (is_top_deal geändert): {report.updated}")
    print(f"  davon neu Top-Deal:      {report.became_top_deal}")
    print(f"  davon nicht mehr Top-Deal: {report.lost_top_deal}")
    print(f"Unverändert (is_top_deal gleich, Felder trotzdem neu berechnet): {report.unchanged}")
    print(f"Übersprungen (kein price_history_model ermittelbar): {report.skipped_no_model}")
    print(f"Übersprungen (kein deal_score/price): {report.skipped_no_score_or_price}")
    if report.skipped_examples:
        print("Beispiele übersprungener (category, rule)-Kombinationen:")
        for ex in report.skipped_examples:
            print(f"  - {ex}")
    print()
    print(f"Top-Deals vorher: {report.before_top_deal_count}")
    print(f"Top-Deals nachher: {report.after_top_deal_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir", default=os.environ.get("DATA_DIR", "/data"),
        help="Verzeichnis mit found.json/price_history.jsonl (Default: $DATA_DIR oder /data).",
    )
    parser.add_argument(
        "--rules-dir", default=str(Path(__file__).parent / "rules"),
        help="Verzeichnis mit rules/*.yaml (Default: rules/ neben diesem Skript).",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Änderungen tatsächlich schreiben (ohne diesen Schalter: nur Dry-Run/Report).",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    found_file = data_dir / "found.json"
    price_history_file = data_dir / "price_history.jsonl"

    if not found_file.exists():
        print(f"Keine found.json unter {found_file} gefunden -- nichts zu tun.")
        return

    entries = json.loads(found_file.read_text(encoding="utf-8"))
    rules_cfg = load_rules(args.rules_dir)
    model_lookup = _build_price_history_model_lookup(rules_cfg)

    points = read_price_points(price_history_file)
    price_stats_by_model = compute_all_price_stats(points)

    updated_entries, report = recompute_entries(entries, price_stats_by_model, model_lookup)
    _print_report(report)

    if not args.apply:
        print("\nDry-Run -- keine Datei verändert. Mit --apply tatsächlich schreiben.")
        return

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_path = found_file.with_name(found_file.name + f".bak-{timestamp}")
    shutil.copy2(found_file, backup_path)

    _atomic_write_json(found_file, updated_entries)
    print(f"\nGeschrieben: {len(updated_entries)} Einträge nach {found_file}")
    print(f"Backup: {backup_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
