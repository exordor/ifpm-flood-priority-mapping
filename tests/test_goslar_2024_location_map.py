import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
SCRIPT = ROOT / "bin/visualize/plot_goslar_2024_location_map.py"


class Goslar2024LocationMapTest(unittest.TestCase):
    def test_map_shows_focus_area_and_layout(self):
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
            self.assertTrue((output / "goslar_focus_area_location_map.png").exists())
            manifest = json.loads(
                (output / "goslar_focus_area_location_map_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["focus_area_id"], "goslar_harz_2024_focus_extent")
            self.assertEqual(manifest["claim_level"], "diagnostic_only")
            self.assertEqual(manifest.get("layout_overlap_count"), 0)
            self.assertFalse(manifest["focus_extent_is_hazard_footprint"])


if __name__ == "__main__":
    unittest.main()
