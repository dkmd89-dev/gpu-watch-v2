ACTIVE FP FIX PROGRESS
======================

Historical FPs:
    19

Currently active (Stand vor diesem Batch, verifiziert per benchmark.py
gegen historical_forensics_baseline.json, NACH Wiederherstellung von
konsolen_bundles.yaml -- der vorherige Report-Stand von 2/19 war durch
die zwischenzeitlich fehlende Datei verfälscht):
    5 (iphone, konsolen_bundles/Switch, konsolen_bundles/Xbox,
       retro_konsolen/DS-Lite, konsolen_bundles/PS4 [MANUAL REVIEW])

Fixed during this run:
    1 (iphone)

Remaining (final, nach Nutzerentscheidung -- alle 4 bewusst NICHT
gefixt, siehe MANUAL REVIEW-Abschnitt unten):
    4

Regressions:
    0

Kategorie-Übersicht (final):

    category           | historical_fp | currently_active | fixed | regressions
    gaming_pc           | 1             | 0                 | 1     | 0
    handhelds           | 4             | 0                 | 4     | 0
    iphone              | 1             | 0                 | 1     | 0
    konsolen_bundles    | 6             | 3                 | 3     | 0
    notebook_resell     | 1             | 0                 | 1     | 0
    office_pc           | 2             | 0                 | 2     | 0
    retro_konsolen      | 4             | 1                 | 3     | 0
    GESAMT              | 19            | 4                 | 15    | 0

Routing-Aufschlüsselung (final, alle 19 historischen FP):

    FALSE_POSITIVE -> KEIN_TREFFER:    15
    FALSE_POSITIVE -> SAME_CATEGORY:    4  (alle 4 verbleibend aktiven,
                                             siehe MANUAL REVIEW)
    FALSE_POSITIVE -> OTHER_CATEGORY:   0

----------------------

FIX #1
Category:       iphone
Listing:        Apple iPhone 15 Pro Max 512GB Mainboard Platine mit FaceID
                und Kameramodul (400€)
                https://www.ebay.de/itm/236995682525
Old rule:       iPhone 15 Pro Max (≥512GB) 👍 Guter Preis
New rule:       KEIN_TREFFER
Root cause:     replacement_part_false_positive (confirmed)
Change:         app/rules/iphone.yaml -- exclude_category um "mainboard"/
                "motherboard" ergänzt (bare Wort). Identisches, bereits
                5-fach etabliertes Muster (gaming_pc.yaml/office_pc.yaml/
                notebook_resell.yaml/handhelds.yaml/konsolen_bundles.yaml).
Blast Radius:   0 Kollisionen gegen alle 478 historischen iphone-
                TRUE_POSITIVE-Titel (docs/DASHBOARD_MATCH_FORENSICS.json)
                und den aktuellen found.json-Korpus. Alle 3 im
                price_history.jsonl-Korpus gefundenen "mainboard"/
                "motherboard"-Titel sind eindeutige Ersatzteil-Angebote.
Result:         FALSE_POSITIVE -> KEIN_TREFFER (bestätigter Fix)
Tests:          6 neue Tests (test_iphone_replacement_part_fix.py),
                app/tests/ -k "iphone" -> 19 passed, 0 failed
Regression:     pytest app/tests/ -k "matcher or category_validation or
                ruleset" -> 373 passed, 0 failed
                benchmark.py gegen historical_forensics_baseline.json:
                0 neue CRITICAL/HIGH_CANDIDATE-Fälle in iphone
                rule_analyzer.py: 0 Findings (355 Regeln, 19 Kategorien)
                cross-category: keine andere Kategorie betroffen
                (exclude_category ist kategorie-lokal)
Status:         ERFOLGREICH -- alle Akzeptanzkriterien erfüllt.

----------------------

UNTERSUCHUNG #2-4 (VOR IMPLEMENTIERUNG GESTOPPT -- siehe Begründung unten)

