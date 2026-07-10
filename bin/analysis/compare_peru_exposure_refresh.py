#!/usr/bin/env python3
"""Compare the Peru mentor PIM before and after the exposure-input refresh."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
COMPARISON_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/comparison"
BEFORE = COMPARISON_DIR / "before_exposure_refresh.tif"
AFTER = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
    "priority_mentor_peru_direct_pim.tif"
)
CSV_OUTPUT = COMPARISON_DIR / "exposure_refresh_comparison.csv"
JSON_OUTPUT = COMPARISON_DIR / "exposure_refresh_comparison_manifest.json"

INPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/comparison/before_exposure_refresh.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
]
OUTPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/comparison/exposure_refresh_comparison.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/comparison/exposure_refresh_comparison_manifest.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compare_arrays(
    before: np.ndarray,
    after: np.ndarray,
    *,
    percentile: float = 80.0,
) -> dict[str, float | int]:
    if before.shape != after.shape:
        raise ValueError("before and after arrays must share one shape")
    valid = np.isfinite(before) & np.isfinite(after)
    if not valid.any():
        raise ValueError("before and after arrays have no common valid cells")

    old = before[valid].astype("float64")
    new = after[valid].astype("float64")
    before_threshold = float(np.percentile(old, percentile))
    after_threshold = float(np.percentile(new, percentile))
    before_top = old >= before_threshold
    after_top = new >= after_threshold
    intersection = int(np.sum(before_top & after_top))
    union = int(np.sum(before_top | after_top))
    rho = float(spearmanr(old, new).statistic)

    return {
        "common_valid_cells": int(valid.sum()),
        "mean_absolute_change": float(np.mean(np.abs(new - old))),
        "mean_signed_change": float(np.mean(new - old)),
        "maximum_absolute_change": float(np.max(np.abs(new - old))),
        "spearman_rank_correlation": rho,
        "before_top_threshold": before_threshold,
        "after_top_threshold": after_threshold,
        "before_top_cells": int(before_top.sum()),
        "after_top_cells": int(after_top.sum()),
        "top_cell_intersection": intersection,
        "top_cell_union": union,
        "top_cell_jaccard": float(intersection / union) if union else float("nan"),
        "top_cell_retention_from_before": (
            float(intersection / before_top.sum()) if before_top.any() else float("nan")
        ),
    }


def read_raster(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        profile = src.profile.copy()
    data[~np.isfinite(data)] = np.nan
    return data, profile


def main() -> None:
    for path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(path)
    before, before_profile = read_raster(BEFORE)
    after, after_profile = read_raster(AFTER)
    for field in ("crs", "transform", "width", "height"):
        if before_profile[field] != after_profile[field]:
            raise ValueError(f"grid mismatch for {field}")

    metrics = compare_arrays(before, after)
    cell_area_km2 = abs(float(after_profile["transform"].a * after_profile["transform"].e)) / 1e6
    metrics["top_cell_intersection_area_km2"] = metrics["top_cell_intersection"] * cell_area_km2
    metrics["before_top_area_km2"] = metrics["before_top_cells"] * cell_area_km2
    metrics["after_top_area_km2"] = metrics["after_top_cells"] * cell_area_km2

    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
        writer.writeheader()
        for metric, value in metrics.items():
            writer.writerow({"metric": metric, "value": value})

    manifest = {
        "status": "sensitivity_scenario",
        "comparison": "mentor Peru PIM before vs after exposure-indicator refresh",
        "before": {"path": str(BEFORE.relative_to(ROOT)), "sha256": sha256(BEFORE)},
        "after": {"path": str(AFTER.relative_to(ROOT)), "sha256": sha256(AFTER)},
        "top_area_definition": "independent highest-priority quintile in each raster",
        "metrics": metrics,
        "claim_boundary": "describes model sensitivity to the exposure-indicator refresh; not validation",
    }
    JSON_OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"mean absolute PIM change: {metrics['mean_absolute_change']:.6f}")
    print(f"Spearman rank correlation: {metrics['spearman_rank_correlation']:.6f}")
    print(f"top-quintile Jaccard overlap: {metrics['top_cell_jaccard']:.6f}")


if __name__ == "__main__":
    main()
