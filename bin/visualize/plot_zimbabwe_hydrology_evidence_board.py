#!/usr/bin/env python3
"""Plot V1 hydrology candidate evidence board for mentor review (no overlay).

Local TOOLING script. 2x2 board: (a) TWI raw, (b) TWI standardized high-wetness, (c) distance-to-
drainage raw, (d) drainage-proximity standardized. Pairs each raw layer with its 0-1 candidate so
the mentor sees the transformation. All labelled candidate evidence, no overlay/interpretation.

Usage:
    .venv/bin/python bin/visualize/plot_zimbabwe_hydrology_evidence_board.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
TWI = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_twi.tif"
TWI_STD = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization/zimbabwe_twi_high_wetness_0_1.tif"
DIST = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_distance_to_drainage_t500.tif"
DIST_STD = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization/zimbabwe_drainage_proximity_0_1.tif"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
OUT_DIR = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_standardization"
BOARD_PNG = OUT_DIR / "zimbabwe_mentor_hydrology_evidence_board.png"
BOARD_PDF = OUT_DIR / "zimbabwe_mentor_hydrology_evidence_board.pdf"
CAPTION_MD = OUT_DIR / "mentor_v1_hydrology_evidence_caption.md"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 9.5,
    "axes.titlesize": 10.5, "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
})


def read_array(path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64"); a[a == ds.nodata] = np.nan; return a, ds


def base_geo(ax, src):
    b = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(src.crs)
    b.boundary.plot(ax=ax, color="#111", linewidth=0.9)
    ax.set_xlabel("Easting (km, EPSG:32735)"); ax.set_ylabel("Northing (km, EPSG:32735)")
    km = lambda v, _p: f"{v/1000:.0f}"
    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(km)); ax.yaxis.set_major_formatter(FuncFormatter(km))
    ax.set_aspect("equal", adjustable="box"); ax.grid(alpha=0.12, linewidth=0.5)


def extent_of(src):
    return [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    twi, twi_s = read_array(TWI); twi_std, twi_std_s = read_array(TWI_STD)
    dist, dist_s = read_array(DIST); dist_std, dist_std_s = read_array(DIST_STD)

    fig, axes = plt.subplots(2, 2, figsize=(13.6, 11.2), constrained_layout=False)
    fig.subplots_adjust(left=0.07, right=0.95, top=0.88, bottom=0.07, wspace=0.23, hspace=0.34)

    ax = axes[0, 0]
    im = ax.imshow(twi, cmap="viridis", extent=extent_of(twi_s), origin="upper",
                   vmin=np.nanpercentile(twi, 2), vmax=np.nanpercentile(twi, 98))
    base_geo(ax, twi_s)
    ax.set_title("(a) TWI (topographic wetness index)\nln(As/tan(slope)); high = wet/converging areas", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.72, label="TWI (dimensionless)")

    ax = axes[0, 1]
    im = ax.imshow(twi_std, cmap="YlGnBu", extent=extent_of(twi_std_s), origin="upper", vmin=0, vmax=1)
    base_geo(ax, twi_std_s)
    ax.set_title("(b) TWI high-wetness candidate (0-1)\n2-98 percentile clip; high TWI -> higher value", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.72, label="standardized (0-1)")

    ax = axes[1, 0]
    im = ax.imshow(dist, cmap="viridis_r", extent=extent_of(dist_s), origin="upper",
                   vmin=0, vmax=np.nanpercentile(dist, 98))
    base_geo(ax, dist_s)
    ax.set_title("(c) Distance to drainage (t500)\ncloser to streams = more flood exposure", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.72, label="distance (m)")

    ax = axes[1, 1]
    im = ax.imshow(dist_std, cmap="YlGnBu", extent=extent_of(dist_std_s), origin="upper", vmin=0, vmax=1)
    base_geo(ax, dist_std_s)
    ax.set_title("(d) Drainage-proximity candidate (0-1)\ninverted; near-stream -> higher value", pad=7)
    fig.colorbar(im, ax=ax, shrink=0.72, label="standardized (0-1)")

    fig.suptitle("Upper Mzingwane Catchment: Hydrology Candidate Evidence\nTWI and drainage proximity for mentor review",
                 fontsize=13.0, weight="bold", y=0.965)
    fig.text(0.5, 0.025, "Candidate evidence only: no AHP overlay, no flood-risk interpretation.", ha="center", fontsize=8.0, style="italic", color="#333")
    fig.savefig(BOARD_PNG); fig.savefig(BOARD_PDF); plt.close(fig)
    print(f"wrote {BOARD_PNG}"); print(f"wrote {BOARD_PDF}")

    CAPTION_MD.write_text(
        f"# V1 hydrology candidate evidence\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        f"**Status: CANDIDATE EVIDENCE for mentor review - not a flood-risk criterion, no overlay.**\n\n"
        f"Two hydrology candidates standardized to 0-1, using the same method as the terrain "
        f"candidates:\n"
        f"- (a/b) TWI high-wetness: high topographic wetness index = wet, flat, converging areas "
        f"(flood-susceptible).\n"
        f"- (c/d) Drainage-proximity: closer to streams = more flood exposure (inverted).\n\n"
        f"Both pass the V1 raster grid gate (grid_compatible=true). Not overlay-ready: pending "
        f"mentor criteria-hierarchy and modelling-unit decisions.\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
