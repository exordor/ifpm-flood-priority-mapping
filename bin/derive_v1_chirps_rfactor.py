#!/usr/bin/env python3
"""Derive USLE/RUSLE rainfall-erosivity R-factor for V1 from CHIRPS annual + monthly TIFs.

Local TOOLING script. Reads already-downloaded CHIRPS Africa TIFs (annual 1981-2024 and rainy-season
monthly Nov-Mar) for the V1 bounding-box window only (no full-Africa arrays are stacked). Computes
the Modified Fournier Index (MFI; Arnoldus 1980) and converts it to the USLE/RUSLE R-factor via the
Renard & Freimund (1994) coefficients.

CRITICAL GRID RULE: CHIRPS is ~0.05 deg (~5 km). The R-factor is produced ONLY on the native CHIRPS
0.05 deg grid (V1 window) and as a V1 zonal scalar. It is NOT resampled to the V1 30 m terrain grid
(per context/docs/data-management/v1_terrain_reference_grid_rule.md). No 30 m raster is produced.

Formulas:
    MFI (Arnoldus 1980) = sum_i( Pi^2 ) / P_annual
        where Pi = long-term mean precipitation for month i (mm), summed over the available months,
        and P_annual = long-term mean annual precipitation (mm).
    R-factor (Renard & Freimund 1994), in MJ.mm.ha-1.h-1.yr-1:
        if MFI <  80: R = 0.0483 * MFI^1.61
        if MFI >= 80: R = 587.8 - 1.219*MFI + 0.004105*MFI^2

KNOWN LIMITATION (documented in outputs): only Nov, Dec, Jan, Feb, Mar monthly means are available
(rainy season). Apr-Oct monthly means are missing, so the MFI numerator is summed over 5 months only.
This UNDERESTIMATES the true 12-month MFI modestly; in semi-arid southern Africa the dry-season
months contribute little to erosivity, so the bias is small and conservative. P_annual in the
denominator is the full 12-month annual total from the annual TIFs (correct).

Usage (from workspace root):
    .venv/bin/python bin/derive_v1_chirps_rfactor.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds

try:
    import geopandas as gpd
except ImportError as exc:
    raise SystemExit(f"missing dependency: {exc}. Install geopandas in .venv.") from exc

ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "chirps_v3_zimbabwe_prototype"
ANNUAL_DIR = ROOT / f"data/raw/{DATASET_ID}/annual_africa_tifs"
MONTHLY_DIR = ROOT / f"data/raw/{DATASET_ID}/monthly_africa_tifs"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
V1_BOUNDARY_LAYER = "v1_working_boundary"

# V1 bounding box in EPSG:4326 (CHIRPS native CRS). Windowed reads are clipped to this box and
# aligned to the CHIRPS 0.05 deg grid. A small padding is added so the boundary polygon is fully
# covered by grid cells (the polygon total_bounds is slightly inside this bbox).
V1_LON_MIN, V1_LAT_MIN, V1_LON_MAX, V1_LAT_MAX = 28.514, -21.008, 29.398, -19.984

OUT_DIR = ROOT / f"outputs/{DATASET_ID}/r_factor"
OUT_RASTER = OUT_DIR / "r_factor_modified_fournier_0p05deg.tif"
OUT_DIAG = OUT_DIR / "r_factor_diagnostics.json"
OUT_NOTE = OUT_DIR / "r_factor_processing_note.md"

# Rainy-season calendar months present in the monthly TIF inventory (Nov, Dec, Jan, Feb, Mar).
RAINCY_MONTHS = [11, 12, 1, 2, 3]
# Climatology year range for the long-term mean (full record).
ANNUAL_YEAR_RANGE = (1981, 2024)
MONTHLY_YEAR_RANGE = (1981, 2024)

NODATA = -9999.0
ANNUAL_RE = re.compile(r"chirps-v3\.0\.(\d{4})\.tif$")
MONTHLY_RE = re.compile(r"chirps-v3\.0\.(\d{4})\.(\d{2})\.tif$")


def list_annual_files() -> list[tuple[int, Path]]:
    out: list[tuple[int, Path]] = []
    for p in sorted(ANNUAL_DIR.glob("chirps-v3.0.*.tif")):
        m = ANNUAL_RE.match(p.name)
        if m:
            out.append((int(m.group(1)), p))
    return out


def list_monthly_files() -> list[tuple[int, int, Path]]:
    out: list[tuple[int, int, Path]] = []
    for p in sorted(MONTHLY_DIR.glob("chirps-v3.0.*.*.tif")):
        m = MONTHLY_RE.match(p.name)
        if m:
            out.append((int(m.group(1)), int(m.group(2)), p))
    return out


def compute_v1_window():
    """Open one CHIRPS file to derive the integer V1 window aligned to the 0.05 deg grid.

    Returns (Window, transform, crs, height, width) so callers can reuse the same grid.
    """
    ref = ANNUAL_DIR / "chirps-v3.0.1981.tif"
    if not ref.exists():
        ref = list_annual_files()[0][1]
    with rasterio.open(ref) as ds:
        win_f = from_bounds(V1_LON_MIN, V1_LAT_MIN, V1_LON_MAX, V1_LAT_MAX, ds.transform)
        # Snap to integer pixel bounds so every file reads the identical grid window.
        col_off = int(np.floor(win_f.col_off))
        row_off = int(np.floor(win_f.row_off))
        width = int(np.ceil(win_f.width))
        height = int(np.ceil(win_f.height))
        win = Window(col_off=col_off, row_off=row_off, width=width, height=height)
        transform = ds.window_transform(win)
        crs = ds.crs
    return win, transform, crs, height, width


def read_window(path: Path, win: Window) -> np.ndarray:
    """Read the V1 window from a CHIRPS TIF as float32 with NaN for missing values."""
    with rasterio.open(path) as ds:
        arr = ds.read(1, window=win).astype("float32")
    # CHIRPS Africa TIFs declare nodata=None; guard against any non-finite or negative fill values.
    arr[~np.isfinite(arr)] = np.nan
    arr[arr < 0] = np.nan
    return arr


def long_term_mean(files: list[Path], win: Window) -> tuple[np.ndarray, int]:
    """Incremental long-term mean of a stack of windowed rasters (memory-friendly)."""
    if not files:
        raise ValueError("no files supplied to long_term_mean")
    acc = None
    count = 0
    for p in files:
        arr = read_window(p, win)
        if acc is None:
            acc = np.zeros_like(arr, dtype="float64")
        valid = np.isfinite(arr)
        acc = np.where(valid, acc + arr, acc)
        count += 1
    acc = acc / count
    return acc.astype("float32"), count


def renard_freimund_r(mfi: np.ndarray) -> np.ndarray:
    """Renard & Freimund (1994) R-factor from MFI. Piecewise; vectorised."""
    mfi = np.where(mfi <= 0, np.nan, mfi)
    low = mfi < 80.0
    high = ~low
    r = np.full_like(mfi, np.nan, dtype="float64")
    r_low = 0.0483 * np.power(mfi, 1.61)
    r_high = 587.8 - 1.219 * mfi + 0.004105 * np.power(mfi, 2.0)
    r = np.where(low & np.isfinite(mfi), r_low, r)
    r = np.where(high & np.isfinite(mfi), r_high, r)
    return r.astype("float32")


def zonal_stats(arr: np.ndarray, mask: np.ndarray) -> dict:
    vals = arr[mask & np.isfinite(arr)]
    if vals.size == 0:
        return {"valid_cells": 0}
    return {
        "valid_cells": int(vals.size),
        "mean": float(np.mean(vals)),
        "std": float(np.std(vals)),
        "min": float(np.min(vals)),
        "p05": float(np.percentile(vals, 5)),
        "p50": float(np.percentile(vals, 50)),
        "p95": float(np.percentile(vals, 95)),
        "max": float(np.max(vals)),
    }


def main() -> None:
    raise SystemExit(
        "DEPRECATED: do not regenerate V1 R-factor from the wrong Renard-Freimund setup "
        "(P-based coefficients on MFI with invented break at 80). "
        "See outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md "
        "and context/docs/project-management/rfactor_investigation_consolidated.md."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    win, transform, crs, h, w = compute_v1_window()
    print(f"V1 window: {w} x {h} px @ 0.05 deg (EPSG:4326), transform={transform}")

    # --- V1 boundary mask on the CHIRPS grid (boundary is already EPSG:4326) ---
    boundary = gpd.read_file(V1_GPKG, layer=V1_BOUNDARY_LAYER).to_crs(crs)
    shapes = [(geom, 1) for geom in boundary.geometry if geom is not None and not geom.is_empty]
    v1_mask = rasterize(shapes, out_shape=(h, w), transform=transform, fill=0, dtype="uint8", all_touched=False)
    print(f"V1 boundary rasterized: {int(v1_mask.sum())} CHIRPS cells inside V1 "
          f"({100 * v1_mask.sum() / (w * h):.1f}% of window)")

    # --- 1. Long-term mean annual precipitation (1981-2024 full climatology) ---
    annual_files_all = list_annual_files()
    y_lo, y_hi = ANNUAL_YEAR_RANGE
    annual_files = [p for (y, p) in annual_files_all if y_lo <= y <= y_hi]
    if not annual_files:
        raise SystemExit(f"no annual CHIRPS files found in {ANNUAL_YEAR_RANGE}")
    p_annual, n_annual = long_term_mean(annual_files, win)
    p_annual = np.where(v1_mask == 1, p_annual, np.nan)  # restrict stats to V1
    print(f"P_annual ({y_lo}-{y_hi}, n={n_annual}): V1 mean={np.nanmean(p_annual):.1f} mm/yr")

    # --- 2. Long-term mean monthly precipitation per rainy-season month ---
    monthly_files_all = list_monthly_files()
    my_lo, my_hi = MONTHLY_YEAR_RANGE
    monthly_files_by_cal = {m: [] for m in RAINCY_MONTHS}
    missing_year_month: list[str] = []
    for (y, m, p) in monthly_files_all:
        if my_lo <= y <= my_hi and m in monthly_files_by_cal:
            monthly_files_by_cal[m].append(p)
    # Check completeness against the expected 5 months per rainy season.
    expected_cal_counts = {11: 0, 12: 0, 1: 0, 2: 0, 3: 0}
    for (y, m, _p) in monthly_files_all:
        if my_lo <= y <= my_hi:
            expected_cal_counts[m] = expected_cal_counts.get(m, 0) + 1

    p_monthly: dict[int, np.ndarray] = {}
    monthly_counts: dict[int, int] = {}
    for m in RAINCY_MONTHS:
        files = monthly_files_by_cal[m]
        if not files:
            missing_year_month.append(f"cal month {m:02d}: no files")
            continue
        arr, n = long_term_mean(files, win)
        arr = np.where(v1_mask == 1, arr, np.nan)
        p_monthly[m] = arr
        monthly_counts[m] = n
        print(f"  P_month cal {m:02d} (n={n}): V1 mean={np.nanmean(arr):.1f} mm/month")

    # --- 3. Modified Fournier Index (Arnoldus 1980) over available months ---
    # MFI = sum_i(Pi^2) / P_annual. Numerator summed over the 5 available months only.
    numerator = np.zeros_like(p_annual, dtype="float64")
    contributing_months: list[int] = []
    for m, arr in p_monthly.items():
        numerator = np.where(np.isfinite(arr), numerator + arr.astype("float64") ** 2, numerator)
        contributing_months.append(m)
    with np.errstate(divide="ignore", invalid="ignore"):
        mfi = numerator / p_annual
    mfi = np.where(v1_mask == 1, mfi, np.nan)
    print(f"MFI (5-month): V1 mean={np.nanmean(mfi):.2f}")

    # --- 4. R-factor (Renard & Freimund 1994) ---
    r_factor = renard_freimund_r(mfi)
    r_factor = np.where(v1_mask == 1, r_factor, np.nan)
    print(f"R-factor: V1 mean={np.nanmean(r_factor):.1f} MJ.mm.ha-1.h-1.yr-1")

    # --- 5. Write native-grid R raster (EPSG:4326, 0.05 deg) ---
    profile = {
        "driver": "GTiff", "height": h, "width": w, "count": 1,
        "dtype": "float32", "crs": crs, "transform": transform,
        "nodata": NODATA, "compress": "deflate", "tiled": True,
    }
    out_arr = np.where(np.isfinite(r_factor), r_factor, NODATA).astype("float32")
    with rasterio.open(OUT_RASTER, "w", **profile) as ds:
        ds.write(out_arr, 1)
    print(f"wrote {OUT_RASTER}")

    # --- 6. Zonal summaries ---
    zonal_p_annual = zonal_stats(p_annual, v1_mask.astype(bool))
    zonal_mfi = zonal_stats(mfi, v1_mask.astype(bool))
    zonal_r = zonal_stats(r_factor, v1_mask.astype(bool))
    monthly_zonal = {
        f"{m:02d}": {
            "calendar_month": m,
            "n_years": monthly_counts.get(m, 0),
            **zonal_stats(p_monthly[m], v1_mask.astype(bool)),
        }
        for m in RAINCY_MONTHS if m in p_monthly
    }

    diagnostics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/derive_v1_chirps_rfactor.py",
        "source": "CHIRPS v3 Africa TIFs (annual 1981-2024; monthly rainy-season Nov-Mar), local download",
        "source_paths": {
            "annual": str(ANNUAL_DIR.relative_to(ROOT)),
            "monthly": str(MONTHLY_DIR.relative_to(ROOT)),
            "boundary": str(V1_GPKG.relative_to(ROOT)),
        },
        "grid": {
            "crs": str(crs),
            "resolution_deg": 0.05,
            "window_width_px": w,
            "window_height_px": h,
            "resampled_to_30m": False,
            "note": "R-factor is on the native CHIRPS 0.05 deg grid only. No 30 m raster produced.",
        },
        "climatologies": {
            "annual_year_range": list(ANNUAL_YEAR_RANGE),
            "annual_n_years": n_annual,
            "monthly_year_range": list(MONTHLY_YEAR_RANGE),
        },
        "months": {
            "rainy_season_months_present": RAINCY_MONTHS,
            "missing_calendar_months": [4, 5, 6, 7, 8, 9, 10],
            "monthly_file_counts_by_calendar_month": {f"{k:02d}": v for k, v in sorted(expected_cal_counts.items())},
        },
        "formula": {
            "mfi": "Arnoldus (1980) Modified Fournier Index: MFI = sum_i(Pi^2) / P_annual",
            "r_factor": "Renard & Freimund (1994): R = 0.0483*MFI^1.61 if MFI<80 else 587.8 - 1.219*MFI + 0.004105*MFI^2",
            "r_units": "MJ.mm.ha-1.h-1.yr-1",
        },
        "p_annual_v1_zonal_mm_per_yr": zonal_p_annual,
        "p_monthly_v1_zonal_mm_per_month": monthly_zonal,
        "mfi_v1_zonal": zonal_mfi,
        "r_factor_v1_zonal_MJ_mm_ha_h_yr": zonal_r,
        "limitations": [
            "Only Nov-Mar (rainy season) monthly means are available; Apr-Oct are missing.",
            "MFI numerator is summed over 5 months only -> MFI (and thus R) is a conservative underestimate of the full 12-month value.",
            "P_annual in the denominator is the full 12-month annual total from annual TIFs (correct).",
            "Output is on the ~5 km CHIRPS grid; it is NOT a 30 m raster and must not be used as pixel-level 30 m evidence.",
        ],
    }
    OUT_DIAG.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(f"wrote {OUT_DIAG}")

    # --- 7. Processing note (concise, public-safe phrasing) ---
    note = f"""# V1 R-factor (Modified Fournier / Renard-Freimund) processing note

