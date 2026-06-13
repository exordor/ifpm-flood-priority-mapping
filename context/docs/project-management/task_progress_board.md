# IFPM Task Progress And Plan Board

Updated: 2026-06-13

Scope: private project planning for the IFPM comparative flood-risk modelling workspace.

## Current Position

The workspace now has a clean split between private context and deliverable code. The minimal
AHP-MCDA weighted-overlay pipeline exists, data-download governance is defined, and future work
should move from method scaffolding to a controlled data/preprocessing prototype.

Do not start broad data downloads yet. HydroSHEDS boundary discovery has been executed for one
authorized artifact, and the Zimbabwe Geoportal Sub-Catchments alternative has been downloaded
and compared for boundary evidence. Mentor feedback now reframes the next step: define the study
catchment from the flood/mining-relevant outlet instead of choosing only between existing named
boundaries. V1 / `HB_L8_1081528840_full_l7_chain` is now
`accepted_with_waiver_for_controlled_prototype` after the mentor gave a thumbs-up reaction to the
evidence board. The V1 working boundary package, SRTM tile preflight, scoped SRTM raw-tile
download/inventory, V1 DEM/slope preprocessing, raster grid gate, terrain-only standardization
diagnostics, CHIRPS rainfall comparison, and full methodology evidence sweep are complete.
Model overlay, flood-risk interpretation, and intervention interpretation remain blocked.

## Done

### IFPM-001 Workspace Boundary Split

- Status: done
- Evidence: root context repo and independent `ifpm-flood-pipeline/` repo are separated.

### IFPM-002 Dataset Inventory Review

- Status: done
- Evidence: reviewed inventory and fact-check notes exist under `context/docs/research-review/`
  and `context/docs/deep-research/`.

### IFPM-003 Mentor Explanation Package

- Status: done
- Evidence: English and Chinese mentor explanation guides exist under
  `context/docs/mentor-explanation/`.

### IFPM-004 Minimal AHP-Overlay Pipeline

- Status: done
- Evidence: `ifpm-flood-pipeline` commit `d2af7a4` implements AHP weights, CR checks,
  GeoTIFF overlay, tests, and CLI.

### IFPM-005 Data Download Governance

- Status: done
- Evidence: root commit `f88a758` adds download registry templates, checklist, and AGENTS rules.

### IFPM-006 Post-Implementation Review Rule

- Status: done
- Evidence: AGENTS now requires adversarial review and hardening after non-trivial
  implementation.

### IFPM-010 Project Task Board

- Status: done
- Evidence: this task progress board exists under `context/docs/project-management/`.

## In Progress

### IFPM-011 First Controlled Data Slice

- Status: V1 accepted with waiver for controlled prototype use; scoped SRTM raw-tile download and
  inventory, DEM/slope preprocessing, grid gate, and terrain-only standardization diagnostics are
  complete.
- Next action: decide whether the next controlled slice is mentor-facing terrain explanation,
  modelling-unit selection, or rainfall preflight. Keep overlay and interpretation blocked.

### IFPM-012 Raster Preprocessing Design

- Status: design drafted; real-data execution remains blocked until mentor decisions and
  preflight blockers are closed.
- Evidence: `context/docs/project-management/real_data_preprocessing_design.md`.
- Next action: use the execution preflight gate to close outlet, boundary, modelling-unit,
  temporal-window, and dataset-specific blockers before downloading or processing source data.

### IFPM-013 Real-Data Execution Preflight Gate

- Status: gate revised; scoped SRTM raw-tile download, inventory, DEM/slope preprocessing, grid
  gate, and terrain-only standardization diagnostics are complete. Current verdict remains
  `NO-GO` for CHIRPS, overlay, and interpretation.
- Evidence: `context/docs/project-management/real_data_execution_preflight_gate.md`.
- Next action: choose the modelling-unit branch and decide whether rainfall should stay as
  native-resolution/zonal summary context. Keep CHIRPS, overlay, and interpretation blocked until
  their own gates are closed.

