# UNCLEAR Routing Assessment

Forensische Klassifikation der 35 historischen UNCLEAR-Faelle aus `docs/DASHBOARD_MATCH_FORENSICS.json` (wird nie veraendert). Betrifft AUSSCHLIESSLICH Faelle mit historischem Verdict UNCLEAR -- niemals TRUE_POSITIVE/FALSE_POSITIVE. Automatisch generiert von `tools/ruleset_quality/unclear_routing_assessment.py`.

- generated_at: 2026-08-16T08:42:49.062095+00:00
- ruleset_signature: 0a9c9f4bb3590872
- source_ground_truth: /mnt/128ssd/claude/docs/DASHBOARD_MATCH_FORENSICS.json

## SUMMARY

- total_unclear: 35
- likely_true_positive: 11
- likely_false_positive: 23
- ground_truth_conflict: 0
- manual_review: 1

## CONFIDENCE

- high: 29
- medium: 5
- low: 1

## CATEGORIES

category           | unclear | TP    | FP    | conflict | manual_review
konsolen_bundles   | 34      | 11    | 23    | 0        | 0
retro_konsolen     | 1       | 0     | 0     | 0        | 1

## CASES

### 2x Nintendo Switch 2 Pro Controller NEU OVP

- case_id: https://www.kleinanzeigen.de/s-anzeige/2x-nintendo-switch-2-pro-controller-neu-ovp/3480514740-279-924
- price: 130.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] 2x ... Pro Controller: Titel nennt ausschliesslich zwei Controller -- kein Konsolen-Kernprodukt.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: Weder Modellbezeichnung noch Speichergroesse noch das Wort 'Konsole'/'System' vorhanden.
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Bayonetta & Vanquish 10th Anniversary Bundle - PlayStation 4 - Neu & OVP

- case_id: https://www.ebay.de/itm/137596202274
- price: 19.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=PS4 Slim / Pro Bundle ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Bayonetta & Vanquish 10th Anniversary Bundle: Zwei genannte Spieltitel als Jubilaeums-Doppelpack -- kein Konsolen-Kernprodukt.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 'Bundle' bezieht sich hier auf die zwei Spiele, nicht auf ein Konsolenpaket.
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### HORI Split Pad Pro Nintendo Switch Controller Schwarz mit OVP

- case_id: https://www.ebay.de/itm/298569642364
- price: 26.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] HORI Split Pad Pro ... Controller: HORI Split Pad Pro ist ein bekanntes Dritthersteller-Controller-Zubehoer; Titel nennt explizit 'Controller', keine Konsole.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: Kein Hinweis auf ein verkauftes Konsolengehaeuse.
  - [context/strong] current_routing_status=A_SAME_WRONG_CATEGORY: Faellt unter den AKTUELLEN Produktivregeln weiterhin in dieselbe Kategorie -- live aktiver Fehltreffer-Kandidat, nicht nur historisch.

### Metroid Prime Remastered Nintendo Switch 2023 Gebraucht In OVP  guter Zustand 

- case_id: https://www.ebay.de/itm/278262114576
- price: 35.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Metroid Prime Remastered: Genannter Einzel-Spieltitel als Eigenname -- exakt das im Forensik-reason beschriebene 'Minecraft'-Beispielszenario.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Microsoft Xbox One X 1TB Schwarz Inkl OVP Ohne Controller

- case_id: https://www.ebay.de/itm/366595666798
- price: 85.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] 1TB: Speichergroessen-Marker -- typisch fuer ein Konsolenangebot, nicht fuer ein Spiel.
  - [positive_signal/strong] Microsoft Xbox One X: Hersteller+Modellname als Kernprodukt des Angebots.
  - [negative_signal/weak] Ohne Controller: Beschreibt nur fehlendes Zubehoer zur Konsole, nicht das verkaufte Hauptprodukt.

### NEU - OVP! Nintendo Switch Pro Controller - Monster Hunter Rise Sunbreak Edition

- case_id: https://www.ebay.de/itm/398090521820
- price: 75.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Nintendo Switch Pro Controller - Monster Hunter Rise Sunbreak Edition: Sonderedition eines Pro Controllers -- Zubehoer, keine Konsole genannt.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Pokémon Purpur Nintendo Switch neu/sealed in OVP

