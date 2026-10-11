"""Distance-decay proximity layers: road access and protected-area context.

Ported from stage_osm_roads / stage_protected_areas in bin/factors/run_goslar_pim_chain.py
and the Secocha protected-area stage in run_secocha_pim_chain.py.
"""

from __future__ import annotations

import json

import numpy as np
from scipy.ndimage import distance_transform_edt


def decay(distance: np.ndarray, decay_m: float) -> np.ndarray:
    """1 at the feature, falling linearly to 0 at ``decay_m``."""
    return np.clip(1.0 - distance / decay_m, 0.0, 1.0).astype("float32")


def stage_osm_roads(ctx) -> None:
    """Clip OSM roads to the boundary, rasterize on the metric grid and score proximity."""
    import geopandas as gpd
    import rasterio.features
    from shapely.geometry import mapping
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    roads_path = ctx.p["ROADS"]
    if not roads_path.exists():
        raise FileNotFoundError(f"OSM roads missing: {roads_path}")
    geometry = ctx.boundary_geometry(ref["crs"])
    # Roads are projected to the metric CRS before rasterizing onto the metric grid.
    roads = gpd.read_file(roads_path).to_crs(ref["crs"])
    clipped = gpd.clip(roads, geometry)
    if clipped.empty:
        raise ValueError("no OSM roads inside the boundary")
    shapes = [(mapping(g), 1) for g in clipped.geometry]
    raster_roads = rasterio.features.rasterize(
        shapes, out_shape=(ref["height"], ref["width"]),
        transform=ref["transform"], fill=0, dtype="float32",
    )
    road_pixels = int((raster_roads > 0).sum())
    dist = distance_transform_edt(raster_roads == 0, sampling=(ctx.res, ctx.res))
    proximity = decay(dist, ctx.cfg["decay_m"]["roads"])
    proximity[~mask] = np.nan
    ctx.write_raster(ctx.p["ROAD_ACCESS"], np.where(np.isfinite(proximity), proximity, ctx.nodata),
                     ref["transform"], ref["crs"])
    ctx.log(f"OSM roads: {len(clipped)} features, {road_pixels} rasterized pixels on metric grid")


def stage_protected_natura(ctx) -> None:
    """Natura 2000 (FFH + SPA) polygons -> protected-area proximity (10 km decay)."""
    import geopandas as gpd
    from rasterio.features import rasterize
    from shapely.geometry import mapping
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    ctx.mkdir(ctx.p["ES_DIR"])
    source = ctx.p["PROTECTED_RAW"]
    if not source.exists():
        raise FileNotFoundError(f"protected areas missing: {source}")
    protected = gpd.read_file(source).to_crs(ctx.crs)
    shapes = [(mapping(g), 1) for g in protected.geometry if g is not None and not g.is_empty]
    if not shapes:
        raise ValueError("no protected-area geometry to rasterize")
    protected_area_km2 = protected.area.sum() / 1e6
    ctx.log(f"EEA Natura2000: {len(shapes)} polygons, {protected_area_km2:.1f} km2 within query box")
    raster = rasterize(shapes, out_shape=(ref["height"], ref["width"]),
                       transform=ref["transform"], fill=0, dtype="uint8")
    dist = distance_transform_edt(raster == 0, sampling=(ctx.res, ctx.res))
    proximity = decay(dist, ctx.cfg["decay_m"]["protected"])
    proximity[~mask] = np.nan
    ctx.write_raster(ctx.p["ES_DIR"] / "protected_area_context_0_1.tif",
                     np.where(np.isfinite(proximity), proximity, ctx.nodata), ref["transform"], ref["crs"])


def stage_protected_confirmed_absence(ctx) -> None:
    """Secocha: the SERNANP query found no protected area, so the context is 0 inside."""
    import geopandas as gpd
    ref = ctx.ref_profile()
    inside = ctx.boundary_mask(ref)
    query = ctx.cfg.path(ctx.cfg["protected_areas"]["dataset"])
    if not query.exists():
        raise FileNotFoundError(query)
    confirmed = gpd.read_file(query)
    if len(confirmed):
        raise RuntimeError("protected-area query is no longer empty; rasterization rule needs review")
    arr = np.full(inside.shape, np.nan, dtype="float32")
    arr[inside] = 0.0
    ctx.write_raster(ctx.p["ES_DIR"] / "protected_area_context_0_1.tif",
                     np.where(np.isfinite(arr), arr, ctx.nodata), ref["transform"], ref["crs"])
    ctx.write_text(ctx.p["ES_DIR"] / "protected_area_manifest.json", json.dumps({
        "source": "SERNANP official ArcGIS layer 0 query",
        "query_result_features": 0, "query_radius_km": 25,
        "interpretation": "confirmed absence in queried national definitive layer; score 0 inside extent",
        "limitation": "does not cover unqueried regional, private, or transitional categories",
        "claim_level": "provisional",
    }, indent=2) + "\n")
