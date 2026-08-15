FALSE POSITIVES BY CATEGORY
============================

gaming_pc (1)

  FP #1
    title: MAINBOARD SET H310M D2P. i5-9500. GTX 1050TI. NWMe. 16GB DDR4.
    url: https://www.kleinanzeigen.de/s-anzeige/mainboard-set-h310m-d2p-i5-9500-gtx-1050ti-nwme-16gb-ddr4-/3480520958-225-8182
    stored_category: gaming_pc
    current_category: KEIN_TREFFER
    stored_rule: Gaming-PC (Mindestanforderung erfüllt)
    current_rule: KEIN_TREFFER
    match_path: gaming_pc :: Gaming-PC (Mindestanforderung erfüllt) -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: replacement_part_false_positive
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "Ersatzteil statt Hauptprodukt"
      - Forensik-Snapshot reason: "Titel enthaelt 'Mainboard'/'Motherboard' -- eindeutiges Einzelteil-Signal, unabhaengig von sonst erfuellten require_all_of-Gruppen (z.B. RAM-Groesse des verbauten Speichers auf dem Board selbst)"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_replacement_part_guard
    regression_risk: LOW


handhelds (4)

  FP #1
    title: USB-C HUB für Steam Deck HDMI 4k 60Hz USB 3.0 PD
    url: https://www.ebay.de/itm/255925725429
    stored_category: handhelds
    current_category: KEIN_TREFFER
    stored_rule: Valve Steam Deck ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: handhelds :: Valve Steam Deck ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: missing_exclude
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "fehlendes Exclude"
      - Forensik-Snapshot reason: "Nur 1 unabhaengige(s) Positiv-Kriterium, Zubehoer-/Ersatzteil-Begriff(e) ohne jeden Exclude-Schutz: ['hub']"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_exclude
    regression_risk: LOW

  FP #2
    title: Steam Deck Skin Faceplate Schutz Klebefolie Design Vinyl Aufkleber Skins OLED
    url: https://www.ebay.de/itm/304780620667
    stored_category: handhelds
    current_category: KEIN_TREFFER
    stored_rule: Valve Steam Deck ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: handhelds :: Valve Steam Deck ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: missing_exclude
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "fehlendes Exclude"
      - Forensik-Snapshot reason: "Nur 1 unabhaengige(s) Positiv-Kriterium, Zubehoer-/Ersatzteil-Begriff(e) ohne jeden Exclude-Schutz: ['skin', 'faceplate', 'klebefolie', 'aufkleber']"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_exclude
    regression_risk: LOW

  FP #3
    title: VITURE USB-C an Brille, Ladeadapter, Laden und Spielen für Switch, Steam Deck
    url: https://www.ebay.de/itm/205573628921
    stored_category: handhelds
    current_category: KEIN_TREFFER
    stored_rule: Valve Steam Deck ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: handhelds :: Valve Steam Deck ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: missing_exclude
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "fehlendes Exclude"
      - Forensik-Snapshot reason: "Nur 1 unabhaengige(s) Positiv-Kriterium, Zubehoer-/Ersatzteil-Begriff(e) ohne jeden Exclude-Schutz: ['ladeadapter']"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_exclude
    regression_risk: LOW

  FP #4
    title: JSAUX Slim-Reisetasche Für Lenovo Legion Go/Go S/Go 2, Hartschalenbeutel | Schla
    url: https://www.ebay.de/itm/307112118573
    stored_category: handhelds
    current_category: KEIN_TREFFER
    stored_rule: Asus ROG Ally / Lenovo Legion Go ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: handhelds :: Asus ROG Ally / Lenovo Legion Go ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: missing_exclude
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "fehlendes Exclude"
      - Forensik-Snapshot reason: "Nur 1 unabhaengige(s) Positiv-Kriterium, Zubehoer-/Ersatzteil-Begriff(e) ohne jeden Exclude-Schutz: ['reisetasche']"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_exclude
    regression_risk: LOW


