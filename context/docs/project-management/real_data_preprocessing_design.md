# Real-Data Raster Preprocessing Design

Status: internal design draft, revised after mentor feedback. HydroBASINS boundary discovery and
Zimbabwe Geoportal Sub-Catchments boundary comparison have been executed as narrow boundary-only
exceptions. A scoped SRTM raw-tile download, inventory, and V1 DEM/slope preprocessing run has
been completed for terrain diagnostics only, but no CHIRPS, overlay input, or interpretation
dataset has been downloaded or processed.

## Purpose

This note defines the first real-data preprocessing rules for the Zimbabwe / Upper Mzingwane
prototype slice. It is a gate before any additional real GIS, raster, vector, validation, or
sample data is downloaded beyond the narrow boundary-only exceptions already recorded for
HydroBASINS and Zimbabwe Geoportal Sub-Catchments. The goal is to prevent a synthetic-tested
pipeline from being applied to real data with unclear grid, CRS, NoData, aggregation, or
resampling assumptions.

## Scope Boundary

- Study side: Zimbabwe.
- Regional context: Upper Mzingwane.
- Working area: an outlet-based upstream catchment after the outlet is supplied or approved, or
  an explicitly waived proxy boundary.
- First data candidates: SRTM 1 Arc-Second, HydroBASINS/HydroRIVERS, and CHIRPS v3.
- First indicator family: terrain, drainage proxy, rainfall summary, and optional sub-basin id.
- Not included in the first real-data slice: mining pressure, socioeconomic vulnerability, and
  rehabilitation potential.

This design supports workflow readiness and preliminary susceptibility screening only. It does
not support validated flood-risk, intervention-priority, mining-impact, or Zimbabwe-Peru
comparison claims.

## Pre-Download Gate

Do not download additional real data or run preprocessing until all of these are true:

1. The outlet or provisional pour point is selected and documented.
2. The outlet's flood/mining relevance is recorded.
3. The outlet-based catchment boundary or approved proxy boundary is selected and documented.
4. The modelling unit is selected: raster-first, sub-basin aggregation, or mixed workflow.
5. The temporal window for rainfall and validation evidence is selected.
6. The relevant dataset preflight checklist has no unchecked blocking item.
7. The intended raw destination is under `data/raw/<dataset_id>/`.
8. The intended output destination is under `outputs/<dataset_id>/` or a prototype-specific
   ignored output directory.

## Boundary And CRS Rules

- Use an outlet-based upstream catchment for the Zimbabwe prototype when the outlet is known.
- Prefer a HydroBASINS-compatible unit only if the selected level and basin id are recorded.
- If a mentor supplies an authoritative local catchment boundary, record its source and replace
  or supplement HydroBASINS.
- Treat Geoportal, HydroBASINS, and the literature `~2138 km2` boundary as comparison layers
  unless one is explicitly accepted as a proxy.
- Keep source CRS information in the dataset registry and preprocessing diagnostics.
- Reproject only derived working rasters or analysis copies, never the raw source files.
- Record the target CRS and transform before producing overlay inputs.

## Boundary Acceptance Gate

An outlet-based, HydroBASINS, or local boundary is not accepted only because it can be loaded.
Before it becomes the prototype mask or aggregation geometry, record:

- outlet name, coordinates, or provisional map description;
- why the outlet is relevant to the flood-affected and mining-influenced area;
- whether the outlet is mentor-selected, mentor-provisional, author/authority supplied, or a
  technical proxy;
- selected HydroBASINS level, HYBAS id, PFAF id, and version, or the local boundary source;
- whether multiple units are unioned or dissolved, and the rule used to do so;
- geometry validity and CRS;
- outlet or downstream plausibility for the intended Upper Mzingwane catchment;
- area and shape comparison against any mentor-supplied or authoritative local boundary;
- mismatch policy if HydroBASINS and a local boundary disagree;
- whether the boundary is accepted, rejected, or accepted with a documented waiver.

Do not run a real-data overlay or aggregation if the boundary acceptance state is still unknown.

## Grid And Resolution Rules

For the active V1 controlled prototype terrain run, the detailed reference-grid rule is saved in
`context/docs/data-management/v1_terrain_reference_grid_rule.md`. That file is authoritative for
V1 terrain derivative compatibility before any standardization, scoring, or overlay.

### Terrain-Derived Raster Grid

- SRTM-derived terrain layers may use an SRTM-compatible 30 m working grid when feasible.
- Terrain derivatives include elevation, slope, and drainage-distance or flow-accumulation
  proxies.
- All terrain-derived rasters used together must share CRS, transform, resolution, shape, and
  NoData semantics before overlay.
- Choose and record a metric working CRS before deriving slope, flow accumulation, drainage
  distance, or other distance/area-sensitive layers.
- Processing order: raw tile inventory, void and NoData check, mosaic or clip if needed,
  reproject an analysis copy to the metric working CRS, then derive terrain layers with units
  recorded.
