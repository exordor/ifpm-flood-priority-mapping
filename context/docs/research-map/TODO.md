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
> **Current mainline (2026-07-06):** D-PERU-FIRST. Complete Peru first. Zimbabwe
> remains secondary/background until stronger Zimbabwe evidence or a later
> comparison question reopens it.

## In progress

- **PERU-FIRST mainline** — build a Peru-only briefing sequence from the current
  PE1 data: input criteria maps, AHP prototype prioritisation map, top-priority
  class map, mining overlay, and data-strength table. Label outputs
  `prototype` / `provisional` / `sensitivity_scenario`, not final rescue
  decision products. Current weights are the Peru mentor direct table plus an
  equal-weight baseline.
- **IFPM-097** July 18 Mentor/Boss Comparison Pack — package generated and still
  useful as background, but no longer the active mainline after D-PERU-FIRST.
  Reuse its figures only when they support the Peru story.
- **IFPM-089** V1 v0.2 weakest-criteria hardening — paused as secondary
  Zimbabwe work. Reopen only if Zimbabwe returns as a main case or stronger
  Zimbabwe ASM/exposure data arrives.

## Default decisions taken (was "awaiting mentor")

The former P1/P2 decision packages (IFPM-061..070, full text in
`context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/`)
were framed as questions for the mentor. In practice the project has been making
the calls autonomously and showing results. The defaults now in effect:

| id | topic | default taken | claim level |
|---|---|---|---|
| IFPM-D01 | Modelling unit | pixel-raster on the 30 m reference grid, with zonal summaries when needed | provisional |
| IFPM-D02 | Peru boundary | PE1 southern Peru comparison catchment in Arequipa Region; replaced only if mentor names a site | provisional |
| IFPM-D03 | Validation evidence | none available; outputs stay at susceptibility/priority level, not validated risk | diagnostic_only |
| IFPM-D04 | AHP weights | Peru direct mentor weights are the current main scenario; Zimbabwe direct weights are implemented only for the secondary Zimbabwe run; equal weights remain baseline; old slide matrix stays historical/background | sensitivity_scenario |
| IFPM-D05 | Mining + Rehabilitation | mining = OSM/INGEMMET indicator; Rehabilitation Potential = deferred (not built until a use is needed) | diagnostic_only |
| IFPM-D06 | Upper Mzingwane boundary | V1 — Upper Mzingwane catchment (~3689 km²); accepted with waiver for prototype | provisional |

If the mentor sees a result and wants a different choice, the project adapts
then. The packages stay archived as the analysis behind each default.

## Backlog

### Peru-first immediate backlog

- Generate Peru five-main-criterion input maps:
  Flood, Sediment, Land Use / ASM, Environmental, Socioeconomic.
- Generate a Peru prioritisation map with plain priority classes
  (low / moderate / high / very high; red for high priority) using the current
  Peru direct mentor weights.
- Overlay INGEMMET small-mining points on the Peru priority classes and report
  overlap with high / very-high priority zones.
- Add a Peru data-strength table that separates stronger evidence
  (SRTM terrain, CHIRPS rainfall context, WorldCover, INGEMMET mining) from
  weaker indicators (road/access exposure, provisional environmental
  sensitivity, lack of flood-impact validation).
- Rebuild or replace the independent Peru K-factor layer before applying the
  mentor K/LS/C sediment subweights directly; until then, keep sediment as the
  current `K x LS x C` composite criterion.
- Add or source an independent infrastructure-exposure layer before applying
  the socioeconomic 0.45 road/access + 0.55 infrastructure split; until then,
  keep road/access proximity as the only implemented socioeconomic component.
- Prepare a short mentor-facing explanation: final product is a prototype flood
  prioritisation map, not a flood-hazard-only map and not a validated rescue
  decision map.
- Keep the secondary Zimbabwe run as background: it now uses direct Zimbabwe
  weights, but still needs stronger ASM evidence, independent infrastructure
  exposure, and a grid-compatible independent K-factor before it can support a
  stronger Zimbabwe-specific claim.

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

## Verification Plan (criteria_stack_v0_2)

- Run `bash bin/validate-boundary.sh`.
- Run `git diff --check`.
- Confirm new outputs are under ignored `outputs/boundary_v1/criteria_stack_v0_2/`.
- Confirm no raw data are copied into `context/` or `ifpm-flood-pipeline/`.
- Confirm archived `criteria_stack_v0_1` outputs remain unchanged unless
  explicitly rerun as baseline.
- Run adversarial review:
  - Domain/correctness: check whether weak proxy evidence is overstated.
  - Engineering/data-governance: check output locations, registry needs, and
    public-safe boundary.

## Next implementation step (criteria_stack_v0_2)

Inventory script implemented: `bin/package/prepare_boundary_v1_criteria_stack_v0_2_inventory.py`
(inspect existing local outputs; produce gap/upgrade tables for mining/ASM and
exposure; should not download, plot, or overlay).

Criteria repair script implemented:
`bin/criteria/build_boundary_v1_criteria_stack_v0_2.py` (read the v0.2 config,
build honest-label grid-compatible criteria rasters, preserve NoData, write a
NoData coverage report + small preview map).

Next: compare archived `criteria_stack_v0_1` repeatedly selected top-20% priority areas against the
`criteria_stack_v0_2` split criteria and inventory layers (`road_river_crossings_v1`,
OSM places, GHSL/WorldPop native summaries, mining proxy) without calling the
comparison validation.

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
