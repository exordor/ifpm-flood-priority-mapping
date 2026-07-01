# Multi-Level Progress Review

Updated: 2026-06-10

Status: internal review report. No real data was downloaded or processed.

## Review Scope

This review asked four read-only subagents to inspect current IFPM progress:

- methodology and domain validity;
- data governance, download management, and public/private boundary;
- deliverable engineering and code readiness;
- project-management consistency and progress truthfulness.

The root repository and `ifpm-flood-pipeline/` were clean before review. The review used current
files and local verification commands as authoritative evidence.

## Overall Verdict

No P1 blocking issue was found.

The current `NO-GO` state for general real-data download, overlay, and interpretation is correct.
A narrow HydroSHEDS boundary-discovery step remains the highest-leverage next move, but only
after its preflight blockers are closed and an authorization record exists.

The main risk is not that the project lacks scaffolding. The risk is that the synthetic-tested
pipeline could be pushed into real-data overlay before the model-unit, AHP weighting, NoData,
mask, and geospatial verification gates are closed.

## P2 Findings And Triage

### P2-1 CHIRPS And Sub-Basin Handling Is Not Yet Executable

Finding: the docs correctly say CHIRPS must not be treated as 30 m raster detail, but the current
pipeline only supports same-grid raster overlay.

Failure mode: rainfall values could be broadcast or resampled into false 30 m precision.

Triage: not fixed in code in this review. Added Step S5 engineering readiness and IFPM-028 so
real-data overlay remains blocked until the selected model-unit branch is executable. If
sub-basin aggregation is selected, a zonal or tabular scoring path is needed before overlay.

### P2-2 First-Slice AHP Protocol Is Underspecified

Finding: the first Zimbabwe slice lists terrain and rainfall indicators, but the weighting source,
criteria hierarchy, group-judgment rule, CR review, and sensitivity scenarios are still open.

Failure mode: the synthetic sample matrix becomes de facto expert judgment.

Triage: recorded as IFPM-038. No real output should be interpreted until a first-slice AHP
protocol exists or the output is explicitly labelled as a synthetic workflow diagnostic.

### P2-3 NoData And Mask Readiness Is Stricter In Methodology Than Code

Finding: root methodology requires NoData and shared-mask handling before overlay, while current
diagnostics separate `ready_for_overlay` from stricter metadata readiness.

Failure mode: untagged sentinel values or mask mismatch can silently affect scores.

Triage: added Step S5 and IFPM-028. Real-data overlay must require strict metadata readiness,
explicit full-coverage or NoData waivers, and mask-loss reporting.

### P2-4 Misplaced Data Artifacts Could Be Hidden By `.gitignore`

Finding: root `.gitignore` hides GIS and archive extensions globally, but the boundary validator
did not scan ignored files under `context/` or `ifpm-flood-pipeline/`.

Failure mode: a misplaced real raster, vector, or archive could sit in a private context or
deliverable path without appearing in `git status`.

Triage: fixed in `bin/validate-boundary.sh`. The validator now scans for GIS/archive artifacts
under `context/` and `ifpm-flood-pipeline/`, while allowing only explicit synthetic fixture
locations.

### P2-5 Geospatial Smoke Coverage Can Pass With Skipped Raster Tests

Finding: `rasterio` is optional, so dev-only tests can pass while GeoTIFF behavior is skipped.

Failure mode: reports say tests pass even though raster diagnostics, standardization, and
synthetic workflow behavior were not exercised.

Triage: recorded in Step S5 and IFPM-028. A local run with geospatial dependencies passed during
this review, but the project still needs a durable pre-real-data verification target that makes
the geospatial test mode explicit.

### P2-6 Overlay Does Not Enforce 0-1 Standardized Inputs

Finding: docs require standardized 0-1 inputs, but overlay currently trusts input layers.

Failure mode: raw elevation or rainfall could be overlaid and produce plausible but meaningless
scores.

Triage: recorded in Step S5 and IFPM-028. Real-data overlay must enforce standardized input
ranges by default or require an explicit experimental override.

### P2-7 Raster Diagnostics Lack Finite-Value And Mask Summaries

Finding: current diagnostics focus on metadata, while the real-data gate needs value and mask
readiness evidence.

Failure mode: sentinel values, all-constant rasters, empty coverage, or severe outliers remain
hidden until after scoring.

Triage: recorded in Step S5 and IFPM-028. Real-data diagnostics need finite count/fraction,
min/max, constant-layer flag, NoData or masked count, and valid-mask coverage.

### P2-8 Overlay Mask Loss Is Silent

Finding: overlay intersects masks, but diagnostics do not yet expose how much area each layer
drops.

Failure mode: one bad criterion can remove large areas without being visible in the handoff.

Triage: recorded in Step S5 and IFPM-028. Real-data overlay readiness must report per-layer valid
fractions, intersection valid fraction, and dropped-cell counts.

## Lower-Severity Findings

- P3: `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/prototype_study_slice_decision.md` had stale wording that made raster diagnostics sound
  wholly unimplemented. It now separates completed scaffolding from remaining real-data blockers.
- P3: the HydroBASINS discovery gate was slightly circular because candidate ids are partly the
  output of discovery. The current exception remains valid, but the HydroSHEDS preflight should
  use a boundary-discovery authorization where candidate ids are an output.
- P3: the validator failed on ignored `.venv` symlinks. It now skips ignored local runtime
  directories before symlink review.
- P3: equal-interval classes are exploratory and not comparison-safe. Fixed-threshold class
  configuration is tracked as IFPM-037.
- P4: root wording still called the nested code repo "future deliverable code". The index now
  says it is an independent deliverable repo with a minimal synthetic-tested pipeline.
- P4: the dataset registry template implied reusable downloads could be documented immediately
  after download. It now requires registry identity, source, destination, licence/access notes,
  and authorization before any real download.

## Verification Evidence

Local verification during this review:

- `uv run --extra dev ruff check .` in `ifpm-flood-pipeline/`: passed.
- `uv run --extra dev ruff format --check .` in `ifpm-flood-pipeline/`: passed.
- `uv run --extra dev pytest` in `ifpm-flood-pipeline/`: 25 passed, 5 skipped.
- `uv run --extra dev --extra geospatial pytest` in `ifpm-flood-pipeline/`: 36 passed.
- `wc -l` on runtime modules: largest runtime file is `cli.py` at 185 lines; modules remain
  review-friendly.

The dev-only test result is not enough for real-data overlay because geospatial tests may be
skipped without `rasterio`. The successful geospatial run is useful evidence, but it should be
made into an explicit pre-real-data verification command before real overlay work starts.

## Recommended Next Step

Close a narrow HydroSHEDS boundary-discovery gate first:

1. record exact HydroBASINS/HydroRIVERS archive names, size, licence text, and overwrite safety;
2. write a boundary-discovery authorization entry;
3. download only to `data/raw/hydrosheds_zimbabwe_prototype/` or
   `data/tmp/hydrosheds_zimbabwe_prototype/`;
4. use the result only to identify candidate Upper Mzingwane boundary units;
5. keep SRTM, CHIRPS, overlay, and interpretation blocked until Step S5 is closed.
