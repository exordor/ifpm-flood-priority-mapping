#!/usr/bin/env python3
"""Download CLMS HRL Tree Cover Density and derive 2018-2024 vegetation loss."""
from __future__ import annotations

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
BASE = ROOT / "data/raw/clms_hrl_tcd_goslar_official_basin"
OUTPUT_DIR = ROOT / "outputs/esa_worldcover_2021_goslar/c_factor"
REF = ROOT / "outputs/srtm_1arcsec_goslar/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif"
BOUNDARY = ROOT / "outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg"
CREDENTIALS = ROOT / "data/tmp/cdse_s3_credentials.json"
PREFIX = "CLMS/landcover_landuse/tree_cover_density/clms_vlcc_tree-cover-density_europe_10m_yearly_v1/{year}/01/01/"
TILES = ("E43N31", "E43N32")
YEARS = (2018, 2024)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(year: int) -> list[Path]:
    credentials = json.loads(CREDENTIALS.read_text())
    client = boto3.client(
        "s3", endpoint_url=credentials["endpoint"],
        aws_access_key_id=credentials["access_key"],
        aws_secret_access_key=credentials["secret_key"],
        region_name=credentials["region"],
    )
    paths = []
    for tile in TILES:
        stem = f"CLMS_HRLVLCC_TCD_S{year}_R10m_{tile}_03035_V01_R00"
        key = f"{PREFIX.format(year=year)}{stem}/{stem}.tif"
        target = BASE / str(year) / f"{stem}.tif"
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            client.download_file("eodata", key, str(target))
        paths.append(target)
    return paths


def mosaic(year: int) -> Path:
    paths = download(year)
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
        output = np.full((height, width), 255, dtype=ref.dtypes[0])
        transform = from_bounds(left, bottom, right, top, width, height)
        for ds in datasets:
            row = round((top - ds.bounds.top) / resolution)
            col = round((ds.bounds.left - left) / resolution)
            data = ds.read(1)
            output[row : row + data.shape[0], col : col + data.shape[1]] = data
        target = BASE / str(year) / f"goslar_official_basin_tcd_{year}_10m_mosaic.tif"
        profile = ref.profile.copy()
        profile.update(height=height, width=width, transform=transform, compress="deflate", tiled=True)
        with rasterio.open(target, "w", **profile) as dst:
            dst.write(output, 1)
        return target
    finally:
        for ds in datasets:
            ds.close()


def to_reference(year: int, source: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(source) as src, rasterio.open(REF) as ref:
        raw = src.read(1).astype("float32")
        raw[(raw < 0) | (raw > 100) | (raw >= 65500)] = np.nan
        output = np.full((ref.height, ref.width), np.nan, dtype="float32")
        reproject(
            raw, output, src_transform=src.transform, src_crs=src.crs,
            dst_transform=ref.transform, dst_crs=ref.crs,
            resampling=Resampling.average, dst_nodata=np.nan,
        )
        boundary = gpd.read_file(BOUNDARY).to_crs(ref.crs)
        mask = geometry_mask(
            [boundary.geometry.union_all()], out_shape=(ref.height, ref.width),
            transform=ref.transform, invert=True,
        )
        valid = mask & np.isfinite(output)
        output[~valid] = np.nan
        stats = {
            "source": str(source.relative_to(ROOT)),
            "valid_fraction": float(valid.sum() / mask.sum()),
            "mean_percent": float(np.nanmean(output)) if valid.any() else None,
            "p2_percent": float(np.percentile(output[valid], 2)) if valid.any() else None,
            "p98_percent": float(np.percentile(output[valid], 98)) if valid.any() else None,
        }
        return output, stats


def main() -> int:
    arrays = {}
    stats = {}
    for year in YEARS:
        source = mosaic(year)
        arrays[year], stats[str(year)] = to_reference(year, source)
    common = np.isfinite(arrays[2018]) & np.isfinite(arrays[2024])
    loss = np.clip((arrays[2018] - arrays[2024]) / 100.0, 0, 1)
    loss[~common] = np.nan
    output_path = OUTPUT_DIR / "clms_tcd_vegetation_loss_2018_2024_goslar_official_basin_30m.tif"
    with rasterio.open(REF) as ref:
        profile = ref.profile.copy()
        profile.update(dtype="float32", nodata=-9999, compress="deflate", tiled=True)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(np.where(np.isfinite(loss), loss, -9999).astype("float32"), 1)
    result = {
        "claim_level": "provisional",
        "method": "positive percent-point TCD decline from 2018 to 2024, divided by 100",
        "years": list(YEARS),
        "annual_stats": stats,
        "output": str(output_path.relative_to(ROOT)),
        "sha256": sha256(output_path),
        "valid_cells": int(np.isfinite(loss).sum()),
        "nonzero_cells": int(np.sum(loss > 0)),
        "mean_loss": float(np.nanmean(loss)),
        "access_date": date.today().isoformat(),
        "limitation": "TCD decline is a candidate vegetation-loss proxy, not a validated forest-loss product",
    }
    (OUTPUT_DIR / "clms_tcd_vegetation_loss_diagnostics.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
