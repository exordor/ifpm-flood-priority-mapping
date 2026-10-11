#!/usr/bin/env python3
"""Build QGIS projects for the governed Peru and Zimbabwe IFPM layers.

The module can be imported with the workspace Python for configuration tests. When
executed without PyQGIS it relaunches itself with the QGIS application Python.
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
OUT_DIR = ROOT / "outputs/qgis_project_package"
STYLE_DIR = OUT_DIR / "styles"
MANIFEST = OUT_DIR / "manifest.csv"
VALIDATION = OUT_DIR / "validation.json"
README = OUT_DIR / "README.txt"
PORTABLE_DIR = (
    ROOT
    / "exports/qgis_packages/_archive/legacy_peru_zimbabwe_combined/IFPM_QGIS_Project_Package"
)

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

PRIORITY_PALETTE = (
    "#1A9850",
    "#91CF60",
    "#FEE08B",
    "#FC8D59",
    "#D73027",
)
CRITERION_PALETTES = {
    "flood_hazard": ("#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B"),
    "sediment": ("#FFFFD4", "#FED98E", "#FE9929", "#D95F0E", "#993404"),
    "landuse_asm": ("#FFFFCC", "#FED976", "#FD8D3C", "#E31A1C", "#800026"),
    "environmental": ("#F7FCF5", "#C7E9C0", "#74C476", "#238B45", "#00441B"),
    "socioeconomic": ("#FCFBFD", "#DADAEB", "#9E9AC8", "#6A51A3", "#3F007D"),
}
INPUT_PALETTES = {
    "rainfall": ("#FFF7EC", "#FDD49E", "#FC8D59", "#D7301F", "#7F0000"),
    "terrain": ("#F7FCB9", "#ADDD8E", "#41AB5D", "#238443", "#005A32"),
    "wetness": ("#F7FBFF", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B"),
    "distance": ("#084081", "#2B8CBE", "#7BCCC4", "#CCECE6", "#F7FCFD"),
    "erosion": ("#FFFFD4", "#FED98E", "#FE9929", "#D95F0E", "#993404"),
    "land": ("#F7FCF5", "#C7E9C0", "#74C476", "#238B45", "#00441B"),
    "population": ("#FFF7F3", "#FCC5C0", "#FA9FB5", "#C51B8A", "#7A0177"),
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
    claim_level: str = "provisional"
    notes: str = ""


@dataclass(frozen=True)
class SiteSpec:
    key: str
    name: str
    project_crs: str
    project_file: str
    layers: tuple[LayerSpec, ...]


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
    claim_level: str = "provisional",
    notes: str = "",
) -> LayerSpec:
    return LayerSpec(
        key, name, group, path, "raster", role, palette, visible, "", unit, claim_level, notes
    )


def vector(
    key: str,
    name: str,
    group: str,
    path: str,
    role: str,
    *,
    visible: bool = True,
    layer_name: str = "",
    claim_level: str = "provisional",
    notes: str = "",
) -> LayerSpec:
    return LayerSpec(
        key, name, group, path, "vector", role, "", visible, layer_name, "", claim_level, notes
    )


PERU_LAYERS = (
    raster(
        "priority",
        "Relative flood-priority index",
        "1. Priority result",
        "outputs/peru_former_pim_chain/priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
        "priority_result",
        "priority",
        visible=True,
        unit="0-1",
        claim_level="sensitivity_scenario",
        notes="Current no-mining test baseline retains the original five top-level weights; only Land Use was rebuilt as LC/BV/BE. No pairwise matrix or consistency ratio was supplied. NoData is transparent.",
    ),
    raster("flood_hazard", "Flood conditioning", "2. Five PIM criteria", "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/flood_hazard_0_1.tif", "criterion", "flood_hazard", unit="0-1"),
    raster("sediment", "Sediment / erosion factors", "2. Five PIM criteria", "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/sediment_0_1.tif", "criterion", "sediment", unit="0-1"),
    raster("landuse_asm", "General land-use pressure", "2. Five PIM criteria", "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/landuse_asm_0_1.tif", "criterion", "landuse_asm", unit="0-1", notes="0.40 LC + 0.35 BV + 0.25 BE; single-date BV/BE are test proxies. Dedicated mining evidence is excluded from scoring."),
    raster("environmental", "Environmental sensitivity", "2. Five PIM criteria", "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/environmental_0_1.tif", "criterion", "environmental", unit="0-1", notes="0.60 water/wetland context + 0.40 protected/ecological context. No protected-area geometry occurs in the current context zone."),
    raster("socioeconomic", "Socioeconomic exposure", "2. Five PIM criteria", "outputs/peru_former_pim_chain/priority_scenarios/pim_criteria/socioeconomic_0_1.tif", "criterion", "socioeconomic", unit="0-1", notes="Unchanged 0.45 road/access + 0.55 infrastructure exposure; infrastructure remains 0.50 WorldPop + 0.50 OSM mapped buildings."),
    raster("rainfall", "Rainfall climatology (Dec-Mar)", "3. Input and derived factors", "outputs/peru_former_pim_chain/rainfall_criterion/rainfall_climatology_raw_mm_per_season_PROVISIONAL_30m.tif", "input_factor", "rainfall", unit="mm per rainy season", notes="CHIRPS effective resolution is about 5 km; displayed on the 30 m reference grid."),
    raster("elevation", "Elevation", "3. Input and derived factors", "outputs/peru_former_pim_chain/terrain_preprocessing/peru_former_dem_utm18s_30m.tif", "input_factor", "terrain", unit="m"),
    raster("slope", "Slope", "3. Input and derived factors", "outputs/peru_former_pim_chain/terrain_preprocessing/peru_former_slope_degrees_utm18s_30m.tif", "input_factor", "terrain", unit="degrees"),
    raster("twi", "Topographic wetness index", "3. Input and derived factors", "outputs/peru_former_pim_chain/hydrology_derivatives/peru_former_twi.tif", "input_factor", "wetness", unit="TWI"),
    raster("distance_drainage", "Distance to derived drainage", "3. Input and derived factors", "outputs/peru_former_pim_chain/hydrology_derivatives/peru_former_distance_to_drainage_t500.tif", "input_factor", "distance", unit="m"),
    raster("upstream_area", "Flow accumulation (contributing cells)", "3. Input and derived factors", "outputs/peru_former_pim_chain/hydrology_derivatives/peru_former_flow_accumulation.tif", "input_factor", "wetness", unit="cells"),
    raster("soil_k", "Soil erodibility K-factor", "3. Input and derived factors", "outputs/peru_former_pim_chain/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif", "input_factor", "erosion", unit="K (US customary)", notes="SoilGrids effective source resolution is 250 m."),
    raster("ls_factor", "LS-factor", "3. Input and derived factors", "outputs/peru_former_pim_chain/ls_factor/peru_former_ls_factor_capped50_hillslope_30m.tif", "input_factor", "erosion", unit="LS"),
    raster("c_factor", "C-factor", "3. Input and derived factors", "outputs/peru_former_esa_worldcover_2021/c_factor/c_factor_peru_former_30m.tif", "input_factor", "erosion", unit="C"),
    raster("land_cover_pressure", "Land-cover pressure", "3. Input and derived factors", "outputs/peru_former_esa_worldcover_2021/c_factor/land_use_pressure_peru_former_30m.tif", "input_factor", "land", unit="0-1"),
    raster("road_access", "Road access proximity", "3. Input and derived factors", "outputs/peru_former_pim_chain/criteria_stack/criteria/road_access_proximity_0_1.tif", "input_factor", "distance", unit="0-1"),
    raster("water_wetland", "Water / wetland context", "3. Input and derived factors", "outputs/peru_former_pim_chain/environmental_sensitivity/water_wetland_context_0_1.tif", "input_factor", "wetness", unit="0-1"),
    raster("population", "Population distribution (WorldPop 2020)", "4. Context and evidence", "data/raw/worldpop_peru_population/per_ppp_2020_UNadj_peru_former_bbox.tif", "context_raster", "population", unit="people per cell", claim_level="context_evidence"),
    vector("mining", "Small-mining reference records (INGEMMET)", "4. Context and evidence", "data/raw/ingemmet_catastro_minero_peru_former/peru_former_pequena_mineria.gpkg", "mining_points", layer_name="pequena_mineria", claim_level="context_evidence"),
    vector("sinpad", "SINPAD event records", "4. Context and evidence", "outputs/peru_former_gap_closure_analysis/peru_former_sinpad_pim_colocation.gpkg", "validation_points", layer_name="sinpad_pim_colocation", claim_level="validation_candidate"),
    vector("boundary", "Vitor-La Joya-Siguas catchment boundary", "4. Context and evidence", "outputs/peru_former_boundary/peru_former_boundary.gpkg", "boundary", layer_name="peru_pilot_boundary", claim_level="working_boundary"),
)

ZIMBABWE_LAYERS = (
    raster(
        "priority",
        "Relative flood-priority index",
        "1. Priority result",
        "outputs/zimbabwe_pim_scenarios/rainfall_exposure/scenarios/priority_mentor_zimbabwe_direct_pim.tif",
        "priority_result",
        "priority",
        visible=True,
        unit="0-1",
        claim_level="sensitivity_scenario",
        notes="Current five-criterion weights documented in July 2026; no pairwise matrix or consistency ratio was supplied. NoData is transparent. Not a validated flood-depth or rescue map.",
    ),
    raster("flood_hazard", "Flood conditioning", "2. Five PIM criteria", "outputs/zimbabwe_pim_scenarios/rainfall_exposure/pim_criteria/flood_hazard_0_1.tif", "criterion", "flood_hazard", unit="0-1"),
    raster("sediment", "Sediment / erosion factors", "2. Five PIM criteria", "outputs/zimbabwe_pim_scenarios/rainfall_exposure/pim_criteria/sediment_0_1.tif", "criterion", "sediment", unit="0-1"),
    raster("landuse_asm", "Land use / mining pressure", "2. Five PIM criteria", "outputs/zimbabwe_pim_scenarios/rainfall_exposure/pim_criteria/landuse_asm_0_1.tif", "criterion", "landuse_asm", unit="0-1"),
    raster("environmental", "Environmental context indicators", "2. Five PIM criteria", "outputs/zimbabwe_pim_scenarios/rainfall_exposure/pim_criteria/environmental_0_1.tif", "criterion", "environmental", unit="0-1", notes="Combined from water/wetland context (0.55) and protected/ecological context (0.45)."),
    raster("socioeconomic", "Road/access exposure indicator", "2. Five PIM criteria", "outputs/zimbabwe_pim_scenarios/rainfall_exposure/pim_criteria/socioeconomic_0_1.tif", "criterion", "socioeconomic", unit="0-1", notes="Current Zimbabwe implementation uses road/access proximity only; no independent infrastructure-exposure raster is available."),
    raster("rainfall", "Rainfall climatology (Nov-Mar)", "3. Input and derived factors", "outputs/zimbabwe_pim_scenarios/rainfall_sensitivity/criteria/rainfall_climatology_raw_mm_per_season_PROVISIONAL_30m.tif", "input_factor", "rainfall", unit="mm per rainy season", notes="CHIRPS effective resolution is about 5 km; displayed on the 30 m reference grid."),
    raster("elevation", "Elevation", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_dem_utm35s_30m.tif", "input_factor", "terrain", unit="m"),
    raster("slope", "Slope", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/terrain_preprocessing/zimbabwe_slope_degrees_utm35s_30m.tif", "input_factor", "terrain", unit="degrees"),
    raster("twi", "Topographic wetness index", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_twi.tif", "input_factor", "wetness", unit="TWI"),
    raster("distance_drainage", "Distance to derived drainage", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_distance_to_drainage_t500.tif", "input_factor", "distance", unit="m"),
    raster("upstream_area", "Flow accumulation (contributing cells)", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/hydrology_derivatives/zimbabwe_flow_accumulation.tif", "input_factor", "wetness", unit="cells"),
    raster("soil_k", "Soil erodibility K-factor", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif", "input_factor", "erosion", unit="K (US customary)", notes="SoilGrids effective source resolution is 250 m."),
    raster("ls_factor", "LS-factor", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/ls_factor/zimbabwe_ls_factor_capped50_hillslope_30m.tif", "input_factor", "erosion", unit="LS"),
    raster("c_factor", "C-factor", "3. Input and derived factors", "outputs/zimbabwe_esa_worldcover_2021/c_factor/c_factor_zimbabwe_30m.tif", "input_factor", "erosion", unit="C"),
    raster("land_cover_pressure", "Land-cover pressure", "3. Input and derived factors", "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/land_cover_pressure_0_1.tif", "input_factor", "land", unit="0-1"),
    raster("road_distance", "Distance to roads", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/comparable_distance_factors/zimbabwe_distance_to_roads_km_30m.tif", "input_factor", "distance", unit="km"),
    raster("water_distance", "Distance to water features", "3. Input and derived factors", "outputs/zimbabwe_terrain_hydrology_factors/comparable_distance_factors/zimbabwe_distance_to_water_features_km_30m.tif", "input_factor", "distance", unit="km"),
    raster("population", "Population distribution (WorldPop 2020)", "4. Context and evidence", "data/raw/worldpop_2020_zimbabwe/zwe_ppp_2020_UNadj.tif", "context_raster", "population", unit="people per cell", claim_level="context_evidence"),
    raster("mineral_proximity", "USGS mineral-reference proximity", "4. Context and evidence", "outputs/zimbabwe_pim_scenarios/criteria_stack/criteria/mining_pressure_0_1.tif", "context_raster", "land", unit="0-1", claim_level="context_evidence", notes="Reference proximity only; not a complete active-mining inventory."),
    vector("mapped_mining", "Mapped mining footprints", "4. Context and evidence", "outputs/slide_ready_figures/zimbabwe_evidence_overlays/zimbabwe_mapped_mining_footprints.gpkg", "mining_polygons", layer_name="mapped_mining_footprints", claim_level="context_evidence", notes="Six mapped polygons intersect the working boundary; the source is not exhaustive."),
    vector("boundary", "Upper Mzingwane catchment boundary", "4. Context and evidence", "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg", "boundary", layer_name="v1_working_boundary", claim_level="working_boundary"),
    vector("outlet", "Upper Mzingwane catchment outlet", "4. Context and evidence", "outputs/zimbabwe_boundary/zimbabwe_boundary.gpkg", "outlet_point", layer_name="v1_outlet_point", claim_level="working_boundary"),
)

SITE_SPECS = {
    "peru": SiteSpec("peru", "Peru: Vitor-La Joya-Siguas catchment, Arequipa", "EPSG:32718", "IFPM_Peru.qgz", PERU_LAYERS),
    "zimbabwe": SiteSpec("zimbabwe", "Zimbabwe: Upper Mzingwane catchment", "EPSG:32735", "IFPM_Zimbabwe.qgz", ZIMBABWE_LAYERS),
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
        return PRIORITY_PALETTE
    if name in CRITERION_PALETTES:
        return CRITERION_PALETTES[name]
    return INPUT_PALETTES[name]


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
    if spec.role == "priority_result":
        fractions = (0.2, 0.4, 0.6, 0.8, 1.0)
        values = tuple(minimum + fraction * (maximum - minimum) for fraction in fractions)
        labels = ("Very low", "Low", "Moderate", "High", "Very high")
        ramp_type = QgsColorRampShader.Discrete
    else:
        fractions = (0.0, 0.25, 0.5, 0.75, 1.0)
        if spec.key in {"upstream_area", "population"} and minimum >= 0:
            low_log = math.log1p(minimum)
            high_log = math.log1p(maximum)
            values = tuple(
                math.expm1(low_log + fraction * (high_log - low_log)) for fraction in fractions
            )
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
    color_shader.setClip(spec.role == "priority_result")
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
    from qgis.core import QgsFillSymbol, QgsMarkerSymbol, QgsSingleSymbolRenderer

    if spec.role == "boundary":
        symbol = QgsFillSymbol.createSimple(
            {"color": "255,255,255,0", "outline_color": "35,35,35,255", "outline_width": "0.8"}
        )
    elif spec.role == "mining_polygons":
        symbol = QgsFillSymbol.createSimple(
            {"color": "230,85,13,105", "outline_color": "166,54,3,255", "outline_width": "0.6"}
        )
    elif spec.role == "validation_points":
        symbol = QgsMarkerSymbol.createSimple(
            {"name": "circle", "color": "117,107,177,230", "outline_color": "255,255,255,255", "size": "3.0"}
        )
    elif spec.role == "mining_points":
        symbol = QgsMarkerSymbol.createSimple(
            {"name": "diamond", "color": "230,85,13,235", "outline_color": "255,255,255,255", "size": "3.2"}
        )
    else:
        symbol = QgsMarkerSymbol.createSimple(
            {"name": "triangle", "color": "31,120,180,235", "outline_color": "255,255,255,255", "size": "3.2"}
        )
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()
    style_path.parent.mkdir(parents=True, exist_ok=True)
    message, success = layer.saveNamedStyle(str(style_path))
    if not success:
        raise RuntimeError(f"could not save style {style_path}: {message}")


def load_layer(spec: LayerSpec, site_key: str):
    from qgis.core import QgsRasterLayer, QgsVectorLayer

    source = ROOT / spec.path
    if not source.exists():
        raise FileNotFoundError(f"missing required {site_key} layer: {source}")
    if spec.kind == "raster":
        layer = QgsRasterLayer(str(source), spec.name)
    else:
        uri = str(source)
        if spec.layer_name:
            uri = f"{uri}|layername={spec.layer_name}"
        layer = QgsVectorLayer(uri, spec.name, "ogr")
    if not layer.isValid():
        raise RuntimeError(f"QGIS could not load {site_key}/{spec.key}: {source}")
    layer.setCustomProperty("ifpm/site", site_key)
    layer.setCustomProperty("ifpm/role", spec.role)
    layer.setCustomProperty("ifpm/claim_level", spec.claim_level)
    layer.setCustomProperty("ifpm/unit", spec.unit)
    if spec.notes:
        layer.serverProperties().setAbstract(spec.notes)
    return layer


def _group_order(layers: Iterable[LayerSpec]) -> list[str]:
    return list(dict.fromkeys(layer.group for layer in layers))


def add_site_to_project(project, site: SiteSpec, parent_group, manifest_rows: list[dict[str, str]]):
    groups = {}
    for group_name in _group_order(site.layers):
        group = parent_group.addGroup(group_name)
        group.setExpanded(group_name.startswith("1."))
        groups[group_name] = group

    priority_extent = None
    for spec in site.layers:
        layer = load_layer(spec, site.key)
        project.addMapLayer(layer, False)
        node = groups[spec.group].addLayer(layer)
        node.setItemVisibilityChecked(spec.visible)
        style_path = STYLE_DIR / f"{site.key}_{spec.key}.qml"
        if spec.kind == "raster":
            apply_raster_style(layer, spec, style_path)
        else:
            apply_vector_style(layer, spec, style_path)
        if spec.role == "priority_result":
            priority_extent = layer.extent()

        if not any(row["site"] == site.key and row["layer_key"] == spec.key for row in manifest_rows):
            manifest_rows.append(
                {
                    "site": site.key,
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
        "boundary": 0,
        "outlet_point": 1,
        "validation_points": 2,
        "mining_points": 3,
        "mining_polygons": 4,
        "priority_result": 5,
        "context_raster": 6,
        "criterion": 7,
        "input_factor": 8,
    }
    layers = list(project.mapLayers().values())
    layers.sort(
        key=lambda layer: (
            role_priority.get(layer.customProperty("ifpm/role"), 99),
            layer.customProperty("ifpm/site"),
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


def _rewrite_project_for_portable_export(
    source_project: Path,
    target_project: Path,
    rows: list[dict[str, str]],
) -> None:
    replacements: dict[str, str] = {}
    vector_sources: set[str] = set()
    for row in rows:
        source = ROOT / row["source_path"]
        old = os.path.relpath(source, OUT_DIR).replace(os.sep, "/")
        portable_name = f"{row['site']}_{row['layer_key']}{source.suffix.lower()}"
        new = f"layers/{row['site']}/{row['layer_key']}/{portable_name}"
        layer_name = next(
            spec.layer_name
            for spec in SITE_SPECS[row["site"]].layers
            if spec.key == row["layer_key"]
        )
        if layer_name:
            old = f"{old}|layername={layer_name}"
            new = f"{new}|layername={row['site']}_{row['layer_key']}"
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
            site_option = map_layer.find(
                ".//customproperties//Option[@name='ifpm/site']"
            )
            site_key = site_option.attrib.get("value", "") if site_option is not None else ""
            if old_id:
                stable_uuid = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"ifpm:{source_project.name}:{site_key}:{data_source}:{layer_name}",
                ).hex[:16]
                layer_ids[old_id] = f"{re.sub(r'[^a-z0-9]+', '_', layer_name.lower()).strip('_')}_{stable_uuid}"

            # Portable projects are read-only research handoffs. Remove source-schema
            # editing metadata so excluded internal fields cannot survive in the QGS.
            if data_source in vector_sources:
                for parent in map_layer.iter():
                    for child in list(parent):
                        if child.tag in {
                            "aliases",
                            "attributetableconfig",
                            "conditionalstyles",
                            "constraintExpressions",
                            "constraints",
                            "defaults",
                            "duplicatePolicies",
                            "editable",
                            "expressionfields",
                            "fieldConfiguration",
                            "labelOnTop",
                            "reuseLastValue",
                            "splitPolicies",
                            "storedexpressions",
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
                key=lambda child: (
                    child.findtext("datasource") or "",
                    child.findtext("layername") or "",
                ),
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
            stable = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"ifpm:{source_project.name}:symbol:{uuid_counter}",
            )
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


PUBLIC_VECTOR_FIELDS = {
    ("peru", "mining"): ("objectid", "mina", "longitud", "latitud"),
    ("peru", "sinpad"): (
        "IDE_SINPAD", "FECHA", "ANHO", "MES", "DEPARTAMENTO", "PROVINCIA",
        "DISTRITO", "FENOMENO", "SAFECTA", "SDAMNI", "SFALLE", "SLESI",
        "SDESTRUVIVI", "SINHABIVIVI", "SAFECTAVIVI", "SCAMIRURAL_AFECTA",
        "SCAMIRURAL_DESTRU", "SCARRE_AFECTA", "SCARRE_DESTRU",
        "SPUENTE_AFECTA", "SPUENTE_DESTRU", "SAREACULTI_AFECTA",
        "SAREACULTI_PERDIDO",
    ),
    ("peru", "boundary"): (
        "boundary_id", "source", "HYBAS_ID", "SUB_AREA_km2", "UP_AREA_km2",
        "geo_area_km2",
    ),
    ("zimbabwe", "mapped_mining"): (
        "ISO3_CODE", "COUNTRY_NAME", "mapped_area_km2",
    ),
    ("zimbabwe", "boundary"): ("source", "catchment_area_km2"),
    ("zimbabwe", "outlet"): ("lon", "lat"),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _export_public_vector(source: Path, target: Path, row: dict[str, str]) -> None:
    from osgeo import gdal

    fields = PUBLIC_VECTOR_FIELDS[(row["site"], row["layer_key"])]
    source_dataset = gdal.OpenEx(str(source), gdal.OF_VECTOR)
    if source_dataset is None:
        raise RuntimeError(f"GDAL could not open vector source {source}")
    layer_name = next(
        spec.layer_name
        for spec in SITE_SPECS[row["site"]].layers
        if spec.key == row["layer_key"]
    )
    options = gdal.VectorTranslateOptions(
        format="GPKG",
        layers=[layer_name],
        layerName=f"{row['site']}_{row['layer_key']}",
        selectFields=list(fields),
    )
    result = gdal.VectorTranslate(str(target), source_dataset, options=options)
    source_dataset = None
    if result is None:
        raise RuntimeError(f"could not export public vector layer {row['site']}/{row['layer_key']}")
    result = None
    with sqlite3.connect(target) as connection:
        connection.execute(
            "UPDATE gpkg_contents SET last_change = ?",
            ("1980-01-01T00:00:00.000Z",),
        )
        connection.commit()
        connection.execute("VACUUM")


def _normalize_portable_qml(path: Path) -> None:
    root = ElementTree.fromstring(path.read_bytes())
    for parent in root.iter():
        for child in list(parent):
            if child.tag in {
                "aliases",
                "attributetableconfig",
                "conditionalstyles",
                "constraintExpressions",
                "constraints",
                "defaults",
                "duplicatePolicies",
                "editable",
                "elevation",
                "expressionfields",
                "fieldConfiguration",
                "labelOnTop",
                "reuseLastValue",
                "splitPolicies",
                "storedexpressions",
            }:
                parent.remove(child)
    text = ElementTree.tostring(root, encoding="unicode")
    counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        stable = uuid.uuid5(uuid.NAMESPACE_URL, f"ifpm:{path.name}:{counter}")
        counter += 1
        return f'id="{{{stable}}}"'

    normalized = re.sub(
        r'id="\{[0-9a-fA-F-]{36}\}"',
        replace,
        text,
    )
    canonical = ElementTree.canonicalize(xml_data=normalized, strip_text=True)
    path.write_text(
        "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n" + canonical,
        encoding="utf-8",
    )


def build_portable_export(rows: list[dict[str, str]]) -> list[Path]:
    temp_dir = PORTABLE_DIR.parent / f".{PORTABLE_DIR.name}.tmp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    for row in rows:
        source = ROOT / row["source_path"]
        target_dir = temp_dir / "layers" / row["site"] / row["layer_key"]
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{row['site']}_{row['layer_key']}{source.suffix.lower()}"
        if row["source_type"] == "vector":
            _export_public_vector(source, target, row)
        else:
            shutil.copy2(source, target)
        row["portable_source_path"] = str(
            (Path("layers") / row["site"] / row["layer_key"] / target.name).as_posix()
        )
        row["source_size_bytes"] = str(source.stat().st_size)
        row["source_sha256"] = _sha256(source)
        row["portable_size_bytes"] = str(target.stat().st_size)
        row["portable_sha256"] = _sha256(target)

    shutil.copytree(STYLE_DIR, temp_dir / "styles")
    for style_path in (temp_dir / "styles").glob("*.qml"):
        _normalize_portable_qml(style_path)
    selected_rows = {
        "IFPM_Peru.qgz": [row for row in rows if row["site"] == "peru"],
        "IFPM_Zimbabwe.qgz": [row for row in rows if row["site"] == "zimbabwe"],
        "IFPM_Combined.qgz": rows,
    }
    for project_name, project_rows in selected_rows.items():
        _rewrite_project_for_portable_export(
            OUT_DIR / project_name, temp_dir / project_name, project_rows
        )

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
    (temp_dir / "README.txt").write_text(
        """IFPM portable QGIS project package

