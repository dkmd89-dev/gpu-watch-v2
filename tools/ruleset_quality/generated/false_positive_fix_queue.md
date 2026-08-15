# False-Positive Fix-Queue

Automatisch generiert von `tools/ruleset_quality/forensics_false_positives.py`. Aendert KEINE YAML-Regeln -- die Entscheidung liegt beim Entwickler.

## MANUAL_REVIEW

### retro_konsolen :: Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`weak_signal` (confidence=confirmed), 1 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `strengthen_positive_signal`
- **Regression-Risiko**: HIGH
- **Betroffene Kategorien**: retro_konsolen
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Nintendo Retro-Konsole (N64/GameCube/DS) ⚠️ Okay' in Kategorie 'retro_konsolen' (z.B. app/tests/test_retro_konsolen.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
  - KEINE automatische YAML-Aenderung -- Status bleibt unsicher, erfordert zusaetzliche Evidenz (z.B. Beschreibungstext/Bildmaterial) vor einer Entscheidung.
- **Beispiel-Listings**:
  - Nintendo DS Lite Handheld-System Weiß Touchscreen inkl. 4 Spiele (https://www.ebay.de/itm/398266334210)

## GROUND_TRUTH_CONFLICT

### konsolen_bundles :: Nintendo Switch (V1/V2/OLED) 👍 Guter Preis

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`weak_signal` (confidence=confirmed), 1 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `strengthen_positive_signal`
- **Regression-Risiko**: HIGH
- **Betroffene Kategorien**: konsolen_bundles
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Nintendo Switch (V1/V2/OLED) 👍 Guter Preis' in Kategorie 'konsolen_bundles' (z.B. app/tests/test_konsolen_bundles.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
  - KEINE YAML-Aenderung geplant -- historisches FALSE_POSITIVE-Label gilt als vermutlich fehlerhaft, aktuelles Matcher-Verhalten wird als korrekt eingestuft.
- **Beispiel-Listings**:
  - Nintendo Switch 32GB Mario Kart 8 Deluxe Bundle Neon Blau/Rot mit Dock (https://www.ebay.de/itm/137602406753)

### konsolen_bundles :: Xbox One S / One X 👍 Guter Preis

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`weak_signal` (confidence=confirmed), 1 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `strengthen_positive_signal`
- **Regression-Risiko**: HIGH
- **Betroffene Kategorien**: konsolen_bundles
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Xbox One S / One X 👍 Guter Preis' in Kategorie 'konsolen_bundles' (z.B. app/tests/test_konsolen_bundles.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
  - KEINE YAML-Aenderung geplant -- historisches FALSE_POSITIVE-Label gilt als vermutlich fehlerhaft, aktuelles Matcher-Verhalten wird als korrekt eingestuft.
- **Beispiel-Listings**:
  - Xbox One S 1TB mit Spiele (https://www.kleinanzeigen.de/s-anzeige/xbox-one-s-1tb-mit-spiele/3479889108-279-4400)

## ALREADY_FIXED

### gaming_pc :: Gaming-PC (Mindestanforderung erfüllt)

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`replacement_part_false_positive` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `add_replacement_part_guard`
- **Regression-Risiko**: LOW
- **Betroffene Kategorien**: gaming_pc
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Gaming-PC (Mindestanforderung erfüllt)' in Kategorie 'gaming_pc' (z.B. app/tests/test_gaming_pc.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - MAINBOARD SET H310M D2P. i5-9500. GTX 1050TI. NWMe. 16GB DDR4. (https://www.kleinanzeigen.de/s-anzeige/mainboard-set-h310m-d2p-i5-9500-gtx-1050ti-nwme-16gb-ddr4-/3480520958-225-8182)

### handhelds :: Asus ROG Ally / Lenovo Legion Go ★ Top-Deal

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`missing_exclude` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `add_exclude`
- **Regression-Risiko**: LOW
- **Betroffene Kategorien**: handhelds
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Asus ROG Ally / Lenovo Legion Go ★ Top-Deal' in Kategorie 'handhelds' (z.B. app/tests/test_handhelds.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - JSAUX Slim-Reisetasche Für Lenovo Legion Go/Go S/Go 2, Hartschalenbeutel | Schla (https://www.ebay.de/itm/307112118573)

### handhelds :: Valve Steam Deck ★ Top-Deal

- **Problem**: 3 bestaetigte(r) historische(r) Fehltreffer, root_cause=`missing_exclude` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `add_exclude`
- **Regression-Risiko**: LOW
- **Betroffene Kategorien**: handhelds
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Valve Steam Deck ★ Top-Deal' in Kategorie 'handhelds' (z.B. app/tests/test_handhelds.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 3 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - USB-C HUB für Steam Deck HDMI 4k 60Hz USB 3.0 PD (https://www.ebay.de/itm/255925725429)
  - Steam Deck Skin Faceplate Schutz Klebefolie Design Vinyl Aufkleber Skins OLED (https://www.ebay.de/itm/304780620667)
  - VITURE USB-C an Brille, Ladeadapter, Laden und Spielen für Switch, Steam Deck (https://www.ebay.de/itm/205573628921)

### iphone :: iPhone 15 Pro Max (≥512GB) 👍 Guter Preis

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`replacement_part_false_positive` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `add_replacement_part_guard`
- **Regression-Risiko**: LOW
- **Betroffene Kategorien**: iphone
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'iPhone 15 Pro Max (≥512GB) 👍 Guter Preis' in Kategorie 'iphone' (z.B. app/tests/test_iphone.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - Apple iPhone 15 Pro Max 512GB Mainboard Platine mit FaceID und Kameramodul  (https://www.ebay.de/itm/236995682525)

### konsolen_bundles :: Nintendo Switch (V1/V2/OLED) ★ Top-Deal

- **Problem**: 3 bestaetigte(r) historische(r) Fehltreffer, root_cause=`weak_signal` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `strengthen_positive_signal`
- **Regression-Risiko**: HIGH
- **Betroffene Kategorien**: konsolen_bundles
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Nintendo Switch (V1/V2/OLED) ★ Top-Deal' in Kategorie 'konsolen_bundles' (z.B. app/tests/test_konsolen_bundles.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 3 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - Luigi's Mansion 2 HD für Nintendo Switch - NEU & OVP (https://www.kleinanzeigen.de/s-anzeige/luigi-s-mansion-2-hd-fuer-nintendo-switch-neu-ovp/3480890852-227-23706)
  - Mario Kart World für Nintendo Switch 2 – NEU  und OVP (https://www.ebay.de/itm/257670779909)
  - NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand (https://www.kleinanzeigen.de/s-anzeige/nba-2k26-fuer-nintendo-switch-2-ovp-schneller-versand/3479886837-227-7978)

### konsolen_bundles :: PS4 Slim / Pro Bundle ★ Top-Deal

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`ambiguous` (confidence=manual_review), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `manual_review`
- **Regression-Risiko**: MEDIUM
- **Betroffene Kategorien**: konsolen_bundles
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'PS4 Slim / Pro Bundle ★ Top-Deal' in Kategorie 'konsolen_bundles' (z.B. app/tests/test_konsolen_bundles.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - Playstation 5 PS4 PS5 Slim HDMI Port Nintendo Reparatur USB PRO (https://www.kleinanzeigen.de/s-anzeige/playstation-5-ps4-ps5-slim-hdmi-port-nintendo-reparatur-usb-pro/3431533294-226-3438)

### notebook_resell :: ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`replacement_part_false_positive` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `add_replacement_part_guard`
- **Regression-Risiko**: LOW
- **Betroffene Kategorien**: notebook_resell
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'ThinkPad T14/X13 (Ryzen/Modern) ★ Resell-Top' in Kategorie 'notebook_resell' (z.B. app/tests/test_notebook_resell.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - Lenovo ThinkPad X390 Mainboard Intel Core i5-8365U 8GB RAM NM-B891 (https://www.ebay.de/itm/357718779954)

### office_pc :: Office-PC (Mindestanforderung erfüllt)

- **Problem**: 2 bestaetigte(r) historische(r) Fehltreffer, root_cause=`replacement_part_false_positive` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `add_replacement_part_guard`
- **Regression-Risiko**: LOW
- **Betroffene Kategorien**: office_pc
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Office-PC (Mindestanforderung erfüllt)' in Kategorie 'office_pc' (z.B. app/tests/test_office_pc.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 2 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - Intel Core i5-8500 Mainboard Bundle 16GB DDR4 RAM Netzteil (https://www.kleinanzeigen.de/s-anzeige/intel-core-i5-8500-mainboard-bundle-16gb-ddr4-ram-netzteil/3480038290-225-13379)
  - Lenovo ThinkPad T490s Mainboard nm-b891 Intel i5-8365U / i5-8265U 8GB RAM (https://www.ebay.de/itm/356717584177)

### retro_konsolen :: Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal

- **Problem**: 2 bestaetigte(r) historische(r) Fehltreffer, root_cause=`weak_signal` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `strengthen_positive_signal`
- **Regression-Risiko**: HIGH
- **Betroffene Kategorien**: retro_konsolen
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Nintendo Retro-Konsole (N64/GameCube/DS) ★ Top-Deal' in Kategorie 'retro_konsolen' (z.B. app/tests/test_retro_konsolen.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 2 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - Nintendo Gamecube Netzteil - original DOL-002 (EUR) - 12V / 3.25A (https://www.ebay.de/itm/227468195928)
  - N64 USB-C Netzteil für Nintendo 64 Ersatznetzteil (https://www.ebay.de/itm/307106426592)

### retro_konsolen :: Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis

- **Problem**: 1 bestaetigte(r) historische(r) Fehltreffer, root_cause=`weak_signal` (confidence=confirmed), 0 davon aktuell noch als aktives Routing-Problem eingestuft.
- **Vorschlag**: `strengthen_positive_signal`
- **Regression-Risiko**: HIGH
- **Betroffene Kategorien**: retro_konsolen
- **Regressionstests**:
  - bestehende TRUE_POSITIVE-Tests fuer Regel 'Sony Retro-Konsole (PS1/PS2) 👍 Guter Preis' in Kategorie 'retro_konsolen' (z.B. app/tests/test_retro_konsolen.py, falls vorhanden) muessen weiterhin gruen bleiben
  - Regression gegen alle 1 bekannten FP-Faelle dieser Gruppe (siehe representative_listings)
  - tools/ruleset_quality/benchmark.py + detailed_transition.py erneut laufen lassen (Regression-Gate)
- **Beispiel-Listings**:
  - Sony PlayStation 2 + Original Netzteil, Videokabel, MemoryCard (https://www.kleinanzeigen.de/s-anzeige/sony-playstation-2-original-netzteil-videokabel-memorycard/3480159305-279-756)
