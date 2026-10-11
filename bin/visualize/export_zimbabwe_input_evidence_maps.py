#!/usr/bin/env python3
"""Export Zimbabwe diagnostic factors aligned with the Peru evidence inventory.

Physical-unit inputs remain in their original units. Existing 0-1 indicators
are labelled as relative evidence scores rather than raw measurements.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rasterio.enums import Resampling
from rasterio.warp import reproject


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/visualize"))

import export_peru_former_raw_input_factor_maps as base


OUT_DIR = ROOT / "outputs/slide_ready_figures/zimbabwe_input_evidence_maps"
INDIVIDUAL_DIR = OUT_DIR / "individual"
BOUNDARY_GPKG = ROOT / "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg"
BOUNDARY_LAYER = "v1_working_boundary"
REFERENCE_GRID = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif"
INDEX = OUT_DIR / "index.csv"


def as_km(data_m: np.ndarray) -> np.ndarray:
    return data_m / 1000.0


RASTER_SPECS = [
    base.RasterSpec(
        "rainfall_climatology", "Rainfall climatology (Nov-Mar)", "mm / rainy season", "flood",
        ROOT / "outputs/zimbabwe_pim_scenarios/rainfall_sensitivity/criteria/rainfall_climatology_raw_mm_per_season_PROVISIONAL_30m.tif",
        ("#eff3ff", "#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c"),
        (380, 420, 460, 500, 540, 580, 630),
        "CHIRPS v3 Nov-Mar climatological mean, 1981/82-2023/24",
        "Effective resolution is about 5 km despite display on the 30 m reference grid",
    ),
    base.RasterSpec(
        "elevation", "Elevation", "m", "terrain_diagnostic",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif",
        ("#006837", "#78c679", "#d9ef8b", "#fee08b", "#d8b365", "#8c510a"),
        (800, 1000, 1200, 1400, 1600, 1800, 2000),
        "SRTM 1 arc-second DEM reprojected to the Zimbabwe reference grid",
        "Terrain elevation, not flood depth or inundation",
    ),
    base.RasterSpec(
        "slope_degrees", "Slope", "degrees", "terrain_diagnostic",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_slope_degrees_utm35s_30m.tif",
        ("#ffffcc", "#ffeda0", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"),
        (0, 5, 15, 25, 35, 45, 90), "Slope derived from the SRTM DEM",
        "Terrain gradient only; not flow velocity",
    ),
    base.RasterSpec(
        "twi", "Topographic wetness index", "TWI", "flood",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_twi.tif",
        ("#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#225ea8"),
        (3, 5, 6, 7, 9, 14, 28), "DEM-derived TWI", "Terrain wetness tendency, not observed inundation",
    ),
    base.RasterSpec(
        "distance_to_drainage", "Distance to drainage", "km", "flood",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_distance_to_drainage_t500.tif",
        ("#084081", "#0868ac", "#2b8cbe", "#4eb3d3", "#a8ddb5", "#f0f9e8"),
        (0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5),
        "Euclidean distance to DEM-derived drainage cells at the 500-cell threshold",
        "Drainage proximity, not hydraulic flood routing", transform=as_km,
    ),
    base.RasterSpec(
        "upstream_area", "Upstream contributing area", "km2", "terrain_diagnostic",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_flow_accumulation.tif",
        ("#f6eff7", "#d0d1e6", "#a6bddb", "#67a9cf", "#1c9099", "#016c59"),
        (0, 0.1, 1, 10, 100, 1000, 3000),
        "D8 flow accumulation converted from cells to upstream area",
        "DEM-derived routing indicator; not calibrated discharge",
        transform=base.flow_cells_to_upstream_area_km2,
        resampling=Resampling.nearest,
    ),
    base.RasterSpec(
        "soil_k_factor", "Soil erodibility K-factor", "K (US customary)", "sediment_diagnostic",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif",
        ("#f7fcf5", "#c7e9c0", "#74c476", "#31a354", "#006d2c", "#00441b"),
        (0.10, 0.13, 0.16, 0.19, 0.22, 0.25, 0.28),
        "SoilGrids-derived 0-5 cm soil-erodibility K-factor aligned to the Zimbabwe reference grid",
        "Displayed on the 30 m grid for alignment; effective source resolution remains 250 m",
    ),
    base.RasterSpec(
        "ls_factor", "LS-factor", "LS", "sediment",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/ls_factor/zimbabwe_ls_factor_capped50_hillslope_30m.tif",
        ("#ffffd4", "#fee391", "#fec44f", "#fe9929", "#d95f0e", "#993404"),
        (0, 0.5, 1, 2, 5, 10, 50), "SRTM-derived hillslope LS-factor, capped at 50",
        "Current Sediment component at local weight 0.35; main-channel cells remain masked",
    ),
    base.RasterSpec(
        "c_factor", "C-factor", "C", "sediment",
        ROOT / "outputs/zimbabwe_esa_worldcover_2021/c_factor/c_factor_zimbabwe_30m.tif",
        ("#006837", "#31a354", "#addd8e", "#ffffbf", "#fdae61", "#d7191c"),
        (0, 0.01, 0.03, 0.05, 0.1, 0.3, 0.7), "ESA WorldCover-derived cover-management factor",
        "Class-based estimate; current Sediment component at local weight 0.30 and related to the separate land-cover evidence family",
        resampling=Resampling.nearest,
    ),
    base.RasterSpec(
        "land_cover_pressure", "Land-cover pressure", "relative score", "land_mining",
        ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/land_cover_pressure_0_1.tif",
        ("#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"),
        (0, 0.2, 0.4, 0.6, 0.8, 1.0),
        "ESA WorldCover-derived land-cover pressure used directly in the Land Use / Mining criterion",
        "Class-based pressure score, not a local land-management survey",
    ),
    base.RasterSpec(
        "mineral_reference_proximity", "USGS mineral-reference proximity", "relative score", "land_mining",
        ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/mining_pressure_0_1.tif",
        ("#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"),
        (0, 0.2, 0.4, 0.6, 0.8, 1.0),
        "Tiered distance-decay score from USGS Africa GIS mineral facilities and deposits",
        "Reference proximity only; not a verified active ASM footprint",
    ),
    base.RasterSpec(
        "water_wetland_context", "Water and wetland context", "relative score", "environmental",
        ROOT / "outputs/zimbabwe_pim_scenarios/environmental_sensitivity/water_wetland_context_0_1.tif",
        ("#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"),
        (0, 0.2, 0.4, 0.6, 0.8, 1.0),
        "Combined WorldCover, JRC surface-water and mapped-water proximity context",
        "Environmental context indicator, not ecological valuation",
    ),
    base.RasterSpec(
        "protected_area_context", "Protected-area proximity score", "relative score", "environmental",
        ROOT / "outputs/zimbabwe_pim_scenarios/environmental_sensitivity/protected_area_context_0_1.tif",
        ("#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"),
        (0, 0.2, 0.4, 0.6, 0.8, 1.0), "WDPA protected/conserved-area proximity context",
        "Proximity context, not a site-specific ecological sensitivity survey",
    ),
    base.RasterSpec(
        "distance_to_roads", "Distance to roads", "km", "socioeconomic_diagnostic",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/comparable_distance_factors/zimbabwe_distance_to_roads_km_30m.tif",
        ("#f7f7f7", "#d9d9d9", "#bdbdbd", "#969696", "#636363", "#252525"),
        (0, 0.25, 0.5, 1, 2, 5, 10),
        "Euclidean distance to OpenStreetMap / Geofabrik road lines",
        "Access-distance context, not socioeconomic vulnerability",
    ),
    base.RasterSpec(
        "distance_to_water_features", "Distance to water features", "km", "environmental_diagnostic",
        ROOT / "outputs/zimbabwe_terrain_hydrology_factors/comparable_distance_factors/zimbabwe_distance_to_water_features_km_30m.tif",
        ("#08306b", "#2171b5", "#6baed6", "#bdd7e7", "#eff3ff", "#f7fbff"),
        (0, 0.25, 0.5, 1, 2, 5, 15),
        "Euclidean distance to OpenStreetMap / Geofabrik water polygons and waterways",
        "Water-context distance only; not ecological valuation",
    ),
    base.RasterSpec(
        "road_access_proximity", "Road-access proximity", "relative score", "socioeconomic",
        ROOT / "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/exposure_indicators_0_1.tif",
        ("#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"),
        (0, 0.2, 0.4, 0.6, 0.8, 1.0), "Road/access proximity indicator used by the current PIM",
        "Does not measure population, buildings, infrastructure exposure or vulnerability",
    ),
]


MAIN_12_COLUMNS = 3
MAIN_12_ROWS = 4

CATEGORY_SPEC = base.CategorySpec(
    "esa_worldcover_2021", "ESA WorldCover 2021", "land_mining",
    (ROOT / "data/raw/esa_worldcover_2021_zimbabwe/ESA_WorldCover_10m_2021_v200_S21E027_Map.tif",),
    "ESA WorldCover 2021 categorical land-cover classes",
    "Global 10 m land-cover classification, not locally validated land use",
)

INPUTS = [spec.source_path for spec in RASTER_SPECS] + [BOUNDARY_GPKG, REFERENCE_GRID, *CATEGORY_SPEC.source_paths]
STALE_OUTPUTS = [
    OUT_DIR / "zimbabwe_current_input_evidence_panel_no_title_caption.png",
    OUT_DIR / "zimbabwe_current_input_evidence_panel_no_title_caption.pdf",
    INDIVIDUAL_DIR / "zimbabwe_evidence_soil_erosion_composite_no_title_caption.png",
    INDIVIDUAL_DIR / "zimbabwe_evidence_soil_erosion_composite_no_title_caption.pdf",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def save_figure(fig, path: Path, **kwargs) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    fig.savefig(temporary, format=path.suffix.lstrip("."), **kwargs)
    temporary.replace(path)


def boundary_stats(data: np.ndarray, boundary_mask: np.ndarray) -> dict[str, object]:
    valid = boundary_mask & np.isfinite(data)
    values = data[valid]
    denominator = int(boundary_mask.sum())
    return {
        "valid_cells": int(values.size),
        "valid_fraction_within_study_area": round(float(values.size / denominator), 6) if denominator else "",
        "min": round(float(values.min()), 6) if values.size else "",
        "mean": round(float(values.mean()), 6) if values.size else "",
        "max": round(float(values.max()), 6) if values.size else "",
    }


def align_to_reference(data: np.ndarray, profile: dict, ref_profile: dict, mask: np.ndarray, resampling: Resampling) -> np.ndarray:
    same_grid = (
        profile["crs"] == ref_profile["crs"]
        and profile["width"] == ref_profile["width"]
        and profile["height"] == ref_profile["height"]
        and profile["transform"].almost_equals(ref_profile["transform"])
    )
    if same_grid:
        result = data.copy()
    else:
        result = np.full((ref_profile["height"], ref_profile["width"]), np.nan, dtype="float32")
        reproject(
            source=data,
            destination=result,
            src_transform=profile["transform"], src_crs=profile["crs"],
            dst_transform=ref_profile["transform"], dst_crs=ref_profile["crs"],
            src_nodata=np.nan, dst_nodata=np.nan, resampling=resampling,
        )
    result[~mask] = np.nan
    return result


def save_individual(slug: str, draw_fn) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(7.0, 8.4), constrained_layout=True)
    draw_fn(ax)
    png = INDIVIDUAL_DIR / f"zimbabwe_evidence_{slug}_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    save_figure(fig, png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    save_figure(fig, pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return png, pdf


def panel_axes(count: int):
    if count == 12:
        fig = plt.figure(figsize=(14.1, 21.0))
        grid = fig.add_gridspec(
            MAIN_12_ROWS, MAIN_12_COLUMNS,
            left=0.045, right=0.985, top=0.97, bottom=0.045,
            wspace=0.16, hspace=0.25,
        )
        return fig, [
            fig.add_subplot(grid[row, column])
            for row in range(MAIN_12_ROWS)
            for column in range(MAIN_12_COLUMNS)
        ]
    if count == 4:
        fig = plt.figure(figsize=(18.0, 5.8))
        grid = fig.add_gridspec(1, 4, left=0.025, right=0.985, top=0.97, bottom=0.05, wspace=0.18)
        return fig, [fig.add_subplot(grid[0, index]) for index in range(4)]
    if count == 5:
        fig = plt.figure(figsize=(15.5, 10.5))
        grid = fig.add_gridspec(2, 6, left=0.035, right=0.985, top=0.98, bottom=0.04, wspace=0.22, hspace=0.22)
        spans = [(0, 0, 2), (0, 2, 4), (0, 4, 6), (1, 1, 3), (1, 3, 5)]
        return fig, [fig.add_subplot(grid[row, start:end]) for row, start, end in spans]
    if count == 6:
        fig = plt.figure(figsize=(14.1, 10.5))
        grid = fig.add_gridspec(
            2, 3, left=0.035, right=0.985, top=0.98, bottom=0.04,
            wspace=0.20, hspace=0.22,
        )
        return fig, [
            fig.add_subplot(grid[row, column])
            for row in range(2)
            for column in range(3)
        ]
    if count == 2:
        fig = plt.figure(figsize=(9.0, 5.8))
        grid = fig.add_gridspec(1, 2, left=0.05, right=0.98, top=0.97, bottom=0.05, wspace=0.20)
        return fig, [fig.add_subplot(grid[0, index]) for index in range(2)]
    if count == 3:
        fig = plt.figure(figsize=(13.5, 5.8))
        grid = fig.add_gridspec(1, 3, left=0.035, right=0.985, top=0.97, bottom=0.05, wspace=0.20)
        return fig, [fig.add_subplot(grid[0, index]) for index in range(3)]
    raise ValueError(f"unsupported evidence-panel item count: {count}")


def save_panel(slug: str, items: list[dict[str, object]], boundary: gpd.GeoDataFrame) -> tuple[Path, Path]:
    fig, axes = panel_axes(len(items))
    compact = len(items) >= 12
    for index, (ax, item) in enumerate(zip(axes, items, strict=True)):
        label = f"({chr(97 + index)})"
        if item["kind"] == "category":
            base.draw_category_map(ax, item["spec"], item["data_wgs84"], item["extent"], boundary, label, compact)
        else:
            base.draw_continuous_map(ax, item["spec"], item["data_wgs84"], item["extent"], boundary, label, compact)
    png = OUT_DIR / f"zimbabwe_{slug}_evidence_panel_no_title_caption.png"
    pdf = png.with_suffix(".pdf")
    save_figure(fig, png, dpi=300, bbox_inches="tight", pad_inches=0.03)
    save_figure(fig, pdf, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return png, pdf


def main() -> None:
    for path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    for path in STALE_OUTPUTS:
        path.unlink(missing_ok=True)
    base.BOUNDARY_GPKG = BOUNDARY_GPKG
    base.BOUNDARY_LAYER = BOUNDARY_LAYER
    base.REFERENCE_GRID = REFERENCE_GRID
    base.CATEGORY_SPECS = [CATEGORY_SPEC]
    boundary_wgs84, boundary_ref = base.load_boundary()
    boundary_mask, ref_profile = base.reference_mask(boundary_ref)
    rows: list[dict[str, object]] = []
    prepared: list[dict[str, object]] = []

    for spec in RASTER_SPECS:
        source_data, source_profile = base.read_raster_data(spec.source_path, spec.transform)
        data = align_to_reference(source_data, source_profile, ref_profile, boundary_mask, spec.resampling)
        data_wgs84, extent = base.reproject_data_to_wgs84(data, ref_profile, spec.resampling)
        item = {"kind": "continuous", "spec": spec, "data_wgs84": data_wgs84, "extent": extent}
        prepared.append(item)
        png, pdf = save_individual(
            spec.slug,
            lambda ax, item=item: base.draw_continuous_map(
                ax, item["spec"], item["data_wgs84"], item["extent"], boundary_wgs84, None, False
            ),
        )
        for fmt, path in (("png", png), ("pdf", pdf)):
            rows.append({
                "site": "Upper Mzingwane working study area, Zimbabwe",
                "factor": spec.slug, "label": spec.label, "criterion_group": spec.group,
                "unit": spec.unit, "figure_format": fmt, "figure_path": rel(path),
                "source_path": rel(spec.source_path), "source_sha256": base.sha256(spec.source_path),
                "classification": "variable-specific physical or explicitly labelled relative-score classes",
                "data_basis": spec.data_basis, "limitation": spec.limitation,
                "claim_level": "diagnostic_only",
                **boundary_stats(data, boundary_mask),
            })

    worldcover, extent = base.load_worldcover(boundary_wgs84)
    worldcover_item = {"kind": "category", "spec": CATEGORY_SPEC, "data_wgs84": worldcover, "extent": extent}
    prepared.append(worldcover_item)
    png, pdf = save_individual(
        CATEGORY_SPEC.slug,
        lambda ax: base.draw_category_map(ax, CATEGORY_SPEC, worldcover, extent, boundary_wgs84, None, False),
    )
    for fmt, path in (("png", png), ("pdf", pdf)):
        rows.append({
            "site": "Upper Mzingwane working study area, Zimbabwe",
            "factor": CATEGORY_SPEC.slug, "label": CATEGORY_SPEC.label, "criterion_group": CATEGORY_SPEC.group,
            "unit": "land-cover class", "figure_format": fmt, "figure_path": rel(path),
            "source_path": rel(CATEGORY_SPEC.source_paths[0]),
            "source_sha256": base.sha256(CATEGORY_SPEC.source_paths[0]),
            "classification": "ESA WorldCover 2021 class codes",
            "data_basis": CATEGORY_SPEC.data_basis, "limitation": CATEGORY_SPEC.limitation,
            "claim_level": "diagnostic_only",
        })

    by_slug = {item["spec"].slug: item for item in prepared}
    panels = {
        "peru_aligned_main_12": [
            by_slug[slug] for slug in base.PERU_MAIN_12_FACTOR_ORDER
        ],
        "flood_sediment_direct": [
            by_slug["rainfall_climatology"], by_slug["twi"], by_slug["distance_to_drainage"],
            by_slug["soil_k_factor"], by_slug["ls_factor"], by_slug["c_factor"],
        ],
        "land_environment_access_direct": [
            by_slug["land_cover_pressure"], by_slug["mineral_reference_proximity"],
            by_slug["water_wetland_context"], by_slug["protected_area_context"],
            by_slug["road_access_proximity"],
        ],
        "supporting_diagnostics": [
            by_slug["elevation"], by_slug["slope_degrees"], by_slug["upstream_area"],
            by_slug["esa_worldcover_2021"], by_slug["distance_to_roads"],
            by_slug["distance_to_water_features"],
        ],
    }
    for panel_slug, items in panels.items():
        png, pdf = save_panel(panel_slug, items, boundary_wgs84)
        source_paths = tuple(dict.fromkeys(
            source
            for item in items
            for source in base.source_paths_for_spec(item["spec"])
        ))
        for fmt, path in (("png", png), ("pdf", pdf)):
            rows.append({
                "site": "Upper Mzingwane working study area, Zimbabwe",
                "panel": panel_slug, "figure_format": fmt, "figure_path": rel(path),
                "factors": "; ".join(item["spec"].slug for item in items),
                "source_path": "; ".join(rel(source) for source in source_paths),
                "source_sha256": base.source_hash_record(source_paths),
                "classification": (
                    "Peru-aligned factor order with site-specific numeric classes and matched variable palettes"
                    if panel_slug == "peru_aligned_main_12"
                    else "physical units, categorical classes, or explicitly labelled relative evidence scores"
                ),
                "missing_factors": "",
                "claim_level": "diagnostic_only",
            })
    write_csv(INDEX, rows)
    print(f"wrote {len(rows)} Zimbabwe evidence-map records to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
