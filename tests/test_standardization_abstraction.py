from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from _lib.standardization import (  # noqa: E402
    ensure_unit_interval,
    percentile_minmax,
    positive_density_scale,
    robust_upper_scale,
)


class StandardizationAbstractionTest(unittest.TestCase):
    def test_percentile_minmax_uses_mask_and_preserves_outside_nodata(self):
        data = np.array([[1.0, 2.0, 100.0], [3.0, -9999.0, 4.0]], dtype="float32")
        mask = np.array([[True, True, False], [True, True, True]])

        result, low, high = percentile_minmax(
            data,
            mask,
            nodata=-9999.0,
            output_nodata=np.nan,
        )

        self.assertLess(low, high)
        self.assertTrue(np.isnan(result[0, 2]))
        self.assertTrue(np.isnan(result[1, 1]))
        self.assertEqual(float(np.nanmin(result)), 0.0)
        self.assertEqual(float(np.nanmax(result)), 1.0)

    def test_percentile_minmax_supports_inversion_and_constant_expansion(self):
        data = np.full((2, 2), 7.0, dtype="float32")
        result, low, high = percentile_minmax(
            data,
            invert=True,
            constant_policy="expand",
        )

        self.assertEqual((low, high), (7.0, 8.0))
        np.testing.assert_allclose(result, np.ones((2, 2), dtype="float32"))

    def test_robust_upper_scale_and_positive_density_keep_nan_contract(self):
        values = np.array([[0.0, 1.0, 3.0, 1000.0, np.nan]], dtype="float32")
        robust, upper = robust_upper_scale(values, upper_percentile=75.0, log1p=True)
        self.assertGreater(upper, 0.0)
        self.assertTrue(np.isnan(robust[0, 4]))
        self.assertEqual(float(robust[0, 3]), 1.0)

        density = np.array([[0.0, 1e-9, 0.1, 0.2, np.nan]], dtype="float32")
        scaled, scale = positive_density_scale(density, percentile=50.0)
        self.assertAlmostEqual(scale, 0.15, places=6)
        self.assertEqual(float(scaled[0, 0]), 0.0)
        self.assertEqual(float(scaled[0, 1]), 0.0)
        self.assertTrue(np.isnan(scaled[0, 4]))

    def test_ensure_unit_interval_is_only_legacy_compatibility_scaling(self):
        already_scaled = np.array([[0.0, 0.5, 1.0, np.nan]], dtype="float32")
        np.testing.assert_allclose(
            ensure_unit_interval(already_scaled), already_scaled, equal_nan=True
        )

        absolute = np.array([[0.0, 5.0, 10.0, np.nan]], dtype="float32")
        np.testing.assert_allclose(
            ensure_unit_interval(absolute),
            np.array([[0.0, 0.5, 1.0, np.nan]], dtype="float32"),
            equal_nan=True,
        )

    def test_active_scripts_do_not_redefine_numeric_standardizers(self):
        active_scripts = (
            ROOT / "bin/package/standardize_v1_hydrology.py",
            ROOT / "bin/criteria/build_v1_soil_k_factor.py",
            ROOT / "bin/criteria/build_peru_hybas_l7_6070641200_soil_k_factor.py",
            ROOT / "bin/criteria/build_peru_hybas_l7_6070641200_rainfall_criterion.py",
            ROOT / "bin/criteria/build_peru_hybas_l7_6070641200_criteria_stack.py",
            ROOT / "bin/factors/run_goslar_peru_style_chain.py",
            ROOT / "bin/criteria/build_peru_exposure_indicators.py",
            ROOT / "bin/scenarios/run_peru_optimized_land_change_sensitivity.py",
        )
        duplicate_names = (
            "standardize",
            "normalize_2_98",
            "normalize_within_boundary",
            "normalize_inverted",
            "robust_normalize",
            "normalize_positive_density",
        )
        for path in active_scripts:
            source = path.read_text(encoding="utf-8")
            for name in duplicate_names:
                self.assertNotIn(f"def {name}(", source, msg=str(path))


if __name__ == "__main__":
    unittest.main()
