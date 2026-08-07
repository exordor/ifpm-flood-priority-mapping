#!/usr/bin/env python3
"""Run the Supervisor-spec parallel PIM baseline for Arequipa Region.

This runner produces the second of two parallel no-mining baselines so the
mentor can compare her complete weight specification against the retained
original test weights. It does NOT replace the canonical
`run_peru_hybas_l7_6070641200_priority_scenarios.py` baseline; it writes to a
separate versioned folder.

Supervisor's complete spec (2026-08-06 message):

  Top-level: FH 0.34, SE 0.25, LU 0.17, ES 0.10, SV 0.14
  FH sub:    rainfall 0.35, TWI 0.25, drainage/flow 0.40
  SE sub:    K 0.25,       LS 0.50, C 0.25
  LU sub:    LC 0.40,      BV 0.35, BE 0.25   (already implemented upstream)
  ES sub:    water/wetland 0.65, protected/ecological 0.35
  SV sub:    road/access 0.35, settlements+population 0.35, critical infrastructure 0.30

Implementation notes / honest gaps:
- FH, SE, ES, SV sub-criteria are REBUILT HERE from existing 0-1 component
  rasters using Supervisor's sub-weights. No upstream re-normalization happens;
  we only re-weight already-standardized components.
- ES: the upstream `environmental_sensitivity_0_1.tif` uses WW 0.60 / PA 0.40.
  Supervisor's WW 0.65 / PA 0.35 is applied here by recombining the WW and PA
  component rasters directly.
- SV three-way split: no true critical-infrastructure inventory exists. CI is
  proxied by `built_infrastructure_exposure_0_1.tif` (OSM mapped-building
  density) and labelled as a proxy. SP uses `population_exposure_0_1.tif`
  (WorldPop). RD uses `road_access_proximity_0_1.tif`. This is the only place
  the SV definition departs from Supervisor's intent, and it is recorded in the
  manifest and the briefing.
- Mining remains excluded from scoring and is retained only as an external
  overlay (consistent with v02 / v03).

Status: sensitivity_scenario. Not a final AHP result; no pairwise matrix or
consistency ratio was supplied.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin"))
from _lib.ifpm_tools import write_raster as _write_raster  # noqa: E402
from functools import partial  # noqa: E402
write_raster = partial(_write_raster, sanitize=True)  # noqa: E305

# Load the canonical baseline runner as a module so we can reuse its
# grid-reading, boundary-masking, weighting, and plotting helpers without
# duplicating them.
_BASE_PATH = ROOT / "bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py"
_spec = importlib.util.spec_from_file_location("peru_baseline_runner", _BASE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_BASE_PATH}")
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)


VERSION_ID = "07_supervisor_spec_full_weights"
OUT_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/pim_versions" / VERSION_ID
CRITERIA_DIR = OUT_DIR / "pim_criteria"
SCENARIO_DIR = OUT_DIR / "scenarios"

CRITERIA_STACK = ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria"
EXPOSURE_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/exposure_indicators"
ENV_DIR = ROOT / "outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1"

# Supervisor's complete sub-criterion weights.
SUPERVISOR_SUBWEIGHTS = {
    "flood_hazard": {
        "rainfall_climatology": 0.35,
        "twi_wetness": 0.25,
        "drainage_proximity": 0.40,
    },
    "sediment": {
        "soil_k_factor": 0.25,
        "ls_factor": 0.50,
        "c_factor": 0.25,
    },
    "landuse_asm": {
        "land_cover_pressure": 0.40,
        "bare_soil_vegetation_loss": 0.35,
        "built_agriculture_road_expansion": 0.25,
    },
    "environmental": {
        "water_wetland_context": 0.65,
        "protected_ecological_context": 0.35,
    },
    "socioeconomic": {
        "road_access_proximity": 0.35,
        "settlement_population": 0.35,
        "critical_infrastructure": 0.30,
    },
}

SUPERVISOR_MAIN_WEIGHTS = {
    "flood_hazard": 0.34,
    "sediment": 0.25,
    "landuse_asm": 0.17,
    "environmental": 0.10,
    "socioeconomic": 0.14,
}

PIM_CRITERIA_ORDER = ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"]

# Same coverage floor as the canonical baseline runner.
MIN_SCOREABLE_VALID_FRACTION = 0.95

# Component rasters needed to rebuild every criterion under Supervisor's spec.
COMPONENT_PATHS = {
    "rainfall_climatology": CRITERIA_STACK / "rainfall_climatology_0_1.tif",
    "twi_wetness": CRITERIA_STACK / "twi_wetness_0_1.tif",
    "drainage_proximity": CRITERIA_STACK / "drainage_proximity_0_1.tif",
    "soil_k_factor": CRITERIA_STACK / "soil_k_factor_0_1.tif",
    "ls_factor": CRITERIA_STACK / "ls_factor_0_1.tif",
    "c_factor": CRITERIA_STACK / "c_factor_0_1.tif",
    "land_cover_pressure": CRITERIA_STACK / "land_cover_pressure_0_1.tif",
    "bare_soil_vegetation_loss": CRITERIA_STACK / "bare_soil_vegetation_loss_0_1.tif",
    "built_agriculture_road_expansion": CRITERIA_STACK / "built_agriculture_road_expansion_0_1.tif",
    "water_wetland_context": ENV_DIR / "water_wetland_context_0_1.tif",
    "protected_ecological_context": ENV_DIR / "protected_area_context_0_1.tif",
    "road_access_proximity": CRITERIA_STACK / "road_access_proximity_0_1.tif",
    "settlement_population": EXPOSURE_DIR / "population_exposure_0_1.tif",
    # Proxy: no true critical-infrastructure inventory exists; mapped-building
    # density stands in for CI and is labelled as such.
    "critical_infrastructure": EXPOSURE_DIR / "built_infrastructure_exposure_0_1.tif",
}

INPUTS = [ROOT / "bin/_lib/ifpm_tools.py", _BASE_PATH] + list(COMPONENT_PATHS.values()) + [
    ROOT / "outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif",
    ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg",
]

OUTPUTS = [
    OUT_DIR / "run_manifest.json",
    OUT_DIR / "supervisor_subcriteria_weights.csv",
    OUT_DIR / "supervisor_main_weights.csv",
    OUT_DIR / "scenario_priority_summary.csv",
    SCENARIO_DIR / "priority_supervisor_spec_pim.tif",
    SCENARIO_DIR / "top20_supervisor_spec_pim.tif",
    OUT_DIR / "supervisor_spec_board.png",
    OUT_DIR / "supervisor_spec_board.pdf",
] + [CRITERIA_DIR / f"{name}_0_1.tif" for name in PIM_CRITERIA_ORDER]


def build_supervisor_criteria(components: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """Recombine base components with Supervisor's sub-weights (complete-case)."""

    return {
        name: base.combine_weighted_layers(components, weights)
        for name, weights in SUPERVISOR_SUBWEIGHTS.items()
    }


