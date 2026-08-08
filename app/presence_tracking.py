"""Presence-Tracking-Datenmodell für seen.json (Reselling-/Arbitrage-Konzept,
STATUS.md Abschnitt 16, Baustein 6 -- Time-to-Sell-Schätzung, Schritt 1+2).

Ziel des Gesamt-Bausteins: aus der Zeitspanne zwischen "zuerst gesehen" und
"zuletzt gesehen, danach nicht mehr in den Suchergebnissen aufgetaucht"
("delisted") eine Time-to-Sell-Schätzung als Liquiditäts-Proxy je Kategorie
ableiten. Dieser Schritt liefert dafür ausschließlich die Datengrundlage --
KEINE Delisting-Erkennung und KEINE Verweildauer-Berechnung (siehe
STATUS.md, Baustein 6, Schritt 2/3).

Bisher: seen.json war eine reine, flache Liste von URLs -- ausschließlich
Dedup-Baseline (verhindert, dass dasselbe Listing zweimal verarbeitet
wird), ohne jede Zeitinformation.

Neu: seen.json speichert je URL zusätzlich first_seen/last_seen (ISO-8601-
Zeitstempel). first_seen wird beim erstmaligen Sehen gesetzt und danach nie
mehr verändert; last_seen wird bei jedem weiteren Scan aktualisiert, in dem
die URL erneut in den Rohsuchergebnissen auftaucht.

Seit Schritt 2: zusätzlich missed_scans (Zähler aufeinanderfolgender Scans
OHNE erneutes Sichten), delisted (True, sobald der Schwellenwert erreicht
wurde -- verhindert mehrfache Time-to-Sell-Datenpunkte für dasselbe
Angebot) sowie category/price_history_model für GEMATCHTE Angebote (siehe
mark_matched()). Letztere werden bewusst direkt im seen.json-Eintrag
mitgeführt statt bei Delisting-Erkennung in found.json nachzuschlagen --
found.json ist auf FOUND_MAX_ITEMS begrenzt (Rotation), ein zwischenzeitlich
herausrotiertes, aber noch nicht delistetes Angebot wäre dort nicht mehr
auffindbar. seen.json wächst dagegen unbegrenzt (bestehendes Verhalten,
unverändert durch diesen Schritt) und bleibt damit die zuverlässigere
Quelle für diese Verknüpfung.

Migration (rückwärtskompatibel): eine bestehende seen.json im alten
Listenformat wird beim Laden automatisch in das neue Dict-Format
überführt. Für migrierte Einträge liegt keine echte Historie vor -- first_
seen/last_seen werden deshalb bewusst auf None gesetzt, statt einen
erfundenen Zeitstempel (z.B. den Migrationszeitpunkt) einzutragen, der
fälschlich eine Time-to-Sell-Spanne von ~0 Tagen vorgaukeln würde. Die
Delisting-Erkennung (Schritt 2) überspringt first_seen is None deshalb
konsequent bei der Time-to-Sell-Berechnung (siehe time_to_sell.py).
"""
from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Any

# Abgestimmtes Konzept (STATUS.md Abschnitt 16, Baustein 6): "N
# aufeinanderfolgende Scans nicht mehr gesehen -> delisted". Als benannte
# Modulkonstante statt Magic Number, ueberschreibbar per Funktionsparameter
# (Config-Anbindung ueber rules/_global.yaml folgt demselben Muster wie bei
# duplicate_detection.py, siehe app.py-Verdrahtung).
DEFAULT_DELISTING_THRESHOLD_SCANS = 3


