#!/usr/bin/env python3
"""Plot the V1 multi-criteria evidence board for mentor review."""

from __future__ import annotations

import sys
import textwrap
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio.errors
import rasterio
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

# pyogrio (the geopandas default backend) raises DataLayerError for a layer that is
# absent from a *present* file; a missing file or a corrupt layer raises
# DataSourceError and is left to propagate. fiona signals a missing layer with a
# plain ValueError, which is too broad to catch safely, so there is no portable
# cross-backend tuple -- we rely on the pyogrio backend. (geopandas >= 1.0 defaults
# to pyogrio; if a non-pyogrio backend is ever forced, an absent optional layer will
# raise loudly instead of being skipped.)
LAYER_MISSING = (pyogrio.errors.DataLayerError,)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/v1_multicriteria_evidence_package"
LAYERS_GPKG = OUT_DIR / "v1_multicriteria_review_layers.gpkg"
EVIDENCE_CSV = OUT_DIR / "v1_candidate_criteria_evidence_table.csv"
COUNTS_CSV = OUT_DIR / "v1_multicriteria_layer_counts.csv"
TERRAIN_DIR = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization"

BOARD_PNG = OUT_DIR / "mentor_v1_multicriteria_evidence_board.png"
BOARD_PDF = OUT_DIR / "mentor_v1_multicriteria_evidence_board.pdf"
PANEL_A_PNG = OUT_DIR / "panel_a_v1_river_context.png"
PANEL_A_PDF = OUT_DIR / "panel_a_v1_river_context.pdf"
PANEL_B_PNG = OUT_DIR / "panel_b_v1_terrain_diagnostics.png"
PANEL_B_PDF = OUT_DIR / "panel_b_v1_terrain_diagnostics.pdf"
PANEL_C_PNG = OUT_DIR / "panel_c_v1_exposure_mining_proxy.png"
PANEL_C_PDF = OUT_DIR / "panel_c_v1_exposure_mining_proxy.pdf"
PANEL_D_PNG = OUT_DIR / "panel_d_v1_criteria_decision_table.png"
PANEL_D_PDF = OUT_DIR / "panel_d_v1_criteria_decision_table.pdf"
CAPTION_MD = OUT_DIR / "mentor_v1_multicriteria_caption.md"
CAPTION_TXT = OUT_DIR / "mentor_v1_multicriteria_caption.txt"
HANDOFF = OUT_DIR / "v1_multicriteria_handoff.md"
TARGET_CRS = "EPSG:32735"

TERRAIN_RASTERS = [
    ("Elevation / lowland context", TERRAIN_DIR / "v1_elevation_lowland_context_0_1.tif"),
    ("Low-slope susceptibility candidate", TERRAIN_DIR / "v1_slope_low_slope_susceptibility_0_1.tif"),
    ("High-slope runoff-pressure alternative", TERRAIN_DIR / "v1_slope_high_runoff_pressure_0_1.tif"),
]


plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8.8,
        "axes.titlesize": 10.2,
        "axes.labelsize": 8.5,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def layer(name: str) -> gpd.GeoDataFrame:
    try:
        gdf = gpd.read_file(LAYERS_GPKG, layer=name)
    except LAYER_MISSING:
        print(f"layer '{name}' not present in {LAYERS_GPKG.name}; treating as empty", file=sys.stderr)
        return gpd.GeoDataFrame(geometry=[], crs=TARGET_CRS)
    if gdf.empty:
        return gdf.set_crs(gdf.crs or TARGET_CRS)
    return gdf.to_crs(TARGET_CRS)


def raster_extent(bounds) -> list[float]:
    return [bounds.left, bounds.right, bounds.bottom, bounds.top]


def km_formatter(value, _pos) -> str:
    return f"{value / 1000:.0f}"


def style_map(ax, title: str, boundary: gpd.GeoDataFrame) -> None:
    minx, miny, maxx, maxy = boundary.total_bounds
    pad_x = (maxx - minx) * 0.08
    pad_y = (maxy - miny) * 0.08
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_title(title, loc="left", weight="bold")
    ax.set_xlabel("Easting (km, EPSG:32735)")
    ax.set_ylabel("Northing (km, EPSG:32735)")
    ax.xaxis.set_major_formatter(FuncFormatter(km_formatter))
    ax.yaxis.set_major_formatter(FuncFormatter(km_formatter))
    ax.grid(alpha=0.12, linewidth=0.5)
    ax.set_aspect("equal", adjustable="box")


def add_scale_bar(ax, length_km: int = 20) -> None:
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x = x0 + 0.07 * (x1 - x0)
    y = y0 + 0.08 * (y1 - y0)
    ax.plot([x, x + length_km * 1000], [y, y], color="#222222", linewidth=2)
    ax.text(x + length_km * 500, y + 0.02 * (y1 - y0), f"{length_km} km", ha="center", fontsize=7)


