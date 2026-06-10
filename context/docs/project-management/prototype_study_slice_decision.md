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
- Boundary rule: use a catchment or sub-catchment boundary, preferably HydroBASINS-compatible,
  until a more authoritative local boundary is supplied.
- First output grain: raster diagnostics at source-compatible resolution, then optional
  aggregation to sub-basin units.
- Initial working resolution: 30 m for terrain and land-cover-compatible layers when feasible.
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

## Code Work Required Before Real Data Use

Before running real downloaded data through the overlay pipeline, implement raster/grid
diagnostics in `ifpm-flood-pipeline`:

- single-band check;
- CRS presence and CRS comparison;
- transform and resolution comparison;
- shape comparison;
- NoData detection;
- basic finite-value summary;
- output diagnostics as JSON.

Use synthetic fixtures first. Real data should only be used after the diagnostics are tested.

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

