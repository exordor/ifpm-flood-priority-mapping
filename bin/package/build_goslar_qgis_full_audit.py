#!/usr/bin/env python3
"""Build a QGIS project package for the Goslar focus area.

The package shows the full Peru-style PIM chain for the Goslar focus area
(Harz, Germany): Copernicus DEM -> slope -> hydrology -> LS/K/C erosion
factors -> REGNIE rainfall -> EEA Natura 2000 protected areas -> criteria
stack -> exposure/environment -> priority scenarios. Intermediate products
are included so the whole pipeline can be inspected in QGIS.

The module can be imported with the workspace Python for configuration tests.
When executed without PyQGIS it relaunches itself with the QGIS application
Python, mirroring ``build_peru_former_zimbabwe_qgis_projects.py``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/goslar_qgis_full_audit"
STYLE_DIR = OUT_DIR / "styles"
MANIFEST = OUT_DIR / "manifest.csv"
VALIDATION = OUT_DIR / "validation.json"
README = OUT_DIR / "README.txt"
PORTABLE_DIR = ROOT / "exports/qgis_packages/goslar/FullAudit"
PROJECT_NAME = "IFPM_Goslar_FullAudit.qgz"
SITE_KEY = "goslar"
EXTERNAL_OVERLAY_GROUP = "7. External validation and overlays"


def discover_qgis_app() -> Path:
    configured = os.environ.get("QGIS_APP_PATH")
    if configured:
        candidates = [Path(configured)]
    else:
        candidates = [
            Path("/Applications/QGIS.app"),
            Path("/Applications/QGIS-LTR.app"),
            Path.home() / "Applications/QGIS.app",
            Path.home() / "Applications/QGIS-LTR.app",
            *sorted(Path("/Applications").glob("QGIS*.app")),
            *sorted((Path.home() / "Applications").glob("QGIS*.app")),
        ]
    for candidate in dict.fromkeys(candidates):
        if (candidate / "Contents/MacOS/python").exists():
            return candidate
    return candidates[0]


QGIS_APP = discover_qgis_app()
QGIS_PYTHON = QGIS_APP / "Contents/MacOS/python"
QGIS_PREFIX = QGIS_APP / "Contents/Resources/qgis"

# Same discrete five-class palettes as the Goslar PIM overview figure and the
# Peru pilot (ColorBrewer, equal-interval 0-1).
PRIORITY_COLORS = ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"]
CRITERIA_COLORS = {
    "flood_hazard": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "sediment": ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
    "landuse_asm": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "environmental": ["#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"],
    "socioeconomic": ["#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"],
}
STANDARD_CLASS_UPPER_BOUNDS = (0.2, 0.4, 0.6, 0.8, 1.0)
STANDARD_CLASS_LABELS = ("0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0")
INPUT_PALETTES = {
    "terrain": ["#f7fcf5", "#d9f0a3", "#addd8e", "#41ab5d", "#005a32"],
    "slope": ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
    "hydrology": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "erosion": ["#ffffd4", "#fed98e", "#fe9929", "#d95f0e", "#993404"],
    "rainfall": ["#fff7ec", "#fdd49e", "#fc8d59", "#d7301f", "#7f0000"],
    "land": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "population": ["#fff7f3", "#fcc5c0", "#fa9fb5", "#c51b8a", "#7a0177"],
    "wetness": ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
    "distance": ["#084081", "#2b8cbe", "#7bccc4", "#ccece6", "#f7fcfd"],
}


@dataclass(frozen=True)
class LayerSpec:
    key: str
    name: str
    group: str
    path: str
    kind: str
    role: str
    palette: str = ""
    visible: bool = False
    layer_name: str = ""
    unit: str = ""
    claim_level: str = "diagnostic_only"
    notes: str = ""


def raster(
    key: str,
    name: str,
    group: str,
    path: str,
    role: str,
    palette: str,
    *,
    visible: bool = False,
    unit: str = "",
    claim_level: str = "diagnostic_only",
    notes: str = "",
) -> LayerSpec:
    return LayerSpec(key, name, group, path, "raster", role, palette, visible, "", unit, claim_level, notes)


def vector(
    key: str,
    name: str,
    group: str,
    path: str,
    role: str,
    *,
    visible: bool = True,
    layer_name: str = "",
    claim_level: str = "diagnostic_only",
    notes: str = "",
) -> LayerSpec:
    return LayerSpec(key, name, group, path, "vector", role, "", visible, layer_name, unit="", claim_level=claim_level, notes=notes)


GOSLAR_LAYERS = (
    # 1. Priority result
    raster(
        "priority",
        "Relative flood-priority index",
        "1. Priority result",
        "outputs/goslar_pim_chain/priority_scenarios/scenarios/priority_goslar_direct_pim.tif",
        "priority_result",
        "priority",
        visible=True,
        unit="0-1",
        claim_level="provisional",
        notes="Goslar prototype mirror of the Peru PIM chain; weights FH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14. Not a validated flood-risk result.",
    ),
    # 2. Five PIM criteria
    raster("flood_hazard", "Flood-conditioning indicator (FH | PIM weight 0.34)", "2. Five PIM criteria", "outputs/goslar_pim_chain/priority_scenarios/pim_criteria/flood_hazard_0_1.tif", "criterion", "flood_hazard", unit="0-1"),
    raster("sediment", "Sediment / erosion score (SE | PIM weight 0.25)", "2. Five PIM criteria", "outputs/goslar_pim_chain/priority_scenarios/pim_criteria/sediment_0_1.tif", "criterion", "sediment", unit="0-1"),
    raster("landuse_asm", "General land-use pressure score (LU | PIM weight 0.17)", "2. Five PIM criteria", "outputs/goslar_pim_chain/priority_scenarios/pim_criteria/landuse_asm_0_1.tif", "criterion", "landuse_asm", unit="0-1"),
    raster("environmental", "Environmental context indicator (ES | PIM weight 0.10)", "2. Five PIM criteria", "outputs/goslar_pim_chain/priority_scenarios/pim_criteria/environmental_0_1.tif", "criterion", "environmental", unit="0-1"),
    raster("socioeconomic", "Socioeconomic exposure indicator (SV | PIM weight 0.14)", "2. Five PIM criteria", "outputs/goslar_pim_chain/priority_scenarios/pim_criteria/socioeconomic_0_1.tif", "criterion", "socioeconomic", unit="0-1"),
    # 3. Terrain and hydrology chain (intermediate products)
    raster("elevation", "Elevation (Copernicus DEM GLO-30)", "3. Terrain and hydrology", "outputs/goslar_pim_chain/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif", "input_factor", "terrain", unit="m"),
    raster("dem_filled", "DEM after sink fill", "3. Terrain and hydrology", "outputs/goslar_pim_chain/hydrology_derivatives/goslar_focus_dem_filled.tif", "input_factor", "terrain", unit="m"),
    raster("slope", "Slope", "3. Terrain and hydrology", "outputs/goslar_pim_chain/terrain_preprocessing/goslar_focus_slope_degrees_utm32n_30m.tif", "input_factor", "slope", unit="degrees"),
    raster("flow_direction", "Flow direction (D8)", "3. Terrain and hydrology", "outputs/goslar_pim_chain/hydrology_derivatives/goslar_focus_flow_direction_d8.tif", "input_factor", "hydrology", unit="D8 code"),
    raster("flow_accumulation", "Flow accumulation (contributing cells)", "3. Terrain and hydrology", "outputs/goslar_pim_chain/hydrology_derivatives/goslar_focus_flow_accumulation.tif", "input_factor", "hydrology", unit="cells"),
    raster("streams", "Derived streams (t500)", "3. Terrain and hydrology", "outputs/goslar_pim_chain/hydrology_derivatives/goslar_focus_streams_t500.tif", "input_factor", "hydrology", unit="stream mask"),
    raster("distance_drainage", "Distance to derived drainage (FH component weight 0.40)", "3. Terrain and hydrology", "outputs/goslar_pim_chain/hydrology_derivatives/goslar_focus_distance_to_drainage_t500.tif", "input_factor", "distance", unit="m", notes="Raw distance input; weight applies after inversion and standardization to the drainage_proximity component."),
    raster("twi", "Topographic wetness index (FH component weight 0.25)", "3. Terrain and hydrology", "outputs/goslar_pim_chain/hydrology_derivatives/goslar_focus_twi.tif", "input_factor", "wetness", unit="TWI", notes="Raw TWI input; weight applies after percentile standardization to the twi_wetness component."),
    # 4. Erosion factors
    raster("ls_factor", "LS-factor, Moore and Nieber (SE component weight 0.50)", "4. Erosion factors", "outputs/goslar_pim_chain/ls_factor/goslar_focus_ls_factor_capped50_hillslope_30m.tif", "input_factor", "erosion", unit="LS", notes="Raw LS input; weight applies after percentile standardization."),
    raster("soil_k", "Soil erodibility K-factor, SoilGrids 250 m (SE component weight 0.25)", "4. Erosion factors", "outputs/goslar_pim_chain/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif", "input_factor", "erosion", unit="K (US customary)", notes="Raw K input; weight applies after percentile standardization. SoilGrids effective source resolution is 250 m; BGR official K-factor is only a rendered 1:1,000,000 service, not exported."),
    raster("c_factor", "C-factor, ESA WorldCover (SE component weight 0.25)", "4. Erosion factors", "outputs/goslar_esa_worldcover_2021/c_factor/c_factor_goslar_focus_30m.tif", "input_factor", "erosion", unit="C", notes="Raw C input; weight applies after percentile standardization."),
    raster("land_use_pressure", "Land-use pressure, WorldCover LUT (LU component weight 0.40)", "4. Erosion factors", "outputs/goslar_esa_worldcover_2021/c_factor/land_use_pressure_goslar_focus_30m.tif", "input_factor", "land", unit="0-1"),
    # 5. Rainfall
    raster("rainfall", "Rainfall climatology, REGNIE JJA 1991-2020 (FH component weight 0.35)", "5. Rainfall", "outputs/goslar_pim_chain/rainfall_criterion/rainfall_climatology_0_1_PROVISIONAL_30m.tif", "input_factor", "rainfall", unit="0-1", notes="Standardized FH rainfall component. DWD REGNIE 1 km native, provisional 30 m resample; official 1991-2020 climate normal."),
    # 6. Exposure and environmental context
    raster("population", "Population, Zensus 2022 100 m (SV component weight 0.35)", "6. Exposure and environment", "outputs/goslar_pim_chain/exposure_indicators/population_exposure_0_1.tif", "input_factor", "population", unit="0-1", notes="Standardized settlement_population component. Destatis Zensus 2022 official 100 m grid for the WRRL water-body reference, resampled to 30 m."),
    raster(
        "built_infrastructure",
        "Critical infrastructure proximity, OSM facilities (SV component weight 0.30)",
        "6. Exposure and environment",
        "outputs/goslar_pim_chain/exposure_indicators/built_infrastructure_exposure_0_1.tif",
        "input_factor",
        "population",
        unit="0-1",
        claim_level="provisional",
        notes="Active critical_infrastructure component: proximity to filtered OSM schools, hospitals, emergency services, works, substations and stations with 2 km linear decay. Community coverage and operating status are not guaranteed.",
    ),
    raster("clms_vegetation_loss", "CLMS tree-cover decline 2018-2024 (LU component weight 0.35)", "6. Exposure and environment", "outputs/goslar_esa_worldcover_2021/c_factor/clms_tcd_vegetation_loss_2018_2024_goslar_official_basin_30m.tif", "input_factor", "land", unit="0-1", notes="Active bare_soil_vegetation_loss component. Positive percent-point Copernicus HRL Tree Cover Density decline; provisional vegetation-loss proxy."),
    raster("built_agri_road", "Built, agriculture and road pressure (LU component weight 0.25)", "6. Exposure and environment", "outputs/goslar_pim_chain/criteria_stack/criteria/built_agriculture_road_expansion_0_1.tif", "input_factor", "land", unit="0-1", notes="Active built_agriculture_road_expansion component."),
    raster("road_access", "Road access proximity, OSM (SV component weight 0.35)", "6. Exposure and environment", "outputs/goslar_pim_chain/criteria_stack/criteria/road_access_proximity_0_1.tif", "input_factor", "distance", unit="0-1", notes="Active road_access_proximity component with 20 km linear decay."),
    raster("water_wetland", "Water / wetland context (ES component weight 0.65)", "6. Exposure and environment", "outputs/goslar_pim_chain/environmental_sensitivity/water_wetland_context_0_1.tif", "input_factor", "wetness", unit="0-1", notes="Active water_wetland_context component."),
    raster("protected_area", "Protected-area context, EEA Natura 2000 (ES component weight 0.35)", "6. Exposure and environment", "outputs/goslar_pim_chain/environmental_sensitivity/protected_area_context_0_1.tif", "input_factor", "land", unit="0-1", notes="Active protected_ecological_context component. EEA Natura 2000 2024 (FFH + SPA), proximity score; national non-Natura2000 designations are not included."),
    # 7. External validation and overlays
    vector(
        "original_project_focus_extent",
        "Original project map focus extent (minimum study-area anchor)",
        EXTERNAL_OVERLAY_GROUP,
        "outputs/goslar_focus_boundary/goslar_focus_boundary.gpkg",
        "study_area_anchor",
        layer_name="goslar_focus_boundary",
        claim_level="project_layout_reference",
        notes="Minimum study-area anchor: every adopted Goslar study boundary must be contained by the final analysis domain. Project layout reference only; not a catchment, municipal boundary, or observed inundation footprint. Weight 0; excluded from PIM scoring.",
    ),
    vector("boundary", "Official WRRL water-body reference boundary", EXTERNAL_OVERLAY_GROUP, "outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg", "boundary", layer_name="goslar_official_hydrologic_reference_boundary", claim_level="provisional_hydrologic_reference", notes="Hydrologic analysis/reference boundary containing the original project focus extent. Weight 0 as an overlay; it defines the current raster mask but is not a PIM criterion, municipal boundary, or observed inundation footprint."),
    vector("natura2000", "EEA Natura 2000 sites (2024)", EXTERNAL_OVERLAY_GROUP, "data/raw/eea_natura2000_goslar/goslar_natura2000_2024.gpkg", "protected_polygons", layer_name="goslar_natura2000_2024", claim_level="context_evidence"),
    vector("roads", "OSM roads", EXTERNAL_OVERLAY_GROUP, "data/raw/geofabrik_osm_goslar/extracted/gis_osm_roads_free_1.shp", "roads", layer_name="gis_osm_roads_free_1", claim_level="context_evidence"),
    vector("lbeg_mining_rights", "Mining rights context (LBEG/NIBIS)", EXTERNAL_OVERLAY_GROUP, "outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg", "mining_context_overlay", visible=False, layer_name="lbeg_mining_rights", claim_level="context_evidence", notes="Official legal mining-right fields within a 12 km context buffer; not proof of active extraction and excluded from PIM scoring."),
    vector("osm_mining_points", "Mining locations context (OSM)", EXTERNAL_OVERLAY_GROUP, "outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg", "mining_context_overlay", visible=False, layer_name="osm_mining_points", claim_level="context_evidence", notes="Community-mapped mine, adit and mineshaft points within the focus+12 km context; incomplete evidence, excluded from PIM scoring."),
    vector("osm_mining_areas", "Mining areas context (OSM)", EXTERNAL_OVERLAY_GROUP, "outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg", "mining_context_overlay", visible=False, layer_name="osm_mining_areas", claim_level="context_evidence", notes="Community-mapped mine and quarry area geometries within the focus+12 km context; incomplete evidence, excluded from PIM scoring."),
    vector("wfd_drainage_basins", "Official WRRL drainage basins / water bodies", EXTERNAL_OVERLAY_GROUP, "outputs/goslar_official_hydrology_and_flood_data/goslar_wfd_drainage_basins_focus_overlap.gpkg", "hydrologic_context", visible=False, layer_name="goslar_wfd_drainage_basins_focus_overlap", claim_level="context_evidence", notes="Lower Saxony Umweltkarten WRRL polygons overlapping the focus extent. Hydrologic context only; not yet a scored PIM component."),
    vector("hwrm_flood_hazard", "HWRM-RL flood-hazard scenarios (Oker / Innerste)", EXTERNAL_OVERLAY_GROUP, "outputs/goslar_official_hydrology_and_flood_data/goslar_hwrm_flood_hazard_boundaries_12km.gpkg", "flood_hazard_context", visible=False, layer_name="goslar_hwrm_flood_hazard_boundaries_12km", claim_level="context_evidence", notes="Modelled regulatory HQ scenarios within focus+12 km. They are independent validation context, not the observed July 2017 inundation footprint and not PIM inputs."),
    vector(
        "affected_locations_2017",
        "Goslar 2017 flood impacts and emergency response (approximate locations)",
        EXTERNAL_OVERLAY_GROUP,
        "outputs/goslar_2017_affected_location_evidence/goslar_2017_affected_location_evidence.gpkg",
        "historical_event_location_evidence",
        visible=True,
        layer_name="affected_location_evidence",
        claim_level="validation_candidate",
        notes="Nine officially reported affected-place samples positioned with present-day OSM reference coordinates. Location-based historical-event consistency evidence only; not a complete inundation footprint, not a PIM input, and not sufficient for accuracy, recall or IoU.",
    ),
    vector(
        "osm_infrastructure",
        "Critical-infrastructure source points (OSM)",
        EXTERNAL_OVERLAY_GROUP,
        "data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_infrastructure_candidates.gpkg",
        "infrastructure_context",
        visible=False,
        layer_name="osm_infrastructure_candidates",
        claim_level="context_evidence",
        notes="Source evidence for the active critical_infrastructure proximity component. Schools, hospitals, emergency services, works, substations and stations from OSM; community coverage and operating status remain unverified.",
    ),
)

GOSLAR_SITE = {
    "key": "goslar",
    "name": "Goslar official WRRL reference - FullAudit processing chain (provisional)",
    "project_crs": "EPSG:32632",
    "project_file": PROJECT_NAME,
    "scored_criteria": ("flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"),
    "layers": GOSLAR_LAYERS,
}


def qgis_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "QT_QPA_PLATFORM": "offscreen",
            "QGIS_PREFIX_PATH": str(QGIS_PREFIX),
            "PROJ_LIB": str(QGIS_PREFIX / "proj"),
            "GDAL_DATA": str(QGIS_PREFIX / "gdal"),
            "QT_PLUGIN_PATH": str(QGIS_APP / "Contents/PlugIns"),
            "GDAL_PAM_ENABLED": "NO",
            "IFPM_QGIS_RUNTIME": "1",
        }
    )
    return env


def relaunch_with_qgis() -> int:
    if not QGIS_PYTHON.exists():
        raise RuntimeError(f"QGIS Python wrapper not found: {QGIS_PYTHON}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    command = [str(QGIS_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]
    return subprocess.run(command, cwd=OUT_DIR, env=qgis_environment(), check=False).returncode


def _palette(name: str) -> tuple[str, ...]:
    if name == "priority":
        return tuple(PRIORITY_COLORS)
    if name in CRITERIA_COLORS:
        return tuple(CRITERIA_COLORS[name])
    return tuple(INPUT_PALETTES[name])


def _is_normalized(spec: LayerSpec) -> bool:
    return spec.unit == "0-1" or spec.role in {"priority_result", "criterion"}


def _raster_range(layer, spec: LayerSpec) -> tuple[float, float]:
    if _is_normalized(spec):
        return 0.0, 1.0
    from osgeo import gdal

    gdal.UseExceptions()
    dataset = gdal.Open(layer.source().split("|", 1)[0])
    if dataset is None:
        raise RuntimeError(f"GDAL could not open {layer.source()}")
    stats = dataset.GetRasterBand(1).GetStatistics(False, True)
    minimum = float(stats[0])
    maximum = float(stats[1])
    dataset = None
    if not minimum < maximum:
        maximum = minimum + 1.0
    return minimum, maximum


def apply_raster_style(layer, spec: LayerSpec, style_path: Path) -> None:
    from qgis.PyQt.QtGui import QColor
    from qgis.core import QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer

    minimum, maximum = _raster_range(layer, spec)
    colors = _palette(spec.palette)
    # The priority result and all five PIM criteria must reproduce the original
    # Peru/Goslar map contract exactly: discrete equal-interval classes with
    # upper bounds 0.2/0.4/0.6/0.8/1.0.  Using an interpolated ramp here changes
    # both the displayed colours and the visual class boundaries in QGIS.
    if spec.role in {"priority_result", "criterion"}:
        values = STANDARD_CLASS_UPPER_BOUNDS
        labels = STANDARD_CLASS_LABELS
        ramp_type = QgsColorRampShader.Discrete
    else:
        fractions = (0.0, 0.25, 0.5, 0.75, 1.0)
        if spec.key in {"flow_accumulation", "population"} and minimum >= 0:
            low_log = math.log1p(minimum)
            high_log = math.log1p(maximum)
            values = tuple(math.expm1(low_log + fraction * (high_log - low_log)) for fraction in fractions)
        else:
            values = tuple(minimum + fraction * (maximum - minimum) for fraction in fractions)
        labels = tuple(f"{value:.4g}" for value in values)
        ramp_type = QgsColorRampShader.Interpolated

    items = [
        QgsColorRampShader.ColorRampItem(value, QColor(color), label)
        for value, color, label in zip(values, colors, labels)
    ]
    color_shader = QgsColorRampShader(minimum, maximum)
    color_shader.setColorRampType(ramp_type)
    color_shader.setColorRampItemList(items)
    color_shader.setClip(spec.role in {"priority_result", "criterion"})
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(color_shader)
    renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, raster_shader)
    renderer.setClassificationMin(minimum)
    renderer.setClassificationMax(maximum)
    layer.setRenderer(renderer)
    layer.setOpacity(0.92 if spec.role == "priority_result" else 1.0)
    layer.triggerRepaint()
    style_path.parent.mkdir(parents=True, exist_ok=True)
    message, success = layer.saveNamedStyle(str(style_path))
    if not success:
        raise RuntimeError(f"could not save style {style_path}: {message}")


def apply_vector_style(layer, spec: LayerSpec, style_path: Path) -> None:
    from qgis.PyQt.QtGui import QColor, QFont
    from qgis.core import (
        Qgis,
        QgsCategorizedSymbolRenderer,
        QgsFillSymbol,
        QgsMarkerSymbol,
        QgsPalLayerSettings,
        QgsRendererCategory,
        QgsSingleSymbolRenderer,
        QgsTextBufferSettings,
        QgsTextFormat,
        QgsVectorLayerSimpleLabeling,
    )

    if spec.role == "study_area_anchor":
        symbol = QgsFillSymbol.createSimple(
            {
                "color": "255,255,255,0",
                "outline_color": "230,126,34,255",
                "outline_width": "1.2",
                "outline_style": "dash",
            }
        )
    elif spec.role == "boundary":
        symbol = QgsFillSymbol.createSimple(
            {"color": "255,255,255,0", "outline_color": "35,35,35,255", "outline_width": "0.8"}
        )
    elif spec.role == "protected_polygons":
        symbol = QgsFillSymbol.createSimple(
            {"color": "46,204,113,90", "outline_color": "26,118,64,255", "outline_width": "0.7"}
        )
    elif spec.role == "roads":
        symbol = QgsFillSymbol.createSimple(
            {"color": "255,255,255,0", "outline_color": "120,120,120,255", "outline_width": "0.4"}
        )
    elif spec.role == "hydrologic_context":
        symbol = QgsFillSymbol.createSimple(
            {"color": "129,207,224,35", "outline_color": "34,112,141,235", "outline_width": "0.9"}
        )
    elif spec.role == "flood_hazard_context":
        symbol = QgsFillSymbol.createSimple(
            {"color": "187,120,160,45", "outline_color": "120,32,105,235", "outline_width": "0.8"}
        )
    elif spec.role == "infrastructure_context" and layer.geometryType() == 2:
        symbol = QgsMarkerSymbol.createSimple(
            {"name": "square", "color": "214,69,129,225", "outline_color": "255,255,255,255", "size": "2.8"}
        )
    elif spec.role == "mining_context_overlay" and layer.geometryType() == 2:
        symbol = QgsFillSymbol.createSimple(
            {"color": "230,126,34,40", "outline_color": "180,80,15,230", "outline_width": "0.7"}
        )
    elif spec.role == "mining_context_overlay":
        symbol = QgsMarkerSymbol.createSimple(
            {"name": "diamond", "color": "211,84,0,230", "outline_color": "255,255,255,255", "size": "3.0"}
        )
    elif spec.role == "event_huaico":
        symbol = QgsFillSymbol.createSimple(
            {"color": "0,255,255,35", "outline_color": "0,190,190,255", "outline_width": "0.9"}
        )
    elif spec.role == "event_mudflow":
        symbol = QgsFillSymbol.createSimple(
            {"color": "255,234,0,35", "outline_color": "190,150,0,255", "outline_width": "0.9"}
        )
    elif spec.role == "event_footprint":
        symbol = QgsFillSymbol.createSimple(
            {"color": "255,255,255,0", "outline_color": "0,255,255,255", "outline_width": "1.2"}
        )
    elif spec.role == "original_hazard":
        symbol = QgsFillSymbol.createSimple(
            {"color": "118,190,200,75", "outline_color": "70,90,95,220", "outline_width": "0.7"}
        )
    elif spec.role == "historical_event_location_evidence":
        categories = []
        for value, label, color, shape in (
            ("Confirmed affected location", "Confirmed affected locations", "30,136,229,240", "circle"),
            ("Evacuation location", "Evacuation locations", "123,31,162,240", "square"),
            ("Infrastructure damage", "Infrastructure damage locations", "211,47,47,240", "triangle"),
            ("Affected river/street reach reference", "Affected street / river reach references", "0,137,123,240", "diamond"),
        ):
            category_symbol = QgsMarkerSymbol.createSimple(
                {"name": shape, "color": color, "outline_color": "255,255,255,255", "outline_width": "0.6", "size": "4.0"}
            )
            categories.append(QgsRendererCategory(value, category_symbol, label))
        layer.setRenderer(QgsCategorizedSymbolRenderer("evidence_group", categories))
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial"))
        text_format.setColor(QColor(40, 40, 40))
        text_format.setSize(8.5)
        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setColor(QColor(255, 255, 255))
        buffer.setSize(1.0)
        text_format.setBuffer(buffer)
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "location_name"
        label_settings.placement = Qgis.LabelPlacement.AroundPoint
        label_settings.setFormat(text_format)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)
        symbol = None
    else:
        symbol = QgsMarkerSymbol.createSimple(
            {"name": "triangle", "color": "31,120,180,235", "outline_color": "255,255,255,255", "size": "3.2"}
        )
    if symbol is not None:
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    if spec.role == "study_area_anchor":
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial"))
        text_format.setColor(QColor(166, 78, 0))
        text_format.setSize(9.5)
        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setColor(QColor(255, 255, 255))
        buffer.setSize(1.0)
        text_format.setBuffer(buffer)
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "'Original project focus extent'"
        label_settings.isExpression = True
        label_settings.placement = Qgis.LabelPlacement.OverPoint
        label_settings.setFormat(text_format)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)
    layer.triggerRepaint()
    style_path.parent.mkdir(parents=True, exist_ok=True)
    message, success = layer.saveNamedStyle(str(style_path))
    if not success:
        raise RuntimeError(f"could not save style {style_path}: {message}")


def load_layer(spec: LayerSpec):
    from qgis.core import QgsRasterLayer, QgsVectorLayer

    source = ROOT / spec.path
    if not source.exists():
        raise FileNotFoundError(f"missing required Goslar layer: {source}")
    if spec.kind == "raster":
        layer = QgsRasterLayer(str(source), spec.name)
    else:
        uri = str(source)
        if spec.layer_name:
            uri = f"{uri}|layername={spec.layer_name}"
        layer = QgsVectorLayer(uri, spec.name, "ogr")
    if not layer.isValid():
        raise RuntimeError(f"QGIS could not load goslar/{spec.key}: {source}")
    layer.setCustomProperty("ifpm/site", SITE_KEY)
    layer.setCustomProperty("ifpm/role", spec.role)
    layer.setCustomProperty("ifpm/claim_level", spec.claim_level)
    layer.setCustomProperty("ifpm/unit", spec.unit)
    if spec.notes:
        layer.serverProperties().setAbstract(spec.notes)
    return layer


def add_site_to_project(project, site: dict, parent_group, manifest_rows: list[dict[str, str]]):
    groups = {}
    for group_name in list(dict.fromkeys(layer.group for layer in site["layers"])):
        group = parent_group.addGroup(group_name)
        group.setExpanded(group_name.startswith("1."))
        groups[group_name] = group

    priority_extent = None
    for spec in site["layers"]:
        layer = load_layer(spec)
        project.addMapLayer(layer, False)
        node = groups[spec.group].addLayer(layer)
        node.setItemVisibilityChecked(spec.visible)
        style_path = STYLE_DIR / f"{SITE_KEY}_{spec.key}.qml"
        if spec.kind == "raster":
            apply_raster_style(layer, spec, style_path)
        else:
            apply_vector_style(layer, spec, style_path)
        if spec.role == "priority_result":
            priority_extent = layer.extent()

        manifest_rows.append(
            {
                "site": SITE_KEY,
                "layer_key": spec.key,
                "display_name": spec.name,
                "group": spec.group,
                "role": spec.role,
                "source_path": spec.path,
                "source_type": spec.kind,
                "provider_crs": layer.crs().authid(),
                "unit": spec.unit,
                "visible_by_default": str(spec.visible).lower(),
                "claim_level": spec.claim_level,
                "style_path": str(style_path.relative_to(OUT_DIR)),
                "load_status": "valid",
                "notes": spec.notes,
            }
        )
    return priority_extent


def configure_project(project, title: str, crs_authid: str, output_path: Path) -> None:
    from qgis.core import Qgis, QgsCoordinateReferenceSystem

    project.clear()
    project.setTitle(title)
    project.setFileName(str(output_path))
    project.setFilePathStorage(Qgis.FilePathType.Relative)
    project.setCrs(QgsCoordinateReferenceSystem(crs_authid))
    project.setCustomVariables(
        {
            "ifpm_status": "prototype map; not a validated flood-risk result",
            "ifpm_weighting": "current five-criterion weights; no pairwise matrix or consistency ratio supplied",
            "ifpm_workspace": "IFPM",
        }
    )
    project.writeEntry("Paths", "Absolute", False)
    project.writeEntry("Gui", "CanvasColorRedPart", 248)
    project.writeEntry("Gui", "CanvasColorGreenPart", 248)
    project.writeEntry("Gui", "CanvasColorBluePart", 248)


def set_default_extent(project, extent, crs_authid: str) -> None:
    from qgis.core import QgsCoordinateReferenceSystem, QgsReferencedRectangle

    if extent is None or extent.isNull():
        raise RuntimeError("priority layer has no valid extent")
    referenced = QgsReferencedRectangle(extent, QgsCoordinateReferenceSystem(crs_authid))
    project.viewSettings().setPresetFullExtent(referenced)
    project.viewSettings().setDefaultViewExtent(referenced)


def set_render_order(project) -> None:
    role_priority = {
        "study_area_anchor": 0,
        "boundary": 1,
        "event_huaico": 2,
        "event_mudflow": 2,
        "event_footprint": 2,
        "evidence_points": 2,
        "original_hazard": 2,
        "mining_context_overlay": 2,
        "roads": 3,
        "protected_polygons": 4,
        "priority_result": 5,
        "input_factor": 6,
        "criterion": 7,
    }
    layers = list(project.mapLayers().values())
    layers.sort(
        key=lambda layer: (
            role_priority.get(layer.customProperty("ifpm/role"), 99),
            layer.name(),
            layer.source(),
        )
    )
    root = project.layerTreeRoot()
    root.setHasCustomLayerOrder(True)
    root.setCustomLayerOrder(layers)


def write_project(project, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not project.write(str(output_path)):
        raise RuntimeError(f"QGIS failed to write {output_path}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_qml_ramp(path: Path) -> dict[str, object]:
    root = ElementTree.fromstring(path.read_bytes())
    shader = root.find(".//colorrampshader")
    if shader is None:
        raise RuntimeError(f"missing color ramp shader in {path}")
    items = shader.findall("item")
    return {
        "type": shader.attrib.get("colorRampType", ""),
        "clip": shader.attrib.get("clip", ""),
        "values": tuple(float(item.attrib["value"]) for item in items),
        "labels": tuple(item.attrib.get("label", "") for item in items),
        "colors": tuple(item.attrib["color"].lower() for item in items),
    }


def _rewrite_project_for_portable_export(source_project: Path, target_project: Path, rows: list[dict[str, str]]) -> None:
    replacements: dict[str, str] = {}
    vector_sources: set[str] = set()
    for row in rows:
        source = ROOT / row["source_path"]
        old = os.path.relpath(source, OUT_DIR).replace(os.sep, "/")
        portable_name = (
            f"{SITE_KEY}_{row['layer_key']}.gpkg"
            if row["source_type"] == "vector"
            else f"{SITE_KEY}_{row['layer_key']}{Path(row['source_path']).suffix.lower()}"
        )
        new = f"layers/{SITE_KEY}/{row['layer_key']}/{portable_name}"
        layer_name = next(
            spec.layer_name
            for spec in GOSLAR_SITE["layers"]
            if spec.key == row["layer_key"]
        )
        if layer_name:
            old = f"{old}|layername={layer_name}"
            new = f"{new}|layername={SITE_KEY}_{row['layer_key']}"
            vector_sources.add(old)
        replacements[old] = new

    with zipfile.ZipFile(source_project) as source_archive:
        qgs_names = [name for name in source_archive.namelist() if name.endswith(".qgs")]
        if len(qgs_names) != 1:
            raise RuntimeError(f"{source_project} must contain exactly one QGS document")
        qgs_name = qgs_names[0]
        root = ElementTree.fromstring(source_archive.read(qgs_name))
        root.attrib.pop("saveUser", None)
        root.attrib.pop("saveUserFull", None)
        root.attrib.pop("saveDateTime", None)

        layer_ids: dict[str, str] = {}
        for index, map_layer in enumerate(root.findall(".//maplayer")):
            old_id = map_layer.findtext("id")
            layer_name = map_layer.findtext("layername") or f"layer_{index}"
            data_source = map_layer.findtext("datasource") or ""
            if old_id:
                stable_uuid = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"ifpm:{source_project.name}:{data_source}:{layer_name}",
                ).hex[:16]
                layer_ids[old_id] = f"{re.sub(r'[^a-z0-9]+', '_', layer_name.lower()).strip('_')}_{stable_uuid}"
            if data_source in vector_sources:
                for parent in map_layer.iter():
                    for child in list(parent):
                        if child.tag in {
                            "aliases", "attributetableconfig", "conditionalstyles",
                            "constraintExpressions", "constraints", "defaults",
                            "duplicatePolicies", "editable", "expressionfields",
                            "fieldConfiguration", "labelOnTop", "reuseLastValue",
                            "splitPolicies", "storedexpressions",
                        }:
                            parent.remove(child)

        replacement_count = 0
        for element in root.iter():
            source_attr = element.attrib.get("source")
            if source_attr in replacements:
                element.set("source", replacements[source_attr])
                replacement_count += 1
            if element.tag == "datasource" and element.text in replacements:
                element.text = replacements[element.text]
                replacement_count += 1
            if element.tag in {"author", "creation"}:
                element.text = ""
        for dates in root.findall(".//dates"):
            dates.clear()
        for parent in root.iter():
            for child in list(parent):
                if child.tag in {"elevation", "main-annotation-layer"}:
                    parent.remove(child)
        for settings in root.findall(".//individual-layer-settings"):
            settings[:] = sorted(settings, key=lambda child: child.attrib.get("id", ""))
        for project_layers in root.findall(".//projectlayers"):
            project_layers[:] = sorted(
                project_layers,
                key=lambda child: (child.findtext("datasource") or "", child.findtext("layername") or ""),
            )
        for settings in root.findall(".//ProjectStyleSettings"):
            settings.set("projectStyleId", "")
            settings.set("iccProfileId", "")
        for element in root.iter():
            if element.text in layer_ids:
                element.text = layer_ids[element.text]
            for key, value in list(element.attrib.items()):
                if value in layer_ids:
                    element.set(key, layer_ids[value])

        if replacement_count == 0:
            raise RuntimeError(f"no data sources were rewritten in {source_project.name}")
        xml_text = ElementTree.tostring(root, encoding="unicode")
        uuid_counter = 0

        def replace_uuid(match: re.Match[str]) -> str:
            nonlocal uuid_counter
            stable = uuid.uuid5(uuid.NAMESPACE_URL, f"ifpm:{source_project.name}:symbol:{uuid_counter}")
            uuid_counter += 1
            return "{" + str(stable) + "}"

        xml_text = re.sub(r"\{[0-9a-fA-F-]{36}\}", replace_uuid, xml_text)
        xml_bytes = (
            "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
            + ElementTree.canonicalize(xml_data=xml_text, strip_text=True)
        ).encode("utf-8")

        zip_info = zipfile.ZipInfo(qgs_name, date_time=(1980, 1, 1, 0, 0, 0))
        zip_info.compress_type = zipfile.ZIP_DEFLATED
        zip_info.external_attr = 0o644 << 16
        with zipfile.ZipFile(target_project, "w") as target_archive:
            target_archive.writestr(zip_info, xml_bytes)


def _normalize_portable_qml(path: Path) -> None:
    root = ElementTree.fromstring(path.read_bytes())
    for parent in root.iter():
        for child in list(parent):
            if child.tag in {
                "aliases", "attributetableconfig", "conditionalstyles",
                "constraintExpressions", "constraints", "defaults",
                "duplicatePolicies", "editable", "elevation", "expressionfields",
                "fieldConfiguration", "labelOnTop", "reuseLastValue",
                "splitPolicies", "storedexpressions",
            }:
                parent.remove(child)
    text = ElementTree.tostring(root, encoding="unicode")
    counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        stable = uuid.uuid5(uuid.NAMESPACE_URL, f"ifpm:{path.name}:{counter}")
        counter += 1
        return f'id="{{{stable}}}"'

    normalized = re.sub(r'id="\{[0-9a-fA-F-]{36}\}"', replace, text)
    canonical = ElementTree.canonicalize(xml_data=normalized, strip_text=True)
    path.write_text(
        "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n" + canonical,
        encoding="utf-8",
    )


def portable_readme_text() -> str:
    return """IFPM Goslar FullAudit QGIS package

