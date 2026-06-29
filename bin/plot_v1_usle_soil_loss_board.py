#!/usr/bin/env python3
"""Deprecated V1 USLE Annual Soil Loss board.

Do not regenerate or send this board. The old R/A products were deprecated after the 2026-06-19
formula audit. Use the verified R-factor send packet instead.

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
    raise SystemExit(
        "DEPRECATED: do not regenerate or send the old V1 USLE A board. "
        "See outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ls, ls_src = read_array(LS)
    c, c_src = read_array(C)
    a, a_src = read_array(A_MEAN)
    cls, cls_src = read_array(A_CLASSES)

    fig, axes = plt.subplots(2, 2, figsize=(13.8, 11.2), constrained_layout=False)
    fig.subplots_adjust(left=0.07, right=0.95, top=0.88, bottom=0.07, wspace=0.23, hspace=0.34)

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
    ax = axes[1, 0]
    a_cap = np.nanpercentile(a, 95)
    im = ax.imshow(a, cmap="YlOrRd", extent=extent(a_src.bounds), origin="upper",
                   vmin=0, vmax=a_cap)
    base_geo(ax, a_src)
    ax.set_title(f"(c) Deprecated annual soil loss A\nOld R product; display capped at p95 = {a_cap:.2f} t/ha/yr", pad=7)
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
    ax.set_title("(d) Deprecated soil-loss severity\nClass thresholds in t/ha/yr", pad=7)
    cbar = fig.colorbar(im, ax=ax, shrink=0.72, ticks=[1, 2, 3, 4, 5])
    cbar.ax.set_yticklabels(["1 very low\n(<1)", "2 low\n(1-5)", "3 moderate\n(5-10)",
                             "4 high\n(10-50)", "5 very high\n(>50)"])

    fig.suptitle(
        "V1 USLE Annual Soil Loss Diagnostic\nDiagnostic data product, not a validated soil-loss map",
        fontsize=13.0, weight="bold", y=0.965,
    )
    fig.text(0.5, 0.025, "See caption for R-factor caveat and scalar assumptions.", ha="center", fontsize=8.0, style="italic", color="#333")

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
        f"- (c) Deprecated annual soil loss A from the old R-factor product.\n"
        f"- (d) Deprecated severity classes from the old R-factor product.\n\n"
        f"**Caveat:** do not use this board for mentor communication. The old V1 R/A outputs are "
        f"deprecated after the 2026-06-19 formula audit. Only the R-invariant structure layer is "
        f"safe as a future re-derivation input.\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
