#!/usr/bin/env python3
"""Exploratory R-factor method comparison for the V1 catchment (semi-arid Zimbabwe).

Local TOOLING script. After the integrity audit found that the V1 R-factor applied the wrong
Renard-Freimund coefficients to MFI with an invented break, this script runs an EXPLORATORY
comparison of four literature-based R-factor methods on the same V1 CHIRPS inputs, and compares
them to MEASURED Zimbabwe R-factor values from the literature. The goal is to provide concrete
evidence for the mentor decision on which R method suits semi-arid Zimbabwe, rather than leaving
it as an abstract choice.

All four methods have verified literature sources (no fabricated coefficients):

  Method A - Corrected Arnoldus (Nakil & Khire 2023, Catena systematic review):
      R = 17.02 * 10^(1.50*log10(MFI) - 0.8188)   [MJ mm ha-1 h-1 yr-1]
      This is the Arnoldus form WITH the 17.02 imperial->metric unit conversion that the review
      shows is widely omitted. Equivalent prefactor 2.583 * MFI^1.50.

  Method B - Renard & Freimund (1994) F-based form, applied CORRECTLY to F=MFI (Eq 13/14):
      R = 0.07397*F^1.847            if F < 55 mm   [Eq 13]
      R = 95.77 - 6.081*F + 0.4770*F^2  if F >= 55 mm [Eq 14]
      F = MFI = sum_i(Pi^2)/P_annual. The break is at F=55 (not the V1-invented 80).

  Method C - Renard & Freimund (1994) P-based form, applied CORRECTLY to P=mean annual precip
  (Eq 11/12):
      R = 0.04830*P^1.61             if P < 850 mm  [Eq 11]
      R = 587.8 - 1.219*P + 0.004105*P^2  if P >= 850 mm [Eq 12]

  Method D - OLD V1 method (WRONG, kept as a labelled reference baseline only):
      P-based coefficients 0.0483/1.61 and 587.8/1.219/0.004105 applied to MFI with an INVENTED
      break at MFI=80. DO NOT USE; shown only to expose the error magnitude.

Measured Zimbabwe anchor (from the literature, for sanity-checking the methods):
  - Epworth (Harare area), RUSLE: R ~ 329 (1984-2000), ~315 (2000-2018) MJ mm ha-1 h-1 yr-1
  - Southern Africa semi-arid lowlands: R ~ 150-400
  So a defensible R for V1 is expected to be in the low hundreds, NOT thousands.

For each method the script also computes an indicative USLE A = a_structure * R_zonal, using the
verified-clean a_structure = K*LS*C*P raster (R-invariant), so the A magnitudes are comparable
across methods on the SAME spatial structure.

CRITICAL GRID RULE: R is produced on the native CHIRPS 0.05 deg grid only. The A estimate uses
a_structure at 30 m multiplied by the R ZONAL SCALAR (no R resampling to 30 m). This is a
zonal-scalar A, consistent with the V1 USLE convention and the V1 terrain reference grid rule.

Usage (from workspace root):
    .venv/bin/python bin/explore_rfactor_methods.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
import rasterio.features
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
A_STRUCTURE = ROOT / "outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif"

# V1 bounding box (EPSG:4326), identical to the V1/V2 R-factor scripts.
V1_LON_MIN, V1_LAT_MIN, V1_LON_MAX, V1_LAT_MAX = 28.514, -21.008, 29.398, -19.984

OUT_DIR = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration"
OUT_RASTER_DIR = OUT_DIR / "rasters"

RAINY_MONTHS = [11, 12, 1, 2, 3]
ANNUAL_YEAR_RANGE = (1981, 2024)
NODATA = -9999.0
ANNUAL_RE = re.compile(r"chirps-v3\.0\.(\d{4})\.tif$")
MONTHLY_RE = re.compile(r"chirps-v3\.0\.(\d{4})\.(\d{2})\.tif$")

# Measured Zimbabwe R-factor anchor (literature), for sanity-checking each method.
ZIMBABWE_MEASURED_R = {
    "epworth_harare_1984_2000": 329.0,
    "epworth_harare_2000_2018": 315.0,
    "southern_africa_semi_arid_lowlands_range": [150.0, 400.0],
    "sources": [
        "Epworth (Harare), Zimbabwe - RUSLE, MDPI Sustainability 12(20):8531",
        "Southern Africa semi-arid lowlands - Lesotho RUSLE assessments",
    ],
}


def list_files(directory: Path, pattern_re):
    out = []
    for p in sorted(directory.glob("chirps-v3.0.*tif")):
        m = pattern_re.match(p.name)
        if m:
            out.append((m.groups(), p))
    return out


def compute_v1_window():
    ref = ANNUAL_DIR / "chirps-v3.0.1981.tif"
    if not ref.exists():
        ref = list_files(ANNUAL_DIR, ANNUAL_RE)[0][1]
    with rasterio.open(ref) as ds:
        win_f = from_bounds(V1_LON_MIN, V1_LAT_MIN, V1_LON_MAX, V1_LAT_MAX, ds.transform)
        win = Window(
            col_off=int(np.floor(win_f.col_off)),
            row_off=int(np.floor(win_f.row_off)),
            width=int(np.ceil(win_f.width)),
            height=int(np.ceil(win_f.height)),
        )
        return win, ds.window_transform(win), ds.crs


def read_window(path: Path, win: Window) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(1, window=win).astype("float64")
        nodata = ds.nodata
    if nodata is not None:
        arr[arr == nodata] = np.nan
    arr[~np.isfinite(arr)] = np.nan
    arr[arr < 0] = np.nan
    return arr.astype("float32")


def long_term_mean(files: list[Path], win: Window) -> tuple[np.ndarray, int]:
    """Per-cell long-term mean using a per-cell valid count (avoids bias from sporadic NaN)."""
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
        return (acc / valid_count).astype("float32"), len(files)


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


# --- The four R-factor methods ---

def r_method_A_corrected_arnoldus(mfi: np.ndarray) -> np.ndarray:
    """Nakil & Khire (2023) corrected Arnoldus: R = 17.02*10^(1.50*log10(MFI)-0.8188)."""
    mfi_safe = np.where(mfi <= 0, np.nan, mfi)
    return 17.02 * np.power(10.0, 1.50 * np.log10(mfi_safe) - 0.8188)


def r_method_B_rf_f_correct(mfi: np.ndarray) -> np.ndarray:
    """Renard & Freimund (1994) F-based form (Eq 13/14), F=MFI, break at 55 mm."""
    mfi_safe = np.where(mfi <= 0, np.nan, mfi)
    low = 0.07397 * np.power(mfi_safe, 1.847)
    high = 95.77 - 6.081 * mfi_safe + 0.4770 * mfi_safe ** 2
    return np.where(mfi_safe < 55.0, low, high)


def r_method_C_rf_p_correct(p_annual: np.ndarray) -> np.ndarray:
    """Renard & Freimund (1994) P-based form (Eq 11/12), P=mean annual precip, break at 850 mm."""
    p_safe = np.where(p_annual <= 0, np.nan, p_annual)
    low = 0.04830 * np.power(p_safe, 1.610)
    high = 587.8 - 1.219 * p_safe + 0.004105 * p_safe ** 2
    return np.where(p_safe < 850.0, low, high)


def r_method_D_old_wrong(mfi: np.ndarray) -> np.ndarray:
    """OLD V1 method (WRONG): P-based coeffs on MFI, invented break at 80. Reference baseline only."""
    mfi_safe = np.where(mfi <= 0, np.nan, mfi)
    low = 0.0483 * np.power(mfi_safe, 1.61)
    high = 587.8 - 1.219 * mfi_safe + 0.004105 * mfi_safe ** 2
    return np.where(mfi_safe < 80.0, low, high)


METHODS = [
    ("method_A_corrected_arnoldus", "Corrected Arnoldus (Nakil & Khire 2023)", r_method_A_corrected_arnoldus, "mfi"),
    ("method_B_rf_f_correct", "Renard-Freimund F-based correct (Eq 13/14)", r_method_B_rf_f_correct, "mfi"),
    ("method_C_rf_p_correct", "Renard-Freimund P-based correct (Eq 11/12)", r_method_C_rf_p_correct, "p_annual"),
    ("method_D_old_wrong", "OLD V1 method (WRONG, reference only)", r_method_D_old_wrong, "mfi"),
]


def main() -> None:
    OUT_RASTER_DIR.mkdir(parents=True, exist_ok=True)
    win, transform, crs = compute_v1_window()
    h, w = win.height, win.width
    print(f"V1 window: {w} x {h} px @ 0.05 deg")

    boundary = gpd.read_file(V1_GPKG, layer=V1_BOUNDARY_LAYER).to_crs(crs)
    shapes = [(geom, 1) for geom in boundary.geometry if geom is not None and not geom.is_empty]
    v1_mask = rasterio.features.rasterize(
        shapes, out_shape=(h, w), transform=transform, fill=0, dtype="uint8", all_touched=False
    )
    v1_bool = v1_mask.astype(bool)

    # --- Climatology inputs ---
    annual_files = [p for (groups, p) in list_files(ANNUAL_DIR, ANNUAL_RE)
                    if ANNUAL_YEAR_RANGE[0] <= int(groups[0]) <= ANNUAL_YEAR_RANGE[1]]
    p_annual, n_annual = long_term_mean(annual_files, win)
    p_annual = np.where(v1_bool, p_annual, np.nan)

    monthly_by_cal = {m: [] for m in RAINY_MONTHS}
    for groups, p in list_files(MONTHLY_DIR, MONTHLY_RE):
        y, m = int(groups[0]), int(groups[1])
        if ANNUAL_YEAR_RANGE[0] <= y <= ANNUAL_YEAR_RANGE[1] and m in monthly_by_cal:
            monthly_by_cal[m].append(p)

    numerator = np.zeros_like(p_annual, dtype="float64")
    for m in RAINY_MONTHS:
        files = monthly_by_cal[m]
        if not files:
            continue
        arr, _ = long_term_mean(files, win)
        arr = np.where(v1_bool, arr, np.nan)
        numerator = np.where(np.isfinite(arr), numerator + arr.astype("float64") ** 2, numerator)
    with np.errstate(divide="ignore", invalid="ignore"):
        mfi = numerator / p_annual
    mfi = np.where(v1_bool, mfi, np.nan)
    print(f"P_annual V1 mean = {np.nanmean(p_annual):.1f} mm; MFI V1 mean = {np.nanmean(mfi):.2f}")

    # --- a_structure stats for the A estimate ---
    with rasterio.open(A_STRUCTURE) as ds:
        a_struct = ds.read(1).astype("float64")
        if ds.nodata is not None:
            a_struct[a_struct == ds.nodata] = np.nan
    struct_valid = a_struct[np.isfinite(a_struct)]
    struct_mean = float(np.mean(struct_valid)) if struct_valid.size else float("nan")

    profile = {
        "driver": "GTiff", "height": h, "width": w, "count": 1,
        "dtype": "float32", "crs": crs, "transform": transform,
        "nodata": NODATA, "compress": "deflate", "tiled": True,
    }

    results = {}
    for mid, display, fn, var in METHODS:
        inp = mfi if var == "mfi" else p_annual
        r = fn(inp).astype("float64")
        r = np.where(v1_bool & np.isfinite(inp), r, np.nan)
        out_arr = np.where(np.isfinite(r), r, NODATA).astype("float32")
        out_path = OUT_RASTER_DIR / f"{mid}_0p05deg.tif"
        with rasterio.open(out_path, "w", **profile) as ds:
            ds.write(out_arr, 1)
            ds.update_tags(1, IFPM_NOTE=f"Exploratory R method: {display}")
        z = zonal_stats(r, v1_bool)
        r_zonal_mean = z.get("mean")
        a_mean_est = struct_mean * r_zonal_mean if r_zonal_mean else None
        results[mid] = {
            "display": display,
            "input_variable": var,
            "raster": str(out_path.relative_to(ROOT)),
            "r_zonal_MJ_mm_ha_h_yr": z,
            "a_structure_mean_t_ha_yr_per_unit_R": round(struct_mean, 6),
            "a_estimate_mean_t_ha_yr": round(a_mean_est, 4) if a_mean_est is not None else None,
        }
        flag = ""
        if r_zonal_mean:
            if r_zonal_mean > 1000:
                flag = "  <-- far above Zimbabwe measured (~300-400); likely non-transferable"
            elif 150 <= r_zonal_mean <= 400:
                flag = "  <-- within semi-arid measured range"
            else:
                flag = "  <-- outside typical range"
        print(f"  {mid:30s} R mean = {r_zonal_mean:8.1f}{flag}")

    diagnostics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/explore_rfactor_methods.py",
        "purpose": (
            "Exploratory comparison of four literature-based R-factor methods on V1 CHIRPS inputs, "
            "to support the mentor decision on the correct R method for semi-arid Zimbabwe after "
            "the V1 formula error (see formula_integrity_audit_2026-06-19.md)."
        ),
        "inputs": {
            "mfi_v1_zonal": zonal_stats(mfi, v1_bool),
            "p_annual_v1_zonal_mm": zonal_stats(p_annual, v1_bool),
            "rainy_months_used": RAINY_MONTHS,
            "annual_year_range": list(ANNUAL_YEAR_RANGE),
            "n_annual_files": n_annual,
        },
        "zimbabwe_measured_r_anchor": ZIMBABWE_MEASURED_R,
        "methods": results,
        "note_on_a_estimate": (
            "A estimate = a_structure_mean * R_zonal_mean. a_structure = K*LS*C*P is R-invariant "
            "and verified clean; only R varies across methods. This is a zonal-scalar A (R not "
            "resampled to 30 m), consistent with the V1 convention and the terrain grid rule."
        ),
        "status": "EXPLORATORY comparison to inform the mentor R-method decision; not an interpretable validated result.",
    }
    out_json = OUT_DIR / "rfactor_method_exploration_diagnostics.json"
    out_json.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(f"\nwrote {out_json}")
    print("\n=== Zimbabwe measured R anchor ===")
    print(f"  Epworth (Harare): ~329 (1984-2000), ~315 (2000-2018)")
    print(f"  Semi-arid lowlands range: 150-400 MJ mm ha-1 h-1 yr-1")


if __name__ == "__main__":
    main()
