#!/usr/bin/env python3
"""Summarize WorldPop population by Peru PIM class."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject

ROOT = Path(__file__).resolve().parents[2]
POP = ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj_peru_hybas_l7_6070641200_bbox.tif"
PIM = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif"
TOP20_MASK = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/top20_mentor_peru_direct_pim.tif"
SCENARIO_SUMMARY = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_priority_summary.csv"
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
OUT_DIR = ROOT / "outputs/peru_gap_closure_analysis"

INPUTS = [
    ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj_peru_hybas_l7_6070641200_bbox.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/top20_mentor_peru_direct_pim.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_priority_summary.csv",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/peru_gap_closure_analysis/peru_population_by_pim_class.csv",
    ROOT / "outputs/peru_gap_closure_analysis/peru_population_by_pim_class_manifest.json",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_top20_threshold() -> float:
    with SCENARIO_SUMMARY.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("scenario") == "mentor_peru_direct_pim":
                return float(row["top20_threshold"])
    raise RuntimeError("mentor_peru_direct_pim top20_threshold not found")


def classify(score: np.ndarray) -> np.ndarray:
    classes = np.zeros(score.shape, dtype="uint8")
    valid = np.isfinite(score)
    classes[valid & (score >= 0.0) & (score < 0.2)] = 1
    classes[valid & (score >= 0.2) & (score < 0.4)] = 2
    classes[valid & (score >= 0.4) & (score < 0.6)] = 3
    classes[valid & (score >= 0.6) & (score < 0.8)] = 4
    classes[valid & (score >= 0.8)] = 5
    return classes


def aggregate_population_to_pim_grid(pop_path: Path, pim_profile: dict) -> np.ndarray:
    """Aggregate population counts onto the native PIM grid with sum resampling."""

    population = np.full(
        (int(pim_profile["height"]), int(pim_profile["width"])),
        np.nan,
        dtype="float64",
    )
    with rasterio.open(pop_path) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=population,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=pim_profile["transform"],
            dst_crs=pim_profile["crs"],
            dst_nodata=np.nan,
            resampling=Resampling.sum,
        )
    population[population < 0.0] = np.nan
    return population


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    top20 = read_top20_threshold()

    with rasterio.open(PIM) as pim_src:
        score = pim_src.read(1).astype("float32")
        if pim_src.nodata is not None:
            score[score == pim_src.nodata] = np.nan
        pim_profile = pim_src.profile.copy()
    with rasterio.open(TOP20_MASK) as selection_src:
        if (
            selection_src.crs != pim_profile["crs"]
            or selection_src.transform != pim_profile["transform"]
            or selection_src.width != pim_profile["width"]
            or selection_src.height != pim_profile["height"]
        ):
            raise ValueError("top-20 selection raster does not match the PIM grid")
        selection = selection_src.read(1).astype("float32")
        if selection_src.nodata is not None:
            selection[selection == selection_src.nodata] = np.nan
    pop_arr = aggregate_population_to_pim_grid(POP, pim_profile)
    boundary = gpd.read_file(BOUNDARY, layer="peru_pilot_boundary").to_crs(pim_profile["crs"])
    boundary_mask = geometry_mask(
        boundary.geometry,
        out_shape=(pim_profile["height"], pim_profile["width"]),
        transform=pim_profile["transform"],
        invert=True,
    )

    valid = boundary_mask & np.isfinite(pop_arr) & np.isfinite(score) & (pop_arr >= 0)
    classes = classify(score)
    labels = {
        1: "very_low",
        2: "low",
        3: "moderate",
        4: "high",
        5: "very_high",
    }
    rows = []
    total_pop = float(pop_arr[valid].sum())
    boundary_population = float(np.nansum(pop_arr[boundary_mask]))
    unscored_population = float(
        np.nansum(pop_arr[boundary_mask & np.isfinite(pop_arr) & ~np.isfinite(score)])
    )
    for cls, label in labels.items():
        mask = valid & (classes == cls)
        pop_sum = float(pop_arr[mask].sum())
        rows.append(
            {
                "scenario": "mentor_peru_direct_pim",
                "classification": "equal_interval_0_1",
                "priority_class": cls,
                "priority_label": label,
                "population_sum": pop_sum,
                "population_share": pop_sum / total_pop if total_pop else 0,
                "pim_cells": int(mask.sum()),
            }
        )

    top_mask = valid & (selection >= 0.5)
    rows.append(
        {
            "scenario": "mentor_peru_direct_pim",
            "classification": "top20_threshold",
            "priority_class": "top20",
            "priority_label": "top_20_percent_priority_cells",
            "population_sum": float(pop_arr[top_mask].sum()),
            "population_share": float(pop_arr[top_mask].sum()) / total_pop if total_pop else 0,
            "pim_cells": int(top_mask.sum()),
        }
    )

    out_csv = OUT_DIR / "peru_population_by_pim_class.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "output": rel(out_csv),
        "population_source": rel(POP),
        "population_sha256": sha256(POP),
        "pim_source": rel(PIM),
        "pim_sha256": sha256(PIM),
        "top20_selection_source": rel(TOP20_MASK),
        "top20_selection_sha256": sha256(TOP20_MASK),
        "method": "WorldPop counts sum-aggregated to the native PIM grid; the canonical scenario selection raster defines the highest-priority quintile",
        "top20_threshold": top20,
        "total_population_with_valid_pim": total_pop,
        "population_inside_boundary": boundary_population,
        "population_in_unscored_cells": unscored_population,
        "unscored_population_share": (
            unscored_population / boundary_population if boundary_population else 0.0
        ),
        "claim_level": "diagnostic_only",
        "evidence_role": "endogenous_exposure_accounting",
        "independence_note": (
            "WorldPop contributes to the PIM exposure indicators, so this summary describes "
            "model-implied exposed population and is not an independent validation."
        ),
    }
    with (OUT_DIR / "peru_population_by_pim_class_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote: {rel(out_csv)}")


if __name__ == "__main__":
    main()