iphone (1)

  FP #1
    title: Apple iPhone 15 Pro Max 512GB Mainboard Platine mit FaceID und Kameramodul 
    url: https://www.ebay.de/itm/236995682525
    stored_category: iphone
    current_category: KEIN_TREFFER
    stored_rule: iPhone 15 Pro Max (≥512GB) 👍 Guter Preis
    current_rule: KEIN_TREFFER
    match_path: iphone :: iPhone 15 Pro Max (≥512GB) 👍 Guter Preis -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: replacement_part_false_positive
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "Ersatzteil statt Hauptprodukt"
      - Forensik-Snapshot reason: "Titel enthaelt 'Mainboard'/'Motherboard' -- eindeutiges Einzelteil-Signal, unabhaengig von sonst erfuellten require_all_of-Gruppen (z.B. RAM-Groesse des verbauten Speichers auf dem Board selbst)"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_replacement_part_guard
    regression_risk: LOW


konsolen_bundles (6)

  FP #1
    title: Luigi's Mansion 2 HD für Nintendo Switch - NEU & OVP
    url: https://www.kleinanzeigen.de/s-anzeige/luigi-s-mansion-2-hd-fuer-nintendo-switch-neu-ovp/3480890852-227-23706
    stored_category: konsolen_bundles
    current_category: KEIN_TREFFER
    stored_rule: Nintendo Switch (V1/V2/OLED) ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: konsolen_bundles :: Nintendo Switch (V1/V2/OLED) ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH ueber generisches Signal ['ovp'] erfuellt (kein staerkeres Alternativwort im selben Treffer), Titel enthaelt zusaetzlich Zubehoer-/Ersatzteil-/Spiel-Indikatoren ([])"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH

  FP #2
    title: Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle Neon Blau/Rot mit Dock
    url: https://www.ebay.de/itm/137602406753
    stored_category: konsolen_bundles
    current_category: konsolen_bundles
    stored_rule: Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
    current_rule: Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
    match_path: konsolen_bundles :: Nintendo Switch (V1/V2/OLED) 👍 Guter Preis -> konsolen_bundles :: Nintendo Switch (V1/V2/OLED) 👍 Guter Preis
    match_state: GLEICHE_KATEGORIE (routing_status=A_SAME_WRONG_CATEGORY)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH ueber generisches Signal ['bundle'] erfuellt (kein staerkeres Alternativwort im selben Treffer), Titel enthaelt zusaetzlich Zubehoer-/Ersatzteil-/Spiel-Indikatoren (['dock'])"
      - aktueller Match-Zustand: GLEICHE_KATEGORIE (routing_status=A_SAME_WRONG_CATEGORY)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH

  FP #3
    title: Playstation 5 PS4 PS5 Slim HDMI Port Nintendo Reparatur USB PRO
    url: https://www.kleinanzeigen.de/s-anzeige/playstation-5-ps4-ps5-slim-hdmi-port-nintendo-reparatur-usb-pro/3431533294-226-3438
    stored_category: konsolen_bundles
    current_category: KEIN_TREFFER
    stored_rule: PS4 Slim / Pro Bundle ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: konsolen_bundles :: PS4 Slim / Pro Bundle ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: ambiguous
    confidence: manual_review
    evidence:
      - Forensik-Snapshot root_cause: "sonstiges"
      - Forensik-Snapshot reason: "Reparatur-/Service-Dienstleistungs-Indikator im Titel: ['reparatur']"
      - Kein bekannter Uebersetzungseintrag fuer diesen Forensik-root_cause-Wert -- keine automatische Taxonomie-Zuordnung ohne Beleg.
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: manual_review
    regression_risk: MEDIUM

  FP #4
    title: Mario Kart World für Nintendo Switch 2 – NEU  und OVP
    url: https://www.ebay.de/itm/257670779909
    stored_category: konsolen_bundles
    current_category: KEIN_TREFFER
    stored_rule: Nintendo Switch (V1/V2/OLED) ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: konsolen_bundles :: Nintendo Switch (V1/V2/OLED) ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH ueber generisches Signal ['ovp'] erfuellt (kein staerkeres Alternativwort im selben Treffer), Titel enthaelt zusaetzlich Zubehoer-/Ersatzteil-/Spiel-Indikatoren ([])"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH

  FP #5
    title: Xbox One S 1TB mit Spiele
    url: https://www.kleinanzeigen.de/s-anzeige/xbox-one-s-1tb-mit-spiele/3479889108-279-4400
    stored_category: konsolen_bundles
    current_category: konsolen_bundles
    stored_rule: Xbox One S / One X 👍 Guter Preis
    current_rule: Xbox One S / One X 👍 Guter Preis
    match_path: konsolen_bundles :: Xbox One S / One X 👍 Guter Preis -> konsolen_bundles :: Xbox One S / One X 👍 Guter Preis
    match_state: GLEICHE_KATEGORIE (routing_status=A_SAME_WRONG_CATEGORY)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH ueber generisches Signal ['mit spiele'] erfuellt (kein staerkeres Alternativwort im selben Treffer), Titel enthaelt zusaetzlich Zubehoer-/Ersatzteil-/Spiel-Indikatoren ([])"
      - aktueller Match-Zustand: GLEICHE_KATEGORIE (routing_status=A_SAME_WRONG_CATEGORY)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH

  FP #6
    title: NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand
    url: https://www.kleinanzeigen.de/s-anzeige/nba-2k26-fuer-nintendo-switch-2-ovp-schneller-versand/3479886837-227-7978
    stored_category: konsolen_bundles
    current_category: KEIN_TREFFER
    stored_rule: Nintendo Switch (V1/V2/OLED) ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: konsolen_bundles :: Nintendo Switch (V1/V2/OLED) ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH ueber generisches Signal ['ovp'] erfuellt (kein staerkeres Alternativwort im selben Treffer), Titel enthaelt zusaetzlich Zubehoer-/Ersatzteil-/Spiel-Indikatoren ([])"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH


