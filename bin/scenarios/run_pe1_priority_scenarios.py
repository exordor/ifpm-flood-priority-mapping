#!/usr/bin/env python3
"""Run priority scenarios for the southern Peru comparison catchment.

PE1 follows the mentor 5-main-criterion AHP framework: Flood, Sediment,
Land Use / ASM, Environmental, and Socioeconomic. Five criteria are actively
scored in the current executable prototype:

- Flood hazard: flood-conditioning factors + rainfall climatology.
- Sediment: soil-erosion factors.
- Land Use / ASM: land-cover pressure + mining pressure.
- Environmental: water/wetland and protected-area sensitivity indicator.
- Socioeconomic: exposure/access indicators.
Three scenarios: equal, mentor-slide available PIM weights, and
flood/sediment-heavy.

Soil-erosion normalization note: the soil_erosion_factors criterion is max-normalized to [0,1] for
MCDA scoring, so its 0-1 value is a relative hotspot intensity, not absolute t/ha/yr. Rank is
not affected by the chosen scalar R-factor.

Outputs (gitignored under outputs/srtm_1arcsec_peru_pilot/priority_scenarios/):
priority mean/std/top20-frequency rasters, per-scenario rasters, weights + summary CSVs,
and a board figure. All provisional / sensitivity_scenario.
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
INPUTS = [ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/flood_conditioning_factors_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/soil_erosion_factors_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/mining_pressure_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/exposure_indicators_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/rainfall_climatology_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif", ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif", ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
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
PIM_CRITERIA_DIR = OUT_DIR / "pim_criteria"
CRITERIA_DIR = ROOT / f"outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
ZIMBABWE_STABILITY_SUMMARY = ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4/hotspot_stability_summary.csv"
# Common-mask overlay must reject true data gaps, but PE1 erosion_structure deliberately
# masks main-channel cells inherited from hillslope LS. Keep those cells NoData and require
# enough common coverage to catch tile seams / missing active criteria.
MIN_COMMON_VALID_FRACTION = 0.95

COMPONENT_PATHS = {
    "flood_conditioning_factors": CRITERIA_DIR / "flood_conditioning_factors_0_1.tif",
    "soil_erosion_factors": CRITERIA_DIR / "soil_erosion_factors_0_1.tif",
    "land_cover_pressure": CRITERIA_DIR / "land_cover_pressure_0_1.tif",
    "mining_pressure": CRITERIA_DIR / "mining_pressure_0_1.tif",
    "exposure_indicators": CRITERIA_DIR / "exposure_indicators_0_1.tif",
    "rainfall_climatology": CRITERIA_DIR / "rainfall_climatology_0_1.tif",
    "environmental_sensitivity": ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif",
}

PIM_CRITERIA_ORDER = ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"]
ACTIVE_PIM_CRITERIA = PIM_CRITERIA_ORDER
PIM_COMPONENTS = {
    "flood_hazard": {"flood_conditioning_factors": 0.5, "rainfall_climatology": 0.5},
    "sediment": {"soil_erosion_factors": 1.0},
    "landuse_asm": {"land_cover_pressure": 0.5, "mining_pressure": 0.5},
    "environmental": {"environmental_sensitivity": 1.0},
    "socioeconomic": {"exposure_indicators": 1.0},
}

# Mentor-slide pairwise matrix (CR 0.022) for the five PIM main criteria.
SLIDE_ORDER = PIM_CRITERIA_ORDER
SLIDE_MATRIX = np.array([
    [1, 3, 5, 4, 6],
    [1/3, 1, 3, 2, 4],
    [1/5, 1/3, 1, 1/2, 2],
    [1/4, 1/2, 2, 1, 3],
    [1/6, 1/4, 1/2, 1/3, 1],
], dtype="float64")


def slide_weights_available_pim() -> tuple[dict[str, float], float]:
    vals, vecs = np.linalg.eig(SLIDE_MATRIX)
    idx = int(np.argmax(vals.real))
    lam = float(vals.real[idx])
    w = np.abs(vecs[:, idx].real)
    w = w / w.sum()
    ci = (lam - len(SLIDE_ORDER)) / (len(SLIDE_ORDER) - 1)
    cr = ci / 1.12
    base = dict(zip(SLIDE_ORDER, w.tolist(), strict=True))
    available_total = sum(base[name] for name in ACTIVE_PIM_CRITERIA)
    return {
        name: base[name] / available_total
        for name in ACTIVE_PIM_CRITERIA
    }, float(cr)


# Three scenarios: equal (neutral), slide PIM weights, flood/sediment-heavy (stress).
SCENARIOS = {
    "equal_active_pim": {name: 1/len(ACTIVE_PIM_CRITERIA) for name in ACTIVE_PIM_CRITERIA},
    "flood_sediment_heavy_pim": {
        "flood_hazard": 0.30,
        "sediment": 0.25,
        "landuse_asm": 0.20,
        "environmental": 0.10,
        "socioeconomic": 0.15,
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


def read_summary_metric(path: Path, metric: str) -> float:
    if not path.exists():
        return float("nan")
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("metric") == metric:
                try:
                    return float(row["value"])
                except (TypeError, ValueError):
                    return float("nan")
    return float("nan")


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


def combine_weighted_layers(
    source_layers: dict[str, np.ndarray],
    component_weights: dict[str, float],
) -> np.ndarray:
    first = next(iter(source_layers.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    valid_all = np.ones(first.shape, dtype=bool)
    total_weight = float(sum(component_weights.values()))
    for component, weight in component_weights.items():
        layer = source_layers[component]
        valid = np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        valid_all &= valid
    combined = np.full(first.shape, np.nan, dtype="float32")
    combined[valid_all] = numerator[valid_all] / total_weight
    return np.clip(combined, 0.0, 1.0).astype("float32")


def build_pim_criteria(components: dict[str, np.ndarray], profile: dict) -> dict[str, np.ndarray]:
    PIM_CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    criteria = {
        name: combine_weighted_layers(components, weights)
        for name, weights in PIM_COMPONENTS.items()
    }
    for name, data in criteria.items():
        write_raster(PIM_CRITERIA_DIR / f"{name}_0_1.tif", data, profile)
    return criteria


def build_grid_check(profile: dict, layers: dict[str, np.ndarray]) -> list[dict[str, object]]:
    rows = []
    for name, data in layers.items():
        values = data[np.isfinite(data)]
        rows.append({
            "criterion": name,
            "grid_compatible": True,
            "crs": str(profile["crs"]),
            "width": profile["width"],
            "height": profile["height"],
            "valid_cells": int(values.size),
            "valid_fraction": round(float(values.size / data.size), 6),
            "min": round(float(values.min()), 6) if values.size else "",
            "mean": round(float(values.mean()), 6) if values.size else "",
            "max": round(float(values.max()), 6) if values.size else "",
        })
    return rows


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
    cax = divider.append_axes("right", size="3%", pad=0.08)
    cb = fig.colorbar(image, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label(label, fontsize=8)


def plot_board(priority_mean, top20_frequency, equal_score, profile) -> None:
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(profile["crs"])
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (bounds[0], bounds[2], bounds[1], bounds[3])

    fig, axes = plt.subplots(1, 3, figsize=(16.2, 4.9), constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=0.12, h_pad=0.08, wspace=0.18, hspace=0.02)
    panels = [
        ("A. Mean priority score across scenarios", priority_mean, "YlOrRd", "0-1 priority score"),
        ("B. Equal-weight priority score", equal_score, "YlOrRd", "0-1 priority score"),
        ("C. Stable hotspot frequency (top 20%)", top20_frequency, "Blues", "hotspot frequency"),
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
    fig.suptitle(
        "Southern Peru Comparison Catchment: PIM 5-Criterion Prototype Priority Screening",
        fontsize=12,
        fontweight="bold",
    )
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
    components = {name: read_band(path, profile) for name, path in COMPONENT_PATHS.items()}
    criteria = build_pim_criteria(components, profile)
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
    slide_w, slide_cr = slide_weights_available_pim()
    all_scenarios = dict(SCENARIOS)
    all_scenarios["mentor_slide_available_pim"] = slide_w
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
                "weight": round(weight, 8), "claim_level": "sensitivity_scenario",
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
    plot_board(priority_mean, top20_frequency, scenario_arrays["equal_active_pim"], profile)

    cell_km2 = 30.0 * 30.0 / 1e6
    zimbabwe_top20_ref_km2 = read_summary_metric(ZIMBABWE_STABILITY_SUMMARY, "stable_area_km2")
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
        {"metric": "zimbabwe_boundary_v1_rainfall_exposure_v0_4_top20_all_ref_km2", "value": round(zimbabwe_top20_ref_km2, 3)},
        {"metric": "pim_main_criteria_count", "value": len(PIM_CRITERIA_ORDER)},
        {"metric": "active_scored_pim_criteria_count", "value": len(ACTIVE_PIM_CRITERIA)},
        {"metric": "component_layer_count", "value": len(COMPONENT_PATHS)},
        {"metric": "active_scored_pim_criteria", "value": ", ".join(ACTIVE_PIM_CRITERIA)},
        {"metric": "component_layers", "value": ", ".join(COMPONENT_PATHS)},
        {"metric": "environmental_sensitivity_status", "value": "provisional"},
    ]
    write_csv(OUT_DIR / "scenario_weights.csv", weight_rows)
    write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)
    write_csv(OUT_DIR / "hotspot_stability_summary.csv", stability_rows)
    write_csv(OUT_DIR / "component_grid_check.csv", build_grid_check(profile, components))
    write_csv(OUT_DIR / "pim_criteria_grid_check.csv", build_grid_check(profile, criteria))
    print(f"wrote southern Peru comparison-catchment priority scenarios to {rel(OUT_DIR)}")
    print(f"  common valid coverage: {common_valid_fraction:.6f}")
    print(f"  top-20% stable across all scenarios: {stability_rows[5]['value']} km2")
    print(f"  mentor slide CR: {round(slide_cr, 6)}")
    print("  (PE1 overlay uses 5 active scored PIM criteria; Environmental sensitivity is provisional)")


if __name__ == "__main__":
    main()
