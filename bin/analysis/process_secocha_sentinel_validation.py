#!/usr/bin/env python3
"""Process the downloaded Secocha Sentinel-2 before/after core pair.

The result is a validation-candidate optical change diagnostic.  It is clipped
to the active Secocha reference window, uses native 10 m grid geometry with a
20 m SCL cloud mask, and never enters the PIM score.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/secocha_2023_validation/satellite_before_after"
PIXEL_MANIFEST = BASE / "sentinel_pixel_download_core_s2_manifest.json"
BOUNDARY = ROOT / "outputs/secocha_boundary/secocha_boundary.gpkg"
BOUNDARY_LAYER = "secocha_active_boundary"
OUT = BASE / "processed"
PRE_ROLE = "s2_pre_event"
POST_ROLE = "s2_post_3d"
DATES = {"before": "2023-02-03", "after": "2023-02-08"}
SCL_VALID_CLASSES = {4, 5, 6, 7}
NDWI_THRESHOLD = 0.15


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_path(role: str, asset: str) -> Path:
    manifest = json.loads(PIXEL_MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["downloaded_assets"]:
        if item["role"] == role and item["asset"] == asset:
            path = ROOT / item["path"]
            if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                raise RuntimeError(f"Sentinel pixel artifact failed lineage check: {path}")
            return path
    raise RuntimeError(f"missing downloaded asset: {role}/{asset}")


def reference_profile() -> tuple[dict[str, object], np.ndarray]:
    with rasterio.open(asset_path(PRE_ROLE, "B03_10m")) as source:
        profile = source.profile.copy()
        profile.update(compress="deflate", tiled=True, BIGTIFF="IF_SAFER")
        boundary = gpd.read_file(BOUNDARY, layer=BOUNDARY_LAYER).to_crs(source.crs)
        mask = geometry_mask(
            [boundary.geometry.union_all()],
            out_shape=(source.height, source.width),
            transform=source.transform,
            invert=True,
        )
        # Keep only a modest margin around the 30 km² reference window so the
        # full 10980² tile is not carried through every derived product.
        rows, cols = np.where(mask)
        row0, row1 = max(int(rows.min()) - 100, 0), min(int(rows.max()) + 101, source.height)
        col0, col1 = max(int(cols.min()) - 100, 0), min(int(cols.max()) + 101, source.width)
        profile.update(
            height=row1 - row0,
            width=col1 - col0,
            transform=source.transform * rasterio.Affine.translation(col0, row0),
        )
        cropped = geometry_mask(
            [boundary.geometry.union_all()],
            out_shape=(profile["height"], profile["width"]),
            transform=profile["transform"],
            invert=True,
        )
        return profile, cropped


def read_band(role: str, asset: str, profile: dict[str, object]) -> np.ndarray:
    path = asset_path(role, asset)
    with rasterio.open(path) as source:
        window = rasterio.windows.from_bounds(
            profile["transform"].c,
            profile["transform"].f + profile["transform"].e * profile["height"],
            profile["transform"].c + profile["transform"].a * profile["width"],
            profile["transform"].f,
            transform=source.transform,
        ).round_offsets().round_lengths()
        data = source.read(1, window=window)
        expected_shape = (profile["height"], profile["width"])
        if data.shape != expected_shape:
            destination = np.full(expected_shape, source.nodata or 0, dtype=data.dtype)
            reproject(
                source.read(1),
                destination,
                src_transform=source.transform,
                src_crs=source.crs,
                dst_transform=profile["transform"],
                dst_crs=profile["crs"],
                resampling=Resampling.bilinear if source.dtypes[0] != "uint8" else Resampling.nearest,
            )
            data = destination
        return data


def write_float(name: str, values: np.ndarray, profile: dict[str, object]) -> Path:
    path = OUT / name
    out_profile = profile.copy()
    out_profile.pop("driver", None)
    out_profile.update(dtype="float32", nodata=np.nan, compress="deflate", tiled=True)
    with rasterio.open(path, "w", **out_profile) as dataset:
        dataset.write(values.astype("float32"), 1)
    return path


def write_mask(name: str, mask: np.ndarray, inside: np.ndarray, profile: dict[str, object]) -> Path:
    path = OUT / name
    out_profile = profile.copy()
    out_profile.pop("driver", None)
    out_profile.update(dtype="uint8", nodata=255, compress="deflate", tiled=True)
    with rasterio.open(path, "w", **out_profile) as dataset:
        dataset.write(np.where(inside, mask, 255).astype("uint8"), 1)
    return path


def process_s2() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    profile, inside = reference_profile()
    outputs: dict[str, Path] = {}
    scl_counts: dict[str, dict[str, int]] = {}
    water: dict[str, np.ndarray] = {}

    for role, label in ((PRE_ROLE, "before"), (POST_ROLE, "after")):
        green = read_band(role, "B03_10m", profile).astype("float32") / 10000.0
        nir = read_band(role, "B08_10m", profile).astype("float32") / 10000.0
        scl = read_band(role, "SCL_20m", profile)
        valid_classes = SCL_VALID_CLASSES
        valid_scl = np.isin(scl, list(valid_classes))
        denominator = green + nir
        valid = (denominator > 1e-6) & valid_scl & (green >= 0) & (nir >= 0)
        ndwi = np.full(green.shape, np.nan, dtype="float32")
        numerator = green - nir
        ratio = np.divide(
            numerator,
            denominator,
            out=np.full(numerator.shape, np.nan, dtype="float32"),
            where=valid,
        )
        ndwi[valid] = ratio[valid]
        water[label] = np.zeros(ndwi.shape, dtype=bool)
        water[label][valid & (ndwi > NDWI_THRESHOLD)] = True
        outputs[f"s2_ndwi_{label}_10m.tif"] = write_float(f"s2_ndwi_{label}_10m.tif", ndwi, profile)
        outputs[f"s2_surface_water_{label}_candidate_10m.tif"] = write_mask(
            f"s2_surface_water_{label}_candidate_10m.tif", water[label], inside, profile
        )
        values, counts = np.unique(scl[inside], return_counts=True)
        scl_counts[label] = {str(int(value)): int(count) for value, count in zip(values, counts)}

    common_valid = np.isin(read_band(PRE_ROLE, "SCL_20m", profile), list(SCL_VALID_CLASSES)) & np.isin(
        read_band(POST_ROLE, "SCL_20m", profile), list(SCL_VALID_CLASSES)
    )
    products = {
        "s2_new_surface_water_candidate_10m.tif": water["after"] & ~water["before"] & common_valid,
        "s2_lost_surface_water_candidate_10m.tif": water["before"] & ~water["after"] & common_valid,
        "s2_persistent_surface_water_candidate_10m.tif": water["before"] & water["after"] & common_valid,
    }
    for name, mask in products.items():
        outputs[name] = write_mask(name, mask, inside, profile)

    counts = {
        "inside_pixels_10m": int(inside.sum()),
        "common_valid_pixels_10m": int((inside & common_valid).sum()),
        "before_valid_pixels_10m": int(
            (inside & np.isin(read_band(PRE_ROLE, "SCL_20m", profile), list(SCL_VALID_CLASSES))).sum()
        ),
        "after_valid_pixels_10m": int(
            (inside & np.isin(read_band(POST_ROLE, "SCL_20m", profile), list(SCL_VALID_CLASSES))).sum()
        ),
        "before_water_pixels_10m": int((water["before"] & inside).sum()),
        "after_water_pixels_10m": int((water["after"] & inside).sum()),
        "new_surface_water_pixels_10m": int((products["s2_new_surface_water_candidate_10m.tif"] & inside).sum()),
        "lost_surface_water_pixels_10m": int((products["s2_lost_surface_water_candidate_10m.tif"] & inside).sum()),
        "persistent_surface_water_pixels_10m": int((products["s2_persistent_surface_water_candidate_10m.tif"] & inside).sum()),
    }
    result = {
        "dataset_id": "secocha_2023_sentinel2_optical_change_candidate",
        "event_id": "secocha_2023_historical_hazard_event",
        "event_date": "2023-02-05",
        "boundary_id": "secocha_reference_extent",
        "claim_level": "validation_candidate",
        "enters_pim_score": False,
        "dates": DATES,
        "method": "NDWI=(B03-B08)/(B03+B08), water candidate NDWI > 0.15; valid SCL classes 4-7; 20 m SCL mask applied to 10 m optical bands; clipped to active reference window",
        "scl_class_counts_inside": scl_counts,
        **counts,
        "limitations": [
            "Optical Sentinel-2 cannot see through clouds, cloud shadow or canopy",
            "The after image is three days post-event and is not peak-flow extent",
            "A simple NDWI threshold does not remove terrain shadow or subpixel sediment effects",
            "Debris-flow deposits may alter bare soil/sediment without producing a positive NDWI water class",
            "Validation candidate only, not an official observed event footprint",
        ],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "input_manifest": {
            "path": str(PIXEL_MANIFEST.relative_to(ROOT)),
            "sha256": sha256(PIXEL_MANIFEST),
        },
        "outputs": {
            name: {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for name, path in outputs.items()
        },
    }
    (OUT / "s2_optical_change_qa.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    print(json.dumps(process_s2(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
