# Review-Bericht: konsolen_bundles -- "Plattformbegriff + OVP" als Fehlsignal

**Reine Analyse. Keine YAML-/Matcher-Änderung, kein Commit, kein Push.**
`found.json`, `seen.json`, `price_history.jsonl` unangetastet. Basis: derselbe
Forensik-Datensatz wie in den vorherigen Berichten (235 sichtbare
`konsolen_bundles`-Treffer, davon 195 TRUE_POSITIVE / 40 nicht-TRUE laut
Diagnose-Klassifikator), zusätzlich direkte Prüfung der realen
`_contains_term_unless_preceded_by()`-Funktion aus `app/matcher.py` gegen
alle 195 TRUE_POSITIVE-Titel, um jeden Lösungsvorschlag VOR der Empfehlung
gegen echte Kollisionen zu testen (nicht nur gegen die vom Auftraggeber
genannten Beispiele).

---

## 1. Aktueller Match-Mechanismus

### 1.1 Alle Regeln in `app/rules/konsolen_bundles.yaml`

| Regel-Label | Gruppe 1 (Plattform) | Gruppe 2 (Zustand/Bundle) | Rolle von OVP |
|---|---|---|---|
| `PS4 / Xbox One (Defekt / Bastler)` ×2 | `ps4`, `playstation 4`, `xbox one` | `defekt`, `bastler`, `für bastler`, `geht nicht an`, `laut`, `überhitzt`, `piept` | keine |
| `Nintendo Switch (V1/V2/OLED)` ×2 | `nintendo switch`, `switch oled`, `switch konsole` | `konsole`, `bundle`, `set`, `mit spiele`, **`ovp`**, `system` | **alleinstehend ausreichend** |
| `Nintendo Switch Lite` ×2 | `switch lite`, `nintendo switch lite` (nur 1 Gruppe) | -- | kein OVP-Pfad (1 Gruppe reicht) |
| `PS4 Slim / Pro Bundle` ×2 | `ps4`, `playstation 4` | `slim`, `pro`, `bundle`, `1tb`, `500gb`, `mit spiele` | **kein OVP** in dieser Gruppe |
| `Xbox One S / One X` ×2 | `xbox one s`, `xbox one x` | `konsole`, `bundle`, `set`, `mit spiele`, **`ovp`**, `system` | **alleinstehend ausreichend** |

**Nur 4 von 10 Regel-Blöcken sind betroffen** (`Nintendo Switch V1/V2/OLED`
×2, `Xbox One S/One X` ×2) -- exakt dort, wo "ovp" Teil von Gruppe 2 ist
und OHNE zusätzliche Bedingung ausreicht. `PS4 Slim/Pro Bundle` hat KEIN
"ovp" in Gruppe 2 (dort sind es Modellvarianten wie "slim"/"pro"/Speicher-
größen) -- strukturell bereits robuster. `Nintendo Switch Lite` hat nur 1
Gruppe, dafür aber einen eindeutigen Mehrwort-Produktnamen als einzige
Bedingung (`switch lite`), kein generisches Zustandswort -- ebenfalls
nicht betroffen.

**Bereits vorhandene Excludes** (`exclude_category`, Auszug, gekürzt):
`hülle`, `case`, `tasche`, `ovp nur`, `nur karton`, `leerkarton`, `nur
spiele`, `spiel für`, `spiel`, `spielesammlung`, `nur controller`,
`station`, `lüfter`, `ständer`, `netzteil`, `ladekabel`, `kabel`,
`ladegerät`, `anleitung`, `modding service`, `reparatur service`,
`repair service`, plus 6 phrasenbasierte Ergänzungen aus dem
vorangegangenen Präzisionsphrasen-Fix (`mini arcade`, `limited run`, `pro
skater`, `spiele-wahl`, `spieleauswahl`, `evolution soccer`, `controller
für`, `controller defekt`, `wireless controller`, `schutzhülle`, `gaming
headset`, `dock set`, `modchip`, `scuff`, `racing wheel`, `zubehör-set`,
`zubehörset`, `versand aus deutschland`). **NICHT vorhanden:** ein
generisches "[X] für Plattform"-Muster, ein "Pro Controller"-Muster, ein
Kompositum-Eintrag für "spielkonsole"/"heimkonsole".

### 1.2 Warum "Nintendo Switch" + "OVP" allein ausreicht

Gruppe 1 wird durch den bloßen Teilstring `"nintendo switch"` erfüllt --
der steckt in JEDEM Switch-Spieltitel ("... für Nintendo Switch") und
JEDEM Switch-Zubehörtitel ("Nintendo Switch Pro Controller") genauso wie
in einer echten Konsolenanzeige. Gruppe 2 wird durch das bloße Wort
`"ovp"` erfüllt -- ein Verkaufsargument, das für ein einzelnes Spiel in
Originalverpackung genauso gilt wie für eine Konsole. Beide Bedingungen
zusammen sind matching-technisch erfüllbar, ohne dass irgendein
Wort im Titel tatsächlich auf **Hardware** hindeutet.

---

## 2. Root Causes, gruppiert nach Produktart

Alle 40 aktuell nicht als TRUE_POSITIVE eingestuften `konsolen_bundles`-
Treffer, kategorisiert:

| Produktart | Anzahl | Charakteristik |
|---|---:|---|
| **Spiele/Software** | 13 | Eigenname-Spieltitel (Luigi's Mansion, Mario Kart, NBA 2K26, Star Fox, Metroid Prime, Super Smash Bros, Pokémon-Reihe, Minecraft, Read Dead Redemption, Bayonetta&Vanquish, Nintendo Switch Sports) + "ovp"/"bundle" -- keine Konsole im Angebot |
| **Controller** | 12 | Standalone-Controller (GameCube-Style-Controller, Pro Controller, Joy-Con-Sets) + "ovp" -- keine Konsole im Angebot |
| **sonstiges Zubehör** | 3 | Joy-Con-/Stick-Reparatursets, Zubehör-Bundles ohne Konsolengehäuse |
| **Ersatzteile** | 0 | In dieser Kategorie aktuell kein beobachteter Fall (anders als `notebook_resell`/`iphone`/`office_pc`, wo "Mainboard"-Muster auftreten) |
| **Konsolen-Zubehör (Grenzfälle, vermutlich TRUE)** | 11 | Enthalten tatsächlich einen Geräte-Marker (Speichergröße, Modellcode, "Spielkonsole") -- vermutlich vom DIAGNOSE-Klassifikator, nicht von der Produktivregel, fehlbewertet (siehe 2.1) |
| **andere** | 1 | Reparatur-Dienstleistungsangebot ohne die Phrase "reparatur service" (Lücke in der bereits existierenden Service/Modding-Exclude-Phrase, separates, kleineres Thema) |

### 2.1 Wichtige Einschränkung: "Konsolen-Zubehör"-Grenzfälle sind vermutlich KEINE echten Fehltreffer der Regel

11 der 40 Fälle (`Microsoft Xbox One X 1TB ... Ohne Controller`, `Nintendo
Switch 32GB Mario Kart 8 Deluxe Bundle ... mit Dock`, `Xbox One S 1 TB + 1
Controller ...`, `Nintendo Switch HAC-001(-01) Joy-Controller Bundle 32GB
Handheld-Spielekonsole`, `Nintendo Switch OLED Modell ... Komplett mit
OVP`, `Nintendo Switch 1. Generation ...`, `Nintendo Switch V1 HAC-001 mit
OVP + Komplett`, `Nintendo Switch Komplett Set OVP`, `Nintendo Switch
Spielkonsole mit Set` ×2, `Xbox One S 1TB mit Spiele`) enthalten
tatsächlich einen Speicher-/Modell-/Kompositum-Marker (`1TB`, `32GB`,
`HAC-001`, `V1`, `1. Generation`, `Spielkonsole`) -- der DIAGNOSE-
Klassifikator aus dem vorherigen Bericht kennt diese Marker nicht und
stuft sie konservativ als FALSE_POSITIVE/UNCLEAR ein. Das ist eine
Einschränkung des Analyse-Werkzeugs, **nicht** der Produktivregel selbst
(die Produktivregel matcht diese Titel korrekt). Sie sind daher aus der
eigentlichen "muss gefixt werden"-Betrachtung herausgenommen und tauchen
unten nur als zusätzliche **positive** Regressionsbeispiele auf.

**Verbleibende, tatsächlich zu adressierende Fehltreffer: 13 (Spiele) + 12
(Controller) + 3 (sonstiges Zubehör) = 28 von 40.**

---

## 3. Beispiele

### 3.1 False Positives -- alle 28 tatsächlich zu adressierenden Fälle

**Spiele/Software (13):**
1. `Luigi's Mansion 2 HD für Nintendo Switch - NEU & OVP`
2. `Mario Kart World für Nintendo Switch 2 – NEU  und OVP`
3. `NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand`
4. `Star Fox "NEU & OVP" (Nintendo Switch 2)`
5. `STAR FOX - Nintendo Switch 2 - NEU-OVP - Händler YAPIDO`
6. `Metroid Prime Remastered Nintendo Switch 2023 Gebraucht In OVP guter Zustand`
7. `Super Smash Bros. Ultimate (Nintendo Switch) (Inklusive OVP)`
8. `Pokémon Let's Go Evoli! Nintendo Switch – OVP komplett`
9. `Nintendo Pokémon Purpur Nintendo Switch neu/sealed in OVP`
10. `Nintendo Switch - Minecraft FRA mit OVP`
11. `Read Dead Redemption 1+2 PlayStation 4 PS4 Steelbook Bundle NEU OVP`
12. `Bayonetta & Vanquish 10th Anniversary Bundle - PlayStation 4 - Neu & OVP`
13. `Nintendo Switch Sports inkl. 12-in-1 Zubehör Set`

**Controller (12):**
14. `Nintendo Switch 2 GameCube Controller | OVP | NEU`
15. `Nintendo Switch 2 GameCube Controller – Nintendo Classics – OVP – NEU`
16. `2x Nintendo Switch 2 Pro Controller NEU OVP`
17. `Nintendo Switch Pro Controller - Schwarz mit OVP kaum genutzt`
18. `Nintendo Switch Pro Controller in OVP`
19. `Nintendo Switch Pro Controller, TOP Zustand mit OVP`
20. `HORI Split Pad Pro Nintendo Switch Controller Schwarz mit OVP`
21. `NEU - OVP! Nintendo Switch Pro Controller - Monster Hunter Rise Sunbreak Edition`
22. `Nintendo Switch Pro Controller Original | OVP | TOP Zustand`
23. `Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP`
24. `Nintendo Switch Controller - Joy-Con 2er-Set Neon-Rot/Neon-Blau -NEU`
25. `Nintendo Switch - Controller Joy-Con Neon-Grün / Neon-Pink 2er - NEU OVP`

**sonstiges Zubehör (3):**
26. `Nintendo Switch Grau Bundle  Neue Sticks (Kein Drift) + Extras!`
27. `Nintendo Switch Neon Bundle  Neue Sticks (Kein Drift!) + Extras`
28. `Nintendo Switch OLED Joy-Con Set - Pokemon Scarlet & Violet mit Handschlaufaufen`

*(Für jeden Titel gilt derselbe Match-Pfad: Gruppe 1 durch bloßes
`"nintendo switch"`/`"xbox one s"` erfüllt, Gruppe 2 ausschließlich durch
`"ovp"`/`"bundle"`/`"mit spiele"` erfüllt, keine der aktuell 30+
`exclude_category`-Einträge greift, kein `exclude_category_unless_...`-
Mechanismus in dieser Kategorie deckt diese Muster ab.)*

### 3.2 True Positives -- 33 reale Beispiele (repräsentativ über alle 10 Regel-Blöcke)

*(vollständiger Match-Pfad je Titel; G1/G2 = tatsächlich erfüllte
require_all_of-Treffer)*

| Titel | Preis | Regel | G1 | G2 |
|---|---:|---|---|---|
| `Nintendo Switch Konsole gebraucht Auswahl- Neon-Rot-Blau, Grau ✅` | 79€ | Switch V1/V2/OLED ★ | nintendo switch, switch konsole | konsole |
| `Nintendo Switch Konsole Grau Joy-Con Controller` | 110€ | Switch V1/V2/OLED ★ | nintendo switch, switch konsole | konsole |
| `Nintendo Switch Konsole inkl. Zubehör` | 95€ | Switch V1/V2/OLED ★ | nintendo switch, switch konsole | konsole |
| `Nintendo Switch Konsole mit Zubehör und Mario Kart 8 Deluxe` | 125€ | Switch V1/V2/OLED 👍 | nintendo switch, switch konsole | konsole |
| `Nintendo Switch Konsole OLED mit Zubehör` | 150€ | Switch V1/V2/OLED 👍 | nintendo switch, switch konsole | konsole |
| `Nintendo Switch 1 (Konsole) voll funktionstüchtig!` | 150€ | Switch V1/V2/OLED 👍 | nintendo switch | konsole |
| `Nintendo Switch Lite in Koralle - technisch einwandfrei` | 60€ | Switch Lite ★ | switch lite | (nur 1 Gruppe) |
| `Switch Lite Go Gelb` | 49€ | Switch Lite ★ | switch lite | (nur 1 Gruppe) |
| `Nintendo Switch Lite 32 GB Handheld-System Rosa, HDH-001` | 50€ | Switch Lite ★ | switch lite | (nur 1 Gruppe) |
| `Nitendo switch Lite + pokemon schild` | 80€ | Switch Lite 👍 | switch lite | (nur 1 Gruppe) |
| `Nintendo Switch Lite Konsole Pokemon Palkia Edition` | 85€ | Switch Lite 👍 | switch lite | (nur 1 Gruppe) |
| `Microsoft Xbox Series X/S und Xbox One Controller, defekt (Stickdrift)` | 19€ | Bastler ★ | xbox one | defekt |
| `Xbox one controller titanfall edition(Defekt) + Zubehör` | 35€ | Bastler 👍 | xbox one | defekt |
| `PS4 Slim, 500gb , voll funktionsfähig` | 70€ | PS4 Slim/Pro ★ | ps4 | slim, 500gb |
| `Sony PlayStation 4 Slim 500 GB Spielekonsole - Jet Black` | 70€ | PS4 Slim/Pro ★ | playstation 4 | slim |
| `PlayStation 4 mit Controller 500GB Ps4` | 65€ | PS4 Slim/Pro ★ | ps4, playstation 4 | 500gb |
| `Sony PlayStation 4 Slim 500GB Schwarz mit DualShock 4 Controller & Headset` | 55€ | PS4 Slim/Pro ★ | playstation 4 | slim, 500gb |
| `PlayStation 4 pro mit 2 Controller` | 90€ | PS4 Slim/Pro 👍 | playstation 4 | pro |
| `Ps4 slim 3 Controller 500 GB !` | 100€ | PS4 Slim/Pro 👍 | ps4 | slim |
| `PlayStation 4 Slim  1 TB inkl. Controller & Ladestation` | 80€ | PS4 Slim/Pro 👍 | playstation 4 | slim |
| `Sony PlayStation 4 PS4 1TB Konsole mit Controller` | 95€ | PS4 Slim/Pro 👍 | ps4, playstation 4 | 1tb |
| `Microsoft Xbox One S 1TB Konsole Rot/Schwarz` | 44€ | Xbox One S/X ★ | xbox one s | konsole |
| `Microsoft Xbox One S 1TB Weiß Konsole` | 55€ | Xbox One S/X ★ | xbox one s | konsole |
| `Xbox One S 500 GB Konsole - Weiß` | 60€ | Xbox One S/X ★ | xbox one s | konsole |
| `Xbox One S 1TB Konsole in Weiß inkl. Controller` | 70€ | Xbox One S/X 👍 | xbox one s | konsole |
| `Xbox One S Konsole mit Controller` | 80€ | Xbox One S/X 👍 | xbox one s | konsole |
| `Xbox One S 500 GB Konsole mit Controller in OVP` | 80€ | Xbox One S/X 👍 | xbox one s | konsole, ovp |

*(27 gezeigt, weitere 6 in den Rohdaten `forensics_records.json`
verfügbar -- insgesamt 195 TRUE_POSITIVE im Datensatz, weit über der
geforderten Mindestmenge von 20.)*

---

## 4. Antworten auf die vier gestellten Detailfragen

**"Kann OVP aus bestimmten require_all_of-Gruppen entfernt oder anders
eingesetzt werden?"** -- Entfernen: NEIN, direkt ausgeschlossen durch die
Auftragsvorgabe `Nintendo Switch mit OVP → MATCH` (dieser Titel hat außer
"ovp" kein zweites Gruppe-2-Wort -- ohne "ovp" würde diese Regel für ihn
gar nicht mehr greifen, was der Vorgabe widerspricht). "Anders einsetzen"
im Sinne einer Gruppe-3-Zusatzbedingung ("ovp" nur gültig in Kombination
mit einem Speicher-/Modellmarker) wurde geprüft und **verworfen** -- siehe
Variante B unten, kollidiert direkt mit derselben Vorgabe.

**"Kann ein echtes Geräte-/Konsolensignal verlangt werden, das bei
Spielen/Zubehör typischerweise fehlt?"** -- Für Gruppe 1 selbst: NEIN
(dieselbe Kollision wie oben, `Nintendo Switch mit OVP` hat kein solches
Zusatzsignal). Als EXCLUDE-seitige Bedingung (nicht als zusätzliches
Pflichtkriterium): JA, wirksam einsetzbar über die Muster "für Plattform"
und "Pro Controller" (siehe Variante C, empfohlen).

**"Können bestehende Exclude-Mechanismen gezielt eingesetzt werden?"** --
Teilweise. `exclude_category` (unbedingt) ist für die "für Plattform"-
Phrase geeignet. `exclude_category_unless_preceded_by` (Variante-C-
Mechanismus, bereits in `controller.yaml` produktiv) ist für die enge
Phrase "pro controller" geeignet, aber **NICHT sicher für bare
"controller"** -- Test gegen alle 195 TRUE_POSITIVE-Titel zeigt 14+ echte
Bundle-Titel, bei denen "Controller" von einer ZAHL statt einem
Konnektor-Wort eingeleitet wird (`"2 Controller"`, `"3 Controller"`, `"4
Controller"`, `"1x Controller"` usw.) -- der Mechanismus erkennt laut
eigener Dokumentation nur EIN direkt vorausgehendes Wort aus einer festen
Konnektor-Liste, keine Zahlen/Mengenangaben. Ein bare-"controller"-
Exclude würde diese 14+ Titel fälschlich blockieren.

**"Gibt es bereits ein Muster in anderen Kategorien, das wir sicher
wiederverwenden können?"** -- JA, zwei: (1) die Kompositum-Ergänzung
("heimkonsole"/"spielekonsole" als eigene Begriffe neben "konsole"),
bereits produktiv in `retro_konsolen.yaml` verifiziert; (2) die
"Variante C"-Konnektor-Logik (`exclude_category_unless_preceded_by`),
bereits produktiv in `controller.yaml` für "ladekabel"/"netzteil"/
"ladegerät"/"anleitung" verifiziert -- hier wiederverwendet für "pro
controller" statt bare "controller" (siehe oben).

---

## 5. Lösungsvarianten

### Variante A -- nur "für Plattform"-Phrasen-Exclude (unbedingt)

`exclude_category` um `"für nintendo switch"`, `"für switch"`, `"für
ps4"`, `"für ps5"`, `"für playstation 4"`, `"für playstation 5"`, `"für
xbox"`, `"für xbox one"`, `"für xbox series"` erweitern.

- **Vorteile:** Sehr einfach, generisch (kein Einzelspiel), 1 neue
  Exclude-Gruppe.
- **Nachteile:** Datengetestet 1 echte Kollision gegen TRUE_POSITIVE:
  `Sony PlayStation 4 Slim Schwarz HDMI USB-A für PS4 Funktioniert
  einwandfrei` (Spec-Beschreibung "für PS4" bei einem echten Gerät) würde
  fälschlich blockiert.
- **Abdeckung:** 3 von 28 relevanten Fehltreffern.

### Variante B -- Gruppe-2-Gating durch Speicher-/Modellmarker (aus vorherigem Bericht, HIER VERWORFEN)

Ursprünglich vorgeschlagen: "ovp"/"bundle"/"mit spiele" nur gültig in
Kombination mit einer neuen Gruppe 3 (Speichergröße/Modellcode).

- **Verworfen**, weil es direkt der neuen Auftragsvorgabe widerspricht:
  `Nintendo Switch mit OVP → MATCH` hat KEINEN Speicher-/Modellmarker --
  Variante B würde genau diesen Pflichtfall brechen. Wird hier nur zur
  Nachvollziehbarkeit dokumentiert, nicht weiterverfolgt.

### Variante C -- kombiniert: "für Plattform" (mit Geräte-Marker-Ausnahme) + "pro controller" (Konnektor-Logik) + Kompositum-Ergänzung -- **EMPFOHLEN**

Drei additive, rein YAML-basierte Bausteine, alle bereits existierende
Matcher-Mechanismen wiederverwendend, kein neuer Code in `matcher.py`:

1. **`exclude_category`** um die "für Plattform"-Phrasen erweitern (wie
   Variante A), aber zusätzlich über **`exclude_category_unless_also_
   contains`** (bereits produktiv für "gehäuse" in dieser Datei) mit einer
   Ausnahmeliste kombiniert: die Phrase blockiert NICHT, wenn der Titel
   zusätzlich einen Geräte-Marker enthält (`\d+\s?(gb|tb)`, `slim`, `pro`,
   `hac-001`, `v1`, `v2`, `1. generation`, `2. generation`, `oled`,
   `spielkonsole`, `spielekonsole`, `heimkonsole`). Löst die einzige in
   Variante A gefundene Kollision.
2. **`exclude_category_unless_preceded_by`** (Variante-C-Konnektor-
   Mechanismus aus `controller.yaml`) für die ENGE Phrase `"pro
   controller"` (nicht bare "controller"!), Konnektoren: `inkl.`, `inkl`,
   `mit`, `+`, `und`, `sowie`.
3. **Kompositum-Ergänzung** in Gruppe 2 der beiden `Nintendo Switch
   (V1/V2/OLED)`-Regeln: `"spielkonsole"`, `"spielekonsole"`,
   `"heimkonsole"` neben `"konsole"` ergänzen (rettet 3 der 11
   Diagnose-Grenzfälle aus 2.1 zusätzlich in ein sauberes TRUE_POSITIVE,
   ohne irgendetwas auszuschließen).

- **Vorteile:** Datengetestet **0 Kollisionen** gegen alle 195
  TRUE_POSITIVE-Titel (die 3 ursprünglich gefundenen "Kollisionen" sind
  bei genauer Prüfung selbst Fehltreffer, siehe unten). Rein additiv,
  jeder Baustein bereits als Muster im Repo etabliert und verifiziert
  (retro_konsolen.yaml, controller.yaml, konsolen_bundles.yaml selbst für
  "gehäuse"). Kein neuer Matcher-Code.
- **Nachteile:** Löst NICHT das Muster "bare `[Plattform] Controller
  OVP`" ohne "Pro" und ohne "für" (z.B. `Nintendo Switch Controller OVP`,
  `Nintendo Switch 2 GameCube Controller | OVP | NEU`) -- siehe Abschnitt
  6, Zeile 9 der Pflicht-Regressionsmatrix. Löst auch NICHT bare
  Eigenname-Spieltitel ohne "für"-Konnektor (z.B. `Nintendo Switch -
  Minecraft FRA mit OVP`, `Nintendo Pokémon Purpur Nintendo Switch
  neu/sealed in OVP`) -- **beide sind bereits bekannte, in
  `konsolen_bundles.yaml` (Zeile 101-106) und `retro_konsolen.yaml`
  (Zeile 138-144) DOKUMENTIERTE, bewusst akzeptierte Restlücken** aus dem
  vorangegangenen Review, keine neue Erkenntnis.
- **Abdeckung:** 10 von 28 relevanten Fehltreffern direkt gelöst (plus 3
  zusätzliche Diagnose-Grenzfälle sauber gerettet durch die Kompositum-
  Ergänzung) = 13 von 40. Die verbleibenden 18 (bare Spieltitel/bare
  Controller ohne generisches Marker-Wort) bleiben ein akzeptierter,
  bereits dokumentierter Rest -- eine vollständige Lösung würde
  Spieltitel-Wissen (Datenbank) oder einen neuen, kontextsensitiveren
  Matcher-Mechanismus erfordern, was der Auftrag ausdrücklich ausschließt.

### Variante D -- neuer, generischer Matcher-Mechanismus (nicht empfohlen, nur zur Vollständigkeit erwähnt)

Ein "Geräte-vs-Software/Zubehör"-Klassifikator (z.B. Zählen der Wörter
zwischen Plattformbegriff und OVP, oder ein Wortarten-/Eigennamen-
Detector) könnte die verbleibenden 18 Fälle zusätzlich lösen.

- **Nicht weiterverfolgt**, weil der Auftrag ausdrücklich KEINEN neuen
  generischen Matcher-Mechanismus verlangt. Nur der Vollständigkeit
  halber als Option für eine mögliche spätere, separate Diskussion
  genannt.

---

## 6. Pflicht-Regressionsmatrix -- ECHTE Baseline zuerst verifiziert

**Wichtig, bevor die Matrix bewertet wird:** Alle 11 Zeilen wurden vor der
Bewertung gegen die reale, unveränderte `matcher.evaluate()`-Funktion
geprüft (nicht nur angenommen). Dabei zeigte sich ein **von der
OVP-Fragestellung unabhängiger, bereits heute bestehender Befund**:

> **Zeile 3 und 4 der vorgegebenen Matrix matchen HEUTE, vor jeder
> Änderung, bereits NICHT** -- `"Nintendo Switch + 2 Controller +
> Spiele"` und `"Nintendo Switch OLED + Controller + Dock + Spiele"`
> scheitern an Gruppe 2, weil dort ausschließlich die EXAKTE Phrase
> `"mit spiele"` als Zwei-Wort-Ausdruck hinterlegt ist, nicht bare
> `"spiele"`. Ein mit "+" aufgezähltes Bundle ("... + Controller + ...
> Spiele") enthält "mit spiele" nicht als zusammenhängende Phrase, daher
> bleibt Gruppe 2 komplett ohne Treffer (`hit: []`, verifiziert via
> direktem Trace). Das ist eine **Recall-Lücke** (etwas, das matchen
> sollte, aber nicht matcht) -- das genaue Gegenteil der in diesem
> Auftrag untersuchten Precision-Lücke (etwas matcht, das nicht sollte).
> Sie hat eine andere Ursache (fehlendes Positivsignal für "+"-Aufzählung
> statt zu breites Positivsignal) und wird durch **keine** der hier
> untersuchten Varianten berührt -- weder verschlimmert noch verbessert.
> Empfehlung: als eigenständigen, separaten Befund behandeln (siehe
> Abschnitt 11), nicht mit der OVP-Fragestellung vermischen.

| # | Titel | Erwartung | Heute (Baseline, verifiziert) | Mit Variante C | Begründung |
|---|---|---|---|---|---|
| 1 | `Nintendo Switch OLED 64GB OVP` | MATCH | ✅ MATCH | ✅ MATCH | kein Exclude greift, G1/G2 wie bisher erfüllt |
| 2 | `Nintendo Switch mit OVP` | MATCH | ✅ MATCH | ✅ MATCH | kein Exclude greift |
| 3 | `Nintendo Switch + 2 Controller + Spiele` | MATCH | ❌ **NO MATCH (Bug, siehe oben)** | ❌ weiterhin NO MATCH | Gruppe 2 hat 0 Treffer -- eigenständiger, hier nicht behobener Befund |
| 4 | `Nintendo Switch OLED + Controller + Dock + Spiele` | MATCH | ❌ **NO MATCH (Bug, siehe oben)** | ❌ weiterhin NO MATCH | dito |
| 5 | `Nintendo 64 + Controller + Kabel` | MATCH | ✅ MATCH | ✅ MATCH | eigene Kategorie `retro_konsolen`, von dieser Änderung nicht berührt |
| 6 | `Mario Kart für Nintendo Switch OVP` | NO MATCH | ❌ MATCH (Fehltreffer) | ✅ NO MATCH | "für Nintendo Switch" ohne Geräte-Marker -> exkludiert |
| 7 | `Minecraft für Nintendo Switch OVP` | NO MATCH | ❌ MATCH (Fehltreffer) | ✅ NO MATCH | dito |
| 8 | `Luigi's Mansion für Nintendo Switch OVP` | NO MATCH | ❌ MATCH (Fehltreffer) | ✅ NO MATCH | dito |
| 9 | `Nintendo Switch Controller OVP` | NO MATCH | ❌ MATCH (Fehltreffer) | ❌ **weiterhin MATCH** | kein "für", kein "pro" -- **bekannte, unveränderte Restlücke** |
| 10 | `GameCube Controller für Nintendo Switch OVP` | NO MATCH | ✅ NO MATCH (bereits heute korrekt) | ✅ NO MATCH | "für Nintendo Switch" ohne Geräte-Marker -> exkludiert |
| 11 | `Nintendo Switch Tasche OVP` | NO MATCH | ✅ NO MATCH (bereits heute korrekt) | ✅ NO MATCH | "tasche" bereits heute unbedingt exkludiert (unverändert) |

**Zusammenfassung:** Von den 11 Pflichtfällen sind heute (Baseline) nur
5 korrekt (1, 2, 5, 10, 11). Variante C behebt 3 weitere (6, 7, 8) --
**8 von 11 nach der Änderung korrekt**. Zeile 9 bleibt eine bekannte,
bewusst nicht geschlossene Restlücke (siehe Abschnitt 5). **Zeile 3 und 4
sind KEIN Ziel dieser Änderung** -- ihre Ursache liegt in einer
fehlenden, nicht in einer zu breiten Positiv-Bedingung, siehe Abschnitt 11.
Korrektur von Zeile 10: entgegen der ursprünglichen Annahme im Entwurf
dieses Berichts matcht dieser Titel bereits HEUTE korrekt nicht (die
existierende `"controller für"`-Exclude-Phrase greift hier bereits,
unabhängig von der neu vorgeschlagenen "für Plattform"-Regel) -- Variante
C ändert daran nichts, bestätigt aber das bereits korrekte Verhalten.

**Zusätzliche reale Beispiele aus dem Datensatz (Ergänzung zur Matrix):**

| Titel | Erwartung | Ergebnis mit Variante C |
|---|---|---|
| `NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand` | NO MATCH | ✅ NO MATCH |
| `Xbox One S 500 GB Konsole mit Controller in OVP` | MATCH | ✅ MATCH (unverändert, "konsole" bereits stark) |
| `Nintendo Switch V1 HAC-001 mit OVP + Komplett` | MATCH (Diagnose-Grenzfall, siehe 2.1) | ✅ MATCH (unverändert, Regel selbst matcht bereits korrekt) |
| `Nintendo Switch Spielkonsole mit Set - Guter Zustand` | MATCH (via Kompositum-Ergänzung neu korrekt als "konsole"-Fall erkennbar) | ✅ MATCH über neues `spielkonsole` |
| `2x Nintendo Switch 2 Pro Controller NEU OVP` | NO MATCH | ✅ NO MATCH (neu, über "pro controller"-Konnektor-Exclude) |
| `PlayStation 4 pro mit 2 Controller` | MATCH | ✅ MATCH ("pro" hier Modellname, keine "für"-Phrase, kein "pro controller"-Bigram) |

---

## 7. Erwartetes Recall-Risiko (Variante C)

- **Kein gemessenes Recall-Risiko gegen den aktuellen Datensatz:** 0
  Kollisionen unter den 195 TRUE_POSITIVE-Titeln (nach Hinzufügen der
  Geräte-Marker-Ausnahme für die "für"-Phrase). Die 3 anfänglich
  gefundenen Kandidaten waren bei genauer Prüfung selbst Fehltreffer
  (`Super Mario 3D All-Stars für Nintendo Switch...` ist ein Spiel,
  `Nacon Revolution Pro Controller 3 PS4...` ist ein Drittanbieter-
  Controller, `Nintendo Switch Pro Controller Schwarz für Nintendo Switch
  Konsole Controller` ist ein Zubehörangebot) -- die vorgeschlagene
  Änderung korrigiert diese sogar zusätzlich.
- **Theoretisches Restrisiko:** ein künftiger Scan-Treffer könnte ein
  echtes Gerät beschreiben, das SOWOHL "für [Plattform]" enthält (z.B.
  als Kompatibilitätshinweis) ALS AUCH keinen der Geräte-Marker aus der
  Ausnahmeliste nennt -- im aktuellen Datensatz kein solcher Fall
  beobachtet, aber nicht mathematisch ausgeschlossen. Empfehlung: nach
  Umsetzung mit einem frischen found.json-Export nachprüfen (identische
  Vorgehensweise wie in den vorherigen Reviews dieser Session).
  **Kein Recall-Risiko** durch das "pro controller"-Konnektor-Muster
  (0 Kollisionen im vollständigen 195-Titel-Test) oder die Kompositum-
  Ergänzung (rein additiv, kann nur zusätzliche TRUE_POSITIVE erzeugen,
  nie welche entfernen).
- **Bewusst nicht geschlossene Lücke (kein Risiko, sondern bekannte
  Grenze):** Zeile 9 der Pflichtmatrix (`Nintendo Switch Controller
  OVP`) und bare bekannte Spieltitel ohne "für" (Minecraft/Pokémon
  Purpur-Muster) bleiben unverändert wie heute -- kein neues Risiko,
  aber auch keine Verbesserung an dieser Stelle.

---

## 8. Konkrete YAML-Änderungen (Vorschlag -- NICHT umgesetzt)

**a) `exclude_category` in `konsolen_bundles.yaml` erweitern** (neue,
unbedingte Einträge, analog zu den bestehenden Phrasen-Einträgen):
```yaml
  # Vorschlag, NICHT umgesetzt: generische "Produkt für Plattform"-Phrase
  # (Spiele UND Zubehör, kein Einzelspiel-Enum) -- via
  # exclude_category_unless_also_contains gegen Geräte-Marker abgesichert,
  # siehe unten.
```

**b) NEU: `exclude_category_unless_also_contains` um "für"-Plattform-Phrasen erweitern** (bestehender Mechanismus, bereits für "gehäuse" produktiv):
```yaml
exclude_category_unless_also_contains:
  gehäuse:
    - "vergilbt"
    # ... (unveraendert)
  "für nintendo switch":
    - "gb"
    - "tb"
    - "slim"
    - "pro"
    - "hac-001"
    - "v1"
    - "v2"
    - "oled"
    - "spielkonsole"
    - "spielekonsole"
    - "heimkonsole"
  "für ps4":
    - [dieselbe Ausnahmeliste]
  "für ps5":
    - [dieselbe Ausnahmeliste]
  "für xbox":
    - [dieselbe Ausnahmeliste]
```
*(Hinweis: exakte Umsetzung der Mehrwort-Schlüssel/ggf. Anpassung der
Matcher-Semantik für Phrasen mit Leerzeichen als Key vor Implementierung
gegen `_any_conditional_exclude_presence()` verifizieren -- aktuell nur
mit Einzelwort-Keys wie "gehäuse" produktiv erprobt.)*

