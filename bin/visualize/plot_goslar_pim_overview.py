#!/usr/bin/env python3
"""Plot the Goslar PIM overview: priority map plus five criteria panels."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios"
PRIORITY = OUT_DIR / "scenarios/priority_goslar_direct_pim.tif"
CRITERIA = {
    "flood_hazard": "Flood-conditioning indicator (FH)",
    "sediment": "Sediment / erosion score",
    "landuse_asm": "General land-use pressure score",
    "environmental": "Environmental context indicator (ES)",
    "socioeconomic": "Socioeconomic exposure indicator",
}
CRITERIA_DIR = OUT_DIR / "pim_criteria"

# Peru-compatible discrete five-class ColorBrewer palettes (same as
# bin/visualize/export_peru_pim_criteria_maps.py and
# bin/visualize/export_paper_style_single_maps.py).
PRIORITY_COLORS = ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"]
CRITERIA_COLORS = {
    "flood_hazard": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "sediment": ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
    "landuse_asm": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "environmental": ["#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"],
    "socioeconomic": ["#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"],
}
PRIORITY_BOUNDS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.000001]
CLASS_LABELS = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]


def read(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        profile = src.profile
    data[data == profile["nodata"]] = np.nan
    return data, profile


def classify_equal_interval(data: np.ndarray) -> np.ndarray:
    classes = np.zeros(data.shape, dtype="uint8")
    valid = np.isfinite(data)
    for index in range(len(PRIORITY_BOUNDS) - 1):
        low, high = PRIORITY_BOUNDS[index], PRIORITY_BOUNDS[index + 1]
        classes[valid & (data >= low) & (data < high)] = index + 1
    classes[valid & (data >= PRIORITY_BOUNDS[-1] - 1e-6)] = len(PRIORITY_BOUNDS) - 1
    return classes


def show_class(ax, data: np.ndarray, colors: list[str], title: str) -> None:
    classes = classify_equal_interval(data)
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(0.5, len(colors) + 1.5), len(colors))
    masked = np.ma.masked_where(classes == 0, classes)
    im = ax.imshow(masked, cmap=cmap, norm=norm, interpolation="nearest", origin="upper")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xticks([]); ax.set_yticks([])
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    cbar.set_ticks(np.arange(1, len(colors) + 1))
    cbar.set_ticklabels(CLASS_LABELS)
    cbar.ax.tick_params(labelsize=7)


def plot_map(output_dir: Path) -> dict[str, object]:
    priority, prof = read(PRIORITY)
    fig = plt.figure(figsize=(15, 9.5), facecolor="white")
    grid = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1], height_ratios=[1.15, 1], hspace=0.32, wspace=0.15)

    ax_main = fig.add_subplot(grid[0, 0])
    show_class(ax_main, priority, PRIORITY_COLORS, "Priority score")

    ax_fh = fig.add_subplot(grid[0, 1])
    fh, _ = read(CRITERIA_DIR / "flood_hazard_0_1.tif")
    show_class(ax_fh, fh, CRITERIA_COLORS["flood_hazard"], "Flood-conditioning indicator (FH)")

    ax_se = fig.add_subplot(grid[0, 2])
    se, _ = read(CRITERIA_DIR / "sediment_0_1.tif")
    show_class(ax_se, se, CRITERIA_COLORS["sediment"], "Sediment / erosion score")

    names = [
        ("landuse_asm", "General land-use pressure score"),
        ("environmental", "Environmental context indicator (ES)"),
        ("socioeconomic", "Socioeconomic exposure indicator"),
    ]
    for i, (key, label) in enumerate(names):
        ax = fig.add_subplot(grid[1, i])
        data, _ = read(CRITERIA_DIR / f"{key}_0_1.tif")
        show_class(ax, data, CRITERIA_COLORS[key], label)

    figure_title = fig.suptitle(
        "Goslar focus area \u2014 flood-risk priority prototype",
        x=0.06, y=0.985, ha="left", fontsize=17, fontweight="bold",
    )
    subtitle = fig.text(
        0.06, 0.945,
        "Data sources: Copernicus DEM GLO-30 terrain; DWD REGNIE June-August 1991-2020 rainfall; "
        "EEA Natura 2000 (2024) protected areas; Destatis Zensus 2022 population.",
        ha="left", fontsize=10, color="#4A4A4A",
    )
    footer = fig.text(
        0.06, 0.015,
        "Prototype map \u2014 diagnostic only, not a final flood-risk result. "
        "Reference grid: UTM zone 32N, 30 m.",
        ha="left", fontsize=8.5, color="#5D5D5D",
    )
    fig.subplots_adjust(top=0.90, bottom=0.07, left=0.04, right=0.985)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    extents = [figure_title.get_window_extent(renderer=renderer),
               subtitle.get_window_extent(renderer=renderer),
               footer.get_window_extent(renderer=renderer)]
    overlap_count = sum(
        extents[i].overlaps(extents[j]) for i in range(len(extents)) for j in range(i + 1, len(extents))
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_dir / "goslar_pim_overview"
    fig.savefig(stem.with_suffix(".png"), dpi=200, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    manifest = {
        "figure_id": "goslar_pim_overview",
        "focus_area_id": "goslar_harz_2024_focus_extent",
        "claim_level": "diagnostic_only",
        "enters_pim_score": False,
        "main_weights": {"flood_hazard": 0.34, "sediment": 0.25, "landuse_asm": 0.17,
                         "environmental": 0.10, "socioeconomic": 0.14},
        "data_gaps": [],
        "data_sources": {
            "dem": "Copernicus DEM GLO-30 (N51E010)",
            "rainfall": "DWD REGNIE JJA 1991-2020 mean (30-y climate normal)",
            "protected_areas": "EEA Natura 2000 2024 (FFH + SPA)",
            "population": "Destatis Zensus 2022 100 m grid",
        },
        "color_palettes": {
            "priority": PRIORITY_COLORS,
            **{key: list(colors) for key, colors in CRITERIA_COLORS.items()},
        },
        "classification": "equal interval 0-1, five classes, Peru-compatible ColorBrewer palettes",
        "layout_overlap_count": int(overlap_count),
        "outputs": [stem.with_suffix(".png").name, stem.with_suffix(".svg").name],
    }
    (output_dir / "goslar_pim_overview_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    print(json.dumps(plot_map(OUT_DIR), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