Für die 3 verbleibenden aktiven Fälle (retro_konsolen/DS-Lite,
konsolen_bundles/Switch, konsolen_bundles/Xbox) ergab die
Pflicht-Analyse ("vor jedem Fix", Schritte 1-7) einen Befund, der eine
Nutzerentscheidung erfordert, bevor eine YAML-Änderung vorgenommen wird:

**retro_konsolen/DS-Lite** ("Nintendo DS Lite Handheld-System Weiß
Touchscreen inkl. 4 Spiele", 80€): require_all_of-Gruppe 2 hittet
AUSSCHLIESSLICH über das generische Wort "system". Der etablierte
Fix-Mechanismus (exclude_category_unless_also_contains, bereits für
"netzteil"/"kabel"/"memory card" in derselben Datei produktiv) wäre
technisch anwendbar. ABER: 3 weitere, nahezu identisch formulierte
Titel im aktuellen Korpus/Preishistorie folgen demselben Muster
("Nintendo DS Lite Handheld-System hellblau Touchscreen" [UNCLEAR
gelabelt, nicht FP], "Nintendo DS Handheld-System grün (PAL)
Touchscreen, Mikrofon, Kopfhöreranschluss" [live, ungelabelt],
"Nintendo DS Lite Konvolut 3xHandheld-System..." [live, ungelabelt]) --
alle lesen sich wie echte Geräteverkäufe (Farbe, Touchscreen-Zustand
genannt). Ein Fix würde alle 4 gleichermaßen blockieren, obwohl nur 1
davon als bestätigter FP gelabelt ist.

**konsolen_bundles/Switch** ("Nintendo Switch 32GB Mario Kart 8 Deluxe
Bundle Neon Blau/Rot mit Dock", 135€) und **konsolen_bundles/Xbox**
("Xbox One S 1TB mit Spiele", 80€): beide Titel enthalten BEREITS einen
Speichergrößen-Marker ("32gb" bzw. "1tb"), der im etablierten
Kontext-Mechanismus (exclude_category_unless_also_contains, siehe
"spiele"/"ovp" in derselben Datei) genau als Beweis für ein echtes
Gerät gilt. Der Standard-Fix (Gate für "bundle"/"mit spiele" mit
derselben Marker-Liste) würde diese beiden Fälle GAR NICHT auflösen,
weil die Marker bereits vorhanden sind -- ein tatsächlicher Fix müsste
entweder eine engere Marker-Liste (ohne bloße Speichergrößen) oder
einen anderen Mechanismus verwenden. Stichprobe weiterer "bundle"-Titel
mit demselben Muster zeigt eine Mischung: mindestens 2 lesen sich wie
echte (reparierte) Konsolen ("Nintendo Switch Neon Bundle Neue Sticks
(Kein Drift!) + Extras", "... Grau Bundle Neue Sticks (Kein Drift) +
Extras!"), 1 klar wie ein reines Spiele-Bundle ohne Gerät ("Nintendo
Switch Spiele Bundle", 25€, kein Marker).

Begründung fürs Stoppen: der Auftrag verlangt explizit "Der Fix darf
bestehende echte Retro-Konsolen-Treffer nicht zerstören" bzw. "NICHT
global ... entfernen" und "Vermeide Lösungen wie: remove ... wenn
dadurch echte Treffer verloren gehen könnten". Alle 3 Fälle zeigen
konkrete Evidenz für genau dieses Risiko. Eine automatische Umsetzung
ohne Rückfrage würde gegen diese explizite Vorgabe verstoßen.
Rückfrage an den Nutzer gestellt (siehe Chat) -- Entscheidung: **beide
Fälle NICHT fixen, als Manual-Review dokumentieren.**

----------------------

MANUAL REVIEW REQUIRED
=======================

Alle 4 verbleibenden aktiven Fälle wurden NICHT per YAML-Änderung
gefixt -- 1 auf explizite Auftragsvorgabe (PS4/PS5-HDMI), 3 auf
Nutzerentscheidung nach Risikoabwägung (siehe oben).

------------------------------------------------------------
1. konsolen_bundles / PS4-PS5-HDMI-Reparatur (explizit als
   Manual-Review vorgegeben)
------------------------------------------------------------
Listing:            Playstation 5 PS4 PS5 Slim HDMI Port Nintendo
                     Reparatur USB PRO (50€)
                     https://www.kleinanzeigen.de/s-anzeige/playstation-5-ps4-ps5-slim-hdmi-port-nintendo-reparatur-usb-pro/3431533294-226-3438
Aktuelle Kategorie:  konsolen_bundles
Aktuelle Regel:      PS4 Slim / Pro Bundle ★ Top-Deal
Matchpfad:           require_all_of Gruppe 1: ["ps4","playstation 4"]
                     -> hit "ps4" (aus "PS4" im Titel)
                     require_all_of Gruppe 2: ["slim","pro","bundle",
                     "1tb","500gb","mit spiele"] -> hit "slim"+"pro"
                     ("slim" vermutlich aus "PS5 Slim", "pro" vermutlich
                     aus "USB PRO" -- einem Produkt-/Werkzeugnamen,
                     NICHT aus "PS4 Pro")
Signale:             "Reparatur" im Titel (kein Exclude dafür in dieser
                     Kategorie -- "reparatur service"/"repair service"
                     sind als MEHRWORT-Phrasen excludet, bare
                     "reparatur" bewusst nicht, siehe office_pc.yaml/
                     iphone.yaml-Kommentare zu Service-Excludes:
                     Risiko, echte Zustandsbeschreibungen wie "frisch
                     repariert, funktioniert einwandfrei" zu blockieren)
Warum ambiguous:     Der Titel nennt DREI verschiedene Plattformen
                     (PS5, PS4, Nintendo) UND ein Werkzeug/Zubehörteil
                     ("USB PRO", "HDMI Port") UND einen Dienstleistungs-
                     Hinweis ("Reparatur"). Das liest sich am
                     plausibelsten als Angebot einer HDMI-Port-
                     Reparatur-DIENSTLEISTUNG oder eines Reparatur-
                     Werkzeugs für mehrere Konsolen -- NICHT als Verkauf
                     einer PS4 Slim/Pro-Konsole. "slim"+"pro" matchen
                     nur zufällig durch Wörter, die nicht die PS4
                     selbst beschreiben. Kein einzelnes, sicher
                     verallgemeinerbares Ausschlusswort ohne Risiko,
                     andere Reparatur-Zustandsbeschreibungen ("Akku
                     getauscht, funktioniert perfekt") mitzublockieren.
Mögliche
Lösungsstrategien:  a) bare "reparatur" als exclude_category -- Risiko:
                        könnte echte "frisch repariert"-Zustands-
                        beschreibungen legitimer Konsolen blockieren
                        (kein Blast-Radius-Nachweis vorhanden).
                     b) Mehrwort-Phrase "reparatur service"/"hdmi port
                        reparatur" --träfe diesen Einzelfall eventuell
                        nicht exakt, zu eng für n=1.
                     c) Kontextbewusstes Gate (exclude_category_
                        unless_also_contains) für "pro", das nur bei
                        Mehrfach-Plattform-Nennung (PS4+PS5+Nintendo im
                        selben Titel) greift -- keine Präzedenz im
                        Regelwerk, neue Mechanik, unklarer Blast Radius.
                     Keine der drei Optionen hat eine tragfähige
                     Datenbasis (n=1) -- entspricht CLAUDE.md Regel 4.
Risiko:              MEDIUM (laut Fix-Queue) -- ohne Datenbasis nicht
                     weiter reduzierbar. Explizit NICHT umgesetzt (Auftragsvorgabe).

------------------------------------------------------------
2. retro_konsolen / Nintendo DS Lite (Nutzerentscheidung: nicht fixen)
------------------------------------------------------------
Listing:            Nintendo DS Lite Handheld-System Weiß Touchscreen
                     inkl. 4 Spiele (80€)
                     https://www.ebay.de/itm/398266334210
Aktuelle Kategorie:  retro_konsolen
Aktuelle Regel:      Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay
Matchpfad:           require_all_of Gruppe 1: ["nintendo 64","n64",
                     "gamecube","nintendo ds"] -> hit "nintendo ds"
                     require_all_of Gruppe 2: ["konsole","heimkonsole",
                     "spielekonsole","gerät","system","netzteil",
                     "kabel","slim","fat","komplett","memory card"]
                     -> hit AUSSCHLIESSLICH "system" (aus
                     "Handheld-System")
Signale:             kein Zubehör-/Ersatzteil-/Spiel-Indikator im
                     Titel (Forensik-Evidenz: leer)
Warum ambiguous:     Etablierter Fix-Mechanismus
                     (exclude_category_unless_also_contains, bereits
                     produktiv für "netzteil"/"kabel"/"memory card" in
                     retro_konsolen.yaml) wäre technisch direkt
                     anwendbar. Aber: 3 weitere, nahezu identisch
                     formulierte Titel im aktuellen Korpus/
                     Preishistorie ("...Handheld-System hellblau
                     Touchscreen" [selbst UNCLEAR gelabelt, NICHT FP],
                     "...Handheld-System grün (PAL) Touchscreen,
                     Mikrofon, Kopfhöreranschluss" [live, ungelabelt],
                     "...Konvolut 3xHandheld-System..." [live,
                     ungelabelt]) folgen demselben lexikalischen Muster
                     und lesen sich allesamt wie echte Geräteverkäufe
                     (Farbe, Zustand, Ausstattung genannt). Kein
                     lexikalisches Unterscheidungsmerkmal zwischen dem
                     bestätigten FP und den 3 mutmaßlich echten
                     Treffern gefunden.
Mögliche
Lösungsstrategien:  a) "system" gaten wie "netzteil"/"kabel" (Kontext:
                        controller/konsole/ersatzkonsole) -- würde alle
                        4 "Handheld-System"-Titel gleichermaßen
                        blockieren, nicht nur den bestätigten FP.
                     b) Preis-/Spiele-Kombination als zusätzliches
                        Signal (dieser Fall hat "inkl. 4 Spiele") --
                        keine Präzedenz, widerspricht zudem der
                        Auftragsvorgabe (keine Preisschwellen-Änderung
                        ohne Datenbasis).
                     c) Manuelle Einzelfall-Prüfung mit mehr Kontext
                        (Bildmaterial/Beschreibung) -- außerhalb der
                        Möglichkeiten dieses Tools (nur Titel/Preis
                        verfügbar).
