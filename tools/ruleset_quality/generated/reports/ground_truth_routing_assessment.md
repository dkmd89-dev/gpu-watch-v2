# Ground-Truth vs. Current-Routing-Assessment

Zweiebenen-Report: trennt historische Ground Truth (aus `docs/DASHBOARD_MATCH_FORENSICS.json`, wird nie veraendert) strikt von der aktuellen Routing-Bewertung (aus `common.evaluate()`, dem echten Produktionspfad). Automatisch generiert von `tools/ruleset_quality/ground_truth_routing_assessment.py`.

- generated_at: 2026-08-15T20:45:50.757043+00:00
- ruleset_signature: f8e07b8b8d97d61a
- source_ground_truth: /mnt/128ssd/claude/docs/DASHBOARD_MATCH_FORENSICS.json

## SUMMARY

- historical_tp: 2252
- historical_fp: 19
- historical_unclear: 35
- current_fixed_fp: 16
- current_active_fp: 0
- category_changed_fp: 0
- manual_review (FP-Ursprung, exkl. UNCLEAR): 1
- ground_truth_conflict: 2

## CATEGORIES

category             | historical_fp | fixed | still_active | category_changed  | manual_review | ground_truth_conflict
gaming_pc            | 1             | 1     | 0            | 0                 | 0             | 0
handhelds            | 4             | 4     | 0            | 0                 | 0             | 0
iphone               | 1             | 1     | 0            | 0                 | 0             | 0
konsolen_bundles     | 6             | 4     | 0            | 0                 | 0             | 2
notebook_resell      | 1             | 1     | 0            | 0                 | 0             | 0
office_pc            | 2             | 2     | 0            | 0                 | 0             | 0
retro_konsolen       | 4             | 3     | 0            | 0                 | 1             | 0

## CASES

### MAINBOARD SET H310M D2P. i5-9500. GTX 1050TI. NWMe. 16GB DDR4.

- listing_id: https://www.kleinanzeigen.de/s-anzeige/mainboard-set-h310m-d2p-i5-9500-gtx-1050ti-nwme-16gb-ddr4-/3480520958-225-8182
- price: 90.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=gaming_pc, rule=Gaming-PC (Mindestanforderung erfüllt)
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### JSAUX Slim-Reisetasche Für Lenovo Legion Go/Go S/Go 2, Hartschalenbeutel | Schla

- listing_id: https://www.ebay.de/itm/307112118573
- price: 41.48
- historical_ground_truth: verdict=FALSE_POSITIVE, category=handhelds, rule=Asus ROG Ally / Lenovo Legion Go ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Steam Deck Skin Faceplate Schutz Klebefolie Design Vinyl Aufkleber Skins OLED

- listing_id: https://www.ebay.de/itm/304780620667
- price: 19.95
- historical_ground_truth: verdict=FALSE_POSITIVE, category=handhelds, rule=Valve Steam Deck ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### USB-C HUB für Steam Deck HDMI 4k 60Hz USB 3.0 PD

- listing_id: https://www.ebay.de/itm/255925725429
- price: 41.99
- historical_ground_truth: verdict=FALSE_POSITIVE, category=handhelds, rule=Valve Steam Deck ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### VITURE USB-C an Brille, Ladeadapter, Laden und Spielen für Switch, Steam Deck

- listing_id: https://www.ebay.de/itm/205573628921
- price: 49.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=handhelds, rule=Valve Steam Deck ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Apple iPhone 15 Pro Max 512GB Mainboard Platine mit FaceID und Kameramodul 

- listing_id: https://www.ebay.de/itm/236995682525
- price: 400.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=iphone, rule=iPhone 15 Pro Max (≥512GB) 👍 Guter Preis
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### 2x Nintendo Switch 2 Pro Controller NEU OVP

- listing_id: https://www.kleinanzeigen.de/s-anzeige/2x-nintendo-switch-2-pro-controller-neu-ovp/3480514740-279-924
- price: 130.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Bayonetta & Vanquish 10th Anniversary Bundle - PlayStation 4 - Neu & OVP

