# Phase 15 – Rule Analysis Report

**Stand:** 2026-08-09 · **Status:** Analyse abgeschlossen (Phase 15, Schritt 3). Keine YAML-Änderung, keine Fixes umgesetzt.

Analysiert mit `app/rule_analyzer.py` (Phase 15, Schritt 2) gegen den aktuellen
Produktivstand des Regelwerks (`app/rules/*.yaml`, Verzeichnis-Modus,
`matcher.load_rules("rules")`). Reiner Lesezugriff — der Analyzer verändert
keine YAML-Datei (Auftragsvorgabe, Abschnitt 14).

---

## 1. Lauf-Ergebnis

```
RULE ANALYSIS REPORT
====================

Categories: 19
Rules: 355

Errors: 0
Warnings: 0
Info: 2

Potential duplicates: 0
Potential overlaps: 2
Potential shadowed rules: 0
Suspicious require_all_of: 0
Exclude conflicts: 0
Unreachable rules: 0
```

**Einordnung:** Ein nahezu befundfreies Ergebnis ist hier kein Zeichen für
einen zu schwachen Analyzer, sondern die erwartbare Konsequenz der bereits
in Phase 12–14 geleisteten Bereinigungsarbeit:

- Der Phase-12-Bug (`require_all_of: [["lego", "star wars"]]` als
  ODER-Gruppe statt zwei UND-Gruppen) ist in den betroffenen Regeln
  (`lego_sw_rare`, `lego_sw_clone`) bereits behoben und durch bestehende
  Regressionstests (`test_matcher_price_calibration_matching_fixes.py`)
  abgesichert — der `suspicious_require_all_of`-Check findet dort
  konsequent 0 Treffer.
- Der Phase-14-Fund (Handheld-/Konsolen-Zubehör-Fehltreffer bei
  `handhelds`/`konsolen_bundles`) ist ebenfalls bereits gefixt
  (Commit `b13559d`).

Der Analyzer wurde während der Implementierung bewusst gegen dieses
bereits bereinigte Ruleset kalibriert (siehe Abschnitt 4) und zusätzlich
mit synthetischen Regressionsfixtures verifiziert, die den historischen
Phase-12-Bug nachbilden (`app/tests/test_rule_analyzer.py`,
`test_lego_star_wars_ein_gruppe_wird_als_suspicious_erkannt`) — der Check
erkennt das Muster zuverlässig, sobald es vorkommt.

---

## 2. Die 2 Infos im Detail

Beide stammen aus der Overlap-Prüfung (Abschnitt 8 des Auftrags) und
betreffen dasselbe Regelpaar in `app/rules/gpu.yaml`:

```
INFO  overlap  Kategorie: gpu
Regel:        "RX 7600 XT"
Andere Regel: "RX 7600 ★ Top-Deal"
Geteilter Begriff: "rx 7600"

INFO  overlap  Kategorie: gpu
Regel:        "RX 7600 XT"
Andere Regel: "RX 7600"
Geteilter Begriff: "rx 7600"
```

**Befund (nur Beobachtung, keine Änderung):** Die Regel `RX 7600 XT`
(Zeile ~440 in `gpu.yaml`, iteriert VOR den `RX 7600`-Regeln) listet
`"rx 7600"` als eigenständigen `match`-Begriff — zusätzlich zu den
spezifischeren Begriffen `"7600 xt"`/`"7600xt"`. Da `evaluate()` die
erste passende Regel gewinnen lässt (first-match-wins,
`compute_ruleset_signature()`-Docstring), könnte ein Titel wie
*"AMD RX 7600 8GB Grafikkarte"* (ohne "XT") theoretisch bereits über den
Begriff `"rx 7600"` in der `RX 7600 XT`-Regel landen, bevor die eigentlich
zuständige `RX 7600`-Regel geprüft wird.

Dagegen sprechen zwei Beobachtungen, die eine sofortige Einstufung als
Bug verhindern:
- Die `RX 7600 XT`-Regel hat ein knapperes `max_price` (230 €) als die
  `RX 7600`-Regeln (160/210 €) — ein zu teures Nicht-XT-Angebot würde
  ohnehin nicht fälschlich matchen, ein günstiges schon.
- Ob `"rx 7600"` als eigener match-Begriff bei der XT-Regel beabsichtigt
  ist (z.B. weil manche Anzeigen "RX 7600" schreiben, aber XT meinen) oder
  ein Kopier-/Nachlässigkeitsfehler ist, lässt sich ohne Rücksprache mit
  den Originalquellen/der Preishistorie nicht abschließend klären.

**Empfehlung:** Für eine spätere, separat freizugebende YAML-Änderung
(STOP 3 des Auftrags) prüfen, ob `"rx 7600"` aus der `RX 7600 XT`-Regel
entfernt werden sollte (die Begriffe `"7600 xt"`/`"7600xt"` allein
reichen zur Erkennung aus). In Phase 15, Schritt 3, wird **keine**
YAML-Änderung vorgenommen — reine Diagnose gemäß Auftrag.

