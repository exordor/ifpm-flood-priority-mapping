#!/usr/bin/env python3
"""Build a mentor-facing Upper Mzingwane methodology evidence report package."""

from __future__ import annotations

import csv
import shutil
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-06-13"
PACKAGE = ROOT / f"exports/v1_methodology_mentor_report_package_{DATE}"
FIGURES = PACKAGE / "figures"
TABLES = PACKAGE / "tables"

FULL = ROOT / "outputs/v1_full_methodology_evidence_sweep"
RAIN = ROOT / "outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison"
TERRAIN = ROOT / "outputs/v1_terrain_mentor_package"
BOUNDARY = ROOT / "outputs/v1_working_boundary"

FIGURE_SOURCES = [
    ("figure_01_v1_working_boundary", BOUNDARY / "v1_boundary_paper.png", BOUNDARY / "v1_boundary_paper.pdf"),
    ("figure_02_chirps_rainfall_comparison", RAIN / "mentor_v1_chirps_rainfall_comparison_board.png", RAIN / "mentor_v1_chirps_rainfall_comparison_board.pdf"),
    ("figure_03_terrain_diagnostic", TERRAIN / "mentor_v1_terrain_diagnostic_board.png", TERRAIN / "mentor_v1_terrain_diagnostic_board.pdf"),
    ("figure_04_land_use_worldcover", FULL / "panel_land_use_worldcover.png", FULL / "panel_land_use_worldcover.pdf"),
    ("figure_05_surface_water_occurrence", FULL / "panel_surface_water_occurrence.png", FULL / "panel_surface_water_occurrence.pdf"),
    ("figure_06_protected_areas", FULL / "panel_protected_areas_wdpca.png", FULL / "panel_protected_areas_wdpca.pdf"),
    ("figure_07_population_built_up_exposure", FULL / "panel_population_exposure.png", FULL / "panel_population_exposure.pdf"),
    ("figure_08_rehabilitation_proximity", FULL / "panel_rehabilitation_proximity.png", FULL / "panel_rehabilitation_proximity.pdf"),
]