- case_id: https://www.ebay.de/itm/407131833744
- price: 40.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Pokémon Purpur: Genannter Einzel-Spieltitel als Eigenname.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch - Controller Joy-Con Neon-Grün / Neon-Pink 2er - NEU OVP

- case_id: https://www.ebay.de/itm/267751986716
- price: 59.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Controller Joy-Con Neon-Gruen / Neon-Pink 2er: Explizit zwei Joy-Con-Controller -- Zubehoer, keine Konsole.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch - Minecraft FRA mit OVP

- case_id: https://www.ebay.de/itm/800482418310
- price: 19.89
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Minecraft: Identisch zum im Forensik-reason genannten Beispiel -- Spieltitel als Eigenname.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch 1. Generation – Neon Blau/Rot – OVP  + Kaufbeleg

- case_id: https://www.ebay.de/itm/287514519935
- price: 125.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] 1. Generation: Modellgenerations-Angabe -- konsolenspezifisch.
  - [positive_signal/medium] Neon Blau/Rot: Farbangabe typisch fuer ein Konsolengehaeuse.
  - [positive_signal/medium] Kaufbeleg: Kaufbeleg-Erwaehnung passt zum Verkauf eines Geraets, nicht eines Spiels.

### Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP

- case_id: https://www.ebay.de/itm/407120679305
- price: 79.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Pro Controller NSWITCH 2: Zubehoer, keine Konsole genannt.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch 2 GameCube Controller | OVP | NEU

- case_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-2-gamecube-controller-ovp-neu/3480875199-227-2761
- price: 85.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] GameCube Controller: Retro-Stil-Controller-Zubehoer fuer Switch 2, keine Konsole im Titel.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch 2 GameCube Controller – Nintendo Classics – OVP – NEU

- case_id: https://www.ebay.de/itm/407132075434
- price: 85.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] GameCube Controller – Nintendo Classics: Identisches Muster zum Schwesterfall (siehe .../3480875199) -- Controller-Zubehoer.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch Controller - Joy-Con 2er-Set Neon-Rot/Neon-Blau -NEU

- case_id: https://www.ebay.de/itm/267751985916
- price: 59.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Controller - Joy-Con 2er-Set: Explizit Joy-Con-Controller-Set -- Zubehoer, keine Konsole.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch Grau Bundle  Neue Sticks (Kein Drift) + Extras!

- case_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-grau-bundle-neue-sticks-kein-drift-extras-/3480736743-279-9668
- price: 120.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=MEDIUM)
- root_cause_pattern: console_confirmed_by_hardware_repair_context
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] Neue Sticks (Kein Drift): Analogstick-Drift ist ein bekanntes physisches Konsolen-/Joy-Con-Hardwareproblem -- kann sich nicht auf ein reines Spiel beziehen, setzt echte Hardware voraus.
  - [positive_signal/medium] Bundle + Extras: Kein einzelner Spieltitel genannt.
  - [negative_signal/medium] kein explizites Wort 'Konsole'/'System' oder Speichergroesse: Deshalb MEDIUM statt HIGH -- Hardwarekontext ist stark, aber kein direkter Konsolen-Begriff vorhanden.

### Nintendo Switch HAC-001(-01) Joy-Controller Bundle 32GB Handheld-Spielekonsole -

- case_id: https://www.ebay.de/itm/188766880820
- price: 116.92
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] HAC-001(-01): Offizielle Nintendo-Switch-Modellnummer.
  - [positive_signal/strong] 32GB: Speichergroessen-Marker der Basis-Switch.
  - [positive_signal/strong] Handheld-Spielekonsole: Explizites Wort 'Spielekonsole' im Titel.

### Nintendo Switch Komplett Set OVP

- case_id: https://www.ebay.de/itm/298572812276
- price: 129.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=MEDIUM)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/medium] Komplett Set: Kein Spieltitel genannt -- 'Komplett Set' ohne Eigenname deutet auf ein vollstaendiges Konsolenpaket hin.
  - [negative_signal/medium] kein explizites Wort 'Konsole'/'System' oder Speichergroesse: Deshalb MEDIUM statt HIGH -- 'Set' bleibt fuer sich genommen generisch.

### Nintendo Switch Neon Bundle  Neue Sticks (Kein Drift!) + Extras

