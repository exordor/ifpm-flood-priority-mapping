#!/usr/bin/env python3
"""Derive V1 hydrology products from the SRTM V1 DEM using WhiteboxTools.

All outputs are written on the exact V1 30 m reference grid (EPSG:32735) defined by
``v1_dem_utm35s_30m.tif``. WhiteboxTools preserves input georeferencing; this script
re-encodes every output to float32 / NoData -9999.0 / V1 boundary mask so the grid gate
(``bin/check_v1_raster_grid.py``) sees the V1 reference grid exactly.

Pipeline (documented standard defaults; data-processing choices, recorded not gate-blocked):
    1. fill_depressions_wang_and_liu (Wang & Liu 2006), fix_flats=True
    2. d8_pointer (whitebox-native D8 encoding, esri_pntr=False)
    3. d8_flow_accumulation on the pointer, out_type 'cells' (primary) and
       'specific contributing area' (auxiliary, feeds TWI)
    4. extract_streams at thresholds 100 / 500 / 1000 / 5000 cells
    5. euclidean_distance to the t500 stream raster (primary threshold)
    6. wetness_index (TWI) from whitebox SCA + V1 slope (degrees)

Scope: these are DIAGNOSTIC terrain/hydrology data products only. They are NOT
interpretable flood-risk claims and do not authorize AHP overlay, CHIRPS pixel-level
overlay, or intervention-priority interpretation. See
``context/docs/data-management/v1_terrain_reference_grid_rule.md``.
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

ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "srtm_1arcsec_zimbabwe_prototype"
TERRAIN_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
HYDRO_DIR = ROOT / f"outputs/{DATASET_ID}/hydrology_derivatives"
TMP_DIR = HYDRO_DIR / "_raw_wbt"

V1_DEM = TERRAIN_DIR / "v1_dem_utm35s_30m.tif"
V1_SLOPE = TERRAIN_DIR / "v1_slope_degrees_utm35s_30m.tif"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
V1_BOUNDARY_LAYER = "v1_working_boundary"

DST_CRS = "EPSG:32735"
NODATA = -9999.0
CELL_AREA_M2 = 30.0 * 30.0
CELL_AREA_KM2 = CELL_AREA_M2 / 1_000_000.0

STREAM_THRESHOLDS = (100, 500, 1000, 5000)
PRIMARY_THRESHOLD = 500

# final raster names
FILLED = HYDRO_DIR / "v1_dem_filled.tif"
D8_PNTR = HYDRO_DIR / "v1_flow_direction_d8.tif"
FLOW_ACC_CELLS = HYDRO_DIR / "v1_flow_accumulation.tif"
FLOW_ACC_SCA = HYDRO_DIR / "v1_flow_accumulation_sca.tif"
STREAM_OUT = {t: HYDRO_DIR / f"v1_streams_t{t}.tif" for t in STREAM_THRESHOLDS}
DISTANCE_OUT = HYDRO_DIR / "v1_distance_to_drainage_t500.tif"
TWI_OUT = HYDRO_DIR / "v1_twi.tif"

DENSITY_CSV = HYDRO_DIR / "v1_drainage_density_by_threshold.csv"
DENSITY_PNG = HYDRO_DIR / "v1_drainage_density_by_threshold.png"
GRID_CHECK_CSV = HYDRO_DIR / "hydrology_grid_check.csv"
NOTE_MD = HYDRO_DIR / "hydrology_processing_note.md"

GRID_GATE = ROOT / "bin" / "check_v1_raster_grid.py"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def rel(p: Path) -> str:
    return str(p.resolve().relative_to(ROOT))


def load_v1_mask(transform, shape) -> np.ndarray:
    boundary = gpd.read_file(V1_GPKG, layer=V1_BOUNDARY_LAYER).to_crs(DST_CRS)
    if len(boundary) != 1:
        raise ValueError("Expected exactly one V1 working boundary feature")
    geom = boundary.geometry.iloc[0]
    return geometry_mask([geom], out_shape=shape, transform=transform, invert=True)


def reference_profile() -> dict:
    with rasterio.open(V1_DEM) as ref:
        prof = ref.profile.copy()
        meta = {
            "crs": ref.crs,
            "transform": ref.transform,
            "width": ref.width,
            "height": ref.height,
            "bounds": ref.bounds,
            "res": ref.res,
            "count": ref.count,
            "dtype": ref.dtypes[0],
            "nodata": ref.nodata,
        }
    return {**prof, **meta}


def normalize_to_v1(raw_path: Path, dst_path: Path, ref: dict, v1_mask: np.ndarray) -> dict:
    """Re-encode a raw WhiteboxTools raster onto the exact V1 grid.

    Asserts geometry matches the reference (WhiteboxTools should preserve it, but this
    catches any accidental resample). Casts to float32, sets NoData=-9999.0, and masks
    cells outside the V1 boundary to NoData.
    """
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
    # enforce V1 mask: inside-V1 keeps value, outside-V1 -> NoData
    data = np.where(v1_mask, data, np.nan)
    out = np.where(np.isfinite(data), data, np.float32(NODATA)).astype("float32")

    profile = {
        "driver": "GTiff",
        "height": ref["height"],
        "width": ref["width"],
        "count": 1,
        "dtype": "float32",
        "crs": ref["crs"],
        "transform": ref["transform"],
        "nodata": NODATA,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.open(dst_path, "w", **profile) as dst:
        dst.write(out, 1)

    inside = v1_mask
    vals = out[inside]
    finite = vals[np.isfinite(vals) & (vals != np.float32(NODATA))]
    return {
        "path": rel(dst_path),
        "min": float(np.nanmin(finite)) if finite.size else None,
        "max": float(np.nanmax(finite)) if finite.size else None,
        "mean": float(np.nanmean(finite)) if finite.size else None,
        "valid_inside_v1": int(finite.size),
        "inside_v1_total": int(inside.sum()),
        "valid_fraction": float(finite.size / inside.sum()) if inside.sum() else 0.0,
    }


def run_wbt(tool_name: str, captured: list[str] | None = None, **kwargs) -> None:
    """Call a WhiteboxTools tool with a text-capturing callback."""
    wbt = whitebox.WhiteboxTools()
    wbt.set_verbose_mode(False)

    def cb(message: str) -> bool:
        if captured is not None and message:
            captured.append(str(message).strip())
        return True

    tool = getattr(wbt, tool_name)
    rc = tool(callback=cb, **kwargs)
    # WhiteboxTools returns True (bool) or integer 0 on success; anything else
    # (False, non-zero int, None) is a failure.
    if rc not in (True, 0):
        raise RuntimeError(f"whitebox {tool_name} failed (rc={rc}); args={kwargs}")


def masked_stats(path: Path, v1_mask: np.ndarray) -> dict:
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
    vals = arr[v1_mask]
    vals = vals[np.isfinite(vals) & (vals != np.float32(NODATA))]
    return {
        "min": float(np.nanmin(vals)) if vals.size else None,
        "max": float(np.nanmax(vals)) if vals.size else None,
        "mean": float(np.nanmean(vals)) if vals.size else None,
        "n_valid": int(vals.size),
    }


# --------------------------------------------------------------------------- #
# pipeline
# --------------------------------------------------------------------------- #
def main() -> int:
    if not V1_DEM.exists():
        raise FileNotFoundError(f"Reference DEM missing: {V1_DEM}")
    if not V1_SLOPE.exists():
        raise FileNotFoundError(f"V1 slope missing: {V1_SLOPE}")
    if not GRID_GATE.exists():
        raise FileNotFoundError(f"Grid gate script missing: {GRID_GATE}")

    HYDRO_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    wbt_version = getattr(whitebox, "__version__", "unknown")
    ref = reference_profile()
    v1_mask = load_v1_mask(ref["transform"], (ref["height"], ref["width"]))
    aoi_cells = int(v1_mask.sum())
    aoi_km2 = aoi_cells * CELL_AREA_KM2
    print(
        f"reference grid {ref['width']}x{ref['height']} {ref['crs']} "
        f"| V1 AOI {aoi_cells} cells ({aoi_km2:.2f} km^2) | whitebox {wbt_version}"
    )

    with rasterio.open(V1_DEM) as s:
        dem = s.read(1).astype("float64")
    dem_nodata = np.float64(NODATA)
    dem_valid = dem != dem_nodata
    dem_inside = dem_valid & v1_mask

    diagnostics: dict = {
        "whitebox_version": wbt_version,
        "aoi_cells": aoi_cells,
        "aoi_km2": aoi_km2,
        "thresholds": STREAM_THRESHOLDS,
        "primary_threshold": PRIMARY_THRESHOLD,
        "reference_grid": rel(V1_DEM),
        "crs": str(ref["crs"]),
        "width": ref["width"],
        "height": ref["height"],
        "cell_area_m2": CELL_AREA_M2,
    }

    # 1. fill depressions (Wang & Liu 2006) ----------------------------------
    fill_log: list[str] = []
    raw_filled = TMP_DIR / "filled.tif"
    print("[1/6] fill_depressions_wang_and_liu ...")
    run_wbt(
        "fill_depressions_wang_and_liu",
        captured=fill_log,
        dem=str(V1_DEM),
        output=str(raw_filled),
        fix_flats=True,
    )
    fill_stats = normalize_to_v1(raw_filled, FILLED, ref, v1_mask)
    diagnostics["fill_log_excerpt"] = "\n".join(fill_log[-8:]) if fill_log else "(no text)"

    # sink-fill diagnostics: filled - dem on inside-V1 cells
    with rasterio.open(FILLED) as s:
        filled = s.read(1).astype("float64")
    diff = np.zeros_like(dem)
    diff[dem_inside] = filled[dem_inside] - dem[dem_inside]
    pos_all = diff[diff > 1e-9]
    pos_mm = diff[diff > 1e-3]   # > 1 mm
    pos_cm = diff[diff > 1e-2]   # > 1 cm
    diagnostics["fill"] = {
        "max_depth_m": float(diff.max()) if diff.size else 0.0,
        "mean_depth_positive_m": float(pos_all.mean()) if pos_all.size else 0.0,
        "n_cells_diff_gt_1mm": int(pos_mm.size),
        "n_cells_diff_gt_1cm": int(pos_cm.size),
        "frac_v1_cells_gt_1cm": float(pos_cm.size / aoi_cells),
        "fill_volume_m3_gt_1mm": float(pos_mm.sum() * CELL_AREA_M2),
        "filled_valid_fraction": fill_stats["valid_fraction"],
    }
    print(
        f"      filled sinks: max depth {diagnostics['fill']['max_depth_m']:.3f} m, "
        f"{diagnostics['fill']['n_cells_diff_gt_1cm']} cells > 1cm "
        f"({diagnostics['fill']['frac_v1_cells_gt_1cm']*100:.2f}% of V1)"
    )

    # 2. D8 flow pointer (whitebox-native encoding) --------------------------
    # Route from the RAW float64 filled DEM, NOT the normalized float32 copy.
    # fix_flats applies a sub-millimetre gradient (~1e-5 m) to flat plateaus so
    # flow can route across them. float32 epsilon is ~1e-4 m at ~1000 m elevation,
    # so casting the filled DEM to float32 destroys the gradient, reintroduces true
    # flats, and d8_pointer then marks them as code-0 (pit) cells -- which shatters
    # flow accumulation (verified: float32 routing -> 238k pit cells, max FA ~1500;
    # float64 routing -> 1.25k pit cells, max FA ~4.0e6 cells).
    raw_pntr = TMP_DIR / "d8pntr.tif"
    print("[2/6] d8_pointer (from raw float64 filled DEM) ...")
    run_wbt("d8_pointer", dem=str(raw_filled), output=str(raw_pntr), esri_pntr=False)
    pntr_stats = normalize_to_v1(raw_pntr, D8_PNTR, ref, v1_mask)
    with rasterio.open(D8_PNTR) as s:
        _p = s.read(1)
    n_pits = int((_p[v1_mask] == 0).sum())
    diagnostics["d8_pointer_encoding"] = (
        "whitebox-native (esri_pntr=False); codes E=1 SE=2 S=4 SW=8 W=16 NW=32 N=64 NE=128; 0 = pit/no-direction"
    )
    diagnostics["d8_pointer_pit_cells"] = n_pits
    print(f"      code-0 pit cells inside V1: {n_pits}")

    # 3. D8 flow accumulation (cells + SCA) ----------------------------------
    raw_acc_cells = TMP_DIR / "acc_cells.tif"
    raw_acc_sca = TMP_DIR / "acc_sca.tif"
    print("[3/6] d8_flow_accumulation (cells) ...")
    run_wbt(
        "d8_flow_accumulation",
        i=str(D8_PNTR),
        output=str(raw_acc_cells),
        out_type="cells",
        pntr=True,
        esri_pntr=False,
    )
    acc_stats = normalize_to_v1(raw_acc_cells, FLOW_ACC_CELLS, ref, v1_mask)
    print("[3/6] d8_flow_accumulation (specific contributing area) ...")
    run_wbt(
        "d8_flow_accumulation",
        i=str(D8_PNTR),
        output=str(raw_acc_sca),
        out_type="specific contributing area",
        pntr=True,
        esri_pntr=False,
    )
    sca_stats = normalize_to_v1(raw_acc_sca, FLOW_ACC_SCA, ref, v1_mask)

    max_acc = acc_stats["max"]
    diagnostics["flow_accumulation_cells"] = {
        "min": acc_stats["min"],
        "max_cells": max_acc,
        "max_area_km2": (max_acc * CELL_AREA_KM2) if max_acc is not None else None,
        "mean": acc_stats["mean"],
        "valid_fraction": acc_stats["valid_fraction"],
    }
    diagnostics["flow_accumulation_sca"] = {
        "min": sca_stats["min"],
        "max": sca_stats["max"],
        "mean": sca_stats["mean"],
        "valid_fraction": sca_stats["valid_fraction"],
    }
    print(
        f"      max contributing area: {max_acc:.0f} cells = "
        f"{max_acc * CELL_AREA_KM2:.2f} km^2"
    )

    # 4. extract streams at multiple thresholds ------------------------------
    print(f"[4/6] extract_streams at {STREAM_THRESHOLDS} cells ...")
    density_rows = []
    for t in STREAM_THRESHOLDS:
        raw_stream = TMP_DIR / f"streams_t{t}.tif"
        run_wbt(
            "extract_streams",
            flow_accum=str(raw_acc_cells),
            output=str(raw_stream),
            threshold=float(t),
            zero_background=True,
        )
        # normalize to binary 1=stream, 0=background (inside V1), NoData (outside)
        with rasterio.open(raw_stream) as src:
            raw = src.read(1).astype("float32")
        rnodata = src.nodata
        if rnodata is not None and not np.isnan(rnodata):
            raw[raw == np.float32(rnodata)] = 0.0
        binary = np.where(raw > 0, 1.0, 0.0).astype("float32")
        out = np.where(v1_mask, binary, np.float32(NODATA)).astype("float32")
        profile = {
            "driver": "GTiff", "height": ref["height"], "width": ref["width"],
            "count": 1, "dtype": "float32", "crs": ref["crs"],
            "transform": ref["transform"], "nodata": NODATA,
            "compress": "deflate", "tiled": True,
            "blockxsize": 256, "blockysize": 256,
        }
        with rasterio.open(STREAM_OUT[t], "w", **profile) as dst:
            dst.write(out, 1)

        n_stream = int(binary[v1_mask].sum())
        channel_len_m = n_stream * 30.0  # first-order; ignores diagonal correction
        density = (channel_len_m / 1000.0) / aoi_km2 if aoi_km2 else float("nan")
        thr_area_km2 = t * CELL_AREA_KM2
        density_rows.append(
            {
                "threshold_cells": t,
                "threshold_area_km2": round(thr_area_km2, 4),
                "stream_cells": n_stream,
                "channel_length_km_approx": round(channel_len_m / 1000.0, 2),
                "drainage_density_km_per_km2_approx": round(density, 4),
            }
        )
        print(
            f"      t={t:>5} ({thr_area_km2:.3f} km^2): {n_stream} cells, "
            f"density ~{density:.3f} km/km^2"
        )

    # write density csv
    with DENSITY_CSV.open("w", encoding="utf-8") as fh:
        fh.write(
            "threshold_cells,threshold_area_km2,stream_cells,"
            "channel_length_km_approx,drainage_density_km_per_km2_approx\n"
        )
        for r in density_rows:
            fh.write(
                f"{r['threshold_cells']},{r['threshold_area_km2']},"
                f"{r['stream_cells']},{r['channel_length_km_approx']},"
                f"{r['drainage_density_km_per_km2_approx']}\n"
            )

    # density figure
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ts = [r["threshold_cells"] for r in density_rows]
    ax[0].plot(ts, [r["stream_cells"] for r in density_rows], "o-", color="#1f77b4")
    ax[0].set_xscale("log")
    ax[0].set_yscale("log")
    ax[0].set_xlabel("Flow-accumulation threshold (cells)")
    ax[0].set_ylabel("Stream cells inside V1")
    ax[0].set_title("Stream cell count vs threshold")
    ax[0].grid(True, which="both", alpha=0.3)
    ax[1].plot(
        ts,
        [r["drainage_density_km_per_km2_approx"] for r in density_rows],
        "s-",
        color="#d62728",
    )
    ax[1].set_xscale("log")
    ax[1].set_xlabel("Flow-accumulation threshold (cells)")
    ax[1].set_ylabel("Drainage density (km/km^2, approx)")
    ax[1].set_title("Drainage density vs threshold")
    ax[1].grid(True, which="both", alpha=0.3)
    fig.suptitle("V1 drainage density sensitivity (D8, whitebox)", fontsize=11)
    fig.tight_layout()
    fig.savefig(DENSITY_PNG, dpi=130)
    plt.close(fig)
    diagnostics["density_rows"] = density_rows

    # 5. distance to drainage (t500 primary) ---------------------------------
    print(f"[5/6] euclidean_distance (streams t{PRIMARY_THRESHOLD}) ...")
    raw_dist = TMP_DIR / "dist_t500.tif"
    run_wbt("euclidean_distance", i=str(STREAM_OUT[PRIMARY_THRESHOLD]), output=str(raw_dist))
    dist_stats = normalize_to_v1(raw_dist, DISTANCE_OUT, ref, v1_mask)
    diagnostics["distance_to_drainage_t500"] = {
        "min_m": dist_stats["min"],
        "max_m": dist_stats["max"],
        "mean_m": dist_stats["mean"],
        "valid_fraction": dist_stats["valid_fraction"],
    }
    print(
        f"      distance range: {dist_stats['min']:.1f}-{dist_stats['max']:.1f} m "
        f"(mean {dist_stats['mean']:.1f} m)"
    )

    # 6. TWI from whitebox SCA + V1 slope (degrees) --------------------------
    print("[6/6] wetness_index (TWI) ...")
    raw_twi = TMP_DIR / "twi.tif"
    run_wbt(
        "wetness_index",
        sca=str(raw_acc_sca),
        slope=str(V1_SLOPE),
        output=str(raw_twi),
    )
    twi_stats = normalize_to_v1(raw_twi, TWI_OUT, ref, v1_mask)
    diagnostics["twi"] = {
        "min": twi_stats["min"],
        "max": twi_stats["max"],
        "mean": twi_stats["mean"],
        "valid_fraction": twi_stats["valid_fraction"],
        "n_invalid_inside_v1": int(aoi_cells - twi_stats["valid_inside_v1"]),
    }
    print(
        f"      TWI range: {twi_stats['min']:.2f}-{twi_stats['max']:.2f} "
        f"(valid fraction inside V1 {twi_stats['valid_fraction']:.4f})"
    )

    # clean raw tmp (keep dir, drop tifs)
    for f in TMP_DIR.glob("*.tif"):
        try:
            f.unlink()
        except OSError:
            pass

    # ----------------------------------------------------------------------- #
    # grid gate: run on flow_accumulation + distance_to_drainage (required),
    # plus filled DEM, SCA, and TWI for completeness.
    # ----------------------------------------------------------------------- #
    gate_targets = [
        FLOW_ACC_CELLS,
        DISTANCE_OUT,
        FILLED,
        FLOW_ACC_SCA,
        TWI_OUT,
    ]
    print("[gate] running bin/check_v1_raster_grid.py ...")
    cmd = [
        sys.executable,
        str(GRID_GATE),
        "--reference",
        str(V1_DEM),
        "--output",
        str(GRID_CHECK_CSV),
        "--rasters",
        *[str(p) for p in gate_targets],
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    diagnostics["grid_gate_stdout"] = proc.stdout.strip()
    diagnostics["grid_gate_stderr"] = proc.stderr.strip()
    diagnostics["grid_gate_returncode"] = proc.returncode
    print(proc.stdout.strip())
    if proc.stderr.strip():
        print("stderr:", proc.stderr.strip())

    write_note(diagnostics)
    write_diagnostics_json(diagnostics)
    print(f"\nwrote {rel(NOTE_MD)}")
    print(f"wrote {rel(GRID_CHECK_CSV)}")
    print("done.")
    return 0


def write_diagnostics_json(d: dict) -> None:
    out = HYDRO_DIR / "hydrology_diagnostics.json"
    out.write_text(json.dumps(d, indent=2), encoding="utf-8")


def write_note(d: dict) -> None:
    fill = d["fill"]
    acc = d["flow_accumulation_cells"]
    twi = d["twi"]
    dist = d["distance_to_drainage_t500"]
    rows = d["density_rows"]
    n_pits = d.get("d8_pointer_pit_cells", "n/a")
    aoi = d["aoi_cells"]

    def fmt(v, n=3):
        return "n/a" if v is None else f"{v:.{n}f}"

    primary_area_km2 = d["primary_threshold"] * CELL_AREA_KM2

    density_table = "\n".join(
        f"| {r['threshold_cells']} | {r['threshold_area_km2']:.3f} | "
        f"{r['stream_cells']} | {r['channel_length_km_approx']:.2f} | "
        f"{r['drainage_density_km_per_km2_approx']:.3f} |"
        for r in rows
    )

    note = f"""# V1 Hydrology Derivatives -- Processing Note

