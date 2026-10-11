"""Soil erodibility (K factor) from the pinned local SoilGrids snapshot.

Ported from stage_soilgrids_kfactor in bin/factors/run_goslar_pim_chain.py.
"""

from __future__ import annotations

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject


def stage_soilgrids_kfactor(ctx) -> None:
    """K (Williams 1995, US units, 0-30 cm) -> SI, nearest to the 30 m grid, 2-98 scaled.

    The snapshot is made by the area's SoilGrids acquire script with a recorded SHA-256.
    NoData stays NaN (it is not filled with 0).
    """
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    ctx.mkdir(ctx.p["K_DIR"])
    snapshot = ctx.p["SOILGRIDS_K_SNAPSHOT"]
    if not snapshot.exists():
        raise FileNotFoundError(f"SoilGrids K snapshot missing: {snapshot}. Run the SoilGrids acquire script first.")
    with rasterio.open(snapshot) as src:
        k_us = src.read(1).astype("float32")
        src_transform, src_crs = src.transform, src.crs
        if src.nodata is not None:
            k_us[k_us == src.nodata] = np.nan
    k_si = k_us * ctx.cfg["k_si_factor"]
    # 250 m source on the 30 m grid (effective resolution stays 250 m).
    dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    reproject(
        source=k_si, destination=dst,
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=ref["transform"], dst_crs=ref["crs"],
        src_nodata=np.nan, dst_nodata=np.nan,
        resampling=Resampling.nearest,
    )
    dst[~mask] = np.nan
    ctx.write_raster(ctx.p["K_ALIGNED"], np.where(np.isfinite(dst), dst, ctx.nodata), ref["transform"], ref["crs"])
    valid = dst[mask & np.isfinite(dst)]
    if valid.size == 0:
        raise RuntimeError("no valid SoilGrids K cells after snapshot read")
    scored, low, high = ctx.normalize(dst, mask, constant_policy="error")
    ctx.write_raster(ctx.p["K_SCORED"], np.where(np.isfinite(scored), scored, ctx.nodata), ref["transform"], ref["crs"])
