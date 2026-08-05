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

## Default Experiment Worker Mode

Default operating mode in this workspace is `EXPERIMENT_WORKER`.

Unless the user explicitly asks for brainstorming, explanation, review-only feedback, or mentor
wording only, every non-trivial task should produce at least one concrete artifact:

- executable code or a small script;
- a config, manifest, registry, preflight, or assumption record;
- a test, smoke test, or reproducible command;
- a generated table, raster, map, figure, or diagnostic under `outputs/`;
- an internal project note that records commands, inputs, assumptions, and blockers.

Long prose-only responses are not enough for implementation tasks. Move the project forward with
small, auditable outputs.

## Governance Budget

Experiments and outputs have priority over process documents.

Do not create new governance documents unless they directly support a concrete experiment output,
data artifact, or mentor-facing evidence packet. In particular, do not create new decision
packages, risk overviews, preflights, registries, handoffs, long methodology clarifications, or
adversarial self-review documents as standalone work unless the user explicitly asks for that
document type or a real data download requires a registry/preflight record.

Active control files should remain few:

- `AGENTS.md`
- `README.md`
- `context/docs/research-map/RESEARCH_OVERVIEW.md` (project scope and status)
- `context/docs/research-map/REPRODUCIBILITY.md` (claim-level ladder, preflight gate, preprocessing rules)
- `context/docs/research-map/EXPERIMENTS.md` (current experiment registry)
- a current experiment manifest or output-local manifest for the active run
- a current mentor packet only when a mentor message or artifact is being prepared

These are the binding **control** tier. The other six files in
`context/docs/research-map/` (`RESEARCH_QUESTIONS`, `HYPOTHESES`, `RESULTS`,
`ARTIFACT_INDEX`, `DECISION_LOG`, and the folder `README`) are active
working docs but derived — see `context/docs/research-map/README.md` for the
control-vs-derived distinction. Control files must stay consistent with each
other and with the codebase; derived files may lag but must not contradict the
control tier.

The older `context/docs/project-management/` folder is archive-only since the
2026-07-05 consolidation into `context/docs/research-map/`. Its former live files
(assumptions_log, execution_status_policy, task_progress_board, etc.) are
preserved under `_archive/superseded_by_research_map_2026-07-05/`.

Older governance documents are archival. They may be referenced for evidence, but they must not
drive new work unless the user explicitly points to them or the active experiment needs a recorded
fact from them.

For every documentation-only task, prefer at least three code, config, test, table, map, raster, or
experiment-output tasks before opening another documentation task. If a task can be completed by
changing code/config/output instead of adding prose, do that.

## Version Naming Convention

Keep boundary versions separate from experiment versions.

- `boundary_id` names the study area / working boundary, for example `boundary_v1`.
- `experiment_id` names a criteria stack, processing run, or scenario set, for example
  `criteria_stack_v0_2`.
- Do not write ambiguous phrases like `V1 v0.2` in human-facing text. Use
  `boundary_v1 / criteria_stack_v0_2`.
- File and directory paths should prefer the same two-level structure when new outputs are created,
  for example `outputs/boundary_v1/<experiment_id>/` or the current Peru-first equivalent
  `outputs/srtm_1arcsec_peru_pilot/<experiment_id>/`.
- If legacy filenames already contain mixed strings such as `v1_v0_2`, treat them as archival
  compatibility artifacts. New scripts and reports should use explicit `boundary_id` and
  `experiment_id` fields.

## Execution Status Policy

Core principle: uncertainty reduces claim level; it does not automatically pause execution.

Detailed internal policy:
`context/docs/research-map/REPRODUCIBILITY.md` (§2 Execution status policy).

If a scientific choice is uncertain, continue with a clearly labelled diagnostic, provisional, or
sensitivity scenario; record the assumption and lineage; expose the choice in config or a table
where practical; and avoid final scientific claims.

Every generated output must declare or inherit one of these status levels:

- `diagnostic_only`: tests pipeline behavior or data readiness; no scientific claim.
- `provisional`: method is defensible enough for controlled prototype work but awaits stronger
  data, mentor review, or validation.
- `sensitivity_scenario`: compares assumptions, weights, thresholds, formulas, or data families.
- `mentor_review_ready`: suitable to show the mentor for feedback on a concrete map/table/result.
- `final_claim`: allowed only after explicit approval, validation/claim evidence, and complete
  documentation.

Most current IFPM work should be `diagnostic_only`, `provisional`, or `sensitivity_scenario`.
Only `final_claim` requires full validation and explicit approval.

The agent may not mark the project as paused merely because mentor confirmation would improve
scientific confidence. Mentor confirmation is a reason to downgrade status, not to stop execution.
Pause only when required inputs are missing and no provisional substitute exists, code cannot run
and the exact error is documented, continuing would overwrite or corrupt valid outputs, or the user
explicitly asks to pause.

## Active Prototype Scope

