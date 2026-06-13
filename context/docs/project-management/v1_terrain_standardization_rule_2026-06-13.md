# V1 Terrain Standardization Rule

Status: active internal rule for terrain-only diagnostics

Updated: 2026-06-13

## Purpose

This note defines the first V1 terrain standardization rule after the V1 DEM and slope rasters
passed the executable raster-grid gate. It produces 0-1 diagnostic terrain candidates only. It
does not run AHP-MCDA overlay, does not include CHIRPS, does not produce flood-risk or
intervention-priority maps, and does not make V1 the final thesis boundary.

## Inputs

- Reference DEM:
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`
- Slope:
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_slope_degrees_utm35s_30m.tif`
- Required gate:
  `bin/check_v1_raster_grid.py`

## Standardization Rule

- Method: percentile-clipped min-max scaling.
- Clip bounds: V1-valid-cell `2nd` and `98th` percentiles.
- Output range: `0` to `1`.
- Output dtype: `float32`.
- Output NoData: `-9999.0`.
- Output grid: must match the V1 reference DEM exactly.

The percentile rule is a prototype diagnostic choice. It is not a final thesis threshold rule and
must not be used for cross-country or cross-period comparison without replacing it with fixed,
documented thresholds.

## Output Candidates

The script `bin/standardize_v1_terrain.py` writes:

- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_elevation_lowland_context_0_1.tif`
  - Direction: lower elevation gives a higher diagnostic value.
  - Role: context only, not a default scoring criterion.
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_slope_low_slope_susceptibility_0_1.tif`
  - Direction: lower slope gives a higher diagnostic value.
  - Role: recommended terrain-only susceptibility candidate for mentor review.
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_slope_high_runoff_pressure_0_1.tif`
  - Direction: higher slope gives a higher diagnostic value.
  - Role: alternative runoff or erosion-pressure framing.

All three outputs are diagnostic candidates. None is authorized for weighted overlay until the
criteria hierarchy and modelling-unit branch are separately accepted.

## Diagnostics And Handoff

Expected outputs:

- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_terrain_standardization_diagnostics.csv`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_terrain_standardization_grid_check.csv`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_terrain_standardization_qa.png`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_terrain_standardization_handoff.md`

The output grid check must report `grid_compatible=true` for every standardized raster before any
future standardization, scoring, or overlay step can use the outputs.

## Limits

- No CHIRPS is used.
- No rainfall proxy is generated.
- No AHP weights are applied.
- No overlay is run.
- No flood-risk or intervention-priority interpretation is allowed from these outputs alone.
- V1 remains `accepted_with_waiver_for_controlled_prototype`, not a final thesis boundary.
