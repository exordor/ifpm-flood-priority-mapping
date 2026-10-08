#!/usr/bin/env python3
"""Acquire and QA a Goslar July-2017 Sentinel-2 event window."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import Window, from_bounds

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "data/validation/goslar_harz_2024_focus_area/satellite_2017"
OUT = ROOT / "outputs/goslar_2017_satellite_validation"
CATALOG = "https://earth-search.aws.element84.com/v1/search"


SCENES = {
    "before": {
        "date": "2017-07-21",
        "base": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/32/U/NC/2017/7/S2B_32UNC_20170721_0_L2A",
    },
    "after": {
        "date": "2017-07-31",
        "base": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/32/U/NC/2017/7/S2B_32UNC_20170731_0_L2A",
    },
}
BBOX_4326 = (10.25, 51.77, 10.57, 51.98)
BANDS = ("B02", "B03", "B04", "B08", "SCL")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_windows() -> dict:
    scenes = STAGE / "scenes"
    scenes.mkdir(parents=True, exist_ok=True)
    manifest = {"dataset_id": "goslar_2017_sentinel2_event_window", "scenes": {}}
    for role, info in SCENES.items():
        for band in BANDS:
            url = f"{info['base']}/{band}.tif"
            with rasterio.open(url) as src:
                left, bottom, right, top = transform_bounds(
                    "EPSG:4326", src.crs, *BBOX_4326, densify_pts=21
                )
                window = from_bounds(left, bottom, right, top, transform=src.transform).round_offsets().round_lengths()
                data = src.read(1, window=window)
                profile = src.profile.copy()
                profile.update(
                    height=data.shape[0], width=data.shape[1],
                    transform=src.window_transform(window), compress="deflate", tiled=True,
                )
                destination = scenes / f"{role}_{band}.tif"
                with rasterio.open(destination, "w", **profile) as dst:
                    dst.write(data, 1)
                manifest["scenes"].setdefault(role, {})[band] = {
                    "url": url, "path": str(destination.relative_to(ROOT)), "shape": list(data.shape)
                }
                if band == "SCL":
                    values, counts = np.unique(data, return_counts=True)
                    manifest["scenes"][role]["scl_classes"] = {
                        str(int(value)): int(count) for value, count in zip(values, counts)
                    }
    manifest["claim_level"] = "validation_candidate"
    manifest["access_date"] = date.today().isoformat()
    (OUT / "sentinel2_window_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def qa_water_change() -> dict:
    scenes = STAGE / "scenes"
    with rasterio.open(scenes / "before_B03.tif") as ref:
        profile = ref.profile.copy()
        transform, crs, shape = ref.transform, ref.crs, ref.shape
    boundary = gpd.read_file(
        ROOT / "outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg"
    ).to_crs(crs)
    basin = geometry_mask(
        [boundary.geometry.union_all()], out_shape=shape, transform=transform, invert=True
    )
    water_masks = {}
    for role in ("before", "after"):
        with rasterio.open(scenes / f"{role}_B03.tif") as green_src:
            green = green_src.read(1).astype("float32") / 10000.0
        with rasterio.open(scenes / f"{role}_B08.tif") as nir_src:
            nir = nir_src.read(1).astype("float32") / 10000.0
        ndwi = (green - nir) / (green + nir + 1e-6)
        with rasterio.open(scenes / f"{role}_SCL.tif") as scl_src:
            scl = np.zeros(shape, dtype="uint8")
            reproject(
                scl_src.read(1), scl, src_transform=scl_src.transform, src_crs=scl_src.crs,
                dst_transform=transform, dst_crs=crs, resampling=Resampling.nearest,
            )
        valid = (scl >= 4) & (scl <= 7)
        water_masks[role] = (ndwi > 0.15) & valid
        ndwi_profile = profile.copy()
        ndwi_profile.update(dtype="float32", nodata=np.nan, compress="deflate", tiled=True)
        with rasterio.open(OUT / f"{role}_ndwi_10m.tif", "w", **ndwi_profile) as dst:
            dst.write(np.where(valid, ndwi, np.nan), 1)
        water_profile = profile.copy()
        water_profile.update(dtype="uint8", nodata=255, compress="deflate", tiled=True)
        with rasterio.open(OUT / f"{role}_surface_water_candidate_10m.tif", "w", **water_profile) as dst:
            dst.write(water_masks[role].astype("uint8"), 1)

    masks = {
        "persistent_water_candidate_10m": water_masks["before"] & water_masks["after"],
        "new_surface_water_candidate_10m": water_masks["after"] & ~water_masks["before"],
        "lost_surface_water_candidate_10m": water_masks["before"] & ~water_masks["after"],
    }
    for name, mask in masks.items():
        water_profile = profile.copy()
        water_profile.update(dtype="uint8", nodata=255, compress="deflate", tiled=True)
        with rasterio.open(OUT / f"{name}.tif", "w", **water_profile) as dst:
            dst.write(np.where(basin, mask, 255).astype("uint8"), 1)

    result = {
        "claim_level": "validation_candidate",
        "dates": {role: SCENES[role]["date"] for role in SCENES},
        "method": "NDWI=(B03-B08)/(B03+B08), water candidate NDWI > 0.15; SCL 4-7 valid; masks clipped to goslar_wrrl_water_bodies_reference_v1",
        "official_basin_pixels_10m": int(basin.sum()),
        "before_water_px": int((water_masks["before"] & basin).sum()),
        "after_water_px": int((water_masks["after"] & basin).sum()),
        "persistent_px": int((masks["persistent_water_candidate_10m"] & basin).sum()),
        "new_px": int((masks["new_surface_water_candidate_10m"] & basin).sum()),
        "lost_px": int((masks["lost_surface_water_candidate_10m"] & basin).sum()),
        "limitations": [
            "Optical Sentinel-2 cannot see through clouds or canopy",
            "The after image is five days post-peak and is not peak-flood extent",
            "NDWI > 0.15 is a simple threshold without shadow or terrain correction",
            "Validation candidate only, not an official observed flood footprint",
        ],
    }
    for name in (
        "before_ndwi_10m.tif", "after_ndwi_10m.tif",
        "before_surface_water_candidate_10m.tif", "after_surface_water_candidate_10m.tif",
        "persistent_water_candidate_10m.tif", "new_surface_water_candidate_10m.tif",
        "lost_surface_water_candidate_10m.tif",
    ):
        path = OUT / name
        result[name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (OUT / "water_change_qa.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()
    STAGE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.skip_download:
        download_windows()
    print(json.dumps(qa_water_change(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
