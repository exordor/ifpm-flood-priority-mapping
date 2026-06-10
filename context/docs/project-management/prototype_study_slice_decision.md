# Prototype Study Slice Decision

Updated: 2026-06-10

Status: draft decision for the first controlled IFPM prototype slice.

## Decision

Use the Zimbabwe / Upper Mzingwane Catchment side as the first prototype slice.

This is a conservative starting point because the study area is already framed as a catchment.
It avoids the immediate Peru ambiguity between administrative regions, ANA hydrographic units,
and hydrological units clipped by administrative regions.

## Prototype Purpose

The first prototype is not a final flood-risk model. It is a controlled workflow slice to prove
that the project can:

- register data before download;
- keep raw data, outputs, and deliverable code separated;
- check raster/vector grid compatibility;
- standardize a small set of spatial layers;
- run the existing AHP weighted-overlay pipeline;
- produce diagnostics that show what is valid, missing, or not yet verified.

## Initial Study Slice

- Study side: Zimbabwe.
- Working study area: Upper Mzingwane Catchment.
- Boundary rule: use a catchment or sub-catchment boundary after the intended definition is
  confirmed. Current unresolved candidates are Geoportal `Upper Mzingwane`, HydroBASINS level 7
  `HYBAS_ID=1071528840`, or a narrower boundary matching the untraced `~2138 km2` reference.
- First output grain: raster diagnostics at source-compatible resolution, then optional
  aggregation to sub-basin units.
- Initial terrain working resolution: 30 m for SRTM-derived terrain layers when feasible.
  Coarser sources such as CHIRPS should remain at native resolution, aggregated, or converted to
  zonal summaries until the overlay/resampling rule is explicitly agreed.
- Comparison scope: prototype only; do not compare against Peru until the Peru boundary rule is
  fixed.

## Starter Dataset Candidates

Do not download these yet. Create registry notes and preflight checks first.

1. DEM / terrain baseline: SRTM 1 Arc-Second Global DEM.
2. Hydrological framework: HydroBASINS and, if needed, HydroRIVERS.
3. Rainfall baseline: CHIRPS v3.

These are starter candidates because they support terrain, hydrological context, and rainfall
hazard indicators without requiring the mining-data interpretation rule to be solved first.

## First Prototype Indicators

Keep the first indicator set deliberately small:

- elevation;
- slope;
- flow accumulation or drainage-distance proxy;
- rainfall summary or rainfall-intensity proxy;
- optional catchment/sub-basin id for aggregation.

Do not include mining pressure, rehabilitation potential, or socioeconomic vulnerability in the
first prototype unless their data source and interpretation rules are explicitly documented.

## Required Notes Before Download

For each selected dataset:

- create a dataset registry note from `context/docs/data-management/dataset_registry_template.md`;
- complete the download preflight checklist;
- confirm the target path is ignored by Git;
- record access/licence requirements;
- record expected file types and expected size where available.

## Code Preconditions Before Real Data Use

Completed scaffolding in `ifpm-flood-pipeline`:

- raster metadata diagnostics for band count, CRS, transform, resolution, shape, and NoData;
- standardization CLI and diagnostics for controlled synthetic GeoTIFF inputs;
- weighted overlay CLI with AHP consistency checks;
- synthetic preprocessing-to-overlay smoke test.

Remaining blockers before a real-data overlay or interpretation run:

- geospatial verification must run with the geospatial extra installed, not only with skipped
  raster tests;
- diagnostics need finite-value and mask summaries, or an explicit waiver for the first real
  diagnostic-only run;
- overlay should enforce standardized 0-1 inputs by default, or require an explicit override;
- overlay diagnostics should report per-layer valid fractions and intersection mask loss;
- the selected model-unit branch must be executable, especially if CHIRPS is aggregated rather
  than raster-overlaid.

## Validation Boundary

The first prototype can prove workflow readiness, not model validity.

It may support claims such as:

- the data-management process is traceable;
- input rasters can be checked for compatibility;
- standardized layers can be combined reproducibly;
- NoData and grid mismatches are visible in diagnostics.

It must not claim:

- validated flood-risk prediction;
- final intervention priority;
- Zimbabwe-Peru comparison;
- mining-impact assessment;
- rehabilitation suitability.

## Exit Criteria

The prototype slice is ready to move to controlled download when:

- this decision note is accepted as the working scope;
- three dataset registry notes exist;
- three preflight checklists are complete;
- raster/grid diagnostics are implemented and tested on synthetic data;
- the parent workspace boundary check passes.
