#!/usr/bin/env python3
"""Build physical road and water-feature distance factors for V1 from Geofabrik OSM."""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from affine import Affine
from rasterio import features
from rasterio.features import geometry_mask
from rasterio.transform import array_bounds
from rasterio.warp import transform_bounds
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/raw/geofabrik_osm_zimbabwe_prototype/zimbabwe-latest-free.gpkg.zip"
VSI_GPKG = f"/vsizip/{ARCHIVE.resolve()}/zimbabwe.gpkg"
REFERENCE = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif"
BOUNDARY = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
OUT_DIR = ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/comparable_distance_factors"
ROAD_DISTANCE = OUT_DIR / "v1_distance_to_roads_km_30m.tif"
WATER_DISTANCE = OUT_DIR / "v1_distance_to_water_features_km_30m.tif"
MANIFEST = OUT_DIR / "distance_factor_manifest.csv"
SEARCH_BUFFER_M = 25_000.0

INPUTS = [ARCHIVE, REFERENCE, BOUNDARY]
OUTPUTS = [ROAD_DISTANCE, WATER_DISTANCE, MANIFEST]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_features(layer: str, bbox: tuple[float, float, float, float], target_crs) -> gpd.GeoDataFrame:
    frame = gpd.read_file(VSI_GPKG, layer=layer, bbox=bbox, engine="pyogrio")
    if frame.empty:
        return gpd.GeoDataFrame(geometry=[], crs=target_crs)
    return frame[["geometry"]].dropna().to_crs(target_crs)


def distance_km(
    frames: list[gpd.GeoDataFrame],
    padded_shape: tuple[int, int],
    padded_transform,
    crop: tuple[slice, slice],
    inside: np.ndarray,
) -> tuple[np.ndarray, int]:
    geometries = [geom for frame in frames for geom in frame.geometry if geom is not None and not geom.is_empty]
    if not geometries:
        raise ValueError("no source features intersect the buffered V1 bounding box")
    source_mask = features.rasterize(
        ((geom, 1) for geom in geometries), out_shape=padded_shape, transform=padded_transform,
        fill=0, dtype="uint8", all_touched=True,
    ).astype(bool)
    if not source_mask.any():
        raise ValueError("source features did not rasterize on the V1 reference grid")
    distance_m = distance_transform_edt(
        ~source_mask, sampling=(abs(float(padded_transform.e)), abs(float(padded_transform.a)))
    ).astype("float32")
    result = distance_m[crop] / 1000.0
    result[~inside] = np.nan
    return result, len(geometries)


def write_raster(path: Path, data: np.ndarray, profile: dict, source_note: str) -> None:
    target = profile.copy()
    target.update(dtype="float32", nodata=-9999.0, compress="deflate", tiled=True)
    with rasterio.open(path, "w", **target) as dst:
        dst.write(np.where(np.isfinite(data), data, -9999.0).astype("float32"), 1)
        dst.update_tags(IFPM_NOTE=source_note)


def main() -> None:
    for path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    boundary_wgs84 = gpd.read_file(BOUNDARY, layer="v1_working_boundary").to_crs("EPSG:4326")
    with rasterio.open(REFERENCE) as ref:
        profile = ref.profile.copy()
        shape = (ref.height, ref.width)
        target_crs = ref.crs
        transform = ref.transform
    pixel_size = max(abs(float(transform.a)), abs(float(transform.e)))
    pad = int(math.ceil(SEARCH_BUFFER_M / pixel_size))
    padded_shape = (shape[0] + 2 * pad, shape[1] + 2 * pad)
    padded_transform = transform * Affine.translation(-pad, -pad)
    projected_bounds = array_bounds(*padded_shape, padded_transform)
    bbox = transform_bounds(target_crs, "EPSG:4326", *projected_bounds, densify_pts=21)
    crop = (slice(pad, pad + shape[0]), slice(pad, pad + shape[1]))
    boundary_ref = boundary_wgs84.to_crs(target_crs)
    inside = geometry_mask(boundary_ref.geometry, out_shape=shape, transform=transform, invert=True)

    roads = load_features("gis_osm_roads_free", bbox, target_crs)
    water_lines = load_features("gis_osm_waterways_free", bbox, target_crs)
    water_areas = load_features("gis_osm_water_a_free", bbox, target_crs)
    road_distance, road_count = distance_km([roads], padded_shape, padded_transform, crop, inside)
    water_distance, water_count = distance_km([water_lines, water_areas], padded_shape, padded_transform, crop, inside)
    write_raster(ROAD_DISTANCE, road_distance, profile, "Euclidean distance in km to Geofabrik OSM road lines")
    write_raster(WATER_DISTANCE, water_distance, profile, "Euclidean distance in km to Geofabrik OSM waterways and water polygons")

    archive_hash = sha256(ARCHIVE)
    reference_hash = sha256(REFERENCE)
    boundary_hash = sha256(BOUNDARY)
    rows = [
        {
            "factor": "distance_to_roads", "output": rel(ROAD_DISTANCE),
            "source_archive": rel(ARCHIVE), "source_sha256": archive_hash,
            "reference_sha256": reference_hash, "boundary_sha256": boundary_hash,
            "layers": "gis_osm_roads_free", "source_feature_count": road_count,
            "unit": "km", "method": "Euclidean distance on EPSG:32735 reference grid",
            "search_buffer_km": SEARCH_BUFFER_M / 1000.0,
            "valid_fraction_within_boundary": round(float(np.isfinite(road_distance).sum() / inside.sum()), 6),
            "output_sha256": sha256(ROAD_DISTANCE),
            "claim_level": "diagnostic_only",
        },
        {
            "factor": "distance_to_water_features", "output": rel(WATER_DISTANCE),
            "source_archive": rel(ARCHIVE), "source_sha256": archive_hash,
            "reference_sha256": reference_hash, "boundary_sha256": boundary_hash,
            "layers": "gis_osm_waterways_free; gis_osm_water_a_free", "source_feature_count": water_count,
            "unit": "km", "method": "Euclidean distance on EPSG:32735 reference grid",
            "search_buffer_km": SEARCH_BUFFER_M / 1000.0,
            "valid_fraction_within_boundary": round(float(np.isfinite(water_distance).sum() / inside.sum()), 6),
            "output_sha256": sha256(WATER_DISTANCE),
            "claim_level": "diagnostic_only",
        },
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote comparable V1 distance factors to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
