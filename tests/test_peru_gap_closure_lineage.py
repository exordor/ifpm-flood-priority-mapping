from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIM = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
    "priority_mentor_peru_direct_pim.tif"
)
TOP20 = ROOT / (
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
    "top20_mentor_peru_direct_pim.tif"
)
POPULATION_MANIFEST = ROOT / "outputs/peru_gap_closure_analysis/peru_population_by_pim_class_manifest.json"
SINPAD_MANIFEST = ROOT / "outputs/peru_gap_closure_analysis/peru_sinpad_colocation_manifest.json"
RUN_MANIFEST = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/run_manifest.json"
WORLDPOP = ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj_peru_hybas_l7_6070641200_bbox.tif"
SINPAD = ROOT / "data/validation/indeci_sinpad_peru_flood_events/peru_hybas_l7_6070641200_sinpad_flood_relevant.gpkg"
LOCAL_OUTPUTS_READY = all(
    path.exists()
    for path in (PIM, TOP20, POPULATION_MANIFEST, SINPAD_MANIFEST, RUN_MANIFEST, WORLDPOP, SINPAD)
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@unittest.skipUnless(LOCAL_OUTPUTS_READY, "requires ignored local Peru data and generated outputs")
class PeruGapClosureLineageTest(unittest.TestCase):
    def test_analysis_manifests_reference_current_pim_checksum(self):
        expected = sha256(PIM)
        expected_top20 = sha256(TOP20)
        for path in (POPULATION_MANIFEST, SINPAD_MANIFEST):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["pim_sha256"], expected, path.name)
            self.assertEqual(manifest["top20_selection_sha256"], expected_top20, path.name)

    def test_sinpad_manifest_keeps_in_boundary_record_count(self):
        manifest = json.loads(SINPAD_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["records_sampled"], 25)
        self.assertEqual(manifest["unique_locations"], 11)
        self.assertEqual(manifest["flood_specific_records"], 4)
        self.assertEqual(manifest["unique_flood_locations"], 2)

    def test_analysis_manifests_reference_current_evidence_checksums(self):
        population = json.loads(POPULATION_MANIFEST.read_text(encoding="utf-8"))
        sinpad = json.loads(SINPAD_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(population["population_sha256"], sha256(WORLDPOP))
        self.assertEqual(sinpad["sinpad_sha256"], sha256(SINPAD))

    def test_scenario_manifest_binds_current_script_inputs_and_outputs(self):
        manifest = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
        script = ROOT / manifest["script"]["path"]
        self.assertEqual(manifest["script"]["sha256"], sha256(script))
        for group in ("inputs", "outputs"):
            for item in manifest[group]:
                path = ROOT / item["path"]
                self.assertEqual(item["sha256"], sha256(path), item["path"])


if __name__ == "__main__":
    unittest.main()
