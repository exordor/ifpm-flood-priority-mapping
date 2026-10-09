# IFPM Flood Risk Modelling Workspace

> New to this project? Start with [HANDOVER.md](HANDOVER.md) (Chinese handover
> note, 2026-10-08). It summarises the current state, directory map and next steps.

This workspace uses a split boundary:

- the root Git repository is the private context/document repository;
- `ifpm-flood-pipeline/` is an independent deliverable code repository with a minimal
  synthetic-tested pipeline. Real-data use remains gated.

The current project mainline is Peru-first flood prioritisation modelling. The
working Peru case is:

- **Secocha, Mariano Nicolas Valcarcel, Camana, Arequipa, Peru** — active under
  boundary id `peru_secocha_a7367_reference_extent_v1`. The current boundary is
  a provisional 30 km² reference window derived from the coordinate frame of
  INGEMMET A7367 Map 7; it is neither a hydrologic catchment nor the observed
  2023 debris-flow footprint.

The previous Vitor-La Joya-Santa Rita de Siguas / HydroBASINS area
`peru_hybas_l7_6070641200` is a frozen baseline. Its existing model outputs are
retained under `outputs/srtm_1arcsec_peru_pilot/` and must not receive new runs.

Goslar, Germany (Abzucht and the expanded multi-river comparison under
`outputs/goslar_multiriver_full_extent_v1/`) is the second active case since
September 2026; it compares the priority index with official flood zones.

Upper Mzingwane Catchment, Zimbabwe remains a secondary/background comparison
case and method-development baseline, but the active result sequence should now
lead with Peru.

## Directory Structure

```text
context/
  docs/
    research-map/         Research map: experiments, results, decisions, reproducibility, hypotheses.
    data-management/      Dataset registry: source, version, access date and licence per dataset.
    methodology/          PIM transformation flow (Chinese).
    mentor-explanation/   English handover draft and email draft for Supervisor.
    glossary.md           Terminology.
  configs/                Zimbabwe criteria-stack config read by bin/ scripts.

ifpm-flood-pipeline/
  src/                     Minimal deliverable pipeline code.
  tests/                   Tests for the code repository.
  configs/                 Public-safe sample configs.
  examples/                Synthetic or approved public examples.
  docs_public/             Client/mentor-facing technical docs.
```

## Document Navigation

- [Research overview](context/docs/research-map/RESEARCH_OVERVIEW.md): current scope and study area.
- [Research map](context/docs/research-map/README.md): experiments, results, decisions and reproducibility.
- [Data management](context/docs/data-management/README.md): dataset provenance, download checks and reference grids.
- [Terminology](context/docs/glossary.md).
- [Internal context](context/README.md): what is kept under `context/`.
- [Local tooling](bin/README.md): processing and verification entry points.

## Boundary Rules

- Keep exploratory notes, mentor-meeting preparation, dataset review, open modelling questions,
  and generated images under `context/`.
- Put future reusable code only under `ifpm-flood-pipeline/`.
- Do not make code depend on files in `context/`.
- Do not put private notes, mentor strategy, raw/derived GIS data, local paths, or unresolved
  assumptions into the deliverable code repository.
- Store raw data, processing outputs, and export packages under ignored local directories such
  as `data/`, `outputs/`, and `exports/`.

## Notes

- Markdown files are the version-managed source documents.
- Generated binary formats such as `.docx` and `.pdf` are ignored and can be exported again when
  the Markdown source is stable.
- The root repository should remain private. Release packages should come only from
  `ifpm-flood-pipeline/` after public-safe review.
