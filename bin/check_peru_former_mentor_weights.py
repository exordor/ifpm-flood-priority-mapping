#!/usr/bin/env python3
"""Check that the Peru-first PIM implementation uses the latest mentor weights."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_SCRIPT = ROOT / "bin/scenarios/run_peru_former_priority_scenarios.py"
ES_SCRIPT = ROOT / "bin/criteria/build_pim_environmental_sensitivity.py"
SCENARIO_WEIGHTS_CSV = ROOT / "outputs/peru_former_pim_chain/priority_scenarios/scenario_weights.csv"
SUBCRITERIA_CSV = ROOT / "outputs/peru_former_pim_chain/priority_scenarios/pim_subcriteria_weights.csv"

EXPECTED_MAIN_WEIGHTS = {
    "flood_hazard": 0.34,
    "sediment": 0.25,
    "landuse_asm": 0.17,
    "environmental": 0.10,
    "socioeconomic": 0.14,
}

EXPECTED_COMPONENT_WEIGHTS = {
    "flood_hazard": {
        "rainfall_climatology": 0.35,
        "twi_wetness": 0.25,
        "drainage_proximity": 0.40,
    },
    "sediment": {
        "soil_k_factor": 0.25,
        "ls_factor": 0.50,
        "c_factor": 0.25,
    },
    "landuse_asm": {
        "land_cover_pressure": 0.40,
        "bare_soil_vegetation_loss": 0.35,
        "built_agriculture_road_expansion": 0.25,
    },
    "environmental": {
        "water_wetland_context": 0.65,
        "protected_ecological_context": 0.35,
    },
    "socioeconomic": {
        "road_access_proximity": 0.35,
        "settlement_population": 0.35,
        "critical_infrastructure": 0.30,
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
    scenarios = load_module(SCENARIO_SCRIPT, "run_peru_former_priority_scenarios")
    es = load_module(ES_SCRIPT, "build_pim_environmental_sensitivity")

    assert_weights(scenarios.MENTOR_PERU_MAIN_WEIGHTS, EXPECTED_MAIN_WEIGHTS, "main weights")
    if set(scenarios.SCENARIOS) != {"mentor_peru_direct_pim"}:
        raise AssertionError(
            f"active Peru scenarios must contain only mentor_peru_direct_pim: {sorted(scenarios.SCENARIOS)}"
        )
    assert_weights(
        scenarios.SCENARIOS["mentor_peru_direct_pim"],
        EXPECTED_MAIN_WEIGHTS,
        "mentor_peru_direct_pim",
    )
    for criterion, expected in EXPECTED_COMPONENT_WEIGHTS.items():
        assert_weights(scenarios.PIM_COMPONENTS[criterion], expected, f"{criterion} components")
    # On this branch the runner recombines WW/PA directly with Supervisor's
    # 0.65/0.35 weights, so the upstream pre-blended 0.60/0.40 no longer feeds
    # the PIM. It is recorded for reference only and not enforced here.
    upstream_es = es.ENVIRONMENTAL_CONTEXT_WEIGHTS["Peru"]
    if upstream_es != {"water_wetland_context": 0.60, "protected_ecological_context": 0.40}:
        print(
            "note: upstream environmental_sensitivity builder uses "
            f"{upstream_es}, but the PIM recombines WW/PA directly at 0.65/0.35"
        )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_outputs() -> None:
    rows = read_csv(SCENARIO_WEIGHTS_CSV)
    output_scenarios = {row["scenario"] for row in rows}
    if output_scenarios != {"mentor_peru_direct_pim"}:
        raise AssertionError(f"unexpected active Peru output scenarios: {sorted(output_scenarios)}")
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
        ("landuse_asm", "bare_soil_vegetation_loss"),
        ("landuse_asm", "built_agriculture_road_expansion"),
        ("environmental", "water_wetland_context"),
        ("environmental", "protected_ecological_context"),
        ("socioeconomic", "road_access_proximity"),
        ("socioeconomic", "settlement_population"),
        ("socioeconomic", "critical_infrastructure"),
    ]
    missing = [item for item in required if item not in implemented]
    if missing:
        raise AssertionError(f"missing subcriteria rows: {missing}")
    socioeconomic_applied = {
        row["component"]: float(row["applied_weight_in_current_run"])
        for row in sub_rows
        if row["pim_criterion"] == "socioeconomic"
    }
    assert_weights(
        socioeconomic_applied,
        {"road_access_proximity": 0.35, "settlement_population": 0.35, "critical_infrastructure": 0.30},
        "socioeconomic subcriteria weights",
    )
    if implemented[("socioeconomic", "critical_infrastructure")] != "implemented_as_built_density_proxy":
        raise AssertionError("critical_infrastructure must be marked as built-density proxy")
    sediment_applied = {
        row["component"]: float(row["applied_weight_in_current_run"])
        for row in sub_rows
        if row["pim_criterion"] == "sediment"
    }
    assert_weights(
        sediment_applied,
        {"soil_k_factor": 0.25, "ls_factor": 0.50, "c_factor": 0.25},
        "sediment subcriteria weights",
    )
    for component in ("soil_k_factor", "ls_factor", "c_factor"):
        if implemented[("sediment", component)] != "implemented":
            raise AssertionError(f"{component} must be marked implemented")


def main() -> int:
    check_script_constants()
    if SCENARIO_WEIGHTS_CSV.exists() or SUBCRITERIA_CSV.exists():
        check_outputs()
    print("Peru mentor-weight implementation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
