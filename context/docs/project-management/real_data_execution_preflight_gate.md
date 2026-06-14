# Real-Data Execution Preflight Gate

Updated: 2026-06-13

Status: internal gate record, revised 2026-06-15 to separate the HiWi data-processing scope from
the mentor/thesis claim scope. Scoped SRTM download, raw inventory, and V1 DEM/slope preprocessing
are complete; scoped CHIRPS rainfall-sensitivity comparison is complete; the deliverable
pipeline's Gate G7 engineering readiness is closed (`ifpm-flood-pipeline` commit `39f6b33`); the
deliverable pipeline's synthetic GeoTIFF fixtures are grid-compliant (`ifpm-flood-pipeline` commit
`6269451`).

## Scope: Data Production vs Interpretable Claim

This gate was originally written as if data production and claim-making were the same activity.
They are not. This section separates them so the HiWi (data processor) is not blocked by
thesis-level decisions that are the mentor's responsibility.

**Data production** (HiWi scope; proceeds with documented defaults; not blocked by this gate
unless a dataset-specific preflight is incomplete):

- downloading public datasets that have a closed registry + preflight + Gate G5 authorization;
- preprocessing, mosaicking, reprojecting, clipping, void-filling;
- deriving terrain, hydrology, sediment-factor, and land-use indicators from already-downloaded
  data;
- standardizing layers to 0-1 with a documented rule;
- producing diagnostic overlays and sensitivity runs with documented synthetic or placeholder
  weights, clearly labelled as non-interpretable diagnostics;
- generating diagnostics, figures, and handoff tables.

Data-production outputs must be labelled as workflow/diagnostic products and must not be
presented as interpretable flood-risk or intervention-priority findings. They are inputs FOR the
mentor and any future modeller, not claims.

**Interpretable claim** (mentor / thesis scope; remains gated by this gate and by the P1/P2
decision packages):

- asserting that an output is a validated flood-risk map;
- presenting priority classes as intervention priorities;
- publishing, presenting, or comparing results as project findings;
- treating synthetic-weight outputs as if they had expert authority;
- making Zimbabwe-Peru comparison claims.

The HiWi does not make claims. The HiWi produces defensible, documented data products and hands
them to the mentor. Thesis-level decisions (minimum viable thesis, validation requirement,
criteria hierarchy acceptance, boundary promotion to final, Peru scope) are the mentor's calls
and do not block data production. Where a data-processing default is needed (for example a
hydro-conditioning algorithm or a USLE formula), the HiWi selects a standard method, documents
the choice and its trade-offs in the processing note, produces the output, and flags any
methodological sensitivity for the mentor's awareness. The gates below (G1-G7) apply to
interpretable claims and to dataset-specific download authorization, not to the production of
diagnostic data products from already-authorized data.

Two real vector artifacts have been downloaded only for boundary discovery and comparison:
HydroBASINS Standard Africa and Zimbabwe Geoportal Sub-Catchments. One scoped SRTM raw-tile
download and a DEM/slope preprocessing run have now been completed for V1 terrain diagnostics
only. A scoped CHIRPS rainfall-sensitivity package has also been completed as native-grid/V1
summary evidence only. No validation data, overlay input, flood-risk map, or interpretation
dataset has been downloaded or processed for this gate.

A first candidate outlet discovery run was completed on 2026-06-11 using only those existing
local vector artifacts. It produced provisional outlet/catchment candidates but did not accept a
boundary or authorize downstream modelling.

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

Per the scope split above: **data production is GO** for already-authorized public datasets and
for deriving diagnostic products from already-downloaded data, using documented defaults.
**Interpretable claims remain NO-GO** (validated flood-risk map, intervention priority,
Zimbabwe-Peru comparison, public release) until the relevant mentor decisions close.

The 30 m CHIRPS resampling rule is a binding data-quality rule (not a claim) and stays in force
regardless of scope: CHIRPS must not be resampled to the V1 30 m terrain grid as pixel-level
evidence.

The project is not ready for broad bulk download or for interpretable claims yet.

The project has completed one narrow terrain chain: six SRTMGL1 raw tiles were downloaded,
inventoried, mosaicked, reprojected, clipped to V1, and converted into DEM/slope diagnostics. The
next terrain-related step must choose modelling-unit and standardization rules, not overlay or
interpretation.

There are two narrow boundary-only exceptions:

- the HydroBASINS boundary-discovery download was authorized and executed after the HydroSHEDS
  preflight note, expected size, and download authorization entry were completed;
- the Zimbabwe Geoportal Sub-Catchments download was authorized and executed after its dataset
  registry, preflight note, and authenticated page inspection were completed.

These exceptions support boundary selection only. The later SRTM exception supports terrain
diagnostics only. The scoped CHIRPS comparison supports rainfall sensitivity review only. None of
these exceptions authorize model overlay, flood-risk interpretation, or intervention-map
interpretation.

Current boundary-discovery status: executed for the authorized HydroBASINS artifact and the
authorized Zimbabwe Geoportal Sub-Catchments artifact. Candidate HYBAS and PFAF ids were
discovered. The Geoportal layer added a named `Upper Mzingwane` feature, but no final boundary has
been accepted. The 2026-06-12 professional map review recommends V1 /
`HB_L8_1081528840_full_l7_chain` because it better matches the mentor's Level-8
downstream-to-Gwanda cue, and the mentor later gave a thumbs-up reaction to the V1 evidence board.
Treat V1 as `accepted_with_waiver_for_controlled_prototype`. The earlier C1 /
`HB_L8_1081522660_literature_near` is demoted to a machine-derived topology prior only.

