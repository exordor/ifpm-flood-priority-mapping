#!/usr/bin/env python3
"""Derive Zimbabwe V1 mining-pressure reference layer with decay-function sensitivity.

Builds the mining-pressure criterion from USGS Africa GIS mineral facilities +
deposits (known mines/quarries/plants/deposits), evaluated under THREE decay
functions so the choice can be compared as a sensitivity scenario:

1. tiered_linear  — 0-500m=1.0, 500m-2km linear to 0.3, 2-5km linear to 0, >5km=0
2. linear_3km     — single linear 0m=1.0 -> 3km=0.0, >3km=0
3. gaussian_1km   — exp(-d^2 / (2*1000^2)), sigma=1km

All three use the SAME USGS features and the SAME distance field. Only the
distance->pressure transform differs. This isolates the decay-function choice.

Literature basis (see registry note + assumptions):
- near-field ASM footprint: metres to ~1-2 km (Appleton 1999; Secocha MDPI)
- mining-agriculture buffer studies: 1-5 km tiers
- project consistency: all existing proximity criteria use a 5 km influence cap

The default output consumed by the V1 criteria stack is the tiered_linear
variant (most defensible). The other two are written alongside for the
sensitivity comparison.

Output replaces v1_mining_activity_indicator_0_1_utm35s_30m.tif (tiered_linear)
and writes two extra variants + a comparison CSV.
"""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask, rasterize
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [
    ROOT / "data/tmp/usgs_africa_gis_mineral_zimbabwe/Africa_GIS.gdb",
    ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg",
    ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif",
]
OUTPUTS = [
    ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_mining_activity_indicator_0_1_utm35s_30m.tif",
    ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_mining_linear_3km_0_1_utm35s_30m.tif",
    ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_mining_gaussian_1km_0_1_utm35s_30m.tif",
]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster
from functools import partial
write_raster = partial(_write_raster, sanitize=True)

USGS_GDB = ROOT / "data/tmp/usgs_africa_gis_mineral_zimbabwe/Africa_GIS.gdb"
V1_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
V1_REF = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif"
OUT_DIR = ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters"
BUFFER_M = 5000


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_reference() -> tuple[dict, np.ndarray]:
    with rasterio.open(V1_REF) as ref:
        profile = ref.profile.copy()
        crs = ref.crs
        shape = (ref.height, ref.width)
        transform = ref.transform
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(crs)
    mask = geometry_mask(boundary.geometry, out_shape=shape, transform=transform, invert=True)
    return profile, mask


def load_usgs_features(crs) -> gpd.GeoDataFrame:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs(crs)
    buf = boundary.geometry.iloc[0].buffer(BUFFER_M)
    combined = []
    for layer in ["AFR_Mineral_Facilities", "AFR_Mineral_Deposits"]:
        gdf = gpd.read_file(USGS_GDB, layer=layer)
        zwe = gdf[gdf["Country"].str.contains("Zimbabwe", case=False, na=False)].to_crs(crs)
        clipped = gpd.clip(zwe, gpd.GeoDataFrame(geometry=[buf], crs=crs))
        clipped["usgs_layer"] = layer
        combined.append(clipped)
        print(f"  {layer}: {len(clipped)} features in V1+{BUFFER_M//1000}km")
    if not combined:
        return gpd.GeoDataFrame(geometry=[], crs=crs)
    return gpd.GeoDataFrame(gpd.pd.concat(combined, ignore_index=True), crs=crs)


def distance_raster(features: gpd.GeoDataFrame, profile: dict) -> np.ndarray:
    shape = (profile["height"], profile["width"])
    transform = profile["transform"]
    if features.empty:
        return np.full(shape, 1e9, dtype="float32")  # "infinitely far"
    burned = rasterize(
        [(geom, 1) for geom in features.geometry if geom is not None and not geom.is_empty],
        out_shape=shape, transform=transform, fill=0, dtype="uint8", all_touched=True,
    )
    res = abs(profile["transform"].a)
    dist = distance_transform_edt(burned == 0) * res
    return dist.astype("float32")


