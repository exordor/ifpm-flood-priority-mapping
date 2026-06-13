#!/usr/bin/env python3
"""Derive V1 slope in degrees from the buffered SRTM DEM."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window, transform as window_transform


ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "srtm_1arcsec_zimbabwe_prototype"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
BUFFERED_DEM = OUT_DIR / "v1_dem_buffered_utm35s_30m.tif"
V1_DEM = OUT_DIR / "v1_dem_utm35s_30m.tif"
SLOPE = OUT_DIR / "v1_slope_degrees_utm35s_30m.tif"
DST_CRS = "EPSG:32735"
NODATA = -9999.0


def load_v1() -> object:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(DST_CRS)
    if len(boundary) != 1:
        raise ValueError("Expected one V1 boundary")
    return boundary.geometry.iloc[0]


def crop_to_geometry(data: np.ndarray, transform, geometry) -> tuple[np.ndarray, object]:
    mask = geometry_mask([geometry], out_shape=data.shape, transform=transform, invert=True)
    rows, cols = np.where(mask)
    if rows.size == 0 or cols.size == 0:
        raise ValueError("Geometry does not intersect slope grid")
    row_start, row_stop = rows.min(), rows.max() + 1
    col_start, col_stop = cols.min(), cols.max() + 1
    window = Window.from_slices((row_start, row_stop), (col_start, col_stop))
    cropped = data[row_start:row_stop, col_start:col_stop].copy()
    cropped_mask = mask[row_start:row_stop, col_start:col_stop]
    cropped[~cropped_mask] = NODATA
    return cropped.astype("float32"), window_transform(window, transform)


def derive_slope(dem: np.ndarray, res_x: float, res_y: float) -> np.ndarray:
    values = dem.astype("float64")
    values[values == NODATA] = np.nan
    grad_y, grad_x = np.gradient(values, abs(res_y), abs(res_x))
    slope = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))
    slope[~np.isfinite(slope)] = NODATA
    return slope.astype("float32")


def write_slope(data: np.ndarray, transform, reference_profile: dict) -> None:
    profile = reference_profile.copy()
    profile.update(
        {
            "driver": "GTiff",
            "height": data.shape[0],
            "width": data.shape[1],
            "count": 1,
            "dtype": "float32",
            "transform": transform,
            "nodata": NODATA,
            "compress": "deflate",
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        }
    )
    with rasterio.open(SLOPE, "w", **profile) as dst:
        dst.write(data, 1)


def assert_matches_dem() -> None:
    with rasterio.open(V1_DEM) as dem, rasterio.open(SLOPE) as slope:
        if dem.crs != slope.crs or dem.transform != slope.transform or dem.shape != slope.shape:
            raise ValueError("Slope raster does not match V1 DEM grid")


def main() -> None:
    geometry = load_v1()
    with rasterio.open(BUFFERED_DEM) as src:
        if str(src.crs) != DST_CRS:
            raise ValueError(f"Expected {DST_CRS}, got {src.crs}")
        dem = src.read(1).astype("float32")
        slope_buffered = derive_slope(dem, src.res[0], src.res[1])
        slope_v1, slope_transform = crop_to_geometry(slope_buffered, src.transform, geometry)
        write_slope(slope_v1, slope_transform, src.profile)
    assert_matches_dem()
    print(f"wrote {SLOPE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
