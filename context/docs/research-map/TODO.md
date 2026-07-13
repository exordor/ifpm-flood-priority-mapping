# TODO

Status: active. Backlog, in-progress, and next steps.

> **Operating mode (2026-07-06):** this project runs on autonomous default
> decisions, not on questions to the mentor. The HiWi makes methodological
> choices with documented defaults, builds the artifact, labels it with the
> appropriate claim level, and shows the result. If the mentor wants something
> different, he will say so when he sees the artifact. Do not gate forward
> progress on "ask the mentor first" — that is not how this project moves.
> Items below that used to be phrased as mentor questions are now recorded as
> the default that was taken or will be taken.
>
> **Current mainline (2026-07-13):** D-PERU-FIRST. Complete Peru first. Zimbabwe
> remains secondary/background until stronger Zimbabwe evidence or a later
> comparison question reopens it.

## In progress

- **PERU-FIRST briefing closure** — assemble the governed Peru source figures
  into one integrated mentor-facing board and add the data-strength table. The
  raw-factor panel, five criterion maps, direct-weight PIM, mining/population
  context overlay, contribution map, and SINPAD diagnostic already exist under
  `outputs/peru_report_figure_chain/current/`. The reporting result uses only
  the Peru mentor direct weights. Keep the language `prototype` /
  `provisional` / `sensitivity_scenario`, not final rescue decision.
- **Evidence-strength closure** — expose the remaining limitations directly on
  the board: provisional PE1 boundary, coarse CHIRPS effective resolution,
  composite sediment implementation, provisional infrastructure blend, 3.83%
  unscored area, and no independent flood-extent validation.

## Default decisions taken (was "awaiting mentor")

The former P1/P2 decision packages (IFPM-061..070, full text in
`context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/`)
were framed as questions for the mentor. In practice the project has been making
the calls autonomously and showing results. The defaults now in effect:

| id | topic | default taken | claim level |
|---|---|---|---|
| IFPM-D01 | Modelling unit | pixel-raster on the 30 m reference grid, with zonal summaries when needed | provisional |
| IFPM-D02 | Peru boundary | PE1 southern Peru comparison catchment in Arequipa Region; replaced only if mentor names a site | provisional |
| IFPM-D03 | Validation evidence | SINPAD point context is available for co-location diagnosis; independent flood-extent validation is unavailable | diagnostic_only |
| IFPM-D04 | AHP weights | Peru direct mentor weights are the reporting scenario; equal weights remain internal QA only; Zimbabwe direct weights are secondary; old slide matrix stays historical/background | sensitivity_scenario |
| IFPM-D05 | Mining + Rehabilitation | mining = OSM/INGEMMET indicator; Rehabilitation Potential = deferred (not built until a use is needed) | diagnostic_only |
| IFPM-D06 | Upper Mzingwane boundary | V1 — Upper Mzingwane catchment (~3689 km²); accepted with waiver for prototype | provisional |

If the mentor sees a result and wants a different choice, the project adapts
then. The packages stay archived as the analysis behind each default.

## Backlog

### Peru-first immediate backlog

- Compose the final Peru-only integrated briefing board from the governed
  figure chain; do not regenerate or substitute ungoverned legacy figures.
- Add a Peru data-strength table that separates stronger evidence
  (SRTM terrain, CHIRPS rainfall context, WorldCover, INGEMMET mining) from
  weaker or provisional evidence (coarse rainfall, composite sediment,
  environmental context, socioeconomic implementation, sparse SINPAD points).
- Rebuild or replace the independent Peru K-factor layer before applying the
  mentor K/LS/C sediment subweights directly; until then, keep sediment as the
  current `K x LS x C` composite criterion.
- Calibrate or replace the provisional infrastructure implementation. The
  supplied 0.45 road/access + 0.55 infrastructure split is implemented, but
  the current value functions produce 94.4% realized road influence and only
  5.6% infrastructure influence.
- Seek independent flood extent or impact evidence if a validation claim is
  required. SINPAD points remain a co-location diagnostic, not validation.
- Prepare a short mentor-facing explanation: final product is a prototype flood
  prioritisation map, not a flood-hazard-only map and not a validated rescue
  decision map.
- Confirm or replace the provisional PE1 boundary before any final study-area
  claim.

### Completed Peru briefing inputs

- Five PIM criterion maps: Flood, Sediment, Land Use / ASM, Environmental,
  and Socioeconomic.
- Peru direct-weight prioritisation map with plain five-class legend.
- INGEMMET mining and population-context overlay; 11 source records collapse
  to 6 unique locations, with 2 inside and 4 near the boundary.
- Largest weighted-contribution map and SINPAD co-location diagnostic.
- One authoritative current figure chain plus source/package checksums; legacy
  report surfaces and QA panels archived.

### Deferred secondary work

- **IFPM-097** Zimbabwe-Peru comparison pack — archived after D-PERU-FIRST;
  historical background only.
- **IFPM-089** Zimbabwe weakest-criteria hardening — reopen only if Zimbabwe
  returns as a main case or stronger ASM/exposure data arrives.
- Zimbabwe still needs stronger ASM evidence, independent infrastructure
  exposure, and a grid-compatible independent K-factor for a stronger claim.

### General engineering backlog

- IFPM-030: add dataset manifest schema for download records.
- IFPM-031: add optional downloader helpers with explicit output directories only.
- IFPM-032: add raster standardization config format.
- IFPM-033: add validation-event ingest design for EM-DAT, DFO, Copernicus EMS,
  or GloFAS.
- IFPM-034: add sensitivity-analysis utilities for AHP weights.
- IFPM-035: add public-safe technical docs for the minimal pipeline.
- IFPM-036: build a small dashboard or report view after approved sample data
  exists.
- IFPM-037: add fixed-threshold class configuration for comparison-safe maps.
- IFPM-038: add a first-slice AHP weighting protocol and sensitivity plan.
- IFPM-047: add official mining routes or verified active-disturbance evidence
  if needed after the terrain prototype.

## Verification plan for the current Peru handoff

- Run `bash bin/validate-boundary.sh`.
- Run `git diff --check`.
- Confirm the current package is generated only from
  `context/docs/research-map/peru_authoritative_figure_chain.csv`.
- Confirm source/package checksums match in
  `outputs/peru_report_figure_chain/manifest.csv`.
- Confirm no raw data are copied into `context/` or `ifpm-flood-pipeline/`.
- Confirm archived report surfaces are not recreated in active output paths.
- Run adversarial review:
  - Domain/correctness: check whether provisional evidence is overstated.
  - Engineering/data-governance: check output locations, registry needs, and
    public-safe boundary.

## Next implementation step

Create the Peru-only integrated briefing board and its data-strength table from
the governed figure chain. Do not reopen Zimbabwe comparison, R-factor,
Rehabilitation Potential, or dashboard work for this deliverable.

## Verification Gates (binding)

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

- No private context, raw/derived GIS data, credentials, local paths, or
  unresolved assumptions.
- Public-safe docs do not depend on `../context`, `../data`, or `../outputs`.
- Release package comes from `ifpm-flood-pipeline/`, not root `exports/`.

## Lineage

Absorbs content from:
- `task_progress_board.md` §Backlog, §In Progress, §Awaiting mentor decisions,
  §Verification Gates
- `boundary_v1_criteria_stack_v0_2_2026-06-29.md` §Verification Plan, §Next
  Implementation Step
- `july18_deliverable_scope_2026-07-02.md` §Out of scope, QA criteria