### IFPM-014 Multi-Level Progress Review

- Status: done; no P1 was found, but P2 gates remain before real-data overlay.
- Evidence: `context/docs/project-management/multi_level_progress_review_2026-06-10.md`.
- Next action: fix the boundary-discovery and engineering-readiness blockers recorded in the
  review report.

## Current Milestones And Gates

### IFPM-020 Select Prototype Study Slice

- Priority: P1
- Task: choose Zimbabwe or Peru, exact boundary rule, and output resolution.
- Status: done for controlled prototype boundary; final thesis boundary remains open.
- Completion evidence:
  `context/docs/project-management/v1_working_boundary_decision_2026-06-12.md`.

### IFPM-021 Create First Dataset Registry Notes

- Priority: P1
- Task: create registry notes for the first three selected datasets.
- Status: done for SRTM, HydroBASINS/HydroRIVERS, and CHIRPS v3.
- Completion evidence: three registry notes exist under `context/docs/data-management/registry/`.

### IFPM-022 Complete Download Preflight Checklists

- Priority: P1
- Task: complete the checklist for each selected dataset.
- Status: SRTM preflight ready for V1; CHIRPS remains blocked pending temporal/model-unit choices.
- Completion evidence: three preflight notes exist under `context/docs/data-management/preflight/`.

### IFPM-027 Close Real-Data Execution Gate

- Priority: P1
- Task: turn the consolidated preflight gate from `NO-GO` to a scoped `GO` for one dataset or
  one tiny prototype bundle.
- Status: scoped SRTM tile planning, download, and raw inventory completed against V1. General
  data download remains blocked by modelling-unit, rainfall-window, and engineering-readiness
  blockers.
- Completion evidence: updated gate record plus selected dataset preflight note with no
  unchecked pre-download blocking item.

### IFPM-029 Prepare HydroSHEDS Boundary Discovery

- Priority: P1
- Task: make candidate HydroBASINS ids a discovery output and prepare the non-executed download
  authorization.
- Status: done before execution; superseded by IFPM-039.
- Completion evidence:
  `context/docs/data-management/preflight/hydrosheds_boundary_discovery_authorization_2026-06-10.md`
  and updated HydroSHEDS registry/preflight notes.

### IFPM-039 Execute HydroSHEDS Boundary Discovery

- Priority: P1
- Task: download the authorized HydroBASINS standard Africa artifact and identify candidate
  HYBAS/PFAF ids without running SRTM, CHIRPS, overlay, or map interpretation.
- Status: done; boundary not accepted.
- Completion evidence:
  `context/docs/project-management/hydrosheds_boundary_discovery_result_2026-06-10.md`.

### IFPM-040 Prepare Upper Mzingwane Boundary Decision Package

- Priority: P1
- Task: convert HydroBASINS discovery output into a mentor-facing decision package and internal
  decision record without accepting a boundary or running real-data overlay.
- Status: done; superseded as the active next-step framing by IFPM-044 outlet-based catchment
  planning after mentor feedback.
- Completion evidence:
  `context/docs/mentor-explanation/Upper_Mzingwane_Boundary_Decision_Package_2026-06-10.md`
  and `context/docs/project-management/upper_mzingwane_boundary_decision_record_2026-06-10.md`.

### IFPM-041 Execute Zimbabwe Geoportal Sub-Catchments Boundary Comparison

- Priority: P1
- Task: use the authenticated Zimbabwe Geoportal Sub-Catchments dataset as the first alternative
  local named-boundary check, without downloading SRTM/CHIRPS or running overlay.
- Status: done; boundary still not accepted.
- Completion evidence:
  `context/docs/project-management/zimbabwe_geoportal_subcatchments_boundary_comparison_2026-06-10.md`,
  `context/docs/data-management/registry/zimbabwe_geoportal_subcatchments_2025.md`, and
  `context/docs/data-management/preflight/zimbabwe_geoportal_subcatchments_2025.md`.
