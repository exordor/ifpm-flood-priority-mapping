"""ESA WorldCover lookup layers (C factor, land-use pressures) and CLMS tree-cover loss.

Ported from stage_worldcover_cfactor in bin/factors/run_goslar_pim_chain.py and the
land-cover steps of the two Goslar extent wrappers.
"""

from __future__ import annotations

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

# Output path key (ctx.p) -> lookup table name in the area config (luts:).
LUT_LAYERS = {
    "CFACTOR": "c_factor",
    "LAND_USE_PRESSURE": "land_use_pressure",
    "LAND_COVER_RUNOFF": "land_cover_runoff_pressure",
    "BARE_SOIL_LOSS": "bare_soil_vegetation_loss",
    "BUILT_UP_PRESSURE": "built_up_pressure",
    "AGRICULTURAL_PRESSURE": "agricultural_pressure",
}


def map_classes(classes: np.ndarray, lut: dict) -> np.ndarray:
    """float32 values for the classes in ``lut``; all other cells (incl. NoData) stay NaN."""
    out = np.full(classes.shape, np.nan, dtype="float32")
    for class_id, value in lut.items():
        out[classes == class_id] = value
    return out


def stage_worldcover_cfactor(ctx) -> None:
    """Map WorldCover classes at 10 m, then nearest-resample each layer to the 30 m grid."""
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    with rasterio.open(ctx.p["WORLDCOVER_FILE"]) as src:
        data = src.read(1)
        src_transform, src_crs = src.transform, src.crs
    for key, lut_name in LUT_LAYERS.items():
        dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
        reproject(
            source=map_classes(data, ctx.cfg["luts"][lut_name]),
            destination=dst,
            src_transform=src_transform, src_crs=src_crs,
            dst_transform=ref["transform"], dst_crs=ref["crs"],
            src_nodata=np.nan, dst_nodata=np.nan,
            resampling=Resampling.nearest,
        )
        dst[~mask] = np.nan
        ctx.write_raster(ctx.p[key], np.where(np.isfinite(dst), dst, ctx.nodata), ref["transform"], ref["crs"])


def tcd_loss(tcd_early: np.ndarray, tcd_late: np.ndarray) -> np.ndarray:
    """Positive tree-cover-density decline as a 0-1 fraction (TCD values are percent)."""
    return np.clip((tcd_early - tcd_late) / 100, 0, 1)
