# Technische Vorbereitung der Entscheidungen 1–4

**Erstellt:** 2026-08-14 · **Charakter:** vollständig READ-ONLY. Keine `price_history.jsonl`-,
`found.json`-, `seen.json`- oder YAML-Änderung. Keine Migration, keine Löschung, keine
Regel-Optimierung. Kein Commit, kein Push, kein Merge, kein PR.

Nutzt ausschließlich den bestehenden Produktions-Matchpfad (`matcher.evaluate()`) und die
bereits vorhandenen Klartext-Titel-Quellen (`data/found.json`, `docs/DASHBOARD_MATCH_FORENSICS.json`).
Skript: `tools/ruleset_quality/final_decisions_prep.py`, Rohdaten:
`generated/reports/final_decisions_prep.json`.

---

## 1. `roehrenfernseher` — Bestätigung (keine erneute Optionsbewertung)

Die Entscheidung (Option A, eigenständiges Modell) ist final und wurde in
`OFFENE_ENTSCHEIDUNGEN_1_BIS_3_BERICHT.md` bereits inhaltlich begründet. Hier nur eine frische
Gesundheitsprüfung, keine neue Analyse der Optionen A/B/C:

```text
Anzahl historischer Punkte:        96 (unverändert)
Zeitraum:                          2026-08-03 bis 2026-08-14 (weiterhin durchgehend bis heute)
Titel rekonstruierbar:             26
Davon valide bei Neubewertung:     25 (96,2%)
Aktuell live matchende Einträge:   13
```

**Status: aktiv, gesund. Keine Regel-, Modell- oder Datenänderung nötig oder vorgeschlagen.**

---

## 2. Orphan-Modelle aus `spielzeug_bundles` — Migrations-/Lösch-Dry-Run

### 2.1 `lego_bundle` → Migration nach `lego_minifiguren` (Teilmenge)

**Selektionsregel (streng, alle drei Kriterien gleichzeitig erforderlich):**

> MIGRIERBAR nur wenn (a) echter Titel rekonstruierbar (`found.json` ODER
> `DASHBOARD_MATCH_FORENSICS.json`) **UND** (b) Titel enthält wörtlich „minifig“/„minifigur"
> **UND** (c) `evaluate(titel, preis, aktuelle_regeln)` matcht auf Kategorie `lego_minifiguren`
> mit `price_history_model` ∈ {`lego_minifig_bundle`, `lego_ninjago_bundle`}.

```text
Punkte gesamt:                     404
Titel rekonstruierbar:             8   (2,0%)
  davon MIGRIERBAR:                 5
  davon NICHT MIGRIERBAR:           3
Titel NICHT rekonstruierbar:       396 (98,0%) — separat ausgewiesen, nicht migriert
```

**Migrierbar (5, konkret):**

| Titel | Preis | Zielmodell |
|---|---|---|
| Lego Ninjago 8 besondere Minifiguren, Sammlung K6 | 13 € | `lego_ninjago_bundle` |
| LEGO Minifiguren Konvolut | 59 € | `lego_minifig_bundle` |
| Lego Star Wars General Grievous Starfighter 8095 mit Minifiguren, Konvolut | 60 € | `lego_minifig_bundle` |
| LEGO Minifiguren Konvolut | 40 € | `lego_minifig_bundle` |
| LEGO Ninjago Minifiguren Sammlung | 1 € | `lego_ninjago_bundle` |

**Nicht migrierbar (3, rekonstruierbar aber Kriterium (c) bzw. (b)+(c) verfehlt):**

| Titel | Preis | Grund |
|---|---|---|
| LEGO Figuren Sammlung | 75 € | kein eindeutiger Minifiguren-Bezug im Titel, matcht nichts |
| Lego star wars minifiguren Konvolut | 75 € | Minifig-Bezug vorhanden, aber über der 60-€-Obergrenze von `lego_minifig_bundle` — matcht nichts |
| LEGO Star Wars Figuren Konvolut | 95 € | kein eindeutiger Minifiguren-Bezug, matcht nichts |

