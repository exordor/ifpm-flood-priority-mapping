#!/usr/bin/env python3
"""Build provisional PIM Environmental Sensitivity criterion rasters.

The criterion is intentionally narrow: it uses water/wetland context and
protected-area proximity as environmental-sensitivity indicators. It does not
claim ecological valuation or final habitat sensitivity.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.warp import Resampling, reproject
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parents[2]
PERU_SERNANP = (
    ROOT / "data/raw/sernanp_peru_protected_areas/pe1_sernanp_protected_areas.gpkg"
)
INPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
    ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W072_Map.tif",
    ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_water_a_free_1.shp",
    ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_waterways_free_1.shp",
    ROOT / "data/raw/sernanp_peru_protected_areas/pe1_sernanp_protected_areas.gpkg",
]
OUTPUTS = [
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/environmental_sensitivity_0_1.tif",
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/water_wetland_context_0_1.tif",
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/protected_area_context_0_1.tif",
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/environmental_sensitivity_manifest.csv",
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/environmental_sensitivity_components.csv",
    ROOT / "outputs/pim_environmental_sensitivity/environmental_sensitivity_v0_1_summary.csv",
]
WORLDCOVER_SENSITIVE_CLASSES = {80, 90, 95}
ENVIRONMENTAL_CONTEXT_WEIGHTS = {
    "Zimbabwe": {
        "water_wetland_context": 0.55,
        "protected_ecological_context": 0.45,
    },
    "Peru": {
        "water_wetland_context": 0.60,
        "protected_ecological_context": 0.40,
    },
}


@dataclass(frozen=True)
class SiteConfig:
    site: str
    boundary_id: str
    ref: Path
    boundary_gpkg: Path
    boundary_layer: str
    output_dir: Path
    worldcover_paths: tuple[Path, ...]
    jrc_occurrence_path: Path | None
    water_vectors: tuple[tuple[Path, str | None], ...]
    protected_vectors: tuple[tuple[Path, str | None], ...]


SITES = [
    SiteConfig(
        site="Zimbabwe",
        boundary_id="boundary_v1",
        ref=ROOT / "outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif",
        boundary_gpkg=ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg",
        boundary_layer="v1_working_boundary",
        output_dir=ROOT / "outputs/boundary_v1/environmental_sensitivity_v0_1",
        worldcover_paths=(
            ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_worldcover_2021_native_10m.tif",
        ),
        jrc_occurrence_path=ROOT / "outputs/v1_full_methodology_evidence_sweep/rasters/v1_jrc_gsw_occurrence.tif",
        water_vectors=(
            (
                ROOT / "outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_review_layers.gpkg",
                "geoportal_water_areas_v1",
            ),
        ),
        protected_vectors=(
            (
                ROOT / "outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_review_layers.gpkg",
                "wdpca_protected_polygons_v1",
            ),
        ),
    ),
    SiteConfig(
        site="Peru",
        boundary_id="pe1",
        ref=ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif",
        boundary_gpkg=ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
        boundary_layer="peru_pilot_boundary",
        output_dir=ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1",
        worldcover_paths=(
            ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W072_Map.tif",
            ROOT / "data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif",
        ),
        jrc_occurrence_path=None,
        water_vectors=(
            (
                ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_water_a_free_1.shp",
                None,
            ),
            (
                ROOT / "data/raw/geofabrik_osm_peru_pilot/extracted/gis_osm_waterways_free_1.shp",
                None,
            ),
        ),
        protected_vectors=(
            (
                PERU_SERNANP,
                "sernanp_protected_areas",
            ),
        ),
    ),
]

import sys
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import raster_stats as stats
from _lib.ifpm_tools import write_raster as _write_raster
from functools import partial

write_raster = partial(_write_raster, sanitize=True)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_reference(config: SiteConfig) -> tuple[dict, np.ndarray, gpd.GeoDataFrame]:
    with rasterio.open(config.ref) as ref:
        profile = ref.profile.copy()
        crs = ref.crs
        shape = (ref.height, ref.width)
        transform = ref.transform
    boundary = gpd.read_file(config.boundary_gpkg, layer=config.boundary_layer).to_crs(crs)
    mask = geometry_mask(boundary.geometry, out_shape=shape, transform=transform, invert=True)
    return profile, mask, boundary


def reproject_to_reference(
    paths: tuple[Path, ...],
    profile: dict,
    resampling: Resampling,
) -> np.ndarray:
    out = np.full((profile["height"], profile["width"]), np.nan, dtype="float32")
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        tmp = np.full(out.shape, np.nan, dtype="float32")
        with rasterio.open(path) as src:
            reproject(
                source=rasterio.band(src, 1),
                destination=tmp,
                src_transform=src.transform,
                src_crs=src.crs,
                src_nodata=src.nodata,
                dst_transform=profile["transform"],
                dst_crs=profile["crs"],
                dst_nodata=np.nan,
                resampling=resampling,
            )
        valid = np.isfinite(tmp)
        out[valid] = tmp[valid]
    return out


def binary_proximity_score(binary: np.ndarray, profile: dict, mask: np.ndarray) -> np.ndarray:
    if not np.any(mask & binary):
        out = np.zeros(mask.shape, dtype="float32")
        out[~mask] = np.nan
        return out
    res = abs(float(profile["transform"].a))
    dist = distance_transform_edt(~binary) * res
    values = dist[mask & np.isfinite(dist)]
    low, high = np.nanpercentile(values, [2, 98])
    if not np.isfinite(high) or high <= low:
        high = low + 1.0
    out = np.clip(1.0 - (dist - low) / (high - low), 0.0, 1.0).astype("float32")
    out[~mask] = np.nan
    return out


def weighted_average_scores(
    layers: list[tuple[np.ndarray, float]],
    mask: np.ndarray,
) -> np.ndarray:
    first = layers[0][0]
    numerator = np.zeros(first.shape, dtype="float32")
    denominator = np.zeros(first.shape, dtype="float32")
    for layer, weight in layers:
        valid = mask & np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        denominator[valid] += weight
    out = np.full(first.shape, np.nan, dtype="float32")
    valid = denominator > 0
    out[valid] = numerator[valid] / denominator[valid]
    out[~mask] = np.nan
    return np.clip(out, 0.0, 1.0).astype("float32")


def read_vector_features(
    vector_specs: tuple[tuple[Path, str | None], ...],
    boundary: gpd.GeoDataFrame,
    target_crs,
    buffer_m: float,
) -> tuple[gpd.GeoDataFrame, int]:
    clipped: list[gpd.GeoDataFrame] = []
    total_raw = 0
    clip_geom = boundary.geometry.iloc[0].buffer(buffer_m)
    clip_gdf = gpd.GeoDataFrame(geometry=[clip_geom], crs=target_crs)
    for path, layer in vector_specs:
        if not path.exists():
            raise FileNotFoundError(path)
        gdf = gpd.read_file(path, layer=layer) if layer else gpd.read_file(path)
        total_raw += len(gdf)
        if gdf.empty:
            continue
        gdf = gdf.to_crs(target_crs)
        candidate = gpd.clip(gdf, clip_gdf)
        if not candidate.empty:
            clipped.append(candidate[["geometry"]].copy())
    if not clipped:
        return gpd.GeoDataFrame(geometry=[], crs=target_crs), total_raw
    merged = gpd.GeoDataFrame(
        geometry=np.concatenate([gdf.geometry.to_numpy() for gdf in clipped]),
        crs=target_crs,
    )
    return merged, total_raw


def vector_proximity_score(
    features: gpd.GeoDataFrame,
    profile: dict,
    mask: np.ndarray,
) -> np.ndarray:
    if features.empty:
        out = np.zeros(mask.shape, dtype="float32")
        out[~mask] = np.nan
        return out
    burned = rasterize(
        [(geom, 1) for geom in features.geometry if geom is not None and not geom.is_empty],
        out_shape=(profile["height"], profile["width"]),
        transform=profile["transform"],
        fill=0,
        dtype="uint8",
        all_touched=True,
    )
    return binary_proximity_score(burned == 1, profile, mask)


def vector_evidence_state(features_in_context: int, raw_features: int) -> str:
    """Describe whether a checked vector source contributes local evidence."""
    if features_in_context > 0:
        return "features_present_within_context_zone"
    if raw_features > 0:
        return "sernanp_national_definitive_layer_checked_no_feature_within_context_zone"
    return "source_returned_no_features"


def build_site(config: SiteConfig) -> dict[str, object]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    profile, mask, boundary = read_reference(config)
    context_weights = ENVIRONMENTAL_CONTEXT_WEIGHTS[config.site]

    worldcover = reproject_to_reference(config.worldcover_paths, profile, Resampling.nearest)
    worldcover_codes = np.nan_to_num(worldcover, nan=-9999).astype("int32")
    worldcover_sensitive = np.isin(worldcover_codes, list(WORLDCOVER_SENSITIVE_CLASSES))
    worldcover_score = binary_proximity_score(worldcover_sensitive, profile, mask)

    component_rows: list[dict[str, object]] = [
        {
            "component": "worldcover_water_wetland_proximity",
            "component_weight": "",
            "source": "ESA WorldCover 2021 classes 80 water, 90 herbaceous wetland, 95 mangroves",
            "source_feature_count": int(np.sum(mask & worldcover_sensitive)),
            "claim_level": "provisional",
            **stats(worldcover_score, mask),
        }
    ]
    water_layers: list[tuple[np.ndarray, float]] = [(worldcover_score, 1.0)]

    if config.jrc_occurrence_path is not None:
        jrc = reproject_to_reference((config.jrc_occurrence_path,), profile, Resampling.bilinear)
        jrc_score = np.clip(jrc / 100.0, 0.0, 1.0).astype("float32")
        jrc_score[~mask] = np.nan
        water_layers.append((jrc_score, 1.0))
        component_rows.append({
            "component": "jrc_surface_water_occurrence",
            "component_weight": "",
            "source": "JRC Global Surface Water occurrence",
            "source_feature_count": "",
            "claim_level": "provisional",
            **stats(jrc_score, mask),
        })

    water_features, water_raw_count = read_vector_features(
        config.water_vectors,
        boundary,
        profile["crs"],
        buffer_m=5000,
    )
    water_vector_score = vector_proximity_score(water_features, profile, mask)
    water_layers.append((water_vector_score, 1.0))
    component_rows.append({
        "component": "water_vector_proximity",
        "component_weight": "",
        "source": "; ".join(rel(path) if layer is None else f"{rel(path)}:{layer}" for path, layer in config.water_vectors),
        "source_feature_count": len(water_features),
        "raw_feature_count": water_raw_count,
        "claim_level": "provisional",
        **stats(water_vector_score, mask),
    })

    protected_features, protected_raw_count = read_vector_features(
        config.protected_vectors,
        boundary,
        profile["crs"],
        buffer_m=5000,
    )
    protected_score = vector_proximity_score(protected_features, profile, mask)
    component_rows.append({
        "component": "protected_area_proximity",
        "component_weight": context_weights["protected_ecological_context"],
        "source": "; ".join(rel(path) if layer is None else f"{rel(path)}:{layer}" for path, layer in config.protected_vectors),
        "source_feature_count": len(protected_features),
        "raw_feature_count": protected_raw_count,
        "evidence_state": vector_evidence_state(
            features_in_context=len(protected_features),
            raw_features=protected_raw_count,
        ),
        "claim_level": "provisional",
        **stats(protected_score, mask),
    })

    water_component_weight = round(1.0 / len(water_layers), 6)
    for row in component_rows:
        if row["component"] in {
            "worldcover_water_wetland_proximity",
            "jrc_surface_water_occurrence",
            "water_vector_proximity",
        }:
            row["component_weight"] = (
                f"{context_weights['water_wetland_context']} * "
                f"{water_component_weight}"
            )

    water_context = weighted_average_scores(water_layers, mask)
    environmental = weighted_average_scores(
        [
            (water_context, context_weights["water_wetland_context"]),
            (protected_score, context_weights["protected_ecological_context"]),
        ],
        mask,
    )

    water_path = config.output_dir / "water_wetland_context_0_1.tif"
    protected_path = config.output_dir / "protected_area_context_0_1.tif"
    out_path = config.output_dir / "environmental_sensitivity_0_1.tif"
    write_raster(water_path, water_context, profile)
    write_raster(protected_path, protected_score, profile)
    write_raster(out_path, environmental, profile)

    protected_source_label = (
        "SERNANP national definitive protected-area proximity (layer 0)"
        if config.site == "Peru"
        else "WDPA protected/conserved-area proximity context"
    )

    manifest = [{
        "site": config.site,
        "boundary_id": config.boundary_id,
        "criterion": "environmental_sensitivity",
        "path": rel(out_path),
        "components": f"water/wetland context; {protected_source_label}",
        "component_rule": (
            f"{context_weights['water_wetland_context']} * water/wetland context + "
            f"{context_weights['protected_ecological_context']} * {protected_source_label}; "
            "water context is an equal-weight average of available water/wetland evidence"
        ),
        "claim_level": "provisional",
        "semantic_meaning": (
            f"water/wetland-led environmental context indicator with {protected_source_label}; "
            "not complete ecological sensitivity valuation"
        ),
        "nodata_policy": "preserve NoData outside boundary; no NoData-to-zero imputation",
        **stats(environmental, mask),
    }]
    write_csv(config.output_dir / "environmental_sensitivity_manifest.csv", manifest)
    write_csv(config.output_dir / "environmental_sensitivity_components.csv", component_rows)
    return manifest[0]


def active_site_configs(site: str = "Peru") -> list[SiteConfig]:
    selected = [config for config in SITES if config.site == site]
    if not selected:
        raise ValueError(f"unknown environmental-sensitivity site: {site}")
    return selected


def main() -> None:
    rows = [build_site(config) for config in active_site_configs()]
    write_csv(
        ROOT / "outputs/pim_environmental_sensitivity/environmental_sensitivity_v0_1_summary.csv",
        rows,
    )
    for row in rows:
        print(f"wrote {row['site']} ES to {row['path']} mean={row['mean']}")


if __name__ == "__main__":
    main()
