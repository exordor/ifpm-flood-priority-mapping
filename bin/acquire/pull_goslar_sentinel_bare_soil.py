#!/usr/bin/env python3
"""Build a reproducible Goslar bare-soil-frequency candidate from Sentinel-2.

The script queries the public Element 84 Earth Search STAC catalogue for
Sentinel-2 Collection-1 Level-2A COGs, selects two low-cloud scenes per
spring/summer/autumn period in 2021 and 2023-2025, and snapshots only the
Goslar focus window. It implements
the Copernicus Data Space soil-erosion example's modified bareness index (MBI)
and preserves cloud/snow/invalid observations as NoData.

This is a diagnostic candidate, not an automatic replacement for the active
WorldCover component. Run with the workspace GIS environment:

    .venv/bin/python bin/acquire/pull_goslar_sentinel_bare_soil.py
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
import warnings
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import reproject


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "outputs/goslar_focus_boundary/goslar_focus_boundary.gpkg"
BOUNDARY_LAYER = "goslar_focus_boundary"
REFERENCE = ROOT / "outputs/srtm_1arcsec_goslar/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif"
RAW_DIR = ROOT / "data/raw/sentinel2_l2a_goslar_bare_soil"
SCENE_DIR = RAW_DIR / "scene_windows_c1_10m"
CATALOG_PATH = RAW_DIR / "earth_search_catalog.json"
OUT_DIR = ROOT / "outputs/goslar_sentinel_bare_soil_candidate"

STAC_SEARCH = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-c1-l2a"
START_YEAR = 2021
END_YEAR = 2025
# Earth Search Collection 1 does not currently provide complete 2022 coverage.
# Keep an explicit gap rather than mixing the legacy, radiometrically
# inconsistent collection into the time series.
OBSERVATION_YEARS = (2021, 2023, 2024, 2025)
SEASONS = {"spring": (3, 5), "summer": (6, 8), "autumn": (9, 11)}
SCENES_PER_SEASON = 2
MAX_CATALOG_CLOUD = 40.0
MINIMUM_CLEAR_OBSERVATIONS = 5
TARGET_CRS = "EPSG:32632"
TARGET_RESOLUTION_M = 10.0
NODATA = -9999.0

REFLECTANCE_ASSETS = ("blue", "red", "nir", "swir16")
INVALID_SCL = np.array([0, 1, 3, 7, 8, 9, 10, 11], dtype="uint8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_bare_soil(
    blue: np.ndarray,
    red: np.ndarray,
    nir: np.ndarray,
    swir: np.ndarray,
    scl: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return bare mask, clear-observation mask and Copernicus-example MBI."""
    finite = np.isfinite(blue) & np.isfinite(red) & np.isfinite(nir) & np.isfinite(swir)
    physical = (
        (blue >= 0) & (blue <= 1.5)
        & (red >= 0) & (red <= 1.5)
        & (nir >= 0) & (nir <= 1.5)
        & (swir >= 0) & (swir <= 1.5)
    )
    scl_codes = np.where(np.isfinite(scl), scl, 0).astype("uint8")
    clear = finite & physical & ~np.isin(scl_codes, INVALID_SCL)
    denominator = swir + red + nir + blue
    with np.errstate(divide="ignore", invalid="ignore"):
        mbi = 2.5 * (swir + red - nir - blue) / denominator
    mbi = np.where(clear & np.isfinite(mbi) & (denominator != 0), mbi, np.nan).astype("float32")
    bare = clear & (mbi > 0)
    return bare, clear, mbi


def safe_ndvi(red: np.ndarray, nir: np.ndarray, clear: np.ndarray) -> np.ndarray:
    """Calculate physically bounded NDVI only where reflectance support is stable."""
    denominator = nir + red
    supported = clear & np.isfinite(red) & np.isfinite(nir) & (red >= 0) & (nir >= 0)
    supported &= denominator >= 0.05
    result = np.full(red.shape, np.nan, dtype="float32")
    with np.errstate(divide="ignore", invalid="ignore"):
        result[supported] = (nir[supported] - red[supported]) / denominator[supported]
    result[(result < -1) | (result > 1)] = np.nan
    return result


def bare_frequency(
    bare_count: np.ndarray,
    clear_count: np.ndarray,
    minimum_clear: int = MINIMUM_CLEAR_OBSERVATIONS,
) -> np.ndarray:
    """Calculate frequency while keeping insufficient support as NoData."""
    result = np.full(clear_count.shape, np.nan, dtype="float32")
    supported = clear_count >= minimum_clear
    result[supported] = bare_count[supported] / clear_count[supported]
    return result


