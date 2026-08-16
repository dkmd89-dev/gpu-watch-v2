# UNCLEAR FP Root-Cause Analysis

Root-Cause-Clustering, TP-Gegenpruefung und Fix-Hypothesen fuer die 23 LIKELY_FALSE_POSITIVE-Kandidaten aus den 35 historischen UNCLEAR-Faellen (`docs/DASHBOARD_MATCH_FORENSICS.json`, unveraendert). **Reine Forensik/Fix-Design -- KEINE YAML-Aenderung, KEINE Ground-Truth-Aenderung.**

- generated_at: 2026-08-16T00:24:16.177152+00:00
- ruleset_signature: f8e07b8b8d97d61a
- source_ground_truth: docs/DASHBOARD_MATCH_FORENSICS.json (unveraendert)

## WICHTIGER BEFUND: fehlerhafte committete unclear_routing_assessment.{json,md}

Die im Repo committeten Dateien tools/ruleset_quality/generated/reports/unclear_routing_assessment.{json,md} enthalten faelschlich nur 1 Fall (Testartefakt aus einem pytest-tmp-Fixture-Lauf, source_ground_truth zeigt auf /tmp/pytest-of-robin/.../forensics.json). Die 35-Faelle-Klassifikation selbst ist vollstaendig und korrekt in der kuratierten _UNCLEAR_ASSESSMENTS-Tabelle in tools/ruleset_quality/unclear_routing_assessment.py erhalten. Dieser Report wurde durch In-Memory-Aufruf von build_report() (ohne write_outputs()) neu erzeugt, um mit den korrekten 35 Faellen zu arbeiten. KEINE der beiden committeten Dateien wurde veraendert -- das Beheben dieses Test-Artefakt-Bugs ist NICHT Teil dieses Auftrags und wird hier nur dokumentiert, nicht behoben.

## SUMMARY

- total_unclear: 35
- likely_false_positive (Kandidaten, nicht bestaetigt): 23
- likely_true_positive: 11
- manual_review: 1
- ground_truth_conflict: 0
- FP-Kandidaten aktuell noch LIVE unter Produktivregeln: 3
- FP-Kandidaten bereits durch vorherige Fixes aufgeloest: 20
- TP-Faelle aktuell durch Produktivregeln blockiert (Recall-Risiko, Seitenbefund): 2

## SEITENBEFUND: Recall-Risiko bei 2 TRUE_POSITIVE-Faellen (ausserhalb des Auftragsscopes)

AUSSERHALB des FP-Scopes dieses Auftrags, aber waehrend der Gegenpruefung entdeckt: 2 der 11 LIKELY_TRUE_POSITIVE-Faelle (echte Konsolenangebote) matchen unter den AKTUELLEN Regeln nicht mehr (routing_status=C_NO_LONGER_MATCHES) -- ein moeglicher Recall-Verlust, keine Handlung in diesem Auftrag.

- **Nintendo Switch 1. Generation – Neon Blau/Rot – OVP  + Kaufbeleg**
  - exclude_category_unless_also_contains['ovp']-Verstaerkungsliste enthaelt 'v1'/'v2', aber NICHT die Textform '1. generation'/'2. generation', obwohl dieselbe Liste beim Key 'joy-con' bereits '1. generation'/'2. generation' enthaelt -- Inkonsistenz zwischen den Verstaerkungslisten verschiedener Keys.
- **Xbox One S 1 TB + 1 Controller - Weiß - OVP - Top Zustand**
  - exclude_category_unless_also_contains['ovp']-Verstaerkungsliste enthaelt '1tb' (ohne Leerzeichen), Titel schreibt '1 TB' (mit Leerzeichen) -- Tokenisierungs-Luecke.
- Empfehlung: Separates Ticket/Freigabe erforderlich, nicht Teil dieses Root-Cause-Audits.

## CLUSTERS

