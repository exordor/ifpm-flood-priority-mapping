#!/usr/bin/env python3
"""Create the active Secocha PIM overview using the established Peru palettes."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios"
PRIORITY = BASE / "scenarios/priority_secocha_direct_pim.tif"
CRITERIA_DIR = BASE / "pim_criteria"
MINING = ROOT / "data/raw/ingemmet_catastro_minero_peru_secocha/secocha_pequena_mineria.gpkg"
ANCHORS = ROOT / "outputs/secocha_2023_validation/ingemmet_field_anchors.geojson"

spec = importlib.util.spec_from_file_location("palettes", ROOT / "bin/visualize/plot_goslar_pim_overview.py")
palettes = importlib.util.module_from_spec(spec); spec.loader.exec_module(palettes)
PRIORITY_COLORS = palettes.PRIORITY_COLORS
CRITERIA_COLORS = palettes.CRITERIA_COLORS
BOUNDS = palettes.PRIORITY_BOUNDS
LABELS = palettes.CLASS_LABELS

LABEL_MAP = {
    "flood_hazard": "Flood-conditioning indicator (FH)",
    "sediment": "Sediment / erosion score (SE)",
    "landuse_asm": "Land-use pressure score (LU)",
    "environmental": "Environmental context indicator (ES)",
    "socioeconomic": "Socioeconomic exposure indicator (SV)",
}


def read(path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32"); profile = src.profile
    if profile.get("nodata") is not None:
        arr[arr == profile["nodata"]] = np.nan
    return arr, profile


def draw(ax, arr, colors, title):
    classes = np.zeros(arr.shape, dtype="uint8")
    valid = np.isfinite(arr)
    for i, (lo, hi) in enumerate(zip(BOUNDS[:-1], BOUNDS[1:]), 1):
        classes[valid & (arr >= lo) & (arr < hi)] = i
    classes[valid & (arr >= 1.0)] = 5
    image = ax.imshow(np.ma.masked_where(classes == 0, classes), cmap=ListedColormap(colors),
                      norm=BoundaryNorm(np.arange(.5, 6.5), 5), origin="upper", interpolation="nearest")
    ax.set_title(title, fontsize=11.5, fontweight="bold"); ax.set_xticks([]); ax.set_yticks([])
    cbar = ax.figure.colorbar(image, ax=ax, fraction=.045, pad=.03)
    cbar.set_ticks(range(1, 6)); cbar.set_ticklabels(LABELS); cbar.ax.tick_params(labelsize=7)


def main():
    priority, profile = read(PRIORITY)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9.5), facecolor="white")
    draw(axes[0, 0], priority, PRIORITY_COLORS, "Relative priority index")
    for ax, key in zip(axes.flat[1:], LABEL_MAP):
        arr, _ = read(CRITERIA_DIR / f"{key}_0_1.tif")
        draw(ax, arr, CRITERIA_COLORS[key], LABEL_MAP[key])

    # The external mining overlay and report anchors appear only on the result panel.
    result_ax = axes[0, 0]
    transform = profile["transform"]
    def pixel_xy(gdf):
        pts = gdf.to_crs(profile["crs"]).geometry
        xs = [(p.x - transform.c) / transform.a for p in pts]
        ys = [(p.y - transform.f) / transform.e for p in pts]
        return xs, ys
    if MINING.exists():
        mines = gpd.read_file(MINING)
        if len(mines):
            x, y = pixel_xy(mines[mines.geometry.notna()])
            result_ax.scatter(x, y, s=18, marker="^", c="#54278f", edgecolors="white", linewidths=.35,
                              label="Mining records (external overlay)")
    if ANCHORS.exists():
        anchors = gpd.read_file(ANCHORS)
        if len(anchors):
            x, y = pixel_xy(anchors[anchors.geometry.notna()])
            result_ax.scatter(x, y, s=32, marker="o", facecolors="none", edgecolors="#00ffff", linewidths=1.2,
                              label="INGEMMET field anchors")
    # Context records outside the active map frame must not change the raster
    # panel extent; they remain available in the QGIS project for inspection.
    result_ax.set_xlim(-0.5, priority.shape[1] - 0.5)
    result_ax.set_ylim(priority.shape[0] - 0.5, -0.5)
    handles, labels = result_ax.get_legend_handles_labels()
    if handles:
        result_ax.legend(handles, labels, loc="lower left", fontsize=7, framealpha=.88)

    fig.suptitle("Secocha active Peru study area — historical-hazard validation prototype",
                 x=.045, y=.985, ha="left", fontsize=17, fontweight="bold")
    fig.text(.045, .945,
             "Unchanged Supervisor v07 weights. Mining records are shown only as an external overlay; they do not enter the score.",
             fontsize=10, color="#444444")
    fig.text(.045, .015,
             "Provisional prototype — the working boundary is the A7367 Map 7 coordinate frame, not an event footprint or catchment. UTM 18S, 30 m overlay grid.",
             fontsize=8.5, color="#555555")
    fig.subplots_adjust(top=.90, bottom=.07, left=.04, right=.985, hspace=.28, wspace=.13)
    out_dir = BASE / "figures"; out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "secocha_pim_overview.png"; svg = out_dir / "secocha_pim_overview.svg"
    fig.savefig(png, dpi=200, bbox_inches="tight", facecolor="white")
    fig.savefig(svg, bbox_inches="tight", facecolor="white"); plt.close(fig)
    manifest = {
        "figure_id": "secocha_pim_overview", "boundary_id": "peru_secocha_a7367_reference_extent_v1",
        "claim_level": "provisional", "weights_changed": False,
        "mining_role": "external overlay only", "classification": "equal interval 0-1, five classes",
        "color_palettes": {"priority": PRIORITY_COLORS, **CRITERIA_COLORS},
        "outputs": [png.name, svg.name],
    }
    (out_dir / "secocha_pim_overview_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
