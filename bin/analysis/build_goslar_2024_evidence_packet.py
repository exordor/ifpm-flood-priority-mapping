#!/usr/bin/env python3
"""Build a source-anchored evidence packet and spatial scope check for Goslar 2024."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "data/validation/goslar_harz_2024_focus_area/source_materials"
DEFAULT_OUTPUT = ROOT / "outputs/goslar_harz_2024_focus_area"
PERU_BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"

COMMON = {
    "focus_area_id": "goslar_harz_2024_focus_extent",
    "claim_level": "validation_candidate",
    "enters_pim_score": "false",
}

# WGS84 extent of the ZLW 2024.04.24 print layout from the QGIS project file.
FOCUS_EXTENT_WGS84 = (10.3646, 51.8544, 10.4194, 51.9089)
# Main canvas extent of ZDIN-2024.qgz, converted from EPSG:3857.
MAIN_CANVAS_WGS84 = (10.33226, 51.75988, 10.51057, 51.83756)

EVIDENCE = [
    {
        **COMMON,
        "observation_id": "qgis_project_layout_extent",
        "evidence_type": "focus_area_extent",
        "value": "ZLW print-layout extent WGS84: 10.3646-10.4194 E, 51.8544-51.9089 N",
        "source_id": "qgis_project",
        "source_page": "layout ZLW2024.04.24Einzugs gebeit & sensors",
        "geometry_role": "focus_extent_reference",
        "interpretation_limit": "Layout extent from project file; not a mapped flood or hazard footprint",
    },
    {
        **COMMON,
        "observation_id": "qgis_project_main_canvas",
        "evidence_type": "focus_area_extent",
        "value": "Main canvas WGS84: 10.3323-10.5106 E, 51.7599-51.8376 N",
        "source_id": "qgis_project",
        "source_page": "theMapCanvas",
        "geometry_role": "focus_extent_reference",
        "interpretation_limit": "Project canvas extent; larger than the printed layout extent",
    },
    {
        **COMMON,
        "observation_id": "qgis_project_layers",
        "evidence_type": "project_context",
        "value": "Layers include DRAINAGE_BASIN_DE, sensor-station CSV, ATKIS DLM25, ALKIS mining shapes, LBEG/NIBIS soil WMS and Inn_Oke_Rad",
        "source_id": "qgis_project",
        "source_page": "layer tree",
        "geometry_role": "layer_inventory",
        "interpretation_limit": "External data sources live on a Windows project path; not bundled with the QGZ",
    },
    {
        **COMMON,
        "observation_id": "zlw_map_catchment_and_sensors",
        "evidence_type": "mapped_context",
        "value": "Printed map shows DRAINAGE_BASIN_DE boundary, sensor locations and ATKIS water features near WS Granetalsperre, Wintertal and Gosetal",
        "source_id": "zlw_catchment_map_pdf",
        "source_page": "1",
        "geometry_role": "mapped_reference",
        "interpretation_limit": "PDF export is a static map; sensor coordinates are not machine-readable in the PDF",
    },
    {
        **COMMON,
        "observation_id": "zdin_2017_flood_catchment",
        "evidence_type": "historical_event_reference",
        "value": "ZDIN slide identifies the catchment area of the 2017 flood in Goslar, sourced to EWAZ Energie- und Wasserspeicher Harz, Ma\u00dfnahme 6: Hochwasserschutz Goslar",
        "source_id": "zdin_study_area_slide",
        "source_page": "slide",
        "geometry_role": "event_context",
        "interpretation_limit": "Slide attribution is a project reference, not an official flood report",
    },
    {
        **COMMON,
        "observation_id": "zdin_intended_study_area",
        "evidence_type": "intended_study_area",
        "value": "Intended study area covers sensor sites near Granetalsperre, Goslar NW, Rosenhof OW, Rammelsberg and further Harz locations",
        "source_id": "zdin_study_area_slide",
        "source_page": "slide",
        "geometry_role": "event_context",
        "interpretation_limit": "Proposed sensor network context, not an observed hazard extent",
    },
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_focus_extent_geojson(path: Path) -> None:
    extent = box(*FOCUS_EXTENT_WGS84)
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[x, y] for x, y in extent.exterior.coords]],
                },
                "properties": {
                    **COMMON,
                    "name": "Goslar Harz 2024 focus-area layout extent",
                    "source": "ZDIN-2024.qgz ZLW print layout",
                    "extent_is_hazard_footprint": False,
                },
            }
        ],
    }
    path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_preview(pdf: Path, output_prefix: Path) -> None:
    subprocess.run(
        ["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-png", "-r", "160", str(pdf), str(output_prefix)],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-previews", action="store_true")
    args = parser.parse_args()
    output = args.output_dir
    write_csv(output / "event_evidence.csv", EVIDENCE)
    write_focus_extent_geojson(output / "goslar_focus_extent.geojson")

    # Spatial scope check: is the Goslar focus area inside the current Peru boundary?
    peru = gpd.read_file(PERU_BOUNDARY).to_crs("EPSG:4326")
    focus_center_wgs84 = ((FOCUS_EXTENT_WGS84[0] + FOCUS_EXTENT_WGS84[2]) / 2,
                          (FOCUS_EXTENT_WGS84[1] + FOCUS_EXTENT_WGS84[3]) / 2)
    center_point = gpd.GeoDataFrame(
        {"name": ["Goslar focus center"]},
        geometry=[box(*FOCUS_EXTENT_WGS84).centroid],
        crs="EPSG:4326",
    )
    inside = bool(center_point.geometry.iloc[0].within(peru.union_all()))
    distance_km = round(
        center_point.to_crs("EPSG:32718").geometry.iloc[0].distance(peru.to_crs("EPSG:32718").union_all()) / 1000, 1
    )
    scope = {
        "focus_area_id": COMMON["focus_area_id"],
        "focus_center_wgs84": focus_center_wgs84,
        "inside_current_peru_boundary": inside,
        "distance_to_peru_boundary_km": distance_km,
        "current_peru_boundary_id": "peru_hybas_l7_6070641200",
        "claim_level": "diagnostic_only",
        "implication": "Goslar is a separate international focus area; it cannot validate the Peru PIM and is not a PIM input.",
    }
    (output / "spatial_scope_check.json").write_text(
        json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    previews = []
    if not args.skip_previews:
        preview_dir = output / "source_previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        prefix = preview_dir / "zlw_catchment_and_sensors"
        render_preview(REPORT_DIR / "ZLW2024.04.24_catchment_and_sensors.pdf", prefix)
        previews.append(str(prefix.with_suffix(".png").relative_to(ROOT)))

    manifest = {
        "focus_area_id": COMMON["focus_area_id"],
        "claim_level": COMMON["claim_level"],
        "enters_pim_score": False,
        "evidence_rows": len(EVIDENCE),
        "preview_files": previews,
        "spatial_scope_check": scope,
        "next_step": "generate focus-area location map",
    }
    (output / "evidence_packet_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