notebook_resell (1)

  FP #1
    title: Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM NM-B891
    url: https://www.ebay.de/itm/357718779954
    stored_category: notebook_resell
    current_category: KEIN_TREFFER
    stored_rule: ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top
    current_rule: KEIN_TREFFER
    match_path: notebook_resell :: ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: replacement_part_false_positive
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "Ersatzteil statt Hauptprodukt"
      - Forensik-Snapshot reason: "Titel enthaelt 'Mainboard'/'Motherboard' -- eindeutiges Einzelteil-Signal, unabhaengig von sonst erfuellten require_all_of-Gruppen (z.B. RAM-Groesse des verbauten Speichers auf dem Board selbst)"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_replacement_part_guard
    regression_risk: LOW


office_pc (2)

  FP #1
    title: Intel Core i5-8500 Mainboard Bundle 16GB DDR4 RAM Netzteil
    url: https://www.kleinanzeigen.de/s-anzeige/intel-core-i5-8500-mainboard-bundle-16gb-ddr4-ram-netzteil/3480038290-225-13379
    stored_category: office_pc
    current_category: KEIN_TREFFER
    stored_rule: Office-PC (Mindestanforderung erfüllt)
    current_rule: KEIN_TREFFER
    match_path: office_pc :: Office-PC (Mindestanforderung erfüllt) -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: replacement_part_false_positive
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "Ersatzteil statt Hauptprodukt"
      - Forensik-Snapshot reason: "Titel enthaelt 'Mainboard'/'Motherboard' -- eindeutiges Einzelteil-Signal, unabhaengig von sonst erfuellten require_all_of-Gruppen (z.B. RAM-Groesse des verbauten Speichers auf dem Board selbst)"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_replacement_part_guard
    regression_risk: LOW

  FP #2
    title: Lenovo ThinkPad T490s Mainboard nm-b891 Intel i5-8365U / i5-8265U 8GB RAM
    url: https://www.ebay.de/itm/356717584177
    stored_category: office_pc
    current_category: KEIN_TREFFER
    stored_rule: Office-PC (Mindestanforderung erfüllt)
    current_rule: KEIN_TREFFER
    match_path: office_pc :: Office-PC (Mindestanforderung erfüllt) -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: replacement_part_false_positive
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "Ersatzteil statt Hauptprodukt"
      - Forensik-Snapshot reason: "Titel enthaelt 'Mainboard'/'Motherboard' -- eindeutiges Einzelteil-Signal, unabhaengig von sonst erfuellten require_all_of-Gruppen (z.B. RAM-Groesse des verbauten Speichers auf dem Board selbst)"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: add_replacement_part_guard
    regression_risk: LOW