def post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "IFPM-Goslar/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def query_catalog(bounds_wgs84: tuple[float, float, float, float]) -> list[dict]:
    payload = {
        "collections": [COLLECTION],
        "bbox": list(bounds_wgs84),
        "datetime": f"{START_YEAR}-03-01T00:00:00Z/{END_YEAR}-11-30T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": MAX_CATALOG_CLOUD}},
        "limit": 1000,
    }
    result = post_json(STAC_SEARCH, payload)
    features = result.get("features", [])
    if not features:
        raise RuntimeError("Earth Search returned no Sentinel-2 L2A scenes for Goslar")
    return features


def choose_distinct_dates(candidates: list[dict], count: int) -> list[dict]:
    """Choose low-cloud scenes without double-counting processing revisions."""
    ordered = sorted(
        candidates,
        key=lambda item: (
            float(item["properties"].get("eo:cloud_cover", 100.0)),
            item["properties"]["datetime"],
        ),
    )
    selected = []
    used_dates = set()
    for item in ordered:
        sensing_date = item["properties"]["datetime"][:10]
        if sensing_date in used_dates:
            continue
        selected.append(item)
        used_dates.add(sensing_date)
        if len(selected) == count:
            break
    return selected


def validate_scene_contract(features: list[dict]) -> None:
    """Fail closed when a scene is outside the harmonized Collection-1 contract."""
    for feature in features:
        baseline_text = str(feature.get("properties", {}).get("s2:processing_baseline", "0"))
        try:
            baseline = float(baseline_text)
        except ValueError as exc:
            raise ValueError(f"invalid processing baseline for {feature.get('id')}: {baseline_text}") from exc
        if baseline < 5.0:
            raise ValueError(
                f"processing baseline {baseline_text} for {feature.get('id')} is below Collection-1 5.x"
            )


def select_scenes(features: list[dict]) -> list[dict]:
    """Select balanced, low-catalog-cloud observations for each year/season."""
    grouped: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for feature in features:
        timestamp = datetime.fromisoformat(feature["properties"]["datetime"].replace("Z", "+00:00"))
        for season, (month_min, month_max) in SEASONS.items():
            if month_min <= timestamp.month <= month_max:
                grouped[(timestamp.year, season)].append(feature)
                break

    selected = []
    for year in OBSERVATION_YEARS:
        for season in SEASONS:
            candidates = choose_distinct_dates(grouped[(year, season)], SCENES_PER_SEASON)
            if len(candidates) < SCENES_PER_SEASON:
                raise RuntimeError(f"insufficient Sentinel-2 scenes for {year} {season}")
            selected.extend(candidates)
    selected = sorted(selected, key=lambda item: item["properties"]["datetime"])
    validate_scene_contract(selected)
    return selected


def target_grid() -> tuple[dict, np.ndarray, tuple[float, float, float, float]]:
    if not BOUNDARY.exists() or not REFERENCE.exists():
        raise FileNotFoundError("Goslar boundary/reference grid must exist before Sentinel processing")
    boundary_m = gpd.read_file(BOUNDARY, layer=BOUNDARY_LAYER).to_crs(TARGET_CRS)
    boundary_wgs84 = boundary_m.to_crs(4326)
    with rasterio.open(REFERENCE) as ref:
        bounds = ref.bounds
    width = int(np.ceil((bounds.right - bounds.left) / TARGET_RESOLUTION_M))
    height = int(np.ceil((bounds.top - bounds.bottom) / TARGET_RESOLUTION_M))
    transform = from_origin(bounds.left, bounds.top, TARGET_RESOLUTION_M, TARGET_RESOLUTION_M)
    mask = geometry_mask(
        boundary_m.geometry,
        out_shape=(height, width),
        transform=transform,
        invert=True,
    )
    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": TARGET_CRS,
        "transform": transform,
        "nodata": NODATA,
        "compress": "deflate",
        "tiled": True,
    }
    return profile, mask, tuple(float(value) for value in boundary_wgs84.total_bounds)


def read_asset(asset: dict, profile: dict, categorical: bool = False) -> np.ndarray:
    resampling = Resampling.nearest if categorical else Resampling.bilinear
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3"):
        with rasterio.open(asset["href"]) as source:
            with WarpedVRT(
                source,
                crs=profile["crs"],
                transform=profile["transform"],
                width=profile["width"],
                height=profile["height"],
                src_nodata=source.nodata,
                nodata=np.nan,
                dtype="float32",
                resampling=resampling,
            ) as vrt:
                data = vrt.read(1).astype("float32")
    if categorical:
        return data
    raster_meta = asset.get("raster:bands", [{}])[0]
    scale = float(raster_meta.get("scale", 1.0))
    offset = float(raster_meta.get("offset", 0.0))
    return data * scale + offset


