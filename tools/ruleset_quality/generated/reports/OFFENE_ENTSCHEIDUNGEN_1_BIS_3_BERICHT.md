# Offene Entscheidungen 1–3 klären + Stichprobenplan für Punkt 4

**Erstellt:** 2026-08-14 · **Charakter:** vollständig READ-ONLY. Keine YAML-, Matcher-, Scoring-,
Preis- oder Resale-Logik geändert. Keine `price_history.jsonl`-, `found.json`- oder
`seen.json`-Änderung. Keine historischen Punkte migriert oder gelöscht. Kein Commit, kein Push,
kein Merge, kein PR.

---

## ⚠️ Methoden-Korrektur (zuerst, weil sie Teile des letzten Berichts betrifft)

Bei der Tiefenanalyse von `roehrenfernseher` fiel auf: `duplicate_detection.normalize_title()`
(die Funktion, die den in `price_history.jsonl` gespeicherten `fingerprint` erzeugt) ersetzt
Umlaute (ä/ö/ü/ß) durch ein **Leerzeichen**, nicht durch eine transliterierte Form:

```text
normalize_title("Röhrenfernseher Grundig 51cm") == "r hrenfernseher grundig 51cm"
```

`evaluate(fingerprint, ...)` matcht dadurch **nie** gegen Umlaut-haltige `match`/`require_all_of`-
Begriffe (z. B. `"röhrenfernseher"`, `"verstärker"`) — unabhängig davon, ob der echte Titel
inhaltlich passen würde. Betroffen: **19 von 355 Regeln in 4 Kategorien** (`handhelds`,
`konsolen_bundles`, `retro_konsolen`, `vintage_elektronik`). Zusätzlich zeigte sich am
Switch-Pro-Controller-Fall ein zweiter Effekt: die vorherige Preishistorie-Simulation nutzte
`price=0.0`, wodurch echte `max_price`-Ausschlüsse (z. B. „Switch Pro Controller“ hat aktuell nur
zwei Preisstufen bis max. 35 €) nicht sichtbar wurden.

**Konkrete Auswirkung auf den letzten Bericht
(`FINALE_REVALIDIERUNG_ABSCHLUSSBERICHT.md`, Abschnitt G):**

| Zahl im letzten Bericht | War | Ist (korrigiert, mit echten Titeln) |
|---|---|---|
| `roehrenfernseher`-Samples nach Revalidierung | 96 → **3** valide | 96 Punkte, davon 26 Titel rekonstruierbar, **25/26 (96,2%) valide** |
| „7 kritische UNCLEAR mit Modellwechsel“ | 7 Fälle, 6× → `controller_switch_pro` | Korrekt: **35 UNCLEAR-Fälle insgesamt**, davon **14 verändert/kein Treffer** — die 6 Switch-Pro-Controller-Fälle landen bei ihrem tatsächlichen Preis (39–130 €) aktuell bei **KEIN TREFFER** (Preis über der 35-€-Obergrenze), nicht bei `controller_switch_pro`. Der Xbox-One-S-Bundle-Fall ist **stabil** (keine Änderung), nicht „→ controller“. |
| „148 TP mit price_history_model-Wechsel“ | 148 | Bei direkter Titel-Auswertung (ohne Fingerprint-Umweg): **124** — Größenordnung bestätigt, exakte Zahl war durch den Fingerprint-Fehler verzerrt |

**Wichtig:** Dieser Fingerprint-Fehler betrifft **nicht nur meine eigenen Analyse-Skripte**, sondern
auch das bereits produktive `app/rule_coverage.py::_is_still_valid()`, das denselben
Fingerprint-basierten Ansatz nutzt. Das ist eine reale, bisher unbekannte Einschränkung der
bestehenden Diagnose-Infrastruktur — hier nur dokumentiert (kein Code geändert, siehe Auftrag).
Alle Ergebnisse in diesem Bericht nutzen ausschließlich **echte Titel** (aus dem Ground-Truth-
Label-Store, der bereits Klartext-Titel speichert) statt Fingerprints.

