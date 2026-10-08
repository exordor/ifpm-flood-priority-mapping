from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin/package/manage_qgis_package_paths.py"
PACKAGE_PATHS_FOR_TEST = {
    "goslar_fullaudit": Path("goslar/FullAudit"),
    "goslar_reviewmap": Path("goslar/ReviewMap"),
    "secocha_fullaudit": Path("secocha/FullAudit"),
    "secocha_reviewmap": Path("secocha/ReviewMap"),
}


class QgisPackagePathManagerTest(unittest.TestCase):
    def test_catalog_exposes_one_canonical_root_and_standalone_legacy_sites(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--catalog-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        catalog = json.loads(completed.stdout)
        self.assertEqual(catalog["canonical_root"], "exports/qgis_packages")
        self.assertEqual(
            catalog["packages"],
            {
                "goslar_fullaudit": "goslar/FullAudit",
                "goslar_reviewmap": "goslar/ReviewMap",
                "secocha_fullaudit": "secocha/FullAudit",
                "secocha_reviewmap": "secocha/ReviewMap",
                "legacy_peru_fullaudit": "legacy_peru_vitor_la_joya_siguas/FullAudit",
                "legacy_zimbabwe_fullaudit": "legacy_zimbabwe_upper_mzingwane/FullAudit",
            },
        )

    def test_split_legacy_fixture_creates_two_self_contained_site_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "combined"
            destination = root / "qgis_packages"
            for site in ("peru", "zimbabwe"):
                (source / "layers" / site / "priority").mkdir(parents=True)
                (source / "layers" / site / "priority" / f"{site}_priority.tif").write_bytes(
                    f"{site}-raster".encode()
                )
                (source / "styles").mkdir(exist_ok=True)
                (source / "styles" / f"{site}_priority.qml").write_text(
                    f"<style>{site}</style>", encoding="utf-8"
                )
                (source / f"IFPM_{site.title()}.qgz").write_bytes(f"{site}-project".encode())

            fields = [
                "site", "layer_key", "display_name", "group", "role", "source_type",
                "provider_crs", "unit", "visible_by_default", "claim_level",
                "portable_source_path", "portable_size_bytes", "portable_sha256",
                "load_status", "notes",
            ]
            with (source / "manifest.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for site in ("peru", "zimbabwe"):
                    layer = source / "layers" / site / "priority" / f"{site}_priority.tif"
                    import hashlib

                    writer.writerow(
                        {
                            "site": site,
                            "layer_key": "priority",
                            "display_name": "Relative priority",
                            "group": "1. Priority result",
                            "role": "priority_result",
                            "source_type": "raster",
                            "provider_crs": "EPSG:32718" if site == "peru" else "EPSG:32735",
                            "unit": "0-1",
                            "visible_by_default": "true",
                            "claim_level": "sensitivity_scenario",
                            "portable_source_path": f"layers/{site}/priority/{site}_priority.tif",
                            "portable_size_bytes": str(layer.stat().st_size),
                            "portable_sha256": hashlib.sha256(layer.read_bytes()).hexdigest(),
                            "load_status": "valid",
                            "notes": "fixture",
                        }
                    )
            (source / "validation.json").write_text(
                json.dumps({"status": "package_integrity_valid"}), encoding="utf-8"
            )
            (source / "README.txt").write_text("combined fixture", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-dir",
                    str(source),
                    "--destination-root",
                    str(destination),
                    "--split-only",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            expected = {
                "legacy_peru_vitor_la_joya_siguas": ("peru", "IFPM_Peru_Legacy_FullAudit.qgz"),
                "legacy_zimbabwe_upper_mzingwane": (
                    "zimbabwe",
                    "IFPM_Zimbabwe_Legacy_FullAudit.qgz",
                ),
            }
            for package_name, (site, project_name) in expected.items():
                package = destination / package_name / "FullAudit"
                self.assertTrue((package / project_name).exists())
                self.assertTrue((package / "layers" / site / "priority" / f"{site}_priority.tif").exists())
                other = "zimbabwe" if site == "peru" else "peru"
                self.assertFalse((package / "layers" / other).exists())
                rows = list(csv.DictReader((package / "manifest.csv").open(newline="", encoding="utf-8")))
                self.assertEqual([row["site"] for row in rows], [site])
                validation = json.loads((package / "validation.json").read_text(encoding="utf-8"))
                self.assertEqual(validation["status"], "package_integrity_valid")
                self.assertEqual(validation["manifest_layer_count"], 1)
                archive = package.with_suffix(".zip")
                self.assertTrue(archive.exists())
                with zipfile.ZipFile(archive) as handle:
                    self.assertIsNone(handle.testzip())

            index = json.loads((destination / "package_index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["legacy_peru_fullaudit"]["layer_count"], 1)
            self.assertEqual(index["legacy_zimbabwe_fullaudit"]["layer_count"], 1)

    def test_current_packages_move_to_canonical_paths_without_duplicate_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "qgis_packages"
            source_root = root / "old_exports"
            package_inputs = {}
            for key in (
                "goslar_fullaudit",
                "goslar_reviewmap",
                "secocha_fullaudit",
                "secocha_reviewmap",
            ):
                package = source_root / key
                package.mkdir(parents=True)
                (package / "manifest.csv").write_text(
                    "site,layer_key\nfixture,priority\n", encoding="utf-8"
                )
                (package / f"{key}.qgz").write_bytes(key.encode())
                archive = package.with_suffix(".zip")
                with zipfile.ZipFile(archive, "w") as handle:
                    handle.writestr(f"{package.name}/manifest.csv", "site,layer_key\nfixture,priority\n")
                package_inputs[key] = package

            command = [
                sys.executable,
                str(SCRIPT),
                "--destination-root",
                str(destination),
                "--skip-split",
                "--move-current",
            ]
            for key, package in package_inputs.items():
                command.extend(["--current-package", f"{key}={package}"])
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            for key, source in package_inputs.items():
                target = destination / PACKAGE_PATHS_FOR_TEST[key]
                self.assertTrue(target.exists(), key)
                self.assertTrue(target.with_suffix(".zip").exists(), key)
                self.assertFalse(source.exists(), key)
                self.assertFalse(source.with_suffix(".zip").exists(), key)

            index = json.loads((destination / "package_index.json").read_text(encoding="utf-8"))
            self.assertEqual(set(index), set(package_inputs))

    def test_verified_combined_source_moves_under_archive_after_split(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "IFPM_QGIS_Project_Package"
            source.mkdir()
            (source / "manifest.csv").write_text("site,layer_key\n", encoding="utf-8")
            source_archive = source.with_suffix(".zip")
            with zipfile.ZipFile(source_archive, "w") as handle:
                handle.writestr("IFPM_QGIS_Project_Package/manifest.csv", "site,layer_key\n")
            destination = root / "qgis_packages"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--destination-root",
                    str(destination),
                    "--source-dir",
                    str(source),
                    "--skip-split",
                    "--archive-combined",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            archived = destination / "_archive/legacy_peru_zimbabwe_combined"
            self.assertTrue((archived / "IFPM_QGIS_Project_Package").is_dir())
            self.assertTrue((archived / "IFPM_QGIS_Project_Package.zip").is_file())
            self.assertFalse(source.exists())
            self.assertFalse(source_archive.exists())

    def test_refresh_index_recomputes_existing_package_hashes_after_rebuild(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "qgis_packages"
            package = destination / "goslar/FullAudit"
            package.mkdir(parents=True)
            (package / "IFPM_Goslar_FullAudit.qgz").write_bytes(b"rebuilt-project")
            (package / "manifest.csv").write_text(
                "site,layer_key\ngoslar,priority\ngoslar,flood_hazard\n",
                encoding="utf-8",
            )
            archive = package.with_suffix(".zip")
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("FullAudit/manifest.csv", "rebuilt")
            (destination / "package_index.json").write_text(
                json.dumps(
                    {
                        "goslar_fullaudit": {"zip_sha256": "stale"},
                        "legacy_combined_archive": {"zip_sha256": "removed"},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--destination-root",
                    str(destination),
                    "--skip-split",
                    "--refresh-index",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            index = json.loads((destination / "package_index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["goslar_fullaudit"]["layer_count"], 2)
            self.assertNotEqual(index["goslar_fullaudit"]["zip_sha256"], "stale")
            self.assertNotIn("legacy_combined_archive", index)

    def test_split_rejects_manifest_paths_outside_the_combined_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "combined"
            source.mkdir()
            (source / "IFPM_Peru.qgz").write_bytes(b"peru-project")
            (source / "validation.json").write_text(
                json.dumps({"status": "package_integrity_valid"}), encoding="utf-8"
            )
            (root / "escape.tif").write_bytes(b"outside")
            (source / "manifest.csv").write_text(
                "site,layer_key,portable_source_path,portable_sha256\n"
                "peru,priority,../escape.tif,"
                "31207f485be64b123d13cfd28c8b4f3ac940858ac0c195d8b3de8785ee2495e8\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-dir",
                    str(source),
                    "--destination-root",
                    str(root / "qgis_packages"),
                    "--split-only",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("unsafe portable source path", completed.stderr)


if __name__ == "__main__":
    unittest.main()