- listing_id: https://www.ebay.de/itm/137596202274
- price: 19.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=PS4 Slim / Pro Bundle ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### HORI Split Pad Pro Nintendo Switch Controller Schwarz mit OVP

- listing_id: https://www.ebay.de/itm/298569642364
- price: 26.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Luigi's Mansion 2 HD für Nintendo Switch - NEU & OVP

- listing_id: https://www.kleinanzeigen.de/s-anzeige/luigi-s-mansion-2-hd-fuer-nintendo-switch-neu-ovp/3480890852-227-23706
- price: 35.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Mario Kart World für Nintendo Switch 2 – NEU  und OVP

- listing_id: https://www.ebay.de/itm/257670779909
- price: 54.99
- historical_ground_truth: verdict=FALSE_POSITIVE, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Metroid Prime Remastered Nintendo Switch 2023 Gebraucht In OVP  guter Zustand 

- listing_id: https://www.ebay.de/itm/278262114576
- price: 35.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Microsoft Xbox One X 1TB Schwarz Inkl OVP Ohne Controller

- listing_id: https://www.ebay.de/itm/366595666798
- price: 85.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand

- listing_id: https://www.kleinanzeigen.de/s-anzeige/nba-2k26-fuer-nintendo-switch-2-ovp-schneller-versand/3479886837-227-7978
- price: 14.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### NEU - OVP! Nintendo Switch Pro Controller - Monster Hunter Rise Sunbreak Edition

- listing_id: https://www.ebay.de/itm/398090521820
- price: 75.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Pokémon Purpur Nintendo Switch neu/sealed in OVP

- listing_id: https://www.ebay.de/itm/407131833744
- price: 40.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch - Controller Joy-Con Neon-Grün / Neon-Pink 2er - NEU OVP

- listing_id: https://www.ebay.de/itm/267751986716
- price: 59.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch - Minecraft FRA mit OVP

- listing_id: https://www.ebay.de/itm/800482418310
- price: 19.89
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch 1. Generation – Neon Blau/Rot – OVP  + Kaufbeleg

- listing_id: https://www.ebay.de/itm/287514519935
- price: 125.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP

- listing_id: https://www.ebay.de/itm/407120679305
- price: 79.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch 2 GameCube Controller | OVP | NEU

- listing_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-2-gamecube-controller-ovp-neu/3480875199-227-2761
- price: 85.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch 2 GameCube Controller – Nintendo Classics – OVP – NEU

- listing_id: https://www.ebay.de/itm/407132075434
- price: 85.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle Neon Blau/Rot mit Dock

- listing_id: https://www.ebay.de/itm/137602406753
- price: 135.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=GROUND_TRUTH_CONFLICT, confidence=high
  - Titel enthaelt echten Speichergroessen-Marker '32GB' (Basis-Switch-Modell) sowie ein Spiel (Mario Kart 8 Deluxe) und Zubehoer (Dock) -- liest sich als vollstaendiger Konsolenverkauf, nicht als Zubehoer-/Spiele-Angebot.
  - Vom Nutzer am 2026-08-15 nach Vorlage der Matchpfad-Analyse explizit als korrekt gematchter TRUE_POSITIVE bestaetigt (siehe active_fp_fix_progress.md).
  - Keine YAML-Aenderung vorgenommen -- das FALSE_POSITIVE-Label im historischen Forensik-Snapshot (Commit 01afd5b, 2026-08-10) ist vermutlich selbst fehlerhaft.

### Nintendo Switch Controller - Joy-Con 2er-Set Neon-Rot/Neon-Blau -NEU

- listing_id: https://www.ebay.de/itm/267751985916
- price: 59.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch Grau Bundle  Neue Sticks (Kein Drift) + Extras!

- listing_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-grau-bundle-neue-sticks-kein-drift-extras-/3480736743-279-9668
- price: 120.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch HAC-001(-01) Joy-Controller Bundle 32GB Handheld-Spielekonsole -

- listing_id: https://www.ebay.de/itm/188766880820
- price: 116.92
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch Komplett Set OVP