Open IFPM_Goslar_FullAudit.qgz directly in QGIS 3.44 or later. All referenced GeoTIFF and
GeoPackage layers are included under layers/ and use package-local relative
paths. The project shows the full Peru-style PIM chain for the Goslar focus
area: Copernicus DEM -> slope -> hydrology -> LS/K/C erosion factors -> REGNIE
rainfall -> EEA Natura 2000 protected areas -> criteria stack -> exposure and
environment -> priority scenarios. Intermediate products are included.

The visible "Goslar 2017 flood impacts and emergency response (approximate locations)" layer contains nine
officially reported affected-place samples positioned with present-day OSM
reference coordinates. It is a location-based consistency check only, has
weight 0, and is not a complete observed inundation footprint or an accuracy
validation dataset.

The orange dashed polygon labelled "Original project focus extent" is the
minimum study-area anchor taken from the original ZLW QGIS print layout. It is
included, visible by default, and has weight 0. It is not a catchment,
municipal boundary, or observed inundation footprint. Any future Goslar study
boundary must fully contain this anchor.

Three mining context layers are included and switched off by default: official
LBEG legal mining-right fields plus OSM mining points and area geometries. They
are context evidence only and are excluded from the five-criterion PIM score.

Priority layers show relative priority values based on the current
five-criterion weights. They are prototype maps, not validated flood-depth,
inundation, or emergency-response maps. Transparent cells represent NoData.
This is a private research handoff; verify source licences before
redistribution outside the project team.
"""


def build_portable_export(rows: list[dict[str, str]]) -> Path:
    temp_dir = PORTABLE_DIR.parent / f".{PORTABLE_DIR.name}.tmp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    for row in rows:
        source = ROOT / row["source_path"]
        target_dir = temp_dir / "layers" / SITE_KEY / row["layer_key"]
        target_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(row["source_path"]).suffix.lower()
        if row["source_type"] == "vector":
            # Vectors are re-exported as a single-layer GPKG so the layer name
            # matches the project reference (goslar_<key>) and no shapefile
            # sidecar files (.shx/.dbf/...) are needed in the portable bundle.
            target = target_dir / f"{SITE_KEY}_{row['layer_key']}.gpkg"
            from osgeo import gdal

            layer_name = next(
                spec.layer_name
                for spec in GOSLAR_SITE["layers"]
                if spec.key == row["layer_key"]
            )
            source_dataset = gdal.OpenEx(str(source), gdal.OF_VECTOR)
            if source_dataset is None:
                raise RuntimeError(f"GDAL could not open vector source {source}")
            options = gdal.VectorTranslateOptions(
                format="GPKG",
                layers=[layer_name],
                layerName=f"{SITE_KEY}_{row['layer_key']}",
            )
            result = gdal.VectorTranslate(str(target), source_dataset, options=options)
            source_dataset = None
            if result is None:
                raise RuntimeError(f"could not export portable vector layer {row['layer_key']}")
            result = None
            with sqlite3.connect(target) as connection:
                connection.execute(
                    "UPDATE gpkg_contents SET last_change = ?",
                    ("1980-01-01T00:00:00.000Z",),
                )
                connection.commit()
                connection.execute("VACUUM")
        else:
            target = target_dir / f"{SITE_KEY}_{row['layer_key']}{suffix}"
            shutil.copy2(source, target)
        row["portable_source_path"] = str((Path("layers") / SITE_KEY / row["layer_key"] / target.name).as_posix())
        row["source_size_bytes"] = str(source.stat().st_size)
        row["source_sha256"] = _sha256(source)
        row["portable_size_bytes"] = str(target.stat().st_size)
        row["portable_sha256"] = _sha256(target)

    shutil.copytree(STYLE_DIR, temp_dir / "styles")
    for style_path in (temp_dir / "styles").glob("*.qml"):
        _normalize_portable_qml(style_path)

    _rewrite_project_for_portable_export(OUT_DIR / PROJECT_NAME, temp_dir / PROJECT_NAME, rows)

    fields = [
        "site", "layer_key", "display_name", "group", "role", "source_type",
        "provider_crs", "unit", "visible_by_default", "claim_level",
        "portable_source_path", "portable_size_bytes", "portable_sha256",
        "load_status", "notes",
    ]
    with (temp_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(({field: row[field] for field in fields} for row in rows))
    (temp_dir / "README.txt").write_text(portable_readme_text(), encoding="utf-8")
    if PORTABLE_DIR.exists():
        shutil.rmtree(PORTABLE_DIR)
    temp_dir.replace(PORTABLE_DIR)
    return PORTABLE_DIR / PROJECT_NAME


def build_portable_zip(package_dir: Path, archive_path: Path) -> Path:
    """Create a deterministic, metadata-free ZIP of a portable package."""
    temp_archive = archive_path.with_name(f".{archive_path.name}.tmp")
    if temp_archive.exists():
        temp_archive.unlink()
    with zipfile.ZipFile(temp_archive, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(path for path in package_dir.rglob("*") if path.is_file()):
            relative = source.relative_to(package_dir)
            if any(part.startswith(".") for part in relative.parts):
                continue
            archive_name = (Path(package_dir.name) / relative).as_posix()
            info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    temp_archive.replace(archive_path)
    return archive_path


def refresh_managed_package_index() -> None:
    from manage_qgis_package_paths import refresh_index

    refresh_index(ROOT / "exports/qgis_packages")


def build_projects() -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    from qgis.core import QgsApplication, QgsProject

    QgsApplication.setPrefixPath(str(QGIS_PREFIX), True)
    app = QgsApplication([], False)
    app.initQgis()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STYLE_DIR.mkdir(parents=True, exist_ok=True)
    expected_style_names = {f"{SITE_KEY}_{spec.key}.qml" for spec in GOSLAR_LAYERS}
    for stale_style in STYLE_DIR.glob(f"{SITE_KEY}_*.qml"):
        if stale_style.name not in expected_style_names:
            stale_style.unlink()
    manifest_rows: list[dict[str, str]] = []
    project = QgsProject.instance()
    project_paths: list[Path] = []
    qgis_readback: list[dict[str, object]] = []
    try:
        output_path = OUT_DIR / GOSLAR_SITE["project_file"]
        configure_project(project, f"IFPM - {GOSLAR_SITE['name']}", GOSLAR_SITE["project_crs"], output_path)
        site_group = project.layerTreeRoot().addGroup(GOSLAR_SITE["name"])
        extent = add_site_to_project(project, GOSLAR_SITE, site_group, manifest_rows)
        set_default_extent(project, extent, GOSLAR_SITE["project_crs"])
        set_render_order(project)
        write_project(project, output_path)
        project_paths.append(output_path)

        portable_path = build_portable_export(manifest_rows)
        project_paths.append(portable_path)

        for path in project_paths:
            project.clear()
            read_success = bool(project.read(str(path)))
            invalid_layers = [layer.name() for layer in project.mapLayers().values() if not layer.isValid()]
            expected = len(GOSLAR_LAYERS)
            layer_count = len(project.mapLayers())
            view_extent = project.viewSettings().defaultViewExtent()
            if not read_success or invalid_layers or layer_count != expected:
                raise RuntimeError(
                    f"QGIS read-back failed for {path.name}: read={read_success}, "
                    f"invalid={invalid_layers}, layers={layer_count}, expected={expected}"
                )
            qgis_readback.append(
                {
                    "project": path.name,
                    "package_type": "portable" if PORTABLE_DIR in path.parents else "workspace_linked",
                    "read_success": read_success,
                    "layer_count": layer_count,
                    "expected_layer_count": expected,
                    "invalid_layers": invalid_layers,
                    "project_crs": project.crs().authid(),
                    "default_extent": [
                        view_extent.xMinimum(),
                        view_extent.yMinimum(),
                        view_extent.xMaximum(),
                        view_extent.yMaximum(),
                    ],
                }
            )
    finally:
        project.clear()
        app.exitQgis()
    return manifest_rows, qgis_readback


def write_manifest(rows: list[dict[str, str]]) -> None:
    fields = [
        "site", "layer_key", "display_name", "group", "role",
        "source_path", "source_type", "provider_crs", "unit", "visible_by_default",
        "claim_level", "style_path", "portable_source_path", "source_size_bytes",
        "source_sha256", "portable_size_bytes", "portable_sha256", "load_status", "notes",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_readme() -> None:
    README.write_text(
        """IFPM Goslar QGIS project package

