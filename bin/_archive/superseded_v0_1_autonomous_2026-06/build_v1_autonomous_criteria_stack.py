#!/usr/bin/env python3
"""Build grid-compatible V1 autonomous prototype criteria rasters."""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
from _lib.ifpm_tools import raster_stats as stats
OUT_DIR = ROOT / "outputs/v1_autonomous_prototype_v0_1"
CRITERIA_DIR = OUT_DIR / "criteria"
REF = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"

INPUTS = {
    "twi": ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization/v1_twi_high_wetness_0_1.tif",
    "drainage": ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization/v1_drainage_proximity_0_1.tif",
    "structure": ROOT / "outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif",
    "c_factor": ROOT / "outputs/esa_worldcover_2021_v1_methodology/c_factor/c_factor_v1_30m.tif",
    "mining": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_mining_activity_indicator_0_1_utm35s_30m.tif",
    "rivers": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_closeness_to_rivers_0_1_utm35s_30m.tif",
    "roads": ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_closeness_to_roads_0_1_utm35s_30m.tif",
}

CRITERIA = [
    "flood_hydrology",
    "sediment_structure",
    "landuse_asm_pressure",
    "environmental_sensitivity",
    "socioeconomic_exposure",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_reference() -> tuple[dict, object, np.ndarray]:
    with rasterio.open(REF) as ref:
        profile = ref.profile.copy()
        crs = ref.crs
        shape = (ref.height, ref.width)
        transform = ref.transform
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(crs)
    mask = geometry_mask(boundary.geometry, out_shape=shape, transform=transform, invert=True)
    return profile, boundary.geometry.iloc[0], mask


def read_band(path: Path, reference_profile: dict) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    with rasterio.open(path) as src:
        if src.crs != reference_profile["crs"]:
            raise ValueError(f"CRS mismatch for {path}")
        if src.transform != reference_profile["transform"]:
            raise ValueError(f"transform mismatch for {path}")
        if src.width != reference_profile["width"] or src.height != reference_profile["height"]:
            raise ValueError(f"shape mismatch for {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def normalize_2_98(data: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, float, float]:
    vals = data[mask & np.isfinite(data)]
    if vals.size == 0:
        raise ValueError("cannot normalize an empty raster")
    low, high = np.nanpercentile(vals, [2, 98])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise ValueError(f"bad percentile range: {low}, {high}")
    out = np.clip((data - low) / (high - low), 0.0, 1.0).astype("float32")
    out[~mask] = np.nan
    return out, float(low), float(high)


def average_layers(layers: list[np.ndarray], mask: np.ndarray) -> np.ndarray:
    stack = np.stack(layers).astype("float32")
    masked_stack = np.where(mask[None, :, :], stack, 0.0)
    valid_counts = np.sum(np.isfinite(stack) & mask[None, :, :], axis=0)
    sums = np.nansum(masked_stack, axis=0)
    out = np.divide(sums, valid_counts, out=np.full(mask.shape, np.nan, dtype="float32"), where=valid_counts > 0)
    out[~mask] = np.nan
    return out.astype("float32")


def fill_inside(data: np.ndarray, mask: np.ndarray, value: float) -> np.ndarray:
    out = data.copy()
    out[mask & ~np.isfinite(out)] = value
    return out
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    profile, _geometry, mask = read_reference()
    rasters = {name: read_band(path, profile) for name, path in INPUTS.items()}

    structure, structure_p02, structure_p98 = normalize_2_98(rasters["structure"], mask)
    structure = fill_inside(structure, mask, 0.0)
    c_pressure, c_p02, c_p98 = normalize_2_98(rasters["c_factor"], mask)

    criteria_arrays = {
        "flood_hydrology": average_layers([rasters["twi"], rasters["drainage"]], mask),
        "sediment_structure": structure,
        "landuse_asm_pressure": average_layers([c_pressure, rasters["mining"]], mask),
        "environmental_sensitivity": rasters["rivers"].copy(),
        "socioeconomic_exposure": rasters["roads"].copy(),
    }

    manifest_rows: list[dict[str, object]] = []
    for name in CRITERIA:
        path = CRITERIA_DIR / f"{name}_0_1.tif"
        arr = np.clip(criteria_arrays[name], 0.0, 1.0)
        arr[~mask] = np.nan
        write_raster(path, arr, profile)
        row = {
            "criterion": name,
            "path": rel(path),
            "components": {
                "flood_hydrology": "TWI high-wetness; drainage proximity",
                "sediment_structure": "safe a_structure_K_LS_C_30m standardized 2-98 percentile; V1-internal NoData filled with 0",
                "landuse_asm_pressure": "C-factor pressure; OSM mining-proxy proximity",
                "environmental_sensitivity": "river/water proximity proxy",
                "socioeconomic_exposure": "road/access proximity proxy",
            }[name],
            "status": "provisional autonomous prototype criterion",
            "grid_compatible": "true",
            **stats(arr, mask),
        }
        manifest_rows.append(row)

    readiness_rows = manifest_rows + [
        {
            "criterion": "rainfall_r_factor",
            "path": "",
            "components": "CHIRPS/ERA5/Voi evidence only",
            "status": "uncertainty module, not a 30 m criterion in v0.1",
            "grid_compatible": "not_applicable",
            "limitation": "R magnitude affects sediment interpretation; scalar R does not change hotspot ranking.",
        },
        {
            "criterion": "population_exposure",
            "path": "outputs/v1_full_methodology_evidence_sweep/rasters/v1_worldpop_2020_unadj_native.tif",
            "components": "WorldPop native grid",
            "status": "context only in v0.1",
            "grid_compatible": "false",
            "limitation": "not on the V1 30 m reference grid; do not force into pixel overlay.",
        },
        {
            "criterion": "protected_area_context",
            "path": "outputs/v1_full_methodology_evidence_sweep/v1_wdpca_protected_area_summary.csv",
            "components": "WDPCA summary",
            "status": "context only in v0.1",
            "grid_compatible": "not_raster",
            "limitation": "environmental context without accepted weighting rule.",
        },
    ]
    write_csv(OUT_DIR / "criteria_stack_manifest.csv", manifest_rows)
    write_csv(OUT_DIR / "criteria_readiness_table.csv", readiness_rows)
    write_csv(
        OUT_DIR / "criteria_standardization_notes.csv",
        [
            {"component": "sediment_structure", "method": "percentile_clip_minmax_2_98", "clip_low": structure_p02, "clip_high": structure_p98},
            {"component": "c_factor_pressure", "method": "percentile_clip_minmax_2_98", "clip_low": c_p02, "clip_high": c_p98},
        ],
    )
    print(f"wrote {len(manifest_rows)} criteria to {rel(CRITERIA_DIR)}")


if __name__ == "__main__":
    main()
