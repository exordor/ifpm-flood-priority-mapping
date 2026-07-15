#!/usr/bin/env python3
"""Derive USLE/RUSLE C-factor for Arequipa Region from ESA WorldCover 2021.

Mirrors `derive_v1_worldcover_cfactor.py`. Peru differences: Arequipa Region boundary, Arequipa Region reference DEM
(EPSG:32718), and multiple WorldCover tiles because Arequipa Region crosses the -72 degree tile boundary.
Same RUSLE C-factor lookup table (literature-derived, identical for both countries), same
MODE-resample-then-lookup approach.

Outputs: C-factor on the WorldCover native 10m grid clipped to Arequipa Region, and C-factor on the Arequipa Region 30m
reference grid (MODE resample 10m->30m, legitimate fine->coarse aggregation, then lookup).
"""

from __future__ import annotations

import json
import subprocess
import sys
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.merge import merge
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg", ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif"]
OUTPUTS = [
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_peru_hybas_l7_6070641200_30m.tif",
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/land_use_pressure_peru_hybas_l7_6070641200_30m.tif",
]

WORLDCOVER_RAW_DIR = ROOT / "data/raw/esa_worldcover_2021_peru_pilot"
WORLDCOVER_GLOB = "ESA_WorldCover_10m_2021_v200_*_Map.tif"
PERU_HYBAS_L7_6070641200_BOUNDARY_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
PERU_HYBAS_L7_6070641200_BOUNDARY_LAYER = "peru_pilot_boundary"
PERU_HYBAS_L7_6070641200_REFERENCE_DEM = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif"
OUTPUT_DIR = ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor"
GRID_CHECK_TOOL = ROOT / "bin/package/check_v1_raster_grid.py"

NODATA = -9999.0
MIN_VALID_FRACTION = 0.98

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

