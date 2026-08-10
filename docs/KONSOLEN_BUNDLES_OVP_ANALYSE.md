# Strukturanalyse: konsolen_bundles (OVP-Problem), notebook_resell & handhelds (offene FP-Signale)

**Reine Analyse. Keine YAML-/Matcher-Änderung, kein Commit.** Basis: derselbe
Forensik-Datensatz (2306 sichtbare Treffer, echter Dashboard-Datenpfad) wie im
vorherigen Bericht (`DASHBOARD_MATCH_FORENSICS.md/.json`).

---

## A. konsolen_bundles: "Nintendo Switch + OVP" als vollständiges Match-Signal

### A.1 Konkrete betroffene Regeln

In `app/rules/konsolen_bundles.yaml` sind **4 von 10 Regel-Blöcken** betroffen –
alle vier verwenden dieselbe generische zweite `require_all_of`-Gruppe, die u.a.
durch das alleinstehende Wort **"ovp"** erfüllt werden kann:

| Regel-Label | Gruppe 1 (Geräte-Indikator) | Gruppe 2 (Zustands-/Bundle-Indikator) |
|---|---|---|
| `Nintendo Switch (V1/V2/OLED) ★ Top-Deal` | `["nintendo switch", "switch oled", "switch konsole"]` | `["konsole", "bundle", "set", "mit spiele", "ovp", "system"]` |
| `Nintendo Switch (V1/V2/OLED) 👍 Guter Preis` | (identisch) | (identisch) |
| `Xbox One S / One X ★ Top-Deal` | `["xbox one s", "xbox one x"]` | `["konsole", "bundle", "set", "mit spiele", "ovp", "system"]` |
| `Xbox One S / One X 👍 Guter Preis` | (identisch) | (identisch) |

**Nicht betroffen** (zur Abgrenzung): `PS4 Slim / Pro Bundle` (Gruppe 2 =
`["slim","pro","bundle","1tb","500gb","mit spiele"]`, kein "ovp") und
`Nintendo Switch Lite` (nur 1 Gruppe, kein "ovp"-Pfad). **Bonusfund** (nicht
Teil der ursprünglichen Anfrage, aber strukturell identisch): `app/rules/
handhelds.yaml`, Regel `PlayStation Vita (PCH-1000/PCH-2000)`, hat exakt
dasselbe Muster: `["ps vita","psvita","playstation vita"]` + `["konsole",
"bundle","set","ovp","system"]`.

