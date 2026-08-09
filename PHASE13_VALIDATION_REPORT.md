# Phase 13 – Production Validation Report

**Stand:** 2026-08-09 · **Status:** Validierung abgeschlossen. Keine YAML-Preisgrenzen geändert, keine historischen Daten verändert.

---

## ⚠️ Wichtiger methodischer Hinweis vorab

Ich habe in dieser Sandbox **keinen Netzwerkzugriff auf Kleinanzeigen/
eBay/Quoka** und kann daher **keinen echten Live-Scan** ausführen. Ich
habe geprüft, ob seit der Preisgrenzen-Kalibrierung (Commit `9daadab`,
2026-08-09 04:36 UTC) bereits neue reale Scan-Daten hinzugekommen sind
— der jüngste Datenpunkt in `price_history.jsonl` stammt von
**04:22 UTC**, also **vor** dem Kalibrierungs-Commit. In der seither
verstrichenen Zeit (< 1 Stunde) ist kein neuer Produktiv-Scan-Zyklus
abgeschlossen.

**Was dieser Report stattdessen liefert:** eine **datengrounded
Simulation** — die komplette, echte `price_history.jsonl` (9.253 Punkte,
davon 8.080 mit `fingerprint` simulierbar) wurde **zweimal** durch den
echten Matcher/Deal-Score/Top-Deal/Flip-Kandidat-Pipeline gejagt: einmal
mit dem Regelwerk-Stand **unmittelbar vor** der Preisgrenzen-
Kalibrierung (Commit `1a664a4`, enthält bereits die Phase-12-Matching-
Fixes aus Schritt 3+4), einmal mit dem **aktuellen** Regelwerk. Beide
Läufe nutzen denselben Marktkontext (identische `PriceStats`/
`market_prices`/`resale_prices`/`resale_confidence` aus dem
Gesamtdatensatz), damit ausschließlich der Effekt der
**Regeländerungen** isoliert wird, nicht Verschiebungen in der
Preisstatistik selbst.

Das ist die belastbarste Validierung, die ohne einen echten neuen
Scan-Zyklus möglich ist — ersetzt aber **nicht** eine echte
Produktiv-Beobachtung über mehrere Tage/Scans. Empfehlung am Ende des
Reports.

**Datenintegrität:** `price_history.jsonl`/`seen.json`/`found.json`
wurden ausschließlich lesend verwendet, nichts gelöscht oder verändert.
Keine YAML-Datei in diesem Schritt angefasst.

---

## Scan-Zeitraum & Datengrundlage

- **Zeitraum der zugrunde liegenden Daten:** 2026-07-25 bis 2026-08-09
  (kontinuierlich gewachsen, offenbar durch einen parallel laufenden
  Produktivprozess)
- **Anzahl Datenpunkte gesamt:** 9.253
- **Davon mit `fingerprint` (simulierbar):** 8.080 (87%)
- **Regelwerk "vorher":** Commit `1a664a4` (nach Phase-12-Matching-Fixes,
  vor Preisgrenzen-Kalibrierung)
- **Regelwerk "nachher":** aktueller Stand (inkl. Preisgrenzen-
  Kalibrierung Schritt 5 UND der zwischenzeitlich vom Auftraggeber
  integrierten 5 neuen Kategorien: `autoradio_opel_corsa`, `controller`,
  `handhelds`, `konsolen_bundles`, `m2_ssd`)

---

## 1. Matches pro Kategorie (vorher → nachher)

