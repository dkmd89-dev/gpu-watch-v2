## Phase 0 – Analyse (noch keine Code-Änderung)

Geprüft: `matcher.py` (`MatchResult`, `evaluate()`), `app.py` (found.json-Entry-Aufbau), `scoring/profit.py` (`compute_profit`), `top_deal.py` (`evaluate_top_deal`), `api/deals.py`, `templates/index.html` (Server-Jinja + Client-JS `renderCardHtml()`).

### Status je Kartenzeile

| Zeile | Backend-Wert | In `found.json` / API? | Im Dashboard sichtbar? |
|---|---|---|---|
| 💰 Angebot | `price` (Scraper) | ✅ immer | ✅ immer |
| 📊 Marktwert | `top_deal_market_price` (= `PriceStats.market_price`, `top_deal.py`) | ✅ vorhanden, sobald genug Preishistorie (`min_samples`) | ⚠️ **nur** wenn `is_top_deal` — sonst gar nicht gerendert, obwohl der Wert da wäre |
| 🏷️ Verkaufspreis geschätzt | `estimated_resale_price` | ❌ **fehlt komplett.** Wird in `matcher.evaluate()` (Zeile 959/961) lokal berechnet und direkt an `compute_profit()` übergeben — landet aber nie auf `MatchResult`, nie in `found.json`, nie in der API. Nur die *Wirkung* (Marge) ist gespeichert, nicht der Wert selbst. | ❌ |
| 📈 Rabatt | `top_deal_discount_pct` | ✅ vorhanden (unabhängig von `is_top_deal`, siehe `evaluate_top_deal()`) | ⚠️ nur im Top-Deal-Block sichtbar |
| 💵 Gewinn | `estimated_margin_eur` | ✅ vorhanden | ✅ bereits im `.margin`-Block |
| 📈 Marge | `estimated_margin_pct` | ✅ vorhanden | ✅ bereits im `.margin`-Block |
| ⭐ Deal Score | `deal_score` / `deal_stars` | ✅ vorhanden | ✅ als Sterne, aber keine "Score: XX"-Zeile |
| Echter Neupreis | — | ❌ existiert im Datenmodell nicht | entsprechend deiner Vorgabe **nicht** anzeigen |

### Kernbefund
Fünf von sechs Werten sind bereits vorhanden — teils nur ungenutzt im Frontend (Marktwert/Rabatt aktuell an `is_top_deal` gekoppelt, sollten das nicht sein), teils schlicht nicht als Zeile gerendert (Deal Score numerisch). **Einzige echte Lücke:** `estimated_resale_price` selbst wurde nie über den Berechnungsschritt hinaus propagiert.

**Kleinstmögliche additive Erweiterung dafür:**
- `MatchResult`: neues Feld `estimated_resale_price: float | None = None` (Default, rückwärtskompatibel)
- `evaluate()`: beim `return MatchResult(...)` den bereits berechneten lokalen Wert (Zeile 959/961) mitgeben — **keine neue Berechnung**
- `app.py`: Feld in den `entry`-Dict übernehmen (analog `estimated_margin_eur`)
- API liefert es automatisch mit (`/api/found`, `/` reichen `found.json`-Entries 1:1 durch — keine Änderung an `api/status.py`/`api/deals.py` nötig)

### Architektur-Hinweis
Die Deal-Karte existiert **zweimal**: server-seitig als Jinja (`index.html` ~Z.791–850) und client-seitig als JS `renderCardHtml()` (~Z.1300–1410, für Live-Refresh nach Scan/Filter). Beide müssen synchron geändert werden — bestehendes Muster im Projekt, keine Abweichung nötig.

### Geplanter Umsetzungsschritt (bei Freigabe)
1. `matcher.py` + `app.py`: additives Feld `estimated_resale_price`
2. `templates/index.html`: Jinja-Block + JS `renderCardHtml()` parallel um Marktwert/Verkaufspreis/Rabatt/Deal-Score-Zeile erweitern, Anzeige-Gate `is_top_deal` für Marktwert/Rabatt entfernen (Werte generell zeigen, wenn vorhanden), Fallback „nicht verfügbar" bei fehlendem `estimated_resale_price`
3. CSS: bestehende `.margin`-Klasse als Vorbild, kompakte Zeilen statt neuem Kartenbereich, Mobile via bestehende Breakpoints prüfen

Keine Änderung an Deal-Score/Top-Deal/Flip/Resale/Notification-Gate/Matcher-Kernlogik/Scrapern vorgesehen — ausschließlich Anzeige + eine additive Datenfeld-Durchreichung.