"""Secocha chain validation: grid compatibility, value range, classes and evidence sampling.

Ported from bin/validate/validate_secocha_pim_chain.py. Writes
<chain>/quality_assurance/chain_validation.json in the run's output root and stops with
exit code 1 when a check fails.
"""

from __future__ import annotations

import json

import numpy as np
import rasterio

from .io import sha256_file
from .scoring import class_table


def validate_secocha(ctx) -> dict:
    import geopandas as gpd
    cfg = ctx.cfg
    p = ctx.p
    pim_path = p["SCENARIO_DIR"] / "scenarios" / cfg["priority_filename"]
    paths = [pim_path, *sorted((p["SCENARIO_DIR"] / "pim_criteria").glob("*.tif"))]
    with rasterio.open(p["DEM"]) as ref:
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
            "path": ctx.rel(path), "grid_compatible": same,
            "valid_fraction": float(valid.mean()), "min": float(values.min()),
            "max": float(values.max()), "mean": float(values.mean()),
            "within_0_1": bool(values.min() >= 0 and values.max() <= 1.000001),
        })

    with rasterio.open(pim_path) as src:
        pim = src.read(1).astype("float64")
        valid = np.isfinite(pim) & (pim != src.nodata)
        classes = class_table(pim, valid, cell_area_km2)
        samples = []
        # Point samples of the event evidence (spatial co-location only).
        for source_name, dataset in cfg["validation"]["evidence"]:
            points = gpd.read_file(cfg.path(dataset)).to_crs(src.crs)
            for index, geom in enumerate(points.geometry):
                if geom is None or geom.is_empty:
                    continue
                value = next(src.sample([(geom.x, geom.y)]))[0]
                inside = bool(np.isfinite(value) and value != src.nodata)
                samples.append({"source": source_name, "feature_index": index, "inside_active_grid": inside,
                                "priority_score": float(value) if inside else None})

    # The frozen former-Peru baseline must be untouched.
    freeze = json.loads(cfg.path(cfg["validation"]["frozen_baseline"]).read_text(encoding="utf-8"))
    frozen_checks = []
    for item in freeze.get("key_artifacts", {}).values():
        path = cfg.root / item["path"]
        frozen_checks.append({"path": item["path"], "exists": path.exists(),
                              "sha256_matches": path.exists() and sha256_file(path) == item["sha256"]})

    report = {
        "boundary_id": ctx.focus_area_id,
        "experiment_id": cfg["validation"]["experiment_id"],
        "claim_level": "provisional", "weights_changed": False,
        "reference_grid": {"crs": str(contract[0]), "width": contract[2], "height": contract[3],
                           "resolution_m": 30, "cell_area_km2": cell_area_km2},
        "raster_checks": raster_checks, "priority_classes": classes,
        "evidence_samples": samples, "frozen_previous_area_checks": frozen_checks,
        "status": "pass" if all(x["grid_compatible"] and x["within_0_1"] for x in raster_checks)
                 and all(x["sha256_matches"] for x in frozen_checks) else "fail",
        "interpretation_limit": "Point samples test spatial co-location only; they do not constitute event-footprint validation.",
    }
    out = p["OUT_BASE"] / "quality_assurance/chain_validation.json"
    ctx.write_text(out, json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)
    return report