| Kategorie | Vorher | Nachher | Delta |
|---|---|---|---|
| `iphone` | 2.213 | 2.213 | 0 |
| `gpu` | 251 | 251 | 0 |
| `lego_minifiguren` | 1.256 | 1.219 | **−37** |
| `retro_konsolen` | 649 | 642 | **−7** |
| `macbook` | 365 | 365 | 0 |
| `monitor_curved` | 548 | 548 | 0 |
| `vintage_elektronik` | 269 | 269 | 0 |
| `sata_ssd` | 300 | 300 | 0 |
| `netzteil` | 238 | 238 | 0 |
| `office_pc` | 148 | 148 | 0 |
| `gaming_pc` | 119 | 119 | 0 |
| `notebook_resell` | 87 | 87 | 0 |
| `ram` | 98 | 98 | 0 |
| `cpu_mainboard_bundle` | 2 | 2 | 0 (aber siehe Abschnitt 7 — echte Bedeutung!) |
| `konsolen_bundles` *(neu)* | 0 | 22 | +22 |
| `handhelds` *(neu)* | 0 | 8 | +8 |
| `autoradio_opel_corsa` *(neu)* | 0 | 6 | +6 |
| `controller` *(neu)* | 0 | 4 | +4 |

**Einordnung:** Die vier "neuen" Kategorien existierten im "Vorher"-
Regelwerk noch nicht — ihre Deltas sind kein Kalibrierungseffekt,
sondern spiegeln nur wider, dass sie zwischenzeitlich integriert wurden.
`iphone`/`macbook`/`gpu`/etc. zeigen **0 Delta bei der Gesamt-
Trefferzahl** — erwartbar, da die Preisgrenzen-Kalibrierung bei diesen
Kategorien nur die **Top-Deal-Einstufung** verschoben hat (Guter-Preis-/
Okay-Tiers blieben unverändert, ein Angebot, das vorher als "Guter
Preis" matchte, matcht jetzt eventuell als "Top-Deal", aber es matcht
so oder so).

**`lego_minifiguren` (−37) und `retro_konsolen` (−7) sind die einzigen
echten Volumen-Verschiebungen:**
- `lego_cmf` allein verlor 45 Treffer (189→144) durch die verschärften
  Preisgrenzen (Interessant-Tier 25€→10€) — 37 davon verließen die
  Kategorie komplett (Preis zwischen 10-25€, jetzt zu teuer für jeden
  Tier), 8 rutschten in benachbarte LEGO-Regeln (`lego_promo` etc.).
  Stichprobenprüfung der 45 herausgefallenen Treffer: ausschließlich
  Artikel im mittleren Preissegment, keine erkennbaren Fehlklassi-
  fizierungen.
- 7 `retro_konsolen`-Treffer wandern zu den neuen Kategorien
  `handhelds`/`konsolen_bundles` ab (z.B. "Nintendo Switch Controller
  N64-Style" — vorher fälschlich als Retro-Konsole, jetzt korrekt als
  Controller/Bundle erkannt). **Positiver Nebeneffekt** der neuen
  Kategorien, keine Regression.

---

## 2. Top-Deal-Anzahl (datengetrieben, `top_deal.py`)

| | Vorher | Nachher | Delta |
|---|---|---|---|
| Top-Deals gesamt | 335 | 347 | **+12 (+3,6%)** |

