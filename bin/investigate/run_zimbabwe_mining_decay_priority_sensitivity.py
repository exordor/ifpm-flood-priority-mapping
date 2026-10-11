#!/usr/bin/env python3
"""Run V1 implementation-layer priority under each mining decay variant.

Isolates the effect of the mining-criterion decay function on the priority
output. Loads the same five non-mining scored layers as rainfall_exposure,
swaps in each of the three mining decay rasters (tiered_linear, linear_3km,
gaussian_1km), runs the same three weight scenarios, and records top-20%
priority-area stability + dominant-driver share for each.

Writes to an isolated directory; does NOT touch the default v0.4 outputs.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "outputs/zimbabwe_pim_scenarios"
OUT_DIR = ROOT / "outputs/zimbabwe_pim_scenarios/mining_decay_priority_sensitivity"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Same five non-mining scored layers as rainfall_exposure.
NON_MINING = {
    "flood_conditioning_factors": V1 / "criteria_stack/criteria/flood_conditioning_factors_0_1.tif",
    "soil_erosion_factors": V1 / "criteria_stack/criteria/soil_erosion_factors_0_1.tif",
    "land_cover_pressure": V1 / "criteria_stack/criteria/land_cover_pressure_0_1.tif",
    "exposure_indicators": V1 / "criteria_stack/criteria/exposure_indicators_0_1.tif",
    "rainfall_climatology": V1 / "rainfall_sensitivity/criteria/rainfall_climatology_0_1_PROVISIONAL_30m.tif",
}
MINING_VARIANTS = {
    "tiered_linear": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_mining_activity_indicator_0_1_utm35s_30m.tif",
    "linear_3km": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_mining_linear_3km_0_1_utm35s_30m.tif",
    "gaussian_1km": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_mining_gaussian_1km_0_1_utm35s_30m.tif",
}
SCENARIOS = {
    "equal_scored_layers": None,  # filled per-variant as 1/6 each
    "rainfall_exposure_balanced": {
        "flood_conditioning_factors": 0.20, "soil_erosion_factors": 0.20,
        "land_cover_pressure": 0.15, "mining_pressure": 0.15,
        "exposure_indicators": 0.15, "rainfall_climatology": 0.15,
    },
    "flood_erosion_rainfall_heavy": {
        "flood_conditioning_factors": 0.30, "soil_erosion_factors": 0.25,
        "land_cover_pressure": 0.05, "mining_pressure": 0.10,
        "exposure_indicators": 0.05, "rainfall_climatology": 0.25,
    },
}
PIXEL_AREA_KM2 = 0.03 * 0.03  # 30m pixel = 0.0009 km2


def read_band(path: Path, profile: dict) -> np.ndarray:
    with rasterio.open(path) as src:
        if src.crs != profile["crs"] or src.transform != profile["transform"]:
            raise ValueError(f"grid mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def normalize(data: np.ndarray) -> np.ndarray:
    v = data[np.isfinite(data)]
    if v.size == 0:
        raise ValueError("empty")
    if v.max() <= 1.000001 and v.min() >= -0.000001:
        return np.clip(data, 0.0, 1.0).astype("float32")
    return np.clip(data / v.max(), 0.0, 1.0).astype("float32")


def load_reference_profile() -> dict:
    with rasterio.open(NON_MINING["flood_conditioning_factors"]) as src:
        return src.profile.copy()


def run_variant(mining_raster: np.ndarray, criteria: dict, profile: dict) -> dict:
    criteria = {**criteria, "mining_pressure": normalize(mining_raster)}
    names = list(criteria)
    scenario_scores = {}
    top20_masks = []
    for sc, weights in SCENARIOS.items():
        w = weights if weights else {n: 1/6 for n in names}
        num = np.zeros(mining_raster.shape, dtype="float32")
        den = np.zeros(mining_raster.shape, dtype="float32")
        for n in names:
            layer = criteria[n]
            valid = np.isfinite(layer)
            num[valid] += layer[valid] * w[n]
            den[valid] += w[n]
        score = np.full_like(num, np.nan, dtype="float32")
        ok = den > 0
        score[ok] = num[ok] / den[ok]
        scenario_scores[sc] = score
        vals = score[np.isfinite(score)]
        thr = float(np.percentile(vals, 80))
        top20_masks.append(score >= thr)

    stack = np.stack(list(scenario_scores.values()))
    # Dominant driver: use the criteria-stack validity mask (a pixel is valid for
    # dominance only if ALL criteria are finite), matching the board scripts.
    # argmax over contributions containing NaN mis-allocates to the NaN position,
    # so mask NaN contributions to -inf and use nanargmax.
    crit_stack = np.stack([criteria[n] for n in names])
    valid = np.all(np.isfinite(crit_stack), axis=0)
    equal_w = {n: 1/6 for n in names}
    mean_w = {n: float(np.mean([ (s or equal_w)[n] for s in SCENARIOS.values()])) for n in names}
    contribs = crit_stack * np.array([mean_w[n] for n in names])[:, None, None]
    winner = np.nanargmax(np.where(valid[None], contribs, -np.inf), axis=0)

    all_mask = np.all(np.stack(top20_masks), axis=0)
    any_mask = np.any(np.stack(top20_masks), axis=0)
    dom = {names[i]: round(float((winner[valid] == i).mean()), 4) for i in range(len(names))}
    return {
        "stable_area_km2": round(float(all_mask.sum() * PIXEL_AREA_KM2), 3),
        "any_area_km2": round(float(any_mask.sum() * PIXEL_AREA_KM2), 3),
        "priority_mean": round(float(np.nanmean(stack)), 4),
        "dominant_rainfall": dom.get("rainfall_climatology", 0),
        "dominant_flood": dom.get("flood_conditioning_factors", 0),
        "dominant_sediment": dom.get("soil_erosion_factors", 0),
        "dominant_land_cover": dom.get("land_cover_pressure", 0),
        "dominant_mining": dom.get("mining_pressure", 0),
        "dominant_exposure": dom.get("exposure_indicators", 0),
    }


def main() -> None:
    profile = load_reference_profile()
    print(f"reference grid: {profile['width']}x{profile['height']}")
    criteria = {n: normalize(read_band(p, profile)) for n, p in NON_MINING.items()}

    rows = []
    for variant, path in MINING_VARIANTS.items():
        mining = read_band(path, profile)
        res = run_variant(mining, criteria, profile)
        res["mining_variant"] = variant
        rows.append(res)
        print(f"\n{variant}:")
        for k, v in res.items():
            if k != "mining_variant":
                print(f"  {k}: {v}")

    fields = ["mining_variant", "stable_area_km2", "any_area_km2",
              "priority_mean", "dominant_rainfall", "dominant_flood",
              "dominant_sediment", "dominant_land_cover",
              "dominant_mining", "dominant_exposure"]
    with (OUT_DIR / "decay_priority_comparison.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT_DIR / 'decay_priority_comparison.csv'}")


if __name__ == "__main__":
    main()
