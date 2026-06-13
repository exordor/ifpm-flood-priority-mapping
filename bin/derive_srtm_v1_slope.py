#!/usr/bin/env python3
"""Derive V1 slope in degrees from the buffered SRTM DEM."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.fill import fillnodata
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
    """Slope in degrees via central finite differences (numpy gradient).

    NoData cells (the out-of-buffer apron AND any real SRTM voids) are filled with
    inverse-distance interpolation *before* differencing so that a single void cannot
    widen into a 3x3 NaN halo: np.gradient needs both neighbours of every cell, so an
    unfilled void forces NaN at itself and its 8 neighbours. Originally-NoData cells
    are returned to NoData in the output (we claim no slope for filled cells); only
    their valid neighbours benefit from the fill.

    NOTE: this is a central-difference slope, NOT GDAL's Horn algorithm (gdaldem slope).
    For a 30 m SRTM cell the two are close but not bit-identical. The V1 AOI sits ~1 km
    (33 cells) inside the buffered DEM edge, so filling the out-of-buffer apron never
    alters any cell that reaches the final (V1-cropped) slope -- it only prevents edge
    halos. Real voids *within* V1, if present, are counted separately in main().
    """
    values = dem.astype("float64")
    nodata_mask = values == NODATA
    values[nodata_mask] = np.nan
    if nodata_mask.any():
        filled = fillnodata(values, mask=(~nodata_mask).astype("uint8"))
        values = np.where(nodata_mask, filled, values)
    grad_y, grad_x = np.gradient(values, abs(res_y), abs(res_x))
    slope = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))
    slope[nodata_mask] = NODATA  # do not claim slope for interpolated void cells
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
        nodata_total = int((dem == NODATA).sum())
        # How many NoData cells fall *inside* the V1 AOI? Those are real source
        # voids that would otherwise create 3x3 NaN halos in the final slope. The
        # remainder of the NoData is the out-of-buffer apron, which is discarded.
        v1_mask = geometry_mask([geometry], out_shape=dem.shape, transform=src.transform, invert=True)
        nodata_in_v1 = int(((dem == NODATA) & v1_mask).sum())
        slope_buffered = derive_slope(dem, src.res[0], src.res[1])
        slope_v1, slope_transform = crop_to_geometry(slope_buffered, src.transform, geometry)
        write_slope(slope_v1, slope_transform, src.profile)
    assert_matches_dem()
    print(f"wrote {SLOPE.relative_to(ROOT)}")
    print(
        f"buffered-DEM NoData filled before slope: {nodata_total} total "
        f"(inside V1 AOI: {nodata_in_v1}; remainder is the out-of-buffer apron). "
        f"Real SRTM voids in V1 = {nodata_in_v1}."
    )


if __name__ == "__main__":
    main()
