#!/usr/bin/env python3
"""Run boundary_v1 priority scenarios as a PIM 5-main-criterion overlay.

This experiment keeps the mentor AHP main criteria as Flood, Sediment,
Land Use / ASM, Environmental, and Socioeconomic. Five criteria are actively
scored in the current executable prototype:

- Flood hazard: flood-conditioning factors + rainfall climatology.
- Sediment: soil-erosion factors.
- Land Use / ASM: land-cover pressure + mining pressure.
- Environmental: water/wetland and protected-area sensitivity indicator.
- Socioeconomic: exposure/access indicators.
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
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/flood_conditioning_factors_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/soil_erosion_factors_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/land_cover_pressure_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/mining_pressure_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/exposure_indicators_0_1.tif", ROOT / "outputs/boundary_v1/rainfall_sensitivity_v0_3/criteria/rainfall_climatology_0_1_PROVISIONAL_30m.tif", ROOT / "outputs/boundary_v1/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif", ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif", ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/priority_mean.tif", ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/top20_frequency.tif", ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/hotspot_stability_summary.csv"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "rainfall_exposure_v0_4"
OUT_DIR = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"
PIM_CRITERIA_DIR = OUT_DIR / "pim_criteria"

REF = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
CRITERIA_DIR = ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria"
RAINFALL_DIR = ROOT / "outputs/boundary_v1/rainfall_sensitivity_v0_3/criteria"

COMPONENT_PATHS = {
    "flood_conditioning_factors": CRITERIA_DIR / "flood_conditioning_factors_0_1.tif",
    "soil_erosion_factors": CRITERIA_DIR / "soil_erosion_factors_0_1.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "mining_pressure": CRITERIA_DIR / "mining_pressure_0_1.tif",
    "exposure_indicators": CRITERIA_DIR / "exposure_indicators_0_1.tif",
    "rainfall_climatology": RAINFALL_DIR / "rainfall_climatology_0_1_PROVISIONAL_30m.tif",
    "environmental_sensitivity": ROOT / "outputs/boundary_v1/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif",
}

PIM_CRITERIA_ORDER = ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"]
ACTIVE_PIM_CRITERIA = PIM_CRITERIA_ORDER
PIM_COMPONENTS = {
    "flood_hazard": {"flood_conditioning_factors": 0.5, "rainfall_climatology": 0.5},
    "sediment": {"soil_erosion_factors": 1.0},
    "landuse_asm": {"land_cover_pressure": 0.5, "mining_pressure": 0.5},
    "environmental": {"environmental_sensitivity": 1.0},
    "socioeconomic": {"exposure_indicators": 1.0},
}
SLIDE_MATRIX = np.array([
    [1, 3, 5, 4, 6],
    [1/3, 1, 3, 2, 4],
    [1/5, 1/3, 1, 1/2, 2],
    [1/4, 1/2, 2, 1, 3],
    [1/6, 1/4, 1/2, 1/3, 1],
], dtype="float64")
CELL_AREA_KM2 = 0.0009
CLAIM_NOTE = (
    "SENSITIVITY SCENARIO: boundary_v1 prototype overlay under the mentor "
    "5-criterion AHP framework. Environmental sensitivity is provisional "
    "water/wetland and protected-area context. Not a validated flood-risk or "
    "intervention-priority map."
)


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


def read_boundary_mask(profile: dict) -> np.ndarray:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(profile["crs"])
    from rasterio.features import geometry_mask

    return geometry_mask(
        boundary.geometry,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        invert=True,
    )


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


def normalize_if_needed(data: np.ndarray) -> np.ndarray:
    values = data[np.isfinite(data)]
    if values.size == 0:
        raise ValueError("empty criterion")
    if float(values.max()) <= 1.000001 and float(values.min()) >= -0.000001:
        return np.clip(data, 0.0, 1.0).astype("float32")
    max_value = float(values.max())
    if max_value <= 0:
        raise ValueError("non-positive criterion range")
    return np.clip(data / max_value, 0.0, 1.0).astype("float32")
def slide_weights_available_pim() -> tuple[dict[str, float], float]:
    vals, vecs = np.linalg.eig(SLIDE_MATRIX)
    idx = int(np.argmax(vals.real))
    lam = float(vals.real[idx])
    weights = np.abs(vecs[:, idx].real)
    weights = weights / weights.sum()
    ci = (lam - len(PIM_CRITERIA_ORDER)) / (len(PIM_CRITERIA_ORDER) - 1)
    cr = ci / 1.12
    raw = dict(zip(PIM_CRITERIA_ORDER, weights.tolist(), strict=True))
    available_total = sum(raw[name] for name in ACTIVE_PIM_CRITERIA)
    return {
        name: raw[name] / available_total
        for name in ACTIVE_PIM_CRITERIA
    }, float(cr)


def scenario_weights() -> tuple[dict[str, dict[str, float]], float]:
    slide_weights, slide_cr = slide_weights_available_pim()
    return {
        "equal_active_pim": {name: 1 / len(ACTIVE_PIM_CRITERIA) for name in ACTIVE_PIM_CRITERIA},
        "mentor_slide_available_pim": slide_weights,
        "flood_sediment_heavy_pim": {
            "flood_hazard": 0.30,
            "sediment": 0.25,
            "landuse_asm": 0.20,
            "environmental": 0.10,
            "socioeconomic": 0.15,
        },
    }, slide_cr


def combine_weighted_layers(
    source_layers: dict[str, np.ndarray],
    component_weights: dict[str, float],
) -> np.ndarray:
    first = next(iter(source_layers.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    valid_all = np.ones(first.shape, dtype=bool)
    total_weight = float(sum(component_weights.values()))
    for component, weight in component_weights.items():
        layer = source_layers[component]
        valid = np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        valid_all &= valid
    combined = np.full(first.shape, np.nan, dtype="float32")
    combined[valid_all] = numerator[valid_all] / total_weight
    return np.clip(combined, 0.0, 1.0).astype("float32")


def build_pim_criteria(components: dict[str, np.ndarray], profile: dict) -> dict[str, np.ndarray]:
    PIM_CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    criteria = {
        name: combine_weighted_layers(components, weights)
        for name, weights in PIM_COMPONENTS.items()
    }
    for name, data in criteria.items():
        write_raster(PIM_CRITERIA_DIR / f"{name}_0_1.tif", data, profile)
    return criteria


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
    cb.ax.tick_params(labelsize=8)
    cb.set_label(label, fontsize=9)


def plot_board(priority_mean: np.ndarray, top20_frequency: np.ndarray, profile: dict) -> None:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0], bounds[2], bounds[1], bounds[3])

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2), constrained_layout=True)
    panels = [
        ("A. Mean priority across PIM scenarios", priority_mean, "YlOrRd", "0-1 priority"),
        ("B. Top-20% hotspot frequency", top20_frequency, "Blues", "top-20% frequency"),
    ]
    km_formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
    for ax, (title, data, cmap, label) in zip(axes, panels, strict=True):
        image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.8)
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32735)", fontsize=9)
        ax.set_ylabel("Northing (km)", fontsize=9)
        ax.xaxis.set_major_formatter(km_formatter)
        ax.yaxis.set_major_formatter(km_formatter)
        ax.tick_params(labelsize=8)
        ax.grid(color="0.9", linewidth=0.35)
        add_colorbar(fig, ax, image, label)
    fig.suptitle(
        "Zimbabwe Upper Mzingwane: PIM 5-criterion framework / provisional ES",
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(OUT_DIR / "rainfall_exposure_v0_4_board.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "rainfall_exposure_v0_4_board.pdf", bbox_inches="tight")
    plt.close(fig)


def build_grid_check(profile: dict, criteria: dict[str, np.ndarray]) -> list[dict[str, object]]:
    rows = []
    for name, data in criteria.items():
        values = data[np.isfinite(data)]
        rows.append({
            "criterion": name,
            "grid_compatible": True,
            "crs": str(profile["crs"]),
            "width": profile["width"],
            "height": profile["height"],
            "valid_cells": int(values.size),
            "valid_fraction": round(float(values.size / data.size), 6),
            "min": round(float(values.min()), 6),
            "mean": round(float(values.mean()), 6),
            "max": round(float(values.max()), 6),
        })
    return rows


def write_handoff(summary: dict[str, object]) -> None:
    text = f"""# boundary_v1 / rainfall_exposure_v0_4

