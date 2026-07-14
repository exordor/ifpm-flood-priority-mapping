#!/usr/bin/env python3
"""Export the current Zimbabwe five-criterion reporting map chain.

The figures use the direct Zimbabwe weights supplied in July 2026. They show
relative scores from the controlled Upper Mzingwane prototype, not validated
flood risk, flood depth, damage, or emergency need.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_paper_style_single_maps as maps


BASE = ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4"
CRITERIA_DIR = BASE / "pim_criteria"
PIM = BASE / "scenarios/priority_mentor_zimbabwe_direct_pim.tif"
BOUNDARY = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
RIVERS = ROOT / "data/raw/zimbabwe_geoportal_candidate_outlet_layers/extracted/rivers/ZWE_water_lines_dcw.shp"
OUT_DIR = ROOT / "outputs/slide_ready_figures/zimbabwe_reporting_maps"
INDEX = OUT_DIR / "index.csv"
DATA_STRENGTH = OUT_DIR / "criterion_data_strength.csv"
RESULT_SUMMARY = OUT_DIR / "result_summary.csv"
CONTRIBUTION_SUMMARY = OUT_DIR / "contribution_summary.csv"

SITE = maps.Site(
    slug="zimbabwe",
    label="Zimbabwe Upper Mzingwane controlled prototype catchment",
    claim_level="sensitivity_scenario",
    priority_mean=PIM,
    flood_conditioning=CRITERIA_DIR / "flood_hazard_0_1.tif",
    boundary_gpkg=BOUNDARY,
    boundary_layer="v1_working_boundary",
)

WEIGHTS = OrderedDict(
    [
        ("flood_hazard", 0.32),
        ("sediment", 0.23),
        ("landuse_asm", 0.18),
        ("environmental", 0.12),
        ("socioeconomic", 0.15),
    ]
)


@dataclass(frozen=True)
class Criterion:
    label: str
    source: Path
    colors: tuple[str, ...]


CRITERIA = OrderedDict(
    [
        (
            "flood_hazard",
            Criterion(
                "Flood-conditioning indicator (FH)",
                CRITERIA_DIR / "flood_hazard_0_1.tif",
                ("#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"),
            ),
        ),
        (
            "sediment",
            Criterion(
                "Erosion-source indicator (SE)",
                CRITERIA_DIR / "sediment_0_1.tif",
                ("#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"),
            ),
        ),
        (
            "landuse_asm",
            Criterion(
                "Land use / mining-reference indicator (LM)",
                CRITERIA_DIR / "landuse_asm_0_1.tif",
                ("#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"),
            ),
        ),
        (
            "environmental",
            Criterion(
                "Environmental context indicator (ES)",
                CRITERIA_DIR / "environmental_0_1.tif",
                ("#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"),
            ),
        ),
        (
            "socioeconomic",
            Criterion(
                "Road-access exposure indicator (SV)",
                CRITERIA_DIR / "socioeconomic_0_1.tif",
                ("#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"),
            ),
        ),
    ]
)

INPUTS = [criterion.source for criterion in CRITERIA.values()] + [PIM, BOUNDARY, RIVERS]
FIGURE_STEMS = ["zimbabwe_study_area_no_title_caption"]
FIGURE_STEMS += [f"zimbabwe_{name}_5class_paper_style_no_title_caption" for name in CRITERIA]
FIGURE_STEMS += [
    "zimbabwe_direct_weight_priority_5class_paper_style_no_title_caption",
    "zimbabwe_largest_weighted_contribution_no_title_caption",
]
OUTPUTS = [OUT_DIR / f"{stem}.{suffix}" for stem in FIGURE_STEMS for suffix in ("png", "pdf")]
OUTPUTS += [INDEX, DATA_STRENGTH, RESULT_SUMMARY, CONTRIBUTION_SUMMARY]

CONTRIBUTION_COLORS = ["#2b83ba", "#d95f0e", "#31a354", "#9e9ac8", "#636363"]
CELL_AREA_KM2 = 0.0009
PALETTE_ID = "ifpm_cross_site_v1"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def assert_same_grid(reference: dict, current: dict, label: str) -> None:
    keys = ("crs", "transform", "width", "height")
    if any(reference[key] != current[key] for key in keys):
        raise ValueError(f"{label} grid does not match the Zimbabwe reference grid")


def read_criteria() -> tuple[OrderedDict[str, np.ndarray], dict]:
    layers: OrderedDict[str, np.ndarray] = OrderedDict()
    profile = None
    for name, criterion in CRITERIA.items():
        data, current = maps.read_raster(criterion.source)
        if profile is None:
            profile = current
        else:
            assert_same_grid(profile, current, name)
        layers[name] = data
    assert profile is not None
    return layers, profile


def study_area_mask(profile: dict) -> np.ndarray:
    boundary = gpd.read_file(BOUNDARY, layer="v1_working_boundary").to_crs(profile["crs"])
    return geometry_mask(
        boundary.geometry,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        invert=True,
    )


def data_strength_rows() -> list[dict[str, object]]:
    rows = {
        "flood_hazard": {
            "evidence_strength": "medium",
            "data_sources": "CHIRPS rainy-season climatology; SRTM TWI; drainage proximity",
            "main_limitation": "CHIRPS is coarse climatology, not event rainfall; no observed inundation depth",
            "claim_level": "sensitivity_scenario",
        },
        "sediment": {
            "evidence_strength": "medium-low",
            "data_sources": "SoilGrids spatial K (effective 250 m); SRTM LS; ESA WorldCover C",
            "main_limitation": "Relative erosion-source susceptibility only; LS channel masking and missing K/LS/C remain unscored; no measured sediment transport",
            "claim_level": "provisional",
        },
        "landuse_asm": {
            "evidence_strength": "low",
            "data_sources": "ESA WorldCover; USGS Africa GIS mineral facilities and deposits",
            "main_limitation": "Proximity-based mineral reference indicator; not a verified active ASM footprint",
            "claim_level": "provisional",
        },
        "environmental": {
            "evidence_strength": "medium-low",
            "data_sources": "WorldCover water/wetland; JRC surface water; mapped water areas; WDPA context",
            "main_limitation": "Proximity-based environmental context, not ecological valuation",
            "claim_level": "provisional",
        },
        "socioeconomic": {
            "evidence_strength": "low",
            "data_sources": "Road/access proximity",
            "main_limitation": "Population, buildings and infrastructure are not included in the scored criterion",
            "claim_level": "diagnostic_only",
        },
    }
    return [
        {
            "criterion": name,
            "weight": WEIGHTS[name],
            "source_raster": rel(CRITERIA[name].source),
            "assessment_basis": "qualitative source authority, spatial coverage, directness and validation status",
            **rows[name],
        }
        for name in CRITERIA
    ]


def save_study_area_map() -> list[dict[str, object]]:
    boundary = gpd.read_file(BOUNDARY, layer="v1_working_boundary").to_crs("EPSG:4326")
    anchors = gpd.read_file(BOUNDARY, layer="v1_anchor_check").to_crs("EPSG:4326")
    anchors = anchors[anchors["anchor"].isin(["Esigodini", "Mzingwane Dam", "Gwanda"])].copy()
    rivers = gpd.read_file(RIVERS).to_crs("EPSG:4326")
    west, south, east, north = boundary.total_bounds
    width, height = east - west, north - south
    frame = (west - width * 0.08, east + width * 0.08, south - height * 0.12, north + height * 0.08)
    rivers = rivers.cx[frame[0] : frame[1], frame[2] : frame[3]]

    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    if not rivers.empty:
        rivers.plot(ax=ax, color="#4EA3D8", linewidth=0.45, alpha=0.75, zorder=1)
    boundary.plot(ax=ax, facecolor="#FFF1CC", edgecolor="#D9823B", linewidth=1.5, alpha=0.72, zorder=2)
    boundary.boundary.plot(ax=ax, color="#D9823B", linewidth=1.5, zorder=3)
    anchors.plot(ax=ax, color="#087F5B", edgecolor="white", linewidth=0.7, markersize=34, zorder=4)
    offsets = {
        "Esigodini": (0.012, 0.008),
        "Mzingwane Dam": (0.012, -0.012),
        "Gwanda": (0.012, -0.008),
    }
    for row in anchors.itertuples():
        dx, dy = offsets[row.anchor]
        ax.text(row.geometry.x + dx, row.geometry.y + dy, row.anchor, fontsize=9, color="#172230", zorder=5)
    ax.set_xlim(frame[0], frame[1])
    ax.set_ylim(frame[2], frame[3])
    ax.xaxis.set_major_locator(maps.MaxNLocator(4))
    ax.yaxis.set_major_locator(maps.MaxNLocator(5))
    ax.xaxis.set_major_formatter(maps.FuncFormatter(maps.degree_formatter("lon")))
    ax.yaxis.set_major_formatter(maps.FuncFormatter(maps.degree_formatter("lat")))
    ax.tick_params(top=True, bottom=True, left=True, right=True, labeltop=True, labelbottom=True, labelleft=True, labelright=True, labelsize=8)
    maps.add_north_arrow(ax)
    maps.add_scale_bar(ax, frame)
    handles = [
        Patch(facecolor="#FFF1CC", edgecolor="#D9823B", label="Study area"),
        Patch(facecolor="#4EA3D8", edgecolor="#4EA3D8", label="River / stream"),
        Patch(facecolor="#087F5B", edgecolor="white", label="Place / reservoir"),
    ]
    legend = ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.065, 0.035), frameon=True, framealpha=0.94, fontsize=8)
    legend._legend_box.align = "left"
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    png = OUT_DIR / "zimbabwe_study_area_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    source_hash = f"boundary:{sha256(BOUNDARY)};rivers:{sha256(RIVERS)}"
    return [
        {
            "site": SITE.label,
            "map_type": "study_area",
            "format": path.suffix.lstrip("."),
            "path": rel(path),
            "source": f"{rel(BOUNDARY)};{rel(RIVERS)}",
            "source_sha256": source_hash,
            "class_note": "study-area boundary with river and place context",
            "classification": "study area context",
            "claim_level": "sensitivity_scenario",
        }
        for path in (png, pdf)
    ]


def save_criterion_maps(layers: OrderedDict[str, np.ndarray], profile: dict) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name, layer in layers.items():
        criterion = CRITERIA[name]
        classes = maps.classify_equal_interval(layer, maps.PRIORITY_BOUNDS)
        rows.extend(
            maps.save_class_map(
                SITE,
                criterion.source,
                classes,
                profile,
                f"{name}_5class",
                criterion.label,
                maps.PRIORITY_LABELS,
                list(criterion.colors),
                "equal interval 0-1, five classes",
            )
        )
    return rows


def save_priority_map(priority: np.ndarray, profile: dict) -> list[dict[str, object]]:
    classes = maps.classify_equal_interval(priority, maps.PRIORITY_BOUNDS)
    gaps = np.zeros(priority.shape, dtype="uint8")
    gaps[study_area_mask(profile) & ~np.isfinite(priority)] = 1
    return maps.save_class_map(
        SITE,
        PIM,
        classes,
        profile,
        "direct_weight_priority_5class",
        "Relative priority index",
        maps.PRIORITY_LABELS,
        maps.PRIORITY_COLORS,
        "equal interval 0-1, five classes",
        overlay_specs=[(gaps, 1, "Unscored data gap", "////")],
    )


def save_contribution_map(
    layers: OrderedDict[str, np.ndarray],
    priority: np.ndarray,
    profile: dict,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scoreable = np.isfinite(priority)
    contributions = np.stack(
        [np.where(scoreable, layer * WEIGHTS[name], np.nan) for name, layer in layers.items()]
    )
    dominant = np.zeros(scoreable.shape, dtype="uint8")
    dominant[scoreable] = np.argmax(contributions[:, scoreable], axis=0).astype("uint8") + 1
    projected, extent = maps.reproject_class(dominant, profile)
    gaps = np.zeros(priority.shape, dtype="uint8")
    gaps[study_area_mask(profile) & ~scoreable] = 1
    projected_gaps, _ = maps.reproject_class(gaps, profile)
    frame_extent = maps.frame_extent_for_legend(extent)
    cmap = ListedColormap(CONTRIBUTION_COLORS)
    norm = BoundaryNorm(np.arange(0.5, len(CONTRIBUTION_COLORS) + 1.5), len(CONTRIBUTION_COLORS))

    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    ax.imshow(
        np.ma.masked_where(projected == 0, projected),
        extent=extent,
        origin="upper",
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        zorder=1,
    )
    if np.any(projected_gaps == 1):
        ax.contourf(
            projected_gaps,
            levels=[0.5, 1.5],
            colors="none",
            hatches=["////"],
            extent=extent,
            origin="upper",
            zorder=2,
        )
    maps.add_boundary_and_frame(ax, SITE, frame_extent)
    maps.add_north_arrow(ax)
    maps.add_scale_bar(ax, frame_extent)
    handles = [
        Patch(facecolor=color, edgecolor="0.4", label=CRITERIA[name].label)
        for name, color in zip(CRITERIA, CONTRIBUTION_COLORS, strict=True)
    ]
    handles.append(Patch(facecolor="none", edgecolor="#555555", hatch="////", label="Unscored data gap"))
    legend = ax.legend(
        handles=handles,
        title="Largest weighted contribution",
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
    png = OUT_DIR / "zimbabwe_largest_weighted_contribution_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

    summary_rows: list[dict[str, object]] = []
    for index, name in enumerate(CRITERIA, start=1):
        summary_rows.append(
            {
                "criterion": name,
                "direct_weight": WEIGHTS[name],
                "dominant_cells": int(np.sum(dominant == index)),
                "dominant_cell_share_scoreable": float(np.sum(dominant == index) / scoreable.sum()),
                "mean_weighted_contribution": float(np.nanmean(contributions[index - 1])),
            }
        )
    index_rows = [
        {
            "site": SITE.label,
            "map_type": "largest_weighted_contribution",
            "format": path.suffix.lstrip("."),
            "path": rel(path),
            "source": ";".join(rel(item.source) for item in CRITERIA.values()),
            "source_sha256": ";".join(sha256(item.source) for item in CRITERIA.values()),
            "class_note": "criterion with largest direct weighted contribution on five-criterion common-support cells",
            "classification": "categorical argmax of five weighted criterion contributions",
            "claim_level": "sensitivity_scenario",
        }
        for path in (png, pdf)
    ]
    return index_rows, summary_rows


def result_summary(priority: np.ndarray, layers: OrderedDict[str, np.ndarray]) -> list[dict[str, object]]:
    valid = np.isfinite(priority)
    _, profile = maps.read_raster(PIM)
    boundary_support = study_area_mask(profile)
    classes = maps.classify_equal_interval(priority, maps.PRIORITY_BOUNDS)
    labels = ["very_low", "low", "moderate", "high", "very_high"]
    rows = []
    for class_value, label in enumerate(labels, start=1):
        count = int(np.sum(classes == class_value))
        rows.append(
            {
                "metric": f"{label}_class_area_km2",
                "value": round(count * CELL_AREA_KM2, 4),
                "definition": maps.PRIORITY_LABELS[class_value - 1],
            }
        )
    rows.extend(
        [
            {
                "metric": "five_criterion_scored_area_km2",
                "value": round(float(valid.sum() * CELL_AREA_KM2), 4),
                "definition": "cells where all five criteria are available",
            },
            {
                "metric": "five_criterion_coverage_fraction",
                "value": round(float(valid.sum() / boundary_support.sum()), 6),
                "definition": "cells represented by all five criteria divided by mapped study-area cells",
            },
        ]
    )
    return rows


def normalize_index_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized = []
    for row in rows:
        normalized.append(
            {
                "site": row["site"],
                "map_type": row["map_type"],
                "format": row["format"],
                "path": row["path"],
                "source": row["source"],
                "source_sha256": row["source_sha256"],
                "classification": row.get("classification", "equal interval 0-1, five classes"),
                "palette_id": PALETTE_ID,
                "class_note": row["class_note"],
                "weight_type": "direct recommended weights; no pairwise matrix or consistency ratio supplied",
                "claim_level": "sensitivity_scenario",
            }
        )
    return normalized


def main() -> None:
    for path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    layers, profile = read_criteria()
    priority, pim_profile = maps.read_raster(PIM)
    assert_same_grid(profile, pim_profile, "PIM")

    old_out_dir = maps.OUT_DIR
    maps.OUT_DIR = OUT_DIR
    try:
        index_rows = save_study_area_map()
        index_rows.extend(save_criterion_maps(layers, profile))
        index_rows.extend(save_priority_map(priority, profile))
    finally:
        maps.OUT_DIR = old_out_dir
    contribution_index, contribution_rows = save_contribution_map(layers, priority, profile)
    index_rows.extend(contribution_index)

    write_csv(INDEX, normalize_index_rows(index_rows))
    write_csv(DATA_STRENGTH, data_strength_rows())
    write_csv(RESULT_SUMMARY, result_summary(priority, layers))
    write_csv(CONTRIBUTION_SUMMARY, contribution_rows)
    print(f"wrote Zimbabwe reporting maps to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
