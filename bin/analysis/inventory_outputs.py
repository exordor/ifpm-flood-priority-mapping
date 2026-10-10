#!/usr/bin/env python3
"""Build a complete, purpose-labelled inventory of the local outputs tree."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "outputs"
REPORT_DIR = OUTPUTS / "project_checks/output_inventory_2026-08-18"


# Status is about present-day use, not scientific validity.
DIRECTORIES: dict[str, tuple[str, str, str, str]] = {
    "[root]": ("directory index", "outputs root notes, historical indexes and small planning records", "not used in scoring", "keep the notes; hidden files can be cleaned up"),
    "boundary_v1": ("frozen baseline", "Zimbabwe Upper Mzingwane former criteria, rainfall and priority workflow", "historical comparison/method provenance", "keep, read-only"),
    "chirps_v3_zimbabwe_prototype": ("frozen baseline", "Zimbabwe CHIRPS rainfall comparison and figures", "coarse-resolution rainfall background", "keep, read-only"),
    "esa_worldcover_2021_goslar": ("Goslar current chain", "Goslar WorldCover/CLMS land cover and C-factor derived layers", "feeds or explains the land-cover criterion", "keep"),
    "esa_worldcover_2021_peru_pilot": ("frozen baseline", "WorldCover/C-factor for the former Peru pilot area", "former Peru land-cover criterion input", "keep, read-only"),
    "esa_worldcover_2021_v1_methodology": ("frozen baseline", "Zimbabwe V1 WorldCover/C-factor", "former method input", "keep, read-only"),
    "geofabrik_osm_peru_pilot": ("frozen baseline", "OSM road and mining-proximity indicators for the former Peru pilot area", "former proxy indicator", "keep, read-only"),
    "goslar_2017_satellite_validation": ("Goslar validation", "Sentinel-2 water-body candidate change before and after 2017", "L2 independent consistency evidence, not used in scoring", "keep"),
    "goslar_focus_boundary": ("Goslar current chain", "Goslar layout focus extent boundary", "clip and display extent, not a catchment", "keep"),
    "goslar_harz_2024_focus_area": ("Goslar validation", "focus area source register, event evidence and location maps", "extent/event context", "keep"),
    "goslar_l2_independent_consistency": ("Goslar validation", "Goslar L2 independent consistency statistics", "supports L2 evidence level, not used in PIM", "keep"),
    "goslar_mining_context_overlay": ("Goslar context", "LBEG/OSM mining context overlay", "external background layer, weight 0", "keep"),
    "goslar_official_hydrology_and_flood_data": ("Goslar validation", "official hydrology boundaries and HWRM flood scenario boundaries", "external validation/extent background, not used in scoring", "keep"),
    "goslar_qgis_project_package": ("Goslar delivery", "Goslar FullAudit workspace QGIS package, styles and QA", "audit project source; use the exports package for formal delivery", "keep"),
    "goslar_qgis_project_package_compact": ("Goslar delivery", "Goslar ReviewMap workspace QGIS package", "compact review project source", "keep"),
    "goslar_sentinel_bare_soil_candidate": ("Goslar support", "Sentinel-2 bare-soil frequency and NDVI change candidate layers", "land-cover upgrade diagnostic", "keep"),
    "hydrosheds_boundary_decision": ("historical method", "Upper Mzingwane boundary candidate diagnostic", "boundary selection provenance", "keep, small files"),
    "indeci_sinpad_peru_flood_events": ("frozen baseline", "SINPAD flood event summary for the former Peru area", "historical event context", "keep, read-only"),
    "inei_peru_poverty_2018": ("frozen baseline", "INEI Arequipa poverty data register", "former socio-economic source record", "keep, read-only"),
    "ingemmet_catastro_minero_peru_pilot": ("frozen baseline", "official mining-concession pressure layer for the former Peru pilot area", "former mining-pressure input", "keep, read-only"),
    "mapbiomas_peru_collection3_change_pilot": ("Secocha support", "MapBiomas multi-period land change alignment and indicators", "land change candidate/sensitivity evidence", "keep"),
    "mentor_voi_rainfall_intake": ("historical method", "structure and field inventory of the supervisor-provided rainfall archive", "source provenance", "keep, small files"),
    "methodology_figures": ("method documentation", "editable method flowcharts and exported figures", "report/thesis method documentation", "keep; hidden backups can be cleaned up"),
    "peru_boundary_discovery": ("frozen baseline", "former Peru boundary discovery and topology checks", "site selection provenance", "keep, read-only"),
    "peru_gap_closure_analysis": ("frozen baseline", "former Peru population/SINPAD and PIM co-location analysis", "former data gap analysis", "keep, read-only"),
    "peru_integrated_briefing_board": ("report support", "Peru integrated briefing board", "former area briefing figure", "keep, read-only"),
    "peru_pilot_boundary": ("frozen baseline", "former southern Peru pilot boundary and pre-checks", "former comparison extent", "keep, read-only"),
    "peru_report_figure_chain": ("report support", "Peru factor-to-result report figure chain", "former Peru figures", "keep, read-only"),
    "peru_scope": ("Secocha current chain", "current Peru/Secocha study area activation and coverage audit", "controls the actual study extent", "keep"),
    "peru_secocha_a7367_reference_extent_v1": ("Secocha current chain", "full Secocha outputs for the five criteria, inputs and priority", "main directory for the current Secocha provisional PIM", "keep"),
    "peru_secocha_boundary": ("Secocha current chain", "Secocha active reference extent boundary", "clip and reference extent", "keep"),
    "peru_secocha_qgis_project_package": ("Secocha delivery", "Secocha FullAudit workspace QGIS package", "audit project source; use the exports package for formal delivery", "keep"),
    "peru_secocha_qgis_project_package_compact": ("Secocha delivery", "Secocha ReviewMap workspace QGIS package", "compact review project source", "keep"),
    "pim_environmental_sensitivity": ("historical method", "early environmental sensitivity summary", "method provenance, not a current result", "can be archived later"),
    "presentation_assets": ("presentation material", "QGIS screenshots, GeoTIFFs and collage assets", "slide deck production input", "keep assets currently in use"),
    "presentation_previews": ("presentation material", "current editable PPT, rendered slides and contact sheet", "slide deck QA", "keep"),
    "project_checks": ("engineering QA", "terminology, inventories and project-wide check reports", "engineering audit, not used in scoring", "keep"),
    "secocha_2023_validation": ("Secocha validation", "2023 event evidence, locations, satellite processing and comparison figures", "provisional validation evidence, not used in PIM", "keep"),
    "slide_ready_figures": ("presentation material", "slide-ready priority, criteria and overlay figures", "presentation/appendix figures", "keep"),
    "soilgrids_250m_peru_pilot": ("frozen baseline", "former Peru SoilGrids K-factor", "former soil erosion input", "keep, read-only"),
    "soilgrids_250m_sediment_candidate": ("frozen baseline", "Zimbabwe SoilGrids K-factor candidate", "former erosion factor input", "keep, read-only"),
    "srtm_1arcsec_goslar": ("Goslar current chain", "Goslar terrain, hydrology, five-criteria and priority outputs", "main directory for the current diagnostic_only PIM; directory name kept for historical compatibility", "keep"),
    "srtm_1arcsec_peru_pilot": ("frozen baseline", "full terrain, criteria and scenario set for the former Peru pilot area", "frozen, not the current Secocha main line", "keep, read-only"),
    "srtm_1arcsec_zimbabwe_prototype": ("frozen baseline", "Zimbabwe terrain, hydrology and erosion derived layers", "former area comparison baseline", "keep, read-only"),
    "v1_working_boundary": ("frozen baseline", "Upper Mzingwane frozen working boundary and figures", "former Zimbabwe spatial extent", "keep, read-only"),
    "worldpop_peru_population": ("frozen baseline", "WorldPop Peru subset register", "former population source record", "keep, read-only"),
    "zimbabwe_geoportal_subcatchments_2025": ("frozen baseline", "Zimbabwe Geoportal and HydroBASINS overlap summary", "former boundary provenance", "keep, read-only"),
    "zimbabwe_integrated_briefing_board": ("report support", "Zimbabwe integrated briefing board", "former area briefing figure", "keep, read-only"),
    "zimbabwe_report_figure_chain": ("report support", "Zimbabwe factor-to-result report figure chain", "former Zimbabwe figures", "keep, read-only"),
}


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError


def file_role(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix == ".qgz":
        return "QGIS project file"
    if suffix == ".qml":
        return "QGIS layer style"
    if "manifest" in name or "lineage" in name or "registry" in name:
        return "source/run manifest"
    if "diagnostic" in name or "qa" in name or "check" in name or "coverage" in name:
        return "quality check/diagnostic"
    if suffix in {".tif", ".tiff"}:
        return "raster input, derived layer or scoring result"
    if suffix in {".gpkg", ".geojson"}:
        return "vector boundary, event or context layer"
    if suffix in {".png", ".pdf", ".svg", ".webp"}:
        return "map, chart or rendered preview"
    if suffix in {".csv", ".json", ".xml", ".ndjson"}:
        return "structured result, parameters or check record"
    if suffix in {".md", ".txt"}:
        return "notes, conclusions or handover record"
    if suffix in {".pptx", ".xlsx", ".drawio"}:
        return "editable deliverable"
    if suffix == ".bkp" or name.startswith("."):
        return "hidden file or editor backup"
    return "other generated file"


def main() -> None:
    generated = datetime.now(timezone.utc).isoformat()
    files = sorted(
        path
        for path in OUTPUTS.rglob("*")
        if path.is_file() and REPORT_DIR not in path.parents
    )
    top_dirs = ["[root]", *sorted(path.name for path in OUTPUTS.iterdir() if path.is_dir())]
    missing = sorted(set(top_dirs) - set(DIRECTORIES))
    if missing:
        raise RuntimeError(f"Unclassified output directories: {missing}")

    rows: list[dict[str, object]] = []
    for path in files:
        relative = path.relative_to(ROOT)
        top = relative.parts[1] if len(relative.parts) > 2 else "[root]"
        group, purpose, scoring_relation, retention = DIRECTORIES[top]
        stat = path.stat()
        rows.append(
            {
                "path": relative.as_posix(),
                "top_directory": top,
                "group": group,
                "file_role": file_role(path),
                "directory_purpose": purpose,
                "scoring_or_evidence_role": scoring_relation,
                "retention": retention,
                "extension": path.suffix.lower() or "[none]",
                "size_bytes": stat.st_size,
                "size_human": human_size(stat.st_size),
                "modified_local": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
            }
        )

    summary: list[dict[str, object]] = []
    by_top: dict[str, list[dict[str, object]]] = {name: [] for name in top_dirs}
    for row in rows:
        by_top[str(row["top_directory"])].append(row)
    for top in top_dirs:
        group, purpose, scoring_relation, retention = DIRECTORIES[top]
        size = sum(int(row["size_bytes"]) for row in by_top[top])
        summary.append(
            {
                "directory": top,
                "group": group,
                "purpose": purpose,
                "scoring_or_evidence_role": scoring_relation,
                "retention": retention,
                "file_count": len(by_top[top]),
                "size_bytes": size,
                "size_mib": round(size / 1024 / 1024, 2),
                "size_human": human_size(size),
            }
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REPORT_DIR / "all_output_files.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary_path = REPORT_DIR / "output_directory_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    total_bytes = sum(int(row["size_bytes"]) for row in rows)
    groups = Counter(str(row["group"]) for row in summary)
    largest = sorted(summary, key=lambda row: int(row["size_bytes"]), reverse=True)
    md = [
        "# IFPM outputs files and purpose inventory",
        "",
        f"Generated: {generated}",
        "",
        f"The current `outputs/` tree holds **{len(rows):,} files** totalling **{human_size(total_bytes)}**, spread across **{len(summary)} top-level directories**.",
        "See `all_output_files.csv` for the full per-file listing; the table below gives a quick view of each directory's role and retention policy.",
        "",
        "## Top-level directory purposes",
        "",
        "| Directory | Group | Files | Size | Purpose | Scoring/evidence role | Recommendation |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in sorted(summary, key=lambda item: (str(item["group"]), str(item["directory"]))):
        md.append(
            f"| `{row['directory']}` | {row['group']} | {row['file_count']} | {row['size_human']} | "
            f"{row['purpose']} | {row['scoring_or_evidence_role']} | {row['retention']} |"
        )
    md.extend(["", "## Largest directories by disk usage", ""])
    for index, row in enumerate(largest[:10], 1):
        md.append(f"{index}. `{row['directory']}` — {row['size_human']} / {row['file_count']} files")
    md.extend(
        [
            "",
            "## Reading rules",
            "",
            "- `Goslar current chain` and `Secocha current chain`: current outputs used for model computation or extent control.",
            "- `validation`, `context`: used for independent evidence or map interpretation; not used in PIM unless the manifest explicitly says so.",
            "- `delivery`: workspace QGIS build results; what is actually sent to recipients is `exports/qgis_packages/`.",
            "- `frozen baseline`: kept for historical comparison and reproduction; do not write to it further or treat it as current Secocha/Goslar results.",
            "- This inventory describes file purposes; it does not upgrade diagnostic/provisional outputs to final flood-risk conclusions.",
            "",
            f"File type counts: {dict(Counter(str(row['extension']) for row in rows).most_common())}",
            f"Directory group counts: {dict(groups)}",
        ]
    )
    (REPORT_DIR / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    chart_labels = {
        "srtm_1arcsec_peru_pilot": "Peru pilot (frozen)",
        "peru_secocha_a7367_reference_extent_v1": "Secocha A7367",
        "srtm_1arcsec_zimbabwe_prototype": "Zimbabwe prototype",
        "goslar_2017_satellite_validation": "Goslar 2017 validation",
        "ingemmet_catastro_minero_peru_pilot": "Peru INGEMMET",
    }
    top_chart = [
        dict(row, rank=index + 1, chart_label=chart_labels.get(str(row["directory"]), str(row["directory"])))
        for index, row in enumerate(largest[:6])
    ]
    composition = [
        {
            "label": chart_labels.get(str(row["directory"]), str(row["directory"])),
            "size_mib": row["size_mib"],
            "directory": row["directory"],
            "file_count": row["file_count"],
        }
        for row in largest[:5]
    ]
    composition.append(
        {
            "label": "Other outputs",
            "size_mib": round(sum(int(row["size_bytes"]) for row in largest[5:]) / 1024 / 1024, 2),
            "directory": "all remaining directories",
            "file_count": sum(int(row["file_count"]) for row in largest[5:]),
        }
    )
    source = {
        "id": "outputs_inventory",
        "label": "IFPM outputs filesystem inventory",
        "path": "outputs/project_checks/output_inventory_2026-08-18/output_directory_summary.csv",
        "query": {
            "engine": "DuckDB",
            "language": "sql",
            "sql": "SELECT * FROM read_csv_auto('output_directory_summary.csv')",
            "description": "Read the generated top-level outputs directory inventory.",
            "tables_used": ["output_directory_summary.csv"],
            "filters": ["regular files under outputs only", "inventory report files excluded"],
            "metric_definitions": [
                "file_count is the count of regular files below each top-level output directory",
                "size_mib is the sum of file sizes divided by 1024^2",
            ],
        },
    }
    artifact = {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "IFPM outputs files and purpose inventory",
            "description": "Purpose, status, disk usage and retention advice for the current outputs directories.",
            "generatedAt": generated,
            "sources": [source],
            "blocks": [
                {"id": "title", "type": "markdown", "body": "# IFPM outputs files and purpose inventory"},
                {
                    "id": "technical-summary",
                    "type": "markdown",
                    "sourceId": "outputs_inventory",
                    "body": (
                        f"## Current outputs are dominated in size by the former Peru pilot baseline\n\n"
                        f"The inventory covers **{len(rows):,} files, {human_size(total_bytes)}, {len(summary)} top-level directories**. "
                        "The Goslar and Secocha current chains, validation evidence and QGIS workspace packages are labelled separately; "
                        "frozen baselines are kept for reproducibility and must not be treated as current model results."
                    ),
                },
                {
                    "id": "size-finding",
                    "type": "markdown",
                    "sourceId": "outputs_inventory",
                    "body": "## Storage is concentrated in a few frozen baseline directories\n\nThe chart below shows the disk usage composition; the Top 10 ranking in `README.md` and `output_directory_summary.csv` give exact values. Whether to delete anything still depends on reproducibility and historical comparison needs.",
                },
                {"id": "size-chart", "type": "chart", "chartId": "storage_composition"},
                {
                    "id": "usage-guide",
                    "type": "markdown",
                    "body": "## Usage guide and limitations\n\n**Details:** `README.md` and `output_directory_summary.csv` list all top-level directories; `all_output_files.csv` lists 1,134 files.\n\n**Current models:** Goslar uses `srtm_1arcsec_goslar/`, Secocha uses `peru_secocha_a7367_reference_extent_v1/`; the four `*_qgis_project_package*` directories are workspace projects, and external deliverables are in `exports/qgis_packages/`.\n\n**Historical baselines:** `srtm_1arcsec_peru_pilot/`, `boundary_v1/` and the Zimbabwe prototype are kept read-only. Whether to keep the roughly 898 MiB Peru pilot should depend on reproducibility needs.\n\n**Scope:** Counts regular files under `outputs/` recursively, excluding `data/` and `exports/`. Directory purposes do not replace the scientific statements in each raster/manifest; a new unclassified directory makes the inventory script fail.",
                },
            ],
            "cards": [],
            "charts": [
                {
                    "id": "storage_composition",
                    "title": "outputs disk usage composition",
                    "subtitle": "five largest top-level directories plus all others combined, MiB",
                    "type": "pie",
                    "intent": "composition",
                    "dataset": "storage_composition",
                    "sourceId": "outputs_inventory",
                    "encodings": {
                        "x": {"field": "label", "type": "nominal", "label": "directory"},
                        "y": {"field": "size_mib", "type": "quantitative", "label": "MiB", "unit": "MiB"},
                        "tooltip": [
                            {"field": "directory", "type": "text", "label": "directory"},
                            {"field": "file_count", "type": "quantitative", "label": "file count"},
                        ],
                    },
                    "valueFormat": "number",
                    "unit": "MiB",
                    "maxRows": 6,
                }
            ],
            "tables": [],
        },
        "snapshot": {
            "version": 1,
            "generatedAt": generated,
            "status": "ready",
            "datasets": {
                "headline": [{"file_count": len(rows), "size_mib": round(total_bytes / 1024 / 1024, 2), "directory_count": len(summary)}],
                "largest_directories": top_chart,
                "storage_composition": composition,
                "directory_summary": summary,
            },
        },
        "sources": [source],
    }
    (REPORT_DIR / "artifact.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"files": len(rows), "directories": len(summary), "bytes": total_bytes, "report_dir": str(REPORT_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
