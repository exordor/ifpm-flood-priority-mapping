"""Each area's rerun (python -m ifpm run <area>) matches the current outputs.

An area is skipped unless outputs/_rerun/<area> exists.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ifpm.config import areas  # noqa: E402


class RegressionTest(unittest.TestCase):
    def test_reruns_match_current_outputs(self):
        from ifpm.verify import verify
        for area in areas():
            rerun = ROOT / "outputs" / "_rerun" / area
            with self.subTest(area=area):
                if not rerun.is_dir():
                    self.skipTest(f"no rerun at {rerun}")
                self.assertTrue(verify(area, rerun), "see the table above for failing files")


if __name__ == "__main__":
    unittest.main()