Risiko:              HIGH (laut Fix-Queue, bestätigt durch diese
                     Analyse). Nutzerentscheidung: NICHT umgesetzt.

------------------------------------------------------------
3. konsolen_bundles / Nintendo Switch Mario Kart Bundle
   (Nutzerentscheidung: nicht fixen)
------------------------------------------------------------
Listing:            Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle
                     Neon Blau/Rot mit Dock (135€)
                     https://www.ebay.de/itm/137602406753
Aktuelle Kategorie:  konsolen_bundles
Aktuelle Regel:      Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
Matchpfad:           require_all_of Gruppe 1: ["nintendo switch",
                     "switch oled","switch konsole"] -> hit
                     "nintendo switch"
                     require_all_of Gruppe 2: ["konsole",
                     "spielkonsole","spielekonsole","heimkonsole",
                     "bundle","set","mit spiele","ovp","system"] ->
                     hit AUSSCHLIESSLICH "bundle"
Signale:             Titel enthält "32GB" (echter Speichergrößen-
                     Marker der Basis-Switch) UND "Dock" (Zubehör-
                     Hinweis, von der Forensik als Indiz gegen ein
                     komplettes Gerät gewertet)
Warum ambiguous:     Der bereits produktive Kontext-Mechanismus
                     (exclude_category_unless_also_contains für
                     "ovp"/"spiele" in derselben Datei) verwendet exakt
                     dieselbe Marker-Liste, die "32gb" als Beweis für
                     ein echtes Gerät akzeptiert -- ein Gate für
                     "bundle" mit dieser Liste würde diesen Fall GAR
                     NICHT blockieren, weil "32gb" bereits vorhanden
                     ist. Ein wirksamer Fix bräuchte eine ENGERE Liste
                     ohne bloße Speichergrößen. Gelesen als Ganzes
                     ("Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle
                     Neon Blau/Rot mit Dock") beschreibt der Titel
                     plausibel eine vollständige Standard-Switch
                     (32GB ist die reale Speichergröße des
                     Basis-Modells, "Neon Blau/Rot" die reale
                     Standard-Joy-Con-Farbe) inkl. Spiel und Dock --
                     liest sich wie ein echter Verkauf, nicht wie ein
                     Zubehör-/Spiel-Angebot.
Mögliche
Lösungsstrategien:  a) Speichergrößen-Marker aus der Kontext-Liste NUR
                        für "bundle"/"set"/"mit spiele" entfernen --
                        Stichprobe (price_history.jsonl) zeigt aber
                        mind. 2 vermutlich echte, reparierte Konsolen
                        mit demselben "bundle"-only-Muster ("Nintendo
                        Switch Neon Bundle Neue Sticks (Kein Drift!) +
                        Extras", "...Grau Bundle Neue Sticks (Kein
                        Drift) + Extras!") -- würde beide mitblockieren.
                     b) "Dock" als eigenes kontextbewusstes Gate
                        (analog "vertical stand") -- kein Bundle-
                        Konnektor-Nachweis für diesen Einzelfall (n=1),
                        keine belastbare Datenbasis.