- Key result: the Geoportal `Upper Mzingwane` polygon contains Mzingwane Dam and Esigodini and
  excludes Gwanda, but its area is about `7321.5 km2`. HydroBASINS level 7
  `HYBAS_ID=1071528840` is nearly contained within it but covers only about `49.8%` of the
  Geoportal named feature.

### IFPM-042 Fact-Check Upper Mzingwane Area References

- Priority: P1
- Task: verify whether the `~2138 km2` Upper Mzingwane area reference has external support and
  whether it supplies usable boundary geometry.
- Status: done; area reference is reported but source/geometry-unresolved.
- Completion evidence:
  `context/docs/project-management/upper_mzingwane_boundary_fact_check_2026-06-10.md`.
- Key result: external sources support `~2138 km2`, but no checked source supplied a reusable GIS
  boundary, outlet point, projection, or area method. Boundary acceptance remains blocked.

### IFPM-043 Trace Upper Mzingwane 2138 km2 Boundary Source

- Priority: P1
- Task: find whether the `~2138 km2` Upper Mzingwane value traces to a public boundary file,
  official water-management GIS source, feasibility-study map, or author-held study-area polygon.
- Status: done for public-source hunt; boundary still not accepted.
- Completion evidence:
  `context/docs/project-management/upper_mzingwane_boundary_source_hunt_2026-06-10.md`.
- Key result: modern papers repeatedly report or use the `~2138 km2` study area but do not expose
  reusable geometry. The strongest source leads are ZINWA's unpublished National catchment
  database, older Bulawayo/Matabeleland-Zambezi feasibility-study maps, Surveyor General map
  channels, or an author-requested study-area polygon.
- Next action: request the actual polygon/source citation from authors, ZINWA, mentor, or the
  feasibility-study/map holders before accepting any boundary or downloading SRTM/CHIRPS.

### IFPM-044 Reframe Prototype As Outlet-Based Catchment

- Priority: P1
- Task: revise the research plan after mentor feedback so the first prototype uses an
  outlet-based catchment definition instead of choosing only between existing named boundaries.
- Status: done as planning update; superseded by V1 working boundary waiver.
- Completion evidence:
  `context/docs/project-management/outlet_based_catchment_research_plan_2026-06-11.md`,
  revised `context/docs/project-management/prototype_study_slice_decision.md`, and revised
  `context/docs/project-management/real_data_execution_preflight_gate.md`.
- Key result: `Upper Mzingwane` is now treated as the regional context, while the operational
  prototype boundary should be the upstream catchment of a mentor-selected or mentor-provisional
  flood/mining-relevant outlet.
- Next action: continue using V1 only under the prototype waiver; do not treat it as the final
  thesis boundary.

### IFPM-045 Candidate Outlet Discovery First Pass

- Priority: P1
- Task: generate provisional outlet and catchment candidates from existing local HydroBASINS and
  Zimbabwe Geoportal data, without accepting a boundary or downloading SRTM/CHIRPS.
- Status: done for first pass; needs domain validation and optional river/flood/mining evidence.
- Completion evidence:
  `context/docs/project-management/candidate_outlet_exploration_2026-06-11.md`,
  `bin/discover_candidate_outlets.py`, and local ignored outputs under
  `outputs/candidate_outlet_discovery/`.
- Key result: `HB_L8_1081522660_literature_near` was the first script-ranked machine prior with
  area about `1879.9 km2`; after the 2026-06-12 mentor cue it is no longer the primary
  recommendation.
- Next action: use professional map evidence and the mentor's Level-8 downstream-to-Gwanda cue to
  review V1 / `HB_L8_1081528840_full_l7_chain`.

### IFPM-046 Candidate Outlet Diagnostic Figure Upgrade

