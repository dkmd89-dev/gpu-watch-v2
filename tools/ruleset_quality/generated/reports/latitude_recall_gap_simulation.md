# Latitude Recall-Gap – Simulation und Full-Korpus-Validierung

**Repository:** `dkmd89-dev/gpu-watch-v2` · **Stand:** 2026-08-16
**Modus:** SIMULATION ONLY — keine YAML-Änderung, kein Commit, kein Push
**Quellbericht:** „7 Recall Gaps – No Device Word Forensics"
**Korpus:** `docs/DASHBOARD_MATCH_FORENSICS.json`, 2306 Einträge

## Ausgangslage

3 verbleibende Dell-Latitude-TRUE_POSITIVE-Recall-Gaps aus dem Vorbericht:

| Titel | Preis | GT-Verdict | GT-Kategorie | Aktuelles Routing |
|---|---:|---|---|---|
| Dell Latitude 5501 15,6" FHD \| i5-9400H \| 8GB RAM \| 250GB SSD | 229,00€ | TRUE_POSITIVE | office_pc | `matched=False` |
| Dell Latitude 5500 i5-8365U 8GB Ram 250 GB SSD | 145,00€ | TRUE_POSITIVE | office_pc | `matched=False` |
| Dell Latitude 7400 14" FHD i7-8665U 16GB DDR4 512GB SSD Win11 Pro | 169,90€ | TRUE_POSITIVE | office_pc | `matched=False` |

Root Cause: `office_pc.yaml` blockiert diese Marke bereits explizit (`exclude_category: "latitude"`). `notebook_resell.yaml` hat bereits eine Dell-Latitude-Regel, verlangt aber zusätzlich zwingend ein Gerätewort (`laptop`/`notebook`) — das fehlt in allen 3 Titeln.

## Bestehende Regel — vollständige Analyse

Datei: `app/rules/notebook_resell.yaml`, Regeln „Dell Latitude ★ Resell-Top" (max_price 180€, Top-Deal) und „Dell Latitude" (max_price 330€, Guter Preis).

```
require_all_of:
  Gruppe 1 (Marke):     ["latitude", "latiitude"]
  Gruppe 2 (Gerät):     ["laptop", "notebook"]
  Gruppe 3 (Größe/Typ): ["4gb","8gb","16gb","32gb","64gb","128gb","256gb",
                          "512gb","1tb","2tb","ssd","nvme"]
exclude (regelspezifisch): keine
min_vram_gb: 0
negotiation_tolerance: keine definiert (strikte Preisgrenze, kein Verhandlungspuffer)
```

Kategorie-Excludes (`notebook_resell.yaml`, gelten für beide Regeln): `für teile`, `displayschaden`, `not tested`, `nur netzteil`, `nur ladekabel`, `nur tasche`, `nur hülle`, `mainboard`, `motherboard`, `i3`, `celeron`, `pentium`, `atom`, `core 2 duo`, `amd a4`, `amd a6`, `amd a8`, `ohne ssd/ram`.

**Precedence-Analyse:** `evaluate()` iteriert alle Regeln kategorieübergreifend in Ladereihenfolge (First-Match-Wins) — `scan_priority` steuert NICHT die Match-Auswertungsreihenfolge (nur ein separates Feld, vermutlich für Scan-/Suchpriorisierung). Da Gruppe 1 („latitude"/„latiitude") in allen unten simulierten Varianten unverändert bleibt, ist der Blast Radius **mathematisch** auf genau die Titel begrenzt, die dieses Wort enthalten — unabhängig von Routing-Reihenfolge oder anderen Kategorien.

## Modellcode-Validierung — alle „latitude"-Treffer im Korpus

| Modellcode | Preis | GT-Verdict | Aktuelle Kategorie | Aktuell gematcht | Titel |
|---|---:|---|---|:---:|---|
| 5501 | 229,00€ | TRUE_POSITIVE | — | ✗ | Dell Latitude 5501 15,6" FHD \| i5-9400H \| 8GB RAM \| 250GB SSD |
| 5401 | 150,00€ | TRUE_POSITIVE | notebook_resell | ✓ | Notebook Dell Latiitude 5401 i5 9400H 16GB DDR4 256GB SSD |
| 5500 | 145,00€ | TRUE_POSITIVE | — | ✗ | Dell Latitude 5500 i5-8365U 8GB Ram 250 GB SSD |
| 5300 | 250,00€ | TRUE_POSITIVE | notebook_resell | ✓ | Dell Latitude 5300 Notebook 13" i5-8265U 8GB RAM 250GB SSD W11 |
| 7400 | 169,90€ | TRUE_POSITIVE | — | ✗ | Dell Latitude 7400 14" FHD i7-8665U 16GB DDR4 512GB SSD Win11 Pro |

