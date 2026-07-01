#!/usr/bin/env python3
"""Re-combine USLE Annual Soil Loss (A) with V2 smoother R-factor candidates and run the
hotspot-survival test requested by the mentor (2026-06-16, IFPM-074).

Local TOOLING script. The V1 soil-loss A used a single V1 zonal-mean R scalar, so the spatial
pattern of A was mathematically fixed by LS x C x K (R was just a global multiplier). The mentor
asked to switch V2 to a smoother R and test whether the hotspot pattern survives.

This script performs two tests per candidate R:

1. Zonal-scalar A (same USLE path as V1): A_v2 = a_structure x R_zonal_scalar, where a_structure
   is the already-produced R-invariant raster K x LS x C x P. This shows how the absolute magnitude
   shifts under each smoother R, but the spatial pattern is identical to V1 by construction.

2. Spatially-varying A (the real survival test): A_v2_spatial = LS x C x K x R_pixelwise, where the
   candidate R raster (0.05 deg) is resampled to the 30 m grid FOR DIAGNOSTIC PURPOSES ONLY and
   labelled as such. This lets R's spatial heterogeneity reshape the hotspot locations. The test
   asks: do the top erosion hotspots still fall on the LS x C high zones (the V1 reference), or does
   spatially-varying R relocate them?

Resolution handling (documented, defensible):
- LS and C vary at the V1 30 m grid.
- K (SoilGrids 250 m) is a V1 zonal-mean scalar (coarse->fine resampling forbidden).
- R per candidate: zonal scalar for path 1; resampled to 30 m for path 2 (diagnostic only).
- P = 1 (documented default assumption).
- The 30 m resample of R in path 2 is explicitly NOT a pixel-level 30 m evidence product; it is a
  diagnostic to quantify how much R's spatial heterogeneity perturbs the hotspot pattern.

Usage (from workspace root):
    .venv/bin/python bin/factors/derive_v2_usle_soil_loss.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]

# Inputs that already exist (V1 processing).
LS = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor/v1_ls_factor_capped50_hillslope_30m.tif"
C = ROOT / "outputs/esa_worldcover_2021_v1_methodology/c_factor/c_factor_v1_30m.tif"
K_DIAG = ROOT / "outputs/soilgrids_250m_sediment_candidate/k_factor_diagnostics.json"
A_STRUCTURE = ROOT / "outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif"
V1_A_MEAN_DIAG = ROOT / "outputs/v1_usle_soil_loss/soil_loss_diagnostics.json"

# V2 R-factor candidate rasters (from bin/factors/derive_v2_rfactor_candidates.py).
V2_R_DIR = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/rasters"
V2_R_DIAG = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/v2_rfactor_diagnostics.json"

# rf_lo removed after literature-integrity check (Lo et al. 1985 used mean annual precipitation,
# not MFI; the 0.0737/1.81 coefficients had no traceable source).
CANDIDATES = ["rf_v1_bimodal", "rf_arnoldus", "rf_rf_low_branch"]

# Output directory (created inside main(), not at import time).
OUTPUT_DIR = ROOT / "outputs/v1_usle_soil_loss/v2_rfactor"

# Severity classes for A (t/ha/yr); identical to V1 so class transitions are comparable.
CLASS_BOUNDS = [0, 1, 5, 10, 50, np.inf]  # boundaries; class index = bucket
CLASS_LABELS = ["1_very_low_0_1", "2_low_1_5", "3_moderate_5_10", "4_high_10_50", "5_very_high_50plus"]


def read_band(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype("float64")
        profile = ds.profile
        nodata = ds.nodata
    if nodata is not None:
        arr[arr == nodata] = np.nan
    return arr, profile


def classify(a: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, dtype="uint8")
    m = np.isfinite(a)
    out[m & (a < 1)] = 1
    out[m & (a >= 1) & (a < 5)] = 2
    out[m & (a >= 5) & (a < 10)] = 3
    out[m & (a >= 10) & (a < 50)] = 4
    out[m & (a >= 50)] = 5
    out[~m] = 0
    return out


def stats(arr: np.ndarray) -> dict:
    v = arr[np.isfinite(arr)]
    if not v.size:
        return {}
    return {
        "valid": int(v.size),
        "mean": round(float(np.mean(v)), 4),
        "std": round(float(np.std(v)), 4),
        "p50": round(float(np.percentile(v, 50)), 4),
        "p95": round(float(np.percentile(v, 95)), 4),
        "max": round(float(np.max(v)), 3),
    }


def class_counts(cls: np.ndarray) -> dict:
    vals, counts = np.unique(cls[cls > 0], return_counts=True)
    return {CLASS_LABELS[int(v) - 1]: int(c) for v, c in zip(vals, counts, strict=True)}


def resample_r_to_30m(r_path: Path, ref_profile: dict) -> np.ndarray:
    """Resample a 0.05 deg R raster to the V1 30 m grid (DIAGNOSTIC ONLY).

    Uses bilinear resampling because R is a continuous climatology field; nearest would create
    block artifacts. The result is labelled diagnostic-only and is not a pixel-level 30 m evidence
    product (per the V1 terrain reference grid rule).
    """
    dst = np.full((ref_profile["height"], ref_profile["width"]), np.nan, dtype="float64")
    with rasterio.open(r_path) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_profile["transform"],
            dst_crs=ref_profile["crs"],
            resampling=Resampling.bilinear,
            src_nodata=src.nodata,
            dst_nodata=np.nan,
        )
    dst[~np.isfinite(dst)] = np.nan
    return dst


def pearson(a: np.ndarray, b: np.ndarray) -> float | None:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return None
    aa, bb = a[m], b[m]
    if aa.std() == 0 or bb.std() == 0:
        return None
    return float(np.corrcoef(aa, bb)[0, 1])


def spearman(a: np.ndarray, b: np.ndarray) -> float | None:
    """Spearman rho via scipy (average-rank tie handling).

    Uses scipy.stats.spearmanr rather than a hand-rolled argsort-based rank, because C-factor has
    large flat regions (identical C per land-cover class) that create many ties; argsort breaks
    ties by index order and biases the rank correlation.
    """
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return None
    aa, bb = a[m], b[m]
    if aa.std() == 0 or bb.std() == 0:
        return None
    rho, _p = spearmanr(aa, bb)
    return float(rho)


def class_transition_matrix(cls_a: np.ndarray, cls_b: np.ndarray) -> dict:
    """Row = class in cls_a, col = class in cls_b. Keys like '1->1'."""
    out: dict[str, int] = {}
    m = (cls_a > 0) & (cls_b > 0)
    for ca in range(1, 6):
        for cb in range(1, 6):
            out[f"{ca}->{cb}"] = int(np.sum(m & (cls_a == ca) & (cls_b == cb)))
    return out


def main() -> None:
    raise SystemExit(
        "DEPRECATED: do not regenerate V2 USLE A products from the old R-factor. "
        "See outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md "
        "and context/docs/project-management/rfactor_investigation_consolidated.md."
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Upfront input validation so a fresh checkout fails with a clear message, not a raw traceback.
    required = [LS, C, K_DIAG, A_STRUCTURE, V1_A_MEAN_DIAG, V2_R_DIAG]
    missing = [p for p in required if not p.exists()]
    if missing:
        raise SystemExit(
            "Missing required inputs (run V1 LS/C/K/USLE processing and V2 R-factor derivation "
            "first):\n  " + "\n  ".join(str(p) for p in missing)
        )
    for cid in CANDIDATES:
        rp = ROOT / json.load(open(V2_R_DIAG))["candidates"][cid]["raster"]
        if not rp.exists():
            raise SystemExit(f"Missing V2 R-factor raster for {cid}: {rp}")

    # --- Load shared V1 spatial structure (R-invariant) and factor rasters ---
    ls, profile30 = read_band(LS)
    c, _ = read_band(C)
    a_structure, _ = read_band(A_STRUCTURE)

    # K SI scalar (same as V1: K_US_mean * 0.1317)
    with open(K_DIAG) as f:
        kd = json.load(f)
    k_us_mean = kd["v1_zonal_summary"]["k_0_5cm_us"]["mean"]
    k_si_mean = k_us_mean * 0.1317
    P = 1.0

    print(f"scalars: K_SI={k_si_mean:.5f}  P={P}")
    print(f"a_structure (K x LS x C x P, R-invariant): mean={np.nanmean(a_structure):.6f} "
          f"p95={np.nanpercentile(a_structure, 95):.6f}")

    # --- Hotspot reference mask: top p95 cells of a_structure (R-invariant) ---
    # These are the erosion hotspots defined purely by LS x C x K, independent of any R choice.
    hotspot_threshold = float(np.nanpercentile(a_structure, 95))
    hotspot_ref = (a_structure >= hotspot_threshold) & np.isfinite(a_structure)
    n_hotspot = int(hotspot_ref.sum())
    print(f"hotspot reference (a_structure p95): {n_hotspot} cells ({100*n_hotspot/np.isfinite(a_structure).sum():.2f}%)")

    # --- Load V2 candidate diagnostics (zonal R scalars + raster paths) ---
    with open(V2_R_DIAG) as f:
        v2_diag = json.load(f)

    out_profile = profile30.copy()
    out_profile.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)

    per_candidate: dict[str, dict] = {}
    for cid in CANDIDATES:
        cand = v2_diag["candidates"][cid]
        r_zonal = float(cand["zonal_summary_MJ_mm_ha_h_yr"]["mean"])
        r_raster_path = ROOT / cand["raster"]

        # Path 1: zonal-scalar A (same USLE path as V1)
        a_zonal = a_structure * r_zonal

        # Path 2: spatially-varying A (R resampled to 30m, DIAGNOSTIC ONLY)
        r_30m = resample_r_to_30m(r_raster_path, profile30)
        # Rebuild A with spatially-varying R; mask invalid cells the same way V1 did.
        a_spatial = k_si_mean * ls * c * r_30m * P
        # Common validity mask: a cell is valid only if LS, C, AND R_30m are finite. Applying the
        # SAME mask to a_zonal keeps the two paths cell-for-cell comparable (previously a_zonal kept
        # ~185k extra cells where R_30m was NaN, which silently trimmed the agreement metrics).
        r_valid = np.isfinite(r_30m)
        common_valid = np.isfinite(ls) & np.isfinite(c) & r_valid
        a_zonal = np.where(common_valid, a_zonal, np.nan)
        a_spatial = np.where(common_valid, a_spatial, np.nan)
        cls_zonal = classify(a_zonal)
        cls_spatial = classify(a_spatial)

        # Hotspot survival: of the R-invariant hotspot cells, how many stay in the top p95 of
        # the spatially-varying A? High overlap => R heterogeneity did NOT relocate hotspots.
        a_spatial_p95 = float(np.nanpercentile(a_spatial, 95))
        hotspot_spatial = (a_spatial >= a_spatial_p95) & np.isfinite(a_spatial)
        overlap = int(np.sum(hotspot_ref & hotspot_spatial))
        survival_rate = overlap / n_hotspot if n_hotspot else 0.0

        # Spatial agreement between the two paths, on the common-valid cell set.
        r_pearson = pearson(a_zonal, a_spatial)
        r_spearman = spearman(a_zonal, a_spatial)

        # Class agreement (zonal vs spatial) normalised on the common-valid intersection, NOT on the
        # full array (which would understate agreement by counting all invalid pixels in the denom).
        both_valid = (cls_zonal > 0) & (cls_spatial > 0)
        if np.any(both_valid):
            cls_agree_zonal_spatial = float(np.mean(cls_zonal[both_valid] == cls_spatial[both_valid]))
        else:
            cls_agree_zonal_spatial = 0.0
        n_zonal = int(np.sum(cls_zonal > 0))
        n_spatial = int(np.sum(cls_spatial > 0))
        n_both = int(np.sum(both_valid))

        # Write A rasters. The spatial product embeds a 0.05deg->30m R resample that is DIAGNOSTIC
        # ONLY (not pixel-level evidence per the V1 terrain reference grid rule), so its filename
        # carries an explicit _DIAGNOSTIC suffix so it cannot be confused with the zonal product.
        for name, arr in [
            (f"a_v2_{cid}_zonal_30m.tif", a_zonal),
            (f"a_v2_{cid}_spatial_DIAGNOSTIC_30m.tif", a_spatial),
        ]:
            out = np.where(np.isfinite(arr), arr, -9999.0).astype("float32")
            with rasterio.open(OUTPUT_DIR / name, "w", **out_profile) as ds:
                ds.write(out, 1)
                ds.update_tags(
                    1,
                    IFPM_NOTE=(
                        "DIAGNOSTIC ONLY: 0.05deg R resampled to 30m for survival test; NOT pixel-level evidence"
                        if "DIAGNOSTIC" in name else "V2 zonal-scalar A (R as zonal mean)"
                    ),
                )
            print(f"wrote {OUTPUT_DIR / name}")

        # Write zonal classes (comparable to V1 a_mean_classes)
        cls_profile = profile30.copy()
        cls_profile.update(dtype="uint8", nodata=0, compress="deflate", tiled=True)
        with rasterio.open(OUTPUT_DIR / f"a_v2_{cid}_zonal_classes_30m.tif", "w", **cls_profile) as ds:
            ds.write(cls_zonal, 1)

        per_candidate[cid] = {
            "r_zonal_scalar_MJ_mm_ha_h_yr": round(r_zonal, 3),
            "a_zonal_stats_t_ha_yr": stats(a_zonal),
            "a_spatial_stats_t_ha_yr": stats(a_spatial),
            "a_zonal_class_counts": class_counts(cls_zonal),
            "a_spatial_class_counts": class_counts(cls_spatial),
            "valid_cell_counts": {
                "n_zonal_valid": n_zonal,
                "n_spatial_valid": n_spatial,
                "n_both_valid": n_both,
                "note": "zonal and spatial are masked to the SAME common-valid set; no cell-count delta.",
            },
            "hotspot_survival": {
                "reference_mask": "a_structure p95 cells (R-invariant LS x C x K hotspots)",
                "n_reference_hotspot_cells": n_hotspot,
                "overlap_with_spatial_p95": overlap,
                "survival_rate": round(survival_rate, 4),
                "test_design_caveat": (
                    "The LS factor spans ~4 orders of magnitude while the resampled R field varies "
                    "only ~3x across the catchment, so the top-p95 tail is dominated by LS x C and "
                    "the survival rate is structurally biased toward high values. The V1 bimodal "
                    "baseline also scores ~0.84, showing the test has low discriminating power "
                    "between good and bad R formulas. Treat survival rates as a weak/confirmatory "
                    "signal, not a quality ranking."
                ),
                "interpretation": (
                    "1.0 = R heterogeneity did not relocate hotspots; <1.0 = spatially-varying R "
                    "moved some hotspots away from the LS x C x K zones."
                ),
            },
            "zonal_vs_spatial_agreement": {
                "pearson_r": round(r_pearson, 4) if r_pearson is not None else None,
                "spearman_rho": round(r_spearman, 4) if r_spearman is not None else None,
                "class_agreement_fraction": round(cls_agree_zonal_spatial, 4),
                "metric_basis": "common-valid cell set (LS, C, and R_30m all finite)",
            },
        }

    # --- Cross-candidate: do smoother candidates agree with each other on hotspot location? ---
    # Using spatial A, pairwise hotspot overlap. NOTE: each candidate's hotspot set is its own
    # top-p95, so the Jaccard of two p95 masks of the same LS*C-dominated field is partly
    # definitional; report it as a concordance summary, not independent cross-validation.
    spatial_hotspots: dict[str, np.ndarray] = {}
    for cid in CANDIDATES:
        a_s = read_band(OUTPUT_DIR / f"a_v2_{cid}_spatial_DIAGNOSTIC_30m.tif")[0]
        thr = float(np.nanpercentile(a_s, 95))
        spatial_hotspots[cid] = (a_s >= thr) & np.isfinite(a_s)

    cross_hotspot = {}
    for i, ci in enumerate(CANDIDATES):
        for cj in CANDIDATES[i + 1:]:
            hi, hj = spatial_hotspots[ci], spatial_hotspots[cj]
            union = np.sum(hi | hj)
            cross_hotspot[f"{ci}__{cj}"] = {
                "overlap_cells": int(np.sum(hi & hj)),
                "jaccard": round(float(np.sum(hi & hj) / union), 4) if union else 0.0,
            }

    diagnostics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/factors/derive_v2_usle_soil_loss.py",
        "purpose": (
            "Re-combine USLE A with V2 smoother R candidates and run the hotspot-survival test "
            "(mentor decision 2026-06-16, IFPM-074)."
        ),
        "formula": "A = R x K x LS x C x P (SI units: A in t/ha/yr)",
        "scalars": {"K_SI_mean": round(k_si_mean, 6), "P": P},
        "resolution_handling": (
            "LS and C at 30 m (spatially varying); K as V1 zonal scalar. R per candidate: zonal "
            "scalar for path 1; resampled to 30 m (bilinear) for path 2 DIAGNOSTIC ONLY. The 30 m R "
            "resample is a deliberate, documented diagnostic waiver of the V1 terrain reference "
            "grid rule (recorded in context/docs/data-management/v1_terrain_reference_grid_rule.md); "
            "the spatial product is NOT pixel-level evidence and its filename carries _DIAGNOSTIC."
        ),
        "hotspot_reference": {
            "definition": "top p95 cells of a_structure (K x LS x C x P), R-invariant",
            "threshold_t_ha_yr_per_unit_R": round(hotspot_threshold, 8),
            "n_cells": n_hotspot,
            "fraction_of_valid": round(n_hotspot / float(np.isfinite(a_structure).sum()), 4),
        },
        "candidates": per_candidate,
        "cross_candidate_hotspot_agreement_jaccard": cross_hotspot,
        "status": "DIAGNOSTIC data product, not an interpretable validated soil-loss map.",
    }
    out_json = OUTPUT_DIR / "v2_hotspot_survival_diagnostics.json"
    out_json.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(f"\nwrote {out_json}")

    print("\n=== V2 hotspot survival summary ===")
    print(f"reference hotspot cells (a_structure p95): {n_hotspot}")
    for cid in CANDIDATES:
        d = per_candidate[cid]
        hs = d["hotspot_survival"]
        ag = d["zonal_vs_spatial_agreement"]
        print(f"  {cid:18s} R_zonal={d['r_zonal_scalar_MJ_mm_ha_h_yr']:7.1f}  "
              f"A_zonal_mean={d['a_zonal_stats_t_ha_yr']['mean']:.4f}  "
              f"survival={hs['survival_rate']:.3f}  "
              f"spearman(zonal,spatial)={ag['spearman_rho']}")


if __name__ == "__main__":
    main()
