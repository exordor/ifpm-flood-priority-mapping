#!/usr/bin/env python3
"""Export Peru conditioning-factor maps for PPT and paper-style review.

These maps show standardized 0-1 conditioning-factor scores, not final PIM
criterion scores and not validated flood-risk outputs. The individual maps and
panel figures are designed as slide-ready images without global titles or
captions so surrounding PPT text can supply the interpretation.
"""

from __future__ import annotations

import csv
import math
import textwrap
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, MaxNLocator
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import array_bounds
from rasterio.warp import calculate_default_transform, reproject


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps"
INDIVIDUAL_DIR = OUT_DIR / "individual"
DST_CRS = CRS.from_epsg(4326)

CRITERIA_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria"
ES_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1"
BOUNDARY_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
BOUNDARY_LAYER = "peru_pilot_boundary"

INPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/rainfall_climatology_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/twi_wetness_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/drainage_proximity_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/ls_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/c_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/soil_erosion_factors_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/mining_pressure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/road_access_proximity_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/water_wetland_context_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/protected_area_context_0_1.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_rainfall_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_rainfall_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_twi_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_twi_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_drainage_proximity_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_drainage_proximity_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_ls_factor_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_ls_factor_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_c_factor_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_c_factor_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_soil_erosion_structure_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_soil_erosion_structure_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_land_cover_pressure_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_land_cover_pressure_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_mining_pressure_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_mining_pressure_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_road_access_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_road_access_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_water_wetland_context_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_water_wetland_context_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_protected_ecological_context_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/individual/peru_protected_ecological_context_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/peru_physical_conditioning_factors_panel_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/peru_physical_conditioning_factors_panel_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/peru_human_environment_conditioning_factors_panel_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/peru_human_environment_conditioning_factors_panel_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_conditioning_factor_maps/index.csv",
]

BOUNDS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.000001]
LABELS = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
SCORE_COLORS = ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"]


@dataclass(frozen=True)
class Factor:
    slug: str
    label: str
    source_raster: Path
    group: str
    claim_level: str
    data_basis: str
    limitation: str


