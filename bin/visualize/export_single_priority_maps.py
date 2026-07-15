#!/usr/bin/env python3
"""Export sensitivity-appendix single-map figures from current priority outputs.

The figures deliberately have no title and no caption. They keep only the map,
boundary, axes, and the minimum legend/colorbar needed to read a single image.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/sensitivity_figures/single_priority_maps"

INPUTS = [
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/priority_mean.tif",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/top20_frequency.tif",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenario_weights.csv",
    ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/flood_hazard_0_1.tif",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/sediment_0_1.tif",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/landuse_asm_0_1.tif",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/environmental_0_1.tif",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/socioeconomic_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/flood_hazard_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/sediment_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/landuse_asm_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/environmental_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/socioeconomic_0_1.tif",
]
OUTPUTS = [
    ROOT / "outputs/sensitivity_figures/single_priority_maps/zimbabwe_mean_priority_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/zimbabwe_mean_priority_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/zimbabwe_top20_priority_selection_frequency_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/zimbabwe_top20_priority_selection_frequency_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/zimbabwe_dominant_priority_driver_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/zimbabwe_dominant_priority_driver_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/peru_mean_priority_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/peru_mean_priority_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/peru_top20_priority_selection_frequency_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/peru_top20_priority_selection_frequency_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/peru_dominant_priority_driver_no_title_caption.png",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/peru_dominant_priority_driver_no_title_caption.pdf",
    ROOT / "outputs/sensitivity_figures/single_priority_maps/index.csv",
]

COLORS = {
    "flood": "#0072B2",
    "sediment": "#D55E00",
    "landuse_asm": "#009E73",
    "environmental": "#CC79A7",
    "socioeconomic": "#E69F00",
}


@dataclass(frozen=True)
class Criterion:
    key: str
    family: str
    label: str
    path: Path


@dataclass(frozen=True)
class Site:
    slug: str
    label: str
    boundary_id: str
    experiment_id: str
    claim_level: str
    priority_mean: Path
    top20_frequency: Path
    weights_csv: Path
    boundary_gpkg: Path
    boundary_layer: str
    crs_label: str
    criteria: tuple[Criterion, ...]


SITES = [
    Site(
        slug="zimbabwe",
        label="Zimbabwe Upper Mzingwane",
        boundary_id="boundary_v1",
        experiment_id="rainfall_exposure_v0_4",
        claim_level="sensitivity_scenario",
        priority_mean=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/priority_mean.tif",
        top20_frequency=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/top20_frequency.tif",
        weights_csv=ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/scenario_weights.csv",
        boundary_gpkg=ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
        boundary_layer="v1_working_boundary",
        crs_label="EPSG:32735",
        criteria=(
            Criterion("flood_hazard", "flood", "Flood hazard", ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/flood_hazard_0_1.tif"),
            Criterion("sediment", "sediment", "Sediment", ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/sediment_0_1.tif"),
            Criterion("landuse_asm", "landuse_asm", "Land Use / ASM", ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/landuse_asm_0_1.tif"),
            Criterion("environmental", "environmental", "Environmental sensitivity", ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/environmental_0_1.tif"),
            Criterion("socioeconomic", "socioeconomic", "Socioeconomic exposure", ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/pim_criteria/socioeconomic_0_1.tif"),
        ),
    ),
    Site(
        slug="peru",
        label="Southern Peru comparison catchment",
        boundary_id="Arequipa Region",
        experiment_id="priority_scenarios",
        claim_level="provisional / sensitivity_scenario",
        priority_mean=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif",
        top20_frequency=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif",
        weights_csv=ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_weights.csv",
        boundary_gpkg=ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
        boundary_layer="peru_pilot_boundary",
        crs_label="EPSG:32718",
        criteria=(
            Criterion("flood_hazard", "flood", "Flood hazard", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/flood_hazard_0_1.tif"),
            Criterion("sediment", "sediment", "Sediment", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/sediment_0_1.tif"),
            Criterion("landuse_asm", "landuse_asm", "Land Use / ASM", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/landuse_asm_0_1.tif"),
            Criterion("environmental", "environmental", "Environmental sensitivity", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/environmental_0_1.tif"),
            Criterion("socioeconomic", "socioeconomic", "Socioeconomic exposure", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/socioeconomic_0_1.tif"),
        ),
    ),
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_raster(path: Path, profile: dict | None = None) -> tuple[np.ndarray, dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        if profile is not None:
            if src.crs != profile["crs"] or src.transform != profile["transform"]:
                raise ValueError(f"grid mismatch: {path}")
            if src.width != profile["width"] or src.height != profile["height"]:
                raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        data[~np.isfinite(data)] = np.nan
        out_profile = {
            "crs": src.crs,
            "transform": src.transform,
            "width": src.width,
            "height": src.height,
        }
    return data, out_profile


def map_extent(profile: dict) -> tuple[float, float, float, float]:
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    return (bounds[0], bounds[2], bounds[1], bounds[3])


def read_mean_weights(site: Site) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    with site.weights_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["experiment_id"] != site.experiment_id:
                continue
            grouped.setdefault(row["criterion"], []).append(float(row["weight"]))
    if not grouped:
        raise ValueError(f"No weights for {site.experiment_id}: {site.weights_csv}")
    return {criterion: float(np.mean(values)) for criterion, values in grouped.items()}


def normalize_if_needed(data: np.ndarray) -> np.ndarray:
    values = data[np.isfinite(data)]
    if values.size == 0:
        raise ValueError("empty raster")
    if float(values.min()) >= -1e-6 and float(values.max()) <= 1.000001:
        return np.clip(data, 0.0, 1.0).astype("float32")
    return np.clip(data / float(values.max()), 0.0, 1.0).astype("float32")


def dominant_driver(site: Site) -> tuple[np.ndarray, dict]:
    weights = read_mean_weights(site)
    arrays: list[np.ndarray] = []
    profile = None
    for criterion in site.criteria:
        raw, profile = read_raster(criterion.path, profile)
        arrays.append(normalize_if_needed(raw))
    assert profile is not None
    stack = np.stack(arrays)
    valid = np.all(np.isfinite(stack), axis=0)
    mean_weights = np.array([weights[c.key] for c in site.criteria], dtype="float32")
    contributions = stack * mean_weights[:, None, None]
    winner = np.nanargmax(np.where(valid[None, :, :], contributions, -np.inf), axis=0)
    dominant = np.full(valid.shape, np.nan, dtype="float32")
    dominant[valid] = winner[valid].astype("float32") + 1.0
    return dominant, profile


def format_axes(ax, site: Site, profile: dict) -> None:
    boundary = gpd.read_file(site.boundary_gpkg, layer=site.boundary_layer).to_crs(profile["crs"])
    boundary.boundary.plot(ax=ax, color="black", linewidth=1.0)
    formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)
    ax.set_xlabel(f"Easting (km, {site.crs_label})", fontsize=10)
    ax.set_ylabel("Northing (km)", fontsize=10)
    ax.grid(color="0.88", linewidth=0.45)
    ax.tick_params(labelsize=9)


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.08)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=9)
    cb.set_label(label, fontsize=10)


def save_continuous_map(site: Site, raster: Path, stem: str, cmap: str, label: str) -> list[dict[str, object]]:
    data, profile = read_raster(raster)
    fig, ax = plt.subplots(figsize=(6.4, 7.0), constrained_layout=True)
    image = ax.imshow(np.ma.masked_invalid(data), extent=map_extent(profile), origin="upper", cmap=cmap, vmin=0, vmax=1)
    format_axes(ax, site, profile)
    add_colorbar(fig, ax, image, label)
    png = OUT_DIR / f"{site.slug}_{stem}_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return [
        {"site": site.label, "map_type": stem, "format": "png", "path": rel(png), "source": rel(raster), "claim_level": site.claim_level},
        {"site": site.label, "map_type": stem, "format": "pdf", "path": rel(pdf), "source": rel(raster), "claim_level": site.claim_level},
    ]


def save_dominant_map(site: Site) -> list[dict[str, object]]:
    data, profile = dominant_driver(site)
    families = [criterion.family for criterion in site.criteria]
    labels = [criterion.label for criterion in site.criteria]
    cmap = ListedColormap([COLORS[family] for family in families])
    norm = BoundaryNorm(np.arange(0.5, len(families) + 1.5), cmap.N)

    fig, ax = plt.subplots(figsize=(7.4, 7.0), constrained_layout=True)
    ax.imshow(np.ma.masked_invalid(data), extent=map_extent(profile), origin="upper", cmap=cmap, norm=norm)
    format_axes(ax, site, profile)
    handles = [Patch(facecolor=COLORS[family], edgecolor="0.25", label=label) for family, label in zip(families, labels, strict=True)]
    ax.legend(handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True, fontsize=8.5)
    png = OUT_DIR / f"{site.slug}_dominant_priority_driver_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    sources = "; ".join(rel(criterion.path) for criterion in site.criteria)
    return [
        {"site": site.label, "map_type": "dominant_priority_driver", "format": "png", "path": rel(png), "source": sources, "claim_level": site.claim_level},
        {"site": site.label, "map_type": "dominant_priority_driver", "format": "pdf", "path": rel(pdf), "source": sources, "claim_level": site.claim_level},
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for site in SITES:
        rows.extend(save_continuous_map(site, site.priority_mean, "mean_priority", "YlOrRd", "0-1 priority score"))
        rows.extend(save_continuous_map(site, site.top20_frequency, "top20_priority_selection_frequency", "Blues", "selection frequency"))
        rows.extend(save_dominant_map(site))
    write_csv(OUT_DIR / "index.csv", rows)
    print(f"wrote {len(rows)} single-map outputs to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
