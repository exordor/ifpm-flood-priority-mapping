#!/usr/bin/env python3
"""Build a CHIRPS-derived rainfall criterion on the PE1 reference grid.

Mirrors `build_boundary_v1_rainfall_criterion_v0_3.py` but for Peru PE1. Differences:
- source: CHIRPS v3 latam (Latin America) monthly GeoTIFFs, not Africa;
- rainy season: Dec-Mar (southern Peru austral summer), same months as Zimbabwe's Nov-Mar
  choice (Zimbabwe also uses Nov-Mar); 
- reference grid: PE1 EPSG:32718 30m, not Zimbabwe EPSG:32735.

GOVERNANCE: CHIRPS is ~5 km native. This is an explicitly labelled coarse-to-reference-grid
resample, allowed ONLY as a `sensitivity_scenario` input, never as native 30 m rainfall evidence
(per peru_pilot_terrain_reference_grid_rule.md and AGENTS.md CHIRPS rules). The output carries
an IFPM_NOTE band tag and the _PROVISIONAL_30m suffix.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import reproject, Resampling
from scipy.ndimage import distance_transform_edt, label as ndimage_label

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
BOUNDARY_ID = "pe1"
EXPERIMENT_ID = "rainfall_criterion"
OUT_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/{EXPERIMENT_ID}"

REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"

CHIRPS_BASE = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/latam/tifs"
# Climatological rainy-season mean over Dec-Mar for a recent window. Use 2014/15-2023/24
# (10 seasons) for a stable recent climatology comparable to Zimbabwe's 1981-2024 long-term.
SEASON_YEARS = list(range(2014, 2024))  # each year y -> Dec(y), Jan(y+1), Feb(y+1), Mar(y+1)
RAINY_MONTHS = [12, 1, 2, 3]

CRITERION_NAME = "rainfall_climatology_proxy"
CLAIM_LEVEL = "sensitivity_scenario"
IFPM_NOTE = (
    "SENSITIVITY SCENARIO ONLY: 0.05 deg CHIRPS latam Dec-Mar rainy-season mean resampled to "
    "30 m via bilinear for overlay compatibility. NOT pixel-level 30 m rainfall evidence. "
    "Do not use for final flood-risk or intervention-priority claims."
)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def pe1_window_lonlat() -> tuple[float, float, float, float]:
    b = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs("EPSG:4326")
    minx, miny, maxx, maxy = b.total_bounds
    pad = 0.2  # ~20km pad for the resample edge
    return minx - pad, miny - pad, maxx + pad, maxy + pad


def read_chirps_month_window(year: int, month: int, win_bounds) -> tuple[np.ndarray, dict]:
    """HTTP-windowed read of one CHIRPS latam monthly file for the PE1 bbox."""
    url = f"{CHIRPS_BASE}/chirps-v3.0.{year}.{month:02d}.tif"
    minx, miny, maxx, maxy = win_bounds
    with rasterio.open(url) as src:
        from rasterio.windows import from_bounds
        win = from_bounds(minx, miny, maxx, maxy, src.transform)
        win = win.round_offsets().round_lengths()
        data = src.read(1, window=win).astype("float32")
        nodata = src.nodata
        profile = src.profile.copy()
        win_transform = src.window_transform(win)
    if nodata is not None:
        data[data == nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data, {"transform": win_transform, "crs": "EPSG:4326", "width": win.width, "height": win.height}


def fetch_rainy_season_mean(win_bounds) -> tuple[np.ndarray, dict]:
    """Mean of Dec-Mar monthly rainfall over the season window, on the native 0.05 grid."""
    season_means = []
    ref_meta = None
    for y in SEASON_YEARS:
        months_data = []
        for m in RAINY_MONTHS:
            yy = y if m == 12 else y + 1
            arr, meta = read_chirps_month_window(yy, m, win_bounds)
            months_data.append(arr)
            ref_meta = ref_meta or meta
        season_total = np.nansum(months_data, axis=0)  # Dec+Jan+Feb+Mar accumulation
        season_means.append(season_total)
    mean = np.nanmean(season_means, axis=0).astype("float32")
    return mean, ref_meta


def resample_to_reference(native_arr: np.ndarray, native_meta: dict, ref_profile: dict) -> np.ndarray:
    dst = np.full((ref_profile["height"], ref_profile["width"]), np.nan, dtype="float64")
    reproject(
        source=native_arr, destination=dst,
        src_transform=native_meta["transform"], src_crs=native_meta["crs"], src_nodata=np.nan,
        dst_transform=ref_profile["transform"], dst_crs=ref_profile["crs"],
        resampling=Resampling.bilinear, dst_nodata=np.nan,
    )
    dst[~np.isfinite(dst)] = np.nan
    return dst


def pe1_inside_mask(ref_profile: dict) -> np.ndarray:
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(ref_profile["crs"])
    return geometry_mask(
        [boundary.geometry.iloc[0].__geo_interface__],
        out_shape=(ref_profile["height"], ref_profile["width"]),
        transform=ref_profile["transform"], invert=True,
    )


def fill_edge_nodata(data: np.ndarray, inside: np.ndarray) -> tuple[np.ndarray, dict[str, int]]:
    work = data.astype("float64").copy()
    holes = inside & ~np.isfinite(work)
    if not holes.any():
        return work, {"hole_cells": 0, "interior_holes": 0, "edge_sliver_holes": 0}
    outside = ~inside
    labeled, n = ndimage_label(holes)
    interior = edge_sliver = 0
    for i in range(1, n + 1):
        region = labeled == i
        dilated = np.zeros_like(region)
        dilated[1:-1, 1:-1] = (
            region[2:, 1:-1] | region[:-2, 1:-1] | region[1:-1, 2:] | region[1:-1, :-2]
            | region[2:, 2:] | region[2:, :-2] | region[:-2, 2:] | region[:-2, :-2]
        )
        if (dilated & outside).any():
            edge_sliver += 1
        else:
            interior += 1
    valid_inside = inside & np.isfinite(work)
    _, (row_idx, col_idx) = distance_transform_edt(~valid_inside, return_indices=True)
    filled = work[row_idx, col_idx]
    filled[~inside] = np.nan
    return filled, {"hole_cells": int(holes.sum()), "interior_holes": interior, "edge_sliver_holes": edge_sliver}
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(REF) as ref:
        ref_profile = ref.profile.copy()
    inside = pe1_inside_mask(ref_profile)
    inside_total = int(inside.sum())

    win_bounds = pe1_window_lonlat()
    print(f"fetching CHIRPS latam Dec-Mar rainy-season mean over {len(SEASON_YEARS)} seasons ...")
    native_mean, native_meta = fetch_rainy_season_mean(win_bounds)
    print(f"  native 0.05 deg mean range: {np.nanmin(native_mean):.1f}-{np.nanmax(native_mean):.1f} mm/season")

    raw = resample_to_reference(native_mean, native_meta, ref_profile)
    raw_valid_before = int((inside & np.isfinite(raw)).sum())
    raw, fill_stats = fill_edge_nodata(raw, inside)
    raw_valid_after = int((inside & np.isfinite(raw)).sum())
    valid = np.isfinite(raw)
    if fill_stats["interior_holes"] > 0:
        raise ValueError(f"{fill_stats['interior_holes']} interior hole(s); refusing to impute real gaps")

    raw_min = float(np.nanmin(raw)); raw_mean = float(np.nanmean(raw)); raw_max = float(np.nanmax(raw))
    if raw_max <= 0:
        raise ValueError(f"non-positive rainfall range, max={raw_max}")
    score = np.clip(raw / raw_max, 0.0, 1.0).astype("float32")
    score[~valid] = np.nan

    raw_path = OUT_DIR / f"{CRITERION_NAME}_raw_mm_per_season_PROVISIONAL_30m.tif"
    score_path = OUT_DIR / f"{CRITERION_NAME}_0_1_PROVISIONAL_30m.tif"
    write_raster(raw_path, raw, ref_profile, ifpm_note=IFPM_NOTE)
    write_raster(score_path, score, ref_profile, ifpm_note=IFPM_NOTE)

    manifest = [
        {"field": "criterion_name", "value": CRITERION_NAME},
        {"field": "claim_level", "value": CLAIM_LEVEL},
        {"field": "source", "value": "CHIRPS v3.0 latam monthly GeoTIFFs (HTTP windowed read)"},
        {"field": "season_definition", "value": "Dec-Mar rainy season (austral summer), mean over 2014/15-2023/24"},
        {"field": "native_resolution", "value": "0.05 deg (~5 km) CHIRPS v3.0 latam"},
        {"field": "target_grid", "value": "PE1 reference: EPSG:32718, 30 m"},
        {"field": "resampling_method", "value": "bilinear"},
        {"field": "effective_resolution_warning", "value": "Effective resolution ~5 km despite 30 m cells; smooth climatology, NOT pixel-level rainfall"},
        {"field": "raw_min_mm_per_season", "value": round(raw_min, 3)},
        {"field": "raw_mean_mm_per_season", "value": round(raw_mean, 3)},
        {"field": "raw_max_mm_per_season", "value": round(raw_max, 3)},
        {"field": "valid_fraction_after_edge_fill", "value": round(raw_valid_after / inside_total, 6)},
        {"field": "fill_edge_sliver_holes", "value": fill_stats["edge_sliver_holes"]},
        {"field": "fill_interior_holes", "value": fill_stats["interior_holes"]},
        {"field": "built", "value": str(date.today())},
    ]
    with (OUT_DIR / f"{CRITERION_NAME}_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["field", "value"])
        w.writeheader()
        w.writerows(manifest)

    print(f"resampled Dec-Mar mean: {raw_min:.1f}-{raw_max:.1f} mm/season -> 0-1 score")
    print(f"edge slivers: {fill_stats['edge_sliver_holes']}, interior: {fill_stats['interior_holes']}")
    print(f"valid inside PE1: {raw_valid_after/inside_total:.4f}")
    print(f"wrote {rel(score_path)}")


if __name__ == "__main__":
    main()
