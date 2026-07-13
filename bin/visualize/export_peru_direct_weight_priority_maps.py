#!/usr/bin/env python3
"""Export slide-ready Peru maps for the current direct-weight scenario."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_paper_style_single_maps as maps


SOURCE = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
    "priority_mentor_peru_direct_pim.tif"
)
TOP20_SOURCE = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
    "top20_mentor_peru_direct_pim.tif"
)
EVIDENCE_SUPPORT = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/evidence_support_class.tif"
)
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
OUT_DIR = ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps"

INPUTS = [
    ROOT / "bin/visualize/export_paper_style_single_maps.py",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/top20_mentor_peru_direct_pim.tif",
    EVIDENCE_SUPPORT,
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/peru_direct_weight_priority_screening_5class_paper_style_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/peru_direct_weight_priority_screening_5class_paper_style_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/peru_direct_weight_top20_scored_cells_paper_style_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/peru_direct_weight_top20_scored_cells_paper_style_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/index.csv",
]


SITE = maps.Site(
    slug="peru",
    label="Peru Arequipa Region, mainly Vitor-La Joya-Santa Rita de Siguas west of Arequipa city",
    claim_level="sensitivity_scenario",
    priority_mean=SOURCE,
    flood_conditioning=ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_conditioning_factors_0_1.tif",
    boundary_gpkg=BOUNDARY,
    boundary_layer="peru_pilot_boundary",
)


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
    original_out_dir = maps.OUT_DIR
    maps.OUT_DIR = OUT_DIR
    try:
        priority, profile = maps.read_raster(SOURCE)
        evidence_support, evidence_profile = maps.read_raster(EVIDENCE_SUPPORT)
        if evidence_profile != profile:
            raise ValueError("evidence-support raster does not match the direct-weight PIM grid")
        evidence_support = np.nan_to_num(evidence_support, nan=0).astype("uint8")
        support_overlays = [
            (evidence_support, 2, "Unscored: LS unavailable", "////"),
            (evidence_support, 3, "Unscored: K unavailable", "xxxx"),
            (evidence_support, 4, "Unscored: other required evidence", "...."),
        ]
        classes = maps.classify_equal_interval(priority, maps.PRIORITY_BOUNDS)
        rows = maps.save_class_map(
            SITE,
            SOURCE,
            classes,
            profile,
            "direct_weight_priority_screening_5class",
            "Priority screening score",
            maps.PRIORITY_LABELS,
            maps.PRIORITY_COLORS,
            "equal interval classes on five-criterion common-support cells; direct weights 0.35/0.25/0.20/0.12/0.08; hatches identify unscored evidence gaps",
            overlay_specs=support_overlays,
        )
        selection, selection_profile = maps.read_raster(TOP20_SOURCE)
        if selection_profile != profile:
            raise ValueError("top-20 selection raster does not match the direct-weight PIM grid")
        top20_classes = selection.copy()
        top20_classes[np.isfinite(selection)] = np.where(selection[np.isfinite(selection)] >= 0.5, 2, 1)
        top20_classes[~np.isfinite(selection)] = 0
        top20_classes = top20_classes.astype("uint8")
        threshold = float(np.nanpercentile(priority, 80))
        top20_rows = maps.save_class_map(
                SITE,
                SOURCE,
                top20_classes,
                profile,
                "direct_weight_top20_scored_cells",
                "Highest-priority scored cells",
                ["Other scored cells", "Highest-priority quintile"],
                maps.TOP20_COLORS,
                f"highest-priority quintile among five-criterion common-support cells; threshold={threshold:.9f}; hatches identify unscored evidence gaps",
                overlay_specs=support_overlays,
            )
        for row in top20_rows:
            row["selection_source"] = maps.rel(TOP20_SOURCE)
            row["selection_sha256"] = maps.sha256(TOP20_SOURCE)
        for row in rows + top20_rows:
            row["evidence_support_source"] = maps.rel(EVIDENCE_SUPPORT)
            row["evidence_support_sha256"] = maps.sha256(EVIDENCE_SUPPORT)
        rows.extend(top20_rows)
    finally:
        maps.OUT_DIR = original_out_dir
    write_csv(OUT_DIR / "index.csv", rows)
    print(f"wrote {len(rows)} direct-weight map outputs to {maps.rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