def add_north_arrow(ax) -> None:
    ax.annotate(
        "N",
        xy=(0.08, 0.92),
        xytext=(0.08, 0.82),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        weight="bold",
        arrowprops={"arrowstyle": "-|>", "linewidth": 1.0, "color": "#222222"},
    )


def draw_panel_legend(legend_ax, handles: list, columns: int) -> None:
    legend_ax.axis("off")
    legend_ax.legend(
        handles=handles,
        loc="center",
        ncol=columns,
        frameon=True,
        framealpha=0.94,
        fontsize=7.0,
        handlelength=1.5,
        columnspacing=1.0,
        borderpad=0.45,
    )


def draw_river_context(ax, legend_ax, layers: dict[str, gpd.GeoDataFrame]) -> None:
    boundary = layers["v1_boundary"]
    layers["hydrorivers_v1"].plot(ax=ax, color="#9DD3EA", linewidth=0.35, alpha=0.75)
    layers["geoportal_rivers_v1"].plot(ax=ax, color="#0072B2", linewidth=0.8)
    if not layers["geoportal_water_areas_v1"].empty:
        layers["geoportal_water_areas_v1"].plot(ax=ax, color="#56B4E9", alpha=0.45, edgecolor="none")
    boundary.boundary.plot(ax=ax, color="#111111", linewidth=1.2)
    layers["v1_anchors"].plot(ax=ax, color="#D55E00", markersize=18, edgecolor="white", linewidth=0.4)
    style_map(ax, "A. V1 catchment and river context", boundary)
    add_north_arrow(ax)
    add_scale_bar(ax)
    draw_panel_legend(
        legend_ax,
        [
            Line2D([0], [0], color="#111111", lw=1.2, label="V1 boundary"),
            Line2D([0], [0], color="#0072B2", lw=0.9, label="Geoportal rivers"),
            Line2D([0], [0], color="#9DD3EA", lw=0.9, label="HydroRIVERS"),
            Patch(facecolor="#56B4E9", alpha=0.45, label="Water areas"),
        ],
        columns=2,
    )


def draw_terrain_panel(fig, gridspec_cell, boundary: gpd.GeoDataFrame) -> None:
    sub = gridspec_cell.subgridspec(1, 3, wspace=0.24)
    axes = [fig.add_subplot(sub[0, i]) for i in range(3)]
    for ax, (title, path) in zip(axes, TERRAIN_RASTERS, strict=True):
        with rasterio.open(path) as src:
            data = src.read(1).astype("float32")
            shown = np.where(data == src.nodata, np.nan, data)
            img = ax.imshow(shown, cmap="viridis", extent=raster_extent(src.bounds), origin="upper", vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="#111111", linewidth=0.75)
        ax.set_title(title, fontsize=8.2, pad=6)
        ax.set_xlabel("Easting (km)")
        ax.set_ylabel("Northing (km)")
        ax.xaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.yaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.grid(alpha=0.11, linewidth=0.45)
        ax.set_aspect("equal", adjustable="box")
        add_north_arrow(ax)
        add_scale_bar(ax)
    axes[0].text(
        -0.06,
        1.13,
        "B. Terrain diagnostic candidates",
        transform=axes[0].transAxes,
        fontsize=10.2,
        weight="bold",
        ha="left",
        va="bottom",
    )
    fig.colorbar(img, ax=axes, shrink=0.76, label="0-1 terrain diagnostic")


def draw_exposure_mining(ax, legend_ax, layers: dict[str, gpd.GeoDataFrame]) -> None:
    boundary = layers["v1_boundary"]
    layers["osm_roads_v1"].plot(ax=ax, color="#8C8C8C", linewidth=0.32, alpha=0.5)
    layers["geoportal_rivers_v1"].plot(ax=ax, color="#0072B2", linewidth=0.65)
    layers["road_river_crossings_v1"].plot(ax=ax, color="#E69F00", markersize=14, alpha=0.85)
    layers["osm_places_v1"].plot(ax=ax, color="#CC79A7", markersize=22, edgecolor="white", linewidth=0.4)
    if not layers["osm_mining_proxy_v1"].empty:
        layers["osm_mining_proxy_v1"].plot(ax=ax, color="#D55E00", alpha=0.45, edgecolor="#D55E00", linewidth=0.7)
    boundary.boundary.plot(ax=ax, color="#111111", linewidth=1.2)
    style_map(ax, "C. Exposure and weak mining proxy evidence", boundary)
    add_north_arrow(ax)
    add_scale_bar(ax)
    draw_panel_legend(
        legend_ax,
        [
            Line2D([0], [0], color="#8C8C8C", lw=1.0, label="OSM roads"),
            Line2D([0], [0], color="#0072B2", lw=1.0, label="Rivers"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="#E69F00", label="Road-river crossing proxy"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="#CC79A7", label="OSM places"),
            Patch(facecolor="#D55E00", alpha=0.45, label="OSM quarry/industrial proxy"),
        ],
        columns=2,
    )


