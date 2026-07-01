#!/usr/bin/env python3
"""Plot separate V1 full-methodology evidence panels and handoff notes."""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio.errors
import rasterio
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


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_full_methodology_evidence_sweep"
RASTER_DIR = OUT_DIR / "rasters"
GPKG = OUT_DIR / "v1_full_methodology_review_layers.gpkg"
MATRIX = OUT_DIR / "v1_full_methodology_evidence_matrix.csv"
LANDCOVER = OUT_DIR / "v1_worldcover_class_area.csv"
GSW = OUT_DIR / "v1_jrc_surface_water_summary.csv"
SUMMARY = OUT_DIR / "v1_full_methodology_layer_summary.csv"
HANDOFF = OUT_DIR / "v1_full_methodology_evidence_handoff.md"
CAPTION_MD = OUT_DIR / "v1_full_methodology_caption.md"
CAPTION_TXT = OUT_DIR / "v1_full_methodology_caption.txt"

PANEL_FILES = {
    "landcover": OUT_DIR / "panel_land_use_worldcover.png",
    "water": OUT_DIR / "panel_surface_water_occurrence.png",
    "protected": OUT_DIR / "panel_protected_areas_wdpca.png",
    "population": OUT_DIR / "panel_population_exposure.png",
    "rehab": OUT_DIR / "panel_rehabilitation_proximity.png",
}

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

LC_COLORS = {
    10: "#1B7837",
    20: "#7FBF7B",
    30: "#D9F0A3",
    40: "#E6C35C",
    50: "#B2182B",
    60: "#D8B365",
    80: "#2B8CBE",
    90: "#80CDC1",
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def boundary(crs: str) -> gpd.GeoDataFrame:
    return gpd.read_file(GPKG, layer="v1_boundary").to_crs(crs)


def extent(bounds) -> list[float]:
    return [bounds.left, bounds.right, bounds.bottom, bounds.top]


def km_formatter(value, _pos) -> str:
    return f"{value / 1000:.0f}"


def save(fig: plt.Figure, png_path: Path) -> None:
    fig.savefig(png_path)
    fig.savefig(png_path.with_suffix(".pdf"))
    plt.close(fig)


def plot_landcover() -> None:
    path = RASTER_DIR / "v1_worldcover_2021_native_10m.tif"
    with rasterio.open(path) as src:
        data = src.read(1)
        shown = np.full(data.shape, np.nan, dtype="float32")
        values = sorted(LC_COLORS)
        for idx, value in enumerate(values, start=1):
            shown[data == value] = idx
        bounds = src.bounds
    colors = [LC_COLORS[value] for value in values]
    cmap = mcolors.ListedColormap(colors)
    fig, ax = plt.subplots(figsize=(5.2, 6.0))
    ax.imshow(shown, cmap=cmap, extent=extent(bounds), origin="upper", vmin=0.5, vmax=len(values) + 0.5)
    boundary("EPSG:4326").boundary.plot(ax=ax, color="#111111", linewidth=1.1)
    ax.set_title("V1 land-cover evidence: ESA WorldCover 2021", loc="left")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    handles = [Patch(facecolor=LC_COLORS[row.class_value], label=f"{row.class_name} ({row.share_of_valid_pct:.1f}%)") for row in pd.read_csv(LANDCOVER).itertuples()]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=2, frameon=False, fontsize=7.4)
    ax.grid(alpha=0.12)
    save(fig, PANEL_FILES["landcover"])


def plot_water() -> None:
    path = RASTER_DIR / "v1_jrc_gsw_occurrence.tif"
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        data[data == 255] = np.nan
        bounds = src.bounds
    fig, ax = plt.subplots(figsize=(5.2, 6.0))
    img = ax.imshow(data, cmap="Blues", extent=extent(bounds), origin="upper", vmin=0, vmax=100)
    boundary("EPSG:4326").boundary.plot(ax=ax, color="#111111", linewidth=1.1)
    ax.set_title("V1 water-history evidence: JRC occurrence", loc="left")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(alpha=0.12)
    cbar = fig.colorbar(img, ax=ax, shrink=0.74, pad=0.03)
    cbar.set_label("Water occurrence (%)")
    save(fig, PANEL_FILES["water"])


