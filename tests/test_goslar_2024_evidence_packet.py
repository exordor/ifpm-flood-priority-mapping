import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/analysis/build_goslar_2024_evidence_packet.py"
PYTHON = ROOT / ".venv/bin/python"


class Goslar2024EvidencePacketTest(unittest.TestCase):
    def test_builds_source_anchored_evidence_and_scope_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            completed = subprocess.run(
                [str(PYTHON), str(SCRIPT), "--output-dir", str(output), "--skip-previews"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with (output / "event_evidence.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertGreaterEqual(len(rows), 6)
            self.assertTrue(all(row["source_id"] for row in rows))
            self.assertTrue(all(row["enters_pim_score"] == "false" for row in rows))
            self.assertIn("focus_area_extent", {row["evidence_type"] for row in rows})
            self.assertIn("historical_event_reference", {row["evidence_type"] for row in rows})
            scope = json.loads((output / "spatial_scope_check.json").read_text(encoding="utf-8"))
            self.assertEqual(scope["focus_area_id"], "goslar_harz_2024_focus_extent")
            self.assertFalse(scope["inside_current_peru_boundary"])
            self.assertGreater(scope["distance_to_peru_boundary_km"], 10000)
            self.assertEqual(scope["claim_level"], "diagnostic_only")


if __name__ == "__main__":
    unittest.main()