def draw_decision_table(ax, evidence: pd.DataFrame, counts: pd.DataFrame) -> None:
    ax.axis("off")
    display = evidence[["criterion_family", "candidate_criterion", "evidence_strength", "suggested_role"]].copy()
    display.columns = ["Family", "Candidate", "Strength", "Role"]
    names = {
        "elevation_lowland_context": "Lowland context",
        "slope_low_slope_susceptibility": "Low-slope susceptibility",
        "slope_high_runoff_pressure": "High-slope runoff pressure",
        "river_context": "River context",
        "flood_prone_zones": "Flood-prone zones",
        "settlement_places": "Settlement places",
        "roads_and_crossings": "Roads and crossings",
        "osm_quarry_industrial_proxy": "OSM quarry / industrial proxy",
        "chirps_rainfall": "CHIRPS rainfall",
    }
    display["Family"] = display["Family"].str.replace("_", " ").str.title()
    display["Candidate"] = display["Candidate"].map(lambda value: "\n".join(textwrap.wrap(names.get(value, value), 24)))
    display["Role"] = display["Role"].map(lambda value: "\n".join(textwrap.wrap(value.replace("_", " "), 18)))
    table = ax.table(cellText=display.values, colLabels=display.columns, loc="center", cellLoc="left", colLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(7.1)
    table.scale(1, 1.55)
    for (row, _col), cell in table.get_celld().items():
        cell.set_linewidth(0.35)
        if row == 0:
            cell.set_facecolor("#E8EDF2")
            cell.set_text_props(weight="bold")
    flood_count = int(counts.loc[counts["layer"] == "geoportal_flood_prone_zones_v1", "feature_count"].iloc[0])
    mining_count = int(counts.loc[counts["layer"] == "osm_mining_proxy_v1", "feature_count"].iloc[0])
    ax.set_title("D. Candidate criteria decision table", loc="left", weight="bold")
    ax.text(
        0,
        -0.08,
        f"Rainfall: CHIRPS comparison available separately. Flood-prone local overlap: {flood_count}. Mining proxy polygons: {mining_count}.",
        transform=ax.transAxes,
        fontsize=8,
        color="#333333",
    )


def load_inputs() -> tuple[dict[str, gpd.GeoDataFrame], pd.DataFrame, pd.DataFrame]:
    names = [
        "v1_boundary",
        "v1_anchors",
        "geoportal_rivers_v1",
        "hydrorivers_v1",
        "geoportal_water_areas_v1",
        "osm_roads_v1",
        "osm_places_v1",
        "osm_mining_proxy_v1",
        "road_river_crossings_v1",
    ]
    return {name: layer(name) for name in names}, pd.read_csv(EVIDENCE_CSV), pd.read_csv(COUNTS_CSV)


def plot_split_panels(layers: dict[str, gpd.GeoDataFrame], evidence: pd.DataFrame, counts: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(6.2, 7.6), constrained_layout=True)
    grid = fig.add_gridspec(2, 1, height_ratios=[1, 0.13])
    draw_river_context(fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[1, 0]), layers)
    fig.savefig(PANEL_A_PNG)
    fig.savefig(PANEL_A_PDF)
    plt.close(fig)

    fig = plt.figure(figsize=(13.8, 5.2), constrained_layout=True)
    draw_terrain_panel(fig, fig.add_gridspec(1, 1)[0, 0], layers["v1_boundary"])
    fig.savefig(PANEL_B_PNG)
    fig.savefig(PANEL_B_PDF)
    plt.close(fig)

    fig = plt.figure(figsize=(6.2, 7.6), constrained_layout=True)
    grid = fig.add_gridspec(2, 1, height_ratios=[1, 0.16])
    draw_exposure_mining(fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[1, 0]), layers)
    fig.savefig(PANEL_C_PNG)
    fig.savefig(PANEL_C_PDF)
    plt.close(fig)

    fig = plt.figure(figsize=(8.8, 5.2), constrained_layout=True)
    draw_decision_table(fig.add_subplot(111), evidence, counts)
    fig.savefig(PANEL_D_PNG)
    fig.savefig(PANEL_D_PDF)
    plt.close(fig)