def plot_protected_areas() -> None:
    fig, ax = plt.subplots(figsize=(5.2, 6.0))
    bnd = boundary("EPSG:4326")
    try:
        wdpca = gpd.read_file(GPKG, layer="wdpca_protected_polygons_v1").to_crs("EPSG:4326")
    except LAYER_MISSING:
        print(f"layer 'wdpca_protected_polygons_v1' not present in {GPKG.name}; treating as empty", file=sys.stderr)
        wdpca = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    bnd.boundary.plot(ax=ax, color="#111111", linewidth=1.1)
    if not wdpca.empty:
        wdpca.plot(ax=ax, color="#009E73", alpha=0.35, edgecolor="#006D4C", linewidth=1.0)
        for item in wdpca.itertuples():
            pt = item.geometry.representative_point()
            ax.text(pt.x, pt.y, str(item.name_eng), fontsize=7, ha="center", va="center", color="#173B2F")
    ax.set_title("V1 environmental evidence: WDPCA protected areas", loc="left")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(alpha=0.12)
    ax.legend(
        handles=[
            Patch(facecolor="none", edgecolor="#111111", label="V1 boundary"),
            Patch(facecolor="#009E73", edgecolor="#006D4C", alpha=0.35, label="WDPCA overlap"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=2,
        frameon=False,
        fontsize=8,
    )
    save(fig, PANEL_FILES["protected"])


def plot_population() -> None:
    rasters = [
        ("WorldPop 2020 population", RASTER_DIR / "v1_worldpop_2020_unadj_native.tif", "log(1 + population count)"),
        ("GHSL 2025 built-up surface", RASTER_DIR / "v1_ghsl_built_surface_2025_native.tif", "built-up surface"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 5.2), constrained_layout=True)
    for ax, (title, path, label) in zip(axes, rasters, strict=True):
        with rasterio.open(path) as src:
            data = src.read(1).astype("float32")
            if src.nodata is not None:
                data[data == src.nodata] = np.nan
            shown = np.log1p(data) if "WorldPop" in title else data
            img = ax.imshow(shown, cmap="magma", extent=extent(src.bounds), origin="upper")
            boundary(str(src.crs)).boundary.plot(ax=ax, color="#111111", linewidth=1.0)
        ax.set_title(title)
        ax.grid(alpha=0.10)
        cbar = fig.colorbar(img, ax=ax, shrink=0.70, pad=0.02)
        cbar.set_label(label)
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[1].set_xlabel("Easting")
    axes[1].set_ylabel("Northing")
    fig.suptitle("V1 socioeconomic exposure evidence", fontweight="bold")
    save(fig, PANEL_FILES["population"])


def plot_rehab() -> None:
    rasters = [
        ("River proximity", RASTER_DIR / "v1_closeness_to_rivers_0_1_utm35s_30m.tif"),
        ("Road accessibility", RASTER_DIR / "v1_closeness_to_roads_0_1_utm35s_30m.tif"),
        ("Mining-proxy proximity", RASTER_DIR / "v1_closeness_to_mining_proxy_0_1_utm35s_30m.tif"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(9.4, 3.9), constrained_layout=True)
    for ax, (title, path) in zip(axes, rasters, strict=True):
        with rasterio.open(path) as src:
            data = src.read(1).astype("float32")
            data[data == src.nodata] = np.nan
            img = ax.imshow(data, cmap="viridis", extent=extent(src.bounds), origin="upper", vmin=0, vmax=1)
            boundary(str(src.crs)).boundary.plot(ax=ax, color="#111111", linewidth=0.85)
        ax.set_title(title)
        ax.set_xlabel("Easting (km)")
        ax.set_ylabel("Northing (km)")
        ax.xaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.yaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.grid(alpha=0.10)
    cbar = fig.colorbar(img, ax=axes, shrink=0.78, pad=0.02)
    cbar.set_label("0-1 proximity diagnostic")
    save(fig, PANEL_FILES["rehab"])


def write_handoff() -> None:
    matrix = pd.read_csv(MATRIX)
    land = pd.read_csv(LANDCOVER)
    summary = pd.read_csv(SUMMARY)
    worldpop = summary[summary["layer"] == "worldpop_2020_unadj"].iloc[0]
    ghsl_pop = summary[summary["layer"] == "ghsl_population_2025"].iloc[0]
    ghsl_built = summary[summary["layer"] == "ghsl_built_surface_2025"].iloc[0]
    dfo = summary[summary["layer"] == "dfo_zimbabwe_flood_events"].iloc[0]
    wdpca = summary[summary["layer"] == "wdpca_protected_areas_v1"].iloc[0]
    factors = ", ".join(matrix["factor"].drop_duplicates())
    top_land = "; ".join(f"{row.class_name}: {row.share_of_valid_pct:.1f}%" for row in land.sort_values("share_of_valid_pct", ascending=False).head(5).itertuples())
    text = f"""# V1 Full Methodology Evidence Sweep

Status: candidate evidence package generated for mentor review. This is not an AHP overlay, not a
flood-risk map, and not final thesis boundary evidence.

## What Was Processed

- Factors represented in the matrix: {factors}.
- New downloaded inputs: ESA WorldCover 2021, WorldPop Zimbabwe 2020, GHSL Zimbabwe 2025
  built-up/population grids, JRC Global Surface Water occurrence/seasonality/recurrence/change/
  transitions, DFO historical flood events, and WDPCA protected/conserved areas via HDX.
- Existing integrated inputs: CHIRPS rainfall comparison, SRTM terrain diagnostics, Geoportal
  rivers/water/flood-prone zones, HydroRIVERS, and Geofabrik OSM roads/places/landuse.
- DFO Global Flood Archive is processed as Zimbabwe-level historical flood context from the HDX
  SHP package, not as V1 flood extent.

## Key Local Evidence

- WorldCover dominant classes in V1: {top_land}.
- WorldPop 2020 V1 population sum from native raster cells: {worldpop['sum']:.0f}.
- GHSL 2025 V1 population sum from native raster cells: {ghsl_pop['sum']:.0f}; built-up surface
  sum: {ghsl_built['sum']:.1f} in native GHSL units.
- Geoportal Flood Prone Zones local overlap remains 0 features in the current V1 review layers.
- DFO Zimbabwe-related flood records: {int(dfo['feature_count'])}; valid event points within V1
  plus 1 degree: {int(dfo['v1_context_points_plus_1deg'])}.
- WDPCA protected/conserved areas overlapping V1: {int(wdpca['feature_count'])} features,
  about {wdpca['area_km2']:.1f} km2 of polygon overlap.
- OSM mining pressure remains weak proxy evidence: quarry/industrial polygons only, not official
  active ASM footprints.
- Distance/proximity components were generated for rivers, roads, and mining proxy on the V1
  30 m terrain grid; they are rehabilitation/accessibility components only.

## Main Artifacts

- Evidence matrix: `{rel(MATRIX)}`.
- Layer summary: `{rel(SUMMARY)}`.
- Source manifest: `{rel(OUT_DIR / 'source_manifest.csv')}`.
- Review layers: `{rel(GPKG)}`.
- Land-cover class table: `{rel(LANDCOVER)}`.
- JRC surface-water summary: `{rel(GSW)}`.
- GHSL built-up/population summary: `{rel(OUT_DIR / 'v1_ghsl_summary.csv')}`.
- Rehabilitation proxy components: `{rel(OUT_DIR / 'v1_rehabilitation_proxy_components.csv')}`.
- DFO Zimbabwe historical flood records: `{rel(OUT_DIR / 'v1_dfo_zimbabwe_flood_events.csv')}`.
- WDPCA protected/conserved-area summary: `{rel(OUT_DIR / 'v1_wdpca_protected_area_summary.csv')}`.
- Separate figure panels:
  - `{rel(PANEL_FILES['landcover'])}`
  - `{rel(PANEL_FILES['water'])}`
  - `{rel(PANEL_FILES['protected'])}`
  - `{rel(PANEL_FILES['population'])}`
  - `{rel(PANEL_FILES['rehab'])}`

## Mentor Decisions Still Needed

1. Which evidence families may enter the first prototype criteria set?
2. Should mining pressure remain weak proxy evidence, or is official mining/cadastre data required?
3. Should WDPCA protected-area overlap be used as an environmental sensitivity criterion or
   context only?
4. Should rehabilitation potential be represented by separate components or a mentor-approved
   composite rule?
5. Which rainfall interpretation should be used if rainfall becomes an AHP criterion?
"""
    HANDOFF.write_text(text, encoding="utf-8")
    caption = """Figure set. V1 full methodology evidence panels for mentor review. The panels show land-cover evidence from ESA WorldCover 2021, surface-water history from JRC Global Surface Water, protected/conserved-area overlap from WDPCA, population and built-up exposure from WorldPop 2020 and GHSL 2025, and rehabilitation/accessibility proximity components derived from rivers, roads, and weak mining-proxy features. These panels are candidate evidence only and should not be interpreted as a flood-risk map, weighted overlay, intervention-priority map, or final thesis boundary evidence."""
    CAPTION_MD.write_text("# Caption: V1 Full Methodology Evidence Panels\n\n" + caption + "\n", encoding="utf-8")
    CAPTION_TXT.write_text(caption + "\n", encoding="utf-8")


def main() -> None:
    plot_landcover()
    plot_water()
    plot_protected_areas()
    plot_population()
    plot_rehab()
    write_handoff()
    print(f"wrote {rel(HANDOFF)}")
    for path in PANEL_FILES.values():
        print(f"wrote {rel(path)}")


if __name__ == "__main__":
    main()
