import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
SCRIPT = ROOT / "bin/visualize/plot_goslar_pim_overview.py"


class GoslarPimOverviewTest(unittest.TestCase):
    def test_builds_priority_and_criteria_overview(self):
        completed = subprocess.run(
            [str(PYTHON), str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        png = ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios/goslar_pim_overview.png"
        self.assertTrue(png.exists())
        manifest = json.loads(
            (ROOT / "outputs/srtm_1arcsec_goslar/priority_scenarios/goslar_pim_overview_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["claim_level"], "diagnostic_only")
        self.assertFalse(manifest["enters_pim_score"])
        self.assertEqual(manifest.get("layout_overlap_count"), 0)
        self.assertEqual(
            manifest["color_palettes"]["priority"],
            ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"],
        )
        self.assertEqual(
            manifest["color_palettes"]["flood_hazard"],
            ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
        )
        self.assertEqual(
            manifest["color_palettes"]["sediment"],
            ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
        )


if __name__ == "__main__":
    unittest.main()