ID   | Name                                               | Count | Safety
---- | -------------------------------------------------- | ----- | ------
C1   | PRO_CONTROLLER_GAMECUBE_CONTROLLER_PHRASE          | 9     | SAFE_FIX
C2   | SINGLE_GAME_TITLE_WITHOUT_CONSOLE_MARKER           | 7     | SAFE_FIX
C3   | JOYCON_CONTROLLER_ACCESSORY_WITHOUT_CONSOLE_MARKER | 2     | SAFE_FIX
C4   | ZUBEHOER_SET_BUNDLE_BARE_EXCLUDE                   | 1     | SAFE_FIX
C5   | THIRD_PARTY_ACCESSORY_BRAND_NAME_MARKER_COLLISION  | 1     | PROBABLY_SAFE
C6   | GAME_BUNDLE_MARKER_SELF_COLLISION                  | 2     | HIGH_RISK
C7   | JOYCON_SET_OLED_MARKER_COLLISION                   | 1     | PROBABLY_SAFE

### C1 -- PRO_CONTROLLER_GAMECUBE_CONTROLLER_PHRASE

- count: 9
- categories: konsolen_bundles
- rules: Nintendo Switch (V1/V2/OLED) ★ Top-Deal, Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- safety: **SAFE_FIX** -- Bereits implementiert, dokumentiert 0-Kollisionen-verifiziert, aktuell reproduzierbar KEIN_TREFFER fuer alle 9 Faelle.

**Representative cases:**
- 2x Nintendo Switch 2 Pro Controller NEU OVP
- Nintendo Pokémon Purpur Nintendo Switch neu/sealed in OVP
- Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP

**Common signals:** nintendo switch, ovp, "pro controller"/"gamecube controller" als eigenstaendiger Zwei-Wort-Ausdruck

**Common missing signals:** konsole/spielkonsole/system/Modellnummer/Speichergroesse

**Root cause:**

Group-1 ("nintendo switch") + Group-2 ("ovp") des require_all_of matchen, obwohl der Titel ausschliesslich ein Controller-Zubehoerteil ("Pro Controller"/"GameCube Controller") beschreibt. Die Plattform-Erwaehnung dient hier als Kompatibilitaetsangabe, nicht als Beweis fuer ein Konsolengehaeuse.

**Evidence:**

require_all_of_detail aus docs/DASHBOARD_MATCH_FORENSICS.json bestaetigt hits=['nintendo switch'] + ['ovp'] fuer alle 9 Faelle; Titel enthaelt in keinem Fall ein Konsolen-/Speichergroessen-Marker.

**Proposed fix:**

- status: BEREITS IMPLEMENTIERT (nicht Teil dieses Auftrags)
- mechanism: `app/rules/konsolen_bundles.yaml :: exclude_category_unless_preceded_by`
- detail: "pro controller"/"pro-controller"/"gamecube controller" werden blockiert, AUSSER ein Bundle-Konnektor ("inkl"/"mit"/"+"/"und"/"sowie") steht unmittelbar davor -- laut YAML-Kommentar bereits gegen 195 TRUE_POSITIVE-Titel mit 0 Kollisionen verifiziert.

**Blast radius:**

- current_matches: 0
- hypothetical_exclusions: 9
- affected_cases: 9
- note: Alle 9 Faelle sind bereits jetzt KEIN_TREFFER unter den aktuellen Produktivregeln (routing_status=C_NO_LONGER_MATCHES).

---

### C2 -- SINGLE_GAME_TITLE_WITHOUT_CONSOLE_MARKER

- count: 7
- categories: konsolen_bundles
- rules: Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- safety: **SAFE_FIX** -- Bereits implementiert und robust (nicht interpunktionsabhaengig, siehe Diagnose-Skript-Output).

**Representative cases:**
- Metroid Prime Remastered Nintendo Switch 2023 Gebraucht In OVP  guter Zustand 
- Nintendo Pokémon Purpur Nintendo Switch neu/sealed in OVP
- Nintendo Switch - Minecraft FRA mit OVP

