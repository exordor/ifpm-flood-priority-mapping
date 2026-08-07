#!/usr/bin/env python3
"""Compare the two parallel Peru no-mining baselines: v02 (old top weights)
vs v07 (Supervisor full spec).

Produces a mentor-facing side-by-side figure and a small comparison table:
priority maps, quintile overlap, area-by-class, and the rank-correlation of
the two PIM surfaces. The figure is the primary artifact for the mentor
review; the CSV is the audit trail.

Reads:
  v02: outputs/srtm_1arcsec_peru_pilot/pim_versions/02_no_mining_test_baseline/
       priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif
  v07: outputs/srtm_1arcsec_peru_pilot/pim_versions/07_supervisor_spec_full_weights/
       scenarios/priority_supervisor_spec_pim.tif

Writes:
  outputs/srtm_1arcsec_peru_pilot/pim_versions/comparison_v02_v07/
    parallel_baselines_comparison.png / .pdf
    parallel_baselines_comparison.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
from rasterio.transform import array_bounds
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))
import importlib.util  # noqa: E402

# Reuse write_csv from the canonical baseline runner to avoid duplication.
_base_path = ROOT / "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py"
_spec = importlib.util.spec_from_file_location("peru_baseline_runner", _base_path)
_base = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules[_spec.name] = _base  # type: ignore[index]
_spec.loader.exec_module(_base)  # type: ignore[union-attr]
write_csv = _base.write_csv

V02_PIM = ROOT / "outputs/srtm_1arcsec_peru_pilot/pim_versions/02_no_mining_test_baseline/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif"
V07_PIM = ROOT / "outputs/srtm_1arcsec_peru_pilot/pim_versions/07_supervisor_spec_full_weights/scenarios/priority_supervisor_spec_pim.tif"
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
OUT_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/pim_versions/comparison_v02_v07"

V02_LABEL = "v02 — retained test weights\nFH .35 SE .25 LU .20 ES .12 SV .08"
V07_LABEL = "v07 — Supervisor full spec\nFH .34 SE .25 LU .17 ES .10 SV .14"

CLASS_BOUNDS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
CLASS_LABELS = ["Very low", "Low", "Moderate", "High", "Very high"]
CMAP = ListedColormap(["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"])
NORM = BoundaryNorm(CLASS_BOUNDS, CMAP.N)


def read_band(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        return src.read(1).astype("float32"), src.profile.copy()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    v02, profile = read_band(V02_PIM)
    v07, _ = read_band(V07_PIM)
    v02[v02 == profile.get("nodata", -9999.0)] = np.nan
    v07[v07 == profile.get("nodata", -9999.0)] = np.nan

    valid = np.isfinite(v02) & np.isfinite(v07)
    boundary_mask = valid.copy()  # both surfaces already masked to boundary upstream

    # --- rank correlation on the common support ---
    rho, pval = spearmanr(v02[valid], v07[valid])

    # --- top-20% overlap (Jaccard) ---
    t02 = float(np.nanpercentile(v02, 80))
    t07 = float(np.nanpercentile(v07, 80))
    top02 = valid & (v02 >= t02)
    top07 = valid & (v07 >= t07)
    union = top02 | top07
    intersection = top02 & top07
    jaccard = float(intersection.sum() / union.sum()) if union.any() else float("nan")

    # --- area by class for each surface ---
    cell_km2 = abs(profile["transform"][0]) * abs(profile["transform"][4]) / 1e6
    class_rows = []
    for i, label in enumerate(CLASS_LABELS):
        lo, hi = CLASS_BOUNDS[i], CLASS_BOUNDS[i + 1]
        in_v02 = valid & (v02 >= lo) & (v02 < hi) if i < 4 else valid & (v02 >= lo) & (v02 <= hi)
        in_v07 = valid & (v07 >= lo) & (v07 < hi) if i < 4 else valid & (v07 >= lo) & (v07 <= hi)
        class_rows.append({
            "priority_class": label,
            "v02_area_km2": round(float(in_v02.sum() * cell_km2), 2),
            "v07_area_km2": round(float(in_v07.sum() * cell_km2), 2),
            "v02_fraction": round(float(in_v02.sum() / valid.sum()), 4),
            "v07_fraction": round(float(in_v07.sum() / valid.sum()), 4),
        })

    summary_rows = [{
        "metric": "common_support_cells", "value": int(valid.sum()),
    }, {
        "metric": "spearman_rho_v02_v07", "value": round(float(rho), 4),
    }, {
        "metric": "spearman_pvalue", "value": float(pval),
    }, {
        "metric": "v02_top20_threshold", "value": round(t02, 6),
    }, {
        "metric": "v07_top20_threshold", "value": round(t07, 6),
    }, {
        "metric": "top20_jaccard", "value": round(jaccard, 4),
    }, {
        "metric": "top20_intersection_km2", "value": round(float(intersection.sum() * cell_km2), 2),
    }, {
        "metric": "top20_union_km2", "value": round(float(union.sum() * cell_km2), 2),
    }, {
        "metric": "v02_mean", "value": round(float(np.nanmean(v02)), 4),
    }, {
        "metric": "v07_mean", "value": round(float(np.nanmean(v07)), 4),
    }]
    write_csv(OUT_DIR / "parallel_baselines_comparison.csv", summary_rows + [{"metric": "", "value": ""}] + class_rows)

    # --- figure: two priority maps + agreement map + weight comparison ---
    west, south, east, north = array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (west, east, south, north)
    boundary = gpd.read_file(BOUNDARY, layer="peru_pilot_boundary").to_crs(profile["crs"])
    km_formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")

    fig = plt.figure(figsize=(15, 13))
    # 2x2 grid: top row = two priority maps, bottom-left = agreement, bottom-right = weights
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.22, wspace=0.18)
    ax_v02 = fig.add_subplot(gs[0, 0])
    ax_v07 = fig.add_subplot(gs[0, 1])
    ax_agree = fig.add_subplot(gs[1, 0])
    ax_weights = fig.add_subplot(gs[1, 1])

    def style_map_ax(ax, data, title):
        ax.imshow(np.ma.masked_invalid(data), cmap=CMAP, norm=NORM, extent=extent, origin="upper")
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.8)
        ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32718)", fontsize=8.5)
        ax.set_ylabel("Northing (km)", fontsize=8.5)
        ax.xaxis.set_major_formatter(km_formatter)
        ax.yaxis.set_major_formatter(km_formatter)
        ax.tick_params(labelsize=7.5)
        ax.set_aspect("equal")
        ax.grid(color="0.9", linewidth=0.3)

    style_map_ax(ax_v02, v02, "A. v02 — retained test weights")
    style_map_ax(ax_v07, v07, "B. v07 — Supervisor full spec")

    # annotate each priority map with its top-20% area
    ax_v02.text(0.02, 0.98, f"top-20% area = {(top02.sum()*cell_km2):.0f} km²", transform=ax_v02.transAxes,
                fontsize=8, va="top", ha="left", bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85, edgecolor="0.7"))
    ax_v07.text(0.02, 0.98, f"top-20% area = {(top07.sum()*cell_km2):.0f} km²", transform=ax_v07.transAxes,
                fontsize=8, va="top", ha="left", bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85, edgecolor="0.7"))

    # agreement map
    agree = np.full(v02.shape, np.nan, dtype="float32")
    agree[intersection] = 1.0
    agree[top02 & ~top07] = 0.6
    agree[top07 & ~top02] = 0.3
    ax_agree.imshow(np.ma.masked_invalid(agree), cmap=ListedColormap(["#fdd0a2", "#756bb1", "#31a354"]),
                    norm=BoundaryNorm([0.0, 0.45, 0.75, 1.05], 3), extent=extent, origin="upper")
    boundary.boundary.plot(ax=ax_agree, color="black", linewidth=0.8)
    ax_agree.set_title(f"C. Top-20% agreement (Jaccard = {jaccard:.2f})", loc="left", fontsize=10.5, fontweight="bold")
    ax_agree.set_xlabel("Easting (km, EPSG:32718)", fontsize=8.5)
    ax_agree.set_ylabel("Northing (km)", fontsize=8.5)
    ax_agree.xaxis.set_major_formatter(km_formatter)
    ax_agree.yaxis.set_major_formatter(km_formatter)
    ax_agree.tick_params(labelsize=7.5)
    ax_agree.set_aspect("equal")
    ax_agree.grid(color="0.9", linewidth=0.3)
    ax_agree.legend(handles=[
        Patch(facecolor="#31a354", label=f"Both ({intersection.sum()*cell_km2:.0f} km²)"),
        Patch(facecolor="#756bb1", label=f"Only v02 ({(top02 & ~top07).sum()*cell_km2:.0f} km²)"),
        Patch(facecolor="#fdd0a2", label=f"Only v07 ({(top07 & ~top02).sum()*cell_km2:.0f} km²)"),
    ], loc="lower left", frameon=True, fontsize=8)

    # weight comparison bar chart
    criteria_order = ["FH", "SE", "LU", "ES", "SV"]
    v02_w = [0.35, 0.25, 0.20, 0.12, 0.08]
    v07_w = [0.34, 0.25, 0.17, 0.10, 0.14]
    x = np.arange(len(criteria_order))
    width = 0.36
    bars_v02 = ax_weights.bar(x - width / 2, v02_w, width, label="v02 (retained)", color="#9ecae1", edgecolor="0.4", linewidth=0.5)
    bars_v07 = ax_weights.bar(x + width / 2, v07_w, width, label="v07 (Supervisor)", color="#fdae6b", edgecolor="0.4", linewidth=0.5)
    for bar, val in zip(list(bars_v02) + list(bars_v07), v02_w + v07_w):
        ax_weights.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.006, f"{val:.2f}",
                        ha="center", va="bottom", fontsize=7.5)
    ax_weights.set_xticks(x)
    ax_weights.set_xticklabels(criteria_order, fontsize=9)
    ax_weights.set_ylabel("Top-level weight", fontsize=9)
    ax_weights.set_title("D. Weight comparison", loc="left", fontsize=10.5, fontweight="bold")
    ax_weights.set_ylim(0, 0.42)
    ax_weights.legend(fontsize=8, loc="upper right")
    ax_weights.grid(axis="y", color="0.9", linewidth=0.4)
    ax_weights.tick_params(labelsize=7.5)
    # annotate the two biggest shifts
    ax_weights.annotate("LU −0.03", xy=(2 - width / 2, 0.20), xytext=(2 - width / 2, 0.30),
                        fontsize=7.5, ha="center", color="#08519c",
                        arrowprops=dict(arrowstyle="->", color="#08519c", lw=0.8))
    ax_weights.annotate("SV +0.06", xy=(4 + width / 2, 0.14), xytext=(4 + width / 2, 0.26),
                        fontsize=7.5, ha="center", color="#e6550d",
                        arrowprops=dict(arrowstyle="->", color="#e6550d", lw=0.8))

    # shared colorbar for the two priority maps
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=NORM)
    sm.set_array([])
    cax = fig.add_axes([0.30, 0.935, 0.40, 0.018])
    cbar = fig.colorbar(sm, cax=cax, ticks=[0.1, 0.3, 0.5, 0.7, 0.9], orientation="horizontal")
    cbar.ax.set_xticklabels(CLASS_LABELS, fontsize=8)

    fig.suptitle(
        "Peru Arequipa Region — two parallel no-mining baselines\n"
        f"Rank correlation ρ = {rho:.3f}   ·   top-20% Jaccard = {jaccard:.2f}   ·   "
        f"v02 mean = {np.nanmean(v02):.3f}, v07 mean = {np.nanmean(v07):.3f}",
        fontsize=12.5, fontweight="bold", y=0.985,
    )
    fig.text(0.5, 0.005, "Provisional sensitivity scenario — not a final flood-risk or rescue-decision result. NoData is transparent.",
             ha="center", fontsize=7.5, color="0.4")
    fig.savefig(OUT_DIR / "parallel_baselines_comparison.png", dpi=200, bbox_inches="tight")
    fig.savefig(OUT_DIR / "parallel_baselines_comparison.pdf", bbox_inches="tight")
    plt.close(fig)

    print(f"wrote comparison to {OUT_DIR}")
    print(f"  Spearman rho: {rho:.4f}")
    print(f"  top-20% Jaccard: {jaccard:.4f}")
    print(f"  v02 mean: {np.nanmean(v02):.4f} | v07 mean: {np.nanmean(v07):.4f}")


if __name__ == "__main__":
    main()
