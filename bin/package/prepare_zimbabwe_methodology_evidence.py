#!/usr/bin/env python3
"""Run the V1 full methodology evidence preparation steps."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STEPS = [
    "bin/package/check_zimbabwe_raster_grid.py",
    "bin/package/prepare_zimbabwe_methodology_raster_layers.py",
    "bin/package/prepare_zimbabwe_methodology_vector_layers.py",
    "bin/criteria/build_zimbabwe_methodology_evidence_matrix.py",
]


def main() -> None:
    for step in STEPS:
        subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT, check=True)
    print("prepared V1 full methodology evidence package")


if __name__ == "__main__":
    main()