Open IFPM_Peru.qgz, IFPM_Zimbabwe.qgz, or IFPM_Combined.qgz directly in QGIS 3.44 or later.
All referenced GeoTIFF and GeoPackage layers are included under layers/ and use package-local
relative paths. PIM layers show relative flood-priority values based on the current five-criterion
weights. They are not validated flood-depth, inundation, or emergency-response maps. Transparent
cells represent NoData / incomplete support. This is a private research handoff; verify source
licences before redistribution outside the project team.
""",
        encoding="utf-8",
    )
    if PORTABLE_DIR.exists():
        shutil.rmtree(PORTABLE_DIR)
    temp_dir.replace(PORTABLE_DIR)
    return [PORTABLE_DIR / name for name in selected_rows]


def build_projects() -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    from qgis.core import (
        QgsApplication,
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsProject,
        QgsRectangle,
    )

    QgsApplication.setPrefixPath(str(QGIS_PREFIX), True)
    app = QgsApplication([], False)
    app.initQgis()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STYLE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, str]] = []
    project = QgsProject.instance()
    project_paths: list[Path] = []
    qgis_readback: list[dict[str, object]] = []
    try:
        for site in SITE_SPECS.values():
            output_path = OUT_DIR / site.project_file
            configure_project(project, f"IFPM - {site.name}", site.project_crs, output_path)
            site_group = project.layerTreeRoot().addGroup(site.name)
            extent = add_site_to_project(project, site, site_group, manifest_rows)
            set_default_extent(project, extent, site.project_crs)
            set_render_order(project)
            write_project(project, output_path)
            project_paths.append(output_path)

        combined_path = OUT_DIR / "IFPM_Combined.qgz"
        configure_project(project, "IFPM - Peru and Zimbabwe", "EPSG:4326", combined_path)
        combined_extent = QgsRectangle()
        for site in SITE_SPECS.values():
            site_group = project.layerTreeRoot().addGroup(site.name)
            site_group.setExpanded(site.key == "peru")
            extent = add_site_to_project(project, site, site_group, manifest_rows)
            transform = QgsCoordinateTransform(
                QgsCoordinateReferenceSystem(site.project_crs),
                project.crs(),
                project.transformContext(),
            )
            transformed = transform.transformBoundingBox(extent)
            combined_extent.combineExtentWith(transformed)
        set_default_extent(project, combined_extent, "EPSG:4326")
        set_render_order(project)
        write_project(project, combined_path)
        project_paths.append(combined_path)

        portable_paths = build_portable_export(manifest_rows)
        project_paths.extend(portable_paths)

        expected_counts = {
            "IFPM_Peru.qgz": len(SITE_SPECS["peru"].layers),
            "IFPM_Zimbabwe.qgz": len(SITE_SPECS["zimbabwe"].layers),
            "IFPM_Combined.qgz": sum(len(site.layers) for site in SITE_SPECS.values()),
        }
        for path in project_paths:
            project.clear()
            read_success = bool(project.read(str(path)))
            invalid_layers = [
                layer.name() for layer in project.mapLayers().values() if not layer.isValid()
            ]
            layer_count = len(project.mapLayers())
            expected = expected_counts[path.name]
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
        "site",
        "layer_key",
        "display_name",
        "group",
        "role",
        "source_path",
        "source_type",
        "provider_crs",
        "unit",
        "visible_by_default",
        "claim_level",
        "style_path",
        "portable_source_path",
        "source_size_bytes",
        "source_sha256",
        "portable_size_bytes",
        "portable_sha256",
        "load_status",
        "notes",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_readme() -> None:
    README.write_text(
        """IFPM QGIS project package