The current practical prototype path is Peru-first controlled experimentation within Arequipa
Region, using the internal boundary id `peru_hybas_l7_6070641200`
(`outputs/srtm_1arcsec_peru_pilot/`), not a full hydrodynamic flood model and not a final thesis
claim. `boundary_v1` / Upper Mzingwane remains a secondary/background method-development case unless
explicitly reopened.

Prefer scoped experiments with:

- one clearly named study area or boundary version;
- one declared CRS and, for raster overlays, one reference grid;
- 3-5 simple spatial indicators before adding complex criteria;
- normalized layers with documented directionality;
- placeholder or candidate weights stored in a config/table and labelled as such;
- one reproducible command chain;
- one generated map, raster, table, or handoff;
- one short experiment note with assumptions and limits.

Allowed first-pass indicators include elevation, slope, TWI/flow accumulation or distance to
drainage, distance to rivers, land-cover/bare-ground classes, road/access proximity, and explicitly
labelled mining/ASM indicators.

Avoid unless explicitly requested or already scoped in a current plan:

- full hydrodynamic modelling;
- broad RUSLE/R-factor rework beyond the named experiment;
- full AHP expert-survey design;
- citizen-science modules;
- WebGIS/dashboard work;
- long literature-review writing;
- broad refactoring or rewriting project documents unrelated to the task.

## Handling Uncertainty During Experiments

Do not stop implementation solely because a scientific decision is uncertain. Instead:

- record the assumption in the relevant project note, registry, preflight file, handoff, or the
  active assumptions register in `context/docs/research-map/RESEARCH_QUESTIONS.md`
  (and a decision record in `context/docs/research-map/DECISION_LOG.md` when the
  assumption is decision-shaped) if one is needed;
- expose uncertain values as config/table parameters where practical;
- continue with clearly labelled placeholder, candidate, indicator, or context evidence;
- never claim scientific validity, validation, final flood-risk status, or intervention priority
  from placeholder evidence.

Examples:

- Placeholder weights are allowed only when labelled as placeholder/candidate and stored in a
  reproducible table or config.
- Demo boundaries or bounding boxes are allowed only for pipeline testing and must be labelled
  non-scientific or prototype-only.
- Missing local data should become a blocker or data-request entry, not a reason to stop coding.
- Indirect evidence such as OSM quarry, road proximity, or coarse population data must remain
  labelled as indicator/context until stronger source data or an accepted modelling rule exists.

## Criteria Design Rules

Criterion names must describe what the data actually measure. Do not use broad scientific labels
when the layer is only a narrow indicator.

- `K x LS x C` without an accepted rainfall erosivity factor is `soil_erosion_factors`, not
  final sediment risk.
- River or water proximity alone is `river_proximity_indicators`, not environmental sensitivity.
- Road proximity alone is `exposure_indicators`, not socioeconomic vulnerability.
- C-factor / vegetation / bare-ground evidence is `land_cover_pressure`.
- Mining or quarry proximity/footprint evidence is `mining_pressure`.
- Population, built-up, schools, health facilities, bridges, damaged roads, or affected places are
  exposure evidence; road distance alone is only an access indicator.

Do not hide within-criterion equal-weight averaging in code. If components are combined, put the
component names, weights, direction, and `claim_level` in a config, manifest, or scenario table.

NoData must remain NoData unless a documented method explicitly justifies imputation. Never treat
NoData as low risk by filling it with `0` for scoring. Produce a coverage report when NoData affects
a scored raster.

Each scored criterion should record:

- semantic meaning;
- input layers;
- transformation / normalization;
- NoData policy;
- component weights, if any;
- `claim_level`.

Mentor-facing requests should normally ask one concrete decision question from a table/map, not a
bundle of abstract methodology questions.

## Rainfall, AHP, R-Factor, And Peru Execution Rules

Rainfall / CHIRPS:

- CHIRPS or other coarse rainfall products must not be represented as native 30 m information.
- Rainfall-derived metrics may enter diagnostic, provisional, or sensitivity MCDA experiments via
  catchment/sub-basin zonal aggregation or explicitly labelled coarse-to-reference-grid resampling
  for overlay compatibility.
- Required metadata: native resolution, target grid, resampling or aggregation method, effective
  resolution warning, source lineage, and claim/status level.
- Do not block rainfall criteria only because CHIRPS is coarse; block only unsupported claims that
  treat CHIRPS as true 30 m rainfall evidence.

AHP:

- AHP matrices from mentor slides, meetings, or documented project materials may be used as
  `sensitivity_scenario` inputs.
- Scenario weights must not be named or described as final approved weights unless explicitly
  confirmed.
- Scenario metadata must include source, date, criteria order, consistency ratio, and status.

R-factor / RUSLE:

- Known-invalid R/A products remain deprecated and must not be revived as accepted evidence.
- New R-factor products may be generated as provisional or sensitivity scenarios if method,
  source, value range, uncertainty, and lineage are documented.
- Do not pause all R-factor work while waiting for mentor confirmation; downgrade the claim level
  and keep invalid old products separate.

Peru:

- Peru work is the active mainline after the 2026-07-06 Peru-first decision. Continue Arequipa Region prototype
  outputs first: five PIM criteria maps, AHP-weighted prioritisation maps, top-priority classes, and
  mining overlay.
- Arequipa Region remains provisional and must not be described as a final research-selected Peru study area or
  validated rescue-decision map.
- Final Zimbabwe-Peru comparison remains blocked until both countries share harmonized criteria,
  normalization, thresholds, and claim rules.
- Do not block Peru prioritisation work merely because the Zimbabwe final methodology is not locked.

Documentation:

- Avoid repeating broad disclaimers in every output.
- Prefer one global scope statement plus per-output status or `claim_level` metadata.
- Prefer code, configs, outputs, maps, and comparison tables over long defensive prose.

## Required Task Workflow

For every non-trivial implementation task:

1. State the concrete artifact to be produced in no more than five bullets.
2. Inspect relevant existing files before editing.
3. Make the smallest useful change.
4. Run a smoke test, validation command, or exact attempted command with the exact error.
5. End with the practical handoff: changed files, commands run, outputs created, assumptions added,
   and remaining blockers.

A task is not complete unless:

- code, config, documentation, or output changed as requested;
- there is a reproducible command or a recorded reason why it could not run;
- outputs are in predictable allowed folders;
- assumptions are separated from results;
- unsupported scientific claims are avoided.

## Mentor-Facing Document Style

Any file under `context/docs/mentor-explanation/`, and any short message or briefing written for
the mentor, must follow the style rule in `context/docs/mentor-explanation/STYLE.md`: first person,
lead with the conclusion, one question per message, and no AI-style scaffolding (TL;DR / "bottom
line" headers, over-symmetric structure, filler hedges, decorative formatting). This keeps
mentor-facing documents reading as the HiWi's own work. It does not apply to internal engineering
notes under `research-map/` or `data-management/`, where full step-by-step evidence chains
are wanted.

## Report-Friendly Figure And Briefing Rule

Mentor-facing and boss-facing outputs must be understandable by a reader who did not follow the
technical details. Treat this as a core project goal, not a cosmetic polish step.

For every mentor/boss-facing map, board, slide, or figure package:

- lead with the one-sentence takeaway before details;
- use plain criterion names and human-readable captions, not internal task ids, gate names, file
  ids, or unexplained dataset codes;
- show why a map matters, not only what the model produced;
- include driver explanation when producing priority, risk, susceptibility, or suitability maps:
  dominant-criterion pixel maps, contribution maps, or another clear "why this area is high"
  explanation;
- separate presentation figures from internal diagnostics when needed. Internal figures may show
  dense QA information; reporting figures should be clean, legible, and captioned;
- avoid long paragraphs inside the figure. Put method notes, limitations, and claim level in the
  caption, handoff, or accompanying note;
- explicitly state the output status in simple language, for example `prototype map`,
  `sensitivity scenario`, `data gap`, or `not final flood-risk result`;
- prefer one clear question or decision request from each package, rather than many abstract
  methodology questions.

Before calling a mentor/boss-facing figure done, preview the rendered image/PDF and check:

- a non-participant can identify the study area, the main result, and the key driver within
  30 seconds;
- legends, colorbars, labels, and captions do not overlap or hide map evidence;
- color coding makes priority criteria or drivers clearer, not just more decorative;
- the wording does not read like an internal experiment log.

## V1 Terrain Reference Grid Rule

For V1 controlled prototype terrain preprocessing, follow the internal rule file:

`context/docs/data-management/v1_terrain_reference_grid_rule.md`

- The active terrain reference raster is
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`.
- Future V1 terrain derivatives must match the reference raster's CRS, transform, resolution,
  width, height, band count, dtype, NoData, and V1 valid-cell coverage before standardization,
  scoring, or weighted overlay.
- Incompatible rasters must be recorded as `grid-compatible=false` and blocked from overlay.
- CHIRPS must not be represented as native `30 m` rainfall evidence. It may be used through
  native/zonal summaries or explicitly labelled coarse-to-reference-grid diagnostic/provisional
  scenarios when native resolution, target grid, resampling/aggregation method, and claim level are
  recorded.
- This rule does not accept V1 as the final thesis boundary and does not authorize final
  flood-risk interpretation or intervention-priority interpretation.

## Python Environment

Use a local Python environment for root-context GIS exploration and private tooling.

- Preferred root environment: `.venv/` at the workspace root. It is local-only and ignored by Git.
- Acceptable temporary environment: `/tmp/<purpose-specific-venv>` when keeping the workspace
  untouched is useful.
- Do not commit virtual environments, package caches, downloaded wheels, or generated dependency
  artifacts.
- Record any non-standard GIS/runtime dependency needed to reproduce a workflow in the relevant
  internal project note, registry, preflight file, or handoff.
- Keep deliverable-code dependencies inside `ifpm-flood-pipeline/` and do not make public-safe
  examples depend on root `.venv`, `context/`, `data/`, or `outputs/`.

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
