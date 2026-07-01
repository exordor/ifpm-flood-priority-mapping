#!/usr/bin/env python3
"""Derive USLE/RUSLE LS-factor (slope length x steepness) for V1 from flow accumulation + slope.

Local TOOLING script. Uses the Moore & Nieber (1989) raster LS-factor based on specific
contributing area (As) and local slope angle:

    LS = (As / 22.13)^0.4 * (sin(theta) / 0.0896)^1.2

where As = specific contributing area (m, from whitebox D8 SCA), theta = slope angle (radians).
This is the most widely implemented raster LS (SAGA, GRASS, ArcGIS derivatives).

Inputs are on the V1 30 m grid (EPSG:32735). Outputs stay at 30 m.

Notes:
- The hillslope LS formula is not physically meaningful on main-channel cells (very high As),
  so an uncapped LS is reported for transparency and a channel-aware variant masks cells above
  the chosen channel-initiation threshold (t500 = 500 cells).
- A capped variant (LS capped at 50, a conservative RUSLE ceiling) is also written for use in
  the USLE A-factor combination.

Usage:
    .venv/bin/python bin/factors/derive_v1_ls_factor.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]

SLOPE_DEG = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_slope_degrees_utm35s_30m.tif"
SCA = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_derivatives/v1_flow_accumulation_sca.tif"
FLOW_ACCUM = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_derivatives/v1_flow_accumulation.tif"
CHANNEL_THRESHOLD_CELLS = 500  # t500 chosen in the hydrology step
LS_CAP = 50.0

OUTPUT_DIR = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def read_band(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype("float64")
        profile = ds.profile
        nodata = ds.nodata
    if nodata is not None:
        arr[arr == nodata] = np.nan
    return arr, profile


def main() -> None:
    slope_deg, profile = read_band(SLOPE_DEG)
    sca, _ = read_band(SCA)
    flow_accum, _ = read_band(FLOW_ACCUM)

    theta = np.radians(slope_deg)
    sin_theta = np.sin(theta)

    # Moore & Nieber (1989) raster LS-factor.
    # Guard against As <= 0 and division issues; nan where inputs are nan.
    as_term = np.where(sca > 0, np.power(np.maximum(sca, 0.0) / 22.13, 0.4), 0.0)
    sl_term = np.where(sin_theta > 0, np.power(np.maximum(sin_theta, 0.0) / 0.0896, 1.2), 0.0)
    ls = as_term * sl_term
    invalid = ~np.isfinite(slope_deg) | ~np.isfinite(sca)
    ls = np.where(invalid, np.nan, ls)

    # Channel-aware variant: set LS to nan on main-channel cells (As formula not meaningful there).
    channel = (flow_accum > CHANNEL_THRESHOLD_CELLS) & np.isfinite(flow_accum)
    ls_hillslope = np.where(channel, np.nan, ls)

    # Capped variant for USLE A-factor combination.
    ls_capped = np.where(np.isfinite(ls_hillslope), np.clip(ls_hillslope, 0.0, LS_CAP), np.nan)

    out_profile = profile.copy()
    out_profile.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)

    for name, arr in [("v1_ls_factor_uncapped_30m.tif", ls),
                      ("v1_ls_factor_hillslope_30m.tif", ls_hillslope),
                      ("v1_ls_factor_capped50_hillslope_30m.tif", ls_capped)]:
        out = np.where(np.isfinite(arr), arr, -9999.0).astype("float32")
        path = OUTPUT_DIR / name
        with rasterio.open(path, "w", **out_profile) as ds:
            ds.write(out, 1)
        print(f"wrote {path}")

    def stats(arr):
        v = arr[np.isfinite(arr)]
        return {
            "valid_cells": int(v.size),
            "mean": float(np.mean(v)) if v.size else None,
            "std": float(np.std(v)) if v.size else None,
            "min": float(np.min(v)) if v.size else None,
            "p50": float(np.percentile(v, 50)) if v.size else None,
            "p95": float(np.percentile(v, 95)) if v.size else None,
            "max": float(np.max(v)) if v.size else None,
        }

    diag = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/factors/derive_v1_ls_factor.py",
        "formula": "Moore & Nieber 1989: LS = (As/22.13)^0.4 * (sin(theta)/0.0896)^1.2",
        "inputs": {"slope_deg": str(SLOPE_DEG), "sca": str(SCA), "flow_accum": str(FLOW_ACCUM)},
        "channel_threshold_cells": CHANNEL_THRESHOLD_CELLS,
        "ls_cap": LS_CAP,
        "stats": {
            "uncapped": stats(ls),
            "hillslope_channel_masked": stats(ls_hillslope),
            "capped50_hillslope": stats(ls_capped),
        },
        "note": ("The hillslope LS formula is not physically meaningful on main-channel cells "
                 "(high specific contributing area). The hillslope variant masks cells above "
                 f"the channel threshold ({CHANNEL_THRESHOLD_CELLS} cells). The capped variant "
                 f"clips hillslope LS at {LS_CAP} for the USLE A-factor combination."),
    }
    (OUTPUT_DIR / "ls_factor_diagnostics.json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
    print(f"\ndiagnostics: {OUTPUT_DIR / 'ls_factor_diagnostics.json'}")
    for k, v in diag["stats"].items():
        if v["mean"] is not None:
            print(f"  {k}: mean={v['mean']:.3f} p50={v['p50']:.3f} p95={v['p95']:.3f} max={v['max']:.1f} valid={v['valid_cells']}")


if __name__ == "__main__":
    main()
