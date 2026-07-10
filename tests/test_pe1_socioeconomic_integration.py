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

    def test_only_equal_and_mentor_peru_scenarios_remain_active(self):
        module = load_module()

        self.assertEqual(set(module.SCENARIOS), {"equal_active_pim", "mentor_peru_direct_pim"})
        self.assertEqual(module.MENTOR_PERU_MAIN_WEIGHTS["socioeconomic"], 0.08)

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

        self.assertNotIn("download_peru_worldpop_population_subset", selected)
        self.assertNotIn("query_peru_sinpad_flood_events", selected)
        self.assertNotIn("compare_peru_exposure_refresh", selected)
        self.assertIn("build_peru_exposure_indicators", selected)
        self.assertIn("run_pe1_priority_scenarios", selected)


if __name__ == "__main__":
    unittest.main()
