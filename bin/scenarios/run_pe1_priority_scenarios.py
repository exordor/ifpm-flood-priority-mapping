#!/usr/bin/env python3
"""Run priority scenarios for the PE1 engineering-pilot criteria stack (6 criteria).

Mirrors `run_boundary_v1_priority_scenarios.py`. PE1 now has 6 criteria (flood_hazard,
erosion_structure, land_cover, mining, exposure, rainfall), comparable to Zimbabwe 6-criteria
prototype runs. Three scenarios: equal, mentor-slide-mapped, and flood/erosion/rainfall heavy.

Sediment normalization note: the erosion_structure criterion is max-normalized to [0,1] for
MCDA scoring, so its 0-1 value is a relative hotspot intensity, not absolute t/ha/yr. Rank is
R-invariant.

Outputs (gitignored under outputs/srtm_1arcsec_peru_pilot/priority_scenarios/):
priority mean/std/top20-frequency rasters, per-scenario rasters, weights + summary CSVs,
and a board figure. All provisional / engineering_pilot.
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
INPUTS = [ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_hazard_proxy_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/erosion_structure_proxy_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/mining_pressure_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/socioeconomic_exposure_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/rainfall_climatology_proxy_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif", ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/hotspot_stability_summary.csv"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster, parse_script_args
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
BOUNDARY_ID = "pe1"
EXPERIMENT_ID = "priority_scenarios"
OUT_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/{EXPERIMENT_ID}"
SCENARIO_DIR = OUT_DIR / "scenarios"
CRITERIA_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
# Common-mask overlay must reject true data gaps, but PE1 erosion_structure deliberately
# masks main-channel cells inherited from hillslope LS. Keep those cells NoData and require
# enough common coverage to catch tile seams / missing active criteria.
MIN_COMMON_VALID_FRACTION = 0.95

CRITERIA_PATHS = {
    "flood_hazard_proxy": CRITERIA_DIR / "flood_hazard_proxy_0_1.tif",
    "erosion_structure_proxy": CRITERIA_DIR / "erosion_structure_proxy_0_1.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "mining_pressure": CRITERIA_DIR / "mining_pressure_0_1.tif",
    "socioeconomic_exposure": CRITERIA_DIR / "socioeconomic_exposure_0_1.tif",
    "rainfall_climatology_proxy": CRITERIA_DIR / "rainfall_climatology_proxy_0_1.tif",
}

# Mentor-slide pairwise matrix (CR 0.022) mapped to PE1's six active criteria. The slide's 5 criteria
# (Flood, Sediment, LandUse/ASM, Environmental, Socioeconomic) map: Flood->flood_hazard,
# Sediment->erosion_structure, LandUse/ASM->land_cover + mining (split), Environmental->(no direct
# PE1 equivalent; folded into flood as terrain-context proxy), Socioeconomic->exposure, and rainfall
# receives zero weight in the slide-mapped scenario because the slide matrix has no rainfall criterion.
# Slide weights derived from principal eigenvector.
SLIDE_ORDER = ["flood", "sediment", "landuse_asm", "environmental", "socioeconomic"]
SLIDE_MATRIX = np.array([
    [1, 3, 5, 4, 6],
    [1/3, 1, 3, 2, 4],
    [1/5, 1/3, 1, 1/2, 2],
    [1/4, 1/2, 2, 1, 3],
    [1/6, 1/4, 1/2, 1/3, 1],
], dtype="float64")


def slide_weights() -> tuple[dict[str, float], float]:
    vals, vecs = np.linalg.eig(SLIDE_MATRIX)
    idx = int(np.argmax(vals.real))
    lam = float(vals.real[idx])
    w = np.abs(vecs[:, idx].real)
    w = w / w.sum()
    ci = (lam - len(SLIDE_ORDER)) / (len(SLIDE_ORDER) - 1)
    cr = ci / 1.12
    base = dict(zip(SLIDE_ORDER, w.tolist(), strict=True))
    landuse_half = base["landuse_asm"] / 2.0
    # environmental folded into flood (no separate PE1 environmental criterion)
    return {
        "flood_hazard_proxy": base["flood"] + base["environmental"],
        "erosion_structure_proxy": base["sediment"],
        "land_cover_pressure": landuse_half,
        "mining_pressure": landuse_half,
        "socioeconomic_exposure": base["socioeconomic"],
        "rainfall_climatology_proxy": 0.0,  # slide matrix has no rainfall criterion; set 0 there
    }, float(cr)


# Three scenarios: equal (neutral), slide-mapped (mentor matrix), flood/erosion/rainfall heavy (stress).
SCENARIOS = {
    "equal": {
        "flood_hazard_proxy": 1/6,
        "erosion_structure_proxy": 1/6,
        "land_cover_pressure": 1/6,
        "mining_pressure": 1/6,
        "socioeconomic_exposure": 1/6,
        "rainfall_climatology_proxy": 1/6,
    },
    "flood_erosion_heavy": {
        "flood_hazard_proxy": 0.30,
        "erosion_structure_proxy": 0.25,
        "land_cover_pressure": 0.05,
        "mining_pressure": 0.10,
        "socioeconomic_exposure": 0.05,
        "rainfall_climatology_proxy": 0.25,
    },
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


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


def read_boundary_mask(profile: dict) -> np.ndarray:
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(profile["crs"])
    from rasterio.features import geometry_mask

    return geometry_mask(
        boundary.geometry,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        invert=True,
    )


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
def raster_stats(data: np.ndarray) -> dict[str, object]:
    values = data[np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "min": round(float(values.min()), 6) if values.size else "",
        "mean": round(float(values.mean()), 6) if values.size else "",
        "p50": round(float(np.percentile(values, 50)), 6) if values.size else "",
        "p95": round(float(np.percentile(values, 95)), 6) if values.size else "",
        "max": round(float(values.max()), 6) if values.size else "",
    }


def add_colorbar(fig, ax, image, label: str) -> None:
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.04)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label(label, fontsize=8)


def plot_board(priority_mean, top20_frequency, equal_score, profile) -> None:
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0], bounds[2], bounds[1], bounds[3])

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), constrained_layout=True)
    panels = [
        ("A. Mean priority across scenarios", priority_mean, "YlOrRd", "0-1 score"),
        ("B. Equal-weight scenario", equal_score, "YlOrRd", "0-1 score"),
        ("C. Top-20% hotspot frequency", top20_frequency, "Blues", "frequency"),
    ]
    for ax, (title, data, cmap, label) in zip(axes, panels, strict=True):
        image = ax.imshow(np.ma.masked_invalid(data), extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1)
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.9)
        ax.set_title(title, loc="left", fontsize=10, fontweight="bold")
        ax.set_xlabel("Easting (km, EPSG:32718)", fontsize=8)
        ax.set_ylabel("Northing (km)", fontsize=8)
        km_formatter = FuncFormatter(lambda value, _: f"{value / 1000:.0f}")
        ax.xaxis.set_major_formatter(km_formatter)
        ax.yaxis.set_major_formatter(km_formatter)
        ax.grid(color="0.9", linewidth=0.4)
        ax.tick_params(labelsize=7)
        add_colorbar(fig, ax, image, label)
    fig.suptitle("PE1 (Peru engineering pilot) / priority scenarios: provisional hotspot map",
                 fontsize=12, fontweight="bold")
    fig.savefig(OUT_DIR / "pe1_priority_scenarios_board.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "pe1_priority_scenarios_board.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    opts = parse_script_args(boundary_id=BOUNDARY_ID, experiment_id=EXPERIMENT_ID)
    boundary_id = opts.get("boundary_id", BOUNDARY_ID)
    experiment_id = opts.get("experiment_id", EXPERIMENT_ID)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    profile = read_reference()
    criteria = {name: read_band(path, profile) for name, path in CRITERIA_PATHS.items()}
    boundary_mask = read_boundary_mask(profile)
    common_valid = boundary_mask.copy()
    for layer in criteria.values():
        common_valid &= np.isfinite(layer)
    common_valid_fraction = float(common_valid.sum() / boundary_mask.sum())
    if common_valid_fraction < MIN_COMMON_VALID_FRACTION:
        missing = []
        for name, layer in criteria.items():
            frac = float((boundary_mask & np.isfinite(layer)).sum() / boundary_mask.sum())
            if frac < MIN_COMMON_VALID_FRACTION:
                missing.append(f"{name}={frac:.6f}")
        raise RuntimeError(
            "PE1 active criteria do not share enough valid coverage; "
            f"common={common_valid_fraction:.6f}, threshold={MIN_COMMON_VALID_FRACTION}; "
            f"low layers: {', '.join(missing) if missing else 'none'}"
        )

    scenario_arrays: dict[str, np.ndarray] = {}
    weight_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    top20_masks: list[np.ndarray] = []

    # Inject the mentor-slide-mapped scenario (weights + CR).
    slide_w, slide_cr = slide_weights()
    all_scenarios = dict(SCENARIOS)
    all_scenarios["mentor_slide_mapped"] = slide_w
    for scenario, weights in all_scenarios.items():
        total = round(sum(weights.values()), 10)
        if total != 1.0:
            raise ValueError(f"weights for {scenario} sum to {total}")
        numerator = np.zeros((profile["height"], profile["width"]), dtype="float32")
        for criterion, weight in weights.items():
            layer = criteria[criterion]
            numerator[common_valid] += layer[common_valid] * weight
            weight_rows.append({
                "boundary_id": boundary_id, "experiment_id": experiment_id,
                "scenario": scenario, "criterion": criterion,
                "weight": round(weight, 8), "claim_level": "provisional",
            })
        score = np.full_like(numerator, np.nan, dtype="float32")
        score[common_valid] = numerator[common_valid]
        score = np.clip(score, 0.0, 1.0).astype("float32")
        scenario_arrays[scenario] = score
        write_raster(SCENARIO_DIR / f"priority_{scenario}.tif", score, profile)
        threshold = float(np.nanpercentile(score, 80))
        top20 = np.where(common_valid, score >= threshold, np.nan).astype("float32")
        top20_masks.append(top20)
        summary_rows.append({
            "boundary_id": boundary_id, "experiment_id": experiment_id,
            "scenario": scenario, "top20_threshold": round(threshold, 6),
            "common_valid_fraction": round(common_valid_fraction, 6),
            **raster_stats(score),
        })

    stack = np.stack(list(scenario_arrays.values())).astype("float32")
    priority_mean = np.full(stack.shape[1:], np.nan, dtype="float32")
    priority_std = np.full(stack.shape[1:], np.nan, dtype="float32")
    top20_frequency = np.full(stack.shape[1:], np.nan, dtype="float32")
    priority_mean[common_valid] = np.mean(stack[:, common_valid], axis=0).astype("float32")
    priority_std[common_valid] = np.std(stack[:, common_valid], axis=0).astype("float32")
    top20_stack = np.stack(top20_masks).astype("float32")
    top20_frequency[common_valid] = np.mean(top20_stack[:, common_valid], axis=0).astype("float32")

    write_raster(OUT_DIR / "priority_mean.tif", priority_mean, profile)
    write_raster(OUT_DIR / "priority_std.tif", priority_std, profile)
    write_raster(OUT_DIR / "top20_frequency.tif", top20_frequency, profile)
    plot_board(priority_mean, top20_frequency, scenario_arrays["equal"], profile)

    cell_km2 = 30.0 * 30.0 / 1e6
    stability_rows = [
        {"metric": "scenario_count", "value": len(all_scenarios)},
        {"metric": "mentor_slide_consistency_ratio", "value": round(slide_cr, 6)},
        {"metric": "common_valid_fraction", "value": round(common_valid_fraction, 6)},
        {"metric": "top20_all_scenarios_cells", "value": int(np.nansum(top20_frequency == 1.0))},
        {"metric": "top20_any_scenario_cells", "value": int(np.nansum(top20_frequency > 0.0))},
        {"metric": "top20_all_scenarios_area_km2", "value": round(float(np.nansum(top20_frequency == 1.0) * cell_km2), 3)},
        {"metric": "top20_any_scenario_area_km2", "value": round(float(np.nansum(top20_frequency > 0.0) * cell_km2), 3)},
        {"metric": "priority_std_mean", "value": round(float(np.nanmean(priority_std)), 6)},
        {"metric": "priority_std_p95", "value": round(float(np.nanpercentile(priority_std, 95)), 6)},
        {"metric": "zimbabwe_boundary_v1_rainfall_exposure_v0_4_top20_all_ref_km2", "value": 570.436},
        {"metric": "criteria_count", "value": len(CRITERIA_PATHS)},
        {"metric": "criteria", "value": "flood, erosion_structure, land_cover, mining, exposure, rainfall"},
    ]
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "hotspot_stability_summary.csv", stability_rows)
    print(f"wrote PE1 priority scenarios to {rel(OUT_DIR)}")
    print(f"  common valid coverage: {common_valid_fraction:.6f}")
    print(f"  top-20% stable across all scenarios: {stability_rows[5]['value']} km2")
    print(f"  mentor slide CR: {round(slide_cr, 6)}")
    print("  (Zimbabwe boundary_v1 / rainfall_exposure_v0_4 ref: 570.436 km2 stable top-20%; PE1 uses 6 criteria incl. rainfall)")


if __name__ == "__main__":
    main()