- case_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-neon-bundle-neue-sticks-kein-drift-extras/3480680031-279-9668
- price: 145.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=MEDIUM)
- root_cause_pattern: console_confirmed_by_hardware_repair_context
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] Neue Sticks (Kein Drift!): Identisches Hardware-Reparatur-Signal wie beim Schwesterfall (siehe .../3480736743) -- Analogstick-Drift ist konsolenspezifisch.
  - [positive_signal/medium] Bundle + Extras: Kein einzelner Spieltitel genannt.
  - [negative_signal/medium] kein explizites Wort 'Konsole'/'System' oder Speichergroesse: 

### Nintendo Switch OLED Joy-Con Set - Pokemon Scarlet & Violet mit Handschlaufaufen

- case_id: https://www.ebay.de/itm/128017856305
- price: 119.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=MEDIUM)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] OLED Joy-Con Set: Explizit ein Joy-Con-Set -- Zubehoer.
  - [positive_signal/medium] mit Handschlaufaufen: Handschlaufen sind Joy-Con-Zubehoer.
  - [negative_signal/medium] Pokemon Scarlet & Violet als genannter Spieltitel: Zusaetzliches Spiel im Bundle, kein Konsolenhinweis.
  - [context/strong] current_routing_status=A_SAME_WRONG_CATEGORY: Faellt unter den AKTUELLEN Produktivregeln weiterhin in dieselbe Kategorie -- live aktiver Fehltreffer-Kandidat. MEDIUM statt HIGH, da 'Set' theoretisch auch ein Konsolenpaket bezeichnen koennte.

### Nintendo Switch OLED Modell - Weiß - Komplett mit OVP

- case_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-oled-modell-weiss-komplett-mit-ovp/3480437137-279-8400
- price: 150.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] OLED Modell: Benennt explizit das Konsolenmodell.
  - [positive_signal/medium] Komplett: Verstaerkt den Eindruck eines vollstaendigen Geraets.

### Nintendo Switch Pro Controller - Schwarz mit OVP kaum genutzt

- case_id: https://www.ebay.de/itm/336734053355
- price: 39.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Pro Controller ... kaum genutzt: Zubehoer, keine Konsole.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch Pro Controller Original | OVP | TOP Zustand

- case_id: https://www.ebay.de/itm/318646020850
- price: 39.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Pro Controller Original: Zubehoer, keine Konsole.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch Pro Controller in OVP

- case_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-pro-controller-in-ovp/3480100632-279-1186
- price: 50.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Pro Controller in OVP: Zubehoer, keine Konsole.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch Pro Controller, TOP Zustand mit OVP

- case_id: https://www.ebay.de/itm/286899614096
- price: 45.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: accessory_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Pro Controller, TOP Zustand: Zubehoer, keine Konsole.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Nintendo Switch Spielkonsole mit Set - Guter Zustand

- case_id: https://www.ebay.de/itm/188763698665
- price: 116.49
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] Spielkonsole: Explizites Wort 'Spielkonsole' im Titel.

### Nintendo Switch Spielkonsole mit Set - Top Zustand

- case_id: https://www.ebay.de/itm/188763696701
- price: 127.49
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] Spielkonsole: Identisches Muster zum Schwesterfall (siehe .../188763698665).

### Nintendo Switch Sports inkl. 12-in-1 Zubehör Set

- case_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-sports-inkl-12-in-1-zubehoer-set/3480799134-227-2661
- price: 30.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Nintendo Switch Sports: Genannter Spieltitel.
  - [positive_signal/strong] 12-in-1 Zubehör Set: Explizit Zubehoer-Set, keine Konsole.

### Nintendo Switch V1 HAC-001 mit OVP + Komplett | BLITZVERSAND⚡️

- case_id: https://www.ebay.de/itm/298572811262
- price: 140.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] V1: Modellgenerations-Angabe.
  - [positive_signal/strong] HAC-001: Offizielle Nintendo-Switch-Modellnummer.
  - [positive_signal/medium] Komplett: 

### Pokémon Let’s Go Evoli! Nintendo Switch – OVP komplett

- case_id: https://www.kleinanzeigen.de/s-anzeige/pok-mon-let-s-go-evoli-nintendo-switch-ovp-komplett/3480723859-227-3213
- price: 39.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=MEDIUM)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Pokémon Let's Go Evoli!: Genannter Einzel-Spieltitel.
  - [negative_signal/weak] 'komplett' vermutlich CIB-Bezeichnung fuers Spiel, nicht Konsolenhinweis: Deshalb MEDIUM statt HIGH -- Restambiguitaet durch das Wort 'komplett'.

