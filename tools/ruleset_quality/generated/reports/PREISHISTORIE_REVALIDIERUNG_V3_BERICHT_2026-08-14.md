# Kontrollierte Preishistorien-Revalidierung v3 — Bericht

**Erstellt:** 2026-08-14 · **Charakter:** vollständig READ-ONLY. **Keine** Zeile in
`data/price_history.jsonl` wurde geschrieben, geändert oder gelöscht. Kein Commit, kein Push,
kein Merge, kein PR.

Grundlage: Fingerprint→Titel-Fix (STATUS.md Datenqualität Nr. 11, heute umgesetzt) +
menschlich verifizierte Labels für 251 Listings (`human_verified_labels_2026-08-14.json`).
Skript: `tools/ruleset_quality/price_history_revalidation_v3.py`,
Rohdaten: `generated/reports/price_history_revalidation_v3.json`.

---

## ⚠️ Zentraler Befund zuerst: Der Fix hilft nur für NEUE Daten, nicht rückwirkend

Der heute umgesetzte Fix (`duplicate_detection.normalize_title()` erhält Umlaute) wirkt
ausschließlich auf **ab jetzt neu geschriebene** `price_history.jsonl`-Zeilen. Bereits
gespeicherte Zeilen behalten ihr altes, fehlerhaftes Fingerprint-Format — weil `PricePoint`
den Rohtitel gar nicht persistiert (nur `fingerprint`, kein `title`-Feld), lässt sich der
korrekte Fingerprint nachträglich **nicht** aus der Datei selbst neu berechnen.

**Konkret geprüft:** Für die 4 historisch betroffenen Kategorien (`handhelds`,
`konsolen_bundles`, `retro_konsolen`, `vintage_elektronik`) wurde jeder „kein Treffer per
Fingerprint"-Punkt gegen `title_recovery.py` (found.json + Forensik-Snapshot) geprüft, wo ein
echter Titel rekonstruierbar ist:

| Kategorie | Punkte gesamt | „Kein Treffer" per Fingerprint | Titel rekonstruierbar | davon: residuales Artefakt (bei echtem Titel gültig) | davon: echte Änderung | **nicht beurteilbar** |
|---|---|---|---|---|---|---|
| handhelds | 98 | 34 | 7 | 0 | 7 | **27** |
| konsolen_bundles | 774 | 59 | 17 | 6 | 11 | **42** |
| retro_konsolen | 1.715 | 714 | 1 | 0 | 1 | **713** |
| vintage_elektronik | 802 | 409 | 0 | 0 | 0 | **409** |

**Für `retro_konsolen` und `vintage_elektronik` ist damit praktisch keine Aussage möglich** —
99,9% bzw. 100% der „kein Treffer"-Punkte sind weder als echte Regel-Drift noch als reines
Fingerprint-Artefakt einzuordnen, der Titel ist unwiederbringlich verloren. Die weiter unten
gezeigten „kein Treffer"-Prozentsätze dieser 4 Kategorien sind **nicht** als
Datenqualitätsproblem misszuverstehen — sie sind größtenteils eine Folge des historischen
Fingerprint-Formats, nicht der aktuellen Regeln.

---

## 1. Gesamtbild (alle 14.899 Punkte, 122 Modelle)

```text
Ohne Fingerprint (Alt-Daten vor Feature-Einführung): 1.173
Unverändert:                                        11.581
Kein Treffer:                                         1.677
Kategorie geändert:                                      17
Modell geändert:                                        451
```

### Aufgeteilt: umlaut-betroffene vs. unbetroffene Kategorien

| | Punkte | Unverändert | Kein Treffer | Modell geändert | Kategorie geändert |
|---|---|---|---|---|---|
| **15 unbetroffene Kategorien** (verlässlich) | 10.337 | 91,1% | 4,5% | 4,4% | 0,1% |
| **4 betroffene Kategorien** (siehe Kasten oben) | 3.389 | 64,0% | **35,9%** (größtenteils unbeurteilbar) | 0,0% | 0,1% |

Für die 15 unbetroffenen Kategorien ist 91,1% „unverändert" ein plausibler, gesunder Wert nach
über 30 gemergten Fix-PRs im Beobachtungszeitraum.

### Auffälligste Bewegungen in den 15 verlässlichen Kategorien

