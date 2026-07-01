#!/usr/bin/env python3
"""Run boundary_v1 six-criteria rainfall + exposure priority scenarios.

This experiment makes the Zimbabwe output comparable to the current Peru PE1
six-criteria pilot: flood, sediment/erosion structure, land cover, mining,
exposure/access, and rainfall. It reuses existing rasters only.
"""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.axes_grid1 import make_axes_locatable


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "rainfall_exposure_v0_4"
OUT_DIR = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"

REF = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
CRITERIA_DIR = ROOT / "outputs/boundary_v1/criteria_stack_v0_2/criteria"
SEDIMENT_DIR = ROOT / "outputs/boundary_v1/sediment_r_factor_scenarios"
RAINFALL_DIR = ROOT / "outputs/boundary_v1/rainfall_sensitivity_v0_3/criteria"

CRITERIA_PATHS = {
    "flood_hazard_proxy": CRITERIA_DIR / "flood_hazard_proxy_0_1.tif",
    "sediment_risk_lowR_provisional": SEDIMENT_DIR / "sediment_risk_lowR_provisional_30m.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "mining_pressure": CRITERIA_DIR / "mining_pressure_0_1.tif",
    "road_accessibility_proxy": CRITERIA_DIR / "road_accessibility_proxy_0_1.tif",
    "rainfall_climatology_proxy": RAINFALL_DIR / "rainfall_climatology_proxy_0_1_PROVISIONAL_30m.tif",
}

CELL_AREA_KM2 = 0.0009
CLAIM_NOTE = (
    "SENSITIVITY SCENARIO: boundary_v1 six-criteria prototype overlay. "
    "Uses rainfall and exposure/access proxies. Not a validated flood-risk or "
    "intervention-priority map."
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


def read_reference() -> dict:
    with rasterio.open(REF) as ref:
        return ref.profile.copy()


def read_band(path: Path, profile: dict) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
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


def normalize_if_needed(data: np.ndarray) -> np.ndarray:
    values = data[np.isfinite(data)]
    if values.size == 0:
        raise ValueError("empty criterion")
    if float(values.max()) <= 1.000001 and float(values.min()) >= -0.000001:
        return np.clip(data, 0.0, 1.0).astype("float32")
    max_value = float(values.max())
    if max_value <= 0:
        raise ValueError("non-positive criterion range")
    return np.clip(data / max_value, 0.0, 1.0).astype("float32")


def write_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    out_profile = profile.copy()
    out_profile.update(
        driver="GTiff",
        count=1,
        dtype="float32",
        nodata=-9999.0,
        compress="deflate",
        tiled=True,
    )
    encoded = np.where(np.isfinite(data), data, -9999.0).astype("float32")
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(encoded, 1)
        dst.update_tags(1, IFPM_NOTE=CLAIM_NOTE)


def scenario_weights() -> dict[str, dict[str, float]]:
    return {
        "equal_6": {name: 1 / 6 for name in CRITERIA_PATHS},
        "rainfall_exposure_balanced": {
            "flood_hazard_proxy": 0.20,
            "sediment_risk_lowR_provisional": 0.20,
            "land_cover_pressure": 0.15,
            "mining_pressure": 0.15,
            "road_accessibility_proxy": 0.15,
            "rainfall_climatology_proxy": 0.15,
        },
        "flood_erosion_rainfall_heavy": {
            "flood_hazard_proxy": 0.30,
            "sediment_risk_lowR_provisional": 0.25,
            "land_cover_pressure": 0.05,
            "mining_pressure": 0.10,
            "road_accessibility_proxy": 0.05,
            "rainfall_climatology_proxy": 0.25,
        },
    }


def raster_stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "p50": round(float(np.percentile(values, 50)), 6),
        "p80": round(float(np.percentile(values, 80)), 6),
        "p95": round(float(np.percentile(values, 95)), 6),
        "max": round(float(values.max()), 6),
    }


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.08)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=8)
    cb.set_label(label, fontsize=9)


