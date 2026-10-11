#!/usr/bin/env python3
"""Plot the active Secocha Peru area and the frozen previous-area baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points


ROOT = Path(__file__).resolve().parents[2]
FROZEN_BOUNDARY = ROOT / "outputs/peru_former_boundary/peru_former_boundary.gpkg"
ACTIVE_BOUNDARY = ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg"
ADMIN0 = ROOT / "data/raw/naturalearth_admin_boundaries/ne_10m_admin_0_countries.zip"
ADMIN1 = ROOT / "data/raw/naturalearth_admin_boundaries/ne_10m_admin_1_states_provinces.zip"
DEFAULT_OUTPUT = ROOT / "outputs/secocha_2023_validation/comparison_maps"

CRS_UTM18S = "EPSG:32718"
SECOCHA_ANCHOR_UTM = Point(695121, 8232667)

BLUE = "#2F6F9F"
ORANGE = "#D55E00"
REGION_FILL = "#E7E2D3"
COUNTRY_FILL = "#F4F2EC"
TEXT = "#17212B"
GRID = "#D8D8D8"


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


def add_scale_bar(ax: plt.Axes, length_km: int = 50) -> None:
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    length = length_km * 1000
    x0 = xmin + 0.06 * (xmax - xmin)
    y0 = ymin + 0.07 * (ymax - ymin)
    ax.plot([x0, x0 + length], [y0, y0], color=TEXT, lw=3, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 2500, y0 + 2500], color=TEXT, lw=1)
    ax.plot([x0 + length, x0 + length], [y0 - 2500, y0 + 2500], color=TEXT, lw=1)
    ax.text(x0 + length / 2, y0 + 5000, f"{length_km} km", ha="center", fontsize=9, color=TEXT)


def load_sources() -> tuple[
    gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame
]:
    frozen = gpd.read_file(FROZEN_BOUNDARY).to_crs(CRS_UTM18S)
    active = gpd.read_file(ACTIVE_BOUNDARY, layer="secocha_active_boundary").to_crs(CRS_UTM18S)
    countries = gpd.read_file(f"zip://{ADMIN0}")
    peru = countries.loc[countries["ADMIN"].eq("Peru")].to_crs("EPSG:4326")
    regions = gpd.read_file(f"zip://{ADMIN1}")
    peru_regions = regions.loc[regions["admin"].eq("Peru")].to_crs("EPSG:4326")
    arequipa = peru_regions.loc[peru_regions["name"].eq("Arequipa")]
    if frozen.empty or active.empty or peru.empty or arequipa.empty:
        raise RuntimeError("required Peru scope or administrative geometry is empty")
    return frozen, active, peru, peru_regions, arequipa


def plot_map(output_dir: Path) -> dict[str, object]:
    frozen, active, peru, peru_regions, arequipa = load_sources()
    frozen_union = frozen.geometry.union_all()
    active_union = active.geometry.union_all()
    secocha_anchor = gpd.GeoDataFrame(
        {"site": ["Secocha"]}, geometry=[SECOCHA_ANCHOR_UTM], crs=CRS_UTM18S
    )

    anchor_nearest, frozen_nearest = nearest_points(SECOCHA_ANCHOR_UTM, frozen_union)
    distance_km = anchor_nearest.distance(frozen_nearest) / 1000
    separation = gpd.GeoSeries(
        [LineString([anchor_nearest, frozen_nearest])], crs=CRS_UTM18S
    )

    fig = plt.figure(figsize=(14, 8.2), facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=[0.8, 1.8], wspace=0.07)
    ax_country = fig.add_subplot(grid[0, 0])
    ax_detail = fig.add_subplot(grid[0, 1])

    # Panel A: national orientation.
    peru.plot(ax=ax_country, color=COUNTRY_FILL, edgecolor="#555555", linewidth=0.8)
    peru_regions.plot(ax=ax_country, color="none", edgecolor="#C4C4C4", linewidth=0.35)
    arequipa.plot(ax=ax_country, color=REGION_FILL, edgecolor="#786F61", linewidth=0.8)
    frozen_wgs84 = frozen.to_crs("EPSG:4326")
    active_wgs84 = active.to_crs("EPSG:4326")
    frozen_wgs84.plot(ax=ax_country, color=BLUE, edgecolor="white", linewidth=0.7, alpha=0.65, zorder=4)
    active_wgs84.plot(ax=ax_country, color=ORANGE, edgecolor="white", linewidth=0.7, zorder=5)
    exp_point = frozen_wgs84.geometry.union_all().representative_point()
    sec_point = active_wgs84.geometry.union_all().centroid
    ax_country.scatter(exp_point.x, exp_point.y, s=45, color=BLUE, edgecolor="white", zorder=6)
    ax_country.scatter(sec_point.x, sec_point.y, s=55, color=ORANGE, marker="D", edgecolor="white", zorder=6)
    ax_country.annotate(
        "Frozen previous Peru area",
        xy=(exp_point.x, exp_point.y),
        xytext=(-77.8, -14.6),
        fontsize=9,
        fontweight="bold",
        color=BLUE,
        arrowprops={"arrowstyle": "-", "color": BLUE, "lw": 1},
    )
    ax_country.annotate(
        "Active Secocha area",
        xy=(sec_point.x, sec_point.y),
        xytext=(-77.8, -16.5),
        fontsize=9,
        fontweight="bold",
        color=ORANGE,
        arrowprops={"arrowstyle": "-", "color": ORANGE, "lw": 1},
    )
    country_title = ax_country.set_title(
        "A  National context", loc="left", fontsize=12, fontweight="bold", color=TEXT
    )
    ax_country.set_xlim(-82.2, -68.2)
    ax_country.set_ylim(-19.0, 0.3)
    ax_country.set_aspect("equal")
    ax_country.axis("off")

    # Panel B: Arequipa and the actual separation.
    arequipa_utm = arequipa.to_crs(CRS_UTM18S)
    arequipa_utm.plot(ax=ax_detail, color=COUNTRY_FILL, edgecolor="#8D8D8D", linewidth=0.9, zorder=1)
    frozen.plot(ax=ax_detail, color=BLUE, edgecolor="#173F5F", linewidth=1.2, alpha=0.6, zorder=4)
    active.plot(
        ax=ax_detail, color=ORANGE, edgecolor="#7A2D00", linewidth=1.4, alpha=0.82, hatch="///", zorder=5
    )
    secocha_anchor.plot(ax=ax_detail, color="#7A2D00", marker="D", markersize=35, zorder=6)
    separation.plot(ax=ax_detail, color="#5E5E5E", linewidth=1.3, linestyle=(0, (5, 4)), zorder=3)

    exp_center = frozen_union.representative_point()
    sec_center = active_union.centroid
    ax_detail.annotate(
        "Frozen previous-area baseline\nperu_former",
        xy=(exp_center.x, exp_center.y),
        xytext=(exp_center.x - 115000, exp_center.y + 45000),
        fontsize=10,
        fontweight="bold",
        color=BLUE,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": BLUE, "alpha": 0.95},
        arrowprops={"arrowstyle": "->", "color": BLUE, "lw": 1.2},
    )
    ax_detail.annotate(
        "Active Peru research area\nSecocha A7367 reference extent",
        xy=(sec_center.x, sec_center.y),
        xytext=(sec_center.x - 75000, sec_center.y + 60000),
        fontsize=10,
        fontweight="bold",
        color=ORANGE,
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": ORANGE, "alpha": 0.95},
        arrowprops={"arrowstyle": "->", "color": ORANGE, "lw": 1.2},
    )
    midpoint = separation.iloc[0].interpolate(0.5, normalized=True)
    ax_detail.text(
        midpoint.x,
        midpoint.y + 14000,
        f"~{distance_km:.0f} km to frozen previous boundary",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#4E4E4E",
        bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#B0B0B0", "alpha": 0.95},
    )

    combined_bounds = gpd.GeoSeries(
        [frozen_union, active_union], crs=CRS_UTM18S
    ).total_bounds
    ax_detail.set_xlim(combined_bounds[0] - 70000, combined_bounds[2] + 70000)
    ax_detail.set_ylim(combined_bounds[1] - 65000, combined_bounds[3] + 85000)
    ax_detail.set_aspect("equal")
    ax_detail.grid(color=GRID, linewidth=0.45, linestyle=":", zorder=0)
    ax_detail.tick_params(labelsize=8, colors="#666666")
    ax_detail.set_xlabel("Easting (m), WGS84 / UTM zone 18S", fontsize=9, color="#555555")
    ax_detail.set_ylabel("Northing (m)", fontsize=9, color="#555555")
    detail_title = ax_detail.set_title(
        "B  Arequipa regional view", loc="left", fontsize=12, fontweight="bold", color=TEXT
    )
    add_scale_bar(ax_detail)
    add_north_arrow(ax_detail)

    legend_handles = [
        Patch(facecolor=BLUE, edgecolor="#173F5F", label="Frozen previous Peru boundary"),
        Patch(facecolor=ORANGE, edgecolor="#7A2D00", hatch="///", label="Active Secocha reference extent"),
        Line2D([0], [0], color="#5E5E5E", linestyle=(0, (5, 4)), label="Spatial separation"),
    ]
    ax_detail.legend(
        handles=legend_handles,
        loc="lower right",
        frameon=True,
        framealpha=0.96,
        fontsize=9,
        title="Mapped areas",
        title_fontsize=9,
    )

    figure_title = fig.suptitle(
        "Secocha is the active Peru research area; the previous area is frozen",
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
        "New model outputs use the Secocha A7367 reference extent; the former PIM remains a read-only baseline.",
        ha="left",
        fontsize=11,
        color="#4A4A4A",
    )
    footer = fig.text(
        0.055,
        0.018,
        "Scope-transition map \u2014 the Secocha extent follows the coordinate frame of INGEMMET "
        "A7367 Map 7 and is not an event footprint or catchment.",
        ha="left",
        fontsize=8.5,
        color="#5D5D5D",
    )
    fig.subplots_adjust(top=0.855, bottom=0.08, left=0.05, right=0.985)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_artists = [figure_title, subtitle, country_title, detail_title, footer]
    extents = [artist.get_window_extent(renderer=renderer) for artist in layout_artists]
    overlap_count = sum(
        extents[left].overlaps(extents[right])
        for left in range(len(extents))
        for right in range(left + 1, len(extents))
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_dir / "peru_experiment_and_secocha_location_map"
    fig.savefig(stem.with_suffix(".png"), dpi=220, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)

    manifest = {
        "figure_id": "peru_experiment_and_secocha_location_map",
        "claim_level": "diagnostic_only",
        "areas_overlap": bool(frozen_union.intersects(active_union)),
        "nearest_distance_km": round(distance_km, 1),
        "distance_definition": "Secocha Figure 59 anchor to nearest frozen previous-boundary point",
        "active_boundary_id": "secocha_reference_extent",
        "frozen_boundary_id": "peru_former",
        "experiment_boundary_id": "peru_former",
        "secocha_area_role": "active_A7367_map_extent_reference",
        "secocha_extent_source": "INGEMMET A7367 Map 7, PDF page 75; coordinate-frame reading",
        "secocha_extent_is_event_footprint": False,
        "secocha_extent_is_catchment": False,
        "layout_overlap_count": int(overlap_count),
        "crs_detail_panel": CRS_UTM18S,
        "outputs": [stem.with_suffix(".png").name, stem.with_suffix(".svg").name],
    }
    manifest_path = output_dir / "peru_experiment_and_secocha_location_map_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(plot_map(args.output_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
