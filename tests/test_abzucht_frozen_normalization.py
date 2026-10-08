from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from analysis.abzucht_frozen_normalization import apply, fit
from _lib.standardization import percentile_minmax


class FrozenNormalizationTest(unittest.TestCase):
    def test_expansion_does_not_shift_original_scores(self):
        baseline = np.arange(101, dtype=float)
        parameters = json.loads(json.dumps(fit(baseline), allow_nan=False))
        expanded = np.concatenate([baseline, [-1e9, 1e9]])
        result = apply(expanded, parameters)
        expected, _, _ = percentile_minmax(baseline)
        np.testing.assert_array_equal(result[:101], expected)
        np.testing.assert_array_equal(result[-2:], [0, 1])
        self.assertEqual((parameters["clip_low"], parameters["clip_high"]), (2, 98))

    def test_valid_support_and_inversion(self):
        values = np.array([0, 50, 100, -9999, np.nan, np.inf, 1e6])
        mask = np.array([True] * 6 + [False])
        parameters = fit(values, mask, nodata=-9999, invert=True)
        self.assertEqual(parameters["baseline_valid_cells"], 3)
        result = apply(values, parameters, mask, nodata=-9999, output_nodata=-9999)
        np.testing.assert_array_equal(result, [1, .5, 0, -9999, -9999, -9999, -9999])

    def test_constant_contracts_remain_frozen(self):
        with self.assertRaises(ValueError):
            fit([7, 7])
        zeros = fit([7, 7], constant_policy="zeros", invert=True)
        np.testing.assert_array_equal(apply([7, 8, np.nan], zeros), [0, 0, np.nan])
        expanded = fit([7, 7], constant_policy="expand", invert=True)
        np.testing.assert_array_equal(apply([7, 7.5, 8], expanded), [1, .5, 0])

    def test_rejects_missing_bounds_and_invalid_support(self):
        parameters = fit([0, 1])
        with self.assertRaises(ValueError):
            fit([np.nan, -9999], nodata=-9999)
        with self.assertRaises(ValueError):
            apply([np.nan], parameters)
        with self.assertRaises(ValueError):
            apply([0, 1], parameters, [True])
        del parameters["clip_low"]
        with self.assertRaises(KeyError):
            apply([0, 1], parameters)


if __name__ == "__main__":
    unittest.main()
