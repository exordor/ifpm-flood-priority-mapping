#!/usr/bin/env python3
"""Align SoilGrids K to the PE1 overlay grid without claiming 30 m detail."""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/soilgrids_250m_peru_pilot/k_factor_pe1_0_5cm_250m.tif"
REFERENCE = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
OUT_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/soil_k_factor"
ALIGNED = OUT_DIR / "soil_k_factor_aligned_250m_effective_30m.tif"
SCORED = OUT_DIR / "soil_k_factor_0_1.tif"
MANIFEST = OUT_DIR / "soil_k_factor_manifest.csv"

INPUTS = [
    ROOT / "outputs/soilgrids_250m_peru_pilot/k_factor_pe1_0_5cm_250m.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]
OUTPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/soil_k_factor/soil_k_factor_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/soil_k_factor/soil_k_factor_manifest.csv",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def normalize_within_boundary(
    data: np.ndarray,
    inside: np.ndarray,
) -> tuple[np.ndarray, float, float]:
    valid = inside & np.isfinite(data)
    values = data[valid]
    if values.size == 0:
        raise ValueError("cannot normalize SoilGrids K without finite PE1 cells")
    low, high = np.percentile(values, [2.0, 98.0])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise ValueError(f"invalid SoilGrids K range: low={low}, high={high}")
    score = np.full(data.shape, np.nan, dtype="float32")
    score[valid] = np.clip((data[valid] - low) / (high - low), 0.0, 1.0).astype("float32")
    return score, float(low), float(high)


def write_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    output = np.where(np.isfinite(data), data, -9999.0).astype("float32")
    target = profile.copy()
    target.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)
    with rasterio.open(path, "w", **target) as dst:
        dst.write(output, 1)
        dst.update_tags(
            IFPM_NOTE=(
                "SoilGrids native 250 m K aligned to the PE1 30 m grid for overlay compatibility; "
                "effective information resolution remains 250 m."
            )
        )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(REFERENCE) as ref:
        profile = ref.profile.copy()
        shape = (ref.height, ref.width)
    boundary = gpd.read_file(BOUNDARY, layer="peru_pilot_boundary").to_crs(profile["crs"])
    inside = geometry_mask(
        boundary.geometry,
        out_shape=shape,
        transform=profile["transform"],
        invert=True,
    )

    aligned = np.full(shape, np.nan, dtype="float32")
    with rasterio.open(SOURCE) as src:
        source_resolution = [abs(float(src.transform.a)), abs(float(src.transform.e))]
        reproject(
            source=rasterio.band(src, 1),
            destination=aligned,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=profile["transform"],
            dst_crs=profile["crs"],
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
    aligned[~inside] = np.nan
    score, low, high = normalize_within_boundary(aligned, inside)
    write_raster(ALIGNED, aligned, profile)
    write_raster(SCORED, score, profile)

    valid = inside & np.isfinite(score)
    rows = [{
        "criterion": "soil_k_factor",
        "source": rel(SOURCE),
        "source_resolution_m": "x".join(str(int(value)) for value in source_resolution),
        "target_grid": "EPSG:32718 30 m",
        "resampling": "bilinear",
        "effective_resolution_warning": "aligned cells remain 250 m SoilGrids evidence",
        "normalization": "PE1 boundary 2-98 percentile min-max",
        "clip_low_k_us": round(low, 8),
        "clip_high_k_us": round(high, 8),
        "valid_fraction": round(float(valid.sum() / inside.sum()), 6),
        "claim_level": "provisional",
        "nodata_policy": "preserve source and boundary NoData; no zero fill",
    }]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote PE1 SoilGrids K criterion to {rel(SCORED)}")


if __name__ == "__main__":
    main()
