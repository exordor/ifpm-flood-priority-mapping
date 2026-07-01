#!/usr/bin/env python3
"""Deprecated V1 USLE Annual Soil Loss generator.

This script combined A = R x K x LS x C x P using the old V1 R-factor. The 2026-06-19 formula
audit deprecated those R/A products because the old R used Renard-Freimund coefficients with the
wrong predictor and an invented break point. Do not rerun this script for mentor figures or
analysis. The existing `a_structure_K_LS_C_30m.tif` is the only safe product from this workflow.

Usage:
    .venv/bin/python bin/factors/derive_v1_usle_soil_loss.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]

LS = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor/v1_ls_factor_capped50_hillslope_30m.tif"
C = ROOT / "outputs/esa_worldcover_2021_v1_methodology/c_factor/c_factor_v1_30m.tif"
K_DIAG = ROOT / "outputs/soilgrids_250m_sediment_candidate/k_factor_diagnostics.json"
R_DIAG = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor/r_factor_diagnostics.json"

OUTPUT_DIR = ROOT / "outputs/v1_usle_soil_loss"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# R bimodal modes (from R-factor diagnostics): approximate low and high cluster centres.
R_LOW = 50.0
R_HIGH = 510.0


def read_band(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype("float64")
        profile = ds.profile
        nodata = ds.nodata
    if nodata is not None:
        arr[arr == nodata] = np.nan
    return arr, profile


def load_scalar(diag_path: Path, summary_key: str, metric: str, si_factor: float = 1.0):
    with open(diag_path) as f:
        d = json.load(f)
    # navigate to the zonal summary
    z = d.get("v1_zonal_summary", d.get("v1_zonal_summary", {}))
    if summary_key in z:
        val = z[summary_key].get(metric)
    else:
        # fallback: top-level
        val = d.get(metric)
    return float(val) * si_factor if val is not None else None


def main() -> None:
    raise SystemExit(
        "DEPRECATED: do not regenerate V1 R/A products from the old R-factor. "
        "See outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md."
    )

    ls, profile = read_band(LS)
    c, _ = read_band(C)

    # K SI scalar: K_US_mean * 0.1317
    with open(K_DIAG) as f:
        kd = json.load(f)
    k_us_mean = kd["v1_zonal_summary"]["k_0_5cm_us"]["mean"]
    k_si_mean = k_us_mean * 0.1317

    # R SI scalar (and document bimodality)
    with open(R_DIAG) as f:
        rd = json.load(f)
    r_mean = rd["v1_zonal_summary"]["r_mean"] if "r_mean" in rd.get("v1_zonal_summary", {}) else None
    if r_mean is None:
        # try alternate key
        rz = rd.get("v1_zonal_summary", {})
        r_mean = rz.get("mean", rz.get("r_zonal_mean", 408.0))
    r_mean = float(r_mean)

    P = 1.0

    print(f"scalars: K_SI={k_si_mean:.5f}  R_mean={r_mean:.1f} (deprecated old-R modes: low~{R_LOW}, high~{R_HIGH})  P={P}")

    # Trustworthy spatial structure at 30 m: K_SI x LS x C x P  (everything except R)
    structure = k_si_mean * ls * c * P
    invalid = ~np.isfinite(ls) | ~np.isfinite(c)
    structure = np.where(invalid, np.nan, structure)

    # A for the three R scenarios (absolute values NOT trustworthy due to R bimodality)
    a_low = structure * R_LOW
    a_mean = structure * r_mean
    a_high = structure * R_HIGH

    out_profile = profile.copy()
    out_profile.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)

    outputs = {
        "a_structure_K_LS_C_30m.tif": structure,        # t/ha/yr per unit R; the trustworthy part
        "a_low_R50_30m.tif": a_low,
        "a_mean_30m.tif": a_mean,
        "a_high_R510_30m.tif": a_high,
    }
    for name, arr in outputs.items():
        out = np.where(np.isfinite(arr), arr, -9999.0).astype("float32")
        path = OUTPUT_DIR / name
        with rasterio.open(path, "w", **out_profile) as ds:
            ds.write(out, 1)
        print(f"wrote {path}")

    def stats(arr):
        v = arr[np.isfinite(arr)]
        if not v.size:
            return {}
        return {"valid": int(v.size), "mean": round(float(np.mean(v)), 4),
                "p50": round(float(np.percentile(v, 50)), 4),
                "p95": round(float(np.percentile(v, 95)), 4),
                "max": round(float(np.max(v)), 3)}

    # Soil-loss severity classes for the mean case (t/ha/yr): a common scheme.
    def classify(arr):
        out = np.zeros(arr.shape, dtype="uint8")
        m = np.isfinite(arr)
        out[m & (arr < 1)] = 1       # very low
        out[m & (arr >= 1) & (arr < 5)] = 2   # low
        out[m & (arr >= 5) & (arr < 10)] = 3  # moderate
        out[m & (arr >= 10) & (arr < 50)] = 4 # high
        out[m & (arr >= 50)] = 5              # very high
        out[~m] = 0
        return out

    a_mean_classes = classify(a_mean)
    cls_profile = profile.copy()
    cls_profile.update(dtype="uint8", nodata=0, compress="deflate", tiled=True)
    with rasterio.open(OUTPUT_DIR / "a_mean_classes_30m.tif", "w", **cls_profile) as ds:
        ds.write(a_mean_classes, 1)

    # class counts
    vals, counts = np.unique(a_mean_classes[a_mean_classes > 0], return_counts=True)
    class_counts = {str(int(v)): int(c) for v, c in zip(vals, counts, strict=True)}

    diag = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/factors/derive_v1_usle_soil_loss.py",
        "formula": "A = R x K x LS x C x P (SI units: A in t/ha/yr)",
        "scalars": {"K_SI_mean": round(k_si_mean, 6), "R_mean": round(r_mean, 1),
                    "R_low": R_LOW, "R_high": R_HIGH, "P": P},
        "resolution_handling": ("LS and C at 30 m (spatially varying); K and R as V1 zonal-mean "
                                 "scalars (coarse->fine resampling forbidden). P=1 default."),
        "r_bimodality_caveat": ("Deprecated: the old V1 R-factor pattern was produced by a "
                                 "wrong Renard-Freimund predictor/break-point setup. Absolute A "
                                 "values from this workflow are NOT trustworthy. The a_structure "
                                 "raster is the trustworthy spatial part (LS x C x K_SI per unit R)."),
        "stats": {
            "structure_per_unit_R": stats(structure),
            "a_low_R50": stats(a_low),
            "a_mean": stats(a_mean),
            "a_high_R510": stats(a_high),
        },
        "a_mean_class_counts_t_per_ha_per_yr": {
            "1_very_low_0_1": class_counts.get("1", 0),
            "2_low_1_5": class_counts.get("2", 0),
            "3_moderate_5_10": class_counts.get("3", 0),
            "4_high_10_50": class_counts.get("4", 0),
            "5_very_high_50plus": class_counts.get("5", 0),
        },
        "status": "DIAGNOSTIC data product, not an interpretable validated soil-loss map.",
    }
    (OUTPUT_DIR / "soil_loss_diagnostics.json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
    print(f"\ndiagnostics: {OUTPUT_DIR / 'soil_loss_diagnostics.json'}")
    print("\n=== A-factor V1 stats (t/ha/yr) ===")
    for k, v in diag["stats"].items():
        if v:
            print(f"  {k}: mean={v['mean']} p50={v['p50']} p95={v['p95']} max={v['max']}")
    print("\n=== A-mean severity classes ===")
    for k, v in diag["a_mean_class_counts_t_per_ha_per_yr"].items():
        print(f"  {k}: {v} cells")


if __name__ == "__main__":
    main()
