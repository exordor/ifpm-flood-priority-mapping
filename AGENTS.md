# AGENTS.md

## Workspace Role

This workspace is for IFPM flood-risk modelling context, mentor-review preparation,
dataset-inventory review, and future pipeline development.

Current migration state: `POST_MIGRATION`.

- Root repository: private context and document repository.
- `context/`: internal documents, review notes, meeting support, generated images, and
  background material.
- `ifpm-flood-pipeline/`: independent deliverable code repository with a minimal
  synthetic-tested pipeline; real-data use remains gated.

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

## Data Download Management

Treat every real dataset download as `LOCAL_DATA` unless it is only a public-safe source link or
metadata note.

Before downloading real GIS, raster, vector, validation, or sample data:

- Confirm the destination is under `data/`, not `context/` or `ifpm-flood-pipeline/`.
- Use a stable dataset id and a subdirectory such as `data/raw/<dataset_id>/`,
  `data/validation/<dataset_id>/`, or `data/tmp/<dataset_id>/`.
- Record at least a minimal public-safe or internal registry note under
  `context/docs/data-management/` for every real download. Mark whether it is reusable. Include
  source URL or portal, product/version, access date, licence or account requirements, study
  area, intended use, download command or manual steps, expected destination, and checksum or
  file-size evidence after download.
- For large, authenticated, rate-limited, paid, or licence-constrained downloads, confirm scope,
  disk footprint, and access constraints before starting.
- Never store credentials, cookies, API tokens, private cloud links, or local absolute paths in
  committed files.
- Keep partial downloads, archives, temporary extraction folders, and failed attempts under
  ignored `data/tmp/` or `tmp/` paths, then clean or label them before handoff.
- Store processed maps, model outputs, and diagnostics under `outputs/`, not `data/raw/`.
- Store packaged local handoff bundles under ignored root `exports/`. Treat root `exports/` as
  private/local-only unless release approval is explicit.
- Public release packages must come from `ifpm-flood-pipeline/` after the public-safe gate and
  must not depend on root `context/`, `data/`, `outputs/`, or private `exports/` contents.
- Do not copy downloaded real data into `ifpm-flood-pipeline/`, `context/`, public docs,
  examples, configs, or release archives unless release permission is explicit.

## Public-Safe Gate

Files in `ifpm-flood-pipeline/README.md`, `ifpm-flood-pipeline/docs_public/`,
`ifpm-flood-pipeline/examples/`, `ifpm-flood-pipeline/configs/`, or release archives must
contain no:

- private mentor-meeting strategy
- unresolved modelling unknowns presented as facts
- unconfirmed assumptions as commitments
- raw or derived confidential GIS data
- local absolute paths
- private cloud links or credentials
- dependency on parent workspace files such as `../context`, `../data`, or `../outputs`

If internal context is needed for public docs, rewrite it into a public-safe summary instead of
copying private notes.

## Modelling Context

Treat the current project as an exploratory flood-risk modelling workflow, not a finalized model
specification.

Key recurring open questions:

- modelling unit and spatial resolution
- time period and validation windows
- validation data availability
- final dataset selection and replacement rules
- GIS preprocessing readiness
- AHP-MCDA criteria hierarchy, weighting protocol, and consistency checks
- rehabilitation-potential and mining-pressure criteria

Prefer concrete checklists, traceable dataset links, and conservative claim boundaries.

## Post-Implementation Adversarial Review

After each non-trivial implementation in this workspace, run an adversarial review loop before
declaring the work complete.

- Inspect the current worktree first; use current files and command output as authoritative.
- Use subagents for code or pipeline implementation when available. Prefer at least two
  independent review angles: correctness/domain assumptions and engineering/boundary
  maintainability.
- If subagents are unavailable, perform the same adversarial review locally and state the
  fallback in the handoff.
- Ask reviewers for severity-ranked findings with concrete file/line references, failure modes,
  and suggested fixes.
- Triage findings before handoff. Fix P1/P2 issues unless explicitly blocked or deliberately
  deferred with a documented reason.
- Strengthen tests, fixtures, validation commands, or public-safe documentation for each fixed
  issue when practical.
- Re-run the relevant tests, format/lint checks, and workspace boundary checks after fixes.
- Keep generated local data, outputs, virtual environments, and caches ignored or cleaned before
  handoff.

## Git Rules

- Confirm the repository root before staging or committing.
- The root context repository must not stage `ifpm-flood-pipeline/`, a gitlink, or `.gitmodules`.
- Keep root context commits and deliverable code commits separate.
- Do not run destructive cleanup from the root. Avoid `git clean -xfd` in this workspace unless
  explicitly requested and exclusions are reviewed.
- Raw data, outputs, exports, and generated binary files stay ignored unless explicitly approved.
