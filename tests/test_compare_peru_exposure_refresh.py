from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bin/analysis/compare_peru_exposure_refresh.py"


def load_module():
    spec = importlib.util.spec_from_file_location("compare_peru_exposure_refresh", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PeruExposureRefreshComparisonTest(unittest.TestCase):
    def test_compare_arrays_uses_common_valid_cells_and_separate_thresholds(self):
        module = load_module()
        before = np.array([[0.0, 0.2, 0.8], [1.0, np.nan, 0.4]], dtype="float32")
        after = np.array([[0.1, 0.3, 0.9], [0.7, 0.5, np.nan]], dtype="float32")

        result = module.compare_arrays(before, after, percentile=75.0)

        self.assertEqual(result["common_valid_cells"], 4)
        self.assertAlmostEqual(result["mean_absolute_change"], 0.15, places=6)
        self.assertGreater(result["spearman_rank_correlation"], 0.0)
        self.assertEqual(result["before_top_cells"], 1)
        self.assertEqual(result["after_top_cells"], 1)
        self.assertEqual(result["top_cell_intersection"], 0)
        self.assertEqual(result["top_cell_union"], 2)
        self.assertEqual(result["top_cell_jaccard"], 0.0)


if __name__ == "__main__":
    unittest.main()
