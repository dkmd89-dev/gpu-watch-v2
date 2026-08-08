# Kalibrierungs-Review (Phase 12, Schritt 2)

**Stand:** 2026-08-09 · **Status:** Analyse abgeschlossen, KEINE YAML-Änderungen vorgenommen

---

## Zusammenfassung der Prüfung

Für alle 41 im ersten Report auffälligen Regeln wurden die zugrunde
liegenden Datenpunkte **einzeln über `fingerprint`** (normalisierter
Titel, für 7.988 von 9.161 Punkten = 87% verfügbar) geprüft — nicht nur
die Statistik-Zahlen. Ergebnis: **8 der 24 betroffenen Modelle zeigen
klare, nachweisbare False-Match-Probleme**, die eine Preisänderung vor
einem Matching-Fix sinnlos machen würden. Bei den übrigen ist die
Datenlage überwiegend sauber.

| Klassifikation | Anzahl Regeln |
|---|---|
| ÄNDERN | 15 |
| MANUELLE PRÜFUNG | 8 |
| ZUERST MATCHING-FIX | 18 |
| NICHT ÄNDERN | 0 |
| ZU WENIGE DATEN | 0 |

---

## 🔴 Kategorie A: ZUERST MATCHING-FIX (18 Regeln über 6 Modelle)

Bei diesen Modellen habe ich **konkrete, nachweisbare Fehlzuordnungen**
in den Stichproben gefunden — echte Preisdaten anderer Produkte/
Produktteile vermischen sich mit den eigentlich gemeinten Angeboten. Eine
Preisgrenzen-Änderung auf dieser Datenbasis wäre nicht vertrauenswürdig.

### `lego_sw_rare` — bestätigter, schwerwiegendster Befund
**Betroffene Regeln:** alle 6 (Darth Revan ×3, seltene Figur ×3)

Stichprobe der günstigsten Punkte zeigt: **die vier billigsten
Datenpunkte sind gar kein Star Wars** — sie stammen aus LEGO Nexo Knights
("Merlok") und Ninjago ("Kai", "Sawyer", "Lloyd"), jeweils 2,49-2,99€.
Der teure Rand (49-50€) zeigt dagegen echte, seltene Star-Wars-/Classic-
Sammlerstücke. Das bestätigt und verschärft den bereits im ersten Report
vermuteten Konflikt: die Regel matcht offenbar auf generische Begriffe
wie "limited edition"/"selten" + "minifigur", **ohne tatsächlich
"Star Wars" zu verlangen** — dadurch landen fremde LEGO-Themen in der
Preisstatistik.
**Empfehlung:** `require_all_of` um ein explizites Star-Wars-Kriterium
(z.B. "star wars", "clone", Figurennamen) ergänzen, BEVOR die Preise neu
kalibriert werden. Zusätzlich weiterhin: eigener `price_history_model`
für "seltene Figur" getrennt von "Darth Revan" (siehe Report 1).

### `nintendo_retro_konsole` — 21% verdächtige Einträge
**Betroffene Regeln:** alle 3 (Top-Deal, Guter Preis, Okay)

21% der 542 Datenpunkte (114) enthalten Begriffe wie "spiele" (nur Spiele,
keine Konsole), "platzhalter" (explizit als Preis-Platzhalter markiert)
oder markenfremde Mehrfach-Nennungen. Konkretes Beispiel: "ps2 ps3 ps4
xbox xbox360 gamecube sammlungs auflösung der preis ist nur platzhalter"
für 1€ — eine Marken-übergreifende Sammlungsauflösung mit explizit
angegebenem Platzhalterpreis, keine reale Nintendo-Konsole.
**Empfehlung:** Ausschluss von "spiele"/"spiel" ohne Konsolen-Begriff,
Ausschluss "platzhalter"/"VB"-typischer Sammelauflösungen, ggf.
zusätzliches `exclude` für andere Marken (PS/Xbox) in Kombination mit
"Sammlung"/"Auflösung".

### `sony_retro_konsole` — 31% verdächtige Einträge (höchster Wert)
**Betroffene Regeln:** alle 3 (Top-Deal, Guter Preis, Okay)

Gleiches Muster wie Nintendo, noch ausgeprägter: 166 von 533 Punkten
(31%) sind reine Spiele- oder Anleitungs-Listings statt Konsolen, z.B.
"ps1 spiel wer wird millionär auch spielbar auf ps2 und ps3" (1,40€,
ein einzelnes Spiel) oder "sony playstation 1 ps1 psone anleitungen
deutsch pal" (2€, nur eine Anleitung).
**Empfehlung:** analog zu Nintendo — "spiele"/"spiel" ohne
Konsolen-Kontext sowie reine Anleitungs-/Zubehör-Listings ausschließen.

### `roehrenfernseher` — Ersatzteile/Werbung statt Geräte
**Betroffene Regel:** Okay-Tier

