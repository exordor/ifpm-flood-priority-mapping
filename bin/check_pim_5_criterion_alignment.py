#!/usr/bin/env python3
"""Check that current priority overlays use PIM main criteria as top-level weights."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIRS = [
    ROOT / "outputs/peru_former_pim_chain/priority_scenarios",
]

PIM_MAIN_CRITERIA = {
    "flood_hazard",
    "sediment",
    "landuse_asm",
    "environmental",
    "socioeconomic",
}
ACTIVE_SCORED_PIM_CRITERIA = {
    "flood_hazard",
    "sediment",
    "landuse_asm",
    "environmental",
    "socioeconomic",
}
FORBIDDEN_TOP_LEVEL_COMPONENTS = {
    "flood_conditioning_factors",
    "soil_erosion_factors",
    "land_cover_pressure",
    "mining_pressure",
    "exposure_indicators",
    "rainfall_climatology",
}

REQUIRED_SUMMARY_METRICS = {
    "pim_main_criteria_count": "5",
    "active_scored_pim_criteria_count": "5",
    "environmental_sensitivity_status": "provisional",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_weights(out_dir: Path) -> list[str]:
    errors: list[str] = []
    rows = read_csv(out_dir / "scenario_weights.csv")
    by_scenario: dict[str, float] = defaultdict(float)
    for row in rows:
        scenario = row["scenario"]
        criterion = row["criterion"]
        weight = float(row["weight"])
        by_scenario[scenario] += weight
        if criterion in FORBIDDEN_TOP_LEVEL_COMPONENTS:
            errors.append(
                f"{out_dir.relative_to(ROOT)} scenario {scenario} uses component "
                f"{criterion!r} as a top-level weight"
            )
        if criterion not in ACTIVE_SCORED_PIM_CRITERIA:
            errors.append(
                f"{out_dir.relative_to(ROOT)} scenario {scenario} has non-active "
                f"PIM top-level criterion {criterion!r}"
            )
        if criterion not in PIM_MAIN_CRITERIA:
            errors.append(
                f"{out_dir.relative_to(ROOT)} scenario {scenario} has unknown "
                f"PIM criterion {criterion!r}"
            )
    for scenario, total in sorted(by_scenario.items()):
        if abs(total - 1.0) > 1e-6:
            errors.append(
                f"{out_dir.relative_to(ROOT)} scenario {scenario} weights sum to "
                f"{total:.8f}, expected 1.0"
            )
    return errors


def check_priority_summary(out_dir: Path) -> list[str]:
    errors: list[str] = []
    rows = read_csv(out_dir / "priority_screening_summary.csv")
    metrics = {row["metric"]: row["value"] for row in rows}
    for metric, expected in REQUIRED_SUMMARY_METRICS.items():
        actual = metrics.get(metric)
        if actual != expected:
            errors.append(
                f"{out_dir.relative_to(ROOT)} metric {metric!r} is {actual!r}, "
                f"expected {expected!r}"
            )
    return errors


def check_pim_criteria_outputs(out_dir: Path) -> list[str]:
    errors: list[str] = []
    criteria_dir = out_dir / "pim_criteria"
    required = {
        "flood_hazard_0_1.tif",
        "sediment_0_1.tif",
        "landuse_asm_0_1.tif",
        "environmental_0_1.tif",
        "socioeconomic_0_1.tif",
    }
    for filename in sorted(required):
        if not (criteria_dir / filename).exists():
            errors.append(
                f"{out_dir.relative_to(ROOT)} missing active PIM criterion raster "
                f"{criteria_dir.name}/{filename}"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    for out_dir in OUTPUT_DIRS:
        errors.extend(check_weights(out_dir))
        errors.extend(check_priority_summary(out_dir))
        errors.extend(check_pim_criteria_outputs(out_dir))
    if errors:
        print("PIM 5-criterion implementation alignment check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PIM 5-criterion implementation alignment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
