# Phase 15 – Rule Coverage Report

**Stand:** 2026-08-09 · **Status:** Analyse abgeschlossen (Phase 15, Schritt 5). Nur lesend gegen `price_history.jsonl` — keine Daten gelöscht/verändert, keine YAML-Datei angefasst.

Erstellt mit `app/rule_coverage.py` (Phase 15, Schritt 5). Datenquelle
ausschließlich `data/price_history.jsonl` (9.753 Datenpunkte,
2026-07-25 bis 2026-08-09), rein lesend.

---

## 1. Methodik

Für jede (Kategorie, `price_history_model`)-Gruppe — sowohl aus dem
aktuellen Regelwerk als auch aus den Daten — werden fünf Kennzahlen
ermittelt:

- **matches**: Rohanzahl der Datenpunkte mit diesem Modell.
- **sample_count**: Teilmenge von `matches` mit vorhandenem `fingerprint`
  (normalisierter Titel, siehe `duplicate_detection.py::normalize_title()`)
  — nur diese Teilmenge ist überhaupt gegen die aktuellen Regeln
  re-validierbar. Ältere Datenpunkte ohne `fingerprint` zählen NICHT als
  Fehltreffer, sondern als **unverifizierbar** (`matches − sample_count`).
- **valid**: `sample_count`-Punkte, die bei erneuter Auswertung
  (`matcher.evaluate()`, Preis bewusst auf 0,0 gesetzt — siehe Kasten
  unten) weiterhin derselben Kategorie **und** demselben
  `price_history_model` zugeordnet werden.
- **false-positive indicators**: `sample_count − valid`.
- **last_seen**: jüngstes Datum unter allen Datenpunkten dieses Modells.

> **Wichtige methodische Entscheidung:** Die Re-Validierung nutzt
> `evaluate(fingerprint, 0.0, rules_cfg)` — mit Preis **0,0**, nicht dem
> historischen Preis. Grund: Diese Analyse soll ausschließlich prüfen, ob
> die **Titel-/Kategoriezuordnung** noch stimmt (Matcher-Qualität,
> Auftrag Abschnitt 34), nicht ob der historische Preis eine
> zwischenzeitlich verschärfte `max_price`-Schwelle noch unterschreitet
> (Phase 15 ist ausdrücklich **keine** Preiskalibrierungsphase, Abschnitt
> 2.3). Keine Regel im Projekt nutzt eine Mindestpreis-Schwelle
> (verifiziert), daher ist dieser Kunstgriff risikofrei. Eine erste
> Version mit dem historischen Preis hätte 135 zusätzliche Punkte
> fälschlich als Matcher-Fehler gezählt, die tatsächlich nur an einer
> späteren, legitimen Preisgrenzen-Verschärfung (Phase 12, Schritt 5)
> lagen.

---

## 2. Lauf-Ergebnis (Übersicht)

```
Modelle im aktuellen Regelwerk:     135
  davon mit Daten:                  113
  davon ohne jegliche Daten:         22
Modelle nur in den Daten (Orphans):   3

Summe matches (aktive Modelle):   9.090
Summe sample_count (verifizierbar): 7.917
Summe valid:                        6.555
Summe false-positive indicators:    1.362  (17,2 % der verifizierbaren Stichprobe)
```

---

## 3. Top 15 produktivste Regeln

| price_history_model | Kategorie | matches | valid | last_seen |
|---|---|---:|---:|---|
| monitor_curved | monitor_curved | 679 | 673 | 2026-08-09 |
| sony_retro_konsole | retro_konsolen | 566 | 348 | 2026-08-09 |
| nintendo_retro_konsole | retro_konsolen | 564 | 326 | 2026-08-09 |
| lego_ninjago_bundle | lego_minifiguren | 541 | 137 | 2026-08-09 |
| gaming_pc | gaming_pc | 535 | 121 | 2026-08-09 |
| lego_sw_clone | lego_minifiguren | 441 | 404 | 2026-08-09 |
| vintage_hifi_verstaerker | vintage_elektronik | 341 | 209 | 2026-08-09 |
| iphone_11_128gb | iphone | 306 | 306 | 2026-08-09 |
| rtx_3060_12gb | gpu | 263 | 104 | 2026-08-09 |
| iphone_13_128gb | iphone | 242 | 242 | 2026-08-09 |
| office_pc | office_pc | 239 | 121 | 2026-08-09 |
| iphone_12_128gb | iphone | 209 | 209 | 2026-08-09 |
| lego_cmf | lego_minifiguren | 184 | 184 | 2026-08-09 |
| iphone_15_128gb | iphone | 155 | 155 | 2026-08-09 |
| macbook_pro_intel_512gb | macbook | 151 | 151 | 2026-08-09 |