retro_konsolen (4)

  FP #1
    title: Nintendo DS Lite Handheld-System Weiß Touchscreen inkl. 4 Spiele
    url: https://www.ebay.de/itm/398266334210
    stored_category: retro_konsolen
    current_category: retro_konsolen
    stored_rule: Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay
    current_rule: Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay
    match_path: retro_konsolen :: Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay -> retro_konsolen :: Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay
    match_state: GLEICHE_KATEGORIE (routing_status=A_SAME_WRONG_CATEGORY)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH ueber generisches Signal ['system'] erfuellt (kein staerkeres Alternativwort im selben Treffer), Titel enthaelt zusaetzlich Zubehoer-/Ersatzteil-/Spiel-Indikatoren ([])"
      - aktueller Match-Zustand: GLEICHE_KATEGORIE (routing_status=A_SAME_WRONG_CATEGORY)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH

  FP #2
    title: Sony PlayStation 2 + Original Netzteil, Videokabel, MemoryCard
    url: https://www.kleinanzeigen.de/s-anzeige/sony-playstation-2-original-netzteil-videokabel-memorycard/3480159305-279-756
    stored_category: retro_konsolen
    current_category: KEIN_TREFFER
    stored_rule: Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis
    current_rule: KEIN_TREFFER
    match_path: retro_konsolen :: Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH durch Zubehoer-Begriff(e) erfuellt (kein staerkeres Alternativwort im selben Treffer): ['netzteil']"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH

  FP #3
    title: Nintendo Gamecube Netzteil - original DOL-002 (EUR) - 12V / 3.25A
    url: https://www.ebay.de/itm/227468195928
    stored_category: retro_konsolen
    current_category: KEIN_TREFFER
    stored_rule: Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: retro_konsolen :: Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH durch Zubehoer-Begriff(e) erfuellt (kein staerkeres Alternativwort im selben Treffer): ['netzteil']"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH

  FP #4
    title: N64 USB-C Netzteil für Nintendo 64 Ersatznetzteil
    url: https://www.ebay.de/itm/307106426592
    stored_category: retro_konsolen
    current_category: KEIN_TREFFER
    stored_rule: Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal
    current_rule: KEIN_TREFFER
    match_path: retro_konsolen :: Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal -> KEIN_TREFFER
    match_state: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    root_cause: weak_signal
    confidence: confirmed
    evidence:
      - Forensik-Snapshot root_cause: "falsches Positivsignal"
      - Forensik-Snapshot reason: "Ein require_all_of-Kriterium wurde AUSSCHLIESSLICH durch Zubehoer-Begriff(e) erfuellt (kein staerkeres Alternativwort im selben Treffer): ['netzteil']"
      - aktueller Match-Zustand: KEIN_TREFFER (routing_status=C_NO_LONGER_MATCHES)
    recommended_fix: strengthen_positive_signal
    regression_risk: HIGH


FP-KANDIDATEN (Ground-Truth-Verdict UNCLEAR -- KEINE bestaetigten FPs)
======================================================================
konsolen_bundles (34)
  - Nintendo Switch 2 GameCube Controller | OVP | NEU [KEIN_TREFFER]
  - Microsoft Xbox One X 1TB Schwarz Inkl OVP Ohne Controller [GLEICHE_KATEGORIE]
  - Nintendo Switch 2 GameCube Controller – Nintendo Classics – OVP – NEU [KEIN_TREFFER]
  - Nintendo Switch Sports inkl. 12-in-1 Zubehör Set [KEIN_TREFFER]
  - Nintendo Switch Grau Bundle  Neue Sticks (Kein Drift) + Extras! [GLEICHE_KATEGORIE]
  - Nintendo Pokémon Purpur Nintendo Switch neu/sealed in OVP [KEIN_TREFFER]
  - Nintendo Switch - Minecraft FRA mit OVP [KEIN_TREFFER]
  - Pokémon Let’s Go Evoli! Nintendo Switch – OVP komplett [KEIN_TREFFER]
  - Star Fox "NEU & OVP" (Nintendo Switch 2) [KEIN_TREFFER]
  - Nintendo Switch Komplett Set OVP [GLEICHE_KATEGORIE]
  ... und 24 weitere

