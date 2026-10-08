from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/goslar_2017_satellite_validation"


def load_module():
    path = ROOT / "bin/acquire/pull_goslar_2017_sentinel2_validation.py"
    spec = importlib.util.spec_from_file_location("goslar_s2_validation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GoslarSentinel2ValidationTest(unittest.TestCase):
    def test_registry_and_outputs_exist(self):
        registry = ROOT / "context/docs/data-management/registry/goslar_2017_sentinel2_validation.md"
        self.assertTrue(registry.exists())
        for name in (
            "sentinel2_window_manifest.json",
            "water_change_qa.json",
            "new_surface_water_candidate_10m.tif",
            "persistent_water_candidate_10m.tif",
        ):
            self.assertTrue((OUT / name).exists(), name)

    def test_validation_candidate_does_not_enter_pim(self):
        qa = json.loads((OUT / "water_change_qa.json").read_text())
        self.assertEqual(qa["claim_level"], "validation_candidate")
        self.assertEqual(qa["dates"], {"before": "2017-07-21", "after": "2017-07-31"})
        self.assertGreater(qa["official_basin_pixels_10m"], 1_000_000)
        self.assertGreater(qa["before_water_px"], 0)
        self.assertGreater(qa["after_water_px"], qa["before_water_px"])
        self.assertGreater(qa["new_px"], 0)
        self.assertIn("not an official observed flood footprint", " ".join(qa["limitations"]))


if __name__ == "__main__":
    unittest.main()
