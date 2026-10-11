"""Goslar rerun (python -m ifpm run goslar) matches the current outputs.

Skipped unless outputs/_rerun/goslar exists; see the phase-2 Mac verification steps.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RERUN = ROOT / "outputs" / "_rerun" / "goslar"


@unittest.skipUnless(RERUN.is_dir(), f"no rerun at {RERUN}")
class GoslarRegressionTest(unittest.TestCase):
    def test_rerun_matches_current_outputs(self):
        from ifpm.verify import verify
        self.assertTrue(verify("goslar", RERUN), "see the table above for failing files")


if __name__ == "__main__":
    unittest.main()