**Common signals:** nintendo switch (Plattformangabe), ovp

**Common missing signals:** konsole/spielkonsole/system, bundle/set (als Konnektor fuer den ovp-Kontext-Check)

**Root cause:**

Ein einzelner Spieltitel als Eigenname ("Minecraft", "Pokémon Purpur", "Star Fox" etc.) + Plattformangabe + "OVP" erfuellt beide require_all_of-Gruppen, obwohl kein Konsolen-Kernprodukt verkauft wird.

**Evidence:**

Fuer alle 7 Faelle greift der bereits vorhandene exclude_category_unless_also_contains-Guard auf den Key "ovp": "ovp" ist zwar vorhanden, aber KEIN Verstaerkungssignal (konsole/spielkonsole/bundle/set/Speichergroesse/Modellname) steht im selben Titel -- der Guard blockiert daher bereits jetzt zuverlaessig.

**Proposed fix:**

- status: BEREITS IMPLEMENTIERT (nicht Teil dieses Auftrags)
- mechanism: `app/rules/konsolen_bundles.yaml :: exclude_category_unless_also_contains['ovp']`
- detail: Blockiert "ovp" als Sekundaersignal, wenn kein Konsolen-/Speichergroessen-/Bundle-Marker im selben Titel vorkommt.

**Blast radius:**

- current_matches: 0
- hypothetical_exclusions: 7
- affected_cases: 7
- note: Alle Faelle bereits KEIN_TREFFER, Guard-Mechanismus feuert unabhaengig von Interpunktion (kein Bindestrich-Zufall wie bei C6).

---

### C3 -- JOYCON_CONTROLLER_ACCESSORY_WITHOUT_CONSOLE_MARKER

- count: 2
- categories: konsolen_bundles
- rules: Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- safety: **SAFE_FIX** -- Bereits implementiert, TP-Schutz explizit dokumentiert und verifiziert (9 Kollisionsfaelle bekannt und geschuetzt).

**Representative cases:**
- Nintendo Switch - Controller Joy-Con Neon-Grün / Neon-Pink 2er - NEU OVP
- Nintendo Switch Controller - Joy-Con 2er-Set Neon-Rot/Neon-Blau -NEU

**Common signals:** nintendo switch, joy-con, ovp/set

**Common missing signals:** konsole/spielkonsole/oled/Speichergroesse/Modellnummer

**Root cause:**

Standalone-Joy-Con-Controller-Paare/-Sets ohne Konsolengehaeuse; Plattformname dient nur als Kompatibilitaetsangabe.

**Evidence:**

exclude_category_unless_also_contains['joy-con'] blockiert bereits: "joy-con" ist vorhanden, aber kein Verstaerkungssignal (konsole/oled/Speichergroesse/hac-001/Generation) im selben Titel.

**TP counterexamples / protection:**

- Bewusst KEIN bare "joy-con"-Exclude (siehe YAML-Kommentar: 9 Kollisionen mit echten Switch-Bundles wie "Nintendo Switch Konsole mit grauen Joy-Cons" real verifiziert) -- der Kontext-Guard ist deshalb die einzig sichere Loesung, ein bare Exclude waere HIGH_RISK gewesen.

**Proposed fix:**

- status: BEREITS IMPLEMENTIERT (nicht Teil dieses Auftrags)
- mechanism: `app/rules/konsolen_bundles.yaml :: exclude_category_unless_also_contains['joy-con'/'joycon'/'joy con']`
- detail: Kontextbewusster Guard statt bare Exclude -- schuetzt die dokumentierten 9 echten Bundle-Kollisionsfaelle.

**Blast radius:**

- current_matches: 0
- hypothetical_exclusions: 2
- affected_cases: 2
- note: Beide Faelle robust blockiert (kein Verstaerkungssignal vorhanden), unabhaengig von Bindestrich-Zufall.

---

### C4 -- ZUBEHOER_SET_BUNDLE_BARE_EXCLUDE

