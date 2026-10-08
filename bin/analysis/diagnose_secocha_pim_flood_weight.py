#!/usr/bin/env python3
"""Check whether Secocha flood scores, other criteria, or class cutoffs drive PIM gaps."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios"
MANIFEST = BASE / "run_manifest.json"
EVENT = ROOT / "outputs/secocha_2023_validation/observed_hazard/secocha_2023_map7_event_digitization.gpkg"
EVENT_MANIFEST = EVENT.parent / "digitization_manifest.json"
OUT = ROOT / "outputs/peru_secocha_a7367_reference_extent_v1/pim_flood_weight_diagnostic"
NAMES = ("flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic")
THRESHOLD = 0.6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_raster(record: dict, reference: dict | None = None) -> tuple[np.ndarray, dict]:
    path = ROOT / record["path"]
    if sha256(path) != record["sha256"]:
        raise ValueError(f"Raster differs from run manifest: {path}")
    with rasterio.open(path) as src:
        grid = {"crs": str(src.crs), "transform": tuple(src.transform), "shape": src.shape}
        if reference is not None and grid != reference:
            raise ValueError(f"Grid mismatch: {path}")
        data = src.read(1, masked=True).filled(np.nan).astype("float64")
    return data, grid


def stats(values: np.ndarray, mask: np.ndarray) -> dict:
    sample = values[mask]
    return {
        "cells": int(sample.size),
        "mean": float(np.mean(sample)) if sample.size else None,
        "median": float(np.median(sample)) if sample.size else None,
        "share_ge_0_6": float(np.mean(sample >= THRESHOLD)) if sample.size else None,
    }


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["boundary_id"] != "peru_secocha_a7367_reference_extent_v1":
        raise ValueError("Unexpected boundary")
    if manifest.get("claim_level") != "provisional":
        raise ValueError("Unexpected claim level")
    weights = manifest["main_weights"]
    if abs(sum(weights.values()) - 1) > 1e-9:
        raise ValueError("Main weights do not sum to one")
    pim, grid = inspect_raster(manifest["priority_raster_lineage"])
    criteria = {name: inspect_raster(manifest["criterion_raster_lineage"][name], grid)[0] for name in NAMES}
    support = np.isfinite(pim)
    for arr in criteria.values():
        support &= np.isfinite(arr)
    if not support.any():
        raise ValueError("No common valid cells")
    reconstructed = sum(weights[name] * criteria[name] for name in NAMES)
    max_error = float(np.max(np.abs(reconstructed[support] - pim[support])))
    if max_error > 2e-5:
        raise ValueError(f"PIM reconstruction failed: max error {max_error}")
    if np.any(np.isfinite(pim) & ~support):
        raise ValueError("PIM has cells outside five-criterion common support")

    if not EVENT.exists():
        raise FileNotFoundError(EVENT)
    event_manifest = json.loads(EVENT_MANIFEST.read_text(encoding="utf-8"))
    event_record = next((item for item in event_manifest["outputs"] if item["path"] == str(EVENT.relative_to(ROOT))), None)
    if event_record is None or event_record["sha256"] != sha256(EVENT):
        raise ValueError("Event geometry differs from digitization manifest")
    if event_manifest["pim_raster_sha256"] != manifest["priority_raster_lineage"]["sha256"]:
        raise ValueError("Event digitization and PIM run reference different rasters")
    event = gpd.read_file(EVENT, layer="event_footprint_candidate")
    if event.empty or event.crs is None:
        raise ValueError("Missing candidate event geometry or CRS")
    event = event.to_crs(grid["crs"])
    def event_mask(geometries, all_touched: bool = False) -> np.ndarray:
        shapes = [(geom, 1) for geom in geometries if geom is not None and not geom.is_empty]
        if not shapes:
            return np.zeros(grid["shape"], dtype=bool)
        return rasterize(
            shapes, out_shape=grid["shape"], transform=rasterio.Affine(*grid["transform"][:6]),
            fill=0, dtype="uint8", all_touched=all_touched,
        ).astype(bool)

    event_grid = event_mask(event.geometry)
    if not event_grid.any():
        raise ValueError("Event candidate misses the PIM grid")
    inside = support & event_grid
    outside = support & ~event_grid
    if not inside.any() or not outside.any():
        raise ValueError("Insufficient event or outside support")

    flood = criteria["flood_hazard"]
    other = sum(weights[name] * criteria[name] for name in NAMES[1:]) / (1 - weights["flood_hazard"])
    rows = []
    for name, array in [("flood_hazard", flood), ("other_criteria_weighted_mean", other),
                        *[(name, criteria[name]) for name in NAMES[1:]], ("pim", pim)]:
        for region, mask in (("event_candidate", inside), ("outside_on_common_support", outside)):
            rows.append({"quantity": name, "region": region, **stats(array, mask)})

    scenarios = []
    for flood_weight in (0.34, 0.50, 0.70, 1.00):
        score = pim if abs(flood_weight - weights["flood_hazard"]) < 1e-12 else flood_weight * flood + (1 - flood_weight) * other
        scenarios.append({
            "flood_weight": flood_weight,
            "event": stats(score, inside),
            "outside": stats(score, outside),
            "event_minus_outside_mean": float(np.mean(score[inside]) - np.mean(score[outside])),
        })
    q80_flood = float(np.quantile(flood[support], 0.8))
    q80_pim = float(np.quantile(pim[support], 0.8))
    joint = {
        "flood_ge_0_6_pim_lt_0_6_event_cells": int(np.sum(inside & (flood >= THRESHOLD) & (pim < THRESHOLD))),
        "flood_lt_0_6_pim_ge_0_6_event_cells": int(np.sum(inside & (flood < THRESHOLD) & (pim >= THRESHOLD))),
        "flood_ge_0_6_event_share": float(np.mean(flood[inside] >= THRESHOLD)),
        "pim_ge_0_6_event_share": float(np.mean(pim[inside] >= THRESHOLD)),
        "flood_top_20pct_event_share": float(np.mean(flood[inside] >= q80_flood)),
        "pim_top_20pct_event_share": float(np.mean(pim[inside] >= q80_pim)),
        "flood_top_20pct_outside_share": float(np.mean(flood[outside] >= q80_flood)),
        "pim_top_20pct_outside_share": float(np.mean(pim[outside] >= q80_pim)),
        "flood_at_or_above_q80_full_support_share": float(np.mean(flood[support] >= q80_flood)),
        "pim_at_or_above_q80_full_support_share": float(np.mean(pim[support] >= q80_pim)),
    }
    event_coverage_by_layer = {name: {
        "valid_cells": int(np.sum(event_grid & np.isfinite(array))),
        "valid_fraction": float(np.mean(np.isfinite(array[event_grid]))),
    } for name, array in (("pim", pim), *criteria.items())}
    event_flood_all_valid = event_grid & np.isfinite(flood)
    event_flood_excluded_from_pim = event_flood_all_valid & ~support
    geometry_sensitivity = []
    for label, geometries, all_touched in (
        ("default_pixel_center", event.geometry, False),
        ("candidate_inset_10m", event.geometry.buffer(-10), False),
        ("candidate_outset_10m", event.geometry.buffer(10), False),
        ("default_all_touched", event.geometry, True),
    ):
        selected = event_mask(geometries, all_touched=all_touched)
        selected_valid = selected & support
        geometry_sensitivity.append({
            "mask_rule": label,
            "event_grid_cells": int(selected.sum()),
            "common_valid_cells": int(selected_valid.sum()),
            "common_valid_fraction": float(selected_valid.sum() / selected.sum()) if selected.any() else None,
            "flood_on_common_support": stats(flood, selected_valid),
            "pim_on_common_support": stats(pim, selected_valid),
        })
    report = {
        "boundary_id": manifest["boundary_id"],
        "experiment_id": manifest["experiment_id"],
        "claim_level": "diagnostic_only",
        "reference": "Semi-automatically digitized 2023-02-05 huaico/mudflow classes from INGEMMET A7367 Map 7; candidate, not confirmed inundation truth",
        "input_hashes": {"run_manifest": sha256(MANIFEST), "event_digitization_manifest": sha256(EVENT_MANIFEST),
                         "event_candidate_gpkg": sha256(EVENT)},
        "weights": weights,
        "common_valid_cells": int(support.sum()),
        "event_grid_cells": int(event_grid.sum()),
        "event_valid_cells": int(inside.sum()),
        "event_coverage_fraction": float(inside.sum() / event_grid.sum()),
        "event_coverage_by_layer": event_coverage_by_layer,
        "flood_score_for_event_cells": {
            "all_flood_valid": stats(flood, event_flood_all_valid),
            "retained_by_pim": stats(flood, inside),
            "excluded_from_pim": stats(flood, event_flood_excluded_from_pim),
        },
        "geometry_sensitivity": geometry_sensitivity,
        "pim_reconstruction_max_abs_error": max_error,
        "event_vs_outside": rows,
        "threshold_diagnostic": joint,
        "weight_sensitivity_fixed_inputs": scenarios,
        "limits": [
            "Weights changed only for sensitivity; the criteria, normalization and support are frozen.",
            "0.6 and the top-20% cut are descriptive classifications, not calibrated flood thresholds.",
            "Event candidate depicts a huaico/mudflow report-map interpretation; it is not a general flood validation sample.",
            "Event comparisons use only cells with all five criteria valid; missing cells may bias the contrast.",
            "The PDF-map candidate has estimated 10 m registration uncertainty; 10 m geometry perturbations and all-touched rasterization test edge sensitivity, not an uncertainty probability model.",
            "Outside cells are not verified negatives; this comparison cannot establish predictive accuracy.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diagnostic.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (OUT / "criterion_comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("quantity", "region", "cells", "mean", "median", "share_ge_0_6"))
        writer.writeheader()
        writer.writerows(rows)
    with (OUT / "weight_sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("flood_weight", "region", "cells", "mean", "median", "share_ge_0_6"))
        writer.writeheader()
        for scenario in scenarios:
            for region in ("event", "outside"):
                writer.writerow({"flood_weight": scenario["flood_weight"], "region": region, **scenario[region]})
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "event_valid_cells": int(inside.sum()),
                      "max_reconstruction_error": max_error, "scenarios": scenarios}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
