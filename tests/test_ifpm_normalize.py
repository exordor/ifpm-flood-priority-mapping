"""ifpm.normalize on small synthetic arrays (NumPy only), checked against bin/_lib/standardization.py while it exists."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bin"))

from ifpm.normalize import Normalizer, apply, fit, percentile_minmax  # noqa: E402

try:  # the old helpers exist until the bin/ scripts are removed
    from _lib import standardization as old_standardization
except ImportError:
    old_standardization = None


def sample(seed=0, shape=(40, 50)):
    rng = np.random.default_rng(seed)
    data = rng.gamma(2.0, 3.0, shape).astype("float32")
    data[rng.random(shape) < .05] = np.nan
    mask = np.ones(shape, dtype=bool)
    mask[:5] = False
    return data, mask


class PercentileMinmaxTest(unittest.TestCase):
    def test_range_mask_and_nodata(self):
        data, mask = sample()
        out, low, high = percentile_minmax(data, mask)
        self.assertEqual(out.dtype, np.float32)
        self.assertTrue(np.isnan(out[~mask]).all())
        self.assertTrue(np.isnan(out[np.isnan(data)]).all())
        self.assertEqual(float(np.nanmin(out)), 0.0)
        self.assertEqual(float(np.nanmax(out)), 1.0)
        values = data[mask & np.isfinite(data)].astype("float64")
        self.assertEqual(low, float(np.percentile(values, 2)))
        self.assertEqual(high, float(np.percentile(values, 98)))

    def test_invert(self):
        data, mask = sample(1)
        plain, _, _ = percentile_minmax(data, mask)
        inverted, _, _ = percentile_minmax(data, mask, invert=True)
        valid = np.isfinite(plain)
        np.testing.assert_allclose(inverted[valid], 1 - plain[valid], atol=1e-7)

    def test_constant_policies(self):
        data = np.full((3, 3), 4.0, dtype="float32")
        with self.assertRaises(ValueError):
            percentile_minmax(data)
        zeros, _, _ = percentile_minmax(data, constant_policy="zeros")
        self.assertTrue((zeros == 0).all())
        expanded, low, high = percentile_minmax(data, constant_policy="expand")
        self.assertEqual(high, low + 1)

    @unittest.skipIf(old_standardization is None, "bin/_lib not present")
    def test_identical_to_old_helper(self):
        for seed in range(3):
            data, mask = sample(seed)
            for options in [{}, {"invert": True}, {"nodata": -9999.0}, {"constant_policy": "zeros"}]:
                new = percentile_minmax(data, mask, **options)
                old = old_standardization.percentile_minmax(data, mask, **options)
                np.testing.assert_array_equal(new[0], old[0])
                self.assertEqual(new[1:], old[1:])


class FixedScaleTest(unittest.TestCase):
    def test_frozen_anchors_reproduce_baseline_and_clip_extension(self):
        data, mask = sample(2)
        anchors = fit(data, mask)
        baseline, _, _ = percentile_minmax(data, mask)
        np.testing.assert_array_equal(apply(data, anchors, mask), baseline)
        # A larger extent with higher values is clipped at the baseline anchors.
        bigger = np.concatenate([data, data * 10])
        out = apply(bigger, anchors, np.concatenate([mask, mask]))
        self.assertEqual(float(np.nanmax(out)), 1.0)
        np.testing.assert_array_equal(out[:data.shape[0]], baseline)


class NormalizerTest(unittest.TestCase):
    def test_record_then_frozen_uses_stage_call_keys(self):
        data, mask = sample(4)
        recorder = Normalizer("record")
        recorder.start("criteria_stack")
        first, _, _ = recorder(data, mask)
        second, _, _ = recorder(data, mask, invert=True)
        self.assertEqual(sorted(recorder.anchors), ["criteria_stack:0", "criteria_stack:1"])
        frozen = Normalizer("frozen", recorder.anchors)
        frozen.start("criteria_stack")
        np.testing.assert_array_equal(frozen(data * 3, mask)[0], apply(data * 3, recorder.anchors["criteria_stack:0"], mask))
        np.testing.assert_array_equal(frozen(data, mask)[0], second)  # options come from the anchor
        with self.assertRaises(KeyError):
            frozen(data, mask)

    def test_fit_mode_is_plain_percentile_minmax(self):
        data, mask = sample(5)
        n = Normalizer()
        n.start("rainfall")
        np.testing.assert_array_equal(n(data, mask)[0], percentile_minmax(data, mask)[0])


if __name__ == "__main__":
    unittest.main()