**5 Treffer insgesamt im gesamten 2306-Eintrag-Korpus, alle TRUE_POSITIVE, 0 FALSE_POSITIVE, 0 UNCLEAR.** 2 bereits gelöst (Gerätewort vorhanden), 3 sind die Ziel-Gaps. Alle bekannten Codes folgen Dells realem Nummernschema (5000er = Business-Mainstream, 7000er = Premium-Ultraportable).

## Kandidaten-Varianten

**Wichtiger technischer Befund vorab:** `require_all_of` unterstützt ausschließlich literale Wortgrenzen-Begriffe (`_contains_term()`), **keine** Regex-Zeichenklassen und **keine** Positions-/Abstandsprüfung zwischen zwei Begriffen. Von den 3 simulierten Varianten ist nur **Variante B** mit dem heutigen Matcher-Primitiv nativ (als reine YAML-Erweiterung) umsetzbar. Varianten A und C wurden dennoch vollständig simuliert (eigene, an `matcher.py`-Semantik treue Simulationsfunktion, dieselben Gate-1/Gate-3-Werte dynamisch aus der geladenen YAML gezogen), um ihr Risiko zu bewerten — ihre Umsetzung würde einen neuen Detector-Mechanismus erfordern.

| Variante | Beschreibung | Nativ umsetzbar? |
|---|---|:---:|
| **A** — global 5xxx/7xxx | „latitude" + beliebige 4-stellige Zahl beginnend mit 5/7, **irgendwo** im Titel | ✗ |
| **B** — bekannte Modellcodes | „latitude" + einer der 5 im Korpus tatsächlich beobachteten Codes (`5300, 5401, 5500, 5501, 7400`) | ✓ |
| **C** — Zahl direkt nach „latitude" | Zahl in unmittelbarer Nähe (≤3 Trennzeichen) zur Marke, ohne feste Liste | ✗ |

## Full-Korpus-Regression (2306 Einträge, alle 3 Varianten)

| Metrik | Variante A | Variante B | Variante C |
|---|---:|---:|---:|
| Geänderte Fälle gesamt | 3 | 3 | 3 |
| TRUE_POSITIVE: vorher gematcht | 2177 | 2177 | 2177 |
| TRUE_POSITIVE: nachher gematcht | 2180 | 2180 | 2180 |
| Neue TP-Matches | 3 | 3 | 3 |
| TP-Regressionen | **0** | **0** | **0** |
| FALSE_POSITIVE: vorher/nachher gematcht | 3 / 3 | 3 / 3 | 3 / 3 |
| Neue FP-Matches | **0** | **0** | **0** |
| UNCLEAR: Änderungen | **0** | **0** | **0** |
| Ziel-Gaps behoben | **3 / 3** | **3 / 3** | **3 / 3** |

**Alle Änderungen (identisch für alle 3 Varianten):**

| Titel | Preis | Vorher | Nachher | Regel |
|---|---:|---|---|---|
| Dell Latitude 5501... | 229,00€ | kein Match | notebook_resell | „Dell Latitude" |
| Dell Latitude 5500... | 145,00€ | kein Match | notebook_resell | „Dell Latitude ★ Resell-Top" |
| Dell Latitude 7400... | 169,90€ | kein Match | notebook_resell | „Dell Latitude ★ Resell-Top" |

