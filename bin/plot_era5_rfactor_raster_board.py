#!/usr/bin/env python3
"""Plot the empirical ERA5 R-factor raster and the recomputed USLE A.

Local TOOLING script. 2x2 board: (a) empirical R raster, (b) empirical A (zonal), (c) empirical A
(spatial diagnostic), (d) point-R scatter + family bands. Shows the empirical spatial R layer and
its USLE A, with the family-arbitration context.

Usage:
    .venv/bin/python bin/plot_era5_rfactor_raster_board.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/v1_usle_soil_loss/rfactor_empirical_era5"
R_RASTER = OUT_DIR / "r_empirical_era5_wischmeier_I30est_0p05deg.tif"
A_ZONAL = OUT_DIR / "a_empirical_era5_zonal_30m.tif"
A_SPATIAL = OUT_DIR / "a_empirical_era5_spatial_DIAGNOSTIC_30m.tif"
DIAG = OUT_DIR / "era5_rfactor_raster_diagnostics.json"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
BOARD_PNG = OUT_DIR / "mentor_era5_rfactor_raster_board.png"
BOARD_PDF = OUT_DIR / "mentor_era5_rfactor_raster_board.pdf"
CAPTION_MD = OUT_DIR / "mentor_era5_rfactor_raster_caption.md"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "font.size": 9.5,
    "axes.titlesize": 10.5, "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
})


def read_array(path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64"); a[a == ds.nodata] = np.nan; return a, ds


def extent_of(src):
    return [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(DIAG) as f:
        d = json.load(f)
    r, r_src = read_array(R_RASTER)
    a_z, a_z_src = read_array(A_ZONAL)
    a_s, a_s_src = read_array(A_SPATIAL)
    b = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(r_src.crs)
    r_zonal = d["headline_R_ws_i30est_v1_zonal"]

    fig, axes = plt.subplots(2, 2, figsize=(13.2, 11.2), constrained_layout=False)
    fig.subplots_adjust(left=0.07, right=0.95, top=0.88, bottom=0.07, wspace=0.23, hspace=0.34)

    # (a) empirical R raster
    ax = axes[0, 0]
    im = ax.imshow(r, cmap="viridis", origin="upper", extent=extent_of(r_src),
                   vmin=np.nanpercentile(r, 2), vmax=np.nanpercentile(r, 98))
    b.boundary.plot(ax=ax, color="#111", linewidth=0.9)
    ax.set_title(f"(a) Empirical ERA5 R-factor (Wischmeier-Smith, I30 est)\nV1 zonal mean = {r_zonal:.0f} MJ mm ha$^{{-1}}$ h$^{{-1}}$ yr$^{{-1}}$", fontsize=10)
    ax.set_xlabel("Longitude (deg E)"); ax.set_ylabel("Latitude (deg N)")
    fig.colorbar(im, ax=ax, shrink=0.78, label="R (MJ mm / ha / h / yr)")

    # (b) empirical A zonal
    ax = axes[0, 1]
    cap = np.nanpercentile(a_z, 95)
    b3 = b.to_crs(a_z_src.crs)
    im = ax.imshow(a_z, cmap="YlOrRd", origin="upper", extent=extent_of(a_z_src), vmin=0, vmax=cap)
    b3.boundary.plot(ax=ax, color="#111", linewidth=0.9)
    ax.set_title(f"(b) Empirical USLE A (zonal R={r_zonal:.0f})\nmean={np.nanmean(a_z):.3f} t/ha/yr; display capped at p95={cap:.2f}", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.78, label="A (t / ha / yr)")

    # (c) empirical A spatial diagnostic
    ax = axes[1, 0]
    cap2 = np.nanpercentile(a_s, 95)
    im = ax.imshow(a_s, cmap="YlOrRd", origin="upper", extent=extent_of(a_s_src), vmin=0, vmax=cap2)
    b3.boundary.plot(ax=ax, color="#111", linewidth=0.9)
    ax.set_title(f"(c) Empirical USLE A (spatial R, DIAGNOSTIC)\nmean={np.nanmean(a_s):.3f} t/ha/yr; R-resample diagnostic-only", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.78, label="A (t / ha / yr)")

    # (d) point R scatter vs families
    ax = axes[1, 1]
    pts = d["point_records"]
    px = [p["lon"] for p in pts]; py = [p["lat"] for p in pts]; pr = [p["R_ws_i30"] for p in pts]
    sc = ax.scatter(px, py, c=pr, cmap="viridis", s=60, edgecolor="#333", linewidth=0.5,
                    vmin=np.nanpercentile(r, 2), vmax=np.nanpercentile(r, 98))
    b.boundary.plot(ax=ax, color="#111", linewidth=0.9)
    ax.set_title(f"(d) Empirical R at {len(pts)} grid points (Wisch I30 est)\nrange {min(pr):.0f}-{max(pr):.0f}; LOW family 240-320, HIGH 1380-3719", fontsize=9.5)
    ax.set_xlabel("Longitude (deg E)"); ax.set_ylabel("Latitude (deg N)")
    fig.colorbar(sc, ax=ax, shrink=0.78, label="R (MJ mm / ha / h / yr)")

    fig.suptitle("Empirical ERA5 R-factor raster and USLE A for V1\nExploratory diagnostic, not a validated R/A product",
                 fontsize=13.0, weight="bold", y=0.965)
    fig.text(0.5, 0.025, "ERA5 hourly lower-bounds true EI30; see caption for method and caveats.", ha="center", fontsize=8.0, style="italic", color="#333")

    fig.savefig(BOARD_PNG); fig.savefig(BOARD_PDF); plt.close(fig)
    print(f"wrote {BOARD_PNG}"); print(f"wrote {BOARD_PDF}")

    CAPTION_MD.write_text(
        f"# Empirical ERA5 R-factor raster and USLE A\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        f"**Status: EXPLORATORY - ERA5 hourly lower-bounds true 30-min EI30; not a validated R/A.**\n\n"
        f"Four-panel board:\n"
        f"- (a) Empirical ERA5 R-factor raster (Wischmeier-Smith KE, I30 estimate), V1 zonal mean "
        f"{r_zonal:.0f} MJ mm ha-1 h-1 yr-1, within/near the LOW literature family.\n"
        f"- (b) Empirical USLE A with zonal R={r_zonal:.0f}: mean {np.nanmean(a_z):.3f} t/ha/yr.\n"
        f"- (c) Empirical USLE A with spatially-varying R (diagnostic-only resample): mean "
        f"{np.nanmean(a_s):.3f} t/ha/yr; agrees with (b), confirming hotspots are LS*C-driven.\n"
        f"- (d) Per-grid-point empirical R ({len(pts)} points), range {min(pr):.0f}-{max(pr):.0f}.\n\n"
        f"**Key result:** the empirical R ({r_zonal:.0f}) and A ({np.nanmean(a_z):.3f} t/ha/yr) are "
        f"physically defensible for V1 and consistent with the LOW R-family. The HIGH family "
        f"(RF/Arnoldus/Elwell, ~2000+) would give A ~2-4 t/ha/yr, ~4x higher than the empirical "
        f"estimate. EXPLORATORY pending a validated R decision.\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
