#!/usr/bin/env python3
"""Download and pin a SoilGrids 250 m window for the Goslar focus area.

Reads clay / silt / sand / soil-organic-carbon at the 0-5, 5-15 and 15-30 cm
mean-depth slices from the official SoilGrids VRT collection via rasterio
windowed HTTP reads over the Goslar focus bounding box only. Each property /
depth window is written as a local GeoTIFF in the SoilGrids native Interrupted
Goode Homolosine CRS, then the 0-30 cm depth-weighted K-factor is computed with
the Williams (1995) EPIC/RUSLE pedotransfer function (US units, four factors)
and stored as a pinned 250 m snapshot.

This replaces the chain's previous un-versioned /latest/ remote read so the
Goslar K-factor is reproducible from a local source with recorded SHA-256
hashes and an access date. On failure the script raises instead of silently
falling back, so a broken source window is never hidden.

Run: .venv/bin/python bin/acquire/pull_goslar_soilgrids_window.py
"""

from __future__ import annotations

import hashlib
import json
import argparse
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds as window_from_bounds


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data/raw/soilgrids_250m_goslar"
RAW_DIR = OUT_DIR / "raw"
DIAGNOSTICS = OUT_DIR / "soilgrids_goslar_diagnostics.json"
K_SNAPSHOT = OUT_DIR / "k_factor_0_30cm_avg_250m_us.tif"
DATASET_ID = "soilgrids_250m_goslar"

FOCUS_LON_MIN, FOCUS_LAT_MIN, FOCUS_LON_MAX, FOCUS_LAT_MAX = 10.3646, 51.8544, 10.4194, 51.9089

SOILGRIDS_BASE = "https://files.isric.org/soilgrids/latest/data"
PROPERTIES = ["clay", "silt", "sand", "soc"]
TOPSOIL_SLICES = ["0-5cm", "5-15cm", "15-30cm"]
DEPTH_THICKNESS_CM = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}
SCALE_TO_PERCENT = {"clay": 10.0, "silt": 10.0, "sand": 10.0, "soc": 100.0}
SOILGRIDS_NODATA = -32768


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def williams_k(clay, silt, sand, soc):
    """Williams (1995) K-factor in US units. Inputs are percent arrays."""
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


