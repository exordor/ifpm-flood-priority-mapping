from __future__ import annotations

import csv
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAIN_CONFIG = ROOT / "context/docs/research-map/peru_authoritative_figure_chain.csv"
CHAIN_BUILDER = ROOT / "bin/package/build_peru_report_figure_chain.py"
OVERLAY_EXPORTER = ROOT / "bin/visualize/export_peru_evidence_overlay_maps.py"
OVERLAY_INDEX = ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/index.csv"
ACTIVE_TERMINOLOGY = ROOT / "bin/check_active_terminology.py"
PROJECT_TERMINOLOGY = ROOT / "bin/check_project_terminology.py"
GLOSSARY_CHECK = ROOT / "bin/check_glossary_sources.py"
ENVIRONMENTAL_BUILDER = ROOT / "bin/criteria/build_pim_environmental_sensitivity.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PeruReportFigureGovernanceTest(unittest.TestCase):
    def test_governance_entrypoints_exist(self):
        self.assertTrue(CHAIN_CONFIG.exists())
        self.assertTrue(CHAIN_BUILDER.exists())
        self.assertTrue(OVERLAY_EXPORTER.exists())

    def test_chain_has_six_ordered_stages_and_no_legacy_paths(self):
        with CHAIN_CONFIG.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(
            list(dict.fromkeys(row["stage_id"] for row in rows)),
            [
                "raw_inputs",
                "pim_criteria",
                "ahp_pim",
                "mining_population_overlay",
                "contribution_explanation",
                "validation_diagnostic",
            ],
        )
        self.assertEqual(len({row["item_id"] for row in rows}), len(rows))
        self.assertTrue(all(row["status"] == "current" for row in rows))
        forbidden = ("zimbabwe", "report_image_catalog_2026-07-06", "mentor_boss_priority_explanation")
        self.assertFalse(any(token in row["source_png"].lower() for row in rows for token in forbidden))

        diagnostic = next(row for row in rows if row["stage_id"] == "validation_diagnostic")
        self.assertEqual(diagnostic["claim_level"], "diagnostic_only")
        self.assertEqual(diagnostic["evidence_role"], "event_point_colocation_context")
        self.assertNotIn("validated", diagnostic["display_role"].lower())

    def test_overlay_exporter_binds_current_evidence_without_validation_claim(self):
        module = load_module("export_peru_evidence_overlay_maps", OVERLAY_EXPORTER)

        self.assertEqual(module.PIM.name, "priority_mentor_peru_direct_pim.tif")
        self.assertEqual(module.POPULATION_EXPOSURE.name, "population_exposure_0_1.tif")
        self.assertEqual(module.MINING.name, "peru_hybas_l7_6070641200_pequena_mineria.gpkg")
        self.assertEqual(module.SINPAD.name, "peru_hybas_l7_6070641200_sinpad_pim_colocation.gpkg")
        self.assertEqual(module.SINPAD_CLAIM_LEVEL, "diagnostic_only")
        self.assertIn("co-location diagnostic", module.SINPAD_NOTE)
        self.assertNotIn("validated", module.SINPAD_NOTE.lower())

    def test_overlay_exporter_collapses_duplicate_reference_locations(self):
        module = load_module("export_peru_evidence_overlay_location_rules", OVERLAY_EXPORTER)
        mining = module.gpd.read_file(module.MINING).to_crs(module.maps.DST_CRS)
        mining_locations = module.collapse_mining_locations(mining)
        self.assertEqual(len(mining), 11)
        self.assertEqual(len(mining_locations), 6)
        boundary = module.gpd.read_file(module.BOUNDARY, layer="peru_pilot_boundary").to_crs(
            module.maps.DST_CRS
        )
        inside, nearby = module.split_locations_by_boundary(mining_locations, boundary.geometry.iloc[0])
        self.assertEqual(len(inside), 2)
        self.assertEqual(len(nearby), 4)

        events = module.gpd.read_file(module.SINPAD).to_crs(module.maps.DST_CRS)
        event_locations = module.collapse_sinpad_locations(events)
        self.assertEqual(len(event_locations), 11)
        self.assertEqual(int(event_locations["is_flood_specific"].sum()), 2)

    @unittest.skipUnless(OVERLAY_INDEX.exists(), "requires ignored local evidence-overlay outputs")
    def test_overlay_index_binds_input_and_output_checksums(self):
        with OVERLAY_INDEX.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 4)
        for row in rows:
            output = ROOT / row["path"]
            pim = ROOT / row["pim_source"]
            self.assertEqual(row["output_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(row["pim_sha256"], hashlib.sha256(pim.read_bytes()).hexdigest())
            self.assertEqual(
                row["boundary_sha256"],
                hashlib.sha256((ROOT / row["boundary_source"]).read_bytes()).hexdigest(),
            )
            if row["figure_id"] == "peru_priority_mining_population_overlay":
                self.assertEqual(
                    row["population_sha256"],
                    hashlib.sha256((ROOT / row["population_source"]).read_bytes()).hexdigest(),
                )
                self.assertEqual(
                    row["mining_sha256"],
                    hashlib.sha256((ROOT / row["mining_source"]).read_bytes()).hexdigest(),
                )
            else:
                self.assertEqual(
                    row["event_sha256"],
                    hashlib.sha256((ROOT / row["event_source"]).read_bytes()).hexdigest(),
                )

    def test_builder_archives_known_legacy_report_surfaces(self):
        module = load_module("build_peru_report_figure_chain", CHAIN_BUILDER)
        legacy = {str(path) for path in module.LEGACY_OUTPUTS}

        self.assertIn("outputs/report_image_catalog_2026-07-06", legacy)
        self.assertIn("outputs/mentor_boss_priority_explanation", legacy)
        self.assertIn("outputs/zimbabwe_peru_prototype_comparison", legacy)
        self.assertIn("outputs/sensitivity_figures", legacy)
        self.assertIn("outputs/slide_ready_figures/peru_conditioning_factor_maps", legacy)
        self.assertIn("outputs/slide_ready_figures/peru_exposure_context_maps", legacy)
        self.assertIn("outputs/v1_full_methodology_evidence_sweep", legacy)
        self.assertIn("outputs/v1_multicriteria_evidence_package", legacy)
        self.assertIn("outputs/v1_terrain_mentor_package", legacy)
        self.assertIn("outputs/study_area_location_map", legacy)
        self.assertIn("outputs/mentor_boundary_decision", legacy)
        slide_files = {str(path) for path in module.LEGACY_SLIDE_FILES}
        self.assertIn("outputs/slide_ready_figures/equal_ahp_hotspot_overlay_summary.csv", slide_files)

    def test_active_checks_do_not_recreate_archived_report_directories(self):
        active = load_module("check_active_terminology_governance", ACTIVE_TERMINOLOGY)
        project = load_module("check_project_terminology_governance", PROJECT_TERMINOLOGY)
        glossary = load_module("check_glossary_sources_governance", GLOSSARY_CHECK)

        self.assertEqual(active.DEFAULT_OUTPUT.parent.name, "project_checks")
        self.assertEqual(project.DEFAULT_OUTPUT.parent.name, "project_checks")
        self.assertEqual(project.DEFAULT_SUMMARY.parent.name, "project_checks")
        self.assertEqual(glossary.DEFAULT_OUTPUT.parent.name, "project_checks")
        active_dirs = {str(path.relative_to(ROOT)) for path in active.ACTIVE_OUTPUT_DIRS}
        self.assertIn("outputs/peru_report_figure_chain", active_dirs)
        self.assertNotIn("outputs/mentor_boss_priority_explanation", active_dirs)
        self.assertNotIn("outputs/zimbabwe_peru_prototype_comparison", active_dirs)

    def test_environmental_summary_writer_creates_the_new_output_directory(self):
        module = load_module("build_pim_environmental_sensitivity_governance", ENVIRONMENTAL_BUILDER)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "pim_environmental_sensitivity" / "summary.csv"
            module.write_csv(target, [{"site": "test", "value": 1}])
            self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
