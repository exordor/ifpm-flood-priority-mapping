#!/usr/bin/env python3
"""Export Peru raw input-factor maps with variable-specific units and colors.

These figures show input data or physically meaningful derived layers before
the MCDA 0-1 scoring step. They are intended for PPT/paper-style method slides,
not as final priority or validated flood-risk maps.
"""

from __future__ import annotations

import csv
import math
import textwrap
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap, to_rgba
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, MaxNLocator
from rasterio import features
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.transform import array_bounds
from rasterio.warp import calculate_default_transform, reproject
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps"
INDIVIDUAL_DIR = OUT_DIR / "individual"
DST_CRS = CRS.from_epsg(4326)

BOUNDARY_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
BOUNDARY_LAYER = "peru_pilot_boundary"
REFERENCE_GRID = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"

RASTER_NODATA = -9999.0

INPUTS = [
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/rainfall_climatology_raw_mm_per_season_PROVISIONAL_30m.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_slope_degrees_utm18s_30m.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_twi.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_distance_to_drainage_t500.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_flow_accumulation.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/ls_factor/pe1_ls_factor_capped50_hillslope_30m.tif",
    ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_pe1_30m.tif",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_roads_free_1.shp",
    ROOT / "data/raw/ingemmet_catastro_minero_peru_pilot/pe1_pequena_mineria.gpkg",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_water_a_free_1.shp",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_waterways_free_1.shp",
    ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W072_Map.tif",
    ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif",
]
OUTPUTS = [
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_rainfall_climatology_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_rainfall_climatology_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_elevation_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_elevation_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_slope_degrees_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_slope_degrees_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_twi_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_twi_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_drainage_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_drainage_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_upstream_area_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_upstream_area_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_ls_factor_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_ls_factor_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_c_factor_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_c_factor_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_roads_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_roads_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_ingemmet_small_mining_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_ingemmet_small_mining_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_water_features_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_distance_to_water_features_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_esa_worldcover_2021_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/individual/peru_raw_esa_worldcover_2021_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_hydrology_terrain_input_factors_panel_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_hydrology_terrain_input_factors_panel_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_erosion_land_human_input_factors_panel_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_erosion_land_human_input_factors_panel_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_environmental_context_input_factors_panel_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_environmental_context_input_factors_panel_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_main_12_input_factors_panel_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_main_12_input_factors_panel_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/index.csv",
]

WORLD_COVER_LABELS = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}

WORLD_COVER_COLORS = {
    10: "#006400",
    20: "#ffbb22",
    30: "#ffff4c",
    40: "#f096ff",
    50: "#fa0000",
    60: "#b4b4b4",
    70: "#f0f0f0",
    80: "#0064c8",
    90: "#0096a0",
    95: "#00cf75",
    100: "#fae6a0",
}


@dataclass(frozen=True)
class RasterSpec:
    slug: str
    label: str
    unit: str
    group: str
    source_path: Path
    colors: tuple[str, ...]
    bins: tuple[float, ...]
    data_basis: str
    limitation: str
    transform: Callable[[np.ndarray], np.ndarray] | None = None
    resampling: Resampling = Resampling.bilinear


@dataclass(frozen=True)
class VectorDistanceSpec:
    slug: str
    label: str
    unit: str
    group: str
    source_paths: tuple[Path, ...]
    colors: tuple[str, ...]
    bins: tuple[float, ...]
    data_basis: str
    limitation: str
    bbox_buffer_deg: float = 0.15


@dataclass(frozen=True)
class CategorySpec:
    slug: str
    label: str
    group: str
    source_paths: tuple[Path, ...]
    data_basis: str
    limitation: str


def as_km(data_m: np.ndarray) -> np.ndarray:
    return data_m / 1000.0


def flow_cells_to_upstream_area_km2(data_cells: np.ndarray) -> np.ndarray:
    return data_cells * 900.0 / 1_000_000.0


