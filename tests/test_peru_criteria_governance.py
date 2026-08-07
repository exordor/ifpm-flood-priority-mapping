from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
LOCAL_GOVERNANCE_OUTPUTS_READY = all(
    path.exists()
    for path in (
        ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/flood_hazard_0_1.tif",
        ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_screening_summary.csv",
        ROOT / "outputs/peru_gap_closure_analysis/peru_sinpad_colocation_cohorts.csv",
    )
) and "marginal_weighted_sd_share" in (
    ROOT
    / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_contribution_diagnostics.csv"
).read_text(encoding="utf-8")
LOCAL_SOIL_K_SOURCE_READY = (
    ROOT / "outputs/soilgrids_250m_peru_pilot/k_factor_peru_hybas_l7_6070641200_0_5cm_250m.tif"
).exists()


def load_module(relative_path: str, module_name: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class PeruCriteriaGovernanceTest(unittest.TestCase):
    def test_run_manifest_does_not_capture_unrelated_worktree_paths(self):
        module = load_module(
            "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py",
            "run_peru_hybas_l7_6070641200_priority_scenarios_git_state_governance",
        )

        state = module.git_state()

        self.assertNotIn("changed_paths", state)
        self.assertIn("dirty", state)

    def test_current_peru_summary_is_not_named_as_hotspot_stability(self):
        module = load_module(
            "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py",
            "run_peru_hybas_l7_6070641200_priority_scenarios_summary_name_governance",
        )

        output_names = {path.name for path in module.OUTPUTS}
        self.assertIn("priority_screening_summary.csv", output_names)
        self.assertNotIn("hotspot_stability_summary.csv", output_names)

    def test_current_criteria_stack_does_not_depend_on_legacy_klsc_composite(self):
        module = load_module(
            "bin/criteria/build_peru_hybas_l7_6070641200_criteria_stack.py",
            "build_peru_hybas_l7_6070641200_criteria_stack_no_legacy_composite",
        )

        self.assertNotIn("structure", module.INPUTS)
        self.assertFalse(
            any(path.name == "soil_erosion_factors_0_1.tif" for path in module.OUTPUTS)
        )

    def test_road_access_component_is_not_named_as_the_combined_exposure_criterion(self):
        stack = load_module(
            "bin/criteria/build_peru_hybas_l7_6070641200_criteria_stack.py",
            "build_peru_hybas_l7_6070641200_criteria_stack_road_name_governance",
        )
        exposure = load_module(
            "bin/criteria/build_peru_exposure_indicators.py",
            "build_peru_exposure_indicators_road_name_governance",
        )

        output_names = {path.name for path in stack.OUTPUTS}
        self.assertIn("road_access_proximity_0_1.tif", output_names)
        self.assertNotIn("exposure_indicators_0_1.tif", output_names)
        self.assertEqual(exposure.ROAD_ACCESS.name, "road_access_proximity_0_1.tif")

        scenarios = load_module(
            "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py",
            "run_peru_hybas_l7_6070641200_priority_scenarios_road_lineage_governance",
        )
        road_row = next(
            row
            for row in scenarios.build_subcriteria_weight_rows()
            if row["component"] == "road_access_proximity"
        )
        self.assertTrue(str(road_row["source_layer"]).endswith("road_access_proximity_0_1.tif"))

        conditioning = load_module(
            "bin/visualize/export_peru_conditioning_factor_maps.py",
            "export_peru_conditioning_factor_maps_road_name_governance",
        )
        road_factor = next(item for item in conditioning.FACTORS if item.slug == "road_access")
        self.assertEqual(road_factor.source_raster.name, "road_access_proximity_0_1.tif")

    def test_active_pipeline_scripts_declare_complete_freshness_boundaries(self):
        pipeline = load_module("bin/pipeline.py", "ifpm_pipeline_io_governance")
        scripts = {item.name: item for item in pipeline.discover_scripts()}

        stack = scripts["build_peru_hybas_l7_6070641200_criteria_stack"]
        self.assertIn(
            ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif",
            stack.inputs,
        )
        self.assertIn(
            ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
            stack.inputs,
        )

        environmental = scripts["build_pim_environmental_sensitivity"]
        self.assertGreaterEqual(len(environmental.inputs), 7)
        self.assertGreaterEqual(len(environmental.outputs), 6)

        package = scripts["build_peru_report_figure_chain"]
        self.assertGreaterEqual(len(package.inputs), 21)
        self.assertGreaterEqual(len(package.outputs), 22)

    def test_rainfall_normalization_uses_boundary_only_and_masks_outside(self):
        module = load_module(
            "bin/criteria/build_peru_hybas_l7_6070641200_rainfall_criterion.py",
            "build_peru_hybas_l7_6070641200_rainfall_criterion_governance",
        )
        values = np.array(
            [[1000.0, 10.0, 20.0], [1000.0, 30.0, 40.0]],
            dtype="float32",
        )
        inside = np.array(
            [[False, True, True], [False, True, True]],
            dtype=bool,
        )

        score, low, high = module.normalize_within_boundary(values, inside)

        self.assertTrue(np.isnan(score[:, 0]).all())
        self.assertEqual(float(np.nanmin(score)), 0.0)
        self.assertEqual(float(np.nanmax(score)), 1.0)
        self.assertLess(low, high)
        self.assertLess(high, 1000.0)

    def test_rainfall_edge_fill_masks_outside_when_no_holes_exist(self):
        module = load_module(
            "bin/criteria/build_peru_hybas_l7_6070641200_rainfall_criterion.py",
            "build_peru_hybas_l7_6070641200_rainfall_criterion_mask",
        )
        values = np.arange(9, dtype="float32").reshape(3, 3)
        inside = np.array(
            [[False, False, False], [False, True, False], [False, False, False]],
            dtype=bool,
        )

        result, stats = module.fill_edge_nodata(values, inside)

        self.assertEqual(stats["hole_cells"], 0)
        self.assertEqual(float(result[1, 1]), 4.0)
        self.assertTrue(np.isnan(result[~inside]).all())

    def test_environmental_peru_uses_official_sernanp_protected_areas(self):
        module = load_module(
            "bin/criteria/build_pim_environmental_sensitivity.py",
            "build_pim_environmental_sensitivity_governance",
        )
        peru = next(config for config in module.SITES if config.site == "Peru")

        self.assertEqual(
            peru.protected_vectors,
            (
                (
                    ROOT
                    / "data/raw/sernanp_peru_protected_areas/peru_hybas_l7_6070641200_sernanp_protected_areas.gpkg",
                    "sernanp_protected_areas",
                ),
            ),
        )

    def test_environmental_default_execution_is_peru_only(self):
        module = load_module(
            "bin/criteria/build_pim_environmental_sensitivity.py",
            "build_pim_environmental_sensitivity_active_sites",
        )

        self.assertEqual(
            [config.site for config in module.active_site_configs()],
            ["Peru"],
        )

    def test_environmental_distinguishes_verified_absence_from_missing_source(self):
        module = load_module(
            "bin/criteria/build_pim_environmental_sensitivity.py",
            "build_pim_environmental_sensitivity_evidence_state",
        )

        self.assertEqual(
            module.vector_evidence_state(features_in_context=0, raw_features=2),
            "sernanp_national_definitive_layer_checked_no_feature_within_context_zone",
        )
        self.assertEqual(
            module.vector_evidence_state(features_in_context=0, raw_features=0),
            "source_returned_no_features",
        )

        boundary = module.gpd.GeoDataFrame(
            geometry=module.gpd.points_from_xy([0.0], [0.0]),
            crs="EPSG:4326",
        )
        with self.assertRaises(FileNotFoundError):
            module.read_vector_features(
                ((ROOT / "data/raw/__missing_environmental_source__.gpkg", None),),
                boundary,
                "EPSG:4326",
                buffer_m=5000,
            )

    def test_land_use_pressure_has_its_own_worldcover_value_function(self):
        module = load_module(
            "bin/factors/derive_peru_pilot_worldcover_cfactor.py",
            "derive_peru_pilot_worldcover_governance",
        )
        classes = np.array([[40, 50, 60, 80]], dtype="int32")

        land_use = module.class_to_land_use_pressure(classes)
        c_factor = module.class_to_c(classes)

        np.testing.assert_allclose(
            land_use,
            np.array([[0.8, 1.0, 0.25, 0.0]], dtype="float32"),
        )
        self.assertFalse(np.array_equal(land_use, c_factor))

    def test_sediment_uses_supplied_k_ls_c_subweights(self):
        module = load_module(
            "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py",
            "run_peru_hybas_l7_6070641200_priority_scenarios_sediment_governance",
        )

        self.assertEqual(
            module.PIM_COMPONENTS["sediment"],
            {"soil_k_factor": 0.25, "ls_factor": 0.50, "c_factor": 0.25},
        )

        rows = [
            row
            for row in module.build_subcriteria_weight_rows()
            if row["pim_criterion"] == "sediment"
        ]
        self.assertEqual(
            {
                row["component"]: row["applied_weight_in_current_run"]
                for row in rows
            },
            {"soil_k_factor": 0.25, "ls_factor": 0.50, "c_factor": 0.25},
        )
        self.assertTrue(
            all(row["implementation_status"] == "implemented" for row in rows)
        )

    def test_sediment_requires_common_k_ls_c_support(self):
        module = load_module(
            "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py",
            "run_peru_hybas_l7_6070641200_priority_scenarios_sediment_nodata_governance",
        )
        layers = {
            "soil_k_factor": np.array([[1.0, np.nan]], dtype="float32"),
            "ls_factor": np.array([[np.nan, 0.5]], dtype="float32"),
            "c_factor": np.array([[0.0, 0.5]], dtype="float32"),
        }

        result = module.combine_weighted_layers(
            layers,
            module.PIM_COMPONENTS["sediment"],
        )

        self.assertTrue(np.isnan(result).all())

    def test_pim_requires_common_five_criterion_support_and_records_evidence(self):
        module = load_module(
            "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py",
            "run_peru_hybas_l7_6070641200_priority_scenarios_main_nodata_governance",
        )
        criteria = {
            "flood_hazard": np.array([[0.8, np.nan]], dtype="float32"),
            "sediment": np.array([[np.nan, 0.4]], dtype="float32"),
            "landuse_asm": np.array([[0.4, 0.4]], dtype="float32"),
            "environmental": np.array([[0.2, 0.2]], dtype="float32"),
            "socioeconomic": np.array([[0.6, 0.6]], dtype="float32"),
        }

        score, available_weight, evidence_count = module.combine_common_support_criteria(
            criteria,
            module.MENTOR_PERU_MAIN_WEIGHTS,
        )

        self.assertTrue(np.isnan(score).all())
        self.assertAlmostEqual(float(available_weight[0, 0]), 0.75, places=6)
        self.assertEqual(int(evidence_count[0, 0]), 4)

    def test_support_class_distinguishes_ls_k_and_other_missing_evidence(self):
        module = load_module(
            "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py",
            "run_peru_hybas_l7_6070641200_priority_scenarios_support_class_governance",
        )
        components = {
            "soil_k_factor": np.array([[0.2, 0.2, np.nan, 0.2]], dtype="float32"),
            "ls_factor": np.array([[0.2, np.nan, 0.2, 0.2]], dtype="float32"),
            "c_factor": np.array([[0.2, 0.2, 0.2, 0.2]], dtype="float32"),
        }
        criteria = {
            "flood_hazard": np.array([[0.2, 0.2, 0.2, np.nan]], dtype="float32"),
            "sediment": np.array([[0.2, np.nan, np.nan, 0.2]], dtype="float32"),
            "landuse_asm": np.full((1, 4), 0.2, dtype="float32"),
            "environmental": np.full((1, 4), 0.2, dtype="float32"),
            "socioeconomic": np.full((1, 4), 0.2, dtype="float32"),
        }
        boundary = np.ones((1, 4), dtype=bool)

        support = module.classify_evidence_support(components, criteria, boundary)

        np.testing.assert_array_equal(support, np.array([[1, 2, 3, 4]], dtype="uint8"))

    @unittest.skipUnless(
        LOCAL_GOVERNANCE_OUTPUTS_READY,
        "requires ignored local governance outputs",
    )
    def test_data_strength_table_describes_the_five_current_criteria(self):
        module = load_module(
            "bin/analysis/summarize_peru_criterion_data_strength.py",
            "summarize_peru_criterion_data_strength_governance",
        )

        rows = module.build_rows()
        by_criterion = {row["criterion_id"]: row for row in rows}

        self.assertEqual(
            set(by_criterion),
            {"flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"},
        )
        self.assertIn("0.30 SoilGrids K", by_criterion["sediment"]["implementation"])
        self.assertNotIn("K x LS x C composite", by_criterion["sediment"]["implementation"])
        self.assertIn("dedicated mining evidence excluded", by_criterion["landuse_asm"]["implementation"])
        self.assertEqual(
            by_criterion["environmental"]["evidence_state"],
            "sernanp_national_definitive_layer_checked_no_feature_within_context_zone",
        )
        self.assertEqual(by_criterion["flood_hazard"]["validation_state"], "not validated")
        self.assertIn("conditioning", by_criterion["flood_hazard"]["display_name"].lower())
        self.assertIn("not an event-extreme", by_criterion["flood_hazard"]["known_limit"])
        self.assertIn("context", by_criterion["environmental"]["display_name"].lower())
        self.assertIn("indicator", by_criterion["socioeconomic"]["display_name"].lower())
        self.assertIn("SINPAD", by_criterion["flood_hazard"]["model_level_diagnostic"])
        self.assertIn("marginal weighted SD share", by_criterion["socioeconomic"]["known_limit"])
        self.assertIn(
            "Spearman rho",
            by_criterion["landuse_asm"]["dependency_sensitivity_diagnostic"],
        )
        self.assertIn(
            "water/wetland",
            by_criterion["environmental"]["dependency_sensitivity_diagnostic"],
        )
        self.assertTrue(all(row["validation_state"] != "validated" for row in rows))

    def test_report_criterion_labels_preserve_framework_ids_but_expose_indicators(self):
        criteria_maps = load_module(
            "bin/visualize/export_peru_pim_criteria_maps.py",
            "export_peru_pim_criteria_maps_semantic_governance",
        )
        contribution = load_module(
            "bin/visualize/export_peru_pim_contribution_map.py",
            "export_peru_pim_contribution_map_semantic_governance",
        )
        labels = {item.slug: item.label for item in criteria_maps.CRITERIA}

        self.assertIn("conditioning", labels["flood_hazard"].lower())
        self.assertIn("context", labels["environmental"].lower())
        self.assertIn("indicator", labels["socioeconomic"].lower())
        self.assertEqual(
            contribution.LABELS["environmental"],
            "Environmental context indicator (ES)",
        )

    def test_sinpad_diagnostic_separates_scored_and_unscored_support_causes(self):
        module = load_module(
            "bin/analysis/compare_peru_pim_sinpad_colocation.py",
            "compare_peru_pim_sinpad_colocation_governance",
        )
        frame = module.gpd.GeoDataFrame(
            {
                "pim_score": [0.7, 0.8, 0.4],
                "in_top20_priority_cells": [True, False, False],
                "evidence_support_class": [1, 2, 3],
            }
        )
        frame.loc[1:, "pim_score"] = np.nan

        row = module.summarize_cohort("test", frame, selected_area_fraction=0.2)

        self.assertEqual(row["valid_pim_count"], 1)
        self.assertEqual(row["unscored_count"], 2)
        self.assertEqual(row["unscored_ls_missing_count"], 1)
        self.assertEqual(row["unscored_k_missing_count"], 1)
        self.assertEqual(row["selected_area_fraction"], 0.2)
        self.assertNotIn("uniform_null", row)

    def test_contribution_map_only_explains_cells_in_the_final_pim_support(self):
        module = load_module(
            "bin/visualize/export_peru_pim_contribution_map.py",
            "export_peru_pim_contribution_map_governance",
        )
        layers = {
            "flood_hazard": np.array([[0.8]], dtype="float32"),
            "sediment": np.array([[np.nan]], dtype="float32"),
            "landuse_asm": np.array([[0.4]], dtype="float32"),
            "environmental": np.array([[0.2]], dtype="float32"),
            "socioeconomic": np.array([[0.6]], dtype="float32"),
        }
        scoreable = np.array([[False]], dtype=bool)

        contributions = module.weighted_contribution_stack(
            layers,
            module.WEIGHTS,
            scoreable,
        )

        self.assertTrue(np.isnan(contributions[:, 0, 0]).all())

    def test_dependency_diagnostic_quantifies_rank_and_top_quintile_change(self):
        module = load_module(
            "bin/analysis/summarize_peru_criterion_dependency.py",
            "summarize_peru_criterion_dependency_governance",
        )
        reference = np.array([[0.1, 0.2, 0.8, 0.9]], dtype="float32")
        candidate = np.array([[0.1, 0.3, 0.7, 0.95]], dtype="float32")

        pair = module.pair_metrics(reference, candidate, max_samples=100)
        sensitivity = module.pim_alternative_metrics(
            reference,
            current_component=np.zeros_like(reference),
            alternative_component=np.array([[0.0, 0.0, 1.0, 1.0]], dtype="float32"),
            main_weight=0.1,
            max_samples=100,
        )

        self.assertAlmostEqual(pair["spearman_rho"], 1.0)
        self.assertEqual(pair["common_cell_count"], 4)
        self.assertGreater(sensitivity["mean_abs_difference"], 0.0)
        self.assertGreaterEqual(sensitivity["top_quintile_jaccard"], 0.0)
        self.assertLessEqual(sensitivity["top_quintile_jaccard"], 1.0)

    def test_soil_k_normalization_preserves_boundary_and_spans_unit_interval(self):
        module = load_module(
            "bin/criteria/build_peru_hybas_l7_6070641200_soil_k_factor.py",
            "build_peru_hybas_l7_6070641200_soil_k_factor_governance",
        )
        values = np.array(
            [[100.0, 0.10, 0.20], [100.0, 0.30, 0.40]],
            dtype="float32",
        )
        inside = np.array(
            [[False, True, True], [False, True, True]],
            dtype=bool,
        )

        score, low, high = module.normalize_within_boundary(values, inside)

        self.assertTrue(np.isnan(score[:, 0]).all())
        self.assertEqual(float(np.nanmin(score)), 0.0)
        self.assertEqual(float(np.nanmax(score)), 1.0)
        self.assertLess(low, high)

    @unittest.skipUnless(LOCAL_SOIL_K_SOURCE_READY, "requires ignored local SoilGrids source")
    def test_soilgrids_window_uses_the_vrt_crs_for_peru_hybas_l7_6070641200_location(self):
        module = load_module(
            "bin/factors/derive_peru_pilot_soilgrids_kfactor.py",
            "derive_peru_pilot_soilgrids_location_governance",
        )
        import rasterio
        from pyproj import Transformer

        source = ROOT / "outputs/soilgrids_250m_peru_pilot/k_factor_peru_hybas_l7_6070641200_0_5cm_250m.tif"
        with rasterio.open(source) as dataset:
            bounds = module.peru_hybas_l7_6070641200_bounds_in_source_crs(dataset.crs)
            transformer = Transformer.from_crs(dataset.crs, "EPSG:4326", always_xy=True)

        center_x = (bounds[0] + bounds[2]) / 2.0
        center_y = (bounds[1] + bounds[3]) / 2.0
        longitude, latitude = transformer.transform(center_x, center_y)

        self.assertAlmostEqual(longitude, -71.9479, delta=0.2)
        self.assertAlmostEqual(latitude, -16.4979, delta=0.2)

    def test_soilgrids_source_window_is_not_prematurely_clipped_to_peru_hybas_l7_6070641200(self):
        module = load_module(
            "bin/factors/derive_peru_pilot_soilgrids_kfactor.py",
            "derive_peru_pilot_soilgrids_support_governance",
        )
        k = np.array([[0.1, 0.2], [0.3, 0.4]], dtype="float32")
        source_invalid = np.array([[False, False], [True, False]])
        peru_hybas_l7_6070641200_mask = np.array([[False, True], [True, False]])

        result = module.preserve_source_window_support(k, source_invalid)

        self.assertAlmostEqual(float(result[0, 0]), 0.1)
        self.assertAlmostEqual(float(result[1, 1]), 0.4)
        self.assertTrue(np.isnan(result[1, 0]))
        self.assertFalse(peru_hybas_l7_6070641200_mask[0, 0])


if __name__ == "__main__":
    unittest.main()
