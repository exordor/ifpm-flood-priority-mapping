#!/usr/bin/env python3
"""Build grid-compatible Arequipa Region component rasters for the PIM criteria.

Mirrors `build_boundary_v1_criteria_stack.py` plus the rainfall criterion
sensitivity layer. Arequipa Region follows the mentor 5-main-criterion AHP framework. This
script prepares the component rasters that are combined later into PIM main
criteria:
flood_conditioning, SoilGrids K, LS, RUSLE C, land_cover_pressure,
road_access_proximity (OSM roads), and rainfall_climatology (CHIRPS
coarse-to-grid, sensitivity). Mining is maintained outside this active
criteria stack for post-PIM overlay and spatial interpretation only.

Outputs standardized 0-1 rasters on the Arequipa Region 30m reference grid (EPSG:32718).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask

ROOT = Path(__file__).resolve().parents[2]
RASTER_INPUTS = {
    "twi": ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/peru_hybas_l7_6070641200_twi.tif",
    "drainage": ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/peru_hybas_l7_6070641200_distance_to_drainage_t500.tif",
    "ls_factor": ROOT / "outputs/srtm_1arcsec_peru_pilot/ls_factor/peru_hybas_l7_6070641200_ls_factor_capped50_hillslope_30m.tif",
    "c_factor": ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_peru_hybas_l7_6070641200_30m.tif",
    "soil_k_factor": ROOT / "outputs/srtm_1arcsec_peru_pilot/soil_k_factor/soil_k_factor_0_1.tif",
    "land_cover_runoff_pressure": ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/land_cover_runoff_pressure_peru_hybas_l7_6070641200_30m.tif",
    "bare_soil_vegetation_loss": ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/bare_soil_vegetation_loss_proxy_peru_hybas_l7_6070641200_30m.tif",
    "built_up_pressure": ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/built_up_pressure_peru_hybas_l7_6070641200_30m.tif",
    "agricultural_pressure": ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/agricultural_pressure_peru_hybas_l7_6070641200_30m.tif",
    "road_access_proximity": ROOT / "outputs/geofabrik_osm_peru_pilot/peru_hybas_l7_6070641200_proximity/closeness_to_roads_0_1.tif",
    "rainfall": ROOT / "outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/rainfall_climatology_0_1_PROVISIONAL_30m.tif",
}

INPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/peru_hybas_l7_6070641200_twi.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/peru_hybas_l7_6070641200_distance_to_drainage_t500.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/ls_factor/peru_hybas_l7_6070641200_ls_factor_capped50_hillslope_30m.tif",
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_peru_hybas_l7_6070641200_30m.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/soil_k_factor/soil_k_factor_0_1.tif",
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/land_cover_runoff_pressure_peru_hybas_l7_6070641200_30m.tif",
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/bare_soil_vegetation_loss_proxy_peru_hybas_l7_6070641200_30m.tif",
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/built_up_pressure_peru_hybas_l7_6070641200_30m.tif",
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/agricultural_pressure_peru_hybas_l7_6070641200_30m.tif",
    ROOT / "outputs/geofabrik_osm_peru_pilot/peru_hybas_l7_6070641200_proximity/closeness_to_roads_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/rainfall_climatology_0_1_PROVISIONAL_30m.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]


OUTPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_conditioning_factors_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/twi_wetness_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/drainage_proximity_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/ls_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/c_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/soil_k_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/bare_soil_vegetation_loss_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/built_agriculture_road_expansion_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/road_access_proximity_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/rainfall_climatology_0_1.tif",
]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
from _lib.ifpm_tools import raster_stats as stats
BOUNDARY_ID = "peru_hybas_l7_6070641200"
EXPERIMENT_ID = "criteria_stack"
OUT_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/{EXPERIMENT_ID}"
CRITERIA_DIR = OUT_DIR / "criteria"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif"
PERU_HYBAS_L7_6070641200_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
# A 0.95 component gate catches tile/data gaps while allowing the documented
# hillslope LS channel mask and limited SoilGrids K support to remain NoData.
MIN_VALID_FRACTION = 0.95

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


def read_reference() -> tuple[dict, np.ndarray]:
    with rasterio.open(REF) as ref:
        profile = ref.profile.copy()
        crs = ref.crs
        shape = (ref.height, ref.width)
        transform = ref.transform
    boundary = gpd.read_file(PERU_HYBAS_L7_6070641200_GPKG, layer="peru_pilot_boundary").to_crs(crs)
    mask = geometry_mask(boundary.geometry, out_shape=shape, transform=transform, invert=True)
    return profile, mask


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


def normalize_2_98(data: np.ndarray, mask: np.ndarray, invert: bool = False) -> tuple[np.ndarray, float, float]:
    """2-98 percentile min-max. invert=True for distance (closer=higher value)."""
    values = data[mask & np.isfinite(data)]
    if values.size == 0:
        raise ValueError("cannot normalize empty raster")
    low, high = np.nanpercentile(values, [2, 98])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise ValueError(f"bad percentile range: {low}, {high}")
    out = np.clip((data - low) / (high - low), 0.0, 1.0).astype("float32")
    if invert:
        out = 1.0 - out
    out[~mask] = np.nan
    return out.astype("float32"), float(low), float(high)


def weighted_average(parts: list[tuple[np.ndarray, float]], mask: np.ndarray) -> np.ndarray:
    numerator = np.zeros(mask.shape, dtype="float32")
    denominator = np.zeros(mask.shape, dtype="float32")
    for layer, weight in parts:
        valid = mask & np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        denominator[valid] += weight
    out = np.divide(numerator, denominator, out=np.full(mask.shape, np.nan, dtype="float32"), where=denominator > 0)
    out[~mask] = np.nan
    return out.astype("float32")


def build_be_proxy(
    built_up: np.ndarray,
    agriculture: np.ndarray,
    road_access: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    """Build BE without penalizing mutually exclusive built/agriculture classes."""

    developed_or_agricultural = np.maximum(built_up, agriculture)
    return weighted_average(
        [(developed_or_agricultural, 0.50), (road_access, 0.50)],
        mask,
    )


def valid_fraction(data: np.ndarray, mask: np.ndarray) -> float:
    inside = int(mask.sum())
    if inside == 0:
        return 0.0
    return float((mask & np.isfinite(data)).sum() / inside)
def main() -> None:
    opts = parse_script_args(boundary_id=BOUNDARY_ID, experiment_id=EXPERIMENT_ID)
    boundary_id = opts.get("boundary_id", BOUNDARY_ID)
    experiment_id = opts.get("experiment_id", EXPERIMENT_ID)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    (CRITERIA_DIR / "soil_erosion_factors_0_1.tif").unlink(missing_ok=True)
    (CRITERIA_DIR / "exposure_indicators_0_1.tif").unlink(missing_ok=True)
    profile, mask = read_reference()
    rasters = {key: read_band(path, profile) for key, path in RASTER_INPUTS.items()}

    # Standardize TWI, drainage, LS, and C. SoilGrids K is already aligned and
    # normalized by its dedicated builder.
    twi_std, twi_lo, twi_hi = normalize_2_98(rasters["twi"], mask, invert=False)
    drain_std, drain_lo, drain_hi = normalize_2_98(rasters["drainage"], mask, invert=True)
    ls_std, ls_lo, ls_hi = normalize_2_98(rasters["ls_factor"], mask, invert=False)
    c_std, c_lo, c_hi = normalize_2_98(rasters["c_factor"], mask, invert=False)
    # K, land use, and roads are already 0-1 scored rasters.
    soil_k_std = rasters["soil_k_factor"]
    land_use_std = rasters["land_cover_runoff_pressure"]
    bare_soil_vegetation_loss = rasters["bare_soil_vegetation_loss"]
    road_access_std = rasters["road_access_proximity"]
    built_agriculture_road_expansion = build_be_proxy(
        rasters["built_up_pressure"],
        rasters["agricultural_pressure"],
        road_access_std,
        mask,
    )

    criteria = {
        "flood_conditioning_factors": weighted_average([(twi_std, 0.5), (drain_std, 0.5)], mask),
        "twi_wetness": twi_std,
        "drainage_proximity": drain_std,
        "ls_factor": ls_std,
        "c_factor": c_std,
        "soil_k_factor": soil_k_std,
        "land_cover_pressure": land_use_std,
        "bare_soil_vegetation_loss": bare_soil_vegetation_loss,
        "built_agriculture_road_expansion": built_agriculture_road_expansion,
        "road_access_proximity": road_access_std,
        "rainfall_climatology": rasters["rainfall"],
    }

    manifest_rows = []
    components_map = {
        "flood_conditioning_factors": "TWI high-wetness + drainage proximity (inverted)",
        "twi_wetness": "DEM-derived TWI standardized high wetness -> high flood susceptibility",
        "drainage_proximity": "distance to drainage standardized as closer drainage -> higher flood susceptibility",
        "ls_factor": "SRTM-derived LS-factor, capped at 50, hillslope/channel mask preserved",
        "c_factor": "ESA WorldCover RUSLE C-factor used only in the Sediment criterion",
        "soil_k_factor": "SoilGrids 250 m K aligned to the 30 m reference grid; effective resolution remains 250 m",
        "land_cover_pressure": "LC: provisional WorldCover land-cover runoff-pressure value function",
        "bare_soil_vegetation_loss": "BV: WorldCover bare/sparse-cover proxy; single-date data cannot measure vegetation loss",
        "built_agriculture_road_expansion": "BE: 0.50 max(current built-up, current agriculture) + 0.50 road proximity; test proxy, not temporal expansion",
        "road_access_proximity": "OSM roads proximity (inverted); access indicator used upstream of the combined socioeconomic criterion",
        "rainfall_climatology": "CHIRPS latam Dec-Mar mean coarse-to-grid (sensitivity_scenario)",
    }
    claim_map = {
        "flood_conditioning_factors": "provisional",
        "twi_wetness": "provisional",
        "drainage_proximity": "provisional",
        "ls_factor": "diagnostic_only",
        "c_factor": "provisional",
        "soil_k_factor": "provisional",
        "land_cover_pressure": "provisional",
        "bare_soil_vegetation_loss": "sensitivity_scenario",
        "built_agriculture_road_expansion": "sensitivity_scenario",
        "road_access_proximity": "provisional",
        "rainfall_climatology": "sensitivity_scenario",
    }
    for name, arr in criteria.items():
        path = CRITERIA_DIR / f"{name}_0_1.tif"
        arr = np.clip(arr, 0.0, 1.0).astype("float32")
        arr[~mask] = np.nan
        frac = valid_fraction(arr, mask)
        write_raster(path, arr, profile)
        manifest_rows.append({
            "boundary_id": boundary_id, "experiment_id": experiment_id,
            "criterion": name, "path": rel(path),
            "components": components_map[name], "claim_level": claim_map[name],
            "status": "provisional southern Peru comparison-catchment criterion",
            "grid_compatible": "true" if frac >= MIN_VALID_FRACTION else "false",
            "coverage_threshold": MIN_VALID_FRACTION,
            "nodata_policy": (
                "preserve NoData; inherits intentional channel mask from hillslope LS"
                if name == "ls_factor" else "preserve NoData; no score imputation"
            ),
            **stats(arr, mask),
        })

    # Readiness table: these are component rasters mapped into the mentor
    # 5-main-criterion framework by run_peru_hybas_l7_6070641200_priority_scenarios.py.
    readiness = manifest_rows

    write_csv(OUT_DIR / "criteria_stack_manifest.csv", manifest_rows)
    write_csv(OUT_DIR / "criteria_readiness_table.csv", readiness)
    write_csv(OUT_DIR / "standardization_notes.csv", [
        {"component": "twi", "method": "percentile_clip_minmax_2_98", "clip_low": twi_lo, "clip_high": twi_hi},
        {"component": "drainage", "method": "percentile_clip_minmax_2_98_inverted", "clip_low": drain_lo, "clip_high": drain_hi},
        {"component": "ls_factor", "method": "percentile_clip_minmax_2_98", "clip_low": ls_lo, "clip_high": ls_hi},
        {"component": "c_factor", "method": "percentile_clip_minmax_2_98", "clip_low": c_lo, "clip_high": c_hi},
    ])
    low_coverage = [
        row for row in manifest_rows
        if float(row["valid_fraction"]) < MIN_VALID_FRACTION
    ]
    if low_coverage:
        details = ", ".join(f"{row['criterion']}={row['valid_fraction']}" for row in low_coverage)
        raise RuntimeError(f"Arequipa Region active criterion coverage below {MIN_VALID_FRACTION}: {details}")
    print(f"wrote {len(manifest_rows)} Arequipa Region scored layers to {rel(CRITERIA_DIR)}")
    print("(component rasters for the 5 PIM main criteria; overlay happens in run_peru_hybas_l7_6070641200_priority_scenarios.py)")


if __name__ == "__main__":
    main()