**Wichtiger Hinweis gegen Fehlinterpretation:** `valid` ≠ `matches` bedeutet
NICHT automatisch ein Matching-Problem. Beispiel `gaming_pc` (535 matches,
121 valid): `sample_count` ist nur 121 — **alle 414 fehlenden Punkte sind
unverifizierbar** (kein `fingerprint`, sehr frühe Scan-Daten vor Einführung
dieses Felds), **0 davon sind tatsächliche False-Positive-Indikatoren**.
Gleiches Bild bei `rtx_3060_12gb` (263 matches, 104 sample_count, 104
valid, 0 Fehltreffer). Bei diesen beiden Regeln ist die Datenqualität also
tatsächlich **einwandfrei** — nur die Stichprobe für eine Aussage ist
kleiner als die Rohanzahl vermuten lässt.

---

## 4. Regeln ohne jegliche Daten (22)

```
autoradio_opel_corsa  autoradio_corsa_d_asure
autoradio_opel_corsa  autoradio_corsa_d_eonon
autoradio_opel_corsa  autoradio_corsa_d_joying
autoradio_opel_corsa  autoradio_corsa_d_junsun
autoradio_opel_corsa  autoradio_corsa_d_xtrons
controller            controller_ps5_drift
cpu_mainboard_bundle  cpu_bundle_i5_12400f_b660
cpu_mainboard_bundle  cpu_bundle_ryzen3600_b450
iphone                iphone_11_512gb
iphone                iphone_12_512gb
iphone                iphone_12_mini_512gb
iphone                iphone_14_plus_512gb
iphone                iphone_15_512gb
iphone                iphone_16_plus_512gb
lego_minifiguren      lego_fantasy_rare
lego_minifiguren      lego_superhero_rare
m2_ssd                m2_ssd_2tb
macbook                macbook_air_m2_1tb
macbook                macbook_air_m4_1tb
macbook                macbook_pro_m2_1tb
macbook                macbook_pro_m3_1tb
gpu                    rx_7600
```

Einordnung: größtenteils plausibel selten (512GB/1TB/2TB-Top-Ausstattungen,
Nischen-Autoradio-Modelle, `cpu_bundle_*` waren laut
PHASE13_VALIDATION_REPORT.md bereits als strukturell selten dokumentiert).
**`gpu / rx_7600` ist die auffällige Ausnahme — siehe Abschnitt 6.**

---

## 5. Orphans: Daten ohne aktuelle Regel (3)

```
lego_bundle                category=spielzeug_bundles  matches=404  last_seen=2026-08-03
playmobil_bundle           category=spielzeug_bundles  matches=210  last_seen=2026-08-03
spielzeug_bundle_sonstige  category=spielzeug_bundles  matches=49   last_seen=2026-08-03
```

Die Kategorie `spielzeug_bundles` existiert in `app/rules/` nicht mehr
(kein `spielzeug_bundles.yaml`) — vermutlich Vorläufer der heutigen
`lego_minifiguren`-Kategorie (`lego_minifig_bundle`/`lego_ninjago_bundle`).
663 Datenpunkte (6,8 % der Gesamtdaten) lassen sich keiner aktuellen Regel
mehr zuordnen. Reine Beobachtung — `price_history.jsonl` bleibt gemäß
Auftrag unangetastet, keine Bereinigung in diesem Schritt.

---

