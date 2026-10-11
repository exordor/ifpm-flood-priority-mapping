from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ZimbabweComparableFactorsTest(unittest.TestCase):
    def test_v1_soilgrids_uses_advertised_source_crs(self):
        path = ROOT / "bin/factors/derive_zimbabwe_soilgrids_kfactor.py"
        module = load_module("derive_zimbabwe_soilgrids_kfactor", path)
        source = path.read_text(encoding="utf-8")
        self.assertNotIn('SOILGRIDS_CRS = "ESRI:54017"', source)
        self.assertIn("source_window = window_from_bounds", source)
        self.assertIn("reproject(", source)
        bounds = module.v1_bounds_in_source_crs("ESRI:54052")
        self.assertEqual(len(bounds), 4)
        self.assertLess(bounds[0], bounds[2])
        self.assertLess(bounds[1], bounds[3])

    def test_v1_k_normalization_preserves_nodata(self):
        module = load_module("build_zimbabwe_soil_k_factor", ROOT / "bin/criteria/build_zimbabwe_soil_k_factor.py")
        data = np.array([[0.1, 0.2], [np.nan, 0.3]], dtype="float32")
        inside = np.ones((2, 2), dtype=bool)
        score, low, high = module.normalize_within_boundary(data, inside)
        self.assertTrue(np.isnan(score[1, 0]))
        self.assertLess(low, high)
        self.assertGreaterEqual(float(np.nanmin(score)), 0.0)
        self.assertLessEqual(float(np.nanmax(score)), 1.0)

    def test_williams_k_matches_reference_texture(self):
        module = load_module("derive_v1_soilgrids_kfactor_formula", ROOT / "bin/factors/derive_zimbabwe_soilgrids_kfactor.py")
        actual = float(module.williams_k(20.0, 40.0, 40.0, 2.0))
        self.assertAlmostEqual(actual, 0.2448597543, places=8)


if __name__ == "__main__":
    unittest.main()
