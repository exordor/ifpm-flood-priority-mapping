#!/usr/bin/env python3
"""Run the Goslar L2 independent-context consistency check.

L2 means spatial consistency against independent flood-context evidence. It is
not event-accuracy validation: no precision/recall/AUC/IoU metric is produced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/goslar_l2_independent_consistency"
PIM = ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios/scenarios/priority_goslar_direct_pim.tif"
FLOOD_HAZARD = ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios/pim_criteria/flood_hazard_0_1.tif"
PIM_MANIFEST = ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios/run_manifest.json"
HWRM = ROOT / "outputs/goslar_official_hydrology_and_flood_data/goslar_hwrm_flood_hazard_boundaries_12km.gpkg"
S2_NEW_WATER = ROOT / "outputs/goslar_2017_satellite_validation/new_surface_water_candidate_10m.tif"
S2_QA = ROOT / "outputs/goslar_2017_satellite_validation/water_change_qa.json"
TERRAIN = {
    "twi": ROOT / "outputs/srtm_1arcsec_goslar/hydrology_derivatives/goslar_focus_twi.tif",
    "distance_to_drainage": ROOT / "outputs/srtm_1arcsec_goslar/hydrology_derivatives/goslar_focus_distance_to_drainage_t500.tif",
    "elevation": ROOT / "outputs/srtm_1arcsec_goslar/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif",
    "slope": ROOT / "outputs/srtm_1arcsec_goslar/terrain_preprocessing/goslar_focus_slope_degrees_utm32n_30m.tif",
}

HWRM_BANDS_M = (0, 100, 250, 500)
S2_MIN_FRACTION = 0.05
BOOTSTRAP_REPEATS = 2000
NULL_REPEATS = 2000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_float(path: Path) -> np.ndarray:
    with rasterio.open(path) as source:
        values = source.read(1).astype("float64")
        if source.nodata is not None:
            values[values == source.nodata] = np.nan
    values[~np.isfinite(values)] = np.nan
    return values


def float_or_none(value: float | np.floating | None) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result if np.isfinite(result) else None


def bootstrap_mean_difference(
    first: np.ndarray,
    second: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, float | None]:
    if first.size == 0 or second.size == 0:
        return {"difference": None, "ci_low": None, "ci_high": None}
    differences = np.empty(BOOTSTRAP_REPEATS, dtype="float64")
    for index in range(BOOTSTRAP_REPEATS):
        left = first[rng.integers(0, first.size, first.size)]
        right = second[rng.integers(0, second.size, second.size)]
        differences[index] = left.mean() - right.mean()
    return {
        "difference": float(first.mean() - second.mean()),
        "ci_low": float(np.quantile(differences, 0.025)),
        "ci_high": float(np.quantile(differences, 0.975)),
    }


def random_null_difference(
    target: np.ndarray,
    candidate_pool: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, float | None]:
    sample_count = min(target.size, candidate_pool.size)
    if sample_count == 0:
        return {"mean": None, "ci_low": None, "ci_high": None, "target_percentile": None}
    random_means = np.empty(NULL_REPEATS, dtype="float64")
    for index in range(NULL_REPEATS):
        sample = candidate_pool[rng.integers(0, candidate_pool.size, sample_count)]
        random_means[index] = sample.mean()
    observed = float(target.mean())
    return {
        "mean": float(random_means.mean()),
        "ci_low": float(np.quantile(random_means, 0.025)),
        "ci_high": float(np.quantile(random_means, 0.975)),
        "target_percentile": float((random_means <= observed).mean() * 100.0),
    }


def hwrm_check(
    values: np.ndarray,
    valid: np.ndarray,
    reference_grid: rasterio.DatasetReader,
    rng: np.random.Generator,
) -> dict:
    polygons = gpd.read_file(HWRM).to_crs(reference_grid.crs)
    cumulative: list[np.ndarray] = []
    for band in HWRM_BANDS_M:
        geometry = polygons.geometry.union_all()
        if band:
            geometry = geometry.buffer(band)
        cumulative_mask = (
            geometry_mask(
                [geometry],
                out_shape=values.shape,
                transform=reference_grid.transform,
                invert=True,
            )
            & valid
        )
        cumulative.append(cumulative_mask)

    bands: list[dict] = []
    for index, band in enumerate(HWRM_BANDS_M):
        zone = cumulative[index].copy()
        if index:
            zone &= ~cumulative[index - 1]
        outside_pool = values[valid & ~cumulative[-1]]
        target = values[zone]
        statistics = bootstrap_mean_difference(target, outside_pool, rng)
        null = random_null_difference(target, outside_pool, rng)
        bands.append(
            {
                "buffer_m": band,
                "definition": "polygon overlap" if band == 0 else f"{HWRM_BANDS_M[index - 1]}-{band} m ring",
                "cells": int(zone.sum()),
                "mean_pim": float_or_none(target.mean()) if target.size else None,
                "mean_pim_outside_all_hwrm_zones": float_or_none(outside_pool.mean()) if outside_pool.size else None,
                "bootstrap": statistics,
                "equal_area_random_null": null,
            }
        )

    positive = [band for band in bands if (band["bootstrap"]["difference"] or 0) > 0]
    strong_percentile = [band for band in bands if (band["equal_area_random_null"]["target_percentile"] or 0) >= 95]
    weak_percentile = [band for band in bands if (band["equal_area_random_null"]["target_percentile"] or 0) >= 80]
    if len(positive) == len(bands) and len(strong_percentile) >= 3:
        status = "consistent"
    elif len(positive) >= 2 and len(weak_percentile) >= 2:
        status = "weakly_consistent"
    else:
        status = "inconsistent_or_unclear"
    return {
        "evidence": "NLWKN HWRM-RL modelled regulatory flood-hazard boundaries",
        "independence": "external regulatory scenario polygons; not PIM inputs",
        "status": status,
        "decision_rule": (
            "consistent requires all four zones positive and at least three equal-area random percentiles >=95; "
            "weakly_consistent requires at least two positive zones and two percentiles >=80"
        ),
        "bands": bands,
        "interpretation": (
            "Higher PIM means in/near HWRM zones indicate spatial context consistency only. "
            "HWRM polygons are modelled regulatory scenarios, not observed 2017 inundation."
        ),
    }


def s2_fraction_on_reference(path: Path, reference_grid: rasterio.DatasetReader) -> np.ndarray:
    with rasterio.open(path) as source:
        values = source.read(1)
        source_nodata = source.nodata if source.nodata is not None else 255
        valid_source = values != source_nodata
        fraction = np.full(reference_grid.shape, np.nan, dtype="float32")
        coverage = np.full(reference_grid.shape, np.nan, dtype="float32")
        reproject(
            values.astype("float32"),
            fraction,
            src_transform=source.transform,
            src_crs=source.crs,
            src_nodata=source_nodata,
            dst_transform=reference_grid.transform,
            dst_crs=reference_grid.crs,
            dst_nodata=np.nan,
            resampling=Resampling.average,
        )
        reproject(
            valid_source.astype("float32"),
            coverage,
            src_transform=source.transform,
            src_crs=source.crs,
            src_nodata=source_nodata,
            dst_transform=reference_grid.transform,
            dst_crs=reference_grid.crs,
            dst_nodata=np.nan,
            resampling=Resampling.average,
        )
        fraction[coverage < 0.999] = np.nan
        return fraction


def sentinel_check(
    values: np.ndarray,
    valid: np.ndarray,
    reference_grid: rasterio.DatasetReader,
    rng: np.random.Generator,
) -> dict:
    fraction = s2_fraction_on_reference(S2_NEW_WATER, reference_grid)
    candidate = valid & (fraction >= S2_MIN_FRACTION)
    background = valid & (fraction < S2_MIN_FRACTION)
    target = values[candidate]
    pool = values[background]
    statistics = bootstrap_mean_difference(target, pool, rng)
    null = random_null_difference(target, pool, rng)
    difference = statistics["difference"]
    ci_low = statistics["ci_low"]
    if difference is not None and difference > 0 and ci_low is not None and ci_low > 0:
        status = "consistent"
    elif difference is not None and difference > 0:
        status = "weakly_consistent"
    else:
        status = "inconsistent_or_unclear"
    return {
        "evidence": "Sentinel-2 NDWI new surface-water candidate (2017-07-21 to 2017-07-31)",
        "independence": "external event-window optical candidate; not a PIM input",
        "status": status,
        "decision_rule": (
            "consistent requires a positive candidate-background difference with bootstrap CI low >0; "
            "weakly_consistent requires only a positive difference"
        ),
        "resampling": {
            "native_resolution_m": 10,
            "reference_resolution_m": reference_grid.res[0],
            "method": "average fraction of candidate 10 m cells per 30 m cell",
            "minimum_fraction": S2_MIN_FRACTION,
        },
        "cells": {
            "candidate": int(candidate.sum()),
            "background": int(background.sum()),
        },
        "mean_pim": {
            "candidate": float_or_none(target.mean()) if target.size else None,
            "background": float_or_none(pool.mean()) if pool.size else None,
        },
        "bootstrap": statistics,
        "equal_area_random_null": null,
        "interpretation": (
            "This is soft supporting evidence only. The after scene is five days post-peak; "
            "NDWI candidates are affected by clouds, canopy, shadow and terrain."
        ),
    }


def quartile_means(values: np.ndarray, mask: np.ndarray) -> list[float | None]:
    data = values[mask]
    if data.size == 0:
        return [None, None, None, None]
    thresholds = np.quantile(data, [0.25, 0.5, 0.75])
    target = values[mask]
    labels = np.digitize(target, thresholds)
    return [
        float_or_none(target[labels == index].mean()) if np.any(labels == index) else None
        for index in range(4)
    ]


def terrain_check(values: np.ndarray, valid: np.ndarray, label: str) -> dict:
    correlations = {}
    quartiles = {}
    expected = {
        "twi": "positive",
        "distance_to_drainage": "negative",
        "elevation": "lower quartiles generally higher",
        "slope": "lower quartiles generally higher",
    }
    for name, path in TERRAIN.items():
        covariate = read_float(path)
        mask = valid & np.isfinite(covariate)
        rho, p_value = spearmanr(values[mask], covariate[mask])
        correlations[name] = {
            "spearman_rho": float_or_none(rho),
            "p_value_descriptive_only": float_or_none(p_value),
            "cells": int(mask.sum()),
            "expected_direction": expected[name],
        }
        quartiles[name] = quartile_means(values, mask)

    twi_ok = (correlations["twi"]["spearman_rho"] or 0) >= 0.05
    drainage_ok = (correlations["distance_to_drainage"]["spearman_rho"] or 0) <= -0.20
    elevation_means = quartiles["elevation"]
    slope_means = quartiles["slope"]
    additional = 0
    if all(value is not None for value in elevation_means) and elevation_means[0] > np.nanmean(elevation_means):
        additional += 1
    if all(value is not None for value in slope_means) and slope_means[0] > np.nanmean(slope_means):
        additional += 1
    if twi_ok and drainage_ok and additional == 2:
        status = "consistent"
    elif twi_ok or drainage_ok:
        status = "weakly_consistent"
    else:
        status = "inconsistent_or_unclear"
    return {
        "target": label,
        "evidence": "terrain and hydrology derivatives used for descriptive sanity review",
        "independence": "internal/model-derived; never described as independent validation",
        "status": status,
        "decision_rule": (
            "consistent requires TWI rho>=0.05, drainage rho<=-0.20, and both elevation/slope "
            "lowest-quartile checks; weakly_consistent requires TWI or drainage to pass"
        ),
        "correlations": correlations,
        "mean_by_quartile": quartiles,
        "interpretation": (
            "Drainage proximity and TWI are expected to align with flood-hazard context. "
            "Elevation and slope quartiles are exploratory because the PIM also contains "
            "exposure, land-use and sediment components."
        ),
    }


def write_csv(path: Path, report: dict) -> None:
    rows = [
        {
            "check_id": "hwrm_regulatory_context",
            "evidence": report["checks"]["hwrm_regulatory_context"]["evidence"],
            "status": report["checks"]["hwrm_regulatory_context"]["status"],
            "key_result": (
                f"PIM minus outside = "
                f"{report['checks']['hwrm_regulatory_context']['bands'][0]['bootstrap']['difference']:.3f} "
                "inside HWRM polygons"
            ),
            "independence": "external context",
            "event_validation": "no",
            "enters_pim": "no",
        },
        {
            "check_id": "sentinel2_new_water_candidate",
            "evidence": report["checks"]["sentinel2_new_water_candidate"]["evidence"],
            "status": report["checks"]["sentinel2_new_water_candidate"]["status"],
            "key_result": (
                f"candidate minus background = "
                f"{report['checks']['sentinel2_new_water_candidate']['bootstrap']['difference']:.3f}"
            ),
            "independence": "external soft evidence",
            "event_validation": "no",
            "enters_pim": "no",
        },
        {
            "check_id": "flood_hazard_terrain_hydrology",
            "evidence": "TWI and distance-to-drainage consistency",
            "status": report["checks"]["flood_hazard_terrain_hydrology"]["status"],
            "key_result": (
                f"TWI rho = {report['checks']['flood_hazard_terrain_hydrology']['correlations']['twi']['spearman_rho']:.3f}; "
                f"distance rho = {report['checks']['flood_hazard_terrain_hydrology']['correlations']['distance_to_drainage']['spearman_rho']:.3f}"
            ),
            "independence": "internal diagnostic",
            "event_validation": "no",
            "enters_pim": "no",
        },
    ]
    header = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(",".join(header) + "\n")
        for row in rows:
            stream.write(",".join(str(row[column]) for column in header) + "\n")


def write_markdown(path: Path, report: dict) -> None:
    checks = report["checks"]
    lines = [
        "# Goslar L2 independent-context consistency check",
        "",
        f"Overall reading: **{report['overall_status']}**. L2 here means spatial consistency against independent flood-context evidence; it is not event-accuracy validation.",
        "",
        "1. HWRM regulatory context: " + str(checks["hwrm_regulatory_context"]["status"]),
        "2. Sentinel-2 new-water candidate: " + str(checks["sentinel2_new_water_candidate"]["status"]),
        "3. Flood-hazard terrain/hydrology diagnostic: " + str(checks["flood_hazard_terrain_hydrology"]["status"]),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def update_pim_manifest(report_path: Path, summary_path: Path, report: dict) -> None:
    manifest = json.loads(PIM_MANIFEST.read_text(encoding="utf-8"))
    manifest["l2_independent_consistency"] = {
        "claim_level": "independent_consistency_check",
        "overall_status": report["overall_status"],
        "event_validation": False,
        "enters_pim_score": False,
        "auc_iou_reported": False,
        "report": str(report_path.relative_to(ROOT)),
        "report_sha256": sha256(report_path),
        "summary_csv": str(summary_path.relative_to(ROOT)),
        "summary_csv_sha256": sha256(summary_path),
        "pim_sha256": sha256(PIM),
    }
    PIM_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_report() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260818)
    with rasterio.open(PIM) as reference_grid:
        pim = read_float(PIM)
        flood_hazard = read_float(FLOOD_HAZARD)
        valid = np.isfinite(pim)
        hazard_valid = valid & np.isfinite(flood_hazard)
        if not np.any(valid) or not np.any(hazard_valid):
            raise ValueError("PIM and flood-hazard inputs must have valid cells")
        hwrm = hwrm_check(pim, valid, reference_grid, rng)
        sentinel = sentinel_check(pim, valid, reference_grid, rng)
    terrain = terrain_check(flood_hazard, hazard_valid, "flood_hazard_criterion")

    statuses = [hwrm["status"], sentinel["status"], terrain["status"]]
    if all(status == "consistent" for status in statuses):
        overall = "consistent"
    elif any(status == "inconsistent_or_unclear" for status in statuses) and not all(status == "consistent" for status in statuses):
        overall = "mixed_or_unclear"
    elif any(status == "weakly_consistent" for status in statuses):
        overall = "weakly_consistent"
    else:
        overall = "inconsistent_or_unclear"

    report = {
        "analysis_id": "goslar_l2_independent_consistency_v1",
        "claim_level": "independent_consistency_check",
        "overall_status": overall,
        "definition": (
            "L2 compares Goslar PIM with independent flood-context evidence for spatial consistency; "
            "it is not event-accuracy validation."
        ),
        "target": {
            "name": "Goslar PIM",
            "path": str(PIM.relative_to(ROOT)),
            "sha256": sha256(PIM),
            "valid_cells": int(valid.sum()),
            "mean": float_or_none(pim[valid].mean()),
        },
        "checks": {
            "hwrm_regulatory_context": hwrm,
            "sentinel2_new_water_candidate": sentinel,
            "flood_hazard_terrain_hydrology": terrain,
        },
        "statistical_boundary": (
            "Bootstrap and random-sample intervals are descriptive under independent-cell resampling; "
            "spatial autocorrelation means they must not be read as design-based p-values."
        ),
        "prohibited_interpretation": [
            "not observed 2017 peak-flood validation",
            "not event precision/recall/AUC/IoU evidence",
            "not a final flood-risk claim",
        ],
        "event_validation": False,
        "auc_iou_reported": False,
        "enters_pim_score": False,
        "run_date": date.today().isoformat(),
        "inputs": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for name, path in (
                ("pim", PIM),
                ("flood_hazard", FLOOD_HAZARD),
                ("hwrm", HWRM),
                ("sentinel2_new_water", S2_NEW_WATER),
                ("sentinel2_qa", S2_QA),
                *(("terrain_" + name, path) for name, path in TERRAIN.items()),
            )
        },
        "software": {
            "script": "bin/analysis/goslar_l2_independent_consistency.py",
            "random_seed": 20260818,
            "bootstrap_repeats": BOOTSTRAP_REPEATS,
            "random_null_repeats": NULL_REPEATS,
        },
    }
    report_path = OUT / "l2_consistency_report.json"
    summary_path = OUT / "l2_consistency_summary.csv"
    markdown_path = OUT / "l2_consistency_summary.md"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(summary_path, report)
    write_markdown(markdown_path, report)
    update_pim_manifest(report_path, summary_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    report = build_report()
    print(json.dumps({
        "overall_status": report["overall_status"],
        "claim_level": report["claim_level"],
        "checks": {name: check["status"] for name, check in report["checks"].items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
