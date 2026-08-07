#!/usr/bin/env python3
"""Test MapBiomas land-change evidence in the Peru PIM without replacing the baseline."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster


write_raster = lambda path, data, profile: _write_raster(  # noqa: E731
    path, data, profile, sanitize=True
)

VERSION_ID = "05_no_mining_mapbiomas_change_sensitivity"
OUT_DIR = (
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/pim_versions"
    / VERSION_ID
)
COMPONENT_DIR = OUT_DIR / "components"
CRITERIA_DIR = OUT_DIR / "criteria"
SCENARIO_DIR = OUT_DIR / "scenarios"
COMPARISON_DIR = OUT_DIR / "comparison"

BASELINE_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios"
MAPBIOMAS_DIR = (
    ROOT
    / "outputs/mapbiomas_peru_collection3_change_pilot"
    / "change_2014_2016_to_2022_2024"
)

INPUT_PATHS = {
    "flood_hazard": BASELINE_DIR / "pim_criteria/flood_hazard_0_1.tif",
    "sediment": BASELINE_DIR / "pim_criteria/sediment_0_1.tif",
    "land_cover_pressure": ROOT
    / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif",
    "bare_soil_vegetation_loss": MAPBIOMAS_DIR
    / "bare_soil_vegetation_loss_stable_windows_0_1.tif",
    "built_up_expansion": MAPBIOMAS_DIR
    / "built_up_expansion_stable_windows_0_1.tif",
    "agricultural_expansion": MAPBIOMAS_DIR
    / "agricultural_expansion_stable_windows_0_1.tif",
    "road_access_proximity": ROOT
    / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/road_access_proximity_0_1.tif",
    "environmental": BASELINE_DIR / "pim_criteria/environmental_0_1.tif",
    "socioeconomic": BASELINE_DIR / "pim_criteria/socioeconomic_0_1.tif",
    "baseline_pim": BASELINE_DIR / "scenarios/priority_mentor_peru_direct_pim.tif",
}

LAND_USE_WEIGHTS = {
    "land_cover_pressure": 0.40,
    "bare_soil_vegetation_loss": 0.35,
    "be": 0.25,
}
MAIN_WEIGHTS = {
    "flood_hazard": 0.35,
    "sediment": 0.25,
    "land_use": 0.20,
    "environmental": 0.12,
    "socioeconomic": 0.08,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def complete_weighted(layers: dict[str, np.ndarray], weights: dict[str, float]) -> np.ndarray:
    total = round(sum(weights.values()), 10)
    if total != 1.0:
        raise ValueError(f"weights sum to {total}, expected 1.0")
    first = next(iter(layers.values()))
    result = np.zeros(first.shape, dtype="float32")
    common = np.ones(first.shape, dtype=bool)
    for name, weight in weights.items():
        values = layers[name]
        if values.shape != first.shape:
            raise ValueError(f"shape mismatch for {name}")
        common &= np.isfinite(values)
        result += np.where(np.isfinite(values), values, 0.0).astype("float32") * weight
    result[~common] = np.nan
    return np.clip(result, 0.0, 1.0).astype("float32")


def build_supplementary_be(
    built_up_expansion: np.ndarray,
    agricultural_expansion: np.ndarray,
    road_access_proximity: np.ndarray,
) -> np.ndarray:
    """Combine observed developed-land expansion with current road pressure."""
    common = (
        np.isfinite(built_up_expansion)
        & np.isfinite(agricultural_expansion)
        & np.isfinite(road_access_proximity)
    )
    developed_expansion = np.maximum(built_up_expansion, agricultural_expansion)
    result = np.full(built_up_expansion.shape, np.nan, dtype="float32")
    result[common] = (
        0.50 * developed_expansion[common] + 0.50 * road_access_proximity[common]
    )
    return np.clip(result, 0.0, 1.0)


def calculate_supplementary_pim(components: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Calculate the change-evidence test. Extra keys such as Mining are ignored."""
    be = build_supplementary_be(
        components["built_up_expansion"],
        components["agricultural_expansion"],
        components["road_access_proximity"],
    )
    land_use = complete_weighted(
        {
            "land_cover_pressure": components["land_cover_pressure"],
            "bare_soil_vegetation_loss": components["bare_soil_vegetation_loss"],
            "be": be,
        },
        LAND_USE_WEIGHTS,
    )
    pim = complete_weighted(
        {
            "flood_hazard": components["flood_hazard"],
            "sediment": components["sediment"],
            "land_use": land_use,
            "environmental": components["environmental"],
            "socioeconomic": components["socioeconomic"],
        },
        MAIN_WEIGHTS,
    )
    return {"be": be, "land_use": land_use, "pim": pim}


