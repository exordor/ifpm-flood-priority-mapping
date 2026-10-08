#!/usr/bin/env python3
"""Build a source-anchored first-stage evidence packet for Secocha 2023."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "data/validation/secocha_2023_validation/official_reports"
DEFAULT_OUTPUT = ROOT / "outputs/secocha_2023_validation"
INGEMMET = REPORT_DIR / "ingemmet_a7367_secocha_hazard_assessment.pdf"
INDECI = REPORT_DIR / "indeci_emergency_report_1733_2023-05-20.pdf"

COMMON = {
    "event_id": "secocha_2023_historical_hazard_event",
    "event_date": "2023-02-05",
    "claim_level": "validation_candidate",
    "enters_pim_score": "false",
}

EVIDENCE = [
    {
        **COMMON,
        "observation_id": "event_chronology_indeci",
        "evidence_type": "event_chronology",
        "value": "Intense rainfall activated San Martin quebrada at approximately 14:00 local time",
        "observation_date": "2023-02-05",
        "source_id": "indeci_emergency_report_1733",
        "source_page": "1",
        "source_update_date": "2023-05-20",
        "geometry_role": "none",
        "interpretation_limit": "Official event chronology; does not define event geometry",
    },
    {
        **COMMON,
        "observation_id": "ingemmet_map7_hazard_cartography",
        "evidence_type": "observed_hazard_footprint",
        "value": "Map 7 distinguishes 5 February debris flow and mudflow from other geological hazards",
        "observation_date": "2023-02-14/2023-02-18 fieldwork",
        "source_id": "ingemmet_a7367",
        "source_page": "75",
        "source_update_date": "2023-03",
        "geometry_role": "digitization_primary",
        "interpretation_limit": "Digitize event-specific legend classes only; do not merge rockfall or older debris-flow classes",
    },
    {
        **COMMON,
        "observation_id": "ingemmet_figures61_63_secocha_event",
        "evidence_type": "observed_hazard_footprint",
        "value": "Figures 61-63 map the 5 February flow, fine-fraction affected zones and distal mudflow in Secocha",
        "observation_date": "2023-02-14/2023-02-18 fieldwork",
        "source_id": "ingemmet_a7367",
        "source_page": "53-54",
        "source_update_date": "2023-03",
        "geometry_role": "digitization_detail",
        "interpretation_limit": "Orthophoto overlays are report evidence; analyst digitization must retain page and class lineage",
    },
    {
        **COMMON,
        "observation_id": "ingemmet_secocha_fan_anchor",
        "evidence_type": "field_coordinate_anchor",
        "value": "UTM WGS84 zone 18S: 695121 E, 8232667 N",
        "observation_date": "2023-02-14/2023-02-18 fieldwork",
        "source_id": "ingemmet_a7367",
        "source_page": "51",
        "source_update_date": "2023-03",
        "geometry_role": "control_point",
        "interpretation_limit": "Point anchors Figure 59 near the initial fan; it is not a polygon footprint",
    },
    {
        **COMMON,
        "observation_id": "ingemmet_secocha_stadium_mudflow_anchor",
        "evidence_type": "field_coordinate_anchor",
        "value": "UTM WGS84 zone 18S: 695802 E, 8231989 N",
        "observation_date": "2023-02-14/2023-02-18 fieldwork",
        "source_id": "ingemmet_a7367",
        "source_page": "54",
        "source_update_date": "2023-03",
        "geometry_role": "control_point",
        "interpretation_limit": "Point anchors distal mudflow evidence at the stadium; it is not a polygon footprint",
    },
    {
        **COMMON,
        "observation_id": "indeci_people_impacts_20230316",
        "evidence_type": "report_dated_impact",
        "value": "2643 homeless/damnificada; 732 affected; 19 deceased; 5 injured; 1 missing",
        "observation_date": "updated 2023-03-16 02:00",
        "source_id": "indeci_emergency_report_1733",
        "source_page": "2",
        "source_update_date": "2023-05-20",
        "geometry_role": "district_aggregate",
        "interpretation_limit": "District aggregate includes Secocha-zone and Urasqui vehicle-accident impacts; not Secocha-only",
    },
    {
        **COMMON,
        "observation_id": "indeci_housing_impacts_20230316",
        "evidence_type": "report_dated_impact",
        "value": "745 dwellings destroyed; 335 uninhabitable; 268 affected",
        "observation_date": "updated 2023-03-16 02:00",
        "source_id": "indeci_emergency_report_1733",
        "source_page": "2",
        "source_update_date": "2023-05-20",
        "geometry_role": "district_aggregate",
        "interpretation_limit": "District aggregate and still under evaluation; do not assign totals to individual localities",
    },
    {
        **COMMON,
        "observation_id": "indeci_transport_impacts_20230316",
        "evidence_type": "report_dated_impact",
        "value": "5500 m road affected; 5000 m road destroyed; 5000 m track affected; 2200 m track destroyed",
        "observation_date": "updated 2023-03-16 02:00",
        "source_id": "indeci_emergency_report_1733",
        "source_page": "2",
        "source_update_date": "2023-05-20",
        "geometry_role": "district_aggregate",
        "interpretation_limit": "Length totals do not supply line geometry",
    },
    {
        **COMMON,
        "observation_id": "indeci_power_impacts_20230316",
        "evidence_type": "report_dated_impact",
        "value": "680 users without electricity: Secocha 166, Misky 206, Posco Misky 283, San Martin 23, Cerro Barroso 2",
        "observation_date": "updated 2023-03-16 02:00",
        "source_id": "indeci_emergency_report_1733",
        "source_page": "2",
        "source_update_date": "2023-05-20",
        "geometry_role": "locality_context",
        "interpretation_limit": "Service impact is exposure/impact evidence, not physical hazard extent",
    },
]

SHELTERS = [
    ("Secocha", "Nueva Vision", -15.98399, -73.173087, 28, 140, 20),
    ("Secocha (La Capilla) - Sector Pampaylima", "Secocha", -15.9824, -73.16968, 92, 460, 70),
    ("Urasqui", "Ojo de Agua", -16.02049, -73.17336, 25, 125, 20),
    ("Secocha (Calle Los Angeles)", "Portocarrero", -15.982363, -73.173908, 32, 160, 25),
    ("Secocha Miski (Sector la Antena)", "Sector la Antena", -15.97758, -73.17581, 30, 150, 16),
    ("Secocha", "Misky II", -15.977659, -73.175637, 75, 375, 67),
    ("San Martin", "San Martin", -15.952918, -73.202996, 62, 310, 50),
    ("San Martin (Posko Miski)", "Posko Miski", -15.952866, -73.203011, 80, 400, 58),
]

INGEMMET_ANCHORS = [
    ("pampaylima_lower_huaico_trace", -73.1809946164, -15.9774426422, 694668, 8232709, "51", "Figure 58"),
    ("secocha_fan_initial_flow", -73.1767598261, -15.9777863231, 695121, 8232667, "51", "Figure 59"),
    ("secocha_stadium_mudflow", -73.1703430965, -15.9838585784, 695802, 8231989, "54", "Photo 2"),
    ("secocha_distal_mudflow", -73.1697266736, -15.9838442958, 695868, 8231990, "54", "Photo 3"),
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_point_geojson(path: Path, rows: list[dict[str, object]]) -> None:
    features = []
    for row in rows:
        properties = {key: value for key, value in row.items() if key not in {"longitude", "latitude"}}
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]],
                },
                "properties": properties,
            }
        )
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def render_preview(pdf: Path, page: int, output_prefix: Path) -> None:
    subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page),
            "-l",
            str(page),
            "-singlefile",
            "-png",
            "-r",
            "160",
            str(pdf),
            str(output_prefix),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-previews", action="store_true")
    args = parser.parse_args()
    output = args.output_dir
    write_csv(output / "event_evidence.csv", EVIDENCE)

    shelter_rows = []
    for locality, shelter, latitude, longitude, families, people, tents in SHELTERS:
        shelter_rows.append(
            {
                **COMMON,
                "locality": locality,
                "shelter": shelter,
                "latitude": latitude,
                "longitude": longitude,
                "families": families,
                "people": people,
                "tents": tents,
                "observation_date": "updated 2023-03-06 18:30",
                "source_id": "indeci_emergency_report_1733",
                "source_page": "6",
                "source_coordinate_header": "Coordenadas UTM, Zona 18",
                "interpreted_crs": "EPSG:4326",
                "coordinate_quality": "candidate_requires_verification",
                "geometry_role": "response_location_context",
                "interpretation_limit": (
                    "The report labels these as UTM, but the numeric values are latitude/longitude; "
                    "verify against another official source before precise spatial use. A shelter "
                    "coordinate is not an affected-building or hazard-footprint coordinate."
                ),
            }
        )
    write_csv(output / "affected_location_context.csv", shelter_rows)
    write_point_geojson(output / "indeci_response_locations.geojson", shelter_rows)

    anchor_rows = []
    for anchor_id, longitude, latitude, easting, northing, page, figure in INGEMMET_ANCHORS:
        anchor_rows.append(
            {
                **COMMON,
                "anchor_id": anchor_id,
                "longitude": longitude,
                "latitude": latitude,
                "source_easting_utm18s": easting,
                "source_northing_utm18s": northing,
                "source_crs": "WGS84 / UTM zone 18S (EPSG:32718)",
                "source_id": "ingemmet_a7367",
                "source_page": page,
                "source_figure": figure,
                "geometry_role": "field_coordinate_anchor",
                "interpretation_limit": "Point anchor only; not an observed hazard polygon",
            }
        )
    write_point_geojson(output / "ingemmet_field_anchors.geojson", anchor_rows)

    previews = []
    if not args.skip_previews:
        preview_dir = output / "official_report_previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        for pdf, page, name in [
            (INGEMMET, 53, "ingemmet_a7367_p53_observed_flow_detail"),
            (INGEMMET, 75, "ingemmet_a7367_p75_map7_hazard_cartography"),
            (INDECI, 2, "indeci_1733_p02_damage_update"),
            (INDECI, 6, "indeci_1733_p06_shelter_locations"),
        ]:
            prefix = preview_dir / name
            render_preview(pdf, page, prefix)
            previews.append(str((prefix.with_suffix(".png")).relative_to(ROOT)))

    manifest = {
        "event_id": COMMON["event_id"],
        "claim_level": COMMON["claim_level"],
        "enters_pim_score": False,
        "evidence_rows": len(EVIDENCE),
        "affected_location_context_rows": len(shelter_rows),
        "ingemmet_field_anchor_rows": len(anchor_rows),
        "gis_layers": [
            "ingemmet_field_anchors.geojson",
            "indeci_response_locations.geojson",
        ],
        "preview_files": previews,
        "next_step": "digitize event-specific classes from INGEMMET Map 7 with page/class lineage",
    }
    (output / "evidence_packet_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
