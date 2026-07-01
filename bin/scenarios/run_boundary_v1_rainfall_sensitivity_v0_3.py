#!/usr/bin/env python3
"""Run rainfall-included vs rainfall-excluded sensitivity scenarios for boundary_v1.

This is the IFPM-090 next-executable experiment: does adding a standalone
CHIRPS-derived rainfall criterion shift the Top-20% hotspot pattern relative to
the v0.2 baseline (where rainfall enters only indirectly via the R-normalized
sediment criterion)?

Three scenarios, all `sensitivity_scenario` under the execution status policy:
  - rainfall_excluded: 4 core criteria at 0.25 each (v0.2 equal_core analogue).
  - rainfall_included_low: 5 criteria, rainfall at 0.10, others re-scaled.
  - rainfall_included_high: 5 criteria, rainfall at 0.25, others re-scaled.

The headline output is the Top-20% hotspot overlap between each rainfall-included
scenario and the v0.2 baseline hotspot, quantifying how much the pattern moves.

GOVERNANCE: the rainfall criterion is a coarse-to-reference-grid CHIRPS proxy
(effective resolution ~5 km, NOT native 30 m rainfall). Outputs are
sensitivity_scenario, not final flood-risk or intervention-priority claims.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "rainfall_sensitivity_v0_3"
OUT_DIR = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"

# Inputs from the main workspace outputs/. Default to ROOT/outputs (correct in
# the main checkout); set IFPM_MAIN_OUTPUTS to run inside a worktree.
MAIN_OUTPUTS = Path(os.environ.get("IFPM_MAIN_OUTPUTS", ROOT / "outputs"))
REF = MAIN_OUTPUTS / "srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
V1_GPKG = MAIN_OUTPUTS / "v1_working_boundary/v1_working_boundary.gpkg"
V02_CRITERIA = MAIN_OUTPUTS / f"{BOUNDARY_ID}/criteria_stack_v0_2/criteria"
SEDIMENT_DIR = MAIN_OUTPUTS / f"{BOUNDARY_ID}/sediment_r_factor_scenarios"
V02_BASELINE = MAIN_OUTPUTS / f"{BOUNDARY_ID}/priority_scenarios_v0_2"

# Rainfall criterion built by build_boundary_v1_rainfall_criterion_v0_3.py
# (lives in this worktree's outputs/).
RAINFALL_CRITERION = OUT_DIR / "criteria/rainfall_climatology_proxy_0_1_PROVISIONAL_30m.tif"

CRITERIA_PATHS = {
    "flood_hazard_proxy": V02_CRITERIA / "flood_hazard_proxy_0_1.tif",
    "sediment_risk_lowR_provisional": SEDIMENT_DIR / "sediment_risk_lowR_provisional_30m.tif",
    "land_cover_pressure": V02_CRITERIA / "land_cover_pressure_0_1.tif",
    "mining_pressure": V02_CRITERIA / "mining_pressure_0_1.tif",
    "rainfall_climatology_proxy": RAINFALL_CRITERION,
}

# v0.2 baseline Top-20% frequency (0-1: fraction of v0.2 scenarios in which the
# cell was a hotspot). Used to measure hotspot displacement.
V02_TOP20_FREQ = V02_BASELINE / "top20_frequency.tif"

CELL_AREA_KM2 = 0.0009  # 30 m x 30 m


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_reference() -> dict:
    with rasterio.open(REF) as ref:
        return ref.profile.copy()


def read_band(path: Path, profile: dict) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        if src.crs != profile["crs"] or src.transform != profile["transform"]:
            raise ValueError(f"grid mismatch: {path}")
        if src.width != profile["width"] or src.height != profile["height"]:
            raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def normalize_if_needed(name: str, data: np.ndarray) -> np.ndarray:
    """Keep 0-1 criteria as-is; max-normalize absolute-range criteria to [0,1]."""
    values = data[np.isfinite(data)]
    if values.size == 0:
        raise ValueError(f"empty criterion: {name}")
    if float(values.max()) <= 1.000001 and float(values.min()) >= -0.000001:
        return np.clip(data, 0.0, 1.0).astype("float32")
    max_value = float(values.max())
    if max_value <= 0:
        raise ValueError(f"non-positive criterion range: {name}")
    return np.clip(data / max_value, 0.0, 1.0).astype("float32")
CLAIM_NOTE = (
    "SENSITIVITY SCENARIO: provisional MCDA overlay testing whether a rainfall "
    "criterion shifts the v0.2 hotspot pattern. Not a validated flood-risk or "
    "intervention-priority map."
)


def scenario_weights() -> dict[str, dict[str, float]]:
    """Three scenarios. Rainfall-included scenarios keep the 4 core criteria and
    insert rainfall, re-scaling the core so weights sum to 1.0."""
    core = ["flood_hazard_proxy", "sediment_risk_lowR_provisional", "land_cover_pressure", "mining_pressure"]

    def with_rainfall(rain_w: float) -> dict[str, float]:
        core_w = (1.0 - rain_w) / len(core)
        weights = {c: core_w for c in core}
        weights["rainfall_climatology_proxy"] = rain_w
        return weights

    return {
        "rainfall_excluded": {c: 0.25 for c in core},
        "rainfall_included_low": with_rainfall(0.10),
        "rainfall_included_high": with_rainfall(0.25),
    }


def raster_stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "p50": round(float(np.percentile(values, 50)), 6),
        "p80": round(float(np.percentile(values, 80)), 6),
        "p95": round(float(np.percentile(values, 95)), 6),
        "max": round(float(values.max()), 6),
    }


def top20_overlap(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Top-20% hotspot overlap between two scored rasters.

    Returns Jaccard (intersection/union) and the per-scenario retention/share
    relative to baseline. Both masks are restricted to cells valid in BOTH.
    """
    valid = np.isfinite(a) & np.isfinite(b)
    a_vals = a[valid]
    b_vals = b[valid]
    ta = float(np.percentile(a_vals, 80))
    tb = float(np.percentile(b_vals, 80))
    mask_a = a[valid] >= ta
    mask_b = b[valid] >= tb
    inter = int(np.sum(mask_a & mask_b))
    union = int(np.sum(mask_a | mask_b))
    jaccard = inter / union if union else 0.0
    # Share of baseline hotspots retained by the scenario.
    retention = inter / int(mask_a.sum()) if mask_a.sum() else 0.0
    return {
        "baseline_top20_threshold": round(ta, 6),
        "scenario_top20_threshold": round(tb, 6),
        "intersection_cells": inter,
        "union_cells": union,
        "jaccard": round(jaccard, 6),
        "baseline_hotspot_cells": int(mask_a.sum()),
        "retention_of_baseline": round(retention, 6),
    }


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.04)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label(label, fontsize=8)


