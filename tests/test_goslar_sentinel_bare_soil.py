from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/acquire/pull_goslar_sentinel_bare_soil.py"


def load_module():
    if not SCRIPT.exists():
        raise AssertionError("Goslar Sentinel bare-soil acquisition module is missing")
    spec = importlib.util.spec_from_file_location("goslar_sentinel_bare_soil", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GoslarSentinelBareSoilTest(unittest.TestCase):
    def test_bare_soil_classifier_masks_cloud_and_separates_vegetation(self):
        """A cloud must never become zero-risk evidence or a bare observation."""
        module = load_module()
        blue = np.array([[0.10, 0.05, 0.10]], dtype="float32")
        red = np.array([[0.25, 0.05, 0.25]], dtype="float32")
        nir = np.array([[0.15, 0.50, 0.15]], dtype="float32")
        swir = np.array([[0.35, 0.10, 0.35]], dtype="float32")
        scl = np.array([[5, 4, 9]], dtype="uint8")

        bare, clear, mbi = module.classify_bare_soil(blue, red, nir, swir, scl)

        np.testing.assert_array_equal(bare, [[True, False, False]])
        np.testing.assert_array_equal(clear, [[True, True, False]])
        self.assertGreater(float(mbi[0, 0]), 0.0)
        self.assertLess(float(mbi[0, 1]), 0.0)
        self.assertTrue(np.isnan(mbi[0, 2]))

    def test_frequency_requires_minimum_clear_observations(self):
        """Sparse observations stay NoData instead of being interpreted as zero."""
        module = load_module()
        bare_count = np.array([[2, 0, 1]], dtype="uint16")
        clear_count = np.array([[5, 5, 2]], dtype="uint16")

        result = module.bare_frequency(bare_count, clear_count, minimum_clear=5)

        np.testing.assert_allclose(result[0, :2], [0.4, 0.0])
        self.assertTrue(np.isnan(result[0, 2]))

    def test_classifier_rejects_nonphysical_surface_reflectance(self):
        """Negative corrected reflectance must not create extreme indices."""
        module = load_module()
        blue = np.array([[-0.09, 0.10]], dtype="float32")
        red = np.array([[0.02, 0.25]], dtype="float32")
        nir = np.array([[0.03, 0.15]], dtype="float32")
        swir = np.array([[0.04, 0.35]], dtype="float32")
        scl = np.array([[5, 5]], dtype="uint8")

        bare, clear, mbi = module.classify_bare_soil(blue, red, nir, swir, scl)

        np.testing.assert_array_equal(clear, [[False, True]])
        np.testing.assert_array_equal(bare, [[False, True]])
        self.assertTrue(np.isnan(mbi[0, 0]))

    def test_ndvi_rejects_near_zero_denominator(self):
        """NDVI cannot be reported when tiny reflectance makes it unstable."""
        module = load_module()
        red = np.array([[0.001, 0.20]], dtype="float32")
        nir = np.array([[0.002, 0.60]], dtype="float32")
        clear = np.array([[True, True]])

        result = module.safe_ndvi(red, nir, clear)

        self.assertTrue(np.isnan(result[0, 0]))
        self.assertAlmostEqual(float(result[0, 1]), 0.5, places=6)

    def test_scene_choice_uses_distinct_dates(self):
        """Two processing revisions of one acquisition cannot count twice."""
        module = load_module()
        candidates = [
            {"id": "revision-a", "properties": {"datetime": "2025-04-01T10:00:00Z", "eo:cloud_cover": 0.1}},
            {"id": "revision-b", "properties": {"datetime": "2025-04-01T10:05:00Z", "eo:cloud_cover": 0.2}},
            {"id": "other-date", "properties": {"datetime": "2025-04-11T10:00:00Z", "eo:cloud_cover": 1.0}},
        ]

        selected = module.choose_distinct_dates(candidates, count=2)

        self.assertEqual([item["id"] for item in selected], ["revision-a", "other-date"])

    def test_collection_contract_rejects_old_processing_baseline(self):
        """Mixed pre-Collection-1 radiometry must fail before scoring."""
        module = load_module()
        feature = {"id": "old", "properties": {"s2:processing_baseline": "04.00"}}

        with self.assertRaisesRegex(ValueError, "processing baseline"):
            module.validate_scene_contract([feature])


if __name__ == "__main__":
    unittest.main()