- count: 1
- categories: konsolen_bundles
- rules: Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- safety: **SAFE_FIX** -- Bereits implementiert und verifiziert.

**Representative cases:**
- Nintendo Switch Sports inkl. 12-in-1 Zubehör Set

**Common signals:** nintendo switch, set, zubehör set

**Common missing signals:** konsole/spielkonsole

**Root cause:**

Spieltitel ("Nintendo Switch Sports") + Zubehoer-Set (12-in-1), kein Konsolengehaeuse.

**Evidence:**

bare _category_exclude_terms Treffer: "zubehör set" (mit Leerzeichen, siehe YAML-Kommentar 2026-08-15).

**Proposed fix:**

- status: BEREITS IMPLEMENTIERT (nicht Teil dieses Auftrags)
- mechanism: `app/rules/konsolen_bundles.yaml :: exclude_category`
- detail: "zubehör set"/"zubehör-set"/"zubehörset" als bare Exclude, 2 reale Treffer verifiziert, 0 Kollisionen.

**Blast radius:**

- current_matches: 0
- hypothetical_exclusions: 1
- affected_cases: 1
- note: Bereits KEIN_TREFFER.

---

### C5 -- THIRD_PARTY_ACCESSORY_BRAND_NAME_MARKER_COLLISION

- count: 1
- categories: konsolen_bundles
- rules: Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- safety: **PROBABLY_SAFE** -- Fix selbst ist eng/spezifisch und 0-Kollisionen-verifiziert -- aber nicht SAFE_FIX, weil eine vollstaendige Verifikation gegen den kompletten 2252-TRUE_POSITIVE-Korpus (ausserhalb der 35+11-Stichprobe dieses Audits) noch aussteht, analog zur bestehenden Praxis bei C1/C3/C4.

**Representative cases:**
- HORI Split Pad Pro Nintendo Switch Controller Schwarz mit OVP

**Common signals:** nintendo switch, ovp, "pro" (Teil des Produktnamens "Split Pad Pro")

**Common missing signals:** konsole/spielkonsole/Speichergroesse

**Root cause:**

Der exclude_category_unless_also_contains-Guard fuer den Key "ovp" akzeptiert "pro" als Verstaerkungssignal (gedacht fuer "PS4 Pro"/"Xbox ... Pro"-Konsolenvarianten). "HORI Split Pad Pro" ist jedoch ein Dritthersteller-Controller-Produktname, dessen "Pro" nichts mit einer Konsolenvariante zu tun hat -- der generische Marker "pro" wird durch den Produktnamen zufaellig mitgetroffen und hebt den Guard auf, obwohl kein Konsolengehaeuse verkauft wird. Zusaetzlich: "Pro" + "Controller" stehen hier NICHT als direkte Zwei-Wort-Phrase ("Split Pad Pro Nintendo Switch Controller") -- der bereits vorhandene "pro controller"-Phrasen-Exclude (siehe C1) greift daher NICHT, weil die Woerter "Pro" und "Controller" im Titel durch "Nintendo Switch" getrennt sind.

**Evidence:**

Diagnose-Skript bestaetigt: current_routing_status=A_SAME_WRONG_CATEGORY, block_mechanism=current_match (kein Guard feuert). Live-Korpus-Scan (found.json + price_history.jsonl, 19014 Titel): 0 Treffer fuer "split pad pro" -- der Fall ist historisch, aktuell nicht im Produktivkorpus vorhanden.

**TP counterexamples / protection:**

- Keiner der 11 LIKELY_TRUE_POSITIVE-Faelle nutzt "pro" als sein einziges Verstaerkungssignal (alle nutzen Speichergroesse/"spielkonsole"/"hac-001"/"komplett" zusaetzlich oder stattdessen). Das bare Wort "pro" selbst NICHT anfassen -- "PS4 Pro"/"Xbox ... Pro" sind reale Konsolenvarianten ausserhalb der 35+11-Stichprobe, deren Risiko mit dieser Stichprobe NICHT abschliessend verifizierbar ist (siehe HIGH_RISK-Warnung unten).

