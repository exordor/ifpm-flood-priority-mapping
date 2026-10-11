#!/usr/bin/env python3
"""Build the portable QGIS chain package for the active Secocha Peru experiment."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "bin/package/build_goslar_qgis_full_audit.py"
spec = importlib.util.spec_from_file_location("ifpm_qgis_template", TEMPLATE_PATH)
q = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = q
spec.loader.exec_module(q)

BASE = "outputs/secocha_pim_chain"
OUT = ROOT / "outputs/secocha_qgis_full_audit"
PORTABLE = ROOT / "exports/qgis_packages/secocha/FullAudit"

q.OUT_DIR = OUT
q.STYLE_DIR = OUT / "styles"
q.MANIFEST = OUT / "manifest.csv"
q.VALIDATION = OUT / "validation.json"
q.README = OUT / "README.txt"
q.PORTABLE_DIR = PORTABLE
q.PROJECT_NAME = "IFPM_Peru_Secocha_FullAudit.qgz"
q.SITE_KEY = "secocha"
EXTERNAL_OVERLAY_GROUP = "7. External validation and overlays"
PROXY_REPLACEMENT_MANIFEST = ROOT / "outputs/secocha_official_proxy_replacements/proxy_replacement_manifest.json"
PROXY_REPLACEMENT_SHA256 = q._sha256(PROXY_REPLACEMENT_MANIFEST)
PROXY_REPLACEMENT_LINEAGE = (
    "dataset_id=secocha_official_proxy_replacements; "
    f"source_manifest_sha256={PROXY_REPLACEMENT_SHA256}."
)
# The shared builder records its generator hash from its module __file__.
# Point that lineage field at this Secocha wrapper so the package invalidates
# when the site-specific layer contract changes.
q.__file__ = str(Path(__file__).resolve())
if q.STYLE_DIR.exists():
    for stale_style in q.STYLE_DIR.glob("goslar_*.qml"):
        stale_style.unlink()

def relaunch():
    if not q.QGIS_PYTHON.exists():
        raise RuntimeError(f"QGIS Python wrapper not found: {q.QGIS_PYTHON}")
    OUT.mkdir(parents=True, exist_ok=True)
    command = [str(q.QGIS_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]
    return subprocess.run(command, cwd=OUT, env=q.qgis_environment(), check=False).returncode
q.relaunch_with_qgis = relaunch

r = q.raster; v = q.vector
layers = (
    r("priority", "Relative priority index", "1. Priority result", f"{BASE}/priority_scenarios/scenarios/priority_secocha_direct_pim.tif", "priority_result", "priority", visible=True, unit="0-1", claim_level="provisional", notes="Active Secocha Peru prototype with unchanged Supervisor v07 weights; mining is excluded from the score."),
    r("flood_hazard", "Flood-conditioning indicator (FH | PIM weight 0.34)", "2. Five PIM criteria", f"{BASE}/priority_scenarios/pim_criteria/flood_hazard_0_1.tif", "criterion", "flood_hazard", unit="0-1", claim_level="provisional"),
    r("sediment", "Sediment / erosion score (SE | PIM weight 0.25)", "2. Five PIM criteria", f"{BASE}/priority_scenarios/pim_criteria/sediment_0_1.tif", "criterion", "sediment", unit="0-1", claim_level="provisional"),
    r("landuse_asm", "Land-use pressure score (LU | PIM weight 0.17)", "2. Five PIM criteria", f"{BASE}/priority_scenarios/pim_criteria/landuse_asm_0_1.tif", "criterion", "landuse_asm", unit="0-1", claim_level="provisional"),
    r("environmental", "Environmental context indicator (ES | PIM weight 0.10)", "2. Five PIM criteria", f"{BASE}/priority_scenarios/pim_criteria/environmental_0_1.tif", "criterion", "environmental", unit="0-1", claim_level="provisional"),
    r("socioeconomic", "Socioeconomic exposure indicator (SV | PIM weight 0.14)", "2. Five PIM criteria", f"{BASE}/priority_scenarios/pim_criteria/socioeconomic_0_1.tif", "criterion", "socioeconomic", unit="0-1", claim_level="provisional"),
    r("elevation", "Elevation (SRTM 1 arc-second)", "3. Terrain and hydrology", f"{BASE}/terrain_preprocessing/secocha_dem_utm18s_30m.tif", "input_factor", "terrain", unit="m"),
    r("slope", "Slope", "3. Terrain and hydrology", f"{BASE}/terrain_preprocessing/secocha_slope_degrees_utm18s_30m.tif", "input_factor", "slope", unit="degrees"),
    r("flow_accumulation", "Flow accumulation (contributing cells)", "3. Terrain and hydrology", f"{BASE}/hydrology_derivatives/secocha_flow_accumulation.tif", "input_factor", "hydrology", unit="cells"),
    r("streams", "Derived drainage (threshold 500 cells)", "3. Terrain and hydrology", f"{BASE}/hydrology_derivatives/secocha_streams_t500.tif", "input_factor", "hydrology", unit="stream mask"),
    r("distance_drainage", "Distance to derived drainage (FH component weight 0.40)", "3. Terrain and hydrology", f"{BASE}/hydrology_derivatives/secocha_distance_to_drainage_t500.tif", "input_factor", "distance", unit="m", notes="Raw distance input; weight applies after inversion and standardization to the drainage_proximity component."),
    r("twi", "Topographic wetness index (FH component weight 0.25)", "3. Terrain and hydrology", f"{BASE}/hydrology_derivatives/secocha_twi.tif", "input_factor", "wetness", unit="TWI", notes="Raw TWI input; weight applies after percentile standardization."),
    r("ls_factor", "LS factor, capped at 50 (SE component weight 0.50)", "4. Erosion and land cover", f"{BASE}/ls_factor/secocha_ls_factor_capped50_hillslope_30m.tif", "input_factor", "erosion", unit="LS", notes="Raw LS input; weight applies after percentile standardization."),
    r("soil_k", "Soil erodibility K factor, SoilGrids (SE component weight 0.25)", "4. Erosion and land cover", f"{BASE}/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif", "input_factor", "erosion", unit="K", notes="Raw K input; weight applies after percentile standardization. 250 m effective source resolution, resampled to the overlay grid."),
    r("c_factor", "Cover-management C factor, WorldCover (SE component weight 0.25)", "4. Erosion and land cover", f"{BASE}/worldcover_factors/c_factor_30m.tif", "input_factor", "erosion", unit="C", notes="Raw C input; weight applies after percentile standardization."),
    r("land_pressure", "Land-cover pressure, WorldCover (LU component weight 0.40)", "4. Erosion and land cover", f"{BASE}/worldcover_factors/land_cover_runoff_pressure_30m.tif", "input_factor", "land", unit="0-1"),
    r("bare_soil", "Bare-soil / vegetation-loss proxy (LU component weight 0.35)", "4. Erosion and land cover", f"{BASE}/criteria_stack/criteria/bare_soil_vegetation_loss_0_1.tif", "input_factor", "land", unit="0-1", notes="Active bare_soil_vegetation_loss component; WorldCover bare/sparse class proxy."),
    r("built_agri_road", "Built, agriculture and road pressure (LU component weight 0.25)", "4. Erosion and land cover", f"{BASE}/criteria_stack/criteria/built_agriculture_road_expansion_0_1.tif", "input_factor", "land", unit="0-1", notes="Active built_agriculture_road_expansion component."),
    r("rainfall", "Rainfall climatology, CHIRPS Dec-Mar (FH component weight 0.35)", "5. Rainfall", f"{BASE}/rainfall_criterion/rainfall_climatology_0_1_PROVISIONAL_30m.tif", "input_factor", "rainfall", unit="0-1", claim_level="sensitivity_scenario", notes="Standardized FH rainfall component. CHIRPS 0.05 degree native; bilinear 30 m resample is only for overlay compatibility."),
    r("population", "Population exposure, WorldPop 2020 (SV component weight 0.35)", "6. Exposure and environment", f"{BASE}/exposure_indicators/population_exposure_0_1.tif", "input_factor", "population", unit="0-1", notes="Standardized settlement_population component."),
    r("built", "Built-up exposure proxy, WorldCover (SV component weight 0.30)", "6. Exposure and environment", f"{BASE}/exposure_indicators/built_infrastructure_exposure_0_1.tif", "input_factor", "population", unit="0-1", notes="Active critical_infrastructure component as a built-up land-cover proxy; not a facility inventory."),
    r("road_access", "Road-access proximity, OSM (SV component weight 0.35)", "6. Exposure and environment", f"{BASE}/criteria_stack/criteria/road_access_proximity_0_1.tif", "input_factor", "distance", unit="0-1", notes="Active road_access_proximity component with 20 km linear decay."),
    r("water_wetland", "Water and wetland context (ES component weight 0.65)", "6. Exposure and environment", f"{BASE}/environmental_sensitivity/water_wetland_context_0_1.tif", "input_factor", "wetness", unit="0-1", notes="Active water_wetland_context component."),
    r("protected", "Protected-area context, confirmed layer-0 absence (ES component weight 0.35)", "6. Exposure and environment", f"{BASE}/environmental_sensitivity/protected_area_context_0_1.tif", "input_factor", "land", unit="0-1", notes="Active protected_ecological_context component. SERNANP layer 0 returned zero features within 25 km; other protection categories were not queried."),
    v("boundary", "Active Secocha working boundary (A7367 map frame)", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_boundary/secocha_boundary.gpkg", "boundary", layer_name="secocha_active_boundary", claim_level="working_boundary", notes="Not an event footprint or catchment boundary."),
    v("original_a7367", "INGEMMET original A7367 hazard polygons", EXTERNAL_OVERLAY_GROUP, "data/raw/ingemmet_a7367_cartografia_peligros_secocha/ingemmet_a7367_cartografia_peligros_layer6_secocha.geojson", "original_hazard", layer_name="ingemmet_a7367_cartografia_peligros_layer6_secocha", claim_level="context_evidence", notes="Original INGEMMET Cartografia de Peligros layer 6 query; three A7367 polygons. General geological-hazard cartography, not automatically the observed 5 February footprint."),
    v("event_footprint", "5 February event footprint candidate", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/observed_hazard/secocha_2023_map7_event_digitization.gpkg", "event_footprint", layer_name="event_footprint_candidate", claim_level="validation_candidate", notes="Union of the two explicit 5 February classes from A7367 Map 7; semi-automatic report-map digitization."),
    v("event_huaico", "5 February huaico candidate", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/observed_hazard/secocha_2023_map7_event_digitization.gpkg", "event_huaico", layer_name="huaico_2023_02_05", claim_level="validation_candidate", notes="Legend-colour extraction of Huaico del 5 de febrero from A7367 Map 7."),
    v("event_mudflow", "5 February mudflow candidate", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/observed_hazard/secocha_2023_map7_event_digitization.gpkg", "event_mudflow", layer_name="mudflow_2023_02_05", claim_level="validation_candidate", notes="Legend-colour extraction of Flujo de lodo del 5 de febrero from A7367 Map 7."),
    v("mining", "INGEMMET mining records (external overlay)", EXTERNAL_OVERLAY_GROUP, "data/raw/ingemmet_catastro_minero_secocha/secocha_pequena_mineria.gpkg", "evidence_points", layer_name="pequena_mineria", claim_level="context_evidence", notes="Reference/cadastral records; not verified active extraction. External overlay only; excluded from the PIM score."),
    v("minedu_schools_2023", "MINEDU educational locations (2023 statistical references)", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_official_proxy_replacements/secocha_official_exposure_mining.gpkg", "evidence_points", layer_name="minedu_education_locations_2023", visible=False, claim_level="context_evidence", notes=f"Official 2023 education register: 47 context locations, including 11 missing-CODLOCAL service-level locations; 12 locations are inside the active frame. Statistical reference points, not building-accurate or confirmed operational on 5 February. Reported student/teacher fields are service-row sums. Excludes director/contact fields and enters no PIM input. {PROXY_REPLACEMENT_LINEAGE}"),
    v("minam_health_facilities", "MINAM health-facility locations (25 km context)", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_official_proxy_replacements/secocha_official_exposure_mining.gpkg", "evidence_points", layer_name="minam_health_facilities_context", visible=False, claim_level="context_evidence", notes=f"Four official health-facility records within the exact 25 km context and none inside the active frame; live-source event-date status is not established. Source warns points may represent populated-centre locations, not exact building positions. {PROXY_REPLACEMENT_LINEAGE}"),
    v("ingemmet_mining_rights", "INGEMMET mining-right polygons (exact 5 km context)", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_official_proxy_replacements/secocha_official_exposure_mining.gpkg", "mining_context_overlay", layer_name="ingemmet_mining_rights", visible=False, claim_level="context_evidence", notes=f"Official referential legal/cadastral rights with status; 173 polygons remain after exact 5 km filtering and 47 have reportable positive-area overlap (at least 1 m2) with the active frame. Not verified active extraction footprints and excluded from PIM. {PROXY_REPLACEMENT_LINEAGE}"),
    v("ingemmet_dgm_activity", "INGEMMET DGM concession status: EXPLOTACION (exact 5 km context)", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_official_proxy_replacements/secocha_official_exposure_mining.gpkg", "mining_context_overlay", layer_name="ingemmet_dgm_activity", visible=False, claim_level="context_evidence", notes=f"Two DGM administrative concession records labelled ESTADO_MINEM=EXPLOTACION occur within the exact 5 km context; neither intersects the active frame. Active extraction is not field-verified, informal activity is not ruled out, and the layer is excluded from PIM. {PROXY_REPLACEMENT_LINEAGE}"),
    v("field_anchors", "INGEMMET A7367 field anchors", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/ingemmet_field_anchors.geojson", "evidence_points", layer_name="ingemmet_field_anchors", claim_level="validation_candidate", notes="Report-derived field anchors, not a complete event footprint."),
    v("response_locations", "INDECI response locations", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/indeci_response_locations.geojson", "evidence_points", layer_name="indeci_response_locations", claim_level="validation_candidate", notes="Report-derived affected/response locations; report date retained in evidence table."),
    r("s2_ndwi_before", "Sentinel-2 NDWI, 3 Feb pre-event", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/satellite_before_after/processed/s2_ndwi_before_10m.tif", "validation_raster", "wetness", visible=False, unit="NDWI", claim_level="validation_candidate", notes="NDWI=(B03-B08)/(B03+B08); SCL 4-7 valid. Validation context only; does not enter the PIM score."),
    r("s2_ndwi_after", "Sentinel-2 NDWI, 8 Feb post-event", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/satellite_before_after/processed/s2_ndwi_after_10m.tif", "validation_raster", "wetness", visible=False, unit="NDWI", claim_level="validation_candidate", notes="Three days post-event; not peak-flow extent. Validation context only; does not enter the PIM score."),
    r("s2_new_surface_water", "Sentinel-2 new surface-water candidate", EXTERNAL_OVERLAY_GROUP, "outputs/secocha_2023_validation/satellite_before_after/processed/s2_new_surface_water_candidate_10m.tif", "validation_raster", "wetness", visible=False, unit="candidate mask", claim_level="validation_candidate", notes="NDWI>0.15 and SCL-common-valid only. Current candidate count is zero for this debris-flow event; negative diagnostic, not an event footprint."),
)

q.GOSLAR_LAYERS = layers
q.GOSLAR_SITE = {"key": "secocha", "name": "Peru: Secocha 2023 prototype - FullAudit processing chain",
                 "project_crs": "EPSG:32718", "project_file": q.PROJECT_NAME, "layers": layers}

original_portable = q.build_portable_export
def portable(rows):
    project = original_portable(rows)
    (q.PORTABLE_DIR / "README.txt").write_text(
        "IFPM Peru Secocha QGIS FullAudit package\n\nOpen IFPM_Peru_Secocha_FullAudit.qgz in QGIS. The groups show the complete chain from terrain and hydrology through the five PIM criteria and relative priority result, plus separate A7367 Map 7 huaico and mudflow event candidates. All paths are package-local. The map-frame boundary is diagnostic, not a catchment. Event polygons are semi-automatic report-map digitization candidates. Mining records are external overlays only and do not enter the score. CHIRPS and SoilGrids retain their native-resolution warnings. The FullAudit package includes processed Sentinel-2 validation context plus newly acquired MINEDU 2023 statistical education locations, MINAM health-facility context, INGEMMET mining-right polygons and DGM administrative concession status (ESTADO_MINEM=EXPLOTACION). These four official layers are default-disabled and remain outside PIM: the facility points are not confirmed building-accurate/event-date observations, and mining status is not field-verified active extraction. This is a provisional research prototype, not a final flood-risk or emergency-response map.\n",
        encoding="utf-8")
    return project
q.build_portable_export = portable

def readme():
    q.OUT_DIR.mkdir(parents=True, exist_ok=True)
    q.README.write_text("Secocha active Peru prototype, FullAudit processing chain. Open IFPM_Peru_Secocha_FullAudit.qgz. See manifest.csv and validation.json for layer lineage and checks. Group 7 includes default-disabled Sentinel-2 candidates and official MINEDU/MINAM/INGEMMET facility and mining context layers; none enters PIM. Event-window CHIRPS and raw Sentinel assets remain under outputs/secocha_2023_validation.\n", encoding="utf-8")
q.write_readme = readme

def main():
    if os.environ.get("IFPM_QGIS_RUNTIME") != "1":
        return relaunch()
    rows, readback = q.build_projects()
    q.write_manifest(rows)
    q.write_readme()
    result = q.validate_package(readback)
    q.build_portable_zip(q.PORTABLE_DIR, q.PORTABLE_DIR.with_suffix(".zip"))
    print(f"wrote Secocha QGIS project with {result['manifest_layer_count']} governed layers to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
