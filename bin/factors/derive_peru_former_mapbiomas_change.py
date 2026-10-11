#!/usr/bin/env python3
"""Align MapBiomas Peru annual classes and derive bounded 2015-2024 change evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject


ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "data/raw/mapbiomas_peru_collection3_peru_former"
REFERENCE = (
    ROOT
    / "outputs/peru_former_pim_chain/terrain_preprocessing"
    / "peru_former_dem_utm18s_30m.tif"
)
OUTPUT_DIR = ROOT / "outputs/peru_former_mapbiomas_collection3_change"

INPUTS = {
    2014: DATASET_DIR / "peru_collection3_integration_v1-classification_2014.tif",
    2015: DATASET_DIR / "peru_collection3_integration_v1-classification_2015.tif",
    2016: DATASET_DIR / "peru_collection3_integration_v1-classification_2016.tif",
    2022: DATASET_DIR / "peru_collection3_integration_v1-classification_2022.tif",
    2023: DATASET_DIR / "peru_collection3_integration_v1-classification_2023.tif",
    2024: DATASET_DIR / "peru_collection3_integration_v1-classification_2024.tif",
}
EARLY_WINDOW = (2014, 2015, 2016)
LATE_WINDOW = (2022, 2023, 2024)

# Collection 3 classes that visibly carry vegetation cover. This includes
# natural vegetation, planted forest, pasture, and agricultural vegetation.
VEGETATED_CLASSES = frozenset({3, 4, 5, 6, 9, 11, 12, 13, 15, 18, 21, 35, 40, 66, 70, 72})
NONVEGETATED_LAND_CLASSES = frozenset({23, 24, 25, 29, 32, 61, 68})
AGRICULTURAL_CLASSES = frozenset({9, 15, 18, 21, 35, 40, 72})
ANTHROPOGENIC_BARE_CLASSES = frozenset({25})
BUILT_UP_CLASS = 24
MINING_CLASS = 30


def _isin(values: np.ndarray, classes: frozenset[int]) -> np.ndarray:
    return np.isin(values, tuple(sorted(classes)))


def derive_change_masks(old: np.ndarray, new: np.ndarray) -> dict[str, np.ndarray]:
    """Return binary state/change masks while keeping Mining outside PIM evidence."""
    if old.shape != new.shape:
        raise ValueError("old and new MapBiomas arrays must have the same shape")

    observed = (old != 0) & (new != 0)
    excludes_mining = (old != MINING_CLASS) & (new != MINING_CLASS)
    eligible = observed & excludes_mining

    old_vegetated = _isin(old, VEGETATED_CLASSES)
    new_nonvegetated = _isin(new, NONVEGETATED_LAND_CLASSES)
    vegetation_loss = eligible & old_vegetated & new_nonvegetated

    anthropogenic_bare_state = eligible & _isin(new, ANTHROPOGENIC_BARE_CLASSES)
    built_up_expansion = eligible & (old != BUILT_UP_CLASS) & (new == BUILT_UP_CLASS)
    agricultural_expansion = eligible & ~_isin(old, AGRICULTURAL_CLASSES) & _isin(
        new, AGRICULTURAL_CLASSES
    )

    bare_soil_vegetation_loss = anthropogenic_bare_state | vegetation_loss

    return {
        "anthropogenic_bare_state": anthropogenic_bare_state.astype("uint8"),
        "vegetation_loss": vegetation_loss.astype("uint8"),
        "bare_soil_vegetation_loss": bare_soil_vegetation_loss.astype("uint8"),
        "built_up_expansion": built_up_expansion.astype("uint8"),
        "agricultural_expansion": agricultural_expansion.astype("uint8"),
    }


def stable_classification(annual: np.ndarray) -> np.ndarray:
    """Reduce three annual classifications to a pixel majority, using the middle year on ties."""
    if annual.ndim != 3 or annual.shape[0] != 3:
        raise ValueError("stable classification requires exactly three annual rasters")
    first, middle, last = annual
    return np.where((first == middle) | (first == last), first, middle).astype("uint8")


def align_classification(path: Path, reference: rasterio.io.DatasetReader) -> np.ndarray:
    aligned = np.zeros((reference.height, reference.width), dtype="uint8")
    with rasterio.open(path) as source:
        reproject(
            source=rasterio.band(source, 1),
            destination=aligned,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=reference.transform,
            dst_crs=reference.crs,
            src_nodata=0,
            dst_nodata=0,
            resampling=Resampling.nearest,
        )
    return aligned


def write_classification(path: Path, values: np.ndarray, reference_profile: dict) -> None:
    profile = reference_profile.copy()
    profile.update(dtype="uint8", nodata=0, count=1, compress="deflate", predictor=2)
    with rasterio.open(path, "w", **profile) as destination:
        destination.write(values, 1)


def write_binary(path: Path, values: np.ndarray, valid: np.ndarray, reference_profile: dict) -> None:
    output = np.full(values.shape, -9999.0, dtype="float32")
    output[valid] = values[valid].astype("float32")
    profile = reference_profile.copy()
    profile.update(dtype="float32", nodata=-9999.0, count=1, compress="deflate", predictor=2)
    with rasterio.open(path, "w", **profile) as destination:
        destination.write(output, 1)


def main() -> None:
    for source in INPUTS.values():
        if not source.exists():
            raise FileNotFoundError(source)
    if not REFERENCE.exists():
        raise FileNotFoundError(REFERENCE)

    aligned_dir = OUTPUT_DIR / "aligned"
    change_dir = OUTPUT_DIR / "change_2014_2016_to_2022_2024"
    aligned_dir.mkdir(parents=True, exist_ok=True)
    change_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(REFERENCE) as reference:
        reference_values = reference.read(1)
        reference_valid = reference_values != reference.nodata
        aligned = {
            year: align_classification(path, reference) for year, path in INPUTS.items()
        }
        profile = reference.profile.copy()

    stable_early = stable_classification(np.stack([aligned[year] for year in EARLY_WINDOW]))
    stable_late = stable_classification(np.stack([aligned[year] for year in LATE_WINDOW]))
    source_valid = reference_valid & (stable_early != 0) & (stable_late != 0)
    for year, values in aligned.items():
        write_classification(
            aligned_dir / f"mapbiomas_peru_collection3_{year}_reference_grid.tif",
            np.where(reference_valid, values, 0).astype("uint8"),
            profile,
        )

    write_classification(
        aligned_dir / "mapbiomas_peru_collection3_stable_2014_2016_reference_grid.tif",
        np.where(reference_valid, stable_early, 0).astype("uint8"),
        profile,
    )
    write_classification(
        aligned_dir / "mapbiomas_peru_collection3_stable_2022_2024_reference_grid.tif",
        np.where(reference_valid, stable_late, 0).astype("uint8"),
        profile,
    )

    masks = derive_change_masks(stable_early, stable_late)
    for name, values in masks.items():
        write_binary(
            change_dir / f"{name}_stable_windows_0_1.tif", values, source_valid, profile
        )

    pixel_area_km2 = abs(profile["transform"].a * profile["transform"].e) / 1_000_000.0
    metrics = {
        name: {
            "pixels": int(values[source_valid].sum()),
            "area_km2": float(values[source_valid].sum() * pixel_area_km2),
        }
        for name, values in masks.items()
    }

    transitions = Counter(
        zip(stable_early[source_valid].tolist(), stable_late[source_valid].tolist())
    )
    with (change_dir / "transition_counts_stable_windows.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["class_2015", "class_2024", "pixels", "area_km2"])
        for (old_class, new_class), count in sorted(transitions.items()):
            writer.writerow([old_class, new_class, count, count * pixel_area_km2])

    manifest = {
        "dataset_id": "mapbiomas_peru_collection3_peru_former",
        "status": "sensitivity_scenario",
        "years": sorted(INPUTS),
        "stable_windows": [list(EARLY_WINDOW), list(LATE_WINDOW)],
        "reference_grid": str(REFERENCE.relative_to(ROOT)),
        "valid_pixels": int(source_valid.sum()),
        "coverage_fraction_of_reference": float(source_valid.sum() / reference_valid.sum()),
        "metrics": metrics,
        "class_contract": {
            "vegetated": sorted(VEGETATED_CLASSES),
            "nonvegetated_land": sorted(NONVEGETATED_LAND_CLASSES),
            "agricultural": sorted(AGRICULTURAL_CLASSES),
            "anthropogenic_bare": sorted(ANTHROPOGENIC_BARE_CLASSES),
            "built_up": BUILT_UP_CLASS,
            "mining": MINING_CLASS,
        },
        "mining_role": "excluded from every BV and BE change mask; external overlay only",
        "interpretation": {
            "bv": "current anthropogenic bare state or observed vegetated-to-nonvegetated transition",
            "be": "separate observed built-up and agricultural footprint expansion; road history remains pending",
        },
        "limitations": [
            "Three-year pixel majorities reduce but do not eliminate classification uncertainty.",
            "The middle year is retained when all three annual classes disagree.",
            "Road expansion is not represented by these land-cover rasters.",
        ],
    }
    (change_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