Skript: `tools/ruleset_quality/decision_points_1_3.py`,
Rohdaten: `generated/reports/decision_points_1_3.json`.

---

## 1. `roehrenfernseher` — vollständige Untersuchung

```text
Anzahl historischer Preispunkte: 96
Zeitraum:                        2026-08-03 bis 2026-08-14 (durchgehend bis heute!)
Median:                          20,00 €
Min / Max:                       1,00 € / 45,00 €
Quartile (25/75):                10,00 € / 29,75 €
Distinkte Listings (Fingerprints): 92
Aktuell live matchende Einträge (found.json, heute): 12
```

**Aktuelle Kategorie-/Regelzuordnung:** Kategorie `vintage_elektronik`, drei Preisstufen-Regeln
(„Röhrenfernseher ★ Top-Deal“ ≤10 €, „👍 Guter Preis“ ≤25 €, „⚠️ Okay“ ≤45 €), alle mit
`price_history_model: roehrenfernseher`. Match-Begriffe: `röhrenfernseher`, `crt fernseher`,
`röhren tv`. Rege gepflegte Exclude-Liste (Ersatzteile/Fernbedienungen/Sammlerfotos, aus dem
Active-FP-Audit).

**Wird das Modell noch durch echte Listings gespeist?** Ja, eindeutig — Datenpunkte bis zum
heutigen Tag, 12 aktuell live matchende Angebote im laufenden Scan.

**Fachlich eindeutig zu `roehrenfernseher` gehörig?** Von 26 mit Klartext-Titel rekonstruierbaren
Punkten sind **25 (96,2%)** bei Neubewertung weiterhin `vintage_elektronik/roehrenfernseher`. Der
einzige Ausreißer: „Frau mit Zigarette neben Röhrenfernseher – Altes Foto 1950er“ (8,90 €) — korrekt
durch den bereits vorhandenen `"foto"`-Exclude blockiert (Sammlerfoto, kein Gerät). Ein Grenzfall
wurde zusätzlich beobachtet: „TV-Zubehör Blenden für LOEWE Röhrenfernseher 80 cm Bildschirmbreite“
(9 €) matcht aktuell noch (könnte streng genommen ein Zubehörteil statt Komplettgerät sein) —
geringe Praxisrelevanz, als Beobachtung vermerkt, keine Regeländerung vorgeschlagen.

**Verwandte Kategorie als theoretische Alternative:** `crt_profi_monitor` (Sony PVM/BVM/Trinitron),
**dieselbe Kategorie** `vintage_elektronik`, aber bewusst getrenntes Preissegment:

```text
                    n     Median    Min     Max
roehrenfernseher    96    20,00 €   1,00 €  45,00 €
crt_profi_monitor   86    99,50 €   1,00 €  250,00 €
```

Kein struktureller Cross-Category-Konflikt zwischen beiden (bereits in der letzten Session per
kategoriegefiltertem `evaluate()` geprüft, 0 Überschneidungen für `vintage_elektronik`).

### Bewertung der drei Optionen

**A — Eigenständiges Modell behalten**
- Vorteile: Median-Preis (20 €) und Preisspanne unterscheiden sich fast 5-fach von
  `crt_profi_monitor` (99,50 €) — die YAML selbst begründet die Trennung ausdrücklich fachlich
  (Massenware/Entsorgungsware vs. gesuchte Profi-Broadcast-Monitore). Aktive, gesunde Datenlage
  (96,2% Validität, tägliche Neuzugänge).
- Nachteile: keine wesentlichen.
- Datenrisiko: minimal — Modell ist aktuell gesund.
- Einfluss Marktpreis/Resale: keiner (Status quo).

**B — Mit `crt_profi_monitor` zusammenführen**
- Vorteile: keine erkennbaren (beide Modelle sind bereits einzeln gut befüllt, keine
  Datenknappheit, die eine Zusammenführung rechtfertigen würde).
- Nachteile: würde zwei fachlich verschiedene Preisklassen vermengen — der Median würde auf
  irgendeinen Wert zwischen 20 € und 99,50 € springen und wäre für **beide** ursprünglichen
  Gruppen falsch.