- Priority: P1
- Task: upgrade the candidate outlet diagnostic outputs so a non-GIS reader can understand why
  C1-C7 are outlet proxies and how `target_id -> NEXT_DOWN` encodes flow direction.
- Status: done for explanation package; C1 later demoted by mentor-driven visual review and
  boundary still not accepted.
- Completion evidence:
  `bin/export_candidate_topology.py`, revised `bin/plot_candidate_outlets.py`,
  `outputs/candidate_outlet_discovery/diagnostic_map_explained.png`,
  `outputs/candidate_outlet_discovery/diagnostic_c1_flow_explainer.png`,
  `outputs/candidate_outlet_discovery/diagnostic_topology_table.png`, and
  `outputs/candidate_outlet_discovery/candidate_topology_edges.csv`.
- Key result: the package separates overview, C1 flow/topology explanation, and topology table
  views. It explicitly labels all C-points as outlet proxies, not measured outlets or accepted
  thesis boundaries.
- Next action: keep these figures as machine-prior diagnostics only; use IFPM-048 for the
  mentor-facing visual evidence package.

### IFPM-048 Professional Map Visual Outlet Review

- Priority: P1
- Task: use professional map evidence to interpret the mentor cue: Level-8 basin containing
  Mzingwane Dam and the main Mzingwane River channel downstream toward Gwanda.
- Status: done for mentor-review evidence package; V1 accepted with waiver for controlled
  prototype use, but final thesis boundary still not accepted.
- Completion evidence:
  `context/docs/project-management/professional_map_outlet_review_2026-06-12.md`,
  `bin/prepare_outlet_review_sources.py`, `bin/compare_visual_outlets.py`,
  `bin/plot_professional_outlet_review.py`,
  `outputs/professional_outlet_review/mentor_outlet_evidence_board.png`, and
  `outputs/professional_outlet_review/visual_outlet_candidates.csv`.
- Key result: V1 / `HB_L8_1081528840_full_l7_chain` is now
  `accepted_with_waiver_for_controlled_prototype`. C1 /
  `HB_L8_1081522660_literature_near` is demoted to machine prior only.
- Evidence notes: HydroRIVERS, Geofabrik OSM, and Geoportal Rivers were downloaded and clipped;
  Geoportal Flood Prone Zones has zero features intersecting the review envelope.
- Next action: use IFPM-049/050 outputs as the input to the next SRTM download authorization.

### IFPM-049 V1 Working Boundary Package

- Priority: P1
- Task: export the V1 working boundary, manifest, anchor check, and diagnostic map without
  downloading DEM or running overlay.
- Status: done; prototype-only waiver, not final thesis boundary.
- Completion evidence:
  `bin/export_v1_working_boundary.py`,
  `context/docs/project-management/v1_working_boundary_decision_2026-06-12.md`,
  `outputs/v1_working_boundary/v1_working_boundary.gpkg`,
  `outputs/v1_working_boundary/v1_working_boundary_manifest.csv`,
  `outputs/v1_working_boundary/v1_anchor_check.csv`, and
  `outputs/v1_working_boundary/v1_boundary_diagnostic.png`.
- Key result: V1 area remains about `3689.484 km2`; Mzingwane Dam and Esigodini are inside V1,
  while Gwanda, Filabusi approx, and West Nicholson approx are outside.
- Next action: use V1 as the mask for the scoped SRTM download step only.

### IFPM-050 SRTM Tile Preflight For V1

- Priority: P1
- Task: compute SRTM tile names from the V1 boundary plus 5 km buffer, without downloading data.
- Status: done for pre-download planning; superseded by IFPM-051.
- Completion evidence:
  `bin/plan_srtm_tiles_for_v1.py`,
  `outputs/v1_working_boundary/srtm_v1_tile_plan.csv`,
  `outputs/v1_working_boundary/srtm_v1_tile_plan.gpkg`, and
  `outputs/v1_working_boundary/srtm_v1_preflight_summary.md`.
