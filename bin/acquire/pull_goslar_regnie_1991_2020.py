#!/usr/bin/env python3
"""Download DWD REGNIE monthly precipitation for the Goslar focus area.

Pulls the JJA (Jun-Aug) monthly grids for the official DWD climate normal
window 1991-2020 (30 years) into ``data/raw/dwd_regnie_germany/raw/``.
Files already present are skipped; existing 2014-2023 JJA files are a subset
and remain valid.

Source: DWD CDC open data
  https://opendata.dwd.de/climate_environment/CDC/grids_germany/monthly/precipitation/<MM_Mon>/
Product: REGNIE monthly precipitation grids, Germany, 1 km, EPSG:31467.

Run: .venv/bin/python bin/acquire/pull_goslar_regnie_1991_2020.py
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/raw/dwd_regnie_germany/raw"
BASE = "https://opendata.dwd.de/climate_environment/CDC/grids_germany/monthly/precipitation"
MONTH_DIR = {6: "06_Jun", 7: "07_Jul", 8: "08_Aug"}
YEAR_START, YEAR_END = 1991, 2020


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as out:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)


def main() -> int:
    missing: list[str] = []
    for year in range(YEAR_START, YEAR_END + 1):
        for month in (6, 7, 8):
            name = f"grids_germany_monthly_precipitation_{year}{month:02d}.asc.gz"
            dest = RAW_DIR / name
            if dest.exists() and dest.stat().st_size > 1000:
                continue
            url = f"{BASE}/{MONTH_DIR[month]}/{name}"
            print(f"downloading {name} ({url})", flush=True)
            try:
                fetch(url, dest)
            except Exception as exc:  # noqa: BLE001 - keep going on per-file errors
                print(f"FAILED {name}: {exc}", flush=True)
                missing.append(name)
    if missing:
        print(f"{len(missing)} file(s) failed: {missing}", file=sys.stderr)
        return 1
    n = len(list(RAW_DIR.glob("grids_germany_monthly_precipitation_*.asc.gz")))
    print(f"done; {n} REGNIE JJA files under {RAW_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