retro_konsolen (1)
  - Nintendo DS Lite Handheld-System hellblau Touchscreen [GLEICHE_KATEGORIE]

CATEGORY SUMMARY
================
category             | confirmed FP | candidates | root causes                                   | priority
gaming_pc            | 1            | 0          | replacement_part_false_positive               | P1
handhelds            | 4            | 0          | missing_exclude                               | P1
iphone               | 1            | 0          | replacement_part_false_positive               | P1
konsolen_bundles     | 6            | 34         | ambiguous, weak_signal                        | P1, P2, P3
notebook_resell      | 1            | 0          | replacement_part_false_positive               | P1
office_pc            | 2            | 0          | replacement_part_false_positive               | P1
retro_konsolen       | 4            | 1          | weak_signal                                   | P1, P2

FIX QUEUE
=========
P1:
  [konsolen_bundles] Regel 'Nintendo Switch (V1/V2/OLED) 👍 Guter Preis' -- root_cause=weak_signal (confidence=confirmed), 1 Fall/Faelle (1 weiterhin aktiv) -- fix=strengthen_positive_signal, risk=HIGH
  [konsolen_bundles] Regel 'Xbox One S / One X 👍 Guter Preis' -- root_cause=weak_signal (confidence=confirmed), 1 Fall/Faelle (1 weiterhin aktiv) -- fix=strengthen_positive_signal, risk=HIGH
  [retro_konsolen] Regel 'Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay' -- root_cause=weak_signal (confidence=confirmed), 1 Fall/Faelle (1 weiterhin aktiv) -- fix=strengthen_positive_signal, risk=HIGH
  [gaming_pc] Regel 'Gaming-PC (Mindestanforderung erfüllt)' -- root_cause=replacement_part_false_positive (confidence=confirmed), 1 Fall/Faelle (0 weiterhin aktiv) -- fix=add_replacement_part_guard, risk=LOW
  [handhelds] Regel 'Asus ROG Ally / Lenovo Legion Go ★ Top-Deal' -- root_cause=missing_exclude (confidence=confirmed), 1 Fall/Faelle (0 weiterhin aktiv) -- fix=add_exclude, risk=LOW
  [handhelds] Regel 'Valve Steam Deck ★ Top-Deal' -- root_cause=missing_exclude (confidence=confirmed), 3 Fall/Faelle (0 weiterhin aktiv) -- fix=add_exclude, risk=LOW
  [iphone] Regel 'iPhone 15 Pro Max (≥512GB) 👍 Guter Preis' -- root_cause=replacement_part_false_positive (confidence=confirmed), 1 Fall/Faelle (0 weiterhin aktiv) -- fix=add_replacement_part_guard, risk=LOW
  [notebook_resell] Regel 'ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top' -- root_cause=replacement_part_false_positive (confidence=confirmed), 1 Fall/Faelle (0 weiterhin aktiv) -- fix=add_replacement_part_guard, risk=LOW
  [office_pc] Regel 'Office-PC (Mindestanforderung erfüllt)' -- root_cause=replacement_part_false_positive (confidence=confirmed), 2 Fall/Faelle (0 weiterhin aktiv) -- fix=add_replacement_part_guard, risk=LOW

P2:
  [konsolen_bundles] Regel 'Nintendo Switch (V1/V2/OLED) ★ Top-Deal' -- root_cause=weak_signal (confidence=confirmed), 3 Fall/Faelle (0 weiterhin aktiv) -- fix=strengthen_positive_signal, risk=HIGH
  [retro_konsolen] Regel 'Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal' -- root_cause=weak_signal (confidence=confirmed), 2 Fall/Faelle (0 weiterhin aktiv) -- fix=strengthen_positive_signal, risk=HIGH
  [retro_konsolen] Regel 'Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis' -- root_cause=weak_signal (confidence=confirmed), 1 Fall/Faelle (0 weiterhin aktiv) -- fix=strengthen_positive_signal, risk=HIGH

P3:
  [konsolen_bundles] Regel 'PS4 Slim / Pro Bundle ★ Top-Deal' -- root_cause=ambiguous (confidence=manual_review), 1 Fall/Faelle (0 weiterhin aktiv) -- fix=manual_review, risk=MEDIUM
