#!/usr/bin/env python3
"""Query INGEMMET Pequeña Minería (small-scale/ASM mining points) for Arequipa Region and build the
mining-pressure proximity criterion.

Reads the public INGEMMET ArcGIS REST service SERV_PEQUENA_MINERIA (layer 0) for features
intersecting the Arequipa Region envelope, saves them as a GeoPackage, then builds an inverted-distance
proximity raster on the Arequipa Region 30m grid. This is the official-source upgrade over the OSM
quarry/industrial proxy used previously.

Outputs (gitignored):
- data/raw/ingemmet_catastro_minero_peru_pilot/peru_hybas_l7_6070641200_pequena_mineria.gpkg (raw points)
- outputs/ingemmet_catastro_minero_peru_pilot/peru_hybas_l7_6070641200_mining_pressure_ingemmet_0_1.tif (criterion)

The criterion replaces the OSM-based closeness_to_mining_indicator in the Arequipa Region criteria stack.
"""

from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask, rasterize
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))
from _lib.standardization import percentile_minmax

INPUTS = [ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg", ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif"]
OUTPUTS = [ROOT / "outputs/ingemmet_catastro_minero_peru_pilot/peru_hybas_l7_6070641200_mining_pressure_ingemmet_0_1.tif"]
SERVICE = "https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_PEQUENA_MINERIA/MapServer/0"
RAW_DIR = ROOT / "data/raw/ingemmet_catastro_minero_peru_pilot"
RAW_GPKG = RAW_DIR / "peru_hybas_l7_6070641200_pequena_mineria.gpkg"
OUT_DIR = ROOT / "outputs/ingemmet_catastro_minero_peru_pilot"
REF = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif"
PERU_HYBAS_L7_6070641200_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def peru_hybas_l7_6070641200_envelope_lonlat() -> tuple[float, float, float, float]:
    b = gpd.read_file(PERU_HYBAS_L7_6070641200_GPKG, layer="peru_pilot_boundary").to_crs("EPSG:4326")
    minx, miny, maxx, maxy = b.total_bounds
    pad = 0.02  # ~2km pad so proximity is defined at the edge
    return minx - pad, miny - pad, maxx + pad, maxy + pad


def query_features(xmin: float, ymin: float, xmax: float, ymax: float) -> list[dict]:
    """Query the ArcGIS REST service for features in the bbox. Paginate if needed."""
    env = f"{xmin},{ymin},{xmax},{ymax}"
    all_feats: list[dict] = []
    offset = 0
    page = 1000
    while True:
        params = {
            "geometry": env, "geometryType": "esriGeometryEnvelope",
            "inSR": "4326", "outSR": "4326", "spatialRel": "esriSpatialRelIntersects",
            "where": "1=1", "outFields": "*", "returnGeometry": "true", "f": "json",
            "resultOffset": str(offset), "resultRecordCount": str(page),
        }
        url = SERVICE + "/query?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        if d.get("error"):
            raise RuntimeError(f"ArcGIS error: {d['error']}")
        feats = d.get("features", [])
        all_feats.extend(feats)
        if len(feats) < page or d.get("exceededTransferLimit") is not True:
            break
        offset += page
    return all_feats


def features_to_gdf(feats: list[dict]) -> gpd.GeoDataFrame:
    rows = []
    geoms = []
    for f in feats:
        g = f.get("geometry", {})
        attrs = f.get("attributes", {})
        if "x" in g and "y" in g:  # point
            geoms.append(Point(g["x"], g["y"]))
            rows.append(attrs)
        elif "rings" in g:  # polygon (unexpected for this layer, but handle)
            from shapely.geometry import shape
            geoms.append(shape({"type": "Polygon", "coordinates": g["rings"][0]}))
            rows.append(attrs)
    return gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:4326")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    xmin, ymin, xmax, ymax = peru_hybas_l7_6070641200_envelope_lonlat()
    print(f"querying INGEMMET PEQUENA_MINERIA in bbox {xmin:.3f},{ymin:.3f},{xmax:.3f},{ymax:.3f} ...")
    feats = query_features(xmin, ymin, xmax, ymax)
    print(f"  features returned: {len(feats)}")
    if not feats:
        print("  no ASM points in Arequipa Region; mining criterion will be all-zero (documented gap).")

    gdf = features_to_gdf(feats) if feats else gpd.GeoDataFrame(
        {"objectid": []}, geometry=[], crs="EPSG:4326")
    gdf.to_file(RAW_GPKG, layer="pequena_mineria", driver="GPKG")
    print(f"  wrote raw points: {rel(RAW_GPKG)}")

    # Build proximity raster on the Arequipa Region grid.
    with rasterio.open(REF) as ref:
        profile = ref.profile.copy()
        crs = ref.crs
        transform = ref.transform
        shape = (ref.height, ref.width)
    boundary = gpd.read_file(PERU_HYBAS_L7_6070641200_GPKG, layer="peru_pilot_boundary").to_crs(crs)
    mask = geometry_mask(boundary.geometry, out_shape=shape, transform=transform, invert=True)

    res = abs(transform.a)
    if not gdf.empty:
        pts = gdf.to_crs(crs)
        burned = rasterize(
            [(geom, 1) for geom in pts.geometry if geom is not None and not geom.is_empty],
            out_shape=shape, transform=transform, fill=0, dtype="uint8", all_touched=True,
        )
        dist = distance_transform_edt(burned == 0) * res
    else:
        dist = np.full(shape, 1e9, dtype="float32")  # very far -> closeness 0

    # 2-98 percentile inverted (closer -> higher pressure), masked to Arequipa
    # Region.  The numeric implementation is shared with all other criteria.
    closeness, low, high = percentile_minmax(
        dist,
        mask,
        invert=True,
        constant_policy="expand",
    )

    out_profile = profile.copy()
    out_profile.update(driver="GTiff", count=1, dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)
    out_raster = OUT_DIR / "peru_hybas_l7_6070641200_mining_pressure_ingemmet_0_1.tif"
    encoded = np.where(np.isfinite(closeness), closeness, -9999.0).astype("float32")
    with rasterio.open(out_raster, "w", **out_profile) as dst:
        dst.write(encoded, 1)
    print(f"wrote criterion: {rel(out_raster)}")

    valid = mask & np.isfinite(closeness)
    vals = closeness[valid]
    manifest = [{
        "layer": "peru_hybas_l7_6070641200_mining_pressure_ingemmet_0_1",
        "path": rel(out_raster),
        "source": "INGEMMET SERV_PEQUENA_MINERIA (official ASM points)",
        "features_in_peru_hybas_l7_6070641200_envelope": len(gdf),
        "method": "euclidean_distance_inverted_percentile_2_98",
        "dist_clip_low_m": round(low, 1), "dist_clip_high_m": round(high, 1),
        "valid_fraction": round(float(vals.size / mask.sum()), 6),
        "mean": round(float(vals.mean()), 6) if vals.size else "",
        "claim_level": "provisional (official-source point evidence; not active-disturbance truth)",
        "note": "upgrade over OSM quarry/industrial proxy; ASM point proximity, not active footprint",
    }]
    with (OUT_DIR / "mining_pressure_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    print(f"features: {len(gdf)}, mean closeness: {manifest[0]['mean']}")


if __name__ == "__main__":
    main()
