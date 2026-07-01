#!/usr/bin/env python3
"""Create V1 terrain-only standardized diagnostic rasters."""

from __future__ import annotations

import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.ticker import FuncFormatter
from rasterio.features import geometry_mask


ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "srtm_1arcsec_zimbabwe_prototype"
PREPROCESS_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_preprocessing"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/terrain_standardization"
GRID_GATE = ROOT / "bin/package/check_v1_raster_grid.py"
V1_GPKG = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
DEM = PREPROCESS_DIR / "v1_dem_utm35s_30m.tif"
SLOPE = PREPROCESS_DIR / "v1_slope_degrees_utm35s_30m.tif"
NODATA = -9999.0
CLIP_LOW = 2.0
CLIP_HIGH = 98.0

OUTPUTS = [
    {
        "path": OUT_DIR / "v1_elevation_lowland_context_0_1.tif",
        "source": DEM,
        "indicator": "elevation_lowland_context",
        "direction": "lower elevation -> higher diagnostic value",
        "invert": True,
        "recommended": "no",
    },
    {
        "path": OUT_DIR / "v1_slope_low_slope_susceptibility_0_1.tif",
        "source": SLOPE,
        "indicator": "slope_low_slope_susceptibility",
        "direction": "lower slope -> higher diagnostic value",
        "invert": True,
        "recommended": "yes_for_mentor_review",
    },
    {
        "path": OUT_DIR / "v1_slope_high_runoff_pressure_0_1.tif",
        "source": SLOPE,
        "indicator": "slope_high_runoff_pressure",
        "direction": "higher slope -> higher diagnostic value",
        "invert": False,
        "recommended": "alternative_only",
    },
]

DIAGNOSTICS = OUT_DIR / "v1_terrain_standardization_diagnostics.csv"
GRID_CHECK = OUT_DIR / "v1_terrain_standardization_grid_check.csv"
QA_PNG = OUT_DIR / "v1_terrain_standardization_qa.png"
HANDOFF = OUT_DIR / "v1_terrain_standardization_handoff.md"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def run_grid_gate(paths: list[Path], output: Path) -> None:
    cmd = [sys.executable, str(GRID_GATE), "--rasters", *map(str, paths), "--output", str(output)]
    subprocess.run(cmd, cwd=ROOT, check=True)


def load_boundary(crs) -> object:
    boundary = gpd.read_file(V1_GPKG, layer="v1_working_boundary")
    if len(boundary) != 1 or boundary.geometry.iloc[0].is_empty:
        raise ValueError("Expected one non-empty V1 working boundary")
    return boundary.to_crs(crs).geometry.iloc[0]


def valid_values(data: np.ndarray, nodata: float) -> np.ndarray:
    mask = np.isfinite(data) & (data != nodata)
    values = data[mask]
    if values.size == 0:
        raise ValueError("No valid input cells for standardization")
    return values


def standardize(data: np.ndarray, nodata: float, invert: bool) -> tuple[np.ndarray, float, float]:
    values = valid_values(data, nodata)
    low = float(np.nanpercentile(values, CLIP_LOW))
    high = float(np.nanpercentile(values, CLIP_HIGH))
    if not high > low:
        raise ValueError(f"Invalid percentile bounds: low={low}, high={high}")

    output = np.full(data.shape, nodata, dtype="float32")
    valid = np.isfinite(data) & (data != nodata)
    scaled = (np.clip(data[valid], low, high) - low) / (high - low)
    if invert:
        scaled = 1.0 - scaled
    output[valid] = scaled.astype("float32")
    return output, low, high