**396 nicht rekonstruierbare Punkte:** alter Bestand (einziger Zeitstempel 2026-08-03), längst aus
beiden verfügbaren Klartext-Quellen herausrotiert. Nach der obigen Regel **nicht migrierbar**, da
Kriterium (a) fehlt — sie werden hier **nicht** automatisch dem alten oder einem neuen Modell
zugeordnet, das wäre eine unbelegte Annahme. Verbleib erfordert eine gesonderte Entscheidung
(z. B. beim inaktiven Namen `lego_bundle` belassen, archivieren, oder pauschal als „nicht
beurteilbar“ kennzeichnen).

### 2.2 `playmobil_bundle` — Lösch-Dry-Run

```text
Punkte gesamt (= zu löschen):      210
Zeitraum:                          2026-08-03 (ein einzelner Tag, kein laufender Zufluss)
Median/Min/Max:                    29,16 € / 1,00 € / 100,00 €
Distinkte Fingerprints:            196
Titel rekonstruierbar:             0 / 210 (erneut geprüft, unverändert ggü. letztem Bericht)
```

Strukturell verifiziert (frisch erneut geprüft): `grep -ril "playmobil" app/rules/*.yaml` → **0
Treffer**. Kein aktives Regelwerk deckt Playmobil-Ware ab.

**Selektionsregel Löschung:** exakte Gleichheit `model == "playmobil_bundle"` in
`price_history.jsonl` (kein Präfix-/Teilstring-Match) → betrifft exakt diese 210 Zeilen.

### 2.3 `spielzeug_bundle_sonstige` — Lösch-Dry-Run

```text
Punkte gesamt (= zu löschen):      49
Zeitraum:                          2026-08-03 (ein einzelner Tag, kein laufender Zufluss)
Median/Min/Max:                    20,00 € / 2,50 € / 90,00 €
Distinkte Fingerprints:            49
Titel rekonstruierbar:             0 / 49 (erneut geprüft, unverändert)
```

Strukturell verifiziert: kein aktives Regelwerk matcht generisches `"spielzeug"` mehr.

**Selektionsregel Löschung:** exakte Gleichheit `model == "spielzeug_bundle_sonstige"` (kein
Präfix-/Teilstring-Match) → betrifft exakt diese 49 Zeilen.

### Reversibilität (für 2.2 und 2.3 identisch)

Vor Ausführung: Sicherungskopie von `data/price_history.jsonl` außerhalb des Git-Verlaufs (z. B.
`price_history.jsonl.bak-<datum>`). Löschung als Zeilenfilter (`model != "<wert>"`), keine
Neuschreibung anderer Zeilen — bei Bedarf durch Zurücklegen der Sicherungskopie vollständig
reversibel, solange kein nachfolgender Scan-Lauf zwischenzeitlich neue Zeilen angehängt hat.

### Exakte Gesamtzählung Punkt 2

```text
Migrierbar (lego_bundle):                    5
Nicht migrierbar, aber rekonstruierbar:       3   (lego_bundle)
Nicht rekonstruierbar (weder Ziel noch
  Ausschluss beurteilbar):                  396   (lego_bundle)
Löschbar (kein Zielmodell, strukturell
  verifiziert, unabhängig vom Titel):       259   (210 playmobil_bundle + 49 spielzeug_bundle_sonstige)
```

---

## 3. UNCLEAR-Fälle — 21/14 korrigiert zu 22/13 (echter Preis statt price=0.0)

**Methodische Präzisierung ggü. dem letzten Bericht:** Die vorherige 21/14-Aufteilung nutzte
`evaluate(titel, 0.0, regeln)` — reine Inhaltsprüfung ohne Preisschwelle. Für die jetzt geforderte
Vertiefung der Preisstufen-Frage wurde mit dem **echten historischen Preis** neu bewertet. Dabei
verschiebt sich ein Fall (Xbox One S Bundle, 80 €) von „stabil laut Inhalt“ tatsächlich korrekt in
die stabile Gruppe (Kategorie/Modell bleiben bei echtem Preis unverändert) — die Gesamtaufteilung
lautet bei Verwendung des echten Preises **22 stabil / 13 verändert** (statt 21/14). Beide Zahlen
sind intern konsistent, unterscheiden sich nur in der verwendeten Preis-Methodik; die 22/13-Zahl
ist die für Preisschwellen-Fragen maßgebliche.

```text
UNCLEAR gesamt:     35
Stabil:             22  (Kategorie + price_history_model unverändert bei echtem Preis)
Verändert:          13  (Kategorie/Modell geändert ODER kein Treffer mehr bei echtem Preis)
```

