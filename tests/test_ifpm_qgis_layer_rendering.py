from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/validate/validate_ifpm_qgis_layer_rendering.py"
QA_REPORT = ROOT / "outputs/qgis_project_package/layer_qa/layer_qa.json"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_ifpm_qgis_layer_rendering", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IfpmQgisLayerRenderingTest(unittest.TestCase):
    def test_qa_outputs_stay_under_outputs(self):
        module = load_module()
        self.assertTrue(module.QA_DIR.is_relative_to(ROOT / "outputs"))
        self.assertTrue(module.PREVIEW_DIR.is_relative_to(module.QA_DIR))

    def test_qa_covers_all_governed_layers(self):
        module = load_module()
        raster_count = sum(
            layer.kind == "raster"
            for site in module.BUILDER.SITE_SPECS.values()
            for layer in site.layers
        )
        layer_count = sum(len(site.layers) for site in module.BUILDER.SITE_SPECS.values())
        self.assertEqual(raster_count, 39)
        self.assertEqual(layer_count, 45)

    @unittest.skipUnless(QA_REPORT.exists(), "run the QGIS layer validator first")
    def test_generated_qa_matches_current_validator(self):
        module = load_module()
        report = json.loads(QA_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["layer_count"], 45)
        self.assertEqual(report["review_count"], 0)
        self.assertEqual(
            report["validator_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
        )
        self.assertEqual(
            report["builder_sha256"],
            hashlib.sha256(module.BUILDER_PATH.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            report["manifest_sha256"],
            hashlib.sha256(module.BUILDER.MANIFEST.read_bytes()).hexdigest(),
        )
        for project_name, digest in report["portable_project_sha256"].items():
            self.assertEqual(
                digest,
                hashlib.sha256((module.BUILDER.PORTABLE_DIR / project_name).read_bytes()).hexdigest(),
            )
        for relative_path in report["contact_sheets"]:
            self.assertTrue((ROOT / relative_path).exists())


if __name__ == "__main__":
    unittest.main()
