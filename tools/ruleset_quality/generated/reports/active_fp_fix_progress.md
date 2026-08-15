ACTIVE FP FIX PROGRESS
======================

Historical FPs:
    19

Currently active (finaler Stand nach diesem Batch):
    3 (konsolen_bundles/Switch, konsolen_bundles/Xbox, retro_konsolen/
       DS-Lite -- alle 3 als Ground-Truth-Artefakt eingestuft, siehe
       GROUND-TRUTH-KORREKTUR unten, KEIN offener Fix-Bedarf)

Fixed during this run:
    2 (iphone, konsolen_bundles/PS4-PS5-HDMI-Reparatur)

Remaining:
    0 mit offenem Fix-Bedarf. 3 als Ground-Truth-Korrektur dokumentiert
    (siehe unten) -- keine YAML-Änderung vorgesehen, da vermutlich keine
    echten Fehltreffer.

Regressions:
    0

Kategorie-Übersicht (final):

    category           | historical_fp | currently_active | fixed | regressions
    gaming_pc           | 1             | 0                 | 1     | 0
    handhelds           | 4             | 0                 | 4     | 0
    iphone              | 1             | 0                 | 1     | 0
    konsolen_bundles    | 6             | 2                 | 4     | 0
    notebook_resell     | 1             | 0                 | 1     | 0
    office_pc           | 2             | 0                 | 2     | 0
    retro_konsolen      | 4             | 1                 | 3     | 0
    GESAMT              | 19            | 3                 | 16    | 0

    Hinweis: die 3 "currently_active" (Switch/Xbox/DS-Lite) sind
    technisch weiterhin FALSE_POSITIVE -> GLEICHE_KATEGORIE laut
    historischem Ground-Truth-Label, wurden aber inhaltlich als
    vermutlich fehlerhaft gelabelt eingestuft (siehe unten) -- nicht
    als "noch zu fixen" zu verstehen.

Routing-Aufschlüsselung (final, alle 19 historischen FP):

    FALSE_POSITIVE -> KEIN_TREFFER:    16
    FALSE_POSITIVE -> SAME_CATEGORY:    3  (Switch/Xbox/DS-Lite, siehe
                                             GROUND-TRUTH-KORREKTUR)
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
Status:         ERFOLGREICH -- alle Akzeptanzkriterien erfüllt.

----------------------

FIX #2
Category:       konsolen_bundles
Listing:        Playstation 5 PS4 PS5 Slim HDMI Port Nintendo Reparatur
                USB PRO (50€)
                https://www.kleinanzeigen.de/s-anzeige/playstation-5-ps4-ps5-slim-hdmi-port-nintendo-reparatur-usb-pro/3431533294-226-3438
Old rule:       PS4 Slim / Pro Bundle ★ Top-Deal
New rule:       KEIN_TREFFER
Root cause:     ambiguous/manual_review laut Fix-Queue -- ursprünglich
                als reine Manual-Review-Vorgabe im Auftrag markiert.
                Auf Vorschlag des Nutzers (kontextbewusstes Gate für
                "reparatur") nachträglich doch umgesetzt, NACH Korrektur
                von 2 konkreten Bugs im ersten Entwurf (siehe unten) --
                kein spekulativer Fix ohne Beleg, sondern verifizierte
                Umsetzung eines bereits im Regelwerk etablierten Musters.
Change:         app/rules/konsolen_bundles.yaml -- neuer Eintrag in
                exclude_category_unless_also_contains für "reparatur"
                (identischer Mechanismus wie "spiele"/"ovp" in
                derselben Datei). Marker-Liste: Geräte-/Modellwörter
                (konsole/spielkonsole/spielekonsole/heimkonsole/system),
                Speichergrößen (1tb/500gb/128gb/64gb/32gb/256gb/512gb/
                2tb), Modellvarianten (xl/oled/lite/v1/v2), "ovp".
                Korrektur ggü. Nutzer-Erstvorschlag: OHNE Markennamen
                ("nintendo"/"playstation"/"xbox" -- beide erstgenannten
                sind im Zielfall selbst bereits vorhanden, jede Regel
                dieser Datei verlangt ohnehin eine Markennennung in
                require_all_of-Gruppe 1) und OHNE "slim"/"pro"/"bundle"/
                "mit spiele" (die auslösende Regel "PS4 Slim / Pro
                Bundle" hat "slim"+"pro" selbst in ihrer eigenen
                require_all_of-Gruppe 2 -- als Kontext verwendet, wären
                sie für genau diese Regelfamilie immer trivial erfüllt).
Blast Radius:   0 Belege für eine echte "repariert"-Zustandsbeschreibung
                im gesamten verfügbaren Korpus (Forensik-Snapshot,
                found.json, price_history.jsonl via title_recovery) --
                alle 3 gefundenen "reparatur"/"repariert"-Titel in
                dieser Kategorie sind Reparatur-Dienstleistungs-/
                Werkzeug-Angebote. Zusätzlich als Sicherheitsnetz (nicht
                als Beleg) ein synthetischer Test mit "frisch repariert"
                + echtem Geräte-Marker -- bleibt korrekt TRUE_POSITIVE.
