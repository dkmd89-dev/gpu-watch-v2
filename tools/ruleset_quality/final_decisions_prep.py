"""Auftrag "Entscheidungen 1-4 technisch vorbereiten": vollstaendig READ-ONLY.

Bereitet vier bereits getroffene/zu treffende Entscheidungen technisch sauber
vor -- mit Dry-Run, exakten Selektionskriterien und reversibler Umsetzungs-
empfehlung. Fuehrt KEINE Migration, KEINE Loeschung und KEINE YAML-Aenderung
aus. Nutzt ausschliesslich den bestehenden Produktions-Matchpfad
(`matcher.evaluate()` ueber `tools/ruleset_quality/common.py`) und die
bereits im Repo vorhandenen Klartext-Titel-Quellen (siehe title_recovery.py).

1. roehrenfernseher: Entscheidung ist final (Option A, siehe vorheriger
   Bericht) -- hier nur noch einmal frisch verifiziert, KEINE Neubewertung
   der Optionen.
2. Orphan-Modelle aus der entfernten Kategorie spielzeug_bundles:
   - lego_bundle: Selektionsregel fuer Migration nach lego_minifiguren
     (lego_minifig_bundle / lego_ninjago_bundle)
   - playmobil_bundle, spielzeug_bundle_sonstige: Loesch-Dry-Run
3. UNCLEAR-Faelle: 21 stabil / 14 veraendert getrennt dokumentiert, dazu
   Tiefenanalyse der Switch-Pro-Controller-Faelle mit ECHTEN Preisen
   (nicht price=0.0) fuer die Vorbereitung einer moeglichen dritten
   Preisstufe in controller.yaml (nur Empfehlung, keine YAML-Aenderung).
4. Frische-Pruefung des 251-Listing-Stichprobenplans (Ueberlappung mit dem
   aktuellen found.json-Korpus).
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from .common import APP_DIR, DATA_DIR, DOCS_DIR, REPORTS_DIR, evaluate, load_current_rules
from .label_store import load_label_store
from .title_recovery import build_fingerprint_title_map

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from price_history import read_price_points  # noqa: E402
from duplicate_detection import normalize_title  # noqa: E402

PRICE_HISTORY_JSONL = DATA_DIR / "price_history.jsonl"
FOUND_JSON = DATA_DIR / "found.json"
FORENSICS_PATH = DOCS_DIR / "DASHBOARD_MATCH_FORENSICS.json"
SAMPLING_WORKSHEET = REPORTS_DIR / "sampling_worksheet_template.csv"

MINIFIG_TARGET_MODELS = {"lego_minifig_bundle", "lego_ninjago_bundle"}


def _price_stats(prices: list[float]) -> dict:
    if not prices:
        return {}
    d = {"n": len(prices), "median": round(statistics.median(prices), 2),
         "min": round(min(prices), 2), "max": round(max(prices), 2)}
    if len(prices) >= 4:
        q = statistics.quantiles(prices, n=4)
        d["q25"], d["q75"] = round(q[0], 2), round(q[2], 2)
    return d


# ---------------------------------------------------------------------------
# 1. roehrenfernseher -- Bestaetigung, keine Neubewertung
# ---------------------------------------------------------------------------

def confirm_roehrenfernseher(points, rules_cfg, fp_map) -> dict:
    pts = [p for p in points if p.model == "roehrenfernseher"]
    dates = sorted(p.date for p in pts)
    prices = [p.price for p in pts]
    recoverable = [(p, fp_map.get(p.fingerprint)) for p in pts]
    n_recoverable = sum(1 for _, t in recoverable if t)
    valid = 0
    for p, title in recoverable:
        if not title:
            continue
        r = evaluate(title, p.price, rules_cfg)
        if r.matched and r.price_history_model == "roehrenfernseher":
            valid += 1
    live_matching = 0
    if FOUND_JSON.exists():
        with FOUND_JSON.open("r", encoding="utf-8") as f:
            for e in json.load(f):
                if e.get("category") == "vintage_elektronik" and "röhrenfernseher" in (e.get("title") or "").lower():
                    live_matching += 1
    return {
        "status": "FINAL -- Option A (eigenstaendig behalten), keine erneute Optionsbewertung",
        "anzahl_punkte": len(pts),
        "zeitraum": [dates[0][:10], dates[-1][:10]] if dates else None,
        "preisverteilung": _price_stats(prices),
        "titel_rekonstruierbar": n_recoverable,
        "davon_valide_bei_neubewertung": valid,
        "live_matchende_eintraege_heute": live_matching,
        "aktion": "keine -- Modell aktiv und gesund, keine Regel-/Modell-/Datenaenderung",
    }


# ---------------------------------------------------------------------------
# 2. Orphan-Modelle -- Migrations-/Loesch-Dry-Run
# ---------------------------------------------------------------------------

def _classify_lego_bundle_point(p, title, rules_cfg) -> dict:
    """Klassifiziert einen einzelnen lego_bundle-Punkt fuer die Migrationspruefung."""
    if not title:
        return {"klasse": "NICHT_REKONSTRUIERBAR", "fingerprint": p.fingerprint,
                "price": p.price, "date": p.date}

    r = evaluate(title, p.price, rules_cfg)
    minifig_terms = ("minifig", "minifigur")
    hat_minifig_bezug = any(t in title.lower() for t in minifig_terms)

    if r.matched and r.price_history_model in MINIFIG_TARGET_MODELS and hat_minifig_bezug:
        klasse = "MIGRIERBAR"
    else:
        klasse = "NICHT_MIGRIERBAR"

    return {
        "klasse": klasse,
        "title": title,
        "price": p.price,
        "date": p.date,
        "eindeutiger_minifig_bezug": hat_minifig_bezug,
        "matched": r.matched,
        "neue_kategorie": r.category if r.matched else None,
        "neues_price_history_model": r.price_history_model if r.matched else None,
    }


def analyze_lego_bundle_migration(points, rules_cfg, fp_map) -> dict:
    pts = [p for p in points if p.model == "lego_bundle"]
    classified = [_classify_lego_bundle_point(p, fp_map.get(p.fingerprint), rules_cfg) for p in pts]

    migrierbar = [c for c in classified if c["klasse"] == "MIGRIERBAR"]
    nicht_migrierbar = [c for c in classified if c["klasse"] == "NICHT_MIGRIERBAR"]
    nicht_rekonstruierbar = [c for c in classified if c["klasse"] == "NICHT_REKONSTRUIERBAR"]

    by_target: dict[str, int] = {}
    for c in migrierbar:
        by_target[c["neues_price_history_model"]] = by_target.get(c["neues_price_history_model"], 0) + 1

    return {
        "model": "lego_bundle",
        "anzahl_punkte_gesamt": len(pts),
        "selektionsregel": (
            "MIGRIERBAR nur wenn (a) echter Titel rekonstruierbar (found.json ODER "
            "DASHBOARD_MATCH_FORENSICS.json) UND (b) Titel enthaelt woertlich 'minifig'/"
            "'minifigur' UND (c) evaluate(titel, preis, aktuelle_regeln) matcht auf "
            "Kategorie lego_minifiguren mit price_history_model in "
            "{lego_minifig_bundle, lego_ninjago_bundle}. Alle drei Kriterien muessen "
            "gleichzeitig erfuellt sein -- kein Kriterium wird einzeln als ausreichend "
            "gewertet."
        ),
        "zaehlung": {
            "migrierbar": len(migrierbar),
            "nicht_migrierbar_aber_rekonstruierbar": len(nicht_migrierbar),
            "nicht_rekonstruierbar": len(nicht_rekonstruierbar),
        },
        "migrierbar_nach_zielmodell": by_target,
        "migrierbar_details": migrierbar,
        "nicht_migrierbar_details": nicht_migrierbar,
        "hinweis_nicht_rekonstruierbar": (
            f"{len(nicht_rekonstruierbar)} von {len(pts)} Punkten haben keinen in "
            "found.json oder DASHBOARD_MATCH_FORENSICS.json auffindbaren Klartext-Titel "
            "(alter Bestand, laengst aus beiden Quellen herausrotiert). Diese Punkte "
            "koennen nach der hier definierten Regel NICHT migriert werden, da ein "
            "eindeutiger Minifiguren-Bezug nicht nachweisbar ist. Sie sind separat "
            "ausgewiesen, nicht geloescht und nicht migriert -- Verbleib erfordert eine "
            "gesonderte Entscheidung (z.B. pauschal beim alten/inaktiven Modellnamen "
            "belassen, archivieren, oder als 'nicht beurteilbar' kennzeichnen)."
        ),
    }


def _deletion_dry_run(model: str, points, fp_map) -> dict:
    pts = [p for p in points if p.model == model]
    dates = sorted(p.date for p in pts)
    prices = [p.price for p in pts]
    fingerprints = sorted({p.fingerprint for p in pts})
    n_recoverable = sum(1 for p in pts if fp_map.get(p.fingerprint))
    return {
        "model": model,
        "selektionsregel": f"Zeile in price_history.jsonl mit Feld model == '{model}' (exakte Gleichheit, kein Praefix-/Teilstring-Match)",
        "anzahl_zu_loeschender_punkte": len(pts),
        "titel_rekonstruierbar": n_recoverable,
        "titel_nicht_rekonstruierbar": len(pts) - n_recoverable,
        "hinweis_titelrekonstruktion": (
            "Fuer die Loesch-Entscheidung irrelevant (kein Zielmodell vorhanden, "
            "unabhaengig vom Titel) -- nur zur Vollstaendigkeit mitgefuehrt."
        ),
        "zeitraum": [dates[0][:10], dates[-1][:10]] if dates else None,
        "preisverteilung": _price_stats(prices),
        "distinkte_fingerprints": len(fingerprints),
        "begruendung": (
            f"Kein aktives Regelwerk (0 Kategorien) matcht die urspruengliche Warengruppe "
            f"von '{model}' -- strukturell verifiziert per grep ueber alle app/rules/*.yaml. "
            "Kein Zielmodell fuer eine Migration vorhanden."
        ),
        "reversibilitaet": (
            "Vor Ausfuehrung: Sicherungskopie von data/price_history.jsonl (z.B. "
            "price_history.jsonl.bak-<datum>) ausserhalb des git-Verlaufs. Loeschung "
            "erfolgt als Zeilenfilter (model != '<wert>'), keine Neuschreibung anderer "
            "Zeilen -- bei Bedarf durch Zuruecklegen der Sicherungskopie vollstaendig "
            "reversibel, solange kein nachfolgender Scan-Lauf neue Zeilen angehaengt hat."
        ),
    }


def analyze_orphans(points, rules_cfg, fp_map) -> dict:
    return {
        "lego_bundle_migration": analyze_lego_bundle_migration(points, rules_cfg, fp_map),
        "playmobil_bundle_loeschung": _deletion_dry_run("playmobil_bundle", points, fp_map),
        "spielzeug_bundle_sonstige_loeschung": _deletion_dry_run("spielzeug_bundle_sonstige", points, fp_map),
    }


# ---------------------------------------------------------------------------
# 3. UNCLEAR-Faelle -- getrennt dokumentiert + Switch-Pro-Controller-Vertiefung
# ---------------------------------------------------------------------------

def _load_unclear_with_price() -> list[dict]:
    """Liest die 35 UNCLEAR-Eintraege direkt aus der Forensik-Rohquelle,
    da der Label-Store (label_store.py) den Preis nicht mitfuehrt."""
    with FORENSICS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for e in data.get("entries", []):
        if e.get("verdict") != "UNCLEAR":
            continue
        out.append({
            "title": e.get("title"),
            "price": e.get("price"),
            "url": e.get("url"),
            "alte_kategorie": e.get("category"),
            "altes_price_history_model": e.get("price_history_model"),
        })
    return out


def analyze_unclear(rules_cfg) -> dict:
    cases = _load_unclear_with_price()
    stable, changed = [], []
    for c in cases:
        title, price = c["title"], c["price"]
        r_real = evaluate(title, price, rules_cfg)
        # Minimalpreis (1.0) umgeht jede max_price-Schwelle -- zeigt, ob ein
        # inhaltlicher Match ueberhaupt prinzipiell moeglich ist (irgendein
        # Modell, nicht zwingend das alte), unabhaengig vom Realpreis.
        r_low = evaluate(title, 1.0, rules_cfg)

        real_unveraendert = r_real.matched and r_real.price_history_model == c["altes_price_history_model"]
        inhaltlich_matchbar = r_low.matched

        entry = {
            **c,
            "neu_matched_bei_echtem_preis": r_real.matched,
            "neue_kategorie_bei_echtem_preis": r_real.category if r_real.matched else None,
            "neues_price_history_model_bei_echtem_preis": r_real.price_history_model if r_real.matched else None,
            "inhaltlich_matchbar_bei_minimalpreis": inhaltlich_matchbar,
            "kategorie_bei_minimalpreis": r_low.category if r_low.matched else None,
            "price_history_model_bei_minimalpreis": r_low.price_history_model if r_low.matched else None,
        }
        if real_unveraendert:
            stable.append(entry)
        else:
            entry["preisschwellen_bedingt"] = inhaltlich_matchbar and not r_real.matched
            changed.append(entry)

    switch_pro = [c for c in cases if "pro controller" in c["title"].lower()]
    switch_pro_detail = []
    for c in switch_pro:
        r_real = evaluate(c["title"], c["price"], rules_cfg)
        switch_pro_detail.append({
            "title": c["title"],
            "preis": c["price"],
            "matcht_heute": r_real.matched,
            "kategorie_heute": r_real.category if r_real.matched else None,
            "price_history_model_heute": r_real.price_history_model if r_real.matched else None,
        })

    return {
        "anzahl_gesamt": len(cases),
        "stabil": {"anzahl": len(stable), "faelle": stable},
        "veraendert": {"anzahl": len(changed), "faelle": changed},
        "switch_pro_controller_vertiefung": {
            "anzahl_faelle_mit_titel_pro_controller": len(switch_pro),
            "faelle": switch_pro_detail,
        },
    }


def _controller_third_tier_prep(switch_pro_detail: list[dict]) -> dict:
    preise = [c["preis"] for c in switch_pro_detail]
    ueber_35 = [c for c in switch_pro_detail if c["preis"] > 35]
    return {
        "aktuelle_regel_ist_stand": {
            "datei": "app/rules/controller.yaml",
            "regeln": [
                {"label": "Switch Pro Controller ★ Top-Deal", "max_price": 25, "deal_rating": "Top-Deal"},
                {"label": "Switch Pro Controller 👍 Guter Preis", "max_price": 35, "deal_rating": "Guter Preis"},
            ],
            "require_all_of": [["switch"], ["pro controller", "pro-controller"]],
            "exclude": ["drift", "defekt", "bastler"],
            "price_history_model": "controller_switch_pro",
        },
        "korrektur_ggue_letztem_bericht": (
            "Der letzte Bericht bezeichnete die 2-Stufigkeit von 'Switch Pro Controller' "
            "als Ausnahme ('anders als fast alle anderen Regelfamilien'). Das ist bei "
            "erneuter Pruefung ueber ALLE app/rules/*.yaml NICHT korrekt: eine dritte "
            "'⚠️ Okay'-Preisstufe ist die Ausnahme, nicht die Regel -- sie kommt nur in "
            "gaming_pc, office_pc, retro_konsolen und vintage_elektronik vor (4 von 19 "
            "Kategorien). ALLE anderen controller.yaml-Regelfamilien (PS5 DualSense, "
            "Xbox Series/One, jeweils voll funktionsfaehig) haben ebenfalls nur 2 Stufen "
            "(bis 25€ bzw. 20€/35€). Eine dritte Stufe fuer Switch Pro Controller waere "
            "damit eine bewusste Abweichung vom in controller.yaml etablierten Muster, "
            "kein Angleich an eine bestehende Norm."
        ),
        "reale_preise_der_faelle": sorted(preise),
        "preisverteilung": _price_stats(preise),
        "faelle_ueber_aktueller_35e_obergrenze": len(ueber_35),
        "moegliche_preislogik_optionen": [
            {
                "option": "A -- keine dritte Stufe einfuehren",
                "begruendung": "konsistent mit dem Muster der uebrigen controller.yaml-Regelfamilien (0 von 3 hat eine 3. Stufe)",
                "konsequenz": "Angebote > 35€ bleiben KEIN_TREFFER, wie in den anderen Voll-funktionsfaehig-Controller-Regeln auch",
            },
            {
                "option": "B -- dritte Stufe '⚠️ Okay' bis 45€",
                "begruendung": "deckt 5 der aktuellen 7 Faelle ab (39/39.99/45/50/... je nach genauer Grenze), naeherungsweise am Median der Faelle orientiert",
                "risiko_fp": "Erhoeht das Risiko, dass generische 'switch' + 'pro controller'-Treffer ohne starkes Zusatzsignal (z.B. Sondereditionen wie 'Monster Hunter Rise Sunbreak' zu 75€, deutlich ueber Marktwert eines Standard-Controllers) faelschlich als Deal markiert werden",
            },
            {
                "option": "C -- dritte Stufe '⚠️ Okay' bis 80€ (deckt alle 7 aktuellen Faelle ab)",
                "begruendung": "keine der 7 UNCLEAR-Faelle bliebe unmatcht",
                "risiko_fp": "hoch -- 80€ liegt nahe am Neupreis eines Switch Pro Controllers, verwaesst die Deal-Definition erheblich; das 130€-Bundle (2 Controller) muesste ohnehin separat betrachtet werden (Stueckzahl-Ambiguitaet, evaluate() kann Bundle-Mengen nicht aus dem Titel zuverlaessig ableiten)",
            },
        ],
        "benoetigte_regressionstests_bei_umsetzung": [
            "app/tests/test_controller.py (oder aequivalent): neuer Testfall je Preisgrenze (genau an, knapp unter, knapp ueber der neuen Obergrenze)",
            "Regressionstest, dass bestehende Top-Deal/Guter-Preis-Stufen unveraendert bleiben (keine Verschiebung bestehender max_price-Werte)",
            "rule_analyzer.py-Lauf nach Aenderung (Duplikat-/Exclude-Konflikt-Check)",
            "Stichprobe historischer price_history.jsonl-Punkte mit price_history_model=controller_switch_pro, um sicherzustellen, dass die neue Stufe keine bereits als KEIN_TREFFER akzeptierten Alt-Faelle unerwuenscht reaktiviert",
        ],
        "empfehlung": (
            "Keine der drei Optionen wird hier final empfohlen -- das ist explizit eine "
            "Preisgrenzen-Entscheidung ohne belastbare Datenbasis (nur 7 Faelle, kein "
            "Markt-/Resale-Preisvergleich durchgefuehrt) und faellt damit unter CLAUDE.md "
            "Regel 4 (keine Threshold-Aenderung ohne Datenbasis). Diese Vorbereitung "
            "liefert nur die Fakten fuer eine spaetere, separat zu beauftragende "
            "Entscheidung."
        ),
    }


# ---------------------------------------------------------------------------
# 4. Frische-Pruefung des Stichprobenplans
# ---------------------------------------------------------------------------

def check_sampling_freshness() -> dict:
    if not SAMPLING_WORKSHEET.exists():
        return {"status": "Worksheet nicht gefunden", "pfad": str(SAMPLING_WORKSHEET)}

    import csv
    with SAMPLING_WORKSHEET.open("r", encoding="utf-8") as f:
        old_urls = {row["url"] for row in csv.DictReader(f) if row.get("url")}

    with FOUND_JSON.open("r", encoding="utf-8") as f:
        current = json.load(f)
    current_urls = {e.get("url") for e in current if e.get("url")}
    current_by_cat: dict[str, int] = {}
    for e in current:
        cat = e.get("category")
        if cat:
            current_by_cat[cat] = current_by_cat.get(cat, 0) + 1

    still_present = old_urls & current_urls
    coverage_pct = round(100 * len(still_present) / len(old_urls), 1) if old_urls else None

    return {
        "worksheet_groesse": len(old_urls),
        "aktueller_korpus_groesse": len(current_urls),
        "aktueller_korpus_kategorien": len(current_by_cat),
        "davon_noch_im_aktuellen_korpus_vorhanden": len(still_present),
        "abdeckung_pct": coverage_pct,
        "empfehlung": (
            "NEU ZIEHEN" if (coverage_pct is None or coverage_pct < 50) else "BESTEHENDE VORLAGE WEITER VERWENDBAR"
        ),
        "begruendung": (
            f"Nur noch {coverage_pct}% der 251 im Worksheet referenzierten Listings sind im "
            "aktuellen found.json-Korpus vorhanden (schnelle Rotation, siehe letzter Bericht: "
            "19,2% -> 0,6% Abdeckungszerfall in 3 Tagen). Eine Stichprobe mit Listings, die "
            "beim eigentlichen Labeling bereits nicht mehr im Live-Korpus sind, waere fuer "
            "eine Live-Ground-Truth wertlos -- neu ziehen aus dem aktuellen Korpus."
            if coverage_pct is not None and coverage_pct < 50 else
            "Abdeckung ausreichend, bestehende Vorlage kann weiterverwendet werden."
        ),
    }


def draw_fresh_sample_template() -> dict:
    """Zieht ausschliesslich eine NEUE LEERE Vorlage (keine Labels) direkt aus
    dem aktuellen Korpus -- reine Wiederverwendung von sampling_plan.py."""
    from .sampling_plan import stratified_sample, write_worksheet

    with FOUND_JSON.open("r", encoding="utf-8") as f:
        found = json.load(f)
    sample = stratified_sample(found)

    by_cat: dict[str, int] = {}
    for e in sample:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1

    out = REPORTS_DIR / "sampling_worksheet_template_v2.csv"
    write_worksheet(sample, out)

    return {
        "neue_vorlage_pfad": str(out),
        "stichprobengroesse": len(sample),
        "kategorien": len(by_cat),
        "nach_kategorie": by_cat,
        "labels_vergeben": False,
    }


# ---------------------------------------------------------------------------

def run() -> dict:
    rules_cfg = load_current_rules()
    points = read_price_points(PRICE_HISTORY_JSONL)
    fp_map = build_fingerprint_title_map()

    unclear = analyze_unclear(rules_cfg)
    freshness = check_sampling_freshness()

    report = {
        "1_roehrenfernseher": confirm_roehrenfernseher(points, rules_cfg, fp_map),
        "2_orphan_modelle": analyze_orphans(points, rules_cfg, fp_map),
        "3_unclear_faelle": unclear,
        "3_switch_pro_controller_dritte_stufe_prep": _controller_third_tier_prep(
            unclear["switch_pro_controller_vertiefung"]["faelle"]
        ),
        "4_stichprobenplan_frische": freshness,
    }

    if freshness.get("empfehlung") == "NEU ZIEHEN":
        report["4_neue_vorlage"] = draw_fresh_sample_template()

    return report


if __name__ == "__main__":
    report = run()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "final_decisions_prep.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"geschrieben nach {out}")

    lb = report["2_orphan_modelle"]["lego_bundle_migration"]["zaehlung"]
    print("lego_bundle:", lb)
    pb = report["2_orphan_modelle"]["playmobil_bundle_loeschung"]["anzahl_zu_loeschender_punkte"]
    sb = report["2_orphan_modelle"]["spielzeug_bundle_sonstige_loeschung"]["anzahl_zu_loeschender_punkte"]
    print("playmobil_bundle zu loeschen:", pb, "| spielzeug_bundle_sonstige zu loeschen:", sb)

    uc = report["3_unclear_faelle"]
    print("UNCLEAR gesamt:", uc["anzahl_gesamt"], "stabil:", uc["stabil"]["anzahl"], "veraendert:", uc["veraendert"]["anzahl"])
    print("Switch Pro Controller Faelle:", uc["switch_pro_controller_vertiefung"]["anzahl_faelle_mit_titel_pro_controller"])

    print("Stichprobenplan-Frische:", report["4_stichprobenplan_frische"]["empfehlung"],
          report["4_stichprobenplan_frische"].get("abdeckung_pct"))
