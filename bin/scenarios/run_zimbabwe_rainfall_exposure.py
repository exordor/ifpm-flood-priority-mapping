#!/usr/bin/env python3
"""Run the direct-weight zimbabwe_upper_mzingwane Zimbabwe PIM overlay.

This experiment keeps the five PIM main criteria as Flood, Sediment, Land
Use / ASM, Environmental, and Socioeconomic. Zimbabwe is secondary/background
after the Peru-first decision, but this run records the latest direct
Zimbabwe weights for the Upper Mzingwane catchment:

- Flood hazard: rainfall climatology, TWI, and drainage proximity.
- Sediment: independently standardized K, LS, and C factors combined with
  the supplied local weights 0.35, 0.35, and 0.30.
- Land Use / ASM: land-cover pressure + mining pressure.
- Environmental: water/wetland and protected-area sensitivity indicator.
- Socioeconomic: road/access exposure indicator; independent infrastructure
  exposure is explicitly unavailable in the current run.

Only the supplied direct Zimbabwe weights are active. Equal-weight and
top-percentile products are not part of this reporting run.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [
    ROOT / "outputs/zimbabwe_pim_scenarios/rainfall_sensitivity/criteria/rainfall_climatology_0_1_PROVISIONAL_30m.tif",
    ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization/zimbabwe_twi_high_wetness_0_1.tif",
    ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization/zimbabwe_drainage_proximity_0_1.tif",
    ROOT / "outputs/zimbabwe_terrain_hydrology_factors/soil_k_factor/soil_k_factor_0_1.tif",
    ROOT / "outputs/zimbabwe_terrain_hydrology_factors/ls_factor/zimbabwe_ls_factor_capped50_hillslope_30m.tif",
    ROOT / "outputs/zimbabwe_esa_worldcover_2021/c_factor/c_factor_zimbabwe_30m.tif",
    ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/land_cover_pressure_0_1.tif",
    ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/mining_pressure_0_1.tif",
    ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/exposure_indicators_0_1.tif",
    ROOT / "outputs/zimbabwe_pim_scenarios/environmental_sensitivity/environmental_sensitivity_0_1.tif",
    ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif",
    ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg",
]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
from _lib.standardization import ensure_unit_interval, percentile_minmax_array
BOUNDARY_ID = "zimbabwe_upper_mzingwane"
OUTPUT_ROOT_ID = "zimbabwe_pim_scenarios"  # outputs folder name (differs from the id since 2026-10-11 rename)
EXPERIMENT_ID = "rainfall_exposure"
OUT_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"
PIM_CRITERIA_DIR = OUT_DIR / "pim_criteria"
SEDIMENT_COMPONENT_DIR = OUT_DIR / "sediment_components"
RUN_MANIFEST = OUT_DIR / "run_manifest.csv"
REF = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
CRITERIA_DIR = ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria"
RAINFALL_DIR = ROOT / "outputs/zimbabwe_pim_scenarios/rainfall_sensitivity/criteria"
HYDROLOGY_STANDARDIZATION_DIR = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization"

COMPONENT_PATHS = {
    "rainfall_climatology": RAINFALL_DIR / "rainfall_climatology_0_1_PROVISIONAL_30m.tif",
    "twi_wetness": HYDROLOGY_STANDARDIZATION_DIR / "zimbabwe_twi_high_wetness_0_1.tif",
    "drainage_proximity": HYDROLOGY_STANDARDIZATION_DIR / "zimbabwe_drainage_proximity_0_1.tif",
    "soil_k_factor": ROOT / "outputs/zimbabwe_terrain_hydrology_factors/soil_k_factor/soil_k_factor_0_1.tif",
    "ls_factor": ROOT / "outputs/zimbabwe_terrain_hydrology_factors/ls_factor/zimbabwe_ls_factor_capped50_hillslope_30m.tif",
    "c_factor": ROOT / "outputs/zimbabwe_esa_worldcover_2021/c_factor/c_factor_zimbabwe_30m.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "mining_pressure": CRITERIA_DIR / "mining_pressure_0_1.tif",
    "exposure_indicators": CRITERIA_DIR / "exposure_indicators_0_1.tif",
    "environmental_sensitivity": ROOT / "outputs/zimbabwe_pim_scenarios/environmental_sensitivity/environmental_sensitivity_0_1.tif",
}

PIM_CRITERIA_ORDER = ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"]
OUTPUTS = [
    SCENARIO_DIR / "priority_mentor_zimbabwe_direct_pim.tif",
    *[PIM_CRITERIA_DIR / f"{name}_0_1.tif" for name in PIM_CRITERIA_ORDER],
    *[
        SEDIMENT_COMPONENT_DIR / f"{name}_0_1.tif"
        for name in ("soil_k_factor", "ls_factor", "c_factor")
    ],
    OUT_DIR / "sediment_component_count.tif",
    OUT_DIR / "scenario_weights.csv",
    OUT_DIR / "pim_subcriteria_weights.csv",
    OUT_DIR / "scenario_priority_summary.csv",
    OUT_DIR / "component_grid_check.csv",
    OUT_DIR / "pim_criteria_grid_check.csv",
    OUT_DIR / "priority_screening_summary.csv",
    OUT_DIR / "handoff.md",
    RUN_MANIFEST,
]
ACTIVE_PIM_CRITERIA = PIM_CRITERIA_ORDER
PIM_COMPONENTS = {
    "flood_hazard": {"rainfall_climatology": 0.35, "twi_wetness": 0.30, "drainage_proximity": 0.35},
    "sediment": {"soil_k_factor": 0.35, "ls_factor": 0.35, "c_factor": 0.30},
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
SCENARIO_ID = "mentor_zimbabwe_direct_pim"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


# Compatibility names retained for callers; implementations are centralized.
normalize_if_needed = ensure_unit_interval
normalize_2_98 = percentile_minmax_array


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
    for filename in (
        "priority_mean.tif",
        "priority_std.tif",
        "top20_frequency.tif",
        "hotspot_stability_summary.csv",
        "rainfall_exposure_v0_4_board.png",
        "rainfall_exposure_v0_4_board.pdf",
        "grid_check.csv",
    ):
        path = OUT_DIR / filename
        if path.exists():
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


def build_grid_check(
    profile: dict,
    criteria: dict[str, np.ndarray],
    boundary_mask: np.ndarray,
) -> list[dict[str, object]]:
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
            "valid_fraction_of_boundary": round(
                float((boundary_mask & np.isfinite(data)).sum() / boundary_mask.sum()), 6
            ),
            "coverage_denominator": "boundary cells",
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
            "component": "soil_k_factor",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented",
            "source_layer": rel(SEDIMENT_COMPONENT_DIR / "soil_k_factor_0_1.tif"),
            "note": "SoilGrids-derived spatial K factor aligned to the reference grid; effective source resolution remains 250 m",
        },
        {
            "pim_criterion": "sediment",
            "component": "ls_factor",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented",
            "source_layer": rel(SEDIMENT_COMPONENT_DIR / "ls_factor_0_1.tif"),
            "note": "SRTM-derived capped hillslope LS factor, normalized by boundary 2-98 percentile min-max",
        },
        {
            "pim_criterion": "sediment",
            "component": "c_factor",
            "suggested_local_weight": 0.30,
            "applied_weight_in_current_run": 0.30,
            "implementation_status": "implemented",
            "source_layer": rel(SEDIMENT_COMPONENT_DIR / "c_factor_0_1.tif"),
            "note": "ESA WorldCover-derived cover-management factor, normalized by boundary 2-98 percentile min-max; higher C indicates weaker protective cover",
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
            "note": "USGS Africa GIS mineral facilities and deposits with tiered distance decay; not a verified active ASM footprint",
        },
        {
            "pim_criterion": "environmental",
            "component": "water_wetland_context",
            "suggested_local_weight": 0.55,
            "applied_weight_in_current_run": 0.55,
            "implementation_status": "implemented_upstream_in_environmental_sensitivity",
            "source_layer": rel(ROOT / "outputs/zimbabwe_pim_scenarios/environmental_sensitivity/water_wetland_context_0_1.tif"),
            "note": "combined before the PIM overlay into environmental_sensitivity",
        },
        {
            "pim_criterion": "environmental",
            "component": "protected_ecological_context",
            "suggested_local_weight": 0.45,
            "applied_weight_in_current_run": 0.45,
            "implementation_status": "implemented_upstream_in_environmental_sensitivity",
            "source_layer": rel(ROOT / "outputs/zimbabwe_pim_scenarios/environmental_sensitivity/protected_area_context_0_1.tif"),
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
    text = f"""# zimbabwe_upper_mzingwane / rainfall_exposure

