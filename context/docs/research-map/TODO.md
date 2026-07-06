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

## In progress

- **IFPM-089** V1 v0.2 weakest-criteria hardening — first inventory complete;
  hotspot comparison and revised maps not yet implemented. Next: compare v0.1
  stable hotspots against road-river crossings, OSM places, GHSL/WorldPop native
  summaries, and mining proxy without calling the comparison validation.
- **IFPM-097** July 18 Mentor/Boss Comparison Pack — package generated; final
  visual QA and send-pack selection with the user pending. Do not open new
  modelling work before this packet is reviewed.

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
| IFPM-D04 | AHP weights | slide matrix (CR 0.022) used as `sensitivity_scenario`; multiple weight scenarios run, hotspot stability reported | sensitivity_scenario |
| IFPM-D05 | Mining + Rehabilitation | mining = OSM/INGEMMET indicator; Rehabilitation Potential = deferred (not built until a use is needed) | diagnostic_only |
| IFPM-D06 | Upper Mzingwane boundary | V1 — Upper Mzingwane catchment (~3689 km²); accepted with waiver for prototype | provisional |

If the mentor sees a result and wants a different choice, the project adapts
then. The packages stay archived as the analysis behind each default.

## Backlog

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

Next: compare archived `criteria_stack_v0_1` stable hotspots against the
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