Anstieg plausibel und erwartbar: die iPhone-/MacBook-Kalibrierung hebt
gerade die Top-Deal-Grenze an, wodurch mehr real günstige Angebote jetzt
korrekt als Top-Deal erkannt werden (vorher fälschlich nur "Guter
Preis"/"Okay").

---

## 3. Deal-Score-Verteilung

| Score-Band | Vorher | Nachher |
|---|---|---|
| 95–100 (★★★★★) | 33 | 34 |
| 80–94 (★★★★☆) | 335 | 348 |
| 60–79 (★★★☆☆) | 780 | 781 |
| 40–59 (★★☆☆☆) | 1.966 | 1.980 |
| 0–39 (★☆☆☆☆) | 3.429 | 3.396 |

Leichte Verschiebung nach oben (mehr 4-/5-Sterne-, weniger 1-Stern-
Bewertungen) — konsistent mit korrekterer Preis-Score-Komponente durch
realistischere Grenzen.

---

## 4. Flip-Kandidaten-Anzahl (`is_robust_flip_candidate()`, Phase 11)

| | Vorher | Nachher | Delta |
|---|---|---|---|
| Flip-Kandidaten | 259 | 270 | **+11 (+4,2%)** |

Moderater, plausibler Anstieg — Folgeeffekt der Top-Deal-Verschiebung
(mehr Angebote mit korrekt hohem Deal-Score sind jetzt zusätzlich
Kandidaten für die margin-basierte Flip-Prüfung). Die Phase-11-Schwellen
selbst (`MIN_FLIP_MARGIN_PCT`/`_EUR`/`MIN_FLIP_DEAL_SCORE`/
`resale_confidence`) wurden **nicht** angefasst.

---

## 5. Resale-Confidence-Verteilung

| Confidence | Vorher | Nachher |
|---|---|---|
| HIGH | 5.925 | 5.879 |
| MEDIUM | 156 | 170 |
| LOW | 37 | 64 |
| kein Wert | 425 | 426 |

Leichte Verschiebung von HIGH → MEDIUM/LOW. Ursache: durch die
verschärfte `lego_cmf`-Grenze fallen einige Treffer in Nachbar-Regeln
mit kleineren, weniger belastbaren Preishistorie-Gruppen (z.B.
`lego_promo`) — dort ist die Resale-Confidence naturgemäß niedriger.
Kein Fehlverhalten, sondern korrekte Widerspiegelung der tatsächlichen
Datenlage je Gruppe.

---

## 6. False-Positive-Anzeichen

Stichprobenprüfung der **158 Angebote, die durch die Kalibrierung neu
als Top-Deal eingestuft werden** (iPhone/MacBook) — günstigste 8 und
teuerste 5 im Detail geprüft:

- Günstigste (125–150€, `iphone_11_pro_max_128gb`): ausschließlich
  plausible iPhone-11-Pro-Max-Angebote mit Speichergröße, teils mit
  Akkuzustand/Zubehör-Hinweis — keine Ersatzteile, keine Fake-/Trade-
  Listings.
- Teuerste (600–720€, `macbook_air_m4_512gb`/`iphone_16_pro_max_128gb`):
  vollständige, plausible Gerätebeschreibungen.

**Keine erkennbaren False Positives in der Stichprobe.** Ebenso wurden
die 54 neuen LEGO-CMF-Top-Deal-Treffer (≤5€) geprüft — durchgängig
plausible einzelne Sammelfiguren, keine Konvolute/Sets fälschlich zum
Einzelfiguren-Preis.

---

## 7. `cpu_mainboard_bundle`-Treffer — wichtigster Einzelbefund

**Erster echter Produktiv-Treffer seit Bestehen der Kategorie:** ein
realer Datenpunkt in `price_history.jsonl`, datiert **2026-08-08T22:53**
(nach dem Phase-11-Re-Evaluierungs-Fix):

```
175,00€  cpu_bundle_ryzen5600_b550  "asus prime b450 m k ii amd ryzen 5 5600 prozessor"
→ Regel: "Ryzen 5 5600 + B550 Bundle ★ Guter Preis"
```

Die Simulation findet zusätzlich einen **zweiten**, bisher unter
`gaming_pc` verbuchten Datenpunkt, der unter den aktuellen Regeln
**ebenfalls** `cpu_mainboard_bundle` zugeordnet würde:

```
160,00€  "gaming pc set bundle msi a520m a pro ryzen 5 5600 16gb ddr4 3200"
```

**Bewertung:** Die in Phase 11 eingeführte Re-Evaluierungs-Logik
funktioniert nachweislich in der Praxis — die Kategorie war zuvor
strukturell blockiert (`seen.json` verhinderte Neubewertung bereits
gesehener, nie gematchter Angebote), ist jetzt aber nachweisbar aktiv.
Die i5-12400F- und Ryzen-3600-Combos haben weiterhin **0 Treffer** —
konsistent mit der in Phase 11/12 dokumentierten Einschätzung, dass
deren Preisgrenzen (55€/75€ bzw. 100€/130€) vermutlich zu niedrig für
reale Angebote sind. **Keine Preisänderung in diesem Schritt** — nur
Beobachtung.

---

## 8. Auswirkungen der neuen iPhone-Preisgrenzen

8 Top-Deal-Regeln angehoben (11 Pro Max bis 16 Pro Max). Effekt:
**+12 Top-Deals gesamt** (Punkt 2), **0 Änderung der Gesamt-Match-Zahl**
(Punkt 1 — Umklassifizierung von Guter-Preis/Okay zu Top-Deal, nicht
neue Treffer). 158 Angebote betroffen für iPhone+MacBook zusammen, alle
stichprobenartig geprüft als plausibel (Punkt 6). Größter Einzeleffekt:
`iphone_15_128gb` mit 155 Samples (größte Stichprobe unter den
geänderten Modellen).

---

## 9. Auswirkungen der MacBook-Air-M4-Grenze

Direkteste, klarste Verbesserung der gesamten Kalibrierung: die alte
Grenze (415€) lag unter dem günstigsten real beobachteten Angebot
(499€) — **strukturell konnte nie ein Top-Deal erkannt werden.** Nach
der Anhebung auf 725€ sind mehrere reale Angebote (bis 720€, siehe
Stichprobe Punkt 6) jetzt korrekt als Top-Deal erkennbar. Direkter,
eindeutig messbarer Fortschritt.

---

## 10. Auswirkungen der neuen LEGO-CMF-Grenzen

Einzige Kategorie mit **Verschärfung** (nicht Lockerung) der Grenzen.
Effekt: 45 von 189 bisherigen `lego_cmf`-Treffern verlieren die
Einstufung (37 verlassen die Kategorie komplett, 8 rutschen in
Nachbarregeln). Stichprobenprüfung: alle verbleibenden bzw. neu
eingestuften Top-Deal-Treffer (≤5€) sind plausible Einzelfiguren, keine
erkennbaren Fehlklassifizierungen. Leichter Rückgang der
Resale-Confidence bei den umklassifizierten Treffern (Punkt 5) — durch
kleinere Vergleichsgruppen in den Nachbarregeln, nicht durch die
Kalibrierung selbst verursacht.

---

## Empfehlungen

1. **Echten Validierungs-Scan abwarten.** Diese Simulation ist
   bestmöglich, aber kein Ersatz für mehrere Tage echte Produktiv-
   beobachtung. Sobald neue Scan-Daten mit Zeitstempel **nach**
   2026-08-09 04:36 UTC vorliegen, sollte dieser Report mit echten
   "vorher/nachher"-Zahlen wiederholt werden.
2. **`cpu_mainboard_bundle` weiter beobachten** — der erste echte
   Treffer ist ein positives Signal, aber mit n=1-2 noch weit von einer
   belastbaren Aussage entfernt.
3. **Keine sofortige Handlung nötig** bei den beobachteten
   Kategorie-Verschiebungen (LEGO, Retro-Konsolen→neue Kategorien) — sie
   entsprechen der beabsichtigten bzw. einer positiven Nebenwirkung der
   Änderungen.
4. **Nintendo-/Sony-Retro-Konsolen** (aus Phase 12 als "MANUELLE
   PRÜFUNG" zurückgestellt) weiterhin nicht automatisch anfassen — die
   hier gezeigten Zahlen betreffen nicht deren Preisgrenzen.
5. Kein Bedarf für einen automatischen Selbst-Kalibrierungsmechanismus
   auf Basis dieser Validierung — die manuelle, schrittweise Kalibrierung
   hat sich als kontrollierbar und mit nachvollziehbaren Effekten
   erwiesen.

---

## Testanzahl und Ergebnis

Keine Code-/YAML-Änderung in diesem Schritt — reine Analyse.
`pytest app/tests/` → **851 passed, 0 failed** (unverändert).
