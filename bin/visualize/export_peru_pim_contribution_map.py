#!/usr/bin/env python3
"""Export the largest weighted contribution per cell for the Peru direct-weight PIM."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_peru_pim_criteria_maps as maps


CRITERIA_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria"
OUT_DIR = ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map"

CRITERIA = {
    "flood_hazard": CRITERIA_DIR / "flood_hazard_0_1.tif",
    "sediment": CRITERIA_DIR / "sediment_0_1.tif",
    "landuse_asm": CRITERIA_DIR / "landuse_asm_0_1.tif",
    "environmental": CRITERIA_DIR / "environmental_0_1.tif",
    "socioeconomic": CRITERIA_DIR / "socioeconomic_0_1.tif",
}
WEIGHTS = {
    "flood_hazard": 0.35,
    "sediment": 0.25,
    "landuse_asm": 0.20,
    "environmental": 0.12,
    "socioeconomic": 0.08,
}
LABELS = {
    "flood_hazard": "Flood hazard",
    "sediment": "Sediment / erosion",
    "landuse_asm": "Land use / ASM",
    "environmental": "Environmental sensitivity",
    "socioeconomic": "Socioeconomic exposure",
}
COLORS = ["#2b83ba", "#d95f0e", "#31a354", "#9e9ac8", "#636363"]

INPUTS = [
    ROOT / "bin/visualize/export_peru_pim_criteria_maps.py",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/flood_hazard_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/sediment_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/landuse_asm_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/environmental_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/socioeconomic_0_1.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/peru_largest_weighted_contribution_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/peru_largest_weighted_contribution_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/contribution_summary.csv",
    ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/index.csv",
]


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    layers: dict[str, np.ndarray] = {}
    profile = None
    for name, path in CRITERIA.items():
        data, current = maps.read_raster(path)
        if profile is None:
            profile = current
        elif (
            current["crs"] != profile["crs"]
            or current["transform"] != profile["transform"]
            or current["width"] != profile["width"]
            or current["height"] != profile["height"]
        ):
            raise ValueError(f"criterion grid mismatch: {path}")
        layers[name] = data
    assert profile is not None

    order = list(CRITERIA)
    common_valid = np.logical_and.reduce([np.isfinite(layers[name]) for name in order])
    contributions = np.stack([layers[name] * WEIGHTS[name] for name in order])
    dominant = np.zeros(common_valid.shape, dtype="uint8")
    dominant[common_valid] = np.argmax(contributions[:, common_valid], axis=0).astype("uint8") + 1

    projected, extent = maps.reproject_class(dominant, profile)
    frame_extent = maps.frame_extent_for_legend(extent)
    cmap = ListedColormap(COLORS)
    norm = BoundaryNorm(np.arange(0.5, len(COLORS) + 1.5), len(COLORS))
    masked = np.ma.masked_where(projected == 0, projected)

    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    ax.imshow(masked, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest", zorder=1)
    maps.add_boundary_and_frame(ax, frame_extent)
    maps.add_north_arrow(ax)
    maps.add_scale_bar(ax, frame_extent)
    handles = [
        Patch(facecolor=color, edgecolor="0.4", label=LABELS[name])
        for name, color in zip(order, COLORS, strict=True)
    ]
    handles.append(Patch(facecolor="#d9d9d9", edgecolor="0.4", label="Unscored (missing sediment evidence)"))
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

    png = OUT_DIR / "peru_largest_weighted_contribution_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

    weighted_means = {
        name: float(np.mean(contributions[index][common_valid]))
        for index, name in enumerate(order)
    }
    total_mean = sum(weighted_means.values())
    rows = []
    for index, name in enumerate(order, start=1):
        rows.append(
            {
                "criterion": name,
                "direct_weight": WEIGHTS[name],
                "mean_criterion_score_common_valid": float(np.mean(layers[name][common_valid])),
                "weighted_mean_contribution": weighted_means[name],
                "realized_mean_contribution_share": weighted_means[name] / total_mean if total_mean else 0.0,
                "dominant_cells": int(np.sum(dominant == index)),
                "dominant_cell_share_common_valid": float(np.sum(dominant == index) / common_valid.sum()),
            }
        )
    write_csv(OUT_DIR / "contribution_summary.csv", rows)

    source_hashes = ";".join(f"{name}:{sha256(path)}" for name, path in CRITERIA.items())
    write_csv(
        OUT_DIR / "index.csv",
        [
            {
                "map_type": "largest_weighted_contribution",
                "figure_path": rel(path),
                "figure_format": path.suffix.lstrip("."),
                "source_rasters": ";".join(rel(path) for path in CRITERIA.values()),
                "source_sha256": source_hashes,
                "classification": "criterion with largest weighted contribution per common-valid cell",
                "weight_type": "direct recommended weights; no pairwise matrix or consistency ratio supplied",
                "claim_level": "sensitivity_scenario",
            }
            for path in (png, pdf)
        ],
    )
    print(f"wrote weighted-contribution map to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
