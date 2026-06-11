# Real-Data Execution Preflight Gate

Updated: 2026-06-11

Status: internal gate record. Current verdict: `NO-GO` for general real data download.

Two real vector artifacts have been downloaded only for boundary discovery and comparison:
HydroBASINS Standard Africa and Zimbabwe Geoportal Sub-Catchments. No SRTM, CHIRPS, validation
data, overlay input, map output, or interpretation dataset has been downloaded or processed for
this gate.

## Purpose

This record turns the first Zimbabwe / Upper Mzingwane prototype blockers into a single
go/no-go gate. It sits above the dataset-specific registry and preflight notes, so a reviewer can
decide whether the project is ready to start controlled real-data download.

The gate is deliberately conservative. Passing it authorizes only a small, traceable prototype
download. It does not authorize broad mirroring, public release, final model claims, or
Zimbabwe-Peru comparison.

## Scope Controlled By This Gate

- Study side: Zimbabwe.
- Working study area: outlet-based catchment within the Upper Mzingwane context, or an approved
  proxy boundary if the outlet cannot yet be fixed.
- Candidate datasets: SRTM 1 Arc-Second, HydroBASINS/HydroRIVERS, and CHIRPS v3.
- First output: workflow diagnostics and, only if later approved, preliminary susceptibility.
- Excluded for this gate: mining pressure, socioeconomic vulnerability, rehabilitation
  potential, Peru-side processing, and validation-event ingestion.

## Current Verdict

The project is not ready for general real data download, overlay, or interpretation yet.

There are two narrow boundary-only exceptions:

- the HydroBASINS boundary-discovery download was authorized and executed after the HydroSHEDS
  preflight note, expected size, and download authorization entry were completed;
- the Zimbabwe Geoportal Sub-Catchments download was authorized and executed after its dataset
  registry, preflight note, and authenticated page inspection were completed.

These exceptions support boundary selection only. They do not authorize SRTM download, CHIRPS
download, overlay, or map interpretation.

Current boundary-discovery status: executed for the authorized HydroBASINS artifact and the
authorized Zimbabwe Geoportal Sub-Catchments artifact. Candidate HYBAS and PFAF ids were
discovered. The Geoportal layer added a named `Upper Mzingwane` feature, but no boundary has
been accepted.

- Outlet and boundary acceptance: blocked.
  Mentor feedback reframed the boundary decision around the catchment near a flood/mining-relevant
  outlet. HydroBASINS, Geoportal, and the reported but source/geometry-unresolved `~2138 km2`
  reference are now comparison layers until the outlet-based catchment is defined.
  Evidence: `real_data_preprocessing_design.md`.
- Modelling unit: blocked.
  Raster-first, sub-basin aggregation, or mixed workflow is not selected.
  Evidence: `real_data_preprocessing_design.md`.
- Rainfall time window: blocked.
  CHIRPS temporal window, timestep, and product type are not selected.
  Evidence: CHIRPS preflight note.
- Dataset preflight: partly closed.
  HydroSHEDS boundary-discovery and Zimbabwe Geoportal Sub-Catchments comparison have been
  executed, while SRTM and CHIRPS remain blocked. Boundary acceptance still needs a documented
  decision or waiver.
  Evidence: `context/docs/data-management/preflight/`.
- Storage boundary: ready.
  Raw, temporary, output, and export destinations are defined and ignored.
  Evidence: AGENTS rules and preflight notes.
- Processing design: ready as draft.
  Grid, CRS, aggregation, NoData, and diagnostics rules are drafted.
  Evidence: `real_data_preprocessing_design.md`.

## Gate G1: Outlet And Boundary Acceptance

Required before SRTM download, CHIRPS download, overlay, or aggregation:

- record the selected or provisional outlet / pour point;
- document why the outlet is relevant to flood impact and mining pressure;
- choose the boundary source or delineation method: outlet-based catchment, Geoportal named
  sub-catchment, HydroBASINS-compatible unit, mentor-supplied local boundary, or a traced
  published-study boundary;