Risiko:              HIGH (laut Fix-Queue, bestätigt: mind. 2 bekannte
                     Kollisionskandidaten im aktuellen Korpus).
                     Nutzerentscheidung: NICHT umgesetzt.

------------------------------------------------------------
4. konsolen_bundles / Xbox One S mit Spielen
   (Nutzerentscheidung: nicht fixen)
------------------------------------------------------------
Listing:            Xbox One S 1TB mit Spiele (80€)
                     https://www.kleinanzeigen.de/s-anzeige/xbox-one-s-1tb-mit-spiele/3479889108-279-4400
Aktuelle Kategorie:  konsolen_bundles
Aktuelle Regel:      Xbox One S / One X 👍 Guter Preis
Matchpfad:           require_all_of Gruppe 1: ["xbox one s",
                     "xbox one x"] -> hit "xbox one s"
                     require_all_of Gruppe 2: ["konsole","bundle",
                     "set","mit spiele","ovp","system"] -> hit
                     AUSSCHLIESSLICH "mit spiele"
Signale:             Titel enthält "1TB" (echter Speichergrößen-
                     Marker der Xbox One S 1TB-Variante), keine
                     Zubehör-/Ersatzteil-Indikatoren
Warum ambiguous:     Identisches Problem wie Fall 3: "1tb" ist bereits
                     in der Kontext-Marker-Liste enthalten, die für
                     "spiele"/"ovp" in derselben Datei produktiv ist --
                     ein Gate für "mit spiele" mit dieser Liste würde
                     diesen Fall NICHT blockieren. "Xbox One S 1TB mit
                     Spiele" liest sich als plausibler echter Verkauf
                     (reale Speichergröße + Modellname + "mit Spiele"
                     als Bundle-Hinweis), nicht als reines
                     Spiele-Angebot.
Mögliche
Lösungsstrategien:  a) Speichergrößen-Marker aus der Kontext-Liste NUR
                        für "mit spiele"/"bundle" entfernen -- gleiches
                        Risiko wie bei Fall 3, hier ohne einen
                        zusätzlichen Zubehör-Hinweis wie "Dock", der
                        eine Unterscheidung ermöglichen würde.
                     b) Keine tragfähige Alternative ohne weitere
                        Datenbasis identifiziert.
Risiko:              HIGH (laut Fix-Queue). Nutzerentscheidung: NICHT
                     umgesetzt.
