"""Tests fuer den optionalen Kategorie-Key "ignore_global_excludes".

Hintergrund: exclude_global (_global.yaml, z.B. "defekt"/"bastler") gilt per
Default fuer ALLE Kategorien und wird in evaluate() VOR der Regel-Schleife
geprueft. Manche Kategorien bilden aber ausdruecklich Bastler-/Reparatur-
Angebote als eigene Deal-Klasse ab (z.B. "PS5 Controller mit Stick Drift")
und brauchen dafuer eine gezielte Ausnahme -- ohne den globalen Ausschluss
fuer alle anderen Kategorien zu schwaechen.

Analog zu test_rules_category_plugin_contract.py: eine voellig synthetische
Kategorie in einem tmp_path-Verzeichnis, unabhaengig vom echten
rules/-Ordner. Reine Testergaenzung -- keine Aenderung an Produktivcode in
diesem Schritt (der matcher.py-Change selbst ist bereits committet/
vorbereitet, siehe PROJEKTSTAND_KOMPLETT.md Abschnitt 20).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import load_rules, evaluate

MINIMAL_GLOBAL_YAML = """
defaults:
  min_vram_gb: 12
exclude_global:
  - defekt
  - bastler
  - tausch
notifications:
  gate_min_stars: "★★★☆☆"
  gate_max_price: 150
scoring_weights:
  price: 0.7
  ausstattung: 0.15
  hardware_qualitaet: 0.15
  hersteller: 0
  zustand: 0
  lieferumfang: 0
"""

# Kategorie MIT Freigabe fuer "defekt"/"bastler" -- exakt das Muster aus
# controller.yaml/konsolen_bundles.yaml (Fix "Option b").
CATEGORY_WITH_IGNORE_YAML = """
category: "_ignore_test_repair"
label: "Ignore-Test Reparatur-Kategorie"
notify_max_price: 50
search_terms:
  - "Reparatur Gadget"
ignore_global_excludes:
  - "defekt"
  - "bastler"
rules:
  - label: "Reparatur-Gadget (Bastler/Defekt)"
    match:
      - "reparatur gadget"
    require_all_of:
      - ["defekt", "bastler"]
    max_price: 30
    deal_rating: "Top-Deal"
    price_history_model: "ignore_test_repair"
  - label: "Reparatur-Gadget (funktionsfaehig)"
    match:
      - "reparatur gadget"
    exclude:
      - "defekt"
      - "bastler"
    max_price: 50
    deal_rating: "Guter Preis"
    price_history_model: "ignore_test_repair_ok"
"""

# Kontroll-Kategorie OHNE den neuen Key -- muss sich exakt wie vor der
# Aenderung verhalten (Regressionsschutz, Default = leere Liste).
CATEGORY_WITHOUT_IGNORE_YAML = """
category: "_ignore_test_normal"
label: "Ignore-Test Normal-Kategorie"
notify_max_price: 50
search_terms:
  - "Normales Gadget"
rules:
  - label: "Normales Gadget"
    match:
      - "normales gadget"
    max_price: 50
    deal_rating: "Guter Preis"
    price_history_model: "ignore_test_normal"
"""


def _write_rules_dir(tmp_path: Path) -> Path:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "_global.yaml").write_text(MINIMAL_GLOBAL_YAML, encoding="utf-8")
    (rules_dir / "_ignore_test_repair.yaml").write_text(
        CATEGORY_WITH_IGNORE_YAML, encoding="utf-8"
    )
    (rules_dir / "_ignore_test_normal.yaml").write_text(
        CATEGORY_WITHOUT_IGNORE_YAML, encoding="utf-8"
    )
    return rules_dir


def test_freigegebener_begriff_matcht_trotz_globalem_exclude(tmp_path):
    """Kernfall: 'defekt' + 'bastler' sind global gesperrt, die Kategorie
    hat sie aber ueber ignore_global_excludes freigegeben -> muss matchen."""
    cfg = load_rules(str(_write_rules_dir(tmp_path)))
    result = evaluate("Reparatur Gadget defekt bastler", 25, cfg)
    assert result.matched is True
    assert result.category == "_ignore_test_repair"
    assert result.rule_label == "Reparatur-Gadget (Bastler/Defekt)"


def test_nicht_freigegebener_globaler_begriff_sperrt_weiterhin(tmp_path):
    """'tausch' ist global gesperrt und wurde NICHT freigegeben -> muss
    weiterhin blockieren, auch in der Kategorie mit ignore_global_excludes."""
    cfg = load_rules(str(_write_rules_dir(tmp_path)))
    result = evaluate("Reparatur Gadget defekt bastler Tausch gegen Handy", 25, cfg)
    assert result.matched is False


def test_regel_eigener_exclude_greift_trotz_freigabe(tmp_path):
    """ignore_global_excludes hebt nur die KATEGORIEWEITE Sperre auf --
    die funktionsfaehige Regel schliesst 'defekt'/'bastler' weiterhin
    ueber ihr eigenes 'exclude:' aus, MUSS also weiterhin leer bleiben."""
    cfg = load_rules(str(_write_rules_dir(tmp_path)))
    result = evaluate("Reparatur Gadget defekt bastler", 25, cfg)
    assert result.rule_label != "Reparatur-Gadget (funktionsfaehig)"


def test_kategorie_ohne_key_verhaelt_sich_wie_vorher(tmp_path):
    """Regressionsschutz: Kategorien ohne ignore_global_excludes (Default
    leere Liste) bleiben durch exclude_global blockiert -- exakt wie vor
    dieser Aenderung."""
    cfg = load_rules(str(_write_rules_dir(tmp_path)))
    result = evaluate("Normales Gadget defekt", 25, cfg)
    assert result.matched is False


def test_kategorie_ohne_key_matcht_ohne_globalen_ausschlussbegriff(tmp_path):
    """Gegenprobe zum vorherigen Test: ohne Ausschlussbegriff im Titel
    matcht die Normal-Kategorie ganz normal."""
    cfg = load_rules(str(_write_rules_dir(tmp_path)))
    result = evaluate("Normales Gadget", 25, cfg)
    assert result.matched is True
    assert result.category == "_ignore_test_normal"


def test_legacy_einzeldatei_modus_kennt_ignore_global_excludes_nicht(tmp_path):
    """directory_mode=False (Legacy-Einzeldatei-Aufruf von load_rules mit
    einer einzelnen Datei statt einem Verzeichnis) darf durch die neue
    Logik nicht veraendert werden -- globaler Exclude blockiert weiterhin
    unconditional, da ignore_global_excludes ein reines Verzeichnis-Modus-
    Feature ist (siehe tests/fixtures/legacy_single_file_rules.yaml fuer
    das echte Legacy-Format: exclude_global liegt hier UNTER "defaults:",
    nicht als Geschwister wie im Verzeichnis-Modus).
    """
    legacy_yaml = """
defaults:
  min_vram_gb: 0
  exclude_global:
    - defekt
    - bastler

rules:
  - label: "Reparatur-Gadget (Bastler/Defekt)"
    match:
      - "reparatur gadget"
    require_all_of:
      - ["defekt", "bastler"]
    max_price: 30
    deal_rating: "Top-Deal"
    price_history_model: "ignore_test_repair"
"""
    single_file = tmp_path / "single.yaml"
    single_file.write_text(legacy_yaml, encoding="utf-8")
    cfg = load_rules(str(single_file))
    result = evaluate("Reparatur Gadget defekt bastler", 25, cfg)
    assert result.matched is False