18% der Punkte (12/68) sind erkennbar KEINE kompletten Fernseher: die
vier günstigsten Einträge sind ein Widerstands-Set (2,09€), eine
Bedienungsanleitung (2,99€), eine Fernbedienung (3,50€) und ein
Netzschalter (4,48€) — allesamt Einzelteile/Zubehör, keine Geräte.
**Empfehlung:** Ausschluss für "ersatzteil"/"anleitung"/"schaltplan"/
"fernbedienung"/"netzschalter"/"widerstand" u.ä. Komponenten-Begriffe.

### `crt_profi_monitor` — Vintage-Werbeanzeigen statt Monitore
**Betroffene Regeln:** Top-Deal, Guter Preis

Die vier günstigsten Datenpunkte sind **Papier-Werbeanzeigen aus den
1970er/80er-Jahren** ("1978 Sony Trinitron... vintage advert werbung
reklame", 4,99€) — Sammler-Papierwaren, keine funktionsfähigen Monitore.
Diese ziehen den unteren Perzentilbereich (P10/P25, Basis der
Top-Deal-Empfehlung) massiv nach unten. Ohne diese Bereinigung ist die
"ZU HOCH"-Einstufung aus Report 1 **nicht verlässlich** — nach Bereinigung
könnte der reale P25 durchaus näher an oder sogar über der aktuellen
Grenze (80€) liegen.
**Empfehlung:** Ausschluss für "werbung"/"reklame"/"advert"/"anleitung"
o.ä. Print-/Papier-Begriffe.

### `thinkpad_modern` — Einzelteile statt Komplettgeräte
**Betroffene Regel:** Resell-Top

Die vier günstigsten Punkte (7-14€) sind sämtlich **Einzelkomponenten**:
Power-Button, Lautsprecher, Gehäuseunterseite, Kühler/Lüfter — keine
kompletten Laptops. Der teure Rand (239-240€) zeigt dagegen echte
Komplettgeräte mit vollständigen Spezifikationen (CPU/RAM/SSD genannt).
**Empfehlung:** `require_all_of` um RAM/SSD/CPU-Spezifikationsangabe
ergänzen (analog zu den Hardware-Spec-Regeln bei office_pc/gaming_pc),
damit reine Ersatzteil-Listings nicht mehr matchen.

---

## 🟡 Kategorie B: MANUELLE PRÜFUNG (8 Regeln über 6 Modelle)

Grenzfälle: kleine Stichprobe, einzelne erkennbare Ausreißer, oder
methodisch uneindeutige Vermischung (z.B. Einzelfigur- vs. Set-Preise),
aber kein klar dominierendes False-Match-Muster wie in Kategorie A.

| Modell | Regel(n) | Befund |
|---|---|---|
| `iphone_15_plus_128gb` | Top-Deal | n=19 (klein), 1 "Tausche"-Angebot mit 1€-Platzhalterpreis in der Stichprobe — bei so kleiner Basis spürbarer Einfluss auf P25 |
| `iphone_16_pro_max_512gb` | Top-Deal | n=16 (klein), ein 0€-Eintrag ("...schwarz" 1TB, offensichtlich Platzhalter) — bei kleiner Basis relevant |
| `netzteil_650w` | Top-Deal | Viele Punkte ohne `fingerprint` (nicht verifizierbar) — Datenqualität nur teilweise prüfbar |
| `retro_konvolut` | Top-Deal | 1-2 klar branchenfremde Treffer gefunden ("Lego-Bausteine-Sammlung", "Kabel-Sammlung") bei n=33 — nicht dominant, aber vorhanden |
| `lego_sw_clone` | alle 3 Tiers | Vermischt Einzelfigur- und Multi-Figuren-Set-Preise (z.B. "501st Battle Pack" für 50€ neben Einzelfiguren) — thematisch korrekt (alles Clone-Trooper-bezogen), aber methodisch nicht ganz sauber vergleichbar |
| `vintage_hifi_verstaerker` | Okay | Cluster von vier 1€-Einträgen am unteren Rand, teils mehrdeutige Bundle-Beschreibungen ("Verstärker ODER Subwoofer") — P75-basierte Empfehlung aber vom unteren Rand weniger stark beeinflusst |
| `lego_promo` | Guter Preis, Interessant | n=16 (Grenzwert), Daten selbst sauber, aber Stichprobe knapp — vorsichtige Kalibrierung empfohlen statt direkter Übernahme |

**Gemeinsame Empfehlung:** vor einer Änderung entweder mehr Daten
sammeln (kleine Stichproben) oder die identifizierten Einzel-Ausreißer
gezielt aus der Betrachtung nehmen und die Perzentile neu prüfen.

---

## 🟢 Kategorie C: ÄNDERN (15 Regeln über 10 Modelle)

Bei diesen Modellen habe ich die Stichproben (günstigster + teuerster
Rand) geprüft und **keine erkennbaren False Matches** gefunden — die
Fingerprints entsprechen durchgängig dem erwarteten Produkt, die
Preisverteilung wirkt plausibel für ein reales Marktsegment.

| Modell | Regel(n) | Aktuell | Empfehlung | Prüfergebnis |
|---|---|---|---|---|
| `iphone_11_pro_max_128gb` | Top-Deal | 100€ | 150€ | Sauber, ein Einzel-Ausreißer ("leere OVP", 15€) liegt ohnehin unter der aktuellen Grenze, beeinflusst die Empfehlung praktisch nicht |
| `iphone_14_plus_128gb` | Top-Deal | 165€ | 250,40€ | Vollständig saubere Fingerprints |
| `iphone_15_128gb` | Top-Deal | 210€ | 312€ | n=154 (sehr groß), einzelne Tausch-/Platzhalter-Ausreißer bei so großer Basis ohne relevanten Einfluss auf P25 |
| `iphone_15_pro_128gb` | Top-Deal | 265€ | 382,50€ | n=126, saubere Fingerprints |
| `iphone_15_pro_max_128gb` | Top-Deal | 300€ | 450€ | n=72, ein mehrdeutiger Bundle-Eintrag gefunden, bei dieser Stichprobengröße ohne relevanten Einfluss |
| `iphone_16_128gb` | Top-Deal | 275€ | 399€ | n=61, ein Tausch-Ausreißer, bei dieser Größe unproblematisch |
| `iphone_16_pro_128gb` | Top-Deal | 360€ | 550€ | n=79, saubere Fingerprints |
| `iphone_16_pro_max_128gb` | Top-Deal | 415€ | 600€ | n=70, ein Tausch-Ausreißer, unproblematisch bei dieser Größe |
| `macbook_air_m4_512gb` | Top-Deal | 415€ | 726,80€ | **Besonders robuster Befund:** die aktuelle Grenze (415€) liegt SOGAR UNTER dem günstigsten real beobachteten Angebot (499€) — unter der aktuellen Regel kann de facto NIE ein M4 MacBook Air als Top-Deal erkannt werden |
| `lego_cmf` | alle 3 Tiers | 8/15/25€ | 5/7/9,7€ | n=175, durchgängig saubere, plausible Sammelfiguren-Fingerprints |

**Wichtiger Kontext zu den iPhone-Befunden:** die gefundenen "Tausche"-/
Platzhalter-Ausreißer wirken alle nach UNTEN (0-1€) — ihre Entfernung
würde die empfohlene Grenze eher noch ANHEBEN, nicht senken. Der Befund
"aktuelle Grenze zu niedrig" ist damit tendenziell eher unterschätzt als
überschätzt.

---

## Auswirkungsanalyse (bei Umsetzung ALLER unter "ÄNDERN" empfohlenen Werte)

Rein qualitativ, ohne echten Re-Scan (dafür bräuchte es einen Live-Lauf):

- **Match Rate:** Bei den 9 iPhone-Regeln + MacBook Air M4 (alle "ZU
  STRENG") würde eine Anhebung der Top-Deal-Grenzen die Trefferquote in
  diesen Regeln erhöhen — aktuell werden dort vermutlich kaum/keine
  Top-Deals erkannt (macbook_air_m4_512gb: aktuell strukturell
  unmöglich, siehe oben).
- **Top Deals:** mehr iPhone-15/16- und MacBook-Air-M4-Angebote würden
  neu als Top-Deal erkannt werden.
- **Deal-Score:** unverändert (Phase-11-Vorgabe eingehalten) — `max_price`
  fließt zwar in den Preis-Score ein, aber die Score-Formel selbst wird
  nicht angefasst.
- **Flip-Kandidaten:** kein direkter Zusammenhang — `is_robust_flip_
  candidate()` (Phase 11) prüft `estimated_margin_pct`/`_eur`/`deal_score`/
  `resale_confidence`, nicht `max_price` direkt. Ein höheres `max_price`
  kann aber indirekt mehr Treffer überhaupt erst ins System bringen, die
  dann auch als Flip-Kandidat in Frage kommen.
- **Notifications:** mehr potenzielle Treffer bei den iPhone-/MacBook-
  Regeln (mehr Top-Deals = mehr Kandidaten fürs Notification-Gate,
  abhängig von Sternen/Preis-Gate).
- Bei den 6 "ZUERST MATCHING-FIX"-Modellen: **keine Preisänderung ohne
  vorherigen Matching-Fix umsetzen** — sonst würden die (teils absichtlich
  zu niedrig wirkenden) aktuellen Grenzen durch noch stärker verzerrte,
  datenbasierte Werte ersetzt.

---

## Empfohlene Reihenfolge für die Umsetzung (nach deiner Freigabe)

1. **Zuerst:** Matching-Fixes für die 6 "ZUERST MATCHING-FIX"-Modelle
   (Exclude-Terms ergänzen) — eigener Schritt, DANACH deren Preise mit
   neu gesammelten, saubereren Daten erneut prüfen.
2. **Dann:** die 10 "ÄNDERN"-Modelle (15 Regeln) — robuste, direkt
   umsetzbare Kalibrierung.
3. **Später/optional:** die 6 "MANUELLE PRÜFUNG"-Modelle nach weiterer
   Datensammlung oder gezielter Einzelfall-Entscheidung.

Wie vereinbart: **keine YAML-Änderung in diesem Schritt.** Warte auf
deine Entscheidung, welche der drei Gruppen zuerst umgesetzt wird.
