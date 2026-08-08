# Preisgrenzen-Kalibrierungsreport (Phase 12, Schritt 1) — mit echten Produktivdaten

**Stand:** 2026-08-09 · **Status:** Analyse abgeschlossen, KEINE YAML-Änderungen vorgenommen
**Datengrundlage:** echte `price_history.jsonl` (von dir hochgeladen), 9.161 Datenpunkte,
Zeitraum 2026-07-25 bis 2026-08-08 (≈2 Wochen), 99 Modelle mit mindestens 1 Sample.

---

## Methodik

- `price_history.jsonl` mit dem bestehenden `price_stats.compute_all_price_stats()`
  ausgewertet (keine neue Berechnungslogik, Single Source of Truth).
- Sample-Klassifikation exakt nach Vorgabe: <5 NICHT KALIBRIERBAR, 5-14 nur
  Empfehlung, 15-29 vorsichtig mit Begründung, 30-49 gute Basis, ≥50 sehr
  gute Basis.
- **Empfehlungslogik je Tier** (bewusst NICHT "Median = max_price"):
  - `Top-Deal` → empfohlene Grenze = **P25** (klar unter Markt, eindeutige Gelegenheit)
  - `Guter Preis` → empfohlene Grenze = **Median** (Marktmitte)
  - `Okay`/`Interessant` → empfohlene Grenze = **P75** (oberes noch prüfenswertes Segment)
- **Urteil:** aktuelle Grenze vs. Empfehlung — Abweichung <30 % = PLAUSIBEL,
  aktuell <70 % der Empfehlung = ZU STRENG (zu niedrig), aktuell >130 % der
  Empfehlung = ZU HOCH. Diese Bänder sind eine dokumentierte Heuristik für
  diesen Report, **keine automatisch angewendete Regel** — jede Empfehlung
  bleibt manuell zu prüfen, insbesondere bei <30 Samples.
- `market_price`/`estimated_resale_price`-Trennung, Phase-11-Flip-Schwellen
  (20 %/30 €/75/nicht-LOW) und Top-Deal-/Deal-Score-Logik **unverändert** —
  dieser Report bewertet ausschließlich `max_price` je Regel.
- **Keine** YAML-Datei verändert.

---

## Übersicht (Pflicht-Kategorisierung)

| Einstufung | Anzahl Regeln |
|---|---|
| **KALIBRIEREN** (≥15 Samples, belastbare Empfehlung möglich) | **169** |
| davon AKTUELLE GRENZE PLAUSIBEL | 128 |
| davon AKTUELLE GRENZE ZU STRENG (zu niedrig) | 13 |
| davon AKTUELLE GRENZE ZU HOCH | 28 |
| NICHT KALIBRIERBAR (<5 Samples) | 95 |
| ZU WENIGE DATEN (5-14 Samples, nur Empfehlung) | 46 |
| **Summe** | **310** |

---

## ⚠️ Wichtigster struktureller Befund: `lego_sw_rare` — jetzt mit echten Daten bestätigt

Im vorherigen (datenlosen) Report hatte ich bereits strukturell auffällig
gefunden, dass `lego_sw_rare` von zwei inhaltlich unterschiedlichen Regeln
geteilt wird ("Darth Revan" 40/60/80€ vs. generische "seltene Figur"
15/30/50€). **Mit echten Daten (103 Samples) bestätigt sich das Problem
sogar noch deutlicher:**

Die komplette Preisverteilung für `lego_sw_rare` reicht von **2,49€ bis
49,99€** — es gibt **keinerlei Hinweis auf einen distinkten,
teureren "Darth Revan"-Preiscluster** (P25=4,5€, Median=8,2€, P75=24,9€).
Die "Darth Revan"-Tier-Preise (40/60/80€) liegen damit **weit außerhalb**
jeder real beobachteten Verteilung für diesen Schlüssel.

**Zwei mögliche Erklärungen** (ohne Blick in die echten Titel nicht sicher
unterscheidbar):
1. Reale Darth-Revan-Angebote sind so selten, dass sie in der Statistik
   von den viel häufigeren generischen "seltene Figur"-Treffern
   überdeckt werden, oder
2. Die "Darth Revan"-Regel matcht in der Praxis primär dieselben
   generischen, günstigen Angebote wie die "seltene Figur"-Regel
   (Titel-Matching zu unscharf) — dann wären die 40/60/80€-Grenzen von
   Anfang an nie realistisch erreicht worden.

**Empfehlung (nur dokumentiert, nicht automatisch geändert):** eigenen
`price_history_model`-Schlüssel für "seltene Figur" vergeben, dann beide
Verteilungen getrennt neu beobachten, bevor eine Preisgrenzen-Entscheidung
für "Darth Revan" getroffen wird — die aktuellen 40/60/80€ könnten sowohl
zu hoch (Erklärung 2) als auch schlicht noch nie getestet worden sein
(Erklärung 1).

---

## Weitere auffällige Muster (systematisch, nicht nur Einzelfälle)

### iPhone 15/16-Serie: Top-Deal-Grenzen durchgängig zu niedrig
Alle iPhone-15/16-Modelle mit ausreichend Daten zeigen dasselbe Muster:
die reale P25-Preisschwelle liegt 40-70 % über der aktuellen Top-Deal-
Grenze. Beispiel: iPhone 15 Pro (256GB) — aktuell 265€, real P25 = 382,5€
(126 Samples, sehr gute Basis). Das deutet auf eine **systematische
Fehlkalibrierung der neueren/teureren iPhone-Modelle** hin (ältere/
günstigere Modelle wie iPhone 11/12 zeigen dieses Muster nicht) —
vermutlich wurden die Top-Deal-Grenzen ursprünglich mit veralteten
Marktpreis-Annahmen gesetzt und seither nicht nachgezogen.

### LEGO-Minifiguren und Retro-Konsolen: Grenzen durchgängig zu hoch
Nahezu die gesamte `lego_minifiguren`-Kategorie (cmf, ninjago_bundle,
sw_clone, sw_rare, promo) sowie beide Retro-Konsolen-Modelle (Nintendo,
Sony) zeigen das umgekehrte Muster: aktuelle Grenzen liegen 40-180 % über
dem, was reale Daten (teils >500 Samples, sehr belastbar) als Top-Deal-
Niveau zeigen. Das deutet darauf hin, dass in diesen Kategorien aktuell
viele Angebote als "Top-Deal"/"Guter Preis" markiert werden, die nach
echten Marktdaten nur durchschnittlich sind.

### `crt_profi_monitor`, `thinkpad_modern`, `vintage_hifi_verstaerker`: ebenfalls zu hoch
Mit jeweils 77-326 Samples eine sehr gute Datenbasis — auch hier liegen
die aktuellen Grenzen deutlich über den realen Marktperzentilen.

---

## Auffälligste Befunde (≥15 Samples, klare Abweichung)

### Grenzen, die zu NIEDRIG wirken (13 Regeln, blockieren vermutlich echte Treffer)

| Kategorie | Modell | Regel | Samples | Aktuell | Empfohlen | Basis |
|---|---|---|---|---|---|---|
| iphone | `iphone_15_128gb` | iPhone 15 (≤256GB) ★ Top-Deal | 154 | 210€ | 312.0€ | P25 |
| iphone | `iphone_15_pro_128gb` | iPhone 15 Pro (≤256GB) ★ Top-Deal | 126 | 265€ | 382.5€ | P25 |
| netzteil | `netzteil_650w` | ~650-749W Netzteil ★ Top-Deal | 87 | 20€ | 29.0€ | P25 |
| iphone | `iphone_16_pro_128gb` | iPhone 16 Pro (≤256GB) ★ Top-Deal | 79 | 360€ | 550.0€ | P25 |
| iphone | `iphone_15_pro_max_128gb` | iPhone 15 Pro Max (≤256GB) ★ Top-Deal | 72 | 300€ | 450.0€ | P25 |
| iphone | `iphone_16_pro_max_128gb` | iPhone 16 Pro Max (≤256GB) ★ Top-Deal | 70 | 415€ | 600.0€ | P25 |
| iphone | `iphone_16_128gb` | iPhone 16 (≤256GB) ★ Top-Deal | 61 | 275€ | 399.0€ | P25 |
| retro_konsolen | `retro_konvolut` | Retro-Konsolen-Konvolut ★ Top-Deal | 33 | 24€ | 39.9€ | P25 |
| iphone | `iphone_11_pro_max_128gb` | iPhone 11 Pro Max (≤256GB) ★ Top-Deal | 29 | 100€ | 150.0€ | P25 |
| iphone | `iphone_14_plus_128gb` | iPhone 14 Plus (≤256GB) ★ Top-Deal | 26 | 165€ | 250.4€ | P25 |
| iphone | `iphone_15_plus_128gb` | iPhone 15 Plus (≤256GB) ★ Top-Deal | 19 | 220€ | 350.0€ | P25 |
| iphone | `iphone_16_pro_max_512gb` | iPhone 16 Pro Max (≥512GB) ★ Top-Deal | 16 | 470€ | 697.5€ | P25 |
| macbook | `macbook_air_m4_512gb` | MacBook Air M4 (≤512GB) ★ Top-Deal | 16 | 415€ | 726.8€ | P25 |

### Grenzen, die zu HOCH wirken (28 Regeln, lassen vermutlich zu viele Angebote als "Top-Deal" durch)

| Kategorie | Modell | Regel | Samples | Aktuell | Empfohlen | Basis |
|---|---|---|---|---|---|---|
| retro_konsolen | `nintendo_retro_konsole` | Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal | 542 | 40€ | 25.0€ | P25 |
| retro_konsolen | `nintendo_retro_konsole` | Nintendo Retro-Konsole (N64/GameCube/DS) 👍 Guter Preis | 542 | 70€ | 49.0€ | Median |
| retro_konsolen | `nintendo_retro_konsole` | Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay | 542 | 100€ | 70.0€ | P75 |
| lego_minifiguren | `lego_ninjago_bundle` | LEGO Ninjago – Figuren-Konvolut ★ Top-Deal | 537 | 20€ | 15.0€ | P25 |
| lego_minifiguren | `lego_ninjago_bundle` | LEGO Ninjago – Figuren-Konvolut 👍 Guter Preis | 537 | 40€ | 30.0€ | Median |
| lego_minifiguren | `lego_ninjago_bundle` | LEGO Ninjago – Figuren-Konvolut ⚠️ Interessant | 537 | 70€ | 45.0€ | P75 |
| retro_konsolen | `sony_retro_konsole` | Sony Retro-Konsole (PS1/PS2) ★ Top-Deal | 533 | 35€ | 20.0€ | P25 |
| retro_konsolen | `sony_retro_konsole` | Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis | 533 | 60€ | 40.0€ | Median |
| retro_konsolen | `sony_retro_konsole` | Sony Retro-Konsole (PS1/PS2) ⚠️ Okay | 533 | 90€ | 60.0€ | P75 |
| lego_minifiguren | `lego_sw_clone` | LEGO Star Wars – Clone Wars ★ Top-Deal | 424 | 20€ | 7.0€ | P25 |
| lego_minifiguren | `lego_sw_clone` | LEGO Star Wars – Clone Wars 👍 Guter Preis | 424 | 35€ | 12.0€ | Median |
| lego_minifiguren | `lego_sw_clone` | LEGO Star Wars – Clone Wars ⚠️ Interessant | 424 | 50€ | 22.0€ | P75 |
| vintage_elektronik | `vintage_hifi_verstaerker` | Vintage-HiFi-Verstärker (Markenware) ⚠️ Okay | 326 | 200€ | 129.7€ | P75 |
| lego_minifiguren | `lego_cmf` | LEGO CMF / Sammelfigur ★ Top-Deal | 175 | 8€ | 5.0€ | P25 |
| lego_minifiguren | `lego_cmf` | LEGO CMF / Sammelfigur 👍 Guter Preis | 175 | 15€ | 7.0€ | Median |
| lego_minifiguren | `lego_cmf` | LEGO CMF / Sammelfigur ⚠️ Interessant | 175 | 25€ | 9.7€ | P75 |
| notebook_resell | `thinkpad_modern` | ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top | 117 | 180€ | 100.0€ | P25 |
| lego_minifiguren | `lego_sw_rare` | LEGO Star Wars – seltene Figur ★ Top-Deal | 103 | 15€ | 4.5€ | P25 |
| lego_minifiguren | `lego_sw_rare` | LEGO Star Wars – seltene Figur 👍 Guter Preis | 103 | 30€ | 8.2€ | Median |
| lego_minifiguren | `lego_sw_rare` | LEGO Star Wars – Darth Revan ★ Top-Deal | 103 | 40€ | 4.5€ | P25 |
| lego_minifiguren | `lego_sw_rare` | LEGO Star Wars – seltene Figur ⚠️ Interessant | 103 | 50€ | 24.9€ | P75 |
| lego_minifiguren | `lego_sw_rare` | LEGO Star Wars – Darth Revan 👍 Guter Preis | 103 | 60€ | 8.2€ | Median |
| lego_minifiguren | `lego_sw_rare` | LEGO Star Wars – Darth Revan ⚠️ Interessant | 103 | 80€ | 24.9€ | P75 |
| vintage_elektronik | `crt_profi_monitor` | Profi-CRT-Monitor (Sony PVM/BVM/Trinitron) ★ Top-Deal | 77 | 80€ | 49.0€ | P25 |
| vintage_elektronik | `crt_profi_monitor` | Profi-CRT-Monitor (Sony PVM/BVM/Trinitron) 👍 Guter Preis | 77 | 150€ | 99.0€ | Median |
| vintage_elektronik | `roehrenfernseher` | Röhrenfernseher ⚠️ Okay | 68 | 45€ | 29.0€ | P75 |
| lego_minifiguren | `lego_promo` | LEGO Promo/Exclusive Minifigur 👍 Guter Preis | 16 | 30€ | 15.7€ | Median |
| lego_minifiguren | `lego_promo` | LEGO Promo/Exclusive Minifigur ⚠️ Interessant | 16 | 50€ | 21.2€ | P75 |

