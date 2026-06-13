#!/usr/bin/env python3
"""Run the V1 full methodology evidence preparation steps."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "bin/check_v1_raster_grid.py",
    "bin/prepare_v1_methodology_raster_layers.py",
    "bin/prepare_v1_methodology_vector_layers.py",
    "bin/build_v1_full_methodology_evidence_matrix.py",
]


def main() -> None:
    for step in STEPS:
        subprocess.run([sys.executable, str(ROOT / step)], cwd=ROOT, check=True)
    print("prepared V1 full methodology evidence package")


if __name__ == "__main__":
    main()
