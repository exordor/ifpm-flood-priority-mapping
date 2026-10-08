#!/usr/bin/env python3
"""Compute presentation-level PIM contribution and weight-sensitivity evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/presentation_assets"
CRITERIA = [
    ("flood_hazard", "flood_hazard_0_1.tif"),
    ("sediment_erosion", "sediment_0_1.tif"),
    ("land_use", "landuse_asm_0_1.tif"),
    ("socioeconomic", "socioeconomic_0_1.tif"),
    ("environmental", "environmental_0_1.tif"),
]
WEIGHTS_A = np.array([0.35, 0.25, 0.20, 0.08, 0.12], dtype="float64")
WEIGHTS_B = np.array([0.34, 0.25, 0.17, 0.14, 0.10], dtype="float64")
COLORS = ["#0072B2", "#D55E00", "#009E73", "#E69F00", "#CC79A7"]
CASES = {
    "goslar": {
        "base": ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios/pim_criteria",
        "output": "goslar_dominant_contribution.png",
        "scale": 2,
    },
    "secocha": {
        "base": ROOT / "outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios/pim_criteria",
        "output": "secocha_dominant_contribution.png",
        "scale": 6,
    },
}
SECOCHA_RERUN = ROOT / "outputs/secocha_2023_validation/rerun_validation_summary.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_stack(base: Path) -> tuple[np.ndarray, rasterio.coords.BoundingBox, str]:
    arrays = []
    reference = None
    for _, filename in CRITERIA:
        path = base / filename
        with rasterio.open(path) as source:
            array = source.read(1).astype("float64")
            if source.nodata is not None:
                array[array == source.nodata] = np.nan
            signature = (source.shape, source.bounds, source.crs.to_string())
            if reference is None:
                reference = signature
            elif signature != reference:
                raise RuntimeError(f"Grid mismatch: {path}")
            arrays.append(array)
    assert reference is not None
    return np.stack(arrays), reference[1], reference[2]


def render_dominance(dominance: np.ndarray, valid: np.ndarray, bounds, output: Path, scale: int) -> None:
    height, width = dominance.shape
    dpi = 200
    figure = plt.figure(figsize=(width * scale / dpi, height * scale / dpi), dpi=dpi,
                        facecolor="white", frameon=False)
    axes = figure.add_axes([0, 0, 1, 1])
    axes.set_axis_off()
    mapped = np.ma.masked_where(~valid, dominance + 1)
    cmap = ListedColormap(COLORS)
    cmap.set_bad("white", alpha=0)
    norm = BoundaryNorm(np.arange(0.5, 6.5), 5)
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    axes.imshow(mapped, cmap=cmap, norm=norm, extent=extent, origin="upper", interpolation="nearest")
    axes.set_xlim(bounds.left, bounds.right)
    axes.set_ylim(bounds.bottom, bounds.top)
    axes.set_aspect("equal", adjustable="box")
    figure.savefig(output, dpi=dpi, facecolor="white", transparent=False)
    plt.close(figure)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "artifact_id": "presentation_pim_insights_20260818",
        "status": "derived from current standardized criterion rasters",
        "dominance_definition": "criterion with the largest Scenario B weighted contribution per common-valid pixel",
        "sensitivity_definition": "Scenario A vs B top-level weights applied to the same current criterion rasters",
        "pim_class_definition": "five equal intervals on 0-1: [0,0.2), [0.2,0.4), [0.4,0.6), [0.6,0.8), [0.8,1.0]",
        "weights": {"scenario_a": WEIGHTS_A.tolist(), "scenario_b": WEIGHTS_B.tolist()},
        "criterion_order": [name for name, _ in CRITERIA],
        "cases": {},
        "input_lineage": {},
    }

    for case, config in CASES.items():
        stack, bounds, crs = read_stack(config["base"])
        valid = np.all(np.isfinite(stack), axis=0)
        weighted = stack * WEIGHTS_B[:, None, None]
        dominance = np.argmax(np.where(np.isfinite(weighted), weighted, -np.inf), axis=0)
        shares = {
            CRITERIA[index][0]: float(np.mean(dominance[valid] == index))
            for index in range(len(CRITERIA))
        }

        score_a = np.sum(stack * WEIGHTS_A[:, None, None], axis=0)[valid]
        score_b = np.sum(stack * WEIGHTS_B[:, None, None], axis=0)[valid]
        class_a = np.minimum((score_a * 5).astype("int16"), 4)
        class_b = np.minimum((score_b * 5).astype("int16"), 4)
        top_a = score_a >= np.quantile(score_a, 0.8)
        top_b = score_b >= np.quantile(score_b, 0.8)
        intersection = int(np.logical_and(top_a, top_b).sum())

        output = OUT / config["output"]
        render_dominance(dominance, valid, bounds, output, config["scale"])
        manifest["cases"][case] = {
            "crs": crs,
            "bounds": list(bounds),
            "valid_cells": int(valid.sum()),
            "dominant_share": shares,
            "sensitivity": {
                "pearson_correlation": float(np.corrcoef(score_a, score_b)[0, 1]),
                "mean_absolute_difference": float(np.mean(np.abs(score_a - score_b))),
                "maximum_absolute_difference": float(np.max(np.abs(score_a - score_b))),
                "five_class_change_fraction": float(np.mean(class_a != class_b)),
                "top20_retained_fraction": float(intersection / int(top_a.sum())),
                "top20_jaccard_fraction": float(intersection / int(np.logical_or(top_a, top_b).sum())),
            },
            "output": {"path": str(output.relative_to(ROOT)), "sha256": sha256(output)},
        }
        for _, filename in CRITERIA:
            path = config["base"] / filename
            manifest["input_lineage"][str(path.relative_to(ROOT))] = sha256(path)

    rerun = json.loads(SECOCHA_RERUN.read_text(encoding="utf-8"))
    event = rerun["historical_event_candidate"]
    manifest["secocha_overlay"] = {
        "candidate_mean_pim": event["event_pim_mean"],
        "study_window_mean_pim": event["study_area_pim_mean"],
        "mean_difference": event["event_pim_mean"] - event["study_area_pim_mean"],
        "valid_candidate_cells": event["valid_support_cells"],
        "total_candidate_cells": event["total_event_cells"],
    }
    manifest["input_lineage"][str(SECOCHA_RERUN.relative_to(ROOT))] = sha256(SECOCHA_RERUN)

    output_manifest = OUT / "pim_insight_metrics.json"
    output_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