---

## Vollständige Detailtabelle je Kategorie

### Kategorie: `cpu_mainboard_bundle` (cpu_mainboard_bundle.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `cpu_bundle_i5_12400f_b660` | Intel i5 12400F DDR4 Bundle ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 100€ | – | NICHT KALIBRIERBAR |
| `cpu_bundle_i5_12400f_b660` | Intel i5 12400F DDR4 Bundle ★ Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 130€ | – | NICHT KALIBRIERBAR |
| `cpu_bundle_ryzen3600_b450` | Ryzen 5 3600 + B450 Bundle ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 55€ | – | NICHT KALIBRIERBAR |
| `cpu_bundle_ryzen3600_b450` | Ryzen 5 3600 + B450 Bundle ★ Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 75€ | – | NICHT KALIBRIERBAR |
| `cpu_bundle_ryzen5600_b550` | Ryzen 5 5600 + B550 Bundle ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 150€ | – | NICHT KALIBRIERBAR |
| `cpu_bundle_ryzen5600_b550` | Ryzen 5 5600 + B550 Bundle ★ Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 200€ | – | NICHT KALIBRIERBAR |

### Kategorie: `gaming_pc` (gaming_pc.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `gaming_pc` | Gaming-PC (Top-Deal, bevorzugte GPU) | Top-Deal | 531 | >=50: sehr gute Basis | 290.0 | 350.0 | 430.0 | 500.0 | 550.0 | 300€ | 350.0 | PLAUSIBEL |
| `gaming_pc` | Gaming-PC (Mindestanforderung erfüllt) | Okay | 531 | >=50: sehr gute Basis | 290.0 | 350.0 | 430.0 | 500.0 | 550.0 | 450€ | 500.0 | PLAUSIBEL |

### Kategorie: `gpu` (gpu.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `rtx_2080_ti` | RTX 2080 Ti ★ Top-Deal | Top-Deal | 47 | 30-49: gute Basis | 19.8 | 177.4 | 220.0 | 250.0 | 262.0 | 220€ | 177.4 | PLAUSIBEL |
| `rtx_2080_ti` | RTX 2080 Ti | Guter Preis | 47 | 30-49: gute Basis | 19.8 | 177.4 | 220.0 | 250.0 | 262.0 | 270€ | 220.0 | PLAUSIBEL |
| `rtx_3060_12gb` | RTX 3060 12GB ★ Top-Deal | Top-Deal | 254 | >=50: sehr gute Basis | 196.9 | 220.0 | 248.0 | 260.0 | 270.0 | 220€ | 220.0 | PLAUSIBEL |
| `rtx_3060_12gb` | RTX 3060 12GB | Guter Preis | 254 | >=50: sehr gute Basis | 196.9 | 220.0 | 248.0 | 260.0 | 270.0 | 280€ | 248.0 | PLAUSIBEL |
| `rtx_3060_ti` | RTX 3060 Ti ★ Top-Deal | Top-Deal | 81 | >=50: sehr gute Basis | 190.0 | 200.0 | 225.0 | 250.0 | 260.0 | 220€ | 200.0 | PLAUSIBEL |
| `rtx_3060_ti` | RTX 3060 Ti | Guter Preis | 81 | >=50: sehr gute Basis | 190.0 | 200.0 | 225.0 | 250.0 | 260.0 | 280€ | 225.0 | PLAUSIBEL |
| `rtx_3070` | RTX 3070 ★ Top-Deal | Top-Deal | 108 | >=50: sehr gute Basis | 200.0 | 220.0 | 250.0 | 279.0 | 300.0 | 250€ | 220.0 | PLAUSIBEL |
| `rtx_3070` | RTX 3070 | Guter Preis | 108 | >=50: sehr gute Basis | 200.0 | 220.0 | 250.0 | 279.0 | 300.0 | 310€ | 250.0 | PLAUSIBEL |
| `rtx_4060` | RTX 4060 ★ Top-Deal | Top-Deal | 22 | 15-29: vorsichtig, manuell pruefen | 155.0 | 202.5 | 227.5 | 265.0 | 278.6 | 240€ | 202.5 | PLAUSIBEL |
| `rtx_4060` | RTX 4060 | Guter Preis | 22 | 15-29: vorsichtig, manuell pruefen | 155.0 | 202.5 | 227.5 | 265.0 | 278.6 | 290€ | 227.5 | PLAUSIBEL |
| `rx_6700_xt` | RX 6700 XT ★ Top-Deal | Top-Deal | 90 | >=50: sehr gute Basis | 200.0 | 225.3 | 250.0 | 280.0 | 299.0 | 240€ | 225.3 | PLAUSIBEL |
| `rx_6700_xt` | RX 6700 XT | Guter Preis | 90 | >=50: sehr gute Basis | 200.0 | 225.3 | 250.0 | 280.0 | 299.0 | 300€ | 250.0 | PLAUSIBEL |
| `rx_6750_xt` | RX 6750 XT ★ Top-Deal | Top-Deal | 23 | 15-29: vorsichtig, manuell pruefen | 250.0 | 250.0 | 279.0 | 290.0 | 299.8 | 250€ | 250.0 | PLAUSIBEL |
| `rx_6750_xt` | RX 6750 XT | Guter Preis | 23 | 15-29: vorsichtig, manuell pruefen | 250.0 | 250.0 | 279.0 | 290.0 | 299.8 | 310€ | 279.0 | PLAUSIBEL |
| `rx_6800` | RX 6800 ★ Top-Deal | Top-Deal | 32 | 30-49: gute Basis | 269.1 | 287.5 | 310.0 | 340.0 | 349.9 | 290€ | 287.5 | PLAUSIBEL |
| `rx_6800` | RX 6800 | Guter Preis | 32 | 30-49: gute Basis | 269.1 | 287.5 | 310.0 | 340.0 | 349.9 | 350€ | 310.0 | PLAUSIBEL |
| `rx_7600` | RX 7600 ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 160€ | – | NICHT KALIBRIERBAR |
| `rx_7600` | RX 7600 | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 210€ | – | NICHT KALIBRIERBAR |
| `rx_7600_xt` | RX 7600 XT ★ Top-Deal | Top-Deal | 8 | 5-14: nur Empfehlung | 172.6 | 195.0 | 200.0 | 220.0 | 220.0 | 180€ | 195.0 | PLAUSIBEL |
| `rx_7600_xt` | RX 7600 XT | Guter Preis | 8 | 5-14: nur Empfehlung | 172.6 | 195.0 | 200.0 | 220.0 | 220.0 | 230€ | 200.0 | PLAUSIBEL |

