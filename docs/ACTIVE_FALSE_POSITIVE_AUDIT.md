# Active False Positive Audit

Systematischer Abgleich des produktiven Rulesets (`app/rules/*.yaml`)
gegen den echten Produktivkorpus, mit Fokus auf `handhelds.yaml`. Kein
theoretischer Ruleset-Review — nur aktuell aktive, reale Fehltreffer.

## Zahlen auf einen Blick (autoritativ, siehe Tabellen unten für Details)

| Größe | Wert | Definition |
|---|---:|---|
| Real aktive FP-Titel **gesamt** in diesem Audit | **21** | alle real bestätigten Fehltreffer-Titel über alle Kategorien, gefixt + zurückgestellt |
| davon **gefixt** (handhelds, dieser Schritt) | **10 Titel** | über **8 root-cause Muster** (ein Muster kann mehrere Titel abdecken) |
| davon **zurückgestellt** (P1/P2, alle Kategorien) | **11 Titel** | über **5 Fälle** (Kategorie×Muster-Kombinationen) |
| neue `exclude_category`-Terme (handhelds.yaml) | **12** | siehe Liste unten |

Diese vier Zahlen sind bewusst unterschiedlich und beschreiben
unterschiedliche Dinge — sie werden im Folgenden nicht mehr synonym
verwendet:

- **"Muster" / "Fälle"** = distinkte Root-Causes (z.B. "Ersatzstift/
  Touchpen/Stylus" ist EIN Muster, deckt aber 3 Titel ab).
- **"Titel"** = einzelne, reale `found.json`-Anzeigen.
- **"Terme"** = einzelne neue YAML-Exclude-Einträge (ein Muster kann
  mehrere Terme benötigen, z.B. "ersatzstift" + "ersatzstifte" +
  "touchpen" + "stylus" für ein Muster).

## Scope

- **Daten:** `data/found.json` (1736 eindeutige Titel, echte Preise),
  Live-Auswertung über `matcher.load_rules()` + `matcher.evaluate()`
  gegen die produktiven `app/rules/*.yaml` (19 Kategorien, 355 Regeln).
- **Methodik-Hinweis (wichtig):** Alle Titel wurden mit ihrem **echten**
  `found.json`-Preis ausgewertet, nicht mit `price=0.0`. Ein Test mit
  `price=0.0` verzerrt First-Match-Wins bei preisgedeckelten Regeln
  (z.B. `controller`-Regeln mit `max_price` 12–35€) systematisch
  zugunsten günstiger Kategorien. Das führte initial zu einer
  Falschmeldung (siehe Abschnitt "Routing / First-Match-Wins" unten).
- **Fokus:** vollständiger Deep-Dive für `handhelds.yaml` (alle 22
  aktuell live matchenden Treffer einzeln bewertet); für alle übrigen
  18 Kategorien ein Keyword-Sweep über Zubehör-/Ersatzteil-/Software-
  Signalwörter auf den aktuell matchenden Titeln, mit manueller
  Einzelprüfung jedes Treffers.
- Bereits gelöste Muster (siehe `docs/KONSOLEN_BUNDLES_REVIEW.md`,
  `docs/KONSOLEN_BUNDLES_OVP_ANALYSE.md`, bestehende Regressionstests)
  wurden nicht erneut als Findings gemeldet.

## Aktive echte Fehltreffer

**Gefixt in diesem Schritt (handhelds, 8 Muster / 10 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| handhelds | Displayschutz-Folie (Kompositum) | `2x 9H Gehärtetes Displayschutz für Lenovo Legion Go...` | 1 |
| handhelds | Controller-Grip-Zubehör | `Ergonomischer Performance Controller Grip...Zubehör` | 1 |
| handhelds | Ersatzstift/Touchpen/Stylus | `Ersatzstifte für die Konsolen...` + 2× `...Touchpen Stylus Ersatzstift...` | 3 |
| handhelds | Schutzhülle (Kompositum) | `Schutzhülle für Lenovo Legion Go - Neu` | 1 |
| handhelds | leere Sammler-Verpackung | `...LEERE BOX mit Inlay` | 1 |
| handhelds | "Spiele für Konsole" (Software statt Gerät) | `Spiele für NINTENDO 3DS XL Konsole - Top` | 1 |
| handhelds | abgetrennte Controller-Hälfte | `Lenovo Legion Go Controller Rechts` | 1 |
| handhelds | Flash-Karte/Spielkarte | `...Flash Karte...Spielkarte` | 1 |
| **Summe** | **8 Muster** | | **10 Titel** |

**Zurückgestellt, real bestätigt, nicht Teil dieses Schritts (P1/P2, 5 Fälle / 11 Titel):**

| Kategorie | Priorität | Muster | Anzahl Titel | Grund für Zurückstellung |
|---|---|---|---:|---|
| handhelds | P1 | Fanxiang M.2 2230 SSD-Einbauteil für Steam Deck | 2 | enger Kandidat, eigener Review-Schritt |
| handhelds | P2 | USB-C-HDMI-Adapterkabel | 1 | Kollisionsrisiko mit echten Spec-Angaben |
| konsolen_bundles | P1 | `Display Ersatz Konsole...DISPLAY ONLY` trotz Geräte-Marker (V2/HAC-001) | 1 | eigener Arbeitsschritt (anderes File) |
| office_pc | P1 | `Lenovo ThinkPad X390 Mainboard...NM-B891` | 1 | in notebook_resell bereits gefixt, Lücke in office_pc, eigener Schritt |
| retro_konsolen | P1 | Standalone Memory Cards (PS1/PS2/GameCube) | 6 | eigener Arbeitsschritt (anderes File) |
| **Summe** | | **5 Fälle** | **11 Titel** | |

**Gesamt in diesem Audit real bestätigt: 10 + 11 = 21 Titel.**

## Handhelds

- **22** aktuell live matchende reale Treffer vollständig einzeln geprüft.
- **8 echte False-Positive-Muster über 10 Titel** bestätigt und in diesem
  Schritt behoben.
- **2 weitere Muster über 3 Titel** real bestätigt, aber zurückgestellt
  (P1/P2, siehe Tabelle oben).
- Bereits korrekt gelöste Muster (nicht erneut gemeldet): Netzteil/
  Ladekabel/Ladegerät/Anleitung (Phase 14), Dockingstation/Mainboard/
  Motherboard/Memory Card/microSD/For-Parts/Not-Working/
  Batterieabdeckung (found.json-Audit), Hub/Skin/Faceplate/Vinyl/
  Klebefolie/Aufkleber/Ladeadapter/Reisetasche (Dashboard-Forensics),
  Gehäuse/Joystick/Thumbstick (kontextbewusst, Phase 15).
- Keine belegten Probleme bei: Steam Deck (0 aktive FPs unter den
  aktuell sichtbaren Treffern über die o.g. hinaus), PS Vita/3DS-
  Kernregeln (keine weiteren aktiven Fehltreffer).
- **1 Grenzfall ohne Fix (NO-FIX):** `Lenovo Legion Go` (bare, 15€) —
  kein Zubehör-/Ersatzteil-Signal im Titel, aus dem Titeltext allein
  nicht sicher als Fehltreffer zu identifizieren.

## Routing / First-Match-Wins

**Untersuchter Fall:** `Microsoft Xbox One X 1TB Schwarz Inkl OVP Ohne
Controller`.

Bei Prüfung mit `price=0.0` matchte dieser Titel fälschlich `controller`
(Regel "Xbox Wireless Controller ★ Top-Deal", `max_price` 20€ — bei
Preis 0 innerhalb des Caps, First-Match-Wins vor `konsolen_bundles`
wegen niedrigerer `scan_priority`, 6 vs. 8). Bei Prüfung mit dem
**echten** `found.json`-Preis (75€) matcht der Titel jedoch korrekt
`konsolen_bundles` (Regel "Xbox One S / One X 👍 Guter Preis",
`max_price` 90€) — die `controller`-Regeln (`max_price` 20/30€) greifen
bei 75€ gar nicht erst.

**Klarstellung:** Dies ist **kein realer aktiver Fehltreffer**, sondern
ein **Testartefakt** der ursprünglichen Prüfmethodik (`price=0.0` statt
echtem Preis). Der Fall ist **nicht** in den obigen Zählungen (21 Titel)
enthalten und wurde in keinem der beiden Audit-Blöcke als Finding
mitgezählt. Der in `controller.yaml` bereits vorhandene Kommentar zu
diesem genauen Kollisionsrisiko (Zeilen 50–54) bleibt als dokumentiertes
Restrisiko gültig, ist aber aktuell durch keinen realen Treffer belegt.

## Ausgeschlossene hypothetische Fälle

Diese Fälle sind **keine real bestätigten Fehltreffer** (anders als die
"zurückgestellten P1/P2-Fälle" oben, die real belegt, aber noch nicht
gefixt sind) — sie wurden geprüft und mangels Datenbasis oder wegen
Kollisionsrisiko bewusst NICHT umgesetzt:

**In diesem Audit neu geprüft und verworfen (4):**

1. `ersatzknopf`/`ersatzknöpfe`/`flashkarte`/`leerkarton` (handhelds) —
   0 Treffer im vollständigen Korpus, keine Datenbasis (Phase 6).
2. `ssd` als bare Exclude (handhelds) — aktuell 0 Kollisionen, aber
   bewusst NICHT verwendet: zu breit, ein reales Steam-Deck-Angebot
   könnte künftig legitim "SSD" im Titel nennen. Die engere Phrase
   `"m.2 2230"` (siehe P1-Tabelle oben) ist der sicherere Kandidat für
   einen künftigen Schritt.
3. `"Controller Links"`/`"Rechter Controller"`/`"Linker Controller"`
   (handhelds) — 0 Treffer im Korpus, nicht ergänzt.
4. genereller `"für [Plattform]"`-Exclude für handhelds — ein
   bestätigter TRUE_POSITIVE-Kollisionsfall (`Nintendo 2DS
   Handheld-System Konsole für Nintendo 3DS Plattform Weiß/Rot`) zeigt,
   dass ein naiver Exclude ohne den vollen Geräte-Marker-Mechanismus aus
   `konsolen_bundles.yaml` echte Geräte blockieren würde.

**Referenz aus vorherigem Arbeitsblock (nicht Teil dieses Audits, nur
zur Einordnung genannt):**

- "+"-Bundle-Recall-Lücke (`Nintendo Switch + 2 Controller + Spiele`) —
  weiterhin 0 reale Verlustfälle im Korpus, unverändert NO-FIX aus dem
  vorherigen Arbeitsblock. Kein neuer Befund dieses Audits.

## Implementierter Fix

`app/rules/handhelds.yaml`, `exclude_category`: **12 neue** bare-word/
phrase Excludes für die **8 gefixten Muster** (`displayschutz`,
`ersatzstift`, `ersatzstifte`, `touchpen`, `stylus`, `schutzhülle`,
`grip`, `leere box`, `spielkarte`, `flash karte`, `spiele für`,
`controller rechts`). Alle 0 Kollisionen gegen den vollständigen
1736-Titel-Korpus (jeder Begriff kommt in Kombination mit einem
Handheld-Markennamen ausschließlich im jeweils identifizierten
Fehltreffer-Titel vor). Reine additive `exclude_category`-Ergänzung,
kein neuer Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_handhelds_active_fp_audit_fix.py`
(12 Tests: 9 FP-Regressions-Testfunktionen, die zusammen alle 10 real
bestätigten Fehltreffer-Titel abdecken, 1 Sammel-TP-Sicherheitstest für
6 reale TRUE_POSITIVES, 1 Grenzfalltest gegen die "für Plattform"-
TRUE_POSITIVE-Kollision, 1 bestehende Pokémon-Bundle-Sicherheitsprüfung).

## Testergebnis

- `pytest app/tests/test_handhelds_active_fp_audit_fix.py -v`: **12/12 passed**
- `pytest app/tests/ -k "handheld" -v`: **59/59 passed**
- `rule_analyzer.py`: **0 Findings, 355 Regeln, 19 Kategorien** (unverändert)
- Volle Suite `pytest app/tests/`: **1197/1197 passed, 0 failed**
  (604s Laufzeit, tatsächlich ausgeführt in dieser Session).
