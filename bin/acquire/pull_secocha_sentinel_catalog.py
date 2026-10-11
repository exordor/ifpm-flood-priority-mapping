#!/usr/bin/env python3
"""Freeze an official Copernicus Data Space Sentinel event catalogue for Secocha.

The public STAC endpoint is queried without credentials.  It provides scene
metadata, footprints and asset links.  This script also stores small public
quicklooks for human review; it deliberately does not pretend that an S3 COG
asset was downloaded or that a quicklook is quantitative pixel evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform as shapely_transform


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg"
BOUNDARY_ID = "secocha_reference_extent"
DATA_DIR = ROOT / "data/validation/secocha_2023_validation/satellite_before_after"
CATALOG_DIR = DATA_DIR / "catalog"
QUICKLOOK_DIR = DATA_DIR / "quicklooks"
OUTPUT_DIR = ROOT / "outputs/secocha_2023_validation/satellite_before_after"
MANIFEST_PATH = OUTPUT_DIR / "sentinel_catalog_manifest.json"
SUMMARY_PATH = OUTPUT_DIR / "sentinel_catalog_summary.json"
SELECTED_GEOJSON = DATA_DIR / "selected_scenes.geojson"
STAC_SEARCH = "https://stac.dataspace.copernicus.eu/v1/search"
STAC_DOCS = "https://documentation.dataspace.copernicus.eu/APIs/STAC.html"
ODATA_DOCS = "https://documentation.dataspace.copernicus.eu/APIs/OData.html"
S3_DOCS = "https://documentation.dataspace.copernicus.eu/APIs/S3.html"
TIME_RANGE = "2023-01-20T00:00:00Z/2023-02-20T23:59:59Z"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def post_json(url: str, payload: dict[str, object], context: ssl.SSLContext) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "IFPM-Secocha/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("type") == "Error" or result.get("error"):
        raise RuntimeError(f"Copernicus STAC query failed: {result}")
    return result


def download_quicklook(url: str, destination: Path, context: ssl.SSLContext) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "IFPM-Secocha/1.0"})
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        payload = response.read()
        content_type = response.headers.get("Content-Type")
    partial.write_bytes(payload)
    partial.replace(destination)
    return {
        "path": str(destination.relative_to(ROOT)),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "content_type": content_type,
    }


def overlap_fraction(feature_geometry: dict[str, object], aoi_utm) -> float:
    scene = shape(feature_geometry)
    if scene.is_empty:
        return 0.0
    if not scene.is_valid:
        scene = scene.buffer(0)
    scene_utm = shapely_transform(Transformer.from_crs(4326, 32718, always_xy=True).transform, scene)
    intersection_area = scene_utm.intersection(aoi_utm).area
    return float(intersection_area / aoi_utm.area) if aoi_utm.area else 0.0


def asset_summary(feature: dict[str, object]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for key, asset in (feature.get("assets") or {}).items():
        if not isinstance(asset, dict):
            continue
        result[key] = {
            field: asset[field]
            for field in ("href", "type", "title", "roles", "file:size")
            if field in asset
        }
    return result


def scene_record(feature: dict[str, object], aoi_utm) -> dict[str, object]:
    properties = feature.get("properties") or {}
    assets = feature.get("assets") or {}
    links = feature.get("links") or []
    self_link = next((link.get("href") for link in links if link.get("rel") == "self"), None)
    enclosure_link = next((link.get("href") for link in links if link.get("rel") == "enclosure"), None)
    thumbnail = None
    for key, asset in assets.items():
        if not isinstance(asset, dict):
            continue
        roles = asset.get("roles") or []
        if key in {"thumbnail", "preview"} or "thumbnail" in roles or "overview" in roles:
            if isinstance(asset.get("href"), str) and asset["href"].startswith("https://"):
                thumbnail = {"asset_key": key, "href": asset["href"]}
                break
    odata_asset_uuid = None
    thumbnail_provider = None
    if thumbnail:
        thumbnail_provider = thumbnail["href"].split("/", 3)[2]
        match = re.search(r"Assets\(([0-9a-fA-F-]{36})\)", thumbnail["href"])
        if match:
            odata_asset_uuid = match.group(1)
    return {
        "id": feature.get("id"),
        "collection": feature.get("collection"),
        "sensing_datetime": properties.get("datetime"),
        "start_datetime": properties.get("start_datetime"),
        "end_datetime": properties.get("end_datetime"),
        "platform": properties.get("platform"),
        "processing_level": properties.get("processing:level"),
        "cloud_cover_percent": properties.get("eo:cloud_cover"),
        "grid_code": properties.get("grid:code"),
        "orbit_state": properties.get("sat:orbit_state"),
        "relative_orbit": properties.get("sat:relative_orbit"),
        "absolute_orbit": properties.get("sat:absolute_orbit"),
        "polarizations": properties.get("sar:polarizations"),
        "product_uuid": (properties.get("_private") or {}).get("product_uuid"),
        "odata_thumbnail_asset_uuid": odata_asset_uuid,
        "thumbnail_provider": thumbnail_provider,
        "stac_item_self": self_link,
        "stac_enclosure_href": enclosure_link,
        "overlap_fraction_with_active_boundary": overlap_fraction(feature["geometry"], aoi_utm),
        "thumbnail": thumbnail,
        "assets": asset_summary(feature),
    }


def main() -> None:
    run_started_utc = datetime.now(timezone.utc).isoformat()
    boundary = gpd.read_file(BOUNDARY, layer="secocha_active_boundary").to_crs(32718)
    if len(boundary) != 1:
        raise RuntimeError(f"expected one active boundary, got {len(boundary)}")
    aoi_utm = boundary.geometry.iloc[0]
    aoi_wgs84 = boundary.to_crs(4326)
    bbox = [float(value) for value in aoi_wgs84.total_bounds]
    context = ssl.create_default_context()
    queries = {
        "sentinel1_grd": {
            "collections": ["sentinel-1-grd"],
            "bbox": bbox,
            "datetime": TIME_RANGE,
            "limit": 100,
        },
        "sentinel2_l2a": {
            "collections": ["sentinel-2-l2a"],
            "bbox": bbox,
            "datetime": TIME_RANGE,
            "limit": 100,
            "query": {"eo:cloud_cover": {"lte": 60}},
        },
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    responses: dict[str, dict[str, object]] = {}
    response_files: list[dict[str, object]] = []
    for key, query in queries.items():
        query_path = CATALOG_DIR / f"{key}_query.json"
        response_path = CATALOG_DIR / f"{key}_response.json"
        query_path.write_text(json.dumps(query, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        response = post_json(STAC_SEARCH, query, context)
        returned = int(response.get("numberReturned", len(response.get("features", []))))
        if returned >= int(query["limit"]):
            raise RuntimeError(f"STAC response for {key} reached limit={query['limit']}; refusing an unpaginated catalogue")
        response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        responses[key] = response
        response_files.extend(
            [
                {"path": str(query_path.relative_to(ROOT)), "bytes": query_path.stat().st_size, "sha256": sha256(query_path)},
                {"path": str(response_path.relative_to(ROOT)), "bytes": response_path.stat().st_size, "sha256": sha256(response_path)},
            ]
        )

    all_features = [feature for response in responses.values() for feature in response.get("features", [])]
    by_id = {feature.get("id"): feature for feature in all_features}
    selected_prefixes = [
        ("s1_pre", "S1A_IW_GRDH_1SDV_20230129T102426_20230129T102458_046997_05A329_0328_COG"),
        ("s1_post", "S1A_IW_GRDH_1SDV_20230210T102425_20230210T102457_047172_05A8F7_D317_COG"),
        ("s2_pre_event", "S2A_MSIL2A_20230203T145721_N0510_R039_T18LXH_"),
        ("s2_post_3d", "S2B_MSIL2A_20230208T145729_N0510_R039_T18LXH_"),
        ("s2_post_8d", "S2A_MSIL2A_20230213T145721_N0510_R039_T18LXH_"),
        ("s2_full_pre", "S2B_MSIL2A_20230122T150719_N0510_R082_T18LXH_"),
        ("s2_full_post", "S2B_MSIL2A_20230211T150719_N0510_R082_T18LXH_"),
    ]
    selected: list[dict[str, object]] = []
    selected_features: list[dict[str, object]] = []
    quicklooks: list[dict[str, object]] = []
    for label, prefix in selected_prefixes:
        candidates = [feature for feature in all_features if str(feature.get("id", "")).startswith(prefix)]
        if len(candidates) != 1:
            raise RuntimeError(f"expected exactly one STAC item for {label} prefix {prefix}, got {len(candidates)}")
        feature = candidates[0]
        record = scene_record(feature, aoi_utm)
        record["role"] = label
        if record["thumbnail"]:
            thumbnail = record["thumbnail"]
            suffix = ".jpg" if "jpeg" in str((feature.get("assets") or {}).get(thumbnail["asset_key"], {}).get("type", "")) else ".png"
            filename = f"{label}_{str(feature['id']).replace('/', '_')}{suffix}"
            try:
                downloaded = download_quicklook(thumbnail["href"], QUICKLOOK_DIR / filename, context)
                record["thumbnail_download"] = downloaded
                quicklooks.append({"scene_id": feature.get("id"), **downloaded})
            except Exception as exc:  # keep catalogue usable if a thumbnail host changes
                record["thumbnail_download_error"] = repr(exc)
        selected.append(record)
        selected_features.append(
            {
                "type": "Feature",
                "id": feature.get("id"),
                "geometry": feature.get("geometry"),
                "properties": {key: value for key, value in record.items() if key not in {"assets", "thumbnail"}},
            }
        )

    SELECTED_GEOJSON.write_text(
        json.dumps({"type": "FeatureCollection", "features": selected_features}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    selected_geojson_record = {
        "path": str(SELECTED_GEOJSON.relative_to(ROOT)),
        "bytes": SELECTED_GEOJSON.stat().st_size,
        "sha256": sha256(SELECTED_GEOJSON),
    }
    manifest = {
        "dataset_id": "secocha_2023_sentinel_before_after_catalog",
        "event_id": "secocha_2023_historical_hazard_event",
        "event_date": "2023-02-05",
        "event_local_timezone": "America/Lima (PET, UTC-05:00)",
        "event_time_local": "2023-02-05 14:00-14:17",
        "event_time_utc": "2023-02-05 19:00-19:17Z",
        "boundary_id": BOUNDARY_ID,
        "boundary_path": str(BOUNDARY.relative_to(ROOT)),
        "boundary_sha256": sha256(BOUNDARY),
        "claim_level": "validation_candidate",
        "enters_pim_score": False,
        "role": "before-after scene catalogue and quicklook context; not yet quantitative pixel validation",
        "publisher": "Copernicus Data Space Ecosystem",
        "stac_search_url": STAC_SEARCH,
        "stac_documentation_url": STAC_DOCS,
        "odata_download_documentation_url": ODATA_DOCS,
        "s3_documentation_url": S3_DOCS,
        "access_date": str(date.today()),
        "run_started_utc": run_started_utc,
        "run_finished_utc": datetime.now(timezone.utc).isoformat(),
        "bbox_wgs84": bbox,
        "datetime": TIME_RANGE,
        "queries": queries,
        "response_files": response_files,
        "response_counts": {
            key: {
                "number_returned": response.get("numberReturned"),
                "number_matched": response.get("numberMatched"),
                "next_links": [link for link in response.get("links", []) if link.get("rel") == "next"],
            }
            for key, response in responses.items()
        },
        "selected_scenes": selected,
        "selection_policy": "Frozen event-relative item prefixes (same-orbit S1 pre/post; low-cloud and full-overlap S2 alternatives); reruns fail on zero/multiple matches rather than silently switching processing versions.",
        "quicklooks": quicklooks,
        "selected_scenes_geojson": selected_geojson_record,
        "pixel_asset_downloaded": False,
        "data_terms": {
            "metadata_and_quicklook": "Copernicus Data Space Ecosystem public catalogue/preview access; retain source attribution and check current terms before redistribution.",
            "quantitative_assets": "CDSE account/token and applicable Copernicus Sentinel data terms required for S3/OData downloads.",
            "licence_documentation": "https://dataspace.copernicus.eu/data-access",
        },
        "access_boundary": [
            "STAC metadata, footprints, asset hrefs and public quicklooks were retrievable without credentials.",
            "Quantitative Sentinel-1/2 assets point to CDSE S3 and require registered credentials; no access token or key is stored.",
            "Quicklooks are for visual scene/cloud/coverage review only and are not used as radiometric or spectral measurements.",
        ],
        "recommended_next_processing": [
            "With CDSE access, download the selected Sentinel-1 VV/VH GRD pair (2023-01-29 and 2023-02-10), then orbit-correct, calibrate, terrain-correct and co-register before log-ratio analysis.",
            "With CDSE access, download Sentinel-2 B02/B03/B04/B08 plus SCL at native 10/20 m for the selected before/after scenes, cloud-mask, and compare only as validation_candidate.",
        ],
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "dataset_id": manifest["dataset_id"],
        "scene_count_s1": len(responses["sentinel1_grd"].get("features", [])),
        "scene_count_s2_cloud_lte_60": len(responses["sentinel2_l2a"].get("features", [])),
        "selected_scene_count": len(selected),
        "quicklook_count": len(quicklooks),
        "selected_scene_roles": [{"role": item["role"], "id": item["id"], "datetime": item["sensing_datetime"], "cloud_cover_percent": item["cloud_cover_percent"], "overlap_fraction": item["overlap_fraction_with_active_boundary"]} for item in selected],
        "pixel_asset_downloaded": False,
        "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
        "selected_scenes_geojson": str(SELECTED_GEOJSON.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
