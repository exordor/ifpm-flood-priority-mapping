#!/usr/bin/env python3
"""Build honest-label criteria_stack_v0_2 rasters for boundary_v1."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "criteria_stack_v0_2"
OUT_DIR = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}"
CRITERIA_DIR = OUT_DIR / "criteria"
CONFIG = ROOT / "context/configs/boundary_v1_criteria_stack_v0_2.csv"
REF = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"

INPUTS = {
    "twi": ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization/v1_twi_high_wetness_0_1.tif",
    "drainage": ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization/v1_drainage_proximity_0_1.tif",
    "structure": ROOT / "outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif",
    "c_factor": ROOT / "outputs/esa_worldcover_2021_v1_methodology/c_factor/c_factor_v1_30m.tif",
    "mining": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_closeness_to_mining_proxy_0_1_utm35s_30m.tif",
    "rivers": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_closeness_to_rivers_0_1_utm35s_30m.tif",
    "roads": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_closeness_to_roads_0_1_utm35s_30m.tif",
}

V01_TO_V02 = [
    {
        "v0_1_name": "sediment_structure",
        "issue": "R-invariant K x LS x C was too close to sediment-risk language and NoData was filled as 0.",
        "v0_2_name": "erosion_structure_proxy",
        "v0_2_meaning": "R-invariant erosion source structure; not final sediment risk.",
        "claim_level": "diagnostic_only",
    },
    {
        "v0_1_name": "landuse_asm_pressure",
        "issue": "C-factor and mining proxy were averaged despite different process meanings.",
        "v0_2_name": "land_cover_pressure + mining_pressure",
        "v0_2_meaning": "Split land-cover pressure from weak mining proxy.",
        "claim_level": "provisional",
    },
    {
        "v0_1_name": "environmental_sensitivity",
        "issue": "Layer was only river/water proximity.",
        "v0_2_name": "river_proximity_proxy",
        "v0_2_meaning": "Diagnostic river-proximity proxy; excluded from core environmental claim.",
        "claim_level": "diagnostic_only",
    },
    {
        "v0_1_name": "socioeconomic_exposure",
        "issue": "Layer was only road/access proximity.",
        "v0_2_name": "road_accessibility_proxy",
        "v0_2_meaning": "Diagnostic access proxy; excluded from socioeconomic-vulnerability claim.",
        "claim_level": "diagnostic_only",
    },
]


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


def read_reference() -> tuple[dict, np.ndarray]:
    with rasterio.open(REF) as ref:
        profile = ref.profile.copy()
        crs = ref.crs
        shape = (ref.height, ref.width)
        transform = ref.transform
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(crs)
    mask = geometry_mask(boundary.geometry, out_shape=shape, transform=transform, invert=True)
    return profile, mask


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


def normalize_2_98(data: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, float, float]:
    values = data[mask & np.isfinite(data)]
    if values.size == 0:
        raise ValueError("cannot normalize empty raster")
    low, high = np.nanpercentile(values, [2, 98])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise ValueError(f"bad percentile range: {low}, {high}")
    out = np.clip((data - low) / (high - low), 0.0, 1.0).astype("float32")
    out[~mask] = np.nan
    return out, float(low), float(high)


def weighted_average(parts: list[tuple[np.ndarray, float]], mask: np.ndarray) -> np.ndarray:
    numerator = np.zeros(mask.shape, dtype="float32")
    denominator = np.zeros(mask.shape, dtype="float32")
    for layer, weight in parts:
        valid = mask & np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        denominator[valid] += weight
    out = np.divide(numerator, denominator, out=np.full(mask.shape, np.nan, dtype="float32"), where=denominator > 0)
    out[~mask] = np.nan
    return out.astype("float32")


def stats(data: np.ndarray, mask: np.ndarray) -> dict[str, object]:
    inside = int(mask.sum())
    valid = mask & np.isfinite(data)
    values = data[valid]
    if values.size == 0:
        return {"valid_cells": 0, "valid_fraction": 0.0, "min": "", "mean": "", "max": ""}
    return {
        "valid_cells": int(values.size),
        "valid_fraction": round(float(values.size / inside), 6),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "max": round(float(values.max()), 6),
    }


def write_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    out_profile = profile.copy()
    out_profile.update(driver="GTiff", count=1, dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)
    encoded = np.where(np.isfinite(data), data, -9999.0).astype("float32")
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(encoded, 1)


def plot_preview(criteria: dict[str, np.ndarray], mask: np.ndarray, path: Path) -> None:
    names = [name for name in criteria if name in {"erosion_structure_proxy", "land_cover_pressure", "mining_pressure"}]
    fig, axes = plt.subplots(1, len(names), figsize=(12, 4), constrained_layout=True)
    for ax, name in zip(np.atleast_1d(axes), names, strict=True):
        data = np.where(mask, criteria[name], np.nan)
        image = ax.imshow(data, cmap="viridis", vmin=0, vmax=1)
        ax.set_title(name.replace("_", " "), fontsize=10)
        ax.set_axis_off()
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("boundary_v1 / criteria_stack_v0_2: split proxies, NoData preserved", fontsize=12)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    profile, mask = read_reference()
    config = pd.read_csv(CONFIG)
    rasters = {key: read_band(path, profile) for key, path in INPUTS.items()}

    normalized = {
        "twi": rasters["twi"],
        "drainage": rasters["drainage"],
        "mining": rasters["mining"],
        "rivers": rasters["rivers"],
        "roads": rasters["roads"],
    }
    normalized["structure"], structure_p02, structure_p98 = normalize_2_98(rasters["structure"], mask)
    normalized["c_factor"], c_p02, c_p98 = normalize_2_98(rasters["c_factor"], mask)

    grouped: dict[str, list[tuple[np.ndarray, float]]] = defaultdict(list)
    metadata: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in config.to_dict("records"):
        grouped[row["criterion"]].append((normalized[row["source_key"]], float(row["weight"])))
        metadata[row["criterion"]].append(row)

    criteria = {name: weighted_average(parts, mask) for name, parts in grouped.items()}
    manifest_rows = []
    for name, arr in criteria.items():
        output_path = CRITERIA_DIR / f"{name}_0_1.tif"
        arr = np.clip(arr, 0.0, 1.0).astype("float32")
        arr[~mask] = np.nan
        write_raster(output_path, arr, profile)
        rows = metadata[name]
        manifest_rows.append(
            {
                "boundary_id": rows[0]["boundary_id"],
                "experiment_id": rows[0]["experiment_id"],
                "criterion": name,
                "path": rel(output_path),
                "components": "; ".join(row["component"] for row in rows),
                "component_weights": "; ".join(f"{row['component']}={row['weight']}" for row in rows),
                "include_in_core": rows[0]["include_in_core"],
                "claim_level": rows[0]["claim_level"],
                "semantic_meaning": rows[0]["semantic_meaning"],
                "nodata_policy": rows[0]["nodata_policy"],
                **stats(arr, mask),
            }
        )

    coverage_rows = [
        {"boundary_id": BOUNDARY_ID, "experiment_id": EXPERIMENT_ID, "layer": key, "path": rel(path), **stats(data, mask)}
        for key, path, data in ((key, INPUTS[key], rasters[key]) for key in INPUTS)
    ] + [
        {
            "boundary_id": BOUNDARY_ID,
            "experiment_id": EXPERIMENT_ID,
            "layer": row["criterion"],
            "path": row["path"],
            **{k: row[k] for k in ["valid_cells", "valid_fraction", "min", "mean", "max"]},
        }
        for row in manifest_rows
    ]

    write_csv(OUT_DIR / "criteria_stack_manifest.csv", manifest_rows)
    write_csv(OUT_DIR / "nodata_coverage_report.csv", coverage_rows)
    write_csv(OUT_DIR / "criteria_stack_v0_1_to_v0_2_comparison.csv", V01_TO_V02)
    write_csv(
        OUT_DIR / "standardization_notes.csv",
        [
            {"component": "erosion_structure_proxy", "method": "percentile_clip_minmax_2_98", "clip_low": structure_p02, "clip_high": structure_p98},
            {"component": "land_cover_pressure", "method": "percentile_clip_minmax_2_98", "clip_low": c_p02, "clip_high": c_p98},
        ],
    )
    plot_preview(criteria, mask, OUT_DIR / "criteria_preview.png")
    print(f"wrote {BOUNDARY_ID} / {EXPERIMENT_ID} to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
