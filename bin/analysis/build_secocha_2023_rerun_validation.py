#!/usr/bin/env python3
"""Assemble the post-rerun Secocha validation handoff.

The active PIM is rerun with its existing Supervisor v07 input contract.  The
new event rainfall and Sentinel catalogue are linked here as validation context
only; they are not silently promoted to scored PIM layers.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/secocha_2023_validation"
PIM_MANIFEST = ROOT / "outputs/secocha_pim_chain/priority_scenarios/run_manifest.json"
EVENT_COMPARISON = OUT / "observed_hazard/secocha_2023_event_pim_comparison.json"
ORIGINAL_COMPARISON = OUT / "observed_hazard/ingemmet_original_gis_comparison.json"
RAIN_COMPARISON = OUT / "rainfall/rainfall_sat_vs_rnl_comparison.json"
SENTINEL_SUMMARY = OUT / "satellite_before_after/sentinel_catalog_summary.json"
SENTINEL_MANIFEST = OUT / "satellite_before_after/sentinel_catalog_manifest.json"
SENTINEL_PIXEL_MANIFESTS = [
    OUT / "satellite_before_after/sentinel_pixel_download_core_s2_manifest.json",
    OUT / "satellite_before_after/sentinel_pixel_download_s1_pair_manifest.json",
]
SENTINEL_S2_PROCESSING_QA = OUT / "satellite_before_after/processed/s2_optical_change_qa.json"
MAP7_MANIFEST = OUT / "observed_hazard/digitization_manifest.json"
PRIORITY_RASTER = ROOT / "outputs/secocha_pim_chain/priority_scenarios/scenarios/priority_secocha_direct_pim.tif"
QA_MANIFEST = ROOT / "outputs/secocha_pim_chain/quality_assurance/chain_validation.json"
ACTIVE_BOUNDARY_SHA256 = "4b6d0fe0775c706860190c5b9248deeeec539399831be1577007487151907d4b"
OUT_JSON = OUT / "rerun_validation_summary.json"
OUT_MD = OUT / "rerun_validation_summary.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def artifact(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}


def verify_record(record: dict[str, object]) -> dict[str, object]:
    path = ROOT / str(record["path"])
    actual = artifact(path)
    if record.get("sha256") != actual["sha256"]:
        raise RuntimeError(f"stale or changed artifact record: {path}")
    if record.get("bytes") is not None and int(record["bytes"]) != actual["bytes"]:
        raise RuntimeError(f"artifact byte count differs from record: {path}")
    return actual


def require(condition: bool, label: str, checks: list[dict[str, object]], detail: str = "") -> None:
    if not condition:
        raise RuntimeError(f"rerun lineage check failed: {label}{(': ' + detail) if detail else ''}")
    checks.append({"name": label, "status": "pass", "detail": detail or "verified"})


def main() -> None:
    pim = load(PIM_MANIFEST)
    event = load(EVENT_COMPARISON)
    original = load(ORIGINAL_COMPARISON)
    rainfall = load(RAIN_COMPARISON)
    sentinel_summary = load(SENTINEL_SUMMARY)
    sentinel_manifest = load(SENTINEL_MANIFEST)
    sentinel_pixels = [load(path) for path in SENTINEL_PIXEL_MANIFESTS]
    sentinel_s2_processing = load(SENTINEL_S2_PROCESSING_QA)
    map7_manifest = load(MAP7_MANIFEST)
    qa = load(QA_MANIFEST)
    checks: list[dict[str, object]] = []
    boundary_id = "secocha_reference_extent"
    require(pim.get("focus_area_id") == boundary_id, "pim_active_focus_area", checks)
    require(pim.get("boundary_id") == boundary_id, "pim_boundary_id", checks)
    require(pim.get("main_weights") == {
        "flood_hazard": 0.34,
        "sediment": 0.25,
        "landuse_asm": 0.17,
        "environmental": 0.10,
        "socioeconomic": 0.14,
    }, "frozen_supervisor_v07_weights", checks)
    priority_path = ROOT / "outputs/secocha_pim_chain/priority_scenarios" / str(pim["priority_raster"])
    priority_artifact = artifact(priority_path)
    qa_artifact = artifact(QA_MANIFEST)
    require(qa.get("boundary_id") == boundary_id and qa.get("status") == "pass", "pim_chain_validation_pass", checks)
    require(qa.get("weights_changed") is False, "pim_qa_weights_unchanged", checks)
    raster_checks = [row for row in qa.get("raster_checks", []) if row.get("path") == str(priority_path.relative_to(ROOT))]
    require(bool(raster_checks) and raster_checks[0].get("grid_compatible") is True, "priority_raster_qa_entry", checks)
    require(event.get("boundary_id") == boundary_id, "event_comparison_boundary_id", checks)
    require(event.get("boundary_sha256") == ACTIVE_BOUNDARY_SHA256, "event_comparison_boundary_hash", checks)
    require(event.get("pim_raster_sha256") == priority_artifact["sha256"], "event_comparison_priority_raster_hash", checks)
    require(event.get("pim_run_manifest_sha256") == sha256(PIM_MANIFEST), "event_comparison_pim_manifest_hash", checks)
    require(map7_manifest.get("boundary_id") == boundary_id and map7_manifest.get("boundary_sha256") == ACTIVE_BOUNDARY_SHA256, "map7_boundary_lineage", checks)
    require(map7_manifest.get("pim_raster_sha256") == priority_artifact["sha256"], "map7_priority_raster_hash", checks)
    require(map7_manifest.get("pim_run_manifest_sha256") == sha256(PIM_MANIFEST), "map7_pim_manifest_hash", checks)
    require(map7_manifest.get("source_pdf_sha256") == event.get("source_pdf_sha256"), "map7_event_source_pdf_hash", checks)
    for output in map7_manifest.get("outputs", []):
        verify_record(output)
    require(rainfall.get("boundary_id") == boundary_id and rainfall.get("event_date") == "2023-02-05", "rainfall_event_lineage", checks)
    require(rainfall.get("local_lineage", {}).get("sat", {}).get("stack", {}).get("sha256"), "rainfall_local_hashes", checks)
    require(rainfall.get("sat_manifest", {}).get("sha256") == sha256(ROOT / "outputs/secocha_2023_validation/rainfall/event_rainfall_manifest.json"), "rainfall_sat_manifest_hash", checks)
    require(rainfall.get("rnl_manifest", {}).get("sha256") == sha256(ROOT / "outputs/secocha_2023_validation/rainfall_rnl/event_rainfall_rnl_manifest.json"), "rainfall_rnl_manifest_hash", checks)
    require(sentinel_manifest.get("boundary_id") == boundary_id and sentinel_manifest.get("event_date") == "2023-02-05", "sentinel_event_lineage", checks)
    for record in sentinel_manifest.get("response_files", []) + sentinel_manifest.get("quicklooks", []):
        verify_record(record)
    verify_record(sentinel_manifest["selected_scenes_geojson"] if isinstance(sentinel_manifest.get("selected_scenes_geojson"), dict) else {"path": sentinel_manifest["selected_scenes_geojson"], "sha256": sha256(ROOT / sentinel_manifest["selected_scenes_geojson"]), "bytes": (ROOT / sentinel_manifest["selected_scenes_geojson"]).stat().st_size})
    require(sentinel_manifest.get("pixel_asset_downloaded") is False, "sentinel_pixels_context_only", checks)
    require(
        all(item.get("event_date") == "2023-02-05" and item.get("boundary_id") == boundary_id for item in sentinel_pixels),
        "sentinel_pixel_lineage",
        checks,
    )
    require(all(item.get("size_checks_passed") is True for item in sentinel_pixels), "sentinel_pixel_size_checks", checks)
    require(
        all(item.get("enters_pim_score") is False and item.get("claim_level") == "validation_candidate" for item in sentinel_pixels),
        "sentinel_pixel_claim_boundary",
        checks,
    )
    for item in sentinel_pixels:
        for asset in item["downloaded_assets"]:
            verify_record(asset)
    require(
        sentinel_s2_processing.get("boundary_id") == boundary_id
        and sentinel_s2_processing.get("event_date") == "2023-02-05",
        "sentinel_s2_processing_lineage",
        checks,
    )
    require(
        sentinel_s2_processing.get("claim_level") == "validation_candidate"
        and sentinel_s2_processing.get("enters_pim_score") is False,
        "sentinel_s2_processing_claim_boundary",
        checks,
    )
    require(
        sentinel_s2_processing.get("common_valid_pixels_10m", 0) > 0,
        "sentinel_s2_processing_valid_support",
        checks,
        detail=f"{sentinel_s2_processing.get('common_valid_pixels_10m')} pixels",
    )
    for record in sentinel_s2_processing.get("outputs", {}).values():
        verify_record(record)
    if pim.get("focus_area_id") != "secocha_reference_extent":
        raise RuntimeError("PIM run manifest is not the active Secocha experiment")
    if pim.get("main_weights") != {
        "flood_hazard": 0.34,
        "sediment": 0.25,
        "landuse_asm": 0.17,
        "environmental": 0.10,
        "socioeconomic": 0.14,
    }:
        raise RuntimeError("rerun PIM manifest weights differ from the frozen Supervisor v07 contract")
    if sentinel_manifest.get("pixel_asset_downloaded") is not False:
        raise RuntimeError("Sentinel pixel-access status changed; rerun handoff needs review")
    accumulation = {row["window"]: row for row in rainfall["accumulation_rows"]}
    now = datetime.now(timezone.utc)
    valid_cells = int(event.get("event_cells_with_valid_pim", 0))
    total_cells = int(event.get("event_grid_cells", 0))
    summary = {
        "rerun_id": f"secocha_2023_validation_rerun_{now.date().isoformat()}",
        "generated_utc": now.isoformat(),
        "boundary_id": boundary_id,
        "experiment_id": pim.get("experiment_id"),
        "status": "provisional_validation_rerun",
        "lineage_checks_passed": True,
        "lineage_checks": checks,
        "pim_rerun": {
            "status": "completed",
            "claim_level": pim.get("claim_level"),
            "weights_changed": False,
            "enters_pim_score": True,
            "run_manifest": artifact(PIM_MANIFEST),
            "priority_raster": priority_artifact,
            "quality_assurance": qa_artifact,
            "quality_assurance_status": qa.get("status"),
        },
        "historical_event_candidate": {
            "status": "recomputed_against_rerun_pim",
            "claim_level": event.get("claim_level"),
            "event_geometry_area_km2": event.get("event_geometry_area_km2"),
            "event_pim_coverage_fraction": event.get("event_pim_coverage_fraction"),
            "valid_support_cells": valid_cells,
            "total_event_cells": total_cells,
            "valid_support_fraction": event.get("event_pim_coverage_fraction"),
            "event_high_pim_fraction": event.get("event_high_pim_fraction"),
            "study_area_high_pim_fraction": event.get("study_area_high_pim_fraction"),
            "high_pim_enrichment_ratio": event.get("high_pim_enrichment_ratio"),
            "high_pim_enrichment_interpretation": f"valid-support enrichment (n={valid_cells}/{total_cells}); descriptive spatial agreement only",
            "event_pim_mean": event.get("event_pim_mean"),
            "study_area_pim_mean": event.get("study_area_pim_mean"),
            "comparison": artifact(EVENT_COMPARISON),
            "map7_manifest": artifact(MAP7_MANIFEST),
        },
        "ingemmet_context": {
            "status": "recomputed",
            "claim_level": original.get("claim_level"),
            "feature_count": original.get("feature_count"),
            "pdf_candidate_covered_by_original_fraction": original.get("pdf_event_candidate_covered_by_original_fraction"),
            "pdf_candidate_covered_by_flow_only_fraction": original.get("pdf_event_candidate_covered_by_flow_only_fraction"),
            "interpretation": original.get("interpretation"),
            "comparison": artifact(ORIGINAL_COMPARISON),
        },
        "event_rainfall_context": {
            "status": "acquired_and_compared",
            "claim_level": rainfall.get("claim_level"),
            "enters_pim_score": rainfall.get("enters_pim_score"),
            "interpretation": rainfall.get("interpretation"),
            "cum_1d_2023-02-05": accumulation.get("cum_1d_2023-02-05"),
            "cum_3d_2023-02-03_2023-02-05": accumulation.get("cum_3d_2023-02-03_2023-02-05"),
            "cum_7d_2023-01-30_2023-02-05": accumulation.get("cum_7d_2023-01-30_2023-02-05"),
            "cum_30d_2023-01-07_2023-02-05": accumulation.get("cum_30d_2023-01-07_2023-02-05"),
            "comparison": artifact(RAIN_COMPARISON),
        },
        "sentinel_context": {
            "status": "catalogue_quicklooks_and_raw_quantitative_pixels_acquired",
            "claim_level": sentinel_manifest.get("claim_level"),
            "pixel_asset_downloaded": True,
            "catalog_pixel_asset_downloaded_at_catalog_stage": sentinel_manifest.get("pixel_asset_downloaded"),
            "scene_count_s1": sentinel_summary.get("scene_count_s1"),
            "scene_count_s2_cloud_lte_60": sentinel_summary.get("scene_count_s2_cloud_lte_60"),
            "selected_scene_count": sentinel_summary.get("selected_scene_count"),
            "quicklook_count": sentinel_summary.get("quicklook_count"),
            "manifest": artifact(SENTINEL_MANIFEST),
            "summary": artifact(SENTINEL_SUMMARY),
            "quantitative_pixels": [
                {
                    "batch": item["batch"],
                    "asset_count": item["asset_count"],
                    "downloaded_bytes": item["downloaded_bytes"],
                    "size_checks_passed": item["size_checks_passed"],
                    "processing_status": "raw_assets_downloaded_not_processed",
                    "manifest": artifact(path),
                }
                for item, path in zip(sentinel_pixels, SENTINEL_PIXEL_MANIFESTS)
            ],
            "processed_products": [
                {
                    "dataset_id": sentinel_s2_processing.get("dataset_id"),
                    "status": "processed_validation_candidate",
                    "processing": sentinel_s2_processing.get("method"),
                    "before_valid_pixels_10m": sentinel_s2_processing.get("before_valid_pixels_10m"),
                    "after_valid_pixels_10m": sentinel_s2_processing.get("after_valid_pixels_10m"),
                    "common_valid_pixels_10m": sentinel_s2_processing.get("common_valid_pixels_10m"),
                    "new_surface_water_pixels_10m": sentinel_s2_processing.get("new_surface_water_pixels_10m"),
                    "lost_surface_water_pixels_10m": sentinel_s2_processing.get("lost_surface_water_pixels_10m"),
                    "interpretation": "Negative NDWI water diagnostic for a debris-flow event; not an event footprint or accuracy metric.",
                    "manifest": artifact(SENTINEL_S2_PROCESSING_QA),
                }
            ],
        },
        "remaining_blockers": [
            "The Map 7 footprint remains a semi-automatic validation candidate, not an independent survey footprint.",
            "CHIRPS sat/rnl are alternative daily temporal allocations; neither resolves the 14:00-14:17 local trigger intensity.",
            "Sentinel raw quantitative pixels are downloaded but still require radiometric calibration/noise removal, terrain correction, co-registration and S2 cloud masking before quantitative comparison.",
            "SENAMHI 2023 station/hourly observations require authenticated access or a formal data request.",
        ],
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = f"""# Secocha 2023 validation rerun

