#!/usr/bin/env python3
"""Plot the Goslar Harz 2024 focus area in national and regional context."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[2]
ADMIN0 = ROOT / "data/raw/naturalearth_admin_boundaries/ne_10m_admin_0_countries.zip"
ADMIN1 = ROOT / "data/raw/naturalearth_admin_boundaries/ne_10m_admin_1_states_provinces.zip"
DEFAULT_OUTPUT = ROOT / "outputs/goslar_harz_2024_focus_area/comparison_maps"

CRS = "EPSG:4326"
FOCUS_EXTENT_WGS84 = (10.3646, 51.8544, 10.4194, 51.9089)

GREEN = "#2E7D32"
DARK_GREEN = "#1B5E20"
TEXT = "#17212B"
GRID = "#D8D8D8"
COUNTRY_FILL = "#F4F2EC"


def add_north_arrow(ax: plt.Axes) -> None:
    ax.annotate(
        "N",
        xy=(0.955, 0.94),
        xytext=(0.955, 0.84),
        xycoords="axes fraction",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color=TEXT,
        arrowprops={"arrowstyle": "-|>", "lw": 1.5, "color": TEXT},
    )


def add_scale_bar(ax: plt.Axes, length_km: int = 4) -> None:
    # Approximate scale for the latitude band.
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    dx = length_km / 111.32
    x0 = xmin + 0.06 * (xmax - xmin)
    y0 = ymin + 0.07 * (ymax - ymin)
    ax.plot([x0, x0 + dx], [y0, y0], color=TEXT, lw=3, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 0.0009, y0 + 0.0009], color=TEXT, lw=1)
    ax.plot([x0 + dx, x0 + dx], [y0 - 0.0009, y0 + 0.0009], color=TEXT, lw=1)
    ax.text(x0 + dx / 2, y0 + 0.0012, f"{length_km} km", ha="center", fontsize=9, color=TEXT)


def load_sources() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    countries = gpd.read_file(f"zip://{ADMIN0}")
    germany = countries.loc[countries["ADMIN"].eq("Germany")].to_crs(CRS)
    regions = gpd.read_file(f"zip://{ADMIN1}")
    german_regions = regions.loc[regions["admin"].eq("Germany")].to_crs(CRS)
    lower_saxony = german_regions.loc[german_regions["name"].eq("Niedersachsen")]
    if germany.empty or lower_saxony.empty:
        raise RuntimeError("Germany or Lower Saxony administrative geometry is empty")
    return germany, german_regions, lower_saxony


def plot_map(output_dir: Path) -> dict[str, object]:
    germany, german_regions, lower_saxony = load_sources()
    focus = gpd.GeoDataFrame(
        {"area": ["Goslar focus layout extent"]},
        geometry=[box(*FOCUS_EXTENT_WGS84)],
        crs=CRS,
    )

    fig = plt.figure(figsize=(14, 8.2), facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=[0.8, 1.8], wspace=0.07)
    ax_country = fig.add_subplot(grid[0, 0])
    ax_detail = fig.add_subplot(grid[0, 1])

    # Panel A: Germany national context.
    germany.plot(ax=ax_country, color=COUNTRY_FILL, edgecolor="#555555", linewidth=0.8)
    german_regions.plot(ax=ax_country, color="none", edgecolor="#C4C4C4", linewidth=0.35)
    lower_saxony.plot(ax=ax_country, color="#E7E2D3", edgecolor="#786F61", linewidth=0.8)
    focus.plot(ax=ax_country, color=GREEN, edgecolor="white", linewidth=0.7, zorder=5)
    focus_point = focus.geometry.iloc[0].centroid
    ax_country.scatter(focus_point.x, focus_point.y, s=70, color=DARK_GREEN, marker="D", edgecolor="white", zorder=6)
    ax_country.annotate(
        "Goslar focus area",
        xy=(focus_point.x, focus_point.y),
        xytext=(10.6, 52.9),
        fontsize=9,
        fontweight="bold",
        color=DARK_GREEN,
        arrowprops={"arrowstyle": "-", "color": DARK_GREEN, "lw": 1},
    )
    ax_country.set_title("A  National context", loc="left", fontsize=12, fontweight="bold", color=TEXT)
    ax_country.set_xlim(5.5, 15.5)
    ax_country.set_ylim(47.0, 55.5)
    ax_country.set_aspect("equal")
    ax_country.axis("off")

    # Panel B: regional detail around Goslar.
    lower_saxony.plot(ax=ax_detail, color=COUNTRY_FILL, edgecolor="#8D8D8D", linewidth=0.9, zorder=1)
    focus.plot(ax=ax_detail, color=GREEN, edgecolor=DARK_GREEN, linewidth=1.4, alpha=0.75, hatch="///", zorder=4)
    ax_detail.scatter(focus_point.x, focus_point.y, s=45, color=DARK_GREEN, marker="D", edgecolor="white", zorder=5)
    ax_detail.annotate(
        "Goslar focus area\n2017 flood catchment (layout extent)",
        xy=(focus_point.x, focus_point.y),
        xytext=(focus_point.x + 0.09, focus_point.y + 0.02),
        fontsize=10,
        fontweight="bold",
        color=DARK_GREEN,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": DARK_GREEN, "alpha": 0.95},
        arrowprops={"arrowstyle": "->", "color": DARK_GREEN, "lw": 1.2},
    )
    ax_detail.set_xlim(FOCUS_EXTENT_WGS84[0] - 0.12, FOCUS_EXTENT_WGS84[2] + 0.12)
    ax_detail.set_ylim(FOCUS_EXTENT_WGS84[1] - 0.09, FOCUS_EXTENT_WGS84[3] + 0.12)
    ax_detail.set_aspect("equal")
    ax_detail.grid(color=GRID, linewidth=0.45, linestyle=":", zorder=0)
    ax_detail.tick_params(labelsize=8, colors="#666666")
    ax_detail.set_xlabel("Longitude (degrees, WGS84)", fontsize=9, color="#555555")
    ax_detail.set_ylabel("Latitude (degrees)", fontsize=9, color="#555555")
    ax_detail.set_title("B  Goslar regional view", loc="left", fontsize=12, fontweight="bold", color=TEXT)
    add_scale_bar(ax_detail)
    add_north_arrow(ax_detail)

    legend_handles = [
        Patch(facecolor=GREEN, edgecolor=DARK_GREEN, hatch="///", label="Goslar focus layout extent"),
    ]
    ax_detail.legend(
        handles=legend_handles,
        loc="lower right",
        frameon=True,
        framealpha=0.96,
        fontsize=9,
        title="Mapped area",
        title_fontsize=9,
    )

    figure_title = fig.suptitle(
        "Goslar Harz 2024 focus area (2017 flood catchment)",
        x=0.055,
        y=0.985,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=TEXT,
    )
    subtitle = fig.text(
        0.055,
        0.925,
        "Focus extent follows the published catchment map for the 2017 Goslar flood-protection "
        "measure; it is not a mapped flood footprint.",
        ha="left",
        fontsize=11,
        color="#4A4A4A",
    )
    footer = fig.text(
        0.055,
        0.018,
        "Prototype location map \u2014 extent is a reference box, not an observed hazard extent.",
        ha="left",
        fontsize=8.5,
        color="#5D5D5D",
    )
    fig.subplots_adjust(top=0.855, bottom=0.08, left=0.05, right=0.985)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_artists = [figure_title, subtitle, footer]
    extents = [artist.get_window_extent(renderer=renderer) for artist in layout_artists]
    overlap_count = sum(
        extents[left].overlaps(extents[right])
        for left in range(len(extents))
        for right in range(left + 1, len(extents))
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_dir / "goslar_focus_area_location_map"
    fig.savefig(stem.with_suffix(".png"), dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    manifest = {
        "figure_id": "goslar_focus_area_location_map",
        "focus_area_id": "goslar_harz_2024_focus_extent",
        "claim_level": "diagnostic_only",
        "focus_extent_wgs84": list(FOCUS_EXTENT_WGS84),
        "focus_extent_is_hazard_footprint": False,
        "layout_overlap_count": int(overlap_count),
        "outputs": [stem.with_suffix(".png").name],
    }
    manifest_path = output_dir / "goslar_focus_area_location_map_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(plot_map(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
