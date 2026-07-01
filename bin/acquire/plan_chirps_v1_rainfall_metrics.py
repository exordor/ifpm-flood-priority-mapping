#!/usr/bin/env python3
"""Write the scoped CHIRPS V1 rainfall-comparison download plan."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET_ID = "chirps_v3_zimbabwe_prototype"
OUT_DIR = ROOT / f"outputs/{DATASET_ID}/rainfall_comparison"
PLAN_CSV = OUT_DIR / "chirps_v1_download_plan.csv"

ANNUAL_YEARS = range(1981, 2025)
RAINY_SEASONS = range(1981, 2024)
RECENT_SEASONS = range(2019, 2024)
DAILY_START = date(2023, 11, 1)
DAILY_END = date(2024, 3, 31)

BASE = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0"
RAW_ROOT = Path(f"data/raw/{DATASET_ID}")


def annual_url(year: int) -> str:
    return f"{BASE}/annual/africa/tifs/chirps-v3.0.{year}.tif"


def monthly_url(year: int, month: int) -> str:
    return f"{BASE}/monthly/africa/tifs/chirps-v3.0.{year}.{month:02d}.tif"


def pentad_url(year: int, month: int, pentad: int) -> str:
    return f"{BASE}/pentads/africa/tifs/chirps-v3.0.{year}.{month:02d}.{pentad}.tif"


def daily_rnl_cog_url(day: date) -> str:
    return f"{BASE}/daily/final/rnl/cogs/{day.year}/chirps-v3.0.rnl.{day:%Y.%m.%d}.cog"


def rainy_months(season_start: int) -> list[tuple[int, int]]:
    return [(season_start, 11), (season_start, 12), (season_start + 1, 1), (season_start + 1, 2), (season_start + 1, 3)]


def date_range(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def row(role: str, year: int | str, month: int | str, period: int | str, source_url: str, local_path: Path) -> dict[str, str]:
    return {
        "input_role": role,
        "year": str(year),
        "month": str(month),
        "period": str(period),
        "source_url": source_url,
        "local_path": str(local_path),
        "download_mode": "direct_file" if role != "daily_rnl_cog_v1_bbox" else "remote_cog_v1_bbox_clip",
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for year in ANNUAL_YEARS:
        rows.append(row("annual_africa_tif", year, "", "", annual_url(year), RAW_ROOT / "annual_africa_tifs" / f"chirps-v3.0.{year}.tif"))

    monthly_keys = {(year, month) for season in RAINY_SEASONS for year, month in rainy_months(season)}
    for year, month in sorted(monthly_keys):
        rows.append(
            row("monthly_africa_tif", year, month, "", monthly_url(year, month), RAW_ROOT / "monthly_africa_tifs" / f"chirps-v3.0.{year}.{month:02d}.tif")
        )

    for season in RECENT_SEASONS:
        for year, month in rainy_months(season):
            for pentad in range(1, 7):
                rows.append(
                    row(
                        "pentad_africa_tif",
                        year,
                        month,
                        pentad,
                        pentad_url(year, month, pentad),
                        RAW_ROOT / "pentad_africa_tifs" / f"chirps-v3.0.{year}.{month:02d}.{pentad}.tif",
                    )
                )

    for day in date_range(DAILY_START, DAILY_END):
        rows.append(
            row(
                "daily_rnl_cog_v1_bbox",
                day.year,
                day.month,
                day.day,
                daily_rnl_cog_url(day),
                RAW_ROOT / "daily_rnl_v1_bbox_tifs" / f"chirps-v3.0.rnl.{day:%Y.%m.%d}.v1_bbox.tif",
            )
        )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PLAN_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    print(f"wrote {PLAN_CSV.relative_to(ROOT)}")
    print(f"planned files: {len(rows)}")


if __name__ == "__main__":
    main()