# Separate land-use intensity value function. This is intentionally not the
# RUSLE C-factor: cropland and built-up land represent direct human land-use
# pressure, while naturally bare semi-arid ground is not treated as equivalent
# to built-up land.
LAND_USE_PRESSURE_LUT: dict[int, float] = {
    10: 0.10,   # tree cover
    20: 0.15,   # shrubland
    30: 0.20,   # grassland
    40: 0.80,   # cropland
    50: 1.00,   # built-up
    60: 0.25,   # bare / sparse vegetation; natural disturbance is ambiguous
    70: 0.00,   # snow / ice
    80: 0.00,   # permanent water
    90: 0.00,   # herbaceous wetland
    95: 0.00,   # mangroves
    100: 0.10,  # moss / lichen
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_peru_hybas_l7_6070641200_boundary() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(PERU_HYBAS_L7_6070641200_BOUNDARY_GPKG, layer=PERU_HYBAS_L7_6070641200_BOUNDARY_LAYER)
    if len(gdf) != 1:
        raise ValueError(f"Expected exactly one Arequipa Region boundary feature, got {len(gdf)}")
    return gdf


def intersects(a, b) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def worldcover_mosaic(bounds4326: tuple[float, float, float, float], pad_deg: float):
    minx, miny, maxx, maxy = bounds4326
    padded = (minx - pad_deg, miny - pad_deg, maxx + pad_deg, maxy + pad_deg)
    paths = sorted(WORLDCOVER_RAW_DIR.glob(WORLDCOVER_GLOB))
    if not paths:
        raise FileNotFoundError(f"No WorldCover tiles found in {WORLDCOVER_RAW_DIR}")

    selected: list[Path] = []
    with ExitStack() as stack:
        datasets = []
        for path in paths:
            src = stack.enter_context(rasterio.open(path))
            if str(src.crs) != "EPSG:4326":
                raise ValueError(f"unexpected WorldCover CRS for {path}: {src.crs}")
            src_bounds = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
            if intersects(src_bounds, padded):
                selected.append(path)
                datasets.append(src)
        if not datasets:
            raise ValueError(f"No WorldCover tile intersects Arequipa Region source bbox {padded}")

        union = (
            min(src.bounds.left for src in datasets),
            min(src.bounds.bottom for src in datasets),
            max(src.bounds.right for src in datasets),
            max(src.bounds.top for src in datasets),
        )
        if not (
            union[0] <= padded[0] and union[1] <= padded[1]
            and union[2] >= padded[2] and union[3] >= padded[3]
        ):
            raise ValueError(
                "WorldCover tile coverage does not cover Arequipa Region padded bbox; "
                f"need bbox={padded}, available union={union}"
            )

        arr, transform = merge(
            datasets,
            bounds=padded,
            res=datasets[0].res,
            nodata=0,
            dtype="uint8",
        )
        profile = datasets[0].profile.copy()

    profile.update(
        driver="GTiff",
        height=arr.shape[1],
        width=arr.shape[2],
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=transform,
        nodata=0,
    )
    return arr[0], transform, profile, selected


def class_to_c(class_arr: np.ndarray) -> np.ndarray:
    out = np.full(class_arr.shape, np.nan, dtype="float32")
    for code, (_label, cval) in C_FACTOR_LUT.items():
        out[class_arr == code] = cval
    return out


def class_to_land_use_pressure(class_arr: np.ndarray) -> np.ndarray:
    out = np.full(class_arr.shape, np.nan, dtype="float32")
    for code, value in LAND_USE_PRESSURE_LUT.items():
        out[class_arr == code] = value
    return out


def mask_on_grid(geometry, transform, shape) -> np.ndarray:
    return rasterize(
        [(geometry, 1)], out_shape=shape, transform=transform, fill=0, dtype="uint8", all_touched=False
    ) == 1


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bnd = load_peru_hybas_l7_6070641200_boundary()

    with rasterio.open(PERU_HYBAS_L7_6070641200_REFERENCE_DEM) as ref:
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_width, ref_height = ref.width, ref.height
        ref_bounds = ref.bounds
        ref_profile = ref.profile.copy()
    print(f"Arequipa Region reference grid: {ref_width} x {ref_height} @ 30 m, {ref_crs}")

    tr = Transformer.from_crs(ref_crs, "EPSG:4326", always_xy=True)
    xs = [ref_bounds.left, ref_bounds.right, ref_bounds.right, ref_bounds.left]
    ys = [ref_bounds.bottom, ref_bounds.bottom, ref_bounds.top, ref_bounds.top]
    lons, lats = tr.transform(xs, ys)
    source_bbox = (min(lons), min(lats), max(lons), max(lats))

    # 1. native 10m C-factor clipped to Arequipa Region; source is a mosaic when Arequipa Region crosses a tile boundary.
    class_arr, wc_transform, wc_profile, source_tiles = worldcover_mosaic(source_bbox, pad_deg=0.01)
    print("WorldCover source tiles:")
    for path in source_tiles:
        print(f"  - {rel(path)}")

    geom4326 = bnd.to_crs("EPSG:4326").geometry.iloc[0]
    peru_hybas_l7_6070641200_mask_native = mask_on_grid(geom4326, wc_transform, class_arr.shape)
    c_native = class_to_c(class_arr)
    c_native_masked = np.where(peru_hybas_l7_6070641200_mask_native, c_native, np.nan)

    native_profile = wc_profile.copy()
    native_profile.update(dtype="float32", nodata=NODATA, compress="deflate", tiled=True)
    c_native_out = np.where(np.isfinite(c_native_masked), c_native_masked, NODATA).astype("float32")
    with rasterio.open(OUTPUT_DIR / "c_factor_peru_hybas_l7_6070641200_10m.tif", "w", **native_profile) as ds:
        ds.write(c_native_out, 1)
    print(f"wrote {OUTPUT_DIR / 'c_factor_peru_hybas_l7_6070641200_10m.tif'}")

    # 2. Arequipa Region 30m grid: MODE resample 10m->30m (fine->coarse aggregation), then lookup
    bnd_ref = bnd.to_crs(ref_crs)
    peru_hybas_l7_6070641200_mask_ref = mask_on_grid(bnd_ref.geometry.iloc[0], ref_transform, (ref_height, ref_width))

    class_30m = np.full((ref_height, ref_width), 0, dtype="uint8")
    reproject(
        source=class_arr, destination=class_30m,
        src_transform=wc_transform, src_crs="EPSG:4326", src_nodata=0,
        dst_transform=ref_transform, dst_crs=ref_crs, dst_nodata=0,
        resampling=Resampling.mode,
    )
    c_30m = class_to_c(class_30m.astype("int32"))
    c_30m_masked = np.where(peru_hybas_l7_6070641200_mask_ref, c_30m, np.nan)
    land_use_30m = class_to_land_use_pressure(class_30m.astype("int32"))
    land_use_30m_masked = np.where(peru_hybas_l7_6070641200_mask_ref, land_use_30m, np.nan)

    out_profile = ref_profile.copy()
    out_profile.update(dtype="float32", nodata=NODATA, count=1, compress="deflate", tiled=True)
    c_30m_out = np.where(np.isfinite(c_30m_masked), c_30m_masked, NODATA).astype("float32")
    with rasterio.open(OUTPUT_DIR / "c_factor_peru_hybas_l7_6070641200_30m.tif", "w", **out_profile) as ds:
        ds.write(c_30m_out, 1)
    print(f"wrote {OUTPUT_DIR / 'c_factor_peru_hybas_l7_6070641200_30m.tif'}")
    land_use_out = np.where(np.isfinite(land_use_30m_masked), land_use_30m_masked, NODATA).astype("float32")
    with rasterio.open(OUTPUT_DIR / "land_use_pressure_peru_hybas_l7_6070641200_30m.tif", "w", **out_profile) as ds:
        ds.write(land_use_out, 1)
    print(f"wrote {OUTPUT_DIR / 'land_use_pressure_peru_hybas_l7_6070641200_30m.tif'}")

    # 3. stats + class-area on Arequipa Region (30m)
    valid = np.isfinite(c_30m_masked) & peru_hybas_l7_6070641200_mask_ref
    c_vals = c_30m_masked[valid]
    cell_area = 30.0 * 30.0 / 1e6  # km2
    class_area_km2 = {}
    for code, (label, cval) in C_FACTOR_LUT.items():
        n = int(((class_30m == code) & peru_hybas_l7_6070641200_mask_ref).sum())
        if n:
            class_area_km2[f"{code}_{label}"] = round(n * cell_area, 2)

    diag = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/factors/derive_peru_pilot_worldcover_cfactor.py",
        "source_tiles": [rel(path) for path in source_tiles],
        "lut": "RUSLE C-factor lookup (literature-derived; identical to Zimbabwe LUT)",
        "land_use_pressure_lut": LAND_USE_PRESSURE_LUT,
        "land_use_pressure_note": (
            "Separate provisional human land-use intensity value function; not a copy of RUSLE C."
        ),
        "resample_method": "MODE (10m->30m, legitimate fine->coarse aggregation); lookup applied AFTER resample",
        "boundary_status": "provisional_comparison_catchment_not_final_study_area",
        "c_factor_30m_stats": {
            "valid_cells": int(valid.sum()),
            "valid_fraction_inside_peru_hybas_l7_6070641200": round(float(valid.sum() / peru_hybas_l7_6070641200_mask_ref.sum()), 6) if peru_hybas_l7_6070641200_mask_ref.sum() else 0.0,
            "mean": round(float(np.mean(c_vals)), 4) if c_vals.size else None,
            "min": round(float(np.min(c_vals)), 4) if c_vals.size else None,
            "max": round(float(np.max(c_vals)), 4) if c_vals.size else None,
        },
        "class_area_km2_on_peru_hybas_l7_6070641200_30m": class_area_km2,
        "zimbabwe_v1_reference_mean_c": 0.0429,
    }
    (OUTPUT_DIR / "c_factor_diagnostics.json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
    print(f"\nArequipa Region C-factor (30m): mean {diag['c_factor_30m_stats']['mean']} "
          f"[{diag['c_factor_30m_stats']['min']} - {diag['c_factor_30m_stats']['max']}] "
          f"(ZW V1 ref mean 0.0429)")
    print("class area (km2):", class_area_km2)

    # 4. grid gate (with Arequipa Region boundary)
    print("[gate] running check_v1_raster_grid.py ...")
    cmd = [sys.executable, str(GRID_CHECK_TOOL),
           "--reference", str(PERU_HYBAS_L7_6070641200_REFERENCE_DEM),
           "--boundary", str(PERU_HYBAS_L7_6070641200_BOUNDARY_GPKG), "--boundary-layer", PERU_HYBAS_L7_6070641200_BOUNDARY_LAYER,
           "--output", str(OUTPUT_DIR / "c_factor_grid_check.csv"),
           "--rasters", str(OUTPUT_DIR / "c_factor_peru_hybas_l7_6070641200_30m.tif"),
           str(OUTPUT_DIR / "land_use_pressure_peru_hybas_l7_6070641200_30m.tif")]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout.strip())
    if proc.stderr.strip():
        print("stderr:", proc.stderr.strip())
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    if valid.sum() / peru_hybas_l7_6070641200_mask_ref.sum() < MIN_VALID_FRACTION:
        raise RuntimeError(
            f"C-factor Arequipa Region valid coverage below threshold: {valid.sum() / peru_hybas_l7_6070641200_mask_ref.sum():.6f}"
        )


if __name__ == "__main__":
    main()