Date: 2026-06-30

Status: `sensitivity_scenario`.

This run follows the mentor's 5 AHP main-criterion framework and keeps the
current executable overlay aligned to active PIM main criteria.

## Mentor AHP main criteria

1. Flood (FH)
2. Sediment (SR)
3. Land Use / ASM (LU)
4. Environmental (ES)
5. Socioeconomic (SV)

## Active scored PIM criteria

1. flood_hazard = flood_conditioning_factors + rainfall_climatology
2. sediment = soil_erosion_factors
3. landuse_asm = land_cover_pressure + mining_pressure
4. environmental = water/wetland context + protected-area proximity
5. socioeconomic = exposure_indicators

## Headline result

- Stable top-20% hotspot area across all three PIM scenarios:
  {summary['stable_area_km2']} km2.
- Top-20% in at least one scenario: {summary['any_area_km2']} km2.

## Limits

- Rainfall is CHIRPS coarse-to-grid context, not native 30 m rainfall.
- Road accessibility is an exposure/access indicator, not observed vulnerability.
- This is not a validated flood-risk map and not an intervention-priority map.
"""
    (OUT_DIR / "handoff.md").write_text(text, encoding="utf-8")


def main() -> None:
    opts = parse_script_args(boundary_id=BOUNDARY_ID, experiment_id=EXPERIMENT_ID,
                             description="Run boundary_v1 PIM 5-main-criterion priority scenarios.")
    boundary_id = opts.get("boundary_id", BOUNDARY_ID)
    experiment_id = opts.get("experiment_id", EXPERIMENT_ID)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()
    components = {
        name: normalize_if_needed(read_band(path, profile))
        for name, path in COMPONENT_PATHS.items()
    }
    criteria = build_pim_criteria(components, profile)
    scenarios, slide_cr = scenario_weights()
    boundary_mask = read_boundary_mask(profile)
    common_valid = boundary_mask.copy()
    for layer in criteria.values():
        common_valid &= np.isfinite(layer)
    common_valid_fraction = float(common_valid.sum() / boundary_mask.sum())

    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    scenario_arrays: dict[str, np.ndarray] = {}
    top20_masks: list[np.ndarray] = []

    for scenario, weights in scenarios.items():
        if round(sum(weights.values()), 10) != 1.0:
            raise ValueError(f"weights do not sum to 1 for {scenario}")
        numerator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        for criterion, weight in weights.items():
            layer = criteria[criterion]
            numerator[common_valid] += layer[common_valid] * weight
            weight_rows.append({
                "boundary_id": boundary_id,
                "experiment_id": experiment_id,
                "scenario": scenario,
                "criterion": criterion,
                "weight": round(weight, 8),
                "claim_level": "sensitivity_scenario",
            })
        score = np.full_like(numerator, np.nan, dtype="float32")
        score[common_valid] = numerator[common_valid]
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}.tif", score, profile)

        values = score[np.isfinite(score)]
        threshold = float(np.percentile(values, 80))
        top20_masks.append(score >= threshold)
        summary_rows.append({
            "boundary_id": boundary_id,
            "experiment_id": experiment_id,
            "scenario": scenario,
            "top20_threshold": round(threshold, 6),
            "common_valid_fraction": round(common_valid_fraction, 6),
            **raster_stats(score),
        })

    stack = np.stack([arr for arr in scenario_arrays.values()])
    stack_valid = np.any(np.isfinite(stack), axis=0)
    priority_mean = np.full(stack.shape[1:], np.nan, dtype="float32")
    priority_std = np.full(stack.shape[1:], np.nan, dtype="float32")
    priority_mean[stack_valid] = np.nanmean(stack[:, stack_valid], axis=0).astype("float32")
    priority_std[stack_valid] = np.nanstd(stack[:, stack_valid], axis=0).astype("float32")
    top20_frequency = np.mean(np.stack(top20_masks).astype("float32"), axis=0)
    top20_frequency[~np.isfinite(priority_mean)] = np.nan

    write_raster(OUT_DIR / "priority_mean.tif", priority_mean, profile)
    write_raster(OUT_DIR / "priority_std.tif", priority_std, profile)
    write_raster(OUT_DIR / "top20_frequency.tif", top20_frequency.astype("float32"), profile)
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "component_grid_check.csv", build_grid_check(profile, components))
    write_csv(OUT_DIR / "pim_criteria_grid_check.csv", build_grid_check(profile, criteria))

    all_mask = np.all(np.stack(top20_masks), axis=0)
    any_mask = np.any(np.stack(top20_masks), axis=0)
    hotspot_summary = {
        "scenario_count": len(scenarios),
        "mentor_slide_consistency_ratio": round(slide_cr, 6),
        "pim_main_criteria_count": len(PIM_CRITERIA_ORDER),
        "active_scored_pim_criteria_count": len(ACTIVE_PIM_CRITERIA),
        "component_layer_count": len(COMPONENT_PATHS),
        "common_valid_fraction": round(common_valid_fraction, 6),
        "top20_all_scenarios_cells": int(all_mask.sum()),
        "top20_any_scenario_cells": int(any_mask.sum()),
        "stable_area_km2": round(float(all_mask.sum() * CELL_AREA_KM2), 3),
        "any_area_km2": round(float(any_mask.sum() * CELL_AREA_KM2), 3),
        "active_scored_pim_criteria": ", ".join(ACTIVE_PIM_CRITERIA),
        "component_layers": ", ".join(COMPONENT_PATHS),
        "environmental_sensitivity_status": "provisional",
    }
    write_csv(
        OUT_DIR / "hotspot_stability_summary.csv",
        [{"metric": key, "value": value} for key, value in hotspot_summary.items()],
    )
    plot_board(priority_mean, top20_frequency, profile)
    write_handoff(hotspot_summary)
    print(f"Wrote {experiment_id} outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
