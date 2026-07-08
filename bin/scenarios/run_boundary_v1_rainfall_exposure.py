#!/usr/bin/env python3
"""Run boundary_v1 priority scenarios as a secondary Zimbabwe PIM overlay.

This experiment keeps the five PIM main criteria as Flood, Sediment, Land
Use / ASM, Environmental, and Socioeconomic. Zimbabwe is secondary/background
after the Peru-first decision, but this run records the latest direct
Zimbabwe weights for the Upper Mzingwane catchment:

- Flood hazard: rainfall climatology, TWI, and drainage proximity.
- Sediment: current K x LS x C erosion-source structure. K/LS/C local
  subweights are recorded as a data gap because K is not currently an
  independently weighted grid-compatible 30 m layer.
- Land Use / ASM: land-cover pressure + mining pressure.
- Environmental: water/wetland and protected-area sensitivity indicator.
- Socioeconomic: road/access exposure indicator; independent infrastructure
  exposure is explicitly unavailable in the current run.

Current scenarios: equal baseline and Zimbabwe direct recommended weights.
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
INPUTS = [ROOT / "outputs/boundary_v1/rainfall_sensitivity_v0_3/criteria/rainfall_climatology_0_1_PROVISIONAL_30m.tif", ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization/v1_twi_high_wetness_0_1.tif", ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization/v1_drainage_proximity_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/soil_erosion_factors_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/land_cover_pressure_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/mining_pressure_0_1.tif", ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/exposure_indicators_0_1.tif", ROOT / "outputs/boundary_v1/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif", ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif", ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"]
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
HYDROLOGY_STANDARDIZATION_DIR = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization"

COMPONENT_PATHS = {
    "rainfall_climatology": RAINFALL_DIR / "rainfall_climatology_0_1_PROVISIONAL_30m.tif",
    "twi_wetness": HYDROLOGY_STANDARDIZATION_DIR / "v1_twi_high_wetness_0_1.tif",
    "drainage_proximity": HYDROLOGY_STANDARDIZATION_DIR / "v1_drainage_proximity_0_1.tif",
    "soil_erosion_factors": CRITERIA_DIR / "soil_erosion_factors_0_1.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "mining_pressure": CRITERIA_DIR / "mining_pressure_0_1.tif",
    "exposure_indicators": CRITERIA_DIR / "exposure_indicators_0_1.tif",
    "environmental_sensitivity": ROOT / "outputs/boundary_v1/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif",
}

PIM_CRITERIA_ORDER = ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"]
ACTIVE_PIM_CRITERIA = PIM_CRITERIA_ORDER
PIM_COMPONENTS = {
    "flood_hazard": {"rainfall_climatology": 0.35, "twi_wetness": 0.30, "drainage_proximity": 0.35},
    "sediment": {"soil_erosion_factors": 1.0},
    "landuse_asm": {"land_cover_pressure": 0.40, "mining_pressure": 0.60},
    "environmental": {"environmental_sensitivity": 1.0},
    "socioeconomic": {"exposure_indicators": 1.0},
}
ZIMBABWE_MENTOR_MAIN_WEIGHTS = {
    "flood_hazard": 0.32,
    "sediment": 0.23,
    "landuse_asm": 0.18,
    "environmental": 0.12,
    "socioeconomic": 0.15,
}
SCENARIOS = {
    "equal_active_pim": {name: 1 / len(ACTIVE_PIM_CRITERIA) for name in ACTIVE_PIM_CRITERIA},
    "mentor_zimbabwe_direct_pim": ZIMBABWE_MENTOR_MAIN_WEIGHTS,
}
CELL_AREA_KM2 = 0.0009
CLAIM_NOTE = (
    "SENSITIVITY SCENARIO: boundary_v1 secondary Zimbabwe prototype overlay "
    "under the 5-criterion AHP framework. Environmental sensitivity is "
    "provisional water/wetland and protected-area context. Not a validated "
    "flood-risk or intervention-priority map."
)


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


def clear_previous_scenario_rasters() -> None:
    for path in SCENARIO_DIR.glob("priority_*.tif"):
        path.unlink()


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
        ("B. Top-20% priority selection frequency", top20_frequency, "Blues", "selection frequency"),
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


def build_subcriteria_weight_rows() -> list[dict[str, object]]:
    rows = [
        {
            "pim_criterion": "flood_hazard",
            "component": "rainfall_climatology",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["rainfall_climatology"]),
            "note": "CHIRPS rainy-season climatology, coarse-to-reference-grid sensitivity layer",
        },
        {
            "pim_criterion": "flood_hazard",
            "component": "twi_wetness",
            "suggested_local_weight": 0.30,
            "applied_weight_in_current_run": 0.30,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["twi_wetness"]),
            "note": "DEM-derived TWI, high wetness -> high flood-conditioning score",
        },
        {
            "pim_criterion": "flood_hazard",
            "component": "drainage_proximity",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["drainage_proximity"]),
            "note": "distance to drainage, closer -> higher flood-conditioning score",
        },
        {
            "pim_criterion": "sediment",
            "component": "soil_erosion_factors",
            "suggested_local_weight": "",
            "applied_weight_in_current_run": 1.00,
            "implementation_status": "implemented_as_current_composite",
            "source_layer": rel(COMPONENT_PATHS["soil_erosion_factors"]),
            "note": "current executable sediment criterion: standardized K x LS x C erosion-source structure",
        },
        {
            "pim_criterion": "sediment",
            "component": "soil_k_factor",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.00,
            "implementation_status": "not_independently_weighted_current_run",
            "source_layer": "outputs/soilgrids_250m_sediment_candidate/k_factor_0_5cm_250m.tif",
            "note": "current PIM uses the K x LS x C sediment structure; independent grid-compatible K weighting is deferred",
        },
        {
            "pim_criterion": "sediment",
            "component": "ls_factor",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.00,
            "implementation_status": "available_but_not_independently_weighted_current_run",
            "source_layer": "outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor/v1_ls_factor_capped50_hillslope_30m.tif",
            "note": "available as a diagnostic layer; current PIM sediment criterion uses K x LS x C as one structure layer",
        },
        {
            "pim_criterion": "sediment",
            "component": "c_factor",
            "suggested_local_weight": 0.30,
            "applied_weight_in_current_run": 0.00,
            "implementation_status": "available_but_not_independently_weighted_current_run",
            "source_layer": "outputs/esa_worldcover_2021_v1_methodology/c_factor/c_factor_v1_30m.tif",
            "note": "available as a diagnostic layer; current PIM sediment criterion uses K x LS x C as one structure layer",
        },
        {
            "pim_criterion": "landuse_asm",
            "component": "land_cover_pressure",
            "suggested_local_weight": 0.40,
            "applied_weight_in_current_run": 0.40,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["land_cover_pressure"]),
            "note": "ESA WorldCover land-cover pressure",
        },
        {
            "pim_criterion": "landuse_asm",
            "component": "mining_pressure",
            "suggested_local_weight": 0.60,
            "applied_weight_in_current_run": 0.60,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["mining_pressure"]),
            "note": "OSM mining/quarry indicator; weaker than official mining evidence",
        },
        {
            "pim_criterion": "environmental",
            "component": "water_wetland_context",
            "suggested_local_weight": 0.55,
            "applied_weight_in_current_run": 0.55,
            "implementation_status": "implemented_upstream_in_environmental_sensitivity",
            "source_layer": rel(ROOT / "outputs/boundary_v1/environmental_sensitivity_v0_1/water_wetland_context_0_1.tif"),
            "note": "combined before the PIM overlay into environmental_sensitivity",
        },
        {
            "pim_criterion": "environmental",
            "component": "protected_ecological_context",
            "suggested_local_weight": 0.45,
            "applied_weight_in_current_run": 0.45,
            "implementation_status": "implemented_upstream_in_environmental_sensitivity",
            "source_layer": rel(ROOT / "outputs/boundary_v1/environmental_sensitivity_v0_1/protected_area_context_0_1.tif"),
            "note": "combined before the PIM overlay into environmental_sensitivity",
        },
        {
            "pim_criterion": "socioeconomic",
            "component": "road_access_proximity",
            "suggested_local_weight": 0.40,
            "applied_weight_in_current_run": 1.00,
            "implementation_status": "implemented_as_only_available_component",
            "source_layer": rel(COMPONENT_PATHS["exposure_indicators"]),
            "note": "current socioeconomic criterion is road/access proximity only",
        },
        {
            "pim_criterion": "socioeconomic",
            "component": "infrastructure_exposure",
            "suggested_local_weight": 0.60,
            "applied_weight_in_current_run": 0.00,
            "implementation_status": "not_available_current_run",
            "source_layer": "",
            "note": "no independent Zimbabwe infrastructure-exposure raster is present in the current workspace",
        },
    ]
    return rows


def write_handoff(summary: dict[str, object]) -> None:
    text = f"""# boundary_v1 / rainfall_exposure_v0_4

