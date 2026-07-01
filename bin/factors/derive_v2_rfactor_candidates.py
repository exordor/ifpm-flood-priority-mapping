#!/usr/bin/env python3
"""Derive V2 candidate USLE/RUSLE R-factors from the same CHIRPS MFI used by V1.

Local TOOLING script. Responds to the 2026-06-16 mentor decision (IFPM-074): keep the V1 bimodal
R-factor as a diagnostic baseline and compute smoother R-factor candidates for V2, so the soil-loss
hotspot pattern can be re-tested. The V1 bimodality comes from the Renard & Freimund (1994)
piecewise R(MFI) at the MFI=80 break; the smoother candidates are single continuous formulas with
no break.

All candidates share the identical MFI input (Arnoldus 1980: MFI = sum_i(Pi^2) / P_annual) computed
from the same CHIRPS long-term climatology as V1. Only the MFI -> R conversion differs:

    rf_v1_bimodal      V1 baseline: Renard & Freimund (1994) piecewise
                       R = 0.0483*MFI^1.61               if MFI < 80
                       R = 587.8 - 1.219*MFI + 0.004105*MFI^2  if MFI >= 80
    rf_arnoldus        Arnoldus (1980) single power law: R = 0.2647 * MFI^1.5
                       NOTE: 0.2647/1.5 are regionally-fitted coefficients reported in some
                       applications; Arnoldus (1980) only provided the R = a*Fm^b framework, not a
                       universal constant. Treat as a candidate smoothing function, not an
                       authoritative formula.
    rf_rf_low_branch   Renard & Freimund low branch only: R = 0.0483 * MFI^1.61  (no MFI=80 break)

VARIABLE-CONFUSION RISK (IMPORTANT): Renard & Freimund (1994) published BOTH a P-based form
(R = 0.0483*P^1.61 with P = mean annual precipitation, break at P=850 mm) AND an F-based form
(F = Modified Fournier Index, with DIFFERENT coefficients). The coefficients 0.0483/1.61/587.8/
1.219/0.004105 applied to MFI here are inherited from V1; in the original paper these coefficient
VALUES belong to the P-based form. This V2 package preserves the V1 convention for comparability
and flags it as an open methodological risk for the mentor to resolve. It does NOT silently fix it,
because changing the convention would break V1-vs-V2 comparability.

(An earlier draft also included a "Lo et al. (1985)" candidate R = 0.0737*MFI^1.81. That candidate
was REMOVED after a literature check showed Lo et al. 1985 used mean annual precipitation, not MFI,
and the 0.0737/1.81 coefficients had no traceable source. Keeping it would have introduced an
unverified formula into the pipeline.)

CRITICAL GRID RULE: every R-factor stays on the native CHIRPS 0.05 deg grid (V1 window) and is
also recorded as a V1 zonal scalar. No raster is resampled to the V1 30 m terrain grid (per
context/docs/data-management/v1_terrain_reference_grid_rule.md).

Bimodality diagnostic: for each candidate the script counts cells with R<100, R in [100,400], and
R>400. The V1 baseline is expected to be strongly bimodal (cells clustered at the extremes, ~0 in
the middle); the smoother candidates must fill the middle band, confirming the break is resolved.

Usage (from workspace root):
    .venv/bin/python bin/factors/derive_v2_rfactor_candidates.py
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

ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "chirps_v3_zimbabwe_prototype"
ANNUAL_DIR = ROOT / f"data/raw/{DATASET_ID}/annual_africa_tifs"
MONTHLY_DIR = ROOT / f"data/raw/{DATASET_ID}/monthly_africa_tifs"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
V1_BOUNDARY_LAYER = "v1_working_boundary"

# V1 bounding box in EPSG:4326 (CHIRPS native CRS); identical to derive_v1_chirps_rfactor.py.
V1_LON_MIN, V1_LAT_MIN, V1_LON_MAX, V1_LAT_MAX = 28.514, -21.008, 29.398, -19.984

OUT_DIR = ROOT / f"outputs/{DATASET_ID}/r_factor_v2"
OUT_RASTER_DIR = OUT_DIR / "rasters"
OUT_DIAG = OUT_DIR / "v2_rfactor_diagnostics.json"
OUT_NOTE = OUT_DIR / "v2_rfactor_processing_note.md"

# Rainy-season calendar months present in the monthly TIF inventory (Nov, Dec, Jan, Feb, Mar).
RAINY_MONTHS = [11, 12, 1, 2, 3]
ANNUAL_YEAR_RANGE = (1981, 2024)
MONTHLY_YEAR_RANGE = (1981, 2024)

NODATA = -9999.0
ANNUAL_RE = re.compile(r"chirps-v3\.0\.(\d{4})\.tif$")
MONTHLY_RE = re.compile(r"chirps-v3\.0\.(\d{4})\.(\d{2})\.tif$")

# Candidate R-factor formulas, keyed by a stable id used in output filenames.
# Each entry: (display_name, citation, callable(MFI array -> R array in MJ.mm.ha-1.h-1.yr-1)).
R_CANDIDATES = {
    "rf_v1_bimodal": (
        "V1 bimodal (Renard & Freimund 1994 piecewise)",
        "Renard & Freimund (1994)",
        lambda m: np.where(m < 80.0, 0.0483 * np.power(m, 1.61),
                           587.8 - 1.219 * m + 0.004105 * np.power(m, 2.0)),
    ),
    "rf_arnoldus": (
        "Arnoldus (1980) single power law (regionally-fitted coefficients)",
        "Arnoldus (1980); coefficients non-universal",
        lambda m: 0.2647 * np.power(m, 1.5),
    ),
    # NOTE: a previous "rf_lo" (Lo et al. 1985, R = 0.0737*MFI^1.81) candidate was removed after a
    # literature check: Lo et al. 1985 used mean annual precipitation, not MFI, and the
    # 0.0737/1.81 coefficients had no traceable source. Do not reintroduce without a verified
    # citation and the correct predictor variable.
    "rf_rf_low_branch": (
        "Renard & Freimund low branch only (no MFI=80 break)",
        "Renard & Freimund (1994), low branch extended",
        lambda m: 0.0483 * np.power(m, 1.61),
    ),
}


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

    Returns (Window, transform, crs, height, width). Identical grid to V1 so candidates are
    directly comparable cell-for-cell.
    """
    ref = ANNUAL_DIR / "chirps-v3.0.1981.tif"
    if not ref.exists():
        ref = list_annual_files()[0][1]
    with rasterio.open(ref) as ds:
        win_f = from_bounds(V1_LON_MIN, V1_LAT_MIN, V1_LON_MAX, V1_LAT_MAX, ds.transform)
        col_off = int(np.floor(win_f.col_off))
        row_off = int(np.floor(win_f.row_off))
        width = int(np.ceil(win_f.width))
        height = int(np.ceil(win_f.height))
        win = Window(col_off=col_off, row_off=row_off, width=width, height=height)
        transform = ds.window_transform(win)
        crs = ds.crs
    return win, transform, crs, height, width


