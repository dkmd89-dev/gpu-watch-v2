# Cross-Category Routing Audit

**Status: P1-Fund aus Abschnitt 5.1/9.1 umgesetzt (auf explizite
Nutzer-Freigabe nach Vertiefung).** `office_pc.yaml` excludiert jetzt
zusätzlich `laptop`/`notebook`/`thinkpad`/`macbook`/`ideapad`/
`alienware`/`lifebook`. Ergebnis nach dem Fix: alle 22 betroffenen
Titel sind sauber `unmatched` (kein neues Fehlrouting in eine andere
Kategorie), die 21 verbleibenden `office_pc`-Treffer sind ausnahmslos
echte Desktop-/Tower-/Bundle-Angebote (0 Laptop-Signalwörter mehr).
Details: Abschnitt 10 (unten, neu ergänzt). Tests:
`tests/test_office_pc_notebook_cross_category_fix.py` (9 neue Tests) +
`tests/test_office_pc_active_fp_audit_fix.py` (angepasst) — 49/49
Tests für `office_pc`/`gaming_pc`/`notebook_resell` grün, Rule Analyzer
weiterhin 0 Findings.

Direkte methodische Fortsetzung von `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`,
aber anderer Blickwinkel: nicht mehr "Ist Kategorie X intern zu breit?",
sondern "Landet ein realer Titel aktuell in der falschen Kategorie,
obwohl eine andere vorhandene Kategorie besser passt?". Read-only,
Phase 0–10: keine Regel-/Test-/Datenänderung in diesem Durchlauf.

## 1. Scope

- **Kategorien:** alle 19 aus `app/rules/*.yaml`.
- **Korpus:** `data/found.json`, 1817 Einträge / **1760 eindeutige Titel**
  (dedupliziert über den Titelstring), Stand des Audit-Laufs
  (2026-08-11 — Live-Scanner läuft weiter, siehe bereits im vorherigen
  Audit dokumentierter Momentaufnahme-Hinweis).
- **Preise:** ausschließlich der **echte** `found.json`-Preis pro Titel,
  **kein** `price=0.0`. Grund identisch zum Vorgänger-Audit: `price=0.0`
  verzerrt First-Match-Wins bei preisgedeckelten Regeln systematisch.
- **Matcher-Logik:** jeder der 1760 Titel wurde **frisch** über
  `matcher.load_rules('rules')` + `matcher.evaluate(title, price, rules_cfg)`
  gegen die aktuell produktiven Regeln (355 Regeln, 19 Kategorien)
  ausgewertet — nicht die in `found.json` gespeicherte (potenziell
  ältere) `category`, sondern das tatsächliche Ergebnis mit dem
  aktuellen Ruleset. Ergebnis je Titel: `stored_cat` (aus `found.json`)
  vs. `actual_cat` (frisch berechnet).

## 2. Gesamt-Qualitätscheck

**Rule Analyzer** (`matcher.load_rules('rules')` + `rule_analyzer.analyze_ruleset()`):

```
355 Regeln, 19 Kategorien
Findings: 0
```

Deckt sich mit dem in STATUS.md/TECHNISCHER_PROJEKTSTATUS.md
dokumentierten Stand. Hinweis: `python app/rule_analyzer.py` allein
erzeugt **keine** Ausgabe — das Modul hat keinen `__main__`-Block,
`analyze_ruleset()` muss explizit mit einer über `matcher.load_rules()`
geladenen Config aufgerufen werden (siehe `app/tests/test_rule_analyzer.py`
für die Aufrufkonvention). Für diesen Report wurde das oben beschriebene
manuelle Skript verwendet.