## 6. Bestätigter Fund: `rx_7600` vs. `rx_7600_xt` (Verbindung zu Schritt 3)

Der Rule Analyzer (Schritt 3, `PHASE15_RULE_ANALYSIS_REPORT.md`) meldete
als INFO, dass die Regel „RX 7600 XT“ den Begriff `"rx 7600"` als eigenen
`match`-Begriff führt und vor den `RX 7600`-Regeln steht — eine
*theoretische* Überschneidung. Die Coverage-Analyse bestätigt das jetzt
**mit einem echten Produktivdatenpunkt**:

```
price: 180.0€
fingerprint: "amd radeon msi rx 7600 mech 2x classic 8g oc ovp"
gespeichert als: rx_7600_xt   (Kategorie gpu)
```

Der Titel („MSI RX 7600 MECH 2X Classic 8G OC“) nennt nirgends „XT“ — es
handelt sich um eine reguläre (Nicht-XT) RX 7600 8GB, die durch den
generischen `"rx 7600"`-Begriff in der früher iterierten
`RX 7600 XT`-Regel abgefangen wurde. Das erklärt zugleich, warum
`gpu / rx_7600` in Abschnitt 4 **0 Datenpunkte** zeigt — Titel, die
eigentlich zu `rx_7600` gehören, landen strukturell bevorzugt bei
`rx_7600_xt`.

**Keine YAML-Änderung in diesem Schritt** — das wäre STOP 3 des
Auftrags (separate Freigabe nötig). Empfehlung bleibt wie in Schritt 3
dokumentiert: `"rx 7600"` als eigenständigen `match`-Begriff aus der
`RX 7600 XT`-Regel entfernen (die spezifischeren Begriffe `"7600 xt"`/
`"7600xt"` reichen zur Erkennung aus).

---

## 7. Einordnung der False-Positive-Indikatoren (17,2 % Gesamtrate)

Die höchsten False-Positive-Raten unter den aktiven Regeln:

| model | Kategorie | matches | sample | valid | fp | fp-Rate |
|---|---|---:|---:|---:|---:|---:|
| roehrenfernseher | vintage_elektronik | 71 | 71 | 4 | 67 | 94,4 % |
| lego_sw_rare | lego_minifiguren | 107 | 107 | 17 | 90 | 84,1 % |
| lego_ninjago_rare | lego_minifiguren | 6 | 6 | 1 | 5 | 83,3 % |
| lego_ninjago_bundle | lego_minifiguren | 541 | 541 | 137 | 404 | 74,7 % |
| retro_konvolut | retro_konsolen | 33 | 33 | 15 | 18 | 54,5 % |
| ram_ddr4_32gb | ram | 16 | 16 | 8 | 8 | 50,0 % |
| nintendo_retro_konsole | retro_konsolen | 564 | 564 | 326 | 238 | 42,2 % |
| gaming_laptop_rtx3060 | notebook_resell | 18 | 18 | 10 | 8 | 44,4 % |
| vintage_hifi_verstaerker | vintage_elektronik | 341 | 341 | 209 | 132 | 38,7 % |
| sony_retro_konsole | retro_konsolen | 566 | 566 | 348 | 218 | 38,5 % |
| thinkpad_modern | notebook_resell | 121 | 121 | 82 | 39 | 32,2 % |

