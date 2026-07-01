#!/usr/bin/env python3
"""Mosaic, reproject, and clip SRTMGL1 tiles for the Peru engineering-pilot (PE1).

Mirrors `preprocess_srtm_v1_dem.py`. Peru differences:
- 2 tiles (S17W073, S17W072), not 6;
- DST_CRS = EPSG:32718 (UTM 18S, southern Peru), NOT Zimbabwe's UTM 35S;
- clips to the PE1 pilot boundary.

The clipped output `pe1_dem_utm18s_30m.tif` becomes the Peru reference grid (the analogue of
the Zimbabwe `v1_dem_utm35s_30m.tif` reference). A separate Peru reference-grid rule will be
written to record its CRS/transform/resolution so future Peru terrain derivatives must match it.
"""

from __future__ import annotations

import zipfile
from contextlib import ExitStack
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.merge import merge
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window, transform as window_transform


ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "srtm_1arcsec_peru_pilot"
RAW_DIR = ROOT / f"data/raw/{DATASET_ID}"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
BUFFERED_DEM = OUT_DIR / "pe1_dem_buffered_utm18s_30m.tif"
PE1_DEM = OUT_DIR / "pe1_dem_utm18s_30m.tif"
EXPECTED_TILES = ["S17W073", "S17W072"]
SRC_NODATA = -32768
DST_NODATA = -9999.0
DST_CRS = "EPSG:32718"
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


def load_pe1() -> gpd.GeoDataFrame:
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(DST_CRS)
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected one non-empty PE1 boundary")
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
        "driver": "GTiff", "height": data.shape[0], "width": data.shape[1],
        "count": 1, "dtype": "float32", "crs": crs, "transform": transform,
        "nodata": DST_NODATA, "compress": "deflate", "tiled": True,
        "blockxsize": 256, "blockysize": 256,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)


def _output_grid(bounds: tuple, res: float) -> tuple[object, int, int]:
    west, south, east, north = bounds
    width = int(round((east - west) / res))
    height = int(round((north - south) / res))
    return from_origin(west, north, res, res), width, height


def build_buffered_mosaic(pe1: gpd.GeoDataFrame) -> tuple[np.ndarray, object]:
    buffered = pe1.geometry.iloc[0].buffer(BUFFER_M)
    bounds = buffered.bounds
    dst_transform, dst_width, dst_height = _output_grid(bounds, RES_M)

    with ExitStack() as stack:
        sources = [stack.enter_context(rasterio.open(raster_uri(archive_for_tile(tile)))) for tile in EXPECTED_TILES]
        for src in sources:
            if src.count != 1 or str(src.crs) != "EPSG:4326":
                raise ValueError(f"Unexpected SRTM source profile: {src.name}")
        src_mosaic, src_transform = merge(sources)

    data = np.full((dst_height, dst_width), DST_NODATA, dtype="float32")
    reproject(
        source=src_mosaic[0], destination=data,
        src_transform=src_transform, src_crs="EPSG:4326", src_nodata=SRC_NODATA,
        dst_transform=dst_transform, dst_crs=DST_CRS, dst_nodata=DST_NODATA,
        resampling=Resampling.bilinear,
    )
    buffer_mask = geometry_mask([buffered], out_shape=data.shape, transform=dst_transform, invert=True)
    data[~buffer_mask] = DST_NODATA
    return data, dst_transform


def main() -> None:
    pe1 = load_pe1()
    buffered_data, buffered_transform = build_buffered_mosaic(pe1)
    write_raster(BUFFERED_DEM, buffered_data, buffered_transform, DST_CRS)

    pe1_data, pe1_transform = crop_to_geometry(buffered_data, buffered_transform, pe1.geometry.iloc[0])
    write_raster(PE1_DEM, pe1_data, pe1_transform, DST_CRS)

    valid = pe1_data[pe1_data != DST_NODATA]
    print(f"wrote {BUFFERED_DEM.relative_to(ROOT)}")
    print(f"wrote {PE1_DEM.relative_to(ROOT)}")
    if valid.size:
        print(f"PE1 DEM: CRS {DST_CRS}, res {RES_M} m, "
              f"shape {pe1_data.shape}, "
              f"elevation {float(valid.min()):.1f}-{float(valid.max()):.1f} m, "
              f"valid cells {valid.size}")


if __name__ == "__main__":
    main()