def read_window(path: Path, win: Window) -> np.ndarray:
    """Read a CHIRPS window, masking the band's native NoData explicitly.

    Reads `ds.nodata` rather than relying on a `(< 0)` heuristic, so positive sentinel nodata
    (e.g. 1e20 in some NetCDF-derived TIFs) cannot leak into the climatology. After masking the
    declared NoData, any remaining non-finite or negative values are also masked (defensive).
    """
    with rasterio.open(path) as ds:
        arr = ds.read(1, window=win).astype("float64")
        nodata = ds.nodata
    if nodata is not None:
        arr[arr == nodata] = np.nan
    arr[~np.isfinite(arr)] = np.nan
    arr[arr < 0] = np.nan
    return arr.astype("float32")


def long_term_mean(files: list[Path], win: Window) -> tuple[np.ndarray, int]:
    """Per-cell long-term mean using a per-cell valid count as the denominator.

    Each cell is divided by its own count of finite contributions, NOT the total file count, so
    cells that are NoData in some years (e.g. over water/coast) are not biased low. Returns
    (mean, n_files) where n_files is the number of files consumed (for provenance only).
    """
    if not files:
        raise ValueError("no files supplied to long_term_mean")
    acc = None
    valid_count = None
    for p in files:
        arr = read_window(p, win)
        valid = np.isfinite(arr)
        if acc is None:
            acc = np.zeros(arr.shape, dtype="float64")
            valid_count = np.zeros(arr.shape, dtype="float32")
        acc = np.where(valid, acc + arr.astype("float64"), acc)
        valid_count = valid_count + valid.astype("float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = acc / valid_count
    return mean.astype("float32"), len(files)


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
        "p25": float(np.percentile(vals, 25)),
        "p50": float(np.percentile(vals, 50)),
        "p75": float(np.percentile(vals, 75)),
        "p95": float(np.percentile(vals, 95)),
        "max": float(np.max(vals)),
    }