### Die 13 veränderten Fälle, getrennt nach Ursache

**7 Fälle — eindeutig preisschwellenbedingt** (matchen bei jedem Preis < 35 € inhaltlich auf
`controller/controller_switch_pro`, scheitern nur an der aktuellen 35-€-Obergrenze):

| Titel | Realer Preis |
|---|---|
| 2x Nintendo Switch 2 Pro Controller NEU OVP | 130,00 € |
| Nintendo Switch Pro Controller - Schwarz mit OVP kaum genutzt | 39,00 € |
| Nintendo Switch Pro Controller in OVP | 50,00 € |
| Nintendo Switch Pro Controller, TOP Zustand mit OVP | 45,00 € |
| NEU - OVP! Nintendo Switch Pro Controller - Monster Hunter Rise Sunbreak Edition | 75,00 € |
| Nintendo Switch Pro Controller Original \| OVP \| TOP Zustand | 39,99 € |
| Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP | 79,99 € |

**Korrektur ggü. letztem Bericht:** Es sind **7**, nicht 6, Switch-Pro-Controller-Fälle — der Titel
„Monster Hunter Rise Sunbreak Edition“-Controller wurde zuvor nicht mitgezählt, ist aber inhaltlich
eindeutig ein Switch-Pro-Controller-Angebot (matcht bei jedem Preis unter 35 € regulär).

**6 Fälle — matchen inhaltlich gar nichts mehr** (unabhängig vom Preis; historische Punkte für
eine Revalidierung ohnehin „nicht mehr gültig“):

| Titel | Realer Preis |
|---|---|
| Nintendo Switch 2 GameCube Controller \| OVP \| NEU | 85,00 € |
| Nintendo Switch 2 GameCube Controller – Nintendo Classics – OVP – NEU | 85,00 € |
| Nintendo Switch - Minecraft FRA mit OVP | 19,89 € |
| Pokémon Let's Go Evoli! Nintendo Switch – OVP komplett | 39,00 € |
| Nintendo Switch - Controller Joy-Con Neon-Grün/Neon-Pink 2er - NEU OVP | 59,99 € |
| Bayonetta & Vanquish 10th Anniversary Bundle - PlayStation 4 - Neu & OVP | 19,00 € |

**Kein Blocker für eine Preishistorien-Revalidierung** — 6 der 13 sind bereits inhaltlich ungültig,
unabhängig vom Preis; die übrigen 7 sind ein reiner, gut verstandener Preisschwellen-Effekt.

### Vorbereitung: mögliche dritte Preisstufe „Switch Pro Controller“ (nur Empfehlung, keine YAML-Änderung)

**Aktuelle Regel (`app/rules/controller.yaml`):**

```yaml
- label: "Switch Pro Controller ★ Top-Deal"
  price_history_model: "controller_switch_pro"
  require_all_of: [["switch"], ["pro controller", "pro-controller"]]
  exclude: ["drift", "defekt", "bastler"]
  max_price: 25
  deal_rating: "Top-Deal"

- label: "Switch Pro Controller 👍 Guter Preis"
  price_history_model: "controller_switch_pro"
  require_all_of: [["switch"], ["pro controller", "pro-controller"]]
  exclude: ["drift", "defekt", "bastler"]
  max_price: 35
  deal_rating: "Guter Preis"
```

**Korrektur einer Fehleinschätzung im letzten Bericht:** Dort wurde die 2-Stufigkeit als Ausnahme
„anders als fast alle anderen Regelfamilien“ bezeichnet. Bei erneuter Prüfung über **alle**
`app/rules/*.yaml` stimmt das nicht: eine dritte „⚠️ Okay“-Stufe ist die Ausnahme, nicht die Regel
(nur in `gaming_pc`, `office_pc`, `retro_konsolen`, `vintage_elektronik`, 4 von 19 Kategorien). Alle
anderen `controller.yaml`-Regelfamilien (PS5 DualSense, Xbox Series/One, jeweils voll
funktionsfähig) haben ebenfalls nur 2 Stufen. Eine dritte Stufe für Switch Pro Controller wäre eine
bewusste Abweichung vom in `controller.yaml` etablierten Muster, kein Angleich an eine Norm.

