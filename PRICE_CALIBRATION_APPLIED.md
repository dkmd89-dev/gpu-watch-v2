# Umgesetzte Preisgrenzen-Kalibrierung (Phase 12, Schritt 5)

**Stand:** 2026-08-09 · **Status:** Umgesetzt, Tests grün.

---

## Vorgehen

Ausschließlich Regeln übernommen, die in `PRICE_CALIBRATION_REVIEW.md`
eindeutig als **ÄNDERN** klassifiziert waren (Kategorie C) — **12 Regeln
über 10 Modelle**. Alle als NICHT ÄNDERN, ZU WENIGE DATEN, MANUELLE
PRÜFUNG oder ZUERST MATCHING-FIX eingestuften Regeln blieben
unverändert, inklusive der in `PRICE_CALIBRATION_REVIEW_V2.md`
aktualisierten Einstufungen (`crt_profi_monitor`/`thinkpad_modern`:
NICHT ÄNDERN; `lego_sw_rare`/`roehrenfernseher`: ZU WENIGE DATEN;
`nintendo_retro_konsole`/`sony_retro_konsole`: MANUELLE PRÜFUNG).

**Werte:** tier-differenziert aus dem Review übernommen — Top-Deal → P25,
Guter Preis → Median, Interessant → P75 (keine pauschale
"Median = max_price"-Formel). Zahlen leicht aktualisiert gegenüber dem
ursprünglichen Report, da `price_history.jsonl` zwischenzeitlich um
wenige weitere reale Datenpunkte gewachsen ist (9.161 → 9.247) — die
Abweichungen sind marginal (z.B. iPhone 15 P25: 312€ → 310,5€).

---

## Änderungen im Detail

### iPhone (8 Regeln, alle Top-Deal-Tier)

**Kategorie:** iphone
**Regel:** iPhone 11 Pro Max (≤256GB) ★ Top-Deal
**Alter max_price:** 100€ → **Neuer max_price:** 150€
**Samples:** 30 · **P10:** – · **P25:** 150,0 · **Median:** – · **P75:** – · **P90:** –
**Begründung:** Reale P25 (150€) liegt 50% über der alten Grenze — die alte Grenze verhinderte praktisch jeden Top-Deal-Treffer.

**Kategorie:** iphone
**Regel:** iPhone 14 Plus (≤256GB) ★ Top-Deal
**Alter max_price:** 165€ → **Neuer max_price:** 250€
**Samples:** 26 · **P25:** 250,4
**Begründung:** wie oben.

**Kategorie:** iphone
**Regel:** iPhone 15 (≤256GB) ★ Top-Deal
**Alter max_price:** 210€ → **Neuer max_price:** 310€
**Samples:** 155 · **P25:** 310,5
**Begründung:** sehr große, belastbare Stichprobe (Confidence HIGH).

**Kategorie:** iphone
**Regel:** iPhone 15 Pro (≤256GB) ★ Top-Deal
**Alter max_price:** 265€ → **Neuer max_price:** 380€
**Samples:** 129 · **P25:** 380,0
**Begründung:** wie oben.

**Kategorie:** iphone
**Regel:** iPhone 15 Pro Max (≤256GB) ★ Top-Deal
**Alter max_price:** 300€ → **Neuer max_price:** 450€
**Samples:** 72 · **P25:** 450,0
**Begründung:** wie oben.

**Kategorie:** iphone
**Regel:** iPhone 16 (≤256GB) ★ Top-Deal
**Alter max_price:** 275€ → **Neuer max_price:** 400€
**Samples:** 61 · **P25:** 399,0 (auf 400 gerundet)
**Begründung:** wie oben.

**Kategorie:** iphone
**Regel:** iPhone 16 Pro (≤256GB) ★ Top-Deal
**Alter max_price:** 360€ → **Neuer max_price:** 550€
**Samples:** 79 · **P25:** 550,0
**Begründung:** wie oben.

**Kategorie:** iphone
**Regel:** iPhone 16 Pro Max (≤256GB) ★ Top-Deal
**Alter max_price:** 415€ → **Neuer max_price:** 600€
**Samples:** 70 · **P25:** 600,0
**Begründung:** wie oben.

> Guter-Preis-/Okay-Tarife dieser Modelle **unverändert** — nur die
> jeweiligen Top-Deal-Regeln waren im Review als ZU STRENG markiert.

### MacBook Air M4

**Kategorie:** macbook
**Regel:** MacBook Air M4 (≤512GB) ★ Top-Deal
**Alter max_price:** 415€ → **Neuer max_price:** 725€
**Datenbasis:** Confidence MEDIUM · **Samples:** 16
**P10:** – · **P25:** 726,8 · **Median:** – · **P75:** – · **P90:** –
**Begründung:** besonders robuster Befund — die alte Grenze (415€) lag
SOGAR UNTER dem günstigsten real beobachteten Angebot (499€). Unter der
alten Regel konnte de facto NIE ein Top-Deal erkannt werden.

