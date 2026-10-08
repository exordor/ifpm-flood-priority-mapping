#!/usr/bin/env python3
"""Run the Secocha event-rainfall crop for CHIRPS v3 ``rnl`` sensitivity context."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "bin/acquire/pull_secocha_2023_event_rainfall.py"
spec = importlib.util.spec_from_file_location("secocha_event_rainfall", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import rainfall implementation from {SOURCE}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.CHIRPS_PRODUCT = "rnl"
module.VARIANT_WRAPPER_PATH = Path(__file__).resolve()
module.CHIRPS_URL_TEMPLATE = (
    "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/{year}/"
    "chirps-v3.0.rnl.{year}.{month:02d}.{day:02d}.tif"
)
module.DATA_DIR = ROOT / "data/validation/secocha_2023_validation/rainfall/chirps_v3_rnl_daily_event_window"
module.OUTPUT_DIR = ROOT / "outputs/secocha_2023_validation/rainfall_rnl"
module.STACK_PATH = module.DATA_DIR / "chirps_v3_rnl_daily_2023-01-07_2023-02-10_native.tif"
module.ACCUM_PATH = module.DATA_DIR / "chirps_v3_rnl_accumulations_to_2023-02-05_native.tif"
module.MANIFEST_PATH = module.OUTPUT_DIR / "event_rainfall_rnl_manifest.json"
module.SUMMARY_PATH = module.OUTPUT_DIR / "event_rainfall_rnl_summary.json"
module.FIGURE_PATH = module.OUTPUT_DIR / "event_rainfall_rnl_accumulation.png"


if __name__ == "__main__":
    module.main()