FACTORS = [
    Factor(
        slug="rainfall",
        label="Rainfall",
        source_raster=CRITERIA_DIR / "rainfall_climatology_0_1.tif",
        group="physical",
        claim_level="sensitivity_scenario",
        data_basis="CHIRPS rainy-season climatology, standardized to 0-1",
        limitation="coarse rainfall context, not native 30 m rainfall",
    ),
    Factor(
        slug="twi",
        label="TWI",
        source_raster=CRITERIA_DIR / "twi_wetness_0_1.tif",
        group="physical",
        claim_level="diagnostic_only",
        data_basis="SRTM DEM-derived topographic wetness index, high wetness -> high score",
        limitation="terrain-conditioning indicator, not observed inundation",
    ),
    Factor(
        slug="drainage_proximity",
        label="Drainage proximity",
        source_raster=CRITERIA_DIR / "drainage_proximity_0_1.tif",
        group="physical",
        claim_level="diagnostic_only",
        data_basis="DEM-derived drainage proximity, closer to drainage -> high score",
        limitation="network proximity indicator, not hydraulic routing",
    ),
    Factor(
        slug="ls_factor",
        label="LS-factor",
        source_raster=CRITERIA_DIR / "ls_factor_0_1.tif",
        group="physical",
        claim_level="diagnostic_only",
        data_basis="SRTM LS-factor standardized to 0-1",
        limitation="terrain erosion structure only",
    ),
    Factor(
        slug="c_factor",
        label="C-factor",
        source_raster=CRITERIA_DIR / "c_factor_0_1.tif",
        group="physical",
        claim_level="diagnostic_only",
        data_basis="ESA WorldCover C-factor standardized to 0-1",
        limitation="land-cover proxy, not field-measured cover management",
    ),
    Factor(
        slug="soil_erosion_structure",
        label="Soil erosion structure",
        source_raster=CRITERIA_DIR / "soil_erosion_factors_0_1.tif",
        group="physical",
        claim_level="diagnostic_only",
        data_basis="K x LS x C erosion-source structure standardized to 0-1",
        limitation="rainfall erosivity not applied",
    ),
    Factor(
        slug="land_cover_pressure",
        label="Land-cover pressure",
        source_raster=CRITERIA_DIR / "land_cover_pressure_0_1.tif",
        group="human_environment",
        claim_level="provisional",
        data_basis="ESA WorldCover land-cover pressure",
        limitation="class-based pressure score, not local field survey",
    ),
    Factor(
        slug="mining_pressure",
        label="Mining pressure",
        source_raster=CRITERIA_DIR / "mining_pressure_0_1.tif",
        group="human_environment",
        claim_level="provisional",
        data_basis="INGEMMET small-mining point proximity",
        limitation="point proximity, not active mining footprint",
    ),
    Factor(
        slug="road_access",
        label="Road/access proximity",
        source_raster=CRITERIA_DIR / "road_access_proximity_0_1.tif",
        group="human_environment",
        claim_level="provisional",
        data_basis="OSM road/access proximity",
        limitation="access indicator, not observed socioeconomic vulnerability",
    ),
    Factor(
        slug="water_wetland_context",
        label="Water/wetland context",
        source_raster=ES_DIR / "water_wetland_context_0_1.tif",
        group="human_environment",
        claim_level="provisional",
        data_basis="WorldCover water/wetland evidence plus OSM water layers",
        limitation="environmental context indicator, not ecological valuation",
    ),
    Factor(
        slug="protected_ecological_context",
        label="Protected/ecological context",
        source_raster=ES_DIR / "protected_area_context_0_1.tif",
        group="human_environment",
        claim_level="provisional",
        data_basis="OSM protected-area proximity",
        limitation="protected/ecological context indicator only",
    ),
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


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


def read_raster(path: Path) -> tuple[np.ndarray, dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        data[~np.isfinite(data)] = np.nan
        profile = {
            "crs": src.crs,
            "transform": src.transform,
            "width": src.width,
            "height": src.height,
        }
    return data, profile


def classify_equal_interval(data: np.ndarray) -> np.ndarray:
    classes = np.zeros(data.shape, dtype="uint8")
    valid = np.isfinite(data)
    classes[valid] = (
        np.digitize(np.clip(data[valid], BOUNDS[0], BOUNDS[-1]), BOUNDS[1:-1], right=False)
        + 1
    )
    return classes


def reproject_class(classes: np.ndarray, profile: dict) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    bounds = array_bounds(profile["height"], profile["width"], profile["transform"])
    dst_transform, dst_width, dst_height = calculate_default_transform(
        profile["crs"],
        DST_CRS,
        profile["width"],
        profile["height"],
        *bounds,
    )
    dst = np.zeros((dst_height, dst_width), dtype="uint8")
    reproject(
        source=classes,
        destination=dst,
        src_transform=profile["transform"],
        src_crs=profile["crs"],
        src_nodata=0,
        dst_transform=dst_transform,
        dst_crs=DST_CRS,
        dst_nodata=0,
        resampling=Resampling.nearest,
    )
    west, south, east, north = array_bounds(dst_height, dst_width, dst_transform)
    return dst, (west, east, south, north)


def frame_extent_for_legend(extent: tuple[float, float, float, float], bottom: float = 0.24) -> tuple[float, float, float, float]:
    west, east, south, north = extent
    width = east - west
    height = north - south
    return (
        west - width * 0.02,
        east + width * 0.02,
        south - height * bottom,
        north + height * 0.02,
    )


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
    bar_h = (north - south) * 0.012
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
                zorder=5,
            )
        )
    ax.text(x0, y0 + bar_h * 1.55, "0", ha="center", va="bottom", fontsize=fontsize)
    ax.text(x0 + length_deg / 2, y0 + bar_h * 1.55, f"{length_km / 2:g}", ha="center", va="bottom", fontsize=fontsize)
    ax.text(x0 + length_deg, y0 + bar_h * 1.55, f"{length_km:g}", ha="center", va="bottom", fontsize=fontsize)
    ax.text(x0 + length_deg / 2, y0 - bar_h * 0.55, "Kilometers", ha="center", va="top", fontsize=fontsize)


