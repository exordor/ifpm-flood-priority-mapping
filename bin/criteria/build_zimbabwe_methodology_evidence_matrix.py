#!/usr/bin/env python3
"""Build the Upper Mzingwane methodology evidence matrix from prepared summaries."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/v1_full_methodology_evidence_sweep"
RASTER_SUMMARY = OUT_DIR / "v1_raster_layer_summary.csv"
VECTOR_SUMMARY = OUT_DIR / "v1_vector_layer_summary.csv"
SUMMARY_CSV = OUT_DIR / "v1_full_methodology_layer_summary.csv"
EVIDENCE_CSV = OUT_DIR / "v1_full_methodology_evidence_matrix.csv"
REHAB_CSV = OUT_DIR / "v1_rehabilitation_indicator_components.csv"
LANDCOVER_CSV = OUT_DIR / "v1_worldcover_class_area.csv"
GSW_CSV = OUT_DIR / "v1_jrc_surface_water_summary.csv"
GHSL_CSV = OUT_DIR / "v1_ghsl_summary.csv"
DFO_CSV = OUT_DIR / "v1_dfo_zimbabwe_flood_events.csv"
WDPCA_CSV = OUT_DIR / "v1_wdpca_protected_area_summary.csv"
LAYERS_GPKG = OUT_DIR / "v1_full_methodology_review_layers.gpkg"
TERRAIN_DIR = ROOT / "outputs/zimbabwe_terrain_hydrology_factors/terrain_standardization"
RAIN_CSV = ROOT / "outputs/zimbabwe_chirps_v3_rainfall/rainfall_comparison/zimbabwe_rainfall_metric_summary.csv"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def metric(summary: pd.DataFrame, layer: str, field: str, default: float = 0.0) -> float:
    rows = summary[summary["layer"] == layer]
    return float(rows.iloc[0][field]) if not rows.empty and field in rows.columns else default


def evidence_row(factor: str, layer: str, source: str, artifact: Path | str, resolution: str, strength: str, ahp: str, limitation: str) -> dict[str, str]:
    artifact_text = artifact if isinstance(artifact, str) else rel(artifact)
    return {
        "factor": factor,
        "candidate_evidence_layer": layer,
        "source": source,
        "processed_artifact": artifact_text,
        "scale_or_resolution": resolution,
        "evidence_strength": strength,
        "ahp_eligibility": ahp,
        "limitation": limitation,
        "status": "candidate evidence only; no overlay",
    }


def matrix_rows(summary: pd.DataFrame) -> list[dict[str, str]]:
    blocked = "Needs mentor criteria hierarchy and modelling-unit decision before AHP."
    dfo_count = metric(summary, "dfo_zimbabwe_flood_events", "feature_count")
    dfo_near = metric(summary, "dfo_zimbabwe_flood_events", "v1_context_points_plus_1deg")
    wdpca_count = metric(summary, "wdpca_protected_areas_v1", "feature_count")
    return [
        evidence_row("Flood hazard", "Geoportal flood-prone zones local gap", "Zimbabwe Geoportal", LAYERS_GPKG, "vector overlap", "weak/gap", "no", "Upper Mzingwane overlap count is 0; use as gap evidence only."),
        evidence_row("Flood hazard", "JRC surface-water occurrence/seasonality/change", "JRC Global Surface Water", GSW_CSV, "0.00025 degree", "medium/context", "review", "Water history supports flood/wetland context but is not event flood depth. " + blocked),
        evidence_row("Flood hazard", "DFO Zimbabwe historical flood-event context", "Dartmouth Flood Observatory via HDX", DFO_CSV, "global event points / country filter", "weak/context", "no", f"{dfo_count:.0f} Zimbabwe-related records; {dfo_near:.0f} valid event points within a one-degree context window around the Upper Mzingwane prototype. Use as historical context only."),
        evidence_row("Rainfall", "CHIRPS multi-window rainfall comparison", "CHIRPS v3", RAIN_CSV, "0.05 degree native/zonal", "medium", "review", "Rainfall is a hazard driver; CHIRPS must not be treated as 30 m evidence. " + blocked),
        evidence_row("Terrain", "Elevation lowland context", "SRTMGL1 DEM", TERRAIN_DIR / "zimbabwe_elevation_lowland_context_0_1.tif", "30 m", "medium", "review", "Low elevation alone is not flood risk. " + blocked),
        evidence_row("Terrain", "Slope low-slope susceptibility", "SRTMGL1 slope", TERRAIN_DIR / "zimbabwe_slope_low_slope_susceptibility_0_1.tif", "30 m", "medium", "review", "Primary terrain framing for mentor review, not accepted criterion yet."),
        evidence_row("Land use / ASM", "WorldCover land-cover class area", "ESA WorldCover 2021", LANDCOVER_CSV, "10 m", "medium", "review", "Land cover is not active ASM truth; use with OSM mining indicators cautiously."),
        evidence_row("Land use / ASM", "Bare/sparse ground and built-up indicator", "ESA WorldCover + OSM landuse", LANDCOVER_CSV, "10 m / vector", "weak-medium", "review", "Bare/sparse ground may be natural or degraded; OSM quarry/industrial mapping is incomplete."),
        evidence_row("Land use / ASM", "OSM quarry/industrial indicator", "Geofabrik OSM Zimbabwe", LAYERS_GPKG, "vector", "weak", "review/no", "Indicator only; official mining/cadastre or remote-sensing disturbance is still preferred."),
        evidence_row("Environmental sensitivity", "Water/wetland proximity context", "JRC GSW + WorldCover + Geoportal/OSM water", GSW_CSV, "10-30 m equivalent native rasters + vector", "medium", "review", "Surface water and wetland classes are sensitivity context, not ecological valuation."),
        evidence_row("Environmental sensitivity", "Vegetation/land-cover sensitivity", "ESA WorldCover 2021", LANDCOVER_CSV, "10 m", "medium", "review", "Class-based sensitivity needs mentor/domain weighting."),
        evidence_row("Environmental sensitivity", "Official protected/conserved areas", "WDPCA Zimbabwe via HDX", WDPCA_CSV, "vector polygons/points", "medium/context", "review", f"{wdpca_count:.0f} WDPCA features overlap the Upper Mzingwane prototype; use as environmental sensitivity context pending mentor weighting."),
        evidence_row("Socioeconomic vulnerability", "WorldPop population exposure", "WorldPop Zimbabwe 2020", OUT_DIR / "rasters/v1_worldpop_2020_unadj_native.tif", "approx. 100 m", "medium", "review", "Population count is an exposure indicator, not full vulnerability."),
        evidence_row("Socioeconomic vulnerability", "GHSL built-up and population exposure cross-check", "Copernicus Global Human Settlement Layer via HDX", GHSL_CSV, "100 m, Mollweide native", "medium/context", "review", "Built-up surface and population grids cross-check exposure only; they do not encode poverty, coping capacity, or observed flood loss."),
        evidence_row("Socioeconomic vulnerability", "OSM settlements/roads/bridges", "Geofabrik OSM Zimbabwe", LAYERS_GPKG, "vector", "medium", "review", "OSM completeness is uncertain; roads/crossings are exposure proxies."),
        evidence_row("Rehabilitation potential", "Bare/degraded land candidate components", "WorldCover + OSM mining indicators", REHAB_CSV, "mixed native summaries", "weak-medium", "review", "Components only; no rehabilitation score or intervention priority produced."),
        evidence_row("Rehabilitation potential", "Accessibility and river-proximity components", "OSM roads + rivers + crossings", REHAB_CSV, "vector summaries", "medium/context", "review", "Distance/proximity components are not combined or weighted yet."),
    ]


def rehab_rows(summary: pd.DataFrame) -> list[dict[str, object]]:
    land = pd.read_csv(LANDCOVER_CSV)
    rows = [{"component": f"worldcover_{row.class_name}", "value": row.area_km2_approx} for row in land.itertuples()]
    keep = ["distance_to_", "closeness_to_", "osm_mining", "osm_roads", "geoportal_rivers", "road_river"]
    for item in summary.itertuples():
        if any(token in str(item.layer) for token in keep):
            for field in ["feature_count", "length_km", "area_km2", "mean", "max"]:
                if hasattr(item, field) and pd.notna(getattr(item, field)):
                    rows.append({"component": f"{item.layer}_{field}", "value": getattr(item, field)})
    return rows


def main() -> None:
    raster = pd.read_csv(RASTER_SUMMARY)
    vector = pd.read_csv(VECTOR_SUMMARY)
    summary = pd.concat([raster, vector], ignore_index=True)
    summary.to_csv(SUMMARY_CSV, index=False)
    write_csv(REHAB_CSV, rehab_rows(summary))
    write_csv(EVIDENCE_CSV, matrix_rows(summary))
    print(f"wrote {EVIDENCE_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
