#!/usr/bin/env python3
"""Render clean, label-free detail maps for the study-area PowerPoint slide.

The map images intentionally contain no text. Place names and callouts are
added as editable PowerPoint objects by the slide-editing step.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/presentation_assets"

COUNTRIES = ROOT / "data/raw/naturalearth_admin_boundaries/ne_10m_admin_0_countries.zip"
ADMIN1 = ROOT / "data/raw/naturalearth_admin_boundaries/ne_10m_admin_1_states_provinces.zip"
PERU_ADMIN = ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_adminareas_a_free_1.shp"
ZIM_SUBCATCHMENTS = ROOT / "data/raw/zimbabwe_geoportal_subcatchments_2025/extracted/sub_catchments.shp"
PERU_BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
ZIM_BOUNDARY = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"


def _canvas() -> tuple[plt.Figure, plt.Axes]:
    fig = plt.figure(figsize=(12, 6), dpi=200, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#EAF3F8")
    ax.set_axis_off()
    ax.set_aspect("equal")
    return fig, ax


def render_peru() -> Path:
    target_crs = "EPSG:32718"
    boundary = gpd.read_file(
        PERU_BOUNDARY,
        layer="peru_pilot_boundary",
    ).to_crs(target_crs)
    countries = gpd.read_file(f"zip://{COUNTRIES}")
    peru = countries[countries["ADMIN"].eq("Peru")].to_crs(target_crs)
    admin = gpd.read_file(
        PERU_ADMIN,
        bbox=(-72.9, -17.4, -71.0, -15.6),
    ).to_crs(target_crs)

    fig, ax = _canvas()
    peru.plot(ax=ax, color="#F2E3D5", edgecolor="#A3A3A3", linewidth=1.1, zorder=1)
    admin.boundary.plot(ax=ax, color="#9A9A9A", linewidth=0.75, alpha=0.85, zorder=2)
    boundary.plot(ax=ax, color="#E7A16B", edgecolor="#8F3B00", linewidth=2.4, zorder=4)

    minx, miny, maxx, maxy = boundary.total_bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    # A wider context window keeps the Pacific coast and nearby districts while
    # making the working catchment the visual focus.
    ax.set_xlim(cx - 92_000, cx + 92_000)
    ax.set_ylim(cy - 52_000, cy + 52_000)

    path = OUT / "peru_pe1_detail_map_no_text.png"
    fig.savefig(path, dpi=200, facecolor="white", transparent=False)
    plt.close(fig)
    return path


def render_zimbabwe() -> Path:
    target_crs = "EPSG:32735"
    boundary = gpd.read_file(
        ZIM_BOUNDARY,
        layer="v1_working_boundary",
    ).to_crs(target_crs)
    admin1 = gpd.read_file(f"zip://{ADMIN1}")
    admin1 = admin1[admin1["adm0_a3"].eq("ZWE")].to_crs(target_crs)
    subcatchments = gpd.read_file(ZIM_SUBCATCHMENTS).to_crs(target_crs)

    fig, ax = _canvas()
    admin1.plot(ax=ax, color="#D9E9E6", edgecolor="#939A99", linewidth=1.0, zorder=1)
    subcatchments.boundary.plot(ax=ax, color="#8C9694", linewidth=0.65, alpha=0.75, zorder=2)
    boundary.plot(ax=ax, color="#75BBB3", edgecolor="#006A63", linewidth=2.5, zorder=4)

    minx, miny, maxx, maxy = boundary.total_bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    ax.set_xlim(cx - 135_000, cx + 135_000)
    ax.set_ylim(cy - 70_000, cy + 70_000)

    path = OUT / "zimbabwe_upper_mzingwane_detail_map_no_text.png"
    fig.savefig(path, dpi=200, facecolor="white", transparent=False)
    plt.close(fig)
    return path


def main() -> None:
    required = [
        COUNTRIES,
        ADMIN1,
        PERU_ADMIN,
        ZIM_SUBCATCHMENTS,
        PERU_BOUNDARY,
        ZIM_BOUNDARY,
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing study-area detail-map input(s): " + ", ".join(map(str, missing)))

    OUT.mkdir(parents=True, exist_ok=True)
    print(render_peru())
    print(render_zimbabwe())


if __name__ == "__main__":
    main()
