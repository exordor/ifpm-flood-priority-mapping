#!/usr/bin/env python3
"""Build candidate-comparison CSV matrices for the V2 R-factor evaluation.

Local TOOLING script. Produces three CSVs that summarise the V2 R-factor candidate comparison for
the mentor and for the processing record:

1. v2_rfactor_candidate_summary.csv  - one row per candidate: zonal R, A-mean, bimodality bands,
   continuity at MFI=80, hotspot survival, zonal-vs-spatial agreement.
2. v2_rfactor_candidate_correlation.csv - pairwise Pearson and Spearman of the 0.05 deg R rasters.
3. v2_rfactor_hotspot_survival.csv  - per-candidate hotspot survival + cross-candidate Jaccard.

Reads the diagnostics JSONs produced by derive_v2_rfactor_candidates.py and
derive_v2_usle_soil_loss.py; does not recompute rasters.

Usage (from workspace root):
    .venv/bin/python bin/investigate/compare_v2_rfactor_candidates.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
V2_R_DIAG = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/v2_rfactor_diagnostics.json"
HOTSPOT_DIAG = ROOT / "outputs/v1_usle_soil_loss/v2_rfactor/v2_hotspot_survival_diagnostics.json"
R_RASTER_DIR = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/rasters"

OUT_DIR = ROOT / "outputs/v1_usle_soil_loss/v2_rfactor"
OUT_SUMMARY = OUT_DIR / "v2_rfactor_candidate_summary.csv"
OUT_CORR = OUT_DIR / "v2_rfactor_candidate_correlation.csv"
OUT_SURVIVAL = OUT_DIR / "v2_rfactor_hotspot_survival.csv"

# rf_lo removed after literature-integrity check (coefficients had no traceable source).
CANDIDATES = ["rf_v1_bimodal", "rf_arnoldus", "rf_rf_low_branch"]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}")


def read_array(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64")
        if ds.nodata is not None:
            a[a == ds.nodata] = np.nan
    return a


def pearson(a: np.ndarray, b: np.ndarray):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3 or a[m].std() == 0 or b[m].std() == 0:
        return None
    return float(np.corrcoef(a[m], b[m])[0, 1])


def spearman(a: np.ndarray, b: np.ndarray):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3 or a[m].std() == 0 or b[m].std() == 0:
        return None
    aa, bb = a[m], b[m]
    ra = np.argsort(np.argsort(aa))
    rb = np.argsort(np.argsort(bb))
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> None:
    raise SystemExit(
        "DEPRECATED: do not regenerate V2 R-factor comparison outputs. "
        "See outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md "
        "and context/docs/project-management/rfactor_investigation_consolidated.md."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(V2_R_DIAG) as f:
        r_diag = json.load(f)
    with open(HOTSPOT_DIAG) as f:
        hs_diag = json.load(f)

    # --- 1. Candidate summary ---
    summary_rows: list[dict] = []
    for cid in CANDIDATES:
        rc = r_diag["candidates"][cid]
        z = rc["zonal_summary_MJ_mm_ha_h_yr"]
        bim = rc["bimodality_bands"]
        cont = rc["continuity_at_mfi_80"]
        hc = hs_diag["candidates"][cid]
        az = hc["a_zonal_stats_t_ha_yr"]
        surv = hc["hotspot_survival"]
        ag = hc["zonal_vs_spatial_agreement"]
        summary_rows.append({
            "candidate_id": cid,
            "display_name": rc["display_name"],
            "citation": rc["citation"],
            "r_zonal_mean": round(z["mean"], 2),
            "r_min": round(z["min"], 2),
            "r_p50": round(z["p50"], 2),
            "r_p95": round(z["p95"], 2),
            "r_max": round(z["max"], 2),
            "cells_lt_100": bim["cells_lt_100"],
            "cells_100_400": bim["cells_100_400"],
            "cells_gt_400": bim["cells_gt_400"],
            "abs_jump_at_mfi_80": cont["abs_jump_at_80"],
            "a_zonal_mean_t_ha_yr": az.get("mean"),
            "a_zonal_p95_t_ha_yr": az.get("p95"),
            "hotspot_survival_rate": surv["survival_rate"],
            "spearman_zonal_vs_spatial": ag["spearman_rho"],
            "pearson_zonal_vs_spatial": ag["pearson_r"],
        })
    write_csv(OUT_SUMMARY, summary_rows)

    # --- 2. Pairwise correlation of 0.05 deg R rasters ---
    arrays = {cid: read_array(R_RASTER_DIR / f"{cid}_0p05deg.tif") for cid in CANDIDATES}
    corr_rows: list[dict] = []
    for i, ci in enumerate(CANDIDATES):
        for cj in CANDIDATES[i:]:
            rp = pearson(arrays[ci], arrays[cj])
            rs = spearman(arrays[ci], arrays[cj])
            corr_rows.append({
                "candidate_a": ci,
                "candidate_b": cj,
                "pearson_r": round(rp, 4) if rp is not None else "",
                "spearman_rho": round(rs, 4) if rs is not None else "",
            })
    write_csv(OUT_CORR, corr_rows)

    # --- 3. Hotspot survival + cross-candidate Jaccard ---
    # Use a fixed superset field schema so per-candidate rows and cross-candidate rows share one CSV.
    surv_rows: list[dict] = []
    for cid in CANDIDATES:
        hc = hs_diag["candidates"][cid]["hotspot_survival"]
        surv_rows.append({
            "candidate_id": cid,
            "n_reference_hotspot_cells": hc["n_reference_hotspot_cells"],
            "overlap_with_spatial_p95": hc["overlap_with_spatial_p95"],
            "survival_rate": hc["survival_rate"],
            "cross_hotspot_jaccard": "",
            "cross_overlap_cells": "",
        })
    # cross-candidate Jaccard on spatial hotspots
    cross = hs_diag["cross_candidate_hotspot_agreement_jaccard"]
    for key, val in cross.items():
        ci, cj = key.split("__")
        surv_rows.append({
            "candidate_id": f"{ci} vs {cj}",
            "n_reference_hotspot_cells": "",
            "overlap_with_spatial_p95": "",
            "survival_rate": "",
            "cross_hotspot_jaccard": val["jaccard"],
            "cross_overlap_cells": val["overlap_cells"],
        })
    # Normalise so DictWriter infers a stable field set from the first row (which has all keys).
    write_csv(OUT_SURVIVAL, surv_rows)

    print("\n=== Candidate summary (key columns) ===")
    print(f"{'candidate':20s} {'R_mean':>8s} {'jump@80':>9s} {'survival':>9s} {'spearman':>9s}")
    for r in summary_rows:
        print(f"{r['candidate_id']:20s} {r['r_zonal_mean']:8.1f} {r['abs_jump_at_mfi_80']:9.1f} "
              f"{r['hotspot_survival_rate']:9.3f} {r['spearman_zonal_vs_spatial']}")


if __name__ == "__main__":
    main()