Das eigentliche Problem ist zweistufig:
- **Gruppe 1 ist bereits sehr breit.** `"nintendo switch"` als bloßer
  Teilstring steckt in praktisch jedem Switch-*Spiel*titel ("... für Nintendo
  Switch") und jedem Switch-*Zubehör*titel ("Nintendo Switch Pro Controller").
- **Gruppe 2 lässt sich durch "ovp" allein erfüllen**, ohne dass "konsole"
  oder "system" (die einzigen wirklich geräte-spezifischen Begriffe der
  Gruppe) vorkommen müssen. "OVP" (Originalverpackung) ist aber ein
  Verkaufsargument, das genauso für ein einzelnes Spiel oder einen
  Controller in Originalverpackung gilt wie für eine Konsole.

### A.2 Konkrete Match-Ursachen -- 39 reale Beispiele aus dem Forensik-Datensatz

Abfrage des vollständigen `konsolen_bundles`-Teildatensatzes (235 sichtbare
Treffer) nach allen Fällen, in denen Gruppe 2 **ausschließlich** durch "ovp"
(26 Treffer) oder durch ein anderes generisches Wort ohne "konsole"/"system"
(13 weitere Treffer, "bundle"/"set"/"mit spiele") erfüllt wurde -- macht **39
Beispiele**, deutlich über der geforderten Mindestmenge von 20. Manuell in drei
Gruppen sortiert:

**Gruppe A -- echte Geräte (müssen weiterhin matchen), 8 von 39:**
1. `Microsoft Xbox One X 1TB Schwarz Inkl OVP Ohne Controller`
2. `Nintendo Switch V1 HAC-001 mit OVP + Komplett | BLITZVERSAND⚡️`
3. `Xbox One S 1 TB + 1 Controller - Weiß - OVP - Top Zustand`
4. `Nintendo Switch OLED Modell - Weiß - Komplett mit OVP`
5. `Nintendo Switch 1. Generation – Neon Blau/Rot – OVP + Kaufbeleg`
6. `Nintendo Switch Komplett Set OVP`
7. `Nintendo Switch Spielkonsole mit Set - Guter Zustand`
8. `Nintendo Switch Spielkonsole mit Set - Top Zustand`

**Gruppe B -- Einzelspiele mit OVP (dürfen NICHT matchen), 13 von 39:**
9. `Luigi's Mansion 2 HD für Nintendo Switch - NEU & OVP`
10. `Mario Kart World für Nintendo Switch 2 – NEU  und OVP`
11. `NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand`
12. `Star Fox "NEU & OVP" (Nintendo Switch 2)`
13. `STAR FOX - Nintendo Switch 2 - NEU-OVP - Händler YAPIDO`
14. `Metroid Prime Remastered Nintendo Switch 2023 Gebraucht In OVP  guter Zustand`
15. `Super Smash Bros. Ultimate (Nintendo Switch) (Inklusive OVP)`
16. `Pokémon Let's Go Evoli! Nintendo Switch – OVP komplett`
17. `Nintendo Pokémon Purpur Nintendo Switch neu/sealed in OVP`
18. `Nintendo Switch - Minecraft FRA mit OVP`
19. `Read Dead Redemption 1+2 PlayStation 4 PS4 Steelbook Bundle NEU OVP`
20. `Bayonetta & Vanquish 10th Anniversary Bundle - PlayStation 4 - Neu & OVP`
21. `Nintendo Switch Sports inkl. 12-in-1 Zubehör Set`

**Gruppe C -- Standalone-Controller/Zubehör mit OVP (dürfen NICHT matchen), 18 von 39:**
22. `Nintendo Switch 2 GameCube Controller | OVP | NEU`
23. `Nintendo Switch 2 GameCube Controller – Nintendo Classics – OVP – NEU`
24. `Nintendo Switch - Controller Joy-Con Neon-Grün / Neon-Pink 2er - NEU OVP`
25. `2x Nintendo Switch 2 Pro Controller NEU OVP`
26. `Nintendo Switch Pro Controller - Schwarz mit OVP kaum genutzt`
27. `Nintendo Switch Pro Controller in OVP`
28. `Nintendo Switch Pro Controller, TOP Zustand mit OVP`
29. `HORI Split Pad Pro Nintendo Switch Controller Schwarz mit OVP`
30. `NEU - OVP! Nintendo Switch Pro Controller - Monster Hunter Rise Sunbreak Edition`
31. `Nintendo Switch Pro Controller Original | OVP | TOP Zustand`
32. `Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP`
33. `Nintendo Switch Controller - Joy-Con 2er-Set Neon-Rot/Neon-Blau -NEU`
34. `Nintendo Switch OLED Joy-Con Set - Pokemon Scarlet & Violet mit Handschlaufaufen`
35. `Xbox One S 1TB mit Spiele` *(Grenzfall, siehe unten)*
36. `Nintendo Switch Grau Bundle  Neue Sticks (Kein Drift) + Extras!`
37. `Nintendo Switch Neon Bundle  Neue Sticks (Kein Drift!) + Extras`
38. `Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle Neon Blau/Rot mit Dock` *(Grenzfall, siehe unten)*
39. `Nintendo Switch HAC-001(-01) Joy-Controller Bundle 32GB Handheld-Spielekonsole` *(eigentlich Gruppe A, siehe unten)*

**Was echte Geräte (Gruppe A) von den Fehltreffern (B/C) unterscheidet:** In
allen 8 Beispielen aus Gruppe A steht **zusätzlich zu "ovp"** mindestens einer
der folgenden Marker im Titel: eine Speichergrößenangabe (`1TB`, `32GB`), ein
Modellcode (`HAC-001`), eine Generationsangabe (`V1`, `1. Generation`), "OLED
Modell", "Komplett" oder das Wort "Spielkonsole" selbst. **Keines** der 31
Beispiele aus Gruppe B/C enthält einen dieser Marker. Das ist kein Zufall,
sondern ein plausibler, wiederkehrender Verkaufsformulierungs-Unterschied:
wer ein komplettes Gerät verkauft, nennt praktisch immer Speichergröße oder
Modellvariante; wer nur ein Spiel oder Zubehörteil verkauft, tut das nicht.

**Zwei Grenzfälle, die zusätzlich auffielen (Nr. 35, 38, 39):**
- `Xbox One S 1TB mit Spiele` und `Nintendo Switch 32GB Mario Kart 8 Deluxe
  Bundle Neon Blau/Rot mit Dock` enthalten tatsächlich eine Speichergröße
  (`1TB`/`32GB`) -- nach obigem Muster wären das eher **echte Geräte-Bundles**
  (Konsole + Spiel/Dock), keine reinen Fehltreffer. Sie wurden im vorherigen
  Bericht als FALSE_POSITIVE eingestuft, weil der bisherige Klassifikator
  Speichergröße nicht als Unterscheidungsmerkmal kennt -- ein Hinweis, dass
  ein Speichergrößen-Marker auch die Klassifikationsqualität selbst verbessern
  würde, nicht nur das YAML-Regelwerk.
- `Nintendo Switch HAC-001(-01) Joy-Controller Bundle 32GB
  Handheld-Spielekonsole` trägt sowohl `HAC-001` als auch `32GB` als auch das
  Wort "Handheld-Spielekonsole" -- nach dem Muster ebenfalls eher ein echtes
  Gerät (die Modellcode-Angabe HAC-001 ist Nintendos offizielle Switch-
  Modellbezeichnung), auch wenn der Titel zusätzlich "Joy-Controller Bundle"
  enthält.

**Bekannter, bereits an anderer Stelle gelöster Nebenbefund:** "Spielkonsole"
(Kompositum aus "Spiele" + "Konsole") wird von der bestehenden Wortgrenzen-
Prüfung NICHT als Vorkommen von "konsole" erkannt (siehe
`matcher.py::_contains_term()`-Semantik) -- exakt dasselbe Muster, das für
`retro_konsolen` bereits mit "heimkonsole"/"spielekonsole" als eigene
Begriffe gelöst wurde. `konsolen_bundles` hat diese Kompositum-Varianten noch
nicht in Gruppe 2.

### A.3 Vorgeschlagene Änderung (konzeptionell -- KEINE YAML-Umsetzung in diesem Schritt)

Ziel: "ovp"/"bundle"/"set"/"mit spiele" bleiben gültige Signale (wie vom
Auftraggeber in der vorherigen Runde ausdrücklich bestätigt: "ovp bleibt
Positivsignal"), dürfen aber nicht mehr **allein** ausreichen. "konsole"/
"system" (die einzigen bereits geräte-spezifischen Wörter der Gruppe) bleiben
weiterhin allein ausreichend.

**Vorschlag: Aufteilung jeder der 4 betroffenen Regeln in zwei Varianten**
(Struktur, nicht exakter YAML-Text):

1. **"Stark"-Variante** (unverändert schnell, kein neues Kriterium):
   Gruppe 1 (wie bisher) + Gruppe 2 nur mit den bereits eindeutig
   geräte-spezifischen Begriffen `["konsole", "system", "spielkonsole",
   "spielekonsole", "heimkonsole"]` (Kompositum-Ergänzung wie oben
   beschrieben).
2. **"Schwach + abgesichert"-Variante** (neu): Gruppe 1 (wie bisher) +
   Gruppe 2 mit den generischen Begriffen `["ovp", "bundle", "set", "mit
   spiele"]` UND einer NEUEN dritten Gruppe, die einen echten
   Geräte-Beleg verlangt: Speichergrößen-Muster (`["1tb","2tb","32gb",
   "64gb","128gb","256gb","500gb","512gb"]`) ODER Modell-/Generationscode
   (`["hac-001","v1","v2","1. generation","2. generation","oled modell"]`).

Das entspricht demselben Architekturmuster, das schon für `notebook_resell`
(RAM-/SSD-Größen-Gruppe gegen Einzelteile) und `retro_konsolen`
(Kompositum-Ergänzung) etabliert ist -- keine neue Matcher-Fähigkeit
notwendig, nur eine zusätzliche `require_all_of`-Gruppe plus zwei
zusätzliche Regel-Varianten pro betroffener Preisstufe (4 betroffene
Regeln -> 8 Regelblöcke).

**Offene Entscheidung, bewusst nicht selbst getroffen:** Soll "komplett" in
die neue dritte Gruppe aufgenommen werden? Dafür spricht Beispiel 6
(`Nintendo Switch Komplett Set OVP`, vermutlich echtes Gerät, hätte ohne
"komplett" keinen anderen Marker). Dagegen spricht Beispiel 16 (`Pokémon
Let's Go Evoli! Nintendo Switch – OVP komplett`) -- hier beschreibt
"komplett" eindeutig die Vollständigkeit der Spielverpackung, nicht eines
Geräts. "Komplett" ist damit weniger zuverlässig als Speichergröße/
Modellcode und sollte vor einer Umsetzung gegen den vollständigen
sichtbaren Datensatz (nicht nur die 39 Beispiele hier) auf Kollisionen
geprüft werden -- exakt die Methodik, die bereits beim
Präzisionsphrasen-Fix verwendet wurde.

### A.4 Positive Regression Cases (müssen nach der Änderung weiterhin matchen)

1. `Microsoft Xbox One X 1TB Schwarz Inkl OVP Ohne Controller` -- via `1tb`
2. `Nintendo Switch V1 HAC-001 mit OVP + Komplett | BLITZVERSAND⚡️` -- via `v1`/`hac-001`
3. `Xbox One S 1 TB + 1 Controller - Weiß - OVP - Top Zustand` -- via `1 tb`
4. `Nintendo Switch OLED Modell - Weiß - Komplett mit OVP` -- via `oled modell`
5. `Nintendo Switch 1. Generation – Neon Blau/Rot – OVP + Kaufbeleg` -- via `1. generation`
6. `Nintendo Switch Spielkonsole mit Set - Guter Zustand` -- via `spielkonsole` (Kompositum-Fix, "Stark"-Variante, kein OVP nötig)
7. `Nintendo Switch Konsole OLED mit Zubehör` (bereits bestehender Regressionstest, `test_konsolen_bundles_precision_phrases_fix.py`) -- via `konsole` ("Stark"-Variante, unverändert)

### A.5 Negative Regression Cases (dürfen nach der Änderung weiterhin NICHT matchen)

1. `Luigi's Mansion 2 HD für Nintendo Switch - NEU & OVP` -- kein Speicher-/Modellmarker (bereits heute korrekt blockiert, muss es bleiben)
2. `Nintendo Switch 2 GameCube Controller | OVP | NEU` -- kein Marker
3. `Mario Kart World für Nintendo Switch 2 – NEU  und OVP` -- kein Marker
4. `2x Nintendo Switch 2 Pro Controller NEU OVP` -- kein Marker
5. `NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand` -- kein Marker
6. `Nintendo Switch Sports inkl. 12-in-1 Zubehör Set` -- kein Marker (Spiel + Zubehör, keine Konsole)

### A.6 Erwartetes Recall-Risiko

- **Haupt-Risiko (Recall-Verlust):** Ein echtes Gerät, dessen Titel WEDER
  Speichergröße noch Modellcode noch "konsole"/"system"/Kompositum nennt
  (z.B. ein sehr knapper Titel wie "Nintendo Switch neu, OVP" ohne jede
  weitere Angabe), würde nach der Änderung nicht mehr matchen. In den
  39 untersuchten Beispielen kam dieser Fall NICHT vor -- jedes plausible
  echte Gerät trug mindestens einen Marker. Das ist aber nur eine
  Stichprobe aus einem Snapshot; bei künftigen Scans mit anderen
  Formulierungen ist ein gewisses Restrisiko nicht auszuschließen.
  Empfehlung: nach Umsetzung eine Nachkontrolle mit einem frischen
  found.json-Export.
- **Präzisions-Risiko durch "komplett" (siehe A.3):** Wird "komplett" als
  Marker aufgenommen, entsteht ein neuer, konkret nachgewiesener Fehltreffer
  (`Pokémon Let's Go Evoli! ... OVP komplett`). Wird "komplett" NICHT
  aufgenommen, geht mindestens 1 der 8 Gruppe-A-Beispiele (`Nintendo Switch
  Komplett Set OVP`) als Recall-Verlust verloren, sofern es tatsächlich ein
  echtes Gerät ist (nicht abschließend verifizierbar allein aus dem Titel).
- **Verdopplung der Regelanzahl** für die 4 betroffenen Familien (4 -> 8
  Blöcke) erhöht die Wartungslast/Regelkomplexität in
  `konsolen_bundles.yaml` spürbar -- reines YAML-Strukturrisiko, kein
  Matching-Risiko.
- **Nicht mitgelöst:** Der separate Controller/Zubehör-Exclude-Bedarf
  (Gruppe C oben, 18 Beispiele) ist NICHT automatisch durch die
  Speichergrößen-Gruppe abgedeckt -- alle 18 Beispiele haben ohnehin keinen
  Speicher-/Modellmarker und würden bereits durch die vorgeschlagene
  Gruppe-3-Absicherung blockiert. Insofern deckt der eine Fix beide
  Root-Causes ab (Einzelspiele UND Standalone-Zubehör), ohne eine separate
  Exclude-Liste erweitern zu müssen.
- **PlayStation Vita (Bonusfund, `handhelds.yaml`)** hat dieselbe Struktur,
  wurde hier aber nicht mit eigenen Beispielen verifiziert (0 PS-Vita-
  Treffer mit diesem Muster im aktuellen Datensatz sichtbar) -- sollte bei
  einer Umsetzung aus Konsistenzgründen mitgeprüft werden, auch ohne
  aktuell nachweisbare Fehltreffer.

---

## B. notebook_resell: offene FP-Signale gruppiert

### B.1 Konkrete betroffene Regeln

`app/rules/notebook_resell.yaml`, beide ThinkPad-Regeln (identische Struktur):

| Regel-Label | Gruppe 1 | Gruppe 2 | Gruppe 3 |
|---|---|---|---|
| `ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top` | `["thinkpad","think pad"]` | `["t14","t490","x13","x390","l14"]` | `["4gb"..."512gb","1tb","2tb","ssd","nvme"]` |
| `ThinkPad T14/X13 (Ryzen/Modern)` | (identisch) | (identisch) | (identisch) |

Die `Gaming Laptop (RTX 3060/4060)`-Regeln verlangen zusätzlich das bare
Wort `"laptop"`/`"notebook"` selbst (kein reiner Modellcode) -- im aktuellen
Datensatz kein vergleichbarer Fehltreffer gefunden, strukturell aber
theoretisch demselben Risiko ausgesetzt, falls ein Verkäufer eine Einzelteil-
Anzeige mit dem Wort "Laptop"/"Notebook" im Titel formuliert (z.B. "RTX 4060
Laptop-Mainboard") -- im Bericht als 1 nicht-verifizierter Treffer mit 0
Beobachtungen markiert.

### B.2 Konkrete Match-Ursachen

Nur **1 offener FALSE_POSITIVE** im aktuellen Datensatz (60 sichtbare
Treffer): `Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM
NM-B891`. Ursache laut Regel-Kommentar (Zeilen 68-82 in
`notebook_resell.yaml`): Gruppe 3 (RAM-/SSD-Größe) wurde ursprünglich
GEZIELT ergänzt, um Einzelteil-Angebote (Power-Button, Lautsprecher,
Gehäuse, Kühler) zu blockieren, die "thinkpad"+Modellcode enthalten, aber
kein komplettes Gerät sind. Der Fix greift nicht bei Mainboard-Angeboten,
weil ein Mainboard selbst über eine verlötete/aufgesteckte RAM-Größe
verfügt, die im Titel genannt wird ("8GB RAM") -- die Gruppe-3-Bedingung
wird dadurch unbeabsichtigt erfüllt.

Root-Cause-Gruppierung (nur 1 Signal-Cluster, da nur 1 offener Fall):
- **"Mainboard"/"Motherboard" als Titel-Wort, unabhängig von RAM-Angabe** --
  1 bestätigter Fall (ThinkPad X390). Verwandte, im selben Datensatz
  gefundene Fälle mit identischem Muster in ANDEREN Kategorien (zum
  Vergleich, kein notebook_resell): `iphone` (1x, "Mainboard Platine"),
  `office_pc` (2x), `gaming_pc` (1x) -- insgesamt 5 Treffer im gesamten
  Datensatz mit demselben Root-Cause "Mainboard/Motherboard im Titel
  vorhanden, aber Regel prüft es nicht". Das deutet auf eine
  kategorieübergreifend fehlende, aber strukturell identische Lücke hin
  (kein `exclude_global`-Eintrag für "mainboard"/"motherboard").
- Sichtprüfung auf weitere, vom bisherigen Bericht evtl. nicht erfasste
  notebook_resell-Muster (Displayschaden/Platine/Gehäuse/Akku defekt/
  Scharnier) ergab **keine zusätzlichen offenen Fälle** unter den aktuell
  59 TRUE_POSITIVE-eingestuften Treffern.

### B.3 Vorgeschlagene Änderung (konzeptionell)

`"mainboard"` und `"motherboard"` als neue Einträge in `exclude_category`
von `notebook_resell.yaml` (analog zu den bereits vorhandenen `"für teile"`,
`"displayschaden"`). Da beide Wörter praktisch nie in einer echten
Komplettgerät-Anzeige vorkommen (siehe Begründung im vorherigen Forensik-
Bericht, Abschnitt 3), ist ein unbedingter Exclude (kein kontextabhängiger
`exclude_category_unless_...`) hier plausibel ausreichend -- müsste aber vor
Umsetzung gegen den vollständigen Datensatz auf Kollisionen geprüft werden
(z.B. falls ein Verkäufer ein komplettes Notebook mit "neues Mainboard
verbaut" bewirbt -- im aktuellen Datensatz kein solcher Fall beobachtet,
aber nicht auszuschließen).

### B.4 Positive Regression Cases

1. `Lenovo ThinkPad X13 16GB RAM 512GB SSD` (kein "mainboard" im Titel) -- muss weiter matchen
2. `ThinkPad T490 8GB 256GB SSD, guter Zustand` -- muss weiter matchen
3. Aus bestehendem Datensatz (TRUE_POSITIVE, stichprobenartig verifiziert): jeder der 59 aktuell korrekt matchenden notebook_resell-Treffer, die kein "Mainboard"/"Motherboard" enthalten

### B.5 Negative Regression Cases

1. `Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM NM-B891` -- muss nach Fix blockiert werden (aktuell FALSE_POSITIVE)
2. Hypothetisch (kein realer Datensatz-Treffer, aber strukturell analog): `ThinkPad T14 Motherboard defekt, 16GB RAM verlötet` -- muss blockiert bleiben
3. Hypothetisch: `ThinkPad X13 Mainboard-Tausch durchgeführt, jetzt 32GB` -- Grenzfall (könnte ein funktionierendes Komplettgerät MIT getauschtem Mainboard sein, kein Einzelteilverkauf) -- als Beispiel für die Grenze eines bare-word-Excludes markiert, nicht abschließend geklärt

### B.6 Erwartetes Recall-Risiko

Sehr gering: "mainboard"/"motherboard" als eigenständiges Titel-Wort
kommt in den 59 aktuellen TRUE_POSITIVE-Treffern kein einziges Mal vor --
ein unbedingter Exclude hätte im aktuellen Datensatz 0 Kollisionen. Das
einzige denkbare Risiko ist der oben genannte Grenzfall
("Mainboard-Tausch" als Reparaturhinweis bei einem ansonsten kompletten
Gerät) -- dafür liegt aktuell kein Beleg im Datensatz vor.

---

## C. handhelds: offene FP-Signale gruppiert

### C.1 Konkrete betroffene Regeln

`app/rules/handhelds.yaml`, alle Regeln mit **nur 1 unabhängiger
require_all_of-Gruppe** (reine Markennamen-Regeln ohne zweites
Gerätekriterium):

| Regel-Label | Gruppe 1 (einzige Gruppe) |
|---|---|
| `Valve Steam Deck ★ Top-Deal` | `["steam deck", "steamdeck"]` |
| `Valve Steam Deck 👍 Guter Preis` | (identisch) |
| `Asus ROG Ally / Lenovo Legion Go ★ Top-Deal` | `["rog ally", "legion go"]` |
| `Asus ROG Ally / Lenovo Legion Go 👍 Guter Preis` | (identisch) |

Nicht betroffen: `Nintendo New 3DS/3DS XL/2DS XL` (2 Gruppen, zweite Gruppe
verlangt zusätzlich `xl`/`new 3ds`/`new 2ds`/`konsole`) und `PlayStation
Vita` (2 Gruppen, siehe A.1-Bonusfund für deren eigenes OVP-Problem).

### C.2 Konkrete Match-Ursachen

4 offene FALSE_POSITIVE (von 26 sichtbaren handhelds-Treffern), alle mit
identischem Muster: der Markenname selbst ("Steam Deck"/"ROG Ally"/"Legion
Go") ist die EINZIGE Bedingung, jedes Angebot -- Gerät ODER Zubehör -- das
den Markennamen nennt, matcht zwangsläufig. Gruppiert nach Zubehör-Signal:

| Zubehör-Signalwort | Betroffene Titel | Aktuell in `exclude_category`? |
|---|---|---|
| `hub` | `USB-C HUB für Steam Deck HDMI 4k 60Hz USB 3.0 PD` | Nein |
| `skin`/`faceplate`/`klebefolie`/`aufkleber`/`vinyl` | `Steam Deck Skin Faceplate Schutz Klebefolie Design Vinyl Aufkleber Skins OLED` | Nein |
| `ladeadapter` | `VITURE USB-C an Brille, Ladeadapter, Laden und Spielen für Switch, Steam Deck` | Nein (nur `"ladekabel"`/`"kabel"`/`"ladegerät"` vorhanden, `"ladeadapter"` fehlt als eigenständiges Wort) |
| `reisetasche` | `JSAUX Slim-Reisetasche Für Lenovo Legion Go/Go S/Go 2, Hartschalenbeutel...` | Nein (nur bare `"tasche"` vorhanden -- "Reisetasche" ist ein Kompositum, Wortgrenzen-Matching erkennt es nicht als "tasche") |

### C.3 Vorgeschlagene Änderung (konzeptionell)

`exclude_category` in `handhelds.yaml` um die vier fehlenden Begriffe
erweitern: `"hub"`, `"skin"`, `"faceplate"`, `"vinyl"` (ggf. redundant zu
bereits vorhandenem `"klebefolie"`/Sticker-Mustern, zu prüfen), `"ladeadapter"`,
`"reisetasche"`. Da diese Regeln nur 1 Gruppe haben und daher besonders
anfällig für jedes neue Zubehörwort sind, wäre alternativ auch eine
zusätzliche zweite require_all_of-Gruppe denkbar (analog Nintendo-3DS-Regel,
verlangt zusätzlich einen Geräte-Hinweis wie Speichergröße/"konsole"/
"handheld") -- das wäre robuster gegen künftige, noch unbekannte
Zubehör-Formulierungen als eine reine Exclude-Liste, aber ein größerer
strukturmethodischer Eingriff.

### C.4 Positive Regression Cases

1. `Valve Steam Deck OLED 1TB, neuwertig` -- muss weiter matchen
2. `Asus ROG Ally Z1 Extreme, 512GB, OVP` -- muss weiter matchen
3. `Lenovo Legion Go 8" 144Hz, wie neu` -- muss weiter matchen

### C.5 Negative Regression Cases

1. `USB-C HUB für Steam Deck HDMI 4k 60Hz USB 3.0 PD` -- muss blockiert werden
2. `Steam Deck Skin Faceplate Schutz Klebefolie Design Vinyl Aufkleber Skins OLED` -- muss blockiert werden
3. `JSAUX Slim-Reisetasche Für Lenovo Legion Go/Go S/Go 2, Hartschalenbeutel` -- muss blockiert werden
4. `VITURE USB-C an Brille, Ladeadapter, Laden und Spielen für Switch, Steam Deck` -- muss blockiert werden

### C.6 Erwartetes Recall-Risiko

Gering: alle 4 Begriffe (`hub`, `skin`, `faceplate`, `vinyl`, `ladeadapter`,
`reisetasche`) sind reine Zubehör-Vokabeln, die in keinem der 22 aktuellen
TRUE_POSITIVE-Treffer dieser Kategorie vorkommen -- 0 Kollisionen im
aktuellen Datensatz. Einziges Restrisiko: "vinyl" könnte theoretisch auch in
Nicht-Zubehör-Kontexten auftauchen (z.B. "Vinyl-Finish-Gehäuse" als
Zustandsbeschreibung eines echten Geräts) -- vor Umsetzung stichprobenartig
zu prüfen, analog zur bereits etablierten Präzisionsphrasen-Methodik.
