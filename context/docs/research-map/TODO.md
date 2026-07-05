# TODO

Status: active. Backlog, in-progress, awaiting-mentor, and next steps.

## In progress

- **IFPM-089** V1 v0.2 weakest-criteria hardening — first inventory complete;
  hotspot comparison and revised maps not yet implemented. Next: compare v0.1
  stable hotspots against road-river crossings, OSM places, GHSL/WorldPop native
  summaries, and mining proxy without calling the comparison validation.
- **IFPM-097** July 18 Mentor/Boss Comparison Pack — package generated; final
  visual QA and send-pack selection with the user pending. Do not open new
  modelling work before this packet is reviewed.

## Awaiting mentor decisions (gate-blocked)

The ten P1/P2 decision packages (IFPM-061..068) plus the compressed mentor
briefing (IFPM-069) and the data-processor scope split (IFPM-070) are all
`decision package complete; awaits mentor`. Full text lives in
`context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/`.

- **IFPM-061** P1 R1.1 Validation Data Decision Package — decision package and
  public-safe preflight scaffolding complete.
- **IFPM-062** P1 R1.2 Mining Data Decision Package — decision package and
  mentor request template complete.
- **IFPM-063** P1 R1.3 AHP Weighting Decision Package — partially advanced; a
  mentor-provided candidate matrix exists but is not yet authorised.
- **IFPM-064** P2 R2.1 Sediment Risk Decision Package — decision package and
  SoilGrids preflight scaffolding complete.
- **IFPM-065** P2 R2.2 Hydrology Derivatives Decision Package — hydrological-
  conditioning assumptions A1-A5 drafted.
- **IFPM-066** P2 R2.4 Modelling Unit Decision Package (IFPM-D01) — trade-off
  matrix and Branch-1 recommendation complete.
- **IFPM-067** P2 R2.3 Peru Side Decision Package — scope and data-holder
  inventory complete.
- **IFPM-068** P2 R2.5 Final Boundary Acceptance Decision Package — public-source
  hunt consolidated as exhausted.
- **IFPM-069** Mentor Decision Briefing (Compressed) — ~35 individual mentor
  questions compressed into eight dependency-ordered key decisions in three
  batches.
- **IFPM-070** Data-Processor Scope Split In Governance — complete.

## Highest-priority open questions (mentor)

1. **R-factor method for semi-arid Zimbabwe** (RQ1) — surface FIRST; it blocks
   USLE A re-derivation. Send only Figure 1 + Figure 2 from the verified R-factor
   send packet.
2. **AHP matrix authorisation** (IFPM-D04) — is the slide matrix the intended
   weight set?
3. **Rehabilitation Potential role** (IFPM-D05) — sixth criterion, post-score
   filter, or output?
4. **Final boundary acceptance** (IFPM-D06) — V1 promotion from waiver to final.
5. **Peru boundary rule** (IFPM-D02) — admin / hydrographic / clipped.

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
