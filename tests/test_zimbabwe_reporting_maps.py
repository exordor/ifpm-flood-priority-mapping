from __future__ import annotations

import csv
import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/visualize/export_zimbabwe_reporting_maps.py"


def load_module():
    spec = importlib.util.spec_from_file_location("export_zimbabwe_reporting_maps", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_named_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ZimbabweReportingMapsTest(unittest.TestCase):
    def test_zimbabwe_pim_uses_independent_sediment_components_and_direct_weights(self):
        scenario = load_named_module(
            ROOT / "bin/scenarios/run_boundary_v1_rainfall_exposure.py",
            "run_boundary_v1_rainfall_exposure_for_governance_test",
        )

        self.assertEqual(
            scenario.PIM_CRITERIA_ORDER,
            ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"],
        )
        self.assertEqual(
            scenario.PIM_COMPONENTS["sediment"],
            {"soil_k_factor": 0.35, "ls_factor": 0.35, "c_factor": 0.30},
        )
        self.assertNotIn("soil_erosion_factors", scenario.COMPONENT_PATHS)
        self.assertEqual(scenario.SCENARIO_ID, "mentor_zimbabwe_direct_pim")
        self.assertAlmostEqual(sum(scenario.ZIMBABWE_MENTOR_MAIN_WEIGHTS.values()), 1.0)

    def test_sediment_requires_common_k_ls_c_support(self):
        scenario = load_named_module(
            ROOT / "bin/scenarios/run_boundary_v1_rainfall_exposure.py",
            "run_boundary_v1_rainfall_exposure_for_nodata_test",
        )
        components = {
            "soil_k_factor": np.array([[0.2, np.nan, 0.2]], dtype="float32"),
            "ls_factor": np.array([[0.4, 0.4, np.nan]], dtype="float32"),
            "c_factor": np.array([[0.6, 0.6, 0.6]], dtype="float32"),
        }

        sediment = scenario.combine_weighted_layers(
            components,
            scenario.PIM_COMPONENTS["sediment"],
        )

        self.assertAlmostEqual(float(sediment[0, 0]), 0.39, places=6)
        self.assertTrue(np.isnan(sediment[0, 1]))
        self.assertTrue(np.isnan(sediment[0, 2]))

    def test_current_scenario_outputs_are_declared_and_hash_bound(self):
        scenario = load_named_module(
            ROOT / "bin/scenarios/run_boundary_v1_rainfall_exposure.py",
            "run_boundary_v1_rainfall_exposure_for_manifest_test",
        )

        for path in scenario.OUTPUTS:
            self.assertTrue(path.exists(), path)
        with scenario.RUN_MANIFEST.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        manifest_paths = {row["path"] for row in rows}
        for path in scenario.OUTPUTS:
            if path != scenario.RUN_MANIFEST:
                self.assertIn(scenario.rel(path), manifest_paths)
        self.assertIn(scenario.rel(Path(scenario.__file__)), manifest_paths)

    def test_reporting_scope_uses_only_direct_weights_and_fixed_classes(self):
        module = load_module()

        self.assertEqual(
            module.WEIGHTS,
            {
                "flood_hazard": 0.32,
                "sediment": 0.23,
                "landuse_asm": 0.18,
                "environmental": 0.12,
                "socioeconomic": 0.15,
            },
        )
        self.assertAlmostEqual(sum(module.WEIGHTS.values()), 1.0)
        output_text = " ".join(str(path).lower() for path in module.OUTPUTS)
        self.assertNotIn("top20", output_text)
        self.assertNotIn("top_20", output_text)
        self.assertNotIn("equal", output_text)

    def test_five_criteria_have_traceable_data_strength_rows(self):
        module = load_module()

        rows = module.data_strength_rows()
        self.assertEqual([row["criterion"] for row in rows], list(module.CRITERIA))
        self.assertEqual(len(rows), 5)
        for row in rows:
            self.assertIn(row["evidence_strength"], {"medium", "medium-low", "low"})
            self.assertTrue(row["data_sources"])
            self.assertTrue(row["main_limitation"])
            self.assertIn(row["claim_level"], {"diagnostic_only", "provisional", "sensitivity_scenario"})

    def test_cross_site_reporting_palettes_match_peru(self):
        module = load_module()
        peru_criteria = load_named_module(
            ROOT / "bin/visualize/export_peru_pim_criteria_maps.py",
            "export_peru_pim_criteria_maps_for_palette_test",
        )
        peru_contribution = load_named_module(
            ROOT / "bin/visualize/export_peru_pim_contribution_map.py",
            "export_peru_pim_contribution_map_for_palette_test",
        )

        peru_colors = {criterion.slug: tuple(criterion.colors) for criterion in peru_criteria.CRITERIA}
        self.assertEqual(list(module.CRITERIA), [criterion.slug for criterion in peru_criteria.CRITERIA])
        self.assertEqual(
            {name: criterion.colors for name, criterion in module.CRITERIA.items()},
            peru_colors,
        )
        self.assertEqual(module.CONTRIBUTION_COLORS, peru_contribution.COLORS)
        self.assertEqual(module.maps.PRIORITY_COLORS, ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"])

    def test_direct_pim_matches_five_criterion_weighted_sum(self):
        module = load_module()

        layers, profile = module.read_criteria()
        priority, pim_profile = module.maps.read_raster(module.PIM)
        module.assert_same_grid(profile, pim_profile, "PIM")
        common = np.ones(priority.shape, dtype=bool)
        expected = np.zeros(priority.shape, dtype="float32")
        for name, layer in layers.items():
            common &= np.isfinite(layer)
            expected += np.nan_to_num(layer, nan=0.0) * module.WEIGHTS[name]
        self.assertTrue(np.array_equal(np.isfinite(priority), common))
        self.assertLess(float(np.max(np.abs(priority[common] - expected[common]))), 2e-6)

    def test_current_inputs_build_reporting_chain(self):
        module = load_module()

        module.main()

        for path in module.OUTPUTS:
            self.assertTrue(path.exists(), path)
            self.assertGreater(path.stat().st_size, 0, path)
        with module.INDEX.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 16)
        self.assertEqual({row["claim_level"] for row in rows}, {"sensitivity_scenario"})
        self.assertEqual(
            {row["classification"] for row in rows},
            {
                "study area context",
                "equal interval 0-1, five classes",
                "categorical argmax of five weighted criterion contributions",
            },
        )
        self.assertEqual({row["palette_id"] for row in rows}, {module.PALETTE_ID})


if __name__ == "__main__":
    unittest.main()