Generated: {date.today().isoformat()}
Script: `bin/derive_v1_hydrology.py`
Reference grid rule: `context/docs/data-management/v1_terrain_reference_grid_rule.md`

## Status

DIAGNOSTIC terrain/hydrology data products derived from the V1 SRTM DEM. These products
are **not** interpretable flood-risk claims and do **not** authorize AHP overlay, CHIRPS
pixel-level overlay, or intervention-priority interpretation. V1 remains
`accepted_with_waiver_for_controlled_prototype`, not a final thesis boundary.

## Environment

- WhiteboxTools python module version: `{d['whitebox_version']}` (task brief stated 2.4.0;
  installed `.venv` reports `{d['whitebox_version']}`). Tool names below are the actual
  whitebox v2.x names (the brief's `d8_flow_accum` / `topographic_wetness_index` do not
  exist; the correct names are `d8_flow_accumulation` and `wetness_index`).
- Reference grid: `{d['reference_grid']}` -- {d['crs']}, 30 m, float32, NoData -9999.0,
  {d['width']}x{d['height']} px. V1 AOI = {d['aoi_cells']} cells ({d['aoi_km2']:.2f} km^2).

## Inputs

- DEM: `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`
- Slope (degrees): `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_slope_degrees_utm35s_30m.tif`
  (V1 central-difference slope, NOT whitebox's Horn slope -- feeds TWI as-is.)

## Method

1. **Fill depressions** -- `fill_depressions_wang_and_liu` (Wang & Liu 2006), `fix_flats=True`
   so a small gradient is applied to flats for routing. Whitebox itself notes depression
   *breaching* is usually preferred; filling was chosen here to match the documented V1
   standard default and to avoid carving artificial trenches across the prototype AOI.
2. **D8 flow direction** -- `d8_pointer` with `esri_pntr=False` (whitebox-native encoding).
   {d['d8_pointer_encoding']}.
3. **D8 flow accumulation** -- `d8_flow_accumulation` on the pointer (`pntr=True`), primary
   output `out_type='cells'` (contributing cell count). Auxiliary
   `out_type='specific contributing area'` (`v1_flow_accumulation_sca.tif`) feeds the TWI
   step in whitebox's own SCA convention.
4. **Stream extraction** -- `extract_streams` (`zero_background=True`) at thresholds
   {', '.join(str(t) for t in d['thresholds'])} cells. Threshold areas at 30 m:
   {CELL_AREA_KM2 * 100:.3f}, {CELL_AREA_KM2 * 500:.3f}, {CELL_AREA_KM2 * 1000:.3f},
   {CELL_AREA_KM2 * 5000:.3f} km^2.
5. **Distance to drainage** -- `euclidean_distance` to the **t{d['primary_threshold']}**
   stream raster (primary). Threshold area = {primary_area_km2:.3f} km^2
   ({d['primary_threshold']} cells x 900 m^2). This is finer than typical ~1 km^2
   channel-initiation thresholds; chosen to approximate the Mzingwane channel density at
   30 m SRTM resolution. It will include headwater/valley threads; treat as a proximity
   proxy, not a mapped river network.
6. **TWI** -- `wetness_index` from whitebox SCA + V1 slope (degrees): `ln(A / tan(slope))`.

All whitebox raw outputs were re-encoded to the exact V1 grid (float32, NoData -9999.0,
masked to the V1 boundary) so the grid gate sees the reference grid exactly.

## Edge handling

The V1 DEM is cropped to the V1 working-boundary bounding box with NoData (-9999.0) outside
the V1 polygon. Whitebox therefore treats the V1 boundary as a no-flow margin: flow reaching
the boundary exits the domain with no wrap-around. **The V1 working boundary is an
administrative/working boundary, NOT a watershed divide**, so flow accumulation near the
boundary underestimates true upslope area (cells outside V1 do not contribute). This is the
dominant caveat for any downstream use of `v1_flow_accumulation.tif`.

## Anomalies and engineering findings

- **float32 precision vs fix_flats gradient (FIXED in script).** `fill_depressions_wang_and_liu`
  with `fix_flats=True` writes a float64 filled DEM and applies a sub-millimetre gradient
  (~1e-5 m) to flat plateaus so D8 flow can route across them. float32 epsilon at the AOI's
  elevation range (~860-1530 m) is ~1e-4 m, which is *larger* than the gradient. Casting the
  filled DEM to float32 therefore rounds the gradient away, reintroduces true flats, and
  `d8_pointer` marks those cells as code-0 pits. In a naive chain this shattered the flow
  network (238k pit cells, max flow accumulation ~1500 cells = 1.35 km^2 -- absurd for a
  3690 km^2 AOI). The script routes `d8_pointer` and all downstream whitebox steps from the
  **raw float64** filled DEM; only the final delivered products are cast to float32 to satisfy
  the V1 grid gate. After the fix: {n_pits} code-0 pit cells inside V1 and max flow
  accumulation {fmt(acc['max_cells'], 0)} cells ({fmt(acc['max_area_km2'], 2)} km^2), i.e.
  ~{fmt(acc['max_area_km2']/d['aoi_km2']*100, 1)}% of the AOI reaches the main outlet. The
  delivered `v1_dem_filled.tif` is float32 and therefore contains sub-mm plateau artifacts;
  it is a filled-DEM product, not a routing input.
- **D8 pointer pit cells (code 0):** {n_pits} inside V1 ({fmt(n_pits/aoi*100, 3)} % of V1).
  These are genuine local minima / boundary-outlet cells where flow terminates, not fill
  artifacts.
- **Whitebox version:** installed `.venv` reports `{d['whitebox_version']}` (the task brief
  stated 2.4.0). Correct tool names in this version are `d8_flow_accumulation` and
  `wetness_index` (the brief's `d8_flow_accum` / `topographic_wetness_index` do not exist).

## Drainage density by threshold

| Threshold (cells) | Threshold area (km^2) | Stream cells | Channel length (km, approx) | Drainage density (km/km^2, approx) |
|---:|---:|---:|---:|---:|
{density_table}

Channel length is a first-order cell count x 30 m and ignores the diagonal correction
(actual channel length is slightly longer). Figure: `v1_drainage_density_by_threshold.png`.

## Key diagnostics

- Max flow accumulation: **{fmt(acc['max_cells'], 0)} cells** =
  **{fmt(acc['max_area_km2'], 2)} km^2** contributing area.
- Chosen primary threshold: **{d['primary_threshold']} cells = {primary_area_km2:.3f} km^2**
  per initiating cell. (The brief's "~4.5 km^2" was a typo; 500 cells x 900 m^2 = 0.45 km^2.)
- Sink fills (filled - dem, inside V1): max depth **{fmt(fill['max_depth_m'], 3)} m**;
  cells > 1 cm: **{fill['n_cells_diff_gt_1cm']}** ({fill['frac_v1_cells_gt_1cm']*100:.2f} %
  of V1); fill volume (cells > 1 mm) ~ **{fmt(fill['fill_volume_m3_gt_1mm'], 0)} m^3**.
  Most of the diff field is the `fix_flats` sub-millimetre increment; the > 1 cm count is
  the cleaner sink-fill indicator.
- Distance to drainage (t500): range **{fmt(dist['min_m'], 1)}-{fmt(dist['max_m'], 1)} m**,
  mean **{fmt(dist['mean_m'], 1)} m**; valid fraction inside V1 **{dist['valid_fraction']:.4f}**.
- TWI: range **{fmt(twi['min'], 2)}-{fmt(twi['max'], 2)}**, mean **{fmt(twi['mean'], 2)}**;
  valid fraction inside V1 **{twi['valid_fraction']:.4f}**
  ({twi['n_invalid_inside_v1']} inside-V1 cells are NoData).

## Grid-gate result

`hydrology_grid_check.csv` records `bin/check_v1_raster_grid.py` on the filled DEM,
flow-accumulation (cells + SCA), distance-to-drainage, and TWI. Geometry (CRS, transform,
width, height, dtype float32, NoData -9999.0) must be `grid_compatible=true` for every
checked raster. A non-geometry flag (e.g. low `valid_cell_fraction` on TWI from legitimate
NoData at flat/slope-zero cells) is a hydrology data gap, not a grid break.

Gate stdout:
```
{d.get('grid_gate_stdout', '')}
```

## Outputs

Directory: `outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_derivatives/`

- `v1_dem_filled.tif` -- depression-filled DEM (Wang-Liu).
- `v1_flow_direction_d8.tif` -- D8 pointer (whitebox-native codes).
- `v1_flow_accumulation.tif` -- D8 contributing cell count.
- `v1_flow_accumulation_sca.tif` -- D8 specific contributing area (auxiliary; feeds TWI).
- `v1_streams_t100.tif` / `t500` / `t1000` / `t5000` -- binary stream rasters.
- `v1_distance_to_drainage_t500.tif` -- Euclidean distance to t500 streams (metres).
- `v1_twi.tif` -- topographic wetness index.
- `hydrology_grid_check.csv` -- grid-gate manifest.
- `v1_drainage_density_by_threshold.csv` / `.png` -- drainage-density sensitivity.
- `hydrology_diagnostics.json` -- machine-readable diagnostics.
"""
    NOTE_MD.write_text(note, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
