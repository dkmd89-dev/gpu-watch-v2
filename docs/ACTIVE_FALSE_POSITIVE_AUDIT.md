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
| gpu | ✅ abgeschlossen (0 Findings) | 0 | 0 | 0 | 0 | — (kein Fix nötig) |
| lego_minifiguren | ✅ abgeschlossen | 1 | 1 | 0 | 0 | `-k "lego"`: 25/25 |
| iphone | ✅ abgeschlossen | 1 | 1 | 1 | 2 | `-k "iphone"`: 15/15 |
| monitor_curved | ✅ abgeschlossen | 2 | 2 | 0 | 0 | `-k "monitor_curved"`: 4/4 |
| vintage_elektronik | ✅ abgeschlossen | 11 | 40 | 1 | 1 | `-k "vintage_elektronik"`: 5/5 |
| netzteil | ✅ abgeschlossen | 1 | 2 | 0 | 0 | `-k "netzteil"`: 20/20 |
| notebook_resell | ✅ abgeschlossen | 1 | 2 | 0 | 0 | `-k "notebook_resell"`: 21/21 |
| ram | ✅ abgeschlossen | 2 | 2 | 0 | 0 | `-k "ram"`: 42/42 |
| sata_ssd | ✅ abgeschlossen | 1 | 3 | 0 | 0 | `-k "sata_ssd"`: 20/20 |
| controller | ✅ abgeschlossen | 5 | 6 | 0 | 0 | `-k "controller"`: 69/69 |
| **Kumulativ (handhelds + office_pc + retro_konsolen + lego_minifiguren + iphone + monitor_curved + vintage_elektronik + netzteil + notebook_resell + ram + sata_ssd + controller)** | | **38** | **105** | **9** | **27** | |

Die kumulative Zeile zählt die zwölf in diesem Durchlauf gefixten
Kategorien (gpu ohne Fix, da 0 Findings — zählt daher nicht mit,
Zeile bleibt zur Nachvollziehbarkeit trotzdem stehen). Ein weiterer,
bereits aus einem vorherigen Arbeitsblock bekannter Fall in
`konsolen_bundles` (1 Titel, "Display Ersatz Konsole...") ist bewusst
NICHT eingerechnet, da für diese Kategorie kein eigener Schritt in
diesem Durchlauf stattfand — siehe Tabelle "Weiterhin offen" weiter
unten.

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
  damals matchende retro_konsolen-Titel (retro_konsolen-Schritt), 1750
  eindeutige Titel / 46 damals matchende gpu-Titel (gpu-Schritt), 455
  damals matchende lego_minifiguren-Titel (lego_minifiguren-Schritt), 210
  damals matchende iphone-Titel (iphone-Schritt), 133 damals matchende
  monitor_curved-Titel (monitor_curved-Schritt), 108 damals matchende
  vintage_elektronik-Titel (vintage_elektronik-Schritt), 94 damals
  matchende netzteil-Titel (netzteil-Schritt), 84 damals matchende
  notebook_resell-Titel (notebook_resell-Schritt), 81 damals matchende
  ram-Titel (ram-Schritt), 75 damals matchende sata_ssd-Titel
  (sata_ssd-Schritt), 56 damals matchende controller-Titel
  (controller-Schritt).
- **Methodik-Hinweis, neu entdeckt im iphone-Schritt (wichtig):**
  `data/found.json` wird von einem laufenden Produktiv-Scanner (Docker
  Compose) live verändert — zwei Live-Auswertungen im Abstand weniger
  Minuten lieferten unterschiedliche eindeutige Titelzahlen (1750 vs.
  1754) und unterschiedliche iphone-Trefferzahlen. Jeder Audit-Schritt
  ist daher eine **Momentaufnahme** zum jeweiligen Ausführungszeitpunkt,
  nicht ein stabiler, wiederholbar identischer Korpus — Titelzahlen aus
  früheren Schritten dieses Reports können bei einer erneuten Live-
  Auswertung geringfügig abweichen. Kein Einfluss auf die Korrektheit
  der einzelnen Fixes (jeder Fund wurde zum jeweiligen Auswertungs-
  zeitpunkt einzeln real verifiziert), nur auf die exakte
  Reproduzierbarkeit der genannten Gesamtzahlen.
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
- **Auswahl der Kategorie nach gpu:** evidenzbasiert statt nach Gefühl —
  Anzahl aktuell matchender Titel je noch nicht auditierter Kategorie
  ermittelt (Live-Auswertung über den vollständigen `found.json`-
  Korpus), `lego_minifiguren` fiel mit **455** Treffern deutlich aus dem
  Rahmen der übrigen unauditierten Kategorien (typischerweise 40–210)
  und wurde deshalb als nächster Deep-Dive gewählt.

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

**Gefixt im gpu-Schritt (0 Muster / 0 Titel):**

Vollständiger Deep-Dive über alle 46 damals live matchenden gpu-Titel
(echte Preise) plus gezielte Suche nach Zubehör-/Bundle-/Ersatzteil-/
Tausch-Signalwörtern ("wasserblock", "riser", "netzteil", "kabel",
"adapter", "mainboard", "bundle", "defekt" u.a.) — **0 reale aktive
Fehltreffer** gefunden. Kein Fix in dieser Kategorie nötig; siehe
Abschnitt "GPU" unten für Details.

