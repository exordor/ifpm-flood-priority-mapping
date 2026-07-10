#!/usr/bin/env python3
"""Create a PE1-bbox WorldPop Peru population subset.

The full WorldPop Peru 2020 raster is ~625 MB. The script keeps that verified
source locally and deterministically writes the current study-area subset under
data/raw.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.windows import from_bounds, transform as window_transform

ROOT = Path(__file__).resolve().parents[2]
PE1_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
RAW_DIR = ROOT / "data/raw/worldpop_peru_population"
OUT_DIR = ROOT / "outputs/worldpop_peru_population"

WORLDPOP_URL = (
    "https://data.worldpop.org/GIS/Population/Global_2000_2020/"
    "2020/PER/per_ppp_2020_UNadj.tif"
)
OUT_TIF = RAW_DIR / "per_ppp_2020_UNadj_pe1_bbox.tif"
FULL_TIF = RAW_DIR / "per_ppp_2020_UNadj.tif"

INPUTS = [ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"]
OUTPUTS = [
    ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj.tif",
    ROOT / "data/raw/worldpop_peru_population/per_ppp_2020_UNadj_pe1_bbox.tif",
    ROOT / "outputs/worldpop_peru_population/worldpop_peru_population_subset_manifest.json",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_size_bytes() -> int | None:
    req = urllib.request.Request(WORLDPOP_URL, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            size = resp.headers.get("Content-Length")
            return int(size) if size else None
    except Exception:
        return None


def download_full_source() -> Path:
    expected_size = source_size_bytes()
    if FULL_TIF.exists() and FULL_TIF.stat().st_size > 0:
        if expected_size is not None and FULL_TIF.stat().st_size != expected_size:
            raise RuntimeError(
                f"existing WorldPop file has unexpected size: {FULL_TIF.stat().st_size} "
                f"!= {expected_size}. Remove it before retrying."
            )
        print(f"using existing full source: {rel(FULL_TIF)}")
        return FULL_TIF

    print("remote range reads are unavailable; downloading full WorldPop source...")
    req = urllib.request.Request(WORLDPOP_URL, headers={"User-Agent": "Mozilla/5.0"})
    part = FULL_TIF.with_suffix(FULL_TIF.suffix + ".part")
    with urllib.request.urlopen(req, timeout=120) as resp, part.open("wb") as out:
        shutil.copyfileobj(resp, out, length=1024 * 1024)
    if expected_size is not None and part.stat().st_size != expected_size:
        raise RuntimeError(f"downloaded WorldPop file has unexpected size: {part.stat().st_size} != {expected_size}")
    part.replace(FULL_TIF)
    print(f"downloaded full source: {rel(FULL_TIF)} ({FULL_TIF.stat().st_size:,} bytes)")
    return FULL_TIF


def write_subset(src_path: str | Path, bounds: tuple[float, float, float, float], env_kwargs: dict[str, str]) -> np.ma.MaskedArray:
    with rasterio.Env(**env_kwargs):
        with rasterio.open(src_path) as src:
            window = from_bounds(*bounds, transform=src.transform)
            window = window.round_offsets().round_lengths()
            data = src.read(1, window=window, masked=True)
            profile = src.profile.copy()
            profile.update(
                driver="GTiff",
                height=data.shape[0],
                width=data.shape[1],
                transform=window_transform(window, src.transform),
                compress="deflate",
                tiled=True,
                blockxsize=256,
                blockysize=256,
            )
            fill = src.nodata if src.nodata is not None else -99999.0
            profile.update(nodata=fill)
            out = np.ma.filled(data, fill).astype(profile["dtype"])
            with rasterio.open(OUT_TIF, "w", **profile) as dst:
                dst.write(out, 1)
            return data


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    boundary = gpd.read_file(PE1_GPKG, layer="peru_pilot_boundary").to_crs("EPSG:4326")
    minx, miny, maxx, maxy = boundary.total_bounds
    pad = 0.05
    bounds = (minx - pad, miny - pad, maxx + pad, maxy + pad)
    print(f"WorldPop source: {WORLDPOP_URL}")
    print(f"full source size bytes: {source_size_bytes()}")
    print(f"reading bbox: {bounds}")

    local_source = download_full_source()
    data = write_subset(local_source, bounds, {})

    valid = data.compressed()
    manifest = {
        "dataset_id": "worldpop_peru_population",
        "source_url": WORLDPOP_URL,
        "source_product": "WorldPop Peru 2020 population count, unconstrained, UN-adjusted",
        "source_full_size_bytes": source_size_bytes(),
        "local_full_source": rel(FULL_TIF) if FULL_TIF.exists() else None,
        "local_full_source_size_bytes": FULL_TIF.stat().st_size if FULL_TIF.exists() else None,
        "local_full_source_sha256": sha256_file(FULL_TIF) if FULL_TIF.exists() else None,
        "local_subset": rel(OUT_TIF),
        "local_subset_size_bytes": OUT_TIF.stat().st_size,
        "local_subset_sha256": sha256_file(OUT_TIF),
        "bbox_epsg4326": [round(float(x), 6) for x in bounds],
        "valid_cells": int(valid.size),
        "population_sum_in_bbox": float(valid.sum()) if valid.size else 0.0,
        "min": float(valid.min()) if valid.size else None,
        "mean": float(valid.mean()) if valid.size else None,
        "max": float(valid.max()) if valid.size else None,
        "claim_level": "diagnostic_only",
        "evidence_role": "population_exposure_input",
        "note": "Raw population-count subset for exposure summaries; not observed affected population.",
    }
    manifest_path = OUT_DIR / "worldpop_peru_population_subset_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    print(f"wrote: {rel(OUT_TIF)}")
    print(f"wrote: {rel(manifest_path)}")


if __name__ == "__main__":
    main()