---

## 3. Was NICHT gefunden wurde (und warum das aussagekräftig ist)

| Check | Funde | Kommentar |
|---|---|---|
| Struktur (7.1) | 0 | Keine fehlenden Pflichtfelder, keine ungültigen `require_all_of`/`exclude`-Strukturen, keine unbekannten Regelfelder in den 355 Produktivregeln. |
| Duplicate Detection (7.2) | 0 | Keine zwei Regeln mit identischer Matching-Bedingung (match/require_all_of/requirements/exclude/max_price); kein `price_history_model`, das über Kategoriegrenzen hinweg geteilt wird. |
| Shadowed Rules (9) | 0 | Keine `match`-basierte Regel wird durch eine früher iterierte, lexikalisch breitere Regel derselben Kategorie bei mindestens gleich weitem Preisfenster verdeckt. |
| Suspicious require_all_of (10) | 0 | Kein Fall eines kategorieweit ubiquitären Begriffs (≥ 40 % der Regeln einer Kategorie mit ≥ 5 Regeln), der zusammen mit einem spezifischen Begriff in einer einzelnen ODER-Gruppe steht. |
| Exclude Conflicts (11) | 0 | Kein geforderter Begriff (match/require_all_of) ist gleichzeitig ausgeschlossen (exclude/exclude_category/nicht freigegebener exclude_global-Begriff). |
| Unreachable Rules (12) | 0 | Keine Regel ist durch leere require_all_of-Gruppen oder vollständige Exclude-Blockade strukturell garantiert unerreichbar. |

**Wichtiger Hinweis zu den Grenzen dieser Aussage** (siehe
`rule_analyzer.py`-Moduldocstring): Shadow- und Overlap-Erkennung sind
lexikalische Heuristiken, kein vollständiger Boolean-Solver. Insbesondere
`require_all_of`-basierte Regeln werden von Shadow-/Overlap-Checks bewusst
ausgeklammert (siehe Abschnitt 4) — ein "0" bei diesen Checks bedeutet
"kein mit der implementierten Heuristik nachweisbarer Fall", nicht
"mathematisch bewiesen fehlerfrei".

---

## 4. Kalibrierungshinweis (Transparenz zur Methodik)

Eine erste, unkalibrierte Version des Overlap- und
`suspicious_require_all_of`-Checks erzeugte gegen dasselbe Ruleset
**> 14.000 Funde** — weit überwiegend Rauschen:

- Einzelne generische Wörter (`"defekt"`, `"controller"`, `"display"`)
  kollidierten über völlig unabhängige Kategorien hinweg.
- Begriffe aus verschiedenen `require_all_of`-UND-Gruppen wurden wie
  eigenständig matchfähige ODER-Begriffe behandelt (z.B. `"128 gb"` als
  vermeintliche Überschneidung zwischen iPhone- und MacBook-Regeln,
  obwohl beide Regeln zusätzlich eine sich gegenseitig ausschließende
  Marken-Gruppe verlangen).
- Die `suspicious_require_all_of`-Erstversion (Label-Textabgleich) meldete
  legitime Alternativpaare wie `"rog ally"/"legion go"` fälschlich als
  Bugmuster.

Nach Kalibrierung (Mehrwort-Phrasen, match-only-Vergleich für Overlap;
kategorieweite Begriffshäufigkeit statt Label-Textabgleich für
`suspicious_require_all_of`) liefert der Analyzer die oben dokumentierten
0/0/2-Zahlen — konsistent mit "Precision > Recall" (Auftrag, Abschnitt 34)
und mit dem bereits bereinigten Zustand des Regelwerks nach Phase 12–14.
Details und Begründung stehen als Docstrings direkt bei den jeweiligen
Prüfungen in `app/rule_analyzer.py`.

---

## 5. Nächste Schritte laut Auftrag

Dies ist **STOP 2** (Auftrag, Abschnitt 32): Alle gefundenen ERROR/
WARNING/INFO sind hiermit vor jeder Implementierung von Fixes
dokumentiert. Da 0 Errors und 0 Warnings vorliegen und die einzigen 2
Infos eine reine Beobachtung ohne dringenden Handlungsbedarf sind, gibt
es aktuell **keinen Fix-Rückstand**, der vor Fortsetzung mit Phase 15,
Schritt 4 (False-Positive Regression Suite) geklärt werden müsste.

Eine mögliche YAML-Korrektur der `RX 7600 XT`-Regel (Abschnitt 2 oben)
wäre eine eigenständige, separat zu genehmigende Änderung (STOP 3) —
nicht Teil dieses Analyseschritts.

---

## Testanzahl und Ergebnis

`pytest app/tests/` → **908 passed, 0 failed** (868 vor Phase 15, Schritt
2, + 40 neue Rule-Analyzer-Tests). Keine bestehende Datei verändert, keine
YAML-Datei angefasst.
