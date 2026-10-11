from __future__ import annotations

import csv
import importlib.util
import json
import unittest
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/goslar_l2_independent_consistency"


def load_module():
    path = ROOT / "bin/analysis/goslar_l2_independent_consistency.py"
    spec = importlib.util.spec_from_file_location("goslar_l2_consistency", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GoslarL2IndependentConsistencyTest(unittest.TestCase):
    def test_outputs_and_registry_exist(self):
        for name in (
            "l2_consistency_report.json",
            "l2_consistency_summary.csv",
            "l2_consistency_summary.md",
        ):
            self.assertTrue((OUT / name).exists(), name)

    def test_report_keeps_l2_claim_boundary(self):
        report = json.loads((OUT / "l2_consistency_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["claim_level"], "independent_consistency_check")
        self.assertFalse(report["event_validation"])
        self.assertFalse(report["auc_iou_reported"])
        self.assertFalse(report["enters_pim_score"])
        self.assertIn("not event precision/recall/AUC/IoU evidence", report["prohibited_interpretation"])
        self.assertEqual(set(report["checks"]), {
            "hwrm_regulatory_context",
            "sentinel2_new_water_candidate",
            "flood_hazard_terrain_hydrology",
        })
        for check in report["checks"].values():
            self.assertIn(check["status"], {"consistent", "weakly_consistent", "inconsistent_or_unclear"})
        self.assertIn(report["overall_status"], {"consistent", "weakly_consistent", "mixed_or_unclear", "inconsistent_or_unclear"})

    def test_hwrm_context_is_not_event_validation(self):
        report = json.loads((OUT / "l2_consistency_report.json").read_text(encoding="utf-8"))
        check = report["checks"]["hwrm_regulatory_context"]
        self.assertEqual(check["independence"], "external regulatory scenario polygons; not PIM inputs")
        self.assertGreater(check["bands"][0]["cells"], 0)
        self.assertGreater(check["bands"][0]["bootstrap"]["difference"], 0)
        for band in check["bands"]:
            self.assertIn("modelled regulatory scenarios", band.get("interpretation", check["interpretation"]))
            self.assertIn("mean_pim_outside_all_hwrm_zones", band)
        self.assertNotIn("AUC", json.dumps(check))
        self.assertNotIn("IoU", json.dumps(check))

    def test_sentinel_check_resampling_and_claim_are_explicit(self):
        report = json.loads((OUT / "l2_consistency_report.json").read_text(encoding="utf-8"))
        check = report["checks"]["sentinel2_new_water_candidate"]
        self.assertEqual(check["resampling"]["native_resolution_m"], 10)
        self.assertEqual(check["resampling"]["method"], "average fraction of candidate 10 m cells per 30 m cell")
        self.assertGreater(check["cells"]["candidate"], 0)
        self.assertIn("five days post-peak", check["interpretation"])
        self.assertIn("bootstrap CI low >0", check["decision_rule"])

    def test_terrain_check_targets_flood_hazard_and_marks_internal(self):
        report = json.loads((OUT / "l2_consistency_report.json").read_text(encoding="utf-8"))
        check = report["checks"]["flood_hazard_terrain_hydrology"]
        self.assertEqual(check["target"], "flood_hazard_criterion")
        self.assertIn("internal/model-derived", check["independence"])
        self.assertGreater(check["correlations"]["distance_to_drainage"]["spearman_rho"] < 0, 0)
        for covariate in ("twi", "distance_to_drainage", "elevation", "slope"):
            self.assertEqual(len(check["mean_by_quartile"][covariate]), 4)
        self.assertIn("drainage rho<=-0.20", check["decision_rule"])

    def test_manifest_and_summary_are_linked_and_hashed(self):
        manifest = json.loads(
            (ROOT / "outputs/goslar_pim_chain/priority_scenarios/run_manifest.json").read_text(encoding="utf-8")
        )
        record = manifest["l2_independent_consistency"]
        self.assertEqual(record["claim_level"], "independent_consistency_check")
        self.assertFalse(record["event_validation"])
        self.assertFalse(record["auc_iou_reported"])
        report_path = ROOT / record["report"]
        summary_path = ROOT / record["summary_csv"]
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(record["overall_status"], report["overall_status"])
        self.assertEqual(
            record["pim_sha256"],
            hashlib.sha256(
                (ROOT / "outputs/goslar_pim_chain/priority_scenarios/scenarios/priority_goslar_direct_pim.tif").read_bytes()
            ).hexdigest(),
        )
        with summary_path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["event_validation"] == "no" for row in rows))
        self.assertTrue(all(row["enters_pim"] == "no" for row in rows))

    def test_standardization_workbook_records_l2_result_without_event_claim(self):
        try:
            from openpyxl import load_workbook
        except ImportError:
            self.skipTest("openpyxl is unavailable in this test environment")
        workbook_path = (
            ROOT
            / "outputs/secocha_pim_chain/priority_scenarios/figures/IFPM_Model_Audit.xlsx"
        )
        workbook = load_workbook(workbook_path, read_only=False, data_only=False)
        self.assertIn("L2 consistency", workbook.sheetnames)
        sheet = workbook["L2 consistency"]
        self.assertEqual(sheet.max_row, 7)
        self.assertEqual(sheet.max_column, 8)
        self.assertIn("GoslarL2Consistency", sheet.tables)
        text = "\n".join(
            str(cell.value)
            for row in sheet.iter_rows()
            for cell in row
            if cell.value is not None
        )
        self.assertIn("mixed_or_unclear", text)
        self.assertIn("not event-accuracy validation", text.lower())
        self.assertIn("no auc/iou", text.lower())
        sources = workbook["Data sources"]
        source_text = "\n".join(
            str(cell.value)
            for row in sources.iter_rows()
            for cell in row
            if cell.value is not None
        )
        self.assertIn("SRC-21", source_text)
        self.assertIn("fixed seed 20260818", source_text)


if __name__ == "__main__":
    unittest.main()
