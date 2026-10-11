#!/usr/bin/env python3
"""Run priority scenarios for zimbabwe_upper_mzingwane repaired criteria stack.

Produces provisional priority rasters under three weight scenarios (equal-core,
mentor-slide-mapped default, mining/exposure stress), plus a mean/std/top-20%
priority-selection-stability board. All outputs are `provisional` or
`sensitivity_scenario` under the execution status policy, not final flood-risk
or intervention claims.

Sediment/erosion criterion note: `soil_erosion_factors` is the standardized
K x LS x C erosion-source structure criterion. It does not include a rainfall
erosivity scalar and must not be read as absolute soil loss.
"""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/flood_conditioning_factors_0_1.tif", ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/soil_erosion_factors_0_1.tif", ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/land_cover_pressure_0_1.tif", ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/mining_pressure_0_1.tif", ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/exposure_indicators_0_1.tif", ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif", ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/zimbabwe_pim_scenarios/priority_scenarios_v0_2/priority_mean.tif", ROOT / "outputs/zimbabwe_pim_scenarios/priority_scenarios_v0_2/top20_frequency.tif", ROOT / "outputs/zimbabwe_pim_scenarios/priority_scenarios_v0_2/hotspot_stability_summary.csv"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
from _lib.standardization import ensure_unit_interval
BOUNDARY_ID = "zimbabwe_upper_mzingwane"
OUTPUT_ROOT_ID = "zimbabwe_pim_scenarios"  # outputs folder name (differs from the id since 2026-10-11 rename)
EXPERIMENT_ID = "priority_scenarios_v0_2"
CRITERIA_ID = "criteria_stack"
OUT_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"
CRITERIA_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/{CRITERIA_ID}/criteria"
REF = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"

CRITERIA_PATHS = {
    "flood_conditioning_factors": CRITERIA_DIR / "flood_conditioning_factors_0_1.tif",
    "soil_erosion_factors": CRITERIA_DIR / "soil_erosion_factors_0_1.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "mining_pressure": CRITERIA_DIR / "mining_pressure_0_1.tif",
    "river_proximity_indicators": CRITERIA_DIR / "river_proximity_indicators_0_1.tif",
    "exposure_indicators": CRITERIA_DIR / "exposure_indicators_0_1.tif",
}

SLIDE_MATRIX = np.array(
    [
        [1, 3, 5, 4, 6],
        [1 / 3, 1, 3, 2, 4],
        [1 / 5, 1 / 3, 1, 1 / 2, 2],
        [1 / 4, 1 / 2, 2, 1, 3],
        [1 / 6, 1 / 4, 1 / 2, 1 / 3, 1],
    ],
    dtype="float64",
)
SLIDE_ORDER = ["flood", "sediment", "landuse_asm", "environmental", "socioeconomic"]


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


normalize_if_needed = ensure_unit_interval
def ahp_slide_weights() -> tuple[dict[str, float], float]:
    vals, vecs = np.linalg.eig(SLIDE_MATRIX)
    idx = int(np.argmax(vals.real))
    lam = float(vals.real[idx])
    weights = np.abs(vecs[:, idx].real)
    weights = weights / weights.sum()
    ci = (lam - len(SLIDE_ORDER)) / (len(SLIDE_ORDER) - 1)
    cr = ci / 1.12
    base = {name: float(weight) for name, weight in zip(SLIDE_ORDER, weights, strict=True)}
    landuse_half = base["landuse_asm"] / 2.0
    return (
        {
            "flood_conditioning_factors": base["flood"],
            "soil_erosion_factors": base["sediment"],
            "land_cover_pressure": landuse_half,
            "mining_pressure": landuse_half,
            "river_proximity_indicators": base["environmental"],
            "exposure_indicators": base["socioeconomic"],
        },
        float(cr),
    )


def scenario_weights() -> tuple[dict[str, dict[str, float]], float]:
    slide, cr = ahp_slide_weights()
    return (
        {
            "equal_core": {
                "flood_conditioning_factors": 0.25,
                "soil_erosion_factors": 0.25,
                "land_cover_pressure": 0.25,
                "mining_pressure": 0.25,
            },
            "default_weighted": slide,
            "mining_exposure_stress": {
                "flood_conditioning_factors": 0.25,
                "soil_erosion_factors": 0.20,
                "land_cover_pressure": 0.10,
                "mining_pressure": 0.25,
                "river_proximity_indicators": 0.05,
                "exposure_indicators": 0.15,
            },
        },
        cr,
    )


def classify_quantiles(data: np.ndarray) -> np.ndarray:
    values = data[np.isfinite(data)]
    breaks = np.nanpercentile(values, [20, 40, 60, 80])
    classes = np.digitize(data, breaks, right=True).astype("float32") + 1
    classes[~np.isfinite(data)] = np.nan
    return classes


def raster_stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "p50": round(float(np.percentile(values, 50)), 6),
        "p80": round(float(np.percentile(values, 80)), 6),
        "p95": round(float(np.percentile(values, 95)), 6),
        "max": round(float(values.max()), 6),
    }


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.08)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label(label, fontsize=8)