def add_north_arrow(
    ax,
    fontsize: int = 12,
    x: float = 0.92,
    text_y: float = 0.96,
    arrow_top: float = 0.91,
    arrow_bottom: float = 0.80,
    width: float = 7,
    headwidth: float = 22,
    headlength: float = 26,
) -> None:
    ax.text(
        x,
        text_y,
        "N",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=fontsize,
        family="serif",
        zorder=8,
    )
    ax.annotate(
        "",
        xy=(x, arrow_top),
        xytext=(x, arrow_bottom),
        xycoords="axes fraction",
        arrowprops={
            "facecolor": "black",
            "edgecolor": "black",
            "width": width,
            "headwidth": headwidth,
            "headlength": headlength,
        },
    )


def add_boundary_and_frame(
    ax,
    extent: tuple[float, float, float, float],
    tick_size: int,
    show_tick_labels: bool = True,
    compact_coord_labels: bool = False,
) -> None:
    boundary = gpd.read_file(BOUNDARY_GPKG, layer=BOUNDARY_LAYER).to_crs(DST_CRS)
    boundary.boundary.plot(ax=ax, color="#222222", linewidth=0.9, zorder=4)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.xaxis.set_major_locator(MaxNLocator(3 if compact_coord_labels else 4))
    ax.yaxis.set_major_locator(MaxNLocator(3 if compact_coord_labels else 5))
    ax.xaxis.set_major_formatter(FuncFormatter(degree_formatter("lon")))
    ax.yaxis.set_major_formatter(FuncFormatter(degree_formatter("lat")))
    ax.tick_params(
        top=True,
        bottom=True,
        left=True,
        right=True,
        labeltop=show_tick_labels,
        labelbottom=show_tick_labels,
        labelleft=show_tick_labels,
        labelright=show_tick_labels,
        labelsize=tick_size,
        pad=2,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def add_legend(ax, title: str, fontsize: int = 8, title_fontsize: int = 9) -> None:
    handles = [
        Patch(facecolor=color, edgecolor="0.4", label=label)
        for label, color in zip(LABELS, SCORE_COLORS, strict=True)
    ]
    legend = ax.legend(
        handles=handles,
        title=title,
        loc="lower left",
        bbox_to_anchor=(0.065, 0.035),
        frameon=True,
        framealpha=0.92,
        facecolor="white",
        edgecolor="white",
        fontsize=fontsize,
        title_fontsize=title_fontsize,
    )
    legend._legend_box.align = "left"


def raster_stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "valid_fraction": round(float(values.size / data.size), 6),
        "min": round(float(values.min()), 6) if values.size else "",
        "mean": round(float(values.mean()), 6) if values.size else "",
        "max": round(float(values.max()), 6) if values.size else "",
    }


def draw_factor(
    ax,
    factor: Factor,
    dst: np.ndarray,
    extent: tuple[float, float, float, float],
    frame_extent: tuple[float, float, float, float],
    panel_label: str | None,
    compact: bool,
) -> None:
    cmap = ListedColormap(SCORE_COLORS)
    norm = BoundaryNorm(np.arange(0.5, len(SCORE_COLORS) + 1.5), len(SCORE_COLORS))
    masked = np.ma.masked_where(dst == 0, dst)
    ax.imshow(masked, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    add_boundary_and_frame(
        ax,
        frame_extent,
        tick_size=5 if compact else 8,
        show_tick_labels=True,
        compact_coord_labels=compact,
    )
    if compact:
        add_north_arrow(
            ax,
            fontsize=8,
            x=0.92,
            text_y=0.93,
            arrow_top=0.88,
            arrow_bottom=0.79,
            width=3.0,
            headwidth=11,
            headlength=13,
        )
        add_scale_bar(ax, frame_extent, fontsize=5)
        label = textwrap.fill(f"{panel_label} {factor.label}", width=28)
        ax.text(
            0.03,
            0.96,
            label,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "none", "alpha": 0.88},
            zorder=7,
        )
    else:
        add_north_arrow(ax)
        add_scale_bar(ax, frame_extent)
        add_legend(ax, f"{factor.label} score")


def prepare_factor(factor: Factor) -> tuple[np.ndarray, np.ndarray, dict, tuple[float, float, float, float], tuple[float, float, float, float]]:
    data, profile = read_raster(factor.source_raster)
    classes = classify_equal_interval(data)
    dst, extent = reproject_class(classes, profile)
    frame_extent = frame_extent_for_legend(extent)
    return data, dst, profile, extent, frame_extent


