#!/usr/bin/env python3
"""Write source and provenance tables for the Zimbabwe-Peru comparison pack."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/zimbabwe_peru_prototype_comparison"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def criteria_rows() -> list[dict[str, str]]:
    return [
        row(
            "Flood (FH)",
            "SRTM-derived TWI / drainage proximity plus CHIRPS rainy-season climatology",
            "30 m terrain; ~5 km rainfall aligned for scenario compatibility",
            "terrain conditioning plus coarse rainfall sensitivity layer",
            "SRTM-derived TWI / drainage proximity plus CHIRPS rainy-season climatology",
            "30 m terrain; ~5 km rainfall aligned for scenario compatibility",
            "terrain conditioning plus coarse rainfall sensitivity layer",
            "NASA SRTM 1 Arc-Second + CHIRPS v3",
            "provisional / sensitivity_scenario",
        ),
        row(
            "Sediment (SR)",
            "SoilGrids K-factor, SRTM LS-factor, WorldCover C-factor",
            "30-250 m",
            "factor structure only; rainfall erosivity not applied",
            "SoilGrids K-factor, SRTM LS-factor, WorldCover C-factor",
            "30-250 m",
            "factor structure only; rainfall erosivity not applied",
            "SoilGrids + SRTM + ESA WorldCover",
            "diagnostic_only",
        ),
        row(
            "Land Use / ASM (LU)",
            "ESA WorldCover 2021 C-factor plus USGS Africa GIS mineral reference proximity",
            "10 m land cover; vector mining reference to 30 m grid",
            "land-cover pressure plus public mining reference layer; not local ASM mapping",
            "ESA WorldCover 2021 land-use pressure plus INGEMMET official small-mining point proximity",
            "10 m land cover; point data to 30 m grid",
            "land-cover pressure plus stronger official-source mining point evidence",
            "ESA WorldCover v200 (2021); Zimbabwe USGS Africa GIS; Peru INGEMMET GEOCATMIN",
            "provisional",
        ),
        row(
            "Environmental (ES)",
            "WorldCover water/wetland classes, JRC surface-water occurrence, Geoportal water areas, WDPCA protected-area proximity",
            "10-30 m grid plus vector proximity",
            "provisional environmental-sensitivity indicator; not ecological valuation",
            "WorldCover water/wetland classes, Geofabrik OSM water, and SERNANP national definitive protected-area proximity (layer 0)",
            "10-30 m grid plus vector proximity",
            "provisional environmental-sensitivity indicator; no layer-0 SERNANP geometry occurs in the PE1 + 5 km context zone; other protected-area layers were not queried",
            "ESA WorldCover + JRC GSW / WDPCA / Geofabrik OSM / SERNANP layer 0",
            "provisional",
        ),
        row(
            "Socioeconomic (SV)",
            "OSM road proximity",
            "vector to 30 m grid",
            "access and infrastructure indicator",
            "OSM road proximity plus WorldPop population and OSM mapped-building exposure",
            "vector and ~100 m population evidence aligned to 30 m grid",
            "provisional access and infrastructure-exposure indicator; poverty and health context remain outside the PIM",
            "Geofabrik OSM (ODbL) + WorldPop 2020",
            "provisional",
        ),
    ]


def row(
    criterion: str,
    zimbabwe_source: str,
    zimbabwe_resolution: str,
    zimbabwe_evidence_strength: str,
    peru_source: str,
    peru_resolution: str,
    peru_evidence_strength: str,
    shared_product: str,
    claim_level: str,
) -> dict[str, str]:
    return {
        "criterion": criterion,
        "zimbabwe_source": zimbabwe_source,
        "zimbabwe_resolution": zimbabwe_resolution,
        "zimbabwe_evidence_strength": zimbabwe_evidence_strength,
        "peru_source": peru_source,
        "peru_resolution": peru_resolution,
        "peru_evidence_strength": peru_evidence_strength,
        "shared_product": shared_product,
        "claim_level": claim_level,
    }


def provenance_rows() -> list[dict[str, str]]:
    return [
        provenance(
            "SRTM 1 Arc-Second",
            "NASA SRTM (2000)",
            "USGS EROS / ESA STEP mirror",
            "30 m",
            "2000-02",
            "public; cite DOI 10.5066/F7PR7TFT",
            "flood conditioning and LS factor",
            "context/docs/data-management/registry/srtm_1arcsec_zimbabwe_prototype.md",
        ),
        provenance(
            "ESA WorldCover",
            "v200 (2021)",
            "ESA WorldCover consortium",
            "10 m",
            "2021 land cover",
            "ESA terms; cite before release",
            "land use/land cover and C-factor",
            "context/docs/data-management/registry/esa_worldcover_2021_v1_methodology.md",
        ),
        provenance(
            "SoilGrids 250 m",
            "2017/2020 release",
            "ISRIC - World Soil Information",
            "250 m",
            "contemporary",
            "CC BY 4.0; attribute ISRIC",
            "K-factor",
            "context/docs/data-management/registry/soilgrids_250m_sediment_candidate.md",
        ),
        provenance(
            "CHIRPS v3",
            "v3",
            "UCSB Climate Hazards Center",
            "~5 km (0.05 degree)",
            "2014/15-2023/24 rainy seasons",
            "CC0 / CC BY 4.0",
            "rainfall sensitivity layer",
            "context/docs/data-management/registry/chirps_v3_zimbabwe_prototype.md",
        ),
        provenance(
            "USGS Africa GIS mineral industries",
            "USGS data release, 2021",
            "U.S. Geological Survey",
            "vector",
            "compiled 2008-2019",
            "public domain; cite DOI 10.5066/P97EQWXP",
            "Zimbabwe mining / ASM activity indicator",
            "context/docs/data-management/registry/usgs_africa_gis_mineral_zimbabwe_prototype.md",
        ),
        provenance(
            "Geofabrik OSM",
            "download-time extract",
            "Geofabrik / OpenStreetMap contributors",
            "vector",
            "current at download",
            "ODbL",
            "roads and access indicators",
            "context/docs/data-management/registry/geofabrik_osm_zimbabwe_prototype.md",
        ),
        provenance(
            "INGEMMET ASM",
            "catastro minero",
            "INGEMMET (Peru)",
            "point",
            "Memorando N 0738-2014",
            "referential, consultation only",
            "Peru mining / ASM activity indicator",
            "context/docs/data-management/registry/ingemmet_catastro_minero_peru_pilot.md",
        ),
        provenance(
            "JRC Global Surface Water / protected-area context",
            "GSW v1 context; WDPCA/OSM extracts",
            "European Commission JRC / WDPCA / OpenStreetMap contributors",
            "30 m equivalent raster plus vector",
            "surface-water history and current protected-area mapping",
            "mixed public/open data; check source-specific licence before release",
            "Water/wetland-led environmental context indicator; not complete ecological sensitivity valuation",
            "outputs/boundary_v1/environmental_sensitivity_v0_1/environmental_sensitivity_manifest.csv",
        ),
    ]


def provenance(
    dataset: str,
    version: str,
    provider: str,
    native_resolution: str,
    temporal_coverage: str,
    license_text: str,
    used_for: str,
    registry: str,
) -> dict[str, str]:
    return {
        "dataset": dataset,
        "version": version,
        "provider": provider,
        "native_resolution": native_resolution,
        "temporal_coverage": temporal_coverage,
        "license": license_text,
        "used_for": used_for,
        "registry": registry,
    }


def write_source_tables(out_dir: Path = OUT_DIR) -> None:
    criteria = criteria_rows()
    provenance_data = provenance_rows()
    write_csv(out_dir / "criteria_data_sources_bilateral.csv", criteria)
    write_csv(out_dir / "core_datasets_provenance.csv", provenance_data)
    write_criteria_markdown(out_dir / "criteria_data_sources_bilateral.md", criteria)
    write_provenance_markdown(out_dir / "core_datasets_provenance.md", provenance_data)


def write_criteria_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Core Criteria Sources: Zimbabwe and Peru Prototype Comparison",
        "",
        "Status: `sensitivity_scenario` / `provisional` — used for prototype priority scoring, not final flood-risk claims.",
        "",
        "Each row is one mentor PIM main criterion. The two sites use the same five top-level criteria in the executable overlay. Flood and Land Use / ASM still have internal component layers; Environmental is implemented as a provisional water/wetland and protected-area sensitivity indicator.",
        "",
        "| Criterion | Zimbabwe source | Resolution | Evidence strength | Peru source | Resolution | Evidence strength | Shared product |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| **{item['criterion']}** | {item['zimbabwe_source']} | {item['zimbabwe_resolution']} | "
            f"{item['zimbabwe_evidence_strength']} | {item['peru_source']} | {item['peru_resolution']} | "
            f"{item['peru_evidence_strength']} | {item['shared_product']} |"
        )
    lines.extend([
        "",
        "## Main asymmetry",
        "",
        "- **The southern Peru comparison catchment** (Arequipa Region, mainly the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city) uses official-source INGEMMET small-mining points.",
        "- **Zimbabwe Upper Mzingwane prototype** uses the public USGS Africa GIS mineral reference layer. It is stronger than the earlier OSM-only evidence, but it is still not a local ASM activity map.",
        "",
        "This supports the current data request: ask whether Zimbabwe ASM mapping, active-site points, or disturbance footprints can be obtained.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_provenance_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Core Dataset Provenance",
        "",
        "Status: data products used by the active five-main-criterion PIM prototype comparison.",
        "",
        "| Dataset | Version | Provider | Native resolution | Temporal coverage | License | Used for | Registry |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| **{item['dataset']}** | {item['version']} | {item['provider']} | {item['native_resolution']} | "
            f"{item['temporal_coverage']} | {item['license']} | {item['used_for']} | `{item['registry']}` |"
        )
    lines.extend([
        "",
        "## Main data-quality note",
        "",
        "The strongest cross-country asymmetry is the mining layer: Peru has official-source INGEMMET small-mining points, while Zimbabwe uses the public USGS mineral reference layer and still needs local ASM mapping if available.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    write_source_tables()
    print(f"Wrote source tables to {OUT_DIR}")


if __name__ == "__main__":
    main()
