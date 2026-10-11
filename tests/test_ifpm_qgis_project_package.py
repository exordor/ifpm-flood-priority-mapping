from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sqlite3
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/package/build_peru_former_zimbabwe_qgis_projects.py"
PACKAGE = ROOT / "outputs/qgis_project_package"
PORTABLE = (
    ROOT
    / "exports/qgis_packages/_archive/legacy_peru_zimbabwe_combined/IFPM_QGIS_Project_Package"
)
GENERATED_PACKAGE_AVAILABLE = (PACKAGE / "validation.json").exists() and PORTABLE.exists()


def load_module():
    spec = importlib.util.spec_from_file_location("build_peru_former_zimbabwe_qgis_projects", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IfpmQgisProjectPackageTest(unittest.TestCase):
    def test_configuration_has_matching_country_layer_roles(self):
        module = load_module()

        self.assertEqual(set(module.SITE_SPECS), {"peru", "zimbabwe"})
        for site in module.SITE_SPECS.values():
            roles = [layer.role for layer in site.layers]
            self.assertEqual(roles.count("priority_result"), 1)
            self.assertEqual(roles.count("criterion"), 5)
            self.assertGreaterEqual(roles.count("input_factor"), 12)

        public_text = " ".join(
            layer.name for site in module.SITE_SPECS.values() for layer in site.layers
        ).lower()
        self.assertNotIn("equal", public_text)
        self.assertNotIn("top 20", public_text)
        self.assertNotIn("top20", public_text)
        self.assertNotIn("ahp direct", public_text)
        self.assertNotIn("mentor", public_text)
        self.assertNotIn("working boundary", public_text)

        for site in module.SITE_SPECS.values():
            priority = next(layer for layer in site.layers if layer.role == "priority_result")
            self.assertEqual(priority.claim_level, "sensitivity_scenario")
            self.assertEqual(priority.name, "Relative flood-priority index")
            factors = {layer.key: layer for layer in site.layers if layer.role == "input_factor"}
            self.assertEqual(factors["distance_drainage"].unit, "m")
            self.assertEqual(factors["upstream_area"].unit, "cells")

        zimbabwe_socioeconomic = next(
            layer
            for layer in module.SITE_SPECS["zimbabwe"].layers
            if layer.key == "socioeconomic"
        )
        self.assertEqual(zimbabwe_socioeconomic.name, "Road/access exposure indicator")

    def test_country_criteria_share_names_and_palettes(self):
        module = load_module()

        peru = {
            layer.key: layer.palette
            for layer in module.SITE_SPECS["peru"].layers
            if layer.role == "criterion"
        }
        zimbabwe = {
            layer.key: layer.palette
            for layer in module.SITE_SPECS["zimbabwe"].layers
            if layer.role == "criterion"
        }
        self.assertEqual(peru, zimbabwe)
        self.assertEqual(set(peru), set(module.CRITERION_PALETTES))

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the QGIS package builder first")
    def test_generated_projects_are_portable_within_workspace(self):
        expected = {
            "IFPM_Peru.qgz",
            "IFPM_Zimbabwe.qgz",
            "IFPM_Combined.qgz",
        }
        self.assertEqual({path.name for path in PACKAGE.glob("*.qgz")}, expected)

        for project_path in PACKAGE.glob("*.qgz"):
            with zipfile.ZipFile(project_path) as archive:
                qgs_names = [name for name in archive.namelist() if name.endswith(".qgs")]
                self.assertEqual(len(qgs_names), 1)
                project_xml = archive.read(qgs_names[0]).decode("utf-8")
            self.assertNotIn("/Users/jlw/", project_xml)
            self.assertIn("<Paths>", project_xml)
            self.assertIn('<Absolute type="bool">false</Absolute>', project_xml)
            self.assertIn('source="../', project_xml)

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the QGIS package builder first")
    def test_manifest_records_valid_layers_and_styles(self):
        manifest = PACKAGE / "manifest.csv"
        self.assertTrue(manifest.exists())
        with manifest.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertGreaterEqual(len(rows), 38)
        self.assertTrue(all(row["load_status"] == "valid" for row in rows))
        self.assertTrue(all((ROOT / row["source_path"]).exists() for row in rows))
        for row in rows:
            source = ROOT / row["source_path"]
            portable = PORTABLE / row["portable_source_path"]
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), row["source_sha256"])
            self.assertEqual(
                hashlib.sha256(portable.read_bytes()).hexdigest(),
                row["portable_sha256"],
            )
        styled = [row for row in rows if row["style_path"]]
        self.assertGreaterEqual(len(styled), 18)
        self.assertTrue(all((PACKAGE / row["style_path"]).exists() for row in styled))

        validation = json.loads((PACKAGE / "validation.json").read_text(encoding="utf-8"))
        self.assertEqual(validation["status"], "package_integrity_valid")
        self.assertEqual(
            validation["generator_sha256"],
            hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        )
        self.assertEqual(len(validation["qgis_readback"]), 6)
        self.assertTrue(all(item["read_success"] for item in validation["qgis_readback"]))
        self.assertTrue(all(not item["invalid_layers"] for item in validation["qgis_readback"]))

        combined = next(
            item
            for item in validation["qgis_readback"]
            if item["project"] == "IFPM_Combined.qgz" and item["package_type"] == "portable"
        )
        xmin, _, xmax, _ = combined["default_extent"]
        self.assertLess(xmin, -70)
        self.assertGreater(xmax, 20)

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the QGIS package builder first")
    def test_portable_export_is_self_contained(self):
        module = load_module()
        portable = module.PORTABLE_DIR
        self.assertEqual(
            {path.name for path in portable.glob("*.qgz")},
            {"IFPM_Peru.qgz", "IFPM_Zimbabwe.qgz", "IFPM_Combined.qgz"},
        )
        with (portable / "manifest.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(all((portable / row["portable_source_path"]).exists() for row in rows))
        self.assertTrue(all(row["portable_sha256"] for row in rows))
        self.assertNotIn("source_path", rows[0])

        for project in portable.glob("*.qgz"):
            with zipfile.ZipFile(project) as archive:
                self.assertEqual(len(archive.namelist()), 1)
                qgs = next(name for name in archive.namelist() if name.endswith(".qgs"))
                project_xml = archive.read(qgs).decode("utf-8")
            self.assertNotIn("jlw", project_xml)
            self.assertNotIn("../", project_xml)
            self.assertNotIn("mentor", project_xml.lower())
            self.assertNotIn("pilot", project_xml.lower())

        forbidden_style_terms = {
            "mentor_review_role",
            "in_top20_priority_cells",
            "evidence_support",
        }
        for style in (portable / "styles").glob("*.qml"):
            style_xml = style.read_text(encoding="utf-8").lower()
            for term in forbidden_style_terms:
                self.assertNotIn(term, style_xml)

        c_factor_style = (portable / "styles/peru_c_factor.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn('clip="0"', c_factor_style)

        self.assertFalse(list(portable.rglob("*.aux.xml")))
        validation = json.loads((portable / "validation.json").read_text(encoding="utf-8"))
        self.assertFalse(validation["checksum_errors"])
        self.assertFalse(validation["unexpected_portable_files"])

    @unittest.skipUnless(GENERATED_PACKAGE_AVAILABLE, "run the QGIS package builder first")
    def test_portable_vectors_exclude_internal_layers_and_fields(self):
        with (PORTABLE / "manifest.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        vector_rows = [row for row in rows if row["source_type"] == "vector"]
        forbidden_fields = {
            "mentor_review_role",
            "reason",
            "confidence",
            "in_top20_priority_cells",
            "evidence_support",
            "claim_level",
        }
        for row in vector_rows:
            path = PORTABLE / row["portable_source_path"]
            connection = sqlite3.connect(path)
            try:
                layers = {
                    item[0]
                    for item in connection.execute(
                        "SELECT table_name FROM gpkg_contents WHERE data_type='features'"
                    )
                }
                self.assertEqual(len(layers), 1)
                layer = next(iter(layers))
                fields = {item[1] for item in connection.execute(f'PRAGMA table_info("{layer}")')}
                self.assertFalse(fields & forbidden_fields)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
