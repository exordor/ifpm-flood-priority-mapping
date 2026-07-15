#!/usr/bin/env python3
"""Diagnose spatial co-location between Peru PIM cells and SINPAD event points."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
SINPAD = ROOT / "data/validation/indeci_sinpad_peru_flood_events/peru_hybas_l7_6070641200_sinpad_flood_relevant.gpkg"
PIM = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif"
TOP20_MASK = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/top20_mentor_peru_direct_pim.tif"
EVIDENCE_COUNT = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/criteria_evidence_count.tif"
AVAILABLE_WEIGHT = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/available_main_weight.tif"
EVIDENCE_SUPPORT = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/evidence_support_class.tif"
SCENARIO_SUMMARY = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_priority_summary.csv"
OUT_DIR = ROOT / "outputs/peru_gap_closure_analysis"

INPUTS = [
    ROOT / "data/validation/indeci_sinpad_peru_flood_events/peru_hybas_l7_6070641200_sinpad_flood_relevant.gpkg",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/top20_mentor_peru_direct_pim.tif",
    EVIDENCE_COUNT,
    AVAILABLE_WEIGHT,
    EVIDENCE_SUPPORT,
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenario_priority_summary.csv",
]
OUTPUTS = [
    ROOT / "outputs/peru_gap_closure_analysis/peru_hybas_l7_6070641200_sinpad_pim_colocation.gpkg",
    ROOT / "outputs/peru_gap_closure_analysis/peru_hybas_l7_6070641200_sinpad_pim_colocation.csv",
    ROOT / "outputs/peru_gap_closure_analysis/peru_sinpad_colocation_cohorts.csv",
    ROOT / "outputs/peru_gap_closure_analysis/peru_sinpad_colocation_manifest.json",
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


def class_label(score: float) -> tuple[int, str]:
    if not np.isfinite(score):
        return 0, "outside_valid_pim"
    if score < 0.2:
        return 1, "very_low"
    if score < 0.4:
        return 2, "low"
    if score < 0.6:
        return 3, "moderate"
    if score < 0.8:
        return 4, "high"
    return 5, "very_high"


def summarize_cohort(
    name: str,
    frame: gpd.GeoDataFrame,
    *,
    selected_area_fraction: float,
) -> dict[str, object]:
    valid = frame["pim_score"].notna()
    valid_count = int(valid.sum())
    selected = int(frame.loc[valid, "in_top20_priority_cells"].sum())
    unscored = ~valid
    support = frame["evidence_support_class"]
    observed_share = selected / valid_count if valid_count else 0.0
    return {
        "cohort": name,
        "record_count": int(len(frame)),
        "valid_pim_count": valid_count,
        "top20_count": selected,
        "full_five_valid_count": valid_count,
        "unscored_count": int(unscored.sum()),
        "unscored_ls_missing_count": int((unscored & (support == 2)).sum()),
        "unscored_k_missing_count": int((unscored & (support == 3)).sum()),
        "unscored_other_evidence_count": int((unscored & (support == 4)).sum()),
        "top20_share": observed_share,
        "selected_area_fraction": selected_area_fraction,
    }


def sample_aligned_raster(
    path: Path,
    pim_profile: dict,
    coords: list[tuple[float, float]],
) -> list[float]:
    with rasterio.open(path) as src:
        if (
            src.crs != pim_profile["crs"]
            or src.transform != pim_profile["transform"]
            or src.width != pim_profile["width"]
            or src.height != pim_profile["height"]
        ):
            raise ValueError(f"evidence raster does not match the PIM grid: {path}")
        values = [value[0] for value in src.sample(coords)]
        return [
            np.nan if src.nodata is not None and value == src.nodata else float(value)
            for value in values
        ]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    top20 = read_top20_threshold()
    gdf = gpd.read_file(SINPAD)
    with rasterio.open(PIM) as src:
        pts = gdf.to_crs(src.crs)
        coords = [(geom.x, geom.y) for geom in pts.geometry]
        sampled = [v[0] for v in src.sample(coords)]
        scores = [np.nan if src.nodata is not None and v == src.nodata else float(v) for v in sampled]
        pim_profile = src.profile.copy()
    with rasterio.open(TOP20_MASK) as selection_src:
        if (
            selection_src.crs != pim_profile["crs"]
            or selection_src.transform != pim_profile["transform"]
            or selection_src.width != pim_profile["width"]
            or selection_src.height != pim_profile["height"]
        ):
            raise ValueError("top-20 selection raster does not match the PIM grid")
        sampled_selection = [value[0] for value in selection_src.sample(coords)]
        selection = selection_src.read(1).astype("float32")
        if selection_src.nodata is not None:
            selection[selection == selection_src.nodata] = np.nan
        valid_selection = np.isfinite(selection)
        selected_area_fraction = float(np.sum(valid_selection & (selection >= 0.5)) / valid_selection.sum())

    evidence_count = sample_aligned_raster(EVIDENCE_COUNT, pim_profile, coords)
    available_weight = sample_aligned_raster(AVAILABLE_WEIGHT, pim_profile, coords)
    evidence_support = sample_aligned_raster(EVIDENCE_SUPPORT, pim_profile, coords)

    gdf["pim_score"] = scores
    class_values = [class_label(score) for score in scores]
    gdf["pim_class"] = [c for c, _ in class_values]
    gdf["pim_class_label"] = [label for _, label in class_values]
    gdf["in_top20_priority_cells"] = [
        bool(np.isfinite(score) and np.isfinite(selected) and selected >= 0.5)
        for score, selected in zip(scores, sampled_selection, strict=True)
    ]
    gdf["criteria_evidence_count"] = evidence_count
    gdf["available_main_weight"] = available_weight
    gdf["evidence_support_class"] = evidence_support
    support_labels = {
        1: "full_five_criteria_scored",
        2: "unscored_ls_unavailable",
        3: "unscored_k_unavailable",
        4: "unscored_other_required_evidence",
    }
    gdf["evidence_support"] = [
        support_labels.get(int(value), "outside_boundary_or_unclassified")
        if np.isfinite(value)
        else "outside_boundary_or_unclassified"
        for value in evidence_support
    ]
    gdf["coordinate_key"] = gdf.geometry.to_wkb(hex=True)
    gdf["is_flood_specific"] = gdf["FENOMENO"].astype(str).str.contains("INUND", case=False, na=False)

    out_gpkg = OUT_DIR / "peru_hybas_l7_6070641200_sinpad_pim_colocation.gpkg"
    out_csv = OUT_DIR / "peru_hybas_l7_6070641200_sinpad_pim_colocation.csv"
    gdf.to_file(out_gpkg, layer="sinpad_pim_colocation", driver="GPKG")
    gdf.drop(columns="geometry").to_csv(out_csv, index=False)

    unique_all = gdf.drop_duplicates(subset=["coordinate_key"])
    flood_records = gdf[gdf["is_flood_specific"]]
    unique_flood = flood_records.drop_duplicates(subset=["coordinate_key"])
    rows = [
        summarize_cohort("all_hydrometeorological_records", gdf, selected_area_fraction=selected_area_fraction),
        summarize_cohort("unique_locations_all_records", unique_all, selected_area_fraction=selected_area_fraction),
        summarize_cohort("flood_specific_records", flood_records, selected_area_fraction=selected_area_fraction),
        summarize_cohort("unique_locations_flood_specific", unique_flood, selected_area_fraction=selected_area_fraction),
    ]

    summary_csv = OUT_DIR / "peru_sinpad_colocation_cohorts.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=sorted({k for row in rows for k in row.keys()}))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "sinpad_source": rel(SINPAD),
        "sinpad_sha256": sha256(SINPAD),
        "pim_source": rel(PIM),
        "pim_sha256": sha256(PIM),
        "top20_selection_source": rel(TOP20_MASK),
        "top20_selection_sha256": sha256(TOP20_MASK),
        "criteria_evidence_count_source": rel(EVIDENCE_COUNT),
        "criteria_evidence_count_sha256": sha256(EVIDENCE_COUNT),
        "available_main_weight_source": rel(AVAILABLE_WEIGHT),
        "available_main_weight_sha256": sha256(AVAILABLE_WEIGHT),
        "evidence_support_source": rel(EVIDENCE_SUPPORT),
        "evidence_support_sha256": sha256(EVIDENCE_SUPPORT),
        "point_output": rel(out_gpkg),
        "summary_output": rel(summary_csv),
        "records_sampled": int(len(gdf)),
        "unique_locations": int(len(unique_all)),
        "flood_specific_records": int(len(flood_records)),
        "unique_flood_locations": int(len(unique_flood)),
        "top20_threshold": top20,
        "selected_area_fraction": selected_area_fraction,
        "records_in_valid_pim": int(np.isfinite(gdf["pim_score"]).sum()),
        "top20_event_count": int(gdf["in_top20_priority_cells"].sum()),
        "records_with_full_five_criteria": int(gdf["pim_score"].notna().sum()),
        "unscored_records_ls_unavailable": int((gdf["evidence_support_class"] == 2).sum()),
        "unscored_records_k_unavailable": int((gdf["evidence_support_class"] == 3).sum()),
        "unscored_records_other_evidence": int((gdf["evidence_support_class"] == 4).sum()),
        "claim_level": "diagnostic_only",
        "evidence_role": "event_point_colocation_context",
        "note": (
            "SINPAD geometries are event reference points rather than observed flood extents. "
            "Repeated coordinates, rainfall-only records, and unscored support causes are "
            "reported separately; the selected-area fraction is descriptive, not a null "
            "model. This is a co-location diagnostic, not "
            "independent model validation."
        ),
    }
    with (OUT_DIR / "peru_sinpad_colocation_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote: {rel(summary_csv)}")


if __name__ == "__main__":
    main()
