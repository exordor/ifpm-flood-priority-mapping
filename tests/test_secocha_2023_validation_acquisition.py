import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/acquire/pull_secocha_2023_validation_reports.py"


class Secocha2023ValidationAcquisitionTest(unittest.TestCase):
    def test_transport_uses_system_curl_without_disabling_tls_verification(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--transport-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        transport = json.loads(completed.stdout)
        self.assertEqual(transport["executable"], "curl")
        self.assertIn("--fail", transport["arguments"])
        self.assertNotIn("--insecure", transport["arguments"])

    def test_catalog_declares_official_reports_and_validation_boundary(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--catalog-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        catalog = json.loads(completed.stdout)
        self.assertEqual(catalog["event_id"], "secocha_2023_historical_hazard_event")
        self.assertEqual(catalog["event_date"], "2023-02-05")
        self.assertEqual(catalog["claim_level"], "validation_candidate")
        self.assertFalse(catalog["enters_pim_score"])
        self.assertEqual(
            {source["publisher"] for source in catalog["sources"]},
            {"INGEMMET", "INDECI"},
        )
        self.assertTrue(all(source["url"].startswith("https://") for source in catalog["sources"]))


if __name__ == "__main__":
    unittest.main()
