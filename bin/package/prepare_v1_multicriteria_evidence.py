#!/usr/bin/env python3
"""Prepare V1 multi-criteria evidence tables and review layers."""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_multicriteria_evidence_package"
# Archived 2026-07-02: see outputs/_archive/superseded_outlet_exploration_2026-06/.
REVIEW_GPKG = ROOT / "outputs/_archive/superseded_outlet_exploration_2026-06/professional_outlet_review/professional_outlet_review_layers.gpkg"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
TERRAIN_DIR = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization"
REVIEW_OUT = OUT_DIR / "v1_multicriteria_review_layers.gpkg"
EVIDENCE_CSV = OUT_DIR / "v1_candidate_criteria_evidence_table.csv"
COUNTS_CSV = OUT_DIR / "v1_multicriteria_layer_counts.csv"


def read_layer(path: Path, layer: str, crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path, layer=layer)
    if gdf.crs is None:
        gdf = gdf.set_crs(crs)
    return gdf.to_crs(crs)


def v1_boundary() -> gpd.GeoDataFrame:
    boundary = read_layer(V1_GPKG, "v1_working_boundary")
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected one non-empty V1 working boundary")
    return boundary


def clip_to_v1(layer: str, boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = read_layer(REVIEW_GPKG, layer)
    if gdf.empty:
        return gdf
    return gdf[gdf.intersects(boundary.geometry.iloc[0])].copy()


def mining_proxy(landuse: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if landuse.empty:
        return landuse
    fclass = landuse["fclass"].fillna("").str.lower()
    name = landuse["name"].fillna("").str.lower()
    return landuse[fclass.isin(["quarry", "industrial"]) | name.str.contains("mine|mining|quarry")].copy()


def road_river_crossings(roads: gpd.GeoDataFrame, rivers: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if roads.empty or rivers.empty:
        return gpd.GeoDataFrame(columns=["crossing_type", "geometry"], geometry="geometry", crs=roads.crs)
    joined = gpd.sjoin(roads, rivers[["geometry"]], predicate="intersects", how="inner")
    if joined.empty:
        return gpd.GeoDataFrame(columns=["crossing_type", "geometry"], geometry="geometry", crs=roads.crs)
    points = joined.drop_duplicates("osm_id").copy()
    points["crossing_type"] = "road_river_intersection_proxy"
    points["geometry"] = points.geometry.representative_point()
    return points[["osm_id", "fclass", "name", "bridge", "crossing_type", "geometry"]].copy()


def write_layers(layers: dict[str, gpd.GeoDataFrame]) -> None:
    if REVIEW_OUT.exists():
        REVIEW_OUT.unlink()
    for name, gdf in layers.items():
        if gdf.empty:
            continue
        gdf.to_file(REVIEW_OUT, layer=name, driver="GPKG")


def count_rows(layers: dict[str, gpd.GeoDataFrame]) -> list[dict[str, object]]:
    roles = {
        "v1_boundary": "working catchment mask",
        "v1_anchors": "place checks and context",
        "geoportal_rivers_v1": "local river context",
        "hydrorivers_v1": "reproducible river context",
        "geoportal_water_areas_v1": "waterbody context",
        "geoportal_flood_prone_zones_v1": "flood-prone evidence gap if zero",
        "osm_places_v1": "settlement exposure proxy",
        "osm_roads_v1": "road exposure proxy",
        "osm_bridges_v1": "bridge exposure proxy",
        "road_river_crossings_v1": "possible crossing exposure proxy",
        "osm_mining_proxy_v1": "weak mining pressure proxy",
    }
    return [{"layer": name, "feature_count": len(gdf), "role": roles.get(name, "")} for name, gdf in layers.items()]


def evidence_rows(counts: dict[str, int]) -> list[dict[str, str]]:
    blocked = "blocked until criteria hierarchy and modelling-unit decision"
    return [
        row("terrain", "elevation_lowland_context", "SRTMGL1 DEM", "30 m raster", "30 m", "medium", "context only", "Use as context or exclude?", "Lowland context only; not flood risk alone", blocked),
        row("terrain", "slope_low_slope_susceptibility", "SRTMGL1 slope", "30 m raster", "30 m", "medium", "candidate criterion", "Accept low-slope susceptibility?", "Terrain-only diagnostic; needs process agreement", blocked),
        row("terrain", "slope_high_runoff_pressure", "SRTMGL1 slope", "30 m raster", "30 m", "medium", "context only", "Keep as alternative framing?", "Opposite slope interpretation from low-slope susceptibility", blocked),
        row("hydro_flood", "river_context", "Geoportal Rivers + HydroRIVERS", "vector lines", "mapped river network", "medium", "context only", "Use as drainage context?", "River lines support interpretation, not observed flood depth", blocked),
        row("hydro_flood", "flood_prone_zones", "Zimbabwe Geoportal Flood Prone Zones", "vector polygons", "local overlap count", "weak", "gap", "Need alternative flood evidence?", f"Current V1/review overlap count is {counts.get('geoportal_flood_prone_zones_v1', 0)}", blocked),
        row("exposure", "settlement_places", "OSM places + anchors", "vector points", "mapped settlements", "medium", "candidate criterion", "Use settlement exposure?", f"{counts.get('osm_places_v1', 0)} OSM places inside V1; completeness uncertain", blocked),
        row("exposure", "roads_and_crossings", "OSM roads/bridges", "vector lines/points", "mapped transport network", "medium", "candidate criterion", "Use road/bridge exposure?", f"{counts.get('osm_roads_v1', 0)} roads and {counts.get('osm_bridges_v1', 0)} bridge-tagged roads inside V1", blocked),
        row("mining_pressure", "osm_quarry_industrial_proxy", "OSM landuse", "vector polygons", "mapped OSM landuse", "weak", "context only", "Is proxy mining evidence acceptable?", f"{counts.get('osm_mining_proxy_v1', 0)} quarry/industrial polygons; not official mining truth", blocked),
        row("rainfall", "chirps_rainfall", "CHIRPS v3 rainfall comparison", "native grid rasters / V1 summaries", "0.05 degree / V1 zonal", "medium", "candidate criterion pending", "Choose rainfall interpretation?", "Comparison available separately; must remain native/zonal, not 30 m overlay", blocked),
    ]


def row(family: str, criterion: str, source: str, unit: str, scale: str, strength: str, role: str, decision: str, limitation: str, overlay: str) -> dict[str, str]:
    return {
        "criterion_family": family,
        "candidate_criterion": criterion,
        "source": source,
        "spatial_unit": unit,
        "scale_or_resolution": scale,
        "evidence_strength": strength,
        "suggested_role": role,
        "mentor_decision_needed": decision,
        "limitation": limitation,
        "overlay_status": overlay,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    boundary = v1_boundary()
    layers = {
        "v1_boundary": boundary,
        "v1_anchors": read_layer(V1_GPKG, "v1_anchor_check"),
        "geoportal_rivers_v1": clip_to_v1("geoportal_rivers", boundary),
        "hydrorivers_v1": clip_to_v1("hydrorivers_review", boundary),
        "geoportal_water_areas_v1": clip_to_v1("geoportal_water_areas", boundary),
        "geoportal_flood_prone_zones_v1": clip_to_v1("geoportal_flood_prone_zones", boundary),
        "osm_places_v1": clip_to_v1("osm_places", boundary),
        "osm_roads_v1": clip_to_v1("osm_roads", boundary),
        "osm_landuse_v1": clip_to_v1("osm_landuse", boundary),
    }
    layers["osm_bridges_v1"] = layers["osm_roads_v1"][layers["osm_roads_v1"]["bridge"] == "T"].copy()
    layers["osm_mining_proxy_v1"] = mining_proxy(layers["osm_landuse_v1"])
    layers["road_river_crossings_v1"] = road_river_crossings(layers["osm_roads_v1"], layers["geoportal_rivers_v1"])

    counts = count_rows(layers)
    write_layers(layers)
    write_csv(COUNTS_CSV, counts)
    count_map = {item["layer"]: int(item["feature_count"]) for item in counts}
    write_csv(EVIDENCE_CSV, evidence_rows(count_map))
    print(f"wrote {EVIDENCE_CSV.relative_to(ROOT)}")
    print(f"wrote {COUNTS_CSV.relative_to(ROOT)}")
    print(f"wrote {REVIEW_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
