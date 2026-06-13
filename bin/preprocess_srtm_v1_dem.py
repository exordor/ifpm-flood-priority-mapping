#!/usr/bin/env python3
"""Mosaic, reproject, and clip SRTMGL1 tiles for the V1 terrain prototype."""

from __future__ import annotations

import zipfile
from contextlib import ExitStack
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.merge import merge
from rasterio.vrt import WarpedVRT
from rasterio.warp import Resampling
from rasterio.windows import Window, transform as window_transform


ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "srtm_1arcsec_zimbabwe_prototype"
RAW_DIR = ROOT / f"data/raw/{DATASET_ID}"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
BUFFERED_DEM = OUT_DIR / "v1_dem_buffered_utm35s_30m.tif"
V1_DEM = OUT_DIR / "v1_dem_utm35s_30m.tif"
EXPECTED_TILES = ["S22E028", "S22E029", "S21E028", "S21E029", "S20E028", "S20E029"]
SRC_NODATA = -32768
DST_NODATA = -9999.0
DST_CRS = "EPSG:32735"
RES_M = 30.0
BUFFER_M = 1_000


def archive_for_tile(tile: str) -> Path:
    matches = sorted(RAW_DIR.glob(f"{tile}*.zip"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one ZIP archive for {tile}, found {len(matches)}")
    return matches[0]


def hgt_member(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".hgt")]
    if len(members) != 1:
        raise ValueError(f"Expected one .hgt member in {path.name}, found {members}")
    return members[0]


def raster_uri(path: Path) -> str:
    return f"zip://{path.resolve()}!{hgt_member(path)}"


def load_v1() -> gpd.GeoDataFrame:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(DST_CRS)
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected one non-empty V1 boundary")
    return boundary


def crop_to_geometry(data: np.ndarray, transform, geometry) -> tuple[np.ndarray, object]:
    mask = geometry_mask([geometry], out_shape=data.shape, transform=transform, invert=True)
    rows, cols = np.where(mask)
    if rows.size == 0 or cols.size == 0:
        raise ValueError("Geometry does not intersect DEM grid")
    row_start, row_stop = rows.min(), rows.max() + 1
    col_start, col_stop = cols.min(), cols.max() + 1
    window = Window.from_slices((row_start, row_stop), (col_start, col_stop))
    cropped = data[row_start:row_stop, col_start:col_stop].copy()
    cropped_mask = mask[row_start:row_stop, col_start:col_stop]
    cropped[~cropped_mask] = DST_NODATA
    return cropped.astype("float32"), window_transform(window, transform)


def write_raster(path: Path, data: np.ndarray, transform, crs: str) -> None:
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": DST_NODATA,
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)


def build_buffered_mosaic(v1: gpd.GeoDataFrame) -> tuple[np.ndarray, object]:
    buffered = v1.geometry.iloc[0].buffer(BUFFER_M)
    bounds = buffered.bounds
    with ExitStack() as stack:
        sources = [stack.enter_context(rasterio.open(raster_uri(archive_for_tile(tile)))) for tile in EXPECTED_TILES]
        for src in sources:
            if src.count != 1 or str(src.crs) != "EPSG:4326":
                raise ValueError(f"Unexpected SRTM source profile: {src.name}")
        vrts = [
            stack.enter_context(
                WarpedVRT(
                    src,
                    crs=DST_CRS,
                    resampling=Resampling.bilinear,
                    src_nodata=SRC_NODATA,
                    nodata=DST_NODATA,
                    dtype="float32",
                )
            )
            for src in sources
        ]
        mosaic, transform = merge(
            vrts,
            bounds=bounds,
            res=(RES_M, RES_M),
            nodata=DST_NODATA,
            dtype="float32",
        )
    data = mosaic[0].astype("float32")
    buffer_mask = geometry_mask([buffered], out_shape=data.shape, transform=transform, invert=True)
    data[~buffer_mask] = DST_NODATA
    return data, transform


def main() -> None:
    v1 = load_v1()
    buffered_data, buffered_transform = build_buffered_mosaic(v1)
    write_raster(BUFFERED_DEM, buffered_data, buffered_transform, DST_CRS)

    v1_data, v1_transform = crop_to_geometry(buffered_data, buffered_transform, v1.geometry.iloc[0])
    write_raster(V1_DEM, v1_data, v1_transform, DST_CRS)

    print(f"wrote {BUFFERED_DEM.relative_to(ROOT)}")
    print(f"wrote {V1_DEM.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
