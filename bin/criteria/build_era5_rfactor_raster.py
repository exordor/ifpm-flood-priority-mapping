#!/usr/bin/env python3
"""Build a spatial empirical R-factor raster for V1 from ERA5 hourly, then recompute USLE A.

Local TOOLING script. Extends IFPM-082 from 7 sample points to a denser V1 grid, interpolates the
per-point empirical R to the native 0.05 deg grid (matching CHIRPS), and recomputes USLE A using
the clean R-invariant a_structure. This moves the empirical R from a family-arbitration number to
a spatially-explicit R layer.

Two A variants, consistent with the V1 convention:
- A_zonal: A = a_structure * R_zonal_mean (R as a catchment scalar; R not resampled to 30 m).
- A_spatial (DIAGNOSTIC ONLY): A = K*LS*C*R_pixelwise, with the 0.05 deg empirical R bilinearly
  resampled to 30 m. The resample is diagnostic-only (per the documented grid-rule waiver); the
  spatial product filename carries _DIAGNOSTIC and is NOT pixel-level evidence.

R reported in two forms: Wischmeier-Smith and Brown-Foster kinetic energy, each with I60 (lower
bound on I30) and I30 estimate (I60*1.1). The headline empirical R uses Wischmeier-Smith I30 est.

Usage (from workspace root):
    .venv/bin/python bin/criteria/build_era5_rfactor_raster.py
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling

try:
    import geopandas as gpd
except ImportError as exc:
    raise SystemExit(f"missing dependency: {exc}") from exc

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data/raw/era5_hourly_precip_zimbabwe_rfactor"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = ROOT / "outputs/v1_usle_soil_loss/rfactor_empirical_era5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
A_STRUCTURE = ROOT / "outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif"

# Denser V1 grid: ~0.12 deg spacing, covering V1 bbox + small buffer.
V1_LON_MIN, V1_LON_MAX = 28.50, 29.40
V1_LAT_MIN, V1_LAT_MAX = -21.00, -19.95
GRID_STEP = 0.12
YEAR_RANGE = (2018, 2023)

STORM_GAP_HOURS = 6
EROSIVE_DEPTH_MM = 12.0
KE_INTENSITY_CAP = 76.0
I30_UPSCALE = 1.1

# 0.05 deg target grid (matches CHIRPS)
TARGET_RES = 0.05
NODATA = -9999.0


def unit_ke_wischmeier(i_mmh: np.ndarray) -> np.ndarray:
    i = np.where(i_mmh <= 0, np.nan, np.minimum(i_mmh, KE_INTENSITY_CAP))
    e = 0.119 + 0.0873 * np.log10(i)
    return np.where(i_mmh <= 0, 0.0, e)


def unit_ke_brown_foster(i_mmh: np.ndarray) -> np.ndarray:
    e = 0.29 * (1.0 - 0.72 * np.exp(-0.05 * i_mmh))
    return np.where(i_mmh <= 0, 0.0, e)


def fetch_era5_hourly(lon: float, lat: float, y0: int, y1: int):
    url = (f"https://archive-api.open-meteo.com/v1/era5?"
           f"latitude={lat}&longitude={lon}"
           f"&start_date={y0}-01-01&end_date={y1}-12-31&hourly=precipitation")
    with urllib.request.urlopen(url, timeout=120) as r:
        d = json.load(r)
    precip = np.array(d["hourly"]["precipitation"], dtype=float)
    precip[~np.isfinite(precip)] = 0.0
    return d["hourly"]["time"], precip


def compute_r(precip: np.ndarray, times: list[str], ke_fn) -> tuple[float, float]:
    n = len(precip)
    is_wet = precip > 0
    storms = []
    i = 0
    while i < n:
        if is_wet[i]:
            j, gap = i, 0
            while j < n:
                if is_wet[j]:
                    j += 1; gap = 0
                else:
                    gap += 1; j += 1
                    if gap >= STORM_GAP_HOURS:
                        break
            storms.append((i, j - gap))
            i = j
        else:
            i += 1
    year_r_i60, year_r_i30 = {}, {}
    for (s, e) in storms:
        seg = precip[s:e]
        if seg.sum() < EROSIVE_DEPTH_MM:
            continue
        unit_e = ke_fn(seg)
        storm_E = float(np.sum(unit_e * seg))
        i60 = float(seg.max())
        yr = int(times[s][:4])
        year_r_i60[yr] = year_r_i60.get(yr, 0.0) + storm_E * i60
        year_r_i30[yr] = year_r_i30.get(yr, 0.0) + storm_E * i60 * I30_UPSCALE
    r_i60 = float(np.mean(list(year_r_i60.values()))) if year_r_i60 else 0.0
    r_i30 = float(np.mean(list(year_r_i30.values()))) if year_r_i30 else 0.0
    return r_i60, r_i30


def main() -> None:
    # --- 1. grid points ---
    lons = np.arange(V1_LON_MIN, V1_LON_MAX + 1e-9, GRID_STEP)
    lats = np.arange(V1_LAT_MIN, V1_LAT_MAX + 1e-9, GRID_STEP)
    pts = [(round(float(lon), 3), round(float(lat), 3)) for lat in lats for lon in lons]
    print(f"V1 grid: {len(lons)} x {len(lats)} = {len(pts)} points @ {GRID_STEP} deg")

    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(4326)
    from shapely.geometry import Point
    # keep points inside or near V1 (within 0.1 deg buffer) to limit downloads
    buf = boundary.unary_union.buffer(0.1)
    pts = [(lon, lat) for (lon, lat) in pts if buf.contains(Point(lon, lat))]
    print(f"after V1(+buffer) clip: {len(pts)} points to fetch")

    # --- 2. fetch + compute R per point (cache to data/raw) ---
    point_records = []
    for k, (lon, lat) in enumerate(pts):
        cache = DATA_DIR / f"grid_{lon:.3f}_{lat:.3f}_{YEAR_RANGE[0]}-{YEAR_RANGE[1]}.json"
        if cache.exists():
            d = json.load(open(cache))
            times, precip = d["times"], np.array(d["precipitation"], dtype=float)
        else:
            times, precip = fetch_era5_hourly(lon, lat, *YEAR_RANGE)
            cache.write_text(json.dumps({"lon": lon, "lat": lat, "times": times,
                                         "precipitation": precip.tolist()}), encoding="utf-8")
            time.sleep(0.3)  # be polite to the API
        r_ws_i60, r_ws_i30 = compute_r(precip, times, unit_ke_wischmeier)
        r_bf_i60, r_bf_i30 = compute_r(precip, times, unit_ke_brown_foster)
        point_records.append({"lon": lon, "lat": lat, "P_total_mm": round(float(np.nansum(precip)), 1),
                              "R_ws_i60": round(r_ws_i60, 1), "R_ws_i30": round(r_ws_i30, 1),
                              "R_bf_i60": round(r_bf_i60, 1), "R_bf_i30": round(r_bf_i30, 1)})
        if (k + 1) % 10 == 0 or k == len(pts) - 1:
            print(f"  {k+1}/{len(pts)} points done")

    # --- 3. interpolate point R to 0.05 deg raster ---
    lons_g = np.arange(V1_LON_MIN, V1_LON_MAX + 1e-9, TARGET_RES)
    lats_g = np.arange(V1_LAT_MAX, V1_LAT_MIN - 1e-9, -TARGET_RES)  # north->south
    transform = from_origin(lons_g[0] - TARGET_RES / 2, lats_g[0] + TARGET_RES / 2, TARGET_RES, TARGET_RES)
    h, w = len(lats_g), len(lons_g)
    pts_xy = np.array([(p["lon"], p["lat"]) for p in point_records])

    def interp(values: np.ndarray) -> np.ndarray:
        """Linear interpolation of point values onto the grid (scipy LinearNDInterpolator)."""
        from scipy.interpolate import LinearNDInterpolator
        return LinearNDInterpolator(pts_xy, values)(lons_g[ None, :], lats_g[:, None])

    for rkey, label in [("R_ws_i30", "wischmeier_I30est"), ("R_ws_i60", "wischmeier_I60lb"),
                        ("R_bf_i30", "brownfoster_I30est"), ("R_bf_i60", "brownfoster_I60lb")]:
        vals = np.array([p[rkey] for p in point_records])
        grid = interp(vals)
        grid = np.where(np.isfinite(grid), grid, NODATA).astype("float32")
        prof = {"driver": "GTiff", "height": h, "width": w, "count": 1, "dtype": "float32",
                "crs": "EPSG:4326", "transform": transform, "nodata": NODATA,
                "compress": "deflate", "tiled": True}
        outp = OUT_DIR / f"r_empirical_era5_{label}_0p05deg.tif"
        with rasterio.open(outp, "w", **prof) as ds:
            ds.write(grid, 1)
            ds.update_tags(1, IFPM_NOTE=f"Empirical ERA5 R, {label}; lower-bound (hourly != 30min)")
        print(f"  wrote {outp.name}")

    # --- 4. V1 zonal mean of the headline empirical R (WS I30 est) ---
    headline = OUT_DIR / "r_empirical_era5_wischmeier_I30est_0p05deg.tif"
    with rasterio.open(headline) as ds:
        arr = ds.read(1).astype("float64"); arr[arr == ds.nodata] = np.nan
        r_transform_grid = ds.transform; r_crs = ds.crs
    b = boundary.to_crs(r_crs)
    shapes = [(g, 1) for g in b.geometry if g is not None and not g.is_empty]
    v1_mask = rasterize(shapes, out_shape=arr.shape, transform=r_transform_grid, fill=0, dtype="uint8")
    r_zonal = float(np.nanmean(arr[v1_mask.astype(bool)]))
    print(f"\nHeadline empirical R (WS I30 est) V1 zonal mean = {r_zonal:.1f}")

    # --- 5. recompute USLE A = a_structure * R ---
    with rasterio.open(A_STRUCTURE) as ds:
        a_struct = ds.read(1).astype("float64"); prof30 = ds.profile
        if ds.nodata is not None:
            a_struct[a_struct == ds.nodata] = np.nan
    struct_mean = float(np.nanmean(a_struct))

    # A_zonal (R as scalar; R not resampled to 30m)
    a_zonal = a_struct * r_zonal
    # A_spatial DIAGNOSTIC (R resampled to 30m, diagnostic-only)
    r_30m = np.full(a_struct.shape, np.nan, dtype="float64")
    reproject(source=rasterio.band(rasterio.open(headline), 1), destination=r_30m,
              src_transform=r_transform_grid, src_crs=r_crs,
              dst_transform=prof30["transform"], dst_crs=prof30["crs"],
              resampling=Resampling.bilinear, src_nodata=NODATA, dst_nodata=np.nan)
    r_30m[~np.isfinite(r_30m)] = np.nan
    # A_spatial (DIAGNOSTIC): a_structure already = K*LS*C*P; multiply by the spatially-varying R.
    # Mask to cells where both a_structure and resampled R are finite.
    a_spatial = np.where(np.isfinite(a_struct) & np.isfinite(r_30m), a_struct * r_30m, np.nan)

    out_prof = prof30.copy(); out_prof.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)
    for name, arr in [("a_empirical_era5_zonal_30m.tif", a_zonal),
                      ("a_empirical_era5_spatial_DIAGNOSTIC_30m.tif", a_spatial)]:
        out = np.where(np.isfinite(arr), arr, -9999.0).astype("float32")
        with rasterio.open(OUT_DIR / name, "w", **out_prof) as ds:
            ds.write(out, 1)
            ds.update_tags(1, IFPM_NOTE=("DIAGNOSTIC: empirical R resampled to 30m; lower-bound; not pixel-level evidence"
                                         if "DIAGNOSTIC" in name else "empirical ERA5 R zonal-scalar A"))
        print(f"  wrote {name}")

    # --- diagnostics ---
    def stats(a):
        v = a[np.isfinite(a)]
        return {"mean": round(float(np.mean(v)), 4), "p50": round(float(np.percentile(v, 50)), 4),
                "p95": round(float(np.percentile(v, 95)), 4)} if v.size else {}
    diag = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/criteria/build_era5_rfactor_raster.py",
        "year_range": list(YEAR_RANGE),
        "n_grid_points": len(point_records),
        "grid_step_deg": GRID_STEP,
        "headline_R_ws_i30est_v1_zonal": round(r_zonal, 1),
        "a_structure_mean": round(struct_mean, 6),
        "a_zonal_stats": stats(a_zonal),
        "a_spatial_diagnostic_stats": stats(a_spatial),
        "point_records": point_records,
        "caveats": ["ERA5 hourly is a lower bound on true 30-min EI30.",
                    "Spatial A uses a documented diagnostic-only 0.05deg->30m R resample.",
                    "Empirical R is exploratory, not a validated V1 R."],
    }
    (OUT_DIR / "era5_rfactor_raster_diagnostics.json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
    print(f"wrote era5_rfactor_raster_diagnostics.json")
    print(f"\n=== Empirical A (WS I30 est R={r_zonal:.0f}) ===")
    print(f"  A_zonal mean = {diag['a_zonal_stats'].get('mean')} t/ha/yr")
    print(f"  A_spatial(diag) mean = {diag['a_spatial_diagnostic_stats'].get('mean')} t/ha/yr")


if __name__ == "__main__":
    main()
