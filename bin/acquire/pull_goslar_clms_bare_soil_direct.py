#!/usr/bin/env python3
"""Download and prepare CLMS HRL Bare Soil After 2024 for the WRRL window."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import boto3
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/raw/clms_hrl_bare_soil_goslar_official_basin"
OUTPUT_DIR = ROOT / "outputs/goslar_esa_worldcover_2021/c_factor"
DIAGNOSTICS = ROOT / "outputs/goslar_esa_worldcover_2021/c_factor/clms_bare_soil_after_2024_diagnostics.json"
REF = ROOT / "outputs/goslar_pim_chain/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif"
BOUNDARY = ROOT / "outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg"
CREDENTIALS = ROOT / "data/tmp/cdse_s3_credentials.json"

PREFIX = "CLMS/landcover_landuse/cropping_patterns/clms_vlcc_bare-soil-after_europe_10m_yearly_v1/{year}/01/01/"
TILES = ("E43N31", "E43N32")
YEARS = tuple(range(2017, 2025))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_tiles(year: int) -> list[Path]:
    credentials = json.loads(CREDENTIALS.read_text())
    client = boto3.client(
        "s3",
        endpoint_url=credentials["endpoint"],
        aws_access_key_id=credentials["access_key"],
        aws_secret_access_key=credentials["secret_key"],
        region_name=credentials["region"],
    )
    paths = []
    for tile in TILES:
        stem = f"CLMS_HRLVLCC_CPBSA_S{year}_R10m_{tile}_03035_V01_R00"
        key = f"{PREFIX.format(year=year)}{stem}/{stem}.tif"
        target = BASE / str(year) / f"{stem}.tif"
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            client.download_file("eodata", key, str(target))
        paths.append(target)
    return paths


def build_mosaic(paths: list[Path], year: int) -> Path:
    datasets = [rasterio.open(path) for path in paths]
    try:
        ref = datasets[0]
        left = min(ds.bounds.left for ds in datasets)
        right = max(ds.bounds.right for ds in datasets)
        bottom = min(ds.bounds.bottom for ds in datasets)
        top = max(ds.bounds.top for ds in datasets)
        resolution = ref.res[0]
        width = round((right - left) / resolution)
        height = round((top - bottom) / resolution)
        mosaic = np.full((height, width), 255, dtype=ref.dtypes[0])
        transform = from_bounds(left, bottom, right, top, width, height)
        for ds in datasets:
            row = round((top - ds.bounds.top) / resolution)
            col = round((ds.bounds.left - left) / resolution)
            data = ds.read(1)
            mosaic[row : row + data.shape[0], col : col + data.shape[1]] = data
        profile = ref.profile.copy()
        profile.update(height=height, width=width, transform=transform, compress="deflate", tiled=True)
        target = BASE / str(year) / f"goslar_official_basin_bare_soil_after_{year}_10m_mosaic.tif"
        with rasterio.open(target, "w", **profile) as dst:
            dst.write(mosaic, 1)
    finally:
        for ds in datasets:
            ds.close()
        return target


def normalize_to_reference(mosaic: Path) -> dict:
    mosaic_diagnostics = []
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(mosaic) as src, rasterio.open(REF) as ref:
        raw = src.read(1).astype("float32")
        raw[(raw < 0) | (raw > 100) | (raw >= 65500)] = np.nan
        target_grid = np.full((ref.height, ref.width), np.nan, dtype="float32")
        reproject(
            raw, target_grid, src_transform=src.transform, src_crs=src.crs,
            dst_transform=ref.transform, dst_crs=ref.crs,
            resampling=Resampling.average, dst_nodata=np.nan,
        )
        boundary = gpd.read_file(BOUNDARY).to_crs(ref.crs)
        mask = geometry_mask(
            [boundary.geometry.union_all()], out_shape=(ref.height, ref.width),
            transform=ref.transform, invert=True,
        )
        valid = mask & np.isfinite(target_grid)
        values = target_grid[valid]
        if values.size == 0:
            raise RuntimeError("no valid CLMS Bare Soil After cells inside boundary")
        low, high = np.percentile(values, [2, 98])
        score = np.clip((target_grid - low) / (high - low), 0, 1)
        score[~mask] = np.nan
        profile = ref.profile.copy()
        profile.update(dtype="float32", nodata=-9999, compress="deflate", tiled=True)
        target = OUTPUT_DIR / f"clms_bare_soil_after_{mosaic.parent.name}_goslar_official_basin_30m.tif"
        with rasterio.open(target, "w", **profile) as dst:
            dst.write(np.where(np.isfinite(score), score, -9999).astype("float32"), 1)
        return {
            "source": str(mosaic.relative_to(ROOT)),
            "output": str(target.relative_to(ROOT)),
            "native_resolution_m": 10,
            "target_resolution_m": 30,
            "resampling": "average then 2-98 percentile min-max",
            "valid_fraction": float(valid.sum() / mask.sum()),
            "p2": float(low),
            "p98": float(high),
            "mean_raw_percent_year": float(values.mean()),
            "nonzero_fraction": float(np.mean(values > 0)),
            "sha256": sha256(target),
            "access_date": date.today().isoformat(),
            "claim": "provisional indicator input; Copernicus HRL Bare Soil After 2024",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    args = parser.parse_args()
    all_diagnostics = {}
    for year in args.years:
        year_dir = BASE / str(year)
        paths = [year_dir / f"CLMS_HRLVLCC_CPBSA_S{year}_R10m_{tile}_03035_V01_R00.tif" for tile in TILES]
        if not all(path.exists() for path in paths):
            paths = download_tiles(year)
        mosaic = build_mosaic(paths, year)
        all_diagnostics[str(year)] = normalize_to_reference(mosaic)
    DIAGNOSTICS.parent.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "clms_bare_soil_after_series_diagnostics.json").write_text(json.dumps(all_diagnostics, indent=2) + "\n")
    print(json.dumps(all_diagnostics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
