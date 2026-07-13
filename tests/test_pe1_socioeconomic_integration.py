from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bin/scenarios/run_pe1_priority_scenarios.py"
PIPELINE_PATH = ROOT / "bin/pipeline.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_pe1_priority_scenarios", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Pe1SocioeconomicIntegrationTest(unittest.TestCase):
    def test_scenario_runner_uses_upgraded_exposure_indicators(self):
        module = load_module()

        self.assertEqual(
            module.COMPONENT_PATHS["exposure_indicators"],
            ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_0_1.tif",
        )
        self.assertEqual(module.PIM_COMPONENTS["socioeconomic"], {"exposure_indicators": 1.0})

    def test_only_mentor_peru_direct_scenario_is_active(self):
        module = load_module()

        self.assertEqual(set(module.SCENARIOS), {"mentor_peru_direct_pim"})
        self.assertEqual(module.MENTOR_PERU_MAIN_WEIGHTS["socioeconomic"], 0.08)
        output_names = {path.name for path in module.OUTPUTS}
        self.assertNotIn("priority_equal_active_pim.tif", output_names)
        self.assertNotIn("top20_equal_active_pim.tif", output_names)
        self.assertNotIn("priority_std.tif", output_names)

    def test_subcriteria_manifest_records_supplied_socioeconomic_split(self):
        module = load_module()
        rows = [
            row
            for row in module.build_subcriteria_weight_rows()
            if row["pim_criterion"] == "socioeconomic"
        ]
        weights = {row["component"]: row["applied_weight_in_current_run"] for row in rows}

        self.assertEqual(weights["road_access_proximity"], 0.45)
        self.assertEqual(weights["infrastructure_exposure"], 0.55)
        self.assertFalse(any("only available component" in str(row.get("note", "")) for row in rows))

    def test_pipeline_dag_runs_exposure_builder_before_scenarios(self):
        spec = importlib.util.spec_from_file_location("ifpm_pipeline", PIPELINE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module: {PIPELINE_PATH}")
        pipeline = importlib.util.module_from_spec(spec)
        sys.modules["ifpm_pipeline"] = pipeline
        spec.loader.exec_module(pipeline)

        scripts = pipeline.discover_scripts()
        dependencies = pipeline.build_dag(scripts)

        self.assertIn("build_peru_exposure_indicators", dependencies["run_pe1_priority_scenarios"])

    def test_pipeline_dag_runs_scenarios_before_exposure_and_colocation_analysis(self):
        spec = importlib.util.spec_from_file_location("ifpm_pipeline_analysis", PIPELINE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module: {PIPELINE_PATH}")
        pipeline = importlib.util.module_from_spec(spec)
        sys.modules["ifpm_pipeline_analysis"] = pipeline
        spec.loader.exec_module(pipeline)

        dependencies = pipeline.build_dag(pipeline.discover_scripts())

        for target in (
            "summarize_peru_population_by_pim_class",
            "compare_peru_pim_sinpad_colocation",
        ):
            self.assertIn("run_pe1_priority_scenarios", dependencies[target])

    def test_default_pipeline_excludes_network_and_one_off_refresh_steps(self):
        spec = importlib.util.spec_from_file_location("ifpm_pipeline_default", PIPELINE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module: {PIPELINE_PATH}")
        pipeline = importlib.util.module_from_spec(spec)
        sys.modules["ifpm_pipeline_default"] = pipeline
        spec.loader.exec_module(pipeline)

        scripts = pipeline.discover_scripts()
        dependencies = pipeline.build_dag(scripts)
        config = pipeline._load_config(ROOT / "pipeline.yaml")
        selected = {item.name for item in pipeline.scripts_for_config(scripts, dependencies, config)}

        self.assertTrue(config["include"])
        self.assertEqual(selected, set(config["include"]))

        self.assertNotIn("download_peru_worldpop_population_subset", selected)
        self.assertNotIn("query_peru_sinpad_flood_events", selected)
        self.assertNotIn("query_peru_sernanp_protected_areas", selected)
        self.assertNotIn("derive_peru_pilot_soilgrids_kfactor", selected)
        self.assertNotIn("build_pe1_rainfall_criterion", selected)
        self.assertNotIn("compare_peru_exposure_refresh", selected)
        self.assertNotIn("derive_peru_pilot_usle_soil_loss", selected)
        self.assertNotIn("export_peru_conditioning_factor_maps", selected)
        self.assertNotIn("plot_zimbabwe_peru_prototype_comparison", selected)
        self.assertNotIn("plot_july18_integrated_priority_board", selected)
        self.assertNotIn("plot_mentor_boss_priority_explanation_package", selected)
        self.assertNotIn("run_boundary_v1_priority_scenarios", selected)
        self.assertNotIn("run_boundary_v1_rainfall_exposure", selected)
        self.assertNotIn("run_boundary_v1_rainfall_sensitivity", selected)
        self.assertNotIn("diagnose_boundary_v1_hotspot_exposure", selected)
        self.assertNotIn("run_v1_mining_decay_priority_sensitivity", selected)
        self.assertNotIn("write_zimbabwe_peru_source_tables", selected)
        self.assertIn("build_peru_exposure_indicators", selected)
        self.assertIn("run_pe1_priority_scenarios", selected)
        self.assertIn("summarize_peru_criterion_data_strength", selected)

        self.assertIn("build_pe1_rainfall_criterion", config["network_scripts"])
        stale_tokens = (
            "srtm_1arcsec_peru_pilot/priority_scenarios/priority_mean.tif",
            "srtm_1arcsec_peru_pilot/priority_scenarios/top20_frequency.tif",
            "srtm_1arcsec_peru_pilot/criteria_stack/criteria/soil_erosion_factors_0_1.tif",
        )
        for item in pipeline.scripts_for_config(scripts, dependencies, config):
            source = item.path.read_text(encoding="utf-8")
            self.assertFalse(
                any(token in source for token in stale_tokens),
                f"default pipeline selected stale Peru consumer: {item.name}",
            )

    def test_stage_execution_uses_the_same_default_allowlist(self):
        spec = importlib.util.spec_from_file_location("ifpm_pipeline_stage", PIPELINE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module: {PIPELINE_PATH}")
        pipeline = importlib.util.module_from_spec(spec)
        sys.modules["ifpm_pipeline_stage"] = pipeline
        spec.loader.exec_module(pipeline)

        scripts = pipeline.discover_scripts()
        dependencies = pipeline.build_dag(scripts)
        config = pipeline._load_config(ROOT / "pipeline.yaml")
        selected = {
            item.name
            for item in pipeline.scripts_for_stage(
                scripts,
                dependencies,
                config,
                "scenarios",
            )
        }

        self.assertEqual(selected, {"run_pe1_priority_scenarios"})


if __name__ == "__main__":
    unittest.main()