**Reale Preise der 7 Fälle:** 39,00 € · 39,99 € · 45,00 € · 50,00 € · 75,00 € · 79,99 € · 130,00 €
(Median 50,00 €)

**Optionen (keine wird hier final empfohlen — siehe unten):**

| Option | Obergrenze | Deckt ab | FP-Risiko |
|---|---|---|---|
| A — keine dritte Stufe | — | 0/7 | keins zusätzlich; konsistent mit allen anderen Voll-funktionsfähig-Regeln in `controller.yaml` |
| B — „⚠️ Okay“ bis 45 € | 45 € | 4/7 (39/39,99/45/50 knapp verfehlt) | moderat — generische `switch`+`pro controller`-Treffer ohne Zusatzsignal werden häufiger als Deal markiert |
| C — „⚠️ Okay“ bis 80 € | 80 € | 7/7 | hoch — nahe am Neupreis, verwässert die Deal-Definition erheblich; das 130-€-Bundle (2 Controller, Stückzahl-Ambiguität) müsste ohnehin separat betrachtet werden |

**Benötigte Regressionstests bei Umsetzung:**
1. Neuer Testfall je Preisgrenze (genau an / knapp unter / knapp über der neuen Obergrenze)
2. Regressionstest: bestehende Top-Deal-/Guter-Preis-Stufen bleiben unverändert
3. `rule_analyzer.py`-Lauf nach Änderung (Duplikat-/Exclude-Konflikt-Check)
4. Stichprobe historischer `price_history.jsonl`-Punkte mit `price_history_model=controller_switch_pro`,
   um sicherzustellen, dass die neue Stufe keine bereits als „kein Treffer“ akzeptierten Altfälle
   unerwünscht reaktiviert

**Empfehlung:** Keine der drei Optionen wird hier final empfohlen — das ist eine
Preisgrenzen-Entscheidung ohne belastbare Datenbasis (nur 7 Fälle, kein Markt-/Resale-Vergleich)
und fällt damit unter CLAUDE.md Regel 4 (keine Threshold-Änderung ohne Datenbasis). Diese
Vorbereitung liefert ausschließlich die Fakten für eine spätere, separat zu beauftragende
Entscheidung.

---

## 4. Frische-Prüfung des 251-Listing-Stichprobenplans

```text
Worksheet-Größe:                    251
Aktueller found.json-Korpus:        2500 Einträge, 19 Kategorien
Davon noch im aktuellen Korpus:     251 / 251 (100%)
```

**Ergebnis: Keine Neuziehung nötig.** Das Worksheet wurde am selben Tag (2026-08-14) in der
vorherigen Session erzeugt — seither ist noch keine relevante Zeit vergangen, daher 100% Deckung.
Das steht nicht im Widerspruch zum früher beobachteten Abdeckungszerfall (19,2% → 0,6% über 3
Tage) — jener Vergleich betraf einen mehrere Tage alten Snapshot, nicht diese taggleiche Ziehung.

**Handlungsempfehlung bleibt unverändert aus dem letzten Bericht:** Da der Korpus schnell rotiert,
sollten zwischen Ziehung und tatsächlichem Labeling **nicht mehr als 24–48h** liegen. Wird das
Labeling nicht innerhalb dieses Fensters durchgeführt, sollte unmittelbar davor über
`tools/ruleset_quality/sampling_plan.py` frisch gezogen werden (Skript unverändert vorhanden,
deterministischer Seed für Reproduzierbarkeit des Plans, nicht der Ziehung selbst).

**Manueller Labeling-Prozess (unverändert vorgeschlagen):**
1. Manuelle Durchsicht der 251 Zeilen in `sampling_worksheet_template.csv`, gleiche Kriterien wie
   im ursprünglichen Forensik-Snapshot (TRUE_POSITIVE/FALSE_POSITIVE/UNCLEAR + kurze Begründung in
   den Spalten `verdict_TP_FP_UNCLEAR`/`root_cause`/`reason`).
2. Ergebnis wird als **neue, separate Quelle** im Ground-Truth-Label-Store abgelegt — mit eigenem
   `source`/`source_date` (z. B. `source="sampling_worksheet_2026-08-14"`), die bestehende Quelle
   `DASHBOARD_MATCH_FORENSICS.json` (Commit `01afd5b`) wird **nicht** überschrieben. So bleiben
   Alter und Herkunft jedes Labels jederzeit unterscheidbar, und künftige Auswertungen können beide
   Quellen getrennt oder kombiniert betrachten.