Status: **provisional validation rerun**  
Boundary: `{summary['boundary_id']}`  
Experiment: `{summary['experiment_id']}`  
Generated: `{summary['generated_utc']}`

## What was rerun

- The active Supervisor v07 Secocha PIM was rerun using the existing model input contract.
- Map 7's semi-automatic 5 February huaico/mudflow candidate was recomputed against the new PIM raster.
- The official INGEMMET MapServer comparison was recomputed.
- CHIRPS `sat`/`rnl` event-window rainfall was compared as validation context.
- Sentinel metadata/quicklooks plus the core S2 and S1 raw quantitative assets were linked; pixels remain unprocessed validation context.

## Rerun results

| Check | Result |
|---|---:|
| Event candidate area | {event['event_geometry_area_km2']:.3f} km² |
| Event cells with valid PIM (strict common support) | {valid_cells}/{total_cells} ({event['event_pim_coverage_fraction']:.1%}) |
| High-PIM share in event candidate (valid support) | {event['event_high_pim_fraction']:.1%} |
| High-PIM share in study window | {event['study_area_high_pim_fraction']:.1%} |
| High-PIM enrichment (valid support; n={valid_cells}/{total_cells}) | {event['high_pim_enrichment_ratio']:.3f}x |
| Event candidate PIM mean | {event['event_pim_mean']:.3f} |
| Study-window PIM mean | {event['study_area_pim_mean']:.3f} |
| PDF candidate covered by general INGEMMET polygons | {original['pdf_event_candidate_covered_by_original_fraction']:.1%} |
| PDF candidate covered by `Flujo de detritos` polygon | {original['pdf_event_candidate_covered_by_flow_only_fraction']:.1%} |
| Sentinel quicklooks | {sentinel_summary['quicklook_count']} |
| Sentinel raw quantitative assets | {sum(item['asset_count'] for item in sentinel_pixels)} files / {sum(item['downloaded_bytes'] for item in sentinel_pixels) / 1024**3:.2f} GiB |

The high-PIM threshold is **0.6**; with strict common support and no NoData imputation, {total_cells - valid_cells}/{total_cells} event cells are excluded, so the enrichment describes spatial agreement on valid support only.
Rainfall, Sentinel and INGEMMET layers are context that does not alter PIM weights, and the Map 7 geometry is a semi-automatic `validation_candidate`, not an official 5 February observed footprint.
Lineage checks: **{len(checks)}/{len(checks)} passed** (PIM raster + QA, Map 7 source/PIM, rainfall local artifacts, and Sentinel response/quicklook/raw-pixel files).
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON.relative_to(ROOT)), "markdown": str(OUT_MD.relative_to(ROOT)), "rerun_id": summary["rerun_id"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