**Proposed fix:**

- status: NICHT IMPLEMENTIERT -- Fix-Hypothese
- mechanism: `app/rules/konsolen_bundles.yaml :: exclude_category_unless_preceded_by (neuer Eintrag, gleicher *bundle_konnektoren-Anker wie 'pro controller'/'gamecube controller')`
- detail: Neuen Eintrag "split pad pro" (und/oder "hori split pad") in exclude_category_unless_preceded_by mit demselben Konnektor-Anker (*bundle_konnektoren) hinzufuegen -- IDENTISCHER, bereits produktiv verifizierter Mechanismus wie bei "pro controller"/"gamecube controller" (C1). WICHTIG: das gemeinsam genutzte Wort "pro" in den bestehenden exclude_category_unless_also_contains-Listen (Keys "ovp"/"spiele") bleibt UNVERAENDERT -- eine Entfernung von "pro" dort waere ein globaler Eingriff mit unbekanntem Risiko fuer "PS4 Pro"/"Xbox ... Pro"-Konsolen ausserhalb der Stichprobe.

**Blast radius:**

- current_matches: 1
- hypothetical_exclusions: 1
- affected_cases: 1
- corpus_collision_check: {'phrase': 'split pad pro', 'titles_scanned': 19014, 'collisions': 0}
- note: 0 Kollisionen im vollstaendigen aktuellen Korpus (found.json+price_history.jsonl) fuer die vorgeschlagene Phrase.

---

### C6 -- GAME_BUNDLE_MARKER_SELF_COLLISION

- count: 2
- categories: konsolen_bundles
- rules: PS4 Slim / Pro Bundle ★ Top-Deal, PS4 Slim / Pro Bundle 👍 Guter Preis
- safety: **HIGH_RISK** -- FP und TP nutzen exakt dasselbe starke Signal ('bundle') ohne verlaessliche Kontexttrennung; die aktuell scheinbar geloeste Instanz (Bayonetta) ist nachweislich nur durch Interpunktions-Zufall geloest, nicht durch inhaltliche Logik -- Auftragsregel 'HIGH_RISK wenn FP und TP dieselben starken Signale verwenden und keine eindeutige Kontexttrennung existiert' greift hier direkt.

**Representative cases:**
- Read Dead Redemption 1+2 PlayStation 4 PS4 Steelbook Bundle NEU OVP
- Bayonetta & Vanquish 10th Anniversary Bundle - PlayStation 4 - Neu & OVP

**Common signals:** ps4/playstation 4, bundle, ovp

**Common missing signals:** konsole/system/Speichergroesse/slim/pro (als tatsaechliches Geraetesignal)

**Root cause:**

"bundle" ist gleichzeitig (a) das require_all_of-Gruppe-2-Signal, das den Treffer ueberhaupt ausloest, UND (b) in der Verstaerkungsliste des exclude_category_unless_also_contains-Guards fuer den Key "ovp" enthalten. Ein Titel, der "Bundle" nur im Sinne von "zwei Spiele im Doppelpack" verwendet ("Read Dead Redemption 1+2 ... Steelbook Bundle"), entwertet den eigenen OVP-Schutzmechanismus mit demselben Wort, das ihn ausgeloest hat -- der Guard kann nicht zwischen "Konsolen-Bundle" und "Spiele-Doppelpack-Bundle" unterscheiden. WICHTIGER NEBENBEFUND: der historisch als 'geloest' erscheinende Schwesterfall ("Bayonetta & Vanquish ... Bundle - PlayStation 4 - Neu & OVP") ist aktuell NUR deshalb KEIN_TREFFER, weil sein Titel zufaellig die Zeichenfolge "playstation 4 -" (mit direkt anschliessendem Bindestrich) enthaelt, wofuer ein SEPARATER Guard (Key "playstation 4 -") mit einer ANDEREN, engeren Verstaerkungsliste (nur Speichergroessen/Modellnamen, OHNE "bundle") existiert. Der Live-Fall "Read Dead Redemption 1+2 ..." enthaelt diesen Bindestrich nicht ("PlayStation 4 PS4 Steelbook Bundle" statt "PlayStation 4 - ...") und entkommt daher demselben Root Cause nur durch Interpunktion, nicht durch inhaltliche Unterscheidung -- der Schwesterfall ist somit KEIN robuster Fix, sondern Zufallstreffer.

