#!/usr/bin/env python3
"""Export paper-style maps for the five Peru PIM criterion rasters.

The maps are presentation figures for the current Peru-first prototype. Each
map shows a standardized 0-1 PIM criterion score, not a validated risk layer.
"""

from __future__ import annotations

import csv
import math
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
OUT_DIR = ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps"
DST_CRS = CRS.from_epsg(4326)
CRITERIA_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria"
BOUNDARY_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
BOUNDARY_LAYER = "peru_pilot_boundary"

BOUNDS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.000001]
LABELS = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]


@dataclass(frozen=True)
class Criterion:
    slug: str
    label: str
    source_raster: Path
    colors: list[str]
    claim_level: str
    data_basis: str
    limitation: str


CRITERIA = [
    Criterion(
        slug="flood_hazard",
        label="Flood hazard score",
        source_raster=CRITERIA_DIR / "flood_hazard_0_1.tif",
        colors=["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
        claim_level="sensitivity_scenario",
        data_basis="terrain-derived flood conditioning plus CHIRPS rainy-season rainfall context",
        limitation="not hydraulic inundation depth",
    ),
    Criterion(
        slug="sediment",
        label="Sediment / erosion score",
        source_raster=CRITERIA_DIR / "sediment_0_1.tif",
        colors=["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
        claim_level="diagnostic_only",
        data_basis="SoilGrids K-factor, SRTM LS-factor, and ESA WorldCover C-factor",
        limitation="K x LS x C structure; rainfall erosivity not applied",
    ),
    Criterion(
        slug="landuse_asm",
        label="Land use / ASM score",
        source_raster=CRITERIA_DIR / "landuse_asm_0_1.tif",
        colors=["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
        claim_level="provisional",
        data_basis="WorldCover land-cover pressure plus INGEMMET small-mining point proximity",
        limitation="mining is point proximity, not active footprint",
    ),
    Criterion(
        slug="environmental",
        label="Environmental sensitivity score",
        source_raster=CRITERIA_DIR / "environmental_0_1.tif",
        colors=["#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"],
        claim_level="provisional",
        data_basis="water/wetland context plus protected-area proximity",
        limitation="environmental-sensitivity indicator, not ecological valuation",
    ),
    Criterion(
        slug="socioeconomic",
        label="Socioeconomic exposure score",
        source_raster=CRITERIA_DIR / "socioeconomic_0_1.tif",
        colors=["#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"],
        claim_level="provisional",
        data_basis="OSM road/access proximity",
        limitation="access indicator, not observed vulnerability",
    ),
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


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
    classes[valid] = np.digitize(np.clip(data[valid], BOUNDS[0], BOUNDS[-1]), BOUNDS[1:-1], right=False) + 1
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


def frame_extent_for_legend(extent: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    west, east, south, north = extent
    width = east - west
    height = north - south
    return (
        west - width * 0.02,
        east + width * 0.02,
        south - height * 0.25,
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


def add_scale_bar(ax, extent: tuple[float, float, float, float]) -> None:
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
    ax.text(x0, y0 + bar_h * 1.55, "0", ha="center", va="bottom", fontsize=8)
    ax.text(x0 + length_deg / 2, y0 + bar_h * 1.55, f"{length_km / 2:g}", ha="center", va="bottom", fontsize=8)
    ax.text(x0 + length_deg, y0 + bar_h * 1.55, f"{length_km:g}", ha="center", va="bottom", fontsize=8)
    ax.text(x0 + length_deg / 2, y0 - bar_h * 0.55, "Kilometers", ha="center", va="top", fontsize=8)


def add_north_arrow(ax) -> None:
    ax.text(0.92, 0.96, "N", transform=ax.transAxes, ha="center", va="bottom", fontsize=12, family="serif")
    ax.annotate(
        "",
        xy=(0.92, 0.91),
        xytext=(0.92, 0.80),
        xycoords="axes fraction",
        arrowprops={"facecolor": "black", "edgecolor": "black", "width": 7, "headwidth": 22, "headlength": 26},
    )


def add_boundary_and_frame(ax, extent: tuple[float, float, float, float]) -> None:
    boundary = gpd.read_file(BOUNDARY_GPKG, layer=BOUNDARY_LAYER).to_crs(DST_CRS)
    boundary.boundary.plot(ax=ax, color="#222222", linewidth=0.9, zorder=4)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_locator(MaxNLocator(5))
    ax.xaxis.set_major_formatter(FuncFormatter(degree_formatter("lon")))
    ax.yaxis.set_major_formatter(FuncFormatter(degree_formatter("lat")))
    ax.tick_params(top=True, bottom=True, left=True, right=True, labeltop=True, labelbottom=True, labelleft=True, labelright=True, labelsize=8)
    ax.set_xlabel("")
    ax.set_ylabel("")
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def add_legend(ax, title: str, colors: list[str]) -> None:
    handles = [Patch(facecolor=color, edgecolor="0.4", label=label) for label, color in zip(LABELS, colors, strict=True)]
    legend = ax.legend(
        handles=handles,
        title=title,
        loc="lower left",
        bbox_to_anchor=(0.065, 0.035),
        frameon=True,
        framealpha=0.92,
        facecolor="white",
        edgecolor="white",
        fontsize=8,
        title_fontsize=9,
    )
    legend._legend_box.align = "left"


def raster_stats(data: np.ndarray) -> dict[str, float | int]:
    valid = np.isfinite(data)
    values = data[valid]
    return {
        "valid_cells": int(valid.sum()),
        "valid_fraction": float(valid.mean()),
        "min": float(np.nanmin(values)),
        "mean": float(np.nanmean(values)),
        "max": float(np.nanmax(values)),
    }


def save_criterion_map(criterion: Criterion) -> list[dict[str, object]]:
    data, profile = read_raster(criterion.source_raster)
    stats = raster_stats(data)
    classes = classify_equal_interval(data)
    dst, extent = reproject_class(classes, profile)
    frame_extent = frame_extent_for_legend(extent)
    cmap = ListedColormap(criterion.colors)
    norm = BoundaryNorm(np.arange(0.5, len(criterion.colors) + 1.5), len(criterion.colors))
    masked = np.ma.masked_where(dst == 0, dst)

    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    ax.imshow(masked, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    add_boundary_and_frame(ax, frame_extent)
    add_north_arrow(ax)
    add_scale_bar(ax, frame_extent)
    add_legend(ax, criterion.label, criterion.colors)
    png = OUT_DIR / f"peru_{criterion.slug}_5class_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

    rows: list[dict[str, object]] = []
    for fmt, path in [("png", png), ("pdf", pdf)]:
        rows.append(
            {
                "site": "Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
                "criterion": criterion.slug,
                "figure_format": fmt,
                "figure_path": rel(path),
                "source_raster": rel(criterion.source_raster),
                "classification": "equal interval 0-1, five classes",
                "claim_level": criterion.claim_level,
                "data_basis": criterion.data_basis,
                "limitation": criterion.limitation,
                **stats,
            }
        )
    return rows


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for criterion in CRITERIA:
        rows.extend(save_criterion_map(criterion))
    write_csv(OUT_DIR / "index.csv", rows)
    print(f"wrote {len(rows)} Peru criterion map outputs to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
