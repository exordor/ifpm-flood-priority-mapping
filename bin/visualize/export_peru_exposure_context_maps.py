#!/usr/bin/env python3
"""Export slide-ready Peru exposure and response-capacity context maps.

Each map is a standalone GIS figure without a global title or caption. Legends,
coordinate ticks, scale bars, north arrows, source lineage, and claim levels are
retained so the figures can be placed directly in a presentation layout.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_peru_pim_criteria_maps as map_helpers


SOURCE_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators"
OUT_DIR = ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps"

INPUTS = [
    ROOT / "bin/visualize/export_peru_pim_criteria_maps.py",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/population_exposure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/built_infrastructure_exposure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/poverty_context_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/health_service_remoteness_0_1.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_population_exposure_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_population_exposure_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_built_infrastructure_exposure_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_built_infrastructure_exposure_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_exposure_indicators_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_exposure_indicators_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_poverty_context_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_poverty_context_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_health_service_remoteness_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/peru_health_service_remoteness_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_exposure_context_maps/index.csv",
]


@dataclass(frozen=True)
class MapSpec:
    slug: str
    legend_title: str
    source_raster: Path
    bounds: tuple[float, ...]
    labels: tuple[str, ...]
    colors: tuple[str, ...]
    data_basis: str
    limitation: str
    claim_level: str
    transform: Callable[[np.ndarray], np.ndarray] | None = None


SCORE_BOUNDS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.000001)
SCORE_LABELS = ("0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0")

MAP_SPECS = [
    MapSpec(
        slug="population_exposure",
        legend_title="Population exposure score",
        source_raster=SOURCE_DIR / "population_exposure_0_1.tif",
        bounds=SCORE_BOUNDS,
        labels=SCORE_LABELS,
        colors=("#f7fbff", "#deebf7", "#9ecae1", "#4292c6", "#08519c"),
        data_basis="WorldPop 2020 population count (native ~3 arc-second / ~100 m), sum-resampled to the 30 m alignment grid then log1p/p99 standardized; effective detail remains source-limited",
        limitation="relative exposure score, not observed affected population",
        claim_level="provisional",
    ),
    MapSpec(
        slug="built_infrastructure_exposure",
        legend_title="Mapped-building exposure score",
        source_raster=SOURCE_DIR / "built_infrastructure_exposure_0_1.tif",
        bounds=SCORE_BOUNDS,
        labels=SCORE_LABELS,
        colors=("#f2f0f7", "#dadaeb", "#bcbddc", "#807dba", "#54278f"),
        data_basis="1 km-radius focal density of OSM mapped-building presence",
        limitation="OSM mapping completeness varies; not a building census",
        claim_level="provisional",
    ),
    MapSpec(
        slug="exposure_indicators",
        legend_title="Socioeconomic exposure score",
        source_raster=SOURCE_DIR / "exposure_indicators_0_1.tif",
        bounds=SCORE_BOUNDS,
        labels=SCORE_LABELS,
        colors=("#ffffcc", "#fed976", "#feb24c", "#fd8d3c", "#bd0026"),
        data_basis="0.45 road/access proximity + 0.55 population/building exposure indicator",
        limitation="provisional exposure indicator, not observed vulnerability",
        claim_level="provisional",
    ),
    MapSpec(
        slug="poverty_context",
        legend_title="INEI poverty midpoint (%)",
        source_raster=SOURCE_DIR / "poverty_context_0_1.tif",
        bounds=(0.0, 10.0, 15.0, 20.0, 30.0, 50.0001),
        labels=("0-10%", "10-15%", "15-20%", "20-30%", "30-50%"),
        colors=("#fff5f0", "#fee0d2", "#fcae91", "#fb6a4a", "#a50f15"),
        data_basis="midpoint of INEI 2018 district poverty 95% interval",
        limitation="district-level response-capacity context; excluded from current AHP overlay",
        claim_level="diagnostic_only",
        transform=lambda values: values * 100.0,
    ),
    MapSpec(
        slug="health_service_remoteness",
        legend_title="Distance to mapped health service",
        source_raster=SOURCE_DIR / "health_service_remoteness_0_1.tif",
        bounds=(0.0, 2.0, 5.0, 10.0, 15.0, 20.0001),
        labels=("0-2 km", "2-5 km", "5-10 km", "10-15 km", "15-20+ km"),
        colors=("#edf8b1", "#c7e9b4", "#7fcdbb", "#fdae61", "#d73027"),
        data_basis="Euclidean distance to OSM clinic, doctor, or hospital points",
        limitation="distance clipped at 20 km; OSM completeness varies; excluded from AHP overlay",
        claim_level="diagnostic_only",
        transform=lambda values: values * 20.0,
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


def classify(data: np.ndarray, bounds: tuple[float, ...]) -> np.ndarray:
    classes = np.zeros(data.shape, dtype="uint8")
    valid = np.isfinite(data)
    classes[valid] = (
        np.digitize(np.clip(data[valid], bounds[0], bounds[-1]), bounds[1:-1], right=False) + 1
    )
    return classes


def add_legend(ax, spec: MapSpec) -> None:
    handles = [
        Patch(facecolor=color, edgecolor="0.4", label=label)
        for label, color in zip(spec.labels, spec.colors, strict=True)
    ]
    handles.append(Patch(facecolor="#d9d9d9", edgecolor="0.4", label="No data / not scored"))
    legend = ax.legend(
        handles=handles,
        title=spec.legend_title,
        loc="lower left",
        bbox_to_anchor=(0.065, 0.035),
        frameon=True,
        framealpha=0.94,
        facecolor="white",
        edgecolor="white",
        fontsize=8,
        title_fontsize=9,
    )
    legend._legend_box.align = "left"


def export_map(spec: MapSpec) -> list[dict[str, object]]:
    data, profile = map_helpers.read_raster(spec.source_raster)
    display = spec.transform(data.copy()) if spec.transform else data
    classes = classify(display, spec.bounds)
    projected, extent = map_helpers.reproject_class(classes, profile)
    frame_extent = map_helpers.frame_extent_for_legend(extent)

    cmap = ListedColormap(spec.colors)
    norm = BoundaryNorm(np.arange(0.5, len(spec.colors) + 1.5), len(spec.colors))
    masked = np.ma.masked_where(projected == 0, projected)
    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    ax.imshow(
        masked,
        extent=extent,
        origin="upper",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        zorder=1,
    )
    map_helpers.add_boundary_and_frame(ax, frame_extent)
    map_helpers.add_north_arrow(ax)
    map_helpers.add_scale_bar(ax, frame_extent)
    add_legend(ax, spec)

    png = OUT_DIR / f"peru_{spec.slug}_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

    values = display[np.isfinite(display)]
    base = {
        "site": "Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
        "map": spec.slug,
        "source_raster": rel(spec.source_raster),
        "source_sha256": sha256(spec.source_raster),
        "classification": "fixed five-class bounds: " + "; ".join(spec.labels),
        "data_basis": spec.data_basis,
        "limitation": spec.limitation,
        "claim_level": spec.claim_level,
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "max": round(float(values.max()), 6),
    }
    return [
        {**base, "figure_format": "png", "figure_path": rel(png)},
        {**base, "figure_format": "pdf", "figure_path": rel(pdf)},
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
    missing = [spec.source_raster for spec in MAP_SPECS if not spec.source_raster.exists()]
    if missing:
        raise FileNotFoundError("missing exposure-map inputs: " + ", ".join(map(str, missing)))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for spec in MAP_SPECS:
        rows.extend(export_map(spec))
    write_csv(OUT_DIR / "index.csv", rows)
    print(f"wrote {len(rows)} exposure/context map outputs to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
