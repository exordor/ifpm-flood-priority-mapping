#!/usr/bin/env python3
"""Export paper-style single maps with graticule, north arrow, and scale bar.

These are presentation figures only. They use current project rasters but avoid
large in-image titles/captions so slide text can provide the interpretation.
"""

from __future__ import annotations

import csv
import hashlib
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
OUT_DIR = ROOT / "outputs/sensitivity_figures/paper_style_single_maps"
DST_CRS = CRS.from_epsg(4326)

INPUTS = [
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/priority_mean.tif",
    ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/flood_conditioning_factors_0_1.tif",
    ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_conditioning_factors_0_1.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/zimbabwe_mean_priority_5class_paper_style_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/zimbabwe_mean_priority_5class_paper_style_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/zimbabwe_top20_priority_areas_paper_style_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/zimbabwe_top20_priority_areas_paper_style_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/zimbabwe_flood_conditioning_5class_paper_style_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/zimbabwe_flood_conditioning_5class_paper_style_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/peru_mean_priority_5class_paper_style_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/peru_mean_priority_5class_paper_style_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/peru_top20_priority_areas_paper_style_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/peru_top20_priority_areas_paper_style_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/peru_flood_conditioning_5class_paper_style_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/peru_flood_conditioning_5class_paper_style_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/paper_style_single_maps/index.csv",
]

PRIORITY_BOUNDS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.000001]
PRIORITY_LABELS = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
PRIORITY_COLORS = ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"]

FLOOD_BOUNDS = PRIORITY_BOUNDS
FLOOD_LABELS = PRIORITY_LABELS
FLOOD_COLORS = ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"]

TOP20_COLORS = ["#eeeeee", "#d73027"]


@dataclass(frozen=True)
class Site:
    slug: str
    label: str
    claim_level: str
    priority_mean: Path
    flood_conditioning: Path
    boundary_gpkg: Path
    boundary_layer: str


SITES = [
    Site(
        slug="zimbabwe",
        label="Zimbabwe Upper Mzingwane",
        claim_level="sensitivity_scenario",
        priority_mean=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/priority_mean.tif",
        flood_conditioning=ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria/flood_conditioning_factors_0_1.tif",
        boundary_gpkg=ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
        boundary_layer="v1_working_boundary",
    ),
    Site(
        slug="peru",
        label="Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
        claim_level="provisional / sensitivity_scenario",
        priority_mean=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif",
        flood_conditioning=ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_conditioning_factors_0_1.tif",
        boundary_gpkg=ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
        boundary_layer="peru_pilot_boundary",
    ),
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def classify_equal_interval(data: np.ndarray, bounds: list[float]) -> np.ndarray:
    classes = np.zeros(data.shape, dtype="uint8")
    valid = np.isfinite(data)
    classes[valid] = np.digitize(np.clip(data[valid], bounds[0], bounds[-1]), bounds[1:-1], right=False) + 1
    return classes


def classify_top20(data: np.ndarray) -> tuple[np.ndarray, float]:
    classes = np.zeros(data.shape, dtype="uint8")
    valid = np.isfinite(data)
    threshold = float(np.nanpercentile(data[valid], 80))
    classes[valid] = 1
    classes[valid & (data >= threshold)] = 2
    return classes, threshold


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
    """Add map-frame whitespace so legends and scale bars do not cover data."""
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


def add_boundary_and_frame(ax, site: Site, extent: tuple[float, float, float, float]) -> None:
    boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(DST_CRS)
    boundary.plot(ax=ax, facecolor="#d9d9d9", edgecolor="#222222", linewidth=0.9, zorder=0)
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


def add_legend(ax, title: str, labels: list[str], colors: list[str]) -> None:
    handles = [Patch(facecolor=color, edgecolor="0.4", label=label) for label, color in zip(labels, colors, strict=True)]
    handles.append(Patch(facecolor="#d9d9d9", edgecolor="0.4", label="Unscored (missing criterion evidence)"))
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


def save_class_map(
    site: Site,
    source: Path,
    classes: np.ndarray,
    profile: dict,
    stem: str,
    legend_title: str,
    labels: list[str],
    colors: list[str],
    class_note: str,
) -> list[dict[str, object]]:
    dst, extent = reproject_class(classes, profile)
    frame_extent = frame_extent_for_legend(extent)
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.arange(0.5, len(colors) + 1.5), len(colors))
    masked = np.ma.masked_where(dst == 0, dst)

    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    ax.imshow(masked, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    add_boundary_and_frame(ax, site, frame_extent)
    add_north_arrow(ax)
    add_scale_bar(ax, frame_extent)
    add_legend(ax, legend_title, labels, colors)
    png = OUT_DIR / f"{site.slug}_{stem}_paper_style_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return [
        {"site": site.label, "map_type": stem, "format": "png", "path": rel(png), "source": rel(source), "source_sha256": sha256(source), "class_note": class_note, "claim_level": site.claim_level},
        {"site": site.label, "map_type": stem, "format": "pdf", "path": rel(pdf), "source": rel(source), "source_sha256": sha256(source), "class_note": class_note, "claim_level": site.claim_level},
    ]


def make_site_maps(site: Site) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    priority, priority_profile = read_raster(site.priority_mean)
    priority_classes = classify_equal_interval(priority, PRIORITY_BOUNDS)
    rows.extend(
        save_class_map(
            site,
            site.priority_mean,
            priority_classes,
            priority_profile,
            "mean_priority_5class",
            "Priority score",
            PRIORITY_LABELS,
            PRIORITY_COLORS,
            "equal interval classes on 0-1 priority_mean",
        )
    )
    top20_classes, threshold = classify_top20(priority)
    rows.extend(
        save_class_map(
            site,
            site.priority_mean,
            top20_classes,
            priority_profile,
            "top20_priority_areas",
            "Priority areas",
            ["Other valid cells", "Top 20% priority areas"],
            TOP20_COLORS,
            f"binary top quintile from priority_mean; threshold={threshold:.6f}",
        )
    )
    flood, flood_profile = read_raster(site.flood_conditioning)
    flood_classes = classify_equal_interval(flood, FLOOD_BOUNDS)
    rows.extend(
        save_class_map(
            site,
            site.flood_conditioning,
            flood_classes,
            flood_profile,
            "flood_conditioning_5class",
            "Flood conditioning score",
            FLOOD_LABELS,
            FLOOD_COLORS,
            "equal interval classes on 0-1 terrain-based flood_conditioning_factors",
        )
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
    for site in SITES:
        rows.extend(make_site_maps(site))
    write_csv(OUT_DIR / "index.csv", rows)
    print(f"wrote {len(rows)} paper-style map outputs to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
