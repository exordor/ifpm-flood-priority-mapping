#!/usr/bin/env python3
"""Check that the Zimbabwe secondary PIM run uses the latest direct weights."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_SCRIPT = ROOT / "bin/scenarios/run_boundary_v1_rainfall_exposure_v0_4.py"
ES_SCRIPT = ROOT / "bin/criteria/build_pim_environmental_sensitivity_v0_1.py"
SCENARIO_WEIGHTS_CSV = ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenario_weights.csv"
SUBCRITERIA_CSV = ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_subcriteria_weights.csv"
SCENARIO_DIR = ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenarios"

EXPECTED_MAIN_WEIGHTS = {
    "flood_hazard": 0.32,
    "sediment": 0.23,
    "landuse_asm": 0.18,
    "environmental": 0.12,
    "socioeconomic": 0.15,
}

EXPECTED_COMPONENT_WEIGHTS = {
    "flood_hazard": {
        "rainfall_climatology": 0.35,
        "twi_wetness": 0.30,
        "drainage_proximity": 0.35,
    },
    "sediment": {
        "soil_erosion_factors": 1.0,
    },
    "landuse_asm": {
        "land_cover_pressure": 0.40,
        "mining_pressure": 0.60,
    },
    "environmental": {
        "environmental_sensitivity": 1.0,
    },
    "socioeconomic": {
        "exposure_indicators": 1.0,
    },
}

EXPECTED_ES_CONTEXT_WEIGHTS = {
    "water_wetland_context": 0.55,
    "protected_ecological_context": 0.45,
}

EXPECTED_SCENARIO_FILES = {
    "priority_equal_active_pim.tif",
    "priority_mentor_zimbabwe_direct_pim.tif",
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def assert_weights(actual: dict[str, float], expected: dict[str, float], label: str) -> None:
    if set(actual) != set(expected):
        raise AssertionError(f"{label} keys {sorted(actual)} != {sorted(expected)}")
    for key, expected_value in expected.items():
        actual_value = float(actual[key])
        if abs(actual_value - expected_value) > 1e-9:
            raise AssertionError(
                f"{label} {key}={actual_value:.8f}, expected {expected_value:.8f}"
            )


def check_script_constants() -> None:
    scenarios = load_module(SCENARIO_SCRIPT, "run_boundary_v1_rainfall_exposure_v0_4")
    es = load_module(ES_SCRIPT, "build_pim_environmental_sensitivity_v0_1")

    assert_weights(
        scenarios.ZIMBABWE_MENTOR_MAIN_WEIGHTS,
        EXPECTED_MAIN_WEIGHTS,
        "main weights",
    )
    if "mentor_zimbabwe_direct_pim" not in scenarios.SCENARIOS:
        raise AssertionError("missing mentor_zimbabwe_direct_pim scenario")
    assert_weights(
        scenarios.SCENARIOS["mentor_zimbabwe_direct_pim"],
        EXPECTED_MAIN_WEIGHTS,
        "mentor_zimbabwe_direct_pim",
    )
    for criterion, expected in EXPECTED_COMPONENT_WEIGHTS.items():
        assert_weights(scenarios.PIM_COMPONENTS[criterion], expected, f"{criterion} components")
    assert_weights(
        es.ENVIRONMENTAL_CONTEXT_WEIGHTS["Zimbabwe"],
        EXPECTED_ES_CONTEXT_WEIGHTS,
        "Zimbabwe environmental context weights",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_outputs() -> None:
    if SCENARIO_DIR.exists():
        actual_files = {path.name for path in SCENARIO_DIR.glob("priority_*.tif")}
        if actual_files != EXPECTED_SCENARIO_FILES:
            raise AssertionError(
                f"scenario rasters {sorted(actual_files)} != {sorted(EXPECTED_SCENARIO_FILES)}"
            )

    rows = read_csv(SCENARIO_WEIGHTS_CSV)
    mentor = {
        row["criterion"]: float(row["weight"])
        for row in rows
        if row["scenario"] == "mentor_zimbabwe_direct_pim"
    }
    assert_weights(mentor, EXPECTED_MAIN_WEIGHTS, "scenario_weights mentor_zimbabwe_direct_pim")

    sub_rows = read_csv(SUBCRITERIA_CSV)
    implemented = {
        (row["pim_criterion"], row["component"]): row["implementation_status"]
        for row in sub_rows
    }
    required = [
        ("flood_hazard", "rainfall_climatology"),
        ("flood_hazard", "twi_wetness"),
        ("flood_hazard", "drainage_proximity"),
        ("sediment", "soil_k_factor"),
        ("sediment", "ls_factor"),
        ("sediment", "c_factor"),
        ("landuse_asm", "land_cover_pressure"),
        ("landuse_asm", "mining_pressure"),
        ("environmental", "water_wetland_context"),
        ("environmental", "protected_ecological_context"),
        ("socioeconomic", "road_access_proximity"),
        ("socioeconomic", "infrastructure_exposure"),
    ]
    missing = [item for item in required if item not in implemented]
    if missing:
        raise AssertionError(f"missing subcriteria rows: {missing}")
    if implemented[("socioeconomic", "infrastructure_exposure")] != "not_available_current_run":
        raise AssertionError("infrastructure exposure must be explicitly marked unavailable")
    if implemented[("sediment", "soil_k_factor")] != "not_independently_weighted_current_run":
        raise AssertionError("SoilGrids K-factor must be marked as not independently weighted")
    for component in ("ls_factor", "c_factor"):
        status = implemented[("sediment", component)]
        if status != "available_but_not_independently_weighted_current_run":
            raise AssertionError(f"{component} must be available but not independently weighted")


def main() -> int:
    check_script_constants()
    if SCENARIO_WEIGHTS_CSV.exists() or SUBCRITERIA_CSV.exists():
        check_outputs()
    print("Zimbabwe mentor-weight implementation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
