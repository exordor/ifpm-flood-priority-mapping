"""Run context and the basin chain (Goslar official basin, Secocha reference extent).

The old scripts kept their file paths in module constants and the wrappers changed those
constants to run the same stages elsewhere. Here the same names live in ``Context.p``,
built from the area config, so each extent gets its own paths without patching modules.

All writes go through ``Context`` and must land inside the run's output root (--out),
never in the current outputs/ tree.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask

from . import criteria, io, landcover, proximity, rainfall, soil, terrain
from .config import ROOT, Config
from .normalize import Normalizer
from .scoring import combine_common_support, strict_sum, weighted_average

# Folders inside every chain folder (same layout for all areas and extents).
CHAIN_DIRS = {
    "RAIN_DIR": "rainfall_criterion",
    "TERRAIN_DIR": "terrain_preprocessing",
    "HYDRO_DIR": "hydrology_derivatives",
    "LS_DIR": "ls_factor",
    "K_DIR": "soil_k_factor",
    "CRITERIA_DIR": "criteria_stack/criteria",
    "EXPOSURE_DIR": "exposure_indicators",
    "ES_DIR": "environmental_sensitivity",
    "SCENARIO_DIR": "priority_scenarios",
    "TMP_WBT": "_raw_wbt",
}

# Component name -> raster written by the earlier stages (relative to the chain folder).
COMPONENT_FILES = {
    "rainfall_climatology": "criteria_stack/criteria/rainfall_climatology_0_1.tif",
    "twi_wetness": "criteria_stack/criteria/twi_wetness_0_1.tif",
    "drainage_proximity": "criteria_stack/criteria/drainage_proximity_0_1.tif",
    "soil_k_factor": "criteria_stack/criteria/soil_k_factor_0_1.tif",
    "ls_factor": "criteria_stack/criteria/ls_factor_0_1.tif",
    "c_factor": "criteria_stack/criteria/c_factor_0_1.tif",
    "land_cover_pressure": "criteria_stack/criteria/land_cover_pressure_0_1.tif",
    "bare_soil_vegetation_loss": "criteria_stack/criteria/bare_soil_vegetation_loss_0_1.tif",
    "built_agriculture_road_expansion": "criteria_stack/criteria/built_agriculture_road_expansion_0_1.tif",
    "road_access_proximity": "criteria_stack/criteria/road_access_proximity_0_1.tif",
    "water_wetland_context": "environmental_sensitivity/water_wetland_context_0_1.tif",
    "protected_ecological_context": "environmental_sensitivity/protected_area_context_0_1.tif",
    "settlement_population": "exposure_indicators/population_exposure_0_1.tif",
    "critical_infrastructure": "exposure_indicators/built_infrastructure_exposure_0_1.tif",
}


class Context:
    """Everything a stage needs: config, grid settings, named paths and the writers."""

    def __init__(self, cfg: Config, extent: str, run_root: Path, *, chain_dir: Path,
                 landcover_dir: Path, boundary_gpkg: Path, boundary_layer: str,
                 focus_area_id: str, read_only: bool = False):
        self.cfg = cfg
        self.extent = extent
        self.ext = cfg.extent(extent)
        self.run_root = Path(run_root)
        self.crs = cfg["metric_crs"]
        self.res = float(cfg["res_m"])
        self.nodata = float(cfg["nodata"])
        self.boundary_gpkg = boundary_gpkg
        self.boundary_layer = boundary_layer
        self.focus_area_id = focus_area_id
        self.read_only = read_only
        self.normalize = Normalizer("fit")
        self.raster_writer = io.write_raster   # replaced by a comparison during anchor replay
        self.lineage_missing_ok = False
        inputs = cfg["inputs"]
        self.infrastructure_layer = cfg.layer(inputs["facilities"]) if "facilities" in inputs else None
        p = {"OUT_BASE": chain_dir, "WC_DIR": landcover_dir}
        p.update({key: chain_dir / sub for key, sub in CHAIN_DIRS.items()})
        p.update({key: chain_dir / rel for key, rel in cfg["chain_files"].items()})
        p.update({key: landcover_dir / rel for key, rel in cfg["landcover_files"].items()})
        p["ROAD_ACCESS"] = p["CRITERIA_DIR"] / "road_access_proximity_0_1.tif"
        dataset_keys = {"DEM_SOURCE": "dem", "WORLDCOVER_FILE": "worldcover",
                        "SOILGRIDS_K_SNAPSHOT": "soilgrids_k", "ROADS": "roads",
                        "INFRASTRUCTURE": "facilities", "ZENSUS_TIF": "population",
                        "PROTECTED_RAW": "protected", "CLMS_TCD_LOSS": "clms_tcd_loss",
                        "CLMS_BARE_SOIL": "clms_bare_soil"}
        for key, name in dataset_keys.items():
            p[key] = cfg.path(inputs[name]) if name in inputs else None
        self.p = p

    # --- paths -------------------------------------------------------------------
    def rel(self, path: Path) -> str:
        """Path for manifests: relative to the run root if inside it, else to the workspace."""
        path = Path(path).resolve()
        for base in (self.run_root.resolve(), ROOT.resolve()):
            try:
                return str(path.relative_to(base))
            except ValueError:
                continue
        return str(path)

    def _guard(self, path: Path) -> None:
        if self.read_only:
            raise PermissionError(f"read-only context must not write {path}")
        try:
            Path(path).resolve().relative_to(self.run_root.resolve())
        except ValueError:
            raise PermissionError(f"refusing to write outside the output root {self.run_root}: {path}")

    def mkdir(self, path: Path) -> None:
        if not self.read_only:
            self._guard(path)
            Path(path).mkdir(parents=True, exist_ok=True)

    def write_raster(self, path: Path, data, transform, crs, nodata: float | None = None) -> None:
        nodata = self.nodata if nodata is None else nodata
        if self.raster_writer is io.write_raster:
            self._guard(path)
        self.raster_writer(Path(path), data, transform, crs, nodata)

    def write_text(self, path: Path, text: str) -> None:
        self._guard(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")

    def log(self, message: str) -> None:
        print(f"[{self.cfg['log_prefix']}] {message}", flush=True)

    # --- grid --------------------------------------------------------------------
    def read_band(self, path: Path, profile: dict):
        return io.read_band(path, profile)

    def ref_profile(self) -> dict:
        with rasterio.open(self.p["DEM"]) as src:
            return src.profile

    def boundary_geometry(self, dst_crs):
        import geopandas as gpd
        gdf = gpd.read_file(self.boundary_gpkg, layer=self.boundary_layer)
        if len(gdf) != 1:
            raise ValueError(f"expected one boundary feature, got {len(gdf)}")
        return gdf.to_crs(dst_crs).geometry.iloc[0]

    def boundary_mask(self, profile: dict) -> np.ndarray:
        geometry = self.boundary_geometry(str(profile["crs"]))
        return geometry_mask([geometry], out_shape=(profile["height"], profile["width"]),
                             transform=profile["transform"], invert=True)

    # --- lineage -----------------------------------------------------------------
    def lineage(self, path: Path) -> dict:
        path = Path(path)
        if not path.exists():
            if self.lineage_missing_ok:
                return {"path": self.rel(path), "status": "not_used_by_expanded_wrapper"}
            raise FileNotFoundError(path)
        return {"path": self.rel(path), "bytes": path.stat().st_size, "sha256": io.sha256_file(path)}

    def optional_lineage(self, path: Path) -> dict:
        if not Path(path).exists():
            return {"path": self.rel(path), "exists": False}
        return {**self.lineage(path), "exists": True}


def resolve(run_root: Path, rel: str) -> Path:
    """An upstream product: from the run root when it was produced there, else from the workspace."""
    candidate = Path(run_root) / rel
    return candidate if candidate.exists() else ROOT / rel


def basin_context(cfg: Config, extent: str, run_root: Path, read_only: bool = False) -> Context:
    ext = cfg.extent(extent)
    return Context(cfg, extent, run_root,
                   chain_dir=Path(run_root) / ext["chain_dir"],
                   landcover_dir=Path(run_root) / ext["landcover_dir"],
                   boundary_gpkg=cfg.path(ext["boundary"]),
                   boundary_layer=cfg.layer(ext["boundary"]),
                   focus_area_id=ext["focus_area_id"], read_only=read_only)


# --- priority -------------------------------------------------------------------------

def read_components(ctx, ref) -> dict:
    return {name: ctx.read_band(ctx.p["OUT_BASE"] / rel, ref) for name, rel in COMPONENT_FILES.items()}


def stage_priority_scenarios(ctx) -> None:
    """Combine components into the five criteria and the criteria into the PIM score."""
    p = ctx.p
    ref = ctx.ref_profile()
    mask = ctx.boundary_mask(ref)
    scenario_dir = p["SCENARIO_DIR"]
    ctx.mkdir(scenario_dir / "scenarios")
    ctx.mkdir(scenario_dir / "pim_criteria")
    components = read_components(ctx, ref)
    weights = ctx.cfg["weights"]
    pim_criteria = {}
    for criterion, parts in weights["components"].items():
        if ctx.cfg["criterion_support"] == "strict":
            pim_criteria[criterion] = strict_sum(components, parts, mask)
        else:
            pim_criteria[criterion] = weighted_average([(components[k], v) for k, v in parts.items()], mask)
    for name, arr in pim_criteria.items():
        arr = np.clip(arr, 0.0, 1.0).astype("float32")
        arr[~mask] = np.nan
        ctx.write_raster(scenario_dir / "pim_criteria" / f"{name}_0_1.tif",
                         np.where(np.isfinite(arr), arr, ctx.nodata), ref["transform"], ref["crs"])
    pim, available, count = combine_common_support(pim_criteria, weights["main"], mask)
    priority_path = scenario_dir / "scenarios" / ctx.cfg["priority_filename"]
    ctx.write_raster(priority_path, np.where(np.isfinite(pim), pim, ctx.nodata), ref["transform"], ref["crs"])
    # Coverage rasters are masked so zeros outside the boundary are not read as "no support".
    available = np.where(mask, available, np.nan).astype("float32")
    count = np.where(mask, count.astype("float32"), np.nan).astype("float32")
    ctx.write_raster(scenario_dir / "available_main_weight.tif",
                     np.where(np.isfinite(available), available, ctx.nodata), ref["transform"], ref["crs"])
    ctx.write_raster(scenario_dir / "criteria_evidence_count.tif",
                     np.where(np.isfinite(count), count, ctx.nodata), ref["transform"], ref["crs"])
    if ctx.cfg["area"] == "goslar":
        manifest = goslar_manifest(ctx, priority_path, list(pim_criteria))
        text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    else:
        manifest = secocha_manifest(ctx, priority_path, list(pim_criteria))
        text = json.dumps(manifest, indent=2) + "\n"
    ctx.write_text(scenario_dir / "run_manifest.json", text)


def _component_weights(cfg, short_names: bool = False) -> dict:
    comps = cfg["weights"]["components"]
    if not short_names:
        return dict(comps)
    short = {"flood_hazard": "FH", "sediment": "SE", "landuse_asm": "LU", "environmental": "ES", "socioeconomic": "SV"}
    return {short[k]: v for k, v in comps.items()}


def goslar_manifest(ctx, priority_path: Path, criteria_names: list[str]) -> dict:
    cfg, m, p = ctx.cfg, ctx.cfg["manifest"], ctx.p
    context = {key: cfg.path(dataset) for key, dataset in m["context_datasets"].items()}
    scenario_dir = p["SCENARIO_DIR"]
    return {
        "focus_area_id": ctx.focus_area_id,
        "focus_area_name": m["focus_area_name"],
        "metric_crs": ctx.crs,
        "reference_resolution_m": ctx.res,
        "enters_pim_score": m["enters_pim_score"],
        "claim_level": m["claim_level"],
        "weight_contract": m["weight_contract"],
        "main_weights": cfg["weights"]["main"],
        "component_weights": _component_weights(cfg),
        "removed_components": {},
        "local_weight_limitations": m["local_weight_limitations"],
        "mining_role": m["mining_role"],
        "mining_enters_pim_score": m["mining_enters_pim_score"],
        "mining_overlay": {"path": ctx.rel(context["mining_overlay"]),
                           "manifest": ctx.rel(context["mining_overlay_manifest"]),
                           "claim_level": "context_evidence"},
        "official_hydrology_and_validation": {
            "enters_pim_score": False,
            "claim_level": "validation_candidate/context",
            "sources": {key: ctx.rel(context[key]) for key in
                        ["nlwkn_2017_report", "wfd_drainage_basins", "hwrm_flood_hazard_boundaries",
                         "osm_infrastructure_candidates"]}
                       | {"lineage": ctx.rel(context["source_lineage"]),
                          "diagnostics": ctx.rel(context["diagnostics"])},
            "interpretation": m["official_hydrology_interpretation"],
        },
        "normalization": dict(m["normalization"]),
        "nodata_policy": m["nodata_policy"],
        "effective_resolutions": m["effective_resolutions"],
        "hydrology_buffer_m": float(cfg["terrain"]["dem_buffer_m"]),
        "soilgrids_k_snapshot": {"path": ctx.rel(p["SOILGRIDS_K_SNAPSHOT"]),
                                 "sha256": io.sha256_file(p["SOILGRIDS_K_SNAPSHOT"]),
                                 "method": m["soilgrids_method"]},
        "priority_raster_lineage": ctx.lineage(priority_path),
        "criterion_raster_lineage": {name: ctx.lineage(scenario_dir / "pim_criteria" / f"{name}_0_1.tif")
                                     for name in criteria_names},
        "input_lineage": {
            "implementation": ctx.lineage(Path(__file__).resolve()),
            "boundary": ctx.lineage(ctx.boundary_gpkg),
            "dem": ctx.lineage(p["DEM_SOURCE"]),
            "worldcover": ctx.lineage(p["WORLDCOVER_FILE"]),
            "soilgrids_k_snapshot": ctx.lineage(p["SOILGRIDS_K_SNAPSHOT"]),
            "roads": ctx.lineage(p["ROADS"]),
            "population": ctx.lineage(p["ZENSUS_TIF"]),
            "infrastructure": ctx.lineage(p["INFRASTRUCTURE"]),
            "clms_bare_soil": ctx.lineage(p["CLMS_BARE_SOIL"]),
            "clms_tcd_loss": ctx.lineage(p["CLMS_TCD_LOSS"]),
            "protected_areas": ctx.lineage(p["PROTECTED_RAW"]),
            "mining_overlay": ctx.optional_lineage(context["mining_overlay"]),
            "mining_overlay_manifest": ctx.optional_lineage(context["mining_overlay_manifest"]),
            "official_hydrology_and_validation": {
                key: ctx.optional_lineage(context[key]) for key in
                ["wfd_drainage_basins", "hwrm_flood_hazard_boundaries", "source_lineage", "diagnostics",
                 "nlwkn_2017_report", "osm_infrastructure_candidates"]},
        },
        "data_gaps": {},
        "data_sources": dict(m["data_sources"]),
        "boundary_contract": dict(m["boundary_contract"]),
        "run_date": date.today().isoformat(),
        "note": m["note"],
    }


def secocha_manifest(ctx, priority_path: Path, criteria_names: list[str]) -> dict:
    cfg, m, p = ctx.cfg, ctx.cfg["manifest"], ctx.p
    scenario_dir = p["SCENARIO_DIR"]
    sources = dict(m["data_sources"])
    sources["mining_external_overlay"] = ctx.rel(cfg.path(cfg["inputs"]["mining_overlay"]))
    return {
        "focus_area_id": ctx.focus_area_id,
        "metric_crs": ctx.crs,
        "reference_resolution_m": ctx.res,
        "boundary_id": ctx.focus_area_id,
        "boundary_path": ctx.rel(ctx.boundary_gpkg),
        "boundary_sha256": io.sha256_file(ctx.boundary_gpkg),
        "boundary_role": m["boundary_role"],
        "enters_peru_active_pim": True,
        "enters_pim_score": True,
        "claim_level": m["claim_level"],
        "experiment_id": m["experiment_id"],
        "main_weights": cfg["weights"]["main"],
        "component_weights": _component_weights(cfg, short_names=True),
        "nodata_policy": m["nodata_policy"],
        "mining_role": m["mining_role"],
        "priority_raster": f"scenarios/{cfg['priority_filename']}",
        "priority_raster_lineage": ctx.lineage(priority_path),
        "criterion_raster_lineage": {name: ctx.lineage(scenario_dir / "pim_criteria" / f"{name}_0_1.tif")
                                     for name in criteria_names},
        "input_lineage": {
            "implementation": ctx.lineage(Path(__file__).resolve()),
            "boundary": ctx.lineage(ctx.boundary_gpkg),
            "long_term_rainfall_manifest": ctx.lineage(p["RAIN_DIR"] / "rainfall_manifest.json"),
            "protected_area_manifest": ctx.lineage(p["ES_DIR"] / "protected_area_manifest.json"),
            "exposure_manifest": ctx.lineage(p["EXPOSURE_DIR"] / "exposure_manifest.json"),
        },
        "data_sources": sources,
        "run_date": date.today().isoformat(),
        "note": m["note"],
    }


# --- stage table ----------------------------------------------------------------------

def _rainfall(ctx):
    method = ctx.cfg["rainfall"]["method"]
    return rainfall.stage_rainfall_regnie(ctx) if method == "regnie" else rainfall.stage_rainfall_chirps(ctx)


def _protected(ctx):
    method = ctx.cfg.get("protected_areas", {}).get("method", "natura2000")
    if method == "confirmed_absence":
        return proximity.stage_protected_confirmed_absence(ctx)
    return proximity.stage_protected_natura(ctx)


def _exposure(ctx):
    method = ctx.cfg.get("exposure", {}).get("method", "zensus")
    if method == "worldpop":
        return criteria.stage_exposure_worldpop(ctx)
    return criteria.stage_exposure_zensus(ctx)


def _validate(ctx):
    from .validate import validate_secocha
    return validate_secocha(ctx)


STAGES = {
    "dem": terrain.stage_dem,
    "slope": terrain.stage_slope,
    "hydrology": terrain.stage_hydrology,
    "ls_factor": terrain.stage_ls_factor,
    "worldcover_cfactor": landcover.stage_worldcover_cfactor,
    "soilgrids_kfactor": soil.stage_soilgrids_kfactor,
    "osm_roads": proximity.stage_osm_roads,
    "rainfall": _rainfall,
    "protected_areas": _protected,
    "criteria_stack": criteria.stage_criteria_stack,
    "exposure_indicators": _exposure,
    "environmental_sensitivity": criteria.stage_environmental_sensitivity,
    "priority_scenarios": stage_priority_scenarios,
    "validate": _validate,
}


def run_stage(ctx, name: str) -> None:
    ctx.log(f"{name} ...")
    ctx.normalize.start(name)
    STAGES[name](ctx)


def run_basin(cfg: Config, extent: str, run_root: Path, steps: list[str] | None = None) -> None:
    ctx = basin_context(cfg, extent, run_root)
    for name in ctx.ext["stages"]:
        if steps is None or name in steps:
            run_stage(ctx, name)