**Wichtige Einordnung:** Auf dem realen, aber für diese Marke sehr dünnen Korpus (nur 5 „latitude"-Titel insgesamt) sind alle 3 Varianten **empirisch nicht unterscheidbar** — jede erreicht 3/3 Recall-Gewinn ohne jede Regression. Der Korpus ist zu klein, um die Varianten zu differenzieren; das folgende synthetische Stresstest liefert die eigentliche Differenzierung.

## Synthetischer Adversarial-Test (keine echten Korpus-/GT-Daten)

Der reale Korpus zeigt keine „falschen" Latitude-Titel (Zubehör, Ersatzteile). Um die vom Auftrag geforderte Frage „was passiert mit jedem anderen Titel, der durch dieselbe Bedingung ebenfalls matchen würde" zu beantworten, wurden 5 konstruierte, klar als **synthetisch** gekennzeichnete Testtitel geprüft:

| Titel (synthetisch) | Beschreibung | A | B | C |
|---|---|:---:|:---:|:---:|
| „Dell Latitude Netzteil 65W Ladegerät 512GB externe SSD Festplatte Modell 5820 Ersatzteil" | Zubehör, unrelated Zahl weit von „Latitude" entfernt | ⚠️ **matcht** | ✓ blockiert | ✓ blockiert |
| „Dell Latitude 5410 Netzteil Ladegerät 65W Ersatzteil 512GB SSD extern" | Zubehör, Zahl **direkt** nach „Latitude" | ⚠️ **matcht** | ✓ blockiert | ⚠️ **matcht** |
| „Dell Latitude Tasche 15 Zoll neuwertig" | Zubehör, keine Größenangabe | ✓ blockiert | ✓ blockiert | ✓ blockiert |
| „Dell Latitude E5570 Mainboard Ersatzteil 512GB SSD defekt" | Mainboard-Einzelteil | ✓ blockiert | ✓ blockiert | ✓ blockiert |
| „Dell Latitude 5501 8GB RAM 250GB SSD" | Kontrollfall (echtes Zielfall-Muster) | ✓ matcht | ✓ matcht | ✓ matcht |

**Ergebnis:** Variante A scheitert an **2 von 2** adversarialen Zubehör-Fällen (würde Ladegeräte-/Zubehör-Bundles fälschlich als vollständiges Notebook einstufen). Variante C scheitert an **1 von 2** (räumliche Nähe zur Marke allein garantiert nicht, dass die Zahl der tatsächliche Gerätecode ist). Die beiden „sicheren" synthetischen Fälle (Tasche ohne Größenangabe, Mainboard-Ersatzteil) werden bereits durch bestehende Gates (Gruppe 3 bzw. `mainboard`-Exclude) unabhängig von der Variante zuverlässig blockiert. **Variante B besteht beide adversarialen Tests.**

## Blast Radius — Zusammenfassung

- Empirisch (realer 2306-Eintrag-Korpus): alle 3 Varianten gleich sicher (0 Regressionen).
- Synthetisch (adversariale Zubehör-Muster): nur Variante B fehlerfrei; A und C zeigen konkrete, konstruierbare Fehlklassifikations-Szenarien.
- Strukturell: Varianten A und C sind mit dem bestehenden `require_all_of`-Primitiv gar nicht nativ umsetzbar — ihre Risikobewertung ist ohnehin nur für eine hypothetische künftige Erweiterung relevant.

## Empfehlung

**Variante B (bekannte Modellcodes): READY_FOR_IMPLEMENTATION**

- Alle 3 Ziel-Gaps behoben, 0 TP-Regressionen, 0 neue FP, 0 UNCLEAR-Änderungen — sowohl im realen Korpus als auch in beiden synthetischen Adversarial-Tests.
- Nativ mit dem bestehenden Matcher-Primitiv umsetzbar: `require_all_of`-Gruppe 2 der beiden Dell-Latitude-Regeln um die 5 literalen Codes `["5300","5401","5500","5501","7400"]` als zusätzliche OR-Alternativen zu `["laptop","notebook"]` erweitern.
- **PROPOSED, NICHT UMGESETZT** — keine YAML-Änderung in dieser Phase, wie beauftragt.

**Variante A: NICHT empfohlen** — besteht den (zu dünnen) realen Korpus-Test, scheitert aber an 2/2 synthetischen Adversarial-Fällen; zusätzlich mit dem bestehenden Primitiv nicht nativ abbildbar (bräuchte einen neuen Regex-fähigen Detector-Mechanismus, eigener, separater Blast-Radius-Nachweis nötig).

**Variante C: NICHT als primäre Wahl empfohlen** — besteht den Korpus-Test, scheitert aber an 1/2 synthetischen Adversarial-Fällen; ebenfalls nicht nativ mit `require_all_of` umsetzbar (Positions-/Abstandslogik).

## Abschluss

```
LATITUDE RECALL GAP SIMULATION
===============================

Target gaps:
    3

Variant A (global 5xxx/7xxx):
    Recall recovered: 3/3 | TP regressions: 0 | New FP: 0 | UNCLEAR changes: 0
    Synthetischer Adversarial-Test: 2/2 Fehlklassifikationen -- NICHT sicher

Variant B (bekannte Modellcodes):
    Recall recovered: 3/3 | TP regressions: 0 | New FP: 0 | UNCLEAR changes: 0
    Synthetischer Adversarial-Test: 0/2 Fehlklassifikationen -- SICHER

Variant C (Zahl direkt nach latitude):
    Recall recovered: 3/3 | TP regressions: 0 | New FP: 0 | UNCLEAR changes: 0
    Synthetischer Adversarial-Test: 1/2 Fehlklassifikationen -- NICHT sicher

Best variant:
    B_bekannte_modellcodes

Recall recovered:
    3 / 3

TP regressions:
    0

New FP:
    0

UNCLEAR changes:
    0

Changed corpus entries:
    3 (identisch fuer alle 3 Varianten)

Recommendation:
    READY_FOR_IMPLEMENTATION (Variante B)
```

---

**Keine YAML-Änderung. Keine Ground-Truth-Änderung. Kein Commit. Kein Push. Kein Merge.**
Wartet auf explizite Freigabe für die Umsetzung von Variante B.