def plot_board(scenario_arrays: dict[str, np.ndarray], top20_frequency: np.ndarray, profile: dict) -> None:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0] / 1000, bounds[2] / 1000, bounds[1] / 1000, bounds[3] / 1000)

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), constrained_layout=True)
    panels = [
        ("A. Rainfall-excluded (baseline analogue)", scenario_arrays["rainfall_excluded"]),
        ("B. Rainfall-included high (w=0.25)", scenario_arrays["rainfall_included_high"]),
        ("C. Top-20% frequency across 3 scenarios", top20_frequency),
    ]
    for ax, (title, data) in zip(axes, panels, strict=True):
        cmap = "YlOrRd" if "frequency" not in title else "Blues"
        image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.9)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32735)", fontsize=8)
        ax.set_ylabel("Northing (km)", fontsize=8)
        ax.grid(color="0.9", linewidth=0.4)
        ax.tick_params(labelsize=7)
        add_colorbar(fig, ax, image, "0-1 score" if "frequency" not in title else "frequency")
    fig.suptitle(
        "boundary_v1 / rainfall_sensitivity_v0_3: does a rainfall criterion shift hotspots?",
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(OUT_DIR / "rainfall_sensitivity_board.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "rainfall_sensitivity_board.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()

    criteria = {
        name: normalize_if_needed(name, read_band(path, profile))
        for name, path in CRITERIA_PATHS.items()
    }
    scenarios = scenario_weights()

    # v0.2 baseline Top-20% frequency (the reference pattern to compare against).
    v02_freq = read_band(V02_TOP20_FREQ, profile)
    v02_hotspot = v02_freq >= 1.0  # stable across all 3 v0.2 scenarios

    scenario_arrays: dict[str, np.ndarray] = {}
    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    overlap_rows: list[dict[str, object]] = []
    top20_masks: list[np.ndarray] = []
    valid_any = np.logical_or.reduce([np.isfinite(arr) for arr in criteria.values()])

    for scenario, weights in scenarios.items():
        total = round(sum(weights.values()), 10)
        if total != 1.0:
            raise ValueError(f"weights for {scenario} sum to {total}")
        numerator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        denominator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        for criterion, weight in weights.items():
            layer = criteria[criterion]
            valid = np.isfinite(layer)
            numerator[valid] += layer[valid] * weight
            denominator[valid] += weight
            weight_rows.append(
                {
                    "boundary_id": BOUNDARY_ID,
                    "experiment_id": EXPERIMENT_ID,
                    "scenario": scenario,
                    "criterion": criterion,
                    "weight": round(weight, 8),
                    "claim_level": "sensitivity_scenario",
                }
            )
        score = np.divide(numerator, denominator, out=np.full_like(numerator, np.nan), where=denominator > 0)
        score[~valid_any] = np.nan
        score = np.clip(score, 0.0, 1.0).astype("float32")
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}.tif", score, profile, ifpm_note=CLAIM_NOTE)
        threshold = float(np.nanpercentile(score, 80))
        top20_masks.append(score >= threshold)

        summary_rows.append(
            {
                "boundary_id": BOUNDARY_ID,
                "experiment_id": EXPERIMENT_ID,
                "scenario": scenario,
                "top20_threshold": round(threshold, 6),
                **raster_stats(score),
            }
        )

    # Cross-scenario stability of THIS experiment's three scenarios.
    stack = np.stack(list(scenario_arrays.values())).astype("float32")
    finite_count = np.sum(np.isfinite(stack), axis=0)
    valid_stack = np.isfinite(stack)
    stack_zero = np.where(valid_stack, stack, 0.0)
    priority_mean = np.divide(
        np.sum(stack_zero, axis=0),
        finite_count,
        out=np.full(stack.shape[1:], np.nan, dtype="float32"),
        where=finite_count > 0,
    ).astype("float32")
    top20_frequency = np.mean(np.stack(top20_masks), axis=0).astype("float32")
    priority_mean[finite_count == 0] = np.nan
    top20_frequency[finite_count == 0] = np.nan

    write_raster(OUT_DIR / "priority_mean.tif", priority_mean, profile, ifpm_note=CLAIM_NOTE)
    write_raster(OUT_DIR / "top20_frequency.tif", top20_frequency, profile, ifpm_note=CLAIM_NOTE)
    plot_board(scenario_arrays, top20_frequency, profile)

    # Like-for-like v0.3-vs-v0.2 comparison: BOTH use "stable across all of their
    # own scenarios" (top20_frequency >= 1.0), so the two masks are comparable
    # set-size-wise. Comparing an 80th-percentile mask against a strict-stable
    # mask would be apples-to-oranges (20% vs ~12% of cells).
    v03_stable = top20_frequency >= 1.0
    valid_common = np.isfinite(top20_frequency) & np.isfinite(v02_freq)
    v03_s = v03_stable & valid_common
    v02_s = v02_hotspot & valid_common
    inter_v = int(np.sum(v03_s & v02_s))
    union_v = int(np.sum(v03_s | v02_s))
    overlap_rows.append(
        {
            "comparison": "v03_stable_all_vs_v02_stable_all",
            "method": "both use top20_frequency>=1.0 (stable across all own scenarios)",
            "v03_stable_cells": int(np.sum(v03_s)),
            "v02_stable_cells": int(np.sum(v02_s)),
            "intersection": inter_v,
            "union": union_v,
            "jaccard": round(inter_v / union_v, 6) if union_v else 0.0,
            "retention_of_v02": round(inter_v / int(np.sum(v02_s)), 6) if v02_s.any() else 0.0,
        }
    )

    # Pairwise overlap: rainfall-included scenarios vs the rainfall-excluded
    # baseline analogue (direct within-experiment displacement measure, both at
    # their own 80th percentile on the common-valid mask).
    # Also compute Spearman rank correlation, which is NOT threshold-sensitive:
    # the Top-20% Jaccard only measures the tail, while Spearman rho measures
    # how much the full priority ranking is reordered by adding rainfall. This
    # matters because rainfall is near-degenerate (mean 0.81, narrow range) and
    # may shift absolute scores without reordering cells.
    from scipy.stats import spearmanr

    excl = scenario_arrays["rainfall_excluded"]
    rank_rows: list[dict[str, object]] = []
    for name in ("rainfall_included_low", "rainfall_included_high"):
        ov = top20_overlap(excl, scenario_arrays[name])
        ov["comparison"] = f"{name}_vs_rainfall_excluded"
        ov["method"] = "both at own 80th percentile on common-valid mask"
        overlap_rows.append(ov)
        other = scenario_arrays[name]
        valid_pair = np.isfinite(excl) & np.isfinite(other)
        rho, pval = spearmanr(excl[valid_pair], other[valid_pair])
        rank_rows.append(
            {
                "scenario": name,
                "reference": "rainfall_excluded",
                "spearman_rho": round(float(rho), 6),
                "p_value": f"{float(pval):.3e}",
                "valid_cells_compared": int(valid_pair.sum()),
                "interpretation": (
                    "rho near 1.0 = rainfall barely reorders the full priority "
                    "ranking (only shifts absolute scores); lower rho = more "
                    "rank reordering."
                ),
            }
        )

    stability_rows = [
        {"metric": "scenario_count", "value": len(scenarios)},
        {"metric": "top20_all_scenarios_cells", "value": int(np.nansum(top20_frequency == 1.0))},
        {"metric": "top20_any_scenario_cells", "value": int(np.nansum(top20_frequency > 0.0))},
        {"metric": "top20_all_scenarios_area_km2", "value": round(float(np.nansum(top20_frequency == 1.0) * CELL_AREA_KM2), 3)},
        {"metric": "top20_any_scenario_area_km2", "value": round(float(np.nansum(top20_frequency > 0.0) * CELL_AREA_KM2), 3)},
        {"metric": "rainfall_score_mean_inside_v1", "value": round(float(np.nanmean(criteria["rainfall_climatology_proxy"])), 6)},
    ]

    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "hotspot_overlap.csv", overlap_rows)
    write_csv(OUT_DIR / "rank_correlation.csv", rank_rows)
    write_csv(OUT_DIR / "hotspot_stability_summary.csv", stability_rows)
    print(f"wrote {BOUNDARY_ID} / {EXPERIMENT_ID} to {rel(OUT_DIR)}")
    v03v02 = overlap_rows[0]
    print(f"v0.3 stable-vs-v0.2 stable: jaccard={v03v02['jaccard']}, retention={v03v02['retention_of_v02']}")
    for row in rank_rows:
        print(f"  {row['scenario']} vs excluded: spearman_rho={row['spearman_rho']}")
    for row in overlap_rows[1:]:
        print(f"  {row['comparison']}: jaccard={row['jaccard']}, retention={row['retention_of_baseline']}")


if __name__ == "__main__":
    main()
