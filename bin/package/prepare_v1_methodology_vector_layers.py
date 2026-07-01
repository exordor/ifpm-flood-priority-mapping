#!/usr/bin/env python3
"""Prepare V1 vector, history, protection, and proximity evidence."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyogrio.errors
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt

# pyogrio (the geopandas default backend) raises DataLayerError for a layer that is
# absent from a *present* file; a missing file or a corrupt layer raises
# DataSourceError and is left to propagate. fiona signals a missing layer with a
# plain ValueError, which is too broad to catch safely, so there is no portable
# cross-backend tuple -- we rely on the pyogrio backend. (geopandas >= 1.0 defaults
# to pyogrio; if a non-pyogrio backend is ever forced, an absent optional layer will
# raise loudly instead of being skipped.)
LAYER_MISSING = (pyogrio.errors.DataLayerError,)


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_full_methodology_evidence_sweep"
RASTER_DIR = OUT_DIR / "rasters"
LAYERS_GPKG = OUT_DIR / "v1_full_methodology_review_layers.gpkg"
SUMMARY_CSV = OUT_DIR / "v1_vector_layer_summary.csv"
DFO_CSV = OUT_DIR / "v1_dfo_zimbabwe_flood_events.csv"
WDPCA_CSV = OUT_DIR / "v1_wdpca_protected_area_summary.csv"

V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
MC_GPKG = ROOT / "outputs/v1_multicriteria_evidence_package/v1_multicriteria_review_layers.gpkg"
REFERENCE_DEM = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
DFO_ZIP = ROOT / "data/raw/dfo_global_flood_archive_v1_methodology/wlf_nhr_fl_dfomasterlist_20190418.zip"
WDPCA_GPKG = ROOT / "data/raw/wdpca_zimbabwe_v1_methodology/protected_conserved_areas_wdpca.gpkg"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def boundary() -> gpd.GeoDataFrame:
    return gpd.read_file(V1_GPKG, layer="v1_working_boundary").to_crs("EPSG:4326")


def read_layer(layer: str) -> gpd.GeoDataFrame:
    try:
        gdf = gpd.read_file(MC_GPKG, layer=layer)
    except LAYER_MISSING:
        print(f"layer '{layer}' not present in {MC_GPKG.name}; treating as empty", file=sys.stderr)
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    return gdf.to_crs("EPSG:4326") if not gdf.empty else gdf.set_crs(gdf.crs or "EPSG:4326")


def base_layers(bnd: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    layers = {
        "v1_boundary": bnd,
        "geoportal_rivers_v1": read_layer("geoportal_rivers_v1"),
        "hydrorivers_v1": read_layer("hydrorivers_v1"),
        "geoportal_water_areas_v1": read_layer("geoportal_water_areas_v1"),
        "geoportal_flood_prone_zones_v1": read_layer("geoportal_flood_prone_zones_v1"),
        "osm_places_v1": read_layer("osm_places_v1"),
        "osm_roads_v1": read_layer("osm_roads_v1"),
        "osm_bridges_v1": read_layer("osm_bridges_v1"),
        "osm_mining_proxy_v1": read_layer("osm_mining_proxy_v1"),
        "road_river_crossings_v1": read_layer("road_river_crossings_v1"),
    }
    if LAYERS_GPKG.exists():
        LAYERS_GPKG.unlink()
    for name, gdf in layers.items():
        if not gdf.empty:
            gdf.to_file(LAYERS_GPKG, layer=name, driver="GPKG")
    return layers


def vector_summary(layers: dict[str, gpd.GeoDataFrame]) -> list[dict[str, object]]:
    rows = []
    for name, gdf in layers.items():
        metric = gdf.to_crs("EPSG:32735") if not gdf.empty else gdf
        rows.append(
            {
                "layer": name,
                "feature_count": len(gdf),
                "length_km": float(metric.length.sum() / 1000) if not metric.empty else 0.0,
                "area_km2": float(metric.area.sum() / 1_000_000) if not metric.empty else 0.0,
            }
        )
    return rows


def write_float_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    profile = profile.copy()
    profile.update(driver="GTiff", count=1, dtype="float32", nodata=-9999.0, compress="deflate")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype("float32"), 1)


def distance_rows(label: str, gdf: gpd.GeoDataFrame) -> list[dict[str, object]]:
    with rasterio.open(REFERENCE_DEM) as ref:
        dem = ref.read(1)
        valid = dem != ref.nodata
        if gdf.empty:
            distance = np.full(dem.shape, -9999.0, dtype="float32")
            closeness = np.full(dem.shape, -9999.0, dtype="float32")
        else:
            shapes = [(geom, 1) for geom in gdf.to_crs(ref.crs).geometry if geom is not None and not geom.is_empty]
            burned = rasterize(shapes, out_shape=dem.shape, transform=ref.transform, fill=0, all_touched=True, dtype="uint8")
            distance = distance_transform_edt(burned == 0, sampling=(abs(ref.transform.e), ref.transform.a)).astype("float32")
            distance[~valid] = -9999.0
            vals = distance[valid]
            cap = float(np.nanpercentile(vals[vals >= 0], 98)) if vals.size else np.nan
            closeness = np.full(dem.shape, -9999.0, dtype="float32")
            if np.isfinite(cap) and cap > 0:
                closeness[valid] = 1.0 - np.minimum(distance[valid] / cap, 1.0)
        dist_path = RASTER_DIR / f"v1_distance_to_{label}_m_utm35s_30m.tif"
        close_path = RASTER_DIR / f"v1_closeness_to_{label}_0_1_utm35s_30m.tif"
        write_float_raster(dist_path, distance, ref.profile)
        write_float_raster(close_path, closeness, ref.profile)
    return summarize_array(f"distance_to_{label}_m", dist_path, distance) + summarize_array(f"closeness_to_{label}_0_1", close_path, closeness)


def summarize_array(layer: str, path: Path, data: np.ndarray) -> list[dict[str, object]]:
    vals = data[data >= 0]
    return [
        {
            "layer": layer,
            "artifact": rel(path),
            "valid_cells": int(vals.size),
            "min": float(vals.min()) if vals.size else np.nan,
            "mean": float(vals.mean()) if vals.size else np.nan,
            "max": float(vals.max()) if vals.size else np.nan,
        }
    ]


def dfo_rows(bnd: gpd.GeoDataFrame) -> list[dict[str, object]]:
    dfo = gpd.read_file(f"zip://{DFO_ZIP.resolve()}").to_crs("EPSG:4326")
    text = dfo[["Country__c", "Other", "Nations", "Detailed_L"]].fillna("").agg(" ".join, axis=1)
    zim = dfo[text.str.contains("Zimbabwe", case=False, regex=False)].copy()
    valid = zim.geometry.x.between(-180, 180) & zim.geometry.y.between(-90, 90)
    zim["valid_event_point"] = valid
    minx, miny, maxx, maxy = bnd.total_bounds
    context = zim[valid].cx[minx - 1 : maxx + 1, miny - 1 : maxy + 1].copy()
    cols = ["Register__", "Country__c", "Other", "Nations", "Began", "Ended", "Main_cause", "Dead", "Displaced", "Magnitude", "valid_event_point", "geometry"]
    zim[cols].to_csv(DFO_CSV, index=False)
    return [{"layer": "dfo_zimbabwe_flood_events", "artifact": rel(DFO_CSV), "feature_count": len(zim), "valid_points": int(valid.sum()), "v1_context_points_plus_1deg": len(context)}]


def wdpca_rows(bnd: gpd.GeoDataFrame) -> list[dict[str, object]]:
    geom = bnd.geometry.iloc[0]
    metric_geom = bnd.to_crs("EPSG:32735").geometry.iloc[0]
    polygons = gpd.read_file(WDPCA_GPKG, layer="polygons").to_crs("EPSG:4326")
    points = gpd.read_file(WDPCA_GPKG, layer="points").to_crs("EPSG:4326")
    poly_v1 = polygons[polygons.intersects(geom)].copy()
    point_v1 = points[points.intersects(geom)].copy()
    rows = []
    area = 0.0
    if not poly_v1.empty:
        metric = poly_v1.to_crs("EPSG:32735")
        metric["v1_overlap_km2"] = metric.geometry.intersection(metric_geom).area / 1_000_000
        area = float(metric["v1_overlap_km2"].sum())
        poly_v1["v1_overlap_km2"] = metric["v1_overlap_km2"].values
        poly_v1.to_file(LAYERS_GPKG, layer="wdpca_protected_polygons_v1", driver="GPKG")
        for item in poly_v1[["name", "name_eng", "desig_eng", "iucn_cat", "rep_area", "v1_overlap_km2"]].itertuples():
            rows.append({"feature_type": "polygon", "name": item.name, "name_eng": item.name_eng, "designation": item.desig_eng, "iucn_category": item.iucn_cat, "reported_area_km2": item.rep_area, "v1_overlap_km2": item.v1_overlap_km2})
    if not rows:
        rows.append({"feature_type": "none", "name": "", "name_eng": "", "designation": "", "iucn_category": "", "reported_area_km2": 0.0, "v1_overlap_km2": 0.0})
    write_csv(WDPCA_CSV, rows)
    return [{"layer": "wdpca_protected_areas_v1", "artifact": rel(WDPCA_CSV), "feature_count": len(poly_v1) + len(point_v1), "polygon_count": len(poly_v1), "point_count": len(point_v1), "area_km2": area}]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RASTER_DIR.mkdir(parents=True, exist_ok=True)
    bnd = boundary()
    layers = base_layers(bnd)
    rows = vector_summary(layers)
    for label, layer_name in {"rivers": "geoportal_rivers_v1", "roads": "osm_roads_v1", "mining_proxy": "osm_mining_proxy_v1"}.items():
        rows.extend(distance_rows(label, layers[layer_name]))
    rows.extend(dfo_rows(bnd))
    rows.extend(wdpca_rows(bnd))
    write_csv(SUMMARY_CSV, rows)
    print(f"wrote {SUMMARY_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
