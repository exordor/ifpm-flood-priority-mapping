#!/usr/bin/env python3
"""Run priority scenarios for the PE1 engineering-pilot criteria stack.

Mirrors `run_boundary_v1_priority_scenarios.py` but for PE1's 3 available criteria
(flood_hazard, erosion_structure, land_cover). No mining/exposure criteria because no Peru
OSM/INGEMMET data has been processed yet.

Sediment normalization note: the erosion_structure criterion is max-normalized to [0,1] for
MCDA scoring, so its 0-1 value is a relative hotspot intensity, not absolute t/ha/yr. Rank is
R-invariant.

Outputs (gitignored under outputs/srtm_1arcsec_peru_pilot/priority_scenarios/):
priority mean/std/top20-frequency rasters, per-scenario rasters, weights + summary CSVs,
and a board figure. All provisional / engineering_pilot.
"""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_ID = "pe1"
EXPERIMENT_ID = "priority_scenarios"
OUT_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"
CRITERIA_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"

CRITERIA_PATHS = {
    "flood_hazard_proxy": CRITERIA_DIR / "flood_hazard_proxy_0_1.tif",
    "erosion_structure_proxy": CRITERIA_DIR / "erosion_structure_proxy_0_1.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
}

# Two scenarios: equal-weight (neutral) and hazard-erosion heavy (stress test for flood+sedi).
# No AHP slide scenario because the mentor slide matrix has 5 criteria; PE1 only has 3.
SCENARIOS = {
    "equal": {
        "flood_hazard_proxy": 1 / 3,
        "erosion_structure_proxy": 1 / 3,
        "land_cover_pressure": 1 / 3,
    },
    "flood_erosion_heavy": {
        "flood_hazard_proxy": 0.45,
        "erosion_structure_proxy": 0.45,
        "land_cover_pressure": 0.10,
    },
}


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


def read_reference() -> dict:
    with rasterio.open(REF) as ref:
        return ref.profile.copy()


def read_band(path: Path, profile: dict) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        if src.crs != profile["crs"] or src.transform != profile["transform"]:
            raise ValueError(f"grid mismatch: {path}")
        if src.width != profile["width"] or src.height != profile["height"]:
            raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def write_raster(path: Path, data: np.ndarray, profile: dict, dtype: str = "float32", nodata=-9999.0) -> None:
    out_profile = profile.copy()
    out_profile.update(driver="GTiff", count=1, dtype=dtype, nodata=nodata, compress="deflate", tiled=True)
    encoded = np.where(np.isfinite(data), data, nodata).astype(dtype)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(encoded, 1)


def raster_stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6) if values.size else "",
        "mean": round(float(values.mean()), 6) if values.size else "",
        "p50": round(float(np.percentile(values, 50)), 6) if values.size else "",
        "p95": round(float(np.percentile(values, 95)), 6) if values.size else "",
        "max": round(float(values.max()), 6) if values.size else "",
    }


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.04)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label(label, fontsize=8)


