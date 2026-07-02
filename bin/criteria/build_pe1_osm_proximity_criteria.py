#!/usr/bin/env python3
"""Extract PE1 OSM layers and build mining/exposure proximity criteria rasters.

Reads Geofabrik Peru OSM (roads, places, landuse), clips to PE1, and builds two criteria
rasters on the PE1 30m reference grid (EPSG:32718):

- mining_pressure: proximity to OSM landuse quarry/industrial polygons (inverted distance ->
  closer = higher mining pressure). Weak proxy, same logic as Zimbabwe.
- socioeconomic_exposure: proximity to OSM roads (inverted distance -> closer = more accessible/
  exposed). Same logic as Zimbabwe's road_accessibility_proxy.

Both standardized 0-1 via 2-98 percentile min-max (inverted), masked to PE1. These fill the two
deferred PE1 criteria so the PE1 stack reaches 5 criteria, comparable to Zimbabwe v0.2.
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
INPUTS = [ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUTPUTS = [ROOT / "outputs/geofabrik_osm_peru_pilot/pe1_proximity/closeness_to_roads_0_1.tif"]
import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster
from functools import partial
write_raster = partial(_write_raster, sanitize=True)
from _lib.ifpm_tools import raster_stats as stats
OSM_DIR = ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted"
OUT_DIR = ROOT / "outputs/geofabrik_osm_peru_pilot/pe1_proximity"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"

ROADS_SHP = OSM_DIR / "gis_osm_roads_free_1.shp"
PLACES_SHP = OSM_DIR / "gis_osm_places_free_1.shp"
LANDUSE_SHP = OSM_DIR / "gis_osm_landuse_a_free_1.shp"


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
    with rasterio.open(REF) as ref:
        profile = ref.profile.copy()
        crs = ref.crs
        shape = (ref.height, ref.width)
        transform = ref.transform
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(crs)
    mask = geometry_mask(boundary.geometry, out_shape=shape, transform=transform, invert=True)
    return profile, mask


def clip_osm_to_pe1(shp_path: Path, crs) -> gpd.GeoDataFrame:
    """Read an OSM layer and clip to the PE1 boundary (+ small buffer) in the target CRS."""
    if not shp_path.exists():
        return gpd.GeoDataFrame(geometry=[], crs=crs)
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs(crs)
    buf = boundary.geometry.iloc[0].buffer(5000)  # 5km buffer so proximity is defined at the edge
    gdf = gpd.read_file(shp_path).to_crs(crs)
    if gdf.empty:
        return gdf
    return gpd.clip(gdf, gpd.GeoDataFrame(geometry=[buf], crs=crs))


def proximity_raster(features: gpd.GeoDataFrame, profile: dict, mask: np.ndarray) -> np.ndarray:
    """Euclidean distance (metres) from each cell to the nearest feature, inverted to 0-1 closeness.

    Rasterize features to the reference grid (1=feature, 0=background), then distance transform.
    Closer to a feature -> higher value.
    """
    transform = profile["transform"]
    shape = (profile["height"], profile["width"])
    if features.empty:
        # no features: return all-zero (no proximity pressure) inside PE1
        out = np.zeros(shape, dtype="float32")
        out[~mask] = np.nan
        return out
    burned = rasterize(
        [(geom, 1) for geom in features.geometry if geom is not None and not geom.is_empty],
        out_shape=shape, transform=transform, fill=0, dtype="uint8", all_touched=True,
    )
    res = abs(profile["transform"].a)  # pixel size in metres (30m)
    dist = distance_transform_edt(burned == 0) * res
    return dist.astype("float32")


def normalize_inverted(data: np.ndarray, mask: np.ndarray, clip_low: float | None = None) -> tuple[np.ndarray, float, float]:
    """2-98 percentile min-max inverted: closer (lower distance) -> higher 0-1 value."""
    values = data[mask & np.isfinite(data)]
    if values.size == 0:
        raise ValueError("cannot normalize empty proximity raster")
    low, high = np.nanpercentile(values, [2, 98])
    if high <= low:
        high = low + 1.0
    out = np.clip(1.0 - (data - low) / (high - low), 0.0, 1.0).astype("float32")
    out[~mask] = np.nan
    return out, float(low), float(high)
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile, mask = load_reference()
    crs = profile["crs"]

    # --- roads (exposure) ---
    print("clipping roads to PE1 ...")
    roads = clip_osm_to_pe1(ROADS_SHP, crs)
    print(f"  roads features inside PE1+5km: {len(roads)}")
    roads_dist = proximity_raster(roads, profile, mask)
    roads_01, r_lo, r_hi = normalize_inverted(roads_dist, mask)
    write_raster(OUT_DIR / "closeness_to_roads_0_1.tif", roads_01, profile)

    # --- mining proxy (landuse quarry/industrial) ---
    print("clipping landuse to PE1 ...")
    landuse = clip_osm_to_pe1(LANDUSE_SHP, crs)
    if not landuse.empty and "fclass" in landuse.columns:
        fclass = landuse["fclass"].astype(str)
        name = landuse["name"].astype(str) if "name" in landuse.columns else fclass
        mining = landuse[fclass.isin(["quarry", "industrial"]) | name.str.contains("mine|mining|quarry", case=False, na=False)].copy()
    else:
        mining = gpd.GeoDataFrame(geometry=[], crs=crs)
    print(f"  mining proxy features (quarry/industrial) inside PE1+5km: {len(mining)}")
    mining_dist = proximity_raster(mining, profile, mask)
    mining_01, m_lo, m_hi = normalize_inverted(mining_dist, mask)
    write_raster(OUT_DIR / "closeness_to_mining_proxy_0_1.tif", mining_01, profile)

    # --- places (context, for diagnostics) ---
    print("clipping places to PE1 ...")
    places = clip_osm_to_pe1(PLACES_SHP, crs)
    print(f"  places features inside PE1+5km: {len(places)}")

    manifest = [
        {"layer": "closeness_to_roads_0_1", "path": rel(OUT_DIR / "closeness_to_roads_0_1.tif"),
         "components": "OSM roads proximity (inverted); exposure/access proxy",
         "source_features": len(roads), "claim_level": "diagnostic_only", **stats(roads_01, mask)},
        {"layer": "closeness_to_mining_proxy_0_1", "path": rel(OUT_DIR / "closeness_to_mining_proxy_0_1.tif"),
         "components": "OSM landuse quarry/industrial proximity (inverted); weak mining proxy",
         "source_features": len(mining), "claim_level": "diagnostic_only", **stats(mining_01, mask)},
        {"layer": "osm_places_count", "path": "", "components": "OSM places (context only, not a criterion)",
         "source_features": len(places), "claim_level": "diagnostic_only"},
    ]
    write_csv(OUT_DIR / "osm_proximity_manifest.csv", manifest)
    write_csv(OUT_DIR / "standardization_notes.csv", [
        {"component": "roads", "method": "euclidean_distance_inverted_percentile_2_98", "dist_clip_low_m": r_lo, "dist_clip_high_m": r_hi},
        {"component": "mining", "method": "euclidean_distance_inverted_percentile_2_98", "dist_clip_low_m": m_lo, "dist_clip_high_m": m_hi},
    ])
    print(f"\nwrote PE1 OSM proximity criteria to {rel(OUT_DIR)}")
    print(f"  roads: {len(roads)} features; closeness mean {manifest[0]['mean']}")
    print(f"  mining proxy: {len(mining)} features; closeness mean {manifest[1]['mean']}")
    if len(mining) == 0:
        print("  WARNING: 0 mining proxy features in PE1 — mining_pressure will be all-zero (no OSM quarry/industrial).")
        print("           This is expected for a remote Andean basin; INGEMMET/GEOCATMIN is the real source.")


if __name__ == "__main__":
    main()
