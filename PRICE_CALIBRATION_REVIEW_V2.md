# Kalibrierungs-Review V2 (Phase 12, Schritt 3) — nach Matching-Fixes

**Stand:** 2026-08-09 · **Status:** Matching-Fixes umgesetzt, Tests grün.
**Noch immer KEINE Preisgrenzen-Änderung.**

---

## Methodik dieser Simulation (wichtige Einschränkung)

Da in dieser Sandbox kein echter Live-Scan möglich ist, habe ich **jeden
bereits vorhandenen Preishistorie-Punkt der sechs betroffenen Modelle
erneut durch den jetzt reparierten Matcher laufen lassen** (über den
gespeicherten `fingerprint`, alle 6 Modelle: 100% Abdeckung, kein Punkt
ohne Fingerprint). Das zeigt zuverlässig, **welche der bisherigen
Datenpunkte nach dem Fix weiterhin gültig wären** — ist aber **keine
neue Datensammlung**. Echte neue Angebote, die durch die Fixes jetzt
NEU erkannt werden könnten (z.B. weil `thinkpad_modern` jetzt strenger
filtert, aber dafür bei anderen Kategorien evtl. mehr Vertrauen
verdient), zeigen sich erst nach künftigen echten Scans.

`price_history.jsonl` wurde **nicht verändert** — diese Simulation ist
rein lesend.

---

## Ergebnis auf einen Blick: teils dramatische Bestätigung der bisherigen Grenzen

| Modell | Punkte vorher | Ausgeschlossen | Verbleibend | Neue Confidence |
|---|---|---|---|---|
| `lego_sw_rare` | 104 | 90 (87%) | 14 | MEDIUM |
| `crt_profi_monitor` | 78 | 18 (23%) | 60 | HIGH |
| `roehrenfernseher` | 68 | 64 (94%) | 4 | LOW (nicht kalibrierbar) |
| `thinkpad_modern` | 118 | 39 (33%) | 79 | HIGH |
| `nintendo_retro_konsole` | 547 | 238 (44%) | 309 | HIGH |
| `sony_retro_konsole` | 537 | 218 (41%) | 319 | HIGH |

**Wichtigster Befund:** Bei **zwei Modellen (`crt_profi_monitor`,
`thinkpad_modern`) kehrt sich die ursprüngliche "ZU HOCH"-Einstufung aus
Report 1 nahezu vollständig um**, sobald die Fehltreffer entfernt werden
— die aktuellen Grenzen waren die ganze Zeit über plausibel, nur die
kontaminierte Datenbasis hatte das verschleiert.

---

## Detailauswertung je Modell

### `lego_sw_rare` — jetzt MEDIUM-Confidence (vorher fälschlich HIGH mit falschen Daten)
| | P10 | P25 | Median | P75 | P90 |
|---|---|---|---|---|---|
| **Neu (bereinigt, n=14)** | 3,89€ | 7,17€ | 14,95€ | 24,25€ | 38,47€ |
| Alt (kontaminiert, n=103) | — | 4,50€ | 8,20€ | 24,90€ | — |

Mit n=14 liegt die Kategorie an der Grenze zwischen "5-14: nur
Empfehlung" und "15-29: vorsichtige Kalibrierung" — **noch keine robuste
Empfehlung möglich**, aber die neue P25 (7,17€) liegt deutlich näher an
der aktuellen Top-Deal-Grenze (15€) als der alte, kontaminierte Wert
(4,50€). Die "ZU HOCH"-Einstufung bleibt tendenziell bestehen, aber
deutlich schwächer als ursprünglich berechnet. **Empfehlung: weitere
Datensammlung abwarten, dann neu bewerten.**

### `crt_profi_monitor` — Umkehrung: Grenze war plausibel, nicht zu hoch
| | P10 | P25 | Median | P75 | P90 |
|---|---|---|---|---|---|
| **Neu (bereinigt, n=60)** | 48,67€ | 76,75€ | 149,50€ | 219,93€ | 249,10€ |
| Alt (kontaminiert, n=77) | — | 49,00€ | 99,00€ | — | — |

**Auffällig:** die neue Median (149,50€) liegt fast exakt auf der
aktuellen Guter-Preis-Grenze (150€), die neue P25 (76,75€) liegt fast
exakt auf der aktuellen Top-Deal-Grenze (80€). Die im ersten Report
vorgeschlagene Kalibrierung ("ZU HOCH", empfohlen 49€/99€) war ein
**Artefakt der Werbeanzeigen-Kontamination** — nach Bereinigung sehen
die bestehenden Grenzen **plausibel** aus. **Empfehlung: NICHT ändern.**

