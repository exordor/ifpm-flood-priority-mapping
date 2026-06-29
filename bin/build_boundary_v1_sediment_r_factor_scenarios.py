#!/usr/bin/env python3
"""Build provisional LOW/HIGH R sediment scenarios for boundary_v1."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "sediment_r_factor_scenarios"
CONFIG = ROOT / "context/configs/boundary_v1_sediment_r_factor_scenarios.csv"
STRUCTURE = ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/erosion_structure_proxy_0_1.tif"
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
        raise FileNotFoundError(f"Missing erosion structure proxy: {STRUCTURE}")
    with rasterio.open(STRUCTURE) as src:
        data = src.read(1).astype("float32")
        profile = src.profile.copy()
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data, profile


def write_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    out_profile = profile.copy()
    out_profile.update(driver="GTiff", count=1, dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)
    encoded = np.where(np.isfinite(data), data, -9999.0).astype("float32")
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(encoded, 1)


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
                "boundary_id": BOUNDARY_ID,
                "experiment_id": EXPERIMENT_ID,
                "scenario_id": scenario_id,
                "path": rel(output),
                "formula": "sediment_scenario = erosion_structure_proxy * R_mean",
                "r_source_key": record["r_source_key"],
                "r_mean": r_mean,
                "claim_level": record["claim_level"],
                "role": record["role"],
                "use_as_default": record["use_as_default"],
                "nodata_policy": "inherits erosion_structure_proxy mask; no zero fill",
                "notes": record["notes"],
                **stats(sediment),
            }
        )

    write_csv(OUT_DIR / "r_factor_sensitivity_summary.csv", rows)
    print(f"wrote {BOUNDARY_ID} / {EXPERIMENT_ID} to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