- record HydroBASINS level, HYBAS id, PFAF id, and version if HydroBASINS is used;
- record whether multiple units are unioned or dissolved;
- check geometry validity and CRS;
- compare area and shape against any available authoritative, Geoportal, HydroBASINS, or
  mentor-supplied boundary;
- state the mismatch policy if candidate boundary sources disagree;
- mark the boundary as accepted, rejected, or accepted with waiver.

Exit evidence:

- a short boundary decision note or a completed section in this file;
- a candidate outlet table with source/rationale;
- exact raw destination remains under `data/raw/<dataset_id>/`;
- no boundary file is copied into `context/` or `ifpm-flood-pipeline/`.

Current state: blocked. HydroBASINS and Geoportal boundary-only comparisons are complete, but
the outlet has not been selected and their areas/modelling scopes are not reconciled.

Boundary-only exceptions already executed:

- HydroBASINS boundary discovery:
  - allowed only for HydroBASINS candidate inspection;
  - required the HydroSHEDS preflight checklist to have no unchecked pre-download blocker except
    final accepted boundary id and post-download verification fields;
  - required exact archive names, expected size, licence source, and overwrite confirmation;
  - treated candidate HYBAS and PFAF ids as discovery outputs;
  - wrote only to `data/raw/hydrosheds_zimbabwe_prototype/` or
    `data/tmp/hydrosheds_zimbabwe_prototype/`;
  - produced no public-facing output and no model claim.
- Zimbabwe Geoportal Sub-Catchments comparison:
  - allowed only for local named-boundary comparison;
  - required the Geoportal registry and preflight note to be completed before download;
  - required page-level source, version, licence, expected size, and destination evidence;
  - treated `Upper Mzingwane` name, anchor containment, area, and HydroBASINS overlap as
    comparison outputs;
  - wrote raw files only to `data/raw/zimbabwe_geoportal_subcatchments_2025/` and diagnostics
    only to `outputs/zimbabwe_geoportal_subcatchments_2025/`;
  - produced no public-facing output and no model claim.

## Gate G2: Modelling Unit

Select one branch before combining terrain and rainfall:

1. Terrain-only raster screening with CHIRPS reported as context or a separate summary.
2. Sub-basin aggregation with terrain and CHIRPS summarized to the same accepted units.
3. Mixed product with terrain rasters and rainfall tables reported separately.

The first branch is simplest for testing raster diagnostics. The second branch is more coherent
for combining CHIRPS and terrain, but it depends on the boundary acceptance gate. The third branch
is safest when scale mismatch remains unresolved.

Exit evidence:

- selected branch and rationale;
- statement of whether any pixel-level overlay is allowed;
- statement that CHIRPS will not be treated as 30 m information.

Current state: blocked.

## Gate G3: Temporal Window And Rainfall Product

Required before CHIRPS download:

- choose the first rainfall window, such as one event month, one rainy season, or a multi-year
  climatology;
- choose timestep, with monthly or annual preferred for the first small prototype;
- choose final or preliminary product;
- record the expected file count and expected byte size before download;
- decide whether CHIRPS is aggregated to catchment/sub-basin units or kept as diagnostics only.

Exit evidence:

- updated CHIRPS preflight note with checked temporal-window and product-type items;
- selected artifact names or manual download steps;
- expected size judged acceptable.

Current state: blocked.

## Gate G4: Dataset-Specific Preflight Closure

Before any individual dataset download, its preflight note must have no unchecked pre-download
blocking item.

Current blockers:

- SRTM: boundary mask or bounding box, expected disk footprint, and overwrite confirmation.
- HydroSHEDS: boundary-discovery download and inspection are complete. Boundary acceptance,
  comparison against Geoportal, and redistribution clearance remain open.
- Zimbabwe Geoportal Sub-Catchments: boundary-comparison download and inspection are complete.
  Boundary acceptance and redistribution clearance remain open.
- CHIRPS: temporal window, product type, timestep, expected disk footprint, and overwrite
  confirmation.

Exit evidence:

- all pre-download blocking checklist items are checked or explicitly waived;
- waiver explains risk and reviewer approval;
- command or manual workflow cannot overwrite unrelated local data.

Current state: blocked.

## Gate G5: Download Authorization Record

