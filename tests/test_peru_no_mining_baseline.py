from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = ROOT / "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py"
ENVIRONMENT_PATH = ROOT / "bin/criteria/build_pim_environmental_sensitivity.py"
DEPENDENCY_PATH = ROOT / "bin/analysis/summarize_peru_criterion_dependency.py"
WORLDCOVER_PATH = ROOT / "bin/factors/derive_peru_pilot_worldcover_cfactor.py"
STACK_PATH = ROOT / "bin/criteria/build_peru_hybas_l7_6070641200_criteria_stack.py"


def load_scenarios():
    spec = importlib.util.spec_from_file_location("peru_no_mining_scenarios", SCENARIO_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCENARIO_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PeruNoMiningBaselineTest(unittest.TestCase):
    def test_current_baseline_uses_supervisor_weights_and_lc_bv_be(self):
        """Catches top-level redesign, missing LC/BV/BE, or mining re-entering PIM."""

        module = load_scenarios()
        components = {
            "rainfall_climatology": np.array([[0.1]], dtype="float32"),
            "twi_wetness": np.array([[0.2]], dtype="float32"),
            "drainage_proximity": np.array([[0.3]], dtype="float32"),
            "soil_k_factor": np.array([[0.4]], dtype="float32"),
            "ls_factor": np.array([[0.5]], dtype="float32"),
            "c_factor": np.array([[0.6]], dtype="float32"),
            "land_cover_pressure": np.array([[0.7]], dtype="float32"),
            "bare_soil_vegetation_loss": np.array([[0.4]], dtype="float32"),
            "built_agriculture_road_expansion": np.array([[0.2]], dtype="float32"),
            "water_wetland_context": np.array([[0.8]], dtype="float32"),
            "protected_ecological_context": np.array([[0.1]], dtype="float32"),
            "road_access_proximity": np.array([[0.2]], dtype="float32"),
            "settlement_population": np.array([[0.6]], dtype="float32"),
            "critical_infrastructure": np.array([[0.5]], dtype="float32"),
            # Deliberately extreme: this external overlay must not change the score.
            "mining_pressure": np.array([[1.0]], dtype="float32"),
        }

        criteria = module.calculate_pim_criteria(components)
        score, _, _ = module.combine_common_support_criteria(
            criteria,
            module.MENTOR_PERU_MAIN_WEIGHTS,
        )

        self.assertEqual(
            list(criteria),
            [
                "flood_hazard",
                "sediment",
                "landuse_asm",
                "environmental",
                "socioeconomic",
            ],
        )
        # FH = 0.35*0.1 + 0.25*0.2 + 0.40*0.3 = 0.205
        self.assertAlmostEqual(float(criteria["flood_hazard"][0, 0]), 0.205, places=6)
        # SE = 0.25*0.4 + 0.50*0.5 + 0.25*0.6 = 0.50
        self.assertAlmostEqual(float(criteria["sediment"][0, 0]), 0.50, places=6)
        # LU = 0.40*0.7 + 0.35*0.4 + 0.25*0.2 = 0.47
        self.assertAlmostEqual(float(criteria["landuse_asm"][0, 0]), 0.47, places=6)
        # ES = 0.65*0.8 + 0.35*0.1 = 0.555
        self.assertAlmostEqual(float(criteria["environmental"][0, 0]), 0.555, places=6)
        # SV = 0.35*0.2 + 0.35*0.6 + 0.30*0.5 = 0.43
        self.assertAlmostEqual(float(criteria["socioeconomic"][0, 0]), 0.43, places=6)
        # PIM = 0.34*0.205 + 0.25*0.50 + 0.17*0.47 + 0.10*0.555 + 0.14*0.43 = 0.3903
        self.assertAlmostEqual(float(score[0, 0]), 0.3903, places=4)

    def test_mining_is_external_to_current_component_contract(self):
        """Catches an active runner dependency on a mining raster."""

        module = load_scenarios()

        self.assertNotIn("mining_pressure", module.COMPONENT_PATHS)
        self.assertNotIn("mining_pressure", module.PIM_COMPONENTS["landuse_asm"])

        dependency = load_module(DEPENDENCY_PATH, "peru_no_mining_dependency")
        self.assertFalse(any("mining_pressure" in path.name for path in dependency.INPUTS))

        stack = load_module(STACK_PATH, "peru_no_mining_stack")
        output_names = {path.name for path in stack.OUTPUTS}
        self.assertIn("bare_soil_vegetation_loss_0_1.tif", output_names)
        self.assertIn("built_agriculture_road_expansion_0_1.tif", output_names)
        self.assertNotIn("mining_pressure_0_1.tif", output_names)

    def test_environmental_and_exposure_upstream_builders_unchanged(self):
        """The upstream pre-blended builders are reference-only on this branch;
        the runner recombines WW/PA and road/pop/CI directly. This test guards
        that the upstream contract has not drifted unexpectedly."""

        environmental = load_module(ENVIRONMENT_PATH, "peru_no_mining_environment")

        # Upstream ES builder still uses 0.60/0.40; the PIM overrides to 0.65/0.35.
        self.assertEqual(
            environmental.ENVIRONMENTAL_CONTEXT_WEIGHTS["Peru"],
            {"water_wetland_context": 0.60, "protected_ecological_context": 0.40},
        )

    def test_worldcover_value_functions_separate_lc_bv_and_be_inputs(self):
        """Catches LC/BV/BE collapsing back into one layer or using mining as a substitute."""

        module = load_module(WORLDCOVER_PATH, "peru_land_use_value_functions")
        classes = np.array([[10, 40, 50, 60]], dtype="int32")

        np.testing.assert_allclose(
            module.class_to_land_cover_runoff_pressure(classes),
            np.array([[0.15, 0.70, 1.00, 0.90]], dtype="float32"),
        )
        np.testing.assert_allclose(
            module.class_to_bare_soil_vegetation_loss_proxy(classes),
            np.array([[0.0, 0.0, 0.0, 1.0]], dtype="float32"),
        )
        np.testing.assert_allclose(
            module.class_to_built_up_pressure(classes),
            np.array([[0.0, 0.0, 1.0, 0.0]], dtype="float32"),
        )
        np.testing.assert_allclose(
            module.class_to_agricultural_pressure(classes),
            np.array([[0.0, 1.0, 0.0, 0.0]], dtype="float32"),
        )

    def test_be_proxy_combines_developed_land_family_with_road_access(self):
        """Catches the mutually exclusive built/agriculture classes suppressing BE below 1."""

        stack = load_module(STACK_PATH, "peru_be_proxy")
        built = np.array([[1.0, 0.0]], dtype="float32")
        agriculture = np.array([[0.0, 1.0]], dtype="float32")
        road = np.array([[1.0, 0.0]], dtype="float32")
        mask = np.array([[True, True]], dtype=bool)

        result = stack.build_be_proxy(built, agriculture, road, mask)

        np.testing.assert_allclose(result, np.array([[1.0, 0.5]], dtype="float32"))


if __name__ == "__main__":
    unittest.main()
