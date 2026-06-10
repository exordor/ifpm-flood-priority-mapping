# IFPM Task Progress And Plan Board

Updated: 2026-06-10

Scope: private project planning for the IFPM comparative flood-risk modelling workspace.

## Current Position

The workspace now has a clean split between private context and deliverable code. The minimal
AHP-MCDA weighted-overlay pipeline exists, data-download governance is defined, and future work
should move from method scaffolding to a controlled data/preprocessing prototype.

Do not start broad data downloads yet. The next milestone is to run one small, traceable
prototype slice through data registration, preprocessing checks, standardization, and overlay.

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

- Status: not implemented
- Next action: define grid alignment, CRS, NoData, and standardization checks.

## Next

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

### IFPM-023 Implement Raster Grid Diagnostics

- Priority: P1
- Task: add checks for CRS, transform, resolution, shape, band count, and NoData.
- Completion evidence: tests and CLI/function diagnostics for valid and invalid rasters.

### IFPM-024 Implement Standardization Rules

- Priority: P1
- Task: start with synthetic rasters before real data.
- Completion evidence: tests proving normalized outputs and NoData preservation.

### IFPM-025 Run Synthetic Preprocessing-To-Overlay Smoke Test

- Priority: P2
- Task: run a full synthetic flow through preprocessing and overlay.
- Completion evidence: generated ignored outputs and diagnostics from synthetic inputs.

### IFPM-026 Prepare Mentor-Facing Next-Step Summary

- Priority: P2
- Task: summarize prototype scope, unresolved decisions, and validation plan.
- Completion evidence: short internal note ready to turn into mentor-facing text.

## Blocked Or Needs Decision

### IFPM-D01 Final Modelling Unit

- Decision needed: pixel, HydroBASINS/sub-basin, ANA hydrographic unit, or mixed mask.
- Why it matters: controls normalization, aggregation, and comparability.

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
