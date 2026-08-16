"""Hardware-Anforderungsprüfung (Phase 5: Office-PC/Gaming-PC).

Schritt 4 der Modularisierung (siehe Analysebericht): unveraendert aus
matcher/core.py extrahiert.

Diese Funktionen pruefen die Ausgabe der Detectors (categories/detectors/)
gegen die "requirements:"-Angaben einer Kategorie-Regel. Jede Funktion ist
bewusst eigenstaendig testbar und kennt nichts von YAML-Parsing oder der
restlichen evaluate()-Orchestrierung in core.py.

PC_AUSSCHLIESSEN wandert mit hierher, da es ausschliesslich von
_ist_kompletter_pc() genutzt wird (vermeidet einen Zirkelimport zurueck
nach core.py). matcher/core.py re-exportiert die Konstante unveraendert
fuer matcher/__init__.py.
"""
from __future__ import annotations

import re

from categories.detectors.cpu import detect_cpu, CpuMatch
from categories.detectors.ram import detect_ram_gb, detect_ram_type
from categories.detectors.case import detect_case_type
from categories.detectors.gpu import detect_dedicated_gpu
from categories.detectors.storage import detect_ssd_gb
from categories.detectors.psu import detect_psu_watt

from matcher.text_matching import _any_term

# Legacy-Fallback: wird NUR noch verwendet, wenn load_rules() im alten
# Einzeldatei-Modus (eine rules.yaml ohne Kategorie-Kontext) aufgerufen wird.
# Im neuen Verzeichnis-Modus liegt die Liste stattdessen in der jeweiligen
# Kategorie-YAML unter "exclude_category" (siehe rules/gpu.yaml) und wird
# NUR für die Regeln dieser einen Kategorie angewendet -- andere Kategorien
# (z.B. künftig "office_pc", "gaming_pc") definieren dort bewusst eine
# andere oder leere Liste, da bei ihnen komplette PC-Systeme ja genau das
# gewünschte Ergebnis sind.
PC_AUSSCHLIESSEN = [
    "gaming pc", "gaming-pc", "gamer pc", "spiele pc",
    "setup", "komplett pc", "fertig pc", "pc komplett",
    "system", "computer", "rechner", "workstation",
    "monitor", "monitore", "bildschirm", "tastatur", "maus",
    "mit monitor", "mit bildschirm",
    "komplettsystem", "komplett-system",
]


def _ist_kompletter_pc(title_lower: str) -> bool:
    """Prüft ob der Titel auf einen kompletten PC hindeutet."""
    return _any_term(title_lower, PC_AUSSCHLIESSEN)


def _cpu_meets_requirement(cpu: CpuMatch | None, requirement: dict) -> bool:
    """Prüft eine erkannte CPU gegen eine Mindestanforderung pro Hersteller.

    requirement-Format: {"intel": {"min_tier_rank": 5, "min_generation": 8},
                          "amd": {"min_tier_rank": 5, "min_generation": 2000}}
    Fehlt der erkannte Hersteller im requirement-Dict, gilt die Anforderung
    als NICHT erfüllt (z.B. eine Intel-Anforderung lässt keine AMD-CPU zu,
    außer AMD ist ebenfalls im requirement-Dict definiert).
    """
    if cpu is None:
        return False

    brand_req = requirement.get(cpu.brand.lower())
    if brand_req is None:
        return False

    tier_digit = re.search(r"\d", cpu.tier)
    tier_rank = int(tier_digit.group()) if tier_digit else 0

    min_tier_rank = brand_req.get("min_tier_rank")
    if min_tier_rank is not None and tier_rank < min_tier_rank:
        return False

    min_generation = brand_req.get("min_generation")
    if min_generation is not None and cpu.generation < min_generation:
        return False

    return True


def _ram_meets_requirement(ram_gb: int | None, ram_type: str | None, requirement: dict) -> bool:
    """Prüft erkannte RAM-Größe/-Typ gegen eine Mindestanforderung.

    Fehlende RAM-Erkennung (ram_gb is None) gilt als NICHT erfüllt, wenn
    ein min_gb gefordert ist -- ohne erkennbare RAM-Angabe im Titel kann
    die Mindestanforderung nicht bestätigt werden.
    """
    min_gb = requirement.get("min_gb")
    if min_gb is not None:
        if ram_gb is None or ram_gb < min_gb:
            return False

    type_exclude = requirement.get("type_exclude", [])
    if ram_type is not None and ram_type in type_exclude:
        return False

    return True


def _storage_meets_requirement(ssd_gb: int | None, requirement: dict) -> bool:
    """Prüft die erkannte SSD-Kapazität gegen eine Mindest-/Höchstgrenze.

    requirement-Format: {"min_ssd_gb": 320, "max_ssd_gb": 639} (beide
    Grenzen optional, mind. eine muss gesetzt sein, damit der Aufrufer
    diese Prüfung überhaupt anstößt -- siehe _evaluate_hardware_requirements).

    Fehlende Kapazitätserkennung (ssd_gb is None) gilt als NICHT erfüllt,
    analog zu _ram_meets_requirement: ohne erkennbare Größe im Titel kann
    eine Kapazitäts-Anforderung nicht bestätigt werden.
    """
    if ssd_gb is None:
        return False

    min_gb = requirement.get("min_ssd_gb")
    if min_gb is not None and ssd_gb < min_gb:
        return False

    max_gb = requirement.get("max_ssd_gb")
    if max_gb is not None and ssd_gb > max_gb:
        return False

    return True