Date: 2026-07-14

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
2. sediment = 0.35 soil K + 0.35 LS + 0.30 C
3. landuse_asm = land_cover_pressure + ASM/mining pressure
4. environmental = water/wetland context + protected-area proximity
5. socioeconomic = road/access exposure indicator

## Coverage

- Five-criterion common-support coverage: {summary['common_valid_fraction']}.
- Unscored boundary fraction: {summary['unscored_boundary_fraction']}.

## Limits

- Rainfall is CHIRPS coarse-to-grid context, not native 30 m rainfall.
- Sediment uses independently scored K, LS, and C factors. This remains an
  erosion-source indicator, not measured sediment transport or soil-loss rate.
- Road accessibility is an exposure/access indicator, not observed vulnerability.
- Independent infrastructure exposure is not available in the current Zimbabwe run.
- This is not a validated flood-risk map and not an intervention-priority map.
"""
    (OUT_DIR / "handoff.md").write_text(text, encoding="utf-8")


def write_run_manifest() -> None:
    rows = [
        {
            "role": "input",
            "path": rel(path),
            "sha256": sha256(path),
            "claim_level": "sensitivity_scenario",
        }
        for path in INPUTS
    ]
    rows.extend(
        {
            "role": "output",
            "path": rel(path),
            "sha256": sha256(path),
            "claim_level": "sensitivity_scenario",
        }
        for path in OUTPUTS
        if path != RUN_MANIFEST
    )
    rows.append({
        "role": "script",
        "path": rel(Path(__file__)),
        "sha256": sha256(Path(__file__)),
        "claim_level": "sensitivity_scenario",
    })
    write_csv(RUN_MANIFEST, rows)


def main() -> None:
    opts = parse_script_args(boundary_id=BOUNDARY_ID, experiment_id=EXPERIMENT_ID,
                             description="Run zimbabwe_upper_mzingwane PIM 5-main-criterion priority scenarios.")
    boundary_id = opts.get("boundary_id", BOUNDARY_ID)
    experiment_id = opts.get("experiment_id", EXPERIMENT_ID)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    SEDIMENT_COMPONENT_DIR.mkdir(parents=True, exist_ok=True)
    clear_previous_scenario_rasters()
    profile = read_reference()
    boundary_mask = read_boundary_mask(profile)
    components = {
        name: normalize_if_needed(read_band(path, profile))
        for name, path in COMPONENT_PATHS.items()
    }
    components["ls_factor"] = normalize_2_98(
        read_band(COMPONENT_PATHS["ls_factor"], profile), boundary_mask
    )
    components["c_factor"] = normalize_2_98(
        read_band(COMPONENT_PATHS["c_factor"], profile), boundary_mask
    )
    for name in ("soil_k_factor", "ls_factor", "c_factor"):
        write_raster(
            SEDIMENT_COMPONENT_DIR / f"{name}_0_1.tif",
            components[name],
            profile,
        )
    criteria = build_pim_criteria(components, profile)
    common_valid = boundary_mask.copy()
    for layer in criteria.values():
        common_valid &= np.isfinite(layer)
    common_valid_fraction = float(common_valid.sum() / boundary_mask.sum())

    if round(sum(ZIMBABWE_MENTOR_MAIN_WEIGHTS.values()), 10) != 1.0:
        raise ValueError("Zimbabwe direct weights do not sum to 1")
    numerator = np.zeros((profile["height"], profile["width"]), dtype="float32")
    weight_rows: list[dict[str, object]] = []
    for criterion, weight in ZIMBABWE_MENTOR_MAIN_WEIGHTS.items():
        layer = criteria[criterion]
        numerator[common_valid] += layer[common_valid] * weight
        weight_rows.append({
            "boundary_id": boundary_id,
            "experiment_id": experiment_id,
            "scenario": SCENARIO_ID,
            "criterion": criterion,
            "weight": round(weight, 8),
            "weight_source": "Zimbabwe direct recommended weights, July 2026; no pairwise matrix supplied",
            "claim_level": "sensitivity_scenario",
        })
    score = np.full_like(numerator, np.nan, dtype="float32")
    score[common_valid] = numerator[common_valid]
    write_raster(SCENARIO_DIR / f"priority_{SCENARIO_ID}.tif", score, profile)
    summary_rows = [{
        "boundary_id": boundary_id,
        "experiment_id": experiment_id,
        "scenario": SCENARIO_ID,
        "common_valid_fraction": round(common_valid_fraction, 6),
        **raster_stats(score),
    }]

    sediment_component_count = sum(
        np.isfinite(components[name]).astype("uint8")
        for name in ("soil_k_factor", "ls_factor", "c_factor")
    ).astype("float32")
    sediment_component_count[~boundary_mask] = np.nan
    write_raster(OUT_DIR / "sediment_component_count.tif", sediment_component_count, profile)
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "pim_subcriteria_weights.csv", build_subcriteria_weight_rows())
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(
        OUT_DIR / "component_grid_check.csv",
        build_grid_check(profile, components, boundary_mask),
    )
    write_csv(
        OUT_DIR / "pim_criteria_grid_check.csv",
        build_grid_check(profile, criteria, boundary_mask),
    )

    screening_summary = {
        "scenario_count": 1,
        "mentor_zimbabwe_direct_weights": "flood_hazard=0.32, sediment=0.23, landuse_asm=0.18, environmental=0.12, socioeconomic=0.15",
        "mentor_zimbabwe_weight_type": "direct recommended weights; no pairwise matrix consistency ratio supplied in the current note",
        "pim_main_criteria_count": len(PIM_CRITERIA_ORDER),
        "active_scored_pim_criteria_count": len(ACTIVE_PIM_CRITERIA),
        "component_layer_count": len(COMPONENT_PATHS),
        "common_valid_fraction": round(common_valid_fraction, 6),
        "unscored_boundary_fraction": round(1.0 - common_valid_fraction, 6),
        "interpretation_domain": "five-criterion common-support cells only; NoData is never treated as low priority or compensated by weight renormalization",
        "active_scored_pim_criteria": ", ".join(ACTIVE_PIM_CRITERIA),
        "component_layers": ", ".join(COMPONENT_PATHS),
        "environmental_sensitivity_status": "provisional",
        "socioeconomic_infrastructure_exposure_status": "not_available_current_run; road/access proximity is used as the only available component",
    }
    write_csv(
        OUT_DIR / "priority_screening_summary.csv",
        [{"metric": key, "value": value} for key, value in screening_summary.items()],
    )
    write_handoff(screening_summary)
    write_run_manifest()
    print(f"Wrote {experiment_id} outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
