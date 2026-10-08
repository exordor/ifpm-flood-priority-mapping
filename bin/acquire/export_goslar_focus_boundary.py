#!/usr/bin/env python3
"""Export the Goslar focus-area boundary for the Peru-style processing chain.

The Goslar focus area follows the ZLW print-layout extent of ZDIN-2024.qgz
(WGS84 10.3646-10.4194 E, 51.8544-51.9089 N). This is the agreed focus box for
the Goslar 2017 flood catchment prototype. It is a prototype-only boundary,
NOT a validated scientific study area and NOT a PIM validation of Peru.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import geopandas as gpd
from pyproj import Geod
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/goslar_focus_boundary"
OUT_GPKG = OUT_DIR / "goslar_focus_boundary.gpkg"

FOCUS_EXTENT_WGS84 = (10.3646, 51.8544, 10.4194, 51.9089)
BOUNDARY_ID = "goslar_focus_extent_v1"
GEOD = Geod(ellps="WGS84")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    min_lon, min_lat, max_lon, max_lat = FOCUS_EXTENT_WGS84
    geometry = box(min_lon, min_lat, max_lon, max_lat)
    area, _ = GEOD.geometry_area_perimeter(geometry)
    geo_area_km2 = round(abs(area) / 1e6, 3)

    boundary = gpd.GeoDataFrame(
        [{
            "boundary_id": BOUNDARY_ID,
            "source": "ZDIN-2024.qgz ZLW print layout extent (WGS84)",
            "study_area": "Goslar 2017 flood catchment focus area, Harz, Lower Saxony, Germany",
            "extent_min_lon": min_lon,
            "extent_min_lat": min_lat,
            "extent_max_lon": max_lon,
            "extent_max_lat": max_lat,
            "geo_area_km2": geo_area_km2,
            "crs_source": "EPSG:4326",
            "status": "prototype_focus_extent_not_final_study_area",
            "claim_level": "prototype_only",
            "export_date": date.today().isoformat(),
        }],
        geometry=[geometry],
        crs="EPSG:4326",
    )
    boundary.to_file(OUT_GPKG, layer="goslar_focus_boundary", driver="GPKG")

    manifest = {
        "boundary_id": BOUNDARY_ID,
        "extent_wgs84": list(FOCUS_EXTENT_WGS84),
        "geo_area_km2": geo_area_km2,
        "crs": "EPSG:4326",
        "metric_crs": "EPSG:32632",
        "claim_level": "prototype_only",
        "source": "ZDIN-2024.qgz ZLW print layout extent",
        "note": "Focus box only; not a validated catchment, not Peru PIM validation.",
        "export_date": date.today().isoformat(),
    }
    (OUT_DIR / "goslar_focus_boundary_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