Generated: {diagnostics["generated_at"]} (UTC) by `bin/derive_v1_chirps_rfactor.py`.

## Inputs
- CHIRPS v3 Africa annual TIFs (1981-2024, n={n_annual}):
  `data/raw/chirps_v3_zimbabwe_prototype/annual_africa_tifs/`.
- CHIRPS v3 Africa monthly TIFs (rainy season Nov-Mar only):
  `data/raw/chirps_v3_zimbabwe_prototype/monthly_africa_tifs/`.
- V1 working boundary: `outputs/v1_working_boundary/v1_working_boundary.gpkg`
  (layer `v1_working_boundary`, EPSG:4326).

## Data window
All reads are clipped to the V1 bounding box and aligned to the native CHIRPS
0.05 deg (~5 km) grid in EPSG:4326. Window size: {w} x {h} px. Only the V1
window is read from each file; full-Africa arrays are never stacked.

## Method
1. Long-term mean annual precipitation `P_annual` (mean over {y_lo}-{y_hi}).
2. Long-term mean monthly precipitation `Pi` for each available calendar month
   (Nov, Dec, Jan, Feb, Mar).
3. Modified Fournier Index (Arnoldus, 1980):
   `MFI = sum_i(Pi^2) / P_annual`  (summed over available months).
4. R-factor (Renard & Freimund, 1994), in MJ.mm.ha-1.h-1.yr-1:
   - if `MFI < 80`:  `R = 0.0483 * MFI^1.61`
   - if `MFI >= 80`: `R = 587.8 - 1.219*MFI + 0.004105*MFI^2`

