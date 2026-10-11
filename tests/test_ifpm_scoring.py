"""ifpm.scoring on small synthetic arrays (NumPy only)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ifpm import scoring  # noqa: E402

WEIGHTS = {"flood_hazard": .34, "sediment": .22, "landuse_asm": .16, "environmental": .14, "socioeconomic": .14}


def criteria(seed=0, shape=(30, 30)):
    rng = np.random.default_rng(seed)
    layers = {k: rng.random(shape).astype("float32") for k in WEIGHTS}
    layers["sediment"][rng.random(shape) < .1] = np.nan
    return layers


class WeightedAverageTest(unittest.TestCase):
    def test_renormalizes_over_valid_components(self):
        mask = np.array([[True, True, False]])
        a = np.array([[1.0, np.nan, 1.0]], dtype="float32")
        b = np.array([[0.0, 0.5, 0.0]], dtype="float32")
        out = scoring.weighted_average([(a, .75), (b, .25)], mask)
        self.assertEqual(out.dtype, np.float32)
        self.assertAlmostEqual(float(out[0, 0]), .75, places=6)
        self.assertAlmostEqual(float(out[0, 1]), .5, places=6)  # only b valid
        self.assertTrue(np.isnan(out[0, 2]))  # outside mask

    def test_strict_sum_needs_every_component(self):
        layers = criteria()
        mask = np.ones((30, 30), dtype=bool)
        out = scoring.strict_sum(layers, WEIGHTS, mask)
        np.testing.assert_array_equal(np.isnan(out), np.isnan(layers["sediment"]))
        self.assertTrue(np.nanmax(out) <= 1)


class CommonSupportTest(unittest.TestCase):
    def test_score_coverage_and_count(self):
        layers = criteria(1)
        mask = np.ones((30, 30), dtype=bool)
        score, available, count = scoring.combine_common_support(layers, WEIGHTS, mask)
        missing = np.isnan(layers["sediment"])
        self.assertTrue(np.isnan(score[missing]).all())
        np.testing.assert_allclose(available[missing], 1 - WEIGHTS["sediment"], atol=1e-6)
        self.assertTrue((count[missing] == 4).all() and (count[~missing] == 5).all())
        expected = sum(layers[k].astype("float64") * w for k, w in WEIGHTS.items())
        np.testing.assert_allclose(score[~missing], expected[~missing], atol=1e-6)


class AlternativeWeightsTest(unittest.TestCase):
    def test_weights_at_keeps_ratios_and_sum(self):
        w = scoring.weights_at(WEIGHTS, .6)
        self.assertAlmostEqual(sum(w.values()), 1.0)
        self.assertEqual(w["flood_hazard"], .6)
        self.assertAlmostEqual(w["sediment"] / w["landuse_asm"], WEIGHTS["sediment"] / WEIGHTS["landuse_asm"])
        with self.assertRaises(ValueError):
            scoring.weights_at(WEIGHTS, 1.5)


class ClassTest(unittest.TestCase):
    def test_class_edges_include_one(self):
        pim = np.array([0, .19, .2, .59, .6, .99, 1.0], dtype="float32")
        valid = np.ones(pim.shape, dtype=bool)
        table = scoring.class_table(pim, valid, cell_area_km2=.0009)
        self.assertEqual([table[k]["cells"] for k in scoring.CLASS_LABELS], [2, 1, 1, 1, 2])
        self.assertAlmostEqual(sum(v["fraction_of_valid"] for v in table.values()), 1.0)
        s = scoring.summarize(pim, valid)
        self.assertEqual(s["class_counts"], [2, 1, 1, 1, 2])
        self.assertAlmostEqual(s["high_share"], 3 / 7)  # .6, .99, 1.0


if __name__ == "__main__":
    unittest.main()