def bimodality_breakdown(arr: np.ndarray, mask: np.ndarray) -> dict:
    """Count cells in three R bands that expose the V1 bimodal split.

    V1 baseline clusters near R~50 (low mode) and R~510 (high mode) with ~0 cells in between.
    A smoother candidate is confirmed unimodal/continuous if it fills the middle [100,400] band.
    """
    vals = arr[mask & np.isfinite(arr)]
    if vals.size == 0:
        return {"cells_lt_100": 0, "cells_100_400": 0, "cells_gt_400": 0, "total": 0}
    return {
        "cells_lt_100": int(np.sum(vals < 100.0)),
        "cells_100_400": int(np.sum((vals >= 100.0) & (vals <= 400.0))),
        "cells_gt_400": int(np.sum(vals > 400.0)),
        "total": int(vals.size),
    }


def continuity_at_break(mfi: np.ndarray, mask: np.ndarray, r_fn) -> dict:
    """Measure the R jump magnitude across the MFI=80 break.

    Evaluates the formula just below and just above MFI=80 (79.9 and 80.1) to quantify the
    discontinuity. The V1 piecewise formula has a large jump; the smoother candidates have ~0.
    """
    eps = 0.1
    below = float(r_fn(np.array([80.0 - eps]))[0])
    above = float(r_fn(np.array([80.0 + eps]))[0])
    return {
        "r_just_below_80": round(below, 3),
        "r_just_above_80": round(above, 3),
        "abs_jump_at_80": round(abs(above - below), 3),
    }


