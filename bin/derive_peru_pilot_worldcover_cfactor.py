#!/usr/bin/env python3
"""Derive USLE/RUSLE C-factor for PE1 from ESA WorldCover 2021.

Mirrors `derive_v1_worldcover_cfactor.py`. Peru differences: S18W072 tile, PE1 boundary,
PE1 reference DEM (EPSG:32718). Same RUSLE C-factor lookup table (literature-derived, identical
for both countries), same MODE-resample-then-lookup approach.

Outputs: C-factor on the WorldCover native 10m grid clipped to PE1, and C-factor on the PE1 30m
reference grid (MODE resample 10m->30m, legitimate fine->coarse aggregation, then lookup).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]

WORLDCOVER_TILE = ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W072_Map.tif"
PE1_BOUNDARY_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
PE1_BOUNDARY_LAYER = "peru_pilot_boundary"
PE1_REFERENCE_DEM = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
OUTPUT_DIR = ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor"
GRID_CHECK_TOOL = ROOT / "bin/check_v1_raster_grid.py"

NODATA = -9999.0

# ESA WorldCover v200 class code -> (label, RUSLE C-factor). Identical to the Zimbabwe LUT.
C_FACTOR_LUT: dict[int, tuple[str, float]] = {
    10:  ("Tree cover", 0.003),
    20:  ("Shrubland", 0.040),
    30:  ("Grassland", 0.030),
    40:  ("Cropland", 0.230),
    50:  ("Built-up", 0.000),
    60:  ("Bare / sparse vegetation", 0.700),
    70:  ("Snow / ice", 0.000),
    80:  ("Permanent water bodies", 0.000),
    90:  ("Herbaceous wetland", 0.050),
    95:  ("Mangroves", 0.010),
    100: ("Moss / lichen", 0.030),
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_pe1_boundary() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(PE1_BOUNDARY_GPKG, layer=PE1_BOUNDARY_LAYER)
    if len(gdf) != 1:
        raise ValueError(f"Expected exactly one PE1 boundary feature, got {len(gdf)}")
    return gdf


def worldcover_window(bounds4326: tuple[float, float, float, float], pad_deg: float):
    minx, miny, maxx, maxy = bounds4326
    with rasterio.open(WORLDCOVER_TILE) as src:
        win = from_bounds(minx - pad_deg, miny - pad_deg, maxx + pad_deg, maxy + pad_deg, src.transform)
        win = win.round_offsets().round_lengths()
        win_transform = src.window_transform(win)
        arr = src.read(1, window=win)
        profile = src.profile.copy()
    return arr, win_transform, profile


def class_to_c(class_arr: np.ndarray) -> np.ndarray:
    out = np.full(class_arr.shape, np.nan, dtype="float32")
    for code, (_label, cval) in C_FACTOR_LUT.items():
        out[class_arr == code] = cval
    return out


def mask_on_grid(geometry, transform, shape) -> np.ndarray:
    return rasterize(
        [(geometry, 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8", all_touched=False
    ) == 1


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bnd = load_pe1_boundary()
    geom4326 = bnd.to_crs("EPSG:4326").geometry.iloc[0]
    bounds4326 = geom4326.bounds

    # 1. native 10m C-factor clipped to PE1
    class_arr, wc_transform, wc_profile = worldcover_window(bounds4326, pad_deg=0.01)
    pe1_mask_native = mask_on_grid(geom4326, wc_transform, class_arr.shape)
    c_native = class_to_c(class_arr)
    c_native_masked = np.where(pe1_mask_native, c_native, np.nan)

    native_profile = wc_profile.copy()
    native_profile.update(dtype="float32", nodata=NODATA, compress="deflate", tiled=True)
    c_native_out = np.where(np.isfinite(c_native_masked), c_native_masked, NODATA).astype("float32")
    with rasterio.open(OUTPUT_DIR / "c_factor_pe1_10m.tif", "w", **native_profile) as ds:
        ds.write(c_native_out, 1)
    print(f"wrote {OUTPUT_DIR / 'c_factor_pe1_10m.tif'}")

    # 2. PE1 30m grid: MODE resample 10m->30m (fine->coarse aggregation), then lookup
    with rasterio.open(PE1_REFERENCE_DEM) as ref:
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_width, ref_height = ref.width, ref.height
        ref_profile = ref.profile.copy()

    bnd_ref = bnd.to_crs(ref_crs)
    pe1_mask_ref = mask_on_grid(bnd_ref.geometry.iloc[0], ref_transform, (ref_height, ref_width))

    class_30m = np.full((ref_height, ref_width), 0, dtype="uint8")
    reproject(
        source=class_arr, destination=class_30m,
        src_transform=wc_transform, src_crs="EPSG:4326", src_nodata=0,
        dst_transform=ref_transform, dst_crs=ref_crs, dst_nodata=0,
        resampling=Resampling.mode,
    )
    c_30m = class_to_c(class_30m.astype("int32"))
    c_30m_masked = np.where(pe1_mask_ref, c_30m, np.nan)

    out_profile = ref_profile.copy()
    out_profile.update(dtype="float32", nodata=NODATA, count=1, compress="deflate", tiled=True)
    c_30m_out = np.where(np.isfinite(c_30m_masked), c_30m_masked, NODATA).astype("float32")
    with rasterio.open(OUTPUT_DIR / "c_factor_pe1_30m.tif", "w", **out_profile) as ds:
        ds.write(c_30m_out, 1)
    print(f"wrote {OUTPUT_DIR / 'c_factor_pe1_30m.tif'}")

    # 3. stats + class-area on PE1 (30m)
    valid = np.isfinite(c_30m_masked) & pe1_mask_ref
    c_vals = c_30m_masked[valid]
    cell_area = 30.0 * 30.0 / 1e6  # km2
    class_area_km2 = {}
    for code, (label, cval) in C_FACTOR_LUT.items():
        n = int(((class_30m == code) & pe1_mask_ref).sum())
        if n:
            class_area_km2[f"{code}_{label}"] = round(n * cell_area, 2)

    diag = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/derive_peru_pilot_worldcover_cfactor.py",
        "source_tile": rel(WORLDCOVER_TILE),
        "lut": "RUSLE C-factor lookup (literature-derived; identical to Zimbabwe LUT)",
        "resample_method": "MODE (10m->30m, legitimate fine->coarse aggregation); lookup applied AFTER resample",
        "boundary_status": "engineering_pilot_not_research_selected",
        "c_factor_30m_stats": {
            "valid_cells": int(valid.sum()),
            "mean": round(float(np.mean(c_vals)), 4) if c_vals.size else None,
            "min": round(float(np.min(c_vals)), 4) if c_vals.size else None,
            "max": round(float(np.max(c_vals)), 4) if c_vals.size else None,
        },
        "class_area_km2_on_pe1_30m": class_area_km2,
        "zimbabwe_v1_reference_mean_c": 0.0429,
    }
    (OUTPUT_DIR / "c_factor_diagnostics.json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
    print(f"\nPE1 C-factor (30m): mean {diag['c_factor_30m_stats']['mean']} "
          f"[{diag['c_factor_30m_stats']['min']} - {diag['c_factor_30m_stats']['max']}] "
          f"(ZW V1 ref mean 0.0429)")
    print("class area (km2):", class_area_km2)

    # 4. grid gate (with PE1 boundary)
    print("[gate] running check_v1_raster_grid.py ...")
    cmd = [sys.executable, str(GRID_CHECK_TOOL),
           "--reference", str(PE1_REFERENCE_DEM),
           "--boundary", str(PE1_BOUNDARY_GPKG), "--boundary-layer", PE1_BOUNDARY_LAYER,
           "--output", str(OUTPUT_DIR / "c_factor_grid_check.csv"),
           "--rasters", str(OUTPUT_DIR / "c_factor_pe1_30m.tif")]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout.strip())
    if proc.stderr.strip():
        print("stderr:", proc.stderr.strip())


if __name__ == "__main__":
    main()