### Kategorie: `iphone` (iphone.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `iphone_11_128gb` | iPhone 11 (≤256GB) ★ Top-Deal | Top-Deal | 299 | >=50: sehr gute Basis | 79.5 | 95.0 | 110.0 | 120.0 | 129.2 | 70€ | 95.0 | PLAUSIBEL |
| `iphone_11_128gb` | iPhone 11 (≤256GB) 👍 Guter Preis | Guter Preis | 299 | >=50: sehr gute Basis | 79.5 | 95.0 | 110.0 | 120.0 | 129.2 | 100€ | 110.0 | PLAUSIBEL |
| `iphone_11_128gb` | iPhone 11 (≤256GB) ⚠️ Okay | Okay | 299 | >=50: sehr gute Basis | 79.5 | 95.0 | 110.0 | 120.0 | 129.2 | 130€ | 120.0 | PLAUSIBEL |
| `iphone_11_512gb` | iPhone 11 (≥512GB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 125€ | – | NICHT KALIBRIERBAR |
| `iphone_11_512gb` | iPhone 11 (≥512GB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 180€ | – | NICHT KALIBRIERBAR |
| `iphone_11_512gb` | iPhone 11 (≥512GB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 230€ | – | NICHT KALIBRIERBAR |
| `iphone_11_pro_128gb` | iPhone 11 Pro (≤256GB) ★ Top-Deal | Top-Deal | 83 | >=50: sehr gute Basis | 99.2 | 115.0 | 139.0 | 150.0 | 160.0 | 90€ | 115.0 | PLAUSIBEL |
| `iphone_11_pro_128gb` | iPhone 11 Pro (≤256GB) 👍 Guter Preis | Guter Preis | 83 | >=50: sehr gute Basis | 99.2 | 115.0 | 139.0 | 150.0 | 160.0 | 125€ | 139.0 | PLAUSIBEL |
| `iphone_11_pro_128gb` | iPhone 11 Pro (≤256GB) ⚠️ Okay | Okay | 83 | >=50: sehr gute Basis | 99.2 | 115.0 | 139.0 | 150.0 | 160.0 | 160€ | 150.0 | PLAUSIBEL |
| `iphone_11_pro_512gb` | iPhone 11 Pro (≥512GB) ★ Top-Deal | Top-Deal | 5 | 5-14: nur Empfehlung | 186.4 | 190.0 | 220.0 | 229.0 | 241.6 | 145€ | 190.0 | PLAUSIBEL |
| `iphone_11_pro_512gb` | iPhone 11 Pro (≥512GB) 👍 Guter Preis | Guter Preis | 5 | 5-14: nur Empfehlung | 186.4 | 190.0 | 220.0 | 229.0 | 241.6 | 205€ | 220.0 | PLAUSIBEL |
| `iphone_11_pro_512gb` | iPhone 11 Pro (≥512GB) ⚠️ Okay | Okay | 5 | 5-14: nur Empfehlung | 186.4 | 190.0 | 220.0 | 229.0 | 241.6 | 260€ | 229.0 | PLAUSIBEL |
| `iphone_11_pro_max_128gb` | iPhone 11 Pro Max (≤256GB) ★ Top-Deal | Top-Deal | 29 | 15-29: vorsichtig, manuell pruefen | 100.0 | 150.0 | 160.0 | 175.0 | 180.0 | 100€ | 150.0 | ZU STRENG |
| `iphone_11_pro_max_128gb` | iPhone 11 Pro Max (≤256GB) 👍 Guter Preis | Guter Preis | 29 | 15-29: vorsichtig, manuell pruefen | 100.0 | 150.0 | 160.0 | 175.0 | 180.0 | 140€ | 160.0 | PLAUSIBEL |
| `iphone_11_pro_max_128gb` | iPhone 11 Pro Max (≤256GB) ⚠️ Okay | Okay | 29 | 15-29: vorsichtig, manuell pruefen | 100.0 | 150.0 | 160.0 | 175.0 | 180.0 | 180€ | 175.0 | PLAUSIBEL |
| `iphone_11_pro_max_512gb` | iPhone 11 Pro Max (≥512GB) ★ Top-Deal | Top-Deal | 3 | NICHT KALIBRIERBAR | 252.0 | 255.0 | 260.0 | 269.5 | 275.2 | 155€ | 255.0 | ZU STRENG |
| `iphone_11_pro_max_512gb` | iPhone 11 Pro Max (≥512GB) 👍 Guter Preis | Guter Preis | 3 | NICHT KALIBRIERBAR | 252.0 | 255.0 | 260.0 | 269.5 | 275.2 | 220€ | 260.0 | PLAUSIBEL |
| `iphone_11_pro_max_512gb` | iPhone 11 Pro Max (≥512GB) ⚠️ Okay | Okay | 3 | NICHT KALIBRIERBAR | 252.0 | 255.0 | 260.0 | 269.5 | 275.2 | 280€ | 269.5 | PLAUSIBEL |
| `iphone_12_128gb` | iPhone 12 (≤256GB) ★ Top-Deal | Top-Deal | 204 | >=50: sehr gute Basis | 90.0 | 118.0 | 139.4 | 150.0 | 158.7 | 90€ | 118.0 | PLAUSIBEL |
| `iphone_12_128gb` | iPhone 12 (≤256GB) 👍 Guter Preis | Guter Preis | 204 | >=50: sehr gute Basis | 90.0 | 118.0 | 139.4 | 150.0 | 158.7 | 125€ | 139.4 | PLAUSIBEL |
| `iphone_12_128gb` | iPhone 12 (≤256GB) ⚠️ Okay | Okay | 204 | >=50: sehr gute Basis | 90.0 | 118.0 | 139.4 | 150.0 | 158.7 | 160€ | 150.0 | PLAUSIBEL |
| `iphone_12_512gb` | iPhone 12 (≥512GB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 145€ | – | NICHT KALIBRIERBAR |
| `iphone_12_512gb` | iPhone 12 (≥512GB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 205€ | – | NICHT KALIBRIERBAR |
| `iphone_12_512gb` | iPhone 12 (≥512GB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 260€ | – | NICHT KALIBRIERBAR |
| `iphone_12_mini_128gb` | iPhone 12 mini (≤256GB) ★ Top-Deal | Top-Deal | 80 | >=50: sehr gute Basis | 98.0 | 103.8 | 120.0 | 135.0 | 140.0 | 75€ | 103.8 | PLAUSIBEL |
| `iphone_12_mini_128gb` | iPhone 12 mini (≤256GB) 👍 Guter Preis | Guter Preis | 80 | >=50: sehr gute Basis | 98.0 | 103.8 | 120.0 | 135.0 | 140.0 | 110€ | 120.0 | PLAUSIBEL |
| `iphone_12_mini_128gb` | iPhone 12 mini (≤256GB) ⚠️ Okay | Okay | 80 | >=50: sehr gute Basis | 98.0 | 103.8 | 120.0 | 135.0 | 140.0 | 140€ | 135.0 | PLAUSIBEL |
| `iphone_12_mini_512gb` | iPhone 12 mini (≥512GB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 130€ | – | NICHT KALIBRIERBAR |
| `iphone_12_mini_512gb` | iPhone 12 mini (≥512GB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 185€ | – | NICHT KALIBRIERBAR |
| `iphone_12_mini_512gb` | iPhone 12 mini (≥512GB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 240€ | – | NICHT KALIBRIERBAR |
| `iphone_12_pro_128gb` | iPhone 12 Pro (≤256GB) ★ Top-Deal | Top-Deal | 45 | 30-49: gute Basis | 114.6 | 145.0 | 160.0 | 170.0 | 188.0 | 105€ | 145.0 | PLAUSIBEL |
| `iphone_12_pro_128gb` | iPhone 12 Pro (≤256GB) 👍 Guter Preis | Guter Preis | 45 | 30-49: gute Basis | 114.6 | 145.0 | 160.0 | 170.0 | 188.0 | 150€ | 160.0 | PLAUSIBEL |
| `iphone_12_pro_128gb` | iPhone 12 Pro (≤256GB) ⚠️ Okay | Okay | 45 | 30-49: gute Basis | 114.6 | 145.0 | 160.0 | 170.0 | 188.0 | 190€ | 170.0 | PLAUSIBEL |
| `iphone_12_pro_512gb` | iPhone 12 Pro (≥512GB) ★ Top-Deal | Top-Deal | 9 | 5-14: nur Empfehlung | 179.0 | 222.0 | 250.0 | 264.9 | 290.0 | 160€ | 222.0 | PLAUSIBEL |
| `iphone_12_pro_512gb` | iPhone 12 Pro (≥512GB) 👍 Guter Preis | Guter Preis | 9 | 5-14: nur Empfehlung | 179.0 | 222.0 | 250.0 | 264.9 | 290.0 | 225€ | 250.0 | PLAUSIBEL |
| `iphone_12_pro_512gb` | iPhone 12 Pro (≥512GB) ⚠️ Okay | Okay | 9 | 5-14: nur Empfehlung | 179.0 | 222.0 | 250.0 | 264.9 | 290.0 | 290€ | 264.9 | PLAUSIBEL |
| `iphone_12_pro_max_128gb` | iPhone 12 Pro Max (≤256GB) ★ Top-Deal | Top-Deal | 30 | 30-49: gute Basis | 139.0 | 150.0 | 199.5 | 215.0 | 220.0 | 120€ | 150.0 | PLAUSIBEL |
| `iphone_12_pro_max_128gb` | iPhone 12 Pro Max (≤256GB) 👍 Guter Preis | Guter Preis | 30 | 30-49: gute Basis | 139.0 | 150.0 | 199.5 | 215.0 | 220.0 | 170€ | 199.5 | PLAUSIBEL |
| `iphone_12_pro_max_128gb` | iPhone 12 Pro Max (≤256GB) ⚠️ Okay | Okay | 30 | 30-49: gute Basis | 139.0 | 150.0 | 199.5 | 215.0 | 220.0 | 220€ | 215.0 | PLAUSIBEL |
| `iphone_12_pro_max_512gb` | iPhone 12 Pro Max (≥512GB) ★ Top-Deal | Top-Deal | 5 | 5-14: nur Empfehlung | 216.0 | 240.0 | 260.0 | 310.0 | 316.0 | 175€ | 240.0 | PLAUSIBEL |
| `iphone_12_pro_max_512gb` | iPhone 12 Pro Max (≥512GB) 👍 Guter Preis | Guter Preis | 5 | 5-14: nur Empfehlung | 216.0 | 240.0 | 260.0 | 310.0 | 316.0 | 250€ | 260.0 | PLAUSIBEL |
| `iphone_12_pro_max_512gb` | iPhone 12 Pro Max (≥512GB) ⚠️ Okay | Okay | 5 | 5-14: nur Empfehlung | 216.0 | 240.0 | 260.0 | 310.0 | 316.0 | 320€ | 310.0 | PLAUSIBEL |
| `iphone_13_128gb` | iPhone 13 (≤256GB) ★ Top-Deal | Top-Deal | 235 | >=50: sehr gute Basis | 146.6 | 170.0 | 199.0 | 210.0 | 220.0 | 120€ | 170.0 | PLAUSIBEL |
| `iphone_13_128gb` | iPhone 13 (≤256GB) 👍 Guter Preis | Guter Preis | 235 | >=50: sehr gute Basis | 146.6 | 170.0 | 199.0 | 210.0 | 220.0 | 170€ | 199.0 | PLAUSIBEL |
| `iphone_13_128gb` | iPhone 13 (≤256GB) ⚠️ Okay | Okay | 235 | >=50: sehr gute Basis | 146.6 | 170.0 | 199.0 | 210.0 | 220.0 | 220€ | 210.0 | PLAUSIBEL |
| `iphone_13_512gb` | iPhone 13 (≥512GB) ★ Top-Deal | Top-Deal | 2 | NICHT KALIBRIERBAR | 243.5 | 248.8 | 257.5 | 266.2 | 271.5 | 175€ | 248.8 | PLAUSIBEL |
| `iphone_13_512gb` | iPhone 13 (≥512GB) 👍 Guter Preis | Guter Preis | 2 | NICHT KALIBRIERBAR | 243.5 | 248.8 | 257.5 | 266.2 | 271.5 | 250€ | 257.5 | PLAUSIBEL |
| `iphone_13_512gb` | iPhone 13 (≥512GB) ⚠️ Okay | Okay | 2 | NICHT KALIBRIERBAR | 243.5 | 248.8 | 257.5 | 266.2 | 271.5 | 320€ | 266.2 | PLAUSIBEL |
| `iphone_13_mini_128gb` | iPhone 13 mini (≤256GB) ★ Top-Deal | Top-Deal | 32 | 30-49: gute Basis | 100.0 | 140.0 | 172.5 | 180.0 | 189.5 | 105€ | 140.0 | PLAUSIBEL |
| `iphone_13_mini_128gb` | iPhone 13 mini (≤256GB) 👍 Guter Preis | Guter Preis | 32 | 30-49: gute Basis | 100.0 | 140.0 | 172.5 | 180.0 | 189.5 | 150€ | 172.5 | PLAUSIBEL |
| `iphone_13_mini_128gb` | iPhone 13 mini (≤256GB) ⚠️ Okay | Okay | 32 | 30-49: gute Basis | 100.0 | 140.0 | 172.5 | 180.0 | 189.5 | 190€ | 180.0 | PLAUSIBEL |
| `iphone_13_mini_512gb` | iPhone 13 mini (≥512GB) ★ Top-Deal | Top-Deal | 1 | NICHT KALIBRIERBAR | 198.0 | 198.0 | 198.0 | 198.0 | 198.0 | 160€ | 198.0 | PLAUSIBEL |
| `iphone_13_mini_512gb` | iPhone 13 mini (≥512GB) 👍 Guter Preis | Guter Preis | 1 | NICHT KALIBRIERBAR | 198.0 | 198.0 | 198.0 | 198.0 | 198.0 | 225€ | 198.0 | PLAUSIBEL |
| `iphone_13_mini_512gb` | iPhone 13 mini (≥512GB) ⚠️ Okay | Okay | 1 | NICHT KALIBRIERBAR | 198.0 | 198.0 | 198.0 | 198.0 | 198.0 | 290€ | 198.0 | ZU HOCH |
| `iphone_13_pro_128gb` | iPhone 13 Pro (≤256GB) ★ Top-Deal | Top-Deal | 72 | >=50: sehr gute Basis | 151.0 | 200.0 | 250.0 | 270.0 | 280.0 | 155€ | 200.0 | PLAUSIBEL |
| `iphone_13_pro_128gb` | iPhone 13 Pro (≤256GB) 👍 Guter Preis | Guter Preis | 72 | >=50: sehr gute Basis | 151.0 | 200.0 | 250.0 | 270.0 | 280.0 | 220€ | 250.0 | PLAUSIBEL |
| `iphone_13_pro_128gb` | iPhone 13 Pro (≤256GB) ⚠️ Okay | Okay | 72 | >=50: sehr gute Basis | 151.0 | 200.0 | 250.0 | 270.0 | 280.0 | 280€ | 270.0 | PLAUSIBEL |
| `iphone_13_pro_512gb` | iPhone 13 Pro (≥512GB) ★ Top-Deal | Top-Deal | 10 | 5-14: nur Empfehlung | 277.5 | 302.5 | 332.5 | 350.0 | 361.0 | 210€ | 302.5 | ZU STRENG |
| `iphone_13_pro_512gb` | iPhone 13 Pro (≥512GB) 👍 Guter Preis | Guter Preis | 10 | 5-14: nur Empfehlung | 277.5 | 302.5 | 332.5 | 350.0 | 361.0 | 295€ | 332.5 | PLAUSIBEL |
| `iphone_13_pro_512gb` | iPhone 13 Pro (≥512GB) ⚠️ Okay | Okay | 10 | 5-14: nur Empfehlung | 277.5 | 302.5 | 332.5 | 350.0 | 361.0 | 380€ | 350.0 | PLAUSIBEL |
| `iphone_13_pro_max_128gb` | iPhone 13 Pro Max (≤256GB) ★ Top-Deal | Top-Deal | 37 | 30-49: gute Basis | 218.0 | 250.0 | 290.0 | 300.0 | 300.0 | 175€ | 250.0 | PLAUSIBEL |
| `iphone_13_pro_max_128gb` | iPhone 13 Pro Max (≤256GB) 👍 Guter Preis | Guter Preis | 37 | 30-49: gute Basis | 218.0 | 250.0 | 290.0 | 300.0 | 300.0 | 250€ | 290.0 | PLAUSIBEL |
| `iphone_13_pro_max_128gb` | iPhone 13 Pro Max (≤256GB) ⚠️ Okay | Okay | 37 | 30-49: gute Basis | 218.0 | 250.0 | 290.0 | 300.0 | 300.0 | 320€ | 300.0 | PLAUSIBEL |
| `iphone_13_pro_max_512gb` | iPhone 13 Pro Max (≥512GB) ★ Top-Deal | Top-Deal | 5 | 5-14: nur Empfehlung | 154.0 | 160.0 | 200.0 | 280.0 | 345.4 | 230€ | 160.0 | ZU HOCH |
| `iphone_13_pro_max_512gb` | iPhone 13 Pro Max (≥512GB) 👍 Guter Preis | Guter Preis | 5 | 5-14: nur Empfehlung | 154.0 | 160.0 | 200.0 | 280.0 | 345.4 | 330€ | 200.0 | ZU HOCH |
| `iphone_13_pro_max_512gb` | iPhone 13 Pro Max (≥512GB) ⚠️ Okay | Okay | 5 | 5-14: nur Empfehlung | 154.0 | 160.0 | 200.0 | 280.0 | 345.4 | 420€ | 280.0 | ZU HOCH |
| `iphone_14_128gb` | iPhone 14 (≤256GB) ★ Top-Deal | Top-Deal | 143 | >=50: sehr gute Basis | 170.0 | 219.0 | 250.0 | 262.5 | 279.0 | 155€ | 219.0 | PLAUSIBEL |
| `iphone_14_128gb` | iPhone 14 (≤256GB) 👍 Guter Preis | Guter Preis | 143 | >=50: sehr gute Basis | 170.0 | 219.0 | 250.0 | 262.5 | 279.0 | 220€ | 250.0 | PLAUSIBEL |
| `iphone_14_128gb` | iPhone 14 (≤256GB) ⚠️ Okay | Okay | 143 | >=50: sehr gute Basis | 170.0 | 219.0 | 250.0 | 262.5 | 279.0 | 280€ | 262.5 | PLAUSIBEL |
| `iphone_14_512gb` | iPhone 14 (≥512GB) ★ Top-Deal | Top-Deal | 3 | NICHT KALIBRIERBAR | 326.0 | 335.0 | 350.0 | 350.0 | 350.0 | 210€ | 335.0 | ZU STRENG |
| `iphone_14_512gb` | iPhone 14 (≥512GB) 👍 Guter Preis | Guter Preis | 3 | NICHT KALIBRIERBAR | 326.0 | 335.0 | 350.0 | 350.0 | 350.0 | 295€ | 350.0 | PLAUSIBEL |
| `iphone_14_512gb` | iPhone 14 (≥512GB) ⚠️ Okay | Okay | 3 | NICHT KALIBRIERBAR | 326.0 | 335.0 | 350.0 | 350.0 | 350.0 | 380€ | 350.0 | PLAUSIBEL |
| `iphone_14_plus_128gb` | iPhone 14 Plus (≤256GB) ★ Top-Deal | Top-Deal | 26 | 15-29: vorsichtig, manuell pruefen | 194.5 | 250.4 | 274.9 | 283.8 | 300.0 | 165€ | 250.4 | ZU STRENG |
| `iphone_14_plus_128gb` | iPhone 14 Plus (≤256GB) 👍 Guter Preis | Guter Preis | 26 | 15-29: vorsichtig, manuell pruefen | 194.5 | 250.4 | 274.9 | 283.8 | 300.0 | 235€ | 274.9 | PLAUSIBEL |
| `iphone_14_plus_128gb` | iPhone 14 Plus (≤256GB) ⚠️ Okay | Okay | 26 | 15-29: vorsichtig, manuell pruefen | 194.5 | 250.4 | 274.9 | 283.8 | 300.0 | 300€ | 283.8 | PLAUSIBEL |
| `iphone_14_plus_512gb` | iPhone 14 Plus (≥512GB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 220€ | – | NICHT KALIBRIERBAR |
| `iphone_14_plus_512gb` | iPhone 14 Plus (≥512GB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 310€ | – | NICHT KALIBRIERBAR |
| `iphone_14_plus_512gb` | iPhone 14 Plus (≥512GB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 400€ | – | NICHT KALIBRIERBAR |
| `iphone_14_pro_128gb` | iPhone 14 Pro (≤256GB) ★ Top-Deal | Top-Deal | 124 | >=50: sehr gute Basis | 253.0 | 299.0 | 337.5 | 350.0 | 375.0 | 210€ | 299.0 | PLAUSIBEL |
| `iphone_14_pro_128gb` | iPhone 14 Pro (≤256GB) 👍 Guter Preis | Guter Preis | 124 | >=50: sehr gute Basis | 253.0 | 299.0 | 337.5 | 350.0 | 375.0 | 295€ | 337.5 | PLAUSIBEL |
| `iphone_14_pro_128gb` | iPhone 14 Pro (≤256GB) ⚠️ Okay | Okay | 124 | >=50: sehr gute Basis | 253.0 | 299.0 | 337.5 | 350.0 | 375.0 | 380€ | 350.0 | PLAUSIBEL |
| `iphone_14_pro_512gb` | iPhone 14 Pro (≥512GB) ★ Top-Deal | Top-Deal | 6 | 5-14: nur Empfehlung | 360.0 | 422.5 | 440.0 | 450.0 | 450.0 | 265€ | 422.5 | ZU STRENG |
| `iphone_14_pro_512gb` | iPhone 14 Pro (≥512GB) 👍 Guter Preis | Guter Preis | 6 | 5-14: nur Empfehlung | 360.0 | 422.5 | 440.0 | 450.0 | 450.0 | 375€ | 440.0 | PLAUSIBEL |
| `iphone_14_pro_512gb` | iPhone 14 Pro (≥512GB) ⚠️ Okay | Okay | 6 | 5-14: nur Empfehlung | 360.0 | 422.5 | 440.0 | 450.0 | 450.0 | 480€ | 450.0 | PLAUSIBEL |
| `iphone_14_pro_max_128gb` | iPhone 14 Pro Max (≤256GB) ★ Top-Deal | Top-Deal | 82 | >=50: sehr gute Basis | 271.0 | 305.0 | 369.0 | 400.0 | 410.0 | 230€ | 305.0 | PLAUSIBEL |
| `iphone_14_pro_max_128gb` | iPhone 14 Pro Max (≤256GB) 👍 Guter Preis | Guter Preis | 82 | >=50: sehr gute Basis | 271.0 | 305.0 | 369.0 | 400.0 | 410.0 | 330€ | 369.0 | PLAUSIBEL |
| `iphone_14_pro_max_128gb` | iPhone 14 Pro Max (≤256GB) ⚠️ Okay | Okay | 82 | >=50: sehr gute Basis | 271.0 | 305.0 | 369.0 | 400.0 | 410.0 | 420€ | 400.0 | PLAUSIBEL |
| `iphone_14_pro_max_512gb` | iPhone 14 Pro Max (≥512GB) ★ Top-Deal | Top-Deal | 5 | 5-14: nur Empfehlung | 399.4 | 400.0 | 420.0 | 450.0 | 480.0 | 285€ | 400.0 | PLAUSIBEL |
| `iphone_14_pro_max_512gb` | iPhone 14 Pro Max (≥512GB) 👍 Guter Preis | Guter Preis | 5 | 5-14: nur Empfehlung | 399.4 | 400.0 | 420.0 | 450.0 | 480.0 | 405€ | 420.0 | PLAUSIBEL |
| `iphone_14_pro_max_512gb` | iPhone 14 Pro Max (≥512GB) ⚠️ Okay | Okay | 5 | 5-14: nur Empfehlung | 399.4 | 400.0 | 420.0 | 450.0 | 480.0 | 520€ | 450.0 | PLAUSIBEL |
| `iphone_15_128gb` | iPhone 15 (≤256GB) ★ Top-Deal | Top-Deal | 154 | >=50: sehr gute Basis | 282.7 | 312.0 | 350.0 | 370.0 | 380.0 | 210€ | 312.0 | ZU STRENG |
| `iphone_15_128gb` | iPhone 15 (≤256GB) 👍 Guter Preis | Guter Preis | 154 | >=50: sehr gute Basis | 282.7 | 312.0 | 350.0 | 370.0 | 380.0 | 295€ | 350.0 | PLAUSIBEL |
| `iphone_15_128gb` | iPhone 15 (≤256GB) ⚠️ Okay | Okay | 154 | >=50: sehr gute Basis | 282.7 | 312.0 | 350.0 | 370.0 | 380.0 | 380€ | 370.0 | PLAUSIBEL |
| `iphone_15_512gb` | iPhone 15 (≥512GB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 265€ | – | NICHT KALIBRIERBAR |
| `iphone_15_512gb` | iPhone 15 (≥512GB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 375€ | – | NICHT KALIBRIERBAR |
| `iphone_15_512gb` | iPhone 15 (≥512GB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 480€ | – | NICHT KALIBRIERBAR |
| `iphone_15_plus_128gb` | iPhone 15 Plus (≤256GB) ★ Top-Deal | Top-Deal | 19 | 15-29: vorsichtig, manuell pruefen | 320.0 | 350.0 | 379.0 | 390.0 | 400.0 | 220€ | 350.0 | ZU STRENG |
| `iphone_15_plus_128gb` | iPhone 15 Plus (≤256GB) 👍 Guter Preis | Guter Preis | 19 | 15-29: vorsichtig, manuell pruefen | 320.0 | 350.0 | 379.0 | 390.0 | 400.0 | 310€ | 379.0 | PLAUSIBEL |
| `iphone_15_plus_128gb` | iPhone 15 Plus (≤256GB) ⚠️ Okay | Okay | 19 | 15-29: vorsichtig, manuell pruefen | 320.0 | 350.0 | 379.0 | 390.0 | 400.0 | 400€ | 390.0 | PLAUSIBEL |
| `iphone_15_plus_512gb` | iPhone 15 Plus (≥512GB) ★ Top-Deal | Top-Deal | 1 | NICHT KALIBRIERBAR | 450.0 | 450.0 | 450.0 | 450.0 | 450.0 | 275€ | 450.0 | ZU STRENG |
| `iphone_15_plus_512gb` | iPhone 15 Plus (≥512GB) 👍 Guter Preis | Guter Preis | 1 | NICHT KALIBRIERBAR | 450.0 | 450.0 | 450.0 | 450.0 | 450.0 | 390€ | 450.0 | PLAUSIBEL |
| `iphone_15_plus_512gb` | iPhone 15 Plus (≥512GB) ⚠️ Okay | Okay | 1 | NICHT KALIBRIERBAR | 450.0 | 450.0 | 450.0 | 450.0 | 450.0 | 500€ | 450.0 | PLAUSIBEL |
| `iphone_15_pro_128gb` | iPhone 15 Pro (≤256GB) ★ Top-Deal | Top-Deal | 126 | >=50: sehr gute Basis | 310.0 | 382.5 | 427.0 | 459.3 | 479.0 | 265€ | 382.5 | ZU STRENG |
| `iphone_15_pro_128gb` | iPhone 15 Pro (≤256GB) 👍 Guter Preis | Guter Preis | 126 | >=50: sehr gute Basis | 310.0 | 382.5 | 427.0 | 459.3 | 479.0 | 375€ | 427.0 | PLAUSIBEL |
| `iphone_15_pro_128gb` | iPhone 15 Pro (≤256GB) ⚠️ Okay | Okay | 126 | >=50: sehr gute Basis | 310.0 | 382.5 | 427.0 | 459.3 | 479.0 | 480€ | 459.3 | PLAUSIBEL |
| `iphone_15_pro_512gb` | iPhone 15 Pro (≥512GB) ★ Top-Deal | Top-Deal | 4 | NICHT KALIBRIERBAR | 509.0 | 522.5 | 540.0 | 552.5 | 557.0 | 320€ | 522.5 | ZU STRENG |
| `iphone_15_pro_512gb` | iPhone 15 Pro (≥512GB) 👍 Guter Preis | Guter Preis | 4 | NICHT KALIBRIERBAR | 509.0 | 522.5 | 540.0 | 552.5 | 557.0 | 450€ | 540.0 | PLAUSIBEL |
| `iphone_15_pro_512gb` | iPhone 15 Pro (≥512GB) ⚠️ Okay | Okay | 4 | NICHT KALIBRIERBAR | 509.0 | 522.5 | 540.0 | 552.5 | 557.0 | 580€ | 552.5 | PLAUSIBEL |
| `iphone_15_pro_max_128gb` | iPhone 15 Pro Max (≤256GB) ★ Top-Deal | Top-Deal | 72 | >=50: sehr gute Basis | 382.0 | 450.0 | 500.0 | 549.0 | 550.0 | 300€ | 450.0 | ZU STRENG |
| `iphone_15_pro_max_128gb` | iPhone 15 Pro Max (≤256GB) 👍 Guter Preis | Guter Preis | 72 | >=50: sehr gute Basis | 382.0 | 450.0 | 500.0 | 549.0 | 550.0 | 430€ | 500.0 | PLAUSIBEL |
| `iphone_15_pro_max_128gb` | iPhone 15 Pro Max (≤256GB) ⚠️ Okay | Okay | 72 | >=50: sehr gute Basis | 382.0 | 450.0 | 500.0 | 549.0 | 550.0 | 550€ | 549.0 | PLAUSIBEL |
| `iphone_15_pro_max_512gb` | iPhone 15 Pro Max (≥512GB) ★ Top-Deal | Top-Deal | 17 | 15-29: vorsichtig, manuell pruefen | 368.0 | 480.0 | 540.0 | 580.0 | 631.6 | 360€ | 480.0 | PLAUSIBEL |
| `iphone_15_pro_max_512gb` | iPhone 15 Pro Max (≥512GB) 👍 Guter Preis | Guter Preis | 17 | 15-29: vorsichtig, manuell pruefen | 368.0 | 480.0 | 540.0 | 580.0 | 631.6 | 505€ | 540.0 | PLAUSIBEL |
| `iphone_15_pro_max_512gb` | iPhone 15 Pro Max (≥512GB) ⚠️ Okay | Okay | 17 | 15-29: vorsichtig, manuell pruefen | 368.0 | 480.0 | 540.0 | 580.0 | 631.6 | 650€ | 580.0 | PLAUSIBEL |
| `iphone_16_128gb` | iPhone 16 (≤256GB) ★ Top-Deal | Top-Deal | 61 | >=50: sehr gute Basis | 300.0 | 399.0 | 450.0 | 490.0 | 500.0 | 275€ | 399.0 | ZU STRENG |
| `iphone_16_128gb` | iPhone 16 (≤256GB) 👍 Guter Preis | Guter Preis | 61 | >=50: sehr gute Basis | 300.0 | 399.0 | 450.0 | 490.0 | 500.0 | 390€ | 450.0 | PLAUSIBEL |
| `iphone_16_128gb` | iPhone 16 (≤256GB) ⚠️ Okay | Okay | 61 | >=50: sehr gute Basis | 300.0 | 399.0 | 450.0 | 490.0 | 500.0 | 500€ | 490.0 | PLAUSIBEL |
| `iphone_16_512gb` | iPhone 16 (≥512GB) ★ Top-Deal | Top-Deal | 1 | NICHT KALIBRIERBAR | 570.0 | 570.0 | 570.0 | 570.0 | 570.0 | 330€ | 570.0 | ZU STRENG |
| `iphone_16_512gb` | iPhone 16 (≥512GB) 👍 Guter Preis | Guter Preis | 1 | NICHT KALIBRIERBAR | 570.0 | 570.0 | 570.0 | 570.0 | 570.0 | 470€ | 570.0 | PLAUSIBEL |
| `iphone_16_512gb` | iPhone 16 (≥512GB) ⚠️ Okay | Okay | 1 | NICHT KALIBRIERBAR | 570.0 | 570.0 | 570.0 | 570.0 | 570.0 | 600€ | 570.0 | PLAUSIBEL |
| `iphone_16_plus_128gb` | iPhone 16 Plus (≤256GB) ★ Top-Deal | Top-Deal | 3 | NICHT KALIBRIERBAR | 404.0 | 440.0 | 500.0 | 515.0 | 524.0 | 290€ | 440.0 | ZU STRENG |
| `iphone_16_plus_128gb` | iPhone 16 Plus (≤256GB) 👍 Guter Preis | Guter Preis | 3 | NICHT KALIBRIERBAR | 404.0 | 440.0 | 500.0 | 515.0 | 524.0 | 415€ | 500.0 | PLAUSIBEL |
| `iphone_16_plus_128gb` | iPhone 16 Plus (≤256GB) ⚠️ Okay | Okay | 3 | NICHT KALIBRIERBAR | 404.0 | 440.0 | 500.0 | 515.0 | 524.0 | 530€ | 515.0 | PLAUSIBEL |
| `iphone_16_plus_512gb` | iPhone 16 Plus (≥512GB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 345€ | – | NICHT KALIBRIERBAR |
| `iphone_16_plus_512gb` | iPhone 16 Plus (≥512GB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 490€ | – | NICHT KALIBRIERBAR |
| `iphone_16_plus_512gb` | iPhone 16 Plus (≥512GB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 630€ | – | NICHT KALIBRIERBAR |
| `iphone_16_pro_128gb` | iPhone 16 Pro (≤256GB) ★ Top-Deal | Top-Deal | 79 | >=50: sehr gute Basis | 450.0 | 550.0 | 600.0 | 649.0 | 650.0 | 360€ | 550.0 | ZU STRENG |
| `iphone_16_pro_128gb` | iPhone 16 Pro (≤256GB) 👍 Guter Preis | Guter Preis | 79 | >=50: sehr gute Basis | 450.0 | 550.0 | 600.0 | 649.0 | 650.0 | 505€ | 600.0 | PLAUSIBEL |
| `iphone_16_pro_128gb` | iPhone 16 Pro (≤256GB) ⚠️ Okay | Okay | 79 | >=50: sehr gute Basis | 450.0 | 550.0 | 600.0 | 649.0 | 650.0 | 650€ | 649.0 | PLAUSIBEL |
| `iphone_16_pro_512gb` | iPhone 16 Pro (≥512GB) ★ Top-Deal | Top-Deal | 1 | NICHT KALIBRIERBAR | 750.0 | 750.0 | 750.0 | 750.0 | 750.0 | 415€ | 750.0 | ZU STRENG |
| `iphone_16_pro_512gb` | iPhone 16 Pro (≥512GB) 👍 Guter Preis | Guter Preis | 1 | NICHT KALIBRIERBAR | 750.0 | 750.0 | 750.0 | 750.0 | 750.0 | 585€ | 750.0 | PLAUSIBEL |
| `iphone_16_pro_512gb` | iPhone 16 Pro (≥512GB) ⚠️ Okay | Okay | 1 | NICHT KALIBRIERBAR | 750.0 | 750.0 | 750.0 | 750.0 | 750.0 | 750€ | 750.0 | PLAUSIBEL |
| `iphone_16_pro_max_128gb` | iPhone 16 Pro Max (≤256GB) ★ Top-Deal | Top-Deal | 70 | >=50: sehr gute Basis | 536.0 | 600.0 | 679.0 | 746.8 | 750.0 | 415€ | 600.0 | ZU STRENG |
| `iphone_16_pro_max_128gb` | iPhone 16 Pro Max (≤256GB) 👍 Guter Preis | Guter Preis | 70 | >=50: sehr gute Basis | 536.0 | 600.0 | 679.0 | 746.8 | 750.0 | 585€ | 679.0 | PLAUSIBEL |
| `iphone_16_pro_max_128gb` | iPhone 16 Pro Max (≤256GB) ⚠️ Okay | Okay | 70 | >=50: sehr gute Basis | 536.0 | 600.0 | 679.0 | 746.8 | 750.0 | 750€ | 746.8 | PLAUSIBEL |
| `iphone_16_pro_max_512gb` | iPhone 16 Pro Max (≥512GB) ★ Top-Deal | Top-Deal | 16 | 15-29: vorsichtig, manuell pruefen | 410.0 | 697.5 | 800.0 | 805.0 | 845.0 | 470€ | 697.5 | ZU STRENG |
| `iphone_16_pro_max_512gb` | iPhone 16 Pro Max (≥512GB) 👍 Guter Preis | Guter Preis | 16 | 15-29: vorsichtig, manuell pruefen | 410.0 | 697.5 | 800.0 | 805.0 | 845.0 | 665€ | 800.0 | PLAUSIBEL |
| `iphone_16_pro_max_512gb` | iPhone 16 Pro Max (≥512GB) ⚠️ Okay | Okay | 16 | 15-29: vorsichtig, manuell pruefen | 410.0 | 697.5 | 800.0 | 805.0 | 845.0 | 850€ | 805.0 | PLAUSIBEL |

### Kategorie: `lego_minifiguren` (lego_minifiguren.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `lego_cmf` | LEGO CMF / Sammelfigur ★ Top-Deal | Top-Deal | 175 | >=50: sehr gute Basis | 4.0 | 5.0 | 7.0 | 9.7 | 14.0 | 8€ | 5.0 | ZU HOCH |
| `lego_cmf` | LEGO CMF / Sammelfigur 👍 Guter Preis | Guter Preis | 175 | >=50: sehr gute Basis | 4.0 | 5.0 | 7.0 | 9.7 | 14.0 | 15€ | 7.0 | ZU HOCH |
| `lego_cmf` | LEGO CMF / Sammelfigur ⚠️ Interessant | Interessant | 175 | >=50: sehr gute Basis | 4.0 | 5.0 | 7.0 | 9.7 | 14.0 | 25€ | 9.7 | ZU HOCH |
| `lego_collector_generic` | LEGO Sammler-Minifigur ★ Top-Deal | Top-Deal | 5 | 5-14: nur Empfehlung | 9.4 | 10.0 | 15.0 | 22.9 | 26.6 | 10€ | 10.0 | PLAUSIBEL |
| `lego_collector_generic` | LEGO Sammler-Minifigur 👍 Guter Preis | Guter Preis | 5 | 5-14: nur Empfehlung | 9.4 | 10.0 | 15.0 | 22.9 | 26.6 | 20€ | 15.0 | ZU HOCH |
| `lego_collector_generic` | LEGO Sammler-Minifigur ⚠️ Interessant | Interessant | 5 | 5-14: nur Empfehlung | 9.4 | 10.0 | 15.0 | 22.9 | 26.6 | 35€ | 22.9 | ZU HOCH |
| `lego_fantasy_rare` | LEGO Harry Potter / LOTR – seltene Figur ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 15€ | – | NICHT KALIBRIERBAR |
| `lego_fantasy_rare` | LEGO Harry Potter / LOTR – seltene Figur 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 30€ | – | NICHT KALIBRIERBAR |
| `lego_fantasy_rare` | LEGO Harry Potter / LOTR – seltene Figur ⚠️ Interessant | Interessant | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 50€ | – | NICHT KALIBRIERBAR |
| `lego_minifig_bundle` | LEGO Minifiguren-Sammlung ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 15€ | – | NICHT KALIBRIERBAR |
| `lego_minifig_bundle` | LEGO Minifiguren-Sammlung 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 35€ | – | NICHT KALIBRIERBAR |
| `lego_minifig_bundle` | LEGO Minifiguren-Sammlung ⚠️ Interessant | Interessant | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 60€ | – | NICHT KALIBRIERBAR |
| `lego_ninjago_bundle` | LEGO Ninjago – Figuren-Konvolut ★ Top-Deal | Top-Deal | 537 | >=50: sehr gute Basis | 4.0 | 15.0 | 30.0 | 45.0 | 60.0 | 20€ | 15.0 | ZU HOCH |
| `lego_ninjago_bundle` | LEGO Ninjago – Figuren-Konvolut 👍 Guter Preis | Guter Preis | 537 | >=50: sehr gute Basis | 4.0 | 15.0 | 30.0 | 45.0 | 60.0 | 40€ | 30.0 | ZU HOCH |
| `lego_ninjago_bundle` | LEGO Ninjago – Figuren-Konvolut ⚠️ Interessant | Interessant | 537 | >=50: sehr gute Basis | 4.0 | 15.0 | 30.0 | 45.0 | 60.0 | 70€ | 45.0 | ZU HOCH |
| `lego_ninjago_rare` | LEGO Ninjago – seltene Figur ★ Top-Deal | Top-Deal | 5 | 5-14: nur Empfehlung | 4.6 | 7.0 | 7.0 | 10.0 | 13.6 | 10€ | 7.0 | ZU HOCH |
| `lego_ninjago_rare` | LEGO Ninjago – seltene Figur 👍 Guter Preis | Guter Preis | 5 | 5-14: nur Empfehlung | 4.6 | 7.0 | 7.0 | 10.0 | 13.6 | 20€ | 7.0 | ZU HOCH |
| `lego_ninjago_rare` | LEGO Ninjago – seltene Figur ⚠️ Interessant | Interessant | 5 | 5-14: nur Empfehlung | 4.6 | 7.0 | 7.0 | 10.0 | 13.6 | 35€ | 10.0 | ZU HOCH |
| `lego_promo` | LEGO Promo/Exclusive Minifigur ★ Top-Deal | Top-Deal | 16 | 15-29: vorsichtig, manuell pruefen | 6.3 | 11.6 | 15.7 | 21.2 | 32.8 | 15€ | 11.6 | PLAUSIBEL |
| `lego_promo` | LEGO Promo/Exclusive Minifigur 👍 Guter Preis | Guter Preis | 16 | 15-29: vorsichtig, manuell pruefen | 6.3 | 11.6 | 15.7 | 21.2 | 32.8 | 30€ | 15.7 | ZU HOCH |
| `lego_promo` | LEGO Promo/Exclusive Minifigur ⚠️ Interessant | Interessant | 16 | 15-29: vorsichtig, manuell pruefen | 6.3 | 11.6 | 15.7 | 21.2 | 32.8 | 50€ | 21.2 | ZU HOCH |
| `lego_retro_rare` | LEGO Classic Castle/Pirates/Space – selten ★ Top-Deal | Top-Deal | 5 | 5-14: nur Empfehlung | 9.9 | 10.0 | 14.0 | 15.0 | 23.4 | 15€ | 10.0 | ZU HOCH |
| `lego_retro_rare` | LEGO Classic Castle/Pirates/Space – selten 👍 Guter Preis | Guter Preis | 5 | 5-14: nur Empfehlung | 9.9 | 10.0 | 14.0 | 15.0 | 23.4 | 30€ | 14.0 | ZU HOCH |
| `lego_retro_rare` | LEGO Classic Castle/Pirates/Space – selten ⚠️ Interessant | Interessant | 5 | 5-14: nur Empfehlung | 9.9 | 10.0 | 14.0 | 15.0 | 23.4 | 50€ | 15.0 | ZU HOCH |
| `lego_superhero_rare` | LEGO Marvel/DC – seltene Minifigur ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 15€ | – | NICHT KALIBRIERBAR |
| `lego_superhero_rare` | LEGO Marvel/DC – seltene Minifigur 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 30€ | – | NICHT KALIBRIERBAR |
| `lego_superhero_rare` | LEGO Marvel/DC – seltene Minifigur ⚠️ Interessant | Interessant | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 50€ | – | NICHT KALIBRIERBAR |
| `lego_sw_clone` | LEGO Star Wars – Clone Wars ★ Top-Deal | Top-Deal | 424 | >=50: sehr gute Basis | 4.9 | 7.0 | 12.0 | 22.0 | 35.0 | 20€ | 7.0 | ZU HOCH |
| `lego_sw_clone` | LEGO Star Wars – Clone Wars 👍 Guter Preis | Guter Preis | 424 | >=50: sehr gute Basis | 4.9 | 7.0 | 12.0 | 22.0 | 35.0 | 35€ | 12.0 | ZU HOCH |
| `lego_sw_clone` | LEGO Star Wars – Clone Wars ⚠️ Interessant | Interessant | 424 | >=50: sehr gute Basis | 4.9 | 7.0 | 12.0 | 22.0 | 35.0 | 50€ | 22.0 | ZU HOCH |
| `lego_sw_rare` | LEGO Star Wars – seltene Figur ★ Top-Deal | Top-Deal | 103 | >=50: sehr gute Basis | 3.0 | 4.5 | 8.2 | 24.9 | 39.0 | 15€ | 4.5 | ZU HOCH |
| `lego_sw_rare` | LEGO Star Wars – seltene Figur 👍 Guter Preis | Guter Preis | 103 | >=50: sehr gute Basis | 3.0 | 4.5 | 8.2 | 24.9 | 39.0 | 30€ | 8.2 | ZU HOCH |
| `lego_sw_rare` | LEGO Star Wars – Darth Revan ★ Top-Deal | Top-Deal | 103 | >=50: sehr gute Basis | 3.0 | 4.5 | 8.2 | 24.9 | 39.0 | 40€ | 4.5 | ZU HOCH |
| `lego_sw_rare` | LEGO Star Wars – seltene Figur ⚠️ Interessant | Interessant | 103 | >=50: sehr gute Basis | 3.0 | 4.5 | 8.2 | 24.9 | 39.0 | 50€ | 24.9 | ZU HOCH |
| `lego_sw_rare` | LEGO Star Wars – Darth Revan 👍 Guter Preis | Guter Preis | 103 | >=50: sehr gute Basis | 3.0 | 4.5 | 8.2 | 24.9 | 39.0 | 60€ | 8.2 | ZU HOCH |
| `lego_sw_rare` | LEGO Star Wars – Darth Revan ⚠️ Interessant | Interessant | 103 | >=50: sehr gute Basis | 3.0 | 4.5 | 8.2 | 24.9 | 39.0 | 80€ | 24.9 | ZU HOCH |

### Kategorie: `macbook` (macbook.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `macbook_air_intel_1tb` | MacBook Air Intel (≥1TB) ★ Top-Deal | Top-Deal | 1 | NICHT KALIBRIERBAR | 380.0 | 380.0 | 380.0 | 380.0 | 380.0 | 220€ | 380.0 | ZU STRENG |
| `macbook_air_intel_1tb` | MacBook Air Intel (≥1TB) 👍 Guter Preis | Guter Preis | 1 | NICHT KALIBRIERBAR | 380.0 | 380.0 | 380.0 | 380.0 | 380.0 | 310€ | 380.0 | PLAUSIBEL |
| `macbook_air_intel_1tb` | MacBook Air Intel (≥1TB) ⚠️ Okay | Okay | 1 | NICHT KALIBRIERBAR | 380.0 | 380.0 | 380.0 | 380.0 | 380.0 | 400€ | 380.0 | PLAUSIBEL |
| `macbook_air_intel_512gb` | MacBook Air Intel (≤512GB) ★ Top-Deal | Top-Deal | 23 | 15-29: vorsichtig, manuell pruefen | 81.2 | 119.5 | 150.0 | 199.5 | 224.0 | 140€ | 119.5 | PLAUSIBEL |
| `macbook_air_intel_512gb` | MacBook Air Intel (≤512GB) 👍 Guter Preis | Guter Preis | 23 | 15-29: vorsichtig, manuell pruefen | 81.2 | 119.5 | 150.0 | 199.5 | 224.0 | 195€ | 150.0 | PLAUSIBEL |
| `macbook_air_intel_512gb` | MacBook Air Intel (≤512GB) ⚠️ Okay | Okay | 23 | 15-29: vorsichtig, manuell pruefen | 81.2 | 119.5 | 150.0 | 199.5 | 224.0 | 250€ | 199.5 | PLAUSIBEL |
| `macbook_air_m1_1tb` | MacBook Air M1 (≥1TB) ★ Top-Deal | Top-Deal | 4 | NICHT KALIBRIERBAR | 508.0 | 535.0 | 550.0 | 557.5 | 571.0 | 330€ | 535.0 | ZU STRENG |
| `macbook_air_m1_1tb` | MacBook Air M1 (≥1TB) 👍 Guter Preis | Guter Preis | 4 | NICHT KALIBRIERBAR | 508.0 | 535.0 | 550.0 | 557.5 | 571.0 | 470€ | 550.0 | PLAUSIBEL |
| `macbook_air_m1_1tb` | MacBook Air M1 (≥1TB) ⚠️ Okay | Okay | 4 | NICHT KALIBRIERBAR | 508.0 | 535.0 | 550.0 | 557.5 | 571.0 | 600€ | 557.5 | PLAUSIBEL |
| `macbook_air_m1_512gb` | MacBook Air M1 (≤512GB) ★ Top-Deal | Top-Deal | 49 | 30-49: gute Basis | 299.8 | 335.0 | 379.0 | 400.0 | 450.0 | 250€ | 335.0 | PLAUSIBEL |
| `macbook_air_m1_512gb` | MacBook Air M1 (≤512GB) 👍 Guter Preis | Guter Preis | 49 | 30-49: gute Basis | 299.8 | 335.0 | 379.0 | 400.0 | 450.0 | 350€ | 379.0 | PLAUSIBEL |
| `macbook_air_m1_512gb` | MacBook Air M1 (≤512GB) ⚠️ Okay | Okay | 49 | 30-49: gute Basis | 299.8 | 335.0 | 379.0 | 400.0 | 450.0 | 450€ | 400.0 | PLAUSIBEL |
| `macbook_air_m2_1tb` | MacBook Air M2 (≥1TB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 385€ | – | NICHT KALIBRIERBAR |
| `macbook_air_m2_1tb` | MacBook Air M2 (≥1TB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 545€ | – | NICHT KALIBRIERBAR |
| `macbook_air_m2_1tb` | MacBook Air M2 (≥1TB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 700€ | – | NICHT KALIBRIERBAR |
| `macbook_air_m2_512gb` | MacBook Air M2 (≤512GB) ★ Top-Deal | Top-Deal | 8 | 5-14: nur Empfehlung | 14.7 | 153.8 | 457.0 | 500.0 | 515.0 | 300€ | 153.8 | ZU HOCH |
| `macbook_air_m2_512gb` | MacBook Air M2 (≤512GB) 👍 Guter Preis | Guter Preis | 8 | 5-14: nur Empfehlung | 14.7 | 153.8 | 457.0 | 500.0 | 515.0 | 430€ | 457.0 | PLAUSIBEL |
| `macbook_air_m2_512gb` | MacBook Air M2 (≤512GB) ⚠️ Okay | Okay | 8 | 5-14: nur Empfehlung | 14.7 | 153.8 | 457.0 | 500.0 | 515.0 | 550€ | 500.0 | PLAUSIBEL |
| `macbook_air_m3_1tb` | MacBook Air M3 (≥1TB) ★ Top-Deal | Top-Deal | 1 | NICHT KALIBRIERBAR | 800.0 | 800.0 | 800.0 | 800.0 | 800.0 | 440€ | 800.0 | ZU STRENG |
| `macbook_air_m3_1tb` | MacBook Air M3 (≥1TB) 👍 Guter Preis | Guter Preis | 1 | NICHT KALIBRIERBAR | 800.0 | 800.0 | 800.0 | 800.0 | 800.0 | 625€ | 800.0 | PLAUSIBEL |
| `macbook_air_m3_1tb` | MacBook Air M3 (≥1TB) ⚠️ Okay | Okay | 1 | NICHT KALIBRIERBAR | 800.0 | 800.0 | 800.0 | 800.0 | 800.0 | 800€ | 800.0 | PLAUSIBEL |
| `macbook_air_m3_512gb` | MacBook Air M3 (≤512GB) ★ Top-Deal | Top-Deal | 10 | 5-14: nur Empfehlung | 494.1 | 522.5 | 614.4 | 641.2 | 650.0 | 360€ | 522.5 | ZU STRENG |
| `macbook_air_m3_512gb` | MacBook Air M3 (≤512GB) 👍 Guter Preis | Guter Preis | 10 | 5-14: nur Empfehlung | 494.1 | 522.5 | 614.4 | 641.2 | 650.0 | 505€ | 614.4 | PLAUSIBEL |
| `macbook_air_m3_512gb` | MacBook Air M3 (≤512GB) ⚠️ Okay | Okay | 10 | 5-14: nur Empfehlung | 494.1 | 522.5 | 614.4 | 641.2 | 650.0 | 650€ | 641.2 | PLAUSIBEL |
| `macbook_air_m4_1tb` | MacBook Air M4 (≥1TB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 495€ | – | NICHT KALIBRIERBAR |
| `macbook_air_m4_1tb` | MacBook Air M4 (≥1TB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 700€ | – | NICHT KALIBRIERBAR |
| `macbook_air_m4_1tb` | MacBook Air M4 (≥1TB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 900€ | – | NICHT KALIBRIERBAR |
| `macbook_air_m4_512gb` | MacBook Air M4 (≤512GB) ★ Top-Deal | Top-Deal | 16 | 15-29: vorsichtig, manuell pruefen | 709.0 | 726.8 | 750.0 | 750.0 | 750.0 | 415€ | 726.8 | ZU STRENG |
| `macbook_air_m4_512gb` | MacBook Air M4 (≤512GB) 👍 Guter Preis | Guter Preis | 16 | 15-29: vorsichtig, manuell pruefen | 709.0 | 726.8 | 750.0 | 750.0 | 750.0 | 585€ | 750.0 | PLAUSIBEL |
| `macbook_air_m4_512gb` | MacBook Air M4 (≤512GB) ⚠️ Okay | Okay | 16 | 15-29: vorsichtig, manuell pruefen | 709.0 | 726.8 | 750.0 | 750.0 | 750.0 | 750€ | 750.0 | PLAUSIBEL |
| `macbook_pro_intel_1tb` | MacBook Pro Intel (≥1TB) ★ Top-Deal | Top-Deal | 41 | 30-49: gute Basis | 260.0 | 325.0 | 440.0 | 499.0 | 549.0 | 300€ | 325.0 | PLAUSIBEL |
| `macbook_pro_intel_1tb` | MacBook Pro Intel (≥1TB) 👍 Guter Preis | Guter Preis | 41 | 30-49: gute Basis | 260.0 | 325.0 | 440.0 | 499.0 | 549.0 | 430€ | 440.0 | PLAUSIBEL |
| `macbook_pro_intel_1tb` | MacBook Pro Intel (≥1TB) ⚠️ Okay | Okay | 41 | 30-49: gute Basis | 260.0 | 325.0 | 440.0 | 499.0 | 549.0 | 550€ | 499.0 | PLAUSIBEL |
| `macbook_pro_intel_512gb` | MacBook Pro Intel (≤512GB) ★ Top-Deal | Top-Deal | 147 | >=50: sehr gute Basis | 150.0 | 190.0 | 250.0 | 349.0 | 385.0 | 220€ | 190.0 | PLAUSIBEL |
| `macbook_pro_intel_512gb` | MacBook Pro Intel (≤512GB) 👍 Guter Preis | Guter Preis | 147 | >=50: sehr gute Basis | 150.0 | 190.0 | 250.0 | 349.0 | 385.0 | 310€ | 250.0 | PLAUSIBEL |
| `macbook_pro_intel_512gb` | MacBook Pro Intel (≤512GB) ⚠️ Okay | Okay | 147 | >=50: sehr gute Basis | 150.0 | 190.0 | 250.0 | 349.0 | 385.0 | 400€ | 349.0 | PLAUSIBEL |
| `macbook_pro_m1_1tb` | MacBook Pro M1 (≥1TB) ★ Top-Deal | Top-Deal | 12 | 5-14: nur Empfehlung | 409.0 | 499.8 | 577.0 | 680.0 | 680.5 | 415€ | 499.8 | PLAUSIBEL |
| `macbook_pro_m1_1tb` | MacBook Pro M1 (≥1TB) 👍 Guter Preis | Guter Preis | 12 | 5-14: nur Empfehlung | 409.0 | 499.8 | 577.0 | 680.0 | 680.5 | 585€ | 577.0 | PLAUSIBEL |
| `macbook_pro_m1_1tb` | MacBook Pro M1 (≥1TB) ⚠️ Okay | Okay | 12 | 5-14: nur Empfehlung | 409.0 | 499.8 | 577.0 | 680.0 | 680.5 | 750€ | 680.0 | PLAUSIBEL |
| `macbook_pro_m1_512gb` | MacBook Pro M1 (≤512GB) ★ Top-Deal | Top-Deal | 33 | 30-49: gute Basis | 387.9 | 435.0 | 499.0 | 550.0 | 599.0 | 330€ | 435.0 | PLAUSIBEL |
| `macbook_pro_m1_512gb` | MacBook Pro M1 (≤512GB) 👍 Guter Preis | Guter Preis | 33 | 30-49: gute Basis | 387.9 | 435.0 | 499.0 | 550.0 | 599.0 | 470€ | 499.0 | PLAUSIBEL |
| `macbook_pro_m1_512gb` | MacBook Pro M1 (≤512GB) ⚠️ Okay | Okay | 33 | 30-49: gute Basis | 387.9 | 435.0 | 499.0 | 550.0 | 599.0 | 600€ | 550.0 | PLAUSIBEL |
| `macbook_pro_m2_1tb` | MacBook Pro M2 (≥1TB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 495€ | – | NICHT KALIBRIERBAR |
| `macbook_pro_m2_1tb` | MacBook Pro M2 (≥1TB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 700€ | – | NICHT KALIBRIERBAR |
| `macbook_pro_m2_1tb` | MacBook Pro M2 (≥1TB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 900€ | – | NICHT KALIBRIERBAR |
| `macbook_pro_m2_512gb` | MacBook Pro M2 (≤512GB) ★ Top-Deal | Top-Deal | 11 | 5-14: nur Empfehlung | 500.0 | 574.0 | 649.0 | 724.5 | 749.0 | 415€ | 574.0 | PLAUSIBEL |
| `macbook_pro_m2_512gb` | MacBook Pro M2 (≤512GB) 👍 Guter Preis | Guter Preis | 11 | 5-14: nur Empfehlung | 500.0 | 574.0 | 649.0 | 724.5 | 749.0 | 585€ | 649.0 | PLAUSIBEL |
| `macbook_pro_m2_512gb` | MacBook Pro M2 (≤512GB) ⚠️ Okay | Okay | 11 | 5-14: nur Empfehlung | 500.0 | 574.0 | 649.0 | 724.5 | 749.0 | 750€ | 724.5 | PLAUSIBEL |
| `macbook_pro_m3_1tb` | MacBook Pro M3 (≥1TB) ★ Top-Deal | Top-Deal | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 580€ | – | NICHT KALIBRIERBAR |
| `macbook_pro_m3_1tb` | MacBook Pro M3 (≥1TB) 👍 Guter Preis | Guter Preis | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 820€ | – | NICHT KALIBRIERBAR |
| `macbook_pro_m3_1tb` | MacBook Pro M3 (≥1TB) ⚠️ Okay | Okay | 0 | NICHT KALIBRIERBAR | – | – | – | – | – | 1050€ | – | NICHT KALIBRIERBAR |
| `macbook_pro_m3_512gb` | MacBook Pro M3 (≤512GB) ★ Top-Deal | Top-Deal | 2 | NICHT KALIBRIERBAR | 574.1 | 611.8 | 674.5 | 737.2 | 774.9 | 495€ | 611.8 | PLAUSIBEL |
| `macbook_pro_m3_512gb` | MacBook Pro M3 (≤512GB) 👍 Guter Preis | Guter Preis | 2 | NICHT KALIBRIERBAR | 574.1 | 611.8 | 674.5 | 737.2 | 774.9 | 700€ | 674.5 | PLAUSIBEL |
| `macbook_pro_m3_512gb` | MacBook Pro M3 (≤512GB) ⚠️ Okay | Okay | 2 | NICHT KALIBRIERBAR | 574.1 | 611.8 | 674.5 | 737.2 | 774.9 | 900€ | 737.2 | PLAUSIBEL |
| `macbook_pro_m4_1tb` | MacBook Pro M4 (≥1TB) ★ Top-Deal | Top-Deal | 2 | NICHT KALIBRIERBAR | 929.0 | 972.5 | 1045.0 | 1117.5 | 1161.0 | 690€ | 972.5 | PLAUSIBEL |
| `macbook_pro_m4_1tb` | MacBook Pro M4 (≥1TB) 👍 Guter Preis | Guter Preis | 2 | NICHT KALIBRIERBAR | 929.0 | 972.5 | 1045.0 | 1117.5 | 1161.0 | 975€ | 1045.0 | PLAUSIBEL |
| `macbook_pro_m4_1tb` | MacBook Pro M4 (≥1TB) ⚠️ Okay | Okay | 2 | NICHT KALIBRIERBAR | 929.0 | 972.5 | 1045.0 | 1117.5 | 1161.0 | 1250€ | 1117.5 | PLAUSIBEL |
| `macbook_pro_m4_512gb` | MacBook Pro M4 (≤512GB) ★ Top-Deal | Top-Deal | 4 | NICHT KALIBRIERBAR | 269.7 | 674.2 | 999.5 | 1100.0 | 1100.0 | 605€ | 674.2 | PLAUSIBEL |
| `macbook_pro_m4_512gb` | MacBook Pro M4 (≤512GB) 👍 Guter Preis | Guter Preis | 4 | NICHT KALIBRIERBAR | 269.7 | 674.2 | 999.5 | 1100.0 | 1100.0 | 860€ | 999.5 | PLAUSIBEL |
| `macbook_pro_m4_512gb` | MacBook Pro M4 (≤512GB) ⚠️ Okay | Okay | 4 | NICHT KALIBRIERBAR | 269.7 | 674.2 | 999.5 | 1100.0 | 1100.0 | 1100€ | 1100.0 | PLAUSIBEL |

### Kategorie: `monitor_curved` (monitor_curved.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `monitor_curved` | Curved Monitor ★ Top-Deal | Top-Deal | 643 | >=50: sehr gute Basis | 50.0 | 70.0 | 95.0 | 119.0 | 145.0 | 70€ | 70.0 | PLAUSIBEL |
| `monitor_curved` | Curved Monitor | Guter Preis | 643 | >=50: sehr gute Basis | 50.0 | 70.0 | 95.0 | 119.0 | 145.0 | 121€ | 95.0 | PLAUSIBEL |

### Kategorie: `netzteil` (netzteil.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `netzteil_550w` | ~550-649W Netzteil ★ Top-Deal | Top-Deal | 136 | >=50: sehr gute Basis | 13.0 | 18.0 | 22.0 | 26.2 | 35.0 | 13€ | 18.0 | PLAUSIBEL |
| `netzteil_550w` | ~550-649W Netzteil | Guter Preis | 136 | >=50: sehr gute Basis | 13.0 | 18.0 | 22.0 | 26.2 | 35.0 | 28€ | 22.0 | PLAUSIBEL |
| `netzteil_650w` | ~650-749W Netzteil ★ Top-Deal | Top-Deal | 87 | >=50: sehr gute Basis | 21.2 | 29.0 | 30.0 | 35.0 | 46.5 | 20€ | 29.0 | ZU STRENG |
| `netzteil_650w` | ~650-749W Netzteil | Guter Preis | 87 | >=50: sehr gute Basis | 21.2 | 29.0 | 30.0 | 35.0 | 46.5 | 38€ | 30.0 | PLAUSIBEL |
| `netzteil_750w_plus` | 750W+ Netzteil ★ Top-Deal | Top-Deal | 141 | >=50: sehr gute Basis | 25.0 | 32.0 | 45.0 | 50.0 | 59.0 | 30€ | 32.0 | PLAUSIBEL |
| `netzteil_750w_plus` | 750W+ Netzteil | Guter Preis | 141 | >=50: sehr gute Basis | 25.0 | 32.0 | 45.0 | 50.0 | 59.0 | 50€ | 45.0 | PLAUSIBEL |

### Kategorie: `notebook_resell` (notebook_resell.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `gaming_laptop_rtx3060` | Gaming Laptop (RTX 3060) ★ Resell-Top | Top-Deal | 4 | NICHT KALIBRIERBAR | 293.0 | 297.5 | 307.5 | 323.5 | 338.8 | 400€ | 297.5 | ZU HOCH |
| `gaming_laptop_rtx3060` | Gaming Laptop (RTX 3060) | Guter Preis | 4 | NICHT KALIBRIERBAR | 293.0 | 297.5 | 307.5 | 323.5 | 338.8 | 490€ | 307.5 | ZU HOCH |
| `gaming_laptop_rtx4060` | Gaming Laptop (RTX 4060) ★ Resell-Top | Top-Deal | 1 | NICHT KALIBRIERBAR | 550.0 | 550.0 | 550.0 | 550.0 | 550.0 | 550€ | 550.0 | PLAUSIBEL |
| `thinkpad_modern` | ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top | Top-Deal | 117 | >=50: sehr gute Basis | 28.0 | 100.0 | 185.0 | 209.0 | 226.6 | 180€ | 100.0 | ZU HOCH |
| `thinkpad_modern` | ThinkPad T14/X13 (Ryzen/Modern) | Guter Preis | 117 | >=50: sehr gute Basis | 28.0 | 100.0 | 185.0 | 209.0 | 226.6 | 240€ | 185.0 | PLAUSIBEL |

### Kategorie: `office_pc` (office_pc.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `office_pc` | Office-PC (Mindestanforderung erfüllt) | Okay | 226 | >=50: sehr gute Basis | 130.0 | 170.0 | 239.0 | 270.0 | 299.0 | 300€ | 270.0 | PLAUSIBEL |

### Kategorie: `ram` (ram.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ram_ddr4_16gb` | 16GB DDR4 RAM ★ Top-Deal | Top-Deal | 54 | >=50: sehr gute Basis | 31.5 | 40.5 | 49.9 | 50.0 | 55.0 | 35€ | 40.5 | PLAUSIBEL |
| `ram_ddr4_16gb` | 16GB DDR4 RAM | Guter Preis | 54 | >=50: sehr gute Basis | 31.5 | 40.5 | 49.9 | 50.0 | 55.0 | 55€ | 49.9 | PLAUSIBEL |
| `ram_ddr4_32gb` | 32GB DDR4 RAM ★ Top-Deal | Top-Deal | 12 | 5-14: nur Empfehlung | 65.3 | 69.5 | 82.5 | 95.2 | 99.9 | 70€ | 69.5 | PLAUSIBEL |
| `ram_ddr4_32gb` | 32GB DDR4 RAM | Guter Preis | 12 | 5-14: nur Empfehlung | 65.3 | 69.5 | 82.5 | 95.2 | 99.9 | 110€ | 82.5 | ZU HOCH |
| `ram_ddr4_8gb` | 8GB DDR4 RAM ★ Top-Deal | Top-Deal | 29 | 15-29: vorsichtig, manuell pruefen | 14.1 | 18.0 | 20.0 | 20.1 | 21.8 | 15€ | 18.0 | PLAUSIBEL |
| `ram_ddr4_8gb` | 8GB DDR4 RAM | Guter Preis | 29 | 15-29: vorsichtig, manuell pruefen | 14.1 | 18.0 | 20.0 | 20.1 | 21.8 | 22€ | 20.0 | PLAUSIBEL |

### Kategorie: `retro_konsolen` (retro_konsolen.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `nintendo_retro_konsole` | Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal | Top-Deal | 542 | >=50: sehr gute Basis | 14.9 | 25.0 | 49.0 | 70.0 | 90.0 | 40€ | 25.0 | ZU HOCH |
| `nintendo_retro_konsole` | Nintendo Retro-Konsole (N64/GameCube/DS) 👍 Guter Preis | Guter Preis | 542 | >=50: sehr gute Basis | 14.9 | 25.0 | 49.0 | 70.0 | 90.0 | 70€ | 49.0 | ZU HOCH |
| `nintendo_retro_konsole` | Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay | Okay | 542 | >=50: sehr gute Basis | 14.9 | 25.0 | 49.0 | 70.0 | 90.0 | 100€ | 70.0 | ZU HOCH |
| `retro_konvolut` | Retro-Konsolen-Konvolut ★ Top-Deal | Top-Deal | 33 | 30-49: gute Basis | 21.0 | 39.9 | 89.9 | 109.9 | 114.0 | 24€ | 39.9 | ZU STRENG |
| `retro_konvolut` | Retro-Konsolen-Konvolut 👍 Guter Preis | Guter Preis | 33 | 30-49: gute Basis | 21.0 | 39.9 | 89.9 | 109.9 | 114.0 | 79€ | 89.9 | PLAUSIBEL |
| `retro_konvolut` | Retro-Konsolen-Konvolut ⚠️ Okay | Okay | 33 | 30-49: gute Basis | 21.0 | 39.9 | 89.9 | 109.9 | 114.0 | 117€ | 109.9 | PLAUSIBEL |
| `sony_retro_konsole` | Sony Retro-Konsole (PS1/PS2) ★ Top-Deal | Top-Deal | 533 | >=50: sehr gute Basis | 10.0 | 20.0 | 40.0 | 60.0 | 79.0 | 35€ | 20.0 | ZU HOCH |
| `sony_retro_konsole` | Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis | Guter Preis | 533 | >=50: sehr gute Basis | 10.0 | 20.0 | 40.0 | 60.0 | 79.0 | 60€ | 40.0 | ZU HOCH |
| `sony_retro_konsole` | Sony Retro-Konsole (PS1/PS2) ⚠️ Okay | Okay | 533 | >=50: sehr gute Basis | 10.0 | 20.0 | 40.0 | 60.0 | 79.0 | 90€ | 60.0 | ZU HOCH |

### Kategorie: `sata_ssd` (sata_ssd.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `sata_ssd_128gb` | ~128GB SATA SSD ★ Top-Deal | Top-Deal | 57 | >=50: sehr gute Basis | 10.0 | 12.0 | 15.0 | 17.0 | 22.4 | 10€ | 12.0 | PLAUSIBEL |
| `sata_ssd_128gb` | ~128GB SATA SSD | Guter Preis | 57 | >=50: sehr gute Basis | 10.0 | 12.0 | 15.0 | 17.0 | 22.4 | 17€ | 15.0 | PLAUSIBEL |
| `sata_ssd_1tb` | ~1TB SATA SSD ★ Top-Deal | Top-Deal | 88 | >=50: sehr gute Basis | 50.0 | 68.0 | 79.0 | 85.8 | 99.0 | 69€ | 68.0 | PLAUSIBEL |
| `sata_ssd_1tb` | ~1TB SATA SSD | Guter Preis | 88 | >=50: sehr gute Basis | 50.0 | 68.0 | 79.0 | 85.8 | 99.0 | 89€ | 79.0 | PLAUSIBEL |
| `sata_ssd_250gb` | ~250GB SATA SSD ★ Top-Deal | Top-Deal | 124 | >=50: sehr gute Basis | 16.0 | 20.0 | 25.0 | 30.0 | 30.6 | 25€ | 20.0 | PLAUSIBEL |
| `sata_ssd_250gb` | ~250GB SATA SSD | Guter Preis | 124 | >=50: sehr gute Basis | 16.0 | 20.0 | 25.0 | 30.0 | 30.6 | 32€ | 25.0 | PLAUSIBEL |
| `sata_ssd_2tb` | ~2TB SATA SSD ★ Top-Deal | Top-Deal | 62 | >=50: sehr gute Basis | 114.1 | 125.4 | 150.0 | 180.0 | 192.3 | 115€ | 125.4 | PLAUSIBEL |
| `sata_ssd_2tb` | ~2TB SATA SSD | Guter Preis | 62 | >=50: sehr gute Basis | 114.1 | 125.4 | 150.0 | 180.0 | 192.3 | 155€ | 150.0 | PLAUSIBEL |
| `sata_ssd_500gb` | ~500GB SATA SSD ★ Top-Deal | Top-Deal | 109 | >=50: sehr gute Basis | 28.8 | 36.0 | 45.0 | 50.0 | 55.0 | 40€ | 36.0 | PLAUSIBEL |
| `sata_ssd_500gb` | ~500GB SATA SSD | Guter Preis | 109 | >=50: sehr gute Basis | 28.8 | 36.0 | 45.0 | 50.0 | 55.0 | 56€ | 45.0 | PLAUSIBEL |

### Kategorie: `vintage_elektronik` (vintage_elektronik.yaml)

| Modell | Regel | Rating | Samples | Klassifikation | P10 | P25 | Median | P75 | P90 | Aktuell | Empfohlen | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `crt_profi_monitor` | Profi-CRT-Monitor (Sony PVM/BVM/Trinitron) ★ Top-Deal | Top-Deal | 77 | >=50: sehr gute Basis | 8.0 | 49.0 | 99.0 | 199.0 | 249.0 | 80€ | 49.0 | ZU HOCH |
| `crt_profi_monitor` | Profi-CRT-Monitor (Sony PVM/BVM/Trinitron) 👍 Guter Preis | Guter Preis | 77 | >=50: sehr gute Basis | 8.0 | 49.0 | 99.0 | 199.0 | 249.0 | 150€ | 99.0 | ZU HOCH |
| `crt_profi_monitor` | Profi-CRT-Monitor (Sony PVM/BVM/Trinitron) ⚠️ Okay | Okay | 77 | >=50: sehr gute Basis | 8.0 | 49.0 | 99.0 | 199.0 | 249.0 | 250€ | 199.0 | PLAUSIBEL |
| `roehrenfernseher` | Röhrenfernseher ★ Top-Deal | Top-Deal | 68 | >=50: sehr gute Basis | 5.0 | 9.9 | 20.0 | 29.0 | 39.0 | 10€ | 9.9 | PLAUSIBEL |
| `roehrenfernseher` | Röhrenfernseher 👍 Guter Preis | Guter Preis | 68 | >=50: sehr gute Basis | 5.0 | 9.9 | 20.0 | 29.0 | 39.0 | 25€ | 20.0 | PLAUSIBEL |
| `roehrenfernseher` | Röhrenfernseher ⚠️ Okay | Okay | 68 | >=50: sehr gute Basis | 5.0 | 9.9 | 20.0 | 29.0 | 39.0 | 45€ | 29.0 | ZU HOCH |
| `vintage_hifi_verstaerker` | Vintage-HiFi-Verstärker (Markenware) ★ Top-Deal | Top-Deal | 326 | >=50: sehr gute Basis | 45.0 | 65.2 | 99.0 | 129.7 | 175.0 | 60€ | 65.2 | PLAUSIBEL |
| `vintage_hifi_verstaerker` | Vintage-HiFi-Verstärker (Markenware) 👍 Guter Preis | Guter Preis | 326 | >=50: sehr gute Basis | 45.0 | 65.2 | 99.0 | 129.7 | 175.0 | 120€ | 99.0 | PLAUSIBEL |
| `vintage_hifi_verstaerker` | Vintage-HiFi-Verstärker (Markenware) ⚠️ Okay | Okay | 326 | >=50: sehr gute Basis | 45.0 | 65.2 | 99.0 | 129.7 | 175.0 | 200€ | 129.7 | ZU HOCH |

---

## Zusammenfassung nach den 8 angeforderten Punkten

1. **Analysierte Preisregeln insgesamt:** 310 Regeln über 113 verschiedene
   `price_history_model`-Werte in 14 Kategorien.
2. **Regeln mit ausreichenden Daten (≥15 Samples):** **169 von 310** (54,5 %).
3. **Regeln, die kalibriert werden sollten** (≥15 Samples UND Abweichung
   >30 %): **41** (13 ZU STRENG + 28 ZU HOCH) — Detailtabelle oben.
4. **Grenzen, die zu niedrig wirken:** 13 Regeln, u.a. systematisch die
   gesamte iPhone-15/16-Serie (siehe Muster oben), `netzteil_650w`
   Top-Deal, `macbook_air_m4_512gb` Top-Deal, `retro_konvolut` Top-Deal.
5. **Grenzen, die zu hoch wirken:** 28 Regeln, u.a. systematisch fast die
   gesamte `lego_minifiguren`-Kategorie, beide Retro-Konsolen-Modelle,
   `crt_profi_monitor`, `thinkpad_modern`, `vintage_hifi_verstaerker`.
6. **Regeln mit zu wenig Daten:** 141 (95 mit <5 Samples/NICHT
   KALIBRIERBAR, 46 mit 5-14 Samples/nur Empfehlung).
7. **Besonders auffällige Kategorien:**
   - `lego_sw_rare` (geteilter Schlüssel zweier unterschiedlicher Produkte,
     jetzt mit echten Daten bestätigt — siehe eigener Abschnitt oben)
   - `iphone` (systematisch zu niedrige Top-Deal-Grenzen bei 15/16-Serie)
   - `lego_minifiguren` (systematisch zu hohe Grenzen, fast durchgängig)
   - `retro_konsolen` (beide Modelle zu hoch, sehr große Datenbasis)
   - **Verwaiste Preishistorie-Daten ohne aktuelle Regel:** `lego_bundle`
     (404 Samples!), `playmobil_bundle` (210 Samples), `spielzeug_bundle_
     sonstige` (49 Samples) — insgesamt 663 Datenpunkte aus einer
     offenbar früheren Kategorie-Struktur, die aktuell von keiner Regel
     mehr abgedeckt wird. Kein Kalibrierungsthema, aber erwähnenswert.
   - `cpu_mainboard_bundle`: weiterhin 0 Samples für alle drei Combos —
     bestätigt Phase-11-Befund, die Re-Evaluierungs-Logik konnte in den
     ~2 Wochen Datenzeitraum noch keine neuen Treffer erzeugen (oder die
     Regeln sind seit dem Phase-11-Fix noch nicht erneut gescannt worden).
8. **Vollständiger Pfad zum Report:** `/home/claude/repo/PRICE_CALIBRATION_REPORT.md`
   (im Sandbox-Klon; Datei zusätzlich zum Download bereitgestellt).

**Testanzahl/-ergebnis:** Keine Code-/YAML-Änderung in diesem Schritt —
reine Analyse. Letzter bekannter Teststand: **797 passed, 0 failed**
(unverändert, da kein Code angefasst wurde).

---

## Nächster Schritt

Wie in deinem Auftrag festgelegt: **noch keine automatischen
YAML-Änderungen.** Sobald du diesen Report geprüft hast, entscheiden wir
gemeinsam, welche der 41 konkret vorgeschlagenen Kalibrierungen (13 zu
niedrig, 28 zu hoch) tatsächlich umgesetzt werden — vermutlich sinnvoll
gruppiert nach den identifizierten Mustern (iPhone-15/16-Serie als Block,
LEGO-Minifiguren als Block, Retro-Konsolen als Block) statt Regel für
Regel einzeln.