- Datenrisiko: hoch — 96 gesunde `roehrenfernseher`-Punkte und 86 gesunde `crt_profi_monitor`-
  Punkte würden gemeinsam ein Preismodell ergeben, das für keine der beiden realen Warengruppen
  eine sinnvolle Schätzung liefert.
- Einfluss Marktpreis: stark negativ — voraussichtlich systematisch falsche Markt-/Resale-Preise
  für beide Gerätetypen.

**C — Modell stilllegen/löschen**
- Nicht sachlich begründbar: Modell ist aktiv, gesund, aktuell befüllt. Stilllegung würde
  funktionierende, produktiv genutzte Preisdaten ohne fachlichen Anlass entsorgen.

### Empfehlung

**Option A — eigenständiges Modell behalten.** Keine Zusammenführung, keine Stilllegung. Die
Vorab-Sorge aus dem letzten Bericht („96 → 3 valide Punkte“) war ein Methodik-Artefakt (siehe
Korrektur oben), keine reale Datenqualitätslücke. Einzige Detailbeobachtung (kein Handlungsbedarf,
nur dokumentiert): der „Blenden für …“-Grenzfall könnte bei Gelegenheit zusammen mit anderen
Zubehör-Excludes für `vintage_elektronik` überprüft werden — nicht dringend, 1 von 26 Fällen.

---

## 2. Die 3 Orphan-Modelle aus `spielzeug_bundles`

**Kontext (verifiziert per `git log`):** `spielzeug_bundles.yaml` wurde am 2026-08-08 (Commit
`ac09d06`) entfernt und **ausdrücklich durch `lego_minifiguren.yaml` ersetzt** (Commit-Message:
„rules/spielzeug_bundles.yaml -> rules/lego_minifiguren.yaml“) — aber die Nachfolge-Kategorie ist
**bewusst enger**: nur noch LEGO-**Minifiguren**-Sammlerwert, kein generisches Lego-Kilo-Konvolut,
kein Playmobil, kein generisches „Spielzeug“ mehr.

### 2.1 `lego_bundle` (404 Punkte)

```text
Zeitraum:       2026-08-03 (ein einzelner Tag — Altbestand, kein laufender Zufluss)
Median/Min/Max: 35,00 € / 1,00 € / 150,00 €
Distinkte Fingerprints: 388
Alte Kategorie: spielzeug_bundles
```

Titel rekonstruierbar: 8/404 (2,0% — sehr dünn, da alt und aus `found.json`/Forensik-Snapshot
inzwischen herausrotiert). Von diesen 8:

```text
5/8 matchen aktuell etwas Sinnvolles:
  "LEGO Minifiguren Konvolut" (59€, 40€)              -> lego_minifiguren/lego_minifig_bundle
  "Lego Ninjago 8 besondere Minifiguren, Sammlung" (13€) -> lego_minifiguren/lego_ninjago_bundle
  "LEGO Ninjago Minifiguren Sammlung" (1€)             -> lego_minifiguren/lego_ninjago_bundle
  "Lego Star Wars General Grievous ... mit Minifig" (60€) -> lego_minifiguren/lego_minifig_bundle

3/8 matchen NICHTS mehr:
  "LEGO Figuren Sammlung" (75€)                — über der 60€-Obergrenze von lego_minifig_bundle
  "Lego star wars minifiguren Konvolut" (75€)  — dito
  "LEGO Star Wars Figuren Konvolut" (95€)      — dito, zusätzlich fehlt ein Sammler-Signalwort
                                                  ("rar/selten/sammler/...") für die generische
                                                  Sammler-Regel
```

**Mögliches Zielmodell:** `lego_minifig_bundle` bzw. themenspezifisch `lego_ninjago_bundle` für
Minifiguren-**spezifische** Bundles — aber **nur für den Teil der alten `lego_bundle`-Population,
der tatsächlich Minifiguren-Sammelwert bewirbt**. Generische Kilo-/Konvolut-Ware ohne
Minifiguren-Framing (die die alte Kategorie ausdrücklich auch abdeckte, siehe historischer
YAML-Kommentar „Diese Kategorie zielt explizit auf BUNDLES/KILOWARE/SAMMLUNGEN ab“) hat **keinen**
sauberen Nachfolger mehr.

