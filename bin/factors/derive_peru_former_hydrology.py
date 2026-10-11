#!/usr/bin/env python3
"""Derive Arequipa Region hydrology products from the SRTM Arequipa Region DEM using WhiteboxTools.

Mirrors `derive_zimbabwe_hydrology.py`. Peru differences: Arequipa Region boundary, EPSG:32718 (UTM 18S), Arequipa Region
DEM/slope paths, peru_former_ output prefixes. Pipeline (fill -> D8 -> flow acc -> streams -> distance ->
TWI), the run_wbt wrapper, normalize-to-reference, and the float64 routing fix are identical.

All outputs are on the Arequipa Region 30 m reference grid (EPSG:32718). DIAGNOSTIC terrain/hydrology products
only; NOT interpretable flood-risk claims; do not authorize overlay or Zimbabwe-Peru comparison.
See the grid rules in AGENTS.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.features import geometry_mask

import whitebox

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/peru_former_pim_chain/terrain_preprocessing/peru_former_dem_utm18s_30m.tif", ROOT / "outputs/peru_former_boundary/peru_former_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/peru_former_pim_chain/hydrology_derivatives/peru_former_flow_accumulation_sca.tif", ROOT / "outputs/peru_former_pim_chain/hydrology_derivatives/peru_former_twi.tif", ROOT / "outputs/peru_former_pim_chain/hydrology_derivatives/peru_former_distance_to_drainage_t500.tif"]
DATASET_ID = "srtm_1arcsec_peru_former"
OUTPUT_ROOT_ID = "peru_former_pim_chain"  # outputs folder name (differs from the id since 2026-10-11 rename)
TERRAIN_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/terrain_preprocessing"
HYDRO_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/hydrology_derivatives"
TMP_DIR = HYDRO_DIR / "_raw_wbt"

PERU_HYBAS_L7_6070641200_DEM = TERRAIN_DIR / "peru_former_dem_utm18s_30m.tif"
PERU_HYBAS_L7_6070641200_SLOPE = TERRAIN_DIR / "peru_former_slope_degrees_utm18s_30m.tif"
PERU_HYBAS_L7_6070641200_GPKG = ROOT / "outputs/peru_former_boundary/peru_former_boundary.gpkg"
PERU_HYBAS_L7_6070641200_BOUNDARY_LAYER = "peru_pilot_boundary"

DST_CRS = "EPSG:32718"
NODATA = -9999.0
CELL_AREA_M2 = 30.0 * 30.0
CELL_AREA_KM2 = CELL_AREA_M2 / 1_000_000.0

STREAM_THRESHOLDS = (100, 500, 1000, 5000)
PRIMARY_THRESHOLD = 500

FILLED = HYDRO_DIR / "peru_former_dem_filled.tif"
D8_PNTR = HYDRO_DIR / "peru_former_flow_direction_d8.tif"
FLOW_ACC_CELLS = HYDRO_DIR / "peru_former_flow_accumulation.tif"
FLOW_ACC_SCA = HYDRO_DIR / "peru_former_flow_accumulation_sca.tif"
STREAM_OUT = {t: HYDRO_DIR / f"peru_former_streams_t{t}.tif" for t in STREAM_THRESHOLDS}
DISTANCE_OUT = HYDRO_DIR / "peru_former_distance_to_drainage_t500.tif"
TWI_OUT = HYDRO_DIR / "peru_former_twi.tif"

DENSITY_CSV = HYDRO_DIR / "peru_former_drainage_density_by_threshold.csv"
DENSITY_PNG = HYDRO_DIR / "peru_former_drainage_density_by_threshold.png"
GRID_CHECK_CSV = HYDRO_DIR / "hydrology_grid_check.csv"

GRID_GATE = ROOT / "bin" / "package" / "check_zimbabwe_raster_grid.py"


def rel(p: Path) -> str:
    return str(p.resolve().relative_to(ROOT))


def load_peru_former_mask(transform, shape) -> np.ndarray:
    boundary = gpd.read_file(PERU_HYBAS_L7_6070641200_GPKG, layer=PERU_HYBAS_L7_6070641200_BOUNDARY_LAYER).to_crs(DST_CRS)
    if len(boundary) != 1:
        raise ValueError("Expected exactly one Arequipa Region boundary feature")
    geom = boundary.geometry.iloc[0]
    return geometry_mask([geom], out_shape=shape, transform=transform, invert=True)


def reference_profile() -> dict:
    with rasterio.open(PERU_HYBAS_L7_6070641200_DEM) as ref:
        prof = ref.profile.copy()
        meta = {
            "crs": ref.crs, "transform": ref.transform, "width": ref.width,
            "height": ref.height, "bounds": ref.bounds, "res": ref.res,
            "count": ref.count, "dtype": ref.dtypes[0], "nodata": ref.nodata,
        }
    return {**prof, **meta}


def normalize_to_peru_former(raw_path: Path, dst_path: Path, ref: dict, peru_former_mask: np.ndarray) -> dict:
    with rasterio.open(raw_path) as src:
        if src.width != ref["width"] or src.height != ref["height"]:
            raise RuntimeError(
                f"{rel(raw_path)}: shape mismatch ({src.width}x{src.height}) vs "
                f"reference ({ref['width']}x{ref['height']}) -- whitebox altered the grid"
            )
        if src.transform != ref["transform"]:
            raise RuntimeError(f"{rel(raw_path)}: transform mismatch vs reference")
        data = src.read(1).astype("float32", copy=True)
        raw_nodata = src.nodata
    if raw_nodata is not None and not np.isnan(raw_nodata):
        data[data == np.float32(raw_nodata)] = np.nan
    data[~np.isfinite(data)] = np.nan
    data = np.where(peru_former_mask, data, np.nan)
    out = np.where(np.isfinite(data), data, np.float32(NODATA)).astype("float32")
    profile = {
        "driver": "GTiff", "height": ref["height"], "width": ref["width"], "count": 1,
        "dtype": "float32", "crs": ref["crs"], "transform": ref["transform"], "nodata": NODATA,
        "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
    }
    with rasterio.open(dst_path, "w", **profile) as dst:
        dst.write(out, 1)
    inside = peru_former_mask
    vals = out[inside]
    finite = vals[np.isfinite(vals) & (vals != np.float32(NODATA))]
    return {
        "path": rel(dst_path),
        "min": float(np.nanmin(finite)) if finite.size else None,
        "max": float(np.nanmax(finite)) if finite.size else None,
        "mean": float(np.nanmean(finite)) if finite.size else None,
        "valid_inside_peru_former": int(finite.size),
        "inside_peru_former_total": int(inside.sum()),
        "valid_fraction": float(finite.size / inside.sum()) if inside.sum() else 0.0,
    }


def run_wbt(tool_name: str, captured: list[str] | None = None, **kwargs) -> None:
    wbt = whitebox.WhiteboxTools()
    wbt.set_verbose_mode(False)

    def cb(message: str) -> bool:
        if captured is not None and message:
            captured.append(str(message).strip())
        return True

    tool = getattr(wbt, tool_name)
    rc = tool(callback=cb, **kwargs)
    if rc not in (True, 0):
        raise RuntimeError(f"whitebox {tool_name} failed (rc={rc}); args={kwargs}")


def main() -> int:
    if not PERU_HYBAS_L7_6070641200_DEM.exists():
        raise FileNotFoundError(f"Reference DEM missing: {PERU_HYBAS_L7_6070641200_DEM}")
    if not PERU_HYBAS_L7_6070641200_SLOPE.exists():
        raise FileNotFoundError(f"Arequipa Region slope missing: {PERU_HYBAS_L7_6070641200_SLOPE}")

    HYDRO_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    wbt_version = getattr(whitebox, "__version__", "unknown")
    ref = reference_profile()
    peru_former_mask = load_peru_former_mask(ref["transform"], (ref["height"], ref["width"]))
    aoi_cells = int(peru_former_mask.sum())
    aoi_km2 = aoi_cells * CELL_AREA_KM2
    print(f"reference grid {ref['width']}x{ref['height']} {ref['crs']} "
          f"| Arequipa Region AOI {aoi_cells} cells ({aoi_km2:.2f} km^2) | whitebox {wbt_version}")

    with rasterio.open(PERU_HYBAS_L7_6070641200_DEM) as s:
        dem = s.read(1).astype("float64")
    dem_nodata = np.float64(NODATA)
    dem_valid = dem != dem_nodata
    dem_inside = dem_valid & peru_former_mask

    diagnostics: dict = {
        "whitebox_version": wbt_version, "aoi_cells": aoi_cells, "aoi_km2": aoi_km2,
        "thresholds": STREAM_THRESHOLDS, "primary_threshold": PRIMARY_THRESHOLD,
        "reference_grid": rel(PERU_HYBAS_L7_6070641200_DEM), "crs": str(ref["crs"]),
        "width": ref["width"], "height": ref["height"], "cell_area_m2": CELL_AREA_M2,
        "boundary_status": "provisional_comparison_catchment_not_final_study_area",
    }

    # 1. fill depressions
    fill_log: list[str] = []
    raw_filled = TMP_DIR / "filled.tif"
    print("[1/6] fill_depressions_wang_and_liu ...")
    run_wbt("fill_depressions_wang_and_liu", captured=fill_log, dem=str(PERU_HYBAS_L7_6070641200_DEM),
            output=str(raw_filled), fix_flats=True)
    fill_stats = normalize_to_peru_former(raw_filled, FILLED, ref, peru_former_mask)
    with rasterio.open(FILLED) as s:
        filled = s.read(1).astype("float64")
    diff = np.zeros_like(dem)
    diff[dem_inside] = filled[dem_inside] - dem[dem_inside]
    pos_cm = diff[diff > 1e-2]
    diagnostics["fill"] = {
        "max_depth_m": float(diff.max()) if diff.size else 0.0,
        "n_cells_diff_gt_1cm": int(pos_cm.size),
        "frac_peru_former_cells_gt_1cm": float(pos_cm.size / aoi_cells),
        "filled_valid_fraction": fill_stats["valid_fraction"],
    }
    print(f"      filled sinks: max depth {diagnostics['fill']['max_depth_m']:.3f} m, "
          f"{diagnostics['fill']['n_cells_diff_gt_1cm']} cells > 1cm "
          f"({diagnostics['fill']['frac_peru_former_cells_gt_1cm']*100:.2f}% of Arequipa Region)")

    # 2. D8 pointer (from raw float64 filled DEM — float32 routing fix)
    raw_pntr = TMP_DIR / "d8pntr.tif"
    print("[2/6] d8_pointer (from raw float64 filled DEM) ...")
    run_wbt("d8_pointer", dem=str(raw_filled), output=str(raw_pntr), esri_pntr=False)
    normalize_to_peru_former(raw_pntr, D8_PNTR, ref, peru_former_mask)
    with rasterio.open(D8_PNTR) as s:
        _p = s.read(1)
    n_pits = int((_p[peru_former_mask] == 0).sum())
    diagnostics["d8_pointer_pit_cells"] = n_pits
    print(f"      code-0 pit cells inside Arequipa Region: {n_pits}")

    # 3. flow accumulation (cells + SCA)
    raw_acc_cells = TMP_DIR / "acc_cells.tif"
    raw_acc_sca = TMP_DIR / "acc_sca.tif"
    print("[3/6] d8_flow_accumulation (cells) ...")
    run_wbt("d8_flow_accumulation", i=str(D8_PNTR), output=str(raw_acc_cells),
            out_type="cells", pntr=True, esri_pntr=False)
    acc_stats = normalize_to_peru_former(raw_acc_cells, FLOW_ACC_CELLS, ref, peru_former_mask)
    print("[3/6] d8_flow_accumulation (specific contributing area) ...")
    run_wbt("d8_flow_accumulation", i=str(D8_PNTR), output=str(raw_acc_sca),
            out_type="specific contributing area", pntr=True, esri_pntr=False)
    sca_stats = normalize_to_peru_former(raw_acc_sca, FLOW_ACC_SCA, ref, peru_former_mask)
    max_acc = acc_stats["max"]
    diagnostics["flow_accumulation_cells"] = {
        "max_cells": max_acc,
        "max_area_km2": (max_acc * CELL_AREA_KM2) if max_acc is not None else None,
        "mean": acc_stats["mean"], "valid_fraction": acc_stats["valid_fraction"],
    }
    print(f"      max contributing area: {max_acc:.0f} cells = {max_acc * CELL_AREA_KM2:.2f} km^2")

    # 4. extract streams
    print(f"[4/6] extract_streams at {STREAM_THRESHOLDS} cells ...")
    density_rows = []
    for t in STREAM_THRESHOLDS:
        raw_stream = TMP_DIR / f"streams_t{t}.tif"
        run_wbt("extract_streams", flow_accum=str(raw_acc_cells), output=str(raw_stream),
                threshold=float(t), zero_background=True)
        with rasterio.open(raw_stream) as src:
            raw = src.read(1).astype("float32")
        rnodata = src.nodata
        if rnodata is not None and not np.isnan(rnodata):
            raw[raw == np.float32(rnodata)] = 0.0
        binary = np.where(raw > 0, 1.0, 0.0).astype("float32")
        out = np.where(peru_former_mask, binary, np.float32(NODATA)).astype("float32")
        profile = {
            "driver": "GTiff", "height": ref["height"], "width": ref["width"], "count": 1,
            "dtype": "float32", "crs": ref["crs"], "transform": ref["transform"], "nodata": NODATA,
            "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
        }
        with rasterio.open(STREAM_OUT[t], "w", **profile) as dst:
            dst.write(out, 1)
        n_stream = int(binary[peru_former_mask].sum())
        channel_len_m = n_stream * 30.0
        density = (channel_len_m / 1000.0) / aoi_km2 if aoi_km2 else float("nan")
        density_rows.append({
            "threshold_cells": t, "threshold_area_km2": round(t * CELL_AREA_KM2, 4),
            "stream_cells": n_stream, "channel_length_km_approx": round(channel_len_m / 1000.0, 2),
            "drainage_density_km_per_km2_approx": round(density, 4),
        })
        print(f"      t={t:>5}: {n_stream} cells, density ~{density:.3f} km/km^2")

    with DENSITY_CSV.open("w", encoding="utf-8") as fh:
        fh.write("threshold_cells,threshold_area_km2,stream_cells,"
                 "channel_length_km_approx,drainage_density_km_per_km2_approx\n")
        for r in density_rows:
            fh.write(f"{r['threshold_cells']},{r['threshold_area_km2']},"
                     f"{r['stream_cells']},{r['channel_length_km_approx']},"
                     f"{r['drainage_density_km_per_km2_approx']}\n")

    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ts = [r["threshold_cells"] for r in density_rows]
    ax[0].plot(ts, [r["stream_cells"] for r in density_rows], "o-", color="#1f77b4")
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel("Flow-accumulation threshold (cells)"); ax[0].set_ylabel("Stream cells")
    ax[0].set_title("Stream cell count vs threshold"); ax[0].grid(True, which="both", alpha=0.3)
    ax[1].plot(ts, [r["drainage_density_km_per_km2_approx"] for r in density_rows], "s-", color="#d62728")
    ax[1].set_xscale("log")
    ax[1].set_xlabel("Flow-accumulation threshold (cells)"); ax[1].set_ylabel("Drainage density (km/km^2)")
    ax[1].set_title("Drainage density vs threshold"); ax[1].grid(True, which="both", alpha=0.3)
    fig.suptitle("Peru Engineering Pilot Site: Drainage-Density Sensitivity (D8)", fontsize=11)
    fig.tight_layout(); fig.savefig(DENSITY_PNG, dpi=130); plt.close(fig)
    diagnostics["density_rows"] = density_rows

    # 5. distance to drainage
    print(f"[5/6] euclidean_distance (streams t{PRIMARY_THRESHOLD}) ...")
    raw_dist = TMP_DIR / "dist_t500.tif"
    run_wbt("euclidean_distance", i=str(STREAM_OUT[PRIMARY_THRESHOLD]), output=str(raw_dist))
    dist_stats = normalize_to_peru_former(raw_dist, DISTANCE_OUT, ref, peru_former_mask)
    diagnostics["distance_to_drainage_t500"] = {
        "min_m": dist_stats["min"], "max_m": dist_stats["max"],
        "mean_m": dist_stats["mean"], "valid_fraction": dist_stats["valid_fraction"],
    }
    print(f"      distance range: {dist_stats['min']:.1f}-{dist_stats['max']:.1f} m "
          f"(mean {dist_stats['mean']:.1f} m)")

    # 6. TWI
    print("[6/6] wetness_index (TWI) ...")
    raw_twi = TMP_DIR / "twi.tif"
    run_wbt("wetness_index", sca=str(raw_acc_sca), slope=str(PERU_HYBAS_L7_6070641200_SLOPE), output=str(raw_twi))
    twi_stats = normalize_to_peru_former(raw_twi, TWI_OUT, ref, peru_former_mask)
    diagnostics["twi"] = {
        "min": twi_stats["min"], "max": twi_stats["max"], "mean": twi_stats["mean"],
        "valid_fraction": twi_stats["valid_fraction"],
        "n_invalid_inside_peru_former": int(aoi_cells - twi_stats["valid_inside_peru_former"]),
    }
    print(f"      TWI range: {twi_stats['min']:.2f}-{twi_stats['max']:.2f} "
          f"(valid fraction {twi_stats['valid_fraction']:.4f})")

    for f in TMP_DIR.glob("*.tif"):
        try:
            f.unlink()
        except OSError:
            pass

    # grid gate
    gate_targets = [FLOW_ACC_CELLS, DISTANCE_OUT, FILLED, FLOW_ACC_SCA, TWI_OUT]
    print("[gate] running bin/package/check_zimbabwe_raster_grid.py ...")
    cmd = [sys.executable, str(GRID_GATE), "--reference", str(PERU_HYBAS_L7_6070641200_DEM),
           "--output", str(GRID_CHECK_CSV), "--rasters", *[str(p) for p in gate_targets]]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    diagnostics["grid_gate_stdout"] = proc.stdout.strip()
    diagnostics["grid_gate_returncode"] = proc.returncode
    print(proc.stdout.strip())
    if proc.stderr.strip():
        print("stderr:", proc.stderr.strip())

    (HYDRO_DIR / "hydrology_diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(f"\nwrote {rel(GRID_CHECK_CSV)}")
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
