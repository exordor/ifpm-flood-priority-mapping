#!/usr/bin/env python3
"""Derive USLE/RUSLE soil-erodibility K-factor for V1 from SoilGrids VRT (windowed HTTP read).

Local TOOLING script. Reads clay / silt / sand / soil-organic-carbon from the SoilGrids 250m VRT
collection (files.isric.org) via rasterio HTTP windowed reads for the V1 bounding box. No global
raster is downloaded; only the V1 window is read. Computes K-factor per depth slice with the
Williams (1995) EPIC/RUSLE pedotransfer function, then a 0-30 cm depth-weighted average.

Outputs are 250m rasters in the SoilGrids native Interrupted Goode Homolosine projection, plus a
V1 zonal summary and diagnostics. The output is explicitly NOT resampled to the V1 30 m terrain
grid (per the V1 terrain reference grid rule: SoilGrids must not become pixel-level 30 m truth).

K-factor formula (Williams 1995; SWAT/EPIC documentation, Neitsch et al.):
    K = X1 * X2 * X3 * X4          (US units, 0.0-~0.6)
    X1 = 0.2 + 0.3 * exp(-0.0256 * SAN * (1 - SIL/100))
    X2 = (SIL / (CLA + SIL)) ** 0.3
    X3 = 1 - (0.25 * C) / (C + exp(3.72 - 2.95*C))
    X4 = 1 - (0.7 * SN1) / (SN1 + exp(22.9*SN1 - 5.51))
    SN1 = 1 - SAN/100
    SAN, SIL, CLA = sand/silt/clay percent; C = organic carbon percent
    K_US * 0.1317 = K_SI  (t ha h / (ha MJ mm))

Usage:
    .venv/bin/python bin/derive_v1_soilgrids_kfactor.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from rasterio.windows import from_bounds as window_from_bounds

try:
    import geopandas as gpd
    from pyproj import Transformer
except ImportError as exc:
    raise SystemExit(f"missing dependency: {exc}. Install geopandas/pyproj in .venv.") from exc

SOILGRIDS_BASE = "https://files.isric.org/soilgrids/latest/data"
SOILGRIDS_CRS = "ESRI:54017"  # Interrupted Goode Homolosine

# V1 bounding box in EPSG:4326 (from srtm_v1_tile_plan / v1_working_boundary)
V1_LON_MIN, V1_LAT_MIN, V1_LON_MAX, V1_LAT_MAX = 28.514, -21.008, 29.398, -19.984
V1_BOUNDARY_GPKG = Path("outputs/v1_working_boundary/v1_working_boundary.gpkg")

# SoilGrids depth slices (cm) and depth-weighted average target for 0-30 cm
DEPTH_SLICES = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
DEPTH_THICKNESS_CM = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15, "30-60cm": 30, "60-100cm": 40, "100-200cm": 100}
TOPSOIL_SLICES = ["0-5cm", "5-15cm", "15-30cm"]  # for 0-30 cm weighted average

PROPERTIES = ["clay", "silt", "sand", "soc"]
# SoilGrids 2.0 storage convention: texture in g/kg (= permille); soc in dg/kg.
# To get percent: texture raw / 10 = %; soc raw / 100 = %C.
SCALE_TO_PERCENT = {"clay": 10.0, "silt": 10.0, "sand": 10.0, "soc": 100.0}
SOILGRIDS_NODATA = -32768

OUTPUT_DIR = Path("outputs/soilgrids_250m_sediment_candidate")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def read_vrt_window(property_name: str, depth: str, window, transform, crs):
    """Read a SoilGrids mean VRT window; return float32 array in percent units + nodata mask."""
    url = f"{SOILGRIDS_BASE}/{property_name}/{property_name}_{depth}_mean.vrt"
    with rasterio.open(url) as ds:
        arr = ds.read(1, window=window).astype("float32")
    nodata_mask = arr == SOILGRIDS_NODATA
    arr = arr / SCALE_TO_PERCENT[property_name]
    arr[nodata_mask] = np.nan
    return arr, nodata_mask


def williams_k(clay, silt, sand, soc):
    """Williams (1995) K-factor in US units. Inputs are percent arrays (clay, silt, sand, soc)."""
    san = np.clip(sand, 0.0, 100.0)
    sil = np.clip(silt, 0.0, 100.0)
    cla = np.clip(clay, 0.0, 100.0)
    c = np.clip(soc, 0.0, None)
    sn1 = 1.0 - san / 100.0
    x1 = 0.2 + 0.3 * np.exp(-0.0256 * san * (1.0 - sil / 100.0))
    denom = cla + sil
    denom = np.where(denom <= 0, np.nan, denom)
    x2 = (sil / denom) ** 0.3
    x3 = 1.0 - (0.25 * c) / (c + np.exp(3.72 - 2.95 * c))
    x4 = 1.0 - (0.7 * sn1) / (sn1 + np.exp(22.9 * sn1 - 5.51))
    k = x1 * x2 * x3 * x4
    k = np.where(k < 0, 0.0, k)
    return k


def main() -> None:
    # 1. V1 bbox -> Goode Homolosine
    transformer = Transformer.from_crs("EPSG:4326", SOILGRIDS_CRS, always_xy=True)
    x1, y1 = transformer.transform(V1_LON_MIN, V1_LAT_MAX)
    x2, y2 = transformer.transform(V1_LON_MAX, V1_LAT_MIN)
    gx_min, gx_max = min(x1, x2), max(x1, x2)
    gy_min, gy_max = min(y1, y2), max(y1, y2)
    print(f"V1 bbox in Goode Homolosine: x[{gx_min:.0f},{gx_max:.0f}] y[{gy_min:.0f},{gy_max:.0f}]")

    # 2. Open one VRT to get transform/window aligned to SoilGrids grid
    ref_url = f"{SOILGRIDS_BASE}/clay/clay_0-5cm_mean.vrt"
    with rasterio.open(ref_url) as ds:
        win = window_from_bounds(gx_min, gy_min, gx_max, gy_max, ds.transform)
        win_transform = ds.window_transform(win)
        win_crs = ds.crs
        pix_w, pix_h = int(round(win.width)), int(round(win.height))
    print(f"V1 window: {pix_w} x {pix_h} px @ 250 m (Goode Homolosine)")

    # 3. Rasterize V1 boundary onto the window grid as a boolean mask
    v1_mask = np.ones((pix_h, pix_w), dtype="uint8")
    if V1_BOUNDARY_GPKG.exists():
        gdf = gpd.read_file(V1_BOUNDARY_GPKG, layer="v1_working_boundary").to_crs(SOILGRIDS_CRS)
        shapes = [(geom, 1) for geom in gdf.geometry if geom is not None]
        if shapes:
            v1_mask = rasterize(shapes, out_shape=(pix_h, pix_w), transform=win_transform,
                                fill=0, dtype="uint8", all_touched=False)
        print(f"V1 boundary rasterized: {int(v1_mask.sum())} cells inside V1 "
              f"({100*v1_mask.sum()/(pix_w*pix_h):.1f}% of window)")
    else:
        print(f"[warn] {V1_BOUNDARY_GPKG} not found; using whole window as V1 proxy")

    # 4. Read properties per depth and compute K
    k_by_depth: dict[str, np.ndarray] = {}
    raw_ranges: dict[str, dict] = {}
    for depth in DEPTH_SLICES:
        layers = {}
        shared_valid = None
        for prop in PROPERTIES:
            arr, nd = read_vrt_window(prop, depth, win, win_transform, win_crs)
            layers[prop] = arr
            shared_valid = nd if shared_valid is None else (shared_valid & nd)
        # K-factor
        k = williams_k(layers["clay"], layers["silt"], layers["sand"], layers["soc"])
        invalid = np.isnan(k) | shared_valid | (v1_mask == 0)
        k = np.where(invalid, np.nan, k)
        k_by_depth[depth] = k
        raw_ranges[depth] = {
            "clay_pct": (float(np.nanmin(layers["clay"])), float(np.nanmax(layers["clay"]))),
            "silt_pct": (float(np.nanmin(layers["silt"])), float(np.nanmax(layers["silt"]))),
            "sand_pct": (float(np.nanmin(layers["sand"])), float(np.nanmax(layers["sand"]))),
            "soc_pct": (float(np.nanmin(layers["soc"])), float(np.nanmax(layers["soc"]))),
            "k_us": (float(np.nanmin(k)), float(np.nanmax(k))),
        }
        valid = np.isfinite(k)
        print(f"  {depth}: K mean={float(np.nanmean(k)):.4f} range=[{float(np.nanmin(k)):.3f},{float(np.nanmax(k)):.3f}] "
              f"(valid cells={int(valid.sum())})")

    # 5. 0-30 cm depth-weighted average
    weights = np.array([DEPTH_THICKNESS_CM[d] for d in TOPSOIL_SLICES], dtype="float32")
    weights = weights / weights.sum()
    k_0_30 = np.zeros_like(k_by_depth["0-5cm"])
    w_sum = np.zeros_like(k_0_30)
    for d, w in zip(TOPSOIL_SLICES, weights, strict=True):
        kd = k_by_depth[d]
        m = np.isfinite(kd)
        k_0_30 = np.where(m, k_0_30 + kd * w, k_0_30)
        w_sum = np.where(m, w_sum + w, w_sum)
    k_0_30 = np.where(w_sum > 0, k_0_30 / w_sum, np.nan)

    # 6. Write 250m rasters (Goode Homolosine, native) - NOT resampled to 30m
    profile = {
        "driver": "GTiff", "height": pix_h, "width": pix_w, "count": 1,
        "dtype": "float32", "crs": win_crs, "transform": win_transform,
        "nodata": -9999.0, "compress": "deflate", "tiled": True,
    }
    for name, arr in [("k_factor_0_5cm_250m.tif", k_by_depth["0-5cm"]),
                      ("k_factor_0_30cm_avg_250m.tif", k_0_30)]:
        out = np.where(np.isfinite(arr), arr, -9999.0).astype("float32")
        path = OUTPUT_DIR / name
        with rasterio.open(path, "w", **profile) as ds:
            ds.write(out, 1)
        print(f"wrote {path}")

    # 7. V1 zonal summary
    def zonal(arr):
        m = np.isfinite(arr) & (v1_mask == 1)
        vals = arr[m]
        if vals.size == 0:
            return {}
        return {
            "valid_cells": int(m.sum()),
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "min": float(np.min(vals)),
            "p05": float(np.percentile(vals, 5)),
            "p50": float(np.percentile(vals, 50)),
            "p95": float(np.percentile(vals, 95)),
            "max": float(np.max(vals)),
        }

    zonal_summary = {
        "k_0_5cm_us": zonal(k_by_depth["0-5cm"]),
        "k_0_5cm_si": {k: (round(v * 0.1317, 6) if isinstance(v, float) and k != "valid_cells" else v)
                       for k, v in zonal(k_by_depth["0-5cm"]).items()},
        "k_0_30cm_us": zonal(k_0_30),
        "k_0_30cm_si": {k: (round(v * 0.1317, 6) if isinstance(v, float) and k != "valid_cells" else v)
                        for k, v in zonal(k_0_30).items()},
    }

    diagnostics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/derive_v1_soilgrids_kfactor.py",
        "source": "SoilGrids 250m VRT (files.isric.org), windowed HTTP read",
        "v1_window_px": {"width": pix_w, "height": pix_h, "crs": str(win_crs)},
        "v1_mask_cells": int(v1_mask.sum()),
        "formula": "Williams 1995 EPIC/RUSLE (see module docstring)",
        "depth_note": "0-5cm = surface topsoil; 0-30cm = depth-weighted average of 0-5/5-15/15-30",
        "units_note": "K in US units; multiply by 0.1317 for SI (t ha h / ha MJ mm)",
        "property_ranges_by_depth": raw_ranges,
        "v1_zonal_summary": zonal_summary,
    }
    diag_path = OUTPUT_DIR / "k_factor_diagnostics.json"
    diag_path.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(f"\ndiagnostics: {diag_path}")
    print("\n=== V1 zonal K-factor ===")
    for key, vals in zonal_summary.items():
        if vals:
            print(f"  {key}: mean={vals['mean']:.4f} [{vals['min']:.3f} - {vals['max']:.3f}]  valid={vals['valid_cells']}")


if __name__ == "__main__":
    main()