**c) NEU: `exclude_category_unless_preceded_by` um "pro controller" erweitern:**
```yaml
exclude_category_unless_preceded_by:
  ladekabel:
    - "inkl."
    # ... (unveraendert)
  "pro controller":
    - "inkl."
    - "inkl"
    - "mit"
    - "+"
    - "und"
    - "sowie"
```

**d) Kompositum-Ergänzung in beiden `Nintendo Switch (V1/V2/OLED)`-Regeln:**
```yaml
    require_all_of:
      - ["nintendo switch", "switch oled", "switch konsole"]
      - ["konsole", "spielkonsole", "spielekonsole", "heimkonsole", "bundle", "set", "mit spiele", "ovp", "system"]
```

---

## 9. Notwendige Regressionstests (Vorschlag -- NICHT erstellt)

Neue Testdatei `test_konsolen_bundles_plattform_referenz_fix.py`, Struktur
analog zu `test_konsolen_bundles_precision_phrases_fix.py`:

1. `test_spiel_mit_fuer_phrase_matcht_nicht()` -- alle 13 Spiele/Software-Beispiele aus 3.1 (parametrisiert)
2. `test_pro_controller_standalone_matcht_nicht()` -- alle "Pro Controller"-Fälle aus 3.1 (Nr. 16-23)
3. `test_pro_controller_im_bundle_matcht_weiterhin()` -- Gegenprobe: `"PlayStation 4 pro mit 2 Controller"`, `"Xbox One S 500 GB Konsole mit Controller in OVP"`
4. `test_spielkonsole_kompositum_matcht()` -- `"Nintendo Switch Spielkonsole mit Set - Guter Zustand"` muss neu MATCH liefern
5. `test_bare_ovp_ohne_zusatzangabe_matcht_weiterhin()` -- Pflichtfälle 1-5 aus Abschnitt 6 (MATCH)
6. `test_fuer_phrase_mit_geraetemarker_matcht_weiterhin()` -- Sicherheitsprüfung gegen die einzige gefundene Kollision: `"Sony PlayStation 4 Slim Schwarz HDMI USB-A für PS4 Funktioniert einwandfrei"` muss MATCH bleiben
7. `test_bekannte_restluecke_dokumentiert()` -- expliziter, kommentierter Test, der Zeile 9 der Pflichtmatrix (`"Nintendo Switch Controller OVP"`) als bekannten, unveränderten Ist-Zustand festhält (kein Assertion-Fail, sondern Dokumentation, analog zum bestehenden Kommentar in `retro_konsolen.yaml` Zeile 138-144)
8. Vollständiger Lauf aller 195 TRUE_POSITIVE-Titel aus `forensics_records.json` gegen `evaluate()` als Massen-Regressionsschutz (0 erwartete neue NO-MATCH-Fälle)

