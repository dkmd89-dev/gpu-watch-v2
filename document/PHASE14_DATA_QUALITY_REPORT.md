# Phase 14 – Dashboard-/Datenbereinigung & False-Positive-Filter

**Status: ANALYSE ABGESCHLOSSEN – keine Code-/YAML-Änderung vorgenommen. Wartet auf Freigabe.**

Analysiert gegen Produktionsstand `13e409f` (nach Phase 13 / Validation Report).

---

## 1. Datenfluss Dashboard/API (Architektur-Ist-Zustand)

```
Scraper (kleinanzeigen.py / ebay.py)
   ↓  liefert Rohdaten (title, price, url, ...)
matcher.evaluate()  ←  rules_cfg = load_rules("rules/")  (ALLE *.yaml zusammen, directory_mode)
   ↓  MatchResult (matched, category, price_history_model, deal_score, deal_stars, ...)
app.py: run_scan()
   ↓  bei matched=True → found.json (Liste, FOUND_MAX_ITEMS gekappt) + seen.json + price_history.jsonl
app/api/deals.py
   ↓  GET /            → render_template("index.html", found=<found.json roh>)
   ↓  GET /api/found    → jsonify(<found.json roh>)
```

**Kernbefund:** `found.json` wird **ungeprüft** ausgeliefert. Es gibt **keine zentrale Kategorievalidierung** zwischen Matcher und Dashboard/API — `api/deals.py` liest `found.json` 1:1 und reicht es durch (`_load_json(found_file, [])`, keine Filterung, keine Re-Prüfung). Ein einmal als `handhelds` gespeicherter Fehltreffer bleibt dauerhaft und unverändert im Dashboard sichtbar, auch wenn die Regel später korrigiert wird.

Ebenfalls ungeprüft dieselbe Quelle: `app/deal_intelligence.py` (Flip-Kandidaten) und `app/top_deal.py` — beide arbeiten direkt mit dem `category`/`price_history_model`-Feld aus dem MatchResult, das zum Scan-Zeitpunkt in `found.json` geschrieben wurde. Es existiert **keine gemeinsame, zentrale Re-Validierungsfunktion**, die von Dashboard, API, Flip-Ansicht und Deal-Ansicht gleichermaßen genutzt wird.

---

## 2. Analyse Kategorie "handhelds" (`app/rules/handhelds.yaml`)

**Search-Terms:** Nintendo 3DS, 3DS XL, New 3DS, 2DS XL, PS Vita, PSVita, Steam Deck, SteamDeck, ROG Ally, Lenovo Legion Go.

**Wichtig:** *Nintendo Switch* ist **nicht** Teil von `handhelds`, sondern eine eigene Kategorie `konsolen_bundles` (`rules/konsolen_bundles.yaml`). Die im Auftrag genannten Switch-Testfälle betreffen daher architektonisch die Kategorie `konsolen_bundles`, nicht `handhelds` — beide Kategorien haben aber dasselbe strukturelle Problem (siehe Punkt 4).

### Regelstruktur

| Rule-Gruppe | require_all_of-Gruppen | Zusatz-Bedingung "Gerät vorhanden"? |
|---|---|---|
| Nintendo 3DS/2DS XL | 2 (Marke + `xl`/`new 3ds`/`konsole`) | ✅ ja |
| PS Vita | 2 (Marke + `konsole`/`bundle`/`set`/`ovp`/`system`) | ✅ ja |
| **Steam Deck** | **1** (nur Marke) | ❌ **nein** |
| **ROG Ally / Legion Go** | **1** (nur Marke) | ❌ **nein** |

### Root Cause

Für Steam Deck und ROG Ally/Legion Go genügt **allein** die Erwähnung des Markennamens im Titel — es gibt keine zweite `require_all_of`-Gruppe, die das Vorhandensein eines physischen Geräts bestätigt (wie bei 3DS/Vita). Der Schutz gegen Zubehör/Ersatzteile hängt hier **ausschließlich** von der `exclude_category`-Blockliste ab:

```yaml
exclude_category:
  - "hülle" - "case" - "tasche" - "schutzfolie" - "glas" - "grips"
  - "sd karte" - "dock" - "ladestation" - "ersatzteil" - "display"
  - "akku" - "ovp nur" - "spiel" - "spielesammlung" - "spiele sammlung"
  - "modul" - "cartridge"
```

Diese Liste ist **nicht vollständig** — u.a. fehlen `netzteil`, `ladekabel`, `kabel`, `ladegerät`, `anleitung`. Jede Formulierung außerhalb der Liste rutscht durch.