### Read Dead Redemption 1+2 PlayStation 4 PS4 Steelbook Bundle NEU OVP

- case_id: https://www.ebay.de/itm/327297670888
- price: 100.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=PS4 Slim / Pro Bundle 👍 Guter Preis
- current_routing: category=konsolen_bundles, rule=PS4 Slim / Pro Bundle 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Read Dead Redemption 1+2 ... Steelbook Bundle: Zwei genannte Spieltitel in Steelbook-Sonderverpackung -- kein Konsolen-Kernprodukt.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/strong] current_routing_status=A_SAME_WRONG_CATEGORY: Faellt unter den AKTUELLEN Produktivregeln weiterhin in dieselbe Kategorie -- live aktiver Fehltreffer-Kandidat.

### STAR FOX - Nintendo Switch 2 - NEU-OVP - Händler YAPIDO

- case_id: https://www.ebay.de/itm/298566727139
- price: 47.9
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] STAR FOX: Genannter Einzel-Spieltitel, Haendlerverkauf.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Star Fox "NEU & OVP" (Nintendo Switch 2)

- case_id: https://www.ebay.de/itm/227468705699
- price: 49.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Star Fox: Identisches Muster zum Schwesterfall (siehe .../298566727139).
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Super Smash Bros. Ultimate (Nintendo Switch) (Inklusive OVP)

- case_id: https://www.ebay.de/itm/800481313890
- price: 38.79
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_FALSE_POSITIVE (confidence=HIGH)
- root_cause_pattern: single_game_title_without_console_marker
- recommended_action: ruleset_review
- evidence:
  - [positive_signal/strong] Super Smash Bros. Ultimate: Genannter Einzel-Spieltitel.
  - [negative_signal/strong] kein Konsolen-/Speichergroessen-Marker im Titel: 
  - [context/weak] require_all_of-Kriterium nur ueber generisches Signal (ovp/set/bundle) erfuellt: Forensik-Snapshot-reason: automatisierte Erkennung stoesst hier an ihre Grenze (kein staerkeres Alternativsignal wie 'konsole'/'system' im selben Treffer) -- das ist der Grund, warum der Fall ueberhaupt als UNCLEAR markiert wurde.

### Xbox One S 1 TB + 1 Controller - Weiß - OVP - Top Zustand

- case_id: https://www.ebay.de/itm/377405800415
- price: 80.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis
- current_routing: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: LIKELY_TRUE_POSITIVE (confidence=HIGH)
- root_cause_pattern: console_confirmed_by_explicit_model_or_keyword
- recommended_action: regression_test
- evidence:
  - [positive_signal/strong] 1 TB: Speichergroessen-Marker.
  - [negative_signal/weak] + 1 Controller: Zubehoer-Ergaenzung zur Konsole, nicht das Hauptprodukt selbst.

### Nintendo DS Lite Handheld-System hellblau Touchscreen

- case_id: https://www.ebay.de/itm/318701631164
- price: 50.0
- historical_ground_truth: verdict=UNCLEAR, category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) 👍 Guter Preis
- current_routing: category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: MANUAL_REVIEW (confidence=LOW)
- root_cause_pattern: lexically_ambiguous_vs_confirmed_false_positive
- recommended_action: manual_review
- evidence:
  - [context/strong] Titelmuster 'Handheld-System': Lexikalisch (fast) identisch zum bereits bestaetigten FALSE_POSITIVE 'Nintendo DS Lite Handheld-System Weiss Touchscreen inkl. 4 Spiele' (forensics_false_positives._MANUAL_ASSESSMENT_OVERRIDES, url=.../398266334210).
  - [context/strong] bereits dokumentierte Vorpruefung (2026-08-15): Fuer genau diesen Fall wurde bereits festgestellt: 'kein lexikalisches Unterscheidungsmerkmal zwischen dem bestaetigten FP und den mutmasslich echten Treffern gefunden' (siehe active_fp_fix_progress.md). Diese Erkenntnis wird hier NICHT durch eine neue Heuristik ueberschrieben.

## CONSISTENCY

- total_cases: 35
- matched_cases: 35
- missing_cases: 0
- duplicate_cases: 0
- classification_sum: 35
- consistency_ok: True