---

## 10. Klare Empfehlung

**Variante C** (kombiniert: "für Plattform"-Exclude mit Geräte-Marker-
Ausnahme + "pro controller"-Konnektor-Exclude + Kompositum-Ergänzung).
Begründung: einzige Variante mit **0 gemessenen Kollisionen** gegen den
vollständigen TRUE_POSITIVE-Datensatz, verwendet ausschließlich bereits
im Repository etablierte, verifizierte YAML-Mechanismen (kein neuer
Matcher-Code), hebt die Pflicht-Regressionsmatrix von 5/11 (Baseline) auf
8/11 korrekte Zeilen, und adressiert das strukturelle Muster
("Plattformbegriff ist kein Hardware-Beweis") statt einzelner Spieltitel.
Die verbleibende Lücke (Zeile 9, bare "Controller" ohne "für"/"Pro") ist
eine bereits an anderer Stelle im Code dokumentierte, bewusst akzeptierte
Grenze der Keyword-Matching-Architektur -- ihre Schließung würde laut
Auftrag ausdrücklich vermiedene neue Matcher-Fähigkeiten erfordern.

**Ausdrücklich NICHT Teil dieser Empfehlung:** Zeile 3/4 der
Pflichtmatrix (siehe Abschnitt 11) -- das ist ein anderes Problem
(fehlendes Positivsignal für "+"-Bundle-Aufzählungen) und sollte separat
untersucht werden, um die beiden Fragestellungen (zu breite Excludes vs.
zu enge Positivsignale) nicht in einer Änderung zu vermischen.

