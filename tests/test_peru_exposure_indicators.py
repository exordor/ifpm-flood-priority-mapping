from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
from rasterio.transform import from_origin


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bin/criteria/build_peru_exposure_indicators.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_peru_exposure_indicators", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PeruExposureIndicatorsTest(unittest.TestCase):
    def test_robust_normalize_preserves_nodata_and_clips_upper_tail(self):
        module = load_module()
        values = np.array([[0.0, 1.0, 3.0, 1000.0, np.nan]], dtype="float32")

        result, upper = module.robust_normalize(values, upper_percentile=75.0, log1p=True)

        self.assertTrue(np.isnan(result[0, 4]))
        self.assertEqual(float(result[0, 0]), 0.0)
        self.assertEqual(float(result[0, 3]), 1.0)
        self.assertTrue(0.0 < float(result[0, 1]) < float(result[0, 2]) < 1.0)
        self.assertGreater(upper, 0.0)

    def test_weighted_complete_case_keeps_any_component_nodata(self):
        module = load_module()
        first = np.array([[0.0, 1.0], [0.5, np.nan]], dtype="float32")
        second = np.array([[1.0, 0.0], [np.nan, 0.5]], dtype="float32")
        boundary = np.array([[True, True], [True, False]])

        result = module.combine_weighted_complete_case(
            {"first": first, "second": second},
            {"first": 0.25, "second": 0.75},
            boundary,
        )

        np.testing.assert_allclose(result[0], np.array([0.75, 0.25], dtype="float32"))
        self.assertTrue(np.isnan(result[1, 0]))
        self.assertTrue(np.isnan(result[1, 1]))

    def test_normalize_name_matches_inei_district_spelling(self):
        module = load_module()

        self.assertEqual(module.normalize_name("Vítor"), "VITOR")
        self.assertEqual(module.normalize_name("Santa  Rita de Siguas"), "SANTA RITA DE SIGUAS")

    def test_health_remoteness_increases_with_distance_and_preserves_mask(self):
        module = load_module()
        presence = np.zeros((5, 5), dtype=bool)
        presence[2, 2] = True
        boundary = np.ones((5, 5), dtype=bool)
        boundary[0, 0] = False

        result = module.health_remoteness_from_presence(
            presence,
            boundary,
            pixel_size_m=1000.0,
            max_distance_m=3000.0,
        )

        self.assertEqual(float(result[2, 2]), 0.0)
        self.assertGreater(float(result[2, 3]), float(result[2, 2]))
        self.assertGreater(float(result[2, 4]), float(result[2, 3]))
        self.assertLessEqual(float(np.nanmax(result)), 1.0)
        self.assertTrue(np.isnan(result[0, 0]))

    def test_reference_bbox_is_converted_without_geoseries_from_bbox(self):
        module = load_module()
        profile = {
            "crs": "EPSG:32718",
            "width": 2,
            "height": 2,
            "transform": from_origin(800000.0, 8200000.0, 30.0, 30.0),
        }

        bbox = module.reference_bbox_wgs84(profile)

        self.assertEqual(len(bbox), 4)
        self.assertLess(bbox[0], bbox[2])
        self.assertLess(bbox[1], bbox[3])
        self.assertTrue(all(np.isfinite(value) for value in bbox))

    def test_padded_bbox_expands_in_all_directions(self):
        module = load_module()
        profile = {
            "crs": "EPSG:32718",
            "width": 2,
            "height": 2,
            "transform": from_origin(800000.0, 8200000.0, 30.0, 30.0),
        }

        base = module.reference_bbox_wgs84(profile)
        padded = module.reference_bbox_wgs84(profile, padding_m=20000.0)

        self.assertLess(padded[0], base[0])
        self.assertLess(padded[1], base[1])
        self.assertGreater(padded[2], base[2])
        self.assertGreater(padded[3], base[3])

    def test_circular_focal_density_excludes_square_corners(self):
        module = load_module()
        presence = np.zeros((7, 7), dtype="float32")
        presence[3, 3] = 1.0

        density = module.circular_focal_density(presence, radius_cells=2)

        self.assertGreater(float(density[3, 3]), 0.0)
        self.assertGreater(float(density[3, 5]), 0.0)
        self.assertAlmostEqual(float(density[1, 1]), 0.0, places=6)

    def test_component_diagnostics_separate_prevalence_from_spatial_variability(self):
        module = load_module()
        valid = np.ones((2, 2), dtype=bool)
        layers = {
            "road": np.array([[0.8, 0.9], [0.8, 0.9]], dtype="float32"),
            "infrastructure": np.array([[0.0, 0.0], [0.0, 1.0]], dtype="float32"),
        }
        weights = {"road": 0.45, "infrastructure": 0.55}

        rows = module.component_influence_diagnostics(layers, weights, valid)

        self.assertEqual({row["component"] for row in rows}, set(layers))
        self.assertAlmostEqual(
            sum(float(row["realized_mean_contribution_share"]) for row in rows),
            1.0,
        )
        self.assertAlmostEqual(
            sum(float(row["marginal_weighted_sd_share"]) for row in rows),
            1.0,
        )
        self.assertTrue(all("not ranking attribution" in row["interpretation"] for row in rows))


if __name__ == "__main__":
    unittest.main()
