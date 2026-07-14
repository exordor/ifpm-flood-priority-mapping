from __future__ import annotations

import csv
import importlib.util
import sys
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/package/build_zimbabwe_integrated_briefing_board.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_zimbabwe_integrated_briefing_board", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ZimbabweIntegratedBriefingBoardTest(unittest.TestCase):
    def test_board_scope_excludes_equal_and_top20(self):
        module = load_module()

        text = SCRIPT.read_text(encoding="utf-8").lower()
        self.assertNotIn("top20", text)
        self.assertNotIn("top 20", text)
        self.assertNotIn("equal weight", text)

    def test_current_inputs_build_board_and_manifest(self):
        module = load_module()

        self.assertEqual(
            module.FIGURES["priority"].name,
            "08_zimbabwe_priority_mining_population_overlay.png",
        )

        module.main()

        with Image.open(module.OUT_PNG) as image:
            self.assertEqual(image.size, (3600, 2400))
        with module.OUT_MANIFEST.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        roles = {row["role"] for row in rows}
        self.assertIn("integrated_briefing_board_png", roles)
        self.assertIn("zimbabwe_figure_chain_manifest", roles)
        self.assertIn("criterion_data_strength", roles)
        self.assertIn("governed_figure_priority", roles)
        priority_row = next(row for row in rows if row["role"] == "governed_figure_priority")
        self.assertIn("mining_population_overlay", priority_row["path"])
        self.assertEqual(
            next(row for row in rows if row["role"] == "integrated_briefing_board_png")["claim_level"],
            "sensitivity_scenario",
        )

    def test_summary_uses_current_fixed_class_and_contribution_results(self):
        module = load_module()

        summary = module.summary_values()
        self.assertAlmostEqual(summary["high_area_km2"], 50.1336, places=4)
        self.assertAlmostEqual(summary["very_high_area_km2"], 0.0063, places=4)
        self.assertAlmostEqual(summary["coverage_fraction"], 0.96609, places=6)
        self.assertAlmostEqual(summary["high_share"], 50.1336 / 3565.422, places=8)
        self.assertAlmostEqual(summary["flood_dominant_share"], 0.9304492147, places=8)


if __name__ == "__main__":
    unittest.main()
