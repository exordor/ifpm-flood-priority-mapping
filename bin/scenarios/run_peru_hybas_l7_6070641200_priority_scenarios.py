#!/usr/bin/env python3
"""Run the Supervisor-spec no-mining Peru PIM baseline for Arequipa Region.

WEIGHT BRANCH: weights/supervisor-full-spec. This branch applies Supervisor's
complete weight specification (2026-08-06 message). The main branch carries the
retained original test weights; switching branches switches the full scheme.

Arequipa Region follows the mentor 5-main-criterion AHP framework: Flood, Sediment,
General Land Use Pressure, Environmental, and Socioeconomic. Five criteria are actively
scored in the current executable prototype, all using Supervisor's sub-weights:

- Flood hazard: rainfall 0.35, TWI 0.25, drainage/flow 0.40.
- Sediment: independently scored SoilGrids K 0.25, LS 0.50, C 0.25.
- General Land Use Pressure: 0.40 LC + 0.35 BV + 0.25 BE. Mining is excluded
  from the PIM calculation and retained only as an external overlay.
- Environmental: water/wetland 0.65 + protected/ecological 0.35, recombined
  directly from components (not the upstream pre-blended 0.60/0.40 raster).
- Socioeconomic: road/access 0.35 + settlement/population 0.35 + critical
  infrastructure 0.30. CI is proxied by mapped-building density (no true CI
  inventory exists). Poverty and health-service remoteness remain
  response-capacity context layers outside the current AHP overlay.

Top-level weights: FH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14.
No pairwise matrix or AHP consistency ratio was supplied (expert-informed
provisional weights).

Sediment note: K, LS, and C are independently normalized and combined by the
supplied local subweights. The resulting 0-1 score is a relative
erosion/sediment-source priority indicator, not an absolute soil-loss rate.

Outputs (gitignored under outputs/srtm_1arcsec_peru_pilot/priority_scenarios/):
the direct-weight priority raster, highest-priority-quintile selection, five
criterion rasters, weights, diagnostics, and a board figure. All provisional /
sensitivity_scenario.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
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
INPUTS = [
    ROOT / "bin/_lib/ifpm_tools.py",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/twi_wetness_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/drainage_proximity_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/soil_k_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/ls_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/c_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/bare_soil_vegetation_loss_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/built_agriculture_road_expansion_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/rainfall_climatology_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/peru_hybas_l7_6070641200_priority_scenarios_board.png",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/peru_hybas_l7_6070641200_priority_scenarios_board.pdf",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/top20_mentor_peru_direct_pim.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/flood_hazard_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/sediment_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/landuse_asm_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/environmental_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/socioeconomic_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/criteria_evidence_count.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/available_main_weight.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/sediment_component_count.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/evidence_support_class.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_subcriteria_weights.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_screening_summary.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_priority_summary.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/component_grid_check.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria_grid_check.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/run_manifest.json",
]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
BOUNDARY_ID = "peru_hybas_l7_6070641200"
EXPERIMENT_ID = "priority_scenarios"
OUT_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"
PIM_CRITERIA_DIR = OUT_DIR / "pim_criteria"
CRITERIA_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria"
EXPOSURE_INDICATORS_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif"
PERU_HYBAS_L7_6070641200_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
# Common-mask overlay must reject true data gaps. Arequipa Region LS deliberately masks
# main-channel cells; K also preserves source-edge NoData. Keep those cells
# unscored and require enough common coverage to catch missing active evidence.
MIN_SCOREABLE_VALID_FRACTION = 0.95

COMPONENT_PATHS = {
    "rainfall_climatology": CRITERIA_DIR / "rainfall_climatology_0_1.tif",
    "twi_wetness": CRITERIA_DIR / "twi_wetness_0_1.tif",
    "drainage_proximity": CRITERIA_DIR / "drainage_proximity_0_1.tif",
    "soil_k_factor": CRITERIA_DIR / "soil_k_factor_0_1.tif",
    "ls_factor": CRITERIA_DIR / "ls_factor_0_1.tif",
    "c_factor": CRITERIA_DIR / "c_factor_0_1.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "bare_soil_vegetation_loss": CRITERIA_DIR / "bare_soil_vegetation_loss_0_1.tif",
    "built_agriculture_road_expansion": CRITERIA_DIR / "built_agriculture_road_expansion_0_1.tif",
    # Supervisor spec ES: components read directly, not the upstream pre-blended raster.
    "water_wetland_context": ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/water_wetland_context_0_1.tif",
    "protected_ecological_context": ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/protected_area_context_0_1.tif",
    # Supervisor spec SV: three-way split. CI is a mapped-building-density proxy.
    "road_access_proximity": CRITERIA_DIR / "road_access_proximity_0_1.tif",
    "settlement_population": EXPOSURE_INDICATORS_DIR / "population_exposure_0_1.tif",
    "critical_infrastructure": EXPOSURE_INDICATORS_DIR / "built_infrastructure_exposure_0_1.tif",
}

PIM_CRITERIA_ORDER = ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"]
ACTIVE_PIM_CRITERIA = PIM_CRITERIA_ORDER
PIM_COMPONENTS = {
    # Supervisor full spec (2026-08-06): FH sub rainfall 0.35 / TWI 0.25 / drainage 0.40
    "flood_hazard": {"rainfall_climatology": 0.35, "twi_wetness": 0.25, "drainage_proximity": 0.40},
    # Supervisor full spec: SE sub K 0.25 / LS 0.50 / C 0.25
    "sediment": {"soil_k_factor": 0.25, "ls_factor": 0.50, "c_factor": 0.25},
    # Keep the historical internal slug for downstream path compatibility. Its
    # current semantic meaning is General Land Use Pressure, with no ASM/mining input.
    "landuse_asm": {
        "land_cover_pressure": 0.40,
        "bare_soil_vegetation_loss": 0.35,
        "built_agriculture_road_expansion": 0.25,
    },
    # Supervisor full spec: ES sub WW 0.65 / PA 0.35 (rebuilt from components here,
    # not the upstream pre-blended 0.60/0.40 raster).
    "environmental": {"water_wetland_context": 0.65, "protected_ecological_context": 0.35},
    # Supervisor full spec: SV sub road 0.35 / settlement+population 0.35 /
    # critical infrastructure 0.30 (CI proxied by mapped-building density; no
    # true CI inventory exists).
    "socioeconomic": {
        "road_access_proximity": 0.35,
        "settlement_population": 0.35,
        "critical_infrastructure": 0.30,
    },
}
MENTOR_PERU_MAIN_WEIGHTS = {
    "flood_hazard": 0.34,
    "sediment": 0.25,
    "landuse_asm": 0.17,
    "environmental": 0.10,
    "socioeconomic": 0.14,
}


SCENARIOS = {
    "mentor_peru_direct_pim": MENTOR_PERU_MAIN_WEIGHTS,
}

STALE_MULTI_SCENARIO_OUTPUTS = [
    OUT_DIR / "priority_mean.tif",
    OUT_DIR / "priority_std.tif",
    OUT_DIR / "top20_frequency.tif",
    SCENARIO_DIR / "priority_equal_active_pim.tif",
    SCENARIO_DIR / "top20_equal_active_pim.tif",
    OUT_DIR / "hotspot_stability_summary.csv",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_state() -> dict[str, object]:
    """Return private run-lineage context without changing the worktree."""

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.splitlines()
        return {
            "head": head,
            "dirty": bool(status),
            "scope_note": (
                "dirty is repository-wide; worktree paths are intentionally omitted "
                "because unrelated local work is outside this run's lineage"
            ),
        }
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"head": None, "dirty": None, "error": str(exc)}


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


def read_summary_metric(path: Path, metric: str) -> float:
    if not path.exists():
        return float("nan")
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("metric") == metric:
                try:
                    return float(row["value"])
                except (TypeError, ValueError):
                    return float("nan")
    return float("nan")


def read_reference() -> dict:
    with rasterio.open(REF) as ref:
        return ref.profile.copy()


def read_boundary_mask(profile: dict) -> np.ndarray:
    boundary = gpd.read_file(PERU_HYBAS_L7_6070641200_GPKG, layer="peru_pilot_boundary").to_crs(profile["crs"])
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


def combine_weighted_layers(
    source_layers: dict[str, np.ndarray],
    component_weights: dict[str, float],
) -> np.ndarray:
    first = next(iter(source_layers.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    common_support = np.ones(first.shape, dtype=bool)
    for component, weight in component_weights.items():
        layer = source_layers[component]
        valid = np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        common_support &= valid
    combined = np.full(first.shape, np.nan, dtype="float32")
    combined[common_support] = numerator[common_support]
    return np.clip(combined, 0.0, 1.0).astype("float32")


def combine_common_support_criteria(
    criteria: dict[str, np.ndarray],
    weights: dict[str, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Combine criteria only where all five inputs share finite support."""

    first = next(iter(criteria.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    available_weight = np.zeros(first.shape, dtype="float32")
    evidence_count = np.zeros(first.shape, dtype="uint8")
    common_support = np.ones(first.shape, dtype=bool)
    for criterion, weight in weights.items():
        layer = criteria[criterion]
        valid = np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        available_weight[valid] += weight
        evidence_count[valid] += 1
        common_support &= valid

    score = np.full(first.shape, np.nan, dtype="float32")
    score[common_support] = numerator[common_support]
    return np.clip(score, 0.0, 1.0), available_weight, evidence_count


def classify_evidence_support(
    components: dict[str, np.ndarray],
    criteria: dict[str, np.ndarray],
    boundary_mask: np.ndarray,
) -> np.ndarray:
    """Classify why a boundary cell is or is not eligible for the final PIM."""

    support = np.zeros(boundary_mask.shape, dtype="uint8")
    support[boundary_mask] = 4
    k_valid = np.isfinite(components["soil_k_factor"])
    ls_valid = np.isfinite(components["ls_factor"])
    c_valid = np.isfinite(components["c_factor"])
    support[boundary_mask & ~k_valid] = 3
    support[boundary_mask & k_valid & c_valid & ~ls_valid] = 2
    common_support = boundary_mask.copy()
    for layer in criteria.values():
        common_support &= np.isfinite(layer)
    support[common_support] = 1
    return support


def calculate_pim_criteria(components: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Calculate the five current criteria without reading or writing files."""

    return {
        name: combine_weighted_layers(components, weights)
        for name, weights in PIM_COMPONENTS.items()
    }


def build_pim_criteria(components: dict[str, np.ndarray], profile: dict) -> dict[str, np.ndarray]:
    PIM_CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    criteria = calculate_pim_criteria(components)
    for name, data in criteria.items():
        write_raster(PIM_CRITERIA_DIR / f"{name}_0_1.tif", data, profile)
    return criteria


def build_grid_check(profile: dict, layers: dict[str, np.ndarray]) -> list[dict[str, object]]:
    rows = []
    for name, data in layers.items():
        values = data[np.isfinite(data)]
        rows.append({
            "criterion": name,
            "grid_compatible": True,
            "crs": str(profile["crs"]),
            "width": profile["width"],
            "height": profile["height"],
            "valid_cells": int(values.size),
            "valid_fraction": round(float(values.size / data.size), 6),
            "min": round(float(values.min()), 6) if values.size else "",
            "mean": round(float(values.mean()), 6) if values.size else "",
            "max": round(float(values.max()), 6) if values.size else "",
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
            "suggested_local_weight": 0.25,
            "applied_weight_in_current_run": 0.25,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["twi_wetness"]),
            "note": "DEM-derived TWI, high wetness -> high flood-conditioning score",
        },
        {
            "pim_criterion": "flood_hazard",
            "component": "drainage_proximity",
            "suggested_local_weight": 0.40,
            "applied_weight_in_current_run": 0.40,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["drainage_proximity"]),
            "note": "distance to drainage, closer -> higher flood-conditioning score",
        },
        {
            "pim_criterion": "sediment",
            "component": "soil_k_factor",
            "suggested_local_weight": 0.25,
            "applied_weight_in_current_run": 0.25,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["soil_k_factor"]),
            "note": "SoilGrids 250 m K aligned to the reference grid; effective resolution remains 250 m",
        },
        {
            "pim_criterion": "sediment",
            "component": "ls_factor",
            "suggested_local_weight": 0.50,
            "applied_weight_in_current_run": 0.50,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["ls_factor"]),
            "note": (
                "SRTM-derived hillslope LS; channel-mask NoData remains unscored and "
                "is not replaced or weight-renormalized"
            ),
        },
        {
            "pim_criterion": "sediment",
            "component": "c_factor",
            "suggested_local_weight": 0.25,
            "applied_weight_in_current_run": 0.25,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["c_factor"]),
            "note": "WorldCover-derived RUSLE C-factor, independently scored inside Sediment",
        },
        {
            "pim_criterion": "landuse_asm",
            "component": "land_cover_pressure",
            "suggested_local_weight": 0.40,
            "applied_weight_in_current_run": 0.40,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["land_cover_pressure"]),
            "note": (
                "LC land-cover runoff-pressure test value function; no dedicated mining input"
            ),
        },
        {
            "pim_criterion": "landuse_asm",
            "component": "bare_soil_vegetation_loss",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented_as_single_date_proxy",
            "source_layer": rel(COMPONENT_PATHS["bare_soil_vegetation_loss"]),
            "note": "BV uses current WorldCover bare/sparse cover; it does not measure temporal vegetation loss",
        },
        {
            "pim_criterion": "landuse_asm",
            "component": "built_agriculture_road_expansion",
            "suggested_local_weight": 0.25,
            "applied_weight_in_current_run": 0.25,
            "implementation_status": "implemented_as_equal_component_test_proxy",
            "source_layer": rel(COMPONENT_PATHS["built_agriculture_road_expansion"]),
            "note": "BE = 0.50 max(built-up, agriculture) + 0.50 road proximity; explicit test proxy, not temporal expansion",
        },
        {
            "pim_criterion": "environmental",
            "component": "water_wetland_context",
            "suggested_local_weight": 0.65,
            "applied_weight_in_current_run": 0.65,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["water_wetland_context"]),
            "note": "Supervisor spec: WW recombined directly in the runner, not the upstream pre-blended raster",
        },
        {
            "pim_criterion": "environmental",
            "component": "protected_ecological_context",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["protected_ecological_context"]),
            "note": "Supervisor spec: PA recombined directly in the runner",
        },
        {
            "pim_criterion": "socioeconomic",
            "component": "road_access_proximity",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["road_access_proximity"]),
            "note": "Supervisor spec: road/access as its own SV component",
        },
        {
            "pim_criterion": "socioeconomic",
            "component": "settlement_population",
            "suggested_local_weight": 0.35,
            "applied_weight_in_current_run": 0.35,
            "implementation_status": "implemented",
            "source_layer": rel(COMPONENT_PATHS["settlement_population"]),
            "note": "Supervisor spec: settlement+population (WorldPop) as its own SV component",
        },
        {
            "pim_criterion": "socioeconomic",
            "component": "critical_infrastructure",
            "suggested_local_weight": 0.30,
            "applied_weight_in_current_run": 0.30,
            "implementation_status": "implemented_as_built_density_proxy",
            "source_layer": rel(COMPONENT_PATHS["critical_infrastructure"]),
            "note": "Supervisor spec: CI proxied by OSM mapped-building density; no true CI inventory exists",
        },
    ]
    return rows


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
    cax = divider.append_axes("right", size="3%", pad=0.08)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label(label, fontsize=8)


def plot_board(direct_score, direct_top20, profile) -> None:
    boundary = gpd.read_file(PERU_HYBAS_L7_6070641200_GPKG, layer="peru_pilot_boundary").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0], bounds[2], bounds[1], bounds[3])

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.9), constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=0.12, h_pad=0.08, wspace=0.18, hspace=0.02)
    panels = [
        ("A. Direct-weight priority score", direct_score, "YlOrRd", "0-1 priority score"),
        ("B. Highest-priority quintile", direct_top20, "Reds", "selected cell"),
    ]
    for ax, (title, data, cmap, label) in zip(axes, panels, strict=True):
        image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.9)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32718)", fontsize=8)
        ax.set_ylabel("Northing (km)", fontsize=8)
        km_formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
        ax.xaxis.set_major_formatter(km_formatter)
        ax.yaxis.set_major_formatter(km_formatter)
        ax.grid(color="0.9", linewidth=0.4)
        ax.tick_params(labelsize=7)
        add_colorbar(fig, ax, image, label)
    fig.suptitle(
        "Peru Arequipa Mining Region: PIM 5-Criterion Prototype Priority Screening",
        fontsize=12,
        fontweight="bold",
    )
    fig.savefig(OUT_DIR / "peru_hybas_l7_6070641200_priority_scenarios_board.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "peru_hybas_l7_6070641200_priority_scenarios_board.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    opts = parse_script_args(boundary_id=BOUNDARY_ID, experiment_id=EXPERIMENT_ID)
    boundary_id = opts.get("boundary_id", BOUNDARY_ID)
    experiment_id = opts.get("experiment_id", EXPERIMENT_ID)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    for stale_path in STALE_MULTI_SCENARIO_OUTPUTS:
        stale_path.unlink(missing_ok=True)
    profile = read_reference()
    components = {name: read_band(path, profile) for name, path in COMPONENT_PATHS.items()}
    criteria = build_pim_criteria(components, profile)
    boundary_mask = read_boundary_mask(profile)
    full_five_valid = boundary_mask.copy()
    for layer in criteria.values():
        full_five_valid &= np.isfinite(layer)
    scoreable_valid_fraction = float(full_five_valid.sum() / boundary_mask.sum())
    full_five_fraction = scoreable_valid_fraction
    if scoreable_valid_fraction < MIN_SCOREABLE_VALID_FRACTION:
        missing = []
        for name in PIM_CRITERIA_ORDER:
            layer = criteria[name]
            frac = float((boundary_mask & np.isfinite(layer)).sum() / boundary_mask.sum())
            if frac < MIN_SCOREABLE_VALID_FRACTION:
                missing.append(f"{name}={frac:.6f}")
        raise RuntimeError(
            "Arequipa Region five-criterion common support does not provide enough scoreable coverage; "
            f"scoreable={scoreable_valid_fraction:.6f}, threshold={MIN_SCOREABLE_VALID_FRACTION}; "
            f"low layers: {', '.join(missing) if missing else 'none'}"
        )

    scenario_arrays: dict[str, np.ndarray] = {}
    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    top20_arrays: dict[str, np.ndarray] = {}

    all_scenarios = dict(SCENARIOS)
    for scenario, weights in all_scenarios.items():
        total = round(sum(weights.values()), 10)
        if total != 1.0:
            raise ValueError(f"weights for {scenario} sum to {total}")
        for criterion, weight in weights.items():
            weight_rows.append({
                "boundary_id": boundary_id, "experiment_id": experiment_id,
                "scenario": scenario, "criterion": criterion,
                "weight": round(weight, 8),
                "weight_source": "mentor-recommended Peru direct weights, July 2026; no pairwise matrix supplied",
                "claim_level": "sensitivity_scenario",
            })
        score, available_weight, evidence_count = combine_common_support_criteria(criteria, weights)
        score[~boundary_mask] = np.nan
        available_weight = available_weight.astype("float32")
        available_weight[~boundary_mask] = np.nan
        evidence_count_output = evidence_count.astype("float32")
        evidence_count_output[~boundary_mask] = np.nan
        sediment_component_count = sum(
            np.isfinite(components[name]).astype("uint8")
            for name in ("soil_k_factor", "ls_factor", "c_factor")
        )
        sediment_component_count_output = sediment_component_count.astype("float32")
        sediment_component_count_output[~boundary_mask] = np.nan
        evidence_support = classify_evidence_support(components, criteria, boundary_mask)
        evidence_support_output = evidence_support.astype("float32")
        evidence_support_output[~boundary_mask] = np.nan
        write_raster(OUT_DIR / "available_main_weight.tif", available_weight, profile)
        write_raster(OUT_DIR / "criteria_evidence_count.tif", evidence_count_output, profile)
        write_raster(OUT_DIR / "sediment_component_count.tif", sediment_component_count_output, profile)
        write_raster(OUT_DIR / "evidence_support_class.tif", evidence_support_output, profile)
        scoreable = boundary_mask & np.isfinite(score)
        incomplete_evidence_fraction = float((boundary_mask & ~scoreable).sum() / boundary_mask.sum())
        ls_missing_fraction = float(np.sum(evidence_support == 2) / boundary_mask.sum())
        k_missing_fraction = float(np.sum(evidence_support == 3) / boundary_mask.sum())
        other_missing_fraction = float(np.sum(evidence_support == 4) / boundary_mask.sum())
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}.tif", score, profile)
        threshold = float(np.nanpercentile(score, 80))
        top20 = np.where(scoreable, score >= threshold, np.nan).astype("float32")
        write_raster(SCENARIO_DIR / f"top20_{scenario}.tif", top20, profile)
        top20_arrays[scenario] = top20
        summary_rows.append({
            "boundary_id": boundary_id, "experiment_id": experiment_id,
            "scenario": scenario, "top20_threshold": threshold,
            "scoreable_valid_fraction": round(scoreable_valid_fraction, 6),
            "full_five_criterion_fraction": round(full_five_fraction, 6),
            "incomplete_evidence_fraction": round(incomplete_evidence_fraction, 6),
            "ls_missing_fraction": round(ls_missing_fraction, 6),
            "k_missing_fraction": round(k_missing_fraction, 6),
            "other_missing_fraction": round(other_missing_fraction, 6),
            "common_valid_fraction": round(full_five_fraction, 6),
            **raster_stats(score),
        })

    direct_score = scenario_arrays["mentor_peru_direct_pim"]
    direct_top20 = top20_arrays["mentor_peru_direct_pim"]
    plot_board(direct_score, direct_top20, profile)

    cell_km2 = 30.0 * 30.0 / 1e6
    screening_summary_rows = [
        {"metric": "scenario_count", "value": len(all_scenarios)},
        {"metric": "mentor_peru_direct_weights", "value": "flood_hazard=0.34, sediment=0.25, landuse_asm=0.17, environmental=0.10, socioeconomic=0.14"},
        {"metric": "weight_branch", "value": "weights/supervisor-full-spec (Supervisor complete spec, 2026-08-06)"},
        {"metric": "mining_role", "value": "external overlay only; excluded from all current PIM scores"},
        {"metric": "mentor_peru_weight_type", "value": "Supervisor expert-informed provisional weights; no pairwise matrix consistency ratio supplied"},
        {"metric": "scoreable_valid_fraction", "value": round(scoreable_valid_fraction, 6)},
        {"metric": "full_five_criterion_fraction", "value": round(full_five_fraction, 6)},
        {"metric": "incomplete_evidence_fraction", "value": round(incomplete_evidence_fraction, 6)},
        {"metric": "ls_missing_fraction", "value": round(ls_missing_fraction, 6)},
        {"metric": "k_missing_fraction", "value": round(k_missing_fraction, 6)},
        {"metric": "other_missing_fraction", "value": round(other_missing_fraction, 6)},
        {"metric": "unscored_boundary_fraction", "value": round(1.0 - scoreable_valid_fraction, 6)},
        {"metric": "interpretation_domain", "value": "five-criterion common-support cells only; NoData is never converted to low priority or compensated by weight renormalization"},
        {"metric": "direct_top20_cells", "value": int(np.nansum(direct_top20 == 1.0))},
        {"metric": "direct_top20_area_km2", "value": round(float(np.nansum(direct_top20 == 1.0) * cell_km2), 3)},
        {"metric": "pim_main_criteria_count", "value": len(PIM_CRITERIA_ORDER)},
        {"metric": "active_scored_pim_criteria_count", "value": len(ACTIVE_PIM_CRITERIA)},
        {"metric": "component_layer_count", "value": len(COMPONENT_PATHS)},
        {"metric": "active_scored_pim_criteria", "value": ", ".join(ACTIVE_PIM_CRITERIA)},
        {"metric": "component_layers", "value": ", ".join(COMPONENT_PATHS)},
        {"metric": "environmental_sensitivity_status", "value": "provisional; WW/PA recombined in-runner at 0.65/0.35 (Supervisor spec)"},
        {"metric": "socioeconomic_status", "value": "Supervisor three-way split: 0.35 road + 0.35 settlement/population + 0.30 CI (built-density proxy); recombined in-runner"},
        {"metric": "socioeconomic_response_capacity_context_status", "value": "INEI district poverty and OSM health-service remoteness exported outside the AHP overlay"},
    ]
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "pim_subcriteria_weights.csv", build_subcriteria_weight_rows())
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "priority_screening_summary.csv", screening_summary_rows)
    write_csv(OUT_DIR / "component_grid_check.csv", build_grid_check(profile, components))
    write_csv(OUT_DIR / "pim_criteria_grid_check.csv", build_grid_check(profile, criteria))
    manifest_path = OUT_DIR / "run_manifest.json"
    manifest = {
        "boundary_id": boundary_id,
        "experiment_id": experiment_id,
        "claim_level": "sensitivity_scenario",
        "scenario_ids": list(all_scenarios),
        "weights": all_scenarios,
        "mentor_weight_type": (
            "direct recommended weights; no pairwise matrix or consistency ratio supplied"
        ),
        "mining_role": "external overlay only; excluded from PIM calculation",
        "scoreable_valid_fraction": scoreable_valid_fraction,
        "full_five_criterion_fraction": full_five_fraction,
        "incomplete_evidence_fraction": incomplete_evidence_fraction,
        "ls_missing_fraction": ls_missing_fraction,
        "k_missing_fraction": k_missing_fraction,
        "other_missing_fraction": other_missing_fraction,
        "unscored_boundary_fraction": 1.0 - scoreable_valid_fraction,
        "interpretation_domain": (
            "five-criterion common-support cells only; NoData is never converted to low "
            "priority or compensated by weight renormalization"
        ),
        "script": {
            "path": rel(Path(__file__)),
            "sha256": sha256(Path(__file__)),
        },
        "git": git_state(),
        "inputs": [
            {"path": rel(path), "sha256": sha256(path)}
            for path in INPUTS
        ],
        "outputs": [
            {"path": rel(path), "sha256": sha256(path)}
            for path in OUTPUTS
            if path != manifest_path
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    direct_area = next(
        row["value"] for row in screening_summary_rows
        if row["metric"] == "direct_top20_area_km2"
    )
    print(f"wrote Peru-first priority scenarios to {rel(OUT_DIR)}")
    print(f"  scoreable coverage: {scoreable_valid_fraction:.6f}")
    print(f"  full five-criterion coverage: {full_five_fraction:.6f}")
    print(f"  highest-priority quintile area: {direct_area} km2")
    print("  Supervisor-spec weights: 0.34 FH, 0.25 SE, 0.17 LU, 0.10 ES, 0.14 SV")
    print("  weight branch: weights/supervisor-full-spec")
    print("  mining: external overlay only; excluded from the PIM calculation")
    print("  socioeconomic: Supervisor three-way split (road 0.35 + pop 0.35 + CI-proxy 0.30)")


if __name__ == "__main__":
    main()