### Live-Verifikation (gegen die echten Produktivregeln, `matcher.evaluate()`)

```
"Netzteil für Steam Deck 45W"                 (15 €)  → MATCH: handhelds / handheld_steam_deck
                                                          Top-Deal, ★★★★☆, Score 91
"Ladekabel für Nintendo Switch Lite Original"  (8 €)  → MATCH: konsolen_bundles / konsole_switch_lite
                                                          Top-Deal, ★★★★☆, Score 88
```

Beides sind **bestätigte False Positives**: ein Netzteil bzw. ein Ladekabel wird als vollständige Konsole mit Top-Deal-Bewertung eingestuft und würde im Dashboard prominent (★★★★☆, hoher Score) erscheinen.

Zum Vergleich – korrekt funktionierende zweistufige Regeln filtern bereits zuverlässig:
```
"Nintendo Switch Spiel Mario Kart 8 Deluxe"    → kein Match (korrekt, nur "spiel" ohne Konsolen-Indikator)
"Zelda Spiel Nintendo Switch OVP"              → kein Match (korrekt)
"Spiel für Steam Deck – Hades Download Code"   → kein Match (korrekt, "spiel" exact-word-exclude greift)
"Nintendo Switch Lite Hülle Tasche Grau"       → kein Match (korrekt, "hülle"/"tasche" exclude greift)
"Nintendo Switch Pro Controller original"      → Match, aber korrekt Kategorie "controller", nicht handheld
```

Das bestätigt: das Grundmuster (Marke + Geräte-Indikator, ergänzt um gezielte Excludes statt Pauschalausschluss von "Spiel") funktioniert. Es fehlt nur bei den vier genannten Regeln.

### Bereits vorhandener Präzedenzfall im selben Repo

`rules/retro_konsolen.yaml` hatte laut Code-Kommentaren exakt dasselbe Problem und wurde bereits nach demselben Muster gefixt (Zitat aus der YAML, Robin-Feedback "ich bekomme Spiele und Sonstiges"): zweistufiges `require_all_of` (Marke + `konsole`/`gerät`/`system`/`controller`/`netzteil`) statt Pauschal-Exclude von "Spiel", dokumentiert mit einer Vorher/Nachher-Verifikation gegen `found.json` (152 → 59 Treffer, 93 Fehltreffer entfernt). Für `handhelds` und `konsolen_bundles` wurde dieses Muster nie nachgezogen.

---

## 3. Weitere betroffene Kategorien (Punkt 4 des Auftrags)

Automatisierte Prüfung aller `rules/*.yaml` auf `require_all_of`-Regeln mit nur **einer** Gruppe (= dasselbe Strukturmuster wie oben):

| Kategorie | Regeln gesamt | davon 1-Gruppen-`require_all_of` | betroffen |
|---|---|---|---|
| **handhelds** | 8 | **4** (Steam Deck ×2, ROG Ally/Legion Go ×2) | ✅ ja |
| **konsolen_bundles** | 10 | **2** (Nintendo Switch Lite ×2) | ✅ ja |
| retro_konsolen | 9 | 0 | ✅ bereits gefixt |
| controller | 10 | 0 | nein |
| cpu_mainboard_bundle | 6 | 0 | nein |
| iphone | 138 | 0 | nein |
| lego_minifiguren | 36 | 0 | nein |
| macbook | 60 | 0 | nein |
| m2_ssd / ram / monitor_curved / notebook_resell / vintage_elektronik / autoradio_opel_corsa | je 0 | 0 | nein |

→ Das Problem betrifft **ausschließlich `handhelds` und `konsolen_bundles`**, und dort jeweils nur die Regeln, die kein zweites Bestätigungs-Kriterium für "es ist wirklich das Gerät" verlangen.

Zusätzlich fehlende Exclude-Begriffe (Lücken in `exclude_category`), unabhängig von der require_all_of-Struktur:
- `handhelds.yaml`: `netzteil`, `ladekabel`, `kabel`, `ladegerät`, `anleitung` fehlen.
- `konsolen_bundles.yaml`: `netzteil`, `ladekabel`, `kabel`, `anleitung`, bloßes `controller` (nur `"nur controller"` vorhanden) fehlen.

---

## 4. Vorgeschlagene Lösung (noch NICHT umgesetzt)