@dataclass
class SeenEntry:
    """Presence-Historie für ein einzelnes, per URL identifiziertes Angebot.

    category/price_history_model bleiben None, solange dieses Angebot noch
    nie gematcht wurde (die meisten seen.json-Einträge sind rohe,
    ungematchte Suchtreffer) -- siehe mark_matched().
    """

    first_seen: str | None = None
    last_seen: str | None = None
    missed_scans: int = 0
    delisted: bool = False
    category: str | None = None
    price_history_model: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def migrate_seen_data(raw: Any) -> dict[str, dict]:
    """Überführt geladene seen.json-Rohdaten in das einheitliche
    Dict-Format (siehe SeenEntry).

    - Altes Format (Liste von URL-Strings): migriert, first_seen/last_seen
      beide None (siehe Moduldoku -- keine erfundene Historie).
    - Neues Format (Dict): unverändert durchgereicht (idempotent, ein
      erneuter Load-Aufruf auf bereits migrierten Daten ist ein No-Op).
      Das gilt auch für Dicts aus einer älteren Version dieses Moduls (nur
      first_seen/last_seen, ohne missed_scans/delisted/category/
      price_history_model) -- alle Folgefunktionen greifen defensiv per
      `.get(key, default)` darauf zu statt direkter Schlüssel-Zugriffe.
    - Unbekannter/korrupter Typ: leeres Dict statt Crash (analog zum
      bisherigen `_load_json(..., default=[])`-Verhalten bei fehlender
      Datei).
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {url: SeenEntry().to_dict() for url in raw}
    return {}


def mark_seen(entries: dict[str, dict], url: str, timestamp: str) -> None:
    """Aktualisiert das Presence-Tracking für eine URL in-place.

    Bereits bekannte URL: nur last_seen wird auf `timestamp` gesetzt,
    first_seen bleibt unverändert (auch wenn es -- bei migrierten
    Alt-Einträgen -- None ist; siehe Moduldoku).
    Neue URL: first_seen == last_seen == timestamp.

    Bewusst OHNE missed_scans/delisted-Handling (siehe
    detect_newly_delisted() weiter unten, das läuft einmal pro Scan als
    separater Sweep) -- so bleibt dieser bereits in Schritt 1 getestete
    Pfad unverändert.
    """
    entry = entries.get(url)
    if entry is None:
        entries[url] = SeenEntry(first_seen=timestamp, last_seen=timestamp).to_dict()
    else:
        entry["last_seen"] = timestamp


def mark_matched(
    entries: dict[str, dict], url: str, category: str | None, price_history_model: str | None,
) -> None:
    """Vermerkt category/price_history_model für ein GEMATCHTES Angebot.

    Wird nur für Treffer aufgerufen (result.matched == True), NICHT für
    jeden rohen Suchtreffer -- die meisten seen.json-Einträge betreffen
    Angebote, die nie eine Kategorie-Regel erfüllt haben und sollen auch
    keinen Time-to-Sell-Datenpunkt erzeugen (siehe Moduldoku, Konzept:
    "zuvor GEMATCHTES Angebot").

    Erwartet, dass mark_seen() für dieselbe URL bereits vorher im selben
    Scan aufgerufen wurde (der Eintrag also existiert) -- rein defensiv
    KEIN Crash, falls nicht (legt dann keinen Eintrag an, da ohne
    first_seen/last_seen kein sinnvoller Time-to-Sell-Datenpunkt möglich
    wäre).
    """
    entry = entries.get(url)
    if entry is None:
        return
    entry["category"] = category
    entry["price_history_model"] = price_history_model


def detect_newly_delisted(
    entries: dict[str, dict],
    currently_seen_urls: set[str],
    threshold: int = DEFAULT_DELISTING_THRESHOLD_SCANS,
) -> list[str]:
    """Einmal pro Scan aufzurufender Sweep über ALLE bekannten URLs.

    Für jede URL NICHT in `currently_seen_urls` (also in diesem Scan nicht
    in den Rohsuchergebnissen aufgetaucht) wird `missed_scans` erhöht; für
    jede URL, die weiterhin/wieder auftaucht, wird der Zähler
    zurückgesetzt. Sobald `missed_scans >= threshold`, gilt das Angebot
    als "delisted" (`delisted = True`, damit es künftig übersprungen wird
    -- verhindert mehrfache Time-to-Sell-Datenpunkte für dasselbe Angebot).

    Gibt die Liste der URLs zurück, die GENAU IN DIESEM Aufruf neu als
    delisted erkannt wurden (für die also ein Time-to-Sell-Datenpunkt
    erzeugt werden sollte, siehe time_to_sell.py). Bereits zuvor delistete
    URLs werden übersprungen (weder Zähler noch Flag verändert).
    """
    newly_delisted: list[str] = []
    for url, entry in entries.items():
        if entry.get("delisted"):
            continue
        if url in currently_seen_urls:
            entry["missed_scans"] = 0
            continue
        entry["missed_scans"] = entry.get("missed_scans", 0) + 1
        if entry["missed_scans"] >= threshold:
            entry["delisted"] = True
            newly_delisted.append(url)
    return newly_delisted


def prune_delisted_entries(
    entries: dict[str, dict], max_age_days: int,
) -> tuple[dict[str, dict], int]:
    """Entfernt bereits DELISTETE Einträge, deren `last_seen` älter als
    `max_age_days` ist -- Fix für das unbegrenzte Wachstum von seen.json
    (Produktions-Vorfall, siehe app.py::SEEN_DELISTED_MAX_AGE_DAYS).

    Nur `delisted == True`-Einträge kommen infrage: für sie wurde der
    Time-to-Sell-Datenpunkt bereits in detect_newly_delisted() erzeugt
    (siehe time_to_sell.py) -- die Historie wird danach nur noch für die
    Delisting-Erkennung selbst gebraucht (verhindert erneutes Zählen), die
    nach dem Setzen von `delisted=True` aber bereits abgeschlossen ist.

    Noch aktive (nicht delistete) Einträge bleiben UNABHÄNGIG vom Alter
    erhalten -- deren Entfernung würde den `missed_scans`-Zähler verlieren
    und beim nächsten Sehen fälschlich `first_seen` zurücksetzen.

    Migrierte Alt-Einträge ohne `last_seen` (None, siehe migrate_seen_data())
    werden bei delisted=True ebenfalls entfernt -- ihr Alter ist nicht
    bestimmbar, sie enthalten aber ohnehin keine verwertbare Historie mehr.

    Gibt (bereinigtes Dict, Anzahl entfernter Einträge) zurück. Erstellt
    ein neues Dict statt in-place zu mutieren, um Seiteneffekte auf vom
    Aufrufer evtl. noch parallel referenzierte Objekte zu vermeiden.
    """
    now = datetime.now(timezone.utc)
    kept: dict[str, dict] = {}
    removed = 0
    for url, entry in entries.items():
        if not entry.get("delisted"):
            kept[url] = entry
            continue
        last_seen = entry.get("last_seen")
        if last_seen:
            try:
                last_seen_dt = datetime.fromisoformat(last_seen)
                if last_seen_dt.tzinfo is None:
                    last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
                age_days = (now - last_seen_dt).total_seconds() / 86400
            except ValueError:
                age_days = None
        else:
            age_days = None
        if age_days is None or age_days > max_age_days:
            removed += 1
            continue
        kept[url] = entry
    return kept, removed


def enforce_max_size(
    entries: dict[str, dict], max_items: int,
) -> tuple[dict[str, dict], int]:
    """Begrenzt seen.json zusätzlich auf eine harte Obergrenze an Einträgen
    -- Ergänzung zu prune_delisted_entries() (STATUS.md Abschnitt 31,
    L5-Restlücke): AKTIVE (nicht delistete) Einträge bleiben dort bewusst
    unabhängig vom Alter erhalten (siehe Docstring oben), was bei breiten
    search_terms über viele Kategorien in der Praxis zu unbegrenztem
    Wachstum führt, da die meisten Einträge rohe, ungematchte Suchtreffer
    sind, die so lange aktiv bleiben, wie die Anzeige online ist.

    Nur wirksam, wenn `len(entries) > max_items` -- Normalfall (Anzahl
    unterhalb der Grenze) bleibt unverändert, KEIN Eingriff. Wird die
    Grenze überschritten, werden die ÄLTESTEN Einträge nach `first_seen`
    entfernt, bis die Grenze wieder eingehalten ist. Einträge ohne
    `first_seen` (None -- migrierte Alt-Einträge, siehe migrate_seen_data())
    gelten als am ältesten und werden zuerst entfernt, da für sie ohnehin
    keine verwertbare Historie vorliegt.

    Bekanntes Restrisiko (dokumentiert, nicht automatisch vermeidbar): eine
    entfernte, aber weiterhin aktive Anzeige fällt aus der Dedup-Baseline
    und würde beim nächsten Scan erneut verarbeitet (ggf. erneute
    Benachrichtigung, falls sie weiterhin die Kriterien erfüllt) --
    seltener Edge-Case, nur bei dauerhafter Überschreitung von max_items,
    und betrifft ausschließlich die ältesten (am längsten laufenden)
    Anzeigen im Bestand.

    Gibt (bereinigtes Dict, Anzahl entfernter Einträge) zurück. Erstellt
    ein neues Dict statt in-place zu mutieren, analog zu
    prune_delisted_entries().
    """
    overflow = len(entries) - max_items
    if overflow <= 0:
        return entries, 0

    def _sort_key(item: tuple[str, dict]) -> str:
        # None (kein first_seen) sortiert als leerer String vor jedem
        # echten ISO-8601-Zeitstempel -> gilt als aeltestes.
        return item[1].get("first_seen") or ""

    ordered = sorted(entries.items(), key=_sort_key)
    to_remove = {url for url, _ in ordered[:overflow]}
    kept = {url: entry for url, entry in entries.items() if url not in to_remove}
    return kept, overflow
