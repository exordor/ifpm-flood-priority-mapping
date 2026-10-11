"""ifpm.rescore: the combination rules, and the frozen peru_former pins."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ifpm import rescore  # noqa: E402
from ifpm.config import Config  # noqa: E402

FROZEN = ROOT / "outputs/peru_former_pim_chain/FROZEN_BASELINE.json"


class CombineTest(unittest.TestCase):
    def test_criterion_needs_every_component(self):
        a = np.array([[1.0, np.nan]], dtype="float32")
        b = np.array([[0.5, 0.5]], dtype="float32")
        out = rescore.combine({"a": a, "b": b}, {"a": .4, "b": .6}, divide_by_total=False)
        self.assertAlmostEqual(float(out[0, 0]), .7, places=6)
        self.assertTrue(np.isnan(out[0, 1]))

    def test_score_has_no_weight_renormalization(self):
        x = np.array([[1.0, 1.0]], dtype="float32")
        y = np.array([[1.0, np.nan]], dtype="float32")
        score, available, count = rescore.score_common_support({"x": x, "y": y}, {"x": .3, "y": .7})
        self.assertAlmostEqual(float(score[0, 0]), 1.0, places=6)
        self.assertTrue(np.isnan(score[0, 1]))
        self.assertAlmostEqual(float(available[0, 1]), .3, places=6)
        self.assertEqual(count.tolist(), [[2, 1]])

    def test_unit_interval_max_scales_absolute_layers(self):
        np.testing.assert_allclose(rescore.ensure_unit_interval(np.array([0., 5., 10.])), [0, .5, 1])


@unittest.skipUnless(FROZEN.exists(), "frozen peru_former outputs not present")
class FrozenPeruTest(unittest.TestCase):
    def test_rescore_reproduces_the_pinned_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            # check_pins raises SystemExit when the rescored raster or a frozen file differs.
            rescore.run_rescore(Config("peru_former"), "arequipa", Path(tmp))


if __name__ == "__main__":
    unittest.main()