RASTER_SPECS = [
    RasterSpec(
        slug="rainfall_climatology",
        label="Rainfall climatology",
        unit="mm / rainy season",
        group="hydrology_terrain",
        source_path=ROOT / "outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/rainfall_climatology_raw_mm_per_season_PROVISIONAL_30m.tif",
        colors=("#ffffcc", "#c7e9b4", "#7fcdbb", "#41b6c4", "#2c7fb8", "#253494"),
        bins=(0, 50, 100, 150, 200, 250, 300),
        data_basis="CHIRPS v3 Dec-Mar rainy-season climatology, 2014/15-2023/24, shown in mm per season",
        limitation="coarse ~5 km CHIRPS context resampled to the 30 m display grid",
    ),
    RasterSpec(
        slug="elevation",
        label="Elevation",
        unit="m",
        group="hydrology_terrain",
        source_path=ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif",
        colors=("#d9f0a3", "#addd8e", "#78c679", "#31a354", "#756bb1", "#54278f"),
        bins=(0, 1000, 2000, 3000, 4000, 5000, 6500),
        data_basis="SRTM 1 arc-second DEM reprojected to the Peru reference grid",
        limitation="terrain elevation, not flood depth or inundation",
    ),
    RasterSpec(
        slug="slope_degrees",
        label="Slope",
        unit="degrees",
        group="hydrology_terrain",
        source_path=ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_slope_degrees_utm18s_30m.tif",
        colors=("#ffffcc", "#ffeda0", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"),
        bins=(0, 5, 15, 25, 35, 45, 90),
        data_basis="Slope derived from the SRTM DEM",
        limitation="terrain gradient only; not flow velocity",
    ),
    RasterSpec(
        slug="twi",
        label="Topographic wetness index",
        unit="TWI",
        group="hydrology_terrain",
        source_path=ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_twi.tif",
        colors=("#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#225ea8"),
        bins=(0, 4, 6, 8, 10, 15, 30),
        data_basis="DEM-derived TWI",
        limitation="terrain wetness tendency; not observed flood extent",
    ),
    RasterSpec(
        slug="distance_to_drainage",
        label="Distance to drainage",
        unit="km",
        group="hydrology_terrain",
        source_path=ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_distance_to_drainage_t500.tif",
        colors=("#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#a8ddb5", "#f0f9e8"),
        bins=(0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.6),
        data_basis="Euclidean distance to DEM-derived drainage cells, threshold = 500 contributing cells",
        limitation="distance to extracted drainage, not hydraulic flood routing",
        transform=as_km,
    ),
    RasterSpec(
        slug="upstream_area",
        label="Upstream contributing area",
        unit="km2",
        group="hydrology_terrain",
        source_path=ROOT / "outputs/srtm_1arcsec_peru_pilot/hydrology_derivatives/pe1_flow_accumulation.tif",
        colors=("#f7fcf5", "#c7e9c0", "#74c476", "#31a354", "#006d2c", "#00441b"),
        bins=(0, 0.1, 1, 10, 100, 1000, 3000),
        data_basis="D8 flow accumulation converted from cells to upstream area",
        limitation="DEM-routing proxy; not calibrated discharge",
        transform=flow_cells_to_upstream_area_km2,
        resampling=Resampling.nearest,
    ),
    RasterSpec(
        slug="ls_factor",
        label="LS-factor",
        unit="LS",
        group="erosion_land_human",
        source_path=ROOT / "outputs/srtm_1arcsec_peru_pilot/ls_factor/pe1_ls_factor_capped50_hillslope_30m.tif",
        colors=("#f7fcfd", "#d0d1e6", "#a6bddb", "#74a9cf", "#2b8cbe", "#045a8d"),
        bins=(0, 2, 5, 10, 20, 35, 50),
        data_basis="SRTM-derived hillslope LS-factor, capped at 50",
        limitation="USLE terrain factor; main-channel cells are masked",
    ),
    RasterSpec(
        slug="c_factor",
        label="C-factor",
        unit="C",
        group="erosion_land_human",
        source_path=ROOT / "outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_pe1_30m.tif",
        colors=("#006837", "#31a354", "#addd8e", "#ffffbf", "#fdae61", "#d7191c"),
        bins=(0, 0.05, 0.1, 0.2, 0.4, 0.7, 1.0),
        data_basis="ESA WorldCover-derived cover-management C-factor",
        limitation="class-based C-factor proxy, not locally measured cover management",
    ),
]

VECTOR_DISTANCE_SPECS = [
    VectorDistanceSpec(
        slug="distance_to_roads",
        label="Distance to roads",
        unit="km",
        group="erosion_land_human",
        source_paths=(ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_roads_free_1.shp",),
        colors=("#8c510a", "#d8b365", "#f6e8c3", "#c7eae5", "#5ab4ac", "#01665e"),
        bins=(0, 0.25, 0.5, 1, 2, 5, 10),
        data_basis="Euclidean distance to OpenStreetMap / Geofabrik road lines",
        limitation="access-distance context, not socioeconomic vulnerability",
        bbox_buffer_deg=0.08,
    ),
    VectorDistanceSpec(
        slug="distance_to_ingemmet_small_mining",
        label="Distance to INGEMMET small-mining points",
        unit="km",
        group="erosion_land_human",
        source_paths=(ROOT / "data/raw/ingemmet_catastro_minero_peru_pilot/pe1_pequena_mineria.gpkg",),
        colors=("#ffffcc", "#ffeda0", "#feb24c", "#fd8d3c", "#e31a1c", "#800026"),
        bins=(0, 2.5, 5, 10, 20, 40, 70),
        data_basis="Euclidean distance to official INGEMMET SERV_PEQUENA_MINERIA points",
        limitation="distance to official small-mining point evidence, not active footprint",
        bbox_buffer_deg=0.25,
    ),
    VectorDistanceSpec(
        slug="distance_to_water_features",
        label="Distance to water features",
        unit="km",
        group="environmental_context",
        source_paths=(
            ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_water_a_free_1.shp",
            ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_waterways_free_1.shp",
        ),
        colors=("#08306b", "#2171b5", "#6baed6", "#bdd7e7", "#eff3ff", "#f7fbff"),
        bins=(0, 0.25, 0.5, 1, 2, 5, 15),
        data_basis="Euclidean distance to OSM water polygons and waterways",
        limitation="water-context distance only; not ecological valuation",
        bbox_buffer_deg=0.15,
    ),
]

CATEGORY_SPECS = [
    CategorySpec(
        slug="esa_worldcover_2021",
        label="ESA WorldCover 2021",
        group="erosion_land_human",
        source_paths=(
            ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W072_Map.tif",
            ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif",
        ),
        data_basis="ESA WorldCover 2021 categorical land-cover classes",
        limitation="10 m global land-cover map resampled to display resolution",
    )
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


SKIPPED_RAW_FACTORS = [
    {
        "factor": "soil_k_factor",
        "label": "Soil K-factor",
        "group": "erosion_land_human",
        "unit": "K",
        "map_type": "not_generated_georeferencing_mismatch",
        "source_path": rel(ROOT / "outputs/soilgrids_250m_peru_pilot/k_factor_pe1_0_30cm_avg_250m.tif"),
        "classification": "not rendered",
        "data_basis": "SoilGrids-derived K-factor, 0-30 cm average",
        "limitation": "Current native SoilGrids Interrupted Goode Homolosine raster does not reproject to the Peru boundary location cleanly for slide-ready mapping; treat K as an unresolved raw-map issue.",
    }
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_boundary() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    boundary_wgs84 = gpd.read_file(BOUNDARY_GPKG, layer=BOUNDARY_LAYER).to_crs(DST_CRS)
    with rasterio.open(REFERENCE_GRID) as src:
        boundary_ref = boundary_wgs84.to_crs(src.crs)
    return boundary_wgs84, boundary_ref


def expanded_bounds(bounds: tuple[float, float, float, float], pad: float) -> tuple[float, float, float, float]:
    west, south, east, north = bounds
    return west - pad, south - pad, east + pad, north + pad


def degree_formatter(kind: str):
    def _format(value: float, _: int) -> str:
        hemi = "E" if kind == "lon" and value >= 0 else "W" if kind == "lon" else "N" if value >= 0 else "S"
        val = abs(value)
        deg = int(val)
        minutes = int(round((val - deg) * 60))
        if minutes == 60:
            deg += 1
            minutes = 0
        if minutes == 0:
            return f"{deg}°{hemi}"
        return f"{deg}°{minutes}'{hemi}"

    return _format


def nice_scale_length(width_km: float) -> int:
    candidates = [1, 2, 5, 10, 20, 25, 50, 100, 200]
    target = width_km / 4.0
    return max([value for value in candidates if value <= target] or [1])


def add_scale_bar(ax, extent: tuple[float, float, float, float], fontsize: int = 8) -> None:
    west, east, south, north = extent
    mid_lat = (south + north) / 2
    width_km = (east - west) * 111.32 * math.cos(math.radians(mid_lat))
    length_km = nice_scale_length(width_km)
    length_deg = length_km / (111.32 * math.cos(math.radians(south + (north - south) * 0.09)))
    x0 = east - (east - west) * 0.08 - length_deg
    y0 = south + (north - south) * 0.045
    bar_h = (north - south) * 0.011
    segments = 4
    seg_len = length_deg / segments
    for idx in range(segments):
        ax.add_patch(
            Rectangle(
                (x0 + idx * seg_len, y0),
                seg_len,
                bar_h,
                facecolor="black" if idx % 2 == 0 else "white",
                edgecolor="black",
                linewidth=0.7,
                zorder=8,
            )
        )
    ax.text(x0, y0 + bar_h * 1.55, "0", ha="center", va="bottom", fontsize=fontsize, zorder=8)
    ax.text(x0 + length_deg / 2, y0 + bar_h * 1.55, f"{length_km / 2:g}", ha="center", va="bottom", fontsize=fontsize, zorder=8)
    ax.text(x0 + length_deg, y0 + bar_h * 1.55, f"{length_km:g}", ha="center", va="bottom", fontsize=fontsize, zorder=8)
    ax.text(x0 + length_deg / 2, y0 - bar_h * 0.65, "Kilometers", ha="center", va="top", fontsize=fontsize, zorder=8)


def add_north_arrow(ax, fontsize: int = 12, compact: bool = False) -> None:
    x = 0.91
    text_y = 0.96 if not compact else 0.93
    arrow_top = 0.91 if not compact else 0.88
    arrow_bottom = 0.80 if not compact else 0.78
    width = 7 if not compact else 3.2
    headwidth = 22 if not compact else 12
    headlength = 26 if not compact else 14
    ax.text(x, text_y, "N", transform=ax.transAxes, ha="center", va="bottom", fontsize=fontsize, family="serif", zorder=8)
    ax.annotate(
        "",
        xy=(x, arrow_top),
        xytext=(x, arrow_bottom),
        xycoords="axes fraction",
        arrowprops={"facecolor": "black", "edgecolor": "black", "width": width, "headwidth": headwidth, "headlength": headlength},
    )


def frame_extent_for_map(extent: tuple[float, float, float, float], bottom: float = 0.22) -> tuple[float, float, float, float]:
    west, east, south, north = extent
    width = east - west
    height = north - south
    return (
        west - width * 0.02,
        east + width * 0.02,
        south - height * bottom,
        north + height * 0.03,
    )


def add_boundary_and_frame(
    ax,
    boundary_wgs84: gpd.GeoDataFrame,
    frame_extent: tuple[float, float, float, float],
    tick_size: int,
) -> None:
    boundary_wgs84.boundary.plot(ax=ax, color="#222222", linewidth=0.9, zorder=7)
    ax.set_xlim(frame_extent[0], frame_extent[1])
    ax.set_ylim(frame_extent[2], frame_extent[3])
    ax.xaxis.set_major_locator(MaxNLocator(3))
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(FuncFormatter(degree_formatter("lon")))
    ax.yaxis.set_major_formatter(FuncFormatter(degree_formatter("lat")))
    ax.tick_params(
        top=True,
        bottom=True,
        left=True,
        right=True,
        labeltop=True,
        labelbottom=True,
        labelleft=True,
        labelright=True,
        labelsize=tick_size,
        pad=2,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def read_raster_data(path: Path, transform: Callable[[np.ndarray], np.ndarray] | None) -> tuple[np.ndarray, dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        valid = np.isfinite(data)
        if src.nodata is not None:
            valid &= data != src.nodata
        data = np.where(valid, data, np.nan).astype("float32")
        if transform is not None:
            data = transform(data).astype("float32")
        profile = {
            "crs": src.crs,
            "transform": src.transform,
            "width": src.width,
            "height": src.height,
        }
    return data, profile


def reproject_data_to_wgs84(
    data: np.ndarray,
    profile: dict,
    resampling: Resampling,
    nodata: float = RASTER_NODATA,
) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    bounds = array_bounds(profile["height"], profile["width"], profile["transform"])
    dst_transform, dst_width, dst_height = calculate_default_transform(
        profile["crs"],
        DST_CRS,
        profile["width"],
        profile["height"],
        *bounds,
    )
    src = np.where(np.isfinite(data), data, nodata).astype("float32")
    dst = np.full((dst_height, dst_width), nodata, dtype="float32")
    reproject(
        source=src,
        destination=dst,
        src_transform=profile["transform"],
        src_crs=profile["crs"],
        src_nodata=nodata,
        dst_transform=dst_transform,
        dst_crs=DST_CRS,
        dst_nodata=nodata,
        resampling=resampling,
    )
    dst = np.where(dst == nodata, np.nan, dst)
    west, south, east, north = array_bounds(dst_height, dst_width, dst_transform)
    return dst, (west, east, south, north)


def reference_mask(boundary_ref: gpd.GeoDataFrame) -> tuple[np.ndarray, dict]:
    with rasterio.open(REFERENCE_GRID) as src:
        profile = {
            "crs": src.crs,
            "transform": src.transform,
            "width": src.width,
            "height": src.height,
        }
        mask = features.rasterize(
            ((geom, 1) for geom in boundary_ref.geometry),
            out_shape=(src.height, src.width),
            transform=src.transform,
            fill=0,
            dtype="uint8",
            all_touched=True,
        ).astype(bool)
    return mask, profile


def mask_to_reference_boundary(data: np.ndarray, profile: dict, boundary_mask: np.ndarray, reference_profile: dict) -> np.ndarray:
    same_crs = profile["crs"] == reference_profile["crs"]
    same_shape = profile["width"] == reference_profile["width"] and profile["height"] == reference_profile["height"]
    same_transform = profile["transform"].almost_equals(reference_profile["transform"])
    if same_crs and same_shape and same_transform:
        out = data.copy()
        out[~boundary_mask] = np.nan
        return out
    return data


def distance_from_vectors_km(spec: VectorDistanceSpec, boundary_wgs84: gpd.GeoDataFrame, boundary_ref: gpd.GeoDataFrame) -> tuple[np.ndarray, dict, int]:
    boundary_mask, profile = reference_mask(boundary_ref)
    bbox = expanded_bounds(tuple(boundary_wgs84.total_bounds), spec.bbox_buffer_deg)
    parts: list[gpd.GeoDataFrame] = []
    for path in spec.source_paths:
        if not path.exists():
            raise FileNotFoundError(path)
        gdf = gpd.read_file(path, bbox=bbox)
        if len(gdf) == 0:
            continue
        parts.append(gdf[["geometry"]].to_crs(profile["crs"]))
    if not parts:
        empty = np.full(boundary_mask.shape, np.nan, dtype="float32")
        return empty, profile, 0
    features_gdf = gpd.GeoDataFrame(
        geometry=np.concatenate([part.geometry.values for part in parts]),
        crs=profile["crs"],
    )
    feature_mask = features.rasterize(
        ((geom, 1) for geom in features_gdf.geometry if geom is not None and not geom.is_empty),
        out_shape=boundary_mask.shape,
        transform=profile["transform"],
        fill=0,
        dtype="uint8",
        all_touched=True,
    ).astype(bool)
    if not feature_mask.any():
        empty = np.full(boundary_mask.shape, np.nan, dtype="float32")
        return empty, profile, len(features_gdf)
    pixel_y = abs(profile["transform"].e)
    pixel_x = abs(profile["transform"].a)
    distance_m = distance_transform_edt(~feature_mask, sampling=(pixel_y, pixel_x)).astype("float32")
    distance_km = distance_m / 1000.0
    distance_km[~boundary_mask] = np.nan
    return distance_km, profile, len(features_gdf)


def load_worldcover(boundary_wgs84: gpd.GeoDataFrame) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    bounds = expanded_bounds(tuple(boundary_wgs84.total_bounds), 0.02)
    datasets = [rasterio.open(path) for path in CATEGORY_SPECS[0].source_paths]
    try:
        mosaic, transform = merge(
            datasets,
            bounds=bounds,
            res=(1 / 3600, 1 / 3600),
            nodata=0,
            resampling=Resampling.nearest,
        )
    finally:
        for dataset in datasets:
            dataset.close()
    data = mosaic[0].astype("uint16")
    mask = features.rasterize(
        ((geom, 1) for geom in boundary_wgs84.geometry),
        out_shape=data.shape,
        transform=transform,
        fill=0,
        dtype="uint8",
        all_touched=True,
    ).astype(bool)
    data[~mask] = 0
    west, south, east, north = array_bounds(data.shape[0], data.shape[1], transform)
    return data, (west, east, south, north)


def value_stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "valid_fraction": round(float(values.size / data.size), 6),
        "min": round(float(values.min()), 6) if values.size else "",
        "mean": round(float(values.mean()), 6) if values.size else "",
        "max": round(float(values.max()), 6) if values.size else "",
    }


def class_labels(bins: tuple[float, ...], unit: str) -> list[str]:
    labels = []
    for lo, hi in zip(bins[:-1], bins[1:], strict=True):
        labels.append(f"{lo:g}-{hi:g} {unit}".strip())
    return labels


def add_continuous_legend(ax, colors: Iterable[str], labels: Iterable[str], title: str, compact: bool) -> None:
    handles = [Patch(facecolor=color, edgecolor="0.4", label=label) for color, label in zip(colors, labels, strict=True)]
    legend = ax.legend(
        handles=handles,
        title=title,
        loc="lower left",
        bbox_to_anchor=(0.055, 0.035),
        frameon=True,
        framealpha=0.94,
        facecolor="white",
        edgecolor="white",
        fontsize=5 if compact else 7,
        title_fontsize=6 if compact else 8,
        handlelength=1.2,
        borderpad=0.35,
        labelspacing=0.35,
    )
    legend._legend_box.align = "left"


def add_category_legend(ax, codes: list[int], compact: bool) -> None:
    handles = [
        Patch(facecolor=WORLD_COVER_COLORS.get(code, "#ffffff"), edgecolor="0.4", label=WORLD_COVER_LABELS.get(code, str(code)))
        for code in codes
    ]
    legend = ax.legend(
        handles=handles,
        title="WorldCover class",
        loc="lower left",
        bbox_to_anchor=(0.055, 0.035),
        frameon=True,
        framealpha=0.94,
        facecolor="white",
        edgecolor="white",
        fontsize=5 if compact else 7,
        title_fontsize=6 if compact else 8,
        handlelength=1.2,
        borderpad=0.35,
        labelspacing=0.35,
    )
    legend._legend_box.align = "left"


def draw_continuous_map(
    ax,
    spec: RasterSpec | VectorDistanceSpec,
    data_wgs84: np.ndarray,
    extent: tuple[float, float, float, float],
    boundary_wgs84: gpd.GeoDataFrame,
    panel_label: str | None = None,
    compact: bool = False,
) -> None:
    frame_extent = frame_extent_for_map(extent, bottom=0.25 if not compact else 0.22)
    cmap = ListedColormap(spec.colors)
    norm = BoundaryNorm(spec.bins, len(spec.colors), clip=True)
    masked = np.ma.masked_invalid(data_wgs84)
    ax.imshow(masked, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    add_boundary_and_frame(ax, boundary_wgs84, frame_extent, tick_size=5 if compact else 8)
    if panel_label is not None:
        label = textwrap.fill(f"{panel_label} {spec.label}", width=30)
        ax.text(
            0.03,
            0.965,
            label,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8 if compact else 10,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "none", "alpha": 0.88},
            zorder=9,
        )
    add_north_arrow(ax, fontsize=8 if compact else 12, compact=compact)
    add_scale_bar(ax, frame_extent, fontsize=5 if compact else 8)
    add_continuous_legend(ax, spec.colors, class_labels(spec.bins, spec.unit), spec.unit, compact=compact)


def draw_category_map(
    ax,
    spec: CategorySpec,
    data_wgs84: np.ndarray,
    extent: tuple[float, float, float, float],
    boundary_wgs84: gpd.GeoDataFrame,
    panel_label: str | None = None,
    compact: bool = False,
) -> None:
    frame_extent = frame_extent_for_map(extent, bottom=0.25 if not compact else 0.22)
    rgba = np.zeros((data_wgs84.shape[0], data_wgs84.shape[1], 4), dtype="float32")
    present_codes = sorted(int(code) for code in np.unique(data_wgs84) if int(code) in WORLD_COVER_COLORS)
    for code in present_codes:
        rgba[data_wgs84 == code] = to_rgba(WORLD_COVER_COLORS[code])
    ax.imshow(rgba, extent=extent, origin="upper", interpolation="nearest", zorder=1)
    add_boundary_and_frame(ax, boundary_wgs84, frame_extent, tick_size=5 if compact else 8)
    if panel_label is not None:
        label = textwrap.fill(f"{panel_label} {spec.label}", width=30)
        ax.text(
            0.03,
            0.965,
            label,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8 if compact else 10,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "none", "alpha": 0.88},
            zorder=9,
        )
    add_north_arrow(ax, fontsize=8 if compact else 12, compact=compact)
    add_scale_bar(ax, frame_extent, fontsize=5 if compact else 8)
    add_category_legend(ax, present_codes, compact=compact)


def save_individual_png_pdf(
    slug: str,
    draw_fn: Callable[[plt.Axes], None],
) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    draw_fn(ax)
    png = INDIVIDUAL_DIR / f"peru_raw_{slug}_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return png, pdf


def save_panel(
    slug: str,
    prepared_items: list[dict[str, object]],
    boundary_wgs84: gpd.GeoDataFrame,
    columns: int = 3,
) -> tuple[Path, Path]:
    rows = int(math.ceil(len(prepared_items) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(columns * 4.7, rows * 5.25), constrained_layout=False)
    fig.subplots_adjust(left=0.045, right=0.985, top=0.97, bottom=0.045, wspace=0.16, hspace=0.25)
    axes_flat = np.atleast_1d(axes).ravel()
    labels = [f"({chr(97 + idx)})" for idx in range(len(prepared_items))]
    for ax, item, panel_label in zip(axes_flat, prepared_items, labels, strict=False):
        if item["kind"] == "category":
            draw_category_map(
                ax,
                item["spec"],
                item["data_wgs84"],
                item["extent"],
                boundary_wgs84,
                panel_label=panel_label,
                compact=True,
            )
        else:
            draw_continuous_map(
                ax,
                item["spec"],
                item["data_wgs84"],
                item["extent"],
                boundary_wgs84,
                panel_label=panel_label,
                compact=True,
            )
    for ax in axes_flat[len(prepared_items):]:
        ax.axis("off")
    png = OUT_DIR / f"peru_raw_{slug}_input_factors_panel_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return png, pdf


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    boundary_wgs84, boundary_ref = load_boundary()
    boundary_mask_ref, reference_profile = reference_mask(boundary_ref)
    rows: list[dict[str, object]] = []
    prepared: list[dict[str, object]] = []

    for spec in RASTER_SPECS:
        data, profile = read_raster_data(spec.source_path, spec.transform)
        data = mask_to_reference_boundary(data, profile, boundary_mask_ref, reference_profile)
        data_wgs84, extent = reproject_data_to_wgs84(data, profile, spec.resampling)
        item = {"kind": "continuous", "spec": spec, "data_wgs84": data_wgs84, "extent": extent}
        prepared.append(item)
        png, pdf = save_individual_png_pdf(
            spec.slug,
            lambda ax, item=item: draw_continuous_map(
                ax,
                item["spec"],
                item["data_wgs84"],
                item["extent"],
                boundary_wgs84,
                panel_label=None,
                compact=False,
            ),
        )
        stats = value_stats(data)
        for fmt, path in (("png", png), ("pdf", pdf)):
            rows.append(
                {
                    "site": "Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
                    "factor": spec.slug,
                    "label": spec.label,
                    "group": spec.group,
                    "unit": spec.unit,
                    "map_type": "raw_or_physical_derived_continuous",
                    "figure_format": fmt,
                    "figure_path": rel(path),
                    "source_path": rel(spec.source_path),
                    "classification": "variable-specific physical-unit classes",
                    "data_basis": spec.data_basis,
                    "limitation": spec.limitation,
                    **stats,
                }
            )

    worldcover_spec = CATEGORY_SPECS[0]
    worldcover, worldcover_extent = load_worldcover(boundary_wgs84)
    worldcover_item = {
        "kind": "category",
        "spec": worldcover_spec,
        "data_wgs84": worldcover,
        "extent": worldcover_extent,
    }
    prepared.append(worldcover_item)
    png, pdf = save_individual_png_pdf(
        worldcover_spec.slug,
        lambda ax, item=worldcover_item: draw_category_map(
            ax,
            item["spec"],
            item["data_wgs84"],
            item["extent"],
            boundary_wgs84,
            panel_label=None,
            compact=False,
        ),
    )
    present_codes = sorted(int(code) for code in np.unique(worldcover) if int(code) in WORLD_COVER_LABELS)
    for fmt, path in (("png", png), ("pdf", pdf)):
        rows.append(
            {
                "site": "Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
                "factor": worldcover_spec.slug,
                "label": worldcover_spec.label,
                "group": worldcover_spec.group,
                "unit": "land-cover class",
                "map_type": "raw_categorical",
                "figure_format": fmt,
                "figure_path": rel(path),
                "source_path": "; ".join(rel(path) for path in worldcover_spec.source_paths),
                "classification": "ESA WorldCover 2021 class codes",
                "data_basis": worldcover_spec.data_basis,
                "limitation": worldcover_spec.limitation,
                "present_classes": "; ".join(WORLD_COVER_LABELS[code] for code in present_codes),
            }
        )

    for spec in VECTOR_DISTANCE_SPECS:
        data, profile, feature_count = distance_from_vectors_km(spec, boundary_wgs84, boundary_ref)
        data_wgs84, extent = reproject_data_to_wgs84(data, profile, Resampling.bilinear)
        item = {"kind": "continuous", "spec": spec, "data_wgs84": data_wgs84, "extent": extent}
        prepared.append(item)
        png, pdf = save_individual_png_pdf(
            spec.slug,
            lambda ax, item=item: draw_continuous_map(
                ax,
                item["spec"],
                item["data_wgs84"],
                item["extent"],
                boundary_wgs84,
                panel_label=None,
                compact=False,
            ),
        )
        stats = value_stats(data)
        for fmt, path in (("png", png), ("pdf", pdf)):
            rows.append(
                {
                    "site": "Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
                    "factor": spec.slug,
                    "label": spec.label,
                    "group": spec.group,
                    "unit": spec.unit,
                    "map_type": "raw_vector_distance",
                    "figure_format": fmt,
                    "figure_path": rel(path),
                    "source_path": "; ".join(rel(path) for path in spec.source_paths),
                    "classification": "variable-specific physical-distance classes",
                    "source_feature_count_after_bbox_filter": feature_count,
                    "data_basis": spec.data_basis,
                    "limitation": spec.limitation,
                    **stats,
                }
            )

    by_group = {
        "hydrology_terrain": [item for item in prepared if item["spec"].group == "hydrology_terrain"],
        "erosion_land_human": [item for item in prepared if item["spec"].group == "erosion_land_human"],
        "environmental_context": [item for item in prepared if item["spec"].group == "environmental_context"],
    }
    for group, items in by_group.items():
        if not items:
            continue
        png, pdf = save_panel(group, items, boundary_wgs84)
        for fmt, path in (("png", png), ("pdf", pdf)):
            rows.append(
                {
                    "panel": group,
                    "figure_format": fmt,
                    "figure_path": rel(path),
                    "factors": ", ".join(item["spec"].slug for item in items),
                    "classification": "raw unit/category classes; no 0-1 normalization legend",
                }
            )

    main_items = by_group["hydrology_terrain"] + by_group["erosion_land_human"][:5] + by_group["environmental_context"][:1]
    png, pdf = save_panel("main_12", main_items, boundary_wgs84)
    for fmt, path in (("png", png), ("pdf", pdf)):
        rows.append(
            {
                "panel": "main_12",
                "figure_format": fmt,
                "figure_path": rel(path),
                "factors": ", ".join(item["spec"].slug for item in main_items),
                "classification": "raw unit/category classes; no 0-1 normalization legend",
            }
        )

    rows.extend(SKIPPED_RAW_FACTORS)
    write_csv(OUT_DIR / "index.csv", rows)
    print(f"wrote {len(rows)} raw input-factor map records to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