### `roehrenfernseher` — nicht mehr kalibrierbar
Von 68 Punkten bleiben nach Bereinigung nur noch **4** übrig — weit
unter der 5-Sample-Schwelle. Die Kategorie ist aktuell **NICHT
KALIBRIERBAR**. Interessant: die vier verbleibenden echten Datenpunkte
liegen bei 10-40€ (P75=31,73€), das ist NICHT dramatisch von der
aktuellen Okay-Grenze (45€) entfernt — aber die Stichprobe ist zu klein
für jede belastbare Aussage. **Empfehlung: mehr Daten sammeln, aktuelle
Grenzen vorerst unverändert lassen.**

### `thinkpad_modern` — Umkehrung: Grenze war plausibel, nicht zu hoch
| | P10 | P25 | Median | P75 | P90 |
|---|---|---|---|---|---|
| **Neu (bereinigt, n=79)** | 142,99€ | 178,39€ | 199,00€ | 214,50€ | 229,99€ |
| Alt (kontaminiert, n=117) | — | 100,00€ | — | — | — |

Die neue P25 (178,39€) liegt praktisch exakt auf der aktuellen
Top-Deal-Grenze (180€) — die ursprüngliche "ZU HOCH"-Einstufung (empfohlen
100€) war fast ausschließlich ein Artefakt der Ersatzteil-Kontamination
(33% der alten Stichprobe waren Einzelteile, die die Statistik massiv
nach unten gezogen haben). **Empfehlung: NICHT ändern**, aktuelle Grenze
(180€/240€) erscheint nach Bereinigung gut getroffen.

### `nintendo_retro_konsole` — Signal bleibt, aber deutlich schwächer
| | P10 | P25 | Median | P75 | P90 |
|---|---|---|---|---|---|
| **Neu (bereinigt, n=309)** | 17,99€ | 30,00€ | 55,00€ | 79,99€ | 92,92€ |
| Alt (kontaminiert, n=542) | — | 25,00€ | 49,00€ | 70,00€ | — |

Auch nach Bereinigung bleibt die aktuelle Top-Deal-Grenze (40€) spürbar
über der bereinigten P25 (30€) — das "ZU HOCH"-Signal ist real,
wenn auch schwächer als der ursprüngliche, kontaminierte Befund nahelegte.
**Empfehlung: moderate Anpassung in Betracht ziehen (Phase 4), aber mit
kleinerem Abstand als ursprünglich berechnet.**

### `sony_retro_konsole` — Signal bleibt, aber deutlich schwächer
| | P10 | P25 | Median | P75 | P90 |
|---|---|---|---|---|---|
| **Neu (bereinigt, n=319)** | 18,00€ | 30,00€ | 50,00€ | 69,99€ | 80,00€ |
| Alt (kontaminiert, n=533) | — | 20,00€ | 40,00€ | 60,00€ | — |

Gleiches Muster wie Nintendo: aktuelle Top-Deal-Grenze (35€) liegt nahe,
aber noch etwas über der bereinigten P25 (30€) — deutlich schwächeres
Signal als ursprünglich. **Empfehlung: moderate Anpassung in Betracht
ziehen (Phase 4), aber mit kleinerem Abstand als ursprünglich
berechnet.**

---

## Aktualisierte Klassifikation (ersetzt die Einträge dieser 6 Modelle aus PRICE_CALIBRATION_REVIEW.md)

| Modell | Alte Klassifikation | Neue Klassifikation | Begründung |
|---|---|---|---|
| `lego_sw_rare` | ZUERST MATCHING-FIX | ZU WENIGE DATEN | Fix umgesetzt, aber nur n=14 verbleibend |
| `crt_profi_monitor` | ZUERST MATCHING-FIX | **NICHT ÄNDERN** | Fix umgesetzt, bereinigte Daten bestätigen aktuelle Grenze |
| `roehrenfernseher` | ZUERST MATCHING-FIX | ZU WENIGE DATEN | Fix umgesetzt, nur n=4 verbleibend |
| `thinkpad_modern` | ZUERST MATCHING-FIX | **NICHT ÄNDERN** | Fix umgesetzt, bereinigte Daten bestätigen aktuelle Grenze |
| `nintendo_retro_konsole` | ZUERST MATCHING-FIX | MANUELLE PRÜFUNG | Fix umgesetzt, Signal bleibt aber schwächer |
| `sony_retro_konsole` | ZUERST MATCHING-FIX | MANUELLE PRÜFUNG | Fix umgesetzt, Signal bleibt aber schwächer |

---

## Geänderte Regeln (Übersicht)

