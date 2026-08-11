# Active False Positive Audit

Systematischer, kategorienweiser Abgleich des produktiven Rulesets
(`app/rules/*.yaml`) gegen den echten Produktivkorpus. Kein
theoretischer Ruleset-Review — nur aktuell aktive, reale Fehltreffer.
Läuft Kategorie für Kategorie; dieser Report wird nach jeder
abgeschlossenen Kategorie um einen eigenen Abschnitt ergänzt statt
ersetzt.

## Fortschritt über alle Kategorien

| Kategorie | Status | Muster gefixt | Titel gefixt | Muster zurückgestellt | Titel zurückgestellt | kategorienbez. Testlauf |
|---|---|---:|---:|---:|---:|---|
| handhelds | ✅ abgeschlossen | 8 | 10 | 2 | 3 | `-k "handheld"`: 59/59 |
| office_pc | ✅ abgeschlossen | 2 | 27 | 1 | 7 | `-k "office_pc"`: 11/11 |
| retro_konsolen | ✅ abgeschlossen | 3 | 9 | 4 | 14 | `-k "retro_konsolen"`: 31/31 |
| **Kumulativ (handhelds + office_pc + retro_konsolen)** | | **13** | **46** | **7** | **24** | |

Die kumulative Zeile zählt die drei in diesem Durchlauf abgeschlossenen
Kategorien. Ein weiterer, bereits aus einem vorherigen Arbeitsblock
bekannter Fall in `konsolen_bundles` (1 Titel, "Display Ersatz
Konsole...") ist bewusst NICHT eingerechnet, da für diese Kategorie
kein eigener Schritt in diesem Durchlauf stattfand — siehe Tabelle
"Weiterhin offen" weiter unten.

**Begriffsdefinitionen** (gelten für den ganzen Report, nicht mehr
synonym verwendet):

- **"Muster" / "Fälle"** = distinkte Root-Causes (z.B. "Ersatzstift/
  Touchpen/Stylus" ist EIN Muster, deckt aber 3 Titel ab).
- **"Titel"** = einzelne, reale `found.json`-Anzeigen.
- **"Terme"** = einzelne neue YAML-Exclude-Einträge (ein Muster kann
  mehrere Terme benötigen, z.B. "ersatzstift" + "ersatzstifte" +
  "touchpen" + "stylus" für ein Muster).

## Scope

- **Daten:** `data/found.json`, Live-Auswertung über
  `matcher.load_rules()` + `matcher.evaluate()` gegen die produktiven
  `app/rules/*.yaml` (19 Kategorien, 355 Regeln), jeweils mit dem zum
  Zeitpunkt des jeweiligen Schritts aktuellen Korpusstand: 1736
  eindeutige Titel / 22 damals matchende handhelds-Titel (handhelds-
  Schritt), 69 damals matchende office_pc-Titel (office_pc-Schritt), 91
  damals matchende retro_konsolen-Titel (retro_konsolen-Schritt).
- **Methodik-Hinweis (wichtig):** Alle Titel wurden mit ihrem **echten**
  `found.json`-Preis ausgewertet, nicht mit `price=0.0`. Ein Test mit
  `price=0.0` verzerrt First-Match-Wins bei preisgedeckelten Regeln
  (z.B. `controller`-Regeln mit `max_price` 12–35€) systematisch
  zugunsten günstiger Kategorien. Das führte initial zu einer
  Falschmeldung (siehe Abschnitt "Routing / First-Match-Wins" unten).
- **Fokus je Schritt:** vollständiger Deep-Dive für die jeweils aktuell
  bearbeitete Kategorie (alle aktuell live matchenden Treffer einzeln
  bewertet); für die übrigen Kategorien punktuell ein Keyword-Sweep über
  Zubehör-/Ersatzteil-/Software-Signalwörter auf den aktuell matchenden
  Titeln, mit manueller Einzelprüfung jedes Treffers — daraus stammen
  die bereits bekannten, aber noch nicht bearbeiteten Funde in
  `konsolen_bundles` und `retro_konsolen`.
- Bereits gelöste Muster (siehe `docs/KONSOLEN_BUNDLES_REVIEW.md`,
  `docs/KONSOLEN_BUNDLES_OVP_ANALYSE.md`, bestehende Regressionstests)
  wurden nicht erneut als Findings gemeldet.

## Aktive echte Fehltreffer

**Gefixt in diesem Schritt (handhelds, 8 Muster / 10 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| handhelds | Displayschutz-Folie (Kompositum) | `2x 9H Gehärtetes Displayschutz für Lenovo Legion Go...` | 1 |
| handhelds | Controller-Grip-Zubehör | `Ergonomischer Performance Controller Grip...Zubehör` | 1 |
| handhelds | Ersatzstift/Touchpen/Stylus | `Ersatzstifte für die Konsolen...` + 2× `...Touchpen Stylus Ersatzstift...` | 3 |
| handhelds | Schutzhülle (Kompositum) | `Schutzhülle für Lenovo Legion Go - Neu` | 1 |
| handhelds | leere Sammler-Verpackung | `...LEERE BOX mit Inlay` | 1 |
| handhelds | "Spiele für Konsole" (Software statt Gerät) | `Spiele für NINTENDO 3DS XL Konsole - Top` | 1 |
| handhelds | abgetrennte Controller-Hälfte | `Lenovo Legion Go Controller Rechts` | 1 |
| handhelds | Flash-Karte/Spielkarte | `...Flash Karte...Spielkarte` | 1 |
| **Summe handhelds** | **8 Muster** | | **10 Titel** |

**Gefixt im office_pc-Schritt (2 Muster / 27 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| office_pc | Mainboard/Motherboard-Ersatzteil (identisches Muster wie notebook_resell.yaml) | `Lenovo ThinkPad X390 Mainboard...NM-B891` + 2 weitere | 3 |
| office_pc | "Aufrüstkit"/"Aufrüstbundle" (bare Komponenten-Bundle ohne Gehäuse) | `PC Aufrüstkit Bundle [CPU] bis [RAM] mit [Mainboard]` (21×) + `Aufrüstbundle...` (3×) | 24 |
| **Summe office_pc** | **2 Muster** | | **27 Titel** |

**Gefixt im retro_konsolen-Schritt (3 Muster / 9 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| retro_konsolen | Standalone Memory Cards ohne Geräte-Kontext | `Nintendo Gamecube Memory Card` + 5 weitere | 6 |
| retro_konsolen | "Zubehör-Set" (Bindestrich-Variante) | `N64 / Nintendo 64 Zubehör-Set Auswahl...` + 1 weiterer | 2 |
| retro_konsolen | "Ersatznetzteil" (Kompositum) | `N64 USB-C Netzteil für Nintendo 64 Ersatznetzteil` | 1 |
| **Summe retro_konsolen** | **3 Muster** | | **9 Titel** |

**Zurückgestellt, real bestätigt, aktuell noch offen (P1/P2, 7 Fälle / 24 Titel):**

| Kategorie | Priorität | Muster | Anzahl Titel | Grund für Zurückstellung |
|---|---|---|---:|---|
| handhelds | P1 | Fanxiang M.2 2230 SSD-Einbauteil für Steam Deck | 2 | enger Kandidat, eigener Review-Schritt |
| handhelds | P2 | USB-C-HDMI-Adapterkabel | 1 | Kollisionsrisiko mit echten Spec-Angaben |
| office_pc | P1/P2 | bare "bundle"/"kit" ohne "Aufrüst"-Signal (`Bundle AMD Ryzen 5 3400G...`, `MSI TOMAHAWK B450...Kit`, `Gaming Bundle: Ryzen 7 5800X...` u.a.) | 7 | kein eindeutiges Signalwort, Kollisionsrisiko mit echten Komplettsystem-Zubehör-Bundles |
| retro_konsolen | P2/NO-FIX | "Spieltitel [+ Bindestrich] + Plattform" matcht via "komplett" (z.B. `Silent Hill – PlayStation 1 – Komplett...`, `Super Mario 64 für Nintendo 64 - Komplett mit OVP...`) | 11 | identisches Muster zur bereits in konsolen_bundles als unsicher zurückgestellten "Spieltitel-vor-Plattform"-Lücke, kein kollisionsfreies Substring-Muster ohne Spieltitel-Datenbank |
| retro_konsolen | P1 | `Nintendo Netzteil für Nintendo DS USG-002...` ("[Zubehör] für [Plattform]") | 1 | identisches, bereits in konsolen_bundles gelöstes Muster, bräuchte aber den vollen Geräte-Marker-Mechanismus — eigener Arbeitsschritt |
| retro_konsolen | P2 | `Nintendo DS ... Display LCD Bildschirm oben oder unten` (Ersatzteil) | 1 | nur 1 bestätigter Fall, zu wenig Evidenz für eine verallgemeinerbare Regel |
| retro_konsolen | P2 | `Flohmarkt, Trödel Konvolut, Vtech, Konsole, Kleidung, Dvds` (generisches Konvolut, bare "konsole"/"nintendo" als Gruppe-1-Signal zu breit) | 1 | Fix würde Gruppe-1-Logik der Konvolut-Regel anfassen — eigener, strukturell größerer Arbeitsschritt |
| **Summe** | | **7 Fälle** | **24 Titel** | |

**Weiterhin offen, aus vorherigem Kontext bekannt, kein Schritt dieses
Durchlaufs (nicht in der Summe oben):**

| Kategorie | Priorität | Muster | Anzahl Titel | Status |
|---|---|---|---:|---|
| konsolen_bundles | P1 | `Display Ersatz Konsole...DISPLAY ONLY` trotz Geräte-Marker (V2/HAC-001) | 1 | eigener Arbeitsschritt, noch nicht terminiert |

**Kumulativ (handhelds + office_pc + retro_konsolen, alle drei in
diesem Durchlauf abgeschlossenen Kategorien): 10 + 27 + 9 = 46 Titel
gefixt, 3 + 7 + 14 = 24 Titel zurückgestellt.**

## Handhelds

- **22** aktuell live matchende reale Treffer vollständig einzeln geprüft.
- **8 echte False-Positive-Muster über 10 Titel** bestätigt und in diesem
  Schritt behoben.
- **2 weitere Muster über 3 Titel** real bestätigt, aber zurückgestellt
  (P1/P2, siehe Tabelle oben).
- Bereits korrekt gelöste Muster (nicht erneut gemeldet): Netzteil/
  Ladekabel/Ladegerät/Anleitung (Phase 14), Dockingstation/Mainboard/
  Motherboard/Memory Card/microSD/For-Parts/Not-Working/
  Batterieabdeckung (found.json-Audit), Hub/Skin/Faceplate/Vinyl/
  Klebefolie/Aufkleber/Ladeadapter/Reisetasche (Dashboard-Forensics),
  Gehäuse/Joystick/Thumbstick (kontextbewusst, Phase 15).
- Keine belegten Probleme bei: Steam Deck (0 aktive FPs unter den
  aktuell sichtbaren Treffern über die o.g. hinaus), PS Vita/3DS-
  Kernregeln (keine weiteren aktiven Fehltreffer).
- **1 Grenzfall ohne Fix (NO-FIX):** `Lenovo Legion Go` (bare, 15€) —
  kein Zubehör-/Ersatzteil-Signal im Titel, aus dem Titeltext allein
  nicht sicher als Fehltreffer zu identifizieren.

## Office PC

**Ausgangspunkt:** `Lenovo ThinkPad X390 Mainboard Intel Core
i5-8365U 8GB RAM NM-B891` (49€) — bereits im handhelds-Audit als
zurückgestellter P1-Kandidat notiert.

**Untersuchung des Ausgangsfalls:**

1. **Routing:** matcht `office_pc` (einzige Regel "Office-PC
   (Mindestanforderung erfüllt)").
2. **Warum greift office_pc:** die Regel prüft ausschließlich über
   `requirements:` (Detector-basiert: RAM ≥ 8GB, CPU-Tier/Generation,
   Gehäuse nicht Tiny/Mini/USFF/SFF/AiO) — kein `exclude_category`
   existierte bisher (`office_pc.yaml` bewusst "WILL komplette
   PC-Systeme"). Der Titel erfüllt RAM (8GB) und CPU (i5, 8. Generation)
   formal.
3. **Konkrete Ursache:** `matcher.py::_case_meets_requirement()`
   behandelt "kein erkennbares Gehäuse" bewusst als **erfüllt**
   (neutral) statt als Ausschlusskriterium — ein bares Mainboard-
   Ersatzteil ohne jedes Gehäuse rutscht dadurch strukturell durch.
4. **Präzedenzfall in notebook_resell.yaml:** dort ist "mainboard"/
   "motherboard" bereits als bare `exclude_category`-Begriff etabliert
   (identische Begründung: ein Mainboard-Ersatzteil trägt oft eine
   eigene RAM-Angabe, die die RAM-Anforderung unbeabsichtigt erfüllt).
5. **Übertragbarkeit geprüft, nicht blind kopiert:** `office_pc.yaml`
   nutzt eine strukturell andere Regel-Art (`requirements:` statt
   `require_all_of`/`exclude`) — verifiziert, dass `exclude_category`
   im Matcher bereits VOR der `requirements`-Prüfung ausgewertet wird
   (`matcher.py` Zeilen ~1058–1097 vs. 1099+), der Mechanismus also
   technisch korrekt greift, obwohl er in dieser Kategorie bisher nie
   verwendet wurde.
6. **Weitere reale Titel mit demselben/verwandtem Muster:** vollständiger
   Sweep über die 69 damals matchenden office_pc-Titel ergab zusätzlich
   einen deutlich größeren, bisher unbekannten Cluster: 21 Titel nach
   dem Muster `PC Aufrüstkit Bundle [CPU] bis [RAM] mit [Mainboard]`
   sowie 3 weitere `Aufrüstbundle`-Titel — alles bare Komponenten-Kits
   (Mainboard+CPU+RAM) ohne jedes Gehäuse, semantisch eindeutig
   ("Aufrüstkit" = Nachrüstteile für ein bereits vorhandenes System,
   nie ein Komplettsystem).
7. **TRUE_POSITIVE-Kollisionen:** 0 — gegen alle 69 damals matchenden
   Titel geprüft, zusätzlich explizit gegen Gehäuse-/Tower-Nennungen in
   den 27 geflaggten Titeln (keine gefunden). 42 verbleibende
   TRUE_POSITIVE-Titel (Notebooks, Business-Desktops mit Marke/Modell)
   bleiben unverändert erhalten.

**Vollständiger Active-FP-Audit (über den Ausgangsfall hinaus):**
alle 69 damals live matchenden office_pc-Titel einzeln geprüft (Mainboards,
Ersatzteile, Barebones, Gehäuse, Netzteile, CPU/RAM/SSD/GPU-Einzelteile,
Kühlung, Dockingstations, Monitore, Zubehör, Reparaturteile,
Einzelkomponenten als Suchraster). Ergebnis: **2 reale FP-Muster über 27
Titel** (siehe Tabelle oben), plus **1 weiteres, real bestätigtes aber
zurückgestelltes Muster über 7 Titel** (bare "bundle"/"kit" ohne
"Aufrüst"-Signal — dieselbe Root-Cause, aber kein eindeutiges,
kollisionsfreies Signalwort identifizierbar; z.B. `Gigabyte H410M H
V3...PC Bundle` könnte theoretisch auch ein komplettes System mit
zusätzlichem Zubehör-Bundle sein, nicht abschließend aus dem Titel
allein entscheidbar). Keine weiteren aktiven FPs bei Monitoren, Netzteilen,
Kühlung, Dockingstations oder Zubehör gefunden — diese Suchraster-Punkte
ergaben keine Treffer im aktuellen Korpus.

**Routing-Analyse (First-Match-Wins):** kein First-Match-Wins-Problem
festgestellt — `office_pc` ist die einzige Kategorie mit
`requirements`-basiertem Matching für diese Titelmuster, keine andere
Kategorie hätte diese Titel vorher abfangen können oder sollen.
Root-Cause-Klasse **A** (eigene Regel zu breit, konkret: fehlendes
Gehäuse-Erfordernis) + **C** (fehlendes Exclude).

## Retro-Konsolen

**Vollständiger Active-FP-Audit:** alle 91 damals live matchenden
retro_konsolen-Titel einzeln geprüft.

**Kernfund:** `"memory card"` ist in allen drei Regel-Blöcken (Nintendo,
Sony, Konvolut) als Gruppe-2-Geräte-Signal akzeptiert — ursprünglich
ergänzt, um echte Bundles ohne anderes Signalwort zu retten (bestätigt:
2 reale TRUE_POSITIVE-Titel hängen ausschließlich davon ab, z.B.
`Playstation 1 original mit Controller, Spielen und Memory Card`).
Dasselbe Signal lässt aber auch 6 reale Standalone-Speicherkarten-
Angebote ohne jedes Gerät durch. **Weder Entfernen noch ein unbedingter
Exclude war sicher möglich** (beides hätte die 2 echten Bundles
zerstört) — gelöst über den bereits in dieser Datei für "gehäuse"
etablierten kontextbewussten Mechanismus
(`exclude_category_unless_also_contains`): blockiert nur, wenn im
gesamten Titel kein Geräte-Kontextbegriff (`controller`/`konsole`/
`ersatzkonsole`) vorkommt.

Zusätzlich 2 klar abgrenzbare Standalone-Zubehör-Muster (`Zubehör-Set`,
`Ersatznetzteil`) über bare `exclude_category`-Ergänzungen behoben,
analog zum bereits vorhandenen `zubehörpaket`/`zubehör paket`.

**Größter zurückgestellter Fund:** 11 Einzelspiel-Titel matchen über
`"komplett"` (z.B. `Silent Hill – PlayStation 1 – Komplett & in
hervorragendem Zustand`, `Super Mario 64 für Nintendo 64 - Komplett mit
OVP und Anleitung`). Root Cause: das Muster "Spieltitel [+ Bindestrich]
+ Plattformname" — **identisch** zur bereits in einem vorherigen
Arbeitsblock (konsolen_bundles) explizit untersuchten und als unsicher
zurückgestellten "Spieltitel-vor-Plattform"-Lücke (siehe STATUS.md:
"kein Substring-Muster ohne Kollisionsrisiko identifiziert"). Konkret
geprüft: ein Exclude auf `"- playstation"`/`"– nintendo 64"` u.ä. würde
den realen TRUE_POSITIVE-Titel `N64 - Nintendo 64 Konsole Einzeln -
NUS-001 (EUR)` treffen (Bindestrich zwischen Markenkürzel und
Vollname, kein Spieltitel-Muster) — ohne einen vollständigen
Geräte-Marker-Mechanismus (wie in konsolen_bundles) nicht sicher lösbar.
Bewusst NICHT gefixt, dokumentiert als P2/NO-FIX.

**Weiterer struktureller Befund (nicht gefixt):** die Konvolut-Regel
akzeptiert in Gruppe 1 bare `"nintendo"`/`"konsole"` als ausreichendes
Markensignal — ein generischer Flohmarkt-Sammelposten
(`Flohmarkt, Trödel Konvolut, Vtech, Konsole, Kleidung, Dvds`, Vtech =
Kinderspielzeug-Marke, kein Gaming-Bezug) matcht dadurch fälschlich.
Nur 1 bestätigter Fall — ein Fix würde die Gruppe-1-Logik der
Konvolut-Regel anfassen (Kategorie A: Regel-Gruppe selbst zu breit),
das ist ein strukturell größerer, eigener Schritt und wurde bewusst
nicht im Rahmen dieses additiven Excludes mitgelöst.

## Routing / First-Match-Wins

**Untersuchter Fall:** `Microsoft Xbox One X 1TB Schwarz Inkl OVP Ohne
Controller`.

Bei Prüfung mit `price=0.0` matchte dieser Titel fälschlich `controller`
(Regel "Xbox Wireless Controller ★ Top-Deal", `max_price` 20€ — bei
Preis 0 innerhalb des Caps, First-Match-Wins vor `konsolen_bundles`
wegen niedrigerer `scan_priority`, 6 vs. 8). Bei Prüfung mit dem
**echten** `found.json`-Preis (75€) matcht der Titel jedoch korrekt
`konsolen_bundles` (Regel "Xbox One S / One X 👍 Guter Preis",
`max_price` 90€) — die `controller`-Regeln (`max_price` 20/30€) greifen
bei 75€ gar nicht erst.

**Klarstellung:** Dies ist **kein realer aktiver Fehltreffer**, sondern
ein **Testartefakt** der ursprünglichen Prüfmethodik (`price=0.0` statt
echtem Preis). Der Fall ist in **keiner** der obigen Zählungen (weder
"gefixt" noch "zurückgestellt", in keiner Kategorie) enthalten und
wurde in keinem der drei Audit-Schritte als Finding mitgezählt. Der in
`controller.yaml` bereits vorhandene Kommentar zu
diesem genauen Kollisionsrisiko (Zeilen 50–54) bleibt als dokumentiertes
Restrisiko gültig, ist aber aktuell durch keinen realen Treffer belegt.

## Ausgeschlossene hypothetische Fälle

Diese Fälle sind **keine real bestätigten Fehltreffer** (anders als die
"zurückgestellten P1/P2-Fälle" oben, die real belegt, aber noch nicht
gefixt sind) — sie wurden geprüft und mangels Datenbasis oder wegen
Kollisionsrisiko bewusst NICHT umgesetzt:

**In diesem Audit neu geprüft und verworfen (4):**

1. `ersatzknopf`/`ersatzknöpfe`/`flashkarte`/`leerkarton` (handhelds) —
   0 Treffer im vollständigen Korpus, keine Datenbasis (Phase 6).
2. `ssd` als bare Exclude (handhelds) — aktuell 0 Kollisionen, aber
   bewusst NICHT verwendet: zu breit, ein reales Steam-Deck-Angebot
   könnte künftig legitim "SSD" im Titel nennen. Die engere Phrase
   `"m.2 2230"` (siehe P1-Tabelle oben) ist der sicherere Kandidat für
   einen künftigen Schritt.
3. `"Controller Links"`/`"Rechter Controller"`/`"Linker Controller"`
   (handhelds) — 0 Treffer im Korpus, nicht ergänzt.
4. genereller `"für [Plattform]"`-Exclude für handhelds — ein
   bestätigter TRUE_POSITIVE-Kollisionsfall (`Nintendo 2DS
   Handheld-System Konsole für Nintendo 3DS Plattform Weiß/Rot`) zeigt,
   dass ein naiver Exclude ohne den vollen Geräte-Marker-Mechanismus aus
   `konsolen_bundles.yaml` echte Geräte blockieren würde.

**Referenz aus vorherigem Arbeitsblock (nicht Teil dieses Audits, nur
zur Einordnung genannt):**

- "+"-Bundle-Recall-Lücke (`Nintendo Switch + 2 Controller + Spiele`) —
  weiterhin 0 reale Verlustfälle im Korpus, unverändert NO-FIX aus dem
  vorherigen Arbeitsblock. Kein neuer Befund dieses Audits.

## Implementierter Fix

**handhelds:** `app/rules/handhelds.yaml`, `exclude_category`: **12
neue** bare-word/phrase Excludes für die **8 gefixten Muster**
(`displayschutz`, `ersatzstift`, `ersatzstifte`, `touchpen`, `stylus`,
`schutzhülle`, `grip`, `leere box`, `spielkarte`, `flash karte`,
`spiele für`, `controller rechts`). Alle 0 Kollisionen gegen den
vollständigen 1736-Titel-Korpus (jeder Begriff kommt in Kombination mit
einem Handheld-Markennamen ausschließlich im jeweils identifizierten
Fehltreffer-Titel vor). Reine additive `exclude_category`-Ergänzung,
kein neuer Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_handhelds_active_fp_audit_fix.py`
(12 Tests: 9 FP-Regressions-Testfunktionen, die zusammen alle 10 real
bestätigten Fehltreffer-Titel abdecken, 1 Sammel-TP-Sicherheitstest für
6 reale TRUE_POSITIVES, 1 Grenzfalltest gegen die "für Plattform"-
TRUE_POSITIVE-Kollision, 1 bestehende Pokémon-Bundle-Sicherheitsprüfung).

**office_pc:** `app/rules/office_pc.yaml`, neu eingeführtes
`exclude_category` (Kategorie hatte bisher bewusst keins): **4 neue**
bare-word Excludes für die **2 gefixten Muster** (`mainboard`,
`motherboard`, `aufrüstkit`, `aufrüstbundle`). Alle 0 Kollisionen gegen
die 69 damals matchenden office_pc-Titel, zusätzlich explizit gegen
Gehäuse-/Tower-Nennungen in den 27 geflaggten Titeln geprüft. Der
Mechanismus ist technisch identisch zu den anderen Kategorien und wird
bereits vor der `requirements`-Detector-Prüfung ausgewertet (siehe
Abschnitt "Office PC" oben) — reine additive Ergänzung, kein neuer
Matcher-Mechanismus, kein Eingriff in `_case_meets_requirement()`
selbst.

Neue Regressionstestdatei: `app/tests/test_office_pc_active_fp_audit_fix.py`
(6 Tests: 4 FP-Regressions-Testfunktionen für alle 27 real bestätigten
Fehltreffer-Titel, 1 Sammel-TP-Sicherheitstest für 7 reale
TRUE_POSITIVES, 1 Grenzfalltest, der explizit bestätigt, dass die
bewusst NICHT gefixten bare-"bundle"/"kit"-Titel weiterhin matchen).

**retro_konsolen:** `app/rules/retro_konsolen.yaml` — 1 neuer
`exclude_category_unless_also_contains`-Eintrag (`"memory card"` mit
Kontextliste `controller`/`konsole`/`ersatzkonsole`, reine Erweiterung
des bereits für `"gehäuse"` etablierten Mechanismus) + 2 neue bare
`exclude_category`-Terme (`zubehör-set`, `ersatznetzteil`). Alle 0
Kollisionen gegen die 91 damals matchenden retro_konsolen-Titel; die 2
bekannten TRUE_POSITIVE-Titel, die ausschließlich über `"memory card"`
matchen, bleiben explizit erhalten. Kein neuer Matcher-Mechanismus —
reine Wiederverwendung/Erweiterung bestehender YAML-Primitiven.

Neue Regressionstestdatei: `app/tests/test_retro_konsolen_active_fp_audit_fix.py`
(6 Tests: 3 FP-Regressions-Testfunktionen für alle 9 real bestätigten
Fehltreffer-Titel, 2 Sammel-TP-Sicherheitstests — davon einer gezielt
für die 5 memory-card-Bundles inkl. der 2 ausschließlich davon
abhängigen TRUE_POSITIVES —, 1 Grenzfalltest gegen eine
Bindestrich-Kollision).

## Testergebnis

**handhelds:**
- `pytest app/tests/test_handhelds_active_fp_audit_fix.py -v`: **12/12 passed**
- `pytest app/tests/ -k "handheld" -v`: **59/59 passed**

**office_pc:**
- `pytest app/tests/ -k "office_pc" -v`: **11/11 passed** (6 neue Tests
  + 5 bereits bestehende office_pc-relevante Tests aus
  `test_detector_cpu.py`, `test_detector_gpu.py`,
  `test_matcher_hardware_requirements.py`, `test_matcher_part_out.py`,
  `test_matcher_price_history_model.py`)

**retro_konsolen:**
- `pytest app/tests/ -k "retro_konsolen" -v`: **31/31 passed** (6 neue
  Tests + 25 bereits bestehende retro_konsolen-relevante Tests aus
  `test_matcher_gehaeuse_shell_fix.py`, `test_matcher_resale_price_groups.py`,
  `test_retro_konsolen_controller_signal_fix.py`,
  `test_rule_service_modding_fix.py` — inkl. des bereits bestehenden
  `test_signal_memory_card_positiv`, unverändert grün)

**Rule Analyzer (nach allen drei Schritten):** `0 Findings, 355 Regeln,
19 Kategorien` (unverändert).

**Volle Suite:** noch nicht erneut ausgeführt seit dem handhelds-Fix —
läuft laut Teststrategie dieses Durchlaufs erst am Ende dieses
Optimierungsdurchlaufs, auf explizite Freigabe. Letzter dokumentierter
vollständiger Lauf (vor office_pc/retro_konsolen): **1197/1197 passed,
0 failed** (604s).