Recommended entry points:
- IFPM_Peru.qgz: Vitor-La Joya-Siguas catchment, Arequipa, in EPSG:32718.
- IFPM_Zimbabwe.qgz: Upper Mzingwane catchment in EPSG:32735.
- IFPM_Combined.qgz: both study areas in EPSG:4326.

The projects use relative paths to the existing workspace data under data/ and outputs/.
Keep this package inside outputs/qgis_project_package/ when opening it. The package does not
duplicate large raster files. PIM layers are visible by default; criteria and factor layers are
available in collapsed groups. The maps are prototype relative-priority outputs, not validated
flood-depth, inundation, or emergency-response maps.
""",
        encoding="utf-8",
    )


def validate_package(qgis_readback: list[dict[str, object]] | None = None) -> dict[str, object]:
    projects = [OUT_DIR / name for name in ("IFPM_Peru.qgz", "IFPM_Zimbabwe.qgz", "IFPM_Combined.qgz")]
    checks: list[dict[str, object]] = []
    for path in projects:
        if not path.exists():
            raise FileNotFoundError(path)
        with zipfile.ZipFile(path) as archive:
            qgs_names = [name for name in archive.namelist() if name.endswith(".qgs")]
            if len(qgs_names) != 1:
                raise RuntimeError(f"{path.name} contains {len(qgs_names)} QGS documents")
            xml_bytes = archive.read(qgs_names[0])
        ElementTree.fromstring(xml_bytes)
        text = xml_bytes.decode("utf-8")
        absolute_path_free = str(ROOT) not in text and "/Users/jlw/" not in text
        if not absolute_path_free:
            raise RuntimeError(f"absolute workspace path found in {path.name}")
        checks.append(
            {
                "project": path.name,
                "qgs_document": qgs_names[0],
                "xml_valid": True,
                "absolute_path_free": True,
                "size_bytes": path.stat().st_size,
            }
        )

    portable_checks: list[dict[str, object]] = []
    for path in [PORTABLE_DIR / project.name for project in projects]:
        if not path.exists():
            raise FileNotFoundError(path)
        with zipfile.ZipFile(path) as archive:
            qgs_names = [name for name in archive.namelist() if name.endswith(".qgs")]
            if len(qgs_names) != 1:
                raise RuntimeError(f"{path.name} contains {len(qgs_names)} QGS documents")
            xml_bytes = archive.read(qgs_names[0])
        root = ElementTree.fromstring(xml_bytes)
        sources = [
            element.attrib["source"]
            for element in root.iter()
            if "source" in element.attrib and not element.attrib["source"].startswith("attachment://")
        ]
        sources.extend(
            element.text or "" for element in root.iter("datasource") if element.text
        )
        external_sources = [
            source
            for source in sources
            if source.startswith(("/", "../", "file://")) or ":\\" in source
        ]
        if external_sources:
            raise RuntimeError(f"external data sources found in portable {path.name}: {external_sources}")
        portable_checks.append(
            {
                "project": path.name,
                "qgs_document": qgs_names[0],
                "package_local_sources": True,
                "source_reference_count": len(sources),
                "size_bytes": path.stat().st_size,
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
        "IFPM_Peru.qgz", "IFPM_Zimbabwe.qgz", "IFPM_Combined.qgz",
        "README.txt", "manifest.csv", "validation.json",
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
    from osgeo import gdal
    from qgis.core import Qgis, QgsProjUtils

    semantic_errors: list[str] = []
    for site in ("peru", "zimbabwe"):
        site_rows = [row for row in rows if row["site"] == site]
        priority = next(row for row in site_rows if row["role"] == "priority_result")
        if priority["claim_level"] != "sensitivity_scenario":
            semantic_errors.append(f"{site} priority claim level is not sensitivity_scenario")
        units = {row["layer_key"]: row["unit"] for row in site_rows}
        if units.get("distance_drainage") != "m":
            semantic_errors.append(f"{site} drainage-distance unit is not metres")
        if units.get("upstream_area") != "cells":
            semantic_errors.append(f"{site} flow-accumulation unit is not contributing cells")
    zimbabwe_socioeconomic = next(
        row
        for row in rows
        if row["site"] == "zimbabwe" and row["layer_key"] == "socioeconomic"
    )
    if zimbabwe_socioeconomic["display_name"] != "Road/access exposure indicator":
        semantic_errors.append("Zimbabwe socioeconomic label overstates available evidence")

    combined_readbacks = [
        item for item in (qgis_readback or []) if item["project"] == "IFPM_Combined.qgz"
    ]
    for item in combined_readbacks:
        xmin, _, xmax, _ = item["default_extent"]
        if xmin >= -70 or xmax <= 20:
            semantic_errors.append(
                f"{item['package_type']} combined extent does not contain both study areas"
            )
    if semantic_errors:
        raise RuntimeError(f"semantic validation failed: {semantic_errors}")

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> int:
    parse_args()
    if os.environ.get("IFPM_QGIS_RUNTIME") != "1":
        return relaunch_with_qgis()
    rows, qgis_readback = build_projects()
    write_manifest(rows)
    write_readme()
    result = validate_package(qgis_readback)
    print(
        f"wrote {len(result['projects'])} QGIS projects with "
        f"{result['manifest_layer_count']} governed layers to {OUT_DIR.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
