"""Raster and table input/output shared by all stages.

The raster helpers are copied from the old chains so the files they write are the same:
float32, deflate, 256x256 tiles, NoData -9999 (bin/factors/run_goslar_pim_chain.py), and
masked reads to float64 with NaN for NoData (bin/_lib/goslar_comparison.py).
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask

NODATA = -9999.0


def sha256_file(path: Path) -> str | None:
    """SHA-256 of a file, or None when it does not exist."""
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_raster(path: Path, data: np.ndarray, transform, crs, nodata: float = NODATA) -> None:
    """Write one float32 band (callers replace NaN with ``nodata`` first)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff", "height": data.shape[0], "width": data.shape[1], "count": 1,
        "dtype": "float32", "crs": crs, "transform": transform, "nodata": nodata,
        "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype("float32"), 1)


def read_band(path: Path, profile: dict) -> np.ndarray:
    """Read band 1 as float32 with NaN for NoData; the grid must equal ``profile``."""
    with rasterio.open(path) as src:
        if str(src.crs) != str(profile["crs"]) or src.transform != profile["transform"]:
            raise ValueError(f"grid mismatch: {path}")
        if src.width != profile["width"] or src.height != profile["height"]:
            raise ValueError(f"shape mismatch: {path}")
        data = src.read(1).astype("float32")
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
    data[~np.isfinite(data)] = np.nan
    return data


def read_grid(path: Path, ref: dict | None = None):
    """Read band 1 as float64 with NaN for NoData; optionally require the ``ref`` grid."""
    with rasterio.open(path) as ds:
        if ref is not None and (ds.crs != ref['crs'] or ds.transform != ref['transform']
                                or ds.shape != (ref['height'], ref['width'])):
            raise ValueError(f'Incompatible reference grid: {path.name}')
        arr = ds.read(1, masked=True).astype('float64').filled(np.nan)
        arr[~np.isfinite(arr)] = np.nan
        return arr, ds.profile


def raster_mask(geometry, ref: dict, touched: bool = False) -> np.ndarray:
    """Cells of the ``ref`` grid inside ``geometry`` (cell centre, or all touched)."""
    shape = (ref['height'], ref['width'])
    if geometry.is_empty:
        return np.zeros(shape, dtype=bool)
    return geometry_mask([geometry], out_shape=shape, transform=ref['transform'], invert=True,
                         all_touched=touched)


def write_csv(path: Path, rows: list[dict]) -> None:
    """Write dict rows; the columns are the keys of the first row."""
    if not rows:
        raise ValueError('No rows for ' + str(path))
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