| Datei | Modell | Art des Fixes |
|---|---|---|
| `rules/lego_minifiguren.yaml` | `lego_sw_rare` | `require_all_of`-Struktur repariert: `["lego","star wars"]` (1 Gruppe = ODER) → `["lego"], ["star wars"]` (2 Gruppen = UND), 6 Regeln betroffen (Darth Revan ×3, seltene Figur ×3) |
| `rules/vintage_elektronik.yaml` | `crt_profi_monitor` | Neue Excludes: "werbung", "reklame", "advert", "anleitung", "bedienungsanleitung" (3 Regeln) |
| `rules/vintage_elektronik.yaml` | `roehrenfernseher` | Neue Excludes: "ersatzteil", "anleitung", "bedienungsanleitung", "schaltplan", "fernbedienung", "netzschalter", "widerstand" (3 Regeln) |
| `rules/notebook_resell.yaml` | `thinkpad_modern` | Neue dritte `require_all_of`-Gruppe: RAM-/Speicher-Größenangabe (4-512GB, 1TB, 2TB, SSD, NVMe) erforderlich (2 Regeln) |
| — | `nintendo_retro_konsole`, `sony_retro_konsole` | **Keine Änderung nötig** — bereits durch einen früheren, im Regelwerk dokumentierten Fix ("NACHTRAG", `retro_konsolen.yaml`) behoben. Per Test verifiziert. |

**Keine Preisgrenzen geändert. Keine Top-Deal-/Deal-Score-/Flip-/Notification-Logik verändert. Keine Löschung/Manipulation von `price_history.jsonl`/`seen.json`/`found.json`.**

---

## Wichtiger Nebenbefund: derselbe Bug existiert vermutlich anderswo

Die zwei ursprünglich `lego_sw_rare` kontaminierenden Titel ("LEGO Ninjago
Limited Edition..." und "LEGO Nexo Knights Limited Edition...") matchen
nach dem Fix jetzt stattdessen auf **`lego_ninjago_rare`** — eine
Nachbar-Regel mit demselben strukturellen Muster (`["lego","ninjago"]`
als eine Gruppe). Das bestätigt: der Bug ist **nicht isoliert**, sondern
ein wiederkehrendes Strukturmuster in `lego_minifiguren.yaml` (mindestens
auch bei den Clone-Wars- und Ninjago-Regeln, insgesamt ca. 21 weitere
betroffene Regeln). **Bewusst nicht in diesem Schritt korrigiert** (nur
`lego_sw_rare` war beauftragt) — empfohlen als eigener Folge-Schritt.

---

## Erwartete Auswirkungen auf zukünftige Price-History-Daten

- **`lego_sw_rare`**: künftige Datenpunkte werden ausschließlich echte
  Star-Wars-Minifiguren betreffen — die Kategorie wird langsamer wachsen
  (weniger, aber korrekte Treffer), dafür wird die Statistik ab jetzt
  belastbar.
- **`crt_profi_monitor`/`roehrenfernseher`**: weniger, aber sauberere
  Treffer. `roehrenfernseher` wird vorübergehend sehr wenige neue Punkte
  liefern (94% des bisherigen "Volumens" waren Fehltreffer) — Kalibrierung
  frühestens in einigen Wochen sinnvoll möglich.
- **`thinkpad_modern`**: die RAM-/Speicher-Anforderung filtert
  Einzelteil-Angebote zuverlässig heraus — künftige Statistik wird sich
  näher an den bereits jetzt beobachteten bereinigten Werten bewegen.
- **`nintendo_retro_konsole`/`sony_retro_konsole`**: keine Änderung nötig,
  Datenqualität bereits gut (Fix war schon aktiv).

---

## Testanzahl und Ergebnis

- 23 neue Tests in `app/tests/test_matcher_price_calibration_matching_fixes.py`
  (je 3-6 Tests pro Kategorie: Junk wird jetzt korrekt abgelehnt, echte
  Angebote matchen weiterhin, inkl. Regressionsschutz für den bereits
  vorher gefixten Nintendo-/Sony-Fall).
- **826 passed, 0 failed** (Gesamt-Suite, vorher 797 + 23 neue + einige
  bereits vorhandene, die durch parallele Weiterentwicklung des Repos
  hinzugekommen waren).
- Keine bestehenden Tests gelöscht oder abgeschwächt.

---

## Nächster Schritt

Wie vereinbart: **noch keine Preisgrenzen geändert.** Basierend auf
dieser aktualisierten Klassifikation:
- **2 Modelle (`crt_profi_monitor`, `thinkpad_modern`) brauchen
  vermutlich GAR KEINE Preisänderung** — bereits gut kalibriert.
- **2 Modelle (`lego_sw_rare`, `roehrenfernseher`) brauchen mehr
  gesammelte (jetzt saubere) Daten**, bevor überhaupt kalibriert werden
  kann.
- **2 Modelle (`nintendo_retro_konsole`, `sony_retro_konsole`) zeigen
  weiterhin ein (schwächeres) "zu hoch"-Signal** — Kandidaten für eine
  moderate, manuell geprüfte Anpassung in einem späteren Schritt.

Damit reduziert sich die eigentliche Preisgrenzen-Kalibrierung
voraussichtlich auf deutlich weniger Fälle als ursprünglich in Report 1
vermutet.
