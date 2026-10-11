import importlib
import unittest

import numpy as np


class PeruOptimizedLandChangeSensitivityTest(unittest.TestCase):
    def _load_module(self):
        try:
            return importlib.import_module(
                "bin.scenarios.run_peru_former_optimized_land_change_sensitivity"
            )
        except ModuleNotFoundError:
            self.fail("optimized land-change sensitivity runner has not been implemented")

    def test_valid_aware_focal_density_does_not_dilute_boundary_edges(self):
        module = self._load_module()
        valid = np.zeros((5, 5), dtype=bool)
        valid[:3, :3] = True
        presence = valid.astype("float32")

        density = module.circular_focal_density(presence, valid, radius_cells=2)

        np.testing.assert_allclose(density[valid], np.ones(valid.sum(), dtype="float32"))
        self.assertTrue(np.isnan(density[~valid]).all())

    def test_positive_density_normalization_preserves_zero_and_clips_tail(self):
        module = self._load_module()
        density = np.array([[0.0, 0.1, 0.2, 1.0, np.nan]], dtype="float32")

        normalized, scale = module.normalize_positive_density(density, percentile=50.0)

        self.assertAlmostEqual(scale, 0.2, places=6)
        np.testing.assert_allclose(
            normalized[0, :4],
            np.array([0.0, 0.5, 1.0, 1.0], dtype="float32"),
        )
        self.assertTrue(np.isnan(normalized[0, 4]))

    def test_positive_density_normalization_ignores_fft_roundoff_noise(self):
        module = self._load_module()
        density = np.array(
            [[0.0, 1e-9, 0.1, 0.2, 1.0, np.nan]],
            dtype="float32",
        )

        normalized, scale = module.normalize_positive_density(density, percentile=50.0)

        self.assertAlmostEqual(scale, 0.2, places=6)
        self.assertEqual(float(normalized[0, 1]), 0.0)

    def test_nominal_metric_radii_map_to_nearest_30m_cells(self):
        module = self._load_module()

        result = [module.radius_m_to_cells(radius, 30.0) for radius in (500, 1000, 2000)]

        self.assertEqual(result, [17, 33, 67])


if __name__ == "__main__":
    unittest.main()
