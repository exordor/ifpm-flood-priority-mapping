#!/usr/bin/env python3
"""Deprecated V1-vs-V2 R-factor comparison board.

Local TOOLING script kept only for provenance. Do not regenerate this board for mentor use:
the 2026-06-19 formula audit showed that the V1 bimodality was an artifact of an invented
Renard-Freimund break point, so the "V2 resolves bimodality" framing is invalid.

Usage:
    .venv/bin/python bin/plot_v2_rfactor_comparison_board.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import json

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]

# R candidates on the 0.05 deg grid (EPSG:4326). rf_lo removed after a literature-integrity check.
R_V1 = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/rasters/rf_v1_bimodal_0p05deg.tif"
R_ARNOLDUS = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/rasters/rf_arnoldus_0p05deg.tif"
R_RF_LOW = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/rasters/rf_rf_low_branch_0p05deg.tif"

# 30 m A rasters.
A_V1_MEAN = ROOT / "outputs/v1_usle_soil_loss/a_mean_30m.tif"
A_V2_ARNOLDUS_SPATIAL = ROOT / "outputs/v1_usle_soil_loss/v2_rfactor/a_v2_rf_arnoldus_spatial_DIAGNOSTIC_30m.tif"
A_STRUCTURE = ROOT / "outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif"
# Diagnostics JSON drives the caption so survival percentages can never drift from the panels.
HOTSPOT_DIAG_JSON = ROOT / "outputs/v1_usle_soil_loss/v2_rfactor/v2_hotspot_survival_diagnostics.json"

V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
OUT_DIR = ROOT / "outputs/v1_usle_soil_loss/v2_rfactor"
BOARD_PNG = OUT_DIR / "mentor_v2_rfactor_comparison_board.png"
BOARD_PDF = OUT_DIR / "mentor_v2_rfactor_comparison_board.pdf"
CAPTION_MD = OUT_DIR / "mentor_v2_rfactor_caption.md"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def load_boundary(crs) -> gpd.GeoDataFrame:
    b = gpd.read_file(V1_GPKG, layer="v1_working_boundary")
    return b.to_crs(crs)


def extent_of(b) -> list[float]:
    return [b.left, b.right, b.bottom, b.top]


def km(v, _p):
    return f"{v/1000:.0f}"


def north(ax):
    ax.annotate("N", xy=(0.08, 0.93), xytext=(0.08, 0.83), xycoords="axes fraction",
                textcoords="axes fraction", ha="center", va="center", fontsize=10, weight="bold",
                arrowprops={"arrowstyle": "-|>", "color": "#222", "linewidth": 1.0})


def scale_bar(ax, km_len=20):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    sx = x0 + 0.07 * (x1 - x0); y = y0 + 0.075 * (y1 - y0); ex = sx + km_len * 1000
    th = 0.012 * (y1 - y0)
    ax.plot([sx, ex], [y, y], color="#222", linewidth=2.0, solid_capstyle="butt", zorder=12)
    ax.plot([sx, sx], [y - th, y + th], color="#222", linewidth=0.9, zorder=12)
    ax.plot([ex, ex], [y - th, y + th], color="#222", linewidth=0.9, zorder=12)
    ax.text((sx + ex) / 2, y + 1.7 * th, f"{km_len} km", ha="center", va="bottom", fontsize=7.8)


def base_geo(ax, src):
    boundary = load_boundary(src.crs)
    boundary.boundary.plot(ax=ax, color="#111", linewidth=0.9, zorder=10)
    # Axis labels differ for geographic (deg) vs projected (km) panels.
    if src.crs.is_geographic:
        ax.set_xlabel("Longitude (deg E)")
        ax.set_ylabel("Latitude (deg N)")
    else:
        ax.set_xlabel("Easting (km, EPSG:32735)")
        ax.set_ylabel("Northing (km, EPSG:32735)")
        ax.xaxis.set_major_formatter(FuncFormatter(km))
        ax.yaxis.set_major_formatter(FuncFormatter(km))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.12, linewidth=0.5)
    north(ax)
    if not src.crs.is_geographic:
        scale_bar(ax)


def read_array(path: Path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64")
        a[a == ds.nodata] = np.nan
        return a, ds


def main() -> None:
    raise SystemExit(
        "DEPRECATED: do not regenerate or send this board. "
        "See outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md "
        "and context/docs/project-management/rfactor_investigation_consolidated.md."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    r_v1, r_v1_src = read_array(R_V1)
    r_ar, r_ar_src = read_array(R_ARNOLDUS)
    r_rfl, r_rfl_src = read_array(R_RF_LOW)
    a_v1, a_v1_src = read_array(A_V1_MEAN)
    a_v2, a_v2_src = read_array(A_V2_ARNOLDUS_SPATIAL)
    a_struct, a_struct_src = read_array(A_STRUCTURE)

    fig, axes = plt.subplots(3, 2, figsize=(13.2, 16.0), constrained_layout=False)
    fig.subplots_adjust(left=0.07, right=0.95, top=0.91, bottom=0.05, wspace=0.23, hspace=0.38)

    # --- Panel (a): V1 bimodal R (0.05 deg) ---
    ax = axes[0, 0]
    im = ax.imshow(r_v1, cmap="viridis", extent=extent_of(r_v1_src.bounds), origin="upper",
                   vmin=np.nanmin(r_v1), vmax=np.nanmax(r_v1))
    base_geo(ax, r_v1_src)
    ax.set_title("(a) Deprecated old V1 R-factor\nDo not use as R evidence", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.78, label="R (MJ mm / ha / h / yr)")

    # --- Panel (b): Arnoldus R (0.05 deg) ---
    ax = axes[0, 1]
    im = ax.imshow(r_ar, cmap="viridis", extent=extent_of(r_ar_src.bounds), origin="upper",
                   vmin=np.nanmin(r_ar), vmax=np.nanmax(r_ar))
    base_geo(ax, r_ar_src)
    ax.set_title("(b) Deprecated V2 R-factor candidate\nDo not use as R evidence", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.78, label="R (MJ mm / ha / h / yr)")

    # --- Panel (c): RF-low-branch R (0.05 deg) ---
    ax = axes[1, 0]
    im = ax.imshow(r_rfl, cmap="viridis", extent=extent_of(r_rfl_src.bounds), origin="upper",
                   vmin=np.nanmin(r_rfl), vmax=np.nanmax(r_rfl))
    base_geo(ax, r_rfl_src)
    ax.set_title("(c) Deprecated V2 R-factor candidate\nDo not use as R evidence", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.78, label="R (MJ mm / ha / h / yr)")

    # --- Panel (d): V1 A-mean (30 m) ---
    ax = axes[1, 1]
    a_cap = np.nanpercentile(a_v1, 95)
    im = ax.imshow(a_v1, cmap="YlOrRd", extent=extent_of(a_v1_src.bounds), origin="upper",
                   vmin=0, vmax=a_cap)
    base_geo(ax, a_v1_src)
    ax.set_title(f"(d) V1 soil loss A (mean R=408)\nDisplay capped at p95={a_cap:.2f} t/ha/yr", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.78, label="A (t / ha / yr)")

    # --- Panel (e): V2 A Arnoldus spatial (30 m) ---
    ax = axes[2, 0]
    a2_cap = np.nanpercentile(a_v2, 95)
    im = ax.imshow(a_v2, cmap="YlOrRd", extent=extent_of(a_v2_src.bounds), origin="upper",
                   vmin=0, vmax=a2_cap)
    base_geo(ax, a_v2_src)
    ax.set_title(f"(e) V2 soil loss A (Arnoldus R, spatial)\nDisplay capped at p95={a2_cap:.2f} t/ha/yr; hotspots survive", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.78, label="A (t / ha / yr)")

    # --- Panel (f): hotspot overlay ---
    # Reference hotspots = a_structure p95 (R-invariant). V2 spatial hotspots = a_v2 p95.
    struct_thr = float(np.nanpercentile(a_struct, 95))
    ref_hot = (a_struct >= struct_thr) & np.isfinite(a_struct)
    v2_thr = float(np.nanpercentile(a_v2, 95))
    v2_hot = (a_v2 >= v2_thr) & np.isfinite(a_v2)
    overlap = ref_hot & v2_hot
    ref_only = ref_hot & ~v2_hot
    v2_only = ~ref_hot & v2_hot

    # Build a 3-value overlay raster: 1=overlap, 2=ref-only, 3=v2-only
    overlay = np.zeros(a_struct.shape, dtype="float64")
    overlay[overlap] = 1
    overlay[ref_only] = 2
    overlay[v2_only] = 3
    overlay[~np.isfinite(a_struct)] = np.nan

    ax = axes[2, 1]
    overlay_colors = ["#ffffff", "#d73027", "#4575b4", "#fee08b"]  # 0 unused, overlap, ref-only, v2-only
    overlay_cmap = ListedColormap(overlay_colors[1:])
    # Show on a light grey base
    base = np.where(np.isfinite(a_struct), 0.0, np.nan)
    ax.imshow(base, cmap="Greys", extent=extent_of(a_struct_src.bounds), origin="upper", vmin=0, vmax=1, alpha=0.5)
    im = ax.imshow(overlay, cmap=overlay_cmap, extent=extent_of(a_struct_src.bounds), origin="upper",
                   vmin=1, vmax=3, interpolation="nearest")
    base_geo(ax, a_struct_src)
    n_ref = int(ref_hot.sum())
    n_overlap = int(overlap.sum())
    surv = n_overlap / n_ref if n_ref else 0.0
    ax.set_title(f"(f) Hotspot survival (Arnoldus)\nOverlap={n_overlap}/{n_ref} cells = {100*surv:.1f}% of R-invariant hotspots survive", pad=7)
    legend_elements = [
        Patch(facecolor="#d73027", edgecolor="none", label="Overlap (both)"),
        Patch(facecolor="#4575b4", edgecolor="none", label="LS$\\times$C$\\times$K only"),
        Patch(facecolor="#fee08b", edgecolor="none", label="Spatial-R only"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="center left",
        bbox_to_anchor=(1.02, 0.50),
        borderaxespad=0.0,
        frameon=True,
        framealpha=0.92,
    )

    fig.suptitle(
        "Deprecated V1/V2 R-Factor Comparison\nDo not send; old R/A products are deprecated",
        fontsize=13.0, weight="bold", y=0.97,
    )

    # Build the caveat from the diagnostics JSON so the survival percentages can never drift from
    # the numbers in panel (f) / the hotspot diagnostics JSON.
    with open(HOTSPOT_DIAG_JSON) as _f:
        _hs = json.load(_f)
    surv = {cid: _hs["candidates"][cid]["hotspot_survival"]["survival_rate"]
            for cid in ["rf_v1_bimodal", "rf_arnoldus", "rf_rf_low_branch"]}
    fig.text(0.5, 0.018, "Diagnostic data product, not a validated soil-loss map. See caption for hotspot-survival caveat.", ha="center", fontsize=8.0, style="italic", color="#333")

    fig.savefig(BOARD_PNG)
    fig.savefig(BOARD_PDF)
    plt.close(fig)
    print(f"wrote {BOARD_PNG}")
    print(f"wrote {BOARD_PDF}")

    CAPTION_MD.write_text(
        f"# V1 vs V2 R-Factor Comparison Board\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        f"**Status: DIAGNOSTIC data product, not a validated soil-loss map.**\n\n"
        f"Six-panel board responding to the 2026-06-16 mentor decision (IFPM-074: keep V1 as "
        f"baseline, switch V2 to a smoother R, test hotspot survival):\n\n"
        f"- (a) Deprecated old V1 R-factor product.\n"
        f"- (b) Deprecated V2 R-factor candidate product.\n"
        f"- (c) Deprecated V2 R-factor candidate product.\n"
        f"- (d) V1 soil loss A (mean R=408): V1 baseline soil loss, display capped at p95.\n"
        f"- (e) V2 soil loss A (Arnoldus R, spatially varying): hotspots in the same steep-slope / "
        f"cropland locations as V1.\n"
        f"- (f) Hotspot survival: overlap of V2 spatial-R hotspots with the R-invariant "
        f"K$\\times$LS$\\times$C hotspots. Survival rates: V1 baseline "
        f"{100*surv['rf_v1_bimodal']:.1f}%, Arnoldus {100*surv['rf_arnoldus']:.1f}%, "
        f"RF low-branch {100*surv['rf_rf_low_branch']:.1f}%.\n\n"
        f"**Current decision:** do not use this board. The 2026-06-19 formula audit deprecated the "
        f"old R/A products and invalidated the old causal framing. The hotspot-overlap values may "
        f"only be revisited later as a separate R-invariant structure check.\n\n"
        f"**Caveats:** (1) absolute A values remain R-method-dependent and the V2 R resample to 30 m "
        f"is diagnostic-only, not pixel-level evidence. (2) The hotspot survival rate is structurally "
        f"biased high (LS dynamic range >> R); it is a weak confirmatory signal, not a quality "
        f"ranking. (3) The final V2 R formula remains a mentor methodological decision. (4) A "
        f"previous \"Lo et al. 1985\" candidate was removed after a literature-integrity check "
        f"(coefficients had no traceable source). See the V2 R-factor processing note.\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
