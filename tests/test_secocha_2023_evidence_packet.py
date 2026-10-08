import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/analysis/build_secocha_2023_evidence_packet.py"


class Secocha2023EvidencePacketTest(unittest.TestCase):
    def test_builds_source_anchored_observations_without_pim_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--output-dir", str(output), "--skip-previews"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with (output / "event_evidence.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertGreaterEqual(len(rows), 8)
            self.assertTrue(all(row["source_page"] for row in rows))
            self.assertTrue(all(row["enters_pim_score"] == "false" for row in rows))
            self.assertIn("observed_hazard_footprint", {row["evidence_type"] for row in rows})
            self.assertIn("report_dated_impact", {row["evidence_type"] for row in rows})
            self.assertTrue((output / "ingemmet_field_anchors.geojson").exists())
            self.assertTrue((output / "indeci_response_locations.geojson").exists())
            response = json.loads((output / "indeci_response_locations.geojson").read_text(encoding="utf-8"))
            properties = response["features"][0]["properties"]
            self.assertEqual(properties.get("interpreted_crs"), "EPSG:4326")
            self.assertEqual(properties.get("coordinate_quality"), "candidate_requires_verification")


if __name__ == "__main__":
    unittest.main()