Result:         FALSE_POSITIVE -> KEIN_TREFFER (bestätigter Fix). Als
                Nebeneffekt zusätzlich "PS4 & PS4 Slim – Reinigung,
                Wärmeleitpaste & Reparatur" (60€, live in found.json,
                nicht Teil der 19 formal gelabelten FP, aber identisches
                Muster) korrekt blockiert.
Tests:          4 neue Tests
                (test_konsolen_bundles_reparatur_kontext_fix.py),
                app/tests/ -k "konsolen_bundle" -> 78 passed, 0 failed
Regression:     pytest app/tests/ -k "matcher or category_validation or
                ruleset or retro_konsolen or handheld" -> 464 passed,
                0 failed. benchmark.py: konsolen_bundles-CRITICAL-Fälle
                (4, unverändert ggü. vorher) enthalten kein "reparatur".
                rule_analyzer.py: 0 Findings (355 Regeln, 19 Kategorien).
Status:         ERFOLGREICH -- alle Akzeptanzkriterien erfüllt.

----------------------

GROUND-TRUTH-KORREKTUR (kein Fix, keine YAML-Änderung)
=======================================================

Für die 3 verbleibenden aktiven Fälle wurde nach Rückfrage und
zusätzlicher Nutzer-Prüfung festgestellt: es handelt sich vermutlich
NICHT um echte Fehltreffer, sondern um fehlerhafte Labels im
historischen Forensik-Snapshot (docs/DASHBOARD_MATCH_FORENSICS.json,
Commit 01afd5b, 2026-08-10). Der Matcher arbeitet in allen 3 Fällen
korrekt -- es wird bewusst KEINE YAML-Änderung vorgenommen.