- Key result: planned bbox EPSG:4326 is
  `28.514098, -21.007996, 29.398052, -19.984062`; planned tiles are `S22E028`,
  `S22E029`, `S21E028`, `S21E029`, `S20E028`, and `S20E029`.
- Next action: superseded by IFPM-051.

### IFPM-051 SRTM V1 Download And Raw Inventory

- Priority: P1
- Task: download only the six approved SRTMGL1 tiles, record source file evidence, compute
  checksums, and verify raw raster metadata without deriving terrain indicators.
- Status: done for raw download and inventory; no terrain preprocessing or overlay was run.
- Completion evidence:
  `bin/download_srtm_v1_tiles.py`,
  `bin/inventory_srtm_v1_tiles.py`,
  `context/docs/project-management/srtm_v1_download_and_inventory_2026-06-12.md`,
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`,
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_inventory.csv`, and
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_coverage_check.png`.
- Key result: six ZIP archives were downloaded from the ESA STEP SRTMGL1 mirror without login,
  totaling `41,162,741` bytes. Each tile opens as `SRTMHGT`, `EPSG:4326`, `3601 x 3601`, one
  `int16` band, NoData `-32768`.
- Next action: plan and execute a separate terrain preprocessing step only after recording metric
  CRS, mosaic/clip rule, void/NoData handling, and output diagnostics.

### IFPM-052 SRTM V1 Terrain Preprocessing

- Priority: P1
- Task: convert the downloaded SRTM raw tiles into V1 DEM and slope diagnostic rasters without
  hydrological conditioning, rainfall, overlay, or interpretation.
- Status: done for DEM, QA hillshade visualization, and slope diagnostics.
- Completion evidence:
  `bin/preprocess_srtm_v1_dem.py`,
  `bin/derive_srtm_v1_slope.py`,
  `bin/plot_srtm_v1_terrain_qa.py`,
  `context/docs/project-management/srtm_v1_terrain_preprocessing_2026-06-12.md`, and
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_terrain_preprocessing_diagnostics.csv`.
- Key result: final DEM and slope rasters are `EPSG:32735`, `30 m`, single-band `float32`, NoData
  `-9999.0`, and both have `1.0` valid-cell fraction inside V1. DEM elevation ranges from about
  `863.0` to `1531.5 m`; slope ranges from `0.0` to `55.6 degrees`.
- Next action: implement or run a V1 raster-grid gate before using terrain derivatives in any
  standardization or score.

### IFPM-053 V1 Terrain Reference Grid Rule

- Priority: P1
- Task: fix the V1 terrain raster compatibility rule in a saved project file so later terrain
  derivatives cannot silently drift from the V1 DEM grid.
- Status: done as an internal rule; no new data downloaded and no overlay run.
- Completion evidence:
  `context/docs/data-management/v1_terrain_reference_grid_rule.md`.
- Key result: the current V1 DEM is the only reference raster for V1 terrain derivatives.
  Overlay is blocked unless candidate terrain rasters match its CRS, transform, resolution,
  shape, band count, dtype, NoData, and V1 valid-cell coverage. CHIRPS is explicitly excluded
  from pixel-level 30 m terrain-grid overlay.
- Next action: add or run `bin/check_v1_raster_grid.py` before any future V1 standardization,
  scoring, or weighted overlay.

### IFPM-054 V1 Raster Grid Gate

- Priority: P1
- Task: implement the executable gate that checks V1 terrain rasters against the fixed reference
  DEM before any standardization, scoring, or overlay.