def read_window_to_local(prop, depth, ref_crs, extent):
    """Read one SoilGrids VRT window and write it as a local GeoTIFF snapshot."""
    url = f"{SOILGRIDS_BASE}/{prop}/{prop}_{depth}_mean.vrt"
    with rasterio.open(url) as ds:
        if ds.crs != ref_crs:
            raise ValueError(f"SoilGrids CRS drift for {prop} {depth}: {ds.crs} != {ref_crs}")
        sx_min, sy_min, sx_max, sy_max = transform_bounds(
            "EPSG:4326", ds.crs,
            extent[0] - 0.02, extent[1] - 0.02,
            extent[2] + 0.02, extent[3] + 0.02,
            densify_pts=21,
        )
        window = window_from_bounds(sx_min, sy_min, sx_max, sy_max, transform=ds.transform)
        window = window.round_offsets().round_lengths()
        col0 = max(int(window.col_off), 0)
        row0 = max(int(window.row_off), 0)
        col1 = min(col0 + int(window.width), ds.width)
        row1 = min(row0 + int(window.height), ds.height)
        window = Window(col0, row0, max(col1 - col0, 1), max(row1 - row0, 1))
        data = ds.read(1, window=window).astype("float32")
        win_transform = ds.window_transform(window)
        nodata = ds.nodata if ds.nodata is not None else SOILGRIDS_NODATA
        data[data == nodata] = np.nan

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"{prop}_{depth}_mean.tif"
    profile = {
        "driver": "GTiff", "height": data.shape[0], "width": data.shape[1],
        "count": 1, "dtype": "float32", "crs": ref_crs, "transform": win_transform,
        "nodata": np.nan, "compress": "deflate", "tiled": True,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(np.where(np.isfinite(data), data, np.nan).astype("float32"), 1)

    finite = data[np.isfinite(data)]
    stats = {
        "valid_cells": int(finite.size),
        "min": float(finite.min()) if finite.size else None,
        "max": float(finite.max()) if finite.size else None,
        "mean": float(finite.mean()) if finite.size else None,
    }
    return out_path, sha256_file(out_path), data.shape, stats


def main() -> int:
    global OUT_DIR, RAW_DIR, DIAGNOSTICS, K_SNAPSHOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--extent", nargs=4, type=float, metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"))
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    args.out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    extent = tuple(args.extent) if args.extent else (FOCUS_LON_MIN, FOCUS_LAT_MIN, FOCUS_LON_MAX, FOCUS_LAT_MAX)

    OUT_DIR = args.out_dir
    RAW_DIR = OUT_DIR / "raw"
    DIAGNOSTICS = OUT_DIR / "soilgrids_goslar_diagnostics.json"
    K_SNAPSHOT = OUT_DIR / "k_factor_0_30cm_avg_250m_us.tif"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(f"{SOILGRIDS_BASE}/clay/clay_0-5cm_mean.vrt") as ref:
        ref_crs = ref.crs

    arrays = {}
    provenance = {
        "dataset_id": DATASET_ID,
        "source": "ISRIC SoilGrids 250m VRT (files.isric.org/soilgrids/latest/data)",
        "licence": "CC BY 4.0",
        "access_date": date.today().isoformat(),
        "focus_extent_wgs84": list(extent),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "native_crs": str(ref_crs),
        "depth_weighting_cm": DEPTH_THICKNESS_CM,
        "properties": PROPERTIES,
        "depth_slices": TOPSOIL_SLICES,
        "files": {},
    }

    win_transform = None
    ref_shape = None
    for depth in TOPSOIL_SLICES:
        for prop in PROPERTIES:
            out_path, digest, shape, stats = read_window_to_local(prop, depth, ref_crs, extent)
            with rasterio.open(out_path) as ds:
                arr = ds.read(1).astype("float32")
                arr[arr == SOILGRIDS_NODATA] = np.nan
                arr = arr / SCALE_TO_PERCENT[prop]
                arrays.setdefault(depth, {})[prop] = arr
                win_transform = ds.transform
                if ref_shape is None:
                    ref_shape = arr.shape
                elif arr.shape != ref_shape:
                    raise ValueError(
                        f"SoilGrids window shape mismatch for {prop} {depth}: "
                        f"{arr.shape} != {ref_shape}; K-factor requires aligned windows"
                    )
            provenance["files"][f"{prop}_{depth}_mean.tif"] = {
                "path": str(out_path.relative_to(ROOT)),
                "sha256": digest,
                "shape": [int(shape[0]), int(shape[1])],
                "scale_to_percent": SCALE_TO_PERCENT[prop],
                "stats_raw": stats,
            }
            print(f"pinned {prop} {depth}: {out_path.name} ({digest[:12]})", flush=True)

    total_cm = sum(DEPTH_THICKNESS_CM[d] for d in TOPSOIL_SLICES)
    k_stack = None
    for depth in TOPSOIL_SLICES:
        s = arrays[depth]
        k = williams_k(s["clay"], s["silt"], s["sand"], s["soc"])
        weight = DEPTH_THICKNESS_CM[depth] / total_cm
        k_stack = k * weight if k_stack is None else k_stack + k * weight
    if k_stack is None:
        raise RuntimeError("no SoilGrids windows read; K snapshot not built")

    profile = {
        "driver": "GTiff", "height": k_stack.shape[0], "width": k_stack.shape[1],
        "count": 1, "dtype": "float32", "crs": ref_crs, "transform": win_transform,
        "nodata": np.nan, "compress": "deflate", "tiled": True,
    }
    with rasterio.open(K_SNAPSHOT, "w", **profile) as dst:
        dst.write(np.where(np.isfinite(k_stack), k_stack, np.nan).astype("float32"), 1)

    finite = k_stack[np.isfinite(k_stack)]
    provenance["k_snapshot"] = {
        "path": str(K_SNAPSHOT.relative_to(ROOT)),
        "sha256": sha256_file(K_SNAPSHOT),
        "method": "Williams (1995) EPIC/RUSLE, US units, 4 factors, 0-30 cm depth-weighted",
        "unit": "US customary (0.0-~0.6); multiply by 0.1317 for SI",
        "shape": [int(k_stack.shape[0]), int(k_stack.shape[1])],
        "valid_cells": int(finite.size),
        "min": float(finite.min()) if finite.size else None,
        "max": float(finite.max()) if finite.size else None,
        "mean": float(finite.mean()) if finite.size else None,
    }
    provenance["generated_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    DIAGNOSTICS.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance["k_snapshot"], ensure_ascii=False, indent=2), flush=True)
    print(f"diagnostics: {DIAGNOSTICS.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
