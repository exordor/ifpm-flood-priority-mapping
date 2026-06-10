# IFPM Task Progress And Plan Board

Updated: 2026-06-10

Scope: private project planning for the IFPM comparative flood-risk modelling workspace.

## Current Position

The workspace now has a clean split between private context and deliverable code. The minimal
AHP-MCDA weighted-overlay pipeline exists, data-download governance is defined, and future work
should move from method scaffolding to a controlled data/preprocessing prototype.

Do not start broad data downloads yet. HydroSHEDS boundary discovery has been executed for one
authorized artifact, but the boundary is not accepted. SRTM, CHIRPS, overlay, and interpretation
remain blocked until the later gates are closed.

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

- Status: draft decision created
- Next action: review `prototype_study_slice_decision.md` and confirm or revise the scope.

### IFPM-012 Raster Preprocessing Design

- Status: design drafted; real-data execution remains blocked until mentor decisions and
  preflight blockers are closed.
- Evidence: `context/docs/project-management/real_data_preprocessing_design.md`.
- Next action: use the execution preflight gate to close boundary, modelling-unit,
  temporal-window, and dataset-specific blockers before downloading or processing source data.

### IFPM-013 Real-Data Execution Preflight Gate

- Status: gate drafted; current verdict is `NO-GO` for general real data download, with only a
  completed HydroSHEDS boundary-discovery exception.
- Evidence: `context/docs/project-management/real_data_execution_preflight_gate.md`.
- Next action: resolve boundary acceptance by mentor/local boundary comparison or a documented
  HydroBASINS waiver; keep SRTM, CHIRPS, overlay, and interpretation blocked.

### IFPM-014 Multi-Level Progress Review

- Status: done; no P1 was found, but P2 gates remain before real-data overlay.
- Evidence: `context/docs/project-management/multi_level_progress_review_2026-06-10.md`.
- Next action: fix the boundary-discovery and engineering-readiness blockers recorded in the
  review report.

## Current Milestones And Gates

### IFPM-020 Select Prototype Study Slice

- Priority: P1
- Task: choose Zimbabwe or Peru, exact boundary rule, and output resolution.
- Status: draft decision created
- Completion evidence: accepted decision note with boundary source and resolution.

### IFPM-021 Create First Dataset Registry Notes

- Priority: P1
- Task: create registry notes for the first three selected datasets.
- Status: done for SRTM, HydroBASINS/HydroRIVERS, and CHIRPS v3.
- Completion evidence: three registry notes exist under `context/docs/data-management/registry/`.

### IFPM-022 Complete Download Preflight Checklists

- Priority: P1
- Task: complete the checklist for each selected dataset.
- Status: draft checklists created; downloads remain blocked pending unresolved items.
- Completion evidence: three preflight notes exist under `context/docs/data-management/preflight/`.

### IFPM-027 Close Real-Data Execution Gate

- Priority: P1
- Task: turn the consolidated preflight gate from `NO-GO` to a scoped `GO` for one dataset or
  one tiny prototype bundle.
- Status: partially closed for HydroSHEDS boundary discovery; general data download remains
  blocked by boundary acceptance, modelling-unit, rainfall-window, and engineering-readiness
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

- Decision needed: mentor/local boundary, HydroBASINS level 7 candidate, or reviewed level 8
  union.
- Why it matters: discovered HydroBASINS candidates are plausible but not accepted, and the
  strongest single candidate is larger than the commonly reported Upper Mzingwane area.

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