def main() -> None:
    raise SystemExit(
        "DEPRECATED: do not regenerate V2 R-factor candidates. The V1 bimodality this was built "
        "to resolve was an artifact of the wrong break point, so the premise does not hold. "
        "See outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md "
        "and context/docs/project-management/rfactor_investigation_consolidated.md."
    )

    OUT_RASTER_DIR.mkdir(parents=True, exist_ok=True)

    win, transform, crs, h, w = compute_v1_window()
    print(f"V1 window: {w} x {h} px @ 0.05 deg (EPSG:4326), transform={transform}")

    boundary = gpd.read_file(V1_GPKG, layer=V1_BOUNDARY_LAYER).to_crs(crs)
    shapes = [(geom, 1) for geom in boundary.geometry if geom is not None and not geom.is_empty]
    v1_mask = rasterize(
        shapes, out_shape=(h, w), transform=transform, fill=0, dtype="uint8", all_touched=False
    )
    v1_bool = v1_mask.astype(bool)
    print(
        f"V1 boundary rasterized: {int(v1_mask.sum())} CHIRPS cells inside V1 "
        f"({100 * v1_mask.sum() / (w * h):.1f}% of window)"
    )

    # --- 1. Long-term mean annual precipitation (shared with V1) ---
    annual_files_all = list_annual_files()
    y_lo, y_hi = ANNUAL_YEAR_RANGE
    annual_files = [p for (y, p) in annual_files_all if y_lo <= y <= y_hi]
    if not annual_files:
        raise SystemExit(f"no annual CHIRPS files found in {ANNUAL_YEAR_RANGE}")
    p_annual, n_annual = long_term_mean(annual_files, win)
    p_annual = np.where(v1_bool, p_annual, np.nan)
    print(f"P_annual ({y_lo}-{y_hi}, n={n_annual}): V1 mean={np.nanmean(p_annual):.1f} mm/yr")

    # --- 2. Long-term mean monthly precipitation per rainy-season month ---
    monthly_files_all = list_monthly_files()
    my_lo, my_hi = MONTHLY_YEAR_RANGE
    monthly_files_by_cal = {m: [] for m in RAINY_MONTHS}
    for (y, m, p) in monthly_files_all:
        if my_lo <= y <= my_hi and m in monthly_files_by_cal:
            monthly_files_by_cal[m].append(p)

    p_monthly: dict[int, np.ndarray] = {}
    for m in RAINY_MONTHS:
        files = monthly_files_by_cal[m]
        if not files:
            continue
        arr, _n = long_term_mean(files, win)
        arr = np.where(v1_bool, arr, np.nan)
        p_monthly[m] = arr

    # --- 3. Modified Fournier Index (Arnoldus 1980) over available months (identical to V1) ---
    numerator = np.zeros_like(p_annual, dtype="float64")
    for _m, arr in p_monthly.items():
        numerator = np.where(np.isfinite(arr), numerator + arr.astype("float64") ** 2, numerator)
    with np.errstate(divide="ignore", invalid="ignore"):
        mfi = numerator / p_annual
    mfi = np.where(v1_bool, mfi, np.nan)
    print(f"MFI (5-month, shared with V1): V1 mean={np.nanmean(mfi):.2f}")

    # --- 4. Candidate R-factors (vectorised, per-cell) ---
    profile = {
        "driver": "GTiff", "height": h, "width": w, "count": 1,
        "dtype": "float32", "crs": crs, "transform": transform,
        "nodata": NODATA, "compress": "deflate", "tiled": True,
    }

    candidate_diagnostics: dict[str, dict] = {}
    for cid, (display, citation, r_fn) in R_CANDIDATES.items():
        # Guard non-positive MFI before power laws.
        mfi_safe = np.where(mfi <= 0, np.nan, mfi)
        r = r_fn(mfi_safe).astype("float64")
        r = np.where(v1_bool & np.isfinite(mfi_safe), r, np.nan)
        out_arr = np.where(np.isfinite(r), r, NODATA).astype("float32")
        out_path = OUT_RASTER_DIR / f"{cid}_0p05deg.tif"
        with rasterio.open(out_path, "w", **profile) as ds:
            ds.write(out_arr, 1)
        z = zonal_stats(r, v1_bool)
        bim = bimodality_breakdown(r, v1_bool)
        cont = continuity_at_break(mfi, v1_bool, r_fn)
        candidate_diagnostics[cid] = {
            "display_name": display,
            "citation": citation,
            "raster": str(out_path.relative_to(ROOT)),
            "zonal_summary_MJ_mm_ha_h_yr": z,
            "bimodality_bands": bim,
            "continuity_at_mfi_80": cont,
        }
        mean_str = f"{z['mean']:.1f}" if z.get("valid_cells", 0) > 0 else "NaN(all-invalid)"
        print(
            f"  {cid:18s} R mean={mean_str}  "
            f"bands(<100/100-400/>400)={bim['cells_lt_100']}/{bim['cells_100_400']}/{bim['cells_gt_400']}  "
            f"jump@80={cont['abs_jump_at_80']}"
        )

    diagnostics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/factors/derive_v2_rfactor_candidates.py",
        "purpose": (
            "V2 smoother R-factor candidates responding to the 2026-06-16 mentor decision "
            "(IFPM-074): keep V1 bimodal R as baseline, test smoother R, re-test hotspot survival."
        ),
        "source": (
            "CHIRPS v3 Africa TIFs (annual 1981-2024; monthly rainy-season Nov-Mar), local download. "
            "Identical MFI to V1 (derive_v1_chirps_rfactor.py)."
        ),
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
            "note": "All candidates on the native CHIRPS 0.05 deg grid. No 30 m raster produced.",
        },
        "climatologies": {
            "annual_year_range": list(ANNUAL_YEAR_RANGE),
            "annual_n_years": n_annual,
            "monthly_year_range": list(MONTHLY_YEAR_RANGE),
            "rainy_season_months_present": RAINY_MONTHS,
            "missing_calendar_months": [4, 5, 6, 7, 8, 9, 10],
        },
        "formula": {
            "mfi": "Arnoldus (1980) Modified Fournier Index: MFI = sum_i(Pi^2) / P_annual (5 months)",
            "candidates": {
                cid: {
                    "display_name": R_CANDIDATES[cid][0],
                    "citation": R_CANDIDATES[cid][1],
                }
                for cid in R_CANDIDATES
            },
            "r_units": "MJ.mm.ha-1.h-1.yr-1",
        },
        "p_annual_v1_zonal_mm_per_yr": zonal_stats(p_annual, v1_bool),
        "mfi_v1_zonal": zonal_stats(mfi, v1_bool),
        "candidates": candidate_diagnostics,
        "limitations": [
            "Only Nov-Mar monthly means are available; Apr-Oct are missing. MFI is summed over 5 "
            "months, a conservative underestimate of the full 12-month value (identical to V1).",
            "P_annual in the denominator is the full 12-month annual total (correct).",
            "All outputs are on the ~5 km CHIRPS grid; NOT 30 m rasters and must not be used as "
            "pixel-level 30 m evidence (per the V1 terrain reference grid rule).",
            "DIAGNOSTIC data products, not interpretable validated erosivity values.",
        ],
        "status": "DIAGNOSTIC data product, not an interpretable validated R-factor.",
    }
    OUT_DIAG.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(f"wrote {OUT_DIAG}")

    # --- 5. Processing note ---
    note = f"""# V2 R-factor candidates (smoother formulas) processing note

Generated: {diagnostics["generated_at"]} (UTC) by `bin/factors/derive_v2_rfactor_candidates.py`.

## Purpose

Responds to the 2026-06-16 mentor decision (IFPM-074): keep the V1 bimodal R-factor as a
diagnostic baseline, switch V2 to a smoother R, and re-test whether the soil-loss hotspot pattern
survives. The V1 bimodality is an artifact of the Renard & Freimund (1994) piecewise R(MFI) at the
MFI=80 break; the smoother candidates are single continuous formulas with no break.

## Inputs (identical to V1)

- CHIRPS v3 Africa annual TIFs (1981-2024, n={n_annual}).
- CHIRPS v3 Africa monthly TIFs (rainy season Nov-Mar).
- V1 working boundary: `outputs/v1_working_boundary/v1_working_boundary.gpkg`.

## Method

1. MFI (Arnoldus 1980) computed identically to V1: `MFI = sum_i(Pi^2) / P_annual` over the 5
   available rainy-season months. V1 mean MFI = {diagnostics["mfi_v1_zonal"]["mean"]:.2f}.
2. Three candidate MFI -> R conversions applied cell-by-cell on the 0.05 deg grid:

| Candidate | Formula | Role |
|---|---|---|
| rf_v1_bimodal | Renard-Freimund 1994 piecewise | V1 baseline (MFI=80 break) |
| rf_arnoldus | 0.2647 * MFI^1.5 | V2 main candidate (regionally-fitted coeffs; Arnoldus gave only the R=a*Fm^b framework) |
| rf_rf_low_branch | 0.0483 * MFI^1.61 (full range) | minimal-change same-source |

A fourth candidate "Lo et al. (1985)" (R = 0.0737*MFI^1.81) was removed after a literature check:
Lo et al. 1985 used mean annual precipitation (not MFI), and the 0.0737/1.81 coefficients had no
traceable source. See the variable-confusion-risk note in the script docstring.

## Bimodality resolution check

For each candidate the diagnostics count cells in three R bands (R<100, 100-400, >400). The V1
baseline clusters at the extremes with ~0 cells in the middle. A smoother candidate is confirmed
when the middle band is populated and the MFI=80 jump is ~0.

## Outputs

- `rasters/<candidate_id>_0p05deg.tif` - R-factor on the native CHIRPS 0.05 deg grid.
- `v2_rfactor_diagnostics.json` - per-candidate zonal summaries, bimodality bands, continuity.

## Limitations

- Same 5-month MFI underestimate as V1 (Apr-Oct missing); conservative bias is small here.
- All outputs are on the ~5 km grid; NOT 30 m and must not be used as pixel-level 30 m evidence.
- DIAGNOSTIC data products, not interpretable validated erosivity values. Final R formula for V2
  remains a mentor methodological decision; this package only supplies candidates and evidence.
"""
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"wrote {OUT_NOTE}")

    print("\n=== V2 R-factor candidate summary ===")
    mfi_z = diagnostics['mfi_v1_zonal']
    print(f"  MFI (shared)  : mean={mfi_z.get('mean', float('nan')):.2f} "
          f"[{mfi_z.get('min', float('nan')):.1f} .. {mfi_z.get('max', float('nan')):.1f}]")
    for cid, d in candidate_diagnostics.items():
        z = d["zonal_summary_MJ_mm_ha_h_yr"]
        b = d["bimodality_bands"]
        mean_str = f"{z['mean']:7.1f}" if z.get("valid_cells", 0) > 0 else "  NaN  "
        print(f"  {cid:18s} mean={mean_str}  bands={b['cells_lt_100']}/{b['cells_100_400']}/{b['cells_gt_400']}  "
              f"jump@80={d['continuity_at_mfi_80']['abs_jump_at_80']}")


if __name__ == "__main__":
    main()
