#!/usr/bin/env python3
"""Run continuous MapBiomas change-intensity sensitivity scenarios at three radii."""

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
from scipy.signal import fftconvolve


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bin.scenarios import run_peru_mapbiomas_change_sensitivity as change_runner


VERSION_ID = "06_no_mining_optimized_land_change_sensitivity"
OUT_DIR = (
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/pim_versions"
    / VERSION_ID
)
COMPONENT_DIR = OUT_DIR / "components"
SCENARIO_DIR = OUT_DIR / "scenarios"
COMPARISON_DIR = OUT_DIR / "comparison"
FIGURE_DIR = OUT_DIR / "figures"

NOMINAL_RADII_M = (500, 1000, 2000)
NORMALIZATION_PERCENTILE = 95.0
DENSITY_EPSILON = 1e-7
PURE_CHANGE_PIM = (
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/pim_versions"
    / "05_no_mining_mapbiomas_change_sensitivity/scenarios"
    / "priority_mapbiomas_change_sensitivity_pim.tif"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def radius_m_to_cells(radius_m: float, pixel_size_m: float) -> int:
    if radius_m <= 0 or pixel_size_m <= 0:
        raise ValueError("radius and pixel size must be positive")
    return max(1, int(round(radius_m / pixel_size_m)))


def circular_focal_density(
    presence: np.ndarray,
    valid_mask: np.ndarray,
    radius_cells: int,
) -> np.ndarray:
    """Calculate valid-area-adjusted circular density and preserve outside NoData."""
    if presence.shape != valid_mask.shape:
        raise ValueError("presence and valid mask must share a shape")
    if radius_cells < 1:
        raise ValueError("radius_cells must be at least 1")
    yy, xx = np.ogrid[-radius_cells : radius_cells + 1, -radius_cells : radius_cells + 1]
    kernel = ((xx * xx + yy * yy) <= radius_cells * radius_cells).astype("float32")
    numerator = fftconvolve(
        np.where(valid_mask, presence, 0.0).astype("float32"), kernel, mode="same"
    )
    denominator = fftconvolve(valid_mask.astype("float32"), kernel, mode="same")
    result = np.full(presence.shape, np.nan, dtype="float32")
    usable = valid_mask & (denominator > 0)
    result[usable] = np.clip(numerator[usable] / denominator[usable], 0.0, 1.0)
    return result


def normalize_positive_density(
    density: np.ndarray,
    percentile: float = NORMALIZATION_PERCENTILE,
) -> tuple[np.ndarray, float]:
    """Scale positive density by a robust upper percentile while keeping true zero at zero."""
    if not 0 < percentile <= 100:
        raise ValueError("percentile must be in (0, 100]")
    finite = np.isfinite(density)
    signal = finite & (density > DENSITY_EPSILON)
    positive = density[signal]
    result = np.full(density.shape, np.nan, dtype="float32")
    result[finite] = 0.0
    if positive.size == 0:
        return result, 0.0
    scale = float(np.percentile(positive, percentile))
    if scale <= 0:
        return result, scale
    result[signal] = np.clip(density[signal] / scale, 0.0, 1.0)
    return result, scale


def read_raster_on_profile(path: Path, profile: dict) -> np.ndarray:
    import rasterio

    with rasterio.open(path) as source:
        contract = (source.crs, source.transform, source.width, source.height)
        expected = (
            profile["crs"],
            profile["transform"],
            profile["width"],
            profile["height"],
        )
        if contract != expected:
            raise ValueError(f"grid mismatch: {path}")
        values = source.read(1).astype("float32")
        if source.nodata is not None:
            values[values == source.nodata] = np.nan
        values[~np.isfinite(values)] = np.nan
        return values


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def plot_optimization_board(
    baseline: np.ndarray,
    pure_change: np.ndarray,
    optimized: np.ndarray,
    top20_frequency: np.ndarray,
    profile: dict,
    candidate_metrics: dict[str, object],
    png_path: Path,
    pdf_path: Path,
) -> None:
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
        "Continuous land-change intensity test — Peru prototype",
        fontsize=17,
        fontweight="bold",
    )

    score_panels = (
        (axes[0, 0], baseline, "Current-state baseline"),
        (axes[0, 1], pure_change, "Direct binary-change test"),
        (axes[1, 0], optimized, "Optimized 1 km change intensity"),
    )
    for axis, values, title in score_panels:
        image = axis.imshow(values, extent=extent, cmap="YlOrRd", vmin=0, vmax=1)
        axis.set_title(title)
        fig.colorbar(image, ax=axis, fraction=0.046, label="Priority score")

    stability_image = axes[1, 1].imshow(
        top20_frequency,
        extent=extent,
        cmap="viridis",
        vmin=0,
        vmax=1,
    )
    axes[1, 1].set_title("Top-quintile stability across 0.5–2 km")
    fig.colorbar(stability_image, ax=axes[1, 1], fraction=0.046, label="Selection frequency")

    for axis in axes.flat:
        axis.set_xlabel("Easting (km)")
        axis.set_ylabel("Northing (km)")
        axis.set_aspect("equal")

    fig.text(
        0.5,
        0.025,
        (
            f"1 km vs baseline: rank r={float(candidate_metrics['rank_correlation']):.3f}, "
            f"Top-20% overlap={float(candidate_metrics['top20_jaccard']):.1%}, "
            f"mean score={float(candidate_metrics['test_mean']):.3f}.  "
            "Mining excluded; road term is current pressure, not measured expansion."
        ),
        ha="center",
        fontsize=10,
    )
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    for directory in (COMPONENT_DIR, SCENARIO_DIR, COMPARISON_DIR, FIGURE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if not PURE_CHANGE_PIM.exists():
        raise FileNotFoundError(PURE_CHANGE_PIM)

    arrays, profile = change_runner.read_inputs()
    pure_change = read_raster_on_profile(PURE_CHANGE_PIM, profile)
    pixel_size_m = abs(float(profile["transform"].a))
    valid_change = (
        np.isfinite(arrays["bare_soil_vegetation_loss"])
        & np.isfinite(arrays["built_up_expansion"])
        & np.isfinite(arrays["agricultural_expansion"])
    )
    cell_area_km2 = abs(profile["transform"].a * profile["transform"].e) / 1_000_000.0

    scenario_pims: dict[int, np.ndarray] = {}
    scenario_top20: dict[int, np.ndarray] = {}
    summary_rows: list[dict[str, object]] = []
    output_paths: dict[str, Path] = {}
    normalization_scales: dict[str, dict[str, float]] = {}

    for nominal_radius_m in NOMINAL_RADII_M:
        radius_cells = radius_m_to_cells(nominal_radius_m, pixel_size_m)
        actual_radius_m = radius_cells * pixel_size_m
        radius_dir = COMPONENT_DIR / f"radius_{nominal_radius_m}m"
        radius_dir.mkdir(parents=True, exist_ok=True)

        normalized_layers: dict[str, np.ndarray] = {}
        radius_scales: dict[str, float] = {}
        for name in (
            "bare_soil_vegetation_loss",
            "built_up_expansion",
            "agricultural_expansion",
        ):
            density = circular_focal_density(arrays[name], valid_change, radius_cells)
            normalized, scale = normalize_positive_density(density)
            normalized_layers[name] = normalized
            radius_scales[name] = scale
            density_path = radius_dir / f"{name}_density.tif"
            normalized_path = radius_dir / f"{name}_intensity_0_1.tif"
            change_runner.write_raster(density_path, density, profile)
            change_runner.write_raster(normalized_path, normalized, profile)
            output_paths[f"{name}_density_{nominal_radius_m}m"] = density_path
            output_paths[f"{name}_intensity_{nominal_radius_m}m"] = normalized_path

        scenario_components = dict(arrays)
        scenario_components.update(normalized_layers)
        result = change_runner.calculate_supplementary_pim(scenario_components)
        metrics, delta, top20, top20_change = change_runner.comparison_metrics(
            arrays["baseline_pim"], result["pim"], cell_area_km2
        )
        _, _, _, top20_change_vs_pure = change_runner.comparison_metrics(
            pure_change, result["pim"], cell_area_km2
        )
        common_pure = np.isfinite(pure_change) & np.isfinite(result["pim"])
        metrics.update(
            {
                "scenario": f"optimized_{nominal_radius_m}m",
                "nominal_radius_m": nominal_radius_m,
                "radius_cells": radius_cells,
                "actual_radius_m": actual_radius_m,
                "normalization_percentile": NORMALIZATION_PERCENTILE,
                "mean_vs_pure_change": float(
                    np.mean(result["pim"][common_pure] - pure_change[common_pure])
                ),
                "rank_correlation_vs_pure_change": change_runner.rank_correlation(
                    pure_change[common_pure], result["pim"][common_pure]
                ),
            }
        )
        summary_rows.append(metrics)
        scenario_pims[nominal_radius_m] = result["pim"]
        scenario_top20[nominal_radius_m] = top20
        normalization_scales[str(nominal_radius_m)] = radius_scales

        be_path = radius_dir / "be_optimized_0_1.tif"
        land_use_path = radius_dir / "land_use_optimized_0_1.tif"
        pim_path = SCENARIO_DIR / f"priority_optimized_{nominal_radius_m}m_pim.tif"
        top20_path = SCENARIO_DIR / f"top20_optimized_{nominal_radius_m}m_pim.tif"
        delta_path = COMPARISON_DIR / f"pim_delta_{nominal_radius_m}m_vs_baseline.tif"
        change_path = COMPARISON_DIR / f"top20_change_{nominal_radius_m}m_vs_baseline.tif"
        pure_change_path = COMPARISON_DIR / f"top20_change_{nominal_radius_m}m_vs_pure_change.tif"
        for path, values in (
            (be_path, result["be"]),
            (land_use_path, result["land_use"]),
            (pim_path, result["pim"]),
            (top20_path, top20),
            (delta_path, delta),
            (change_path, top20_change),
            (pure_change_path, top20_change_vs_pure),
        ):
            change_runner.write_raster(path, values, profile)
        output_paths.update(
            {
                f"be_{nominal_radius_m}m": be_path,
                f"land_use_{nominal_radius_m}m": land_use_path,
                f"pim_{nominal_radius_m}m": pim_path,
                f"top20_{nominal_radius_m}m": top20_path,
                f"delta_{nominal_radius_m}m": delta_path,
                f"top20_change_{nominal_radius_m}m": change_path,
                f"top20_change_vs_pure_{nominal_radius_m}m": pure_change_path,
            }
        )

    pim_stack = np.stack([scenario_pims[radius] for radius in NOMINAL_RADII_M])
    top20_stack = np.stack([scenario_top20[radius] for radius in NOMINAL_RADII_M])
    common_sensitivity = np.all(np.isfinite(pim_stack), axis=0)
    pim_std = np.full(common_sensitivity.shape, np.nan, dtype="float32")
    top20_frequency = np.full(common_sensitivity.shape, np.nan, dtype="float32")
    pim_std[common_sensitivity] = np.std(pim_stack[:, common_sensitivity], axis=0)
    top20_frequency[common_sensitivity] = np.mean(
        top20_stack[:, common_sensitivity], axis=0
    )
    pim_std_path = COMPARISON_DIR / "pim_standard_deviation_across_radii.tif"
    frequency_path = COMPARISON_DIR / "top20_frequency_across_radii.tif"
    change_runner.write_raster(pim_std_path, pim_std, profile)
    change_runner.write_raster(frequency_path, top20_frequency, profile)
    output_paths["pim_std_across_radii"] = pim_std_path
    output_paths["top20_frequency_across_radii"] = frequency_path

    summary_path = COMPARISON_DIR / "radius_sensitivity_summary.csv"
    write_summary(summary_path, summary_rows)
    output_paths["radius_sensitivity_summary"] = summary_path

    candidate_metrics = next(row for row in summary_rows if row["nominal_radius_m"] == 1000)
    png_path = FIGURE_DIR / "baseline_binary_change_optimized_comparison.png"
    pdf_path = FIGURE_DIR / "baseline_binary_change_optimized_comparison.pdf"
    plot_optimization_board(
        arrays["baseline_pim"],
        pure_change,
        scenario_pims[1000],
        top20_frequency,
        profile,
        candidate_metrics,
        png_path,
        pdf_path,
    )
    output_paths["comparison_figure_png"] = png_path
    output_paths["comparison_figure_pdf"] = pdf_path

    manifest_path = OUT_DIR / "run_manifest.json"
    manifest = {
        "version_id": VERSION_ID,
        "status": "sensitivity_scenario",
        "baseline_replaced": False,
        "recommended_candidate": "optimized_1000m",
        "candidate_reason": "middle radius of the declared 0.5/1/2 km sensitivity set; not an approved final scale",
        "nominal_radii_m": list(NOMINAL_RADII_M),
        "normalization": {
            "method": "positive focal density divided by its 95th percentile; zero remains zero; upper tail clipped at 1",
            "percentile": NORMALIZATION_PERCENTILE,
            "scales": normalization_scales,
        },
        "formula": {
            "bv": "normalized circular focal density of stable-window vegetation loss",
            "development_expansion": "max(normalized built expansion density, normalized agricultural expansion density)",
            "be": "0.50 development expansion intensity + 0.50 current road pressure",
            "land_use": "0.40 LC + 0.35 BV + 0.25 BE",
            "pim": "0.35 FH + 0.25 SE + 0.20 LU + 0.12 ES + 0.08 SV",
        },
        "mining_role": "external overlay only; no input and no weight",
        "mining_inputs": [],
        "candidate_metrics": candidate_metrics,
        "input_paths": [
            {
                "role": role,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
            for role, path in {**change_runner.INPUT_PATHS, "pure_change_pim": PURE_CHANGE_PIM}.items()
        ],
        "outputs": [
            {
                "role": role,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
            for role, path in output_paths.items()
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "README.md").write_text(
        "# Optimized continuous land-change sensitivity\n\n"
        "This version converts stable-window MapBiomas change masks into valid-area-adjusted "
        "circular focal densities at nominal 0.5, 1, and 2 km radii. Positive densities are "
        "scaled by their 95th percentile while zero remains zero. The 1 km result is the "
        "middle sensitivity candidate, not an approved final scale. Original PIM and Land Use "
        "weights are retained, Mining remains external, and the baseline is not replaced.\n",
        encoding="utf-8",
    )

    print(json.dumps(candidate_metrics, indent=2))
    print(f"wrote optimized sensitivity scenarios to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