**Wichtigste Einordnung:** Fast alle betroffenen Regelgruppen
(`retro_konsolen`, `lego_sw_rare`/`lego_sw_clone`, `vintage_elektronik`)
wurden laut Git-Historie **am selben Tag wie dieser Report** (2026-08-09,
Commits `fe5f605`/`1a664a4`/`9daadab`, "Phase 12, Schritt 3/4") strukturell
verschärft — u.a. genau wegen bereits dokumentierter Fehltreffer-Probleme
(die `retro_konsolen.yaml`-Kommentare selbst nennen 72 % Fehltreffer vor
dem Fix). Da `price_history.jsonl` den gesamten Zeitraum seit 2026-07-25
abdeckt, stammt ein erheblicher Teil der jetzt als „nicht mehr valide“
markierten Datenpunkte plausibel aus der Zeit **vor** diesen Fixes — die
hohen Raten sind größtenteils die erwartete, bereits an anderer Stelle
dokumentierte Altlast, kein neu entdeckter, aktiver Matcher-Bug. Eine
exakte Vorher/Nachher-Trennung ist anhand der Zeitstempel allein nicht
sauber möglich (Datenpunkt-Zeitstempel und Commit-Zeitstempel des
Regelwerks fallen in diesem Repository auf denselben Tag) — das ist eine
Grenze dieser Analyse, keine gesicherte Entwarnung. Empfehlung: die
False-Positive-Rate dieser Modelle in ein bis zwei Wochen erneut mit
diesem Tool prüfen; sie sollte spürbar sinken, sobald ausschließlich
Post-Fix-Daten in `price_history.jsonl` überwiegen.

Einzige Ausnahme mit einem konkret nachgewiesenen, aktiven Ursachenpfad:
`rx_7600`/`rx_7600_xt` (Abschnitt 6) — dort ist die Struktur der Regel
selbst (nicht ein zeitlich abgeschlossener Fix) die Ursache.

---

## 8. Rule Quality (Abschnitt 18) — NUR EIN VORSCHLAG

`app/rule_coverage.py::compute_rule_quality()` implementiert die im
Auftrag beispielhaft genannte Gewichtung als **Vorschlag**, ausdrücklich
**keine** Erweiterung von `scoring/deal_score.py` und **keine** endgültige
Bewertung:

```
Match volume        30 %  (min(1, matches / 15))
False-positive rate  30 %  (1 - fp_rate; 0.5 neutral bei sample_count=0)
Data freshness       15 %  (linear abfallend, 0 nach 90 Tagen ohne neuen Treffer)
Price confidence     15 %  (price_stats.py::_confidence(), wiederverwendet)
Rule stability        10 %  (Platzhalter-Proxy = false-positive-Score,
                              siehe Modul-Docstring fuer die Einschraenkung)
```

Beispielwerte:

| model | overall | volume | fp | freshness | price_conf |
|---|---:|---:|---:|---:|---|
| monitor_curved | 1,00 | 1,00 | 0,99 | 1,00 | HIGH |
| gaming_pc | 1,00 | 1,00 | 1,00 | 1,00 | HIGH |
| sony_retro_konsole | 0,85 | 1,00 | 0,61 | 1,00 | HIGH |
| nintendo_retro_konsole | 0,83 | 1,00 | 0,58 | 1,00 | HIGH |
| lego_ninjago_bundle | 0,70 | 1,00 | 0,25 | 1,00 | HIGH |
| roehrenfernseher | 0,62 | 1,00 | 0,06 | 1,00 | HIGH |
| lego_ninjago_rare | 0,43 | 0,40 | 0,17 | 1,00 | MEDIUM |
| rx_7600 | 0,23 | 0,00 | 0,50 | 0,00 | LOW |

`rx_7600` (0 Datenpunkte, siehe Abschnitt 6) landet erwartungsgemäß ganz
unten — konsistent mit dem strukturellen Befund, nicht mit fehlender
Marktnachfrage.

---

## 9. Nicht Teil dieses Schritts

- Keine YAML-Änderung (auch nicht für den bestätigten `rx_7600`/
  `rx_7600_xt`-Fund — STOP 3, separate Freigabe erforderlich).
- Keine Bereinigung/Löschung der 3 Orphan-Modelle oder von
  `price_history.jsonl` allgemein.
- Keine Anbindung von `compute_rule_quality()` an `scoring/deal_score.py`
  oder das Dashboard — reine Diagnosefunktion, Vorschlag laut Auftrag.

---

## Testanzahl und Ergebnis

`pytest app/tests/` → **958 passed, 0 failed** (946 vor Schritt 5 + 12
neue `test_rule_coverage.py`-Tests). Keine bestehende Datei verändert,
keine YAML-Datei angefasst, `price_history.jsonl`/`found.json`/
`seen.json` ausschließlich lesend verwendet.
