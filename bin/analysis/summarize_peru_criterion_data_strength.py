#!/usr/bin/env python3
"""Write an auditable data-strength table for the active Peru PIM criteria."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/srtm_1arcsec_peru_pilot"
PIM_DIR = BASE / "priority_scenarios/pim_criteria"
BOUNDARY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
ENV_COMPONENTS = BASE / "environmental_sensitivity_v0_1/environmental_sensitivity_components.csv"
SOCIO_DIAGNOSTICS = BASE / "exposure_indicators/exposure_indicators_contribution_diagnostics.csv"
MINING_MANIFEST = ROOT / "outputs/ingemmet_catastro_minero_peru_pilot/mining_pressure_manifest.csv"
PIM_SUPPORT = BASE / "priority_scenarios/priority_screening_summary.csv"
SINPAD_COHORTS = ROOT / "outputs/peru_gap_closure_analysis/peru_sinpad_colocation_cohorts.csv"
DEPENDENCY_DIAGNOSTICS = BASE / "priority_scenarios/criterion_dependency_diagnostics.csv"
OUT_CSV = BASE / "priority_scenarios/criterion_data_strength.csv"
OUT_MANIFEST = BASE / "priority_scenarios/criterion_data_strength_manifest.json"

CRITERION_RASTERS = {
    "flood_hazard": PIM_DIR / "flood_hazard_0_1.tif",
    "sediment": PIM_DIR / "sediment_0_1.tif",
    "landuse_asm": PIM_DIR / "landuse_asm_0_1.tif",
    "environmental": PIM_DIR / "environmental_0_1.tif",
    "socioeconomic": PIM_DIR / "socioeconomic_0_1.tif",
}

INPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/flood_hazard_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/sediment_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/landuse_asm_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/environmental_0_1.tif",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/pim_criteria/socioeconomic_0_1.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/environmental_sensitivity_components.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_contribution_diagnostics.csv",
    ROOT / "outputs/ingemmet_catastro_minero_peru_pilot/mining_pressure_manifest.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_screening_summary.csv",
    ROOT / "outputs/peru_gap_closure_analysis/peru_sinpad_colocation_cohorts.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/criterion_dependency_diagnostics.csv",
]
OUTPUTS = [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/criterion_data_strength.csv",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/criterion_data_strength_manifest.json",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def coverage_within_boundary(path: Path) -> float:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        boundary = gpd.read_file(BOUNDARY, layer="peru_pilot_boundary").to_crs(src.crs)
        inside = geometry_mask(
            boundary.geometry,
            out_shape=(src.height, src.width),
            transform=src.transform,
            invert=True,
        )
    return float(np.sum(inside & np.isfinite(data)) / np.sum(inside))


def protected_evidence_state() -> str:
    rows = read_csv_rows(ENV_COMPONENTS)
    row = next(item for item in rows if item["component"] == "protected_area_proximity")
    return row.get("evidence_state", "unrecorded")


def mining_feature_count() -> int:
    rows = read_csv_rows(MINING_MANIFEST)
    return int(rows[0]["features_in_pe1_envelope"])


def socioeconomic_influence_note() -> str:
    rows = read_csv_rows(SOCIO_DIAGNOSTICS)
    by_component = {row["component"]: row for row in rows}
    road = by_component["road_access_proximity"]
    infrastructure = by_component["infrastructure_exposure"]
    return (
        f"Mean-contribution shares are {float(road['realized_mean_contribution_share']):.1%} road "
        f"and {float(infrastructure['realized_mean_contribution_share']):.1%} infrastructure; "
        f"marginal weighted SD shares are {float(road['marginal_weighted_sd_share']):.1%} and "
        f"{float(infrastructure['marginal_weighted_sd_share']):.1%}. These ignore covariance "
        "and are not an effective weight, ranking attribution, or calibration target."
    )


def pim_support_metrics() -> dict[str, float]:
    rows = read_csv_rows(PIM_SUPPORT)
    values = {row["metric"]: row["value"] for row in rows}
    return {
        "pim_scoreable_fraction": float(values["scoreable_valid_fraction"]),
        "pim_full_five_fraction": float(values["full_five_criterion_fraction"]),
        "pim_incomplete_evidence_fraction": float(values["incomplete_evidence_fraction"]),
        "pim_ls_missing_fraction": float(values["ls_missing_fraction"]),
        "pim_k_missing_fraction": float(values["k_missing_fraction"]),
    }


def sinpad_model_diagnostic_note() -> str:
    rows = read_csv_rows(SINPAD_COHORTS)
    all_records = next(row for row in rows if row["cohort"] == "all_hydrometeorological_records")
    flood = next(row for row in rows if row["cohort"] == "flood_specific_records")
    return (
        f"SINPAD point co-location diagnostic: {all_records['top20_count']}/{all_records['valid_pim_count']} "
        f"all scoreable records are in the highest-priority quintile; "
        f"{all_records['unscored_count']} records fall outside complete five-criterion support. "
        f"For flood-specific records, {flood['top20_count']}/{flood['valid_pim_count']} "
        "scoreable records are selected. This is a model-level point co-location diagnostic, "
        "not criterion validation or observed flood-extent validation."
    )


def dependency_diagnostic_notes() -> dict[str, str]:
    rows = {row["diagnostic_id"]: row for row in read_csv_rows(DEPENDENCY_DIAGNOSTICS)}

    def rho(diagnostic_id: str) -> float:
        return float(rows[diagnostic_id]["spearman_rho"])

    def jaccard(diagnostic_id: str) -> float:
        return float(rows[diagnostic_id]["top_quintile_jaccard"])

    shared_worldcover = (
        f"C versus land-use pressure Spearman rho={rho('c_factor_vs_land_use_pressure'):.3f}; "
        "the two scores use distinct value functions but share the WorldCover classification."
    )
    return {
        "flood_hazard": "No component-removal dependency diagnostic is reported for Flood in this run.",
        "sediment": shared_worldcover,
        "landuse_asm": (
            f"{shared_worldcover} Replacing Land Use / Mining with mining pressure only gives "
            f"highest-priority-quintile Jaccard={jaccard('pim_landuse_without_worldcover_pressure'):.3f}."
        ),
        "environmental": (
            f"Environmental versus water/wetland context Spearman rho="
            f"{rho('environmental_vs_water_context'):.3f}; water-only rescaling gives "
            f"highest-priority-quintile Jaccard={jaccard('pim_environmental_water_only_rescaled'):.3f}."
        ),
        "socioeconomic": (
            f"Combined Socioeconomic versus road/access Spearman rho="
            f"{rho('socioeconomic_vs_road_access'):.3f}; road-only and infrastructure-only PIM "
            f"alternatives give highest-priority-quintile Jaccard="
            f"{jaccard('pim_socioeconomic_road_only'):.3f} and "
            f"{jaccard('pim_socioeconomic_infrastructure_only'):.3f}."
        ),
    }


def build_rows() -> list[dict[str, object]]:
    local_protected_state = protected_evidence_state()
    mining_count = mining_feature_count()
    socio_note = socioeconomic_influence_note()
    support = pim_support_metrics()
    sinpad_note = sinpad_model_diagnostic_note()
    dependency_notes = dependency_diagnostic_notes()
    definitions: list[dict[str, object]] = [
        {
            "criterion_id": "flood_hazard",
            "display_name": "Flood-conditioning indicator (FH)",
            "main_weight": 0.35,
            "implementation": "0.40 CHIRPS rainy-season climatology + 0.30 DEM-derived TWI + 0.30 drainage proximity",
            "source_evidence": "CHIRPS v3 (~5 km effective), SRTM terrain and drainage derivatives",
            "evidence_state": "implemented_provisional",
            "known_limit": "CHIRPS is a rainy-season climatology, not an event-extreme rainfall metric; it is resampled to the 30 m reference grid but remains ~5 km evidence; no observed flood extent or depth layer",
            "validation_state": "not validated",
            "next_upgrade": "event-matched rainfall and observed flood extent/depth or documented affected locations",
        },
        {
            "criterion_id": "sediment",
            "display_name": "Sediment / erosion",
            "main_weight": 0.25,
            "implementation": "0.30 SoilGrids K + 0.45 SRTM LS + 0.25 WorldCover C; additive normalized AHP subcriteria",
            "source_evidence": "SoilGrids K (250 m effective), SRTM LS, ESA WorldCover C",
            "evidence_state": "implemented_provisional",
            "known_limit": "K is coarse; any K, LS or C NoData leaves Sediment and the final PIM unscored; no measured erosion or sediment transport observations",
            "validation_state": "not validated",
            "next_upgrade": "field or remote-sensing erosion/sediment observations and a justified channel treatment",
        },
        {
            "criterion_id": "landuse_asm",
            "display_name": "Land use / mining",
            "main_weight": 0.20,
            "implementation": "0.35 WorldCover land-use pressure (distinct from RUSLE C) + 0.65 INGEMMET small-mining point proximity",
            "source_evidence": f"ESA WorldCover and {mining_count} official INGEMMET small-mining points in the PE1 envelope",
            "evidence_state": "implemented_provisional",
            "known_limit": "Mining points indicate registered/reference locations, not verified active disturbance footprints or intensity",
            "validation_state": "not validated",
            "next_upgrade": "date-matched active mine footprints, concessions or imagery-based disturbance evidence",
        },
        {
            "criterion_id": "environmental",
            "display_name": "Environmental context indicator (ES)",
            "main_weight": 0.12,
            "implementation": "0.60 water/wetland context + 0.40 SERNANP national definitive protected-area proximity (MapServer layer 0)",
            "source_evidence": "ESA WorldCover water/wetland, OSM water vectors and SERNANP national definitive protected areas (MapServer layer 0)",
            "evidence_state": local_protected_state,
            "known_limit": "No layer-0 SERNANP national definitive protected-area geometry occurs within the PE1 + 5 km context zone; regional, private and transitional protected-area layers were not queried, so the current score is driven by water/wetland evidence",
            "validation_state": "not validated",
            "next_upgrade": "local wetlands, riparian/ecological condition or other accepted sensitivity evidence",
        },
        {
            "criterion_id": "socioeconomic",
            "display_name": "Socioeconomic exposure indicator",
            "main_weight": 0.08,
            "implementation": "0.45 road/access proximity + 0.55 infrastructure exposure; infrastructure is 0.50 WorldPop + 0.50 OSM buildings",
            "source_evidence": "OSM roads/buildings and WorldPop 2020 population",
            "evidence_state": "implemented_provisional",
            "known_limit": socio_note + " No observed affected-population or infrastructure-damage data are used.",
            "validation_state": "not validated",
            "next_upgrade": "settlement/infrastructure inventory and observed flood impacts; revisit the internal 0.50/0.50 split",
        },
    ]
    for row in definitions:
        row["coverage_within_boundary"] = round(
            coverage_within_boundary(CRITERION_RASTERS[str(row["criterion_id"])]),
            6,
        )
        row["claim_level"] = "provisional"
        row["decision_use"] = "prototype screening; not a final flood-risk or rescue-decision result"
        row["model_level_diagnostic"] = sinpad_note
        row["dependency_sensitivity_diagnostic"] = dependency_notes[str(row["criterion_id"])]
        row.update(support)
    return definitions


def main() -> None:
    rows = build_rows()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "generated": date.today().isoformat(),
        "output": rel(OUT_CSV),
        "criteria_count": len(rows),
        "active_scenario": "mentor_peru_direct_pim",
        "input_sha256": {rel(path): sha256(path) for path in INPUTS},
        "claim_level": "diagnostic_only",
    }
    with OUT_MANIFEST.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    print(f"wrote: {rel(OUT_CSV)}")


if __name__ == "__main__":
    main()
