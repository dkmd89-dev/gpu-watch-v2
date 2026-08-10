"""Regressionstests für den konsolen_bundles-"Plattformbegriff ist kein
Hardware-Beweis"-Fix (kontrollierter Review, "Variante C", freigegeben
nach KONSOLEN_BUNDLES_REVIEW.md).

Hintergrund: "Nintendo Switch"/"Xbox One S" + "ovp" allein reichte bisher
als vollständiges Match-Signal für konsolen_bundles, unabhängig davon, ob
der Titel tatsächlich ein Gerät oder nur ein Spiel/Zubehörteil mit
Plattformreferenz beschrieb (Gruppe 1 wird durch den bloßen Plattform-
Teilstring erfüllt, Gruppe 2 durch das alleinstehende Wort "ovp").

Auftragsvorgabe (KONSOLEN_BUNDLES_REVIEW.md, freigegebene "Variante C"):
- "ovp" NICHT aus den require_all_of-Gruppen entfernen.
- KEIN bare "controller"-Exclude (Kollisionstest gegen alle 195
  TRUE_POSITIVE-Titel zeigte 14+ echte Bundles, bei denen "Controller"
  von einer Zahl statt einem Konnektor-Wort eingeleitet wird, z.B.
  "2 Controller"/"3 Controller" -- ein bare-Exclude würde diese Bundles
  zerstören).
- KEINE einzelnen Spieltitel (Minecraft, Mario Kart, Pokémon, ...) als
  Excludes sammeln.
- Die "+"-Bundle-Recall-Lücke (siehe KONSOLEN_BUNDLES_REVIEW.md
  Abschnitt 11, z.B. "Nintendo Switch + 2 Controller + Spiele" matcht
  bereits vor diesem Fix nicht, weil Gruppe 2 nur die exakte Phrase "mit
  spiele" kennt) wird hier NICHT gelöst -- eigenständiger, separater
  Befund, andere Ursache (fehlendes statt zu breites Positivsignal).
- Kein neuer Matcher-Mechanismus -- ausschließlich bereits produktive
  YAML-Fähigkeiten wiederverwendet: exclude_category_unless_also_contains
  (bereits für "gehäuse" in dieser Datei aktiv) für die "für Plattform"-
  Phrasen, exclude_category_unless_preceded_by (bereits in
  controller.yaml für "ladekabel"/"netzteil" aktiv) für "pro controller",
  Kompositum-Ergänzung (bereits in retro_konsolen.yaml für "heimkonsole"/
  "spielekonsole" aktiv) für Gruppe 2 der beiden Nintendo-Switch-Regeln.

Nachtrag (Dashboard-Match-Validierung Variante C, Session 2026-08-10):
die vormals dokumentierte Restlücke "GameCube Controller" ohne "für"/
"pro controller" (Abschnitt 7) ist geschlossen -- via
exclude_category_unless_preceded_by, identisches Muster wie "pro
controller", 0 Kollisionen gegen den vollständigen 318-Fingerprint-
Korpus der Kategorie aus data/price_history.jsonl verifiziert.

Weiterhin NICHT geschlossen (siehe Dashboard-Match-Validierung Variante
C, Session 2026-08-10, Antwort an den Auftraggeber): "bare" Spieltitel,
die den Plattformnamen OHNE "für" nennen (z.B. "Nintendo Switch -
Minecraft FRA mit OVP", "Donkey Kong Bananza Nintendo Switch 2 2025
OVP") -- reales, mehrfach in price_history.jsonl bestätigtes Muster,
aber bewusst nicht mit einem ungeprüften YAML-Heuristik-Vorschlag
geschlossen: eine Lockerung würde entweder (a) das explizit geschützte
"OVP bleibt Positivsignal auch ohne Geräte-Marker" umkehren (siehe
test_bare_ovp_ohne_zusatzangabe_matcht_weiterhin(), Abschnitt 5) oder
(b) einzelne Spieltitel sammeln (laut Auftragsvorgabe oben explizit
ausgeschlossen). Erfordert eine eigene, datengetestete Review-Runde.

Läuft gegen die echten, produktiven rules/*.yaml."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate

RULES_DIR = str(Path(__file__).resolve().parent.parent / "rules")
_cfg = None


def _rules_cfg():
    global _cfg
    if _cfg is None:
        _cfg = load_rules(RULES_DIR)
    return _cfg


def _matches_kb(title, price=0.0):
    r = evaluate(title, price, _rules_cfg())
    return r.matched and r.category == "konsolen_bundles"


# ============================================================
# 1. Spiele/Software mit "für Plattform" -- müssen jetzt blockiert werden.
# ============================================================

def test_luigis_mansion_matcht_nicht():
    assert _matches_kb("Luigi's Mansion 2 HD für Nintendo Switch - NEU & OVP") is False


def test_mario_kart_world_matcht_nicht():
    assert _matches_kb("Mario Kart World für Nintendo Switch 2 – NEU  und OVP") is False


def test_nba_2k26_matcht_nicht():
    assert _matches_kb("NBA 2K26 für Nintendo Switch 2 - OVP Schneller Versand") is False
    assert _matches_kb("NBA 2K26 für Nintendo Switch 2 - OVP") is False


def test_weitere_fuer_plattform_spiele_matchen_nicht():
    assert _matches_kb("Minecraft für Nintendo Switch OVP") is False
    assert _matches_kb("Star Wars Outlaws für PS5 OVP") is False
    assert _matches_kb("FIFA 24 für Xbox OVP") is False


# ============================================================
# 2. Standalone-Zubehör mit "für Plattform" / "Pro Controller" --
#    müssen jetzt blockiert werden (bzw. korrekt der eigenen
#    Zubehör-Kategorie zugeordnet werden, siehe Test 2b).
# ============================================================

def test_gamecube_controller_fuer_switch_matcht_nicht():
    assert _matches_kb("GameCube Controller für Nintendo Switch OVP") is False


def test_2x_pro_controller_matcht_nicht_als_konsolen_bundle():
    # "2x Nintendo Switch 2 Pro Controller NEU OVP" ist ein echter
    # Standalone-Controller-Verkauf (2 Stück). Nach diesem Fix matcht er
    # NICHT mehr als konsolen_bundles -- er matcht stattdessen (bereits
    # vor diesem Fix, unveraendert, first-match-wins) korrekt die eigene
    # "controller"-Kategorie (Switch Pro Controller-Regel in
    # controller.yaml). Das ist die inhaltlich richtige Kategorie fuer
    # ein reines Controller-Angebot -- kein Fehlverhalten dieses Fixes.
    r = evaluate("2x Nintendo Switch 2 Pro Controller NEU OVP", 0.0, _rules_cfg())
    assert not (r.matched and r.category == "konsolen_bundles")


def test_pro_controller_standalone_varianten_matchen_nicht_als_konsolen_bundle():
    for title in [
        "Nintendo Switch Pro Controller - Schwarz mit OVP kaum genutzt",
        "Nintendo Switch Pro Controller in OVP",
        "Nintendo Switch Pro Controller, TOP Zustand mit OVP",
        "Nintendo Switch Pro Controller Original | OVP | TOP Zustand",
        "Nintendo Switch 2 - Pro Controller NSWITCH 2 Neu & OVP",
    ]:
        r = evaluate(title, 0.0, _rules_cfg())
        assert not (r.matched and r.category == "konsolen_bundles"), title


# ============================================================
# 3. Sicherheitsprüfung: "für Plattform" bei einem echten Gerät (Spec-
#    Beschreibung, kein Zubehör/Spiel) bleibt dank Geräte-Marker-Ausnahme
#    erhalten.
# ============================================================

def test_fuer_plattform_mit_geraetemarker_matcht_weiterhin():
    r = evaluate(
        "Sony PlayStation 4 Slim Schwarz HDMI USB-A für PS4 Funktioniert einwandfrei",
        0.0, _rules_cfg(),
    )
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_pro_controller_im_echten_bundle_matcht_weiterhin():
    # "Pro" hier Modellname (PS4 Pro), kein "Pro Controller"-Bigram --
    # unveraendert.
    r = evaluate("PlayStation 4 pro mit 2 Controller", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"

    # "Pro Controller" durch Bundle-Konnektor "mit" eingeleitet -- bleibt
    # erlaubt (Variante-C-Konnektor-Logik).
    r2 = evaluate(
        "Nintendo Switch Konsole mit Pro Controller", 0.0, _rules_cfg()
    )
    assert r2.matched is True
    assert r2.category == "konsolen_bundles"


# ============================================================
# 4. Kompositum-Ergänzung: "Spielkonsole"/"Heimkonsole" werden jetzt als
#    Konsolensignal erkannt.
# ============================================================

def test_spielkonsole_kompositum_matcht():
    r = evaluate("Nintendo Switch Spielkonsole mit Set - Guter Zustand", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"

    r2 = evaluate("Nintendo Switch Spielkonsole mit Set - Top Zustand", 0.0, _rules_cfg())
    assert r2.matched is True
    assert r2.category == "konsolen_bundles"


# ============================================================
# 5. Sicherheitsprüfung: bare "ovp" ohne jede Zusatzangabe bleibt
#    weiterhin ein gültiges Positivsignal (Auftragsvorgabe: OVP NICHT
#    entfernen).
# ============================================================

def test_bare_ovp_ohne_zusatzangabe_matcht_weiterhin():
    r = evaluate("Nintendo Switch mit OVP", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_switch_oled_64gb_ovp_matcht_weiterhin():
    r = evaluate("Nintendo Switch OLED 64GB OVP", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_xbox_one_x_1tb_ovp_matcht_weiterhin():
    r = evaluate("Microsoft Xbox One X 1TB Schwarz Inkl OVP", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_switch_v1_hac001_komplett_ovp_matcht_weiterhin():
    r = evaluate("Nintendo Switch V1 HAC-001 mit OVP + Komplett", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


def test_xbox_one_s_konsole_mit_controller_in_ovp_matcht_weiterhin():
    r = evaluate("Xbox One S 500 GB Konsole mit Controller in OVP", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


# ============================================================
# 6. Bereits bestehende, von diesem Fix unberührte Fälle (Sicherheits-
#    prüfung gegen Regression bei bereits vorher korrektem Verhalten).
# ============================================================

def test_bereits_vorher_korrekte_faelle_bleiben_unveraendert():
    # "tasche" bereits unbedingt exkludiert -- unveraendert.
    assert _matches_kb("Nintendo Switch Tasche OVP") is False
    # "controller für" bereits als Phrase exkludiert -- unveraendert.
    assert _matches_kb("Wireless Controller für PS4 Slim Pro") is False
    # Echte Bundles aus dem Praezisionsphrasen-Fix bleiben unveraendert.
    r = evaluate("Nintendo Switch Konsole mit grauen Joy-Cons", 0.0, _rules_cfg())
    assert r.matched is True and r.category == "konsolen_bundles"
    r2 = evaluate(
        "Sony PlayStation 4 Slim 500GB Schwarz mit DualShock 4 Controller & Headset",
        0.0, _rules_cfg(),
    )
    assert r2.matched is True and r2.category == "konsolen_bundles"


# ============================================================
# 7. Nachtrag (Dashboard-Match-Validierung Variante C, Session
#    2026-08-10): die vormals bewusst offene Restluecke "GameCube
#    Controller" ohne "für"/"pro controller" ist jetzt geschlossen --
#    identisches Muster wie "Pro Controller" (exclude_category_unless_
#    preceded_by, Variante-C-Konnektor-Mechanismus, kein bare
#    "controller"-Exclude). Bestaetigt an zwei realen
#    price_history.jsonl-Treffern ("Nintendo Switch 2 GameCube
#    Controller OVP" / "... Nintendo Classics OVP"), 0 Kollisionen
#    gegen den vollstaendigen 318-Fingerprint-Korpus der Kategorie
#    verifiziert.
# ============================================================

def test_gamecube_controller_ohne_fuer_oder_pro_matcht_jetzt_nicht_mehr():
    r = evaluate("Nintendo Switch 2 GameCube Controller OVP", 0.0, _rules_cfg())
    assert not (r.matched and r.category == "konsolen_bundles")

    # Aus dem urspruenglichen Match-Validierungs-Auftrag, mit
    # Trennzeichen-Variante wie im real gemeldeten Titel.
    r2 = evaluate("Nintendo Switch 2 GameCube Controller | OVP | NEU", 0.0, _rules_cfg())
    assert not (r2.matched and r2.category == "konsolen_bundles")


def test_gamecube_controller_im_echten_bundle_matcht_weiterhin():
    # Variante-C-Konnektor-Ausnahme: "mit GameCube Controller" bleibt
    # als echtes Bundle-Zubehoer erlaubt, identisch zu "mit Pro
    # Controller".
    r = evaluate("Nintendo Switch Konsole mit GameCube Controller", 0.0, _rules_cfg())
    assert r.matched is True
    assert r.category == "konsolen_bundles"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