def write_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    output_profile = profile.copy()
    output_profile.update(
        {
            "driver": "GTiff",
            "dtype": "float32",
            "count": 1,
            "nodata": NODATA,
            "compress": "deflate",
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **output_profile) as dst:
        dst.write(data.astype("float32"), 1)


def raster_stats(path: Path, geometry) -> dict[str, object]:
    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        inside = geometry_mask([geometry], out_shape=data.shape, transform=src.transform, invert=True)
        valid = inside & np.isfinite(data) & (data != src.nodata)
        values = data[valid]
        if values.size == 0:
            raise ValueError(f"No valid V1 cells in {path.name}")
        return {
            "output_min": round(float(np.nanmin(values)), 6),
            "output_max": round(float(np.nanmax(values)), 6),
            "output_mean": round(float(np.nanmean(values)), 6),
            "valid_cell_fraction": round(float(valid.sum() / inside.sum()), 6),
        }


def process_one(spec: dict[str, object]) -> dict[str, object]:
    with rasterio.open(spec["source"]) as src:
        source_data = src.read(1).astype("float32")
        input_values = valid_values(source_data, src.nodata)
        standardized, clip_low, clip_high = standardize(source_data, src.nodata, bool(spec["invert"]))
        write_raster(spec["path"], standardized, src.profile)
        stats = raster_stats(spec["path"], load_boundary(src.crs))

    return {
        "output": rel(spec["path"]),
        "source": rel(spec["source"]),
        "indicator": spec["indicator"],
        "method": f"percentile_clip_minmax_{CLIP_LOW:g}_{CLIP_HIGH:g}",
        "direction": spec["direction"],
        "clip_low": round(clip_low, 6),
        "clip_high": round(clip_high, 6),
        "input_min": round(float(np.nanmin(input_values)), 6),
        "input_max": round(float(np.nanmax(input_values)), 6),
        "input_mean": round(float(np.nanmean(input_values)), 6),
        **stats,
        "recommended_for_mentor_review": spec["recommended"],
        "eligible_for_overlay": "no_pending_criteria_decision",
        "notes": "terrain-only diagnostic; not flood risk; not final boundary evidence",
    }


def write_diagnostics(rows: list[dict[str, object]]) -> None:
    with DIAGNOSTICS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def extent(bounds) -> list[float]:
    return [bounds.left, bounds.right, bounds.bottom, bounds.top]


def km_formatter(value, _pos) -> str:
    return f"{value / 1000:.0f}"


def plot_qa(rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, len(OUTPUTS), figsize=(15, 5.2), constrained_layout=True)
    for ax, spec, row in zip(axes, OUTPUTS, rows, strict=True):
        with rasterio.open(spec["path"]) as src:
            data = src.read(1).astype("float32")
            shown = np.where(data == src.nodata, np.nan, data)
            img = ax.imshow(shown, cmap="viridis", extent=extent(src.bounds), origin="upper", vmin=0, vmax=1)
        ax.set_title(str(row["indicator"]).replace("_", " "))
        ax.set_xlabel("Easting (km, EPSG:32735)")
        ax.set_ylabel("Northing (km, EPSG:32735)")
        ax.xaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.yaxis.set_major_formatter(FuncFormatter(km_formatter))
        ax.set_aspect("equal", adjustable="box")
        fig.colorbar(img, ax=ax, shrink=0.76, label="0-1 diagnostic value")
    fig.savefig(QA_PNG, dpi=220)
    plt.close(fig)


def write_handoff(rows: list[dict[str, object]]) -> None:
    HANDOFF.write_text(
        "\n".join(
            [
                "# V1 Terrain Standardization Handoff",
                "",
                f"Updated: {date.today().isoformat()}",
                "",
                "Status: terrain-only 0-1 diagnostic candidates produced after the V1 raster grid gate.",
                "",
                "Method: 2nd-98th percentile clipping followed by min-max scaling inside the V1 raster mask.",
                "",
                "Outputs:",
                *[f"- `{row['output']}` ({row['indicator']})" for row in rows],
                "",
                f"Diagnostics: `{rel(DIAGNOSTICS)}`",
                f"Output grid check: `{rel(GRID_CHECK)}`",
                f"QA map: `{rel(QA_PNG)}`",
                "",
                "Recommended for mentor review: `slope_low_slope_susceptibility`.",
                "Alternative retained: `slope_high_runoff_pressure` for runoff or erosion-pressure framing.",
                "Elevation is kept as lowland context, not as a default scoring criterion.",
                "",
                "Scope limits: no CHIRPS, no AHP weights, no overlay, no flood-risk map, and no final thesis boundary claim.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_grid_gate([DEM, SLOPE], PREPROCESS_DIR / "v1_raster_grid_check.csv")
    rows = [process_one(spec) for spec in OUTPUTS]
    write_diagnostics(rows)
    output_paths = [Path(spec["path"]) for spec in OUTPUTS]
    run_grid_gate(output_paths, GRID_CHECK)
    plot_qa(rows)
    write_handoff(rows)
    print(f"wrote {rel(DIAGNOSTICS)}")
    print(f"wrote {rel(GRID_CHECK)}")
    print(f"wrote {rel(QA_PNG)}")
    print(f"wrote {rel(HANDOFF)}")


if __name__ == "__main__":
    main()
