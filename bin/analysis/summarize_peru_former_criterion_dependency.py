#!/usr/bin/env python3
"""Quantify source dependence and component-removal sensitivity in the Peru PIM."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/peru_former_pim_chain"
PIM = BASE / "priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif"
LANDUSE_CRITERION = BASE / "priority_scenarios/pim_criteria/landuse_asm_0_1.tif"
SOCIOECONOMIC_CRITERION = BASE / "priority_scenarios/pim_criteria/socioeconomic_0_1.tif"
ENVIRONMENTAL_CRITERION = BASE / "priority_scenarios/pim_criteria/environmental_0_1.tif"
C_FACTOR = BASE / "criteria_stack/criteria/c_factor_0_1.tif"
LAND_USE_PRESSURE = BASE / "criteria_stack/criteria/land_cover_pressure_0_1.tif"
ROAD_ACCESS = BASE / "criteria_stack/criteria/road_access_proximity_0_1.tif"
INFRASTRUCTURE = BASE / "exposure_indicators/infrastructure_exposure_0_1.tif"
WATER_CONTEXT = BASE / "environmental_sensitivity/water_wetland_context_0_1.tif"
PROTECTED_CONTEXT = BASE / "environmental_sensitivity/protected_area_context_0_1.tif"
OUT_CSV = BASE / "priority_scenarios/criterion_dependency_diagnostics.csv"
OUT_MANIFEST = BASE / "priority_scenarios/criterion_dependency_diagnostics_manifest.json"

INPUTS = [
    ROOT / "outputs/peru_former_pim_chain/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
    ROOT / "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/landuse_asm_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/socioeconomic_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/environmental_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/criteria_stack/criteria/c_factor_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/criteria_stack/criteria/land_cover_pressure_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/criteria_stack/criteria/road_access_proximity_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/exposure_indicators/infrastructure_exposure_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/environmental_sensitivity/water_wetland_context_0_1.tif",
    ROOT / "outputs/peru_former_pim_chain/environmental_sensitivity/protected_area_context_0_1.tif",
]
OUTPUTS = [
    ROOT / "outputs/peru_former_pim_chain/priority_scenarios/criterion_dependency_diagnostics.csv",
    ROOT / "outputs/peru_former_pim_chain/priority_scenarios/criterion_dependency_diagnostics_manifest.json",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_raster(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def sampled_pairs(
    reference: np.ndarray,
    candidate: np.ndarray,
    max_samples: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    valid = np.isfinite(reference) & np.isfinite(candidate)
    indices = np.flatnonzero(valid)
    common_count = int(indices.size)
    if common_count == 0:
        raise ValueError("comparison has no common finite cells")
    if common_count > max_samples:
        positions = np.linspace(0, common_count - 1, max_samples, dtype="int64")
        indices = indices[positions]
    return reference.ravel()[indices], candidate.ravel()[indices], common_count


def pair_metrics(
    reference: np.ndarray,
    candidate: np.ndarray,
    *,
    max_samples: int = 250_000,
) -> dict[str, float | int]:
    x, y, common_count = sampled_pairs(reference, candidate, max_samples)
    rho = float(spearmanr(x, y).statistic)
    return {
        "common_cell_count": common_count,
        "sampled_cell_count": int(x.size),
        "spearman_rho": rho,
        "mean_abs_difference": float(np.mean(np.abs(x - y))),
    }


def pim_alternative_metrics(
    full_pim: np.ndarray,
    *,
    current_component: np.ndarray,
    alternative_component: np.ndarray,
    main_weight: float,
    max_samples: int = 250_000,
) -> dict[str, float | int]:
    valid = (
        np.isfinite(full_pim)
        & np.isfinite(current_component)
        & np.isfinite(alternative_component)
    )
    candidate = np.full(full_pim.shape, np.nan, dtype="float32")
    candidate[valid] = (
        full_pim[valid]
        + main_weight * (alternative_component[valid] - current_component[valid])
    )
    metrics = pair_metrics(full_pim, candidate, max_samples=max_samples)
    reference_threshold = float(np.percentile(full_pim[valid], 80))
    candidate_threshold = float(np.percentile(candidate[valid], 80))
    reference_top = valid & (full_pim >= reference_threshold)
    candidate_top = valid & (candidate >= candidate_threshold)
    union = int(np.sum(reference_top | candidate_top))
    intersection = int(np.sum(reference_top & candidate_top))
    metrics.update(
        {
            "top_quintile_jaccard": intersection / union if union else 1.0,
            "reference_top_quintile_count": int(np.sum(reference_top)),
            "alternative_top_quintile_count": int(np.sum(candidate_top)),
        }
    )
    return metrics


def diagnostic_row(
    diagnostic_id: str,
    diagnostic_type: str,
    reference: str,
    alternative: str,
    metrics: dict[str, float | int],
    interpretation: str,
) -> dict[str, object]:
    return {
        "diagnostic_id": diagnostic_id,
        "diagnostic_type": diagnostic_type,
        "reference": reference,
        "alternative": alternative,
        **metrics,
        "claim_level": "diagnostic_only",
        "interpretation": interpretation,
    }


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


def main() -> None:
    arrays = {path: read_raster(path) for path in INPUTS}
    pim = arrays[PIM]
    landuse = arrays[LANDUSE_CRITERION]
    socioeconomic = arrays[SOCIOECONOMIC_CRITERION]
    environmental = arrays[ENVIRONMENTAL_CRITERION]
    protected = arrays[PROTECTED_CONTEXT]

    rows = [
        diagnostic_row(
            "c_factor_vs_land_use_pressure",
            "shared_source_dependence",
            "WorldCover RUSLE C score",
            "WorldCover land-use pressure score",
            pair_metrics(arrays[C_FACTOR], arrays[LAND_USE_PRESSURE]),
            "Distinct value functions share one WorldCover classification; correlation is dependence evidence, not duplication proof.",
        ),
        diagnostic_row(
            "socioeconomic_vs_road_access",
            "component_rank_dependence",
            "combined socioeconomic criterion",
            "road/access component only",
            pair_metrics(socioeconomic, arrays[ROAD_ACCESS]),
            "High rank agreement indicates that road/access may dominate the combined spatial ordering.",
        ),
        diagnostic_row(
            "socioeconomic_vs_infrastructure",
            "component_rank_dependence",
            "combined socioeconomic criterion",
            "population/building infrastructure component only",
            pair_metrics(socioeconomic, arrays[INFRASTRUCTURE]),
            "Comparison diagnoses spatial ordering; the current score uses separate 0.35 population and 0.30 mapped-infrastructure components.",
        ),
        diagnostic_row(
            "environmental_vs_water_context",
            "component_rank_dependence",
            "current environmental criterion",
            "water/wetland context only",
            {
                **pair_metrics(environmental, arrays[WATER_CONTEXT]),
                "protected_context_nonzero_fraction": float(
                    np.mean(protected[np.isfinite(protected)] > 0)
                ),
            },
            "SERNANP national definitive layer 0 contributes no local nonzero cells; current ordering is water/wetland-led.",
        ),
        diagnostic_row(
            "pim_socioeconomic_road_only",
            "component_removal_sensitivity",
            "current direct-weight PIM",
            "replace Socioeconomic criterion with road/access only",
            pim_alternative_metrics(
                pim,
                current_component=socioeconomic,
                alternative_component=arrays[ROAD_ACCESS],
                main_weight=0.08,
            ),
            "Tests how much the final PIM changes if provisional population/building evidence is removed.",
        ),
        diagnostic_row(
            "pim_socioeconomic_infrastructure_only",
            "component_removal_sensitivity",
            "current direct-weight PIM",
            "replace Socioeconomic criterion with infrastructure only",
            pim_alternative_metrics(
                pim,
                current_component=socioeconomic,
                alternative_component=arrays[INFRASTRUCTURE],
                main_weight=0.08,
            ),
            "Tests how much the final PIM changes if road/access evidence is removed.",
        ),
        diagnostic_row(
            "pim_environmental_water_only_rescaled",
            "component_availability_sensitivity",
            "current direct-weight PIM",
            "replace current Environmental score with water/wetland context rescaled to full criterion range",
            pim_alternative_metrics(
                pim,
                current_component=environmental,
                alternative_component=arrays[WATER_CONTEXT],
                main_weight=0.12,
            ),
            "Sensitivity only; it does not authorize silently reallocating the absent protected/ecological subweight.",
        ),
    ]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_CSV, rows)
    manifest = {
        "status": "diagnostic_only",
        "purpose": "criterion dependence and component-removal sensitivity; not model validation",
        "sampling": "all common cells for top-quintile metrics; deterministic evenly spaced sample up to 250000 cells for Spearman and mean absolute difference",
        "inputs": [{"path": rel(path), "sha256": sha256(path)} for path in INPUTS],
        "output": {"path": rel(OUT_CSV), "sha256": sha256(OUT_CSV)},
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote: {rel(OUT_CSV)}")


if __name__ == "__main__":
    main()
