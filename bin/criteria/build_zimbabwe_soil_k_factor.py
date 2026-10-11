#!/usr/bin/env python3
"""Align the corrected V1 SoilGrids K-factor to the overlay grid."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))
from _lib.standardization import percentile_minmax

SOURCE = ROOT / "outputs/zimbabwe_soilgrids_k_factor/k_factor_0_5cm_250m.tif"
REFERENCE = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif"
BOUNDARY = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
OUT_DIR = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/soil_k_factor"
ALIGNED = OUT_DIR / "soil_k_factor_aligned_250m_effective_30m.tif"
SCORED = OUT_DIR / "soil_k_factor_0_1.tif"
MANIFEST = OUT_DIR / "soil_k_factor_manifest.csv"

INPUTS = [SOURCE, REFERENCE, BOUNDARY]
OUTPUTS = [ALIGNED, SCORED, MANIFEST]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


# Backwards-compatible name used by the existing tests and manifests.  The
# implementation is centralized in ``bin/_lib/standardization.py``.
normalize_within_boundary = percentile_minmax


def write_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    target = profile.copy()
    target.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)
    with rasterio.open(path, "w", **target) as dst:
        dst.write(np.where(np.isfinite(data), data, -9999.0).astype("float32"), 1)
        dst.update_tags(
            IFPM_NOTE=(
                "SoilGrids native 250 m K aligned to the V1 30 m grid for overlay compatibility; "
                "effective information resolution remains 250 m."
            )
        )


def main() -> None:
    for path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(REFERENCE) as ref:
        profile = ref.profile.copy()
        shape = (ref.height, ref.width)
    boundary = gpd.read_file(BOUNDARY, layer="v1_working_boundary").to_crs(profile["crs"])
    inside = geometry_mask(
        boundary.geometry,
        out_shape=shape,
        transform=profile["transform"],
        invert=True,
        all_touched=True,
    )

    aligned = np.full(shape, np.nan, dtype="float32")
    with rasterio.open(SOURCE) as src:
        source_resolution = [abs(float(src.transform.a)), abs(float(src.transform.e))]
        reproject(
            source=rasterio.band(src, 1), destination=aligned,
            src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
            dst_transform=profile["transform"], dst_crs=profile["crs"], dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
    aligned[~inside] = np.nan
    score, low, high = normalize_within_boundary(aligned, inside)
    write_raster(ALIGNED, aligned, profile)
    write_raster(SCORED, score, profile)

    valid = inside & np.isfinite(score)
    rows = [{
        "criterion": "soil_k_factor", "source": rel(SOURCE),
        "source_sha256": sha256(SOURCE),
        "reference_sha256": sha256(REFERENCE), "boundary_sha256": sha256(BOUNDARY),
        "source_resolution_m": "x".join(str(int(value)) for value in source_resolution),
        "target_grid": "EPSG:32735 30 m", "resampling": "bilinear",
        "effective_resolution_warning": "aligned cells remain 250 m SoilGrids evidence",
        "normalization": "V1 boundary 2-98 percentile min-max",
        "clip_low_k_us": round(low, 8), "clip_high_k_us": round(high, 8),
        "valid_fraction": round(float(valid.sum() / inside.sum()), 6),
        "claim_level": "provisional",
        "nodata_policy": "preserve source and boundary NoData; no zero fill",
        "aligned_sha256": sha256(ALIGNED), "score_sha256": sha256(SCORED),
    }]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote V1 SoilGrids K criterion to {rel(SCORED)}")


if __name__ == "__main__":
    main()
