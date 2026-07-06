#!/usr/bin/env python3
"""Build grid-compatible PE1 component rasters for the PIM criteria.

Mirrors `build_boundary_v1_criteria_stack_v0_2.py` plus the v0.3 rainfall
sensitivity layer. PE1 follows the mentor 5-main-criterion AHP framework. This
script prepares the component rasters that are combined later into PIM main
criteria:
flood_conditioning, soil_erosion_factors, land_cover_pressure,
mining_pressure (INGEMMET), exposure_indicators (OSM roads), and
rainfall_climatology (CHIRPS coarse-to-grid, sensitivity).

Outputs standardized 0-1 rasters on the PE1 30m reference grid (EPSG:32718).
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
INPUTS = {
    "twi": ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_twi.tif",
    "drainage": ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_distance_to_drainage_t500.tif",
    "ls_factor": ROOT / "outputs/srtm_1arcsec_peru_pilot/ls_factor/pe1_ls_factor_capped50_hillslope_30m.tif",
    "structure": ROOT / "outputs/srtm_1arcsec_peru_pilot/usle_soil_loss/a_structure_K_LS_C_30m.tif",
    "c_factor": ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_pe1_30m.tif",
    "roads": ROOT / "outputs/geofabrik_osm_peru_pilot/pe1_proximity/closeness_to_roads_0_1.tif",
    "mining": ROOT / "outputs/ingemmet_catastro_minero_peru_pilot/pe1_mining_pressure_ingemmet_0_1.tif",
    "rainfall": ROOT / "outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/rainfall_climatology_0_1_PROVISIONAL_30m.tif",
}


OUTPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_conditioning_factors_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/twi_wetness_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/drainage_proximity_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/soil_erosion_factors_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/ls_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/c_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/mining_pressure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/exposure_indicators_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/rainfall_climatology_0_1.tif",
]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
from _lib.ifpm_tools import raster_stats as stats
BOUNDARY_ID = "pe1"
EXPERIMENT_ID = "criteria_stack"
OUT_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/{EXPERIMENT_ID}"
CRITERIA_DIR = OUT_DIR / "criteria"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
# PE1 erosion_structure intentionally inherits hillslope LS NoData on main-channel cells
# (about 3.8% of PE1). A 0.95 gate catches tile/data gaps such as the old C-factor seam
# while allowing this documented channel mask to remain NoData instead of being filled.
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
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(crs)
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
    profile, mask = read_reference()
    rasters = {key: read_band(path, profile) for key, path in INPUTS.items()}

    # Standardize: TWI high->high (wetness), drainage inverted (closer->higher),
    # LS/C high->high for diagnostics, and K x LS x C structure high->high for
    # the current executable sediment criterion. SoilGrids K remains embedded as
    # the current scalar K in the structure layer until a grid-compatible K raster
    # is rebuilt.
    twi_std, twi_lo, twi_hi = normalize_2_98(rasters["twi"], mask, invert=False)
    drain_std, drain_lo, drain_hi = normalize_2_98(rasters["drainage"], mask, invert=True)
    ls_std, ls_lo, ls_hi = normalize_2_98(rasters["ls_factor"], mask, invert=False)
    structure_std, s_lo, s_hi = normalize_2_98(rasters["structure"], mask, invert=False)
    c_std, c_lo, c_hi = normalize_2_98(rasters["c_factor"], mask, invert=False)
    # roads + mining are already 0-1 proximity rasters from build_pe1_osm_proximity_criteria.py
    roads_std = rasters["roads"]
    mining_std = rasters["mining"]

    criteria = {
        "flood_conditioning_factors": weighted_average([(twi_std, 0.5), (drain_std, 0.5)], mask),
        "twi_wetness": twi_std,
        "drainage_proximity": drain_std,
        "soil_erosion_factors": structure_std,
        "ls_factor": ls_std,
        "c_factor": c_std,
        "land_cover_pressure": c_std,
        "mining_pressure": mining_std,
        "exposure_indicators": roads_std,
        "rainfall_climatology": rasters["rainfall"],
    }

    manifest_rows = []
    components_map = {
        "flood_conditioning_factors": "TWI high-wetness + drainage proximity (inverted)",
        "twi_wetness": "DEM-derived TWI standardized high wetness -> high flood susceptibility",
        "drainage_proximity": "distance to drainage standardized as closer drainage -> higher flood susceptibility",
        "soil_erosion_factors": "K x LS x C erosion source structure standardized 2-98; rainfall erosivity not applied",
        "ls_factor": "SRTM-derived LS-factor, capped at 50, hillslope/channel mask preserved",
        "c_factor": "ESA WorldCover C-factor pressure, also used as land-cover pressure evidence",
        "land_cover_pressure": "WorldCover C-factor pressure",
        "mining_pressure": "INGEMMET Pequeña Minería ASM-point proximity (inverted); official source",
        "exposure_indicators": "OSM roads proximity (inverted); access/exposure indicator",
        "rainfall_climatology": "CHIRPS latam Dec-Mar mean coarse-to-grid (sensitivity_scenario)",
    }
    claim_map = {
        "flood_conditioning_factors": "provisional",
        "twi_wetness": "provisional",
        "drainage_proximity": "provisional",
        "soil_erosion_factors": "diagnostic_only",
        "ls_factor": "diagnostic_only",
        "c_factor": "provisional",
        "land_cover_pressure": "provisional",
        "mining_pressure": "provisional",
        "exposure_indicators": "provisional",
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
                if name in {"soil_erosion_factors", "ls_factor"} else "preserve NoData; no score imputation"
            ),
            **stats(arr, mask),
        })

    # Readiness table: these are component rasters mapped into the mentor
    # 5-main-criterion framework by run_pe1_priority_scenarios.py.
    readiness = manifest_rows + [
        {"criterion": "rainfall_r_factor", "path": "", "components": "provisional R=238.6 (LOW family, shared default)",
         "status": "scalar R in soil-loss (absolute magnitude); the rainfall_climatology criterion handles the spatial overlay role",
         "grid_compatible": "not_applicable"},
    ]

    write_csv(OUT_DIR / "criteria_stack_manifest.csv", manifest_rows)
    write_csv(OUT_DIR / "criteria_readiness_table.csv", readiness)
    write_csv(OUT_DIR / "standardization_notes.csv", [
        {"component": "twi", "method": "percentile_clip_minmax_2_98", "clip_low": twi_lo, "clip_high": twi_hi},
        {"component": "drainage", "method": "percentile_clip_minmax_2_98_inverted", "clip_low": drain_lo, "clip_high": drain_hi},
        {"component": "structure", "method": "percentile_clip_minmax_2_98", "clip_low": s_lo, "clip_high": s_hi},
        {"component": "ls_factor", "method": "percentile_clip_minmax_2_98", "clip_low": ls_lo, "clip_high": ls_hi},
        {"component": "c_factor", "method": "percentile_clip_minmax_2_98", "clip_low": c_lo, "clip_high": c_hi},
    ])
    low_coverage = [
        row for row in manifest_rows
        if float(row["valid_fraction"]) < MIN_VALID_FRACTION
    ]
    if low_coverage:
        details = ", ".join(f"{row['criterion']}={row['valid_fraction']}" for row in low_coverage)
        raise RuntimeError(f"PE1 active criterion coverage below {MIN_VALID_FRACTION}: {details}")
    print(f"wrote {len(manifest_rows)} PE1 scored layers to {rel(CRITERIA_DIR)}")
    print("(component rasters for the 5 PIM main criteria; overlay happens in run_pe1_priority_scenarios.py)")


if __name__ == "__main__":
    main()
