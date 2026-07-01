#!/usr/bin/env python3
"""Derive USLE/RUSLE cover-management C-factor for V1 from ESA WorldCover 2021 v200.

Local TOOLING script. Maps ESA WorldCover 10 m 2021 v200 land-cover classes to RUSLE
cover-management C-factor values via a fixed literature-derived lookup table, then
produces two V1 products:

  (a) ``c_factor_worldcover_10m.tif``
      C-factor on the WorldCover native 10 m grid (EPSG:4326), clipped to the V1
      working boundary (cells outside V1 set to NoData). Reference-resolution product.

  (b) ``c_factor_v1_30m.tif``
      C-factor on the fixed V1 reference terrain grid (EPSG:32735, 30 m, same
      transform / size / NoData as ``v1_dem_utm35s_30m.tif``).

      Resampling rule: the categorical WorldCover class is reprojected 10 m -> 30 m
      with MODE (majority-class) resampling, and the lookup is applied AFTER the
      class aggregation. The C value is never averaged across mixed classes at a
      30 m cell; the majority class is preserved and its C is assigned.

      This 10 m -> 30 m aggregation is explicitly ALLOWED because WorldCover is
      FINER than the V1 target grid (fine -> coarse aggregation preserves the
      categorical class). This is the OPPOSITE of the CHIRPS / SoilGrids rule
      (coarse -> fine forbidden, which fabricates detail). See
      ``context/docs/data-management/v1_terrain_reference_grid_rule.md``.

      C-factor here is a STATIC LAND-COVER PROXY derived from a single
      classification, NOT a dynamic C-factor from NDVI / multi-temporal cover time
      series. It captures between-cover-type differences but not within-class
      seasonal / management variability.

Lookup table (RUSLE C, dimensionless 0-1; typical literature ranges for generic
land-cover classes, e.g. Wischmeier & Smith 1978; Renard et al. 1997; pan-European
/ review compilations). These are nominal annual C values used as a first-order
proxy; they are not calibrated to local management or crop calendars::

      10  Tree cover                  0.003
      20  Shrubland                   0.040
      30  Grassland                   0.030
      40  Cropland                    0.230
      50  Built-up                    0.000
      60  Bare / sparse vegetation    0.700
      70  Snow / ice                  0.000
      80  Permanent water bodies      0.000
      90  Herbaceous wetland          0.050
      95  Mangroves                   0.010
      100 Moss / lichen               0.030

Usage:
    .venv/bin/python bin/factors/derive_v1_worldcover_cfactor.py
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
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import geometry_mask, rasterize
from rasterio.warp import reproject
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[2]

WORLDCOVER_TILE = ROOT / "data/raw/esa_worldcover_2021_v1_methodology/ESA_WorldCover_10m_2021_v200_S21E027_Map.tif"
V1_BOUNDARY_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
V1_BOUNDARY_LAYER = "v1_working_boundary"
V1_REFERENCE_DEM = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
OUTPUT_DIR = ROOT / "outputs/esa_worldcover_2021_v1_methodology/c_factor"
GRID_CHECK_TOOL = ROOT / "bin/package/check_v1_raster_grid.py"

NODATA = -9999.0

# ESA WorldCover v200 class code -> (label, RUSLE C-factor)
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


def load_v1_boundary() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(V1_BOUNDARY_GPKG, layer=V1_BOUNDARY_LAYER)
    if len(gdf) != 1:
        raise ValueError(f"Expected exactly one V1 boundary feature, got {len(gdf)}")
    return gdf


def worldcover_window(bounds4326: tuple[float, float, float, float], pad_deg: float):
    """Open the WorldCover tile and read a window covering bounds4326 + padding."""
    minx, miny, maxx, maxy = bounds4326
    with rasterio.open(WORLDCOVER_TILE) as src:
        win = from_bounds(minx - pad_deg, miny - pad_deg,
                          maxx + pad_deg, maxy + pad_deg, src.transform)
        win = win.round_offsets().round_lengths()
        win_transform = src.window_transform(win)
        arr = src.read(1, window=win)
        profile = src.profile.copy()
    return arr, win_transform, profile


def class_to_c(class_arr: np.ndarray) -> np.ndarray:
    """Map WorldCover class codes to C-factor (float32). Unknown / 0 -> NaN."""
    out = np.full(class_arr.shape, np.nan, dtype="float32")
    for code, (_label, cval) in C_FACTOR_LUT.items():
        out[class_arr == code] = cval
    return out


def v1_mask_on_grid(geometry, transform, shape) -> np.ndarray:
    """Boolean mask (True inside V1) rasterized onto a target grid (all_touched=False)."""
    return rasterize(
        [(geometry, 1)],
        out_shape=shape,
        transform=transform,
        fill=0,
        dtype="uint8",
        all_touched=False,
    ).astype(bool)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    v1 = load_v1_boundary()

    # --- Reference grid (the exact V1 30 m grid we must reproduce) ---------------
    with rasterio.open(V1_REFERENCE_DEM) as ref:
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_width, ref_height = ref.width, ref.height
        ref_bounds = ref.bounds
    print(f"V1 reference grid: {ref_width} x {ref_height} @ 30 m, {ref_crs}")

    # --- Source window: cover the full DEM extent (+pad) in EPSG:4326 -------------
    # Reproject the 30 m grid corners to 4326 so the WorldCover source fully covers
    # every destination cell during the 10 m -> 30 m reproject.
    tr = Transformer.from_crs(ref_crs, "EPSG:4326", always_xy=True)
    lb, bb, rb, tb = ref_bounds
    xs = [lb, rb, rb, lb]
    ys = [bb, bb, tb, tb]
    lons, lats = tr.transform(xs, ys)
    src_bbox = (min(lons), min(lats), max(lons), max(lats))
    pad_deg = 0.01  # ~1.1 km safety pad for CRS distortion + mode kernel edges
    class_src, src_transform, src_profile = worldcover_window(src_bbox, pad_deg)
    src_crs = src_profile["crs"]
    print(f"WorldCover source window: {class_src.shape[1]} x {class_src.shape[0]} "
          f"px @ 10 m, {src_crs}")

    src_classes = np.unique(class_src)
    unknown = [int(c) for c in src_classes if c != 0 and int(c) not in C_FACTOR_LUT]
    if unknown:
        print(f"[warn] source classes not in lookup (will become NoData): {unknown}")

    # === (a) Native 10 m C-factor, clipped to V1 ================================
    v1_geom_4326 = v1.to_crs(src_crs).geometry.iloc[0]
    mask10 = v1_mask_on_grid(v1_geom_4326, src_transform, class_src.shape)
    c10 = class_to_c(class_src)
    c10[~mask10] = np.nan  # outside V1 -> NoData
    c10_write = np.where(np.isfinite(c10), c10, NODATA).astype("float32")

    profile10 = {
        "driver": "GTiff", "height": c10.shape[0], "width": c10.shape[1], "count": 1,
        "dtype": "float32", "crs": src_crs, "transform": src_transform,
        "nodata": NODATA, "compress": "deflate", "tiled": True,
    }
    out_10m = OUTPUT_DIR / "c_factor_worldcover_10m.tif"
    with rasterio.open(out_10m, "w", **profile10) as dst:
        dst.write(c10_write, 1)
        dst.set_band_description(1, "RUSLE C-factor from ESA WorldCover 2021 v200 (10 m, V1 clip)")
    print(f"wrote {rel(out_10m)}")

    # === (b) 30 m C-factor on the V1 reference grid =============================
    # Step 1: reproject the CATEGORICAL class with MODE (majority) resampling.
    class_dst = np.zeros((ref_height, ref_width), dtype="uint8")
    reproject(
        source=class_src,
        destination=class_dst,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=Resampling.mode,
        src_nodata=0,   # WorldCover NoData (0) excluded from majority vote
        dst_nodata=0,
        init_dest_nodata=False,
    )
    # Step 2: clip to V1, THEN apply the lookup -> C value (majority class preserved).
    v1_geom_ref = v1.to_crs(ref_crs).geometry.iloc[0]
    mask30 = v1_mask_on_grid(v1_geom_ref, ref_transform, (ref_height, ref_width))
    c30 = class_to_c(class_dst)
    c30[~mask30] = np.nan  # outside V1 -> NoData
    c30_write = np.where(np.isfinite(c30), c30, NODATA).astype("float32")

    profile30 = {
        "driver": "GTiff", "height": ref_height, "width": ref_width, "count": 1,
        "dtype": "float32", "crs": ref_crs, "transform": ref_transform,
        "nodata": NODATA, "compress": "deflate", "tiled": True,
    }
    out_30m = OUTPUT_DIR / "c_factor_v1_30m.tif"
    with rasterio.open(out_30m, "w", **profile30) as dst:
        dst.write(c30_write, 1)
        dst.set_band_description(1, "RUSLE C-factor from ESA WorldCover 2021 v200 (V1 30 m grid)")
    print(f"wrote {rel(out_30m)}")

    # === Zonal summary: per-class fractions + area-weighted mean C ==============
    # Authoritative fractions from the native 10 m clip (pure-class, ~equal-area cells).
    codes, counts = np.unique(class_src[mask10], return_counts=True)
    total = int(counts.sum())
    class_dist = {}
    weighted_c = 0.0
    for code, cnt in zip(codes.tolist(), counts.tolist()):
        code = int(code)
        if code not in C_FACTOR_LUT:
            continue
        label, cval = C_FACTOR_LUT[code]
        frac = cnt / total
        weighted_c += frac * cval
        class_dist[code] = {
            "label": label,
            "c_factor": cval,
            "cells_10m": cnt,
            "fraction_v1": round(frac, 6),
        }

    # Cross-check: area-weighted mean C from the 30 m grid (should be close to 10 m).
    c30_valid = c30[np.isfinite(c30)]
    mean_c_30m = float(np.mean(c30_valid)) if c30_valid.size else float("nan")
    valid_c30 = int(np.isfinite(c30).sum())
    inside_v1_30 = int(mask30.sum())
    valid_fraction_30 = valid_c30 / inside_v1_30 if inside_v1_30 else 0.0

    print(f"\nV1 per-class fractions (10 m):")
    for code in sorted(class_dist):
        d = class_dist[code]
        print(f"  {code:>3} {d['label']:<28} C={d['c_factor']:.3f}  frac={d['fraction_v1']:.4f}")
    print(f"\nV1 area-weighted mean C (10 m) = {weighted_c:.4f}")
    print(f"V1 mean C (30 m grid)          = {mean_c_30m:.4f}  (valid frac inside V1 = {valid_fraction_30:.4f})")

    # === Grid check via the authoritative tool ==================================
    grid_csv = OUTPUT_DIR / "c_factor_v1_30m_grid_check.csv"
    grid_cmd = [
        sys.executable, str(GRID_CHECK_TOOL),
        "--reference", str(V1_REFERENCE_DEM),
        "--rasters", str(out_30m),
        "--output", str(grid_csv),
    ]
    proc = subprocess.run(grid_cmd, capture_output=True, text=True)
    grid_result = {
        "tool": rel(GRID_CHECK_TOOL),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "manifest": rel(grid_csv) if grid_csv.exists() else None,
    }
    # Parse the single candidate row for grid_compatible + issues.
    grid_compatible = None
    grid_issues = ""
    if grid_csv.exists():
        import csv
        with grid_csv.open() as fh:
            rows = list(csv.DictReader(fh))
        cand = [r for r in rows if r.get("role") == "candidate"]
        if cand:
            grid_compatible = cand[0].get("grid_compatible")
            grid_issues = cand[0].get("issues", "")
    print(f"\ngrid check (30 m): grid_compatible={grid_compatible} issues='{grid_issues}'")

    # === Diagnostics JSON =======================================================
    lookup_serialised = {
        str(code): {"label": label, "c_factor": cval}
        for code, (label, cval) in C_FACTOR_LUT.items()
    }
    diagnostics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": rel(Path(__file__)),
        "source": "ESA WorldCover 10 m 2021 v200",
        "source_tile": rel(WORLDCOVER_TILE),
        "source_crs": str(src_crs),
        "source_pixel_size_deg": 8.333333333333333e-05,
        "source_nodata": 0,
        "v1_boundary": rel(V1_BOUNDARY_GPKG),
        "v1_boundary_layer": V1_BOUNDARY_LAYER,
        "v1_reference_grid": rel(V1_REFERENCE_DEM),
        "v1_reference_grid_crs": str(ref_crs),
        "v1_reference_grid_res_m": [30.0, 30.0],
        "lookup_table": lookup_serialised,
        "lookup_reference": (
            "Nominal annual RUSLE C values (dimensionless 0-1) for generic land-cover "
            "classes, after Wischmeier & Smith (1978) and Renard et al. (1997); typical "
            "ranges from review compilations. Static land-cover proxy, not a dynamic "
            "NDVI / multi-temporal C-factor."
        ),
        "resampling": {
            "10m_to_30m_method": "mode (majority class) on categorical codes",
            "lookup_applied_after_resampling": True,
            "rationale": (
                "WorldCover (10 m) is FINER than the V1 30 m target grid, so 10 m -> 30 m "
                "aggregation is ALLOWED and preserves the categorical class via majority. "
                "This is the OPPOSITE of the CHIRPS / SoilGrids rule (coarse -> fine "
                "forbidden). The lookup is applied AFTER class aggregation so C values are "
                "not averaged across mixed classes at a 30 m cell."
            ),
        },
        "outputs": {
            "c_factor_worldcover_10m": rel(out_10m),
            "c_factor_v1_30m": rel(out_30m),
        },
        "source_classes_in_window": [int(c) for c in src_classes.tolist()],
        "unknown_classes_becoming_nodata": unknown,
        "v1_class_distribution_10m": {str(k): v for k, v in class_dist.items()},
        "v1_area_weighted_mean_c_10m": round(weighted_c, 6),
        "v1_mean_c_30m": round(mean_c_30m, 6),
        "v1_30m_valid_cells": valid_c30,
        "v1_30m_inside_cells": inside_v1_30,
        "v1_30m_valid_fraction_inside_v1": round(valid_fraction_30, 6),
        "grid_check_30m": {
            "grid_compatible": grid_compatible,
            "issues": grid_issues,
            **grid_result,
        },
        "caveats": [
            "C-factor is a STATIC land-cover proxy from a single 2021 classification, not "
            "a dynamic C-factor from NDVI / multi-temporal cover time series.",
            "Cropland C (0.230) is a nominal annual value and does not reflect local "
            "crop calendars, tillage, or residue management.",
            "Built-up, water, snow/ice are assigned C=0 (non-eroding) per standard RUSLE "
            "convention; they are retained for completeness but contribute ~0 to erosion.",
        ],
    }
    diag_path = OUTPUT_DIR / "c_factor_diagnostics.json"
    diag_path.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(f"wrote {rel(diag_path)}")


if __name__ == "__main__":
    main()