Recommended entry point: IFPM_Goslar_FullAudit.qgz - Goslar FullAudit processing chain in EPSG:32632.
The project uses relative paths to the existing workspace data under data/ and
outputs/. Keep this package inside outputs/goslar_qgis_full_audit/ when
opening it. The package does not duplicate large raster files.

Groups follow the processing chain: priority result, five PIM criteria,
terrain and hydrology (including intermediate products), erosion factors,
rainfall, exposure and environment, and context and evidence. PIM layers are
visible by default; criteria and factor layers are available in collapsed
groups. The maps are prototype relative-priority outputs, not validated
flood-depth, inundation, or emergency-response maps.
""",
        encoding="utf-8",
    )


def validate_package(qgis_readback: list[dict[str, object]] | None = None) -> dict[str, object]:
    project_path = OUT_DIR / PROJECT_NAME
    if not project_path.exists():
        raise FileNotFoundError(project_path)
    with zipfile.ZipFile(project_path) as archive:
        qgs_names = [name for name in archive.namelist() if name.endswith(".qgs")]
        if len(qgs_names) != 1:
            raise RuntimeError(f"{project_path.name} contains {len(qgs_names)} QGS documents")
        xml_bytes = archive.read(qgs_names[0])
    ElementTree.fromstring(xml_bytes)
    text = xml_bytes.decode("utf-8")
    absolute_path_free = str(ROOT) not in text and "/Users/jlw/" not in text
    if not absolute_path_free:
        raise RuntimeError(f"absolute workspace path found in {project_path.name}")
    checks = [
        {
            "project": project_path.name,
            "qgs_document": qgs_names[0],
            "xml_valid": True,
            "absolute_path_free": True,
            "size_bytes": project_path.stat().st_size,
        }
    ]

    portable_checks: list[dict[str, object]] = []
    portable_project = PORTABLE_DIR / PROJECT_NAME
    if not portable_project.exists():
        raise FileNotFoundError(portable_project)
    with zipfile.ZipFile(portable_project) as archive:
        qgs_names = [name for name in archive.namelist() if name.endswith(".qgs")]
        if len(qgs_names) != 1:
            raise RuntimeError(f"{portable_project.name} contains {len(qgs_names)} QGS documents")
        xml_bytes = archive.read(qgs_names[0])
    root = ElementTree.fromstring(xml_bytes)
    sources = [
        element.attrib["source"]
        for element in root.iter()
        if "source" in element.attrib and not element.attrib["source"].startswith("attachment://")
    ]
    sources.extend(element.text or "" for element in root.iter("datasource") if element.text)
    external_sources = [source for source in sources if source.startswith(("/", "../", "file://")) or ":\\" in source]
    if external_sources:
        raise RuntimeError(f"external data sources found in portable {portable_project.name}: {external_sources}")
    portable_checks.append(
        {
            "project": portable_project.name,
            "qgs_document": qgs_names[0],
            "package_local_sources": True,
            "source_reference_count": len(sources),
            "size_bytes": portable_project.stat().st_size,
        }
    )

    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    missing_sources = [row["source_path"] for row in rows if not (ROOT / row["source_path"]).exists()]
    missing_styles = [row["style_path"] for row in rows if not (OUT_DIR / row["style_path"]).exists()]
    missing_portable_sources = [
        row["portable_source_path"]
        for row in rows
        if not (PORTABLE_DIR / row["portable_source_path"]).exists()
    ]
    checksum_errors: list[str] = []
    for row in rows:
        source = ROOT / row["source_path"]
        portable = PORTABLE_DIR / row["portable_source_path"]
        if _sha256(source) != row["source_sha256"]:
            checksum_errors.append(f"source checksum changed: {row['site']}/{row['layer_key']}")
        if _sha256(portable) != row["portable_sha256"]:
            checksum_errors.append(f"portable checksum mismatch: {row['site']}/{row['layer_key']}")
    expected_portable_files = {
        PROJECT_NAME, "README.txt", "manifest.csv", "validation.json",
        *(row["portable_source_path"] for row in rows),
        *(f"styles/{Path(row['style_path']).name}" for row in rows),
    }
    actual_portable_files = {
        str(path.relative_to(PORTABLE_DIR).as_posix())
        for path in PORTABLE_DIR.rglob("*")
        if path.is_file()
    }
    unexpected_portable_files = sorted(actual_portable_files - expected_portable_files)
    if checksum_errors or unexpected_portable_files:
        raise RuntimeError(
            f"checksum errors={checksum_errors}; unexpected portable files={unexpected_portable_files}"
        )
    if missing_sources or missing_styles or missing_portable_sources:
        raise RuntimeError(
            f"missing sources={missing_sources}; missing styles={missing_styles}; "
            f"missing portable sources={missing_portable_sources}"
        )

    semantic_errors: list[str] = []
    roles = [row["role"] for row in rows]
    if roles.count("priority_result") != 1:
        semantic_errors.append("expected exactly one priority_result layer")
    if roles.count("criterion") != 5:
        semantic_errors.append("expected exactly five criterion layers")
    units = {row["layer_key"]: row["unit"] for row in rows}
    if units.get("distance_drainage") != "m":
        semantic_errors.append("drainage-distance unit is not metres")
    if units.get("twi") != "TWI":
        semantic_errors.append("TWI unit is not TWI")

    expected_discrete_palettes = {
        "priority": tuple(PRIORITY_COLORS),
        **{key: tuple(colors) for key, colors in CRITERIA_COLORS.items()},
    }
    for layer_key, expected_colors in expected_discrete_palettes.items():
        for package_name, style_root in (
            ("workspace", STYLE_DIR),
            ("portable", PORTABLE_DIR / "styles"),
        ):
            ramp = _read_qml_ramp(style_root / f"{SITE_KEY}_{layer_key}.qml")
            if ramp["type"] != "DISCRETE":
                semantic_errors.append(f"{package_name}/{layer_key} color ramp is not discrete")
            if ramp["clip"] != "1":
                semantic_errors.append(f"{package_name}/{layer_key} color ramp is not clipped")
            if ramp["values"] != STANDARD_CLASS_UPPER_BOUNDS:
                semantic_errors.append(
                    f"{package_name}/{layer_key} thresholds differ from 0.2 equal intervals"
                )
            if ramp["labels"] != STANDARD_CLASS_LABELS:
                semantic_errors.append(f"{package_name}/{layer_key} class labels differ")
            if ramp["colors"] != expected_colors:
                semantic_errors.append(f"{package_name}/{layer_key} color codes differ")
    if semantic_errors:
        raise RuntimeError(f"semantic validation failed: {semantic_errors}")

    from osgeo import gdal
    from qgis.core import Qgis, QgsProjUtils

    result = {
        "qgis_version": Qgis.QGIS_VERSION,
        "gdal_version": gdal.VersionInfo("RELEASE_NAME"),
        "proj_version": f"{QgsProjUtils.projVersionMajor()}.{QgsProjUtils.projVersionMinor()}",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "projects": checks,
        "portable_projects": portable_checks,
        "manifest_layer_count": len(rows),
        "style_count": len(list(STYLE_DIR.glob("*.qml"))),
        "qgis_readback": qgis_readback or [],
        "missing_sources": missing_sources,
        "missing_styles": missing_styles,
        "missing_portable_sources": missing_portable_sources,
        "checksum_errors": checksum_errors,
        "unexpected_portable_files": unexpected_portable_files,
        "semantic_errors": semantic_errors,
        "status": "package_integrity_valid",
    }
    validation_text = json.dumps(result, indent=2) + "\n"
    VALIDATION.write_text(validation_text, encoding="utf-8")
    (PORTABLE_DIR / "validation.json").write_text(validation_text, encoding="utf-8")
    return result


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    if os.environ.get("IFPM_QGIS_RUNTIME") != "1":
        return relaunch_with_qgis()
    rows, qgis_readback = build_projects()
    write_manifest(rows)
    write_readme()
    result = validate_package(qgis_readback)
    build_portable_zip(PORTABLE_DIR, PORTABLE_DIR.with_suffix(".zip"))
    refresh_managed_package_index()
    print(
        f"wrote Goslar QGIS project with {result['manifest_layer_count']} governed layers to "
        f"{OUT_DIR.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