Immediately before a real download, create a short authorization entry in the dataset registry
or preflight note with:

- dataset id;
- source URL or portal;
- exact source artifact names;
- expected file count and byte size;
- intended raw destination under `data/raw/<dataset_id>/`;
- temporary destination under `data/tmp/<dataset_id>/` if needed;
- output destination under `outputs/<dataset_id>/`;
- licence or account constraints confirmed for this attempt;
- download command or manual steps;
- operator/date;
- statement that credentials, cookies, tokens, and private links are not recorded.

After download, add:

- actual file count and size;
- checksum or file-size evidence;
- partial or failed-download disposition;
- CRS, georeferencing, and integrity check state.

Current state: ready as a required template for remaining datasets. The HydroSHEDS
boundary-discovery and Zimbabwe Geoportal Sub-Catchments exceptions used their own authorization
records.

## Gate G6: Execution Rules After Download

After a controlled download succeeds:

- keep raw files unchanged under `data/raw/<dataset_id>/`;
- write transformed analysis copies and diagnostics under `outputs/`;
- run grid diagnostics before standardization or overlay;
- use a shared validity mask for pixel overlay, or document why masks differ;
- block interpretation if CRS, transform, resolution, shape, band count, or NoData checks fail
  without waiver;
- label any output as workflow or preliminary susceptibility only.

Current state: ready as a draft rule set.

## Gate G7: Pre-Real-Data Engineering Readiness

Before any real-data overlay, scoring, or interpretation:

- run deliverable tests with geospatial dependencies installed and record whether GeoTIFF tests
  were executed or skipped;
- require raster diagnostics to expose finite-value and mask summaries, or record a waiver for a
  diagnostic-only run;
- require overlay inputs to be standardized 0-1 rasters by default, or record an explicit
  experimental override;
- report per-layer valid-cell fractions and intersection mask loss before interpreting an
  overlay output;
- confirm the selected model-unit branch is executable in code. A sub-basin CHIRPS branch needs a
  zonal or tabular scoring path, not only same-grid raster overlay.

Current state: blocked for real-data overlay. Boundary discovery and metadata-only inspection can
proceed only under their own gate rules.

## Go Criteria

General real-data download may proceed only when all of these are true:

- Gate G1 boundary acceptance is complete.
- Gate G2 modelling unit is selected.
- Gate G3 CHIRPS temporal/product decision is complete, or CHIRPS is explicitly deferred.
- Gate G4 selected dataset preflight has no unchecked pre-download blocker.
- Gate G5 authorization entry is written before download.
- Gate G7 engineering readiness is complete before overlay or interpretation.
- The target dataset directory is under ignored `data/`.
- The reviewer confirms the download is small and scoped.

The completed HydroSHEDS and Zimbabwe Geoportal downloads remain boundary-selection steps, not
modelling runs.

## No-Go Triggers

Stop before download if any of these appears:

- boundary acceptance remains unknown for SRTM, CHIRPS, overlay, or interpretation;
- expected size is unknown or too large for a prototype;
- licence, account, or redistribution rules are unclear for the intended use;
- command would write outside `data/` or overwrite unrelated local files;
- selected artifact names are not recorded;
- the workflow would imply CHIRPS has 30 m spatial detail;
- real-data overlay would run without the Gate G7 engineering readiness checks;
- credentials, cookies, tokens, or private cloud links would be written to a committed file.

## Immediate Next Action

Close the smallest useful decision set:

1. ask the mentor for the rough flood/mining-relevant outlet location or downstream impact point;
2. record candidate outlet evidence and select an outlet-based delineation branch;
3. use
   `context/docs/project-management/upper_mzingwane_boundary_fact_check_2026-06-10.md`
   and
   `context/docs/project-management/zimbabwe_geoportal_subcatchments_boundary_comparison_2026-06-10.md`
   as comparison context, not as automatic boundary choices;
4. choose the initial modelling branch;
5. choose whether CHIRPS is deferred or limited to one small rainfall summary window;
6. update the affected dataset preflight notes from `not ready` to either `ready` or
   `blocked with waiver`.

Until those steps are complete, the correct state remains `NO-GO`.
