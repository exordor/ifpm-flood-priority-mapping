#!/usr/bin/env python3
"""Mosaic, reproject, and clip SRTMGL1 tiles for the southern Peru Arequipa Region catchment.

Mirrors `preprocess_zimbabwe_srtm_dem.py`. Peru differences:
- 2 tiles (S17W073, S17W072), not 6;
- DST_CRS = EPSG:32718 (UTM 18S, southern Peru), NOT Zimbabwe's UTM 35S;
- clips to the Arequipa Region boundary.

The clipped output `peru_former_dem_utm18s_30m.tif` becomes the Peru reference grid (the analogue of
the Zimbabwe `zimbabwe_dem_utm35s_30m.tif` reference). A separate Peru reference-grid rule will be
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
INPUTS = [ROOT / "outputs/peru_former_boundary/peru_former_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/peru_former_pim_chain/terrain_preprocessing/peru_former_dem_utm18s_30m.tif"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster
from _lib.ifpm_tools import load_boundary_df
DATASET_ID = "srtm_1arcsec_peru_former"
OUTPUT_ROOT_ID = "peru_former_pim_chain"  # outputs folder name (differs from the id since 2026-10-11 rename)
RAW_DIR = ROOT / f"data/raw/{DATASET_ID}"
OUT_DIR = ROOT / f"outputs/{OUTPUT_ROOT_ID}/terrain_preprocessing"
PERU_HYBAS_L7_6070641200_GPKG = ROOT / "outputs/peru_former_boundary/peru_former_boundary.gpkg"
BUFFERED_DEM = OUT_DIR / "peru_former_dem_buffered_utm18s_30m.tif"
PERU_HYBAS_L7_6070641200_DEM = OUT_DIR / "peru_former_dem_utm18s_30m.tif"
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
def _output_grid(bounds: tuple, res: float) -> tuple[object, int, int]:
    west, south, east, north = bounds
    width = int(round((east - west) / res))
    height = int(round((north - south) / res))
    return from_origin(west, north, res, res), width, height


def build_buffered_mosaic(peru_former: gpd.GeoDataFrame) -> tuple[np.ndarray, object]:
    buffered = peru_former.geometry.iloc[0].buffer(BUFFER_M)
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
    peru_former = load_boundary_df(PERU_HYBAS_L7_6070641200_GPKG, "peru_pilot_boundary", DST_CRS)
    buffered_data, buffered_transform = build_buffered_mosaic(peru_former)
    write_raster(BUFFERED_DEM, buffered_data, transform=buffered_transform, crs=DST_CRS)

    peru_former_data, peru_former_transform = crop_to_geometry(buffered_data, buffered_transform, peru_former.geometry.iloc[0])
    write_raster(PERU_HYBAS_L7_6070641200_DEM, peru_former_data, transform=peru_former_transform, crs=DST_CRS)

    valid = peru_former_data[peru_former_data != DST_NODATA]
    print(f"wrote {BUFFERED_DEM.relative_to(ROOT)}")
    print(f"wrote {PERU_HYBAS_L7_6070641200_DEM.relative_to(ROOT)}")
    if valid.size:
        print(f"Arequipa Region DEM: CRS {DST_CRS}, res {RES_M} m, "
              f"shape {peru_former_data.shape}, "
              f"elevation {float(valid.min()):.1f}-{float(valid.max()):.1f} m, "
              f"valid cells {valid.size}")


if __name__ == "__main__":
    main()
