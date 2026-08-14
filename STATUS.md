# STATUS — Aktueller technischer Projektstatus

> **Stand:** 2026-08-14  
> **Repository:** `dkmd89-dev/gpu-watch-v2`  
> **Branch:** `main`  
> **Letzter Code-Commit auf `main`:** `2745a95` (davor `b9081e3`, `cb6787e`, `4311683` = Merge PR #29)  
> **Technische Referenz:** `TECHNISCHER_PROJEKTSTATUS.md`

## Gesamtstatus

**Stabil / aktiv weiterentwickelbar.** Seit dem letzten dokumentierten Stand (`1f65553`, PR #25)
wurden zwei getrennte Arbeitsblöcke abgeschlossen: (1) ein weiterer Cross-Category-Routing-Audit
mit zwei realen Fixes (PR #26–#28) und (2) der Aufbau eines vollständigen, reproduzierbaren
**Ruleset-Qualitätssystems** (`tools/ruleset_quality/`, PR #29 + zwei read-only Folge-Sessions) —
ein Regression-Benchmark, das den echten Produktionspfad wiederverwendet, plus eine Tiefenanalyse
der drei zuvor offenen Preishistorie-Entscheidungspunkte. Kein Rewrite, keine Ruleset-Änderung
seit PR #28 (Ruleset-Signatur unverändert: `acd510eb61845cb5`).

## Verifiziert dokumentierter Stand

```text
main: 2745a95
docs: README auf aktuellen Stand bringen (Quoka-Scraper, Verweis auf ruleset_quality Tooling)

Vergleich 1f65553...2745a95: 8 Commits (main), davon 3 gemergte PRs (#26–#29
zählt als 1 Merge-Commit 4311683 + 1 direkter Commit b9081e3 + 2 reine
Doku-Commits cb6787e/2745a95), sowie PR #26/#27/#28 einzeln gemergt

Vollständiger Testlauf (in dieser Session lokal ausgeführt und
verifiziert, nicht aus Dokumentation übernommen):
pytest app/tests/ -> 1296 passed, 0 failed (671,17s)

Rule Analyzer:
355 Regeln
19 Kategorien
0 Findings
Ruleset-Signatur: acd510eb61845cb5 (unverändert seit PR #28)
```

Der Teststand 1296/0 wurde in der aktuellen Session tatsächlich per `pytest app/tests/`
ausgeführt. Vorheriger dokumentierter Stand: 1241/1241 (PR #25). Die 55 neuen Tests stammen aus
PR #26–#28 (Cross-Category-Fixes) und den neuen `tools/ruleset_quality/`-Tests (39 Tests für
Ruleset-Qualitätssystem-Logik: `test_ruleset_quality_tooling.py`,
`test_ruleset_quality_detailed_transition.py`).

## Zuletzt abgeschlossene Batches

### 1. Cross-Category-Routing-Audit (PR #26–#28)

Fortsetzung von PR #6/#8/#11–#25, aber anderer Blickwinkel: nicht "ist Kategorie X intern zu
breit", sondern "landet ein Titel in der *richtigen* Kategorie". Read-only-Audit über alle 1760
eindeutigen `found.json`-Titel (Stand des Audit-Laufs), zwei reale Fixes:

- **`office_pc`**: excludiert jetzt `laptop`/`notebook`/`thinkpad`/`macbook`/`ideapad`/
  `alienware`/`lifebook` — 22 betroffene Titel sauber `unmatched`, 21 verbleibende Treffer
  ausnahmslos echte Desktop-/Tower-/Bundle-Angebote. (PR #27)
- **`macbook`**: `"1024GB"`-Speichergrößen-Schreibweise ergänzt (P2-Fund aus demselben Audit).
  (PR #28)

Details: `docs/CROSS_CATEGORY_ROUTING_AUDIT.md`.

### 2. Ruleset-Qualitätssystem (`tools/ruleset_quality/`, PR #29 + 2 Folge-Sessions)

Reproduzierbares, read-only Regression-/Qualitäts-Tooling, das ausschließlich den echten
Produktionspfad wiederverwendet (`matcher.evaluate()`, `category_validation.
is_still_valid_category()`, `rule_analyzer.analyze_ruleset()`, `rule_coverage.
compute_rule_coverage()`) — **keine zweite Matching-Logik**. Vollständige Doku:
`tools/ruleset_quality/README.md` (Architektur/Datenfluss), Berichte unter
`tools/ruleset_quality/generated/reports/`.

**Kernbefunde:**

- Die zuvor kursierenden Referenzzahlen "2252 TP / 19 FP / 35 UNCLEAR" stammen nachweislich aus
  `docs/DASHBOARD_MATCH_FORENSICS.json` (Snapshot **vor** dem 19-Kategorien-Audit, Commit
  `01afd5b`) — nicht aus dem aktuellen Korpus. Ground-Truth-Abdeckung des Live-Korpus zerfällt
  sehr schnell (19,2% → 0,6% innerhalb von 3 Tagen), da `found.json` kontinuierlich vom laufenden
  Scanner rotiert wird.
- Historischer Regressionsvergleich (Forensik-Snapshot vor Audit vs. aktuelles Ruleset): 93,1%
  aller vormals bestätigten TRUE_POSITIVE bleiben exakt stabil, keine unbestätigten Regressionen.
- Cross-Category-Ambiguität aktuell niedrig (23/2500 Listings, 0,9%), in allen Fällen löst sich
  First-Match-Wins zugunsten der semantisch richtigeren Kategorie auf.
- **Wichtiger Methoden-Fund:** `duplicate_detection.normalize_title()` (Basis von
  `PricePoint.fingerprint`) ersetzt deutsche Umlaute (ä/ö/ü/ß) durch ein Leerzeichen statt einer
  Transliteration. Jede Fingerprint-basierte Revalidierung — inkl. des bereits produktiven
  `app/rule_coverage.py::_is_still_valid()` — matcht dadurch nie gegen Umlaut-haltige
  `match`/`require_all_of`-Begriffe (19 von 355 Regeln in 4 Kategorien betroffen: `handhelds`,
  `konsolen_bundles`, `retro_konsolen`, `vintage_elektronik`). Dadurch war eine erste
  Preishistorie-Simulation an einer Stelle irreführend (`roehrenfernseher` schien auf 3 valide
  Punkte eingebrochen; mit echten Titeln statt Fingerprints: **25 von 26 rekonstruierbaren
  Punkten (96,2%) weiterhin valide**, Modell gesund). **Nur dokumentiert, nicht behoben** (kein
  Code-Change im Read-only-Auftrag) — siehe Datenqualität/offene Punkte, Nr. 11.
- Die drei zuvor offenen Preishistorie-Entscheidungspunkte wurden geklärt (Details:
  `tools/ruleset_quality/generated/reports/OFFENE_ENTSCHEIDUNGEN_1_BIS_3_BERICHT.md`):
  1. `roehrenfernseher` bleibt eigenständiges `price_history_model` (Option A) — fachlich klar von
     `crt_profi_monitor` getrennt (Median 20€ vs. 99,50€), aktiv und gesund.
  2. Die 3 Orphan-Modelle aus der entfernten Kategorie `spielzeug_bundles` (663 Punkte) sind seit
     mind. 11 Tagen ohne neuen Zufluss. `lego_bundle` ist nur teilweise zu `lego_minifiguren`
     migrierbar (nur der Minifiguren-Anteil); `playmobil_bundle`/`spielzeug_bundle_sonstige` haben
     strukturell verifiziert **keinen** Nachfolger im aktuellen Regelwerk. Keine automatische
     Migration möglich — Freigabe-Entscheidung weiterhin offen (siehe unten, Nr. 3).
  3. Von 35 UNCLEAR-gelabelten Fällen (nicht 7, siehe Methoden-Korrektur) sind 14 verändert/matchen
     nicht mehr — keiner davon blockiert eine Preishistorie-Revalidierung. Neuer Strukturbefund:
     die Regel "Switch Pro Controller" hat nur zwei Preisstufen (bis 35 €), keine dritte — jeder
     teurere Controller fällt aktuell durchs Raster (nur dokumentiert, keine Regeländerung).
- Konkreter, geschichteter Stichprobenplan für eine frische Ground-Truth-Erhebung erstellt:
  251-Listing-Worksheet über alle 19 Kategorien (`generated/reports/
  sampling_worksheet_template.csv`), noch nicht gelabelt.

Alle Berichte: `tools/ruleset_quality/generated/reports/`
(`ABSCHLUSSBERICHT.md`, `FINALE_REVALIDIERUNG_ABSCHLUSSBERICHT.md`,
`OFFENE_ENTSCHEIDUNGEN_1_BIS_3_BERICHT.md`).

## Abgeschlossen

- ursprüngliche Phasen 0–10
- YAML-Regelwerk und dynamische Kategorie-Discovery
- Scraper- und Detector-Registry
- Deal Score und Notification-Gating
- Price History / Marktpreisstatistik
- separates Resale-Price-Grouping
- Profit-/Flip-Kandidaten mit Margin-Feldern
- Top-Deal-Logik und Dashboard-KPIs
- Duplicate Detection und Presence Tracking
- Kategorie-Revalidierung und Data-Quality-Bausteine
- Rule Analyzer und Rule Coverage
- Rules-/Entry-/Regex-Caching
- Condition-/Lieferumfang-Detektoren
- mehrere neue Kategorien ohne Python-Code
- Phase-15-Performance-Optimierungen
- Systematischer Active-False-Positive-Audit über alle 19 Kategorien (PR #11–#25)
- Cross-Category-Routing-Audit mit zwei realen Fixes (PR #26–#28)
- Ruleset-Qualitätssystem: Baseline-Freeze, Regression-Benchmark, Kategoriequalitäts-Report,
  Preishistorie-Simulation, Cross-Category-Analyse (`tools/ruleset_quality/`, PR #29 + 2
  Folge-Sessions) — Details siehe Batch-Eintrag oben

## Aktuelle Systemkette

```text
Scraper
  → Dedup / Presence
  → YAML Rules
  → Matcher + Detectoren
  → Deal Score
  → Marktpreis / Resale
  → Profit / Flip
  → Top-Deal / KPIs
  → Notifications
  → Dashboard / API / Statistics
```

Zusätzlich (read-only, außerhalb der Produktionskette): `tools/ruleset_quality/` — Regression-
Benchmark/Qualitätssystem, siehe Batch-Eintrag oben und `tools/ruleset_quality/README.md`.

Wichtige Architekturregeln:

- `market_price` und `estimated_resale_price` bleiben getrennt.
- Dünne Resale-Daten dürfen keinen künstlich optimistischen Flip-Kandidaten erzeugen.
- YAML bleibt die primäre Erweiterungsebene für Kategorien.
- Neue Detector-Typen benötigen weiterhin Python-Code.
- Fixes verwenden bestehende YAML-/Matcher-Primitive statt eines neuen generischen Matcher-Systems.
- `tools/ruleset_quality/` ist kein Bestandteil der Produktionskette und wird von `app.py`/
  `matcher.py` nicht importiert.

## Datenqualität / offene Punkte

1. Coverage-/False-Positive-Rate nach ausreichender neuer Datensammlung erneut messen —
   teilweise bereits durch das Ruleset-Qualitätssystem adressiert (historischer
   Regressionsvergleich zeigt 93,1% TP-Stabilität), aber der Live-Korpus selbst hat aktuell nur
   0,6% Ground-Truth-Abdeckung (siehe Nr. 12).
2. 19 Regeln ohne Produktivdaten weiter beobachten (frisch gemessen, vorheriger Wert "22" war
   veraltet).
3. 663 historische Orphan-Datenpunkte aus der entfernten `spielzeug_bundles`-Kategorie —
   Tiefenanalyse abgeschlossen (siehe Batch-Eintrag oben): `lego_bundle` nur teilmigrierbar,
   `playmobil_bundle`/`spielzeug_bundle_sonstige` strukturell ohne Nachfolger. Löschen/Migrieren
   weiterhin nicht ohne separaten Auftrag.
4. dokumentierte `RX 7600 XT`/`RX 7600`-Überlappung — durch die Preishistorie-Simulation erneut
   bestätigt (Sample-Count-Warnung: 12 → 4 valide Punkte).
5. `controller`-`ladekabel`-Exclude separat bewerten.
6. Resale-Confidence (`HIGH/MEDIUM/LOW`) ist eine mögliche nächste Qualitätsstufe.
7. automatische Data-Quality-Warnungen weiterentwickeln.
8. `konsolen_bundles`: "Spieltitel VOR Plattform ohne Bindestrich"-Restlücke — weiterhin offen.
9. 9 real belegte, aber bewusst zurückgestellte Fehltreffer-Muster (27 Titel) aus dem Active-FP-
   Audit — vollständige Liste: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.
10. Restliche unauditierte Nischen-Feinheiten nur bei neuem Datenpunkt erneut aufgreifen.
11. **Neu:** `duplicate_detection.normalize_title()`/`PricePoint.fingerprint` ist für
    Fingerprint-basierte `evaluate()`-Revalidierung (u. a. `app/rule_coverage.py`) bei
    Umlaut-haltigen Match-Begriffen strukturell unzuverlässig (19/355 Regeln in 4 Kategorien
    betroffen) — nur dokumentiert, nicht behoben. Jede künftige Auswertung sollte, wo möglich,
    echte Titel statt Fingerprints verwenden.
12. **Neu:** Ground-Truth-Label-Abdeckung des `found.json`-Live-Korpus ist auf 0,6% gefallen
    (Zerfall von 19,2% in 3 Tagen) — ein fertig vorbereitetes, geschichtetes 251-Listing-
    Labeling-Worksheet liegt bereit (`tools/ruleset_quality/generated/reports/
    sampling_worksheet_template.csv`), aber noch nicht ausgefüllt.
13. **Neu:** Regel "Switch Pro Controller" (`controller.yaml`) hat nur zwei Preisstufen (bis 35 €)
    statt der sonst üblichen drei — Controller über 35 € werden aktuell nicht erfasst (nur
    dokumentiert, keine Regeländerung).

## Nächste Prioritäten

### P0 — Preishistorie-Revalidierung vorbereiten

- Stichproben-Worksheet labeln (`sampling_worksheet_template.csv`, 251 Listings) — zeitnah nach
  Ziehung, da der Korpus schnell rotiert.
- Anschließend kontrollierte Preishistorie-Revalidierung (auf separate Freigabe) unter
  Verwendung der in Nr. 11 dokumentierten Methodik-Korrektur (echte Titel statt Fingerprints).
- Freigabe-Entscheidung zu den 3 Orphan-Modellen aus `spielzeug_bundles`.

### P1 — Datenqualität

- Resale-Confidence ausbauen.
- Datenqualitätsdiagnosen automatisieren.
- historische Alt-/Neu-Daten methodisch sauber trennen.

### P2 — Wartbarkeit

- `app.py` nur schrittweise weiter modularisieren, wenn konkreter Änderungsdruck besteht.
- keine Komplett-Refaktorierung.

### P3 — Features

Neue Kategorien oder weitere Deal-Intelligence erst nach den Stabilitäts-/Qualitätsschritten
priorisieren.

## Arbeitsregeln

- Kein Big-Bang-Rewrite.
- Keine Threshold-Änderungen ohne Datenbasis.
- Keine Tests löschen oder abschwächen.
- Keine Performance-Optimierung ohne Messung.
- Keine bestehende Business-Logik duplizieren.
- Nach technischen Änderungen vollständige Testsuite ausführen.
- `TECHNISCHER_PROJEKTSTATUS.md` und `STATUS.md` nach abgeschlossenen Änderungen synchron halten.

## Dokumentationsregel

`TECHNISCHER_PROJEKTSTATUS.md` ist die aktuelle technische Referenz. Historische Phase-/
Completion-Reports bleiben als Entscheidungs- und Messnachweise erhalten, gelten aber nicht als
aktueller HEAD- oder Teststand.
