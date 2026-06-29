#!/usr/bin/env python3
"""Check V1 terrain rasters against the fixed reference DEM grid."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "srtm_1arcsec_zimbabwe_prototype"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
REFERENCE_DEM = OUT_DIR / "v1_dem_utm35s_30m.tif"
DEFAULT_RASTERS = [
    REFERENCE_DEM,
    OUT_DIR / "v1_slope_degrees_utm35s_30m.tif",
]
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
CHECK_CSV = OUT_DIR / "v1_raster_grid_check.csv"
EXPECTED_NODATA = -9999.0
EXPECTED_DTYPE = "float32"
EXPECTED_COUNT = 1
MIN_VALID_FRACTION = 0.98


FIELDNAMES = [
    "path",
    "role",
    "crs",
    "transform",
    "width",
    "height",
    "resolution_x",
    "resolution_y",
    "band_count",
    "dtype",
    "nodata",
    "min",
    "max",
    "mean",
    "valid_cell_fraction",
    "grid_compatible",
    "issues",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check V1 terrain raster grid compatibility before standardization or overlay."
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=REFERENCE_DEM,
        help="Reference DEM. Defaults to the V1 DEM fixed in the project rule.",
    )
    parser.add_argument(
        "--rasters",
        type=Path,
        nargs="+",
        default=DEFAULT_RASTERS,
        help="Candidate terrain rasters to check. Defaults to V1 DEM and V1 slope.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=CHECK_CSV,
        help="CSV manifest output path.",
    )
    parser.add_argument(
        "--boundary",
        type=Path,
        default=V1_GPKG,
        help="Boundary GeoPackage for valid-cell-fraction masking. Defaults to the V1 Zimbabwe "
        "boundary. Pass a country-specific boundary (e.g. the Peru PE1 boundary) when checking "
        "non-Zimbabwe rasters, so the gate masks against the correct AOI.",
    )
    parser.add_argument(
        "--boundary-layer",
        type=str,
        default="v1_working_boundary",
        help="Layer name in the boundary GeoPackage.",
    )
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def transform_text(transform) -> str:
    return ",".join(f"{value:.12g}" for value in transform.to_gdal())


def load_boundary_geometry(crs, boundary_path: Path, boundary_layer: str) -> object:
    boundary = gpd.read_file(boundary_path, layer=boundary_layer)
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError(f"Expected one non-empty boundary feature in {boundary_layer}")
    return boundary.to_crs(crs).geometry.iloc[0]


# Back-compat alias used elsewhere in the file.
def load_v1_geometry(crs, boundary_path: Path | None = None, boundary_layer: str = "v1_working_boundary") -> object:
    if boundary_path is None:
        boundary_path = V1_GPKG
    return load_boundary_geometry(crs, boundary_path, boundary_layer)


def valid_stats(src, geometry) -> tuple[float, float | str, float | str, float | str]:
    data = src.read(1).astype("float32")
    inside = geometry_mask([geometry], out_shape=data.shape, transform=src.transform, invert=True)
    inside_count = int(inside.sum())
    if inside_count == 0:
        return 0.0, "", "", ""

    valid = inside & np.isfinite(data)
    if src.nodata is not None:
        valid &= data != src.nodata
    values = data[valid]
    valid_fraction = float(valid.sum() / inside_count)
    if values.size == 0:
        return valid_fraction, "", "", ""
    return (
        valid_fraction,
        round(float(np.nanmin(values)), 6),
        round(float(np.nanmax(values)), 6),
        round(float(np.nanmean(values)), 6),
    )


def reference_profile(reference: Path) -> dict[str, object]:
    if not reference.exists():
        raise FileNotFoundError(f"Reference raster not found: {reference}")
    with rasterio.open(reference) as ref:
        return {
            "crs": ref.crs,
            "transform": ref.transform,
            "width": ref.width,
            "height": ref.height,
            "bounds": ref.bounds,
            "res": ref.res,
            "count": ref.count,
            "dtype": ref.dtypes[0],
            "nodata": ref.nodata,
        }


def compare_raster(path: Path, reference: Path, ref_profile: dict[str, object],
                   boundary_path: Path | None = None, boundary_layer: str = "v1_working_boundary") -> dict[str, object]:
    role = "reference" if path.resolve() == reference.resolve() else "candidate"
    row: dict[str, object] = {
        "path": rel(path),
        "role": role,
        "crs": "",
        "transform": "",
        "width": "",
        "height": "",
        "resolution_x": "",
        "resolution_y": "",
        "band_count": "",
        "dtype": "",
        "nodata": "",
        "min": "",
        "max": "",
        "mean": "",
        "valid_cell_fraction": "",
        "grid_compatible": "false",
        "issues": "",
    }
    issues: list[str] = []

    if not path.exists():
        row["issues"] = "file_missing"
        return row

    try:
        with rasterio.open(path) as src:
            row.update(
                {
                    "crs": str(src.crs),
                    "transform": transform_text(src.transform),
                    "width": src.width,
                    "height": src.height,
                    "resolution_x": src.res[0],
                    "resolution_y": src.res[1],
                    "band_count": src.count,
                    "dtype": src.dtypes[0],
                    "nodata": src.nodata,
                }
            )

            if src.crs != ref_profile["crs"]:
                issues.append(f"crs_mismatch expected={ref_profile['crs']} got={src.crs}")
            if src.transform != ref_profile["transform"]:
                issues.append("transform_mismatch")
            if src.width != ref_profile["width"]:
                issues.append(f"width_mismatch expected={ref_profile['width']} got={src.width}")
            if src.height != ref_profile["height"]:
                issues.append(f"height_mismatch expected={ref_profile['height']} got={src.height}")
            if src.bounds != ref_profile["bounds"]:
                issues.append("bounds_mismatch")
            if src.res != ref_profile["res"]:
                issues.append(f"resolution_mismatch expected={ref_profile['res']} got={src.res}")
            if src.count != EXPECTED_COUNT:
                issues.append(f"band_count_mismatch expected={EXPECTED_COUNT} got={src.count}")
            if src.dtypes[0] != EXPECTED_DTYPE:
                issues.append(f"dtype_mismatch expected={EXPECTED_DTYPE} got={src.dtypes[0]}")
            if src.nodata != EXPECTED_NODATA:
                issues.append(f"nodata_mismatch expected={EXPECTED_NODATA} got={src.nodata}")

            geometry = load_v1_geometry(src.crs, boundary_path, boundary_layer)
            valid_fraction, raster_min, raster_max, raster_mean = valid_stats(src, geometry)
            row.update(
                {
                    "min": raster_min,
                    "max": raster_max,
                    "mean": raster_mean,
                    "valid_cell_fraction": round(valid_fraction, 6),
                }
            )
            if valid_fraction < MIN_VALID_FRACTION:
                issues.append(
                    f"valid_cell_fraction_below_threshold expected>={MIN_VALID_FRACTION} got={valid_fraction:.6f}"
                )
            if raster_min == "":
                issues.append("no_valid_cells_inside_v1")
    except Exception as exc:  # noqa: BLE001 - preserve failure evidence in the manifest.
        issues.append(f"open_or_check_error {type(exc).__name__}: {exc}")

    row["issues"] = "; ".join(issues)
    row["grid_compatible"] = "false" if issues else "true"
    return row


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    reference = resolve(args.reference)
    rasters = [resolve(path) for path in args.rasters]
    output = resolve(args.output)

    ref_profile = reference_profile(reference)
    rows = [compare_raster(path, reference, ref_profile, args.boundary, args.boundary_layer) for path in rasters]
    write_manifest(output, rows)

    failed = [row for row in rows if row["grid_compatible"] != "true"]
    print(f"wrote {rel(output)}")
    if failed:
        for row in failed:
            print(f"grid check failed: {row['path']} -> {row['issues']}")
        return 1
    print("all checked V1 terrain rasters are grid-compatible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