def plot_board(layers: dict[str, gpd.GeoDataFrame], evidence: pd.DataFrame, counts: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(16.2, 10.4), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=[0.8, 1.65])

    a_grid = grid[0, 0].subgridspec(2, 1, height_ratios=[1, 0.15])
    draw_river_context(fig.add_subplot(a_grid[0, 0]), fig.add_subplot(a_grid[1, 0]), layers)

    draw_terrain_panel(fig, grid[0, 1], layers["v1_boundary"])

    c_grid = grid[1, 0].subgridspec(2, 1, height_ratios=[1, 0.18])
    draw_exposure_mining(fig.add_subplot(c_grid[0, 0]), fig.add_subplot(c_grid[1, 0]), layers)

    draw_decision_table(fig.add_subplot(grid[1, 1]), evidence, counts)
    fig.savefig(BOARD_PNG)
    fig.savefig(BOARD_PDF)
    plt.close(fig)


def caption_text() -> str:
    return """Figure X. V1 multi-criteria evidence package for mentor review. The package is provided as separate panels first: river/flood context, terrain diagnostics, exposure and mining-pressure proxy evidence, and a candidate-criteria decision table. The combined board is a secondary overview only.

Source note: The board uses existing V1 terrain diagnostics, HydroRIVERS, Zimbabwe Geoportal river/water/flood-prone layers, and Geofabrik OSM roads/places/landuse. A separate CHIRPS rainfall-sensitivity package is available; CHIRPS is not resampled or overlaid in this figure.

Interpretation note: This is a candidate-criteria evidence package, not a model output. Geoportal Flood Prone Zones have zero local overlap in the current review layers, and OSM quarry/industrial features are weak proxy evidence rather than official mining truth.

Limitation note: This figure is not a flood-risk map, not an AHP-MCDA overlay, not an intervention-priority map, and not final thesis boundary evidence.
"""


def write_text_outputs() -> None:
    caption = "# Caption: V1 Multi-Criteria Evidence Package\n\n" + caption_text()
    (OUT_DIR / "mentor_v1_multicriteria_caption.md").write_text(caption, encoding="utf-8")
    (OUT_DIR / "mentor_v1_multicriteria_caption.txt").write_text(caption_text(), encoding="utf-8")
    HANDOFF.write_text(
        "\n".join(
            [
                "# V1 Multi-Criteria Evidence Package Handoff",
                "",
                f"Updated: {date.today().isoformat()}",
                "",
                "Status: mentor-facing evidence package generated as separate panels first. This is not a flood-risk map.",
                "",
                f"- Panel A river context PNG: `{rel(PANEL_A_PNG)}`",
                f"- Panel A river context PDF: `{rel(PANEL_A_PDF)}`",
                f"- Panel B terrain diagnostics PNG: `{rel(PANEL_B_PNG)}`",
                f"- Panel B terrain diagnostics PDF: `{rel(PANEL_B_PDF)}`",
                f"- Panel C exposure/mining proxy PNG: `{rel(PANEL_C_PNG)}`",
                f"- Panel C exposure/mining proxy PDF: `{rel(PANEL_C_PDF)}`",
                f"- Panel D decision table PNG: `{rel(PANEL_D_PNG)}`",
                f"- Panel D decision table PDF: `{rel(PANEL_D_PDF)}`",
                f"- Board PNG: `{rel(BOARD_PNG)}`",
                f"- Board PDF: `{rel(BOARD_PDF)}`",
                f"- Evidence table: `{rel(EVIDENCE_CSV)}`",
                f"- Layer counts: `{rel(COUNTS_CSV)}`",
                f"- Review layers: `{rel(LAYERS_GPKG)}`",
                "",
                "Use the split panels as the primary mentor-facing material; the combined board is a secondary overview only.",
                "",
                "Recommended mentor question: Which evidence families should enter the first prototype criteria set: terrain, rainfall, exposure, mining pressure, and/or river-flood context?",
                "",
                "Specific decisions needed: slope direction, which CHIRPS rainfall interpretation to use, exposure role, and whether OSM mining proxies are acceptable or official mining data is required.",
                "",
                "Scope limits: no AHP weights, no overlay, no 30 m CHIRPS resampling, no flood-risk map, and no final thesis boundary claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not EVIDENCE_CSV.exists() or not LAYERS_GPKG.exists():
        raise FileNotFoundError("Run bin/prepare_v1_multicriteria_evidence.py first")
    layers, evidence, counts = load_inputs()
    plot_split_panels(layers, evidence, counts)
    plot_board(layers, evidence, counts)
    write_text_outputs()
    print(f"wrote {rel(PANEL_A_PNG)}")
    print(f"wrote {rel(PANEL_B_PNG)}")
    print(f"wrote {rel(PANEL_C_PNG)}")
    print(f"wrote {rel(PANEL_D_PNG)}")
    print(f"wrote {rel(BOARD_PNG)}")
    print(f"wrote {rel(BOARD_PDF)}")
    print("wrote outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_caption.md")
    print("wrote outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_caption.txt")
    print(f"wrote {rel(HANDOFF)}")


if __name__ == "__main__":
    main()
