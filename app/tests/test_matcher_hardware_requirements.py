"""Tests für die Hardware-Requirement-Logik in matcher.py (Phase 5)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matcher import (
    _cpu_meets_requirement,
    _ram_meets_requirement,
    _case_meets_requirement,
    _gpu_meets_requirement,
    _evaluate_hardware_requirements,
)
from categories.detectors.cpu import CpuMatch
from categories.detectors.case import CaseMatch
from categories.detectors.gpu import GpuMatch


OFFICE_CPU_REQ = {
    "intel": {"min_tier_rank": 5, "min_generation": 8},
    "amd": {"min_tier_rank": 5, "min_generation": 2000},
}


# ---------- _cpu_meets_requirement ----------

def test_cpu_intel_i5_8400_erfuellt_office_anforderung():
    cpu = CpuMatch(brand="Intel", tier="i5", model_number=8400, generation=8)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is True


def test_cpu_intel_i7_10700_erfuellt_office_anforderung():
    # Besserer Tier UND neuere Generation als Minimum -> muss erfuellen
    cpu = CpuMatch(brand="Intel", tier="i7", model_number=10700, generation=10)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is True


def test_cpu_intel_i3_erfuellt_nicht_zu_niedriger_tier():
    cpu = CpuMatch(brand="Intel", tier="i3", model_number=8100, generation=8)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is False


def test_cpu_intel_i5_7500_erfuellt_nicht_zu_alte_generation():
    cpu = CpuMatch(brand="Intel", tier="i5", model_number=7500, generation=7)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is False


def test_cpu_amd_ryzen5_3600_erfuellt_office_anforderung():
    cpu = CpuMatch(brand="AMD", tier="Ryzen 5", model_number=3600, generation=3000)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is True


def test_cpu_amd_ryzen5_2600_erfuellt_grenzwert_exakt():
    cpu = CpuMatch(brand="AMD", tier="Ryzen 5", model_number=2600, generation=2000)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is True


def test_cpu_amd_ryzen3_erfuellt_nicht_zu_niedriger_tier():
    cpu = CpuMatch(brand="AMD", tier="Ryzen 3", model_number=3200, generation=3000)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is False


def test_cpu_amd_ryzen5_1600_erfuellt_nicht_zu_alte_generation():
    cpu = CpuMatch(brand="AMD", tier="Ryzen 5", model_number=1600, generation=1000)
    assert _cpu_meets_requirement(cpu, OFFICE_CPU_REQ) is False


def test_cpu_none_erfuellt_nie():
    assert _cpu_meets_requirement(None, OFFICE_CPU_REQ) is False


def test_cpu_hersteller_nicht_im_requirement_erfuellt_nicht():
    intel_only_req = {"intel": {"min_tier_rank": 5, "min_generation": 8}}
    cpu = CpuMatch(brand="AMD", tier="Ryzen 5", model_number=5600, generation=5000)
    assert _cpu_meets_requirement(cpu, intel_only_req) is False


# ---------- _ram_meets_requirement ----------

def test_ram_erfuellt_mindestgroesse():
    assert _ram_meets_requirement(16, "DDR4", {"min_gb": 8, "type_exclude": ["DDR3"]}) is True


def test_ram_erfuellt_exakte_mindestgroesse():
    assert _ram_meets_requirement(8, None, {"min_gb": 8, "type_exclude": []}) is True


def test_ram_zu_wenig_erfuellt_nicht():
    assert _ram_meets_requirement(4, "DDR4", {"min_gb": 8, "type_exclude": []}) is False


def test_ram_ddr3_wird_ausgeschlossen():
    assert _ram_meets_requirement(16, "DDR3", {"min_gb": 8, "type_exclude": ["DDR3"]}) is False


def test_ram_unbekannt_erfuellt_nicht_wenn_min_gefordert():
    assert _ram_meets_requirement(None, None, {"min_gb": 8, "type_exclude": []}) is False


# ---------- _case_meets_requirement ----------

def test_case_none_erfuellt_immer():
    assert _case_meets_requirement(None, {"exclude_categories": ["excluded"]}) is True


def test_case_tower_erfuellt():
    case = CaseMatch(case_type="Tower", category="allowed")
    assert _case_meets_requirement(case, {"exclude_categories": ["excluded"]}) is True


def test_case_mini_pc_erfuellt_nicht():
    case = CaseMatch(case_type="Mini-PC", category="excluded")
    assert _case_meets_requirement(case, {"exclude_categories": ["excluded"]}) is False


# ---------- _gpu_meets_requirement ----------

def test_gpu_nicht_erforderlich_erfuellt_ohne_gpu():
    assert _gpu_meets_requirement(None, False) is True


def test_gpu_nicht_erforderlich_erfuellt_auch_mit_gpu():
    gpu = GpuMatch(brand="NVIDIA", model="RTX 3060", is_preferred=True)
    assert _gpu_meets_requirement(gpu, False) is True


def test_gpu_erforderlich_erfuellt_nicht_ohne_gpu():
    assert _gpu_meets_requirement(None, True) is False


def test_gpu_erforderlich_erfuellt_mit_gpu():
    gpu = GpuMatch(brand="AMD", model="RX 6700 XT", is_preferred=True)
    assert _gpu_meets_requirement(gpu, True) is True


def test_gpu_preferred_only_erfuellt_mit_vorzugsmodell():
    gpu = GpuMatch(brand="NVIDIA", model="RTX 3060", is_preferred=True)
    assert _gpu_meets_requirement(gpu, True, preferred_only=True) is True


def test_gpu_preferred_only_erfuellt_nicht_mit_nicht_vorzugsmodell():
    # z.B. RTX 4060 -- dedizierte GPU vorhanden, aber nicht in der Phase-5-Liste
    gpu = GpuMatch(brand="NVIDIA", model="RTX 4060", is_preferred=False)
    assert _gpu_meets_requirement(gpu, True, preferred_only=True) is False


def test_gpu_preferred_only_ohne_gpu_erfuellt_nicht():
    assert _gpu_meets_requirement(None, True, preferred_only=True) is False


def test_gpu_preferred_only_ohne_gpu_pflicht_hat_keine_wirkung():
    # preferred_gpu_only ohne requires_dedicated_gpu=True darf nichts blockieren
    assert _gpu_meets_requirement(None, False, preferred_only=True) is True


# ---------- _evaluate_hardware_requirements (Integration) ----------

OFFICE_REQUIREMENTS = {
    "min_ram_gb": 8,
    "ram_type_exclude": ["DDR3"],
    "min_cpu": OFFICE_CPU_REQ,
    "case": {"exclude_categories": ["excluded"]},
    "requires_dedicated_gpu": False,
}


def test_hardware_requirements_gueltiger_office_pc():
    title = "office pc intel core i5-8500 16gb ddr4 ram 256gb ssd tower"
    matched, _ = _evaluate_hardware_requirements(title, OFFICE_REQUIREMENTS)
    assert matched is True


def test_hardware_requirements_zu_wenig_ram():
    title = "office pc intel core i5-8500 4gb ram 256gb ssd"
    matched, _ = _evaluate_hardware_requirements(title, OFFICE_REQUIREMENTS)
    assert matched is False


def test_hardware_requirements_ddr3_ausgeschlossen():
    title = "office pc intel core i5-8500 16gb ddr3 ram 256gb ssd"
    matched, _ = _evaluate_hardware_requirements(title, OFFICE_REQUIREMENTS)
    assert matched is False


def test_hardware_requirements_cpu_zu_schwach():
    title = "office pc intel core i3-8100 16gb ddr4 ram 256gb ssd"
    matched, _ = _evaluate_hardware_requirements(title, OFFICE_REQUIREMENTS)
    assert matched is False


def test_hardware_requirements_mini_pc_ausgeschlossen():
    title = "mini pc intel core i5-8500 16gb ddr4 ram 256gb ssd"
    matched, _ = _evaluate_hardware_requirements(title, OFFICE_REQUIREMENTS)
    assert matched is False


def test_hardware_requirements_amd_ryzen5_gueltig():
    title = "office pc amd ryzen 5 3600 16gb ddr4 ram tower"
    matched, _ = _evaluate_hardware_requirements(title, OFFICE_REQUIREMENTS)
    assert matched is True


def test_hardware_requirements_mit_dedizierter_gpu_weiterhin_gueltig():
    # requires_dedicated_gpu=False schliesst PCs MIT GPU nicht aus
    title = "office/gaming pc intel core i5-8500 16gb ddr4 ram rtx 3060 tower"
    matched, _ = _evaluate_hardware_requirements(title, OFFICE_REQUIREMENTS)
    assert matched is True


# ---------- Gaming-PC (Integration, requires_dedicated_gpu + preferred_gpu_only) ----------

GAMING_TOP_DEAL_REQUIREMENTS = {
    "min_ram_gb": 8,
    "ram_type_exclude": ["DDR3"],
    "min_cpu": OFFICE_CPU_REQ,
    "case": {"exclude_categories": ["excluded"]},
    "requires_dedicated_gpu": True,
    "preferred_gpu_only": True,
}

GAMING_OKAY_REQUIREMENTS = {
    "min_ram_gb": 8,
    "ram_type_exclude": ["DDR3"],
    "min_cpu": OFFICE_CPU_REQ,
    "case": {"exclude_categories": ["excluded"]},
    "requires_dedicated_gpu": True,
}


def test_gaming_top_deal_mit_vorzugs_gpu_gueltig():
    title = "gaming pc intel core i5-8500 16gb ddr4 ram rtx 3060 tower"
    matched, _ = _evaluate_hardware_requirements(title, GAMING_TOP_DEAL_REQUIREMENTS)
    assert matched is True


def test_gaming_top_deal_mit_nicht_vorzugs_gpu_ungueltig():
    title = "gaming pc intel core i5-8500 16gb ddr4 ram rtx 4060 tower"
    matched, _ = _evaluate_hardware_requirements(title, GAMING_TOP_DEAL_REQUIREMENTS)
    assert matched is False


def test_gaming_okay_mit_beliebiger_dedizierter_gpu_gueltig():
    title = "gaming pc intel core i5-8500 16gb ddr4 ram rtx 4060 tower"
    matched, _ = _evaluate_hardware_requirements(title, GAMING_OKAY_REQUIREMENTS)
    assert matched is True


def test_gaming_ohne_dedizierte_gpu_scheitert_an_gpu_pflicht():
    # APU-Fall: Ryzen 5600G hat nur integrierte Grafik (Radeon Vega) --
    # erfuellt CPU/RAM/Gehaeuse, aber keine dedizierte GPU erkennbar.
    title = "gaming pc amd ryzen 5 5600g 16gb ddr4 ram tower"
    matched, _ = _evaluate_hardware_requirements(title, GAMING_OKAY_REQUIREMENTS)
    assert matched is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
