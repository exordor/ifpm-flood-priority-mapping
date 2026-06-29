#!/usr/bin/env python3
"""Derive PE1 slope in degrees from the buffered SRTM DEM.

Mirrors `derive_srtm_v1_slope.py`. Peru differences: PE1 boundary, EPSG:32718 (UTM 18S),
PE1 DEM paths. Logic (central-difference slope, NoData fill before differencing, crop to
boundary) is identical and grid-generic.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.fill import fillnodata
from rasterio.features import geometry_mask
from rasterio.windows import Window, transform as window_transform


ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "srtm_1arcsec_peru_pilot"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
BUFFERED_DEM = OUT_DIR / "pe1_dem_buffered_utm18s_30m.tif"
PE1_DEM = OUT_DIR / "pe1_dem_utm18s_30m.tif"
SLOPE = OUT_DIR / "pe1_slope_degrees_utm18s_30m.tif"
DST_CRS = "EPSG:32718"
NODATA = -9999.0


def load_pe1() -> object:
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(DST_CRS)
    if len(boundary) != 1:
        raise ValueError("Expected one PE1 boundary")
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
    """Slope in degrees via central finite differences (numpy gradient).

    NoData cells (out-of-buffer apron AND any real SRTM voids) are filled with
    inverse-distance interpolation before differencing so a single void cannot widen
    into a 3x3 NaN halo. Originally-NoData cells are returned to NoData in the output.
    """
    values = dem.astype("float64")
    nodata_mask = values == NODATA
    values[nodata_mask] = np.nan
    if nodata_mask.any():
        filled = fillnodata(values, mask=(~nodata_mask).astype("uint8"))
        values = np.where(nodata_mask, filled, values)
    grad_y, grad_x = np.gradient(values, abs(res_y), abs(res_x))
    slope = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))
    slope[nodata_mask] = NODATA
    slope[~np.isfinite(slope)] = NODATA
    return slope.astype("float32")


def write_slope(data: np.ndarray, transform, reference_profile: dict) -> None:
    profile = reference_profile.copy()
    profile.update({
        "driver": "GTiff", "height": data.shape[0], "width": data.shape[1],
        "count": 1, "dtype": "float32", "transform": transform, "nodata": NODATA,
        "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
    })
    with rasterio.open(SLOPE, "w", **profile) as dst:
        dst.write(data, 1)


def assert_matches_dem() -> None:
    with rasterio.open(PE1_DEM) as dem, rasterio.open(SLOPE) as slope:
        if dem.crs != slope.crs or dem.transform != slope.transform or dem.shape != slope.shape:
            raise ValueError("Slope raster does not match PE1 DEM grid")


def main() -> None:
    geometry = load_pe1()
    with rasterio.open(BUFFERED_DEM) as src:
        if str(src.crs) != DST_CRS:
            raise ValueError(f"Expected {DST_CRS}, got {src.crs}")
        dem = src.read(1).astype("float32")
        nodata_total = int((dem == NODATA).sum())
        pe1_mask = geometry_mask([geometry], out_shape=dem.shape, transform=src.transform, invert=True)
        nodata_in_pe1 = int(((dem == NODATA) & pe1_mask).sum())
        slope_buffered = derive_slope(dem, src.res[0], src.res[1])
        slope_pe1, slope_transform = crop_to_geometry(slope_buffered, src.transform, geometry)
        write_slope(slope_pe1, slope_transform, src.profile)
    assert_matches_dem()
    valid = slope_pe1[slope_pe1 != NODATA]
    print(f"wrote {SLOPE.relative_to(ROOT)}")
    print(f"buffered-DEM NoData filled before slope: {nodata_total} total "
          f"(inside PE1 AOI: {nodata_in_pe1}; real SRTM voids in PE1 = {nodata_in_pe1}).")
    if valid.size:
        print(f"PE1 slope: {float(valid.min()):.2f}-{float(valid.max()):.2f} deg, "
              f"mean {float(valid.mean()):.2f}, valid {valid.size}")


if __name__ == "__main__":
    main()