def _psu_meets_requirement(psu_watt: int | None, requirement: dict) -> bool:
    """Prüft die erkannte Netzteilleistung (Watt) gegen eine Mindest-/
    Höchstgrenze.

    requirement-Format: {"min_psu_watt": 550, "max_psu_watt": 1200} (beide
    Grenzen optional, mind. eine muss gesetzt sein, damit der Aufrufer
    diese Prüfung überhaupt anstößt -- siehe _evaluate_hardware_requirements).
    Analog zu _storage_meets_requirement(), inkl. gleicher Begründung für
    "keine Erkennung -> nicht erfüllt": ohne erkennbare Watt-Zahl im Titel
    kann eine Leistungs-Anforderung nicht bestätigt werden.
    """
    if psu_watt is None:
        return False

    min_watt = requirement.get("min_psu_watt")
    if min_watt is not None and psu_watt < min_watt:
        return False

    max_watt = requirement.get("max_psu_watt")
    if max_watt is not None and psu_watt > max_watt:
        return False

    return True


def _case_meets_requirement(case_match, requirement: dict) -> bool:
    """Prüft den erkannten Gehäusetyp gegen eine Ausschluss-Anforderung.

    Keine erkennbare Gehäuseform (case_match is None) gilt als ERFÜLLT --
    die meisten Anzeigen nennen den Formfaktor gar nicht explizit, das
    darf kein PC-Angebot pauschal ausschließen.
    """
    if case_match is None:
        return True

    exclude_categories = requirement.get("exclude_categories", [])
    if case_match.category in exclude_categories:
        return False

    return True


def _gpu_meets_requirement(gpu_match, requires_dedicated_gpu: bool, preferred_only: bool = False) -> bool:
    """Prüft, ob eine geforderte dedizierte GPU vorhanden ist.

    requires_dedicated_gpu=False bedeutet "nicht erforderlich", schließt
    aber Angebote MIT dedizierter GPU nicht aus (z.B. Office-PC mit
    zusätzlicher GPU ist weiterhin ein gültiger Office-PC-Treffer).

    preferred_only=True verlangt zusätzlich, dass die erkannte GPU auf
    der Phase-5-Vorzugsliste steht (siehe categories.detectors.gpu) --
    für eine höherwertige Deal-Einstufung (z.B. "Top-Deal" nur bei
    bevorzugter GPU, "Okay" bei jeder anderen dedizierten GPU).
    """
    if requires_dedicated_gpu and gpu_match is None:
        return False
    # preferred_only ist eine VERSCHÄRFUNG der GPU-Pflicht ("muss zusätzlich
    # eine Vorzugs-GPU sein") und hat daher nur eine Wirkung, wenn überhaupt
    # eine dedizierte GPU gefordert ist. Ohne requires_dedicated_gpu=True gibt
    # es keine GPU-Anforderung, an die preferred_only "verschärfen" könnte.
    if requires_dedicated_gpu and preferred_only and (gpu_match is None or not gpu_match.is_preferred):
        return False
    return True


def _evaluate_hardware_requirements(title_lower: str, requirements: dict) -> tuple[bool, dict]:
    """Orchestriert die Detector-Aufrufe für eine "requirements:"-Regel.

    Ruft nur die Detectors auf, die für die jeweils angegebenen
    Anforderungen tatsächlich gebraucht werden. Gibt zusätzlich zum
    Ergebnis ein "features"-Dict mit den erkannten Rohwerten zurück
    (ram_gb, ram_type, ssd_gb, psu_watt, cpu, case, gpu -- je nachdem,
    was tatsächlich geprüft wurde), damit compute_deal_score() diese
    Werte für die Score-Berechnung weiterverwenden kann, ohne dieselben
    Detectors ein zweites Mal aufzurufen.
    """
    features: dict = {}

    if "min_ram_gb" in requirements or "ram_type_exclude" in requirements:
        ram_gb = detect_ram_gb(title_lower)
        ram_type = detect_ram_type(title_lower)
        features["ram_gb"] = ram_gb
        features["ram_type"] = ram_type
        ram_requirement = {
            "min_gb": requirements.get("min_ram_gb"),
            "type_exclude": requirements.get("ram_type_exclude", []),
        }
        if not _ram_meets_requirement(ram_gb, ram_type, ram_requirement):
            return False, features

    if "min_ssd_gb" in requirements or "max_ssd_gb" in requirements:
        ssd_gb = detect_ssd_gb(title_lower)
        features["ssd_gb"] = ssd_gb
        storage_requirement = {
            "min_ssd_gb": requirements.get("min_ssd_gb"),
            "max_ssd_gb": requirements.get("max_ssd_gb"),
        }
        if not _storage_meets_requirement(ssd_gb, storage_requirement):
            return False, features

    if "min_psu_watt" in requirements or "max_psu_watt" in requirements:
        psu_watt = detect_psu_watt(title_lower)
        features["psu_watt"] = psu_watt
        psu_requirement = {
            "min_psu_watt": requirements.get("min_psu_watt"),
            "max_psu_watt": requirements.get("max_psu_watt"),
        }
        if not _psu_meets_requirement(psu_watt, psu_requirement):
            return False, features

    if "min_cpu" in requirements:
        cpu = detect_cpu(title_lower)
        features["cpu"] = cpu
        if not _cpu_meets_requirement(cpu, requirements["min_cpu"]):
            return False, features

    if "case" in requirements:
        case_match = detect_case_type(title_lower)
        features["case"] = case_match
        if not _case_meets_requirement(case_match, requirements["case"]):
            return False, features

    if "requires_dedicated_gpu" in requirements or "preferred_gpu_only" in requirements:
        gpu_match = detect_dedicated_gpu(title_lower)
        features["gpu"] = gpu_match
        requires_dedicated = requirements.get("requires_dedicated_gpu", False)
        preferred_only = requirements.get("preferred_gpu_only", False)
        if not _gpu_meets_requirement(gpu_match, requires_dedicated, preferred_only):
            return False, features

    return True, features