## Outputs
- `r_factor_modified_fournier_0p05deg.tif` — R-factor on the native CHIRPS
  0.05 deg grid (V1 window, EPSG:4326, float32, NoData -9999).
- `r_factor_diagnostics.json` — climatologies, monthly means, MFI and R V1
  zonal summaries, and method notes.

## V1 zonal summary (R-factor)
- mean = {zonal_r.get("mean"):.1f}
- std  = {zonal_r.get("std"):.1f}
- min  = {zonal_r.get("min"):.1f} | p05 = {zonal_r.get("p05"):.1f} |
  p50 = {zonal_r.get("p50"):.1f} | p95 = {zonal_r.get("p95"):.1f} |
  max = {zonal_r.get("max"):.1f}
  (units: MJ.mm.ha-1.h-1.yr-1, valid cells = {zonal_r.get("valid_cells")})

## Limitations
- Only Nov-Mar monthly means are available; Apr-Oct are missing. The MFI
  numerator is therefore summed over 5 months, so MFI (and R) is a
  **conservative underestimate** of the full 12-month value. In this semi-arid
  region the dry-season months contribute little to erosivity, so the bias is
  small. `P_annual` in the denominator is the full annual total (correct).
- **This output is NOT a 30 m raster.** It is on the ~5 km CHIRPS grid. It must
  not be resampled to the V1 30 m terrain grid or treated as pixel-level 30 m
  evidence (per the V1 terrain reference grid rule). Use it as a zonal scalar
  or at its native resolution.
"""
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"wrote {OUT_NOTE}")

    print("\n=== V1 R-factor summary ===")
    print(f"  P_annual mean : {zonal_p_annual.get('mean'):.1f} mm/yr")
    print(f"  MFI (5-month) : mean={zonal_mfi.get('mean'):.2f}")
    print(f"  R-factor      : mean={zonal_r.get('mean'):.1f} "
          f"[{zonal_r.get('min'):.1f} .. {zonal_r.get('max'):.1f}] MJ.mm.ha-1.h-1.yr-1")


if __name__ == "__main__":
    main()