**Gefixt im lego_minifiguren-Schritt (1 Muster / 1 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| lego_minifiguren | Negation vor "Figur(en)" ("Ohne Figuren") | `Lego Star Wars Sammlung, 75082,7959,9488, Komplett Ohne Figuren` | 1 |
| **Summe lego_minifiguren** | **1 Muster** | | **1 Titel** |

**Gefixt im iphone-Schritt (1 Muster / 1 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| iphone | leere Sammler-Originalverpackung ohne Gerät | `Titel: Leere Originalverpackung Apple iPhone 11 - 128GB - Schwarz (Black)` (5€) | 1 |
| **Summe iphone** | **1 Muster** | | **1 Titel** |

**Gefixt im monitor_curved-Schritt (2 Muster / 2 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| monitor_curved | Konsolen-Bundle über PS-Kurzform ("ps4slim" statt "playstation") | `Ps4slim + curved Samsung Monitor+controller+Wandhalterung` | 1 |
| monitor_curved | Fitnessgerät mit eigenem curved-Display | `Klappbarer Heimtrainer F‑Bike CURVED LCD-Display Fahrrad Top` | 1 |
| **Summe monitor_curved** | **2 Muster** | | **2 Titel** |

**Gefixt im vintage_elektronik-Schritt (11 Muster / 40 Titel) — größter
Einzelfund dieses gesamten Durchlaufs:**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| vintage_elektronik | Sony PVM/BVM-Ersatzteile (Platine/Transformator/Chip/Widerstand) | `SONY PVM-14M4U CRT Monitor Transformer Assy Flyback...` u.a. | 13 |
| vintage_elektronik | Sony PVM/BVM-Akkus/Ladegeräte | `2x Li-Ion Akku 95Wh...für Sony PVM-9040ME...`, `Charger für SONY BVM-D9...` | 5 |
| vintage_elektronik | Sony PVM/BVM-Kabel/Adapter/Schutzblende/Einbauset | `Netzkabel für Sony BVM F250...`, `SCART zu BNC Breakout Adapter...`, `SONY BKM-23M Protection Panel...`, `Sony BVM PVM Monitor Einbauset...` | 4 |
| vintage_elektronik | Fernbedienungen für Profi-CRT-Monitor (fehlender Exclude ggü. Röhrenfernseher-Regel) | `Sony Trinitron RM 694 Fernbedienung` u.a. | 4 |
| vintage_elektronik | Sammlerfotos/Postkarten ("- Altes Foto"/"- Foto") | `Giraffe auf Röhrenfernseher 1954 - Altes Foto 1950er` u.a. | 6 |
| vintage_elektronik | Subwoofer-Zubehör für ein Gerät | `Subwoofer von/für SONY Trinitron KV-E2911A Fernseher` | 1 |
| vintage_elektronik | T-Shirt/Merchandise | `Testbild T-Shirt Fernseher Shirt Retro Fun...` | 1 |
| vintage_elektronik | Wandhalterung (Montage-Zubehör) | `17"- 21" meliconi...Wandhalterung silber A21` | 1 |
| vintage_elektronik | Kippsicherung (Sicherheits-Zubehör) | `TV Kippsicherung zum Verschrauben...Kippschutz` | 1 |
| vintage_elektronik | Schulkarte/Rollkarte (Lehrmaterial) | `Rollkarte Schulkarte Fernsehbildröhre...` | 1 |
| vintage_elektronik | Dokumentation/Vertreterkoffer/Adapter-Konvolut (Funktionsbeschreibung, Werbekoffer, SCART-Cinch-Konvolut) | `Philips Service Fernsehgeräte Funktionsbeschreibung 1964/65...`, `KENWOOD HiFi Vintage Werbekoffer...`, `37x SCART Cinch Adapter Konvolut...` | 3 |
| **Summe vintage_elektronik** | **11 Muster** | | **40 Titel** |

**Gefixt im netzteil-Schritt (1 Muster / 2 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| netzteil | HiFi-Verstärker mit Watt-Angabe (psu.py-Detector interpretiert Verstärker-Ausgangs-Watt als PSU-Watt) | `1000W Verstärker Stereo Amplifier HIFI...`, `600W Bluetooth Mini Verstärker HiFi...` | 2 |
| **Summe netzteil** | **1 Muster** | | **2 Titel** |

**Gefixt im notebook_resell-Schritt (1 Muster / 2 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| notebook_resell | "Ohne SSD/RAM" — Negation vor bare "ssd" nicht erkannt (Gruppe-3-Alternative) | `Lenovo ThinkPad L14 Gen 3...BIOS OK \| Ohne SSD/RAM` (2×) | 2 |
| **Summe notebook_resell** | **1 Muster** | | **2 Titel** |

**Gefixt im ram-Schritt (2 Muster / 2 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| ram | Pluralform "Laptops" (Wortgrenzen-Lücke ggü. bare "laptop") | `Samsung 8GB DDR4 RAM Riegel für Laptops` | 1 |
| ram | "SO- DIMM" (Bindestrich+Leerzeichen-Variante) | `SK hynix16GB(2x8GB) DDR4 SO- DIMM 1Rx8...` | 1 |
| **Summe ram** | **2 Muster** | | **2 Titel** |

**Gefixt im sata_ssd-Schritt (1 Muster / 3 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| sata_ssd | Externe USB-SSDs ("Portable"/"Externer Speicher", kein SATA-Interface) | `SanDisk Portable SSD 1 TB Speicher`, `SSK Pro 1TB SSD Externer Speicher USB-Stick` u.a. | 3 |
| **Summe sata_ssd** | **1 Muster** | | **3 Titel** |

**Gefixt im controller-Schritt (5 Muster / 6 Titel):**

| Kategorie | Muster | Betroffene Titel (Beispiel) | Anzahl Titel |
|---|---|---|---:|
| controller | Controller-Halter/-Ständer + Wandhalterung (Kompositum) | `Controller Halter "Fight" Faust Design`, `PS5 Wandhalterung für PS5 Controller...` | 2 |
| controller | Ersatz-Akku für Controller | `Controller Akku für Xbox One/Xbox Series X&S...` | 1 |
| controller | Wireless-Empfänger/-Dongle für PC | `...Controller Adapter Empfänger Stick Windows 10 11 PC USB DE` | 1 |
| controller | Ersatzteil (Analog-Sticks) | `2x Ersatz Analog Sticks für PS5 Controller DualSense...` | 1 |
| controller | Konsolen-Bundle über Speicherkapazität (bereits im Regel-Kommentar dokumentiertes Restrisiko, jetzt real bestätigt) | `XBOX Series S 1TB + 2 Controller[...]` | 1 |
| **Summe controller** | **5 Muster** | | **6 Titel** |

**Zurückgestellt, real bestätigt, aktuell noch offen (P1/P2, 9 Fälle / 27 Titel):**

| Kategorie | Priorität | Muster | Anzahl Titel | Grund für Zurückstellung |
|---|---|---|---:|---|
| handhelds | P1 | Fanxiang M.2 2230 SSD-Einbauteil für Steam Deck | 2 | enger Kandidat, eigener Review-Schritt |
| handhelds | P2 | USB-C-HDMI-Adapterkabel | 1 | Kollisionsrisiko mit echten Spec-Angaben |
| office_pc | P1/P2 | bare "bundle"/"kit" ohne "Aufrüst"-Signal (`Bundle AMD Ryzen 5 3400G...`, `MSI TOMAHAWK B450...Kit`, `Gaming Bundle: Ryzen 7 5800X...` u.a.) | 7 | kein eindeutiges Signalwort, Kollisionsrisiko mit echten Komplettsystem-Zubehör-Bundles |
| retro_konsolen | P2/NO-FIX | "Spieltitel [+ Bindestrich] + Plattform" matcht via "komplett" (z.B. `Silent Hill – PlayStation 1 – Komplett...`, `Super Mario 64 für Nintendo 64 - Komplett mit OVP...`) | 11 | identisches Muster zur bereits in konsolen_bundles als unsicher zurückgestellten "Spieltitel-vor-Plattform"-Lücke, kein kollisionsfreies Substring-Muster ohne Spieltitel-Datenbank |
| retro_konsolen | P1 | `Nintendo Netzteil für Nintendo DS USG-002...` ("[Zubehör] für [Plattform]") | 1 | identisches, bereits in konsolen_bundles gelöstes Muster, bräuchte aber den vollen Geräte-Marker-Mechanismus — eigener Arbeitsschritt |
| retro_konsolen | P2 | `Nintendo DS ... Display LCD Bildschirm oben oder unten` (Ersatzteil) | 1 | nur 1 bestätigter Fall, zu wenig Evidenz für eine verallgemeinerbare Regel |
| retro_konsolen | P2 | `Flohmarkt, Trödel Konvolut, Vtech, Konsole, Kleidung, Dvds` (generisches Konvolut, bare "konsole"/"nintendo" als Gruppe-1-Signal zu breit) | 1 | Fix würde Gruppe-1-Logik der Konvolut-Regel anfassen — eigener, strukturell größerer Arbeitsschritt |
| iphone | P2/NO-FIX | bare "Zubehörpaket" — 2 gegensätzliche Titel im Korpus (`iPhone 15 Pro...91% Akku...*Zubehörpaket*` = echtes Gerät + Bonus-Zubehör, vs. `iPhone 11 128GB Weiß - Zubehörpaket` = evtl. reines Zubehör ohne Gerät) | 2 | kein sicheres Unterscheidungsmerkmal ohne Beschreibungstext, n=1 je Fall — zu wenig Evidenz für eine verallgemeinerbare Regel |
| vintage_elektronik | P2/NO-FIX | `SONY IC VG-469 LXP-P75ST for Sony BVM-20F1 Monitor BVM RGB Broadcast PVM` (Ersatzteil-IC) | 1 | bare "ic" als 2-Zeichen-Begriff zu generisch/riskant für einen einzelnen Beleg |
| **Summe** | | **9 Fälle** | **27 Titel** | |

**Weiterhin offen, aus vorherigem Kontext bekannt, kein Schritt dieses
Durchlaufs (nicht in der Summe oben):**

| Kategorie | Priorität | Muster | Anzahl Titel | Status |
|---|---|---|---:|---|
| konsolen_bundles | P1 | `Display Ersatz Konsole...DISPLAY ONLY` trotz Geräte-Marker (V2/HAC-001) | 1 | eigener Arbeitsschritt, noch nicht terminiert |

**Kumulativ (handhelds + office_pc + retro_konsolen + gpu +
lego_minifiguren + iphone + monitor_curved + vintage_elektronik +
netzteil + notebook_resell + ram + sata_ssd + controller, alle
dreizehn in diesem Gesamtprojekt abgeschlossenen Kategorien): 10 + 27 +
9 + 0 + 1 + 1 + 2 + 40 + 2 + 2 + 2 + 3 + 6 = 105 Titel gefixt, 3 + 7 +
14 + 0 + 0 + 2 + 0 + 1 + 0 + 0 + 0 + 0 + 0 = 27 Titel zurückgestellt.**

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

## GPU

**Vollständiger Active-FP-Audit:** alle 46 damals live matchenden
gpu-Titel einzeln geprüft (echte Preise). Alle 46 Titel sind eindeutig
reale Einzelkarten-Angebote (Marke + Modell + VRAM-Angabe), keine
PC-Systeme, Laptops, Konsolen oder Zubehörteile darunter — die
bestehenden `exclude_category`-Blöcke (PCs, Laptops, Konsolen,
Monitore/Peripherie, Kühl-Zubehör, defekte Ware) greifen sichtbar
korrekt.

**Ergänzende gezielte Suche** über den gesamten 1750-Titel-Korpus nach
GPU-Keyword-Titeln (`rtx`/`geforce`/`radeon`/`grafikkarte`/`rx`/`gpu`)
kombiniert mit Zubehör-/Bundle-/Ersatzteil-/Tausch-Signalwörtern
(`wasserblock`, `riser`, `netzteil`, `kabel`, `adapter`, `halterung`,
`slotblende`, `bios`, `mining`, `ersatzteil`, `defekt`, `tausch`,
`mainboard`, `bundle`, `kit` u.a.): 3 rohe Treffer, alle bei genauerer
Prüfung keine echten Fehltreffer (2× reine Teilstring-Kollision der
eigenen Suchheuristik mit "VRAM", 1× ein legitimes Tauschangebot für
eine echte Einzelkarte, kein Bundle).

**Ergebnis: 0 reale aktive Fehltreffer.** Kein Fix in dieser Kategorie
nötig — ein valides, dokumentiertes Ergebnis eines systematischen
Audits, keine Lücke in der Prüfung.

## LEGO Minifiguren

**Auswahlgrund:** kein vorab bekannter Kandidat wie bei office_pc —
evidenzbasiert über einen Matchvolumen-Vergleich aller noch nicht
auditierten Kategorien ermittelt (455 aktuell matchende Titel, deutlich
über dem Durchschnitt der übrigen Kategorien).

**Vollständiger Active-FP-Audit:** alle 455 damals live matchenden
Titel einzeln durchgesehen. Die deutliche Mehrheit sind eindeutig echte
LEGO-Minifiguren-/Konvolut-Angebote (Star-Wars-Clone-Trooper-Einzelfiguren,
Ninjago-/CMF-/Promo-Figuren, Sammlungs-/Konvolut-Angebote mit Marken- und
Themenbezug) — die hohe Absolutzahl ist strukturell erklärbar (LEGO-
Minifiguren sind ein sehr häufiger Kleinanzeigen-Angebotstyp), kein
Hinweis auf systematische Fehlklassifikation.

**Kernfund:** 1 Titel — `Lego Star Wars Sammlung, 75082,7959,9488,
Komplett Ohne Figuren` (34,99€) — matcht als "LEGO Minifiguren-Sammlung",
obwohl der Titel explizit **"Ohne Figuren"** aussagt (reines Set-/
Fahrzeug-Konvolut ohne Minifiguren). Root Cause: die
`require_all_of`-Gruppen prüfen nur, ob das Wort "figur"/"figuren" im
Titel vorkommt — eine vorangestellte Negation wird nicht erkannt, da
"figuren" als Teilstring von "Ohne Figuren" identisch matcht wie in
einem echten Figuren-Angebot.

**Evidenzstärke bewusst benannt:** mit n=1 im vollständigen
1750-Titel-Korpus deutlich dünner belegt als alle bisher in diesem
Durchlauf gefixten Muster (office_pc: 27, retro_konsolen: 9,
handhelds: 3–10 je Muster) und schwächer als einzelne bereits
zurückgestellte P1/P2-Fälle anderer Kategorien. Auf explizite Anfrage
trotzdem umgesetzt, da das Muster strukturell eindeutig und praktisch
kollisionsfrei ist (eine Negationsphrase wie "ohne Figuren" kommt in
keinem denkbaren echten Figuren-Verkaufsangebot vor) — anders als z.B.
die zurückgestellten retro_konsolen-Einzelfälle, bei denen die
Verallgemeinerbarkeit selbst unsicher war, nicht nur die Fallzahl.

**TRUE_POSITIVE-Kollisionen:** 0 — gegen den vollständigen
455-Titel-Match-Korpus geprüft; keine anderen Titel enthalten
"ohne"/"keine"/"kein" unmittelbar vor "figur"/"figuren"/"minifigur"/
"minifiguren".

## iPhone

**Auswahlgrund:** evidenzbasiert — nach gpu (0 Findings) und
lego_minifiguren wurde erneut das Matchvolumen aller noch nicht
auditierten Kategorien verglichen; `iphone` lag mit 210 aktuell
matchenden Titeln mit Abstand vorn unter den verbleibenden Kandidaten
(monitor_curved 133, vintage_elektronik 108, netzteil 94,
notebook_resell 84, ram 81, sata_ssd 75).

**Vollständiger Active-FP-Audit:** alle 210 damals live matchenden
Titel einzeln durchgesehen, zusätzlich gezielte Suche nach
Ersatzteil-/Defekt-/Verpackungs-/Zubehör-Signalwörtern über den
gesamten iPhone-Teilkorpus. Die deutliche Mehrheit sind eindeutig echte
Gerätverkäufe (Modell + Speichergröße + Zustand/Akku-Prozent/Zubehör-
Angaben) — Akku-Prozentwerte, Displayrisse, Rückseitenrisse o.ä.
beschreiben den Zustand eines real angebotenen, funktionierenden (oder
explizit als "Teildefekt" gekennzeichneten) Geräts und sind **keine**
Fehltreffer, auch wenn sie riskante Käufe darstellen könnten — das
Ruleset filtert Kategorie-Zugehörigkeit, keine Kaufrisiken.

**Kernfund:** 1 Titel — `Titel: Leere Originalverpackung Apple iPhone
11 - 128GB - Schwarz (Black)` (5€) — matcht als "iPhone 11 (≤256GB) ★
Top-Deal", obwohl der Titel explizit eine **leere** Verpackung ohne
Gerät beschreibt (der Preis von 5€ ist selbst schon ein starkes Indiz).
Identisches Muster zum bereits in `handhelds.yaml` gelösten
"leere box"-Fall.

**Zurückgestellter Zweitfund (P2/NO-FIX):** 2 Titel mit "Zubehörpaket"
im gesamten iPhone-Korpus, mit **gegensätzlichem** Befund: `iPhone 15
Pro 128GB Titan Grau 91% Akku Iphone 17 Pro Umbau *Zubehörpaket*`
(429,99€) nennt eine Akku-Prozentangabe — klar ein echtes Gerät mit
zusätzlichem Bonus-Zubehör. `iPhone 11 128GB Weiß - Zubehörpaket` (91€)
enthält dagegen keinerlei Zustands-/Akku-Angabe — könnte ein reines
Zubehörpaket ohne Gerät sein, ist aber aus dem Titeltext allein nicht
sicher zu entscheiden (kein Zugriff auf den Beschreibungstext). Mit
je 1 Beleg pro (widersprüchlicher) Seite keine belastbare Evidenzbasis
für eine verallgemeinerbare Regel — anders als bei retro_konsolens
"memory card"-Fall gibt es hier keinen klar erkennbaren
Rettungs-Kontextbegriff, der zuverlässig zwischen beiden Fällen
unterscheidet.

**TRUE_POSITIVE-Kollisionen:** 0 — explizit gegen reale Titel mit
"OVP"/Verpackungsbezug im Gerätekontext geprüft (`iPhone 12 Blau 64gb
mit OVP und Ladekabel`, `iPhone 16 Pro 128 GB Titan Weiß | Top Zustand
| OVP + Rechnung` u.a.), alle bleiben unverändert TRUE_POSITIVE.

## Monitor Curved

**Auswahlgrund:** evidenzbasiert — nach iphone erneuter Matchvolumen-
Vergleich der verbleibenden unauditierten Kategorien; `monitor_curved`
lag mit 133 aktuell matchenden Titeln deutlich vorn (vor
vintage_elektronik 108, netzteil 94, notebook_resell 84, ram 81,
sata_ssd 75).

**Vollständiger Active-FP-Audit:** alle 133 damals live matchenden
Titel einzeln durchgesehen. Die Kategorie war bereits aus einer
früheren Preiskalibrierungs-Phase vorgehärtet (Handy-/Smartwatch-
Zubehör-Excludes wie `folie`/`spudger`/`smartwatch` bereits vorhanden)
— die deutliche Mehrheit der 133 Titel sind eindeutig echte
Curved-PC-Monitore (Marke + Modell + Zoll/Hz-Angabe).

**Zwei unabhängige reale Funde:**

1. `Ps4slim + curved Samsung Monitor+controller+Wandhalterung` (110€)
   — ein PS4-Konsolen-Bundle, der Monitor ist nur Bundle-Beilage.
   Identischer Ausschlussgrund wie der bereits bestehende
   "Konsolen"-Exclude-Block (`playstation`/`xbox`/`nintendo`/`switch`)
   — die dortige Absicht ("Komplette PCs/Laptops (Monitor nur als
   Bundle-Beilage erwähnt)") gilt hier 1:1, aber `"playstation"` allein
   deckt die verbreitete Kurzform `"ps4"`/`"ps4slim"` nicht ab. Root
   Cause identifiziert: `"ps4slim"` ist als zusammengeschriebenes Wort
   ohne Wortgrenze zwischen `"ps4"` und `"slim"` — ein bare
   `"ps4"`-Exclude hätte NICHT gegriffen (siehe
   `matcher.py::_contains_term()`-Wortgrenzenlogik). Zusätzlich
   `"ps1"`-`"ps5"` ergänzt, analog zum bereits in `gpu.yaml`
   etablierten Muster für denselben Ausschlussgrund — 0 Kollisionen
   gegen den vollständigen Korpus geprüft (u.a. keine "PS/2"-
   Anschluss-Nennung vorhanden, die fälschlich anschlagen könnte).
2. `Klappbarer Heimtrainer F‑Bike CURVED LCD-Display Fahrrad Top` (79€)
   — ein Fitnessgerät mit eigenem gebogenem Trainingscomputer-Display,
   kein PC-Monitor. Strukturell identisches Muster zu den bereits
   bestehenden Handy-/Smartwatch-Zubehör-Excludes (Klasse "Nicht-PC-
   Gerät mit eigenem 'curved'-Display").

**TRUE_POSITIVE-Kollisionen:** 0 — gegen den vollständigen
133-Titel-Match-Korpus geprüft.

## Vintage Elektronik

**Auswahlgrund:** evidenzbasiert — nach monitor_curved erneuter
Matchvolumen-Vergleich; `vintage_elektronik` lag mit 108 aktuell
matchenden Titeln vorn (vor netzteil 94, notebook_resell 84, ram 81,
sata_ssd 75).

**Größter Einzelfund dieses gesamten Durchlaufs:** vollständiger
Active-FP-Audit über alle 108 damals live matchenden Titel ergab **11
Muster über 40 Titel** — mehr als bei jeder anderen bisher auditierten
Kategorie außer office_pc.

**Root Cause:** Die "Profi-CRT-Monitor"-Regeln (Sony PVM/BVM/Trinitron)
hatten — anders als die direkt darunterstehenden
"Röhrenfernseher"-Regeln — **keinerlei** Excludes für Ersatzteile,
Zubehör oder Fernbedienungen. Die Röhrenfernseher-Regeln excludieren
bereits seit Phase 12 `"fernbedienung"`/`"ersatzteil"`/
`"netzschalter"`/`"widerstand"`/`"schaltplan"` — dieser Schutz wurde
beim Hinzufügen der Profi-CRT-Monitor-Regeln (höheres Preissegment,
dieselbe Produktklasse) nicht mit übernommen. Sony-Broadcast-Monitore
(PVM/BVM) haben einen aktiven Ersatzteilmarkt (Platinen, Transformatoren,
Chips, Akkus, Ladegeräte, Kabel) — genau diese Ersatzteile matchten
bisher als komplettes Gerät.

**Zusätzlich ein kategorieweiter, regelunabhängiger Fund:** 6
Sammlerfoto-/Postkarten-Titel (`"- Altes Foto"`/`"- Foto"` als
Titelsuffix, z.B. `Giraffe auf Röhrenfernseher 1954 - Altes Foto
1950er`) sowie vereinzelte Merchandise-/Dokumentations-/Zubehör-Titel
(T-Shirt, Wandhalterung, Kippsicherung, Schulkarte,
Funktionsbeschreibung, Werbekoffer, SCART-Cinch-Adapter-Konvolut) — alle
matchten unabhängig von der Profi-CRT-Lücke über die generischen
Röhrenfernseher-Suchbegriffe.

**Kollisionsschutz besonders geprüft bei zwei Begriffen:**
- Bare `"subwoofer"` hätte einen echten TRUE_POSITIVE-Röhrenverstärker
  mit Subwoofer-Ausgang getroffen (`HiFi Bluetooth Hybrid Röhren
  Verstärker Stereo Subwoofer Tube Power Amplifier`) — stattdessen die
  engere Phrase `"subwoofer für"`/`"subwoofer von"` verwendet.
- Bare `"netzkabel"` hätte potenziell ein reales Komplettgerät treffen
  können, das "inkl. Netzkabel" bewirbt — stattdessen die engere Phrase
  `"netzkabel für"` verwendet.

**Bewusst zurückgestellt (P2/NO-FIX):** `SONY IC VG-469 LXP-P75ST for
Sony BVM-20F1 Monitor` (1 Titel) — bare `"ic"` als 2-Zeichen-Begriff zu
generisch/riskant für einen einzelnen Beleg.

**TRUE_POSITIVE-Kollisionen:** 0 — gegen den vollständigen
108-Titel-Match-Korpus geprüft.

## Netzteil

**Auswahlgrund:** evidenzbasiert — nach vintage_elektronik erneuter
Matchvolumen-Vergleich; `netzteil` lag mit 94 aktuell matchenden
Titeln vorn (vor notebook_resell 84, ram 81, sata_ssd 75).

**Vollständiger Active-FP-Audit:** alle 94 damals live matchenden
Titel einzeln durchgesehen. Anders als bei den bisherigen Kategorien
mit Titel-Keyword-Matching nutzt `netzteil.yaml` einen
Hardware-Detector (`categories/detectors/psu.py`,
`min_psu_watt`/`max_psu_watt`) — die Wattzahl im Titel entscheidet über
die Preisstufe, unabhängig vom Produkttyp.

**Kernfund:** 2 Titel — `1000W Verstärker Stereo Amplifier HIFI
Digital Bluetooth FM USB Vollverstärker` und `600W Bluetooth Mini
Verstärker HiFi Power Audio Stereo Bass Amplifier USB MP3 FM` — matchen
als PC-Netzteil, obwohl es sich um HiFi-Verstärker handelt. Root Cause:
der `psu.py`-Detector interpretiert jede Wattzahl im Titel als
PSU-Leistung, ohne zwischen "Netzteil-Watt" und
"Verstärker-Ausgangs-Watt" zu unterscheiden — ein strukturelles Muster,
nicht auf diese beiden Titel beschränkt (jeder HiFi-Verstärker mit
Watt-Angabe im 550-1100W-Bereich wäre potenziell betroffen), aber
aktuell nur mit 2 realen Belegen im Korpus.

**Sonstige Auffälligkeit, bewusst NICHT als Fehltreffer gewertet:** `Pc
Gehäuse Crosair inkl Netzteil 750w` — ein PC-Gehäuse-Angebot mit
eingebautem 750W-Netzteil als Bundle-Bestandteil. Anders als bei den
"Monitor nur als Bundle-Beilage"-Fällen in anderen Kategorien ist das
Netzteil hier ein echtes, mitverkauftes Bauteil (kein reines
Zubehör-Anhängsel eines Fremdprodukts) — kein eindeutiger
Fehlklassifikations-Fall.

**TRUE_POSITIVE-Kollisionen:** 0 — `"verstärker"`/`"amplifier"`
kommen in keinem der 92 verbleibenden echten Netzteil-Titel vor.

## Notebook Resell

**Auswahlgrund:** evidenzbasiert — nach netzteil erneuter
Matchvolumen-Vergleich; `notebook_resell` lag mit 84 aktuell
matchenden Titeln vorn (vor ram 81, sata_ssd 75, controller 56).

**Vollständiger Active-FP-Audit:** alle 84 damals live matchenden
Titel einzeln durchgesehen. Die dritte `require_all_of`-Gruppe der
ThinkPad-Regel akzeptiert bare `"ssd"`/`"nvme"` als Alternative zu
einer konkreten Speichergrößenangabe (ursprünglich eingeführt, um
Einzelteil-Angebote ohne jede GB-Angabe abzufangen, siehe bestehender
Regel-Kommentar) — eine vorangestellte Negation wird dabei nicht
erkannt.

**Kernfund:** 2 Titel (Duplikate desselben Angebots unter
verschiedenen IDs) — `Lenovo ThinkPad L14 Gen 3 | Ryzen 5 PRO 5675U |
BIOS OK | Ohne SSD/RAM #TR326`/`#TR343` — matchen als komplettes
Notebook, obwohl der Titel explizit **weder RAM noch SSD** installiert
ausweist (bloßes Mainboard+CPU-Gehäuse). "ssd" matcht als Teilstring
von "SSD/RAM" identisch wie in einem echten Angebot.

**Bewusst NICHT generalisiert:** 2 weitere, strukturell ähnliche Titel
(`...8GB RAM OHNE SSD...`, `...8GB RAM ohne SSD ohne Netzteil...`)
haben echtes RAM und erfüllen die Gruppe bereits unabhängig über die
RAM-Größe (`"8gb"`) — ein bare `"ohne ssd"`-Exclude hätte diese
echten Barebone-mit-RAM-Angebote fälschlich blockiert. Stattdessen die
exakte Phrase `"ohne ssd/ram"` verwendet, die nur beide fehlenden
Komponenten gemeinsam trifft.

**TRUE_POSITIVE-Kollisionen:** 0 — gegen den vollständigen
84-Titel-Match-Korpus geprüft, inkl. der beiden Barebone-mit-RAM-Titel.

## RAM

**Auswahlgrund:** evidenzbasiert — nach notebook_resell erneuter
Matchvolumen-Vergleich; `ram` lag mit 81 aktuell matchenden Titeln vorn
(vor sata_ssd 75, controller 56).

**Vollständiger Active-FP-Audit:** alle 81 damals live matchenden
Titel einzeln durchgesehen. Zwei unabhängige Wortgrenzen-/
Schreibweisen-Lücken bei bereits bestehenden Excludes gefunden (kein
neues Konzept, reine Vervollständigung):

1. `Samsung 8GB DDR4 RAM Riegel für Laptops` — die Pluralform
   `"Laptops"` wird von der bereits bestehenden bare `"laptop"`-Exclude
   wegen fehlender Wortgrenze nicht erfasst (`_contains_term()`
   verlangt ein Wortende direkt nach "laptop"; das trailing "s" in
   "Laptops" bricht die Grenze).
2. `SK hynix16GB(2x8GB) DDR4 SO- DIMM 1Rx8 PC4-3200AA-SA2-11` — die
   Schreibweise `"SO- DIMM"` (Bindestrich direkt nach "SO", dann
   Leerzeichen vor "DIMM") wird von keinem der drei bereits
   bestehenden Varianten (`"sodimm"`/`"so-dimm"`/`"so dimm"`) exakt
   getroffen.

**TRUE_POSITIVE-Kollisionen:** 0 — gegen den vollständigen
81-Titel-Match-Korpus geprüft.

## SATA SSD

**Auswahlgrund:** evidenzbasiert — nach ram erneuter
Matchvolumen-Vergleich; `sata_ssd` lag mit 75 aktuell matchenden
Titeln vorn (vor controller 56, autoradio_opel_corsa 55).

**Vollständiger Active-FP-Audit:** alle 75 damals live matchenden
Titel einzeln durchgesehen. Die Kategorie hat bereits einen sehr
umfangreichen, mehrfach nachgeschärften `exclude_category`-Block
(Laptop-Modellreihen, Komplett-PC-Modellreihen, HDD-Modellreihen,
Server) — die Mehrheit der 75 Titel sind eindeutig echte interne 2,5"-
SATA-SSDs.

**Kernfund:** 3 Titel — `SanDisk Portable SSD 1 TB Speicher`, `Seagate
Expansion SSD, 500GB, Portable External Solid State Drive for PC and
Mac`, `SSK Pro 1TB SSD Externer Speicher USB-Stick` — matchen als
interne SATA-SSD, obwohl es sich um externe USB-Laufwerke handelt
(kein SATA-Interface). Root Cause: die bestehenden Excludes
`"externe festplatte"`/`"externes gehaeuse"` decken nur diese beiden
exakten Phrasen ab — die im Handel gängigen Produktbezeichnungen
"Portable SSD" und "Externer Speicher" fallen nicht darunter.

**TRUE_POSITIVE-Kollisionen:** 0 — `"portable"`/`"externer speicher"`
kommen in keinem der 72 verbleibenden echten SATA-SSD-Titel vor.

## Controller

**Auswahlgrund:** evidenzbasiert — Fortsetzung des Durchlaufs mit den
verbleibenden, kleineren Kategorien nach dem ersten Abschluss-Report
(12 Kategorien). `controller` hatte mit 56 aktuell matchenden Titeln
das höchste Matchvolumen der verbleibenden Kategorien (vor
autoradio_opel_corsa 55, macbook 50).

**Vollständiger Active-FP-Audit:** alle 56 damals live matchenden
Titel einzeln durchgesehen. **5 unabhängige reale Muster über 6
Titel** gefunden:

1. Controller-Halter/-Ständer (`Controller Halter "Fight" Faust
   Design`) und Wandhalterung (`PS5 Wandhalterung für PS5 Controller
   mit Controller-Halter...` — Kompositum, von der bereits
   bestehenden bare `"halterung"`-Exclude wegen fehlender Wortgrenze
   nicht erfasst) — Zubehör, kein Controller selbst.
2. Ersatz-Akku für einen Controller.
3. Wireless-Empfänger/-Dongle für PC (`...Adapter Empfänger Stick
   Windows 10 11 PC USB DE`).
4. Ersatzteil-Angebot (`2x Ersatz Analog Sticks für PS5 Controller
   DualSense`, 2,95€ — der Preis allein ist schon ein starkes Indiz).
   Bewusst NICHT bare `"sticks"` verwendet: würde den echten
   TRUE_POSITIVE-Titel `TMR Sticks! Nintendo Switch 1 Pro
   Controller...` treffen (Stick-Technologie als Verkaufsargument,
   kein Ersatzteil-Angebot).
5. **Bereits im bestehenden Regel-Kommentar dokumentiertes Restrisiko,
   jetzt real bestätigt:** `XBOX Series S 1TB + 2
   Controller[BITTE BESCHREIBUNG LESEN]` — ein komplettes
   Konsolen-Bundle, das weder `"konsole"` noch `"playstation"` im
   Titel nennt (nur `"xbox"`, das aus den bereits im Code
   dokumentierten Gründen nicht blanket-excludiert werden kann). Der
   YAML-Kommentar hatte diesen genauen Fall bereits vorab als
   Restrisiko benannt und eine Kalibrierung "anhand realer
   Scan-Treffer" empfohlen — dieser Audit-Schritt liefert den ersten
   realen Beleg. Fix: `"1tb"` als Speicherkapazitäts-Signal (kein
   echter Standalone-Controller-Titel nennt eine Speicherkapazität).

**TRUE_POSITIVE-Kollisionen:** 0 — gegen den vollständigen
56-Titel-Match-Korpus geprüft, inkl. des "TMR Sticks"-Grenzfalls.

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

**gpu:** kein Fix — 0 reale aktive Fehltreffer, keine Regelanpassung.

**lego_minifiguren:** `app/rules/lego_minifiguren.yaml`, `exclude_category`:
**4 neue** bare-phrase Excludes für das **1 gefixte Muster**
(`ohne figur`, `ohne figuren`, `ohne minifigur`, `ohne minifiguren`) —
Singular/Plural beider Wortformen, analog zum bereits etablierten
Singular/Plural-Muster in `handhelds.yaml` (`ersatzstift`/
`ersatzstifte`). Bewusst NICHT ergänzt: andere Negationswörter
("keine"/"kein") — kein Korpusbeleg dafür. 0 Kollisionen gegen den
vollständigen 455-Titel-Match-Korpus. Reine additive
`exclude_category`-Ergänzung, kein neuer Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_lego_minifiguren_active_fp_audit_fix.py`
(3 Tests: 1 FP-Regressionstest für den real bestätigten Fehltreffer-
Titel, 1 Test für die 3 unbelegten aber strukturell identischen
Singular/Plural-Geschwisterformen, 1 Sammel-TP-Sicherheitstest inkl.
der positiven Gegenprobe "Mit Figuren" statt "Ohne Figuren").

**iphone:** `app/rules/iphone.yaml`, `exclude_category`: **1 neue**
bare-phrase Exclude für das **1 gefixte Muster** (`leere
originalverpackung`), identisches Muster/identische Begründung wie
`"leere box"` in `handhelds.yaml`. 0 Kollisionen gegen den
vollständigen 210-Titel-Match-Korpus, explizit gegen reale OVP-/
Verpackungs-Titel im Gerätekontext geprüft. Reine additive
`exclude_category`-Ergänzung, kein neuer Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_iphone_active_fp_audit_fix.py`
(2 Tests: 1 FP-Regressionstest für den real bestätigten Fehltreffer-
Titel, 1 Sammel-TP-Sicherheitstest für 4 reale OVP-/Verpackungs-Titel
im Gerätekontext).

**monitor_curved:** `app/rules/monitor_curved.yaml`, `exclude_category`:
**7 neue** bare-phrase Excludes für die **2 gefixten Muster**
(`ps4slim`, `ps1`, `ps2`, `ps3`, `ps4`, `ps5` im bestehenden
"Konsolen"-Block; `heimtrainer` im bestehenden Handy-/Smartwatch-
Zubehör-Block). Alle 0 Kollisionen gegen den vollständigen
133-Titel-Match-Korpus. Reine additive `exclude_category`-Ergänzung,
kein neuer Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_monitor_curved_active_fp_audit_fix.py`
(4 Tests: 1 FP-Regressionstest für den real bestätigten PS4-Bundle-
Fehltreffer, 1 Test für 2 unbelegte aber strukturell identische
PS-Kurzform-Geschwisterfälle, 1 FP-Regressionstest für den real
bestätigten Heimtrainer-Fehltreffer, 1 Sammel-TP-Sicherheitstest für 4
reale Curved-Monitor-Titel).

**vintage_elektronik:** `app/rules/vintage_elektronik.yaml`,
`exclude_category`: **25 neue** bare-word/phrase Excludes für die **11
gefixten Muster** — auf Kategorie-Ebene ergänzt statt dreifach pro
Rating-Stufe der Profi-CRT-Monitor-Regel dupliziert (`board`,
`semiconductor`, `akku`, `charger`, `assy`, `protection panel`,
`breakout adapter`, `einbauset`, `netzkabel für` für Ersatzteile/Zubehör;
`fernbedienung`, `ersatzfernbedienung` für Fernbedienungen; `subwoofer
für`, `subwoofer von` für Subwoofer-Zubehör statt bare `subwoofer`;
`foto`, `t-shirt`, `shirt`, `wandhalterung`, `kippsicherung`,
`kippschutz`, `schulkarte`, `rollkarte`, `funktionsbeschreibung`,
`werbekoffer`, `vertreterkoffer`, `cinch adapter` für Sammler-/
Merchandise-/Dokumentations-Artikel). Alle 0 Kollisionen gegen den
vollständigen 108-Titel-Match-Korpus, zwei Begriffe (`subwoofer`,
`netzkabel`) bewusst NICHT bare verwendet, um reale TRUE_POSITIVE-
Kollisionen zu vermeiden (siehe Abschnitt "Vintage Elektronik" oben).
Reine additive `exclude_category`-Ergänzung, kein neuer
Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_vintage_elektronik_active_fp_audit_fix.py`
(5 Tests: 4 FP-Regressions-Testfunktionen, die zusammen alle 40 real
bestätigten Fehltreffer-Titel über alle 11 Muster abdecken, 1
Sammel-TP-Sicherheitstest inkl. des Subwoofer-Grenzfalls).

**netzteil:** `app/rules/netzteil.yaml`, `exclude_category`: **2 neue**
bare-word Excludes für das **1 gefixte Muster** (`verstärker`,
`amplifier`). 0 Kollisionen gegen den vollständigen 94-Titel-Match-
Korpus. Reine additive `exclude_category`-Ergänzung, kein Eingriff in
`categories/detectors/psu.py` selbst (strukturelle Root Cause bleibt
dokumentiert, aber unangetastet — Detector-Änderung wäre ein größerer,
eigener Schritt).

Neue Regressionstestdatei: `app/tests/test_netzteil_active_fp_audit_fix.py`
(2 Tests: 1 FP-Regressionstest für beide real bestätigten
HiFi-Verstärker-Fehltreffer, 1 Sammel-TP-Sicherheitstest für 4 reale
Netzteil-Titel).

**notebook_resell:** `app/rules/notebook_resell.yaml`,
`exclude_category`: **1 neue** bare-phrase Exclude für das **1 gefixte
Muster** (`ohne ssd/ram`, exakte Phrase statt generischem `ohne ssd`,
um die 2 realen Barebone-mit-RAM-TRUE_POSITIVES nicht zu treffen). 0
Kollisionen gegen den vollständigen 84-Titel-Match-Korpus. Reine
additive `exclude_category`-Ergänzung, kein neuer Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_notebook_resell_active_fp_audit_fix.py`
(3 Tests: 1 FP-Regressionstest für beide real bestätigten "Ohne
SSD/RAM"-Fehltreffer, 1 gezielter Kollisionstest für die 2 echten
Barebone-mit-RAM-Titel, 1 Sammel-TP-Sicherheitstest für 2 reale
ThinkPad-Titel).

**ram:** `app/rules/ram.yaml`, `exclude_category`: **2 neue**
bare-word/phrase Excludes für die **2 gefixten Muster** (`laptops`,
`so- dimm`) — reine Vervollständigung bereits bestehender Excludes
(`laptop`, `sodimm`/`so-dimm`/`so dimm`), kein neues Konzept. 0
Kollisionen gegen den vollständigen 81-Titel-Match-Korpus.

Neue Regressionstestdatei: `app/tests/test_ram_active_fp_audit_fix.py`
(3 Tests: 2 FP-Regressions-Testfunktionen für beide real bestätigten
Fehltreffer, 1 Sammel-TP-Sicherheitstest für 3 reale RAM-Titel).

**sata_ssd:** `app/rules/sata_ssd.yaml`, `exclude_category`: **2 neue**
bare-word/phrase Excludes für das **1 gefixte Muster** (`portable`,
`externer speicher`) — Ergänzung der bereits bestehenden, aber zu eng
gefassten Excludes `externe festplatte`/`externes gehaeuse`. 0
Kollisionen gegen den vollständigen 75-Titel-Match-Korpus.

Neue Regressionstestdatei: `app/tests/test_sata_ssd_active_fp_audit_fix.py`
(2 Tests: 1 FP-Regressionstest für alle 3 real bestätigten
Fehltreffer, 1 Sammel-TP-Sicherheitstest für 3 reale SATA-SSD-Titel).

**controller:** `app/rules/controller.yaml`, `exclude_category`: **5
neue** bare-word Excludes für die **5 gefixten Muster** (`halter`,
`akku`, `empfänger`, `ersatz`, `1tb`). Bewusst NICHT bare `"sticks"`
(Kollisionsrisiko mit einem echten TRUE_POSITIVE-Titel, siehe Abschnitt
"Controller" oben). Alle 0 Kollisionen gegen den vollständigen
56-Titel-Match-Korpus. Reine additive `exclude_category`-Ergänzung,
kein neuer Matcher-Mechanismus.

Neue Regressionstestdatei: `app/tests/test_controller_active_fp_audit_fix.py`
(3 Tests: 1 FP-Regressionstest für die 5 real bestätigten Zubehör-/
Ersatzteil-Fehltreffer, 1 FP-Regressionstest für den Konsolen-Bundle-
Fehltreffer, 1 Sammel-TP-Sicherheitstest inkl. des "TMR Sticks"-
Grenzfalls).

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

**gpu:** kein separater Testlauf nötig (kein Code-/YAML-Änderung).

**lego_minifiguren:**
- `pytest app/tests/ -k "lego" -v`: **25/25 passed** (3 neue Tests + 22
  bereits bestehende lego_minifiguren-relevante Tests aus
  `test_matcher_price_calibration_applied.py`,
  `test_matcher_price_calibration_matching_fixes.py`,
  `test_matcher_resale_price_groups.py`, `test_rule_analyzer.py`,
  `test_rule_regressions.py`)

**iphone:**
- `pytest app/tests/ -k "iphone" -v`: **15/15 passed** (2 neue Tests +
  13 bereits bestehende iphone-relevante Tests aus
  `test_matcher_gehaeuse_shell_fix.py`,
  `test_matcher_price_calibration_applied.py`,
  `test_rule_service_modding_fix.py`)

**monitor_curved:**
- `pytest app/tests/ -k "monitor_curved" -v`: **4/4 passed** (alle neu,
  keine bestehenden monitor_curved-spezifischen Tests vor diesem
  Schritt vorhanden)

**vintage_elektronik:**
- `pytest app/tests/ -k "vintage_elektronik" -v`: **5/5 passed** (alle
  neu, keine bestehenden vintage_elektronik-spezifischen Tests vor
  diesem Schritt vorhanden)

**netzteil:**
- `pytest app/tests/ -k "netzteil" -v`: **20/20 passed** (2 neue Tests
  + 18 bereits bestehende netzteil-relevante Tests aus
  `test_detector_lieferumfang.py`, `test_detector_psu.py`,
  `test_matcher_context_aware_exclude.py`,
  `test_matcher_controller_accessory_fix.py`,
  `test_matcher_handheld_false_positives.py`,
  `test_matcher_psu_requirement.py`, `test_notebook_resell_mainboard_fix.py`,
  `test_retro_konsolen_active_fp_audit_fix.py`)

**notebook_resell:**
- `pytest app/tests/ -k "notebook_resell" -v`: **21/21 passed** (3 neue
  Tests + 18 bereits bestehende notebook_resell-relevante Tests aus
  `test_notebook_resell_gaming_fix.py`,
  `test_notebook_resell_mainboard_fix.py`)

**ram:**
- `pytest app/tests/ -k "ram" -v`: **42/42 passed** (3 neue Tests + 39
  bereits bestehende ram-relevante Tests aus `test_detector_ram.py`,
  `test_detector_storage.py`, `test_matcher_deal_score_integration.py`,
  `test_matcher_hardware_requirements.py`,
  `test_matcher_price_calibration_matching_fixes.py`,
  `test_notebook_resell_active_fp_audit_fix.py`,
  `test_notify_max_price_and_sata_ssd_fix.py`, `test_rule_regressions.py`,
  `test_scraper_ebay.py`)

**sata_ssd:**
- `pytest app/tests/ -k "sata_ssd" -v`: **20/20 passed** (2 neue Tests
  + 18 bereits bestehende sata_ssd-relevante Tests aus
  `test_app_category_grouped_scan.py`, `test_detector_storage.py`,
  `test_matcher_ssd_capacity_requirement.py`,
  `test_notify_max_price_and_sata_ssd_fix.py`,
  `test_sata_ssd_search_improvements.py`)

**controller:**
- `pytest app/tests/ -k "controller" -v`: **69/69 passed** (3 neue
  Tests + 66 bereits bestehende controller-relevante Tests aus
  `test_konsolen_bundles_precision_phrases_fix.py`,
  `test_matcher_context_aware_exclude.py`,
  `test_matcher_controller_accessory_fix.py`,
  `test_matcher_gehaeuse_shell_fix.py`,
  `test_retro_konsolen_controller_signal_fix.py`,
  `test_rule_regressions.py`, `test_rule_service_modding_fix.py`)

**Rule Analyzer (nach allen Schritten):** `0 Findings, 355 Regeln,
19 Kategorien` (unverändert).

**Volle Suite (Zwischenstand nach den ersten zwölf Kategorien dieses
Gesamtprojekts, auf Freigabe ausgeführt):** `pytest app/tests/` —
**1233/1233 passed, 0 failed** (620,33s). Vorheriger dokumentierter
Stand (vor diesem Durchlauf, Basis PR #10): 1197/1197 passed — die
Differenz (36 neue Tests) entspricht den bis dahin neu hinzugekommenen
Regressionstestdateien je auditierter Kategorie. **controller** (3
weitere neue Tests) ist in diesem Suite-Lauf noch NICHT enthalten —
läuft in der finalen Suite mit, sobald der fortgesetzte Durchlauf mit
den verbleibenden kleineren Kategorien erneut abgeschlossen und
freigegeben wird.