- listing_id: https://www.ebay.de/itm/298572812276
- price: 129.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch Neon Bundle  Neue Sticks (Kein Drift!) + Extras

- listing_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-neon-bundle-neue-sticks-kein-drift-extras/3480680031-279-9668
- price: 145.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch OLED Joy-Con Set - Pokemon Scarlet & Violet mit Handschlaufaufen

- listing_id: https://www.ebay.de/itm/128017856305
- price: 119.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch OLED Modell - Weiß - Komplett mit OVP

- listing_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-oled-modell-weiss-komplett-mit-ovp/3480437137-279-8400
- price: 150.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch Pro Controller - Schwarz mit OVP kaum genutzt

- listing_id: https://www.ebay.de/itm/336734053355
- price: 39.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch Pro Controller Original | OVP | TOP Zustand

- listing_id: https://www.ebay.de/itm/318646020850
- price: 39.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch Pro Controller in OVP

- listing_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-pro-controller-in-ovp/3480100632-279-1186
- price: 50.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch Pro Controller, TOP Zustand mit OVP

- listing_id: https://www.ebay.de/itm/286899614096
- price: 45.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch Spielkonsole mit Set - Guter Zustand

- listing_id: https://www.ebay.de/itm/188763698665
- price: 116.49
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch Spielkonsole mit Set - Top Zustand

- listing_id: https://www.ebay.de/itm/188763696701
- price: 127.49
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Switch Sports inkl. 12-in-1 Zubehör Set

- listing_id: https://www.kleinanzeigen.de/s-anzeige/nintendo-switch-sports-inkl-12-in-1-zubehoer-set/3480799134-227-2661
- price: 30.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Nintendo Switch V1 HAC-001 mit OVP + Komplett | BLITZVERSAND⚡️

- listing_id: https://www.ebay.de/itm/298572811262
- price: 140.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Playstation 5 PS4 PS5 Slim HDMI Port Nintendo Reparatur USB PRO

- listing_id: https://www.kleinanzeigen.de/s-anzeige/playstation-5-ps4-ps5-slim-hdmi-port-nintendo-reparatur-usb-pro/3431533294-226-3438
- price: 50.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=konsolen_bundles, rule=PS4 Slim / Pro Bundle ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Pokémon Let’s Go Evoli! Nintendo Switch – OVP komplett

- listing_id: https://www.kleinanzeigen.de/s-anzeige/pok-mon-let-s-go-evoli-nintendo-switch-ovp-komplett/3480723859-227-3213
- price: 39.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Read Dead Redemption 1+2 PlayStation 4 PS4 Steelbook Bundle NEU OVP

- listing_id: https://www.ebay.de/itm/327297670888
- price: 100.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=PS4 Slim / Pro Bundle 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=PS4 Slim / Pro Bundle 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### STAR FOX - Nintendo Switch 2 - NEU-OVP - Händler YAPIDO

- listing_id: https://www.ebay.de/itm/298566727139
- price: 47.9
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Star Fox "NEU & OVP" (Nintendo Switch 2)

- listing_id: https://www.ebay.de/itm/227468705699
- price: 49.99
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Super Smash Bros. Ultimate (Nintendo Switch) (Inklusive OVP)

- listing_id: https://www.ebay.de/itm/800481313890
- price: 38.79
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Nintendo Switch (V1/V2/OLED) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Xbox One S 1 TB + 1 Controller - Weiß - OVP - Top Zustand

- listing_id: https://www.ebay.de/itm/377405800415
- price: 80.0
- historical_ground_truth: verdict=UNCLEAR, category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: KEIN_TREFFER

### Xbox One S 1TB mit Spiele

