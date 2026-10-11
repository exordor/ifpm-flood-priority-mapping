from __future__ import annotations

import csv
import hashlib
import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "goslar_full": (
        ROOT / "outputs/goslar_qgis_full_audit",
        "IFPM_Goslar_FullAudit.qgz",
        37,
    ),
    "goslar_review_map": (
        ROOT / "outputs/goslar_qgis_review",
        "IFPM_Goslar_ReviewMap.qgz",
        25,
    ),
    "secocha_full": (
        ROOT / "outputs/secocha_qgis_full_audit",
        "IFPM_Peru_Secocha_FullAudit.qgz",
        39,
    ),
    "secocha_review_map": (
        ROOT / "outputs/secocha_qgis_review",
        "IFPM_Peru_Secocha_ReviewMap.qgz",
        23,
    ),
}

PORTABLE_PACKAGES = {
    "goslar_full": ROOT / "exports/qgis_packages/goslar/FullAudit",
    "goslar_review_map": ROOT / "exports/qgis_packages/goslar/ReviewMap",
    "secocha_full": ROOT / "exports/qgis_packages/secocha/FullAudit",
    "secocha_review_map": ROOT / "exports/qgis_packages/secocha/ReviewMap",
}


class QgisFullCompactPackageTest(unittest.TestCase):
    def test_projects_exist_and_validate(self):
        for name, (directory, project_name, expected_count) in PACKAGES.items():
            with self.subTest(name):
                self.assertTrue((directory / project_name).exists(), project_name)
                self.assertTrue((directory / "manifest.csv").exists())
                validation = json.loads((directory / "validation.json").read_text(encoding="utf-8"))
                self.assertEqual(validation["status"], "package_integrity_valid")
                self.assertEqual(validation["manifest_layer_count"], expected_count)
                self.assertTrue(all(row["read_success"] for row in validation["qgis_readback"]))
                self.assertTrue(all(not row["invalid_layers"] for row in validation["qgis_readback"]))

    def test_current_portable_packages_use_canonical_managed_paths(self):
        for key, package in PORTABLE_PACKAGES.items():
            with self.subTest(key):
                self.assertTrue(package.is_dir(), package)
                self.assertTrue(package.with_suffix(".zip").is_file(), package)
                self.assertTrue((package / "manifest.csv").is_file(), package)

    def test_secocha_review_map_zip_matches_directory_and_readme(self):
        package = PORTABLE_PACKAGES["secocha_review_map"]
        self.assertTrue((package / "README.txt").read_text(encoding="utf-8").startswith(
            "IFPM Peru Secocha ReviewMap QGIS package"
        ))
        files = {
            path.relative_to(package).as_posix(): path
            for path in package.rglob("*")
            if path.is_file()
        }
        self.assertFalse(any(name.endswith(".aux.xml") for name in files))
        with zipfile.ZipFile(package.with_suffix(".zip")) as archive:
            archived = {
                name.removeprefix(f"{package.name}/"): name
                for name in archive.namelist()
            }
            self.assertEqual(set(archived), set(files))
            for relative, path in files.items():
                self.assertEqual(archive.read(archived[relative]), path.read_bytes(), relative)

    def test_goslar_review_map_readme_names_the_actual_entrypoint_and_scope(self):
        readme = (PORTABLE_PACKAGES["goslar_review_map"] / "README.txt").read_text(
            encoding="utf-8"
        )
        self.assertTrue(readme.startswith("IFPM Goslar ReviewMap QGIS package"))
        self.assertIn("Open IFPM_Goslar_ReviewMap.qgz", readme)
        self.assertIn("omits terrain intermediates", readme)
        self.assertNotIn("Open IFPM_Goslar_FullAudit.qgz", readme)

    def test_goslar_projects_use_a_windows_compatible_label_font(self):
        for package_key in ("goslar_full", "goslar_review_map"):
            with self.subTest(package_key):
                package = PORTABLE_PACKAGES[package_key]
                project_name = PACKAGES[package_key][1]
                with zipfile.ZipFile(package / project_name) as archive:
                    qgs_name = next(name for name in archive.namelist() if name.endswith(".qgs"))
                    project_xml = archive.read(qgs_name).decode("utf-8")
                self.assertIn('fontFamily="Arial"', project_xml)
                self.assertNotIn(".AppleSystemUIFont", project_xml)

    def test_goslar_portable_zips_and_index_match_current_directories(self):
        index = json.loads(
            (ROOT / "exports/qgis_packages/package_index.json").read_text(encoding="utf-8")
        )
        expected = {"goslar_full": "goslar_fullaudit", "goslar_review_map": "goslar_reviewmap"}
        for package_key, index_key in expected.items():
            with self.subTest(package_key):
                package = PORTABLE_PACKAGES[package_key]
                archive_path = package.with_suffix(".zip")
                record = index[index_key]
                self.assertEqual(record["layer_count"], PACKAGES[package_key][2])
                self.assertEqual(
                    hashlib.sha256(archive_path.read_bytes()).hexdigest(),
                    record["zip_sha256"],
                )
                files = {
                    path.relative_to(package).as_posix(): path
                    for path in package.rglob("*")
                    if path.is_file()
                }
                with zipfile.ZipFile(archive_path) as archive:
                    archived = {
                        name.removeprefix(f"{package.name}/"): name
                        for name in archive.namelist()
                    }
                    self.assertEqual(set(archived), set(files))
                    for relative, path in files.items():
                        self.assertEqual(archive.read(archived[relative]), path.read_bytes())

    def test_review_map_subset_omits_audit_intermediates(self):
        with (PACKAGES["goslar_full"][0] / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            full_keys = {row["layer_key"] for row in csv.DictReader(handle)}
        with (PACKAGES["goslar_review_map"][0] / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            review_keys = {row["layer_key"] for row in csv.DictReader(handle)}
        self.assertLess(review_keys, full_keys)
        self.assertNotIn("dem_filled", review_keys)
        self.assertNotIn("flow_direction", review_keys)
        self.assertNotIn("flow_accumulation", review_keys)
        self.assertNotIn("streams", review_keys)
        self.assertIn("original_project_focus_extent", review_keys)

    def test_review_map_keeps_decision_evidence_and_weighted_criteria(self):
        expected = {
            "priority",
            "flood_hazard",
            "sediment",
            "landuse_asm",
            "environmental",
            "socioeconomic",
            "boundary",
        }
        for key in ("goslar_review_map", "secocha_review_map"):
            directory, _, _ = PACKAGES[key]
            with (directory / "manifest.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            layer_keys = {row["layer_key"] for row in rows}
            self.assertTrue(expected.issubset(layer_keys), layer_keys)
            self.assertEqual(sum(row["role"] == "priority_result" for row in rows), 1)
            self.assertEqual(sum(row["role"] == "criterion" for row in rows), 5)

    def test_goslar_location_evidence_is_in_full_and_review_packages(self):
        for key in ("goslar_full", "goslar_review_map"):
            directory, _, _ = PACKAGES[key]
            with (directory / "manifest.csv").open(newline="", encoding="utf-8") as handle:
                rows = {row["layer_key"]: row for row in csv.DictReader(handle)}
            evidence = rows["affected_locations_2017"]
            self.assertEqual(evidence["group"], "7. External validation and overlays")
            self.assertEqual(evidence["role"], "historical_event_location_evidence")
            self.assertEqual(evidence["claim_level"], "validation_candidate")
            self.assertEqual(evidence["visible_by_default"], "true")

    def test_processed_sentinel_products_are_fullaudit_only(self):
        with (PACKAGES["secocha_full"][0] / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            full_keys = {row["layer_key"] for row in csv.DictReader(handle)}
        with (PACKAGES["secocha_review_map"][0] / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            review_keys = {row["layer_key"] for row in csv.DictReader(handle)}
        processed = {"s2_ndwi_before", "s2_ndwi_after", "s2_new_surface_water"}
        self.assertTrue(processed.issubset(full_keys))
        self.assertFalse(processed & review_keys)

        with (PACKAGES["secocha_full"][0] / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            full_rows = {row["layer_key"]: row for row in csv.DictReader(handle)}
        for key in processed:
            self.assertEqual(full_rows[key]["group"], "7. External validation and overlays")
            self.assertEqual(full_rows[key]["claim_level"], "validation_candidate")

    def test_official_proxy_replacements_are_fullaudit_only(self):
        with (PACKAGES["secocha_full"][0] / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            full_rows = {row["layer_key"]: row for row in csv.DictReader(handle)}
        with (PACKAGES["secocha_review_map"][0] / "manifest.csv").open(newline="", encoding="utf-8") as handle:
            review_keys = {row["layer_key"] for row in csv.DictReader(handle)}
        expected = {
            "minedu_schools_2023",
            "minam_health_facilities",
            "ingemmet_mining_rights",
            "ingemmet_dgm_activity",
        }
        self.assertTrue(expected.issubset(full_rows))
        self.assertFalse(expected & review_keys)
        for key in expected:
            self.assertEqual(full_rows[key]["group"], "7. External validation and overlays")
            self.assertEqual(full_rows[key]["claim_level"], "context_evidence")
            self.assertEqual(full_rows[key]["visible_by_default"], "false")
        self.assertIn(
            "not verified active extraction",
            full_rows["ingemmet_mining_rights"]["notes"].lower(),
        )
        self.assertIn("not exact building", full_rows["minam_health_facilities"]["notes"].lower())


if __name__ == "__main__":
    unittest.main()
