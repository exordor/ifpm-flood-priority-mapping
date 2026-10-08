#!/usr/bin/env python3
"""Run the Supervisor-weight Peru PIM chain on the active Secocha extent.

The spatial support is the diagnostic A7367 Map 7 coordinate-frame extent. It
is neither an event footprint nor a hydrological catchment. Mining remains an
external comparison overlay and is not included in the PIM score.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window
from rasterio.windows import transform as window_transform


ROOT = Path(__file__).resolve().parents[2]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module(ROOT / "bin/factors/run_goslar_peru_style_chain.py", "ifpm_shared_chain")
rain = load_module(
    ROOT / "bin/criteria/build_peru_hybas_l7_6070641200_rainfall_criterion.py",
    "ifpm_peru_rainfall",
)

BOUNDARY_ID = "peru_secocha_a7367_reference_extent_v1"
METRIC_CRS = "EPSG:32718"
RES_M = 30.0
NODATA = -9999.0
PREFIX = "peru_secocha_a7367_reference_extent_v1"
BOUNDARY_GPKG = ROOT / "outputs/peru_secocha_boundary/peru_secocha_active_boundary.gpkg"
BOUNDARY_LAYER = "secocha_active_boundary"
OUT_BASE = ROOT / f"outputs/{BOUNDARY_ID}"
SRTM_ZIP = ROOT / "data/raw/srtm_1arcsec_peru_secocha/S16W074.SRTMGL1.hgt.zip"
WORLDCOVER_FILE = ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif"
WORLDPOP_FILE = ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj.tif"
ROADS_FILE = ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_roads_free_1.shp"
PROTECTED_QUERY = ROOT / "data/raw/sernanp_peru_secocha/secocha_sernanp_layer0_query.geojson"
MINING_OVERLAY = ROOT / "data/raw/ingemmet_catastro_minero_peru_secocha/secocha_pequena_mineria.gpkg"

RAIN_DIR = OUT_BASE / "rainfall_criterion"
TERRAIN_DIR = OUT_BASE / "terrain_preprocessing"
HYDRO_DIR = OUT_BASE / "hydrology_derivatives"
LS_DIR = OUT_BASE / "ls_factor"
K_DIR = OUT_BASE / "soil_k_factor"
WC_DIR = OUT_BASE / "worldcover_factors"
CRITERIA_DIR = OUT_BASE / "criteria_stack/criteria"
EXPOSURE_DIR = OUT_BASE / "exposure_indicators"
ES_DIR = OUT_BASE / "environmental_sensitivity"
SCENARIO_DIR = OUT_BASE / "priority_scenarios"

DEM = TERRAIN_DIR / f"{PREFIX}_dem_utm18s_30m.tif"
DEM_BUFFERED = TERRAIN_DIR / f"{PREFIX}_dem_buffered_utm18s_30m.tif"
SLOPE = TERRAIN_DIR / f"{PREFIX}_slope_degrees_utm18s_30m.tif"
SLOPE_BUFFERED = TERRAIN_DIR / f"{PREFIX}_slope_degrees_buffered_utm18s_30m.tif"
RAINFALL = RAIN_DIR / "rainfall_climatology_0_1_PROVISIONAL_30m.tif"
PRIORITY_FILENAME = "priority_secocha_direct_pim.tif"
SOILGRIDS_DIR = ROOT / "data/raw/soilgrids_250m_peru_secocha"
SOILGRIDS_K_SNAPSHOT = SOILGRIDS_DIR / "k_factor_0_30cm_avg_250m_us.tif"
SOILGRIDS_DIAGNOSTICS = SOILGRIDS_DIR / "soilgrids_peru_secocha_diagnostics.json"
SOILGRIDS_PULL_SCRIPT = "bin/acquire/pull_secocha_soilgrids_window.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lineage_record(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}


def configure_shared_chain() -> None:
    """Bind the tested shared stages to the Secocha paths and reference grid."""
    assignments = {
        "FOCUS_AREA_ID": BOUNDARY_ID, "METRIC_CRS": METRIC_CRS, "RES_M": RES_M,
        "BOUNDARY_GPKG": BOUNDARY_GPKG, "BOUNDARY_LAYER": BOUNDARY_LAYER,
        "FOCUS_EXTENT_WGS84": tuple(gpd.read_file(BOUNDARY_GPKG, layer=BOUNDARY_LAYER).to_crs(4326).total_bounds),
        "OUT_BASE": OUT_BASE, "RAIN_DIR": RAIN_DIR, "TERRAIN_DIR": TERRAIN_DIR,
        "HYDRO_DIR": HYDRO_DIR, "LS_DIR": LS_DIR, "K_DIR": K_DIR, "WC_DIR": WC_DIR,
        "CRITERIA_DIR": CRITERIA_DIR, "EXPOSURE_DIR": EXPOSURE_DIR, "ES_DIR": ES_DIR,
        "SCENARIO_DIR": SCENARIO_DIR, "TMP_WBT": OUT_BASE / "_raw_wbt",
        "DEM": DEM, "DEM_BUFFERED": DEM_BUFFERED, "SLOPE": SLOPE,
        "SLOPE_BUFFERED": SLOPE_BUFFERED,
        "FILLED": HYDRO_DIR / f"{PREFIX}_dem_filled.tif",
        "D8_PNTR": HYDRO_DIR / f"{PREFIX}_flow_direction_d8.tif",
        "FLOW_ACC_CELLS": HYDRO_DIR / f"{PREFIX}_flow_accumulation.tif",
        "FLOW_ACC_SCA": HYDRO_DIR / f"{PREFIX}_flow_accumulation_sca.tif",
        "STREAMS_T500": HYDRO_DIR / f"{PREFIX}_streams_t500.tif",
        "DISTANCE": HYDRO_DIR / f"{PREFIX}_distance_to_drainage_t500.tif",
        "TWI": HYDRO_DIR / f"{PREFIX}_twi.tif",
        "LS_CAPPED": LS_DIR / f"{PREFIX}_ls_factor_capped50_hillslope_30m.tif",
        "CFACTOR": WC_DIR / "c_factor_30m.tif",
        "LAND_USE_PRESSURE": WC_DIR / "land_use_pressure_30m.tif",
        "LAND_COVER_RUNOFF": WC_DIR / "land_cover_runoff_pressure_30m.tif",
        "BARE_SOIL_LOSS": WC_DIR / "bare_soil_vegetation_loss_proxy_30m.tif",
        "BUILT_UP_PRESSURE": WC_DIR / "built_up_pressure_30m.tif",
        "AGRICULTURAL_PRESSURE": WC_DIR / "agricultural_pressure_30m.tif",
        "K_ALIGNED": K_DIR / "soil_k_factor_aligned_250m_effective_30m.tif",
        "K_SCORED": K_DIR / "soil_k_factor_0_1.tif",
        "SOILGRIDS_K_SNAPSHOT": SOILGRIDS_K_SNAPSHOT,
        "SOILGRIDS_DIAGNOSTICS": SOILGRIDS_DIAGNOSTICS,
        "SOILGRIDS_PULL_SCRIPT": SOILGRIDS_PULL_SCRIPT,
        "ROADS": ROADS_FILE, "ROAD_ACCESS": CRITERIA_DIR / "road_access_proximity_0_1.tif",
        "RAINFALL": RAINFALL, "WORLDCOVER_FILE": WORLDCOVER_FILE,
        "PRIORITY_FILENAME": PRIORITY_FILENAME,
    }
    for name, value in assignments.items():
        setattr(base, name, value)


configure_shared_chain()


def stage_dem() -> None:
    if not SRTM_ZIP.exists():
        raise FileNotFoundError(SRTM_ZIP)
    TERRAIN_DIR.mkdir(parents=True, exist_ok=True)
    geom_m = base.load_boundary_geometry(METRIC_CRS)
    bounds = geom_m.buffer(1000).bounds
    width = int(np.ceil((bounds[2] - bounds[0]) / RES_M))
    height = int(np.ceil((bounds[3] - bounds[1]) / RES_M))
    transform = from_origin(bounds[0], bounds[3], RES_M, RES_M)
    src_url = f"zip://{SRTM_ZIP.resolve()}!S16W074.hgt"
    buffered = np.full((height, width), NODATA, dtype="float32")
    with rasterio.open(src_url) as src:
        reproject(
            source=src.read(1), destination=buffered,
            src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
            dst_transform=transform, dst_crs=METRIC_CRS, dst_nodata=NODATA,
            resampling=Resampling.bilinear,
        )
    base.write_raster(DEM_BUFFERED, buffered, transform, METRIC_CRS)
    mask = geometry_mask([geom_m], out_shape=buffered.shape, transform=transform, invert=True)
    rows, cols = np.where(mask)
    if not rows.size:
        raise RuntimeError("active Secocha boundary does not intersect the SRTM grid")
    row0, row1, col0, col1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
    window = Window.from_slices((row0, row1), (col0, col1))
    cropped = buffered[row0:row1, col0:col1].copy()
    cropped[~mask[row0:row1, col0:col1]] = NODATA
    base.write_raster(DEM, cropped, window_transform(window, transform), METRIC_CRS)


def stage_rainfall() -> None:
    RAIN_DIR.mkdir(parents=True, exist_ok=True)
    ref = base.ref_profile()
    inside = base.boundary_mask(ref)
    bounds = gpd.read_file(BOUNDARY_GPKG, layer=BOUNDARY_LAYER).to_crs(4326).total_bounds
    win_bounds = (bounds[0] - 0.2, bounds[1] - 0.2, bounds[2] + 0.2, bounds[3] + 0.2)
    native, meta = rain.fetch_rainy_season_mean(win_bounds)
    aligned = rain.resample_to_reference(native, meta, ref)
    aligned, fill_report = rain.fill_edge_nodata(aligned, inside)
    score, low, high = rain.normalize_within_boundary(aligned, inside)
    base.write_raster(RAIN_DIR / "rainfall_dec_mar_2014_2024_mean_mm_30m_resample.tif",
                      np.where(np.isfinite(aligned), aligned, NODATA), ref["transform"], ref["crs"])
    base.write_raster(RAINFALL, np.where(np.isfinite(score), score, NODATA), ref["transform"], ref["crs"])
    (RAIN_DIR / "rainfall_manifest.json").write_text(json.dumps({
        "source": "CHIRPS v3.0 Latin America monthly GeoTIFFs",
        "season": "December-March", "seasons": "2014/15-2023/24",
        "native_resolution": "0.05 degree (approximately 5 km)",
        "target_grid": f"{METRIC_CRS}, 30 m overlay grid",
        "resampling": "bilinear; no new spatial information implied",
        "normalization": {"method": "2nd-98th percentile within active extent", "low_mm": low, "high_mm": high},
        "edge_fill": fill_report, "claim_level": "sensitivity_scenario",
    }, indent=2) + "\n", encoding="utf-8")


def stage_protected_areas() -> None:
    ref = base.ref_profile()
    inside = base.boundary_mask(ref)
    if not PROTECTED_QUERY.exists():
        raise FileNotFoundError(PROTECTED_QUERY)
    confirmed = gpd.read_file(PROTECTED_QUERY)
    if len(confirmed):
        raise RuntimeError("protected-area query is no longer empty; rasterization rule needs review")
    arr = np.full(inside.shape, np.nan, dtype="float32")
    arr[inside] = 0.0
    base.write_raster(ES_DIR / "protected_area_context_0_1.tif",
                      np.where(np.isfinite(arr), arr, NODATA), ref["transform"], ref["crs"])
    (ES_DIR / "protected_area_manifest.json").write_text(json.dumps({
        "source": "SERNANP official ArcGIS layer 0 query",
        "query_result_features": 0, "query_radius_km": 25,
        "interpretation": "confirmed absence in queried national definitive layer; score 0 inside extent",
        "limitation": "does not cover unqueried regional, private, or transitional categories",
        "claim_level": "provisional",
    }, indent=2) + "\n", encoding="utf-8")


def stage_exposure() -> None:
    ref = base.ref_profile()
    inside = base.boundary_mask(ref)
    dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    with rasterio.open(WORLDPOP_FILE) as src:
        source = src.read(1).astype("float32")
        if src.nodata is not None:
            source[source == src.nodata] = np.nan
        reproject(source=source, destination=dst, src_transform=src.transform, src_crs=src.crs,
                  src_nodata=np.nan, dst_transform=ref["transform"], dst_crs=ref["crs"],
                  dst_nodata=np.nan, resampling=Resampling.sum)
    dst[~inside] = np.nan
    pop, low, high = base.normalize_2_98(dst, inside)
    built = base.read_band(base.BUILT_UP_PRESSURE, ref)
    road = base.read_band(base.ROAD_ACCESS, ref)
    overall = base.weighted_average([(road, .35), (pop, .35), (built, .30)], inside)
    layers = {
        "population_exposure_0_1.tif": pop,
        "built_infrastructure_exposure_0_1.tif": built,
        "infrastructure_exposure_0_1.tif": built,
        "exposure_indicators_0_1.tif": overall,
    }
    for name, arr in layers.items():
        base.write_raster(EXPOSURE_DIR / name, np.where(np.isfinite(arr), arr, NODATA), ref["transform"], ref["crs"])
    (EXPOSURE_DIR / "exposure_manifest.json").write_text(json.dumps({
        "population_source": "WorldPop Peru 2020 UN-adjusted population counts",
        "population_resampling": "sum to 30 m overlay grid",
        "population_normalization": {"method": "2nd-98th percentile", "low": low, "high": high},
        "critical_infrastructure_proxy": "ESA WorldCover built-up class; not a facility inventory",
        "weights": base.SV_COMPONENTS, "claim_level": "provisional",
    }, indent=2) + "\n", encoding="utf-8")


def stage_priority() -> None:
    ref = base.ref_profile()
    mask = base.boundary_mask(ref)
    (SCENARIO_DIR / "scenarios").mkdir(parents=True, exist_ok=True)
    (SCENARIO_DIR / "pim_criteria").mkdir(parents=True, exist_ok=True)
    components = {
        "rainfall_climatology": base.read_band(CRITERIA_DIR / "rainfall_climatology_0_1.tif", ref),
        "twi_wetness": base.read_band(CRITERIA_DIR / "twi_wetness_0_1.tif", ref),
        "drainage_proximity": base.read_band(CRITERIA_DIR / "drainage_proximity_0_1.tif", ref),
        "soil_k_factor": base.read_band(CRITERIA_DIR / "soil_k_factor_0_1.tif", ref),
        "ls_factor": base.read_band(CRITERIA_DIR / "ls_factor_0_1.tif", ref),
        "c_factor": base.read_band(CRITERIA_DIR / "c_factor_0_1.tif", ref),
        "land_cover_pressure": base.read_band(CRITERIA_DIR / "land_cover_pressure_0_1.tif", ref),
        "bare_soil_vegetation_loss": base.read_band(CRITERIA_DIR / "bare_soil_vegetation_loss_0_1.tif", ref),
        "built_agriculture_road_expansion": base.read_band(CRITERIA_DIR / "built_agriculture_road_expansion_0_1.tif", ref),
        "road_access_proximity": base.read_band(CRITERIA_DIR / "road_access_proximity_0_1.tif", ref),
        "water_wetland_context": base.read_band(ES_DIR / "water_wetland_context_0_1.tif", ref),
        "protected_ecological_context": base.read_band(ES_DIR / "protected_area_context_0_1.tif", ref),
        "settlement_population": base.read_band(EXPOSURE_DIR / "population_exposure_0_1.tif", ref),
        "critical_infrastructure": base.read_band(EXPOSURE_DIR / "built_infrastructure_exposure_0_1.tif", ref),
    }

    def strict(weights: dict[str, float]) -> np.ndarray:
        arrays = [components[name] for name in weights]
        common = mask.copy()
        for arr in arrays:
            common &= np.isfinite(arr)
        out = np.full(mask.shape, np.nan, dtype="float32")
        out[common] = sum(components[name][common] * weight for name, weight in weights.items())
        return np.clip(out, 0, 1)

    criteria = {
        "flood_hazard": strict(base.FH_COMPONENTS),
        "sediment": strict(base.SE_COMPONENTS),
        "landuse_asm": strict(base.LU_COMPONENTS),
        "environmental": strict(base.ES_COMPONENTS),
        "socioeconomic": strict(base.SV_COMPONENTS),
    }
    for name, arr in criteria.items():
        base.write_raster(SCENARIO_DIR / "pim_criteria" / f"{name}_0_1.tif",
                          np.where(np.isfinite(arr), arr, NODATA), ref["transform"], ref["crs"])
    pim, available, count = base.combine_common_support(criteria, base.MAIN_WEIGHTS, mask)
    base.write_raster(SCENARIO_DIR / "scenarios" / PRIORITY_FILENAME,
                      np.where(np.isfinite(pim), pim, NODATA), ref["transform"], ref["crs"])
    base.write_raster(SCENARIO_DIR / "available_main_weight.tif",
                      np.where(mask, available, NODATA), ref["transform"], ref["crs"])
    base.write_raster(SCENARIO_DIR / "criteria_evidence_count.tif",
                      np.where(mask, count.astype("float32"), NODATA), ref["transform"], ref["crs"])
    manifest_path = SCENARIO_DIR / "run_manifest.json"
    priority_path = SCENARIO_DIR / "scenarios" / PRIORITY_FILENAME
    criteria_paths = {
        name: SCENARIO_DIR / "pim_criteria" / f"{name}_0_1.tif"
        for name in criteria
    }
    manifest = {
        "focus_area_id": BOUNDARY_ID,
        "metric_crs": METRIC_CRS,
        "reference_resolution_m": RES_M,
        "boundary_id": BOUNDARY_ID,
        "boundary_path": str(BOUNDARY_GPKG.relative_to(ROOT)),
        "boundary_sha256": sha256(BOUNDARY_GPKG),
        "boundary_role": "A7367 Map 7 coordinate-frame diagnostic extent; not catchment or event footprint",
        "enters_peru_active_pim": True,
        "enters_pim_score": True,
        "claim_level": "provisional",
        "experiment_id": "supervisor_full_spec_v07_secocha",
        "main_weights": base.MAIN_WEIGHTS,
        "component_weights": {"FH": base.FH_COMPONENTS, "SE": base.SE_COMPONENTS,
                              "LU": base.LU_COMPONENTS, "ES": base.ES_COMPONENTS,
                              "SV": base.SV_COMPONENTS},
        "nodata_policy": "strict common support within each criterion and across the five main criteria; no weight renormalization on missing components",
        "mining_role": "external overlay only; excluded from PIM score",
        "priority_raster": f"scenarios/{PRIORITY_FILENAME}",
        "priority_raster_lineage": lineage_record(priority_path),
        "criterion_raster_lineage": {name: lineage_record(path) for name, path in criteria_paths.items()},
        "input_lineage": {
            "implementation": lineage_record(Path(__file__).resolve()),
            "boundary": lineage_record(BOUNDARY_GPKG),
            "long_term_rainfall_manifest": lineage_record(RAIN_DIR / "rainfall_manifest.json"),
            "protected_area_manifest": lineage_record(ES_DIR / "protected_area_manifest.json"),
            "exposure_manifest": lineage_record(EXPOSURE_DIR / "exposure_manifest.json"),
        },
        "data_sources": {
            "dem": "NASA SRTMGL1 S16W074, 1 arc-second",
            "rainfall": "CHIRPS v3 Dec-Mar 2014/15-2023/24, 0.05 degree native",
            "land_cover": "ESA WorldCover 2021 v200, 10 m native",
            "soil": "ISRIC SoilGrids 250 m effective resolution",
            "roads": "Geofabrik Peru OSM extract",
            "population": "WorldPop Peru 2020 UN-adjusted",
            "protected_areas": "SERNANP layer 0 query; zero features within 25 km",
            "mining_external_overlay": str(MINING_OVERLAY.relative_to(ROOT)),
        },
        "run_date": date.today().isoformat(),
        "note": "Active Peru Secocha prototype using unchanged Supervisor v07 weights; not a final flood-risk result.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


STAGES = ["dem", "slope", "hydrology", "ls_factor", "worldcover_cfactor",
          "soilgrids_kfactor", "osm_roads", "rainfall", "protected_areas",
          "criteria_stack", "exposure_indicators", "environmental_sensitivity",
          "priority_scenarios"]
FUNCS = {
    "dem": stage_dem, "slope": base.stage_slope, "hydrology": base.stage_hydrology,
    "ls_factor": base.stage_ls_factor, "worldcover_cfactor": base.stage_worldcover_cfactor,
    "soilgrids_kfactor": base.stage_soilgrids_kfactor, "osm_roads": base.stage_osm_roads,
    "rainfall": stage_rainfall, "protected_areas": stage_protected_areas,
    "criteria_stack": base.stage_criteria_stack, "exposure_indicators": stage_exposure,
    "environmental_sensitivity": base.stage_environmental_sensitivity,
    "priority_scenarios": stage_priority,
}


def catalog() -> dict:
    return {
        "boundary_id": BOUNDARY_ID, "boundary_role": "diagnostic A7367 Map 7 coordinate-frame extent",
        "metric_crs": METRIC_CRS, "reference_resolution_m": RES_M,
        "experiment_id": "supervisor_full_spec_v07_secocha", "claim_level": "provisional",
        "weights_changed": False, "main_weights": base.MAIN_WEIGHTS,
        "component_weights": {"FH": base.FH_COMPONENTS, "SE": base.SE_COMPONENTS,
                              "LU": base.LU_COMPONENTS, "ES": base.ES_COMPONENTS, "SV": base.SV_COMPONENTS},
        "slope_buffered_path": str(SLOPE_BUFFERED.relative_to(ROOT)),
        "soilgrids_snapshot_path": str(SOILGRIDS_K_SNAPSHOT.relative_to(ROOT)),
        "mining_role": "external overlay only", "stages": STAGES,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--max-stage", choices=STAGES)
    parser.add_argument("--start-stage", choices=STAGES, default=STAGES[0])
    args = parser.parse_args()
    if args.catalog_only:
        print(json.dumps(catalog(), indent=2))
        return
    start = STAGES.index(args.start_stage)
    end = STAGES.index(args.max_stage) if args.max_stage else len(STAGES) - 1
    if end < start:
        raise SystemExit("--max-stage must not precede --start-stage")
    for stage in STAGES[start:end + 1]:
        print(f"[peru-secocha] {stage} ...", flush=True)
        FUNCS[stage]()


if __name__ == "__main__":
    main()
