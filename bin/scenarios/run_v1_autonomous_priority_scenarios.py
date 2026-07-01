#!/usr/bin/env python3
"""Run provisional V1 autonomous priority scenarios and hotspot stability."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_autonomous_prototype_v0_1"
CRITERIA_DIR = OUT_DIR / "criteria"
SCENARIO_DIR = OUT_DIR / "scenarios"
REF = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"

CRITERIA = [
    "flood_hydrology",
    "sediment_structure",
    "landuse_asm_pressure",
    "environmental_sensitivity",
    "socioeconomic_exposure",
]

SLIDE_MATRIX = np.array(
    [
        [1, 3, 5, 4, 6],
        [1 / 3, 1, 3, 2, 4],
        [1 / 5, 1 / 3, 1, 1 / 2, 2],
        [1 / 4, 1 / 2, 2, 1, 3],
        [1 / 6, 1 / 4, 1 / 2, 1 / 3, 1],
    ],
    dtype="float64",
)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_reference() -> dict:
    with rasterio.open(REF) as ref:
        return ref.profile.copy()


def read_band(path: Path, profile: dict) -> np.ndarray:
    with rasterio.open(path) as src:
        if src.crs != profile["crs"] or src.transform != profile["transform"]:
            raise ValueError(f"grid mismatch: {path}")
        if src.width != profile["width"] or src.height != profile["height"]:
            raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def write_raster(path: Path, data: np.ndarray, profile: dict, dtype: str = "float32", nodata: float | int = -9999.0) -> None:
    out_profile = profile.copy()
    out_profile.update(driver="GTiff", count=1, dtype=dtype, nodata=nodata, compress="deflate", tiled=True)
    encoded = np.where(np.isfinite(data), data, nodata).astype(dtype)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(encoded, 1)


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


def ahp_weights() -> tuple[dict[str, float], float]:
    vals, vecs = np.linalg.eig(SLIDE_MATRIX)
    idx = int(np.argmax(vals.real))
    lam = float(vals.real[idx])
    weights = np.abs(vecs[:, idx].real)
    weights = weights / weights.sum()
    ci = (lam - len(CRITERIA)) / (len(CRITERIA) - 1)
    cr = ci / 1.12
    return {criterion: float(weight) for criterion, weight in zip(CRITERIA, weights, strict=True)}, float(cr)


def scenario_weights() -> tuple[dict[str, dict[str, float]], float]:
    slide, cr = ahp_weights()
    return (
        {
            "equal": dict.fromkeys(CRITERIA, 0.20),
            "methodology_slide_candidate": slide,
            "flood_sediment_heavy": {
                "flood_hydrology": 0.35,
                "sediment_structure": 0.30,
                "landuse_asm_pressure": 0.15,
                "environmental_sensitivity": 0.10,
                "socioeconomic_exposure": 0.10,
            },
            "exposure_heavy": {
                "flood_hydrology": 0.25,
                "sediment_structure": 0.20,
                "landuse_asm_pressure": 0.15,
                "environmental_sensitivity": 0.10,
                "socioeconomic_exposure": 0.30,
            },
        },
        cr,
    )


def classify_quantiles(data: np.ndarray) -> np.ndarray:
    vals = data[np.isfinite(data)]
    breaks = np.nanpercentile(vals, [20, 40, 60, 80])
    classes = np.digitize(data, breaks, right=True).astype("float32") + 1
    classes[~np.isfinite(data)] = np.nan
    return classes


def raster_stats(data: np.ndarray) -> dict[str, object]:
    vals = data[np.isfinite(data)]
    return {
        "valid_cells": int(vals.size),
        "min": round(float(vals.min()), 6),
        "mean": round(float(vals.mean()), 6),
        "p50": round(float(np.percentile(vals, 50)), 6),
        "p80": round(float(np.percentile(vals, 80)), 6),
        "p95": round(float(np.percentile(vals, 95)), 6),
        "max": round(float(vals.max()), 6),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()
    criteria = {
        name: read_band(CRITERIA_DIR / f"{name}_0_1.tif", profile)
        for name in CRITERIA
    }
    valid_mask = np.logical_and.reduce([np.isfinite(arr) for arr in criteria.values()])
    scenarios, ahp_cr = scenario_weights()

    weight_rows = []
    scenario_arrays = {}
    summary_rows = []
    top20_masks = []
    for scenario, weights in scenarios.items():
        total = round(sum(weights.values()), 10)
        if total != 1.0:
            raise ValueError(f"weights for {scenario} sum to {total}")
        score = np.zeros(profile["height"] * profile["width"], dtype="float32").reshape(profile["height"], profile["width"])
        for criterion, weight in weights.items():
            score += criteria[criterion] * weight
            weight_rows.append({"scenario": scenario, "criterion": criterion, "weight": round(weight, 8)})
        score[~valid_mask] = np.nan
        score = np.clip(score, 0.0, 1.0).astype("float32")
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}_0_1.tif", score, profile)
        write_raster(SCENARIO_DIR / f"priority_{scenario}_class_1_5.tif", classify_quantiles(score), profile, dtype="uint8", nodata=0)
        threshold = float(np.nanpercentile(score, 80))
        top20 = score >= threshold
        top20_masks.append(top20)
        summary_rows.append({"scenario": scenario, "top20_threshold": round(threshold, 6), **raster_stats(score)})

    stack = np.stack(list(scenario_arrays.values())).astype("float32")
    priority_mean = np.full_like(stack[0], np.nan, dtype="float32")
    priority_std = np.full_like(stack[0], np.nan, dtype="float32")
    priority_mean[valid_mask] = np.mean(stack[:, valid_mask], axis=0)
    priority_std[valid_mask] = np.std(stack[:, valid_mask], axis=0)
    top20_frequency = np.mean(np.stack(top20_masks), axis=0).astype("float32")
    priority_mean[~valid_mask] = np.nan
    priority_std[~valid_mask] = np.nan
    top20_frequency[~valid_mask] = np.nan

    write_raster(OUT_DIR / "priority_mean_0_1.tif", priority_mean, profile)
    write_raster(OUT_DIR / "priority_std_0_1.tif", priority_std, profile)
    write_raster(OUT_DIR / "top20_frequency_0_1.tif", top20_frequency, profile)

    stability_rows = [
        {"metric": "scenario_count", "value": len(scenarios)},
        {"metric": "ahp_candidate_consistency_ratio", "value": round(ahp_cr, 6)},
        {"metric": "top20_all_scenarios_cells", "value": int(np.nansum(top20_frequency == 1.0))},
        {"metric": "top20_any_scenario_cells", "value": int(np.nansum(top20_frequency > 0.0))},
        {"metric": "top20_all_scenarios_area_km2", "value": round(float(np.nansum(top20_frequency == 1.0) * 0.0009), 3)},
        {"metric": "top20_any_scenario_area_km2", "value": round(float(np.nansum(top20_frequency > 0.0) * 0.0009), 3)},
        {"metric": "priority_std_mean", "value": round(float(np.nanmean(priority_std)), 6)},
        {"metric": "priority_std_p95", "value": round(float(np.nanpercentile(priority_std, 95)), 6)},
    ]
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "hotspot_stability_summary.csv", stability_rows)
    write_handoff(scenarios, ahp_cr)
    print(f"wrote {len(scenarios)} priority scenarios to {rel(SCENARIO_DIR)}")


def write_handoff(scenarios: dict[str, dict[str, float]], ahp_cr: float) -> None:
    names = ", ".join(scenarios)
    handoff = f"""# V1 Autonomous Prototype v0.1 Handoff