def read_inputs() -> tuple[dict[str, np.ndarray], dict]:
    missing = [path for path in INPUT_PATHS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing inputs: " + ", ".join(str(path) for path in missing))

    profile = None
    arrays: dict[str, np.ndarray] = {}
    reference_contract = None
    for name, path in INPUT_PATHS.items():
        with rasterio.open(path) as source:
            contract = (source.crs, source.transform, source.width, source.height)
            if reference_contract is None:
                reference_contract = contract
                profile = source.profile.copy()
            elif contract != reference_contract:
                raise ValueError(f"grid mismatch: {path}")
            values = source.read(1).astype("float32")
            if source.nodata is not None:
                values[values == source.nodata] = np.nan
            values[~np.isfinite(values)] = np.nan
            arrays[name] = values
    if profile is None:
        raise RuntimeError("no input profile")
    return arrays, profile


def rank_correlation(left: np.ndarray, right: np.ndarray) -> float:
    left_rank = np.argsort(np.argsort(left, kind="mergesort"), kind="mergesort")
    right_rank = np.argsort(np.argsort(right, kind="mergesort"), kind="mergesort")
    return float(np.corrcoef(left_rank, right_rank)[0, 1])


def comparison_metrics(
    baseline: np.ndarray,
    test: np.ndarray,
    cell_area_km2: float,
) -> tuple[dict[str, object], np.ndarray, np.ndarray, np.ndarray]:
    common = np.isfinite(baseline) & np.isfinite(test)
    if not common.any():
        raise ValueError("baseline and test have no common finite support")
    baseline_values = baseline[common]
    test_values = test[common]
    delta_values = test_values - baseline_values

    baseline_threshold = float(np.percentile(baseline_values, 80))
    test_threshold = float(np.percentile(test_values, 80))
    baseline_top = common & (baseline >= baseline_threshold)
    test_top = common & (test >= test_threshold)
    intersection = baseline_top & test_top
    union = baseline_top | test_top

    delta = np.full(baseline.shape, np.nan, dtype="float32")
    delta[common] = test[common] - baseline[common]
    top20 = np.full(baseline.shape, np.nan, dtype="float32")
    top20[common] = test_top[common].astype("float32")
    top20_change = np.full(baseline.shape, np.nan, dtype="float32")
    top20_change[common] = 0.0
    top20_change[baseline_top & ~test_top] = -1.0
    top20_change[test_top & ~baseline_top] = 1.0

    metrics: dict[str, object] = {
        "common_valid_cells": int(common.sum()),
        "common_valid_area_km2": float(common.sum() * cell_area_km2),
        "baseline_mean": float(baseline_values.mean()),
        "test_mean": float(test_values.mean()),
        "mean_delta": float(delta_values.mean()),
        "mean_absolute_delta": float(np.abs(delta_values).mean()),
        "rmse": float(np.sqrt(np.mean(delta_values**2))),
        "max_absolute_delta": float(np.abs(delta_values).max()),
        "pearson_correlation": float(np.corrcoef(baseline_values, test_values)[0, 1]),
        "rank_correlation": rank_correlation(baseline_values, test_values),
        "baseline_top20_threshold": baseline_threshold,
        "test_top20_threshold": test_threshold,
        "top20_jaccard": float(intersection.sum() / union.sum()),
        "top20_retained_area_km2": float(intersection.sum() * cell_area_km2),
        "top20_gained_area_km2": float((test_top & ~baseline_top).sum() * cell_area_km2),
        "top20_lost_area_km2": float((baseline_top & ~test_top).sum() * cell_area_km2),
        "baseline_high_0_6_area_km2": float((common & (baseline >= 0.6)).sum() * cell_area_km2),
        "test_high_0_6_area_km2": float((common & (test >= 0.6)).sum() * cell_area_km2),
    }
    return metrics, delta, top20, top20_change


def write_metrics(path: Path, metrics: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows({"metric": key, "value": value} for key, value in metrics.items())


def build_comparison_figure(
    baseline: np.ndarray,
    test: np.ndarray,
    delta: np.ndarray,
    top20_change: np.ndarray,
    profile: dict,
    metrics: dict[str, object],
) -> tuple[plt.Figure, np.ndarray, plt.Text]:
    transform = profile["transform"]
    extent = [
        transform.c / 1000.0,
        (transform.c + transform.a * profile["width"]) / 1000.0,
        (transform.f + transform.e * profile["height"]) / 1000.0,
        transform.f / 1000.0,
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.subplots_adjust(left=0.07, right=0.93, top=0.90, bottom=0.12, wspace=0.24, hspace=0.24)
    fig.suptitle(
        "Peru supplementary land-change test — sensitivity scenario",
        fontsize=16,
        fontweight="bold",
    )

    for axis, values, title in (
        (axes[0, 0], baseline, "Current no-mining baseline"),
        (axes[0, 1], test, "MapBiomas change-evidence test"),
    ):
        image = axis.imshow(values, extent=extent, cmap="YlOrRd", vmin=0, vmax=1)
        axis.set_title(title)
        fig.colorbar(image, ax=axis, fraction=0.046, label="Priority score")

    finite_delta = np.abs(delta[np.isfinite(delta)])
    delta_limit = max(float(np.percentile(finite_delta, 99)), 0.01)
    delta_image = axes[1, 0].imshow(
        delta,
        extent=extent,
        cmap="RdBu_r",
        vmin=-delta_limit,
        vmax=delta_limit,
    )
    axes[1, 0].set_title("Score change: supplementary test − baseline")
    fig.colorbar(delta_image, ax=axes[1, 0], fraction=0.046, label="Score difference")

    change_cmap = ListedColormap(["#4575b4", "#d9d9d9", "#d73027"])
    change_norm = BoundaryNorm([-1.5, -0.5, 0.5, 1.5], change_cmap.N)
    change_image = axes[1, 1].imshow(
        top20_change, extent=extent, cmap=change_cmap, norm=change_norm
    )
    axes[1, 1].set_title("Highest-priority quintile movement")
    colorbar = fig.colorbar(change_image, ax=axes[1, 1], fraction=0.046, ticks=[-1, 0, 1])
    colorbar.ax.set_yticklabels(["Leaves", "Unchanged", "Enters"])

    for axis in axes.flat:
        axis.set_xlabel("Easting (km)")
        axis.set_ylabel("Northing (km)")
        axis.set_aspect("equal")

    footer = fig.text(
        0.5,
        0.025,
        (
            f"Top-quintile overlap: {float(metrics['top20_jaccard']):.1%} Jaccard  |  "
            f"Mean absolute score change: {float(metrics['mean_absolute_delta']):.3f}  |  "
            "Mining excluded; road term remains current road pressure, not measured road expansion."
        ),
        ha="center",
        fontsize=10,
    )
    footer.set_gid("comparison_footer")
    return fig, axes, footer


def plot_comparison(
    baseline: np.ndarray,
    test: np.ndarray,
    delta: np.ndarray,
    top20_change: np.ndarray,
    profile: dict,
    metrics: dict[str, object],
    path: Path,
) -> None:
    fig, _, _ = build_comparison_figure(
        baseline, test, delta, top20_change, profile, metrics
    )
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for directory in (COMPONENT_DIR, CRITERIA_DIR, SCENARIO_DIR, COMPARISON_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    arrays, profile = read_inputs()
    result = calculate_supplementary_pim(arrays)
    cell_area_km2 = abs(profile["transform"].a * profile["transform"].e) / 1_000_000.0
    metrics, delta, top20, top20_change = comparison_metrics(
        arrays["baseline_pim"], result["pim"], cell_area_km2
    )

    output_paths = {
        "be": COMPONENT_DIR / "built_agriculture_expansion_plus_current_road_0_1.tif",
        "land_use": CRITERIA_DIR / "general_land_use_pressure_0_1.tif",
        "pim": SCENARIO_DIR / "priority_mapbiomas_change_sensitivity_pim.tif",
        "top20": SCENARIO_DIR / "top20_mapbiomas_change_sensitivity_pim.tif",
        "delta": COMPARISON_DIR / "pim_delta_vs_current_baseline.tif",
        "top20_change": COMPARISON_DIR / "top20_change_vs_current_baseline.tif",
    }
    write_raster(output_paths["be"], result["be"], profile)
    write_raster(output_paths["land_use"], result["land_use"], profile)
    write_raster(output_paths["pim"], result["pim"], profile)
    write_raster(output_paths["top20"], top20, profile)
    write_raster(output_paths["delta"], delta, profile)
    write_raster(output_paths["top20_change"], top20_change, profile)

    metrics.update(
        {
            "scenario_status": "sensitivity_scenario",
            "top_weights": "FH=0.35; SE=0.25; LU=0.20; ES=0.12; SV=0.08",
            "land_use_weights": "LC=0.40; BV=0.35; BE=0.25",
            "be_definition": "0.50*max(MapBiomas built expansion, MapBiomas agricultural expansion) + 0.50*current OSM road proximity",
            "mining_role": "external overlay only; no input and no weight",
        }
    )
    metrics_path = COMPARISON_DIR / "comparison_summary.csv"
    write_metrics(metrics_path, metrics)
    board_path = COMPARISON_DIR / "baseline_vs_mapbiomas_change_test.png"
    plot_comparison(
        arrays["baseline_pim"],
        result["pim"],
        delta,
        top20_change,
        profile,
        metrics,
        board_path,
    )

    manifest_path = OUT_DIR / "run_manifest.json"
    manifest = {
        "version_id": VERSION_ID,
        "status": "sensitivity_scenario",
        "baseline_replaced": False,
        "weights": {"main": MAIN_WEIGHTS, "land_use": LAND_USE_WEIGHTS},
        "be_definition": metrics["be_definition"],
        "mining_role": metrics["mining_role"],
        "mining_inputs": [],
        "mapbiomas_stable_windows": [[2014, 2015, 2016], [2022, 2023, 2024]],
        "metrics": metrics,
        "inputs": [
            {"role": role, "path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for role, path in INPUT_PATHS.items()
        ],
        "outputs": [
            {"role": role, "path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for role, path in {
                **output_paths,
                "comparison_summary": metrics_path,
                "comparison_board": board_path,
            }.items()
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# MapBiomas change-evidence sensitivity scenario\n\n"
        "This version keeps the current main and Land Use weights, replaces BV with "
        "stable-window MapBiomas vegetation-loss evidence, and replaces the built/agriculture "
        "part of BE with mapped expansion evidence. The road term remains current road "
        "pressure. Mining is excluded and the current baseline is not replaced.\n",
        encoding="utf-8",
    )

    print(json.dumps(metrics, indent=2))
    print(f"wrote sensitivity scenario to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