def plot_board(priority_mean: np.ndarray, top20_frequency: np.ndarray, mentor_score: np.ndarray, profile: dict) -> None:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(profile["crs"])
    boundary["geometry"] = boundary.geometry.scale(xfact=0.001, yfact=0.001, origin=(0, 0))
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0] / 1000, bounds[2] / 1000, bounds[1] / 1000, bounds[3] / 1000)

    fig, axes = plt.subplots(1, 3, figsize=(16.2, 4.9), constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=0.12, h_pad=0.08, wspace=0.18, hspace=0.02)
    panels = [
        ("A. Mean priority score across scenarios", priority_mean, "YlOrRd", "0-1 priority score"),
        ("B. Candidate AHP-weighted priority score", mentor_score, "YlOrRd", "0-1 priority score"),
        ("C. Top-20% priority selection frequency", top20_frequency, "Blues", "selection frequency"),
    ]
    for ax, (title, data, cmap, label) in zip(axes, panels, strict=True):
        image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.9)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32735)", fontsize=8)
        ax.set_ylabel("Northing (km)", fontsize=8)
        ax.grid(color="0.9", linewidth=0.4)
        ax.tick_params(labelsize=7)
        add_colorbar(fig, ax, image, label)
    fig.suptitle("Upper Mzingwane Catchment: Prototype Flood-Priority Screening", fontsize=13, fontweight="bold")
    fig.savefig(OUT_DIR / "priority_scenarios_board.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "priority_scenarios_board.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    opts = parse_script_args(boundary_id=BOUNDARY_ID, experiment_id=EXPERIMENT_ID)
    boundary_id = opts.get("boundary_id", BOUNDARY_ID)
    experiment_id = opts.get("experiment_id", EXPERIMENT_ID)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()
    criteria = {
        name: ensure_unit_interval(read_band(path, profile), name=name)
        for name, path in CRITERIA_PATHS.items()
    }
    scenarios, ahp_cr = scenario_weights()

    scenario_arrays: dict[str, np.ndarray] = {}
    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    top20_masks: list[np.ndarray] = []
    valid_any = np.logical_or.reduce([np.isfinite(arr) for arr in criteria.values()])

    for scenario, weights in scenarios.items():
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
            weight_rows.append(
                {
                    "boundary_id": boundary_id,
                    "experiment_id": experiment_id,
                    "scenario": scenario,
                    "criterion": criterion,
                    "weight": round(weight, 8),
                    "claim_level": "provisional" if scenario != "mining_exposure_stress" else "sensitivity_scenario",
                }
            )
        score = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
        score[~valid_any] = np.nan
        score = np.clip(score, 0.0, 1.0).astype("float32")
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}.tif", score, profile)
        write_raster(SCENARIO_DIR / f"priority_{scenario}_class_1_5.tif", classify_quantiles(score), profile, dtype="uint8", nodata=0)
        threshold = float(np.nanpercentile(score, 80))
        top20 = score >= threshold
        top20_masks.append(top20)
        summary_rows.append(
            {
                "boundary_id": boundary_id,
                "experiment_id": experiment_id,
                "scenario": scenario,
                "top20_threshold": round(threshold, 6),
                **raster_stats(score),
            }
        )

    stack = np.stack(list(scenario_arrays.values())).astype("float32")
    finite_count = np.sum(np.isfinite(stack), axis=0)
    valid_stack = np.isfinite(stack)
    stack_zero = np.where(valid_stack, stack, 0.0)
    priority_mean = np.divide(
        np.sum(stack_zero, axis=0),
        finite_count,
        out=np.full(stack.shape[1:], np.nan, dtype="float32"),
        where=finite_count > 0,
    ).astype("float32")
    centered = np.where(valid_stack, stack - priority_mean[None, :, :], 0.0)
    priority_std = np.sqrt(
        np.divide(
            np.sum(centered * centered, axis=0),
            finite_count,
            out=np.full(stack.shape[1:], np.nan, dtype="float32"),
            where=finite_count > 0,
        )
    ).astype("float32")
    top20_frequency = np.mean(np.stack(top20_masks), axis=0).astype("float32")
    priority_mean[finite_count == 0] = np.nan
    priority_std[finite_count == 0] = np.nan
    top20_frequency[finite_count == 0] = np.nan

    write_raster(OUT_DIR / "priority_mean.tif", priority_mean, profile)
    write_raster(OUT_DIR / "priority_std.tif", priority_std, profile)
    write_raster(OUT_DIR / "top20_frequency.tif", top20_frequency, profile)
    plot_board(priority_mean, top20_frequency, scenario_arrays["default_weighted"], profile)

    stability_rows = [
        {"metric": "scenario_count", "value": len(scenarios)},
        {"metric": "mentor_slide_consistency_ratio", "value": round(ahp_cr, 6)},
        {"metric": "top20_all_scenarios_cells", "value": int(np.nansum(top20_frequency == 1.0))},
        {"metric": "top20_any_scenario_cells", "value": int(np.nansum(top20_frequency > 0.0))},
        {"metric": "top20_all_scenarios_area_km2", "value": round(float(np.nansum(top20_frequency == 1.0) * 0.0009), 3)},
        {"metric": "top20_any_scenario_area_km2", "value": round(float(np.nansum(top20_frequency > 0.0) * 0.0009), 3)},
        {"metric": "priority_std_mean", "value": round(float(np.nanmean(priority_std)), 6)},
        {"metric": "priority_std_p95", "value": round(float(np.nanpercentile(priority_std, 95)), 6)},
    ]
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "hotspot_stability_summary.csv", stability_rows)
    print(f"wrote {boundary_id} / {experiment_id} to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