**Evidence:**

Diagnose-Skript: RDR2-Fall block_mechanism=current_match (kein Guard feuert); Bayonetta-Fall block_mechanism=exclude_unless_also_contains, fired_context_keys enthaelt 'playstation 4 -', NICHT 'ovp' (der ovp-Key selbst wird durch 'bundle' im selben Titel neutralisiert -- identisch zum RDR2-Fall).

**TP counterexamples / protection:**

- 3 der 11 LIKELY_TRUE_POSITIVE-Faelle nutzen 'bundle' selbst als Signal ("Nintendo Switch Grau Bundle Neue Sticks...", "Nintendo Switch HAC-001 Joy-Controller Bundle 32GB Handheld-Spielekonsole", "Nintendo Switch Neon Bundle Neue Sticks...") -- "bundle" darf daher NICHT generell aus der Verstaerkungsliste entfernt werden, sonst wuerden diese 3 echten Konsolenangebote neu blockiert.

**Proposed fix:**

- status: NICHT IMPLEMENTIERT -- keine sichere Fix-Hypothese identifiziert
- detail: Kein Keyword-Fix identifizierbar, der (a) 'Read Dead Redemption 1+2 ... Bundle' zuverlaessig blockiert und (b) 'Nintendo Switch Grau Bundle Neue Sticks' weiterhin durchlaesst, OHNE eine neue, vom Titel unabhaengige Heuristik einzufuehren (z.B. 'enthaelt Bundle-Wort, aber KEIN Geraete-eigenes Signal wie Speichergroesse/Konsole/Modell' -- das waere strukturell dasselbe Problem, das den urspruenglichen 35er-UNCLEAR-Batch erzeugt hat, nur eine Ebene tiefer). Eine schmale Phrase wie 'steelbook bundle' wuerde nur den einen Live-Fall abdecken (0 weitere Korpustreffer), loest aber nicht das strukturelle Self-Collision-Problem und waere reines Symptom-Patching.

**Blast radius:**

- current_matches: 1
- hypothetical_exclusions: None
- affected_cases: 2
- corpus_collision_check: {'phrase_steelbook': {'titles_scanned': 19014, 'collisions': 0}, 'phrase_bundle_broad': {'titles_scanned': 19014, 'collisions': 19}}
- note: 'steelbook' hat 0 Korpustreffer (schmaler Fix moeglich, aber niedriger Wert). 'bundle' als bare Wort hat sehr viele Korpustreffer -- KEIN globaler Eingriff an diesem Signal ohne Vollkorpus-Review.

---

### C7 -- JOYCON_SET_OLED_MARKER_COLLISION

- count: 1
- categories: konsolen_bundles
- rules: Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- safety: **PROBABLY_SAFE** -- Fix ist eng/spezifisch und 0-Kollisionen-verifiziert; PROBABLY_SAFE statt SAFE_FIX, da bare 'joy-con' laut bestehender Dokumentation bereits 9 reale Kollisionsfaelle hatte -- die neue, engere Phrase 'joy-con set' muss vor Implementierung gegen denselben TRUE_POSITIVE-Korpus wie damals gegengeprueft werden, nicht nur gegen die 11 Faelle dieser Stichprobe.

**Representative cases:**
- Nintendo Switch OLED Joy-Con Set - Pokemon Scarlet & Violet mit Handschlaufaufen

