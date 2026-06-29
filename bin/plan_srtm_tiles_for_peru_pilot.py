#!/usr/bin/env python3
"""Plan SRTM 1 Arc-Second tiles for the Peru engineering-pilot boundary (PE1).

Mirrors `plan_srtm_tiles_for_v1.py` but for the Peru pilot boundary. Pre-download planning only:
computes tile names from PE1 + 5 km buffer without downloading any data.

Peru uses UTM 18S (EPSG:32718) for the metric buffer, NOT the Zimbabwe UTM 35S.
"""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs/peru_pilot_boundary"
PE1_GPKG = OUT_DIR / "peru_pilot_boundary.gpkg"
OUT_GPKG = OUT_DIR / "srtm_peru_pilot_tile_plan.gpkg"
OUT_CSV = OUT_DIR / "srtm_peru_pilot_tile_plan.csv"
SUMMARY = OUT_DIR / "srtm_peru_pilot_preflight_summary.md"
METRIC_CRS = "EPSG:32718"  # UTM 18S covers southern Peru / the PE1 pilot area
BUFFER_M = 5_000
DATASET_ID = "srtm_1arcsec_peru_pilot"
DESTINATION = f"data/raw/{DATASET_ID}/"


def tile_name(lat: int, lon: int) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{ns}{abs(lat):02d}{ew}{abs(lon):03d}"


def load_pe1_boundary() -> gpd.GeoDataFrame:
    if not PE1_GPKG.exists():
        raise FileNotFoundError(f"Run bin/export_peru_pilot_boundary.py first: {PE1_GPKG}")
    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs("EPSG:4326")
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected exactly one non-empty PE1 boundary geometry")
    return boundary


def buffered_bbox(boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    buffered = boundary.to_crs(METRIC_CRS).buffer(BUFFER_M).to_crs("EPSG:4326")
    minx, miny, maxx, maxy = buffered.total_bounds
    return gpd.GeoDataFrame(
        [{
            "name": "pe1_bbox_5km_buffer",
            "buffer_m": BUFFER_M,
            "min_lon": minx,
            "min_lat": miny,
            "max_lon": maxx,
            "max_lat": maxy,
            "geometry": box(minx, miny, maxx, maxy),
        }],
        geometry="geometry",
        crs="EPSG:4326",
    )


def build_tile_plan(bbox_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    bounds = bbox_gdf.iloc[0]
    min_lon = math.floor(float(bounds["min_lon"]))
    max_lon = math.ceil(float(bounds["max_lon"]))
    min_lat = math.floor(float(bounds["min_lat"]))
    max_lat = math.ceil(float(bounds["max_lat"]))
    rows = []
    for lat in range(min_lat, max_lat):
        for lon in range(min_lon, max_lon):
            name = tile_name(lat, lon)
            rows.append({
                "tile_name": name,
                "lower_left_lon": lon,
                "lower_left_lat": lat,
                "upper_right_lon": lon + 1,
                "upper_right_lat": lat + 1,
                "expected_source_pattern": f"{name}.*",
                "destination_dataset_id": DATASET_ID,
                "destination_dir": DESTINATION,
                "download_status": "planned_not_downloaded",
                "geometry": box(lon, lat, lon + 1, lat + 1),
            })
    if not rows:
        raise ValueError("No SRTM tiles intersect the PE1 buffered bounding box")
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def write_outputs(bbox_gdf: gpd.GeoDataFrame, tiles: gpd.GeoDataFrame) -> None:
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()
    tiles.drop(columns="geometry").to_csv(OUT_CSV, index=False)
    bbox_gdf.to_file(OUT_GPKG, layer="pe1_bbox_5km_buffer", driver="GPKG")
    tiles.to_file(OUT_GPKG, layer="srtm_tiles", driver="GPKG")
    bbox = bbox_gdf.iloc[0]
    SUMMARY.write_text(
        "\n".join([
            "# SRTM Peru Pilot Tile Preflight Summary",
            "",
            f"Updated: {date.today().isoformat()}",
            "",
            "Status: ready to download, not downloaded.",
            "",
            f"- Dataset id: `{DATASET_ID}`",
            f"- Destination: `{DESTINATION}`",
            f"- Boundary source: `outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg`",
            f"- Buffer: `{BUFFER_M} m` around PE1 boundary (metric CRS {METRIC_CRS})",
            f"- Bbox EPSG:4326: `{bbox['min_lon']:.6f}, {bbox['min_lat']:.6f}, {bbox['max_lon']:.6f}, {bbox['max_lat']:.6f}`",
            f"- Tile count: `{len(tiles)}`",
            f"- Tiles: `{', '.join(tiles['tile_name'])}`",
            "",
            "This file is a pre-download manifest only. No SRTM file was downloaded.",
            "",
        ]),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    boundary = load_pe1_boundary()
    bbox_gdf = buffered_bbox(boundary)
    tiles = build_tile_plan(bbox_gdf)
    write_outputs(bbox_gdf, tiles)
    print(tiles.drop(columns="geometry").to_string(index=False))
    print(f"tile plan written to {OUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
