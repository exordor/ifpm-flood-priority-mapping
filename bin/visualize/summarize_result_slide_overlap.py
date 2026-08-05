#!/usr/bin/env python3
"""Summarize map-context overlap metrics used on the result slides.

The metrics are descriptive screening summaries.  They do not validate the
priority model or estimate flood probability.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import mapping


ROOT = Path(__file__).resolve().parents[2]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lineage(paths: list[Path]) -> dict[str, str]:
    return {
        "input_sources": ";".join(rel(path) for path in paths),
        "input_sha256": ";".join(sha256(path) for path in paths),
    }


def score_class(value: float, nodata: float | None) -> str:
    if np.isnan(value) or (nodata is not None and value == nodata):
        return "NoData"
    if value < 0.2:
        return "very_low"
    if value < 0.4:
        return "low"
    if value < 0.6:
        return "moderate"
    if value < 0.8:
        return "high"
    return "very_high"


def peru_rows() -> list[dict[str, str | int | float]]:
    raster_path = ROOT / (
        "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/scenarios/"
        "priority_mentor_peru_direct_pim.tif"
    )
    point_path = ROOT / (
        "data/raw/ingemmet_catastro_minero_peru_pilot/"
        "peru_hybas_l7_6070641200_pequena_mineria.gpkg"
    )
    boundary_path = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
    inputs = [raster_path, point_path, boundary_path]
    missing = [path for path in inputs if not path.exists()]
    if missing:
        raise FileNotFoundError("missing Peru overlap input(s): " + ", ".join(map(str, missing)))
    source_lineage = lineage(inputs)

    points = gpd.read_file(point_path).drop_duplicates(
        subset=["longitud", "latitud"]
    )
    boundary = gpd.read_file(boundary_path)

    with rasterio.open(raster_path) as src:
        points = points.to_crs(src.crs)
        boundary = boundary.to_crs(src.crs)
        inside = points.geometry.within(boundary.geometry.union_all())
        values = [float(item[0]) for item in src.sample([(g.x, g.y) for g in points.geometry])]
        classes = [score_class(value, src.nodata) for value in values]

    inside_classes = [klass for klass, is_inside in zip(classes, inside) if is_inside]
    return [
        {
            **source_lineage,
            "country": "Peru",
            "metric": "unique_ingemmet_locations_inside_boundary",
            "value": int(inside.sum()),
            "unit": "locations",
            "claim_level": "model_input_context",
            "note": "Unique official INGEMMET reference locations inside the working boundary.",
        },
        {
            **source_lineage,
            "country": "Peru",
            "metric": "inside_locations_in_high_class",
            "value": inside_classes.count("high"),
            "unit": "locations",
            "claim_level": "model_input_context",
            "note": "Point-cell sampling of the provisional priority raster; not validation.",
        },
        {
            **source_lineage,
            "country": "Peru",
            "metric": "inside_locations_in_moderate_class",
            "value": inside_classes.count("moderate"),
            "unit": "locations",
            "claim_level": "model_input_context",
            "note": "Point-cell sampling of the provisional priority raster; not validation.",
        },
    ]


def zimbabwe_rows() -> list[dict[str, str | int | float]]:
    raster_path = ROOT / (
        "outputs/boundary_v1/rainfall_exposure_v0_4/scenarios/"
        "priority_mentor_zimbabwe_direct_pim.tif"
    )
    mining_path = ROOT / (
        "data/raw/global_mining_polygons_v2_zimbabwe/"
        "global_mining_polygons_v2.gpkg"
    )
    boundary_path = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
    inputs = [raster_path, mining_path, boundary_path]
    missing = [path for path in inputs if not path.exists()]
    if missing:
        raise FileNotFoundError("missing Zimbabwe overlap input(s): " + ", ".join(map(str, missing)))
    source_lineage = lineage(inputs)

    boundary = gpd.read_file(boundary_path, layer="v1_working_boundary")
    mining = gpd.read_file(mining_path)
    mining = mining[mining["ISO3_CODE"].eq("ZWE")]

    with rasterio.open(raster_path) as src:
        boundary = boundary.to_crs(src.crs)
        mining = mining.to_crs(src.crs)
        study_area = boundary.geometry.union_all()
        mining = mining[mining.intersects(study_area)].copy()
        mining["geometry"] = mining.geometry.intersection(study_area)
        mining = mining[~mining.is_empty]

        priority = src.read(1, masked=True)
        footprint_mask = geometry_mask(
            [mapping(geometry) for geometry in mining.geometry],
            out_shape=priority.shape,
            transform=src.transform,
            invert=True,
        )
        values = priority.data[footprint_mask & ~priority.mask]

    moderate = float(np.mean((values >= 0.4) & (values < 0.6)))
    high = float(np.mean((values >= 0.6) & (values < 0.8)))
    very_high = float(np.mean(values >= 0.8))
    return [
        {
            **source_lineage,
            "country": "Zimbabwe",
            "metric": "mapped_mining_footprints_in_boundary",
            "value": len(mining),
            "unit": "polygons",
            "claim_level": "independent_context",
            "note": "Non-exhaustive satellite-interpreted mining land-use footprints.",
        },
        {
            **source_lineage,
            "country": "Zimbabwe",
            "metric": "mining_footprint_cells_moderate_to_very_high_fraction",
            "value": moderate + high + very_high,
            "unit": "fraction",
            "claim_level": "diagnostic_only",
            "note": "Share of scored footprint cells; descriptive overlap, not validation.",
        },
        {
            **source_lineage,
            "country": "Zimbabwe",
            "metric": "mining_footprint_cells_high_fraction",
            "value": high,
            "unit": "fraction",
            "claim_level": "diagnostic_only",
            "note": "Share of scored footprint cells in the 0.6-0.8 class.",
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "outputs/slide_ready_figures/result_slide_metrics/overlap_summary.csv",
    )
    args = parser.parse_args()

    rows = peru_rows() + zimbabwe_rows()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "country",
                "metric",
                "value",
                "unit",
                "claim_level",
                "note",
                "input_sources",
                "input_sha256",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(args.output)


if __name__ == "__main__":
    main()