def save_individual_map(factor: Factor, prepared: tuple[np.ndarray, np.ndarray, dict, tuple[float, float, float, float], tuple[float, float, float, float]]) -> list[dict[str, object]]:
    data, dst, _profile, extent, frame_extent = prepared
    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    draw_factor(ax, factor, dst, extent, frame_extent, panel_label=None, compact=False)
    png = INDIVIDUAL_DIR / f"peru_{factor.slug}_5class_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    stats = raster_stats(data)
    return [
        {
            "site": "Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
            "factor": factor.slug,
            "label": factor.label,
            "group": factor.group,
            "figure_format": "png",
            "figure_path": rel(png),
            "source_raster": rel(factor.source_raster),
            "classification": "equal interval 0-1, five classes",
            "claim_level": factor.claim_level,
            "data_basis": factor.data_basis,
            "limitation": factor.limitation,
            **stats,
        },
        {
            "site": "Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
            "factor": factor.slug,
            "label": factor.label,
            "group": factor.group,
            "figure_format": "pdf",
            "figure_path": rel(pdf),
            "source_raster": rel(factor.source_raster),
            "classification": "equal interval 0-1, five classes",
            "claim_level": factor.claim_level,
            "data_basis": factor.data_basis,
            "limitation": factor.limitation,
            **stats,
        },
    ]


def add_common_panel_legend(fig) -> None:
    handles = [
        Patch(facecolor=color, edgecolor="0.4", label=label)
        for label, color in zip(LABELS, SCORE_COLORS, strict=True)
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=5,
        frameon=False,
        title="Standardized conditioning-factor score",
        fontsize=9,
        title_fontsize=10,
        bbox_to_anchor=(0.5, 0.025),
    )


def save_panel(
    slug: str,
    factors: list[Factor],
    prepared_by_slug: dict[str, tuple[np.ndarray, np.ndarray, dict, tuple[float, float, float, float], tuple[float, float, float, float]]],
    columns: int = 3,
) -> list[dict[str, object]]:
    rows = int(math.ceil(len(factors) / columns))
    fig, axes = plt.subplots(rows, columns, figsize=(columns * 4.1, rows * 4.6), constrained_layout=False)
    fig.subplots_adjust(left=0.05, right=0.985, top=0.955, bottom=0.13, wspace=0.09, hspace=0.24)
    axes_flat = np.atleast_1d(axes).ravel()
    labels = [f"({chr(97 + idx)})" for idx in range(len(factors))]
    for ax, factor, panel_label in zip(axes_flat, factors, labels, strict=False):
        _data, dst, _profile, extent, frame_extent = prepared_by_slug[factor.slug]
        compact_extent = frame_extent_for_legend(extent, bottom=0.18)
        draw_factor(ax, factor, dst, extent, compact_extent, panel_label=panel_label, compact=True)
    for ax in axes_flat[len(factors):]:
        ax.axis("off")
    add_common_panel_legend(fig)
    png = OUT_DIR / f"peru_{slug}_conditioning_factors_panel_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return [
        {
            "panel": slug,
            "figure_format": "png",
            "figure_path": rel(png),
            "factors": ", ".join(factor.slug for factor in factors),
            "classification": "equal interval 0-1, five classes",
        },
        {
            "panel": slug,
            "figure_format": "pdf",
            "figure_path": rel(pdf),
            "factors": ", ".join(factor.slug for factor in factors),
            "classification": "equal interval 0-1, five classes",
        },
    ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    prepared_by_slug = {factor.slug: prepare_factor(factor) for factor in FACTORS}

    rows: list[dict[str, object]] = []
    for factor in FACTORS:
        rows.extend(save_individual_map(factor, prepared_by_slug[factor.slug]))
    rows.extend(
        save_panel(
            "physical",
            [factor for factor in FACTORS if factor.group == "physical"],
            prepared_by_slug,
        )
    )
    rows.extend(
        save_panel(
            "human_environment",
            [factor for factor in FACTORS if factor.group == "human_environment"],
            prepared_by_slug,
        )
    )
    write_csv(OUT_DIR / "index.csv", rows)
    print(f"wrote {len(rows)} conditioning-factor map records to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
