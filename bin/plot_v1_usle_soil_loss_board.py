#!/usr/bin/env python3
"""Create a mentor-facing V1 USLE Annual Soil Loss diagnostic figure board.

Local TOOLING script. Produces a 2x2 PNG board: LS-factor, C-factor, A-mean soil loss, and
severity classes. Clearly framed as a DIAGNOSTIC (not validated). Flags the R-factor bimodality
so the mentor reads absolute A values with the right caution.

Usage:
    .venv/bin/python bin/plot_v1_usle_soil_loss_board.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
LS = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor/v1_ls_factor_capped50_hillslope_30m.tif"
C = ROOT / "outputs/esa_worldcover_2021_v1_methodology/c_factor/c_factor_v1_30m.tif"
A_MEAN = ROOT / "outputs/v1_usle_soil_loss/a_mean_30m.tif"
A_CLASSES = ROOT / "outputs/v1_usle_soil_loss/a_mean_classes_30m.tif"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
OUT_DIR = ROOT / "outputs/v1_usle_soil_loss"
BOARD_PNG = OUT_DIR / "mentor_v1_usle_soil_loss_board.png"
BOARD_PDF = OUT_DIR / "mentor_v1_usle_soil_loss_board.pdf"
CAPTION_MD = OUT_DIR / "mentor_v1_usle_soil_loss_caption.md"

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


def extent(b) -> list[float]:
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
    ax.set_xlabel("Easting (km, EPSG:32735)")
    ax.set_ylabel("Northing (km, EPSG:32735)")
    ax.xaxis.set_major_formatter(FuncFormatter(km))
    ax.yaxis.set_major_formatter(FuncFormatter(km))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.12, linewidth=0.5)
    north(ax); scale_bar(ax)


def read_array(path: Path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64")
        a[a == ds.nodata] = np.nan
        return a, ds


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ls, ls_src = read_array(LS)
    c, c_src = read_array(C)
    a, a_src = read_array(A_MEAN)
    cls, cls_src = read_array(A_CLASSES)

    fig, axes = plt.subplots(2, 2, figsize=(13.6, 11.4), constrained_layout=True)

    # Panel A: LS-factor
    ax = axes[0, 0]
    im = ax.imshow(ls, cmap="cividis", extent=extent(ls_src.bounds), origin="upper",
                   vmin=0, vmax=np.nanpercentile(ls, 98))
    base_geo(ax, ls_src)
    ax.set_title("(a) LS-factor (hillslope, capped 50)\nMoore & Nieber 1989; channel cells masked", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.72, label="LS (dimensionless)")

    # Panel B: C-factor
    ax = axes[0, 1]
    im = ax.imshow(c, cmap="YlGn_r", extent=extent(c_src.bounds), origin="upper",
                   vmin=0, vmax=0.7)
    base_geo(ax, c_src)
    ax.set_title("(b) C-factor (cover management)\nESA WorldCover 2021 lookup", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.72, label="C (dimensionless)")

    # Panel C: A-mean soil loss (display capped at p95 for visibility)
    ax = axes[0, 1]  # placeholder reassignment below
    ax = axes[1, 0]
    a_cap = np.nanpercentile(a, 95)
    im = ax.imshow(a, cmap="YlOrRd", extent=extent(a_src.bounds), origin="upper",
                   vmin=0, vmax=a_cap)
    base_geo(ax, a_src)
    ax.set_title(f"(c) Annual soil loss A (mean R = 408)\n$A = R \\cdot K \\cdot LS \\cdot C \\cdot P$; display capped at p95 = {a_cap:.2f} t/ha/yr", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.72, label="A (t / ha / yr)")

    # Panel D: severity classes
    ax = axes[1, 1]
    cls_colors = ["#f7f7f7", "#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027"]
    cls_cmap = ListedColormap(cls_colors)
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = BoundaryNorm(bounds, cls_cmap.N)
    cls_show = np.where(np.isfinite(cls), cls, np.nan)
    im = ax.imshow(cls_show, cmap=cls_cmap, norm=norm, extent=extent(cls_src.bounds), origin="upper",
                   interpolation="nearest")
    base_geo(ax, cls_src)
    ax.set_title("(d) Soil-loss severity (mean R)\nClass thresholds in t/ha/yr", pad=7)
    cbar = fig.colorbar(im, ax=ax, shrink=0.72, ticks=[1, 2, 3, 4, 5])
    cbar.ax.set_yticklabels(["1 very low\n(<1)", "2 low\n(1-5)", "3 moderate\n(5-10)",
                             "4 high\n(10-50)", "5 very high\n(>50)"])

    # shared legend
    axes[0, 0].legend(
        handles=[Line2D([0], [0], color="#111", linewidth=1.0, label="V1 working boundary")],
        loc="lower right", frameon=True, framealpha=0.92,
    )

    fig.suptitle(
        "V1 USLE Annual Soil Loss Diagnostic  |  R$\\times$K$\\times$LS$\\times$C$\\times$P\n"
        "DIAGNOSTIC DATA PRODUCT - not a validated soil-loss map",
        fontsize=12.5, weight="bold", y=1.0,
    )

    # caveat text below the board
    caveat = (
        "Scalars: K$_{SI}$=0.0223 (V1 mean, SoilGrids 250m), R$_{mean}$=408 (V1 mean, CHIRPS modified Fournier), P=1.   "
        "R is bimodal (MFI=80 discontinuity): A$_{low(R=50)}$=0.06, A$_{high(R=510)}$=0.63 t/ha/yr mean.\n"
        "Absolute A depends on the R method (needs review); spatial structure (LS$\\times$C$\\times$K) is trustworthy. "
        "K and R are zonal scalars here; spatial variation masked."
    )
    fig.text(0.5, -0.012, caveat, ha="center", va="top", fontsize=8.0, style="italic", color="#333")

    fig.savefig(BOARD_PNG)
    fig.savefig(BOARD_PDF)
    plt.close(fig)
    print(f"wrote {BOARD_PNG}")
    print(f"wrote {BOARD_PDF}")

    CAPTION_MD.write_text(
        f"# V1 USLE Annual Soil Loss Diagnostic\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        f"**Status: DIAGNOSTIC data product, not a validated soil-loss map.**\n\n"
        f"Four-panel board:\n"
        f"- (a) LS-factor (hillslope, channel-masked, capped 50): mean 1.563, p95 5.511.\n"
        f"- (b) C-factor (ESA WorldCover 2021 lookup): V1 mean 0.0429.\n"
        f"- (c) Annual soil loss A with mean R=408: V1 mean 0.50 t/ha/yr; display capped at p95 for visibility.\n"
        f"- (d) Severity classes: ~87% of V1 is very-low (<1 t/ha/yr); hotspots where steep slopes meet cropland/bare ground.\n\n"
        f"**Scalars (V1 zonal means):** K$_{{SI}}$=0.0223, R$_{{mean}}$=408 (bimodal: low~50, high~510), P=1.\n\n"
        f"**Caveat:** the V1 R-factor is bimodal due to the Renard-Freimund MFI=80 discontinuity. "
        f"Absolute A values depend on the R method and need mentor review; the spatial structure "
        f"(driven by LS and C) is trustworthy. K and R are kept as zonal scalars (coarse-to-fine "
        f"resampling is forbidden), so their spatial variation is masked in this 30 m map.\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