- listing_id: https://www.kleinanzeigen.de/s-anzeige/xbox-one-s-1tb-mit-spiele/3479889108-279-4400
- price: 80.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis
- current_routing_assessment: category=konsolen_bundles, rule=Xbox One S / One X 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=GROUND_TRUTH_CONFLICT, confidence=high
  - Titel enthaelt echten Speichergroessen-Marker '1TB' (Xbox One S 1TB-Variante), keine Zubehoer-/Ersatzteil-Indikatoren.
  - Vom Nutzer am 2026-08-15 nach Vorlage der Matchpfad-Analyse explizit als korrekt gematchter TRUE_POSITIVE bestaetigt (siehe active_fp_fix_progress.md).
  - Keine YAML-Aenderung vorgenommen -- das FALSE_POSITIVE-Label im historischen Forensik-Snapshot ist vermutlich selbst fehlerhaft.

### Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM NM-B891

- listing_id: https://www.ebay.de/itm/357718779954
- price: 49.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=notebook_resell, rule=ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Intel Core i5-8500 Mainboard Bundle 16GB DDR4 RAM Netzteil

- listing_id: https://www.kleinanzeigen.de/s-anzeige/intel-core-i5-8500-mainboard-bundle-16gb-ddr4-ram-netzteil/3480038290-225-13379
- price: 160.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=office_pc, rule=Office-PC (Mindestanforderung erfüllt)
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Lenovo ThinkPad T490s Mainboard nm-b891 Intel i5-8365U / i5-8265U 8GB RAM

- listing_id: https://www.ebay.de/itm/356717584177
- price: 69.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=office_pc, rule=Office-PC (Mindestanforderung erfüllt)
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### N64 USB-C Netzteil für Nintendo 64 Ersatznetzteil

- listing_id: https://www.ebay.de/itm/307106426592
- price: 30.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Nintendo DS Lite Handheld-System Weiß Touchscreen inkl. 4 Spiele

- listing_id: https://www.ebay.de/itm/398266334210
- price: 80.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay
- current_routing_assessment: category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=low
  - 3 weitere, lexikalisch identisch formulierte 'Handheld-System'-Titel im aktuellen Korpus/Preishistorie gefunden, davon 1 selbst als UNCLEAR (nicht FALSE_POSITIVE) gelabelt -- kein lexikalisches Unterscheidungsmerkmal zwischen dem bestaetigten FP und den mutmasslich echten Treffern gefunden.
  - Nutzerentscheidung 2026-08-15 nach Rueckfrage: nicht fixen, aber auch nicht als Ground-Truth-Konflikt einstufen -- Status bleibt unsicher (siehe active_fp_fix_progress.md).

### Nintendo DS Lite Handheld-System hellblau Touchscreen

- listing_id: https://www.ebay.de/itm/318701631164
- price: 50.0
- historical_ground_truth: verdict=UNCLEAR, category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) 👍 Guter Preis
- current_routing_assessment: category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) 👍 Guter Preis, match_state=GLEICHE_KATEGORIE, routing_status=A_SAME_WRONG_CATEGORY
- assessment: status=MANUAL_REVIEW, confidence=manual_review
  - historischer Ground-Truth-Verdict ist UNCLEAR, nicht FALSE_POSITIVE -- wird gemaess Auftrag ('Fall E') niemals automatisch zu FALSE_POSITIVE oder TRUE_POSITIVE aufgeloest.
  - aktueller Match-Zustand: GLEICHE_KATEGORIE

### Nintendo Gamecube Netzteil - original DOL-002 (EUR) - 12V / 3.25A

- listing_id: https://www.ebay.de/itm/227468195928
- price: 12.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=retro_konsolen, rule=Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.

### Sony PlayStation 2 + Original Netzteil, Videokabel, MemoryCard

- listing_id: https://www.kleinanzeigen.de/s-anzeige/sony-playstation-2-original-netzteil-videokabel-memorycard/3480159305-279-756
- price: 50.0
- historical_ground_truth: verdict=FALSE_POSITIVE, category=retro_konsolen, rule=Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis
- current_routing_assessment: category=KEIN_TREFFER, rule=KEIN_TREFFER, match_state=KEIN_TREFFER, routing_status=C_NO_LONGER_MATCHES
- assessment: status=FIXED, confidence=confirmed
  - aktueller Match-Zustand: KEIN_TREFFER -- objektiv ueber evaluate() bestaetigt.
