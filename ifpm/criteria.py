"""Criteria stack (0-1 components), exposure (SV) and environmental sensitivity (ES).

Ported from stage_criteria_stack / stage_exposure_indicators /
stage_environmental_sensitivity in bin/factors/run_goslar_pim_chain.py and the WorldPop
exposure stage of run_secocha_pim_chain.py.
"""

from __future__ import annotations

import json

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject
from scipy.ndimage import distance_transform_edt

from .proximity import decay
from .scoring import weighted_average


def bare_soil_source(ctx):
    """Vegetation-loss layer: CLMS tree-cover loss, else CLMS bare soil, else WorldCover proxy."""
    p = ctx.p
    for key in ("CLMS_TCD_LOSS", "CLMS_BARE_SOIL"):
        if p.get(key) is not None and p[key].exists():
            return p[key]
    return p["BARE_SOIL_LOSS"]


def build_be_proxy(built_up, agriculture, road_access, mask, weights):
    """Built/agriculture/road expansion: max(built, agriculture) mixed with road access."""
    developed_or_agricultural = np.maximum(built_up, agriculture)
    return weighted_average([(developed_or_agricultural, weights[0]), (road_access, weights[1])], mask)


def stage_criteria_stack(ctx) -> None:
    """Scale the terrain and land-cover components to 0-1 and write the criteria stack."""
    p = ctx.p
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    rasters = {
        "rainfall": ctx.read_band(p["RAINFALL"], ref),
        "twi": ctx.read_band(p["TWI"], ref),
        "drainage": ctx.read_band(p["DISTANCE"], ref),
        "ls_factor": ctx.read_band(p["LS_CAPPED"], ref),
        "c_factor": ctx.read_band(p["CFACTOR"], ref),
        "soil_k_factor": ctx.read_band(p["K_SCORED"], ref),
        "land_cover_runoff_pressure": ctx.read_band(p["LAND_COVER_RUNOFF"], ref),
        "bare_soil_vegetation_loss": ctx.read_band(bare_soil_source(ctx), ref),
        "built_up_pressure": ctx.read_band(p["BUILT_UP_PRESSURE"], ref),
        "agricultural_pressure": ctx.read_band(p["AGRICULTURAL_PRESSURE"], ref),
        "road_access_proximity": ctx.read_band(p["ROAD_ACCESS"], ref),
    }
    # The call order fixes the frozen-anchor keys criteria_stack:0..3.
    twi_std, _, _ = ctx.normalize(rasters["twi"], mask)
    drain_std, _, _ = ctx.normalize(rasters["drainage"], mask, invert=True)
    ls_std, _, _ = ctx.normalize(rasters["ls_factor"], mask)
    c_std, _, _ = ctx.normalize(rasters["c_factor"], mask)
    road_std = rasters["road_access_proximity"]
    built_agri_road = build_be_proxy(rasters["built_up_pressure"], rasters["agricultural_pressure"],
                                     road_std, mask, ctx.cfg["weights"]["built_agriculture_road"])
    criteria = {
        "rainfall_climatology": rasters["rainfall"],
        "twi_wetness": twi_std,
        "drainage_proximity": drain_std,
        "ls_factor": ls_std,
        "c_factor": c_std,
        "soil_k_factor": rasters["soil_k_factor"],
        "land_cover_pressure": rasters["land_cover_runoff_pressure"],
        "bare_soil_vegetation_loss": rasters["bare_soil_vegetation_loss"],
        "built_agriculture_road_expansion": built_agri_road,
        "road_access_proximity": road_std,
    }
    ctx.mkdir(p["CRITERIA_DIR"])
    for name, arr in criteria.items():
        arr = np.clip(arr, 0.0, 1.0).astype("float32")
        arr[~mask] = np.nan
        ctx.write_raster(p["CRITERIA_DIR"] / f"{name}_0_1.tif", np.where(np.isfinite(arr), arr, ctx.nodata),
                         ref["transform"], ref["crs"])


def _sv_parts(ctx, road, population, infrastructure):
    """SV components in the configured order with their weights."""
    layers = {"road_access_proximity": road, "settlement_population": population,
              "critical_infrastructure": infrastructure}
    return [(layers[name], weight) for name, weight in ctx.cfg["weights"]["components"]["socioeconomic"].items()]