### 2.2 `playmobil_bundle` (210 Punkte)

```text
Zeitraum: 2026-08-03 (ein einzelner Tag)
Median/Min/Max: 29,16 € / 1,00 € / 100,00 €
Alte Kategorie: spielzeug_bundles
Titel rekonstruierbar: 0/210
```

**Strukturell verifiziert** (nicht nur Rekonstruktions-Limit): `grep -ril "playmobil" app/rules/*.yaml`
→ **0 Treffer**. Keine der 19 aktiven Kategorien enthält irgendeinen Playmobil-Match-Begriff.
**Mögliches Zielmodell: keins — echter, vollständiger Orphan ohne Nachfolgekategorie.**

### 2.3 `spielzeug_bundle_sonstige` (49 Punkte)

```text
Zeitraum: 2026-08-03 (ein einzelner Tag)
Median/Min/Max: 20,00 € / 2,50 € / 90,00 €
Alte Kategorie: spielzeug_bundles
Titel rekonstruierbar: 0/49
```

Ebenfalls strukturell verifiziert: kein aktives Regelwerk matcht generisches `"spielzeug"` mehr.
**Mögliches Zielmodell: keins — echter, vollständiger Orphan.**

### Empfehlung Punkt 2

Alle drei Modelle sind seit **mindestens 11 Tagen** (letzter Datenpunkt 2026-08-03, heute
2026-08-14) ohne jeden neuen Zufluss — technisch tot, nicht nur „datenarm“. Für `playmobil_bundle`
und `spielzeug_bundle_sonstige` gibt es **keine** fachlich passende Zielkategorie im aktuellen
Regelwerk — eine Migration wäre nicht möglich, ohne neue Regeln zu schreiben (außerhalb des
Auftrags). Für `lego_bundle` existiert ein **partieller** Nachfolger (`lego_minifig_bundle`/
`lego_ninjago_bundle`), aber nur für den minifiguren-spezifischen Teil.

**Konkret (nur Empfehlung, keine Umsetzung):** Diese 663 Punkte sind laut STATUS.md ohnehin bereits
als „nicht ohne separaten Auftrag löschen“ markiert — diese Analyse bestätigt, dass eine
**automatische** Migration fachlich nicht sauber möglich ist (Playmobil/Spielzeug: kein Ziel;
LEGO-Bundle: nur Teilmenge passt). Eine etwaige spätere Entscheidung (archivieren/löschen/
gesondert kennzeichnen) bleibt ausdrücklich der separaten Freigabe vorbehalten, die STATUS.md
bereits verlangt.

---

## 3. Die UNCLEAR Controller-/Konsolen-Fälle (korrigiert: 35 gesamt, nicht 7)

Mit der korrigierten Methodik (echte Titel statt Fingerprints) wurden **alle 35** UNCLEAR-gelabelten
Fälle direkt neu ausgewertet (nicht nur die zufällige Schnittmenge mit `price_history.jsonl`, die
den ursprünglichen „7“-Befund erzeugt hatte):

```text
Stabil (Kategorie + price_history_model unverändert): 21
Verändert / kein Treffer mehr:                        14
```

### Die 14 veränderten Fälle im Detail