def raster_stats(data: np.ndarray) -> dict[str, float]:
    valid = np.isfinite(data)
    if not valid.any():
        return {"min": float("nan"), "max": float("nan"), "mean": float("nan"), "std": float("nan")}
    vals = data[valid]
    return {
        "min": round(float(vals.min()), 6),
        "max": round(float(vals.max()), 6),
        "mean": round(float(vals.mean()), 6),
        "std": round(float(vals.std()), 6),
    }


def plot_board(score: np.ndarray, top20: np.ndarray, profile: dict) -> None:
    """Render a clean priority board matching the baseline style."""

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from rasterio.transform import array_bounds

    bounds = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    cmap = ListedColormap(["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"])
    norm = BoundaryNorm(bounds, cmap.N)

    west, south, east, north = array_bounds(profile["height"], profile["width"], profile["transform"])
    extent = (west, east, south, north)

    fig, ax = plt.subplots(figsize=(8, 10))
    masked = np.where(np.isfinite(score), score, np.nan)
    ax.imshow(masked, cmap=cmap, norm=norm, extent=extent)
    ax.set_title("Supervisor-spec PIM (no mining)\nFH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14", fontsize=11)
    ax.set_xlabel("Easting (m, EPSG:32718)")
    ax.set_ylabel("Northing (m, EPSG:32718)")
    ax.set_aspect("equal")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, ticks=[0.1, 0.3, 0.5, 0.7, 0.9], fraction=0.046, pad=0.04)
    cbar.ax.set_yticklabels(["Very low", "Low", "Moderate", "High", "Very high"])
    cbar.set_label("Priority score (sensitivity_scenario)")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "supervisor_spec_board.png", dpi=200)
    fig.savefig(OUT_DIR / "supervisor_spec_board.pdf")
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CRITERIA_DIR.mkdir(parents=True, exist_ok=True)
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)

    profile = base.read_reference()
    boundary_mask = base.read_boundary_mask(profile)

    components = {name: base.read_band(path, profile) for name, path in COMPONENT_PATHS.items()}
    criteria = build_supervisor_criteria(components)
    for name, data in criteria.items():
        write_raster(CRITERIA_DIR / f"{name}_0_1.tif", data, profile)

    score, available_weight, evidence_count = base.combine_common_support_criteria(
        criteria, SUPERVISOR_MAIN_WEIGHTS
    )
    score[~boundary_mask] = np.nan

    write_raster(SCENARIO_DIR / "priority_supervisor_spec_pim.tif", score, profile)

    scoreable = boundary_mask & np.isfinite(score)
    scoreable_valid_fraction = float(scoreable.sum() / boundary_mask.sum())
    # Coverage guard: the SV criterion was redefined from one pre-blended raster
    # into three independent components, so extra NoData could silently drop
    # cells. Fail loudly if common support falls below the project threshold.
    if scoreable_valid_fraction < MIN_SCOREABLE_VALID_FRACTION:
        missing = []
        for name in PIM_CRITERIA_ORDER:
            frac = float((boundary_mask & np.isfinite(criteria[name])).sum() / boundary_mask.sum())
            if frac < MIN_SCOREABLE_VALID_FRACTION:
                missing.append(f"{name}={frac:.6f}")
        raise RuntimeError(
            "Supervisor-spec five-criterion common support does not provide enough "
            f"scoreable coverage; scoreable={scoreable_valid_fraction:.6f}, "
            f"threshold={MIN_SCOREABLE_VALID_FRACTION}; "
            f"low layers: {', '.join(missing) if missing else 'none'}"
        )
    threshold = float(np.nanpercentile(score, 80))
    top20 = np.where(scoreable, score >= threshold, np.nan).astype("float32")
    write_raster(SCENARIO_DIR / "top20_supervisor_spec_pim.tif", top20, profile)

    cell_km2 = 30.0 * 30.0 / 1e6
    top20_area = round(float(np.nansum(top20 == 1.0) * cell_km2), 3)

    # Sub-criteria weights CSV.
    sub_rows = []
    for crit in PIM_CRITERIA_ORDER:
        for comp, w in SUPERVISOR_SUBWEIGHTS[crit].items():
            sub_rows.append({
                "pim_criterion": crit,
                "component": comp,
                "supervisor_local_weight": w,
                "global_weight": round(w * SUPERVISOR_MAIN_WEIGHTS[crit], 6),
                "source_layer": base.rel(COMPONENT_PATHS[comp]),
                "note": (
                    "CI proxied by built-building density (no true CI inventory)"
                    if comp == "critical_infrastructure"
                    else ""
                ),
            })
    base.write_csv(OUT_DIR / "supervisor_subcriteria_weights.csv", sub_rows)

    main_rows = [{"criterion": c, "weight": w} for c, w in SUPERVISOR_MAIN_WEIGHTS.items()]
    base.write_csv(OUT_DIR / "supervisor_main_weights.csv", main_rows)

    summary_rows = [{
        "version_id": VERSION_ID,
        "top20_threshold": round(threshold, 6),
        "scoreable_valid_fraction": round(scoreable_valid_fraction, 6),
        "top20_area_km2": top20_area,
        **raster_stats(score),
    }]
    base.write_csv(OUT_DIR / "scenario_priority_summary.csv", summary_rows)

    plot_board(score, top20, profile)

    manifest = {
        "version_id": VERSION_ID,
        "boundary_id": "peru_hybas_l7_6070641200",
        "claim_level": "sensitivity_scenario",
        "spec_source": "Supervisor 2026-08-06 message; complete top + sub weight table",
        "main_weights": SUPERVISOR_MAIN_WEIGHTS,
        "sub_weights": SUPERVISOR_SUBWEIGHTS,
        "mentor_weight_type": "expert-informed provisional weights; no pairwise matrix or CR supplied",
        "mining_role": "external overlay only; excluded from PIM calculation",
        "known_gaps": [
            "critical_infrastructure is proxied by OSM mapped-building density; no true CI inventory exists",
            "BV and BE are single-date WorldCover proxies; a MapBiomas real-change test (v05) shows the high-priority footprint is stable to the single-date->real-change swap (top-20% Jaccard = 0.94)",
        ],
        "scoreable_valid_fraction": scoreable_valid_fraction,
        "top20_threshold": threshold,
        "top20_area_km2": top20_area,
        "script": {"path": base.rel(Path(__file__)), "sha256": base.sha256(Path(__file__))},
        "git": base.git_state(),
        "inputs": [{"path": base.rel(p), "sha256": base.sha256(p)} for p in INPUTS],
        "outputs": [{"path": base.rel(p), "sha256": base.sha256(p)} for p in OUTPUTS if (p.suffix in {".tif", ".png", ".pdf"} and p != OUT_DIR / "run_manifest.json")],
    }
    (OUT_DIR / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"wrote Supervisor-spec parallel baseline to {base.rel(OUT_DIR)}")
    print(f"  scoreable coverage: {scoreable_valid_fraction:.6f}")
    print(f"  top-20% area: {top20_area} km2")
    print("  weights: FH 0.34, SE 0.25, LU 0.17, ES 0.10, SV 0.14")
    print("  CI is a built-density proxy; BV/BE are single-date proxies")


if __name__ == "__main__":
    main()
