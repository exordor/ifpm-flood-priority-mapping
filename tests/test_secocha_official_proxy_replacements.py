import importlib.util
import ssl
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import geopandas as gpd
import pandas as pd
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bin" / "acquire" / "pull_secocha_official_proxy_replacements.py"


def load_module():
    spec = importlib.util.spec_from_file_location("secocha_proxy_replacements", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SecochaOfficialProxyReplacementTest(unittest.TestCase):
    def test_school_services_are_deduplicated_to_real_locations(self):
        module = load_module()
        services = pd.DataFrame(
            [
                {
                    "CODLOCAL": "A",
                    "COD_MOD": "1",
                    "ANEXO": "0",
                    "CEN_EDU": "School A primary",
                    "NLAT_IE": -15.95,
                    "NLONG_IE": -73.18,
                    "IMPUTADO": "1",
                    "TALUMNO": 10,
                    "TDOCENTE": 2,
                },
                {
                    "CODLOCAL": "A",
                    "COD_MOD": "2",
                    "ANEXO": "0",
                    "CEN_EDU": "School A secondary",
                    "NLAT_IE": -15.95,
                    "NLONG_IE": -73.18,
                    "IMPUTADO": "1",
                    "TALUMNO": 20,
                    "TDOCENTE": 3,
                },
                {
                    "CODLOCAL": "B",
                    "COD_MOD": "3",
                    "ANEXO": "0",
                    "CEN_EDU": "School B",
                    "NLAT_IE": -15.90,
                    "NLONG_IE": -73.18,
                    "IMPUTADO": "2",
                    "TALUMNO": 5,
                    "TDOCENTE": 1,
                },
                {
                    "CODLOCAL": None,
                    "COD_MOD": "4",
                    "ANEXO": "0",
                    "CEN_EDU": "Unresolved location one",
                    "NLAT_IE": -15.96,
                    "NLONG_IE": -73.18,
                    "IMPUTADO": "1",
                    "TALUMNO": 7,
                    "TDOCENTE": 1,
                },
                {
                    "CODLOCAL": None,
                    "COD_MOD": "5",
                    "ANEXO": "0",
                    "CEN_EDU": "Unresolved location two",
                    "NLAT_IE": -15.97,
                    "NLONG_IE": -73.18,
                    "IMPUTADO": "1",
                    "TALUMNO": 8,
                    "TDOCENTE": 1,
                },
                {
                    "CODLOCAL": "BAD",
                    "COD_MOD": "4",
                    "ANEXO": "0",
                    "CEN_EDU": "Invalid coordinate",
                    "NLAT_IE": 0,
                    "NLONG_IE": 0,
                    "IMPUTADO": "1",
                    "TALUMNO": 1,
                    "TDOCENTE": 1,
                },
            ]
        )
        school_a_point = gpd.GeoSeries.from_xy([-73.18], [-15.95], crs="EPSG:4326").to_crs(
            "EPSG:32718"
        ).iloc[0]
        boundary = gpd.GeoDataFrame(
            {"boundary_id": ["test"]},
            geometry=[school_a_point.buffer(1_000).envelope],
            crs="EPSG:32718",
        )

        locations, quality = module.build_school_locations(
            services, boundary, context_buffer_m=20_000
        )

        self.assertEqual(
            set(locations["location_id"]),
            {"A", "B", "SERVICE:4:0", "SERVICE:5:0"},
        )
        school_a = locations.set_index("location_id").loc["A"]
        self.assertEqual(int(school_a["service_count"]), 2)
        self.assertEqual(int(school_a["reported_student_service_sum"]), 30)
        self.assertEqual(int(school_a["reported_teacher_service_sum"]), 5)
        self.assertEqual(school_a["record_provenance"], "declared")
        self.assertNotIn("coordinate_quality", locations.columns)
        self.assertIn("not building-accurate", school_a["position_limit"])
        self.assertEqual(quality["invalid_coordinate_records"], 1)
        self.assertEqual(quality["missing_codlocal_service_records"], 2)
        self.assertEqual(quality["unique_locations"], 4)
        self.assertEqual(quality["record_provenance_counts"], {"declared": 3, "imputed_total": 1})

    def test_mixed_imputation_is_not_downgraded_to_declared(self):
        module = load_module()
        self.assertEqual(
            module.resolve_record_provenance(["1", "2"]),
            "mixed_with_imputation",
        )

    def test_arcgis_transfer_limit_is_a_hard_failure(self):
        module = load_module()
        with self.assertRaisesRegex(RuntimeError, "transfer limit"):
            module.validate_arcgis_response(
                {"features": [], "exceededTransferLimit": True}, "test layer"
            )

    def test_arcgis_errors_are_not_written_as_empty_data(self):
        module = load_module()
        with self.assertRaisesRegex(RuntimeError, "service error"):
            module.validate_arcgis_response(
                {"error": {"code": 500, "message": "broken"}}, "test layer"
            )

    def test_system_curl_is_used_only_after_python_certificate_failure(self):
        module = load_module()
        certificate_error = urllib.error.URLError(
            ssl.SSLCertVerificationError("certificate verify failed")
        )
        curl_result = SimpleNamespace(stdout=b'{"features": []}', stderr=b"", returncode=0)
        with patch.object(module.urllib.request, "urlopen", side_effect=certificate_error), patch.object(
            module.subprocess, "run", return_value=curl_result
        ) as curl_run:
            payload = module._request_json("https://example.invalid/query")

        self.assertEqual(payload, {"features": []})
        self.assertEqual(curl_run.call_count, 1)
        self.assertEqual(curl_run.call_args.args[0][:3], ["curl", "-fsSL", "--max-time"])

    def test_mining_dates_are_human_readable_in_processed_layer(self):
        module = load_module()
        raw = gpd.GeoDataFrame(
            {
                "OBJECTID": [1, 2, 3, 4],
                "CODIGOU": ["050000001", "050000002", "050000003", "050000004"],
                "CONCESION": ["OVERLAP", "TOUCH", "OUTSIDE", "SLIVER"],
                "LEYENDA": ["TITULADO"] * 4,
                "FEC_DENU": [1675555200000] * 4,
                "FECHA_ACTUALIZACION": [1722470400000] * 4,
            },
            geometry=[
                box(260_000, 8_235_000, 261_000, 8_236_000),
                box(259_500, 8_235_500, 260_500, 8_236_000),
                box(258_000, 8_235_000, 259_000, 8_236_000),
                box(260_499.999, 8_235_500, 260_500.001, 8_235_600),
            ],
            crs="EPSG:32718",
        )
        boundary = gpd.GeoDataFrame(
            {"boundary_id": ["test"]},
            geometry=[box(260_500, 8_235_500, 261_500, 8_236_500)],
            crs="EPSG:32718",
        )

        result = module.sanitize_mining(raw, boundary, 0, max_context_m=500)

        self.assertEqual(result.loc[0, "denouncement_date"], "2023-02-05")
        self.assertEqual(result.loc[0, "source_update_date"], "2024-08-01")
        self.assertNotIn("FEC_DENU", result.columns)
        self.assertNotIn("FECHA_ACTUALIZACION", result.columns)
        self.assertEqual(set(result["CONCESION"]), {"OVERLAP", "TOUCH", "SLIVER"})
        indexed = result.set_index("CONCESION")
        self.assertTrue(bool(indexed.loc["OVERLAP", "positive_area_overlap"]))
        self.assertFalse(bool(indexed.loc["TOUCH", "positive_area_overlap"]))
        self.assertTrue(bool(indexed.loc["TOUCH", "touches_active_boundary"]))
        self.assertFalse(bool(indexed.loc["SLIVER", "positive_area_overlap"]))


if __name__ == "__main__":
    unittest.main()