| Titel | Alt: Kategorie/Modell | Neu (bei price=0, d.h. rein inhaltlich) |
|---|---|---|
| Nintendo Switch 2 GameCube Controller \| OVP \| NEU | konsolen_bundles/konsole_switch_standard | **KEIN TREFFER** |
| Nintendo Switch 2 GameCube Controller – Nintendo Classics – OVP – NEU | dito | **KEIN TREFFER** |
| Nintendo Switch - Minecraft FRA mit OVP | dito | **KEIN TREFFER** |
| Pokémon Let's Go Evoli! Nintendo Switch – OVP komplett | dito | **KEIN TREFFER** |
| Nintendo Switch - Controller Joy-Con Neon-Grün/Neon-Pink 2er - NEU OVP | dito | **KEIN TREFFER** |
| Bayonetta & Vanquish 10th Anniversary Bundle - PlayStation 4 - Neu & OVP | konsole_ps4_bundle | **KEIN TREFFER** |
| Xbox One S 1 TB + 1 Controller - Weiß - OVP - Top Zustand | konsole_xbox_one | **stabil laut Inhalt** (bei echtem Preis 80€ ebenfalls stabil, siehe unten) |
| 2x Nintendo Switch 2 Pro Controller NEU OVP (130€) | konsole_switch_standard | inhaltlich `controller/controller_switch_pro`, **bei echtem Preis: KEIN TREFFER** (>35€-Obergrenze) |
| Nintendo Switch Pro Controller - Schwarz mit OVP (39€) | dito | dito |
| Nintendo Switch Pro Controller in OVP (50€) | dito | dito |
| Nintendo Switch Pro Controller, TOP Zustand mit OVP | dito | dito |
| NEU - OVP! ... Monster Hunter Rise Sunbreak Edition (75€) | dito | dito |
| Nintendo Switch Pro Controller Original \| OVP \| TOP Zustand (39,99€) | dito | dito |
| Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP (79,99€) | dito | dito |

**Korrektur des Xbox-Falls:** Bei Neubewertung mit dem echten Titel **und** dem echten Preis (80 €)
bleibt „Xbox One S 1 TB + 1 Controller“ stabil bei `konsolen_bundles/konsole_xbox_one` — der im
letzten Bericht behauptete Wechsel zu `controller/controller_xbox_series` war ein reiner
Fingerprint-Artefakt. **Kein Handlungsbedarf für diesen Fall.**

**Neuer, konkreter Strukturbefund für die 6 Switch-Pro-Controller-Fälle:** Die Regel „Switch Pro
Controller“ (`app/rules/controller.yaml`) hat — anders als fast alle anderen Regelfamilien im
Projekt — **nur zwei** Preisstufen (★ Top-Deal ≤25 €, 👍 Guter Preis ≤35 €), **keine** „⚠️ Okay“-
Stufe. Jeder Switch-Pro-Controller über 35 € fällt aktuell komplett durchs Raster (weder als
Controller noch als Konsole erfasst). Das erklärt sowohl die 6 hier untersuchten UNCLEAR-Fälle als
auch strukturell, warum sie ursprünglich (mangels Alternative) über das schwache `"ovp"`-Signal
in `konsolen_bundles` gelandet waren. **Reine Beobachtung, keine Regeländerung vorgeschlagen**
(Auftrag: keine Regeln optimieren).

Die übrigen 7 Fälle (GameCube-Controller-Bundles, Joy-Con-2er-Set, Minecraft-Switch-Bundle,
Pokémon-Bundle, PS4-Bundle) matchen mit dem korrigierten, echten Titel **gar nichts mehr** —
das sind exakt die Art von Spieltitel-vor-Plattform- bzw. Zubehör-vor-Plattform-Fällen, die
`docs/KONSOLEN_BUNDLES_OVP_ANALYSE.md` bereits als strukturelle Restlücke dokumentiert (kein
kollisionsfreies Muster ohne Spieltitel-Datenbank identifiziert).

### Empfehlung Punkt 3

Keiner der 14 Fälle erfordert eine dringende Preishistorie-Entscheidung: 7 matchen inhaltlich gar
nichts mehr (ihre historischen Punkte sind für eine Revalidierung ohnehin „nicht mehr gültig“,
unabhängig von der UNCLEAR-Einstufung), 6 sind reine Preisschwellen-Randfälle bei einer strukturell
bekannten Regelwerkslücke (fehlende dritte Preisstufe), 1 ist stabil. **Kein Blocker für die
Preishistorien-Revalidierung** — die 6 Preisschwellen-Fälle sollten aber als Kontext mitgegeben
werden, falls im Rahmen der Revalidierung auch über eine (separat zu beauftragende) dritte
Preisstufe für „Switch Pro Controller“ nachgedacht wird.

---

## 4. Stichprobenplan (konkret, aber NICHT ausgeführt — keine Labels vergeben)