def plot_board(priority_mean: np.ndarray, top20_frequency: np.ndarray, profile: dict) -> None:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0], bounds[2], bounds[1], bounds[3])

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2), constrained_layout=True)
    panels = [
        ("A. Mean priority across six-criteria scenarios", priority_mean, "YlOrRd", "0-1 priority"),
        ("B. Top-20% hotspot frequency", top20_frequency, "Blues", "top-20% frequency"),
    ]
    km_formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
    for ax, (title, data, cmap, label) in zip(axes, panels, strict=True):
        image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.8)
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32735)", fontsize=9)
        ax.set_ylabel("Northing (km)", fontsize=9)
        ax.xaxis.set_major_formatter(km_formatter)
        ax.yaxis.set_major_formatter(km_formatter)
        ax.tick_params(labelsize=8)
        ax.grid(color="0.9", linewidth=0.35)
        add_colorbar(fig, ax, image, label)
    fig.suptitle("Zimbabwe Upper Mzingwane: six-criteria prototype scenario", fontsize=13, fontweight="bold")
    fig.savefig(OUT_DIR / "rainfall_exposure_v0_4_board.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "rainfall_exposure_v0_4_board.pdf", bbox_inches="tight")
    plt.close(fig)


def build_grid_check(profile: dict, criteria: dict[str, np.ndarray]) -> list[dict[str, object]]:
    rows = []
    for name, data in criteria.items():
        values = data[np.isfinite(data)]
        rows.append({
            "criterion": name,
            "grid_compatible": True,
            "crs": str(profile["crs"]),
            "width": profile["width"],
            "height": profile["height"],
            "valid_cells": int(values.size),
            "valid_fraction": round(float(values.size / data.size), 6),
            "min": round(float(values.min()), 6),
            "mean": round(float(values.mean()), 6),
            "max": round(float(values.max()), 6),
        })
    return rows


def write_handoff(summary: dict[str, object]) -> None:
    text = f"""# boundary_v1 / rainfall_exposure_v0_4

Date: 2026-06-30

Status: `sensitivity_scenario`.

This run creates a six-criteria Zimbabwe prototype scenario so it can be compared
more cleanly with the current Peru PE1 six-criteria pilot.

## Active criteria

1. flood_hazard_proxy
2. sediment_risk_lowR_provisional
3. land_cover_pressure
4. mining_pressure
5. road_accessibility_proxy
6. rainfall_climatology_proxy

## Headline result

- Stable top-20% hotspot area across all three six-criteria scenarios:
  {summary['stable_area_km2']} km2.
- Top-20% in at least one scenario: {summary['any_area_km2']} km2.

## Limits

- Rainfall is CHIRPS coarse-to-grid context, not native 30 m rainfall.
- Road accessibility is an exposure/access proxy, not observed vulnerability.
- This is not a validated flood-risk map and not an intervention-priority map.
"""
    (OUT_DIR / "handoff.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()
    criteria = {
        name: normalize_if_needed(read_band(path, profile))
        for name, path in CRITERIA_PATHS.items()
    }
    scenarios = scenario_weights()

    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    scenario_arrays: dict[str, np.ndarray] = {}
    top20_masks: list[np.ndarray] = []

    for scenario, weights in scenarios.items():
        if round(sum(weights.values()), 10) != 1.0:
            raise ValueError(f"weights do not sum to 1 for {scenario}")
        numerator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        denominator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        for criterion, weight in weights.items():
            layer = criteria[criterion]
            valid = np.isfinite(layer)
            numerator[valid] += layer[valid] * weight
            denominator[valid] += weight
            weight_rows.append({
                "boundary_id": BOUNDARY_ID,
                "experiment_id": EXPERIMENT_ID,
                "scenario": scenario,
                "criterion": criterion,
                "weight": round(weight, 8),
                "claim_level": "sensitivity_scenario",
            })
        score = np.full_like(numerator, np.nan, dtype="float32")
        valid_score = denominator > 0
        score[valid_score] = numerator[valid_score] / denominator[valid_score]
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}.tif", score, profile)

        values = score[np.isfinite(score)]
        threshold = float(np.percentile(values, 80))
        top20_masks.append(score >= threshold)
        summary_rows.append({
            "boundary_id": BOUNDARY_ID,
            "experiment_id": EXPERIMENT_ID,
            "scenario": scenario,
            "top20_threshold": round(threshold, 6),
            **raster_stats(score),
        })

    stack = np.stack([arr for arr in scenario_arrays.values()])
    stack_valid = np.any(np.isfinite(stack), axis=0)
    priority_mean = np.full(stack.shape[1:], np.nan, dtype="float32")
    priority_std = np.full(stack.shape[1:], np.nan, dtype="float32")
    priority_mean[stack_valid] = np.nanmean(stack[:, stack_valid], axis=0).astype("float32")
    priority_std[stack_valid] = np.nanstd(stack[:, stack_valid], axis=0).astype("float32")
    top20_frequency = np.mean(np.stack(top20_masks).astype("float32"), axis=0)
    top20_frequency[~np.isfinite(priority_mean)] = np.nan

    write_raster(OUT_DIR / "priority_mean.tif", priority_mean, profile)
    write_raster(OUT_DIR / "priority_std.tif", priority_std, profile)
    write_raster(OUT_DIR / "top20_frequency.tif", top20_frequency.astype("float32"), profile)
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "grid_check.csv", build_grid_check(profile, criteria))

    all_mask = np.all(np.stack(top20_masks), axis=0)
    any_mask = np.any(np.stack(top20_masks), axis=0)
    hotspot_summary = {
        "scenario_count": len(scenarios),
        "criteria_count": len(CRITERIA_PATHS),
        "top20_all_scenarios_cells": int(all_mask.sum()),
        "top20_any_scenario_cells": int(any_mask.sum()),
        "stable_area_km2": round(float(all_mask.sum() * CELL_AREA_KM2), 3),
        "any_area_km2": round(float(any_mask.sum() * CELL_AREA_KM2), 3),
        "criteria": ", ".join(CRITERIA_PATHS),
    }
    write_csv(
        OUT_DIR / "hotspot_stability_summary.csv",
        [{"metric": key, "value": value} for key, value in hotspot_summary.items()],
    )
    plot_board(priority_mean, top20_frequency, profile)
    write_handoff(hotspot_summary)
    print(f"Wrote {EXPERIMENT_ID} outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
