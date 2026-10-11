#!/usr/bin/env python3
"""Activate the Secocha A7367 reference extent and freeze the former Peru area.

This is a scope/version transition, not a model run.  It creates a provisional
Secocha working boundary from the coordinate frame of INGEMMET A7367 Map 7,
records the former HydroBASINS Peru area as a frozen baseline, and audits which
existing data can be reused for a like-for-like Secocha PIM rerun.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from pathlib import Path

import geopandas as gpd
import rasterio
from pyproj import Transformer
from shapely.geometry import Point, box


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_BOUNDARY_ID = "secocha_reference_extent"
OUTPUT_ROOT_ID = "secocha_pim_chain"  # outputs folder name (differs from the id since 2026-10-11 rename)
FROZEN_BOUNDARY_ID = "peru_former"
CRS_UTM18S = "EPSG:32718"
SECOCHA_EXTENT_UTM = (691500.0, 8231000.0, 696500.0, 8237000.0)
SECOCHA_ANCHOR_UTM = (695121.0, 8232667.0)

BOUNDARY_DIR = ROOT / "outputs/secocha_boundary"
SCOPE_DIR = ROOT / "outputs/secocha_scope_activation"
ACTIVE_OUTPUT_ROOT = ROOT / f"outputs/{OUTPUT_ROOT_ID}"
BOUNDARY_GPKG = BOUNDARY_DIR / "secocha_boundary.gpkg"
BOUNDARY_MANIFEST = BOUNDARY_DIR / "boundary_manifest.json"
ACTIVE_MANIFEST = SCOPE_DIR / "active_peru_research_area.json"
DATA_AUDIT = SCOPE_DIR / "secocha_data_coverage_audit.json"
FROZEN_ROOT = ROOT / "outputs/peru_former_pim_chain"
FREEZE_MARKER = FROZEN_ROOT / "FROZEN_BASELINE.json"

FROZEN_KEY_ARTIFACTS = {
    "boundary": ROOT / "outputs/peru_former_boundary/peru_former_boundary.gpkg",
    "priority": FROZEN_ROOT / "priority_scenarios/scenarios/priority_mentor_peru_direct_pim.tif",
    "run_manifest": FROZEN_ROOT / "priority_scenarios/run_manifest.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_boundary() -> tuple[gpd.GeoDataFrame, dict]:
    geometry = box(*SECOCHA_EXTENT_UTM)
    anchor = Point(*SECOCHA_ANCHOR_UTM)
    gdf = gpd.GeoDataFrame(
        [
            {
                "boundary_id": ACTIVE_BOUNDARY_ID,
                "status": "active_provisional",
                "role": "working_reference_extent",
                "source_id": "ingemmet_a7367_map7",
                "source_page": 75,
                "event_footprint": False,
                "catchment_boundary": False,
                "geometry": geometry,
            }
        ],
        crs=CRS_UTM18S,
    )
    BOUNDARY_DIR.mkdir(parents=True, exist_ok=True)
    if BOUNDARY_GPKG.exists():
        BOUNDARY_GPKG.unlink()
    gdf.to_file(BOUNDARY_GPKG, layer="secocha_active_boundary", driver="GPKG")
    wgs84 = gdf.to_crs("EPSG:4326")
    manifest = {
        "boundary_id": ACTIVE_BOUNDARY_ID,
        "status": "active_provisional",
        "claim_level": "diagnostic_only",
        "role": "working_reference_extent",
        "source": "INGEMMET A7367 Map 7 coordinate frame, PDF page 75",
        "source_crs": CRS_UTM18S,
        "bounds_utm18s": list(SECOCHA_EXTENT_UTM),
        "bounds_wgs84": [round(float(v), 8) for v in wgs84.total_bounds],
        "area_km2": round(float(geometry.area / 1_000_000), 3),
        "contains_secocha_anchor": bool(geometry.covers(anchor)),
        "is_event_footprint": False,
        "is_catchment_boundary": False,
        "reference_grid": {"crs": CRS_UTM18S, "target_resolution_m": 30},
        "path": rel(BOUNDARY_GPKG),
        "sha256": sha256(BOUNDARY_GPKG),
        "limitation": (
            "The boundary is a provisional model/reference window read from the A7367 Map 7 "
            "coordinate frame. It is neither a digitized 2023 debris-flow footprint nor a hydrologic catchment."
        ),
    }
    json_write(BOUNDARY_MANIFEST, manifest)
    return gdf, manifest


def freeze_previous_area(active_boundary_manifest: dict) -> dict:
    missing = [rel(path) for path in FROZEN_KEY_ARTIFACTS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"cannot freeze previous baseline; missing key artifacts: {missing}")
    key_artifacts = {
        name: {"path": rel(path), "sha256": sha256(path), "size_bytes": path.stat().st_size}
        for name, path in FROZEN_KEY_ARTIFACTS.items()
    }
    payload = {
        "boundary_id": FROZEN_BOUNDARY_ID,
        "status": "frozen_baseline",
        "frozen_on": date.today().isoformat(),
        "replaced_as_active_area_by": ACTIVE_BOUNDARY_ID,
        "reason": "User-directed Peru research-area switch to Secocha.",
        "output_root": rel(FROZEN_ROOT),
        "mutation_policy": (
            "Do not write new model outputs into this root. Preserve existing rasters, manifests, "
            "figures and scenario folders as the frozen previous-area baseline."
        ),
        "key_artifacts": key_artifacts,
        "new_active_boundary_sha256": active_boundary_manifest["sha256"],
    }
    json_write(FREEZE_MARKER, payload)
    return payload


def _raster_covers(path: Path, bounds_wgs84: list[float]) -> dict:
    if not path.exists():
        return {"path": rel(path), "exists": False, "covers_active_extent": False}
    with rasterio.open(path) as src:
        transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = transformer.transform(bounds_wgs84[0], bounds_wgs84[1])
        xmax, ymax = transformer.transform(bounds_wgs84[2], bounds_wgs84[3])
        left, right = sorted((xmin, xmax))
        bottom, top = sorted((ymin, ymax))
        covers = (
            src.bounds.left <= left
            and src.bounds.right >= right
            and src.bounds.bottom <= bottom
            and src.bounds.top >= top
        )
        return {
            "path": rel(path),
            "exists": True,
            "covers_active_extent": bool(covers),
            "crs": str(src.crs),
            "native_resolution": [float(src.res[0]), float(abs(src.res[1]))],
            "bounds": [float(v) for v in src.bounds],
        }


def _vector_count(path: Path, bounds_wgs84: list[float]) -> dict:
    if not path.exists():
        return {"path": rel(path), "exists": False, "intersecting_features": 0}
    try:
        subset = gpd.read_file(path, bbox=tuple(bounds_wgs84))
        return {
            "path": rel(path),
            "exists": True,
            "intersecting_features": int(len(subset)),
            "reusable": bool(len(subset) > 0),
        }
    except Exception as exc:  # audit should report, not hide, source-read failures
        return {
            "path": rel(path),
            "exists": True,
            "intersecting_features": None,
            "reusable": False,
            "error": str(exc),
        }


def audit_data(boundary_manifest: dict) -> dict:
    bounds = boundary_manifest["bounds_wgs84"]
    west = math.floor(bounds[0])
    south = math.floor(bounds[1])
    required_srtm = f"S{abs(south):02d}W{abs(west):03d}.SRTMGL1.hgt.zip"
    raw = ROOT / "data/raw"
    audit = {
        "boundary_id": ACTIVE_BOUNDARY_ID,
        "audit_date": date.today().isoformat(),
        "claim_level": "diagnostic_only",
        "boundary_ready": True,
        "model_run_ready": False,
        "local_coverage": {
            "srtm_dem": {
                "required_tile": required_srtm,
                "path": f"data/raw/srtm_1arcsec_secocha/{required_srtm}",
                "exists": (raw / "srtm_1arcsec_secocha" / required_srtm).exists(),
            },
            "worldcover": _raster_covers(
                raw / "esa_worldcover_2021_peru_former/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif",
                bounds,
            ),
            "worldpop": _raster_covers(
                raw / "worldpop_peru_population/per_ppp_2020_UNadj.tif",
                bounds,
            ),
            "osm_roads": _vector_count(
                raw / "geofabrik_osm_peru_former/extracted/gis_osm_roads_free_1.shp", bounds
            ),
            "osm_buildings": _vector_count(
                raw / "geofabrik_osm_peru_former/extracted/gis_osm_buildings_a_free_1.shp", bounds
            ),
            "osm_places": _vector_count(
                raw / "geofabrik_osm_peru_former/extracted/gis_osm_places_free_1.shp", bounds
            ),
            "old_ingemmet_subset": _vector_count(
                raw / "ingemmet_catastro_minero_peru_former/peru_former_pequena_mineria.gpkg",
                bounds,
            ),
            "old_sernanp_subset": _vector_count(
                raw / "sernanp_protected_areas_peru_former/peru_former_sernanp_protected_areas.gpkg",
                bounds,
            ),
            "official_event_reports": {
                "path": "data/validation/secocha_2023_validation/official_reports",
                "exists": (ROOT / "data/validation/secocha_2023_validation/official_reports").exists(),
                "reusable_for_validation": True,
            },
        },
        "required_before_full_chain": [
            "Download and register the SRTM S16W074 tile for the Secocha reference extent.",
            "Build a Secocha SoilGrids K-factor source window and align it to the new 30 m grid.",
            "Extract/recompute CHIRPS rainfall for the Secocha window; retain the coarse-resolution warning.",
            "Query SERNANP protected areas for the Secocha context window instead of reusing the frozen-area subset.",
            "Query INGEMMET mining records for Secocha as an external overlay; do not put mining into the no-mining PIM score.",
        ],
        "reusable_without_redownload": [
            "ESA WorldCover S18W075 if covers_active_extent=true",
            "WorldPop Peru national raster if covers_active_extent=true",
            "Geofabrik Peru OSM roads/buildings/places",
            "Secocha INGEMMET A7367 and INDECI official reports",
        ],
        "validation_follow_up": [
            "Digitize event-specific 5 February debris-flow/mudflow classes from A7367 Map 7 with page/class lineage.",
            "Acquire event-window rainfall and before/after Sentinel imagery separately from the climatological PIM inputs.",
        ],
    }
    audit["model_run_ready"] = bool(
        audit["local_coverage"]["srtm_dem"]["exists"]
        and audit["local_coverage"]["worldcover"]["covers_active_extent"]
        and audit["local_coverage"]["worldpop"]["covers_active_extent"]
    )
    json_write(DATA_AUDIT, audit)
    return audit


def activate_scope(boundary_manifest: dict, frozen_manifest: dict, audit: dict) -> dict:
    payload = {
        "scope_id": "peru_active_area_2026_08_09",
        "status": "active",
        "activated_on": date.today().isoformat(),
        "active_area": {
            "boundary_id": ACTIVE_BOUNDARY_ID,
            "display_name": "Secocha, Mariano Nicolas Valcarcel, Camana, Arequipa, Peru",
            "boundary_role": "A7367 Map 7 provisional reference extent",
            "boundary_path": boundary_manifest["path"],
            "model_output_root": f"outputs/{OUTPUT_ROOT_ID}",
            "model_status": "boundary_ready_data_acquisition_pending",
            "claim_level": "diagnostic_only",
        },
        "frozen_previous_area": {
            "boundary_id": FROZEN_BOUNDARY_ID,
            "status": frozen_manifest["status"],
            "output_root": frozen_manifest["output_root"],
            "freeze_marker": rel(FREEZE_MARKER),
        },
        "weights_policy": (
            "Research-area switch only. Preserve the current no-mining PIM weight contract; "
            "mining remains an external overlay."
        ),
        "data_audit": rel(DATA_AUDIT),
        "model_run_ready": audit["model_run_ready"],
    }
    json_write(ACTIVE_MANIFEST, payload)
    json_write(
        ACTIVE_OUTPUT_ROOT / "scope_manifest.json",
        {
            "boundary_id": ACTIVE_BOUNDARY_ID,
            "status": "active_provisional",
            "claim_level": "diagnostic_only",
            "boundary_path": boundary_manifest["path"],
            "scope_manifest": rel(ACTIVE_MANIFEST),
            "data_coverage_audit": rel(DATA_AUDIT),
            "allowed_new_output_groups": [
                "terrain_preprocessing",
                "hydrology_derivatives",
                "ls_factor",
                "soil_k_factor",
                "rainfall_criterion",
                "criteria_stack",
                "exposure_indicators",
                "environmental_sensitivity",
                "priority_scenarios",
                "validation_comparison",
                "mining_overlay",
            ],
            "frozen_output_root": frozen_manifest["output_root"],
            "note": "All new Peru model outputs must be written under this root.",
        },
    )
    return payload


def main() -> None:
    boundary, boundary_manifest = create_boundary()
    frozen_manifest = freeze_previous_area(boundary_manifest)
    audit = audit_data(boundary_manifest)
    active = activate_scope(boundary_manifest, frozen_manifest, audit)
    print(
        json.dumps(
            {
                "active_boundary_id": ACTIVE_BOUNDARY_ID,
                "area_km2": boundary_manifest["area_km2"],
                "frozen_boundary_id": FROZEN_BOUNDARY_ID,
                "model_run_ready": audit["model_run_ready"],
                "active_manifest": rel(ACTIVE_MANIFEST),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
