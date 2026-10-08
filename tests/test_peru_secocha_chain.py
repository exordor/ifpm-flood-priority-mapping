from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import unittest
import zipfile
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
CHAIN = ROOT / "bin/factors/run_peru_secocha_chain.py"
BASE = ROOT / "outputs/peru_secocha_a7367_reference_extent_v1"
PACKAGE = ROOT / "outputs/peru_secocha_qgis_project_package"
PORTABLE = ROOT / "exports/qgis_packages/secocha/FullAudit"


class PeruSecochaChainTest(unittest.TestCase):
    def test_catalog_preserves_supervisor_weights_and_external_mining(self):
        result = subprocess.run([PYTHON, CHAIN, "--catalog-only"], cwd=ROOT, text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        catalog = json.loads(result.stdout)
        self.assertEqual(catalog["boundary_id"], "peru_secocha_a7367_reference_extent_v1")
        self.assertEqual(catalog["metric_crs"], "EPSG:32718")
        self.assertFalse(catalog["weights_changed"])
        self.assertEqual(catalog["main_weights"], {"flood_hazard": .34, "sediment": .25,
                         "landuse_asm": .17, "environmental": .10, "socioeconomic": .14})
        self.assertEqual(catalog["mining_role"], "external overlay only")

    def test_shared_chain_uses_secocha_buffer_and_soil_snapshot(self):
        result = subprocess.run([PYTHON, CHAIN, "--catalog-only"], cwd=ROOT, text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        catalog = json.loads(result.stdout)
        self.assertEqual(
            catalog["slope_buffered_path"],
            "outputs/peru_secocha_a7367_reference_extent_v1/terrain_preprocessing/"
            "peru_secocha_a7367_reference_extent_v1_slope_degrees_buffered_utm18s_30m.tif",
        )
        self.assertEqual(
            catalog["soilgrids_snapshot_path"],
            "data/raw/soilgrids_250m_peru_secocha/k_factor_0_30cm_avg_250m_us.tif",
        )
        self.assertNotIn("goslar", catalog["slope_buffered_path"].lower())
        self.assertNotIn("goslar", catalog["soilgrids_snapshot_path"].lower())

    def test_generated_grid_and_quality_report_pass(self):
        ref = BASE / "terrain_preprocessing/peru_secocha_a7367_reference_extent_v1_dem_utm18s_30m.tif"
        priority = BASE / "priority_scenarios/scenarios/priority_secocha_direct_pim.tif"
        with rasterio.open(ref) as src:
            self.assertEqual(src.crs.to_epsg(), 32718)
            self.assertAlmostEqual(src.res[0], 30, delta=.01)
        with rasterio.open(priority) as src:
            self.assertEqual(src.crs.to_epsg(), 32718)
        report = json.loads((BASE / "quality_assurance/chain_validation.json").read_text())
        self.assertEqual(report["status"], "pass")
        self.assertTrue(all(row["grid_compatible"] for row in report["raster_checks"]))
        self.assertTrue(all(row["sha256_matches"] for row in report["frozen_previous_area_checks"]))

    def test_qgis_package_is_valid_portable_and_uses_secocha_names(self):
        validation = json.loads((PACKAGE / "validation.json").read_text())
        self.assertEqual(validation["status"], "package_integrity_valid")
        self.assertEqual(validation["manifest_layer_count"], 39)
        self.assertTrue(all(not x["invalid_layers"] for x in validation["qgis_readback"]))
        with (PACKAGE / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["site"] for row in rows}, {"secocha"})
        self.assertTrue(all("goslar" not in row["style_path"].lower() for row in rows))
        project = PORTABLE / "IFPM_Peru_Secocha_FullAudit.qgz"
        with zipfile.ZipFile(project) as archive:
            qgs = next(name for name in archive.namelist() if name.endswith(".qgs"))
            xml = archive.read(qgs).decode("utf-8")
        self.assertNotIn("/Users/jlw/", xml)
        self.assertNotIn("Goslar", xml)
        self.assertIn("Secocha", xml)

    def test_qgis_direct_scored_layers_expose_weights(self):
        subprocess.run([PYTHON, ROOT / "bin/package/build_peru_secocha_qgis_project_package.py"], cwd=ROOT, check=True)
        with (PACKAGE / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            rows = {row["layer_key"]: row for row in csv.DictReader(handle)}
        expected = {
            "flood_hazard": "PIM weight 0.34",
            "sediment": "PIM weight 0.25",
            "landuse_asm": "PIM weight 0.17",
            "environmental": "PIM weight 0.10",
            "socioeconomic": "PIM weight 0.14",
            "rainfall": "FH component weight 0.35",
            "twi": "FH component weight 0.25",
            "distance_drainage": "FH component weight 0.40",
            "soil_k": "SE component weight 0.25",
            "ls_factor": "SE component weight 0.50",
            "c_factor": "SE component weight 0.25",
            "land_pressure": "LU component weight 0.40",
            "bare_soil": "LU component weight 0.35",
            "built_agri_road": "LU component weight 0.25",
            "water_wetland": "ES component weight 0.65",
            "protected": "ES component weight 0.35",
            "road_access": "SV component weight 0.35",
            "population": "SV component weight 0.35",
            "built": "SV component weight 0.30",
        }
        for key, label in expected.items():
            self.assertIn(key, rows)
            self.assertIn(label, rows[key]["display_name"])

        # Intermediate terrain products are not direct scored components.
        for key in ("elevation", "slope", "flow_accumulation", "streams"):
            self.assertNotIn("weight", rows[key]["display_name"].lower())

    def test_map7_digitization_is_source_anchored_and_bounded(self):
        observed = ROOT / "outputs/secocha_2023_validation/observed_hazard"
        manifest = json.loads((observed / "digitization_manifest.json").read_text())
        comparison = json.loads((observed / "secocha_2023_event_pim_comparison.json").read_text())
        self.assertEqual(manifest["source_pdf_page"], 75)
        self.assertEqual(manifest["map_crs"], "EPSG:32718")
        self.assertEqual(set(manifest["extracted_classes"]), {"huaico_2023_02_05", "mudflow_2023_02_05"})
        self.assertEqual(manifest["claim_level"], "validation_candidate")
        self.assertGreater(comparison["event_geometry_area_km2"], 0)
        self.assertGreater(comparison["event_pim_coverage_fraction"], 0)
        self.assertLess(comparison["event_pim_coverage_fraction"], 1)
        self.assertIn("high_pim_enrichment_ratio", comparison)
        self.assertIn("external overlay only", comparison["mining_role"])

    def test_original_ingemmet_gis_is_a7367_context_evidence(self):
        source = ROOT / "data/raw/ingemmet_a7367_cartografia_peligros_secocha/ingemmet_a7367_cartografia_peligros_layer6_secocha.geojson"
        manifest = json.loads((BASE / "source_acquisition/ingemmet_original_gis_manifest.json").read_text())
        comparison = json.loads((ROOT / "outputs/secocha_2023_validation/observed_hazard/ingemmet_original_gis_comparison.json").read_text())
        self.assertTrue(source.exists())
        self.assertEqual(manifest["boundary_id"], "peru_secocha_a7367_reference_extent_v1")
        self.assertEqual(manifest["boundary_path"], "outputs/peru_secocha_boundary/peru_secocha_active_boundary.gpkg")
        self.assertEqual(manifest["query_where"], "CODIGO = 'A7367' AND DISTRITO = 'Mariano Nicolás Valcárcel' AND PROVINCIA = 'Camaná' AND FECHA_EVAL = 'febrero 2023'")
        self.assertIn("MapServer/6/query", manifest["query_url"])
        self.assertFalse(manifest["exceeded_transfer_limit"])
        self.assertEqual(manifest["negative_layer7_check"]["feature_count"], 0)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), manifest["sha256"])
        boundary = ROOT / manifest["boundary_path"]
        self.assertEqual(hashlib.sha256(boundary.read_bytes()).hexdigest(), manifest["boundary_sha256"])
        self.assertEqual(manifest["feature_count"], 3)
        self.assertEqual(manifest["attribute_filter_check"]["codigo_values"], ["A7367"])
        self.assertEqual({row["hazard_class"] for row in comparison["features"]},
                         {"Avalancha de detritos", "Flujo de detritos", "Caída de rocas"})
        self.assertGreater(comparison["pdf_event_candidate_covered_by_original_fraction"], .9)
        self.assertGreater(comparison["pdf_event_candidate_covered_by_flow_only_fraction"], .8)
        self.assertEqual(comparison["source_sha256"], manifest["sha256"])
        self.assertEqual(comparison["claim_level"], "validation_candidate")


if __name__ == "__main__":
    unittest.main()