**Git-Diff** (`ca4b35b..HEAD`, Basis: letzter vor dem Active-FP-Audit
dokumentierter Stand aus PR #8):

```
git diff --stat ca4b35b..HEAD -- app/rules/ app/tests/
30 files changed, 1946 insertions(+), 2 deletions(-)
```

- 14 Kategorie-YAMLs geändert (`autoradio_opel_corsa`, `controller`,
  `gaming_pc`, `handhelds`, `iphone`, `konsolen_bundles`,
  `lego_minifiguren`, `monitor_curved`, `netzteil`, `notebook_resell`,
  `office_pc`, `ram`, `retro_konsolen`, `sata_ssd`, `vintage_elektronik`)
  + 15 neue Regressionstestdateien.
- **Ausschließlich additiv**: die einzigen 2 gelöschten Zeilen sind ein
  obsolet gewordener Kommentar in `gaming_pc.yaml`/`office_pc.yaml`
  ("bewusst KEIN exclude_category"), der nach Einführung des jeweiligen
  `exclude_category`-Blocks nicht mehr zutraf.
- Kein Fund außerhalb des erwarteten Scopes: `git diff --stat` über den
  Rest des Repos (ohne `app/rules/`, `app/tests/`, `data/`, `docs/`,
  `*.md`) zeigt nur `.gitignore` (−1 Zeile).
- `data/found.json` wurde in einem separaten Commit ("chore: enable
  tracking for found.json for temporary edits") erstmals ins Git
  aufgenommen — **kein** Bestandteil der Rule-/Test-Commits, keine
  inhaltliche Manipulation der Live-Daten durch den Audit.
- **`git status --short`** zu Beginn dieser Session: nur `data/*`
  (laufender Scanner, unverändert seit Sessionbeginn, nicht angefasst)
  + 1 neue, nicht getrackte Datei (`data/gpu_watch.log.3`,
  `data/seen.json`) — beides Scanner-Artefakte, nicht Teil dieses Audits.

**Ergebnis Phase 2:** Der komplette bisherige Optimierungsdurchlauf ist
sauber, additiv und scope-konform. Keine versehentliche Datenänderung.

## 3. Auswirkungen der bisherigen 42/113-Fixes (Endrouting-Prüfung)

Kernfrage: Hat ein Exclude einen Titel zwar aus seiner ursprünglich
falschen Kategorie entfernt, ihn danach aber in eine **andere** falsche
Kategorie geroutet (Kategorie A → Exclude → Kategorie B → Match)?

Methodik: alle 1760 eindeutigen Titel aus `found.json` frisch mit dem
aktuellen Ruleset ausgewertet, `stored_cat` (gespeicherte Kategorie zum
Scan-Zeitpunkt) gegen `actual_cat` (frisches Ergebnis) verglichen —
nicht nur eine Stichprobe der 113 bekannten Fix-Titel, sondern der
**komplette** Korpus.

```
Titel mit stored_cat != actual_cat: 116
  davon: stored_cat gesetzt, jetzt unmatched:        115
         stored_cat gesetzt, jetzt ANDERE Kategorie:   1
  davon: vorher unmatched, jetzt neu matched:           0
```

**115 der 116 Diffs sind die erwarteten, sauberen Fixes:** Titel, die
zum Scan-Zeitpunkt (vor dem jeweiligen Fix) in einer falschen Kategorie
landeten, sind nach dem Fix korrekt **komplett unmatched** — kein neues
Fehlrouting in eine andere Kategorie.

**1 echter Domino-Fall gefunden:**

| Titel | Preis | Vorher (`stored_cat`) | Jetzt (`actual_cat`) |
|---|---:|---|---|
| `Lenovo IdeaPad Gaming 3 15IMH05 \| i5-10300H \| GTX 1650 \| 8GB RAM \| 512GB SSD` | 339,00 € | `gaming_pc` (Fix PR #24, "Gaming-Laptop ohne 'laptop'/'notebook' im Titel") | `office_pc` ("Office-PC (Mindestanforderung erfüllt)") |

**Root Cause:** `gaming_pc.yaml` wurde im Active-FP-Audit (PR #24) um
`exclude_category: [laptop, notebook, ideapad, mainboard]` ergänzt, weil
Gaming-Notebooks fälschlich als Desktop-Gaming-PC matchten. Der
zugehörige Regressionstest
(`tests/test_gaming_pc_active_fp_audit_fix.py::test_gaming_laptops_matchen_nicht`)
prüft aber **nur** `r.matched and r.category == "gaming_pc"` ist
`False` — er prüft **nicht**, wo der Titel stattdessen landet. Genau
dieser blinde Fleck ist der Gegenstand dieses Cross-Category-Audits.

`office_pc.yaml` (`requirements:`-basiert, kein Titel-Keyword-Matching)
verlangt RAM ≥ 8 GB, CPU-Tier/Generation, kein Tiny/Mini/USFF/SFF/AiO-
Gehäuse — der Titel erfüllt das formal (8 GB RAM, i5 10. Gen.,
`requires_dedicated_gpu: false`) und `office_pc.yaml` excludiert bisher
nur `mainboard`/`motherboard`/`aufrüstkit`/`aufrüstbundle`, **nicht**
`laptop`/`notebook`/`ideapad`/`thinkpad`/`macbook` — identischer
strukturneller Fehler wie der bereits in `gaming_pc.yaml` gefixte,
einfach eine Kategorie weiter. Details und Einordnung: Abschnitt 5/7.

**Bewertung:** Die 42/113-Fixes selbst sind sauber (115/116 Diffs ohne
Nebenwirkung). Der 1 gefundene Domino-Fall ist real, aber – wie
Abschnitt 5 zeigt – Teil eines größeren, bereits vorher bestehenden und
**bewusst getesteten** Musters (office_pc akzeptiert Notebooks
generell), nicht eine isolierte neue Lücke.

## 4. Routing-Matrix (aktueller Stand, frisch berechnet)

| Kategorie | Aktuell matchende Titel (frisch) | Bewertung |
|---|---:|---|
| lego_minifiguren | 456 | unauffällig |
| iphone | 213 | unauffällig |
| konsolen_bundles | 98 | unauffällig |
| netzteil | 92 | unauffällig |
| retro_konsolen | 83 | 1 bekannter P1-Fall (Abschnitt 8), sonst unauffällig |
| notebook_resell | 82 | unauffällig |
| ram | 79 | unauffällig |
| sata_ssd | 72 | unauffällig |
| **office_pc** | **43** | **21/43 Titel sind Notebooks/Laptops statt Desktop-PCs — siehe Abschnitt 5/7** |
| autoradio_opel_corsa | 53 | unauffällig (homogene Nische) |
| controller | 50 | unauffällig — alle 50 Titel einzeln geprüft, ausschließlich echte Standalone-Controller |
| macbook | 50 | unauffällig |
| gpu | 48 | unauffällig |
| monitor_curved | 131 | unauffällig |
| vintage_elektronik | 68 | unauffällig |
| gaming_pc | 12 | unauffällig (Fix PR #24 wirkt, siehe Abschnitt 3) |
| handhelds | 12 | 2 bekannte P1/P2-Fälle aus Vorgänger-Audit (unverändert offen) |
| m2_ssd | 2 | unauffällig |
| cpu_mainboard_bundle | 1 | unauffällig |
| **unmatched (keine Kategorie)** | **115** | erwartete Fixes aus Abschnitt 3 |

Zusätzlich zur tabellarischen Übersicht wurde für jede Kategorie ein
Fremdsignal-Sweep gefahren (Titel, die starke Erkennungswörter einer
*anderen* Kategorie enthalten — z.B. `"laptop"`/`"notebook"` in
`office_pc`, `"rtx"`/`"ddr4"` in nicht-PC-Kategorien, `"monitor"` in
Nicht-Monitor-Kategorien). Ergebnis: außer dem office_pc/Notebook-Muster
(Abschnitt 5) und bereits bekannten, unveränderten P1/P2-Fällen aus dem
Vorgänger-Audit kein weiterer Cross-Category-Befund mit realer Evidenz
im aktuellen Korpus. Insbesondere:

- **controller** (50 Treffer, vollständig einzeln gelistet): ausnahmslos
  echte Standalone-Controller (Switch Pro, PS5 DualSense, Xbox Wireless),
  Preise 12–35 €, keine Konsolen-Bundles darunter — der im Vorgänger-
  Audit dokumentierte Xbox/konsolen_bundles-Kollisionsfall (Abschnitt 6)
  tritt aktuell nicht real auf.
- **gaming_pc** (12 Treffer): RTX/DDR4-Nennungen sind bei dieser
  Kategorie das *erwartete* Signal (Desktop-Gaming-PC-Spezifikation),
  keine Fremdkategorie-Kollision.
- **vintage_elektronik** (68 Treffer, davon 15 mit "Monitor"-Wort): alle
  15 sind Sony PVM/BVM/Trinitron-Profi-Röhrenmonitore — korrekt in
  dieser Kategorie, kein Fehlrouting zu `monitor_curved` (das ausschließlich
  moderne gekrümmte PC-Monitore abdeckt, keine CRT-Geräte).

## 5. Aktive Cross-Category-Fehltreffer

### 5.1 Hauptfund: `office_pc` fängt Notebooks/Laptops ab

**21 von 43 aktuell matchenden `office_pc`-Titeln (49 %) sind Notebooks/
Laptops**, keine Desktop-Systeme:

| Priorität | Titel | Preis | Actual | Erwartete Kategorie | Grund |
|---|---|---:|---|---|---|
| P1 | `Lenovo IdeaPad Gaming 3 15IMH05 \| i5-10300H \| GTX 1650 \| 8GB RAM \| 512GB SSD` | 339,00 € | office_pc | keine (Gaming-Laptop, von gaming_pc bewusst excludiert) | Domino-Fall aus PR #24, Abschnitt 3 |
| P1 | `DELL [OVP] \|\| Alienware M17 R3 \| i7-10750H - 16GbDDR4 - 2TbM2 - 1660Ti+UHD630 - W11` | 50,00 € | office_pc | keine / notebook_resell (kein Modellcode-Match) | Gaming-Notebook mit dediziertem GTX 1660Ti |
| P1 | `Laptop Lenovo ThinkPad T490s Intel I5-8265U 8GB RAM 256GB NVMe Win11 Pro` | 149,99 € | office_pc | notebook_resell (Modellcode nicht in Regel-Liste) | ThinkPad, aber "T490s" nicht in notebook_resell-`require_all_of` (nur T490 ohne "s" gelistet) |
| P1 | `Lenovo ThinkPad T490s 14 Zoll FHD - Intel i5-8365U 8GB DDR4 256GB NVMe B-Ware` | 219,99 € | office_pc | notebook_resell (s. o.) | wie vor |
| P1 | `Lenovo ThinkPad T490s 14FHD i7 8665U 16GB-RAM 256SSD WINDOWS-11 LTE DE-BACKLIT` | 275,00 € | office_pc | notebook_resell (Preis > 240 € Cap) | ThinkPad T490s, Preis über notebook_resell-Obergrenze |
| P1 | `Lenovo ThinkPad X390 \| 13,3" \| i5-8365U \| 8 GB RAM \| 512 GB SSD` | 293,00 € | office_pc | notebook_resell (Preis > 240 € Cap) | s. u., bereits per Test als office_pc-TRUE_POSITIVE gesperrt |
| P1 | `Lenovo ThinkPad X390, 13,3" FHD Display, Intel Core i7 8565U, 16GB RAM, 512GB SS` | 299,00 € | office_pc | notebook_resell (Preis > Cap) | wie vor |
| P1 | `Laptop Lenovo ThinkPad X390 Yoga 13,3" FHD 256GB SSD i7-8565U 16GB RAM QWERTZ` | 280,00 € | office_pc | notebook_resell (Modellcode "X390 Yoga" nicht separat gelistet + Preis > Cap) | |
| P1 | `Lenovo ThinkPad X13 Gen.1 13,3" Intel i5-10310U 1,70GHz 16GB RAM 256GB SSD Touch` | 249,00 € | office_pc | notebook_resell (Preis > 240 € Cap) | |
| P1 | `Lenovo ThinkPad X13 Yoga Gen 1 i5-10310U 16GB RAM 512GB SSD Touch Windows 11` | 255,00 € | office_pc | notebook_resell (Preis > Cap) | |
| P1 | `Notebook 2 in 1 Lenovo ThinkPad X13 Yoga Gen 1 i7-10510U 16GB RAM SSD512GB Win11` | 320,00 € | office_pc | notebook_resell (Preis > Cap) | |
| P1 | `Lenovo Thinkpad T14s G1 Notebook 14" i5-10310U 16 GB RAM 256 GB SSD Win 11 Pro` | 249,89 € | office_pc | notebook_resell ("T14s" nicht gelistet, nur "T14") | |
| P1 | `Lenovo ThinkPad T14 Gen1 i5 10310U 16GB RAM 256GB SSD 14" FHD Win 11 Pro MwSt.` | 299,99 € | office_pc | notebook_resell (Preis > Cap) | |
| P1 | `✅ Lenovo ThinkPad L14 Gen 1 \| 14" \| 16/32 GB RAM \| 512 GB SSD \| i5-10210U \| Notebook \| Laptop \| MwSt \| ...` | 329,00 € | office_pc | notebook_resell (Preis > Cap) | |
| P1 | `Lenovo ThinkPad L14 G1 Core i5 10310U 16 GB RAM 240 GB M.2 nVME SSD Webcam` | 279,00 € | office_pc | notebook_resell (Preis > Cap) | |
| P1 | `Fujitsu Lifebook U7510 i5-10310U 2.20 GHz , 16GB DDR4, 512GB NVMe, Win 11 Pro` | 245,00 € | office_pc | keine dedizierte Kategorie (Fujitsu-Lifebook-Notebook, kein notebook_resell-Modellcode) | |
| P1 | `HP ProBook 650 G5 Notebook i5-8265U, 256GB Nvme, Intel 620, 32GB DDR4 #1009` | 333,20 € | office_pc | keine dedizierte Kategorie (HP ProBook, kein notebook_resell-Modellcode) | |
| P1 | `ACEMAGIC 16'' AX16Pro Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM 512GB SSD Win11P` | 289,00 € | office_pc | keine dedizierte Kategorie | bereits per Test office_pc-TRUE_POSITIVE |
| P1 | `ACEMAGIC 16'' FHD Laptop AMD Ryzen 7 5700U 16GB DDR4 RAM 512GB SSD Win11 Pro` | 289,00 € | office_pc | keine dedizierte Kategorie | |
| P1 | `ASUS TUF Gaming FX705DT Notebook 17 Zoll 16GB RAM ;AMD Ryzen 5 3550H` | 290,03 € | office_pc | notebook_resell (kein RTX 3060/4060 → keine Regel greift) | Gaming-Notebook, aber ohne RTX-3060/4060-GPU nicht von notebook_resell abgedeckt |
| P1 | `Apple MacBook Pro 16.1 \| i9-9880H \| 16GB RAM 1024GB SSD OHNE OS QWERTY \| Nr. 1` | 299,00 € | office_pc | macbook (eigene Kategorie existiert!) | s. Abschnitt 5.2 |
| P1 | `Lenovo V330-15IKB Laptop i5 8250U 15,6" 8GB DDR4 RAM 256GB SSD Win 11` | 149,95 € | office_pc | keine dedizierte Kategorie | |

**Root Cause (identisch zum bereits in `gaming_pc.yaml` gefixten
Muster):** `office_pc.yaml` nutzt `requirements:`-Detector-Matching
(RAM/CPU/Gehäuse) statt Titel-Keywords. `matcher.py::_case_meets_requirement()`
behandelt "kein erkennbares Gehäuse" bewusst als **erfüllt** — ein
Notebook hat naturgemäß keine separate Gehäuse-Beschreibung und
rutscht damit strukturell durch dieselbe Lücke wie die bereits
gefixten bare Mainboard-Bundles. `office_pc.yaml` excludiert bisher nur
`mainboard`/`motherboard`/`aufrüstkit`/`aufrüstbundle` — **nicht**
`laptop`/`notebook`/`thinkpad`/`ideapad`/`macbook`, obwohl
`gaming_pc.yaml` (identischer Mechanismus, identische ursprüngliche
Begründung "WILL komplette PC-Systeme") diesen Exclude im selben
Audit-Durchlauf (PR #24) bereits erhalten hat.

**Wichtige Einschränkung — das ist KEIN unentdeckter Bug, sondern eine
bereits bewusst getroffene und getestete Entscheidung:**
`tests/test_office_pc_active_fp_audit_fix.py::test_reale_true_positives_matchen_weiterhin`
listet explizit `"ACEMAGIC ... Laptop ..."` und
`"Lenovo ThinkPad X390 | 13,3\" | i5-8365U | 8 GB RAM | 512 GB SSD"` als
**gewünschte** office_pc-Treffer und die Audit-Doku selbst nennt "42
verbleibende TRUE_POSITIVE-Titel (**Notebooks**, Business-Desktops mit
Marke/Modell)" wörtlich als akzeptiertes Ergebnis. Ein Fix (Exclude von
`laptop`/`notebook`/`thinkpad`/etc.) würde diesen bestehenden,
absichtlich geschriebenen Regressionstest brechen — das fällt unter
CLAUDE.md Abschnitt 2, Regel 3 ("Keine bestehenden Funktionen entfernen
ohne vorherige Freigabe") und Regel 5 ("keine Tests abschwächen"). Dies
ist daher **kein mechanisch sicherer P0**, sondern eine
Produktentscheidung mit Kollisionsrisiko zur bestehenden Testabdeckung
— siehe Einordnung Abschnitt 7.

**Zusätzliche Beobachtung:** Von den 21 Notebook-Titeln hätten **11**
(alle ThinkPad-Titel mit T14/X13/T490/X390/L14-Modellcode) technisch
eine passende `notebook_resell`-Regel, scheitern dort aber **nur** am
Preis-Cap (180/240 € vs. `office_pc`-Cap 300 €, teils zusätzlich an
exakter Modellcode-Schreibweise wie "T490s" vs. gelistetem "T490"). Für
diese Untermenge ist das Signal am stärksten: eine dedizierte,
speziell für ThinkPads geschriebene Kategorie existiert und "kennt" den
Titel, matcht aber wegen des niedrigeren Preis-Caps nicht — der Titel
fällt place stattdessen in die generische, für Desktop-Systeme gedachte
office_pc-Regel mit höherem Cap.

### 5.2 Einzelfall: MacBook Pro matcht `office_pc` statt `macbook`

`Apple MacBook Pro 16.1 | i9-9880H | 16GB RAM 1024GB SSD OHNE OS QWERTY | Nr. 1`
(299,00 €) matcht `office_pc`, obwohl eine dedizierte `macbook`-Kategorie
existiert (Position 11 in der Auswertungsreihenfolge, **vor**
`office_pc` Position 15 — würde also bei einem Treffer gewinnen).
Vermutliche Ursache: `macbook.yaml`-Regeln verlangen wahrscheinlich ein
Preis-/Titelmuster, das "OHNE OS" (kein macOS installiert, ggf. als
Hackintosh/Ersatzteil-Signal) nicht abdeckt — nicht abschließend
verifiziert in diesem Read-Only-Durchlauf (kein Regeländerungsvorschlag
ohne tieferen Deep-Dive in `macbook.yaml`, das im Vorgänger-Audit als "0
Findings" bewertet wurde). Nur **1 Titel im Korpus**, daher separat als
P2 gelistet, nicht Teil der P1-Sammelbewertung oben.

## 6. First-Match-Wins-Probleme

**Wichtige Korrektur zur bestehenden Dokumentation:** Der Abschnitt
"Routing / First-Match-Wins" in `docs/ACTIVE_FALSE_POSITIVE_AUDIT.md`
erklärt den dortigen Xbox/Controller-Fall mit *"First-Match-Wins vor
konsolen_bundles wegen niedrigerer `scan_priority`, 6 vs. 8"*. Das ist
**technisch nicht korrekt** und wurde in diesem Audit empirisch
widerlegt:

```python
>>> [r['_category'] for r in cfg['rules'] if ...][:5]  # erste Kategorien in der ausgewerteten Reihenfolge
['autoradio_opel_corsa', 'controller', 'cpu_mainboard_bundle', 'gaming_pc', 'gpu', ...]
```

`matcher._load_rules_from_dir()` baut die für `evaluate()` maßgebliche
`rules`-Liste über `categories/registry.py::discover_categories()`, die
`*.yaml`-Dateien via `sorted(rules_path.glob("*.yaml"))` einliest —
**alphabetisch nach Dateiname**, nicht nach `scan_priority`.
`scan_priority` wird ausschließlich für `category_order` verwendet
(Scan-Reihenfolge/Anzeige-Gruppierung in `app.py`), **nie** in
`evaluate()` selbst (verifiziert: keine `scan_priority`-Referenz in der
Matching-Schleife von `matcher.py`).

**Tatsächliche First-Match-Wins-Reihenfolge (alphabetisch, empirisch
verifiziert):**

```
1. autoradio_opel_corsa   8. konsolen_bundles      15. office_pc
2. controller              9. lego_minifiguren      16. ram
3. cpu_mainboard_bundle   10. m2_ssd                17. retro_konsolen
4. gaming_pc              11. macbook               18. sata_ssd
5. gpu                    12. monitor_curved        19. vintage_elektronik
6. handhelds              13. netzteil
7. iphone                 14. notebook_resell
```

Der Xbox/Controller-Fall (`controller` vor `konsolen_bundles`) stimmt
im Ergebnis zufällig mit der alten Erklärung überein (`c` < `k`
alphabetisch UND 6 < 8 nach `scan_priority`), ist aber aus dem
**falschen Grund** dokumentiert. Das ist für künftige Analysen wichtig:
wer First-Match-Wins-Kollisionen einschätzen will, muss die
**alphabetische Dateireihenfolge**, nicht `scan_priority`, zugrunde
legen. `notebook_resell` (14) kommt vor `office_pc` (15) — das ist auch
der Grund, warum die 11 ThinkPad-Titel aus Abschnitt 5.1 zuerst korrekt
gegen `notebook_resell` geprüft werden und **erst nach** dessen
Preis-Cap-Fehlschlag in `office_pc` landen (kein zusätzliches
First-Match-Wins-Problem, reine Cap-Differenz).

**Keine weiteren realen First-Match-Wins-Kollisionen im aktuellen
Korpus gefunden** (die 12 Beispielrichtungen aus der Aufgabenstellung —
Konsole→controller, Handheld→Zubehör, Mainboard→office_pc,
Notebook-Ersatzteil→notebook_resell, Retro-Konsole→Zubehör,
Monitor→Gaming-PC, GPU→andere Hardware, Netzteil→office_pc,
RAM→office_pc, SSD→office_pc, Controller→Konsole, Spiel→Konsole,
Ersatzteil→Hauptprodukt — wurden alle stichprobenartig gegen den realen
Korpus geprüft, keine davon zeigt aktuell reale Treffer außer dem
bereits in Abschnitt 5 dokumentierten Notebook→office_pc-Muster).

## 7. P0/P1/P2

**P0 (eindeutig falsches Routing, realer aktiver Fall, Ursache
eindeutig, sicherer Fix, geringe Kollisionsgefahr): keiner.**

Der einzige Kandidat mit ausreichender Evidenz (Abschnitt 5.1) hat ein
**Kollisionsrisiko mit einem bestehenden, bewusst geschriebenen
Regressionstest** (`test_reale_true_positives_matchen_weiterhin`) und
berührt eine bereits im Vorgänger-Audit explizit getroffene
Entscheidung ("42 TRUE_POSITIVE-Titel inkl. Notebooks"). Kriterium 5
aus der Aufgabenstellung ("bestehende Regelmechanismen ausreichend")
ist NICHT erfüllt, ohne diese Testentscheidung explizit zu revidieren
— das erfordert nach CLAUDE.md Abschnitt 2 Regel 3/5 vorherige
Freigabe, kein mechanischer P0.

**P1 (real, eindeutige erwartete Kategorie, Fix wahrscheinlich sicher,
aber Entscheidungsbedarf):**

| Titel-Cluster | Titel | Fund |
|---|---:|---|
| office_pc/Notebooks | 21 | Abschnitt 5.1 — Entscheidung nötig: Notebooks aus office_pc ausschließen (→ die meisten werden dann unmatched, da notebook_resell-Preisdeckel niedriger liegt) ODER office_pc-Preisdeckel für Notebooks/notebook_resell anheben ODER Status quo explizit bestätigen |
| MacBook Pro → office_pc | 1 | Abschnitt 5.2 — eigener Deep-Dive in `macbook.yaml` nötig, bevor ein Fix möglich ist |

**P2 (zweifelhaftes Routing, aber Kollisionsrisiko/Semantik unklar):**

Keine zusätzlichen Funde über die bereits im Vorgänger-Audit als P1/P2
dokumentierten, unveränderten Fälle hinaus (handhelds Fanxiang-SSD/
USB-C-Adapter, retro_konsolen "Nintendo Netzteil für Nintendo DS" u.a.
— siehe Abschnitt 8).

**NO-FIX:** keine neuen Fälle in diesem Audit.

**IGNORE (korrektes Routing, exemplarisch geprüft):** `controller` (50
Titel, vollständig verifiziert), `gpu` (48 Titel), `gaming_pc` (12
Titel), `konsolen_bundles`/`retro_konsolen`-Grenze (keine aktive
Kollision), `vintage_elektronik`/`monitor_curved`-Grenze (keine aktive
Kollision).

## 8. Bewusst nicht behobene Fälle

Ausschließlich bereits bekannte, unveränderte Fälle aus
`docs/ACTIVE_FALSE_POSITIVE_AUDIT.md` — kein neuer hypothetischer Fall
wurde in diesem Audit ergänzt (Phase 9: keine Änderung ohne reale
Korpus-Evidenz):

- `handhelds`: Fanxiang M.2-2230-SSD-Einbauteil (2 Titel, P1),
  USB-C-HDMI-Adapterkabel (1 Titel, P2).
- `office_pc`: bare `"bundle"`/`"kit"` ohne "Aufrüst"-Signal (7 Titel,
  P1/P2, unverändert).
- `retro_konsolen`: "Spieltitel-vor-Plattform via 'komplett'" (11 Titel,
  P2/NO-FIX), `"Nintendo Netzteil für Nintendo DS..."` (1 Titel, P1,
  identisches "[Zubehör] für [Plattform]"-Muster wie bereits in
  `konsolen_bundles` gelöst, aber eigener Arbeitsschritt nötig),
  Display-Ersatzteil (1 Titel, P2), Konvolut-Gruppe-1-Logik (1 Titel,
  P2).
- `iphone`: "Zubehörpaket" mit widersprüchlicher Evidenz (2 Titel,
  P2/NO-FIX).
- `vintage_elektronik`: bare `"ic"` (1 Titel, P2/NO-FIX).
- `konsolen_bundles`: "Display Ersatz Konsole...DISPLAY ONLY" (1 Titel,
  P1, aus vorherigem Arbeitsblock).

Alle diese Fälle wurden gegen den aktuellen 1760-Titel-Korpus erneut
stichprobenartig verifiziert (weiterhin unverändert aktiv oder
weiterhin 0 Neuzugänge) und **nicht** angefasst.

## 9. Empfohlener nächster Fix

**Kein P0 vorhanden.** Der beste P1-Kandidat ist der office_pc/Notebook-
Cluster (Abschnitt 5.1, 21 Titel) — aber er lässt sich nicht als
"minimaler, sicherer YAML-Fix" umsetzen, ohne eine bereits bestehende,
bewusst geschriebene Testentscheidung zu revidieren. Empfehlung: dies
dem Nutzer explizit als Produktentscheidung vorlegen (drei Optionen,
siehe P1-Tabelle Abschnitt 7), **bevor** irgendein Regel- oder
Test-Commit erfolgt. Erst nach dieser Entscheidung Phase 11/12 (Fix +
Regressionstests) starten.

### 9.1 Vertiefung auf Nutzeranfrage: sind die notebook_resell-Preisdeckel (180€/240€) noch realistisch?

Auf explizite Anfrage vertieft, **weiterhin read-only, keine
Regeländerung**. Frage: Ist der office_pc-Leck-Effekt (Abschnitt 5.1)
dadurch verursacht, dass die `notebook_resell`-Preisobergrenzen für
ThinkPad T14/X13/T490/X390/L14 (180€ Top-Deal-Stufe / 240€
Guter-Preis-Stufe) veraltet/zu niedrig sind?

**Historie:** Beide Werte stammen unverändert aus der ursprünglichen
Einführung der Kategorie (Commit `97a59a29`, 2026-08-08,
"feat(rules): drei neue Kategorien (ram, cpu_mainboard_bundle,
notebook_resell)"). Seitdem wurden andere `notebook_resell`-Preise
(RTX-3060/4060-Gaming-Laptop-Regeln: 400/490/550€) in PR "reduce false
positives across five categories" (09.08.) einmal nachkalibriert — die
ThinkPad-Werte 180/240€ NIE.

**Methodisches Problem mit `price_history.jsonl` als alleiniger Quelle:**
`price_history_model: "thinkpad_modern"` hat 141 Datenpunkte, Median
186,16€, **Maximum exakt 240,00€** — das ist kein Zufall, sondern ein
Zensierungs-Artefakt: `price_history.jsonl` wird nur für tatsächlich
**gematchte** Treffer fortgeschrieben (siehe `app.py`-Persistenz-Pfad).
Ein ThinkPad-Titel über 240€ matcht `notebook_resell` gar nicht erst
und kann daher in dieser Reihe **strukturell nie auftauchen** — die
Preishistorie kann die eigene Preisgrenze also nicht validieren
(zirkulärer Messfehler). Als alleinige Datenbasis für eine
Schwellenwert-Anpassung ungeeignet.

**Deshalb stattdessen der volle, ungefilterte Korpus verwendet:** alle
Titel in `data/found.json`, die `"thinkpad"` + einen der Modellcodes
(`t14`/`t490`/`x13`/`x390`/`l14`) enthalten — **unabhängig davon, ob
sie aktuell matchen oder nicht**:

```
Gesamt: 97 reale ThinkPad-Angebote (T14/T490/X13/X390/L14-Familie)
<= 180€ (Top-Deal-Tier):        28 Titel (29 %)
181-240€ (Guter-Preis-Tier):    58 Titel (60 %)
> 240€ (aktuell office_pc-Leck): 11 Titel (11 %)
Median (alle 97):              199,49€
```

**Befund:** 89 % des realen ThinkPad-Angebotskorpus liegen bereits
innerhalb der bestehenden 180/240€-Deckel. Nur eine kleine Minderheit
(11 %, 11 Titel, 249–329€) liegt darüber. Das spricht **gegen** die
Hypothese "die Preisdeckel sind veraltet/zu niedrig" — sie decken den
weit überwiegenden Teil des aktuellen Marktes ab. Zusätzlich fehlt für
eine Anhebung die nach CLAUDE.md Regel 4 geforderte Datenbasis für den
eigentlich relevanten Wert: nicht "was wird verlangt" (Angebotspreis),
sondern "was ist ein echter Deal" (Wiederverkaufswert) — dazu liegen
für die 249–329€-Preisspanne keine Resale-/Verkaufsdaten vor, nur
Angebotspreise. Eine Anhebung ohne diese Evidenz wäre "gefühlt", nicht
datenbasiert.

**Nebenbefund (Datenqualität, nicht Teil dieses Audits, nur notiert):**
`office_pc`s eigene `price_history` (286 Datenpunkte, Median 239,45€)
liegt auffällig nah am `notebook_resell`-Deckel von 240€ — ein Hinweis
darauf, dass ein Teil der `office_pc`-Marktpreis-Statistik bereits
durch genau die in Abschnitt 5.1 identifizierten, fehlgerouteten
Notebook-Titel mitgeprägt ist (Marktpreis-Vermischung Desktop/Notebook).
Nicht in diesem Audit weiterverfolgt, aber ein Argument dafür, den
office_pc/Notebook-Cluster eher früher als später zu klären, bevor sich
die Vermischung in der Preishistorie weiter verfestigt.

**Schlussfolgerung zur Nutzerfrage:** Die Preisdeckel-Hypothese ist
durch die Daten **nicht gestützt** — die 180/240€-Grenzen wirken für
den aktuellen ThinkPad-Markt plausibel kalibriert, keine Anpassung
empfohlen ohne weitere Resale-Datenbasis. Der office_pc-Leck-Effekt aus
Abschnitt 5.1 bleibt damit ein Problem der **fehlenden Notebook-
Excludes in `office_pc.yaml`**, nicht der Preisgrenzen in
`notebook_resell.yaml`. Die ursprüngliche P1-Entscheidung aus Abschnitt
7 (drei Optionen) steht damit weiterhin offen und wird durch diesen
Befund eher in Richtung "Notebooks aus office_pc ausschließen" oder
"Status quo bewusst bestätigen" verschoben als in Richtung "Preisdeckel
anheben".

---

## Zusammenfassung

| Kategorie | Routing-FPs gefunden | behoben | zurückgestellt | Tests |
|---|---:|---:|---:|---|
| office_pc | 22 (21 Notebook-Cluster + 1 MacBook-Einzelfall) | 0 | 22 (P1, Entscheidungsbedarf) | — (Read-Only-Phase) |
| gaming_pc | 1 (Domino-Fall, Ursache in office_pc) | 0 | 1 (Teil des office_pc-Clusters) | — |
| alle übrigen 17 Kategorien | 0 neue Funde | 0 | — | — |

- **Anzahl geprüfter Titel:** 1760 (vollständiger `found.json`-Korpus,
  nicht nur Stichprobe).
- **Anzahl Cross-Category-Kandidaten** (Fremdsignal-Sweep + Diff-Check):
  ~140 Rohtreffer vor manueller Prüfung.
- **Anzahl echter Routing-FPs:** 22 (office_pc/Notebook-Cluster + 1
  MacBook-Einzelfall).
- **Anzahl behobener Routing-FPs:** 0 (Phase 0–10 ist read-only; kein
  mechanisch sicherer P0 identifiziert, siehe Abschnitt 7).
- **Anzahl P1/P2:** 2 Cluster (22 Titel gesamt) P1, 0 neue P2.
- **Anzahl NO-FIX:** 0 neue (bestehende NO-FIX-Fälle aus dem
  Vorgänger-Audit unverändert).
- **Anzahl TP-Kollisionen:** 1 dokumentiert (`test_reale_true_positives_matchen_weiterhin`
  in `test_office_pc_active_fp_audit_fix.py` würde durch einen naiven
  Notebook-Exclude brechen — das ist der Grund, warum Abschnitt 7 keinen
  P0 ausweist).

**Rule Analyzer nach Abschluss:** unverändert 0 Findings, 355 Regeln,
19 Kategorien (keine Regel wurde in diesem Durchlauf verändert).

**Git-Status nach Abschluss:** unverändert gegenüber Sessionbeginn
(nur Scanner-Artefakte in `data/`, keine Commits in diesem Durchlauf).

**Volle Testsuite:** in der Read-Only-Phase (Abschnitte 1–9) nicht
ausgeführt. Nach dem in Abschnitt 10 dokumentierten Fix ebenfalls noch
nicht ausgeführt (Vorgabe Phase 13/14: erst kategorienbezogene Tests
nach jedem Einzel-Fix, volle Suite erst am Ende des gesamten
Cross-Category-Durchlaufs bzw. auf explizite Anfrage).

## 10. Umgesetzter Fix: office_pc-Notebook-Exclude

Auf Nutzerentscheidung (nach der Preisdeckel-Vertiefung in Abschnitt
9.1, die eine Anhebung der `notebook_resell`-Preisgrenzen verworfen
hat) umgesetzt: **Option "Notebooks aus office_pc ausschließen"**.

**Geänderte Dateien:**

- `app/rules/office_pc.yaml` — `exclude_category` um `laptop`,
  `notebook`, `thinkpad`, `macbook`, `ideapad`, `alienware`, `lifebook`
  erweitert (bare Markenbegriffe zusätzlich zu "laptop"/"notebook",
  weil mehrere reale Titel keines der beiden Wörter enthalten, z.B.
  `"Lenovo ThinkPad X390 | 13,3\" | i5-8365U..."`).
- `app/tests/test_office_pc_active_fp_audit_fix.py` — die bestehende
  `test_reale_true_positives_matchen_weiterhin()` enthielt 2 Titel
  ("ACEMAGIC ... Laptop ...", "Lenovo ThinkPad X390 | 13,3\" | ...."),
  die durch diesen Fix jetzt bewusst NICHT mehr office_pc matchen.
  Diese 2 Einträge entfernt und durch 2 weitere reale, unveränderte
  Desktop-TRUE_POSITIVES aus demselben Korpus ersetzt (Dell Precision
  3450, Custom Gaming PC), damit der Test weiterhin ausschließlich
  echte, unveränderte TRUE_POSITIVE-Fälle prüft.
- `app/tests/test_office_pc_notebook_cross_category_fix.py` (neu) — 9
  Tests: 5 reale FP-Regressionstests (decken alle 7 neuen
  Exclude-Begriffe ab, inkl. dem Domino-Fall aus Abschnitt 3), 1
  Sammel-TP-Sicherheitstest für 4 reale Desktop-Titel, 2 Grenzfalltests
  (ThinkPad über 240€ landet bewusst unmatched statt in office_pc;
  derselbe Modellcode unter 240€ matcht weiterhin korrekt
  notebook_resell — der office_pc-Exclude darf notebook_resell selbst
  nicht beeinflussen).

**Verifikation gegen den vollständigen Korpus (nach dem Fix, echte
Preise):**

```
office_pc-Treffer vorher: 43 (21 Notebooks + 22 echte Desktop-/Bundle-Titel)
office_pc-Treffer nachher: 21 -- ausschließlich echte Desktop-/Tower-/
                                  Bundle-Titel, 0 verbleibende Laptop-
                                  Signalwörter
```

Alle 22 ursprünglich betroffenen Titel (21 aus Abschnitt 5.1 + der
Domino-Fall aus Abschnitt 3, der zu den 21 zählt) wurden erneut einzeln
gegen den geänderten Ruleset ausgewertet: **alle 22 sind jetzt sauber
`unmatched`** — kein einziger reroutet in eine andere, ebenfalls
falsche Kategorie (insbesondere nicht in `notebook_resell`,
`gaming_pc`, `cpu_mainboard_bundle` oder eine der übrigen 16
Kategorien). Damit ist die in Abschnitt 3 aufgeworfene Kernfrage dieses
Audits ("Exclude verschiebt den Fehltreffer nur in eine andere falsche
Kategorie") für diesen Fix mit "Nein" beantwortet.

**Tests:** `pytest tests/ -k "office_pc or gaming_pc or notebook_resell" -v`
→ **49/49 passed**. `rule_analyzer.py` → weiterhin **0 Findings, 355
Regeln, 19 Kategorien** (Regelanzahl unverändert, nur Exclude-Liste
erweitert).

**Nicht angefasst (bewusst außerhalb dieses Fixes):** der in Abschnitt
5.2 dokumentierte `macbook`-Einzelfall (`Apple MacBook Pro 16.1 | ...
OHNE OS ...`) landet nach diesem Fix korrekt `unmatched` statt
`office_pc` — matcht aber weiterhin NICHT die dedizierte
`macbook`-Kategorie. Das ist ein separater, noch offener P2-Befund
(eigener Deep-Dive in `macbook.yaml` nötig) und war nicht Teil der
Nutzer-Freigabe für diesen Schritt.

**Volle Testsuite:** noch nicht ausgeführt (Vorgabe Phase 13: erst nach
Abschluss des gesamten Cross-Category-Durchlaufs oder auf explizite
Anfrage, nicht nach jedem Einzelfix).