**Common signals:** nintendo switch, switch oled, joy-con, set, spieltitel (Pokemon Scarlet & Violet)

**Common missing signals:** konsole/spielkonsole/Speichergroesse

**Root cause:**

Der exclude_category_unless_also_contains-Guard fuer den Key "joy-con" akzeptiert "oled" als Verstaerkungssignal (gedacht fuer echte Switch-OLED-Konsolen mit Joy-Cons). Hier bezeichnet "OLED" jedoch nur, fuer welches Switch-Modell das separate Joy-Con-SET kompatibel ist -- kein OLED-Konsolengehaeuse wird verkauft. Strukturell identisch zu C5 (C5: "pro" faelschlich als Geraetebeweis, C7: "oled" faelschlich als Geraetebeweis).

**Evidence:**

Diagnose-Skript: current_routing_status=A_SAME_WRONG_CATEGORY, block_mechanism=current_match. Titel enthaelt 'oled' (aus 'Switch OLED Joy-Con Set'), das die joy-con-Verstaerkungsliste erfuellt, obwohl es sich auf die Joy-Con-Variante bezieht, nicht auf ein Konsolengehaeuse.

**TP counterexamples / protection:**

- TP "Nintendo Switch OLED Modell - Weiß - Komplett mit OVP" nutzt 'oled' ZUSAMMEN mit 'Modell'/'Komplett' -- kein Joy-Con-Bezug. Wuerde von einer gezielten Aenderung an der 'joy-con'-Liste (statt einer globalen 'oled'-Aenderung) nicht beruehrt, da diese TP den 'ovp'-Key trifft, nicht den 'joy-con'-Key.

**Proposed fix:**

- status: NICHT IMPLEMENTIERT -- Fix-Hypothese
- mechanism: `app/rules/konsolen_bundles.yaml :: exclude_category (neue bare Phrase, analog 'zubehör set')`
- detail: Neue bare exclude_category-Phrase "joy-con set" (und Varianten "joy-con-set"/"joycon set") -- 0 Korpustreffer, analog zur bestehenden 'zubehör set'-Loesung (C4). Alternative (enger, aber aufwendiger): 'oled' NUR aus der 'joy-con'/'joycon'/'joy con'-Verstaerkungsliste entfernen (NICHT aus der 'ovp'-Liste), da die TP-Gegenprobe zeigt, dass echte OLED-Konsolen ueber den 'ovp'-Key erkannt werden, nicht ueber den 'joy-con'-Key.

**Blast radius:**

- current_matches: 1
- hypothetical_exclusions: 1
- affected_cases: 1
- corpus_collision_check: {'phrase': 'joy-con set', 'titles_scanned': 19014, 'collisions': 0}
- note: 0 Kollisionen im vollstaendigen aktuellen Korpus fuer 'joy-con set'.

---

## MANUAL_REVIEW (1 Fall, unveraendert)

- Nintendo DS Lite Handheld-System hellblau Touchscreen
- Unveraendert MANUAL_REVIEW -- siehe root_cause_pattern=lexically_ambiguous_vs_confirmed_false_positive in unclear_routing_assessment.py. Kein Cluster, keine Fix-Hypothese in diesem Auftrag.

## SIGNAL-MATRIX