---

## 11. Separater, während der Verifikation entdeckter Befund (außerhalb des Scopes)

**"+"-Bundle-Aufzählungen werden von Gruppe 2 nicht erkannt.** Verifiziert
gegen die reale `evaluate()`-Funktion: Titel wie `"Nintendo Switch + 2
Controller + Spiele"` oder `"Nintendo Switch OLED + Controller + Dock +
Spiele"` matchen HEUTE bereits nicht, obwohl sie -- nach den vom
Auftraggeber vorgegebenen Erwartungen -- echte Konsolen-Bundles sein
sollen. Ursache: Gruppe 2 der beiden `Nintendo Switch (V1/V2/OLED)`-Regeln
enthält nur die EXAKTE Zwei-Wort-Phrase `"mit spiele"`, keine bare
Einzelwort-Alternative wie `"spiele"`. Bei einer "+"-getrennten Aufzählung
("... + Spiele") steht "mit" nicht unmittelbar vor "Spiele" -- die Phrase
"mit spiele" wird dadurch nicht gefunden, kein anderer Gruppe-2-Begriff
(`konsole`/`bundle`/`set`/`ovp`/`system`) kommt vor, Gruppe 2 bleibt ohne
Treffer, die Regel schlägt fehl.

Das ist das **Gegenteil** des in diesem Bericht untersuchten Problems:
hier fehlt ein Positivsignal (Recall-Lücke), während die OVP-Fragestellung
ein zu weit gefasstes Positivsignal betrifft (Precision-Lücke). Eine
Lösung (z.B. bare `"spiele"` als zusätzliche Gruppe-2-Alternative
zulassen) müsste eigenständig gegen den vollständigen Datensatz auf NEUE
Fehltreffer geprüft werden (bare "Spiele" könnte z.B. reine
Spielesammlungs-Angebote ohne Konsole treffen) -- exakt dieselbe
Sorgfalt, die dieser Bericht für die OVP-Fragestellung angewendet hat.
**Empfehlung:** als eigenständige Folgeanalyse behandeln, nicht in
Variante C einfließen lassen.

**Noch nicht umgesetzt** -- wartet auf Freigabe.
