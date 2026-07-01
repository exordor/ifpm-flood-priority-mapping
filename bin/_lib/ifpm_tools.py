"""Shared helpers for the IFPM bin/ pipeline scripts.

This module absorbs logic that was duplicated across dozens of standalone scripts:
project-root location, boundary loading, raster I/O, statistics, percentile-clip
standardization, and the V1 grid-gate invocation. Heavy GIS dependencies (rasterio,
numpy, geopandas) are loaded lazily so that `import ifpm_tools` works even in a
stripped environment, and the error message names the missing package.

Design notes:
- Functions are conservative copies of the most common implementation already in the
  codebase. No behavioural changes are introduced; the goal is to have ONE definition
  instead of 10+ near-duplicates.
- Two `stats` signatures coexist because scripts used two conventions: one takes a
  boolean `mask` (inside-boundary indicator) and reports valid_fraction relative to
  it; the other just reports the array's own finite values. Both are provided.
- `write_raster` accepts either a full rasterio profile dict or (transform, crs) so
  it can serve both the "extend an existing profile" and the "build from scratch"
  scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Project root: bin/_lib/ifpm_tools.py -> parents[2] = workspace root.
ROOT: Path = Path(__file__).resolve().parents[2]

# Canonical NoData value used across all V1/PE1 rasters.
NODATA: float = -9999.0


# ---------------------------------------------------------------------------
# Lazy dependency loaders
# ---------------------------------------------------------------------------

def _np():
    """Lazy numpy import with a clear error."""
    try:
        import numpy as np
        return np
    except ImportError as exc:
        raise ImportError(
            "numpy is required for this operation. Install it in .venv."
        ) from exc


def _rasterio():
    """Lazy rasterio import with a clear error."""
    try:
        import rasterio
        return rasterio
    except ImportError as exc:
        raise ImportError(
            "rasterio is required for raster I/O. Install it in .venv."
        ) from exc


def _gpd():
    """Lazy geopandas import with a clear error."""
    try:
        import geopandas as gpd
        return gpd
    except ImportError as exc:
        raise ImportError(
            "geopandas is required for boundary loading. Install it in .venv."
        ) from exc


# ---------------------------------------------------------------------------
# Boundary loading
# ---------------------------------------------------------------------------

def load_boundary(
    gpkg_path: Path | str,
    layer: str,
    dst_crs: str | None = None,
) -> Any:
    """Load a single-feature boundary geometry from a GeoPackage.

    Mirrors the `load_v1()` / `load_pe1()` / `load_boundary()` helpers that were
    duplicated across ~16 scripts. Asserts exactly one feature (a boundary should
    be a single dissolved polygon) and returns its geometry.

    Parameters
    ----------
    gpkg_path : path to the .gpkg file.
    layer     : layer name inside the GeoPackage.
    dst_crs   : if given, reproject to this CRS (e.g. the UTM zone of the DEM).
    """
    gpd = _gpd()
    gdf = gpd.read_file(str(gpkg_path), layer=layer)
    if len(gdf) != 1:
        raise ValueError(
            f"Expected exactly one feature in {gpkg_path}::{layer}, got {len(gdf)}"
        )
    if dst_crs is not None:
        gdf = gdf.to_crs(dst_crs)
    return gdf.geometry.iloc[0]


def load_boundary_df(
    gpkg_path: Path | str,
    layer: str,
    dst_crs: str | None = None,
):
    """Like load_boundary but returns the full GeoDataFrame (for scripts that need
    attributes beyond geometry)."""
    gpd = _gpd()
    gdf = gpd.read_file(str(gpkg_path), layer=layer)
    if dst_crs is not None:
        gdf = gdf.to_crs(dst_crs)
    return gdf


# ---------------------------------------------------------------------------
# Raster I/O
# ---------------------------------------------------------------------------

def write_raster(
    path: Path | str,
    data,
    profile: dict | None = None,
    *,
    transform=None,
    crs: str | None = None,
    dtype: str = "float32",
    nodata: float = NODATA,
    ifpm_note: str = "",
    sanitize: bool = False,
) -> None:
    """Write a single-band GeoTIFF.

    Two calling conventions, matching the two write_raster variants that existed in
    the codebase:

    1. profile-based (most common): pass a rasterio profile dict (usually copied
       from an input raster and updated). ``transform``/``crs`` are ignored.
       write_raster(path, data, profile=src.profile.copy())

    2. transform+crs (DEM preprocessing): pass ``transform`` and ``crs`` instead.
       write_raster(path, data, transform=transform, crs="EPSG:32735")

    The output is always float32, deflate-compressed, tiled 256x256, nodata set,
    matching the convention every script already used independently.

    Extra options absorbed from the criteria/rainfall scripts:
    - ``ifpm_note``: if non-empty, written as a per-band IFPM_NOTE tag (governance
      metadata embedded in the GeoTIFF).
    - ``sanitize``: if True, replace non-finite values (NaN/inf) with ``nodata``
      before writing. Some callers computed arrays that may contain NaN; others
      pre-cleaned their data. Default False preserves the original behaviour of
      the majority of scripts.
    """
    rasterio = _rasterio()
    np = _np()

    if sanitize:
        data = np.where(np.isfinite(data), data, nodata)

    if profile is not None:
        out_profile = dict(profile)
    else:
        if transform is None or crs is None:
            raise ValueError(
                "write_raster needs either `profile` or both `transform` and `crs`"
            )
        out_profile = {
            "driver": "GTiff",
            "height": data.shape[0],
            "width": data.shape[1],
            "count": 1,
            "transform": transform,
            "crs": crs,
        }
    out_profile.update(
        {
            "driver": "GTiff",
            "dtype": dtype,
            "nodata": nodata,
            "compress": "deflate",
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        }
    )
    with rasterio.open(str(path), "w", **out_profile) as dst:
        dst.write(data.astype(dtype), 1)
        if ifpm_note:
            dst.update_tags(1, IFPM_NOTE=ifpm_note)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def raster_stats(data, mask=None) -> dict:
    """Summary statistics for a raster array.

    Two modes, matching the two stats conventions in the codebase:

    - With ``mask`` (a boolean array, True inside the study boundary): reports
      valid_cells, valid_fraction (relative to mask.sum()), min, mean, max.
      Used by criteria-stack builders.
    - Without ``mask``: reports valid_cells, mean, std, min, p50, p95, max over
      the finite values of the array. Used by derive/factor scripts.
    """
    np = _np()
    if mask is not None:
        inside = int(np.asarray(mask).sum())
        valid = np.asarray(mask) & np.isfinite(data)
        values = np.asarray(data)[valid]
        if values.size == 0:
            return {"valid_cells": 0, "valid_fraction": 0.0, "min": "", "mean": "", "max": ""}
        return {
            "valid_cells": int(values.size),
            "valid_fraction": round(float(values.size / inside), 6) if inside else 0.0,
            "min": round(float(values.min()), 6),
            "mean": round(float(values.mean()), 6),
            "max": round(float(values.max()), 6),
        }
    # No-mask mode: full-array stats with percentiles.
    v = np.asarray(data)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return {"valid_cells": 0, "mean": None, "std": None, "min": None,
                "p50": None, "p95": None, "max": None}
    return {
        "valid_cells": int(v.size),
        "mean": float(v.mean()),
        "std": float(v.std()),
        "min": float(v.min()),
        "p50": float(np.percentile(v, 50)),
        "p95": float(np.percentile(v, 95)),
        "max": float(v.max()),
    }


# ---------------------------------------------------------------------------
# Percentile-clip standardization
# ---------------------------------------------------------------------------

def standardize(
    data,
    nodata: float = NODATA,
    invert: bool = False,
    p_low: float = 2.0,
    p_high: float = 98.0,
) -> tuple:
    """Percentile-clip min-max standardization to [0, 1].

    This is the convention used by standardize_v1_terrain.py and the criteria-stack
    builders: clip to the p_low/p_high percentiles of valid values, then scale to
    [0,1]. NoData cells stay NoData. If ``invert``, the direction is flipped
    (higher raw value -> lower score).

    Returns (output_array, low, high) where low/high are the clip bounds actually
    used (needed by callers that record them in diagnostics).
    """
    np = _np()
    valid = np.isfinite(data) & (data != nodata)
    values = data[valid]
    low = float(np.nanpercentile(values, p_low))
    high = float(np.nanpercentile(values, p_high))
    if not high > low:
        raise ValueError(f"Invalid percentile bounds: low={low}, high={high}")

    output = np.full(data.shape, nodata, dtype="float32")
    scaled = (np.clip(data[valid], low, high) - low) / (high - low)
    if invert:
        scaled = 1.0 - scaled
    output[valid] = scaled.astype("float32")
    return output, low, high


# ---------------------------------------------------------------------------
# Grid-gate invocation
# ---------------------------------------------------------------------------

def run_grid_gate(
    reference: Path | str,
    rasters: list[Path | str],
    output: Path | str,
    boundary: Path | str | None = None,
) -> int:
    """Run the V1 raster grid-gate check via subprocess.

    Unifies the subprocess.run([sys.executable, GRID_GATE, ...]) pattern duplicated
    across standardize_v1_terrain, plot_v1_terrain_mentor_package, derive_v1_hydrology,
    derive_peru_pilot_hydrology, derive_v1_worldcover_cfactor,
    derive_peru_pilot_worldcover_cfactor, and prepare_v1_full_methodology_evidence.

    Returns the subprocess exit code.
    """
    import subprocess
    import sys

    grid_gate = ROOT / "bin" / "check_v1_raster_grid.py"
    cmd = [sys.executable, str(grid_gate), "--reference", str(reference),
           "--output", str(output)]
    for r in rasters:
        cmd += ["--rasters", str(r)]
    if boundary is not None:
        cmd += ["--boundary", str(boundary)]
    completed = subprocess.run(cmd, cwd=str(ROOT))
    return completed.returncode


# ---------------------------------------------------------------------------
# Manifest writer (unified criteria-stack metadata)
# ---------------------------------------------------------------------------

def write_manifest_csv(
    path: Path | str,
    rows: list[dict],
    fieldnames: list[str] | None = None,
) -> None:
    """Write a criteria-stack / diagnostics manifest as a CSV with a stable column
    order. Unifies the several hand-rolled csv.DictWriter blocks."""
    import csv
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