TABLE_SOURCES = [
    "v1_full_methodology_evidence_matrix.csv",
    "v1_full_methodology_layer_summary.csv",
    "source_manifest.csv",
    "v1_worldcover_class_area.csv",
    "v1_ghsl_summary.csv",
    "v1_jrc_surface_water_summary.csv",
    "v1_rehabilitation_indicator_components.csv",
    "v1_wdpca_protected_area_summary.csv",
    "v1_dfo_zimbabwe_flood_events.csv",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def require(paths: list[Path]) -> None:
    missing = [rel(path) for path in paths if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("Missing package inputs:\n" + "\n".join(missing))


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_assets() -> list[dict[str, str]]:
    figure_rows = []
    for stem, png, pdf in FIGURE_SOURCES:
        for src in [png, pdf]:
            copy_file(src, FIGURES / f"{stem}{src.suffix}")
        figure_rows.append({"figure": stem, "png": f"figures/{stem}.png", "pdf": f"figures/{stem}.pdf"})

    for name in TABLE_SOURCES:
        copy_file(FULL / name, TABLES / name)
    copy_file(RAIN / "v1_rainfall_metric_summary.csv", TABLES / "v1_rainfall_metric_summary.csv")
    copy_file(TERRAIN / "mentor_v1_terrain_evidence_table.csv", TABLES / "mentor_v1_terrain_evidence_table.csv")
    copy_file(BOUNDARY / "v1_working_boundary_manifest.csv", TABLES / "v1_working_boundary_manifest.csv")
    return figure_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def factor_summary() -> pd.DataFrame:
    matrix = pd.read_csv(FULL / "v1_full_methodology_evidence_matrix.csv")
    return (
        matrix.groupby("factor")
        .agg(
            candidate_layers=("candidate_evidence_layer", "count"),
            evidence_strengths=("evidence_strength", lambda values: "; ".join(sorted(set(values)))),
            ahp_status=("ahp_eligibility", lambda values: "; ".join(sorted(set(values)))),
        )
        .reset_index()
    )


def mentor_message() -> str:
    return """Hi Supervisor,

I prepared a small evidence package for the Upper Mzingwane prototype.

This is not a flood-risk map yet. It has no AHP weights and no weighted overlay. It only shows the data layers we can use for the first prototype.

The package includes rainfall, terrain, land cover, rivers/water, protected areas, population/built-up areas, roads, and provisional mining-indicator data.

Could you please help me decide:

1. Which data groups should be used as criteria?
2. For rainfall, should I use long-term average, rainy-season total, recent anomaly, or extreme rainfall?
3. For terrain, should I use low-slope areas, high-slope runoff pressure, or keep terrain only as background context?
4. Are the OSM mining/quarry indicators acceptable for the prototype, or should I wait for official mining data?
5. Should protected areas and water proximity be used as environmental sensitivity criteria, or only as context?

After your feedback, I can prepare the first AHP criteria table. I will not run the weighted overlay before the criteria and weights are agreed.
"""


def mentor_brief(factors: pd.DataFrame, figures: list[dict[str, str]]) -> str:
    factor_lines = "\n".join(
        f"- {row.factor}: {int(row.candidate_layers)} candidate layer(s); strength/status: {row.evidence_strengths}; AHP: {row.ahp_status}."
        for row in factors.itertuples()
    )
    figure_lines = "\n".join(f"- `{row['png']}` / `{row['pdf']}`" for row in figures)
    return f"""# Upper Mzingwane Multi-Criteria Evidence Package For Mentor Review

Status: mentor-review package only. This is not a final thesis boundary, not a flood-risk map,
not an intervention-priority map, and not an AHP weighted overlay.

## Purpose

The purpose of this package is to show which data layers are currently available for the
Upper Mzingwane controlled prototype and to ask which evidence families should become criteria in
the first prototype model.

## One-Sentence Summary

The Upper Mzingwane prototype now has candidate evidence for flood/water context, rainfall, terrain, land cover / ASM indicators,
environmental sensitivity, socioeconomic exposure, and rehabilitation/accessibility, but the
criteria hierarchy and AHP weights still need mentor approval before any overlay.

## Evidence Families

{factor_lines}

## Key Results To Mention

- The Upper Mzingwane catchment is still a controlled prototype working boundary, accepted with waiver, not the final thesis
  boundary.
- Geoportal Flood Prone Zones have zero local overlap inside the current Upper Mzingwane review layers, so they are
  a gap/weak evidence item, not a flood hazard layer.
- CHIRPS rainfall is processed at native scale and summarized for comparison; it is not resampled
  into a fake 30 m rainfall raster.
- ESA WorldCover gives land-cover and bare/sparse land context, but it does not prove active ASM.
- OSM quarry/industrial features are limited mining-indicator evidence only.
- WorldPop and GHSL provide socioeconomic exposure cross-checks, not full vulnerability.
- WDPCA protected/conserved areas overlap the Upper Mzingwane prototype and can support environmental sensitivity review if
  the mentor agrees.
- Rehabilitation potential is represented by components only: land cover, slope context, and
  distance/proximity to rivers, roads, and limited mining-indicator features.

## Recommended Mentor Decision

Ask the mentor to choose which evidence families should enter the first prototype criteria set:

1. Flood/water-history context
2. Rainfall
3. Terrain
4. Land use / ASM pressure
5. Environmental sensitivity
6. Socioeconomic exposure/vulnerability
7. Rehabilitation/accessibility potential

Then ask for the interpretation direction for rainfall, terrain, mining, and environmental
sensitivity before creating AHP pairwise comparisons.

## Figures Included

{figure_lines}

## Main Tables Included

- `tables/v1_full_methodology_evidence_matrix.csv`
- `tables/source_manifest.csv`
- `tables/v1_rainfall_metric_summary.csv`
- `tables/mentor_v1_terrain_evidence_table.csv`
- `tables/v1_working_boundary_manifest.csv`
"""


def readme() -> str:
    return """# How to use the report package

This package is for reporting to the mentor which evidence layers have already been processed for the Upper Mzingwane prototype, and what she needs to decide next.

Suggested sending order:

1. First send the text in `mentor_message_en.txt`.
2. Attach `mentor_brief_en.md` or copy its Key Results.
3. Send these figures first:
   - `figures/figure_01_v1_working_boundary.png`
   - `figures/figure_02_chirps_rainfall_comparison.png`
   - `figures/figure_03_terrain_diagnostic.png`
   - `figures/figure_07_population_built_up_exposure.png`
4. If the mentor wants more detail, send the land-cover, water, protected areas and rehabilitation panels.
5. If the mentor asks about data sources, send `tables/source_manifest.csv`.
6. If the mentor asks which factors can go into the AHP, send `tables/v1_full_methodology_evidence_matrix.csv`.

Do not describe this package as a flood-risk result. It is only a criteria/evidence review package.
"""


def write_text_files(figures: list[dict[str, str]]) -> None:
    factors = factor_summary()
    factors.to_csv(TABLES / "mentor_factor_summary.csv", index=False)
    write_csv(PACKAGE / "figure_index.csv", figures)
    (PACKAGE / "README_CN.md").write_text(readme(), encoding="utf-8")
    (PACKAGE / "mentor_message_en.txt").write_text(mentor_message(), encoding="utf-8")
    (PACKAGE / "mentor_brief_en.md").write_text(mentor_brief(factors, figures), encoding="utf-8")


def zip_package() -> Path:
    zip_path = PACKAGE.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(PACKAGE.parent))
    return zip_path


def main() -> None:
    required = [src for _, png, pdf in FIGURE_SOURCES for src in [png, pdf]]
    required += [FULL / name for name in TABLE_SOURCES]
    required += [RAIN / "v1_rainfall_metric_summary.csv", TERRAIN / "mentor_v1_terrain_evidence_table.csv"]
    required += [BOUNDARY / "v1_working_boundary_manifest.csv"]
    require(required)

    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    figures = copy_assets()
    write_text_files(figures)
    zip_path = zip_package()
    print(f"wrote {PACKAGE.relative_to(ROOT)}")
    print(f"wrote {zip_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
