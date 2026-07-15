#!/usr/bin/env python3
"""Derive Arequipa Region slope in degrees from the buffered SRTM DEM.

Mirrors `derive_srtm_v1_slope.py`. Peru differences: Arequipa Region boundary, EPSG:32718 (UTM 18S),
Arequipa Region DEM paths. Logic (central-difference slope, NoData fill before differencing, crop to
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


ROOT = Path(__file__).resolve().parents[2]
INPUTS = [ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif", ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_slope_degrees_utm18s_30m.tif"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import load_boundary
DATASET_ID = "srtm_1arcsec_peru_pilot"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
PERU_HYBAS_L7_6070641200_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
BUFFERED_DEM = OUT_DIR / "peru_hybas_l7_6070641200_dem_buffered_utm18s_30m.tif"
PERU_HYBAS_L7_6070641200_DEM = OUT_DIR / "peru_hybas_l7_6070641200_dem_utm18s_30m.tif"
SLOPE = OUT_DIR / "peru_hybas_l7_6070641200_slope_degrees_utm18s_30m.tif"
DST_CRS = "EPSG:32718"
NODATA = -9999.0
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
    with rasterio.open(PERU_HYBAS_L7_6070641200_DEM) as dem, rasterio.open(SLOPE) as slope:
        if dem.crs != slope.crs or dem.transform != slope.transform or dem.shape != slope.shape:
            raise ValueError("Slope raster does not match Arequipa Region DEM grid")


def main() -> None:
    geometry = load_boundary(PERU_HYBAS_L7_6070641200_GPKG, "peru_pilot_boundary", DST_CRS)
    with rasterio.open(BUFFERED_DEM) as src:
        if str(src.crs) != DST_CRS:
            raise ValueError(f"Expected {DST_CRS}, got {src.crs}")
        dem = src.read(1).astype("float32")
        nodata_total = int((dem == NODATA).sum())
        peru_hybas_l7_6070641200_mask = geometry_mask([geometry], out_shape=dem.shape, transform=src.transform, invert=True)
        nodata_in_peru_hybas_l7_6070641200 = int(((dem == NODATA) & peru_hybas_l7_6070641200_mask).sum())
        slope_buffered = derive_slope(dem, src.res[0], src.res[1])
        slope_peru_hybas_l7_6070641200, slope_transform = crop_to_geometry(slope_buffered, src.transform, geometry)
        write_slope(slope_peru_hybas_l7_6070641200, slope_transform, src.profile)
    assert_matches_dem()
    valid = slope_peru_hybas_l7_6070641200[slope_peru_hybas_l7_6070641200 != NODATA]
    print(f"wrote {SLOPE.relative_to(ROOT)}")
    print(f"buffered-DEM NoData filled before slope: {nodata_total} total "
          f"(inside Arequipa Region AOI: {nodata_in_peru_hybas_l7_6070641200}; real SRTM voids in Arequipa Region = {nodata_in_peru_hybas_l7_6070641200}).")
    if valid.size:
        print(f"Arequipa Region slope: {float(valid.min()):.2f}-{float(valid.max()):.2f} deg, "
              f"mean {float(valid.mean()):.2f}, valid {valid.size}")


if __name__ == "__main__":
    main()