| Modell | Punkte | Kein Treffer | Modell geändert | Kategorie geändert | Einordnung |
|---|---|---|---|---|---|
| `lego_ninjago_bundle` | 598 | 44 | **361 (60%)** | 2 | Erwartbar: `lego_minifiguren.yaml` hat seither deutlich granularere Sub-Modelle (`lego_sw_clone`, `lego_cmf`, `lego_minifig_bundle`) bekommen — Punkte wandern innerhalb der Kategorie, keine Fehlklassifikation |
| `office_pc` | 275 | 75 (27%) | 0 | 5 | Erwartbar: deckt sich mit den bekannten Notebook-Cross-Category-Fixes (PR #27 + heutiger PR #31) |
| `thinkpad_modern` | 180 | 41 (23%) | 0 | 0 | Vermutlich verwandter Effekt (Preisdeckel-/Notebook-Abgrenzung) |
| `gaming_laptop_rtx3060`/`rtx4060` | 34/20 | 29/15 (~80%) | 0 | 0 | Kleine Stichprobe, hohe Drop-Rate — nur beobachtet, nicht weiter untersucht (außerhalb des Auftrags) |
| `monitor_curved` | 1.066 | 107 (10%) | 0 | 0 | Moderat, unauffällig |

---

## 2. Cross-Validierung gegen die 251 menschlich verifizierten Labels

282 `price_history.jsonl`-Punkte konnten über den (jetzt korrekten) Fingerprint eindeutig einem
der 251 Sample-Titel zugeordnet werden.

```text
                    Fingerprint-Zustand nach Neubewertung
Human-Verdict       UNVERAENDERT  KEIN_TREFFER  MODELL_GEAENDERT  KATEGORIE_GEAENDERT
TRUE_POSITIVE              251             1                 4                    1
FALSE_POSITIVE               10             4                 0                    0
UNCLEAR                      11             0                 0                    0
```

**Wichtigste Erkenntnis:** Die 4 `FALSE_POSITIVE → KEIN_TREFFER`-Fälle sind **exakt** die vier
Titel, die der heutige Exclude-Fix (PR #31) beheben sollte: „Defekte Asus ROG Ally", „PS2 Slim
mit defekten Laser", „Dynabook Satellite Pro", „Dell Latitude 7300". Das ist eine direkte,
unabhängige Bestätigung, dass der Fix auch auf den echten persistierten Daten wirkt — nicht nur
in den Unit-Tests. Die übrigen **10 von 14 FP-Fällen matchen unverändert** — das sind die
bekannten, bewusst nicht gefixten strukturellen Muster (Zubehör-vs-Gerät,
Spieltitel-ohne-Konsole).

Ein `TRUE_POSITIVE → KATEGORIE_GEAENDERT`-Einzelfall („MSI Gaming M.2 SSD 1 TB") wechselt von
`m2_ssd` zu `sata_ssd` — Ursache: `normalize_title()` entfernt Satzzeichen (aus "M.2" wird
"m 2") und Füllwörter, wodurch die Fingerprint-Fassung leicht andere Signalwörter enthält als
der echte Titel. Eine zusätzliche, vom Umlaut-Fix unabhängige Einschränkung der
Fingerprint-Methodik — nur dieser eine Fall beobachtet, nicht generalisiert.

Die 5 `TRUE_POSITIVE`-Fälle mit `LEGO Figuren Sammlung` (unterschiedliche Preise) zeigen
erwartbare preisstufenabhängige Modellwechsel innerhalb von `lego_minifiguren` — derselbe,
generische Fingerprint kommt bei mehreren realen Listings vor und landet je nach Preis in
unterschiedlichen Preisstufen-Regeln.

---

## 3. Fazit / Einordnung

- **Verlässlich revalidierbar:** 15 von 19 Kategorien (10.337 von 13.726 Punkten mit
  Fingerprint) — Ergebnis ist plausibel und größtenteils durch bereits bekannte, dokumentierte
  Ursachen erklärbar.
- **Nicht sinnvoll fingerprint-revalidierbar:** `retro_konsolen` und `vintage_elektronik`
  (praktisch 0% beurteilbar), `handhelds`/`konsolen_bundles` nur mit sehr kleiner,
  nicht-repräsentativer Stichprobe (7 bzw. 17 rekonstruierte Titel).
- **Der Fix selbst ist korrekt und bereits nachweislich wirksam** (siehe Cross-Validierung),
  löst aber das ursprüngliche STATUS.md-Problem (verlässliche Revalidierung der historischen
  Preishistorie in diesen 4 Kategorien) **nicht rückwirkend** — das wäre nur durch eine
  vollständige Neuerhebung oder eine (hier nicht vorgenommene) Migration mit den wenigen
  rekonstruierbaren Titeln teilweise möglich.

## Keine Handlungsempfehlung ausgesprochen

Es wird hier bewusst **keine** konkrete Lösch-/Korrektur-Aktion für `price_history.jsonl`
vorgeschlagen — die Datenlage lässt für die 4 betroffenen Kategorien keine verlässliche
Einzelfallentscheidung zu, und für die 15 unbetroffenen Kategorien wären die beobachteten
Änderungen (Modell-/Kategoriewechsel) eher als **Korrektur bestehender Fehlklassifikationen**
denn als Fehler zu werten (z. B. `office_pc`/`thinkpad_modern`-Drift durch bereits gebilligte
Notebook-Fixes). Jede tatsächliche Schreibaktion an `price_history.jsonl` erfordert eine
gesonderte, konkret abgegrenzte Freigabe (analog zur vorherigen `lego_bundle`-Migration).

## Bestätigung

Es wurden ausschließlich neue, read-only Analyse-Artefakte erzeugt:
`tools/ruleset_quality/price_history_revalidation_v3.py`,
`generated/reports/price_history_revalidation_v3.json`, dieser Bericht.
**Keine** Änderung an `data/price_history.jsonl`, `data/found.json`, `data/seen.json` oder
`app/rules/*.yaml`. Kein Commit, kein Push, kein Merge, kein PR.
