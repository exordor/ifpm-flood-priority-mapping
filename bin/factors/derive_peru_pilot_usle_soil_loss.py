#!/usr/bin/env python3
"""Derive PE1 USLE/RUSLE soil-loss structure and provisional sediment scenarios.

Mirrors `derive_v1_usle_soil_loss.py` but uses the verified-safe structure layer only
(K_SI x LS x C x P, R-invariant) and applies provisional R scalars. The old Zimbabwe
workflow's R-dependent absolute A values are deprecated; this PE1 script follows the
2026-06-19 audit's corrected approach: structure is trustworthy, R is a labelled scalar.

PE1 structure = K_SI_scalar x LS(hillslope, capped-50) x C(30m) x P(=1.0).
Provisional sediment scenarios = structure x R_mean for a LOW and HIGH R family.
The hotspot RANK is R-invariant; R only scales magnitude.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/srtm_1arcsec_peru_pilot/ls_factor/pe1_ls_factor_capped50_hillslope_30m.tif", ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_pe1_30m.tif"]
OUTPUTS = [ROOT / "outputs/srtm_1arcsec_peru_pilot/usle_soil_loss/a_structure_K_LS_C_30m.tif"]

LS = ROOT / "outputs/srtm_1arcsec_peru_pilot/ls_factor/pe1_ls_factor_capped50_hillslope_30m.tif"
C = ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_pe1_30m.tif"
PE1_REFERENCE_DEM = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
OUTPUT_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/usle_soil_loss"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# K_SI scalar: PE1 zonal mean K_US (0-5cm) x 0.1317 -> SI units. From k_factor_diagnostics.json.
K_US_MEAN_0_5CM = 0.1815
K_SI_MEAN = K_US_MEAN_0_5CM * 0.1317  # = 0.0239

# Provisional R scalars (LOW family default, HIGH family sensitivity).
# LOW: same provisional value used for Zimbabwe (Arnoldus 1980 LOW family, applied as a
# labelled provisional default until a PE1-specific CHIRPS/ERA5 R is derived). Peru PE1 is
# a drier Pacific-slope basin; the true R is likely lower, but the LOW-family provisional
# is a defensible conservative screening value, and the hotspot rank is R-invariant.
R_LOW_DEFAULT = 238.6
R_HIGH_SENSITIVITY = 408.0

P = 1.0  # support practice factor default assumption


def read_band(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype("float64")
        profile = ds.profile
        nodata = ds.nodata
    if nodata is not None:
        arr[arr == nodata] = np.nan
    arr[~np.isfinite(arr)] = np.nan
    return arr, profile


def main() -> None:
    ls, profile = read_band(LS)
    c, _ = read_band(C)

    with rasterio.open(PE1_REFERENCE_DEM) as ref:
        ref_crs = ref.crs
        ref_shape = (ref.height, ref.width)

    # Structure = K_SI x LS x C x P (everything except R). R-invariant spatial structure.
    structure = K_SI_MEAN * ls * c * P
    invalid = ~np.isfinite(ls) | ~np.isfinite(c)
    structure = np.where(invalid, np.nan, structure)

    a_low = structure * R_LOW_DEFAULT
    a_high = structure * R_HIGH_SENSITIVITY

    out_profile = profile.copy()
    out_profile.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)

    for name, arr in [
        ("a_structure_K_LS_C_30m.tif", structure),          # t/ha/yr per unit R; the trustworthy part
        ("a_lowR_provisional_30m.tif", a_low),               # provisional LOW-family A
        ("a_highR_sensitivity_30m.tif", a_high),             # HIGH-family sensitivity A
    ]:
        out = np.where(np.isfinite(arr), arr, -9999.0).astype("float32")
        path = OUTPUT_DIR / name
        with rasterio.open(path, "w", **out_profile) as ds:
            ds.write(out, 1)
        print(f"wrote {path}")

    def stats(arr):
        v = arr[np.isfinite(arr)]
        return {
            "valid_cells": int(v.size),
            "mean": round(float(np.mean(v)), 6) if v.size else None,
            "p50": round(float(np.percentile(v, 50)), 6) if v.size else None,
            "p95": round(float(np.percentile(v, 95)), 6) if v.size else None,
            "max": round(float(np.max(v)), 6) if v.size else None,
            "frac_lt_1_t_ha_yr": round(float((v < 1.0).mean()), 4) if v.size else None,
        }

    diag = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/factors/derive_peru_pilot_usle_soil_loss.py",
        "formula": "structure = K_SI x LS x C x P; A = structure x R",
        "scalars": {
            "K_SI_mean_0_5cm": round(K_SI_MEAN, 6),
            "R_low_default": R_LOW_DEFAULT,
            "R_high_sensitivity": R_HIGH_SENSITIVITY,
            "P": P,
        },
        "boundary_status": "engineering_pilot_not_research_selected",
        "r_invariance_note": ("The hotspot RANK is R-invariant; R only scales absolute magnitude. "
                              "The LOW R is a provisional screening default; a PE1-specific CHIRPS/"
                              "ERA5 R should be derived for any magnitude claim."),
        "zimbabwe_v1_reference": {
            "K_SI_mean": 0.022319,
            "R_low_default": 238.6,
            "a_mean_lowR": 0.5018,
        },
        "stats": {
            "structure_per_unit_R": stats(structure),
            "a_lowR_provisional": stats(a_low),
            "a_highR_sensitivity": stats(a_high),
        },
    }
    (OUTPUT_DIR / "usle_soil_loss_diagnostics.json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
    print(f"\ndiagnostics: {OUTPUT_DIR / 'usle_soil_loss_diagnostics.json'}")
    print(f"scalars: K_SI={K_SI_MEAN:.5f}  R_low={R_LOW_DEFAULT}  R_high={R_HIGH_SENSITIVITY}  P={P}")
    for k, v in diag["stats"].items():
        if v["mean"] is not None:
            print(f"  {k}: mean={v['mean']} p95={v['p95']} max={v['max']} frac<1={v['frac_lt_1_t_ha_yr']}")


if __name__ == "__main__":
    main()
