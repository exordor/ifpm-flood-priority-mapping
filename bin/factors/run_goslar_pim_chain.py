#!/usr/bin/env python3
"""Run the Peru-style PIM processing chain for the Goslar focus area.

Mirrors the Peru chain (preprocess DEM -> slope -> hydrology -> LS -> C-factor
-> soil K -> roads -> criteria stack -> exposure/environmental -> priority
scenarios) for the Goslar focus extent. The Goslar focus box is EPSG:4326
10.3646-10.4194 E, 51.8544-51.9089 N; metric work uses EPSG:32632 (UTM 32N)
with a 30 m reference grid.

Data sources (2026-08-07 upgrade): Copernicus DEM GLO-30 replaces SRTM 1-arcsec;
DWD REGNIE JJA 1991-2020 (official 30-y climate normal) replaces the shorter
2014-2023 window (CHIRPS does not cover 51.88 N); EEA Natura 2000 2024 (FFH +
SPA) replaces the OSM protected-area proxy; Destatis Zensus 2022 100 m grid
replaces WorldPop for the exposure indicator.

All outputs are diagnostic_only / provisional; none enter a scored Peru PIM and
none authorize final flood-risk interpretation.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import whitebox
from rasterio.features import geometry_mask
from rasterio.features import rasterize
from rasterio.fill import fillnodata
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window
from rasterio.windows import transform as window_transform
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))
from _lib.standardization import percentile_minmax

FOCUS_AREA_ID = "goslar_wrrl_basin"
METRIC_CRS = "EPSG:32632"
RES_M = 30.0
NODATA = -9999.0

BOUNDARY_GPKG = ROOT / "outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg"
BOUNDARY_LAYER = "goslar_official_hydrologic_reference_boundary"
FOCUS_EXTENT_WGS84 = (10.3646, 51.8544, 10.4194, 51.9089)

# Copernicus DEM GLO-30 tile covering the Goslar focus (N51E010).
COPERNICUS_DEM_RAW = ROOT / "data/raw/copernicus_dem_30m_goslar"
WORLDCOVER_RAW = ROOT / "data/raw/esa_worldcover_2021_goslar"
WORLDCOVER_FILE = WORLDCOVER_RAW / "ESA_WorldCover_10m_2021_v200_N51E009_Map.tif"
ZENSUS_RAW = ROOT / "data/raw/zensus2022_goslar_official_basin"
MINING_OVERLAY = ROOT / "outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg"
MINING_OVERLAY_MANIFEST = ROOT / "outputs/goslar_mining_context_overlay/mining_overlay_manifest.json"
OFFICIAL_CONTEXT_DIR = ROOT / "outputs/goslar_official_hydrology_and_flood_data"
OFFICIAL_BASINS = OFFICIAL_CONTEXT_DIR / "goslar_wfd_drainage_basins_focus_overlap.gpkg"
HWRM_FLOOD_HAZARD = OFFICIAL_CONTEXT_DIR / "goslar_hwrm_flood_hazard_boundaries_12km.gpkg"
OFFICIAL_SOURCE_LINEAGE = OFFICIAL_CONTEXT_DIR / "source_lineage.json"
OFFICIAL_CONTEXT_DIAGNOSTICS = OFFICIAL_CONTEXT_DIR / "diagnostics.json"

OUT_BASE = ROOT / "outputs/goslar_pim_chain"
RAIN_DIR = OUT_BASE / "rainfall_criterion"
TERRAIN_DIR = OUT_BASE / "terrain_preprocessing"
HYDRO_DIR = OUT_BASE / "hydrology_derivatives"
LS_DIR = OUT_BASE / "ls_factor"
K_DIR = OUT_BASE / "soil_k_factor"
WC_DIR = ROOT / "outputs/goslar_esa_worldcover_2021/c_factor"
CRITERIA_DIR = OUT_BASE / "criteria_stack/criteria"
EXPOSURE_DIR = OUT_BASE / "exposure_indicators"
ES_DIR = OUT_BASE / "environmental_sensitivity"
SCENARIO_DIR = OUT_BASE / "priority_scenarios"
PRIORITY_FILENAME = "priority_goslar_direct_pim.tif"
TMP_WBT = OUT_BASE / "_raw_wbt"

DEM = TERRAIN_DIR / "goslar_focus_dem_utm32n_30m.tif"
DEM_BUFFERED = TERRAIN_DIR / "goslar_focus_dem_buffered_utm32n_30m.tif"
SLOPE = TERRAIN_DIR / "goslar_focus_slope_degrees_utm32n_30m.tif"
SLOPE_BUFFERED = TERRAIN_DIR / "goslar_focus_slope_degrees_buffered_utm32n_30m.tif"

FILLED = HYDRO_DIR / "goslar_focus_dem_filled.tif"
D8_PNTR = HYDRO_DIR / "goslar_focus_flow_direction_d8.tif"
FLOW_ACC_CELLS = HYDRO_DIR / "goslar_focus_flow_accumulation.tif"
FLOW_ACC_SCA = HYDRO_DIR / "goslar_focus_flow_accumulation_sca.tif"
STREAMS_T500 = HYDRO_DIR / "goslar_focus_streams_t500.tif"
DISTANCE = HYDRO_DIR / "goslar_focus_distance_to_drainage_t500.tif"
TWI = HYDRO_DIR / "goslar_focus_twi.tif"

LS_CAPPED = LS_DIR / "goslar_focus_ls_factor_capped50_hillslope_30m.tif"
CFACTOR = WC_DIR / "c_factor_goslar_focus_30m.tif"
LAND_USE_PRESSURE = WC_DIR / "land_use_pressure_goslar_focus_30m.tif"
LAND_COVER_RUNOFF = WC_DIR / "land_cover_runoff_pressure_goslar_focus_30m.tif"
BARE_SOIL_LOSS = WC_DIR / "bare_soil_vegetation_loss_proxy_goslar_focus_30m.tif"
CLMS_BARE_SOIL = WC_DIR / "clms_bare_soil_after_2024_goslar_official_basin_30m.tif"
CLMS_TCD_LOSS = WC_DIR / "clms_tcd_vegetation_loss_2018_2024_goslar_official_basin_30m.tif"
BUILT_UP_PRESSURE = WC_DIR / "built_up_pressure_goslar_focus_30m.tif"
AGRICULTURAL_PRESSURE = WC_DIR / "agricultural_pressure_goslar_focus_30m.tif"

K_ALIGNED = K_DIR / "soil_k_factor_aligned_250m_effective_30m.tif"
K_SCORED = K_DIR / "soil_k_factor_0_1.tif"
# Pinned local SoilGrids 250 m K-factor snapshot (Williams 1995, US units),
# produced by bin/acquire/pull_goslar_soilgrids_window.py. Replaces the
# un-versioned /latest/ remote read.
SOILGRIDS_K_SNAPSHOT = ROOT / "data/raw/soilgrids_250m_goslar_official_basin/k_factor_0_30cm_avg_250m_us.tif"
SOILGRIDS_DIAGNOSTICS = ROOT / "data/raw/soilgrids_250m_goslar/soilgrids_goslar_diagnostics.json"
SOILGRIDS_PULL_SCRIPT = "bin/acquire/pull_goslar_soilgrids_window.py"
K_SI_FACTOR = 0.1317  # US-unit K to SI (t ha h / ha MJ mm)

ROADS = ROOT / "data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_official_basin_roads.gpkg"
INFRASTRUCTURE = ROOT / "data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_infrastructure_candidates.gpkg"
ROAD_ACCESS = CRITERIA_DIR / "road_access_proximity_0_1.tif"

STREAM_THRESHOLDS = (100, 500, 1000, 5000)
PRIMARY_THRESHOLD = 500
LS_CAP = 50.0
# Hydrology is computed on the buffered DEM so flow accumulation keeps the
# upstream contribution from outside the focus box, then derived layers are
# aligned back to the reference grid and masked to the focus extent.
HYDRO_BUFFER_M = 1000.0

# REGNIE (DWD) monthly gridded precipitation, Germany, 1 km, EPSG:31467.
REGNIE_BASE = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/monthly/precipitation"
REGNIE_RAW_DIR = ROOT / "data/raw/dwd_regnie_germany"
RAIN_SEASON_MONTHS = [6, 7, 8]
RAIN_SEASON_YEARS = list(range(1991, 2021))
RAINFALL = RAIN_DIR / "rainfall_climatology_0_1_PROVISIONAL_30m.tif"

# EEA official Natura 2000 (FFH + SPA, 2024 release) near Goslar.
PROTECTED_RAW = ROOT / "data/raw/eea_natura2000_goslar/goslar_natura2000_2024.gpkg"

MAIN_WEIGHTS = {
    "flood_hazard": 0.34,
    "sediment": 0.25,
    "landuse_asm": 0.17,
    "environmental": 0.10,
    "socioeconomic": 0.14,
}
FH_COMPONENTS = {"rainfall_climatology": 0.35, "twi_wetness": 0.25, "drainage_proximity": 0.40}
SE_COMPONENTS = {"soil_k_factor": 0.25, "ls_factor": 0.50, "c_factor": 0.25}
LU_COMPONENTS = {"land_cover_pressure": 0.40, "bare_soil_vegetation_loss": 0.35,
                 "built_agriculture_road_expansion": 0.25}
ES_COMPONENTS = {"water_wetland_context": 0.65, "protected_ecological_context": 0.35}
SV_COMPONENTS = {"road_access_proximity": 0.35, "settlement_population": 0.35,
                 "critical_infrastructure": 0.30}
REMOVED_COMPONENTS = {}
NODATA_POLICY = {
    "worldcover": "NoData preserved (not converted to 0); LUT applied to valid classes only.",
    "soilgrids": "NoData preserved; K-factor NaN cells kept NaN through standardization.",
    "hydrology_background": "Stream-mask background 0 is semantic (not-a-stream), retained.",
}

WORLDCOVER_CFACTOR_LUT = {
    10: 0.001, 20: 0.010, 30: 0.020, 40: 0.200, 50: 0.050, 60: 0.700,
    70: 0.000, 80: 0.000, 90: 0.050, 95: 0.010, 100: 0.030,
}
LAND_USE_PRESSURE_LUT = {
    10: 0.10, 20: 0.15, 30: 0.20, 40: 0.80, 50: 1.00, 60: 0.25,
    70: 0.00, 80: 0.00, 90: 0.00, 95: 0.00, 100: 0.10,
}
LAND_COVER_RUNOFF_LUT = {
    10: 0.15, 20: 0.25, 30: 0.35, 40: 0.70, 50: 1.00, 60: 0.90,
    70: 0.40, 80: 0.00, 90: 0.10, 95: 0.10, 100: 0.20,
}
BARE_SOIL_LOSS_LUT = {10: 0.0, 20: 0.0, 30: 0.0, 40: 0.0, 50: 0.0, 60: 1.0,
                      70: 0.0, 80: 0.0, 90: 0.0, 95: 0.0, 100: 0.0}
BUILT_UP_LUT = {10: 0.0, 20: 0.0, 30: 0.0, 40: 0.0, 50: 1.0, 60: 0.0,
                70: 0.0, 80: 0.0, 90: 0.0, 95: 0.0, 100: 0.0}
AGRICULTURAL_LUT = {10: 0.0, 20: 0.0, 30: 0.0, 40: 1.0, 50: 0.0, 60: 0.0,
                    70: 0.0, 80: 0.0, 90: 0.0, 95: 0.0, 100: 0.0}

STAGES = ["register_inputs", "boundary", "dem", "slope", "hydrology",
          "ls_factor", "worldcover_cfactor", "soilgrids_kfactor", "osm_roads",
          "rainfall", "protected_areas", "criteria_stack",
          "exposure_indicators", "environmental_sensitivity",
          "priority_scenarios"]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lineage_record(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    return {
        "path": rel(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def optional_lineage_record(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"path": rel(path), "exists": False}
    return {**lineage_record(path), "exists": True}


def load_boundary_geometry(dst_crs: str):
    gdf = gpd.read_file(BOUNDARY_GPKG, layer=BOUNDARY_LAYER)
    if len(gdf) != 1:
        raise ValueError(f"expected one Goslar boundary feature, got {len(gdf)}")
    return gdf.to_crs(dst_crs).geometry.iloc[0]


def write_raster(path: Path, data: np.ndarray, transform, crs: str, nodata: float = NODATA) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "height": data.shape[0], "width": data.shape[1], "count": 1,
        "dtype": "float32", "crs": crs, "transform": transform, "nodata": nodata,
        "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype("float32"), 1)


def read_band(path: Path, profile: dict) -> np.ndarray:
    with rasterio.open(path) as src:
        if str(src.crs) != str(profile["crs"]) or src.transform != profile["transform"]:
            raise ValueError(f"grid mismatch: {path}")
        if src.width != profile["width"] or src.height != profile["height"]:
            raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def ref_profile() -> dict:
    with rasterio.open(DEM) as src:
        return src.profile


def boundary_mask(profile: dict) -> np.ndarray:
    geometry = load_boundary_geometry(str(profile["crs"]))
    return geometry_mask([geometry], out_shape=(profile["height"], profile["width"]),
                         transform=profile["transform"], invert=True)


# Compatibility name used throughout the Goslar chain.  The implementation is
# centralized in ``bin/_lib/standardization.py``.
normalize_2_98 = percentile_minmax


def weighted_average(parts: list[tuple[np.ndarray, float]], mask: np.ndarray) -> np.ndarray:
    numerator = np.zeros(mask.shape, dtype="float32")
    denominator = np.zeros(mask.shape, dtype="float32")
    for layer, weight in parts:
        valid = mask & np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        denominator[valid] += weight
    out = np.divide(numerator, denominator, out=np.full(mask.shape, np.nan, dtype="float32"),
                    where=denominator > 0)
    out[~mask] = np.nan
    return out.astype("float32")


def run_wbt(tool_name: str, **kwargs) -> None:
    wbt = whitebox.WhiteboxTools()
    wbt.set_verbose_mode(False)
    tool = getattr(wbt, tool_name)
    rc = tool(**kwargs)
    if rc not in (True, 0):
        raise RuntimeError(f"whitebox {tool_name} failed (rc={rc}); args={kwargs}")


def register_inputs() -> dict:
    records = []
    moves = [
        (ROOT / "data/tmp/copernicus_dem_30m_goslar/Copernicus_DSM_COG_10_N51_00_E010_00_DEM.tif",
         COPERNICUS_DEM_RAW / "Copernicus_DSM_COG_10_N51_00_E010_00_DEM.tif"),
        (ROOT / "data/tmp/esa_worldcover_2021_goslar/ESA_WorldCover_10m_2021_v200_N51E009_Map.tif",
         WORLDCOVER_RAW / "ESA_WorldCover_10m_2021_v200_N51E009_Map.tif"),
    ]
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            continue
        if not src.exists():
            # Copernicus DEM and WorldCover are already registered; Zensus is
            # derived by an acquire step. Only move still-staged inputs.
            continue
        src.replace(dst)
        records.append(str(dst.relative_to(ROOT)))
    return {"registered": records}


def stage_dem() -> None:
    TERRAIN_DIR.mkdir(parents=True, exist_ok=True)
    buffered_geo_m = load_boundary_geometry(METRIC_CRS).buffer(1000)
    bounds_m = buffered_geo_m.bounds
    width = int(round((bounds_m[2] - bounds_m[0]) / RES_M))
    height = int(round((bounds_m[3] - bounds_m[1]) / RES_M))
    dst_transform = from_origin(bounds_m[0], bounds_m[3], RES_M, RES_M)
    dem_tif = COPERNICUS_DEM_RAW / "Copernicus_DSM_COG_10_N51_00_E010_00_DEM.tif"
    if not dem_tif.exists():
        raise FileNotFoundError(f"Copernicus DEM missing: {dem_tif}")
    with rasterio.open(dem_tif) as src:
        if src.count != 1 or str(src.crs) != "EPSG:4326":
            raise ValueError(f"unexpected Copernicus DEM profile: {src.profile}")
        src_mosaic, src_transform = src.read(1), src.transform

    buffered_data = np.full((height, width), NODATA, dtype="float32")
    reproject(
        source=src_mosaic, destination=buffered_data,
        src_transform=src_transform, src_crs="EPSG:4326", src_nodata=src.nodata,
        dst_transform=dst_transform, dst_crs=METRIC_CRS, dst_nodata=NODATA,
        resampling=Resampling.bilinear,
    )
    geometry_m = load_boundary_geometry(METRIC_CRS)
    write_raster(DEM_BUFFERED, buffered_data, dst_transform, METRIC_CRS)

    # Clip to focus boundary on the metric grid.
    mask = geometry_mask([geometry_m], out_shape=buffered_data.shape, transform=dst_transform, invert=True)
    rows, cols = np.where(mask)
    if rows.size == 0:
        raise ValueError("boundary does not intersect DEM grid")
    row0, row1 = rows.min(), rows.max() + 1
    col0, col1 = cols.min(), cols.max() + 1
    window = Window.from_slices((row0, row1), (col0, col1))
    cropped = buffered_data[row0:row1, col0:col1].copy()
    cropped[~mask[row0:row1, col0:col1]] = NODATA
    write_raster(DEM, cropped, window_transform(window, dst_transform), METRIC_CRS)


def stage_slope() -> None:
    geometry = load_boundary_geometry(METRIC_CRS)
    with rasterio.open(DEM_BUFFERED) as src:
        dem = src.read(1).astype("float64")
        nodata_mask = dem == NODATA
        values = dem.copy()
        values[nodata_mask] = np.nan
        if nodata_mask.any():
            filled = fillnodata(values, mask=(~nodata_mask).astype("uint8"))
            values = np.where(nodata_mask, filled, values)
        grad_y, grad_x = np.gradient(values, abs(src.res[1]), abs(src.res[0]))
        slope = np.degrees(np.arctan(np.sqrt(grad_x**2 + grad_y**2)))
        slope[nodata_mask] = NODATA
        slope[~np.isfinite(slope)] = NODATA
        # Full buffered slope for hydrology (TWI needs upstream slope outside
        # the focus box; hydrology runs on the buffered DEM).
        write_raster(SLOPE_BUFFERED, slope, src.transform, METRIC_CRS)
        mask = geometry_mask([geometry], out_shape=dem.shape, transform=src.transform, invert=True)
        rows, cols = np.where(mask)
        row0, row1 = rows.min(), rows.max() + 1
        col0, col1 = cols.min(), cols.max() + 1
        window = Window.from_slices((row0, row1), (col0, col1))
        cropped = slope[row0:row1, col0:col1].copy()
        cropped[~mask[row0:row1, col0:col1]] = NODATA
        write_raster(SLOPE, cropped, window_transform(window, src.transform), METRIC_CRS)


def normalize_to_reference(raw_path: Path, out_path: Path, ref: dict, mask: np.ndarray,
                           resampling=Resampling.bilinear) -> dict:
    with rasterio.open(raw_path) as src:
        data = src.read(1).astype("float64")
        nodata = src.nodata
    if nodata is not None and not np.isnan(nodata):
        data[data == nodata] = np.nan
    data[np.isinf(data)] = np.nan
    out = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    dst_transform = ref["transform"]
    with rasterio.open(raw_path) as src:
        reproject(
            source=data, destination=out,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=dst_transform, dst_crs=ref["crs"], dst_nodata=np.nan,
            resampling=resampling,
        )
    out[~mask] = np.nan
    profile = ref.copy()
    profile.update({"driver": "GTiff", "dtype": "float32", "nodata": NODATA,
                    "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256})
    write_raster(out_path, np.where(np.isfinite(out), out, NODATA), dst_transform, ref["crs"])
    inside = mask.sum()
    valid = np.isfinite(out) & mask
    values = out[valid]
    return {
        "valid_fraction": float(valid.sum() / inside) if inside else 0.0,
        "min": float(np.nanmin(values)) if values.size else None,
        "max": float(np.nanmax(values)) if values.size else None,
        "mean": float(np.nanmean(values)) if values.size else None,
    }


def stage_hydrology() -> None:
    ref = ref_profile()
    mask = boundary_mask(ref)
    TMP_WBT.mkdir(parents=True, exist_ok=True)
    for p in [FILLED, D8_PNTR, FLOW_ACC_CELLS, FLOW_ACC_SCA, STREAMS_T500, DISTANCE, TWI]:
        p.parent.mkdir(parents=True, exist_ok=True)
    # Hydrology runs on the buffered DEM so flow accumulation preserves the
    # upstream contribution from outside the focus box; each derived layer is
    # then aligned to the reference grid and masked to the focus extent.
    raw_filled = TMP_WBT / "filled.tif"
    run_wbt("fill_depressions_wang_and_liu", dem=str(DEM_BUFFERED), output=str(raw_filled), fix_flats=True)
    normalize_to_reference(raw_filled, FILLED, ref, mask)

    raw_pntr = TMP_WBT / "d8pntr.tif"
    run_wbt("d8_pointer", dem=str(raw_filled), output=str(raw_pntr), esri_pntr=False)
    # D8 pointer is categorical; nearest resampling preserves codes.
    normalize_to_reference(raw_pntr, D8_PNTR, ref, mask, resampling=Resampling.nearest)

    raw_acc_cells = TMP_WBT / "acc_cells.tif"
    # Flow accumulation uses the buffered D8 pointer so upstream contribution
    # from outside the focus box is preserved.
    run_wbt("d8_flow_accumulation", i=str(raw_pntr), output=str(raw_acc_cells),
            out_type="cells", pntr=True, esri_pntr=False)
    normalize_to_reference(raw_acc_cells, FLOW_ACC_CELLS, ref, mask)

    raw_acc_sca = TMP_WBT / "acc_sca.tif"
    run_wbt("d8_flow_accumulation", i=str(raw_pntr), output=str(raw_acc_sca),
            out_type="specific contributing area", pntr=True, esri_pntr=False)
    normalize_to_reference(raw_acc_sca, FLOW_ACC_SCA, ref, mask)

    # Streams extracted from the buffered accumulation, then nearest-resampled
    # to the reference grid (streams are categorical, not bilinear).
    raw_streams = TMP_WBT / f"streams_t{PRIMARY_THRESHOLD}.tif"
    run_wbt("extract_streams", flow_accum=str(raw_acc_cells), output=str(raw_streams),
            threshold=float(PRIMARY_THRESHOLD), zero_background=True)
    streams_on_ref = np.full((ref["height"], ref["width"]), 0.0, dtype="float32")
    with rasterio.open(raw_streams) as src:
        reproject(
            source=src.read(1).astype("float32"), destination=streams_on_ref,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=ref["transform"], dst_crs=ref["crs"],
            src_nodata=src.nodata, dst_nodata=NODATA,
            resampling=Resampling.nearest,
        )
    binary = np.where(streams_on_ref > 0, 1.0, 0.0).astype("float32")
    out_streams = np.where(mask, binary, np.float32(NODATA)).astype("float32")
    write_raster(STREAMS_T500, out_streams, ref["transform"], ref["crs"])

    run_wbt("euclidean_distance", i=str(STREAMS_T500), output=str(TMP_WBT / "dist_t500.tif"))
    normalize_to_reference(TMP_WBT / "dist_t500.tif", DISTANCE, ref, mask)

    # TWI uses the buffered slope so upstream wetness is consistent with the
    # buffered flow accumulation.
    run_wbt("wetness_index", sca=str(raw_acc_sca), slope=str(SLOPE_BUFFERED), output=str(TMP_WBT / "twi.tif"))
    normalize_to_reference(TMP_WBT / "twi.tif", TWI, ref, mask)

    for f in TMP_WBT.glob("*.tif"):
        f.unlink(missing_ok=True)


def stage_ls_factor() -> None:
    ref = ref_profile()
    slope_deg = read_band(SLOPE, ref)
    sca = read_band(FLOW_ACC_SCA, ref)
    flow_accum = read_band(FLOW_ACC_CELLS, ref)
    theta = np.radians(slope_deg)
    sin_theta = np.sin(theta)
    as_term = np.where(sca > 0, np.power(np.maximum(sca, 0.0) / 22.13, 0.4), 0.0)
    sl_term = np.where(sin_theta > 0, np.power(np.maximum(sin_theta, 0.0) / 0.0896, 1.2), 0.0)
    ls = as_term * sl_term
    invalid = ~np.isfinite(slope_deg) | ~np.isfinite(sca)
    ls = np.where(invalid, np.nan, ls)
    channel = (flow_accum > 500) & np.isfinite(flow_accum)
    ls_hillslope = np.where(channel, np.nan, ls)
    ls_capped = np.where(np.isfinite(ls_hillslope), np.clip(ls_hillslope, 0.0, LS_CAP), np.nan)
    write_raster(LS_CAPPED, np.where(np.isfinite(ls_capped), ls_capped, NODATA), ref["transform"], ref["crs"])


def stage_worldcover_cfactor() -> None:
    ref = ref_profile()
    mask = boundary_mask(ref)
    with rasterio.open(WORLDCOVER_FILE) as src:
        data = src.read(1)
        nodata = src.nodata
        src_transform, src_crs = src.transform, src.crs

    # Preserve NoData: unmapped classes stay NaN so they are not silently
    # scored as a low/zero value downstream (previously converted to 0).
    def map_value(lut: dict[int, float]) -> np.ndarray:
        out = np.full(data.shape, np.nan, dtype="float32")
        for class_id, value in lut.items():
            out[data == class_id] = value
        return out

    layers = {
        "c_factor": CFACTOR,
        "land_use_pressure": LAND_USE_PRESSURE,
        "land_cover_runoff_pressure": LAND_COVER_RUNOFF,
        "bare_soil_vegetation_loss": BARE_SOIL_LOSS,
        "built_up_pressure": BUILT_UP_PRESSURE,
        "agricultural_pressure": AGRICULTURAL_PRESSURE,
    }
    luts = {
        "c_factor": WORLDCOVER_CFACTOR_LUT,
        "land_use_pressure": LAND_USE_PRESSURE_LUT,
        "land_cover_runoff_pressure": LAND_COVER_RUNOFF_LUT,
        "bare_soil_vegetation_loss": BARE_SOIL_LOSS_LUT,
        "built_up_pressure": BUILT_UP_LUT,
        "agricultural_pressure": AGRICULTURAL_LUT,
    }
    for name, out_path in layers.items():
        dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
        reproject(
            source=map_value(luts[name]),
            destination=dst,
            src_transform=src_transform, src_crs=src_crs,
            dst_transform=ref["transform"], dst_crs=ref["crs"],
            src_nodata=np.nan, dst_nodata=np.nan,
            resampling=Resampling.nearest,
        )
        dst[~mask] = np.nan
        write_raster(out_path, np.where(np.isfinite(dst), dst, NODATA), ref["transform"], ref["crs"])


def stage_soilgrids_kfactor() -> None:
    """Read the pinned local SoilGrids K-factor snapshot for the active focus area.

    The snapshot (Williams 1995, US units, 0-30 cm depth-weighted) is produced
    by bin/acquire/pull_goslar_soilgrids_window.py with recorded SHA-256. It is
    read here instead of the un-versioned /latest/ remote VRT so the K-factor is
    reproducible. US-unit K is converted to SI (x0.1317); NoData is preserved
    rather than filled with 0.
    """
    ref = ref_profile()
    mask = boundary_mask(ref)
    K_DIR.mkdir(parents=True, exist_ok=True)
    if not SOILGRIDS_K_SNAPSHOT.exists():
        raise FileNotFoundError(
            f"SoilGrids K snapshot missing: {SOILGRIDS_K_SNAPSHOT}. "
            f"Run .venv/bin/python {SOILGRIDS_PULL_SCRIPT} first."
        )
    with rasterio.open(SOILGRIDS_K_SNAPSHOT) as src:
        k_us = src.read(1).astype("float32")
        src_transform, src_crs = src.transform, src.crs
        if src.nodata is not None:
            k_us[k_us == src.nodata] = np.nan
    # Convert US-unit K to SI (t ha h / ha MJ mm); NoData stays NaN.
    k_si = k_us * K_SI_FACTOR
    # Reproject the windowed 250m K to the 30m reference grid (documented
    # coarse-source resampling).
    dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    reproject(
        source=k_si, destination=dst,
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=ref["transform"], dst_crs=ref["crs"],
        src_nodata=np.nan, dst_nodata=np.nan,
        resampling=Resampling.nearest,
    )
    dst[~mask] = np.nan
    write_raster(K_ALIGNED, np.where(np.isfinite(dst), dst, NODATA), ref["transform"], ref["crs"])
    valid = dst[mask & np.isfinite(dst)]
    if valid.size == 0:
        raise RuntimeError("no valid SoilGrids K cells after snapshot read")
    scored, low, high = percentile_minmax(dst, mask, constant_policy="error")
    write_raster(K_SCORED, np.where(np.isfinite(scored), scored, NODATA), ref["transform"], ref["crs"])


def stage_osm_roads() -> None:
    """Clip OSM roads to the Goslar focus box and rasterize proximity.

    Roads are projected to the metric CRS (EPSG:32632) before rasterizing onto
    the reference grid. The previous version rasterized WGS84 geometries
    directly onto a metric grid, which placed zero road pixels inside the
    focus box.
    """
    ref = ref_profile()
    mask = boundary_mask(ref)
    if not ROADS.exists():
        raise FileNotFoundError(f"OSM roads missing: {ROADS}")
    geometry = load_boundary_geometry(ref["crs"])
    roads = gpd.read_file(ROADS).to_crs(ref["crs"])
    clipped = gpd.clip(roads, geometry)
    if clipped.empty:
        raise ValueError("no OSM roads inside Goslar focus buffer")
    # Project roads to the metric CRS before rasterizing onto the metric grid.
    clipped_m = clipped
    import rasterio.features
    from shapely.geometry import mapping
    shapes = [(mapping(g), 1) for g in clipped_m.geometry]
    raster_roads = rasterio.features.rasterize(
        shapes, out_shape=(ref["height"], ref["width"]),
        transform=ref["transform"], fill=0, dtype="float32",
    )
    from scipy.ndimage import distance_transform_edt
    road_pixels = int((raster_roads > 0).sum())
    dist = distance_transform_edt(raster_roads == 0, sampling=(RES_M, RES_M))
    max_d = 20000.0
    proximity = np.clip(1.0 - dist / max_d, 0.0, 1.0).astype("float32")
    proximity[~mask] = np.nan
    write_raster(ROAD_ACCESS, np.where(np.isfinite(proximity), proximity, NODATA), ref["transform"], ref["crs"])
    print(f"[goslar-peru-style] OSM roads: {len(clipped)} features, "
          f"{road_pixels} rasterized pixels on metric grid", flush=True)


def read_regnie_month(path: Path) -> tuple[np.ndarray, dict]:
    """Read one DWD REGNIE monthly grid (ESRI ASCII, EPSG:31467)."""
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as stream:
        lines = stream.read().splitlines()
    header = {}
    index = 0
    for index, line in enumerate(lines):
        parts = line.split()
        if len(parts) == 2 and parts[0].replace("_", "").isalpha():
            header[parts[0].upper()] = float(parts[1])
            continue
        break
    ncols = int(header["NCOLS"])
    nrows = int(header["NROWS"])
    xll = header["XLLCORNER"]
    yll = header["YLLCORNER"]
    cell = header["CELLSIZE"]
    nodata = header.get("NODATA_VALUE", -999.0)
    values = []
    for line in lines[index:]:
        values.extend(float(v) for v in line.split())
    data = np.array(values[: ncols * nrows], dtype="float32").reshape((nrows, ncols))
    data[data == nodata] = np.nan
    transform = from_origin(xll, yll + nrows * cell, cell, cell)
    return data, {"transform": transform, "crs": "EPSG:31467",
                  "width": ncols, "height": nrows}


def stage_rainfall() -> None:
    """DWD REGNIE JJA (Jun-Aug) 1991-2020 mean -> provisional 30 m rainfall criterion."""
    ref = ref_profile()
    mask = boundary_mask(ref)
    RAIN_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = REGNIE_RAW_DIR / "raw"
    month_names = {6: "Jun", 7: "Jul", 8: "Aug"}
    month_arrays = {m: [] for m in RAIN_SEASON_MONTHS}
    meta = None
    for year in RAIN_SEASON_YEARS:
        for month in RAIN_SEASON_MONTHS:
            filename = f"grids_germany_monthly_precipitation_{year}{month:02d}.asc.gz"
            path = raw_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"REGNIE file missing: {path}")
            data, m = read_regnie_month(path)
            month_arrays[month].append(data)
            meta = m
    # Mean of JJA monthly means (mm). Use a masked mean so fully-NoData cells
    # at the grid edge do not emit empty-slice warnings.
    with np.errstate(invalid="ignore"):
        month_means = {m: np.ma.mean(np.ma.masked_invalid(np.stack(arrays)), axis=0).filled(np.nan)
                       for m, arrays in month_arrays.items()}
        season_mean = np.ma.mean(
            np.ma.masked_invalid(np.stack([month_means[m] for m in RAIN_SEASON_MONTHS])), axis=0
        ).filled(np.nan)

    # Resample native 1 km GK3 grid to the 30 m reference grid (documented
    # coarse-to-reference resampling, provisional only).
    dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    reproject(
        source=season_mean, destination=dst,
        src_transform=meta["transform"], src_crs=meta["crs"],
        dst_transform=ref["transform"], dst_crs=ref["crs"],
        resampling=Resampling.bilinear,
    )
    dst[~mask] = np.nan
    valid = dst[mask & np.isfinite(dst)]
    if valid.size == 0:
        raise RuntimeError("no valid REGNIE cells inside Goslar focus")
    scored, low, high = percentile_minmax(dst, mask, constant_policy="zeros")
    write_raster(RAINFALL, np.where(np.isfinite(scored), scored, NODATA), ref["transform"], ref["crs"])


def stage_protected_areas() -> None:
    """EEA Natura 2000 (FFH + SPA, 2024) protected-area proximity for ES."""
    from shapely.geometry import mapping
    ref = ref_profile()
    mask = boundary_mask(ref)
    ES_DIR.mkdir(parents=True, exist_ok=True)
    if not PROTECTED_RAW.exists():
        raise FileNotFoundError(f"protected areas missing: {PROTECTED_RAW}")
    protected = gpd.read_file(PROTECTED_RAW).to_crs("EPSG:32632")
    shapes = [(mapping(g), 1) for g in protected.geometry if g is not None and not g.is_empty]
    if not shapes:
        raise ValueError("no protected-area geometry to rasterize")
    protected_area_km2 = protected.area.sum() / 1e6
    print(f"[goslar-peru-style] EEA Natura2000: {len(shapes)} polygons, "
          f"{protected_area_km2:.1f} km2 within query box", flush=True)
    raster = rasterize(shapes, out_shape=(ref["height"], ref["width"]),
                       transform=ref["transform"], fill=0, dtype="uint8")
    dist = distance_transform_edt(raster == 0, sampling=(RES_M, RES_M))
    max_d = 10000.0
    proximity = np.clip(1.0 - dist / max_d, 0.0, 1.0).astype("float32")
    proximity[~mask] = np.nan
    write_raster(ES_DIR / "protected_area_context_0_1.tif",
                 np.where(np.isfinite(proximity), proximity, NODATA), ref["transform"], ref["crs"])


def build_be_proxy(built_up, agriculture, road_access, mask):
    developed_or_agricultural = np.maximum(built_up, agriculture)
    return weighted_average([(developed_or_agricultural, 0.50), (road_access, 0.50)], mask)


def stage_criteria_stack() -> None:
    ref = ref_profile()
    mask = boundary_mask(ref)
    rasters = {
        "rainfall": read_band(RAINFALL, ref),
        "twi": read_band(TWI, ref),
        "drainage": read_band(DISTANCE, ref),
        "ls_factor": read_band(LS_CAPPED, ref),
        "c_factor": read_band(CFACTOR, ref),
        "soil_k_factor": read_band(K_SCORED, ref),
        "land_cover_runoff_pressure": read_band(LAND_COVER_RUNOFF, ref),
        "bare_soil_vegetation_loss": read_band(
            CLMS_TCD_LOSS if CLMS_TCD_LOSS.exists() else (CLMS_BARE_SOIL if CLMS_BARE_SOIL.exists() else BARE_SOIL_LOSS),
            ref,
        ),
        "built_up_pressure": read_band(BUILT_UP_PRESSURE, ref),
        "agricultural_pressure": read_band(AGRICULTURAL_PRESSURE, ref),
        "road_access_proximity": read_band(ROAD_ACCESS, ref),
    }
    twi_std, _, _ = normalize_2_98(rasters["twi"], mask)
    drain_std, _, _ = normalize_2_98(rasters["drainage"], mask, invert=True)
    ls_std, _, _ = normalize_2_98(rasters["ls_factor"], mask)
    c_std, _, _ = normalize_2_98(rasters["c_factor"], mask)
    rainfall_std = rasters["rainfall"]
    soil_k_std = rasters["soil_k_factor"]
    land_use_std = rasters["land_cover_runoff_pressure"]
    bare_soil = rasters["bare_soil_vegetation_loss"]
    road_std = rasters["road_access_proximity"]
    built_agri_road = build_be_proxy(rasters["built_up_pressure"], rasters["agricultural_pressure"], road_std, mask)

    criteria = {
        "rainfall_climatology": rainfall_std,
        "twi_wetness": twi_std,
        "drainage_proximity": drain_std,
        "ls_factor": ls_std,
        "c_factor": c_std,
        "soil_k_factor": soil_k_std,
        "land_cover_pressure": land_use_std,
        "bare_soil_vegetation_loss": bare_soil,
        "built_agriculture_road_expansion": built_agri_road,
        "road_access_proximity": road_std,
    }
    CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    for name, arr in criteria.items():
        arr = np.clip(arr, 0.0, 1.0).astype("float32")
        arr[~mask] = np.nan
        write_raster(CRITERIA_DIR / f"{name}_0_1.tif", np.where(np.isfinite(arr), arr, NODATA),
                     ref["transform"], ref["crs"])


def stage_exposure_indicators() -> None:
    """Zensus 2022 population + independent OSM infrastructure proximity for SV."""
    ref = ref_profile()
    mask = boundary_mask(ref)
    EXPOSURE_DIR.mkdir(parents=True, exist_ok=True)
    road = read_band(ROAD_ACCESS, ref)
    population_dst = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    zensus_tif = ZENSUS_RAW / "goslar_official_basin_population_100m_3035.tif"
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
        raise RuntimeError("no Zensus 2022 data inside Goslar focus")
    pop_std, low, high = percentile_minmax(population_dst, mask, constant_policy="zeros")
    if not INFRASTRUCTURE.exists():
        raise FileNotFoundError(f"OSM infrastructure candidates missing: {INFRASTRUCTURE}")
    facilities = gpd.read_file(INFRASTRUCTURE, layer="osm_infrastructure_candidates").to_crs(ref["crs"])
    from rasterio.features import rasterize as facility_rasterize
    from shapely.geometry import mapping as facility_mapping
    facility_shapes = [(facility_mapping(g), 1) for g in facilities.geometry if g is not None and not g.is_empty]
    if not facility_shapes:
        raise ValueError("no OSM infrastructure candidates available")
    facility_mask = facility_rasterize(
        facility_shapes, out_shape=(ref["height"], ref["width"]),
        transform=ref["transform"], fill=0, dtype="uint8",
    )
    facility_distance = distance_transform_edt(facility_mask == 0, sampling=(RES_M, RES_M))
    built = np.clip(1.0 - facility_distance / 2000.0, 0.0, 1.0).astype("float32")
    built[~mask] = np.nan
    infra = weighted_average([(pop_std, 0.50), (built, 0.50)], mask)
    # Keep the Supervisor v07 / Secocha SV contract exactly: road 0.35,
    # settlement population 0.35, built-up critical-infrastructure proxy 0.30.
    sv = weighted_average([(road, 0.35), (pop_std, 0.35), (built, 0.30)], mask)
    for name, arr in [("population_exposure_0_1.tif", pop_std),
                      ("built_infrastructure_exposure_0_1.tif", built),
                      ("infrastructure_exposure_0_1.tif", infra),
                      ("exposure_indicators_0_1.tif", sv)]:
        write_raster(EXPOSURE_DIR / name, np.where(np.isfinite(arr), arr, NODATA),
                     ref["transform"], ref["crs"])


def stage_environmental_sensitivity() -> None:
    """Water/wetland context from WorldCover; protected-area context documented as gap."""
    ref = ref_profile()
    mask = boundary_mask(ref)
    ES_DIR.mkdir(parents=True, exist_ok=True)
    water_wetland = read_band(LAND_COVER_RUNOFF, ref).copy()
    # Use WorldCover classes 80/90 as water/wetland context proxy.
    with rasterio.open(WORLDCOVER_FILE) as src:
        wc = src.read(1)
        src_transform, src_crs = src.transform, src.crs
    sensitive = np.isin(wc, [80, 90]).astype("float32")
    dst = np.full((ref["height"], ref["width"]), 0.0, dtype="float32")
    reproject(
        source=sensitive, destination=dst,
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=ref["transform"], dst_crs=ref["crs"],
        resampling=Resampling.nearest,
    )
    from scipy.ndimage import distance_transform_edt
    dist = distance_transform_edt(dst == 0, sampling=(RES_M, RES_M))
    max_d = 10000.0
    water_ctx = np.clip(1.0 - dist / max_d, 0.0, 1.0).astype("float32")
    water_ctx[~mask] = np.nan
    # Protected area: no local vector source in this prototype -> constant gap value.
    protected_ctx = np.full((ref["height"], ref["width"]), np.nan, dtype="float32")
    if (ES_DIR / "protected_area_context_0_1.tif").exists():
        protected_ctx = read_band(ES_DIR / "protected_area_context_0_1.tif", ref)
    es = weighted_average([(water_ctx, 0.65), (protected_ctx, 0.35)], mask)
    for name, arr in [("water_wetland_context_0_1.tif", water_ctx),
                      ("protected_area_context_0_1.tif", protected_ctx),
                      ("environmental_sensitivity_0_1.tif", es)]:
        write_raster(ES_DIR / name, np.where(np.isfinite(arr), arr, NODATA),
                     ref["transform"], ref["crs"])


def combine_common_support(criteria: dict, weights: dict, mask: np.ndarray):
    first = next(iter(criteria.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    available = np.zeros(first.shape, dtype="float32")
    count = np.zeros(first.shape, dtype="uint8")
    common = np.ones(first.shape, dtype=bool)
    for name, weight in weights.items():
        layer = criteria[name]
        valid = np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        available[valid] += weight
        count[valid] += 1
        common &= valid
    score = np.full(first.shape, np.nan, dtype="float32")
    score[common] = numerator[common]
    return np.clip(score, 0.0, 1.0).astype("float32"), available, count


def stage_priority_scenarios() -> None:
    ref = ref_profile()
    mask = boundary_mask(ref)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    (SCENARIO_DIR / "scenarios").mkdir(parents=True, exist_ok=True)
    (SCENARIO_DIR / "pim_criteria").mkdir(parents=True, exist_ok=True)

    components = {
        "rainfall_climatology": read_band(CRITERIA_DIR / "rainfall_climatology_0_1.tif", ref),
        "twi_wetness": read_band(CRITERIA_DIR / "twi_wetness_0_1.tif", ref),
        "drainage_proximity": read_band(CRITERIA_DIR / "drainage_proximity_0_1.tif", ref),
        "soil_k_factor": read_band(CRITERIA_DIR / "soil_k_factor_0_1.tif", ref),
        "ls_factor": read_band(CRITERIA_DIR / "ls_factor_0_1.tif", ref),
        "c_factor": read_band(CRITERIA_DIR / "c_factor_0_1.tif", ref),
        "land_cover_pressure": read_band(CRITERIA_DIR / "land_cover_pressure_0_1.tif", ref),
        "bare_soil_vegetation_loss": read_band(CRITERIA_DIR / "bare_soil_vegetation_loss_0_1.tif", ref),
        "built_agriculture_road_expansion": read_band(CRITERIA_DIR / "built_agriculture_road_expansion_0_1.tif", ref),
        "road_access_proximity": read_band(CRITERIA_DIR / "road_access_proximity_0_1.tif", ref),
        "water_wetland_context": read_band(ES_DIR / "water_wetland_context_0_1.tif", ref),
        "protected_ecological_context": read_band(ES_DIR / "protected_area_context_0_1.tif", ref),
        "settlement_population": read_band(EXPOSURE_DIR / "population_exposure_0_1.tif", ref),
        "critical_infrastructure": read_band(EXPOSURE_DIR / "built_infrastructure_exposure_0_1.tif", ref),
    }

    def combine(weights: dict) -> np.ndarray:
        return weighted_average([(components[k], v) for k, v in weights.items()], mask)

    pim_criteria = {
        "flood_hazard": combine(FH_COMPONENTS),
        "sediment": combine(SE_COMPONENTS),
        "landuse_asm": combine(LU_COMPONENTS),
        "environmental": combine(ES_COMPONENTS),
        "socioeconomic": combine(SV_COMPONENTS),
    }
    for name, arr in pim_criteria.items():
        arr = np.clip(arr, 0.0, 1.0).astype("float32")
        arr[~mask] = np.nan
        write_raster(SCENARIO_DIR / "pim_criteria" / f"{name}_0_1.tif",
                     np.where(np.isfinite(arr), arr, NODATA), ref["transform"], ref["crs"])

    pim, available, count = combine_common_support(pim_criteria, MAIN_WEIGHTS, mask)
    priority_path = SCENARIO_DIR / "scenarios" / PRIORITY_FILENAME
    write_raster(priority_path,
                 np.where(np.isfinite(pim), pim, NODATA), ref["transform"], ref["crs"])
    # Mask coverage rasters to the focus box so finite zeros outside the
    # boundary do not masquerade as "zero coverage" support.
    available = np.where(mask, available, np.nan).astype("float32")
    count = np.where(mask, count.astype("float32"), np.nan).astype("float32")
    write_raster(SCENARIO_DIR / "available_main_weight.tif",
                 np.where(np.isfinite(available), available, NODATA), ref["transform"], ref["crs"])
    write_raster(SCENARIO_DIR / "criteria_evidence_count.tif",
                 np.where(np.isfinite(count), count, NODATA),
                 ref["transform"], ref["crs"])

    manifest = {
        "focus_area_id": FOCUS_AREA_ID,
        "focus_area_name": "Goslar official WRRL water-body union (hydrologic reference, not an event footprint)",
        "metric_crs": METRIC_CRS,
        "reference_resolution_m": RES_M,
        "enters_pim_score": False,
        "claim_level": "provisional",
        "weight_contract": "identical to Secocha Supervisor v07; no Goslar-specific reweighting",
        "main_weights": MAIN_WEIGHTS,
        "component_weights": {
            "flood_hazard": FH_COMPONENTS,
            "sediment": SE_COMPONENTS,
            "landuse_asm": LU_COMPONENTS,
            "environmental": ES_COMPONENTS,
            "socioeconomic": SV_COMPONENTS,
        },
        "removed_components": REMOVED_COMPONENTS,
        "local_weight_limitations": {
            "landuse_asm": "bare_soil_vegetation_loss uses positive 2018-2024 Copernicus HRL Tree Cover Density decline; this is a provisional vegetation-loss proxy, not a validated forest-loss product",
            "socioeconomic": "critical_infrastructure uses independent OSM facility proximity (2 km decay); coverage and operating status remain community-data limitations",
        },
        "mining_role": "external context overlay only",
        "mining_enters_pim_score": False,
        "mining_overlay": {
            "path": rel(MINING_OVERLAY),
            "manifest": rel(MINING_OVERLAY_MANIFEST),
            "claim_level": "context_evidence",
        },
        "official_hydrology_and_validation": {
            "enters_pim_score": False,
            "claim_level": "validation_candidate/context",
            "sources": {
                "nlwkn_2017_report": "data/validation/goslar_harz_2024_focus_area/official_event_and_hazard_data/NLWKN_Hochwasserbericht_Juli_2017.pdf",
                "wfd_drainage_basins": rel(OFFICIAL_BASINS),
                "hwrm_flood_hazard_boundaries": rel(HWRM_FLOOD_HAZARD),
                "osm_infrastructure_candidates": "data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_infrastructure_overpass.json",
                "lineage": rel(OFFICIAL_SOURCE_LINEAGE),
                "diagnostics": rel(OFFICIAL_CONTEXT_DIAGNOSTICS),
            },
            "interpretation": (
                "Official WRRL polygons provide hydrologic context; HWRM layers are modelled "
                "regulatory scenarios, not observed 2017 flooding; OSM facilities require "
                "class filtering before scoring."
            ),
        },
        "normalization": {
            "method": "2-98 percentile clip then min-max to [0,1]",
            "module": "bin/_lib/standardization.py:percentile_minmax",
            "applied_to": ["twi", "drainage_proximity(inverted)", "ls_factor",
                           "c_factor", "soil_k_factor", "rainfall_climatology",
                           "population_exposure"],
            "not_percentile": "road_access_proximity (direct 20 km linear decay); "
                               "bare_soil/built/agriculture (LUT, not standardized)",
        },
        "nodata_policy": NODATA_POLICY,
        "effective_resolutions": {
            "dem": "30 m (Copernicus DEM GLO-30 native ~30 m)",
            "worldcover": "10 m native, resampled nearest to 30 m",
            "soilgrids_k": "250 m native, resampled nearest to 30 m (effective 250 m)",
            "rainfall_regnie": "1 km native, provisional 30 m resample (effective 1 km)",
            "population_zensus": "100 m native, sum-resampled to 30 m",
        },
        "hydrology_buffer_m": HYDRO_BUFFER_M,
        "soilgrids_k_snapshot": {
            "path": rel(SOILGRIDS_K_SNAPSHOT),
            "sha256": sha256_file(SOILGRIDS_K_SNAPSHOT),
            "method": "Williams (1995) US units, 0-30 cm depth-weighted; SI via x0.1317",
        },
        "priority_raster_lineage": lineage_record(priority_path),
        "criterion_raster_lineage": {
            name: lineage_record(SCENARIO_DIR / "pim_criteria" / f"{name}_0_1.tif")
            for name in pim_criteria
        },
        "input_lineage": {
            "implementation": lineage_record(Path(__file__).resolve()),
            "boundary": lineage_record(BOUNDARY_GPKG),
            "dem": lineage_record(COPERNICUS_DEM_RAW / "Copernicus_DSM_COG_10_N51_00_E010_00_DEM.tif"),
            "worldcover": lineage_record(WORLDCOVER_FILE),
            "soilgrids_k_snapshot": lineage_record(SOILGRIDS_K_SNAPSHOT),
            "roads": lineage_record(ROADS),
            "population": lineage_record(ZENSUS_RAW / "goslar_official_basin_population_100m_3035.tif"),
            "infrastructure": lineage_record(INFRASTRUCTURE),
            "clms_bare_soil": lineage_record(CLMS_BARE_SOIL),
            "clms_tcd_loss": lineage_record(CLMS_TCD_LOSS),
            "protected_areas": lineage_record(PROTECTED_RAW),
            "mining_overlay": optional_lineage_record(MINING_OVERLAY),
            "mining_overlay_manifest": optional_lineage_record(MINING_OVERLAY_MANIFEST),
            "official_hydrology_and_validation": {
                "wfd_drainage_basins": optional_lineage_record(OFFICIAL_BASINS),
                "hwrm_flood_hazard_boundaries": optional_lineage_record(HWRM_FLOOD_HAZARD),
                "source_lineage": optional_lineage_record(OFFICIAL_SOURCE_LINEAGE),
                "diagnostics": optional_lineage_record(OFFICIAL_CONTEXT_DIAGNOSTICS),
                "nlwkn_2017_report": optional_lineage_record(
                    ROOT / "data/validation/goslar_harz_2024_focus_area/official_event_and_hazard_data/NLWKN_Hochwasserbericht_Juli_2017.pdf"
                ),
                "osm_infrastructure_candidates": optional_lineage_record(
                    ROOT / "data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_infrastructure_overpass.json"
                ),
            },
        },
        "data_gaps": {},
        "data_sources": {
            "rainfall": "DWD REGNIE monthly grid, JJA 1991-2020 mean (30-y climate normal), 1 km native, provisional 30 m resample",
            "protected_areas": "EEA Natura 2000 2024 (FFH + SPA)",
            "dem": "Copernicus DEM GLO-30 (N51E010); outputs/goslar_pim_chain/ dir name is legacy",
            "population": "Destatis Zensus 2022 100 m grid (EPSG:3035)",
            "mining_overlay": "LBEG/NIBIS mining-right fields plus OSM mining features within 12 km; external context only",
            "official_hydrology": "Lower Saxony Umweltkarten WRRL drainage basins / water bodies; external hydrologic context",
            "flood_hazard_scenarios": "NLWKN HWRM-RL Oker and Innerste HQ scenarios; modelled regulatory context, not observed 2017 inundation",
            "infrastructure_candidates": "OpenStreetMap schools, hospitals, emergency services, works, substations and stations; candidate only",
            "clms_bare_soil": "Copernicus HRL VLCC Bare Soil After 2024 (10 m native; provisional indicator input)",
            "clms_tcd_loss": "Copernicus HRL VLCC Tree Cover Density 2018-2024 positive decline (10 m native; provisional vegetation-loss proxy)",
        },
        "boundary_contract": {
            "id": "goslar_wrrl_basin",
            "source": "Lower Saxony Umweltkarten WRRL DrainBasin_Waterbody_LOCAL",
            "area_km2": 153.778655,
            "claim": "provisional official water-body reference; not an observed 2017 inundation footprint",
        },
        "run_date": date.today().isoformat(),
        "note": "Goslar provisional prototype using an official WRRL water-body reference union; not final or validated flood risk.",
    }
    (SCENARIO_DIR / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                    encoding="utf-8")


STAGE_FUNCS = {
    "register_inputs": register_inputs,
    "boundary": lambda: {"boundary": rel(BOUNDARY_GPKG)},
    "dem": stage_dem,
    "slope": stage_slope,
    "hydrology": stage_hydrology,
    "ls_factor": stage_ls_factor,
    "worldcover_cfactor": stage_worldcover_cfactor,
    "soilgrids_kfactor": stage_soilgrids_kfactor,
    "osm_roads": stage_osm_roads,
    "rainfall": stage_rainfall,
    "protected_areas": stage_protected_areas,
    "criteria_stack": stage_criteria_stack,
    "exposure_indicators": stage_exposure_indicators,
    "environmental_sensitivity": stage_environmental_sensitivity,
    "priority_scenarios": stage_priority_scenarios,
}


def catalog() -> dict:
    return {
        "focus_area_id": FOCUS_AREA_ID,
        "focus_extent_wgs84": list(FOCUS_EXTENT_WGS84),
        "metric_crs": METRIC_CRS,
        "reference_resolution_m": RES_M,
        "claim_level": "provisional",
        "enters_pim_score": False,
        "mining_role": "external context overlay only",
        "mining_enters_pim_score": False,
        "weight_contract": "identical to Secocha Supervisor v07; no Goslar-specific reweighting",
        "stages": STAGES,
        "removed_components": REMOVED_COMPONENTS,
        "data_gaps": {},
        "data_sources": {
            "rainfall": "DWD REGNIE monthly grid, JJA 1991-2020 mean (30-y climate normal, 1 km native)",
            "protected_areas": "EEA Natura 2000 2024 (FFH + SPA)",
            "dem": "Copernicus DEM GLO-30 (N51E010)",
            "population": "Destatis Zensus 2022 100 m grid (EPSG:3035)",
            "mining_overlay": "LBEG/NIBIS mining rights + OSM mining features (12 km context; excluded from PIM)",
        },
        "main_weights": MAIN_WEIGHTS,
        "component_weights": {
            "flood_hazard": FH_COMPONENTS,
            "sediment": SE_COMPONENTS,
            "landuse_asm": LU_COMPONENTS,
            "environmental": ES_COMPONENTS,
            "socioeconomic": SV_COMPONENTS,
        },
        "nodata_policy": NODATA_POLICY,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--max-stage", default=None)
    args = parser.parse_args()
    if args.catalog_only:
        print(json.dumps(catalog(), ensure_ascii=False, indent=2))
        return
    max_stage = args.max_stage or STAGES[-1]
    if max_stage not in STAGES:
        raise SystemExit(f"unknown stage: {max_stage}; choose from {STAGES}")
    results = {}
    for stage in STAGES:
        results[stage] = "done"
        print(f"[goslar-peru-style] {stage} ...", flush=True)
        try:
            result = STAGE_FUNCS[stage]()
            if result is not None:
                print(json.dumps(result, ensure_ascii=False))
        except Exception as exc:
            print(f"[goslar-peru-style] stage {stage} FAILED: {exc}", file=sys.stderr)
            raise
        if stage == max_stage:
            break


if __name__ == "__main__":
    main()