- For V1 terrain derivatives, the active reference raster is
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`.
  Later V1 terrain layers must match its CRS, transform, resolution, shape, band count, dtype,
  NoData value, and V1 valid-cell coverage before they can enter standardization or overlay.

### Rainfall Grid

- CHIRPS v3 is much coarser than SRTM terrain layers.
- Do not treat CHIRPS pixels as equivalent to 30 m terrain pixels.
- For the first prototype, use one of these safer options:
  1. aggregate CHIRPS to the selected catchment or sub-basin units;
  2. compute zonal rainfall summaries for the terrain-grid mask;
  3. keep CHIRPS at native resolution for diagnostics and report scale mismatch explicitly.
- Do not resample CHIRPS to 30 m for pixel-level overlay. If a future coarse rainfall
  visualization is approved, label it as a zonal or coarse-summary product, not as 30 m rainfall
  evidence.

### Model-Unit Branches

Choose one interpretation branch before combining rainfall and terrain:

1. Terrain-only raster screening: terrain-derived rasters may be overlaid on a 30 m working grid,
   while CHIRPS is reported as context or a separate tabular/zonal summary.
2. Sub-basin aggregation: terrain summaries and CHIRPS summaries are both aggregated to the same
   accepted catchment or sub-basin units before scoring.
3. Mixed product: terrain rasters and rainfall tables are reported separately, with no visual map
   implying that CHIRPS has 30 m detail.

Do not broadcast a catchment or sub-basin rainfall value across 30 m cells unless the output is
explicitly labelled as a coarse-summary overlay and the limitation is documented.

### Vector Hydrographic Units

- Use HydroBASINS or another approved boundary as mask and aggregation geometry.
- Record selected HydroBASINS level, basin id, and version before processing.
- If using an outlet-based catchment, record the outlet and delineation branch before processing.
- HydroRIVERS may support drainage-distance indicators, but it is not field-survey evidence.

## Resampling And Aggregation Rules

- Prefer aggregation or zonal summaries when source resolution differs strongly.
- Use nearest-neighbour resampling only for categorical or id layers.
- Use bilinear or average-style resampling only for continuous analysis copies when the method is
  documented.
- Do not mix resampled and native layers without recording which layers were transformed.
- Preserve raw source files unchanged and write all transformed analysis copies under `outputs/`.

Aggregation records must include:

- statistic type, such as mean, median, maximum, count, or area-weighted mean;
- boundary inclusion rule, such as center-point inclusion or area-weighted overlap;
- valid-cell coverage fraction and NoData fraction per unit;
- partial-pixel or edge-cell handling;
- minimum acceptable coverage threshold, or a documented waiver if coverage is lower;
- whether results are suitable for scoring or only for diagnostics.

## NoData And Mask Rules

- Treat NoData as a first-class preprocessing property, not as a normal numeric value.
- If a source uses a sentinel such as `-9999` without a NoData tag, record the override before
  standardization.
- Standardized rasters should preserve missing cells as floating NoData.
- Overlay inputs must use a shared validity mask or explicitly document why masks differ.
- Any cell missing from one required criterion must remain missing in the weighted-overlay score.

## Diagnostics Before Overlay

Run diagnostics before a raster is allowed into overlay:

- single-band check;
- CRS presence;
- transform, resolution, width, and height;
- NoData metadata or override;
- per-raster issue list;
- grid compatibility against the chosen reference;
- output path and processing command record.
- for V1 terrain derivatives, compatibility with
  `context/docs/data-management/v1_terrain_reference_grid_rule.md`.

For the first real-data run, attach or summarize diagnostics in the internal handoff before
interpreting any map output.

Overlay is blocked unless:

- every raster overlay input is single-band;
- CRS is present and compatible with the selected model-unit branch;
- transform, resolution, width, and height match for pixel-level raster overlay;
- NoData is recorded either as metadata or an explicit override;
- per-raster issues are empty, or each issue has a documented waiver;
- CHIRPS handling follows the selected model-unit branch.

## Standardization Rules

- Use fixed bounds when indicators must remain comparable across time, sub-basins, or countries.
- Use inferred min-max bounds only for a controlled single-slice diagnostic run.
- Record whether higher standardized values mean higher hazard or susceptibility contribution.
- Use the `--invert` rule only when lower raw values should become higher standardized scores.
- Record clipping counts and input min/max from the standardization diagnostics.

## Output And Handoff Rules

- Raw downloads stay under `data/raw/<dataset_id>/`.
- Temporary downloads stay under `data/tmp/<dataset_id>/`.
- Processed rasters, vector outputs, maps, and diagnostics stay under `outputs/`.
- Public-safe release packages must not depend on root `context/`, `data/`, or `outputs/`.
- Internal handoff notes may summarize source links and diagnostics, but must not copy raw data.

## Minimum First Real-Data Run

The smallest defensible first run should include:

1. one approved outlet-based boundary or approved proxy mask;
2. one SRTM-derived terrain layer;
3. one rainfall summary handled through the selected model-unit branch;
4. raster diagnostics for every produced raster input;
5. standardization diagnostics for every overlay input;
6. a statement that the output is workflow or preliminary susceptibility only.

## Open Decisions

- Exact outlet location/rationale and boundary source or HydroBASINS level/local catchment source.
- Raster-first versus sub-basin aggregation as the first interpretation unit.
- CHIRPS temporal window, timestep, and aggregation method.
- Whether the first real output should remain diagnostics only or include preliminary
  susceptibility.
- Validation evidence hierarchy before any model-quality claim.
