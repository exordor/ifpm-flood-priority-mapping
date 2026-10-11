from __future__ import annotations

import importlib.util
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_GROUP = "7. External validation and overlays"


def load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class QgisExternalOverlayGroupStandardizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.secocha = load_module(
            "qgis_overlay_secocha_builder",
            "bin/package/build_secocha_qgis_full_audit.py",
        )
        cls.goslar = load_module(
            "qgis_overlay_goslar_builder",
            "bin/package/build_goslar_qgis_full_audit.py",
        )

    def assert_overlay_group(self, layers, keys):
        by_key = {layer.key: layer for layer in layers}
        self.assertTrue(set(keys).issubset(by_key))
        self.assertEqual({by_key[key].group for key in keys}, {EXPECTED_GROUP})

    def test_region_overlay_layers_use_one_group(self):
        self.assert_overlay_group(
            self.secocha.layers,
            {
                "boundary",
                "original_a7367",
                "event_footprint",
                "event_huaico",
                "event_mudflow",
                "mining",
                "field_anchors",
                "response_locations",
            },
        )
        self.assert_overlay_group(
            self.goslar.GOSLAR_LAYERS,
            {
                "boundary",
                "natura2000",
                "roads",
                "lbeg_mining_rights",
                "osm_mining_points",
                "osm_mining_areas",
            },
        )

    def test_mining_overlay_notes_do_not_claim_verified_active_mining(self):
        secocha = next(layer for layer in self.secocha.layers if layer.key == "mining")
        self.assertIn("not verified active", secocha.notes.lower())
        goslar = {layer.key: layer for layer in self.goslar.GOSLAR_LAYERS}
        self.assertIn("not proof of active", goslar["lbeg_mining_rights"].notes.lower())
        for key in {"lbeg_mining_rights", "osm_mining_points", "osm_mining_areas"}:
            self.assertEqual(goslar[key].claim_level, "context_evidence")
            self.assertFalse(goslar[key].visible)

    def test_standardization_does_not_invent_missing_historical_events(self):
        goslar_keys = {layer.key for layer in self.goslar.GOSLAR_LAYERS}
        self.assertFalse({"event_footprint", "event_huaico", "event_mudflow"} & goslar_keys)

    def test_generated_manifests_and_projects_use_shared_group(self):
        packages = [
            (ROOT / "outputs/secocha_qgis_full_audit", ["IFPM_Peru_Secocha_FullAudit.qgz"]),
            (ROOT / "outputs/goslar_qgis_full_audit", ["IFPM_Goslar_FullAudit.qgz"]),
        ]
        for package, projects in packages:
            manifest = (package / "manifest.csv").read_text(encoding="utf-8")
            self.assertIn(EXPECTED_GROUP, manifest)
            self.assertNotIn("7. Historical event and mining overlays", manifest)
            self.assertNotIn("7. Context and evidence", manifest)
            self.assertNotIn("4. Context and evidence", manifest)
            for project in projects:
                with zipfile.ZipFile(package / project) as archive:
                    qgs = next(name for name in archive.namelist() if name.endswith(".qgs"))
                    xml = archive.read(qgs).decode("utf-8")
                self.assertIn(EXPECTED_GROUP, xml)

    def test_portable_archives_match_current_directories(self):
        portable_directories = [
            ROOT / "exports/qgis_packages/secocha/FullAudit",
            ROOT / "exports/qgis_packages/goslar/FullAudit",
        ]
        for directory in portable_directories:
            archive_path = directory.with_suffix(".zip")
            expected_names = {
                (Path(directory.name) / path.relative_to(directory)).as_posix()
                for path in directory.rglob("*")
                if path.is_file() and not any(part.startswith(".") for part in path.relative_to(directory).parts)
            }
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(set(archive.namelist()), expected_names, archive_path.name)
                for relative in ["manifest.csv", "validation.json"] + [
                    path.name for path in directory.glob("*.qgz")
                ]:
                    archived = archive.read((Path(directory.name) / relative).as_posix())
                    self.assertEqual(archived, (directory / relative).read_bytes(), relative)


if __name__ == "__main__":
    unittest.main()
