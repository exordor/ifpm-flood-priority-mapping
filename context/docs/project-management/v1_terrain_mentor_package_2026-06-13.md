# V1 Terrain Mentor Package

Status: mentor-facing terrain diagnostic package planned and generated from existing V1 terrain
standardization outputs.

Updated: 2026-06-13

## Purpose

This package translates the V1 terrain-only diagnostics into a mentor-readable figure board,
caption, evidence table, and handoff note. It supports a discussion about how slope should be
represented before any AHP-MCDA overlay or flood-risk interpretation.

## Inputs

- V1 standardized terrain rasters under
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/`
- V1 working boundary under `outputs/v1_working_boundary/`
- V1 raster grid gate script: `bin/check_v1_raster_grid.py`

No new data was downloaded.

## Outputs

- `outputs/v1_terrain_mentor_package/mentor_v1_terrain_diagnostic_board.png`
- `outputs/v1_terrain_mentor_package/mentor_v1_terrain_diagnostic_board.pdf`
- `outputs/v1_terrain_mentor_package/mentor_v1_terrain_caption.md`
- `outputs/v1_terrain_mentor_package/mentor_v1_terrain_caption.txt`
- `outputs/v1_terrain_mentor_package/mentor_v1_terrain_evidence_table.csv`
- `outputs/v1_terrain_mentor_package/mentor_v1_terrain_handoff.md`

## Interpretation

- `slope_low_slope_susceptibility` is the primary terrain candidate for mentor review.
- `slope_high_runoff_pressure` is retained as an alternative framing.
- Elevation is shown as lowland context only, not as a default scoring criterion.

These outputs are not a flood-risk map, not an intervention-priority map, not an AHP-MCDA overlay,
and not final thesis boundary evidence.

## Recommended Mentor Question

Should the terrain component emphasize low-slope susceptibility, keep high-slope runoff pressure
as an alternative, or exclude terrain from scoring until rainfall/exposure evidence is added?
