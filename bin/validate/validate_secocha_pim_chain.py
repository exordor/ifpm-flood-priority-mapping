#!/usr/bin/env python3
"""Validate Secocha grid compatibility, coverage, values, and evidence sampling."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/secocha_pim_chain"
REF = BASE / "terrain_preprocessing/secocha_dem_utm18s_30m.tif"
PIM = BASE / "priority_scenarios/scenarios/priority_secocha_direct_pim.tif"
CRITERIA = BASE / "priority_scenarios/pim_criteria"
OUT = BASE / "quality_assurance/chain_validation.json"
OLD_ROOT = ROOT / "outputs/peru_former_pim_chain"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    paths = [PIM, *sorted(CRITERIA.glob("*.tif"))]
    with rasterio.open(REF) as ref:
        contract = (ref.crs, ref.transform, ref.width, ref.height, ref.nodata)
        cell_area_km2 = abs(ref.transform.a * ref.transform.e) / 1e6
    raster_checks = []
    for path in paths:
        with rasterio.open(path) as src:
            arr = src.read(1).astype("float64")
            valid = np.isfinite(arr) & (arr != src.nodata)
            values = arr[valid]
            same = (src.crs, src.transform, src.width, src.height, src.nodata) == contract
        raster_checks.append({
            "path": str(path.relative_to(ROOT)), "grid_compatible": same,
            "valid_fraction": float(valid.mean()), "min": float(values.min()),
            "max": float(values.max()), "mean": float(values.mean()),
            "within_0_1": bool(values.min() >= 0 and values.max() <= 1.000001),
        })

    with rasterio.open(PIM) as src:
        pim = src.read(1).astype("float64")
        valid = np.isfinite(pim) & (pim != src.nodata)
        classes = {}
        for label, low, high in [("very_low", 0, .2), ("low", .2, .4), ("moderate", .4, .6),
                                 ("high", .6, .8), ("very_high", .8, 1.000001)]:
            count = int((valid & (pim >= low) & (pim < high)).sum())
            classes[label] = {"cells": count, "area_km2": count * cell_area_km2,
                              "fraction_of_valid": count / int(valid.sum())}

        samples = []
        for source_name, path in [
            ("INGEMMET A7367 field anchor", ROOT / "outputs/secocha_2023_validation/ingemmet_field_anchors.geojson"),
            ("INDECI response location", ROOT / "outputs/secocha_2023_validation/indeci_response_locations.geojson"),
            ("INGEMMET mining record", ROOT / "data/raw/ingemmet_catastro_minero_secocha/secocha_pequena_mineria.gpkg"),
        ]:
            points = gpd.read_file(path).to_crs(src.crs)
            for index, geom in enumerate(points.geometry):
                if geom is None or geom.is_empty:
                    continue
                value = next(src.sample([(geom.x, geom.y)]))[0]
                inside = bool(np.isfinite(value) and value != src.nodata)
                samples.append({"source": source_name, "feature_index": index, "inside_active_grid": inside,
                                "priority_score": float(value) if inside else None})

    freeze = json.loads((OLD_ROOT / "FROZEN_BASELINE.json").read_text(encoding="utf-8"))
    frozen_checks = []
    for item in freeze.get("key_artifacts", {}).values():
        path = ROOT / item["path"]
        frozen_checks.append({"path": item["path"], "exists": path.exists(),
                              "sha256_matches": path.exists() and sha256(path) == item["sha256"]})

    report = {
        "boundary_id": "secocha_reference_extent",
        "experiment_id": "supervisor_full_spec_v07_secocha",
        "claim_level": "provisional", "weights_changed": False,
        "reference_grid": {"crs": str(contract[0]), "width": contract[2], "height": contract[3],
                           "resolution_m": 30, "cell_area_km2": cell_area_km2},
        "raster_checks": raster_checks, "priority_classes": classes,
        "evidence_samples": samples, "frozen_previous_area_checks": frozen_checks,
        "status": "pass" if all(x["grid_compatible"] and x["within_0_1"] for x in raster_checks)
                 and all(x["sha256_matches"] for x in frozen_checks) else "fail",
        "interpretation_limit": "Point samples test spatial co-location only; they do not constitute event-footprint validation.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