1. **Zentrale Kategorievalidierung** (Architektur-Vorgabe des Auftrags): eine Funktion, z.B. `matcher.revalidate(entry) -> bool`, die einen bestehenden `found.json`-Eintrag (Titel + gespeicherte `category`/`price_history_model`) gegen die *aktuellen* Regeln erneut prüft. Wird von `api/deals.py` (`index()`, `/api/found`), Flip-Kandidaten-Logik und Deal-Ansicht gemeinsam genutzt, statt dass jede Stelle `found.json` blind durchreicht.
2. **YAML-Fix (additiv, kein Python-Change nötig für die Regeln selbst):** Steam-Deck-, ROG-Ally/Legion-Go- und Switch-Lite-Regeln um eine zweite `require_all_of`-Gruppe ergänzen (Geräte-Indikator wie `konsole`, `system`, `gerät`, oder Kapazitäts-/Editionsangaben wie `gb`/`lcd`/`oled`, die bei reinem Zubehör untypisch sind) — analog zum bereits bewährten `retro_konsolen`-Muster. Zusätzlich fehlende Excludes (`netzteil`, `ladekabel`, `kabel`, `anleitung`) ergänzen.
3. **Historische Bereinigung ohne Datenlöschung:** bestehende `found.json`-Einträge werden beim nächsten Dashboard-Request bzw. Scan durch die zentrale Re-Validierung (Punkt 1) automatisch ausgeblendet, sobald sie gegen die korrigierten Regeln nicht mehr matchen — **kein Löschen/Manipulieren** von `found.json`, `seen.json` oder `price_history.jsonl`. Alternativ (falls Re-Validierung im Read-Pfad zu teuer): ein einmaliges, klar deklariertes Flag `category_invalidated: true` pro Eintrag statt physischem Entfernen.
4. Deal-Score, Top-Deal-Logik, Flip-/Resale-Berechnung, price_history-Modell bleiben unverändert — die Korrektur wirkt ausschließlich auf die Kategoriezuordnung/Matching-Vorbedingung.

---

## 5. Antworten auf die Auftragspunkte

1. **Gefundene False Positives:** Bestätigt und live reproduziert: "Netzteil für Steam Deck" (als `handheld_steam_deck` Top-Deal) und "Ladekabel für Nintendo Switch Lite" (als `konsole_switch_lite` Top-Deal). Strukturell zusätzlich alle Titel, die Marke + irgendein nicht in `exclude_category` gelistetes Zubehörwort enthalten (SD-Karten-Reader, Aufkleber, Skin, Kabel, Netzteile allgemein).
2. **Ursache:** 4 von 8 `handhelds`-Regeln (Steam Deck, ROG Ally/Legion Go) und 2 von 10 `konsolen_bundles`-Regeln (Switch Lite) verlangen nur Markenerwähnung, keine Geräte-Bestätigung; Schutz hängt allein von einer unvollständigen Exclude-Liste ab.
3. **Regeln geändert:** noch keine – Vorschlag siehe Abschnitt 4, wartet auf Freigabe.
4. **Bereinigte Dashboard-Einträge:** noch keine – vorgeschlagen ist Re-Validierung statt Löschung (Abschnitt 4, Punkt 3), wartet auf Freigabe/Umsetzung.
5. **Weitere betroffene Kategorien:** `konsolen_bundles` (gleiches Muster). Alle anderen 12 Kategorien sind nicht betroffen (0 einstufige `require_all_of`-Regeln). `retro_konsolen` hatte dasselbe Problem, ist aber bereits gefixt.
6. **Tests vorher/nachher:** vorher 0 dedizierte Regressionstests für `handhelds`/`konsolen_bundles`-Fehltreffer (keine Datei in `app/tests/` referenziert diese Kategorien für False-Positive-Fälle). Nachher: ausstehend bis Freigabe von Phase 2 (Umsetzung).
7. **Testergebnis:** ausstehend bis Freigabe.

---

## Freigabe-Bedarf

Für die Umsetzung sind zwei unabhängig freigebbare Schritte vorgesehen:

- **Schritt 1:** YAML-Fix (`handhelds.yaml` + `konsolen_bundles.yaml`, zweite `require_all_of`-Gruppe + fehlende Excludes) + neue Regressionstests (`app/tests/test_matcher_handheld_false_positives.py`, analog zu `test_matcher_price_calibration_matching_fixes.py`, gegen die echten `rules/`).
- **Schritt 2:** zentrale Re-Validierungsfunktion + Anbindung in `api/deals.py` (und ggf. Flip-Kandidaten-Ansicht), damit historische Fehltreffer ohne Datenlöschung aus der Anzeige verschwinden.

Bitte Freigabe für Schritt 1 (und danach ggf. separat für Schritt 2).
