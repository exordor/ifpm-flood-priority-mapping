#!/usr/bin/env python3
"""Prepare criteria_stack_v0_2 inventory tables for boundary_v1."""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SWEEP = ROOT / "outputs/v1_full_methodology_evidence_sweep"
V01 = ROOT / "outputs/v1_autonomous_prototype_v0_1"
BOUNDARY_ID = "boundary_v1"
EXPERIMENT_ID = "criteria_stack_v0_2"
OUT = ROOT / f"outputs/{BOUNDARY_ID}/{EXPERIMENT_ID}"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def row_by_layer(df: pd.DataFrame, layer: str) -> dict[str, object]:
    match = df[df["layer"] == layer]
    if match.empty:
        return {}
    return match.iloc[0].to_dict()


def fmt(value: object) -> str:
    if value is None or value == "":
        return ""
    try:
        if pd.isna(value):
            return ""
        number = float(value)
        if number.is_integer():
            return str(int(number))
        return f"{number:.3f}"
    except (TypeError, ValueError):
        return str(value)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_gap_table() -> list[dict[str, object]]:
    return [
        {
            "criterion_family": "landuse_asm_pressure",
            "current_v0_1_evidence": "WorldCover C-factor pressure plus OSM mining-proxy proximity",
            "current_strength": "weak_to_medium",
            "hardening_gap": "OSM quarry/industrial proxy is not official active ASM evidence.",
            "requested_dataset": "official ASM sites, concessions/claims with active status, active disturbance polygons",
            "trip_priority": "must_ask_zimbabwe",
            "candidate_update_rule": "replace or supplement OSM proxy only if source is official, dated, spatial, and overlaps boundary_v1",
            "if_missing": "keep mining as weak proxy/context; do not claim official mining pressure",
        },
        {
            "criterion_family": "socioeconomic_exposure",
            "current_v0_1_evidence": "OSM road/access proximity",
            "current_strength": "medium_proxy",
            "hardening_gap": "Road proximity does not encode observed damage, vulnerable people, or exposed assets.",
            "requested_dataset": "affected settlements, flood-damaged roads/bridges, critical infrastructure, local population/asset data",
            "trip_priority": "must_ask_zimbabwe_and_peru",
            "candidate_update_rule": "separate access proxy from true exposure; keep coarse population as context unless aggregation rule is accepted",
            "if_missing": "keep road/access proxy and label it as access/exposure proxy, not socioeconomic vulnerability",
        },
        {
            "criterion_family": "flood_validation",
            "current_v0_1_evidence": "Geoportal flood-prone local overlap 0; DFO points within V1+1deg 0",
            "current_strength": "missing",
            "hardening_gap": "No local observed flood extent or damage layer for validation.",
            "requested_dataset": "flood extents, event reports, affected places/roads, dates and damage notes",
            "trip_priority": "must_ask_zimbabwe_and_peru",
            "candidate_update_rule": "use only as validation/context until modelling-unit and interpretation rules are accepted",
            "if_missing": "do not call hotspot map validated flood risk",
        },
        {
            "criterion_family": "rainfall_r",
            "current_v0_1_evidence": "ERA5/CHIRPS/Voi context only; no accepted 30 m rainfall layer",
            "current_strength": "uncertain_context",
            "hardening_gap": "R/rainfall source and time step remain method-sensitive.",
            "requested_dataset": "local rain gauge records with station metadata, preferably sub-daily; daily if that is all available",
            "trip_priority": "must_ask_zimbabwe_and_peru",
            "candidate_update_rule": "keep rainfall native/zonal; do not resample rainfall to 30 m as pixel evidence",
            "if_missing": "keep R as uncertainty module; do not produce final sediment magnitude",
        },
        {
            "criterion_family": "boundary_outlet",
            "current_v0_1_evidence": "V1 HydroBASINS-derived controlled prototype boundary",
            "current_strength": "prototype_only",
            "hardening_gap": "Mentor accepted V1 for controlled prototype, not final thesis boundary.",
            "requested_dataset": "marked outlet point/river section or official/local catchment polygon",
            "trip_priority": "must_ask_zimbabwe_and_peru",
            "candidate_update_rule": "preserve boundary_v1 baseline unless a better outlet/catchment is explicitly confirmed",
            "if_missing": "keep V1 as prototype-only working boundary",
        },
    ]


def build_upgrade_matrix(layer_summary: pd.DataFrame, raster_summary: pd.DataFrame) -> list[dict[str, object]]:
    layer = lambda name: row_by_layer(layer_summary, name)
    raster = lambda name: row_by_layer(raster_summary, name)
    candidates = [
        ("OSM mining proxy", layer("osm_mining_proxy_v1"), "mining", "weak_proxy", "context_or_proxy_only"),
        ("Mining-proxy proximity raster", layer("closeness_to_mining_proxy_0_1"), "mining", "weak_proxy_grid", "v0_1_retained_if_no_official_data"),
        ("OSM roads", layer("osm_roads_v1"), "exposure", "medium_access_proxy", "access_proxy"),
        ("OSM bridges", layer("osm_bridges_v1"), "exposure", "medium_infrastructure_proxy", "context_or_crossing_input"),
        ("Road-river crossings", layer("road_river_crossings_v1"), "exposure", "medium_flood_exposure_proxy", "candidate_v0_2_exposure_component"),
        ("OSM places", layer("osm_places_v1"), "exposure", "medium_settlement_context", "context_or_zonal_summary"),
        ("WorldPop 2020", raster("worldpop_2020_unadj"), "exposure", "medium_population_context", "native_or_zonal_context"),
        ("GHSL population 2025", raster("ghsl_population_2025"), "exposure", "medium_population_context", "native_or_zonal_context"),
        ("GHSL built surface 2025", raster("ghsl_built_surface_2025"), "exposure", "medium_asset_context", "native_or_zonal_context"),
        ("Geoportal flood-prone zones", layer("geoportal_flood_prone_zones_v1"), "flood_validation", "missing_local_overlap", "gap"),
        ("DFO Zimbabwe flood records", layer("dfo_zimbabwe_flood_events"), "flood_validation", "country_context_only", "not_local_validation"),
    ]
    rows = []
    for name, source, family, strength, role in candidates:
        rows.append(
            {
                "candidate_layer": name,
                "criterion_family": family,
                "local_artifact": fmt(source.get("artifact", "")),
                "feature_count": fmt(source.get("feature_count", "")),
                "length_km": fmt(source.get("length_km", "")),
                "area_km2": fmt(source.get("area_km2", "")),
                "valid_cells": fmt(source.get("valid_cells", "")),
                "sum_or_total": fmt(source.get("sum", "")),
                "current_strength": strength,
                "candidate_role": role,
                "hardening_action": action_for(family, strength),
            }
        )
    return rows