- Outlet and boundary acceptance: closed only for controlled prototype terrain diagnostics, still
  blocked for final thesis boundary acceptance.
  Mentor feedback reframed the boundary decision around the catchment near a flood/mining-relevant
  outlet. V1 is now the working candidate with prototype-only waiver. HydroBASINS, Geoportal, and
  the reported but source/geometry-unresolved `~2138 km2` reference remain comparison layers for
  final-boundary discussion.
  Evidence: `v1_working_boundary_decision_2026-06-12.md`.
- Modelling unit: blocked.
  Raster-first, sub-basin aggregation, or mixed workflow is not selected.
  Evidence: `real_data_preprocessing_design.md`.
- Rainfall time window: closed for comparison, not final criterion selection.
  Multiple CHIRPS temporal windows and timesteps were processed for sensitivity comparison.
  The rainfall criterion, modelling unit, and overlay role are still unselected.
  Evidence: CHIRPS preflight note and `chirps_v1_rainfall_comparison_2026-06-13.md`.
- Dataset preflight: partly closed.
  HydroSHEDS boundary-discovery and Zimbabwe Geoportal Sub-Catchments comparison have been
  executed. SRTM tile preflight, download, raw inventory, and V1 DEM/slope preprocessing are
  complete for the V1 working boundary. CHIRPS is closed only for native-grid/V1-summary
  rainfall comparison. The V1 direction has a prototype-only waiver, but final-boundary
  acceptance remains open.
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

Current state: closed with waiver for controlled prototype SRTM terrain diagnostics only.

- Working boundary: V1 / `HB_L8_1081528840_full_l7_chain`.
- Decision status: `accepted_with_waiver_for_controlled_prototype`.
- Evidence:
  `context/docs/project-management/v1_working_boundary_decision_2026-06-12.md`.
- Outputs:
  `outputs/v1_working_boundary/v1_working_boundary.gpkg`,
  `outputs/v1_working_boundary/v1_working_boundary_manifest.csv`, and
  `outputs/v1_working_boundary/v1_anchor_check.csv`.

Final boundary acceptance remains open. The waiver does not authorize 30 m CHIRPS resampling,
overlay, flood-risk interpretation, or intervention-priority interpretation.

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

Current state: blocked for combining terrain and rainfall; CHIRPS comparison is available only
as native-grid diagnostics and V1 summaries.

## Gate G3: Temporal Window And Rainfall Product

Required before CHIRPS download or processing:

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

Current state: closed for the scoped rainfall-sensitivity package, not closed for final rainfall
criterion selection or overlay.

## Gate G4: Dataset-Specific Preflight Closure

Before any individual dataset download, its preflight note must have no unchecked pre-download
blocking item.

Current blockers:

- SRTM: raw-tile download, inventory, and V1 DEM/slope preprocessing are complete; scoring-ready
  terrain standardization is not started.
- HydroSHEDS: boundary-discovery download and inspection are complete. Boundary acceptance,
  comparison against Geoportal, and redistribution clearance remain open.
- Zimbabwe Geoportal Sub-Catchments: boundary-comparison download and inspection are complete.
  Boundary acceptance and redistribution clearance remain open.
- CHIRPS: scoped comparison download and native/zonal diagnostics complete. Final rainfall
  criterion, modelling-unit integration, and overlay role remain blocked.

Exit evidence:

- all pre-download blocking checklist items are checked or explicitly waived;
- waiver explains risk and reviewer approval;
- command or manual workflow cannot overwrite unrelated local data.

Current state: closed for the scoped SRTM raw-tile download and scoped CHIRPS comparison; still
blocked for AHP overlay, 30 m CHIRPS resampling, flood-risk interpretation, and intervention
interpretation.

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

Current state: used for the scoped SRTM raw-tile download and ready as a required template for
remaining datasets. The HydroSHEDS boundary-discovery and Zimbabwe Geoportal Sub-Catchments
exceptions used their own authorization records.

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

Current state: the five engineering-readiness items are closed (`ifpm-flood-pipeline` commit
`39f6b33` -- durable geospatial verification target with 0 skipped GeoTIFF tests, finite-value/mask
diagnostics, 0-1 overlay-input enforcement with explicit override, per-layer mask-loss reporting,
and a zonal scoring branch; 36 -> 51 tests passing, 0 skipped). Real-data overlay, scoring, and
interpretation remain blocked pending mentor decisions on modelling unit (Gate G2), criteria, and
final boundary; the pipeline is now executable for a controlled run once those close. Boundary
discovery and metadata-only inspection can proceed only under their own gate rules.

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

## Immediate Next Action (Data-Processor Scope)

Produce the next diagnostic data products from already-downloaded data, documenting the chosen
defaults in a processing note (not a mentor decision package):

1. derive V1 hydrology products (flow direction, flow accumulation, drainage network, stream
   order, TWI, distance-to-drainage) from the existing V1 DEM, using documented standard
   defaults (sink-fill method, D8, channel threshold, edge handling); record the choices and
   their trade-offs in the processing note;
2. derive V1 LS factor from the conditioned DEM and flow accumulation;
3. compute V1 R-factor from existing CHIRPS using a documented modified-Fournier rule, at native
   grid or as a V1 zonal summary (not resampled to 30 m);
4. produce a C-factor proxy from existing ESA WorldCover using a documented lookup table;
5. for each output, run the V1 raster grid gate and write diagnostics under `outputs/`.

None of the above requires mentor sign-off, because none produces an interpretable claim. Each
produces a labelled diagnostic data product for the mentor. Mentor-gated items (mining data
access, expert AHP weights, boundary promotion to final thesis boundary, validation tier,
Peru scope, publication) proceed on their own track and do not block data production.

Until the relevant mentor decisions close, the correct state remains `NO-GO` for interpretable
claims only; diagnostic data production proceeds.
