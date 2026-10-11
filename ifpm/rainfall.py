"""Rainfall climatology criterion: DWD REGNIE (Goslar) or CHIRPS v3 (Secocha).

Ported from stage_rainfall in bin/factors/run_goslar_pim_chain.py (REGNIE) and from
run_secocha_pim_chain.py + bin/criteria/build_peru_former_rainfall_criterion.py (CHIRPS).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from scipy.ndimage import distance_transform_edt, label as ndimage_label


# --- REGNIE (Germany) ----------------------------------------------------------------

def read_regnie_month(path: Path) -> tuple[np.ndarray, dict]:
    """Read one DWD REGNIE monthly grid (gzipped ESRI ASCII, EPSG:31467)."""
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as stream:
        lines = stream.read().splitlines()
    header = {}
    index = 0
    for index, line in enumerate(lines):
        parts = line.split()
        if len(parts) == 2 and parts[0].replace("_", "").isalpha():
            header[parts[0].upper()] = float(parts[1])
            continue
        break
    ncols = int(header["NCOLS"])
    nrows = int(header["NROWS"])
    xll = header["XLLCORNER"]
    yll = header["YLLCORNER"]
    cell = header["CELLSIZE"]
    nodata = header.get("NODATA_VALUE", -999.0)
    values = []
    for line in lines[index:]:
        values.extend(float(v) for v in line.split())
    data = np.array(values[: ncols * nrows], dtype="float32").reshape((nrows, ncols))
    data[data == nodata] = np.nan
    transform = from_origin(xll, yll + nrows * cell, cell, cell)
    return data, {"transform": transform, "crs": "EPSG:31467", "width": ncols, "height": nrows}


def regnie_season_mean(ctx) -> tuple[np.ndarray, dict]:
    """Mean over the seasonal months of the per-month means over the years (mm)."""
    rain = ctx.cfg["rainfall"]
    months = rain["months"]
    years = range(rain["years"][0], rain["years"][1] + 1)
    folder = ctx.cfg.path(rain["dataset"])
    pattern = ctx.cfg.entry(rain["dataset"])["pattern"]
    month_arrays = {m: [] for m in months}
    meta = None
    for year in years:
        for month in months:
            path = folder / pattern.format(year=year, month=month)
            if not path.exists():
                raise FileNotFoundError(f"REGNIE file missing: {path}")
            data, meta = read_regnie_month(path)
            month_arrays[month].append(data)
    # Masked means so fully-NoData edge cells do not warn about empty slices.
    with np.errstate(invalid="ignore"):
        month_means = {m: np.ma.mean(np.ma.masked_invalid(np.stack(arrays)), axis=0).filled(np.nan)
                       for m, arrays in month_arrays.items()}
        season_mean = np.ma.mean(
            np.ma.masked_invalid(np.stack([month_means[m] for m in months])), axis=0
        ).filled(np.nan)
    return season_mean, meta


def stage_rainfall_regnie(ctx) -> None:
    """REGNIE seasonal mean, bilinear from 1 km to the 30 m grid, 2-98 scaled (provisional)."""
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    ctx.mkdir(ctx.p["RAIN_DIR"])
    season_mean, meta = regnie_season_mean(ctx)
    dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    reproject(
        source=season_mean, destination=dst,
        src_transform=meta["transform"], src_crs=meta["crs"],
        dst_transform=ref["transform"], dst_crs=ref["crs"],
        resampling=Resampling.bilinear,
    )
    dst[~mask] = np.nan
    valid = dst[mask & np.isfinite(dst)]
    if valid.size == 0:
        raise RuntimeError("no valid REGNIE cells inside the boundary")
    scored, low, high = ctx.normalize(dst, mask, constant_policy="zeros")
    ctx.write_raster(ctx.p["RAINFALL"], np.where(np.isfinite(scored), scored, ctx.nodata), ref["transform"], ref["crs"])


# --- CHIRPS (Peru) -------------------------------------------------------------------

def read_chirps_month_window(base_url: str, pattern: str, year: int, month: int, win_bounds):
    """Windowed HTTP read of one CHIRPS latam monthly GeoTIFF."""
    url = f"{base_url}/{pattern.format(year=year, month=month)}"
    minx, miny, maxx, maxy = win_bounds
    with rasterio.open(url) as src:
        from rasterio.windows import from_bounds
        win = from_bounds(minx, miny, maxx, maxy, src.transform)
        win = win.round_offsets().round_lengths()
        data = src.read(1, window=win).astype("float32")
        nodata = src.nodata
        win_transform = src.window_transform(win)
    if nodata is not None:
        data[data == nodata] = np.nan
    data[data < 0] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data, {"transform": win_transform, "crs": "EPSG:4326", "width": win.width, "height": win.height}


def chirps_season_mean(ctx, win_bounds) -> tuple[np.ndarray, dict]:
    """Mean seasonal total over the seasons; a season counts only if all its months exist."""
    rain = ctx.cfg["rainfall"]
    entry = ctx.cfg.entry(rain["dataset"])
    months = rain["months"]
    first_month = months[0]
    season_means = []
    ref_meta = None
    for y in range(rain["season_years"][0], rain["season_years"][1] + 1):
        months_data = []
        for m in months:
            # The season starts in December of year y; the other months are in y + 1.
            yy = y if m == first_month else y + 1
            arr, meta = read_chirps_month_window(entry["url"], entry["pattern"], yy, m, win_bounds)
            months_data.append(arr)
            ref_meta = ref_meta or meta
        monthly_stack = np.stack(months_data)
        complete_months = np.isfinite(monthly_stack).sum(axis=0) == len(months)
        season_total = np.where(complete_months, np.nansum(monthly_stack, axis=0), np.nan)
        season_means.append(season_total)
    season_stack = np.stack(season_means)
    valid_counts = np.isfinite(season_stack).sum(axis=0)
    total = np.nansum(season_stack, axis=0)
    mean = np.divide(total, valid_counts, out=np.full(total.shape, np.nan, dtype="float32"),
                     where=valid_counts > 0).astype("float32")
    return mean, ref_meta


def resample_to_reference(native_arr: np.ndarray, native_meta: dict, ref_profile: dict) -> np.ndarray:
    """Bilinear from the 0.05 degree grid to the reference grid (float64)."""
    dst = np.full((ref_profile["height"], ref_profile["width"]), np.nan, dtype="float64")
    reproject(
        source=native_arr, destination=dst,
        src_transform=native_meta["transform"], src_crs=native_meta["crs"], src_nodata=np.nan,
        dst_transform=ref_profile["transform"], dst_crs=ref_profile["crs"],
        resampling=Resampling.bilinear, dst_nodata=np.nan,
    )
    dst[~np.isfinite(dst)] = np.nan
    return dst


def fill_edge_nodata(data: np.ndarray, inside: np.ndarray) -> tuple[np.ndarray, dict[str, int]]:
    """Fill NoData holes inside the boundary from the nearest valid cell; count the holes."""
    work = data.astype("float64").copy()
    holes = inside & ~np.isfinite(work)
    if not holes.any():
        work[~inside] = np.nan
        return work, {"hole_cells": 0, "interior_holes": 0, "edge_sliver_holes": 0}
    outside = ~inside
    labeled, n = ndimage_label(holes)
    interior = edge_sliver = 0
    for i in range(1, n + 1):
        region = labeled == i
        dilated = np.zeros_like(region)
        dilated[1:-1, 1:-1] = (
            region[2:, 1:-1] | region[:-2, 1:-1] | region[1:-1, 2:] | region[1:-1, :-2]
            | region[2:, 2:] | region[2:, :-2] | region[:-2, 2:] | region[:-2, :-2]
        )
        if (dilated & outside).any():
            edge_sliver += 1
        else:
            interior += 1
    valid_inside = inside & np.isfinite(work)
    _, (row_idx, col_idx) = distance_transform_edt(~valid_inside, return_indices=True)
    filled = work[row_idx, col_idx]
    filled[~inside] = np.nan
    return filled, {"hole_cells": int(holes.sum()), "interior_holes": interior, "edge_sliver_holes": edge_sliver}


def stage_rainfall_chirps(ctx) -> None:
    """CHIRPS Dec-Mar seasonal mean, bilinear to 30 m, edge holes filled, 2-98 scaled."""
    import geopandas as gpd
    rain = ctx.cfg["rainfall"]
    ctx.mkdir(ctx.p["RAIN_DIR"])
    ref = ctx.ref_profile()
    inside = ctx.boundary_mask(ref)
    bounds = gpd.read_file(ctx.boundary_gpkg, layer=ctx.boundary_layer).to_crs(4326).total_bounds
    pad = rain["window_pad_deg"]
    win_bounds = (bounds[0] - pad, bounds[1] - pad, bounds[2] + pad, bounds[3] + pad)
    native, meta = chirps_season_mean(ctx, win_bounds)
    aligned = resample_to_reference(native, meta, ref)
    aligned, fill_report = fill_edge_nodata(aligned, inside)
    score, low, high = ctx.normalize(aligned, inside)
    ctx.write_raster(ctx.p["RAIN_DIR"] / "rainfall_dec_mar_2014_2024_mean_mm_30m_resample.tif",
                     np.where(np.isfinite(aligned), aligned, ctx.nodata), ref["transform"], ref["crs"])
    ctx.write_raster(ctx.p["RAINFALL"], np.where(np.isfinite(score), score, ctx.nodata), ref["transform"], ref["crs"])
    ctx.write_text(ctx.p["RAIN_DIR"] / "rainfall_manifest.json", json.dumps({
        "source": "CHIRPS v3.0 Latin America monthly GeoTIFFs",
        "season": "December-March", "seasons": "2014/15-2023/24",
        "native_resolution": "0.05 degree (approximately 5 km)",
        "target_grid": f"{ctx.crs}, 30 m overlay grid",
        "resampling": "bilinear; no new spatial information implied",
        "normalization": {"method": "2nd-98th percentile within active extent", "low_mm": low, "high_mm": high},
        "edge_fill": fill_report, "claim_level": "sensitivity_scenario",
    }, indent=2) + "\n")
