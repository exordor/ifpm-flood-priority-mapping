from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bin/scenarios/run_peru_former_priority_scenarios.py"
PIPELINE_PATH = ROOT / "bin/pipeline.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_peru_former_priority_scenarios", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PeruHybasL76070641200SocioeconomicIntegrationTest(unittest.TestCase):
    def test_scenario_runner_uses_supervisor_three_way_socioeconomic_split(self):
        """On this branch the runner reads road/population/CI components directly
        instead of the upstream pre-blended exposure_indicators raster."""

        module = load_module()

        # The pre-blended key is gone; three components replace it.
        self.assertNotIn("exposure_indicators", module.COMPONENT_PATHS)
        self.assertEqual(
            module.PIM_COMPONENTS["socioeconomic"],
            {"road_access_proximity": 0.35, "settlement_population": 0.35, "critical_infrastructure": 0.30},
        )
        self.assertIn("road_access_proximity", module.COMPONENT_PATHS)
        self.assertIn("settlement_population", module.COMPONENT_PATHS)
        self.assertIn("critical_infrastructure", module.COMPONENT_PATHS)

    def test_only_mentor_peru_direct_scenario_is_active(self):
        module = load_module()

        self.assertEqual(set(module.SCENARIOS), {"mentor_peru_direct_pim"})
        self.assertEqual(module.MENTOR_PERU_MAIN_WEIGHTS["socioeconomic"], 0.14)
        output_names = {path.name for path in module.OUTPUTS}
        self.assertNotIn("priority_equal_active_pim.tif", output_names)
        self.assertNotIn("top20_equal_active_pim.tif", output_names)
        self.assertNotIn("priority_std.tif", output_names)

    def test_subcriteria_manifest_records_supervisor_socioeconomic_split(self):
        module = load_module()
        rows = [
            row
            for row in module.build_subcriteria_weight_rows()
            if row["pim_criterion"] == "socioeconomic"
        ]
        weights = {row["component"]: row["applied_weight_in_current_run"] for row in rows}

        self.assertEqual(weights["road_access_proximity"], 0.35)
        self.assertEqual(weights["settlement_population"], 0.35)
        self.assertEqual(weights["critical_infrastructure"], 0.30)
        # CI is honestly labelled as a built-density proxy.
        ci_row = next(row for row in rows if row["component"] == "critical_infrastructure")
        self.assertEqual(ci_row["implementation_status"], "implemented_as_built_density_proxy")

    def test_pipeline_dag_runs_exposure_builder_before_scenarios(self):
        spec = importlib.util.spec_from_file_location("ifpm_pipeline", PIPELINE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module: {PIPELINE_PATH}")
        pipeline = importlib.util.module_from_spec(spec)
        sys.modules["ifpm_pipeline"] = pipeline
        spec.loader.exec_module(pipeline)

        scripts = pipeline.discover_scripts()
        dependencies = pipeline.build_dag(scripts)

        self.assertIn("build_peru_former_exposure_indicators", dependencies["run_peru_former_priority_scenarios"])

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

        self.assertNotIn("download_peru_former_worldpop_population_subset", selected)
        self.assertNotIn("query_peru_former_sernanp_protected_areas", selected)
        self.assertNotIn("derive_peru_former_soilgrids_kfactor", selected)
        self.assertNotIn("build_peru_former_rainfall_criterion", selected)
        self.assertNotIn("run_zimbabwe_rainfall_exposure", selected)
        self.assertIn("build_peru_former_exposure_indicators", selected)
        self.assertIn("run_peru_former_priority_scenarios", selected)

        self.assertIn("build_peru_former_rainfall_criterion", config["network_scripts"])
        stale_tokens = (
            "peru_former_pim_chain/priority_scenarios/priority_mean.tif",
            "peru_former_pim_chain/priority_scenarios/top20_frequency.tif",
            "peru_former_pim_chain/criteria_stack/criteria/soil_erosion_factors_0_1.tif",
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

        self.assertEqual(selected, {"run_peru_former_priority_scenarios"})


if __name__ == "__main__":
    unittest.main()
