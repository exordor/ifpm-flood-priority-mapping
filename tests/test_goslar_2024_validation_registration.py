import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/acquire/register_goslar_2024_focus_area_sources.py"


class Goslar2024FocusAreaRegistrationTest(unittest.TestCase):
    def test_registers_three_source_files_with_checksums(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--register"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        manifest = json.loads(completed.stdout)
        self.assertEqual(manifest["focus_area_id"], "goslar_harz_2024_focus_extent")
        self.assertEqual(manifest["claim_level"], "validation_candidate")
        self.assertFalse(manifest["enters_pim_score"])
        self.assertEqual(len(manifest["sources"]), 3)
        source_ids = {source["source_id"] for source in manifest["sources"]}
        self.assertEqual(source_ids, {"qgis_project", "zlw_catchment_map_pdf", "zdin_study_area_slide"})
        for source in manifest["sources"]:
            self.assertEqual(len(source["sha256"]), 64)
            self.assertTrue(Path(source["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
