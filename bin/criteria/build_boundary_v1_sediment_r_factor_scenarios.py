#!/usr/bin/env python3
"""Build provisional LOW/HIGH R sediment scenarios for boundary_v1."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/soil_erosion_factors_0_1.tif"]
OUTPUTS = [ROOT / "outputs/boundary_v1/sediment_r_factor_scenarios/sediment_risk_lowR_provisional_30m.tif"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "sediment_r_factor_scenarios"
CONFIG = ROOT / "context/configs/boundary_v1_sediment_r_factor_scenarios.csv"
STRUCTURE = ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/soil_erosion_factors_0_1.tif"
OUT_DIR = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_structure() -> tuple[np.ndarray, dict]:
    if not STRUCTURE.exists():
        raise FileNotFoundError(f"Missing soil erosion factors raster: {STRUCTURE}")
    with rasterio.open(STRUCTURE) as src:
        data = src.read(1).astype("float32")
        profile = src.profile.copy()
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data, profile
def stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    if values.size == 0:
        return {"valid_cells": 0, "min": "", "mean": "", "p50": "", "p95": "", "max": ""}
    return {
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "p50": round(float(np.percentile(values, 50)), 6),
        "p95": round(float(np.percentile(values, 95)), 6),
        "max": round(float(values.max()), 6),
    }


def main() -> None:
    opts = parse_script_args(boundary_id=BOUNDARY_ID, experiment_id=EXPERIMENT_ID)
    boundary_id = opts.get("boundary_id", BOUNDARY_ID)
    experiment_id = opts.get("experiment_id", EXPERIMENT_ID)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = pd.read_csv(CONFIG)
    structure, profile = read_structure()

    rows: list[dict[str, object]] = []
    for record in config.to_dict("records"):
        scenario_id = record["scenario_id"]
        r_mean = float(record["r_mean"])
        sediment = structure * r_mean
        output = OUT_DIR / f"{scenario_id}_30m.tif"
        write_raster(output, sediment, profile)
        rows.append(
            {
                "boundary_id": boundary_id,
                "experiment_id": experiment_id,
                "scenario_id": scenario_id,
                "path": rel(output),
                "formula": "sediment_scenario = soil_erosion_factors * R_mean",
                "r_source_key": record["r_source_key"],
                "r_mean": r_mean,
                "claim_level": record["claim_level"],
                "role": record["role"],
                "use_as_default": record["use_as_default"],
                "nodata_policy": "inherits soil_erosion_factors mask; no zero fill",
                "notes": record["notes"],
                **stats(sediment),
            }
        )

    write_csv(OUT_DIR / "r_factor_sensitivity_summary.csv", rows)
    print(f"wrote {boundary_id} / {experiment_id} to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