Status: provisional autonomous scoring complete.

This package is not a final flood-risk map, intervention-priority map, or final thesis boundary
claim. It is a sensitivity prototype over the V1 working boundary.

## What was scored

Five grid-compatible 30 m criteria were combined:

- flood/hydrology: TWI high-wetness plus drainage proximity
- sediment structure: safe R-invariant `K x LS x C` structure
- land use / ASM pressure: C-factor pressure plus mining-proxy proximity
- environmental sensitivity: river/water proximity proxy
- socioeconomic exposure: road/access proximity proxy

## Scenario weights

Scenarios: {names}.

The methodology-slide candidate weights are computed from the mentor slide pairwise matrix.
The candidate matrix consistency ratio is `{ahp_cr:.4f}`. The matrix is still treated as an
example/candidate, not a final accepted AHP weight source.

## Rainfall and R handling

Rainfall/R is not inserted as a 30 m pixel-level layer in v0.1. R remains an uncertainty module.
The safe sediment layer is spatial structure only; scalar R changes magnitude, not hotspot rank.

## Review question

Do the stable top-20% hotspots make hydrological and land-use sense under the stated assumptions?
"""
    (OUT_DIR / "v1_autonomous_prototype_handoff.md").write_text(handoff, encoding="utf-8")
    prompt = """Review this IFPM V1 autonomous prototype as a critical hydrology/GIS reviewer.

Inputs:
- V1 is a prototype-only HydroBASINS-derived working boundary.
- Outputs are in outputs/v1_autonomous_prototype_v0_1/.
- The prototype uses five 30 m grid-compatible criteria and four weight scenarios.
- Rainfall/R is an uncertainty module, not a 30 m pixel-level accepted layer.

Please judge:
1. Are the criteria defensible as a provisional research prototype?
2. Which criterion is weakest and why?
3. Does top20_frequency provide a reasonable hotspot-stability diagnostic?
4. What would be the highest-priority correction before showing this as thesis evidence?
"""
    (OUT_DIR / "gpt_pro_review_prompt.md").write_text(prompt, encoding="utf-8")


if __name__ == "__main__":
    main()