| case_id_short | status | console_model | console_keyword_explicit | controller_mentioned | joycon_mentioned | bundle_word | set_word | ovp_word | storage_size | block_mechanism |
|---|---|---|---|---|---|---|---|---|---|---|
| 3480514740-279-924 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 137596202274 | FALSE_POSITIVE | False | False | False | False | True | False | True | False | exclude_unless_also_contains |
| 298569642364 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | current_match |
| 278262114576 | FALSE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 398090521820 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 407131833744 | FALSE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 267751986716 | FALSE_POSITIVE | False | False | True | True | False | False | True | False | exclude_unless_also_contains |
| 800482418310 | FALSE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 407120679305 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 3480875199-227-2761 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 407132075434 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 267751985916 | FALSE_POSITIVE | False | False | True | True | False | True | False | False | exclude_unless_also_contains |
| 128017856305 | FALSE_POSITIVE | False | False | False | True | False | True | False | False | current_match |
| 336734053355 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 318646020850 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 3480100632-279-1186 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 286899614096 | FALSE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_preceded_by |
| 3480799134-227-2661 | FALSE_POSITIVE | False | False | False | False | False | True | False | False | bare_category_exclude |
| 3480723859-227-3213 | FALSE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 327297670888 | FALSE_POSITIVE | False | False | False | False | True | False | True | False | current_match |
| 298566727139 | FALSE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 227468705699 | FALSE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 800481313890 | FALSE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 366595666798 | TRUE_POSITIVE | True | False | True | False | False | False | True | True | current_match |
| 287514519935 | TRUE_POSITIVE | False | False | False | False | False | False | True | False | exclude_unless_also_contains |
| 3480736743-279-9668 | TRUE_POSITIVE | False | False | False | False | True | False | False | False | current_match |
| 188766880820 | TRUE_POSITIVE | True | True | True | False | True | False | False | True | current_match |
| 298572812276 | TRUE_POSITIVE | False | False | False | False | False | True | True | False | current_match |
| 3480680031-279-9668 | TRUE_POSITIVE | False | False | False | False | True | False | False | False | current_match |
| 3480437137-279-8400 | TRUE_POSITIVE | True | False | False | False | False | False | True | False | current_match |
| 188763698665 | TRUE_POSITIVE | False | True | False | False | False | True | False | False | current_match |
| 188763696701 | TRUE_POSITIVE | False | True | False | False | False | True | False | False | current_match |
| 298572811262 | TRUE_POSITIVE | True | False | False | False | False | False | True | False | current_match |
| 377405800415 | TRUE_POSITIVE | False | False | True | False | False | False | True | False | exclude_unless_also_contains |

(Vollstaendige Titel/URLs siehe JSON-Report, `signal_matrix`.)

## GLOBAL RECOMMENDATION

**READY_FOR_TARGETED_FIX**

Scope: Gilt AUSSCHLIESSLICH fuer C5 (HORI Split Pad Pro) und C7 (Switch OLED Joy-Con Set) -- beides schmale, 0-Kollisionen-verifizierte Phrasen-Excludes nach demselben bereits produktiven Muster wie C1/C3/C4 (exclude_category_unless_preceded_by bzw. bare exclude_category), OHNE die gemeinsam genutzten generischen Marker 'pro'/'oled'/'bundle' selbst anzufassen.

Explizit ausgeschlossen: C6 (Read Dead Redemption 1+2 PS4 Bundle) bleibt DO_NOT_FIX_YET / MANUAL_REVIEW_REQUIRED -- keine sichere, keyword-basierte Trennung zwischen 'Spiele-Doppelpack-Bundle' und 'Konsolen-Bundle' gefunden, die nicht mindestens 3 bestaetigte TRUE_POSITIVE-Faelle gefaehrdet. C1-C4 sind bereits implementiert -- keine weitere Aktion noetig, nur zur Vollstaendigkeit dokumentiert.

Voraussetzungen vor Implementierung:
- app/rule_analyzer.py erneut laufen lassen vor jeder YAML-Aenderung.
- C5/C7-Phrasen gegen den VOLLSTAENDIGEN TRUE_POSITIVE-Korpus (2252 Faelle in docs/DASHBOARD_MATCH_FORENSICS.json, nicht nur die 11 UNCLEAR-TP dieser Stichprobe) verifizieren, analog zur dokumentierten Praxis bei 'pro controller'/'gamecube controller'/'zubehör set'.
- pytest app/tests/test_konsolen_bundles.py -v nach Implementierung, danach pytest app/tests/ -k konsolen_bundles -v.
- Explizite Nutzer-Freigabe vor jeder YAML-Aenderung (CLAUDE.md Regel 3).