def decay_tiered_linear(d_m: np.ndarray) -> np.ndarray:
    """0-500m=1.0, 500m-2km -> 0.3, 2-5km -> 0, >5km=0. Literature-backed tiers."""
    out = np.zeros_like(d_m, dtype="float32")
    m1 = d_m <= 500
    m2 = (d_m > 500) & (d_m <= 2000)
    m3 = (d_m > 2000) & (d_m <= 5000)
    out[m1] = 1.0
    out[m2] = 1.0 - (d_m[m2] - 500) / (2000 - 500) * (1.0 - 0.3)  # 1.0 -> 0.3
    out[m3] = 0.3 * (1.0 - (d_m[m3] - 2000) / (5000 - 2000))      # 0.3 -> 0
    return out


def decay_linear_3km(d_m: np.ndarray) -> np.ndarray:
    """Single linear: 0m=1.0 -> 3km=0.0, >3km=0."""
    return np.clip(1.0 - d_m / 3000.0, 0.0, 1.0).astype("float32")


def decay_gaussian_1km(d_m: np.ndarray) -> np.ndarray:
    """Gaussian exp(-d^2 / (2*sigma^2)), sigma=1km. Smooth, near-field weighted."""
    sigma = 1000.0
    return np.exp(-(d_m.astype("float64") ** 2) / (2 * sigma ** 2)).astype("float32")


def apply_mask(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = arr.copy()
    out[~mask] = np.nan
    return out


def stat(arr: np.ndarray, mask: np.ndarray) -> dict:
    v = arr[mask & np.isfinite(arr)]
    return {
        "mean": round(float(v.mean()), 4) if v.size else None,
        "p50": round(float(np.median(v)), 4) if v.size else None,
        "p95": round(float(np.percentile(v, 95)), 4) if v.size else None,
        "frac_gt_0": round(float((v > 0).mean()), 4) if v.size else None,
        "frac_gt_0.5": round(float((v > 0.5).mean()), 4) if v.size else None,
    }


def main() -> None:
    profile, mask = load_reference()
    crs = profile["crs"]
    print(f"V1 reference grid: {profile['width']}x{profile['height']} {crs}")

    print("\nLoading USGS mining features (V1 + 5km buffer):")
    usgs = load_usgs_features(crs)
    print(f"Total USGS features: {len(usgs)}")

    dist = distance_raster(usgs, profile)
    dist_v1 = dist[mask]
    print(f"\nDistance to nearest USGS feature inside V1:")
    print(f"  min={dist_v1.min():.0f}m  median={np.median(dist_v1):.0f}m  max={dist_v1.max():.0f}m")

    variants = [
        ("tiered_linear", decay_tiered_linear, "v1_mining_activity_indicator_0_1_utm35s_30m.tif"),
        ("linear_3km", decay_linear_3km, "v1_mining_linear_3km_0_1_utm35s_30m.tif"),
        ("gaussian_1km", decay_gaussian_1km, "v1_mining_gaussian_1km_0_1_utm35s_30m.tif"),
    ]

    rows = []
    for name, fn, fname in variants:
        arr = apply_mask(fn(dist), mask)
        path = OUT_DIR / fname
        write_raster(path, arr, profile)
        s = stat(arr, mask)
        print(f"\n{name}: mean={s['mean']}  frac>0={s['frac_gt_0']}  frac>0.5={s['frac_gt_0.5']}")
        rows.append({"variant": name, "file": rel(path), **s})

    write_csv(OUT_DIR / "v1_mining_decay_sensitivity.csv", rows)
    print(f"\nsensitivity table: {rel(OUT_DIR / 'v1_mining_decay_sensitivity.csv')}")

    # Also write the per-criterion upgrade manifest (default = tiered_linear)
    manifest = [{
        "layer": "v1_mining_activity_indicator_0_1",
        "path": rel(OUT_DIR / "v1_mining_activity_indicator_0_1_utm35s_30m.tif"),
        "components": "USGS mineral facilities+deposits; tiered-linear decay (0-500m=1, 500m-2km->0.3, 2-5km->0)",
        "source_usgs_features": len(usgs),
        "claim_level": "provisional",
        "decay_default": "tiered_linear",
        "sensitivity_variants": "linear_3km, gaussian_1km (see v1_mining_decay_sensitivity.csv)",
        **rows[0],
    }]
    write_csv(OUT_DIR / "v1_mining_upgrade_manifest.csv", manifest)
    print(f"manifest: {rel(OUT_DIR / 'v1_mining_upgrade_manifest.csv')}")


if __name__ == "__main__":
    main()
