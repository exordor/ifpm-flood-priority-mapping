from __future__ import annotations

import csv
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/package/build_zimbabwe_report_figure_chain.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_zimbabwe_report_figure_chain", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ZimbabweReportFigureChainTest(unittest.TestCase):
    def test_chain_excludes_equal_and_top20_reporting_artifacts(self):
        module = load_module()

        text = " ".join(
            f"{item.item_id} {item.source_png} {item.source_pdf}".lower()
            for item in module.ITEMS
        )
        self.assertNotIn("top20", text)
        self.assertNotIn("top_20", text)
        self.assertNotIn("equal", text)
        self.assertEqual(len(module.ITEMS), 13)
        self.assertEqual(module.ITEMS[7].item_id, "zimbabwe_priority_mining_population_overlay")
        self.assertEqual(module.ITEMS[8].item_id, "zimbabwe_weighted_contribution")
        evidence = [item for item in module.ITEMS if "evidence" in item.stage or "diagnostic" in item.stage]
        self.assertTrue(evidence)
        self.assertTrue(all(item.claim_level == "diagnostic_only" for item in evidence))
        self.assertIn("temporary.replace(destination)", SCRIPT.read_text(encoding="utf-8"))

    def test_current_sources_package_with_matching_hashes(self):
        module = load_module()

        module.main()

        with module.MANIFEST.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 13)
        for row in rows:
            for suffix in ("png", "pdf"):
                packaged = ROOT / row[f"packaged_{suffix}"]
                self.assertTrue(packaged.exists(), packaged)
                self.assertEqual(row[f"source_{suffix}_sha256"], row[f"packaged_{suffix}_sha256"])
        readme = (module.CURRENT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("not a validated flood-risk map", readme)
        self.assertIn("road/access proximity only", readme)
        self.assertIn("USGS mineral-reference proximity", readme)
        self.assertIn("spatial K, LS, and C at 0.35/0.35/0.30", readme)
        self.assertNotIn("catchment-mean K", readme)


if __name__ == "__main__":
    unittest.main()