- Status: done for current final V1 DEM and slope rasters.
- Completion evidence:
  `bin/check_v1_raster_grid.py` and
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_raster_grid_check.csv`.
- Key result: the final V1 DEM and final V1 slope are `grid_compatible=true`. A buffered-DEM
  failure probe correctly failed on transform, width, height, and bounds mismatch.
- Next action: decide terrain standardization rules for elevation and slope before any scoring or
  weighted overlay. CHIRPS remains excluded from the 30 m terrain-grid overlay path.

### IFPM-055 V1 Terrain Standardization Diagnostics

- Priority: P1
- Task: generate terrain-only 0-1 diagnostic candidates from the V1 DEM and slope rasters after
  the raster grid gate, without CHIRPS, AHP weights, overlay, or interpretation.
- Status: done for prototype diagnostic candidates.
- Completion evidence:
  `bin/standardize_v1_terrain.py`,
  `context/docs/project-management/v1_terrain_standardization_rule_2026-06-13.md`, and
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_terrain_standardization_diagnostics.csv`.
- Key result: elevation lowland context, low-slope susceptibility, and high-slope runoff-pressure
  candidates were produced with 2nd-98th percentile min-max scaling and passed the V1 raster grid
  gate.
- Next action: decide whether the mentor-facing terrain explanation should use low-slope
  susceptibility, high-slope runoff pressure, or keep both as alternatives before any AHP criteria
  hierarchy or overlay work.

### IFPM-056 V1 Terrain Mentor Package

- Priority: P1
- Task: convert terrain-only standardized diagnostics into a mentor-facing figure board, caption,
  evidence table, and handoff without adding CHIRPS, AHP weights, overlay, or interpretation.
- Status: done for mentor review package.
- Completion evidence:
  `bin/plot_v1_terrain_mentor_package.py`,
  `context/docs/project-management/v1_terrain_mentor_package_2026-06-13.md`, and
  `outputs/v1_terrain_mentor_package/mentor_v1_terrain_diagnostic_board.png`.
- Key result: the package presents lowland context, low-slope susceptibility, and high-slope
  runoff-pressure alternative as terrain-only diagnostic candidates. The low-slope layer is the
  primary mentor-review candidate; high-slope runoff pressure is retained as an alternative.
- Next action: send the board and short question to the mentor before choosing a terrain criterion
  direction for any future AHP criteria hierarchy.

### IFPM-057 V1 Multi-Criteria Evidence Package

- Priority: P1
- Task: combine existing terrain, river/flood context, exposure, mining proxy, and rainfall
  readiness/gap evidence into a mentor-facing criteria review package without CHIRPS download,
  AHP weights, overlay, or interpretation.
- Status: done for first mentor review package.
- Completion evidence:
  `bin/prepare_v1_multicriteria_evidence.py`,
  `bin/plot_v1_multicriteria_evidence_board.py`,
  `context/docs/project-management/v1_multicriteria_evidence_package_2026-06-13.md`, and
  `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_evidence_board.png`.
- Key result: the evidence package covers terrain, hydro/flood context, exposure, mining proxy,
  and rainfall readiness. Rainfall is marked as a CHIRPS preflight gap, Geoportal Flood Prone
  Zones have zero local overlap, and OSM quarry/industrial features are labelled weak proxy
  mining evidence.
- Next action: ask the mentor which evidence families should enter the first prototype criteria
  set before any AHP hierarchy, CHIRPS processing, or overlay.

### IFPM-058 V1 CHIRPS Rainfall Comparison

- Priority: P1
- Task: process multiple CHIRPS rainfall definitions for the V1 working catchment and compare
  annual background, rainy-season accumulation, anomaly, monthly peak, pentad peak, and one
  daily RNL-derived peak without choosing a final rainfall criterion.