def plot_board(priority_mean, top20_frequency, equal_score, profile) -> None:
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0] / 1000, bounds[2] / 1000, bounds[1] / 1000, bounds[3] / 1000)

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), constrained_layout=True)
    panels = [
        ("A. Mean priority across scenarios", priority_mean, "YlOrRd", "0-1 score"),
        ("B. Equal-weight scenario", equal_score, "YlOrRd", "0-1 score"),
        ("C. Top-20% hotspot frequency", top20_frequency, "Blues", "frequency"),
    ]
    for ax, (title, data, cmap, label) in zip(axes, panels, strict=True):
        image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.9)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32718)", fontsize=8)
        ax.set_ylabel("Northing (km)", fontsize=8)
        ax.grid(color="0.9", linewidth=0.4)
        ax.tick_params(labelsize=7)
        add_colorbar(fig, ax, image, label)
    fig.suptitle("PE1 (Peru engineering pilot) / priority scenarios: provisional hotspot map",
                 fontsize=12, fontweight="bold")
    fig.savefig(OUT_DIR / "pe1_priority_scenarios_board.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "pe1_priority_scenarios_board.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()
    criteria = {name: read_band(path, profile) for name, path in CRITERIA_PATHS.items()}

    scenario_arrays: dict[str, np.ndarray] = {}
    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    top20_masks: list[np.ndarray] = []
    valid_any = np.logical_or.reduce([np.isfinite(arr) for arr in criteria.values()])

    for scenario, weights in SCENARIOS.items():
        total = round(sum(weights.values()), 10)
        if total != 1.0:
            raise ValueError(f"weights for {scenario} sum to {total}")
        numerator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        denominator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        for criterion, weight in weights.items():
            layer = criteria[criterion]
            valid = np.isfinite(layer)
            numerator[valid] += layer[valid] * weight
            denominator[valid] += weight
            weight_rows.append({
                "boundary_id": BOUNDARY_ID, "experiment_id": EXPERIMENT_ID,
                "scenario": scenario, "criterion": criterion,
                "weight": round(weight, 8), "claim_level": "provisional",
            })
        score = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
        score[~valid_any] = np.nan
        score = np.clip(score, 0.0, 1.0).astype("float32")
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}.tif", score, profile)
        threshold = float(np.nanpercentile(score, 80))
        top20_masks.append(score >= threshold)
        summary_rows.append({
            "boundary_id": BOUNDARY_ID, "experiment_id": EXPERIMENT_ID,
            "scenario": scenario, "top20_threshold": round(threshold, 6),
            **raster_stats(score),
        })

    stack = np.stack(list(scenario_arrays.values())).astype("float32")
    finite_count = np.sum(np.isfinite(stack), axis=0)
    valid_stack = np.isfinite(stack)
    stack_zero = np.where(valid_stack, stack, 0.0)
    priority_mean = np.divide(np.sum(stack_zero, axis=0), finite_count,
                              out=np.full(stack.shape[1:], np.nan, dtype="float32"), where=finite_count > 0).astype("float32")
    centered = np.where(valid_stack, stack - priority_mean[None, :, :], 0.0)
    priority_std = np.sqrt(np.divide(np.sum(centered * centered, axis=0), finite_count,
                                     out=np.full(stack.shape[1:], np.nan, dtype="float32"), where=finite_count > 0)).astype("float32")
    top20_frequency = np.mean(np.stack(top20_masks), axis=0).astype("float32")
    for arr in (priority_mean, priority_std, top20_frequency):
        arr[finite_count == 0] = np.nan

    write_raster(OUT_DIR / "priority_mean.tif", priority_mean, profile)
    write_raster(OUT_DIR / "priority_std.tif", priority_std, profile)
    write_raster(OUT_DIR / "top20_frequency.tif", top20_frequency, profile)
    plot_board(priority_mean, top20_frequency, scenario_arrays["equal"], profile)

    cell_km2 = 30.0 * 30.0 / 1e6
    stability_rows = [
        {"metric": "scenario_count", "value": len(SCENARIOS)},
        {"metric": "top20_all_scenarios_cells", "value": int(np.nansum(top20_frequency == 1.0))},
        {"metric": "top20_any_scenario_cells", "value": int(np.nansum(top20_frequency > 0.0))},
        {"metric": "top20_all_scenarios_area_km2", "value": round(float(np.nansum(top20_frequency == 1.0) * cell_km2), 3)},
        {"metric": "top20_any_scenario_area_km2", "value": round(float(np.nansum(top20_frequency > 0.0) * cell_km2), 3)},
        {"metric": "priority_std_mean", "value": round(float(np.nanmean(priority_std)), 6)},
        {"metric": "priority_std_p95", "value": round(float(np.nanpercentile(priority_std, 95)), 6)},
        {"metric": "zimbabwe_v1_top20_all_ref_km2", "value": 431.907},
        {"metric": "criteria_count", "value": len(CRITERIA_PATHS)},
        {"metric": "missing_criteria", "value": "mining_pressure, socioeconomic_exposure (no Peru OSM/INGEMMET yet)"},
    ]
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "hotspot_stability_summary.csv", stability_rows)
    print(f"wrote PE1 priority scenarios to {rel(OUT_DIR)}")
    print(f"  top-20% stable across all scenarios: {stability_rows[3]['value']} km2")
    print(f"  (Zimbabwe V1 ref: 431.907 km2; PE1 uses 3 criteria, ZW v0.2 used 4-6)")


if __name__ == "__main__":
    main()