**Ziel:** eine frische, repräsentative, schnell erhebbare Ground-Truth-Stichprobe, die die auf
0,6% eingebrochene Abdeckung des Live-Korpus ersetzt (siehe letzter Bericht).

**Methodik** (`tools/ruleset_quality/sampling_plan.py`):

1. **Schichtung nach Kategorie:** je Kategorie bis zu 15 Listings (kleine Kategorien wie
   `cpu_mainboard_bundle`/`m2_ssd` vollständig, da sie aktuell ohnehin nur 1-3 Einträge haben).
2. **Schichtung nach Preisstufe innerhalb der Kategorie:** gleichmäßig über Top-Deal/Guter
   Preis/Okay verteilt — Preisschwellen sind laut dieser Analyse (Röhrenfernseher, Switch-Pro-
   Controller) ein Hotspot für Randfälle.
3. **Deterministischer Seed** für Reproduzierbarkeit des Plans selbst; die tatsächliche Ziehung
   sollte aber **unmittelbar vor** der Labeling-Sitzung frisch erfolgen (Korpus rotiert schnell,
   siehe unten).

**Ergebnis dieses Laufs (bereits als Vorlage erzeugt, KEINE Labels ausgefüllt):**

```text
Stichprobengröße gesamt: 251 Listings über 19 Kategorien
Datei: generated/reports/sampling_worksheet_template.csv
Spalten: url, title, price, category, rule, deal_rating,
         verdict_TP_FP_UNCLEAR (leer), root_cause (leer), reason (leer)
```

**Labeling-Prozess (Vorschlag):**
- Manuelle Durchsicht durch dich (oder eine von dir beauftragte Person), gleiche Kriterien wie im
  ursprünglichen Forensik-Snapshot (TRUE_POSITIVE/FALSE_POSITIVE/UNCLEAR + kurze Begründung).
- Ergebnis wird als **neue, separate Quelle** im Ground-Truth-Label-Store abgelegt (nicht die
  alte Forensik-Quelle überschreiben) — mit eigenem `source`/`source_date`, damit Alter und
  Herkunft jedes Labels jederzeit nachvollziehbar bleiben.

**Zeitliche Empfehlung (zentral):** Zwischen Ziehung und Labeling sollten **nicht mehr als 24-48h**
liegen — die Abdeckungs-Zerfallsrate aus dem letzten Bericht (19,2% → 0,6% in 3 Tagen) zeigt, dass
ältere Stichproben schnell wieder aus dem Live-Korpus herausrotieren. Die Preishistorie-Revalidierung
selbst sollte **zeitnah nach** dem Labeling stattfinden, nicht Tage später.

**Methodik-Hinweis für die spätere Auswertung:** Jede künftige automatisierte Re-Validierung dieser
neuen Labels muss den **echten Titel** verwenden, nicht `PricePoint.fingerprint` (siehe Korrektur-
Abschnitt oben) — sonst wiederholt sich der hier gefundene Fehler.

---

## Zusammenfassung der Empfehlungen

```text
1. roehrenfernseher:        Option A (eigenständig behalten). Vorheriger "3/96"-Alarm war ein
                             Methodik-Artefakt, real 25/26 (96,2%) valide.
2. Orphan-Modelle:           lego_bundle teilmigrierbar (nur Minifiguren-Teilmenge), playmobil_
                             bundle + spielzeug_bundle_sonstige strukturell ohne Nachfolger.
                             Keine automatische Migration möglich -- Freigabe-Entscheidung bleibt
                             bei dir (STATUS.md-Vorgabe unverändert).
3. UNCLEAR-Fälle:            35 gesamt (nicht 7), 14 verändert -- keiner davon ein Blocker für die
                             Revalidierung. Strukturbefund: "Switch Pro Controller" fehlt eine
                             dritte Preisstufe (>35€) -- nur dokumentiert, nicht behoben.
4. Stichprobenplan:          251-Listing-Worksheet über alle 19 Kategorien erzeugt, bereit zum
                             Ausfüllen. Noch NICHT gelabelt.
```

**STOPP. Warte auf deine Freigabe.**
