# 251-Listing-Worksheet gelabelt — Bericht

**Erstellt:** 2026-08-14 · **Charakter:** vollständig READ-ONLY. Keine `found.json`-,
`price_history.jsonl`-, `seen.json`- oder YAML-Änderung. Kein Commit, kein Push, kein Merge,
kein PR.

## ⚠️ Methodischer Hinweis (wichtig)

Diese Labels sind **KI-gestützt, keine unabhängige menschliche Verifikation** wie die bestehende
`docs/DASHBOARD_MATCH_FORENSICS.json` (die laut `label_store.py` ausdrücklich als „die einzige
im Projekt vorhandene MENSCHLICH verifizierte Ground Truth" dokumentiert ist). Ich habe jede der
251 Zeilen anhand von Titel, Preis und Regel-Diagnose (welche `require_all_of`-Gruppe wodurch
erfüllt wurde, welche Excludes im Titel vorkommen) inhaltlich bewertet — nach denselben Kriterien,
die auch in der Forensik-Quelle verwendet wurden (Zubehör/Ersatzteil vs. Gerät, Spieltitel ohne
Konsole, Defekt-Signale, generische Alleinstellungs-Treffer).

**Deshalb als eigene, getrennte Quelle abgelegt:**
`tools/ruleset_quality/generated/ai_assisted_labels_2026-08-14.json`
(`source: "ai_assisted_sampling_worksheet"`, `source_date: "2026-08-14"`) —
die bestehende `ground_truth_labels.json` (aus der Forensik-Quelle) wurde **nicht** verändert.
Gelabeltes Worksheet als CSV: `generated/reports/sampling_worksheet_labeled_2026-08-14.csv`.

**Empfehlung:** Vor Verwendung als Basis für die Preishistorien-Revalidierung mindestens die
21 FALSE_POSITIVE- und die 13 UNCLEAR-Fälle stichprobenartig gegenprüfen (siehe Tabellen unten) —
insbesondere die neu entdeckten strukturellen Muster (siehe nächster Abschnitt), die über diese
Stichprobe hinaus relevant sein könnten.

---

## Ergebnis

```text
Gesamt:            251
TRUE_POSITIVE:     217  (86,5%)
FALSE_POSITIVE:      21  (8,4%)
UNCLEAR:             13  (5,2%)

Precision (TP / (TP+FP)):  217 / 238 = 91,2%
```

### Nach Kategorie

| Kategorie | TP | FP | UNCLEAR | gesamt |
|---|---|---|---|---|
| autoradio_opel_corsa | 9 | 0 | 0 | 9 |
| controller | 13 | 2 | 0 | 15 |
| cpu_mainboard_bundle | 1 | 0 | 0 | 1 |
| gaming_pc | 14 | 0 | 1 | 15 |
| gpu | 15 | 0 | 0 | 15 |
| **handhelds** | **7** | **7** | 1 | 15 |
| iphone | 15 | 0 | 0 | 15 |
| konsolen_bundles | 12 | 2 | 1 | 15 |
| lego_minifiguren | 13 | 2 | 0 | 15 |
| m2_ssd | 1 | 0 | 0 | 1 |
| macbook | 15 | 0 | 0 | 15 |
| monitor_curved | 15 | 0 | 0 | 15 |
| netzteil | 12 | 1 | 2 | 15 |
| notebook_resell | 13 | 0 | 2 | 15 |
| office_pc | 13 | 2 | 0 | 15 |
| ram | 14 | 1 | 0 | 15 |
| **retro_konsolen** | **10** | **4** | 1 | 15 |
| sata_ssd | 13 | 0 | 2 | 15 |
| vintage_elektronik | 12 | 0 | 3 | 15 |

`handhelds` (7/15 FP) und `retro_konsolen` (4/15 FP) fallen deutlich ab — beide unten im Detail.

---

## Neu entdeckte strukturelle Muster (über die Stichprobe hinaus relevant)

Diese vier Muster tauchen jeweils **mehrfach unabhängig in verschiedenen Kategorien** auf — das
spricht gegen Einzelfälle und für ein systematisches Problem, nicht nur "diese eine Zeile war
Pech". Keine YAML/Matcher-Änderung vorgenommen (außerhalb des Auftrags), nur dokumentiert.

### 1. Flektierte Exclude-Begriffe entgehen dem Whole-Word-Match (4 Fälle, 3 Kategorien)

`matcher.py::_contains_term()` prüft Exclude-Begriffe als **ganzes Wort**
(`(?<!\w)term(?!\w)`) — sinnvoll gegen Teilstring-Fehlalarme (z. B. "system" in "Kühlsystem"),
hat aber eine Kehrseite: **flektierte deutsche Formen werden nicht erkannt**, wenn nur der
Wortstamm in der Exclude-Liste steht:

| Titel | Exclude-Begriff (Stamm) | Tatsächliche Form im Titel | Re-verifiziert via `evaluate()` |
|---|---|---|---|
| "**Defekte** Asus ROG Ally Z1 Extreme 1TB" | `defekt` | `Defekte` | matcht weiterhin ✓ bestätigt |
| "PS2 Slim mit **defekten** Laser" | `defekt` | `defekten` | matcht weiterhin ✓ bestätigt |
| "**Tausche**/Gaming:Core i5 9400F..." | `tausch` | `Tausche` | matcht weiterhin ✓ bestätigt |
| "PS5 Controller **spinnt**" | `defekt`/`drift` (keine Umschreibung erfasst) | Umgangssprache, kein Wortstamm-Treffer möglich | matcht weiterhin |

Das sind eindeutig als defekt/tausch beworbene Angebote, die die Exclude-Liste trotzdem
passieren lassen. Betrifft `exclude_global` (`defekt`, `tausch`) genauso wie kategorie-eigene
Excludes. **Nur dokumentiert, keine Änderung** — eine Lösung (z. B. Wortstamm-Matching statt
Whole-Word, oder explizite Ergänzung der häufigsten Flexionsformen) wäre eine Matcher- bzw.
YAML-Änderung und fällt damit unter CLAUDE.md Regel 3/9 (separate Freigabe nötig).

### 2. Zubehör/Ersatzteil wird als Hauptgerät gematcht (6 Fälle, 4 Kategorien)

| Titel | Kategorie | Tatsächliches Produkt |
|---|---|---|
| "Lötaufsatz / Lötspitze für Xbox Series X & PS5 Controller T900" | controller | Reparatur-Werkzeug |
| "WD SN770 - Crucial P310 - SSD 2TB ... für Steam Deck etc." | handhelds | interne Upgrade-SSD |
| "Sony PS Vita In-Ear Headset ... Zubehör" | handhelds | Kopfhörer |
| "Fikwot M.2 2230 SSD ... For Steam Deck" | handhelds | interne Upgrade-SSD |
| "Kabelset für be quiet! Dark Power Pro 10 850W Netzteil" | netzteil | Kabel-Set |
| "SW - Original Nintendo Switch Joy-Con 2er-Set Grau" | konsolen_bundles | Controller-Set |

Gemeinsames Muster: das Zubehör-Objekt trägt selbst starke Kategorie-Signalwörter (z. B. "Steam
Deck", "Netzteil", "Switch"), die die `require_all_of`-Logik erfüllen, ohne dass das eigentliche
Hauptgerät im Angebot ist.

### 3. Spieltitel/Modul ohne Konsole (5 Fälle, 2 Kategorien)

Bereits in früheren Berichten als bekannte strukturelle Restlücke dokumentiert
(`docs/KONSOLEN_BUNDLES_OVP_ANALYSE.md`) — diese Stichprobe bestätigt, dass das Muster auch in
`retro_konsolen` auftritt, nicht nur `konsolen_bundles`: "Pokémon Stadium für Nintendo 64",
"DINO CRISIS 2 (PS1) KOMPLETT", "S.C.A.R.S. PS1 ... komplett mit Anleitung", "Mariokart World -
Nintendo Switch 2 - NEU & OVP", "Xenoblade Chronicles für Nintendo New 3DS OVP".

### 4. Notebook-Marken, die der office_pc-Notebook-Exclude nicht erfasst (2 Fälle)

PR #27 (`fc59d1d`) hat Notebooks/Laptops für `office_pc` explizit über Markennamen ausgeschlossen
(ThinkPad/MacBook/IdeaPad/Alienware/Lifebook, siehe TECHNISCHER_PROJEKTSTATUS.md Abschnitt 3.10).
Diese Stichprobe zeigt zwei weitere durchrutschende Marken: **"Dynabook Satellite Pro"** und
**"Dell Latitude"** (beides Notebook-Baureihen, hier zusätzlich durch 15,6"/13,3"-Bildschirm- bzw.
mobile "U"-Prozessorangaben erkennbar). Gleiches strukturelles Muster wie der bereits gefixte Fall,
nur mit anderen Markennamen — nicht behoben, nur dokumentiert.

---

## Alle 21 FALSE_POSITIVE-Fälle

| Kategorie | Titel | root_cause |
|---|---|---|
| controller | Lötaufsatz / Lötspitze für Xbox Series X & PS5 Controller T900 | zubehoer_statt_geraet |
| controller | PS5 Controller spinnt | defekt_nicht_erfasst |
| handhelds | WD SN770 - Crucial P310 - SSD 2TB ... für Steam Deck etc. | zubehoer_statt_geraet |
| handhelds | Sony PS Vita In-Ear Headset ... Zubehör | zubehoer_statt_geraet |
| handhelds | Xenoblade Chronicles für Nintendo New 3DS OVP | spieltitel_ohne_konsole |
| handhelds | Fikwot M.2 2230 SSD ... For Steam Deck | zubehoer_statt_geraet |
| handhelds | Defekte Asus ROG Ally Z1 Extreme 1TB | exclude_flexionsform_nicht_erfasst |
| handhelds | Modded SD Karten für 3ds/3ds xl/ | exclude_flexionsform_nicht_erfasst |
| handhelds | Nintendo DS und 3DS Spiele (AUSWAHL) Module ... 2DS DSi XL | spielesammlung_ohne_konsole |
| konsolen_bundles | Mariokart World - Nintendo Switch 2 - NEU & OVP | spieltitel_ohne_konsole |
| konsolen_bundles | SW - Original Nintendo Switch Joy-Con 2er-Set Grau | zubehoer_statt_geraet |
| lego_minifiguren | Original LEGO Clone Trooper NUR KOPF -Star Wars- ... | nur_ersatzteil |
| lego_minifiguren | LEGO DUPLO Konvolut mit Figuren und Sonderteilen | falsches_produktsegment |
| netzteil | Kabelset für be quiet! Dark Power Pro 10 850W Netzteil | zubehoer_statt_geraet |
| office_pc | Dynabook Satellite Pro Intel Core 15,6" i5-8250U ... | notebook_als_desktop |
| office_pc | Dell Latitude 7300 - i7-8665U - 16GB RAM ... | notebook_als_desktop |
| ram | Dell Wyse 5070 ThinClient HomeServer J5005 8GB DDR4 32GB Win 10 | ganzes_geraet_statt_teil |
| retro_konsolen | Pokémon Stadium für Nintendo 64 ... | spieltitel_ohne_konsole |
| retro_konsolen | DINO CRISIS 2 (PlayStation 1 PS1 PSX) KOMPLETT | spieltitel_ohne_konsole |
| retro_konsolen | PS2 Slim mit defekten Laser | exclude_flexionsform_nicht_erfasst |
| retro_konsolen | S.C.A.R.S. PS1 / PlayStation 1 ... komplett mit Anleitung | spieltitel_ohne_konsole |

## Alle 13 UNCLEAR-Fälle

| Kategorie | Titel | root_cause |
|---|---|---|
| gaming_pc | Tausche/Gaming:Core i5 9400F 16Gb DDR4 750Gb GTX 1070 8Gb Win 11 | exclude_flexionsform_nicht_erfasst |
| handhelds | Elgato SteamDeck+ | unklarer_titel |
| konsolen_bundles | Nintendo Switch Spiele Bundle | spiele_bundle_ohne_eindeutiges_geraet |
| netzteil | Redundantes 2U Netzteil DPS-750PB 750W AC-078A | moeglich_falscher_formfaktor |
| netzteil | dell Z930P-00 Netzteil 930W 7001049-y000 | moeglich_falscher_formfaktor |
| notebook_resell | Lenovo ThinkPad T490 i5-8365U 16GB RAM 14" ohne SSD ohne Netzteil#V103 | unvollstaendiger_lieferumfang |
| notebook_resell | Lenovo ThinkPad T14 Gen 1 i5-10310U 16GB Touch ohne SSD Netzteil #V105 | unvollstaendiger_lieferumfang |
| retro_konsolen | Nintendo GameCube Super Mario Sunshine – komplett mit Anleitung | unklar_konsole_oder_spiel |
| sata_ssd | M2 SSD 250 GB | formfaktor_unklar |
| sata_ssd | Festplatte-SSD-256 GB-ADATA | moegliche_rule_drift (einziger Fall mit abweichender Neubewertung, siehe worksheet_diagnostics.json) |
| vintage_elektronik | Vintage HiFi Konvolut T+A, Onkyo, Harman Kardon, Sony | konvolut_produktzusammensetzung_unklar |
| vintage_elektronik | Rarität für Telefunken Röhrenfernseher: TELEklar ... | vermutlich_zubehoer |
| vintage_elektronik | Auna Röhrenverstärker HiFi Verstärker mit VU-Meter | moeglicherweise_kein_original_vintage_geraet |

---

## Bestätigung

Es wurden ausschließlich neue, read-only Analyse-Artefakte erzeugt:
`tools/ruleset_quality/worksheet_diagnostics.py`,
`generated/reports/worksheet_diagnostics.json`,
`generated/reports/sampling_worksheet_labeled_2026-08-14.csv`,
`generated/ai_assisted_labels_2026-08-14.json`, dieser Bericht.
**Keine** Änderung an `data/found.json`, `data/price_history.jsonl`, `data/seen.json` oder
`app/rules/*.yaml`. Kein Commit, kein Push, kein Merge, kein PR.