- Status: done for mentor-review sensitivity package.
- Completion evidence:
  `bin/plan_chirps_v1_rainfall_metrics.py`,
  `bin/download_chirps_v1_rainfall_inputs.py`,
  `bin/compare_chirps_v1_rainfall_metrics.py`,
  `bin/plot_chirps_v1_rainfall_comparison.py`,
  `context/docs/project-management/chirps_v1_rainfall_comparison_2026-06-13.md`,
  and
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/mentor_v1_chirps_rainfall_comparison_board.png`.
- Key result: 561 scoped CHIRPS inputs were downloaded or clipped, all readable at `EPSG:4326`
  and about `0.05 degree`. V1 recent annual and rainy-season anomaly are both about `17.5%`,
  while pentad peak has a much different spatial pattern from long-term annual rainfall.
- Next action: ask the mentor whether rainfall should enter the first prototype criteria set as
  background climate, rainy-season accumulation, recent anomaly, monthly/pentad extreme, daily
  sensitivity only, or context only. Keep AHP weights, 30 m CHIRPS resampling, weighted overlay,
  flood-risk interpretation, and intervention-priority mapping blocked.

### IFPM-059 V1 Full Methodology Evidence Sweep

- Priority: P1
- Task: process every methodology factor into comparable candidate evidence rows and supporting
  layers without creating AHP weights, weighted overlay, flood-risk maps, or intervention maps.
- Status: done for mentor-review evidence package.
- Completion evidence:
  `bin/download_v1_methodology_inputs.py`,
  `bin/prepare_v1_full_methodology_evidence.py`,
  `bin/prepare_v1_methodology_raster_layers.py`,
  `bin/prepare_v1_methodology_vector_layers.py`,
  `bin/build_v1_full_methodology_evidence_matrix.py`,
  `bin/plot_v1_full_methodology_evidence.py`,
  `context/docs/project-management/v1_full_methodology_evidence_sweep_2026-06-13.md`,
  `context/docs/project-management/v1_full_methodology_adversarial_review_2026-06-13.md`, and
  `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_evidence_matrix.csv`.
- Key result: the matrix now covers flood hazard, rainfall, terrain, land use / ASM,
  environmental sensitivity, socioeconomic vulnerability, and rehabilitation potential. New
  processed evidence includes ESA WorldCover, WorldPop, GHSL built-up/population, JRC Global
  Surface Water, DFO Zimbabwe-level historical flood context, and WDPCA Zimbabwe
  protected/conserved areas.
- Next action: use the matrix and separated panels to ask the mentor which evidence families are
  eligible for the first prototype criteria set. Keep AHP weights, overlay, flood-risk
  interpretation, and intervention-priority mapping blocked.

### IFPM-028 Close Pre-Real-Data Engineering Readiness

- Priority: P1
- Task: make the synthetic-tested pipeline safe enough for controlled real-data overlay.
- Status: blocked by a durable geospatial verification target, finite-value diagnostics, 0-1
  overlay input enforcement, mask-loss reporting, and model-unit branch executability.
- Completion evidence: geospatial verification is documented as a required pre-real-data command
  with no required GeoTIFF tests skipped, overlay enforces standardized inputs, and diagnostics
  expose value/mask readiness.

### IFPM-023 Implement Raster Grid Diagnostics

- Priority: P1
- Task: add checks for CRS, transform, resolution, shape, band count, and NoData.
- Status: done in deliverable code.
- Completion evidence: `ifpm-flood-pipeline` commit `81c14e8` adds raster diagnostics,
  CLI support, and tests.

### IFPM-024 Implement Standardization Rules

- Priority: P1
- Task: start with synthetic rasters before real data.
- Status: done in deliverable code.
- Completion evidence: `ifpm-flood-pipeline` commit `758dd10` adds min-max standardization,
  NoData preservation, diagnostics, CLI support, and tests.

### IFPM-025 Run Synthetic Preprocessing-To-Overlay Smoke Test

- Priority: P2
- Task: run a full synthetic flow through preprocessing and overlay.
- Status: done in deliverable code.
- Completion evidence: `ifpm-flood-pipeline` commit `f21fb77` adds a synthetic
  preprocessing-to-overlay smoke test and output profile regression checks.

### IFPM-026 Prepare Mentor-Facing Next-Step Summary

- Priority: P2
- Task: summarize prototype scope, unresolved decisions, and validation plan.
- Status: done as internal draft.
- Completion evidence:
  `context/docs/mentor-explanation/Mentor_Next_Step_Summary_IFPM_2026-06-10.md`.

## Blocked Or Needs Decision

### IFPM-D01 Final Modelling Unit

- Decision needed: pixel, HydroBASINS/sub-basin, ANA hydrographic unit, or mixed mask.
- Why it matters: controls normalization, aggregation, and comparability.

### IFPM-D06 Upper Mzingwane Boundary Acceptance

- Decision needed: final thesis boundary remains open. For controlled prototype work, V1 /
  `HB_L8_1081528840_full_l7_chain` is accepted with waiver. C1 /
  `HB_L8_1081522660_literature_near` is now only a machine prior. Geoportal named sub-catchment,
  HydroBASINS level 7 candidate, a reviewed HydroBASINS union, or the narrower `~2138 km2`
  literature boundary remain comparison/proxy options.
- Why it matters: the outlet controls the operational catchment. The plausible comparison
  boundaries are not equivalent: HydroBASINS level 7 is about `3700 km2`; Geoportal `Upper
  Mzingwane` is about `7321.5 km2`; the reported but source/geometry-unresolved `~2138 km2`
  reference still needs outlet, area-method, and boundary-geometry tracing.
- Current evidence: HydroBASINS discovery, Geoportal boundary comparison, literature fact-check,
  public source hunt, mentor feedback, the 2026-06-11 candidate outlet first pass, the
  2026-06-12 professional map review, mentor thumbs-up acknowledgement, V1 working boundary
  package, SRTM tile preflight, SRTM raw-tile inventory, and V1 DEM/slope preprocessing completed.
  CHIRPS, overlay, and interpretation remain blocked.

### IFPM-D02 Peru Boundary Rule

- Decision needed: administrative regions, hydrographic units, or clipped hydrological units.
- Why it matters: avoids catchment-versus-region bias.

### IFPM-D03 Validation Evidence Hierarchy

- Decision needed: which evidence can support validation or calibration.
- Why it matters: determines whether outputs are susceptibility, risk, or intervention maps.

### IFPM-D04 AHP Weighting Protocol

- Decision needed: who supplies expert pairwise comparisons and how CR is reviewed.
- Why it matters: prevents arbitrary weights.

### IFPM-D05 Mining-Data Interpretation Rule

- Decision needed: how to separate concessions, cadastre records, and active disturbance.
- Why it matters: avoids treating mining rights as active mining footprints.

## Backlog

- IFPM-030: add dataset manifest schema for download records.
- IFPM-031: add optional downloader helpers with explicit output directories only.
- IFPM-032: add raster standardization config format.
- IFPM-033: add validation-event ingest design for EM-DAT, DFO, Copernicus EMS, or GloFAS.
- IFPM-034: add sensitivity-analysis utilities for AHP weights.
- IFPM-035: add public-safe technical docs for the minimal pipeline.
- IFPM-036: build a small dashboard or report view after approved sample data exists.
- IFPM-037: add fixed-threshold class configuration for comparison-safe maps.
- IFPM-038: add a first-slice AHP weighting protocol and sensitivity plan.
- IFPM-047: add official mining routes or verified active-disturbance evidence if needed after
  the terrain prototype.

## Verification Gates

Before data download:

- Dataset registry note exists.
- Download preflight checklist is complete.
- Target path is ignored by Git.
- Licence/account constraints are documented.

Before code handoff:

- Tests pass.
- Ruff check and format check pass where applicable.
- Adversarial review findings are triaged.
- Parent workspace boundary check passes.

Before any public release:

- No private context, raw/derived GIS data, credentials, local paths, or unresolved assumptions.
- Public-safe docs do not depend on `../context`, `../data`, or `../outputs`.
- Release package comes from `ifpm-flood-pipeline/`, not root `exports/`.