def action_for(family: str, strength: str) -> str:
    if family == "mining":
        return "keep as proxy until official ASM/mining data are obtained"
    if family == "exposure" and "population" in strength:
        return "use as context/zonal summary; avoid false 30 m precision"
    if family == "exposure":
        return "compare against hotspots; do not call it vulnerability"
    if family == "flood_validation":
        return "record as gap unless local observed flood evidence is obtained"
    return "review"


def build_manifest() -> list[dict[str, object]]:
    return [
        {
            "criterion": "land_cover_pressure",
            "v0_1_input": "C-factor pressure inside old landuse_asm_pressure average",
            "candidate_status": "split_from_mining_pressure",
            "proposed_change": "use C-factor pressure as separate land-cover criterion",
            "reason": "land-cover protection and mining disturbance are different processes",
        },
        {
            "criterion": "mining_pressure",
            "v0_1_input": "OSM mining-proxy proximity inside old landuse_asm_pressure average",
            "candidate_status": "weak_proxy_until_official_mining_data",
            "proposed_change": "keep as separate mining proxy; do not merge with C-factor",
            "reason": "OSM quarry/industrial evidence is not official active ASM evidence",
        },
        {
            "criterion": "flood_hydrology",
            "v0_1_input": "TWI high-wetness + drainage proximity",
            "candidate_status": "preserve_baseline",
            "proposed_change": "none",
            "reason": "not one of the weakest criteria in current review",
        },
        {
            "criterion": "erosion_structure_proxy",
            "v0_1_input": "R-invariant K x LS x C structure",
            "candidate_status": "renamed_and_masked",
            "proposed_change": "preserve NoData and avoid sediment-risk label",
            "reason": "K x LS x C is only erosion structure without accepted R",
        },
        {
            "criterion": "road_accessibility_proxy",
            "v0_1_input": "road/access proximity inside old socioeconomic_exposure",
            "candidate_status": "diagnostic_only",
            "proposed_change": "exclude from socioeconomic vulnerability claims",
            "reason": "road proximity is access/infrastructure context, not observed vulnerability",
        },
        {
            "criterion": "river_proximity_proxy",
            "v0_1_input": "river/water proximity proxy",
            "candidate_status": "diagnostic_only",
            "proposed_change": "exclude from environmental sensitivity claims",
            "reason": "river proximity alone is not wetlands/protected-area/ecological sensitivity evidence",
        },
    ]


def write_handoff(paths: dict[str, Path]) -> None:
    text = f"""# boundary_v1 / criteria_stack_v0_2 Inventory Handoff

Status: first inventory complete. No new data were downloaded and no overlay was run.

The archived `boundary_v1 / criteria_stack_v0_1` run remains the frozen baseline.
`boundary_v1 / criteria_stack_v0_2` should first harden two weak criteria:

- mining / ASM pressure;
- socioeconomic exposure.

Main outputs:

- `{rel(paths["gap"])}`
- `{rel(paths["upgrade"])}`
- `{rel(paths["manifest"])}`

Main reading:

- Mining remains weak proxy evidence until official ASM/mining data are obtained.
- Exposure should be split into access proxy and population/built-up context.
- Flood validation remains missing locally.
- Rainfall/R remains an uncertainty module, not a 30 m pixel-level layer.

Next action: use the mentor trip data request package to ask for the missing official or observed
datasets before the 18 July trip.
"""
    paths["handoff"].write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    layer_summary = read_csv(SWEEP / "v1_full_methodology_layer_summary.csv")
    raster_summary = read_csv(SWEEP / "v1_raster_layer_summary.csv")
    if not (V01 / "hotspot_stability_summary.csv").exists():
        raise FileNotFoundError(V01 / "hotspot_stability_summary.csv")

    paths = {
        "gap": OUT / "evidence_gap_table.csv",
        "upgrade": OUT / "candidate_data_upgrade_matrix.csv",
        "manifest": OUT / "revised_criteria_manifest.csv",
        "handoff": OUT / "inventory_handoff.md",
    }
    write_csv(paths["gap"], build_gap_table())
    write_csv(paths["upgrade"], build_upgrade_matrix(layer_summary, raster_summary))
    write_csv(paths["manifest"], build_manifest())
    write_handoff(paths)
    print(f"wrote {BOUNDARY_ID} / {EXPERIMENT_ID} inventory to {rel(OUT)}")


if __name__ == "__main__":
    main()
