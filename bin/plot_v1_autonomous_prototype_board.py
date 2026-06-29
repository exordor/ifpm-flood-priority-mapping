#!/usr/bin/env python3
"""Plot a clean V1 autonomous prototype review board."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import BoundaryNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/v1_autonomous_prototype_v0_1"
CRITERIA_DIR = OUT_DIR / "criteria"
SCENARIO_DIR = OUT_DIR / "scenarios"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"

MAPS = [
    ("A. Flood / hydrology", CRITERIA_DIR / "flood_hydrology_0_1.tif", "viridis", 0.0, 1.0, "0-1"),
    ("B. Sediment structure", CRITERIA_DIR / "sediment_structure_0_1.tif", "magma", 0.0, 1.0, "0-1"),
    ("C. Mean priority", OUT_DIR / "priority_mean_0_1.tif", "YlOrRd", 0.0, 1.0, "0-1"),
    ("D. Priority uncertainty", OUT_DIR / "priority_std_0_1.tif", "Purples", 0.0, None, "score SD"),
    ("E. Stable hotspot frequency", OUT_DIR / "top20_frequency_0_1.tif", "Blues", 0.0, 1.0, "0-1"),
]


def read_map(path: Path) -> tuple[np.ndarray, tuple[float, float, float, float], object]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        bounds = src.bounds
        extent = (bounds.left / 1000, bounds.right / 1000, bounds.bottom / 1000, bounds.top / 1000)
        return data, extent, src.crs


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.04)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label(label, fontsize=8)


def add_scale_north(ax) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    bar = 20
    ax.plot([x0 + 0.08 * (x1 - x0), x0 + 0.08 * (x1 - x0) + bar], [y0 + 0.08 * (y1 - y0)] * 2, color="black", lw=2)
    ax.text(x0 + 0.08 * (x1 - x0) + bar / 2, y0 + 0.105 * (y1 - y0), "20 km", ha="center", va="bottom", fontsize=8)
    ax.annotate("N", xy=(x0 + 0.08 * (x1 - x0), y1 - 0.08 * (y1 - y0)), xytext=(x0 + 0.08 * (x1 - x0), y1 - 0.18 * (y1 - y0)),
                arrowprops=dict(arrowstyle="-|>", lw=1.2), ha="center", va="center", fontsize=9)


def plot_map(fig, ax, item, boundary) -> None:
    title, path, cmap, vmin, vmax, label = item
    data, extent, _crs = read_map(path)
    vmax = float(np.nanmax(data)) if vmax is None else vmax
    img = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax)
    boundary.boundary.plot(ax=ax, color="black", linewidth=0.9)
    ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
    ax.set_xlabel("Easting (km, EPSG:32735)", fontsize=8)
    ax.set_ylabel("Northing (km)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(color="0.9", linewidth=0.4)
    add_scale_north(ax)
    add_colorbar(fig, ax, img, label)


def plot_table(ax) -> None:
    ax.axis("off")
    weights = pd.read_csv(OUT_DIR / "scenario_weights.csv")
    summary = pd.read_csv(OUT_DIR / "hotspot_stability_summary.csv")
    pivot = weights.pivot(index="scenario", columns="criterion", values="weight")
    pivot = pivot[["flood_hydrology", "sediment_structure", "landuse_asm_pressure", "environmental_sensitivity", "socioeconomic_exposure"]]
    rows = []
    labels = {
        "equal": "Equal",
        "exposure_heavy": "Exposure",
        "flood_sediment_heavy": "Flood+Sed.",
        "methodology_slide_candidate": "Slide cand.",
    }
    for scenario, values in pivot.iterrows():
        rows.append([labels.get(scenario, scenario), *[f"{v:.2f}" for v in values]])
    cols = ["Scenario", "Flood", "Sed.", "Land/ASM", "Env.", "Socio"]
    table = ax.table(cellText=rows, colLabels=cols, loc="upper center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.35)
    for (row, _col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#e8edf3")
            cell.set_text_props(weight="bold")
    stable = summary[summary["metric"] == "top20_all_scenarios_area_km2"]["value"].iloc[0]
    any_area = summary[summary["metric"] == "top20_any_scenario_area_km2"]["value"].iloc[0]
    ax.set_title("F. Weight scenarios and hotspot stability", loc="left", fontsize=10, fontweight="bold")
    ax.text(0.02, 0.12, f"Top-20% in all scenarios: {stable} km²\nTop-20% in any scenario: {any_area} km²",
            transform=ax.transAxes, fontsize=10, va="bottom")


def main() -> None:
    plt.rcParams.update({"font.family": "DejaVu Serif", "axes.linewidth": 0.8})
    first_data, _extent, crs = read_map(MAPS[0][1])
    del first_data
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(crs)
    boundary["geometry"] = boundary.geometry.scale(xfact=0.001, yfact=0.001, origin=(0, 0))

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    flat = axes.ravel()
    for ax, item in zip(flat[:5], MAPS, strict=True):
        plot_map(fig, ax, item, boundary)
    plot_table(flat[5])
    fig.suptitle("V1 Autonomous Prototype v0.1: provisional criteria and hotspot stability", fontsize=14, fontweight="bold")

    png = OUT_DIR / "v1_autonomous_prototype_board.png"
    pdf = OUT_DIR / "v1_autonomous_prototype_board.pdf"
    fig.savefig(png, dpi=220, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    caption = """# Caption: V1 Autonomous Prototype v0.1

Figure X. Provisional V1 autonomous prototype criteria and hotspot stability. Panels A-B show
selected input criteria, Panels C-E show the mean priority, priority uncertainty, and top-20%
hotspot frequency across four weighting scenarios. Panel F lists the scenario weights and stable
hotspot area. This is a research prototype for sensitivity review only; it is not a validated
flood-risk map or intervention-priority map.
"""
    (OUT_DIR / "v1_autonomous_prototype_caption.md").write_text(caption, encoding="utf-8")
    print(f"wrote {png.relative_to(ROOT)} and {pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
