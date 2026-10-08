#!/usr/bin/env python3
"""Download and pin the SoilGrids 250 m window for the active Secocha extent.

The shared downloader records the twelve property/depth windows, the derived
Williams (1995) 0-30 cm K snapshot, and SHA-256 provenance under data/raw.

Run: .venv/bin/python bin/acquire/pull_secocha_soilgrids_window.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY = ROOT / "outputs/peru_secocha_boundary/peru_secocha_active_boundary.gpkg"
BOUNDARY_LAYER = "secocha_active_boundary"
OUT_DIR = ROOT / "data/raw/soilgrids_250m_peru_secocha"


def load_shared_downloader():
    path = ROOT / "bin/acquire/pull_goslar_soilgrids_window.py"
    spec = importlib.util.spec_from_file_location("ifpm_soilgrids_window", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if not BOUNDARY.exists():
        raise FileNotFoundError(BOUNDARY)
    bounds = gpd.read_file(BOUNDARY, layer=BOUNDARY_LAYER).to_crs(4326).total_bounds
    shared = load_shared_downloader()
    shared.OUT_DIR = OUT_DIR
    shared.RAW_DIR = OUT_DIR / "raw"
    shared.DIAGNOSTICS = OUT_DIR / "soilgrids_peru_secocha_diagnostics.json"
    shared.K_SNAPSHOT = OUT_DIR / "k_factor_0_30cm_avg_250m_us.tif"
    shared.DATASET_ID = "soilgrids_250m_peru_secocha"
    (
        shared.FOCUS_LON_MIN,
        shared.FOCUS_LAT_MIN,
        shared.FOCUS_LON_MAX,
        shared.FOCUS_LAT_MAX,
    ) = map(float, bounds)
    return shared.main()


if __name__ == "__main__":
    raise SystemExit(main())