### LEGO CMF / Sammelfigur (3 Regeln, alle Tiers)

**Kategorie:** lego_minifiguren
**Regel:** LEGO CMF / Sammelfigur ★ Top-Deal
**Alter max_price:** 8€ → **Neuer max_price:** 5€
**Samples:** 175 · **P25:** 5,0

**Regel:** LEGO CMF / Sammelfigur 👍 Guter Preis
**Alter max_price:** 15€ → **Neuer max_price:** 7€
**Samples:** 175 · **Median:** 7,0

**Regel:** LEGO CMF / Sammelfigur ⚠️ Interessant
**Alter max_price:** 25€ → **Neuer max_price:** 10€
**Samples:** 175 · **P75:** 9,7 (auf 10 gerundet)

**Begründung (alle drei):** sehr große, saubere Stichprobe (Confidence
HIGH, keine False-Match-Kontamination in der Prüfung gefunden) — reale
CMF-Sammelfiguren sind deutlich günstiger als die bisherigen Grenzen
annahmen.

---

## Bewusst NICHT geändert (vollständige Liste)

| Modell | Klassifikation | Grund |
|---|---|---|
| `lego_sw_rare` | ZU WENIGE DATEN | nach Matching-Fix nur n=14 verbleibend |
| `roehrenfernseher` | ZU WENIGE DATEN | nach Matching-Fix nur n=4 verbleibend |
| `crt_profi_monitor` | NICHT ÄNDERN | bereinigte Daten bestätigen aktuelle Grenze |
| `thinkpad_modern` | NICHT ÄNDERN | bereinigte Daten bestätigen aktuelle Grenze |
| `nintendo_retro_konsole` | MANUELLE PRÜFUNG | Signal bleibt, aber zu schwach für Automatik |
| `sony_retro_konsole` | MANUELLE PRÜFUNG | Signal bleibt, aber zu schwach für Automatik |
| `lego_promo` (Guter Preis/Interessant) | MANUELLE PRÜFUNG | Stichprobe an der Grenze (n=16) |
| `netzteil_650w` | MANUELLE PRÜFUNG | viele Punkte ohne `fingerprint`, nicht vollständig verifizierbar |
| `retro_konvolut` | MANUELLE PRÜFUNG | branchenfremde Treffer gefunden |
| `vintage_hifi_verstaerker` | MANUELLE PRÜFUNG | Platzhalter-Preis-Cluster am unteren Rand |
| `iphone_15_plus_128gb` | MANUELLE PRÜFUNG | kleine Stichprobe + Tausch-Ausreißer |
| `iphone_16_pro_max_512gb` | MANUELLE PRÜFUNG | kleine Stichprobe + 0€-Ausreißer |
| alle Modelle mit <15 Samples | ZU WENIGE DATEN | (95 + 46 Regeln, siehe Report 1) |
| `cpu_mainboard_bundle` (alle 3 Combos) | ZU WENIGE DATEN | weiterhin 0 Samples (Phase 11) |

---

## Sicherheitsprüfung

- **Deal-Score-/Top-Deal-/Flip-Kandidat-/Resale-/Notification-/
  Duplicate-Detection-/Re-Evaluierungs-Logik:** keine Zeile Code
  angefasst — ausschließlich `max_price`-Werte in `rules/*.yaml`
  geändert.
- **`price_history.jsonl`/`seen.json`/`found.json`:** nicht gelöscht,
  nicht manipuliert (nur lesend für die Kalibrierung verwendet).
- **Kein automatischer Selbst-Kalibrierungsmechanismus gebaut** — alle
  Preisgrenzen bleiben explizit in YAML, wie gefordert.

---

## Tests

- **19 neue Tests** in `app/tests/test_matcher_price_calibration_applied.py`:
  je Modell ein Test "innerhalb neuer Grenze = Top-Deal" + "über neuer
  Grenze = kein Top-Deal", plus 4 Regressionstests, die explizit
  bestätigen, dass die UNVERÄNDERT gebliebenen Modelle
  (`crt_profi_monitor`, `thinkpad_modern`, `lego_sw_rare`,
  `nintendo_retro_konsole`) ihre alten Grenzen behalten haben.
- **Keine bestehenden Tests verändert oder gelöscht.**
- **Vollständiger Testlauf:** `pytest app/tests/` → **851 passed, 0
  failed** (832 vor diesem Schritt + 19 neue).

---

## Nächster Schritt

Wie vereinbart: **kein automatischer Selbst-Kalibrierungsmechanismus.**
Die als MANUELLE PRÜFUNG / ZU WENIGE DATEN eingestuften Modelle
(insbesondere Nintendo/Sony-Retro-Konsolen, die weiterhin ein
schwächeres "zu hoch"-Signal zeigen) sollten erst nach einem
Validierungs-Scan mit den jetzt reparierten Matching-Regeln erneut
bewertet werden — dann mit einer größeren, garantiert sauberen
Datenbasis.