def write_float(path: Path, data: np.ndarray, profile: dict, descriptions: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 1 if data.ndim == 2 else data.shape[0]
    out_profile = profile | {"count": count}
    with rasterio.open(path, "w", **out_profile) as dst:
        arrays = data[np.newaxis, ...] if data.ndim == 2 else data
        dst.write(np.where(np.isfinite(arrays), arrays, NODATA).astype("float32"))
        if descriptions:
            for band, description in enumerate(descriptions, start=1):
                dst.set_band_description(band, description)


def snapshot_scene(feature: dict, profile: dict, mask: np.ndarray) -> tuple[dict, dict[str, np.ndarray]]:
    arrays = {name: read_asset(feature["assets"][name], profile) for name in REFLECTANCE_ASSETS}
    arrays["scl"] = read_asset(feature["assets"]["scl"], profile, categorical=True)
    for name in arrays:
        arrays[name] = np.where(mask, arrays[name], np.nan).astype("float32")

    snapshot = SCENE_DIR / f"{feature['id']}_goslar_10m.tif"
    write_float(
        snapshot,
        np.stack([arrays["blue"], arrays["red"], arrays["nir"], arrays["swir16"], arrays["scl"]]),
        profile,
        ["blue_reflectance", "red_reflectance", "nir_reflectance", "swir16_reflectance", "SCL"],
    )
    record = {
        "id": feature["id"],
        "datetime": feature["properties"]["datetime"],
        "catalog_cloud_percent": feature["properties"].get("eo:cloud_cover"),
        "processing_baseline": feature["properties"].get("s2:processing_baseline"),
        "earth_search_self": next(
            (link["href"] for link in feature.get("links", []) if link.get("rel") == "self"), None
        ),
        "source_assets": {name: feature["assets"][name]["href"] for name in (*REFLECTANCE_ASSETS, "scl")},
        "local_snapshot": str(snapshot.relative_to(ROOT)),
        "local_sha256": sha256_file(snapshot),
        "local_bytes": snapshot.stat().st_size,
    }
    return record, arrays


def align_to_reference(source: np.ndarray, source_profile: dict, mask_30m: np.ndarray) -> np.ndarray:
    with rasterio.open(REFERENCE) as ref:
        destination = np.full((ref.height, ref.width), np.nan, dtype="float32")
        reproject(
            source=source,
            destination=destination,
            src_transform=source_profile["transform"],
            src_crs=source_profile["crs"],
            src_nodata=np.nan,
            dst_transform=ref.transform,
            dst_crs=ref.crs,
            dst_nodata=np.nan,
            resampling=Resampling.average,
        )
    destination[~mask_30m] = np.nan
    return destination


def raster_stats(data: np.ndarray, mask: np.ndarray) -> dict:
    values = data[mask & np.isfinite(data)]
    return {
        "valid_cells": int(values.size),
        "coverage_fraction": float(values.size / int(mask.sum())),
        "nonzero_cells": int(np.count_nonzero(values > 0)),
        "min": float(values.min()) if values.size else None,
        "median": float(np.median(values)) if values.size else None,
        "p98": float(np.percentile(values, 98)) if values.size else None,
        "max": float(values.max()) if values.size else None,
    }


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    profile, focus_mask, bounds_wgs84 = target_grid()
    selected = select_scenes(query_catalog(bounds_wgs84))

    bare_count = np.zeros(focus_mask.shape, dtype="uint16")
    clear_count = np.zeros(focus_mask.shape, dtype="uint16")
    annual_ndvi: dict[int, list[np.ndarray]] = defaultdict(list)
    scene_records = []
    for index, feature in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {feature['id']}", flush=True)
        record, arrays = snapshot_scene(feature, profile, focus_mask)
        bare, clear, _ = classify_bare_soil(
            arrays["blue"], arrays["red"], arrays["nir"], arrays["swir16"], arrays["scl"]
        )
        bare_count += bare.astype("uint16")
        clear_count += clear.astype("uint16")
        ndvi = safe_ndvi(arrays["red"], arrays["nir"], clear)
        year = datetime.fromisoformat(record["datetime"].replace("Z", "+00:00")).year
        annual_ndvi[year].append(ndvi)
        record["clear_focus_fraction"] = float(np.count_nonzero(clear) / int(focus_mask.sum()))
        record["bare_focus_fraction_of_clear"] = (
            float(np.count_nonzero(bare) / np.count_nonzero(clear)) if np.count_nonzero(clear) else None
        )
        scene_records.append(record)

    frequency = bare_frequency(bare_count, clear_count)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered", category=RuntimeWarning)
        baseline_ndvi = np.nanmedian(np.stack(annual_ndvi[START_YEAR]), axis=0).astype("float32")
        recent_ndvi = np.nanmedian(np.stack(annual_ndvi[END_YEAR]), axis=0).astype("float32")
    vegetation_decline = np.clip(baseline_ndvi - recent_ndvi, 0.0, 1.0)
    vegetation_decline[~focus_mask] = np.nan

    outputs_10m = {
        "bare_soil_frequency_2021_2025_10m.tif": frequency,
        "clear_observation_count_2021_2025_10m.tif": clear_count.astype("float32"),
        "ndvi_median_2021_10m.tif": baseline_ndvi,
        "ndvi_median_2025_10m.tif": recent_ndvi,
        "vegetation_decline_ndvi_2021_2025_10m.tif": vegetation_decline,
    }
    for filename, array in outputs_10m.items():
        write_float(OUT_DIR / filename, np.where(focus_mask, array, np.nan), profile)

    boundary_m = gpd.read_file(BOUNDARY, layer=BOUNDARY_LAYER).to_crs(TARGET_CRS)
    with rasterio.open(REFERENCE) as ref:
        mask_30m = geometry_mask(
            boundary_m.geometry, out_shape=(ref.height, ref.width), transform=ref.transform, invert=True
        )
        reference_profile = ref.profile | {
            "driver": "GTiff", "count": 1, "dtype": "float32", "nodata": NODATA,
            "compress": "deflate", "tiled": True,
        }
    aligned_outputs = {
        "bare_soil_frequency_2021_2025_30m.tif": align_to_reference(frequency, profile, mask_30m),
        "vegetation_decline_ndvi_2021_2025_30m.tif": align_to_reference(
            vegetation_decline, profile, mask_30m
        ),
    }
    for filename, array in aligned_outputs.items():
        write_float(OUT_DIR / filename, array, reference_profile)

    catalog = {
        "dataset_id": "sentinel2_l2a_goslar_bare_soil_candidate",
        "publisher": "ESA Copernicus Sentinel-2; public COG mirror/catalogue via Element 84 Earth Search",
        "catalog_url": STAC_SEARCH,
        "collection": COLLECTION,
        "access_date": date.today().isoformat(),
        "focus_extent_wgs84": list(bounds_wgs84),
        "selection": {
            "date_range": [START_YEAR, END_YEAR],
            "observation_years": list(OBSERVATION_YEARS),
            "excluded_years": {"2022": "incomplete Earth Search Collection-1 archive coverage"},
            "months": "March-November",
            "seasons": SEASONS,
            "scenes_per_year_season": SCENES_PER_SEASON,
            "max_catalog_cloud_percent": MAX_CATALOG_CLOUD,
            "selected_scene_count": len(selected),
        },
        "scenes": scene_records,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    diagnostics = {
        "experiment_id": "goslar_sentinel_bare_soil_candidate_v0_1",
        "claim_level": "diagnostic_only",
        "enters_pim_score": False,
        "method": {
            "bare_soil": "Copernicus soil-erosion example modified bareness index; MBI > 0",
            "mbi_formula": "2.5 * (B11 + B04 - B08 - B02) / (B11 + B04 + B08 + B02)",
            "invalid_scl": INVALID_SCL.tolist(),
            "nodata_policy": f"cloud/snow/invalid stay NoData; frequency requires >= {MINIMUM_CLEAR_OBSERVATIONS} clear observations",
            "vegetation_decline": "positive difference between median clear-pixel NDVI in 2021 and 2025; candidate, not validated forest loss",
        },
        "source_catalog": {
            "path": str(CATALOG_PATH.relative_to(ROOT)),
            "sha256": sha256_file(CATALOG_PATH),
        },
        "outputs": {},
        "limitations": [
            "Earth Search is a public Sentinel-2 COG mirror, not the Copernicus Data Space API endpoint.",
            "MBI can respond to built or naturally non-vegetated surfaces; local validation is required.",
            "NDVI decline is seasonal/composite evidence and is not a verified tree-loss product.",
            "The layers are candidates and do not enter the active PIM score.",
        ],
    }
    for filename, array in outputs_10m.items():
        path = OUT_DIR / filename
        diagnostics["outputs"][filename] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
            "stats_within_focus": raster_stats(array, focus_mask),
        }
    for filename, array in aligned_outputs.items():
        path = OUT_DIR / filename
        diagnostics["outputs"][filename] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
            "stats_within_focus": raster_stats(array, mask_30m),
        }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "candidate_built", "selected_scenes": len(selected)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