Date: 2026-06-30

Status: `sensitivity_scenario`.

This is the secondary Zimbabwe PIM run after the Peru-first decision. It uses
the current five AHP main criteria and the latest direct Zimbabwe weights for
the Upper Mzingwane catchment.

## AHP main criteria

1. Flood (FH)
2. Sediment / Erosion (SE)
3. Land Use / ASM Pressure (LM)
4. Environmental (ES)
5. Socioeconomic (SV)

## Active scored PIM criteria

1. flood_hazard = rainfall_climatology + TWI + drainage proximity
2. sediment = soil_erosion_factors composite
3. landuse_asm = land_cover_pressure + ASM/mining pressure
4. environmental = water/wetland context + protected-area proximity
5. socioeconomic = road/access exposure indicator

## Headline result

- Area selected in the top 20% across both PIM scenarios:
  {summary['stable_area_km2']} km2.
- Top-20% in at least one scenario: {summary['any_area_km2']} km2.

## Limits

- Rainfall is CHIRPS coarse-to-grid context, not native 30 m rainfall.
- Sediment local K/LS/C subweights are recorded, but current PIM still uses
  the existing K x LS x C composite as one executable criterion.
- Road accessibility is an exposure/access indicator, not observed vulnerability.
- Independent infrastructure exposure is not available in the current Zimbabwe run.
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
    clear_previous_scenario_rasters()
    profile = read_reference()
    components = {
        name: normalize_if_needed(read_band(path, profile))
        for name, path in COMPONENT_PATHS.items()
    }
    criteria = build_pim_criteria(components, profile)
    boundary_mask = read_boundary_mask(profile)
    common_valid = boundary_mask.copy()
    for layer in criteria.values():
        common_valid &= np.isfinite(layer)
    common_valid_fraction = float(common_valid.sum() / boundary_mask.sum())

    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    scenario_arrays: dict[str, np.ndarray] = {}
    top20_masks: list[np.ndarray] = []

    for scenario, weights in SCENARIOS.items():
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
                "weight_source": (
                    "equal baseline"
                    if scenario == "equal_active_pim"
                    else "Zimbabwe direct recommended weights, July 2026"
                ),
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
    write_csv(OUT_DIR / "pim_subcriteria_weights.csv", build_subcriteria_weight_rows())
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "component_grid_check.csv", build_grid_check(profile, components))
    write_csv(OUT_DIR / "pim_criteria_grid_check.csv", build_grid_check(profile, criteria))

    all_mask = np.all(np.stack(top20_masks), axis=0)
    any_mask = np.any(np.stack(top20_masks), axis=0)
    top20_summary = {
        "scenario_count": len(SCENARIOS),
        "mentor_zimbabwe_direct_weights": "flood_hazard=0.32, sediment=0.23, landuse_asm=0.18, environmental=0.12, socioeconomic=0.15",
        "mentor_zimbabwe_weight_type": "direct recommended weights; no pairwise matrix consistency ratio supplied in the current note",
        "pim_main_criteria_count": len(PIM_CRITERIA_ORDER),
        "active_scored_pim_criteria_count": len(ACTIVE_PIM_CRITERIA),
        "component_layer_count": len(COMPONENT_PATHS),
        "common_valid_fraction": round(common_valid_fraction, 6),
        "top20_all_scenarios_cells": int(all_mask.sum()),
        "top20_any_scenario_cells": int(any_mask.sum()),
        "top20_all_scenarios_area_km2": round(float(all_mask.sum() * CELL_AREA_KM2), 3),
        "top20_any_scenario_area_km2": round(float(any_mask.sum() * CELL_AREA_KM2), 3),
        "stable_area_km2": round(float(all_mask.sum() * CELL_AREA_KM2), 3),
        "any_area_km2": round(float(any_mask.sum() * CELL_AREA_KM2), 3),
        "active_scored_pim_criteria": ", ".join(ACTIVE_PIM_CRITERIA),
        "component_layers": ", ".join(COMPONENT_PATHS),
        "environmental_sensitivity_status": "provisional",
        "socioeconomic_infrastructure_exposure_status": "not_available_current_run; road/access proximity is used as the only available component",
    }
    write_csv(
        OUT_DIR / "hotspot_stability_summary.csv",
        [{"metric": key, "value": value} for key, value in top20_summary.items()],
    )
    plot_board(priority_mean, top20_frequency, profile)
    write_handoff(top20_summary)
    print(f"Wrote {experiment_id} outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
