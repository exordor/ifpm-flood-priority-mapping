#!/usr/bin/env python3
"""Check that the Peru-first PIM implementation uses the latest mentor weights."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_SCRIPT = ROOT / "bin/scenarios/run_pe1_priority_scenarios.py"
ES_SCRIPT = ROOT / "bin/criteria/build_pim_environmental_sensitivity.py"
SCENARIO_WEIGHTS_CSV = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv"
SUBCRITERIA_CSV = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_subcriteria_weights.csv"

EXPECTED_MAIN_WEIGHTS = {
    "flood_hazard": 0.35,
    "sediment": 0.25,
    "landuse_asm": 0.20,
    "environmental": 0.12,
    "socioeconomic": 0.08,
}

EXPECTED_COMPONENT_WEIGHTS = {
    "flood_hazard": {
        "rainfall_climatology": 0.40,
        "twi_wetness": 0.30,
        "drainage_proximity": 0.30,
    },
    "sediment": {
        "soil_erosion_factors": 1.0,
    },
    "landuse_asm": {
        "land_cover_pressure": 0.35,
        "mining_pressure": 0.65,
    },
    "environmental": {
        "environmental_sensitivity": 1.0,
    },
    "socioeconomic": {
        "exposure_indicators": 1.0,
    },
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
    scenarios = load_module(SCENARIO_SCRIPT, "run_pe1_priority_scenarios")
    es = load_module(ES_SCRIPT, "build_pim_environmental_sensitivity")

    assert_weights(scenarios.MENTOR_PERU_MAIN_WEIGHTS, EXPECTED_MAIN_WEIGHTS, "main weights")
    if "mentor_peru_direct_pim" not in scenarios.SCENARIOS:
        raise AssertionError("missing mentor_peru_direct_pim scenario")
    assert_weights(
        scenarios.SCENARIOS["mentor_peru_direct_pim"],
        EXPECTED_MAIN_WEIGHTS,
        "mentor_peru_direct_pim",
    )
    for criterion, expected in EXPECTED_COMPONENT_WEIGHTS.items():
        assert_weights(scenarios.PIM_COMPONENTS[criterion], expected, f"{criterion} components")
    assert_weights(
        es.ENVIRONMENTAL_CONTEXT_WEIGHTS["Peru"],
        {"water_wetland_context": 0.60, "protected_ecological_context": 0.40},
        "environmental context weights",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_outputs() -> None:
    rows = read_csv(SCENARIO_WEIGHTS_CSV)
    mentor = {
        row["criterion"]: float(row["weight"])
        for row in rows
        if row["scenario"] == "mentor_peru_direct_pim"
    }
    assert_weights(mentor, EXPECTED_MAIN_WEIGHTS, "scenario_weights mentor_peru_direct_pim")

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
        if implemented[("sediment", component)] != "available_but_not_independently_weighted_current_run":
            raise AssertionError(f"{component} must be marked available but not independently weighted")


def main() -> int:
    check_script_constants()
    if SCENARIO_WEIGHTS_CSV.exists() or SUBCRITERIA_CSV.exists():
        check_outputs()
    print("Peru mentor-weight implementation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
