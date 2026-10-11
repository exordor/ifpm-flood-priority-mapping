"""DEM, slope, hydrology (WhiteboxTools) and the RUSLE LS factor.

Ported from the stage_dem / stage_slope / stage_hydrology / stage_ls_factor functions of
bin/factors/run_goslar_pim_chain.py and the SRTM stage_dem of run_secocha_pim_chain.py.
Every stage takes the run context ``ctx`` (see ifpm/chain.py); ``ctx.p`` holds the named
file paths that were module constants in the old scripts.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.fill import fillnodata
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window
from rasterio.windows import transform as window_transform


def run_wbt(tool_name: str, **kwargs) -> None:
    """Run one WhiteboxTools tool; raise when it reports failure."""
    import whitebox
    wbt = whitebox.WhiteboxTools()
    wbt.set_verbose_mode(False)
    tool = getattr(wbt, tool_name)
    rc = tool(**kwargs)
    if rc not in (True, 0):
        raise RuntimeError(f"whitebox {tool_name} failed (rc={rc}); args={kwargs}")


def _buffered_grid(ctx):
    """Metric grid covering the boundary plus the DEM buffer."""
    terrain = ctx.cfg["terrain"]
    bounds = ctx.boundary_geometry(ctx.crs).buffer(terrain["dem_buffer_m"]).bounds
    if terrain["grid_rounding"] == "round":
        width = int(round((bounds[2] - bounds[0]) / ctx.res))
        height = int(round((bounds[3] - bounds[1]) / ctx.res))
    else:
        width = int(np.ceil((bounds[2] - bounds[0]) / ctx.res))
        height = int(np.ceil((bounds[3] - bounds[1]) / ctx.res))
    return width, height, from_origin(bounds[0], bounds[3], ctx.res, ctx.res)


def _write_buffered_and_crop(ctx, buffered: np.ndarray, transform) -> None:
    """Write the buffered DEM, then the DEM cropped to the boundary bounding box and masked."""
    geometry = ctx.boundary_geometry(ctx.crs)
    ctx.write_raster(ctx.p["DEM_BUFFERED"], buffered, transform, ctx.crs)
    mask = geometry_mask([geometry], out_shape=buffered.shape, transform=transform, invert=True)
    rows, cols = np.where(mask)
    if rows.size == 0:
        raise ValueError("boundary does not intersect DEM grid")
    row0, row1 = rows.min(), rows.max() + 1
    col0, col1 = cols.min(), cols.max() + 1
    window = Window.from_slices((row0, row1), (col0, col1))
    cropped = buffered[row0:row1, col0:col1].copy()
    cropped[~mask[row0:row1, col0:col1]] = ctx.nodata
    ctx.write_raster(ctx.p["DEM"], cropped, window_transform(window, transform), ctx.crs)


def stage_dem(ctx) -> None:
    """Reproject the source DEM (bilinear) to the buffered metric grid; crop to the boundary."""
    ctx.mkdir(ctx.p["TERRAIN_DIR"])
    width, height, dst_transform = _buffered_grid(ctx)
    buffered = np.full((height, width), ctx.nodata, dtype="float32")
    method = ctx.cfg["terrain"]["dem_method"]
    source = ctx.p["DEM_SOURCE"]
    if not source.exists():
        raise FileNotFoundError(f"DEM missing: {source}")
    if method == "copernicus_tile":
        # One Copernicus GLO-30 tile in EPSG:4326.
        with rasterio.open(source) as src:
            if src.count != 1 or str(src.crs) != "EPSG:4326":
                raise ValueError(f"unexpected Copernicus DEM profile: {src.profile}")
            src_data, src_transform, src_nodata = src.read(1), src.transform, src.nodata
        reproject(
            source=src_data, destination=buffered,
            src_transform=src_transform, src_crs="EPSG:4326", src_nodata=src_nodata,
            dst_transform=dst_transform, dst_crs=ctx.crs, dst_nodata=ctx.nodata,
            resampling=Resampling.bilinear,
        )
    elif method == "srtm_zip":
        # SRTMGL1 .hgt read straight from the downloaded zip.
        member = ctx.cfg.entry(ctx.cfg["inputs"]["dem"])["member"]
        with rasterio.open(f"zip://{source.resolve()}!{member}") as src:
            reproject(
                source=src.read(1), destination=buffered,
                src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
                dst_transform=dst_transform, dst_crs=ctx.crs, dst_nodata=ctx.nodata,
                resampling=Resampling.bilinear,
            )
    else:
        raise ValueError(f"unknown dem_method: {method}")
    _write_buffered_and_crop(ctx, buffered, dst_transform)


def stage_slope(ctx) -> None:
    """Slope in degrees from the buffered DEM (NoData gaps filled first); buffered and cropped."""
    geometry = ctx.boundary_geometry(ctx.crs)
    with rasterio.open(ctx.p["DEM_BUFFERED"]) as src:
        dem = src.read(1).astype("float64")
        nodata_mask = dem == ctx.nodata
        values = dem.copy()
        values[nodata_mask] = np.nan
        if nodata_mask.any():
            filled = fillnodata(values, mask=(~nodata_mask).astype("uint8"))
            values = np.where(nodata_mask, filled, values)
        grad_y, grad_x = np.gradient(values, abs(src.res[1]), abs(src.res[0]))
        slope = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))
        slope[nodata_mask] = ctx.nodata
        slope[~np.isfinite(slope)] = ctx.nodata
        # The buffered slope feeds TWI, which needs upstream slope outside the boundary.
        ctx.write_raster(ctx.p["SLOPE_BUFFERED"], slope, src.transform, ctx.crs)
        mask = geometry_mask([geometry], out_shape=dem.shape, transform=src.transform, invert=True)
        rows, cols = np.where(mask)
        row0, row1 = rows.min(), rows.max() + 1
        col0, col1 = cols.min(), cols.max() + 1
        window = Window.from_slices((row0, row1), (col0, col1))
        cropped = slope[row0:row1, col0:col1].copy()
        cropped[~mask[row0:row1, col0:col1]] = ctx.nodata
        ctx.write_raster(ctx.p["SLOPE"], cropped, window_transform(window, src.transform), ctx.crs)


def normalize_to_reference(ctx, raw_path: Path, out_path: Path, ref: dict, mask: np.ndarray,
                           resampling=Resampling.bilinear) -> dict:
    """Reproject a buffered Whitebox output to the reference grid and mask it."""
    with rasterio.open(raw_path) as src:
        data = src.read(1).astype("float64")
        nodata = src.nodata
    if nodata is not None and not np.isnan(nodata):
        data[data == nodata] = np.nan
    data[np.isinf(data)] = np.nan
    out = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    dst_transform = ref["transform"]
    with rasterio.open(raw_path) as src:
        reproject(
            source=data, destination=out,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=dst_transform, dst_crs=ref["crs"], dst_nodata=np.nan,
            resampling=resampling,
        )
    out[~mask] = np.nan
    ctx.write_raster(out_path, np.where(np.isfinite(out), out, ctx.nodata), dst_transform, ref["crs"])
    inside = mask.sum()
    valid = np.isfinite(out) & mask
    values = out[valid]
    return {
        "valid_fraction": float(valid.sum() / inside) if inside else 0.0,
        "min": float(np.nanmin(values)) if values.size else None,
        "max": float(np.nanmax(values)) if values.size else None,
        "mean": float(np.nanmean(values)) if values.size else None,
    }


def stage_hydrology(ctx) -> None:
    """Fill, D8 pointer, flow accumulation, streams, distance to streams and TWI.

    Whitebox runs on the buffered DEM so flow accumulation keeps the upstream area outside
    the boundary; each result is then aligned to the reference grid and masked.
    """
    p = ctx.p
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    tmp = p["TMP_WBT"]
    ctx.mkdir(tmp)
    threshold = ctx.cfg["stream_threshold"]
    raw_filled = tmp / "filled.tif"
    run_wbt("fill_depressions_wang_and_liu", dem=str(p["DEM_BUFFERED"]), output=str(raw_filled), fix_flats=True)
    normalize_to_reference(ctx, raw_filled, p["FILLED"], ref, mask)

    raw_pntr = tmp / "d8pntr.tif"
    run_wbt("d8_pointer", dem=str(raw_filled), output=str(raw_pntr), esri_pntr=False)
    # The D8 pointer is categorical: nearest resampling keeps the codes.
    normalize_to_reference(ctx, raw_pntr, p["D8_PNTR"], ref, mask, resampling=Resampling.nearest)

    raw_acc_cells = tmp / "acc_cells.tif"
    run_wbt("d8_flow_accumulation", i=str(raw_pntr), output=str(raw_acc_cells),
            out_type="cells", pntr=True, esri_pntr=False)
    normalize_to_reference(ctx, raw_acc_cells, p["FLOW_ACC_CELLS"], ref, mask)

    raw_acc_sca = tmp / "acc_sca.tif"
    run_wbt("d8_flow_accumulation", i=str(raw_pntr), output=str(raw_acc_sca),
            out_type="specific contributing area", pntr=True, esri_pntr=False)
    normalize_to_reference(ctx, raw_acc_sca, p["FLOW_ACC_SCA"], ref, mask)

    # Streams from the buffered accumulation, nearest-resampled (categorical) to the grid.
    raw_streams = tmp / f"streams_t{threshold}.tif"
    run_wbt("extract_streams", flow_accum=str(raw_acc_cells), output=str(raw_streams),
            threshold=float(threshold), zero_background=True)
    streams_on_ref = np.full((ref["height"], ref["width"]), 0.0, dtype="float32")
    with rasterio.open(raw_streams) as src:
        reproject(
            source=src.read(1).astype("float32"), destination=streams_on_ref,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=ref["transform"], dst_crs=ref["crs"],
            src_nodata=src.nodata, dst_nodata=ctx.nodata,
            resampling=Resampling.nearest,
        )
    binary = np.where(streams_on_ref > 0, 1.0, 0.0).astype("float32")
    out_streams = np.where(mask, binary, np.float32(ctx.nodata)).astype("float32")
    ctx.write_raster(p["STREAMS_T500"], out_streams, ref["transform"], ref["crs"])

    run_wbt("euclidean_distance", i=str(p["STREAMS_T500"]), output=str(tmp / "dist_t500.tif"))
    normalize_to_reference(ctx, tmp / "dist_t500.tif", p["DISTANCE"], ref, mask)

    # TWI from the buffered slope, consistent with the buffered accumulation.
    run_wbt("wetness_index", sca=str(raw_acc_sca), slope=str(p["SLOPE_BUFFERED"]), output=str(tmp / "twi.tif"))
    normalize_to_reference(ctx, tmp / "twi.tif", p["TWI"], ref, mask)

    for f in tmp.glob("*.tif"):
        f.unlink(missing_ok=True)


def stage_ls_factor(ctx) -> None:
    """RUSLE LS from slope and specific catchment area; channel cells removed, capped."""
    p = ctx.p
    ref = ctx.ref_profile()
    slope_deg = ctx.read_band(p["SLOPE"], ref)
    sca = ctx.read_band(p["FLOW_ACC_SCA"], ref)
    flow_accum = ctx.read_band(p["FLOW_ACC_CELLS"], ref)
    theta = np.radians(slope_deg)
    sin_theta = np.sin(theta)
    as_term = np.where(sca > 0, np.power(np.maximum(sca, 0.0) / 22.13, 0.4), 0.0)
    sl_term = np.where(sin_theta > 0, np.power(np.maximum(sin_theta, 0.0) / 0.0896, 1.2), 0.0)
    ls = as_term * sl_term
    invalid = ~np.isfinite(slope_deg) | ~np.isfinite(sca)
    ls = np.where(invalid, np.nan, ls)
    channel = (flow_accum > ctx.cfg["stream_threshold"]) & np.isfinite(flow_accum)
    ls_hillslope = np.where(channel, np.nan, ls)
    ls_capped = np.where(np.isfinite(ls_hillslope), np.clip(ls_hillslope, 0.0, ctx.cfg["ls_cap"]), np.nan)
    ctx.write_raster(p["LS_CAPPED"], np.where(np.isfinite(ls_capped), ls_capped, ctx.nodata),
                     ref["transform"], ref["crs"])