3. **Methodik-Pflicht:** jede künftige automatisierte Re-Validierung dieser neuen Labels muss den
   **echten Titel** verwenden, nicht `PricePoint.fingerprint` (siehe Umlaut-Fingerprint-Befund aus
   dem letzten Bericht) — sonst wiederholt sich der dort gefundene Fehler.

---

## Zusammenfassung: Später auszuführen nach Freigabe

| # | Aktion | Zielmenge | Risiken | Rückfallmöglichkeit |
|---|---|---|---|---|
| 1 | `lego_bundle`: 5 Punkte nach `lego_minifig_bundle`/`lego_ninjago_bundle` migrieren | 5 von 404 Punkten | minimal — Selektionsregel dreifach abgesichert (Titel + Minifig-Bezug + aktueller Regel-Match) | Sicherungskopie vor Migration; Migration ist ein reiner Feldwert-Update (`model`), reversibel durch Zurückschreiben des alten Werts |
| 2 | `lego_bundle`: 396 nicht rekonstruierbare Punkte — Verbleibs-Entscheidung treffen (belassen/archivieren/kennzeichnen) | 396 von 404 Punkten | keine technische Aktion vorbereitet, da Zielzustand noch offen | — (offene Entscheidung, siehe unten) |
| 3 | `playmobil_bundle` vollständig löschen | 210 Punkte | gering — strukturell verifiziert kein Zielmodell; Datenverlust ist bei Fehlentscheidung nicht rückgängig zu machen ohne Backup | Pflicht-Sicherungskopie vor Löschung; Zeilenfilter-Ansatz, kein Rewrite anderer Zeilen |
| 4 | `spielzeug_bundle_sonstige` vollständig löschen | 49 Punkte | gering — analog zu 3 | analog zu 3 |
| 5 | Dritte Preisstufe „Switch Pro Controller“ in `controller.yaml` | 1 neue Regelzeile, betrifft künftige Scans + 7 historische UNCLEAR-Fälle | mittel bis hoch je nach gewählter Obergrenze (siehe Optionstabelle B/C) — Threshold-Entscheidung ohne Datenbasis lt. CLAUDE.md Regel 4 | YAML ist volume-gemountet, sofort reversibel durch Zurücksetzen der Zeile; kein Rebuild nötig |
| 6 | 251-Listing-Worksheet labeln | 251 Listings | keins (reine Leseaufgabe) | entfällt |
| 7 | Kontrollierte Preishistorien-Revalidierung (nach Labeling) | gesamter `price_history.jsonl`-Bestand, methodisch mit echten Titeln statt Fingerprints | mittel — größter noch offener Schritt, bisher nur vorbereitet, nicht ausgeführt | rein lesende Simulation vor jeder produktiven Änderung, wie in dieser und den vorherigen Sessions |

## Offene Entscheidungen (explizit, nicht hier getroffen)

- **`lego_bundle`, 396 nicht rekonstruierbare Punkte:** belassen / archivieren / als „nicht
  beurteilbar“ kennzeichnen — keine der drei Optionen wurde hier vorentschieden.
- **Dritte Preisstufe „Switch Pro Controller“:** ob überhaupt eingeführt, und falls ja, welche
  Obergrenze (A/B/C oder eine andere) — explizit nicht empfohlen, nur vorbereitet.
- **Zeitpunkt der tatsächlichen Stichproben-Ziehung:** falls das Labeling nicht innerhalb von
  24–48h nach dieser Prüfung stattfindet, muss vorher neu gezogen werden.
- **Ausführung der Migration/Löschung selbst** (Punkte 1–4 der Tabelle oben) — nur vorbereitet,
  nicht ausgeführt.

## Bestätigung

**Es wurden keine produktiven Daten, Regeln oder Preishistorien geändert.** `data/found.json`,
`data/seen.json`, `data/price_history.jsonl` und alle `app/rules/*.yaml`-Dateien sind unverändert
(die einzigen Änderungen im Arbeitsverzeichnis stammen vom weiterlaufenden Live-Scanner, nicht von
dieser Analyse). **Kein Commit, kein Push, kein Merge, kein PR.**
