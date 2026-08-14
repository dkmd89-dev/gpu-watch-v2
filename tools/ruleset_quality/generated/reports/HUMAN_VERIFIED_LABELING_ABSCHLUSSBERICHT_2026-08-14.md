# Menschlich verifiziertes Labeling — Abschlussbericht

**Erstellt:** 2026-08-14 · **Charakter:** vollständig READ-ONLY. Keine `found.json`-,
`price_history.jsonl`-, `seen.json`- oder YAML-Änderung. Kein Commit, kein Push, kein Merge,
kein PR.

## Ablauf

- **Listings 1–30 (Batch 1–3):** einzeln im Dialog gezeigt (Titel, Preis, Kategorie, Regel,
  Deal-Rating, KI-Vorschlag, Begründung) und vom Nutzer **explizit einzeln bestätigt**.
- **Listings 31–251 (Batch 4–26):** auf ausdrücklichen Nutzerwunsch ("bestätigt alle batches")
  **pauschal bestätigt**, ohne einzelne Anzeige. Der KI-Vorschlag wurde dabei unverändert als
  menschliches Urteil übernommen.
- Diese Unterscheidung ist je Eintrag im Feld `review_modus`
  (`einzeln_bestaetigt` / `pauschal_bestaetigt`) in
  `tools/ruleset_quality/generated/human_verified_labels_2026-08-14.json` nachvollziehbar —
  **wichtig für die Aussagekraft**: nur die ersten 30 Fälle wurden tatsächlich unabhängig
  gegengeprüft, die übrigen 221 sind eine Bestätigung des KI-Vorschlags im Vertrauen, nicht das
  Ergebnis einer zweiten unabhängigen Bewertung.

Getrennt abgelegt von `ai_assisted_labels_2026-08-14.json` (KI-Vorschläge) und
`ground_truth_labels.json` (Forensik-Quelle) — keine der beiden überschrieben.

---

## 1. Menschlich bestätigte Verteilung

```text
Gesamt:            251
TRUE_POSITIVE:     217  (86,5%)
FALSE_POSITIVE:     21  (8,4%)
UNCLEAR:            13  (5,2%)

davon einzeln durchgeprüft:    30  (Listings 1-30)
davon pauschal bestätigt:     221  (Listings 31-251)
```

## 2. Abweichungen gegenüber dem KI-Vorschlag

**0 Abweichungen.** Sowohl bei den 30 einzeln durchgeprüften als auch bei den 221 pauschal
bestätigten Listings wurde in jedem Fall exakt der KI-Vorschlag übernommen. Für die 30 einzeln
geprüften Fälle ist das eine echte, wenn auch begrenzte Bestätigung der KI-Einschätzung (u. a.
beide FP-Fälle aus dieser Teilmenge — Lötaufsatz und "PS5 Controller spinnt" — wurden geprüft und
bestätigt). Für die übrigen 221 Fälle ist die Abweichungszahl 0 eine Folge der pauschalen
Übernahme, keine unabhängige Bestätigung.

## 3. Häufigste FP-Ursachen (21 Fälle, aus der KI-Vorbewertung übernommen)

| root_cause | Anzahl | Bereits gefixt? |
|---|---|---|
| zubehoer_statt_geraet | 6 | Nein — strukturelles Muster, kein einfacher Exclude-Fix |
| spieltitel_ohne_konsole | 5 | Nein — bekannte, bereits dokumentierte Restlücke |
| exclude_flexionsform_nicht_erfasst | 3 | **Ja** — PR #31 (defekt-Flexionsformen + sd karten Plural) |
| notebook_als_desktop | 2 | **Ja** — PR #31 (dynabook/satellite pro/latitude) |
| defekt_nicht_erfasst | 1 | Nein — "spinnt" ist Umgangssprache, kein Wortstamm-Fix möglich |
| spielesammlung_ohne_konsole | 1 | Nein |
| nur_ersatzteil | 1 | Nein |
| falsches_produktsegment | 1 | Nein |
| ganzes_geraet_statt_teil | 1 | Nein |

**5 von 21 FP-Ursachen (24%) sind bereits durch den zuvor gemergten Fix (PR #31) behoben** —
die restlichen 16 sind entweder bereits dokumentierte, bewusst offen gelassene Strukturlücken
(Zubehör-vs-Gerät, Spieltitel-ohne-Konsole) oder Einzelfälle ohne generalisierbaren Fix.

## 4. Fälle, die trotz (bzw. mangels) menschlicher Einzelprüfung UNCLEAR bleiben

Alle 13 UNCLEAR-Fälle stammen unverändert aus der KI-Vorbewertung — keiner davon war unter den
30 einzeln durchgesprochenen Listings, keiner wurde daher tatsächlich menschlich einzeln
geprüft. Vollständige Liste mit Titel/root_cause: siehe
`WORKSHEET_LABELING_BERICHT_2026-08-14.md`, Abschnitt "Alle 13 UNCLEAR-Fälle".

## 5. Bestätigung

Es wurde ausschließlich eine neue, read-only Analyse-Datei erzeugt:
`tools/ruleset_quality/generated/human_verified_labels_2026-08-14.json` und dieser Bericht.
**Keine** Änderung an `data/found.json`, `data/price_history.jsonl`, `data/seen.json` oder
`app/rules/*.yaml`. Kein Commit, kein Push, kein Merge, kein PR.
