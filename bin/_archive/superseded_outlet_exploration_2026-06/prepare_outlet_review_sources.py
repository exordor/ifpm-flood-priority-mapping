#!/usr/bin/env python3
"""Prepare clipped source layers for professional outlet visual review."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/professional_outlet_review"
OUT_GPKG = OUT_DIR / "professional_outlet_review_layers.gpkg"
CANDIDATE_GPKG = ROOT / "outputs/candidate_outlet_discovery/candidate_catchments.gpkg"
HYDRORIVERS = (
    ROOT
    / "data/raw/hydrorivers_africa_visual_review/extracted/HydroRIVERS_v10_af_shp/HydroRIVERS_v10_af.shp"
)
OSM = ROOT / "data/raw/geofabrik_osm_zimbabwe_prototype/extracted/zimbabwe.gpkg"
GEOPORTAL_SUBCATCHMENTS = ROOT / "data/raw/zimbabwe_geoportal_subcatchments_2025/extracted/sub_catchments.shp"
GEOPORTAL_RIVERS = ROOT / "data/raw/zimbabwe_geoportal_candidate_outlet_layers/extracted/rivers/ZWE_water_lines_dcw.shp"
GEOPORTAL_WATER_AREAS = ROOT / "data/raw/zimbabwe_geoportal_candidate_outlet_layers/extracted/rivers/ZWE_water_areas_dcw.shp"
GEOPORTAL_FLOOD_ZONES = (
    ROOT / "data/raw/zimbabwe_geoportal_candidate_outlet_layers/extracted/flood_prone_zones/flood_prone_zones.shp"
)

OSM_LAYERS = {
    "osm_waterways": "gis_osm_waterways_free",
    "osm_roads": "gis_osm_roads_free",
    "osm_places": "gis_osm_places_free",
    "osm_pois": "gis_osm_pois_free",
    "osm_landuse": "gis_osm_landuse_a_free",
    "osm_water": "gis_osm_water_a_free",
}


def read_bbox(path: Path, layer: str | None, bbox: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    kwargs = {"bbox": bbox}
    if layer:
        kwargs["layer"] = layer
    gdf = gpd.read_file(path, **kwargs)
    return gdf.to_crs("EPSG:4326")


def clip_to_review(gdf: gpd.GeoDataFrame, envelope: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    clipped = gpd.clip(gdf, envelope[["geometry"]])
    return clipped[~clipped.geometry.is_empty].reset_index(drop=True)


def add_layer(gdf: gpd.GeoDataFrame, layer: str) -> int:
    if gdf.empty:
        gpd.GeoDataFrame({"source_layer": []}, geometry=[], crs="EPSG:4326").to_file(
            OUT_GPKG, layer=layer, driver="GPKG"
        )
        return 0
    gdf.to_file(OUT_GPKG, layer=layer, driver="GPKG")
    return len(gdf)


def source_manifest(counts: dict[str, int]) -> None:
    rows = [
        {
            "dataset_id": "hydrorivers_africa_visual_review",
            "status": "downloaded_used",
            "source_url": "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af_shp.zip",
            "raw_path": "data/raw/hydrorivers_africa_visual_review/",
            "review_layer": "hydrorivers_review",
            "feature_count": counts.get("hydrorivers_review", 0),
            "role": "river-network plausibility evidence",
        },
        {
            "dataset_id": "geofabrik_osm_zimbabwe_prototype",
            "status": "downloaded_used",
            "source_url": "https://download.geofabrik.de/africa/zimbabwe-latest-free.gpkg.zip",
            "raw_path": "data/raw/geofabrik_osm_zimbabwe_prototype/",
            "review_layer": "osm_*",
            "feature_count": sum(counts.get(k, 0) for k in counts if k.startswith("osm_")),
            "role": "waterways, roads, settlements, POIs, landuse, and water context",
        },
        {
            "dataset_id": "zimbabwe_geoportal_candidate_outlet_layers",
            "status": "downloaded_used",
            "source_url": "https://zimgeoportal.org.zw/datasets/rivers/; https://zimgeoportal.org.zw/datasets/flood-prone-zones/",
            "raw_path": "data/raw/zimbabwe_geoportal_candidate_outlet_layers/",
            "review_layer": "geoportal_rivers; geoportal_water_areas; geoportal_flood_prone_zones",
            "feature_count": counts.get("geoportal_rivers", 0)
            + counts.get("geoportal_water_areas", 0)
            + counts.get("geoportal_flood_prone_zones", 0),
            "role": "official local river and flood-prone evidence; flood-prone layer has no review-envelope overlap",
        },
    ]
    pd.DataFrame(rows).to_csv(OUT_DIR / "source_manifest.csv", index=False)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()

    search = gpd.read_file(CANDIDATE_GPKG, layer="search_envelope").to_crs("EPSG:4326")
    bbox = tuple(search.total_bounds)
    upper = gpd.read_file(GEOPORTAL_SUBCATCHMENTS).to_crs("EPSG:4326")
    upper = upper[upper["SubCatchme"] == "Upper Mzingwane"].reset_index(drop=True)

    counts: dict[str, int] = {}
    counts["review_envelope"] = add_layer(search, "review_envelope")
    counts["geoportal_upper_mzingwane"] = add_layer(upper, "geoportal_upper_mzingwane")

    for layer in ["catchments", "outlets", "target_units", "downstream_units", "flow_edges"]:
        gdf = gpd.read_file(CANDIDATE_GPKG, layer=layer).to_crs("EPSG:4326")
        counts[f"machine_{layer}"] = add_layer(gdf, f"machine_{layer}")

    hydrorivers = clip_to_review(read_bbox(HYDRORIVERS, None, bbox), search)
    counts["hydrorivers_review"] = add_layer(hydrorivers, "hydrorivers_review")
    geoportal_rivers = clip_to_review(read_bbox(GEOPORTAL_RIVERS, None, bbox), search)
    counts["geoportal_rivers"] = add_layer(geoportal_rivers, "geoportal_rivers")
    geoportal_water = clip_to_review(read_bbox(GEOPORTAL_WATER_AREAS, None, bbox), search)
    counts["geoportal_water_areas"] = add_layer(geoportal_water, "geoportal_water_areas")
    flood_zones = clip_to_review(read_bbox(GEOPORTAL_FLOOD_ZONES, None, bbox), search)
    counts["geoportal_flood_prone_zones"] = add_layer(flood_zones, "geoportal_flood_prone_zones")

    for output_layer, source_layer in OSM_LAYERS.items():
        gdf = clip_to_review(read_bbox(OSM, source_layer, bbox), search)
        counts[output_layer] = add_layer(gdf, output_layer)

    pd.DataFrame(
        [{"layer": layer, "feature_count": count} for layer, count in sorted(counts.items())]
    ).to_csv(OUT_DIR / "prepared_layer_counts.csv", index=False)
    source_manifest(counts)
    print(pd.DataFrame(counts.items(), columns=["layer", "feature_count"]).to_string(index=False))


if __name__ == "__main__":
    main()