def stage_exposure_zensus(ctx) -> None:
    """Goslar SV: Zensus 2022 population (sum-resampled) and OSM facility proximity."""
    import geopandas as gpd
    from rasterio.features import rasterize
    from shapely.geometry import mapping
    p = ctx.p
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    ctx.mkdir(p["EXPOSURE_DIR"])
    road = ctx.read_band(p["ROAD_ACCESS"], ref)
    population_dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    zensus_tif = p["ZENSUS_TIF"]
    if not zensus_tif.exists():
        raise FileNotFoundError(f"Zensus 2022 grid missing: {zensus_tif}")
    with rasterio.open(zensus_tif) as src:
        reproject(
            source=src.read(1).astype("float32"), destination=population_dst,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=ref["transform"], dst_crs=ref["crs"],
            resampling=Resampling.sum,
        )
    population_dst[~mask] = np.nan
    pop_valid = population_dst[mask & np.isfinite(population_dst)]
    if pop_valid.size == 0:
        raise RuntimeError("no Zensus 2022 data inside the boundary")
    pop_std, low, high = ctx.normalize(population_dst, mask, constant_policy="zeros")
    facilities_path = p["INFRASTRUCTURE"]
    if not facilities_path.exists():
        raise FileNotFoundError(f"OSM infrastructure candidates missing: {facilities_path}")
    facilities = gpd.read_file(facilities_path, layer=ctx.infrastructure_layer).to_crs(ref["crs"])
    facility_shapes = [(mapping(g), 1) for g in facilities.geometry if g is not None and not g.is_empty]
    if not facility_shapes:
        raise ValueError("no OSM infrastructure candidates available")
    facility_mask = rasterize(facility_shapes, out_shape=(ref["height"], ref["width"]),
                              transform=ref["transform"], fill=0, dtype="uint8")
    facility_distance = distance_transform_edt(facility_mask == 0, sampling=(ctx.res, ctx.res))
    built = decay(facility_distance, ctx.cfg["decay_m"]["facilities"])
    built[~mask] = np.nan
    mix = ctx.cfg["weights"]["infrastructure_mix"]
    infra = weighted_average([(pop_std, mix[0]), (built, mix[1])], mask)
    sv = weighted_average(_sv_parts(ctx, road, pop_std, built), mask)
    for name, arr in [("population_exposure_0_1.tif", pop_std),
                      ("built_infrastructure_exposure_0_1.tif", built),
                      ("infrastructure_exposure_0_1.tif", infra),
                      ("exposure_indicators_0_1.tif", sv)]:
        ctx.write_raster(p["EXPOSURE_DIR"] / name, np.where(np.isfinite(arr), arr, ctx.nodata),
                         ref["transform"], ref["crs"])


def stage_exposure_worldpop(ctx) -> None:
    """Secocha SV: WorldPop population (sum-resampled); WorldCover built-up as infrastructure."""
    p = ctx.p
    ref = ctx.ref_profile()
    inside = ctx.boundary_mask(ref)
    dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    with rasterio.open(ctx.cfg.path(ctx.cfg["exposure"]["dataset"])) as src:
        source = src.read(1).astype("float32")
        if src.nodata is not None:
            source[source == src.nodata] = np.nan
        reproject(source=source, destination=dst, src_transform=src.transform, src_crs=src.crs,
                  src_nodata=np.nan, dst_transform=ref["transform"], dst_crs=ref["crs"],
                  dst_nodata=np.nan, resampling=Resampling.sum)
    dst[~inside] = np.nan
    pop, low, high = ctx.normalize(dst, inside)
    built = ctx.read_band(p["BUILT_UP_PRESSURE"], ref)
    road = ctx.read_band(p["ROAD_ACCESS"], ref)
    overall = weighted_average(_sv_parts(ctx, road, pop, built), inside)
    layers = {
        "population_exposure_0_1.tif": pop,
        "built_infrastructure_exposure_0_1.tif": built,
        "infrastructure_exposure_0_1.tif": built,
        "exposure_indicators_0_1.tif": overall,
    }
    for name, arr in layers.items():
        ctx.write_raster(p["EXPOSURE_DIR"] / name, np.where(np.isfinite(arr), arr, ctx.nodata),
                         ref["transform"], ref["crs"])
    ctx.write_text(p["EXPOSURE_DIR"] / "exposure_manifest.json", json.dumps({
        "population_source": "WorldPop Peru 2020 UN-adjusted population counts",
        "population_resampling": "sum to 30 m overlay grid",
        "population_normalization": {"method": "2nd-98th percentile", "low": low, "high": high},
        "critical_infrastructure_proxy": "ESA WorldCover built-up class; not a facility inventory",
        "weights": ctx.cfg["weights"]["components"]["socioeconomic"], "claim_level": "provisional",
    }, indent=2) + "\n")


def stage_environmental_sensitivity(ctx) -> None:
    """ES: proximity to WorldCover water/wetland classes, mixed with protected-area context."""
    p = ctx.p
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    ctx.mkdir(p["ES_DIR"])
    ctx.read_band(p["LAND_COVER_RUNOFF"], ref)  # grid check only, as in the old chain
    with rasterio.open(p["WORLDCOVER_FILE"]) as src:
        wc = src.read(1)
        src_transform, src_crs = src.transform, src.crs
    sensitive = np.isin(wc, ctx.cfg["water_wetland_classes"]).astype("float32")
    dst = np.full((ref["height"], ref["width"]), 0.0, dtype="float32")
    reproject(
        source=sensitive, destination=dst,
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=ref["transform"], dst_crs=ref["crs"],
        resampling=Resampling.nearest,
    )
    dist = distance_transform_edt(dst == 0, sampling=(ctx.res, ctx.res))
    water_ctx = decay(dist, ctx.cfg["decay_m"]["water"])
    water_ctx[~mask] = np.nan
    protected_ctx = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    if (p["ES_DIR"] / "protected_area_context_0_1.tif").exists():
        protected_ctx = ctx.read_band(p["ES_DIR"] / "protected_area_context_0_1.tif", ref)
    layers = {"water_wetland_context": water_ctx, "protected_ecological_context": protected_ctx}
    es = weighted_average([(layers[name], weight) for name, weight
                           in ctx.cfg["weights"]["components"]["environmental"].items()], mask)
    for name, arr in [("water_wetland_context_0_1.tif", water_ctx),
                      ("protected_area_context_0_1.tif", protected_ctx),
                      ("environmental_sensitivity_0_1.tif", es)]:
        ctx.write_raster(p["ES_DIR"] / name, np.where(np.isfinite(arr), arr, ctx.nodata),
                         ref["transform"], ref["crs"])
