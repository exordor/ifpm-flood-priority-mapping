#!/usr/bin/env python3
"""Build Peru exposure indicators and response-capacity context layers.

The PIM-ready criterion follows the supplied Peru sub-criteria structure:

    exposure indicators = 0.45 * road/access proximity
                        + 0.55 * infrastructure exposure

Infrastructure exposure is an explicit provisional indicator composed equally of
WorldPop population exposure and OSM building-density exposure. INEI district
poverty and OSM health-service remoteness are exported as response-capacity
context only; they are not hidden inputs to the current AHP overlay.

All outputs are provisional and use the Peru 30 m reference grid. WorldPop is
reprojected with sum resampling because the source values are population counts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.warp import Resampling, reproject
from affine import Affine
from scipy.ndimage import distance_transform_edt
from scipy.signal import fftconvolve
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))

from _lib.ifpm_tools import write_raster as _write_raster


BOUNDARY_ID = "pe1"
EXPERIMENT_ID = "exposure_indicators"
OUT_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators"

REFERENCE = ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif"
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
WORLDPOP = ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj_pe1_bbox.tif"
ROAD_ACCESS = ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/road_access_proximity_0_1.tif"
OSM_DIR = ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted"
OSM_BUILDINGS = OSM_DIR / "gis_osm_buildings_a_free_1.shp"
OSM_HEALTH_POIS = OSM_DIR / "gis_osm_pois_free_1.shp"
OSM_DISTRICTS = OSM_DIR / "gis_osm_adminareas_a_free_1.shp"
INEI_POVERTY = ROOT / "data/raw/inei_peru_poverty_2018/arequipa_district_poverty_2018.csv"

SOCIOECONOMIC_WEIGHTS = {"road_access_proximity": 0.45, "infrastructure_exposure": 0.55}
INFRASTRUCTURE_WEIGHTS = {"population_exposure": 0.50, "built_infrastructure_exposure": 0.50}
HEALTH_CLASSES = {"clinic", "doctors", "hospital"}
BUILDING_DENSITY_RADIUS_M = 1000.0
HEALTH_MAX_DISTANCE_M = 20000.0

INPUTS = [
    ROOT / "bin/_lib/ifpm_tools.py",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
    ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj_pe1_bbox.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/road_access_proximity_0_1.tif",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_buildings_a_free_1.shp",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_pois_free_1.shp",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_adminareas_a_free_1.shp",
    ROOT / "data/raw/inei_peru_poverty_2018/arequipa_district_poverty_2018.csv",
]
OUTPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/population_exposure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/built_infrastructure_exposure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/infrastructure_exposure_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/poverty_context_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/health_service_remoteness_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_grid_check.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/district_poverty_match.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_components.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_contribution_diagnostics.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_manifest.json",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def robust_normalize(
    values: np.ndarray,
    *,
    upper_percentile: float = 99.0,
    log1p: bool = False,
) -> tuple[np.ndarray, float]:
    """Scale finite non-negative values to 0-1 using a robust upper bound."""

    source = np.asarray(values, dtype="float32")
    finite = np.isfinite(source)
    result = np.full(source.shape, np.nan, dtype="float32")
    if not finite.any():
        raise ValueError("cannot normalize a raster with no finite values")

    transformed = np.maximum(source[finite], 0.0).astype("float64")
    if log1p:
        transformed = np.log1p(transformed)
    upper = float(np.percentile(transformed, upper_percentile))
    if not np.isfinite(upper) or upper <= 0.0:
        result[finite] = 0.0
        return result, 0.0

    result[finite] = np.clip(transformed / upper, 0.0, 1.0).astype("float32")
    return result, upper


def combine_weighted_complete_case(
    layers: dict[str, np.ndarray],
    weights: dict[str, float],
    boundary_mask: np.ndarray,
) -> np.ndarray:
    """Combine complete finite cells only; missing components stay NoData."""

    if set(layers) != set(weights):
        raise ValueError("layer and weight keys differ")
    if not layers:
        raise ValueError("at least one layer is required")
    total_weight = float(sum(weights.values()))
    if total_weight <= 0.0 or any(weight < 0.0 for weight in weights.values()):
        raise ValueError("weights must be non-negative and sum to a positive value")

    shape = next(iter(layers.values())).shape
    if boundary_mask.shape != shape or any(layer.shape != shape for layer in layers.values()):
        raise ValueError("all layers and the boundary mask must share one shape")

    valid = boundary_mask.astype(bool).copy()
    numerator = np.zeros(shape, dtype="float32")
    for name, layer in layers.items():
        finite = np.isfinite(layer)
        valid &= finite
        numerator[finite] += layer[finite] * float(weights[name])

    result = np.full(shape, np.nan, dtype="float32")
    result[valid] = numerator[valid] / total_weight
    return np.clip(result, 0.0, 1.0).astype("float32")


def health_remoteness_from_presence(
    presence: np.ndarray,
    boundary_mask: np.ndarray,
    *,
    pixel_size_m: float,
    max_distance_m: float,
) -> np.ndarray:
    """Return 0 at a health facility and 1 at or beyond max_distance_m."""

    if not np.asarray(presence, dtype=bool).any():
        raise ValueError("at least one health-service location is required")
    if pixel_size_m <= 0.0 or max_distance_m <= 0.0:
        raise ValueError("pixel size and maximum distance must be positive")
    distance_m = distance_transform_edt(~np.asarray(presence, dtype=bool), sampling=pixel_size_m)
    result = np.clip(distance_m / max_distance_m, 0.0, 1.0).astype("float32")
    result[~boundary_mask.astype(bool)] = np.nan
    return result


def read_reference() -> tuple[dict, np.ndarray]:
    with rasterio.open(REFERENCE) as src:
        profile = src.profile.copy()
        valid = src.read_masks(1) > 0
    boundary = gpd.read_file(BOUNDARY, layer="peru_pilot_boundary").to_crs(profile["crs"])
    mask = geometry_mask(
        boundary.geometry,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        invert=True,
    )
    return profile, valid & mask


def read_matching_raster(path: Path, profile: dict, boundary_mask: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        if src.crs != profile["crs"] or src.transform != profile["transform"]:
            raise ValueError(f"grid mismatch: {path}")
        if src.width != profile["width"] or src.height != profile["height"]:
            raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    data[~boundary_mask] = np.nan
    return data


def build_population_exposure(profile: dict, boundary_mask: np.ndarray) -> tuple[np.ndarray, dict]:
    population_count = np.full((profile["height"], profile["width"]), np.nan, dtype="float32")
    with rasterio.open(WORLDPOP) as src:
        native_crs = str(src.crs)
        native_resolution = [abs(float(src.transform.a)), abs(float(src.transform.e))]
        reproject(
            source=rasterio.band(src, 1),
            destination=population_count,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=profile["transform"],
            dst_crs=profile["crs"],
            dst_nodata=np.nan,
            resampling=Resampling.sum,
        )
    population_count[~boundary_mask] = np.nan
    population_score, upper = robust_normalize(population_count, upper_percentile=99.0, log1p=True)
    return population_score, {
        "population_count_sum": round(float(np.nansum(population_count)), 3),
        "normalization": "log1p then clip/divide by finite-cell p99",
        "normalization_upper_log1p": upper,
        "resampling": "sum",
        "native_crs": native_crs,
        "native_resolution": native_resolution,
        "target_resolution_m": abs(float(profile["transform"].a)),
        "effective_resolution_warning": (
            "Target-grid alignment does not create 30 m population information; "
            "effective detail remains limited by the native approximately 3 arc-second source."
        ),
    }


def reference_bbox_wgs84(
    profile: dict,
    *,
    padding_m: float = 0.0,
) -> tuple[float, float, float, float]:
    bounds = rasterio.transform.array_bounds(profile["height"], profile["width"], profile["transform"])
    if padding_m < 0.0:
        raise ValueError("padding must be non-negative")
    bounds = (
        bounds[0] - padding_m,
        bounds[1] - padding_m,
        bounds[2] + padding_m,
        bounds[3] + padding_m,
    )
    frame = gpd.GeoDataFrame(geometry=[box(*bounds)], crs=profile["crs"]).to_crs("EPSG:4326")
    return tuple(float(value) for value in frame.total_bounds)


def read_osm_subset(path: Path, profile: dict, *, padding_m: float = 0.0) -> gpd.GeoDataFrame:
    return gpd.read_file(
        path,
        bbox=reference_bbox_wgs84(profile, padding_m=padding_m),
    ).to_crs(profile["crs"])


def padded_grid(profile: dict, padding_m: float) -> tuple[dict, int]:
    """Return a symmetric padded raster grid in the projected reference CRS."""

    pixel_size = abs(float(profile["transform"].a))
    pad_cells = int(np.ceil(padding_m / pixel_size))
    padded = profile.copy()
    padded["width"] = int(profile["width"]) + 2 * pad_cells
    padded["height"] = int(profile["height"]) + 2 * pad_cells
    padded["transform"] = profile["transform"] * Affine.translation(-pad_cells, -pad_cells)
    return padded, pad_cells


def circular_focal_density(presence: np.ndarray, radius_cells: int) -> np.ndarray:
    """Return the fraction of present cells inside a circular neighbourhood."""

    if radius_cells < 1:
        raise ValueError("radius_cells must be positive")
    yy, xx = np.ogrid[-radius_cells : radius_cells + 1, -radius_cells : radius_cells + 1]
    kernel = ((xx * xx + yy * yy) <= radius_cells * radius_cells).astype("float32")
    kernel /= float(kernel.sum())
    return fftconvolve(np.asarray(presence, dtype="float32"), kernel, mode="same").astype("float32")


def build_built_infrastructure(
    profile: dict,
    boundary_mask: np.ndarray,
) -> tuple[np.ndarray, dict]:
    padded, pad_cells = padded_grid(profile, BUILDING_DENSITY_RADIUS_M)
    buildings = read_osm_subset(OSM_BUILDINGS, profile, padding_m=BUILDING_DENSITY_RADIUS_M)
    buildings = buildings[buildings.geometry.notna() & ~buildings.geometry.is_empty]
    presence = rasterize(
        ((geometry, 1) for geometry in buildings.geometry),
        out_shape=(padded["height"], padded["width"]),
        transform=padded["transform"],
        fill=0,
        all_touched=True,
        dtype="uint8",
    )
    pixel_size = abs(float(profile["transform"].a))
    radius_cells = max(1, int(round(BUILDING_DENSITY_RADIUS_M / pixel_size)))
    density_padded = circular_focal_density(presence, radius_cells)
    density = density_padded[
        pad_cells : pad_cells + profile["height"],
        pad_cells : pad_cells + profile["width"],
    ]
    density[~boundary_mask] = np.nan
    score, upper = robust_normalize(density, upper_percentile=99.0, log1p=False)
    return score, {
        "building_features_in_padded_bbox": int(len(buildings)),
        "source_read_padding_m": BUILDING_DENSITY_RADIUS_M,
        "focal_kernel": "circular",
        "focal_radius_cells": radius_cells,
        "focal_radius_m": round(radius_cells * pixel_size, 3),
        "normalization": "clip/divide by finite-cell p99 of focal building presence density",
        "normalization_upper_density": upper,
    }


def build_health_remoteness(profile: dict, boundary_mask: np.ndarray) -> tuple[np.ndarray, dict]:
    padded, pad_cells = padded_grid(profile, HEALTH_MAX_DISTANCE_M)
    pois = read_osm_subset(OSM_HEALTH_POIS, profile, padding_m=HEALTH_MAX_DISTANCE_M)
    health = pois[pois["fclass"].isin(HEALTH_CLASSES)].copy()
    health = health[health.geometry.notna() & ~health.geometry.is_empty]
    presence = rasterize(
        ((geometry, 1) for geometry in health.geometry),
        out_shape=(padded["height"], padded["width"]),
        transform=padded["transform"],
        fill=0,
        all_touched=True,
        dtype="uint8",
    ).astype(bool)
    padded_boundary = np.ones(presence.shape, dtype=bool)
    score_padded = health_remoteness_from_presence(
        presence,
        padded_boundary,
        pixel_size_m=abs(float(profile["transform"].a)),
        max_distance_m=HEALTH_MAX_DISTANCE_M,
    )
    score = score_padded[
        pad_cells : pad_cells + profile["height"],
        pad_cells : pad_cells + profile["width"],
    ]
    score[~boundary_mask] = np.nan
    return score, {
        "health_features_in_padded_bbox": int(len(health)),
        "source_read_padding_m": HEALTH_MAX_DISTANCE_M,
        "health_classes": sorted(HEALTH_CLASSES),
        "maximum_distance_m": HEALTH_MAX_DISTANCE_M,
        "direction": "farther from mapped health services -> higher response-capacity gap",
    }


def build_poverty_context(
    profile: dict,
    boundary_mask: np.ndarray,
) -> tuple[np.ndarray, list[dict[str, object]], dict]:
    districts = read_osm_subset(OSM_DISTRICTS, profile)
    districts = districts[districts["fclass"] == "admin_level8"].copy()
    districts = districts[districts.geometry.notna() & ~districts.geometry.is_empty]
    districts["district_key"] = districts["name"].map(normalize_name)

    poverty = pd.read_csv(INEI_POVERTY, dtype={"ubigeo": str})
    poverty["district_key"] = poverty["distrito"].map(normalize_name)
    poverty["poverty_midpoint_pct"] = (
        poverty["pobreza_total_ci95_inferior"] + poverty["pobreza_total_ci95_superior"]
    ) / 2.0
    lookup = poverty.set_index("district_key", drop=False)

    shapes: list[tuple[object, float]] = []
    match_rows: list[dict[str, object]] = []
    for row in districts.itertuples():
        key = row.district_key
        matched = lookup.loc[key] if key in lookup.index else None
        if isinstance(matched, pd.DataFrame):
            matched = matched.iloc[0]
        if matched is None:
            match_rows.append({"osm_district": row.name, "district_key": key, "matched": False})
            continue
        midpoint = float(matched["poverty_midpoint_pct"])
        shapes.append((row.geometry, np.clip(midpoint / 100.0, 0.0, 1.0)))
        match_rows.append({
            "osm_district": row.name,
            "district_key": key,
            "matched": True,
            "ubigeo": matched["ubigeo"],
            "province": matched["provincia"],
            "inei_district": matched["distrito"],
            "poverty_ci95_lower_pct": round(float(matched["pobreza_total_ci95_inferior"]), 6),
            "poverty_ci95_upper_pct": round(float(matched["pobreza_total_ci95_superior"]), 6),
            "poverty_midpoint_pct": round(midpoint, 6),
        })
    if not shapes:
        raise RuntimeError("no OSM districts matched the INEI Arequipa poverty table")

    sentinel = np.float32(-9999.0)
    poverty_score = rasterize(
        shapes,
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        fill=sentinel,
        all_touched=False,
        dtype="float32",
    )
    poverty_score[poverty_score == sentinel] = np.nan
    poverty_score[~boundary_mask] = np.nan
    covered = boundary_mask & np.isfinite(poverty_score)
    return poverty_score, match_rows, {
        "osm_admin_level8_features_in_reference_bbox": int(len(districts)),
        "matched_district_features": int(sum(bool(row["matched"]) for row in match_rows)),
        "boundary_coverage_fraction": round(float(covered.sum() / boundary_mask.sum()), 6),
        "direction": "higher INEI poverty midpoint -> higher response-capacity gap",
    }


def stats(name: str, data: np.ndarray, boundary_mask: np.ndarray) -> dict[str, object]:
    valid = boundary_mask & np.isfinite(data)
    values = data[valid]
    return {
        "layer": name,
        "valid_cells_in_boundary": int(values.size),
        "boundary_valid_fraction": round(float(values.size / boundary_mask.sum()), 6),
        "min": round(float(values.min()), 6) if values.size else "",
        "mean": round(float(values.mean()), 6) if values.size else "",
        "p95": round(float(np.percentile(values, 95)), 6) if values.size else "",
        "max": round(float(values.max()), 6) if values.size else "",
        "within_0_1": bool(values.size and values.min() >= 0.0 and values.max() <= 1.0),
    }


def component_influence_diagnostics(
    layers: dict[str, np.ndarray],
    weights: dict[str, float],
    valid: np.ndarray,
) -> list[dict[str, object]]:
    """Describe component prevalence and spatial variability without rewriting weights."""

    if set(layers) != set(weights):
        raise ValueError("diagnostic layers and weights must use the same component names")
    metrics: dict[str, dict[str, float]] = {}
    for name, layer in layers.items():
        values = layer[valid & np.isfinite(layer)]
        if values.size == 0:
            raise ValueError(f"no finite diagnostic values for {name}")
        metrics[name] = {
            "mean_component_score": float(np.mean(values)),
            "std_component_score": float(np.std(values)),
            "p95_component_score": float(np.percentile(values, 95)),
            "weighted_mean_contribution": float(np.mean(values) * weights[name]),
            "weighted_std_contribution": float(np.std(values) * weights[name]),
        }
    mean_total = sum(item["weighted_mean_contribution"] for item in metrics.values())
    std_total = sum(item["weighted_std_contribution"] for item in metrics.values())
    rows = []
    for name, item in metrics.items():
        rows.append({
            "component": name,
            "nominal_weight": weights[name],
            **item,
            "realized_mean_contribution_share": (
                item["weighted_mean_contribution"] / mean_total if mean_total else 0.0
            ),
            "marginal_weighted_sd_share": (
                item["weighted_std_contribution"] / std_total if std_total else 0.0
            ),
            "interpretation": (
                "Descriptive marginal weighted SD share; ignores covariance, is not an "
                "effective weight, not ranking attribution, and not a calibration target."
            ),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    missing = [path for path in INPUTS if not path.exists()]
    if missing:
        raise FileNotFoundError("missing exposure-indicator inputs: " + ", ".join(map(str, missing)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile, boundary_mask = read_reference()
    road_access = read_matching_raster(ROAD_ACCESS, profile, boundary_mask)
    population, population_meta = build_population_exposure(profile, boundary_mask)
    buildings, building_meta = build_built_infrastructure(profile, boundary_mask)
    health, health_meta = build_health_remoteness(profile, boundary_mask)
    poverty, poverty_matches, poverty_meta = build_poverty_context(profile, boundary_mask)

    infrastructure = combine_weighted_complete_case(
        {"population_exposure": population, "built_infrastructure_exposure": buildings},
        INFRASTRUCTURE_WEIGHTS,
        boundary_mask,
    )
    exposure_indicators = combine_weighted_complete_case(
        {"road_access_proximity": road_access, "infrastructure_exposure": infrastructure},
        SOCIOECONOMIC_WEIGHTS,
        boundary_mask,
    )

    layers = {
        "population_exposure": population,
        "built_infrastructure_exposure": buildings,
        "infrastructure_exposure": infrastructure,
        "poverty_context": poverty,
        "health_service_remoteness": health,
        "exposure_indicators": exposure_indicators,
    }
    output_paths: dict[str, Path] = {}
    for name, data in layers.items():
        path = OUT_DIR / f"{name}_0_1.tif"
        _write_raster(path, data, profile, sanitize=True)
        output_paths[name] = path

    grid_rows = [stats(name, data, boundary_mask) for name, data in layers.items()]
    write_csv(OUT_DIR / "exposure_indicators_grid_check.csv", grid_rows)
    write_csv(OUT_DIR / "district_poverty_match.csv", poverty_matches)
    component_rows = [
        {
            "component": "road_access_proximity",
            "parent": "exposure_indicators",
            "weight": SOCIOECONOMIC_WEIGHTS["road_access_proximity"],
            "included_in_pim": True,
            "source": rel(ROAD_ACCESS),
            "direction": "closer to mapped roads -> higher access/infrastructure exposure score",
            "claim_level": "provisional",
        },
        {
            "component": "infrastructure_exposure",
            "parent": "exposure_indicators",
            "weight": SOCIOECONOMIC_WEIGHTS["infrastructure_exposure"],
            "included_in_pim": True,
            "source": rel(output_paths["infrastructure_exposure"]),
            "direction": "more mapped population/buildings -> higher exposure score",
            "claim_level": "provisional",
        },
        {
            "component": "population_exposure",
            "parent": "infrastructure_exposure",
            "weight": INFRASTRUCTURE_WEIGHTS["population_exposure"],
            "included_in_pim": True,
            "source": rel(WORLDPOP),
            "direction": "higher population count -> higher exposure score",
            "claim_level": "provisional",
        },
        {
            "component": "built_infrastructure_exposure",
            "parent": "infrastructure_exposure",
            "weight": INFRASTRUCTURE_WEIGHTS["built_infrastructure_exposure"],
            "included_in_pim": True,
            "source": rel(OSM_BUILDINGS),
            "direction": "higher local mapped-building density -> higher exposure score",
            "claim_level": "provisional",
        },
        {
            "component": "poverty_context",
            "parent": "response_capacity_context",
            "weight": 0.0,
            "included_in_pim": False,
            "source": rel(INEI_POVERTY),
            "direction": "higher district poverty -> higher response-capacity gap",
            "claim_level": "diagnostic_only",
            "evidence_role": "response_capacity_context",
        },
        {
            "component": "health_service_remoteness",
            "parent": "response_capacity_context",
            "weight": 0.0,
            "included_in_pim": False,
            "source": rel(OSM_HEALTH_POIS),
            "direction": "farther from mapped health services -> higher response-capacity gap",
            "claim_level": "diagnostic_only",
            "evidence_role": "response_capacity_context",
        },
    ]
    write_csv(OUT_DIR / "exposure_indicators_components.csv", component_rows)

    valid = boundary_mask & np.isfinite(exposure_indicators)
    contribution_rows = component_influence_diagnostics(
        {
            "road_access_proximity": road_access,
            "infrastructure_exposure": infrastructure,
        },
        SOCIOECONOMIC_WEIGHTS,
        valid,
    )
    write_csv(OUT_DIR / "exposure_indicators_contribution_diagnostics.csv", contribution_rows)

    manifest = {
        "boundary_id": BOUNDARY_ID,
        "experiment_id": EXPERIMENT_ID,
        "status": "provisional",
        "criterion_name": "exposure_indicators",
        "semantic_meaning": "road/access plus population and mapped-building exposure",
        "reference_grid": {
            "path": rel(REFERENCE),
            "crs": str(profile["crs"]),
            "width": profile["width"],
            "height": profile["height"],
            "resolution_m": abs(float(profile["transform"].a)),
        },
        "weights": {
            "exposure_indicators": SOCIOECONOMIC_WEIGHTS,
            "infrastructure_exposure": INFRASTRUCTURE_WEIGHTS,
        },
        "weight_note": (
            "The 0.45/0.55 split follows the supplied Peru sub-criteria table; the 0.50/0.50 "
            "population/building split is an implementation placeholder. Nominal weights do "
            "not imply equal realized mean contributions; see the contribution diagnostics."
        ),
        "calibration_decision": (
            "Retain the supplied 0.45/0.55 coefficients. Do not force equal component means: "
            "mean-contribution share describes spatial prevalence, while marginal weighted SD "
            "share is only a covariance-blind descriptive diagnostic, not ranking attribution."
        ),
        "nodata_policy": "complete-case within the boundary; any required component NoData stays NoData",
        "population": population_meta,
        "buildings": building_meta,
        "poverty_context": poverty_meta,
        "health_context": health_meta,
        "context_layers_in_pim": False,
        "outputs": {
            name: {"path": rel(path), "sha256": sha256(path)} for name, path in output_paths.items()
        },
    }
    (OUT_DIR / "exposure_indicators_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote exposure indicators: {output_paths['exposure_indicators']}")
    print(f"Boundary-valid cells: {int(boundary_mask.sum()):,}")
    print(f"WorldPop count inside boundary after sum resampling: {population_meta['population_count_sum']:,.3f}")
    print(f"Matched INEI district polygons: {poverty_meta['matched_district_features']}")
    print(f"Health-service features in padded bbox: {health_meta['health_features_in_padded_bbox']}")


if __name__ == "__main__":
    main()
