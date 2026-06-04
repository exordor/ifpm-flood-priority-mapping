# AGENTS.md

## Workspace Role

This workspace is for IFPM flood-risk modelling context, mentor-review preparation, dataset-inventory review, and future pipeline development.

Current migration state: `POST_MIGRATION`.

- Root repository: private context and document repository.
- `context/`: internal documents, review notes, meeting support, generated images, and background material.
- `ifpm-flood-pipeline/`: independent future deliverable code repository.

## Write Classification

Before writing any file, classify it as one of:

- `INTERNAL_CONTEXT`: dataset reviews, mentor notes, open modelling questions, private reasoning.
- `DELIVERABLE`: reusable code, tests, public-safe configs, public-safe technical docs.
- `LOCAL_DATA`: raw GIS datasets, downloaded rasters/vectors, validation data, local samples.
- `OUTPUT`: processed maps, model outputs, reports, diagnostics.
- `EXPORT`: packaged deliverables.
- `TOOLING`: local helper scripts for this workspace.

Allowed locations:

- `INTERNAL_CONTEXT` -> `context/`
- `DELIVERABLE` -> `ifpm-flood-pipeline/`
- `LOCAL_DATA` -> `data/` unless explicitly approved otherwise
- `OUTPUT` -> `outputs/`
- `EXPORT` -> `exports/`
- `TOOLING` -> `bin/` or documented root tooling

## Public-Safe Gate

Files in `ifpm-flood-pipeline/README.md`, `ifpm-flood-pipeline/docs_public/`, `ifpm-flood-pipeline/examples/`, `ifpm-flood-pipeline/configs/`, or release archives must contain no:

- private mentor-meeting strategy
- unresolved modelling unknowns presented as facts
- unconfirmed assumptions as commitments
- raw or derived confidential GIS data
- local absolute paths
- private cloud links or credentials
- dependency on parent workspace files such as `../context`, `../data`, or `../outputs`

If internal context is needed for public docs, rewrite it into a public-safe summary instead of copying private notes.

## Modelling Context

Treat the current project as an exploratory flood-risk modelling workflow, not a finalized model specification.

Key recurring open questions:

- modelling unit and spatial resolution
- time period and validation windows
- validation data availability
- final dataset selection and replacement rules
- GIS preprocessing readiness
- AHP-MCDA criteria hierarchy, weighting protocol, and consistency checks
- rehabilitation-potential and mining-pressure criteria

Prefer concrete checklists, traceable dataset links, and conservative claim boundaries.

## Git Rules

- Confirm the repository root before staging or committing.
- The root context repository must not stage `ifpm-flood-pipeline/`, a gitlink, or `.gitmodules`.
- Keep root context commits and deliverable code commits separate.
- Do not run destructive cleanup from the root. Avoid `git clean -xfd` in this workspace unless explicitly requested and exclusions are reviewed.
- Raw data, outputs, exports, and generated binary files stay ignored unless explicitly approved.
