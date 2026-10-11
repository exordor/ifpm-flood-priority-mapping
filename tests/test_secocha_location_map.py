import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
SCRIPT = ROOT / "bin/visualize/plot_secocha_location_map.py"


class PeruSecochaLocationMapTest(unittest.TestCase):
    def test_map_shows_active_secocha_and_frozen_previous_area(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            completed = subprocess.run(
                [str(PYTHON), str(SCRIPT), "--output-dir", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output / "peru_experiment_and_secocha_location_map.png").exists())
            manifest = json.loads(
                (output / "peru_experiment_and_secocha_location_map_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(manifest["areas_overlap"])
            self.assertAlmostEqual(manifest["nearest_distance_km"], 117.7, delta=1.0)
            self.assertEqual(
                manifest["active_boundary_id"], "secocha_reference_extent"
            )
            self.assertEqual(manifest["frozen_boundary_id"], "peru_former")
            self.assertEqual(manifest["secocha_area_role"], "active_A7367_map_extent_reference")
            self.assertFalse(manifest["secocha_extent_is_event_footprint"])
            self.assertFalse(manifest["secocha_extent_is_catchment"])
            self.assertEqual(manifest["claim_level"], "diagnostic_only")
            self.assertEqual(manifest.get("layout_overlap_count"), 0)


if __name__ == "__main__":
    unittest.main()