**konsolen_bundles/Switch** ("Nintendo Switch 32GB Mario Kart 8 Deluxe
Bundle Neon Blau/Rot mit Dock", 135€, Regel "Nintendo Switch (V1/V2/
OLED) 👍 Guter Preis") und **konsolen_bundles/Xbox** ("Xbox One S 1TB
mit Spiele", 80€, Regel "Xbox One S / One X 👍 Guter Preis"): vom
Nutzer nach Prüfung bestätigt als korrekt gematchte TRUE_POSITIVE,
richtige Kategorie. Beide Titel enthalten reale Geräte-Marker (32GB/
1TB) und lesen sich als vollständige Konsolenverkäufe. Das
FALSE_POSITIVE-Label im Forensik-Snapshot war vermutlich selbst
fehlerhaft (automatisierte Root-Cause-Heuristik hat generisches
require_all_of-Hit-Wort ["bundle"]/["mit spiele"] als "schwaches
Signal" gewertet, ohne den restlichen Titelkontext -- inkl. der
bereits vorhandenen Speichergrößen-Marker -- ausreichend zu
berücksichtigen). Keine weitere Aktion.

**retro_konsolen/DS-Lite** ("Nintendo DS Lite Handheld-System Weiß
Touchscreen inkl. 4 Spiele", 80€, Regel "Nintendo Retro-Konsole (N64/
GameCube/DS) ⚠️ Okay" -- Kategorie/Regel-Zuordnung verifiziert per
grep + evaluate(): Nintendo DS/DS Lite ist in diesem Regelwerk bewusst
Teil von retro_konsolen.yaml (Zeile 48/373/393/413, gemeinsame Regel
mit N64/GameCube), NICHT von handhelds.yaml -- Letzteres deckt in
diesem Projekt ausschließlich moderne Handhelds ab (Steam Deck/ROG
Ally/Legion Go), keine eigene DS-Regel vorhanden). Noch nicht mit
gleicher Sicherheit wie Switch/Xbox als TRUE_POSITIVE bestätigt (3
weitere, lexikalisch identische "Handheld-System"-Titel im Korpus,
davon 1 selbst UNCLEAR gelabelt) -- Risikoabwägung nach Rückfrage:
NICHT fixen, da ein Fix vermutlich mehrheitlich echte Treffer
zerstören würde. Bleibt als offene, dauerhaft dokumentierte
Restlücke bestehen (analog zu anderen in STATUS.md dokumentierten
"bewusst nicht gefixten" Mustern), bis eine bessere Datenbasis
(z. B. Beschreibungstext/Bildmaterial) verfügbar ist.

Auftragskonformität: der Auftrag verlangt explizit "Der Fix darf
bestehende echte Retro-Konsolen-Treffer nicht zerstören" und "Vermeide
Lösungen wie: remove ... wenn dadurch echte Treffer verloren gehen
könnten" -- für alle 3 Fälle hätte die naheliegende YAML-Änderung genau
dieses Risiko realisiert (Switch/Xbox: hätte echte TRUE_POSITIVE
zerstört, ohne den historisch gelabelten Fall überhaupt zu lösen;
DS-Lite: hätte mit hoher Wahrscheinlichkeit mehrheitlich echte Treffer
zerstört). Keine automatische Umsetzung ohne Rückfrage vorgenommen.

------------------------------------------------------------
konsolen_bundles/Switch -- Details
------------------------------------------------------------
Listing:            Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle
                     Neon Blau/Rot mit Dock (135€)
                     https://www.ebay.de/itm/137602406753
Aktuelle Kategorie:  konsolen_bundles (bestätigt korrekt)
Aktuelle Regel:      Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
                     (bestätigt korrekt)
Matchpfad:           require_all_of Gruppe 1: ["nintendo switch",
                     "switch oled","switch konsole"] -> hit
                     "nintendo switch"
                     require_all_of Gruppe 2: ["konsole",
                     "spielkonsole","spielekonsole","heimkonsole",
                     "bundle","set","mit spiele","ovp","system"] ->
                     hit "bundle"
Signale:             Titel enthält "32GB" (echter Speichergrößen-
                     Marker der Basis-Switch) und "Dock"
Einschätzung:        vom Nutzer bestätigt: korrekter Treffer.
Status:              KEIN FIX -- Ground-Truth-Label im Snapshot
                     vermutlich fehlerhaft, Matcher-Verhalten korrekt.

------------------------------------------------------------
konsolen_bundles/Xbox -- Details
------------------------------------------------------------
Listing:            Xbox One S 1TB mit Spiele (80€)
                     https://www.kleinanzeigen.de/s-anzeige/xbox-one-s-1tb-mit-spiele/3479889108-279-4400
Aktuelle Kategorie:  konsolen_bundles (bestätigt korrekt)
Aktuelle Regel:      Xbox One S / One X 👍 Guter Preis (bestätigt
                     korrekt)
Matchpfad:           require_all_of Gruppe 1: ["xbox one s",
                     "xbox one x"] -> hit "xbox one s"
                     require_all_of Gruppe 2: ["konsole","bundle",
                     "set","mit spiele","ovp","system"] -> hit
                     "mit spiele"
Signale:             Titel enthält "1TB" (echter Speichergrößen-
                     Marker der Xbox One S 1TB-Variante)
Einschätzung:        vom Nutzer bestätigt: korrekter Treffer.
Status:              KEIN FIX -- Ground-Truth-Label im Snapshot
                     vermutlich fehlerhaft, Matcher-Verhalten korrekt.

------------------------------------------------------------
retro_konsolen/DS-Lite -- Details
------------------------------------------------------------
Listing:            Nintendo DS Lite Handheld-System Weiß Touchscreen
                     inkl. 4 Spiele (80€)
                     https://www.ebay.de/itm/398266334210
Aktuelle Kategorie:  retro_konsolen (verifiziert: Nintendo DS/DS Lite
                     ist in diesem Regelwerk Teil von
                     retro_konsolen.yaml, nicht handhelds.yaml --
                     grep -i "nintendo ds" app/rules/handhelds.yaml
                     findet nur einen Kommentar, keine Regel;
                     app/rules/retro_konsolen.yaml enthält "Nintendo
                     DS" explizit als match-Begriff der Regelfamilie
                     "Nintendo Retro-Konsole (N64/GameCube/DS)")
Aktuelle Regel:      Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay
Matchpfad:           require_all_of Gruppe 1: ["nintendo 64","n64",
                     "gamecube","nintendo ds"] -> hit "nintendo ds"
                     require_all_of Gruppe 2: ["konsole","heimkonsole",
                     "spielekonsole","gerät","system","netzteil",
                     "kabel","slim","fat","komplett","memory card"]
                     -> hit AUSSCHLIESSLICH "system"
Signale:             kein Zubehör-/Ersatzteil-/Spiel-Indikator im
                     Titel (Forensik-Evidenz: leer)
Einschätzung:        noch nicht mit gleicher Sicherheit wie Switch/
                     Xbox bestätigt (3 weitere lexikalisch identische
                     Titel im Korpus, 1 davon selbst UNCLEAR gelabelt).
                     Fix würde vermutlich mehrheitlich echte Treffer
                     zerstören -- Risikoabwägung nach Rückfrage: nicht
                     fixen.
Mögliche
Lösungsstrategien:  a) "system" gaten wie "netzteil"/"kabel" -- würde
                        alle 4 "Handheld-System"-Titel gleichermaßen
                        blockieren.
                     b) Manuelle Einzelfall-Prüfung mit mehr Kontext
                        (Bildmaterial/Beschreibung) -- außerhalb der
                        Möglichkeiten dieses Tools.
Status:              KEIN FIX -- Nutzerentscheidung nach Rückfrage,
                     bleibt offene Restlücke.
