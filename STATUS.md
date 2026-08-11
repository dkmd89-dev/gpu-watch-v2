# STATUS — Aktueller technischer Projektstatus

> **Stand:** 2026-08-11  
> **Repository:** `dkmd89-dev/gpu-watch-v2`  
> **Branch:** `main`  
> **HEAD:** `1f6555317152b453415e8f74f043a2bcdd758095`  
> **Letzter Code-Commit auf `main`:** `1f65553` (PR #25, Merge-Commit) — davor `158f2ed`  
> **Technische Referenz:** `TECHNISCHER_PROJEKTSTATUS.md`

## Gesamtstatus

**Stabil / aktiv weiterentwickelbar.** Die zentralen Architekturbausteine sind vorhanden und durch eine umfangreiche Testsuite abgesichert. Seit dem letzten dokumentierten Stand (`ca4b35b`, PR #8) wurde ein vollständiger, systematischer Active-False-Positive-Audit über **alle 19 Kategorien** des Rulesets durchgeführt und abgeschlossen (PR #11–#25). Der aktuelle Schwerpunkt bleibt Precision, Datenqualität und kontrollierte Weiterentwicklung – nicht auf einem Rewrite.

## Verifiziert dokumentierter Stand

```text
main: 1f65553
Merge pull request #25 from dkmd89-dev/claude/final-categories-active-fp-audit-complete

Letzter Code-Commit davor (main): 158f2ed
docs: kompletten 19-Kategorien-Ruleset-Audit abschließen

Vergleich ca4b35b...1f65553: 17 gemergte PRs (#9–#25), davon 15 mit
Code-/Regeländerung (PR #10–#24) und 3 reine Doku-Commits (#9, #21, #25)

Vollständiger Testlauf (in dieser Session lokal ausgeführt und
verifiziert, nicht nur aus einer Commit-Message übernommen):
pytest app/tests/ -> 1241 passed, 0 failed (622,17s)

Rule Analyzer:
355 Regeln
19 Kategorien
0 Findings (nach jedem einzelnen Fix in PR #11–#24 erneut verifiziert)
```

Der Teststand 1241/0 wurde in dieser Session tatsächlich per `pytest app/tests/` ausgeführt (kein Ersatz durch Einzel-Funktionsaufrufe), zweimal: einmal als Zwischenstand nach den ersten zwölf Kategorien (1233/1233), einmal final nach Abschluss aller 19 Kategorien (1241/1241).

## Zuletzt abgeschlossener Batch

**Systematischer Active-False-Positive-Audit über alle 19 Kategorien** (PR #11–#25, alle auf `main` gemergt), Fortsetzung des in PR #6/#8 begonnenen Audit-Ansatzes, jetzt aber vollständig statt exemplarisch: pro Kategorie wurde der komplette aktuell live matchende `found.json`-Korpus einzeln gegen die produktiven Regeln geprüft (nicht nur Stichproben), evidenzbasiert nach Matchvolumen priorisiert (höchstes Matchvolumen zuerst), jeder Fix ausschließlich additiv über bestehende YAML-Primitiven (`exclude_category`, `exclude_category_unless_also_contains`, `exclude_category_unless_preceded_by`) ohne neuen Matcher-Code umgesetzt und mit dedizierter Regressionstestdatei abgesichert.

**Ergebnis:**

- **14 Kategorien mit realen Fixes:** handhelds, office_pc, retro_konsolen, lego_minifiguren, iphone, monitor_curved, vintage_elektronik, netzteil, notebook_resell, ram, sata_ssd, controller, autoradio_opel_corsa, gaming_pc — zusammen **42 distinkte Fehltreffer-Muster über 113 real bestätigte Titel** ausgeschlossen.
- **4 Kategorien mit 0 Findings** (bewusst dokumentiert, kein Fix nötig): gpu, macbook, m2_ssd, cpu_mainboard_bundle.
- **9 Muster / 27 Titel real belegt, aber bewusst zurückgestellt** (P1/P2 — zu dünne Evidenz für eine verallgemeinerbare Regel oder ungelöstes Kollisionsrisiko), vollständig dokumentiert statt stillschweigend ignoriert.
- Größter Einzelfund: `vintage_elektronik` (11 Muster / 40 Titel — Sony-PVM/BVM-Ersatzteile, die über die fehlende Excludes-Übernahme aus der Schwesterregel "Röhrenfernseher" durchrutschten).
- Zwei unabhängig bestätigte Instanzen desselben strukturellen Musters: `office_pc.yaml` und `gaming_pc.yaml` hatten beide ursprünglich bewusst **kein** `exclude_category` ("Diese Kategorie WILL komplette PC-Systeme") — in beiden Fällen widerlegten reale Gaming-Notebook-/bare-Mainboard-Bundle-Funde diese Annahme.
- Vollständige Dokumentation inkl. aller zurückgestellten Fälle, Root-Cause-Analysen und Testergebnisse je Kategorie: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`.
- Volle Testsuite zweimal auf explizite Freigabe ausgeführt (nicht nach jeder Einzelkategorie, wie vom Nutzer vorgegeben): 1233/1233 (Zwischenstand), final 1241/1241, 0 Fehlschläge.

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
- Systematischer Active-False-Positive-Audit über **alle 19 Kategorien** des Rulesets (PR #11–#25): 14 Kategorien mit realen Fixes (42 Muster / 113 Titel), 4 Kategorien mit verifiziert 0 Findings — Details siehe Batch-Eintrag oben und `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`

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

Wichtige Architekturregeln:

- `market_price` und `estimated_resale_price` bleiben getrennt.
- Dünne Resale-Daten dürfen keinen künstlich optimistischen Flip-Kandidaten erzeugen.
- YAML bleibt die primäre Erweiterungsebene für Kategorien.
- Neue Detector-Typen benötigen weiterhin Python-Code.
- Die letzten False-Positive-Fixes verwenden bestehende YAML-/Matcher-Primitive statt eines neuen generischen Matcher-Systems.

## Datenqualität / offene Punkte

1. Coverage-/False-Positive-Rate nach ausreichender neuer Datensammlung erneut messen.
2. 22 historische Regelgruppen ohne Produktivdaten beobachten.
3. 663 historische Orphan-Datenpunkte aus der entfernten `spielzeug_bundles`-Kategorie nicht ohne separaten Auftrag löschen.
4. dokumentierte `RX 7600 XT`/`RX 7600`-Überlappung separat bewerten.
5. `controller`-`ladekabel`-Exclude separat bewerten.
6. Resale-Confidence (`HIGH/MEDIUM/LOW`) ist eine mögliche nächste Qualitätsstufe.
7. automatische Data-Quality-Warnungen weiterentwickeln.
8. `konsolen_bundles`: "Spieltitel VOR Plattform ohne Bindestrich"-Restlücke (siehe Batch-Eintrag oben, z.B. "Donkey Kong Bananza Nintendo Switch 2 2025 OVP") — bewusst offen, kein Substring-Muster ohne Kollisionsrisiko mit echten Geräte-Titeln identifiziert.
9. 9 real belegte, aber bewusst zurückgestellte Fehltreffer-Muster (27 Titel) aus dem Active-FP-Audit (PR #11–#25) — u.a. `office_pc` bare "bundle"/"kit", `retro_konsolen` Spieltitel-vor-Plattform via "komplett", `iphone` "Zubehörpaket" (gegensätzliche Evidenz). Vollständige Liste mit Begründung je Fall: `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`, Abschnitt "Aktive echte Fehltreffer" (Tabelle "Zurückgestellt").
10. Restliche unauditierte Nischen-Feinheiten innerhalb bereits geprüfter Kategorien (z.B. weitere Marken-/Formfaktor-Varianten) nur bei neuem Datenpunkt erneut aufgreifen, kein proaktives Nachschärfen ohne Beleg.

## Nächste Prioritäten

### P0 — messen und verifizieren

- echten End-to-End-Scan messen
- Scraping-, Dedup-, Matching-, Scoring-, Statistik-, Persistence- und Notification-Zeiten erfassen
- False-Positive-/Coverage-Rate mit überwiegend Post-Fix-Daten erneut bestimmen

### P1 — Datenqualität

- Resale-Confidence ausbauen
- Datenqualitätsdiagnosen automatisieren
- historische Alt-/Neu-Daten methodisch sauber trennen

### P2 — Wartbarkeit

- `app.py` nur schrittweise weiter modularisieren, wenn konkreter Änderungsdruck besteht
- keine Komplett-Refaktorierung

### P3 — Features

Neue Kategorien oder weitere Deal-Intelligence erst nach den Stabilitäts-/Qualitätsschritten priorisieren.

## Arbeitsregeln

- Kein Big-Bang-Rewrite.
- Keine Threshold-Änderungen ohne Datenbasis.
- Keine Tests löschen oder abschwächen.
- Keine Performance-Optimierung ohne Messung.
- Keine bestehende Business-Logik duplizieren.
- Nach technischen Änderungen vollständige Testsuite ausführen.
- `TECHNISCHER_PROJEKTSTATUS.md` und `STATUS.md` nach abgeschlossenen Änderungen synchron halten.

## Dokumentationsregel

`TECHNISCHER_PROJEKTSTATUS.md` ist die aktuelle technische Referenz. Historische Phase-/Completion-Reports bleiben als Entscheidungs- und Messnachweise erhalten, gelten aber nicht als aktueller HEAD- oder Teststand.
