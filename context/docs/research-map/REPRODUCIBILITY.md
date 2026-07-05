# Reproducibility

Status: active. Environment, runbook, execution-status policy, preflight gate,
preprocessing design, and grid compatibility rules. **Binding.**

This file consolidates the four formerly separate governance documents:
execution-status policy, the real-data execution preflight gate, the real-data
preprocessing design, and the runbook summary.

## 1. Environment

- **OS:** macOS (darwin, arm64). Linux should work but is not tested.
- **Python:** local `.venv/` at the workspace root (local-only, ignored by Git).
  Acceptable alternative: `/tmp/<purpose-specific-venv>` when keeping the
  workspace untouched is useful.
- **Package manager:** `uv` for `ifpm-flood-pipeline/`; plain `pip`/`venv` for
  root-context GIS exploration.
- **GIS deps:** rasterio, geopandas, whitebox (V1 hydrology), numpy, scipy,
  matplotlib. Record any non-standard GIS/runtime dependency in the relevant
  internal project note, registry, preflight, or handoff.
- **External tools:** SRTM mirror via ESA STEP (no login); CHIRPS via Climate
  Hazards Center HTTP windowed read; INGEMMET via ArcGIS REST (no login);
  open-meteo for ERA5 hourly (no auth).
- **Do not commit:** virtual environments, package caches, downloaded wheels,
  generated dependency artifacts.

## 2. Execution status policy (claim-level ladder)

### Core rule

Uncertainty reduces claim level; it does not automatically pause execution.

If a scientific choice is uncertain, continue with a labelled diagnostic,
provisional, or sensitivity scenario. Record the assumption, method lineage,
source data, and output status. Do not present the result as a final scientific
claim.

### Output status levels

Every generated output must declare or inherit one status level:

| status | meaning | allowed use |
|---|---|---|
| `diagnostic_only` | tests code, data readiness, or processing logic | internal QA, debugging, method development |
| `provisional` | defensible for controlled prototype work but not fully validated | internal prototype and mentor discussion |
| `sensitivity_scenario` | compares assumptions, weights, thresholds, formulas, or data families | robustness and method-choice review |
| `mentor_review_ready` | concrete figure/table/map suitable for mentor feedback | mentor review; not final thesis claim |
| `final_claim` | validated and explicitly approved scientific result | thesis/public claim only |

Only `final_claim` requires full validation and explicit approval. Most current
IFPM outputs should be `diagnostic_only`, `provisional`, or `sensitivity_scenario`.

### No-pause rule

Do not pause work merely because mentor confirmation would improve scientific
confidence. Pause only when:

- required inputs are missing and no diagnostic/provisional substitute is possible;
- code cannot run and the exact error has been documented;
- continuing would overwrite or corrupt existing valid outputs;
- credentials, licences, or storage rules prevent safe execution;
- the user explicitly asks to pause.

Mentor confirmation is a reason to downgrade status, not a reason to stop
execution.

### Rainfall / CHIRPS rule

CHIRPS and other coarse rainfall products must not be described as native 30 m
information. Rainfall-derived metrics may enter diagnostic, provisional, or
sensitivity MCDA experiments through:

- catchment or sub-basin zonal aggregation; or
- explicit coarse-to-reference-grid resampling for overlay compatibility.

Required metadata: native resolution, target grid or aggregation unit,
resampling or aggregation method, effective-resolution warning, source lineage,
status / claim level.

Do not block rainfall criteria only because CHIRPS is coarse. Block only
unsupported claims that treat coarse rainfall as true 30 m rainfall evidence.

### AHP rule

AHP matrices from mentor slides, meetings, or documented project material may be
used as `sensitivity_scenario` inputs. They must not be named or described as
final approved weights unless explicitly confirmed. Required metadata: source,
date, criteria order, pairwise matrix or derived weights, consistency ratio,
status / claim level.

### R-factor rule

Known-invalid R/A products remain deprecated. New R-factor products may be
generated as provisional or sensitivity scenarios if method, source, value
range, uncertainty, and lineage are documented. Waiting for mentor confirmation
should not pause all R-factor work.

### Peru rule

Peru work may run in parallel for: data inventory; terrain indicators;
rainfall/land-cover availability checks; diagnostic readiness reports. Final
Zimbabwe-Peru comparison remains blocked until both countries share harmonized
criteria, normalization, thresholds, and claim rules.

### Global scope statement

This repository produces AHP-MCDA-based flood, sediment, and intervention-
priority prototype outputs. These are susceptibility/prioritization products,
not hydrodynamic inundation simulations. Diagnostic and provisional outputs are
intended for internal review and method development only.

## 3. Real-data execution preflight gate

### Scope: data production vs interpretable claim

Execution rule: uncertainty reduces claim level; it does not automatically pause
execution. Use `diagnostic_only`, `provisional`, or `sensitivity_scenario`
outputs when final scientific support is missing. Reserve `final_claim` for
explicitly approved, validated thesis/public results.

**Data production** (HiWi scope; proceeds with documented defaults; not blocked
by this gate unless a dataset-specific preflight is incomplete):

- downloading public datasets that have a closed registry + preflight + Step S3
  authorization;
- preprocessing, mosaicking, reprojecting, clipping, void-filling;
- deriving terrain, hydrology, sediment-factor, and land-use indicators from
  already-downloaded data;
- standardizing layers to 0-1 with a documented rule;
- producing diagnostic overlays and sensitivity runs with documented synthetic,
  placeholder, slide-derived, or candidate weights, clearly labelled with
  claim/status level;
- producing rainfall-derived diagnostic/provisional criteria through zonal
  aggregation or explicitly labelled coarse-to-reference-grid resampling, without
  claiming native 30 m rainfall information;
- producing R-factor family diagnostics and provisional/sensitivity sediment-
  risk products from fresh documented lineage while keeping known-invalid R/A
  products deprecated;
- producing Peru data inventory and terrain/readiness diagnostics before any
  final cross-country comparison;
- generating diagnostics, figures, and handoff tables.

Data-production outputs must be labelled as workflow/diagnostic products and
must not be presented as interpretable flood-risk or intervention-priority
findings. They are inputs FOR the mentor and any future modeller, not claims.

**Interpretable claim** (mentor / thesis scope; remains gated by this gate and
by the P1/P2 decision packages):

- asserting that an output is a validated flood-risk map;
- presenting priority classes as intervention priorities;
- publishing, presenting, or comparing results as project findings;
- treating synthetic-weight outputs as if they had expert authority;
- making Zimbabwe-Peru comparison claims.

The HiWi does not make claims. The HiWi produces defensible, documented data
products and hands them to the mentor. Thesis-level decisions (minimum viable
thesis, validation requirement, criteria hierarchy acceptance, boundary
promotion to final, Peru scope) are the mentor's calls and do not block data
production.

### Current verdict

- **Data production is GO** for already-authorized public datasets and for
  deriving diagnostic products from already-downloaded data, using documented
  defaults.
- **Final claims remain NO-GO** (validated flood-risk map, intervention
  priority, final Zimbabwe-Peru comparison, public release) until the relevant
  mentor decisions close.

The CHIRPS scale rule is a binding data-quality rule (not a claim): CHIRPS must
not be described as native 30 m rainfall evidence.

The project has completed one narrow terrain chain (six SRTMGL1 raw tiles
downloaded, inventoried, mosaicked, reprojected, clipped to V1, converted into
DEM/slope diagnostics), one Peru terrain chain (PE1), and the full 5/6-criteria
prototype priority stacks on both sites.

Boundary-only exceptions executed:
- HydroBASINS boundary-discovery download (authorized + executed).
- Zimbabwe Geoportal Sub-Catchments comparison (authorized + executed).
- SRTM V1 raw-tile download + terrain diagnostics (executed).
- Scoped CHIRPS rainfall comparison (executed).
- HydroBASINS SA + PE1 boundary + terrain chain (executed).

None of these authorizes final flood-risk interpretation or intervention-map
interpretation.

### Numbering note

This gate previously used a "Gate G1-G7" scheme. The two decision-bearing gates
were merged into the decision numbering: G1 (boundary) → **IFPM-D06**, G2
(modelling unit) → **IFPM-D01**. The five engineering-checklist gates were
renumbered as steps: G3 → **Step S1**, G4 → **Step S2**, G5 → **Step S3**,
G6 → **Step S4**, G7 → **Step S5**.

### IFPM-D06: Outlet And Boundary Acceptance (was Gate G1)

Required before SRTM download, CHIRPS download, overlay, or aggregation:

- record the selected or provisional outlet / pour point;
- document why the outlet is relevant to flood impact and mining pressure;
- choose the boundary source or delineation method;
- record HydroBASINS level, HYBAS id, PFAF id, and version if used;
- record whether multiple units are unioned or dissolved;
- check geometry validity and CRS;
- compare area and shape against authoritative / Geoportal / HydroBASINS /
  mentor-supplied boundary;
- state the mismatch policy if candidate boundary sources disagree;
- mark the boundary as accepted, rejected, or accepted with waiver.

Current state: closed with waiver for controlled prototype SRTM terrain
diagnostics only. Working boundary: V1 / `HB_L8_1081528840_full_l7_chain`,
`accepted_with_waiver_for_controlled_prototype`. Final boundary acceptance
remains open.

### IFPM-D01: Modelling Unit (was Gate G2)

Select one branch before combining terrain and rainfall:

1. Terrain-only raster screening with CHIRPS reported as context or a separate
   summary.
2. Sub-basin aggregation with terrain and CHIRPS summarized to the same accepted
   units.
3. Mixed product with terrain rasters and rainfall tables reported separately.

Current state: final terrain-rainfall claim is blocked. Diagnostic/provisional
integration may proceed using either zonal aggregation or labelled coarse-to-
reference-grid rainfall scenarios, with status metadata and no native-30 m
rainfall claim.

### Step S1: Temporal Window And Rainfall Product (was Gate G3)

Required before CHIRPS download or processing:

- choose the first rainfall window (event month, rainy season, multi-year
  climatology);
- choose timestep (monthly or annual preferred for first small prototype);
- choose final or preliminary product;
- record the expected file count and byte size before download;
- decide whether CHIRPS is aggregated to catchment/sub-basin units or kept as
  diagnostics only.

Current state: closed for the scoped rainfall-sensitivity package, not closed
for final rainfall criterion selection or overlay.

### Step S2: Dataset-Specific Preflight Closure (was Gate G4)

Before any individual dataset download, its preflight note must have no
unchecked pre-download blocking item.

Current blockers:
- SRTM: raw-tile download, inventory, V1 DEM/slope preprocessing complete;
  scoring-ready terrain standardization not started.
- HydroSHEDS: boundary-discovery download and inspection complete. Boundary
  acceptance and redistribution clearance remain open.
- Zimbabwe Geoportal Sub-Catchments: boundary-comparison download and inspection
  complete. Boundary acceptance and redistribution clearance remain open.
- CHIRPS: scoped comparison and native/zonal diagnostics complete. Final
  rainfall criterion claims remain blocked; provisional/sensitivity rainfall
  criteria may be produced with status metadata and scale warnings.

### Step S3: Download Authorization Record (was Gate G5)

Immediately before a real download, create a short authorization entry in the
dataset registry or preflight note with:

- dataset id, source URL or portal, exact source artifact names;
- expected file count and byte size;
- intended raw destination under `data/raw/<dataset_id>/`;
- temporary destination under `data/tmp/<dataset_id>/` if needed;
- output destination under `outputs/<dataset_id>/`;
- licence or account constraints confirmed for this attempt;
- download command or manual steps;
- operator/date;
- statement that credentials, cookies, tokens, and private links are not
  recorded.

After download, add: actual file count and size; checksum or file-size
evidence; partial or failed-download disposition; CRS, georeferencing, and
integrity check state.

### Step S4: Execution Rules After Download (was Gate G6)

- keep raw files unchanged under `data/raw/<dataset_id>/`;
- write transformed analysis copies and diagnostics under `outputs/`;
- run grid diagnostics before standardization or overlay;
- use a shared validity mask for pixel overlay, or document why masks differ;
- block final interpretation if CRS, transform, resolution, shape, band count,
  or NoData checks fail without waiver;
- label any output as workflow or preliminary susceptibility only.

### Step S5: Pre-Real-Data Engineering Readiness (was Gate G7)

Before any real-data overlay, scoring, or interpretation:

- run deliverable tests with geospatial dependencies installed and record
  whether GeoTIFF tests were executed or skipped;
- require raster diagnostics to expose finite-value and mask summaries, or
  record a waiver for a diagnostic-only run;
- require overlay inputs to be standardized 0-1 rasters by default, or record an
  explicit experimental override;
- report per-layer valid-cell fractions and intersection mask loss before
  interpreting an overlay output;
- confirm the selected model-unit branch is executable in code.

Current state: the five engineering-readiness items are closed
(`ifpm-flood-pipeline` commit `39f6b33`: durable geospatial verification target
with 0 skipped GeoTIFF tests, finite-value/mask diagnostics, 0-1 overlay-input
enforcement with explicit override, per-layer mask-loss reporting, zonal scoring
branch; 36 → 51 tests passing, 0 skipped). Real-data overlay, scoring, and final
interpretation remain blocked pending mentor decisions.

### Go Criteria

General real-data download may proceed only when all of these are true:

- IFPM-D06 boundary acceptance is complete.
- IFPM-D01 modelling unit is selected.
- Step S1 CHIRPS temporal/product decision is complete, or CHIRPS is explicitly
  deferred.
- Step S2 selected dataset preflight has no unchecked pre-download blocker.
- Step S3 authorization entry is written before download.
- Step S5 engineering readiness is complete before overlay or interpretation.
- The target dataset directory is under ignored `data/`.
- The reviewer confirms the download is small and scoped.

### No-Go Triggers

Stop before download if any of these appears:

- boundary acceptance remains unknown for SRTM, CHIRPS, overlay, or
  interpretation;
- expected size is unknown or too large for a prototype;
- licence, account, or redistribution rules are unclear for the intended use;
- command would write outside `data/` or overwrite unrelated local files;
- selected artifact names are not recorded;
- the workflow would imply CHIRPS has 30 m spatial detail;
- final real-data overlay interpretation would run without Step S5 engineering
  readiness checks;
- credentials, cookies, tokens, or private cloud links would be written to a
  committed file.

## 4. Real-data preprocessing design

### Purpose

Defines the first real-data preprocessing rules for the Zimbabwe / Upper
Mzingwane prototype slice. Sits above the dataset-specific registry and preflight
notes. Goal: prevent a synthetic-tested pipeline from being applied to real data
with unclear grid, CRS, NoData, aggregation, or resampling assumptions.

### Pre-Download Gate

Do not download additional real data or run preprocessing until all of these are
true:

1. The outlet or provisional pour point is selected and documented.
2. The outlet's flood/mining relevance is recorded.
3. The outlet-based catchment boundary or approved proxy boundary is selected
   and documented.
4. The modelling unit is selected.
5. The temporal window for rainfall and validation evidence is selected.
6. The relevant dataset preflight checklist has no unchecked blocking item.
7. The intended raw destination is under `data/raw/<dataset_id>/`.
8. The intended output destination is under `outputs/<dataset_id>/` or a
   prototype-specific ignored output directory.

### Boundary And CRS Rules

- Use an outlet-based upstream catchment for the Zimbabwe prototype when the
  outlet is known.
- Prefer a HydroBASINS-compatible unit only if the selected level and basin id
  are recorded.
- If a mentor supplies an authoritative local catchment boundary, record its
  source and replace or supplement HydroBASINS.
- Treat Geoportal, HydroBASINS, and the literature ~2138 km² boundary as
  comparison layers unless one is explicitly accepted as a proxy.
- Keep source CRS information in the dataset registry and preprocessing
  diagnostics.
- Reproject only derived working rasters or analysis copies, never the raw
  source files.
- Record the target CRS and transform before producing overlay inputs.

### Grid And Resolution Rules

For the active V1 controlled prototype terrain run, the detailed reference-grid
rule is saved in
`context/docs/data-management/v1_terrain_reference_grid_rule.md`. That file is
authoritative for V1 terrain derivative compatibility. The Peru analogue is
`context/docs/data-management/peru_pilot_terrain_reference_grid_rule.md`.

**Terrain-Derived Raster Grid:**

- SRTM-derived terrain layers may use an SRTM-compatible 30 m working grid.
- All terrain-derived rasters used together must share CRS, transform,
  resolution, shape, and NoData semantics before overlay.
- Choose and record a metric working CRS before deriving slope, flow
  accumulation, drainage distance, or other distance/area-sensitive layers.
- Processing order: raw tile inventory, void/NoData check, mosaic/clip if
  needed, reproject an analysis copy to the metric working CRS, then derive
  terrain layers with units recorded.
- V1 active reference raster:
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`.
  Later V1 terrain layers must match its CRS, transform, resolution, shape, band
  count, dtype, NoData value, and V1 valid-cell coverage before they can enter
  standardization or overlay.

**Rainfall Grid:**

- CHIRPS v3 is much coarser than SRTM terrain layers. Do not treat CHIRPS pixels
  as equivalent to 30 m terrain pixels.
- Safer options for the first prototype:
  1. aggregate CHIRPS to the selected catchment or sub-basin units;
  2. compute zonal rainfall summaries for the terrain-grid mask;
  3. keep CHIRPS at native resolution for diagnostics and report scale mismatch
     explicitly.
- Do not resample CHIRPS to 30 m for pixel-level overlay. If a future coarse
  rainfall visualization is approved, label it as a zonal or coarse-summary
  product, not as 30 m rainfall evidence.

**Model-Unit Branches:** (see IFPM-D01 above for the three branches)

Do not broadcast a catchment or sub-basin rainfall value across 30 m cells
unless the output is explicitly labelled as a coarse-summary overlay and the
limitation is documented.

**Vector Hydrographic Units:**

- Use HydroBASINS or another approved boundary as mask and aggregation geometry.
- Record selected HydroBASINS level, basin id, and version before processing.
- HydroRIVERS may support drainage-distance indicators, but it is not
  field-survey evidence.

### Resampling And Aggregation Rules

- Prefer aggregation or zonal summaries when source resolution differs strongly.
- Use nearest-neighbour resampling only for categorical or id layers.
- Use bilinear or average-style resampling only for continuous analysis copies
  when the method is documented.
- Do not mix resampled and native layers without recording which layers were
  transformed.
- Preserve raw source files unchanged and write all transformed analysis copies
  under `outputs/`.

Aggregation records must include: statistic type, boundary inclusion rule,
valid-cell coverage fraction and NoData fraction per unit, partial-pixel/edge
handling, minimum acceptable coverage threshold (or waiver), and whether results
are suitable for scoring or only for diagnostics.

### NoData And Mask Rules

- Treat NoData as a first-class preprocessing property, not as a normal numeric
  value.
- If a source uses a sentinel such as `-9999` without a NoData tag, record the
  override before standardization.
- Standardized rasters should preserve missing cells as floating NoData.
- Overlay inputs must use a shared validity mask or explicitly document why masks
  differ.
- Any cell missing from one required criterion must remain missing in the
  weighted-overlay score.

### Diagnostics Before Overlay

Run before a raster is allowed into overlay: single-band check, CRS presence,
transform/resolution/width/height, NoData metadata or override, per-raster issue
list, grid compatibility against the chosen reference, output path and processing
command record. For V1 terrain derivatives, compatibility with the V1 reference
grid rule.

Overlay is blocked unless:

- every raster overlay input is single-band;
- CRS is present and compatible with the selected model-unit branch;
- transform, resolution, width, and height match for pixel-level raster overlay;
- NoData is recorded either as metadata or an explicit override;
- per-raster issues are empty, or each issue has a documented waiver;
- CHIRPS handling follows the selected model-unit branch.

### Standardization Rules

- Use fixed bounds when indicators must remain comparable across time,
  sub-basins, or countries.
- Use inferred min-max bounds only for a controlled single-slice diagnostic run.
- Record whether higher standardized values mean higher hazard or susceptibility
  contribution.
- Use the `--invert` rule only when lower raw values should become higher
  standardized scores.
- Record clipping counts and input min/max from the standardization diagnostics.

### Output And Handoff Rules

- Raw downloads stay under `data/raw/<dataset_id>/`.
- Temporary downloads stay under `data/tmp/<dataset_id>/`.
- Processed rasters, vector outputs, maps, and diagnostics stay under `outputs/`.
- Public-safe release packages must not depend on root `context/`, `data/`, or
  `outputs/`.
- Internal handoff notes may summarize source links and diagnostics, but must
  not copy raw data.

### Minimum First Real-Data Run

1. one approved outlet-based boundary or approved proxy mask;
2. one SRTM-derived terrain layer;
3. one rainfall summary handled through the selected model-unit branch;
4. raster diagnostics for every produced raster input;
5. standardization diagnostics for every overlay input;
6. a statement that the output is workflow or preliminary susceptibility only.

## 5. Runbook

### Deliverable pipeline (`ifpm-flood-pipeline/`)

```bash
cd ifpm-flood-pipeline
uv sync --extra geospatial           # install with geospatial deps
uv run pytest                        # 51 tests, 0 skipped with geospatial extra
uv run ruff check . && uv run ruff format .
# CLI: ahp, run, standardize, raster-diagnostics, zonal-score
```

### Workspace pipeline (`bin/pipeline.py` DAG runner)

```bash
.venv/bin/python bin/pipeline.py list                  # list all stages
.venv/bin/python bin/pipeline.py dot                   # render DAG
.venv/bin/python bin/pipeline.py run --target factors  # run a stage
.venv/bin/python bin/pipeline.py run --no-deps <task>  # run one task without deps
.venv/bin/python bin/pipeline.py run --force <task>    # force rerun
```

See `bin/README.md` for the full 7-stage map (acquire → factors → criteria →
scenarios → visualize → package → investigate).

### Terminology gate (binding before any mentor/boss-facing send)

```bash
.venv/bin/python bin/check_active_terminology.py       # must pass
```

### Workspace boundary check (binding)

```bash
bash bin/validate-boundary.sh
```

### Reference grid gate (binding before any V1 standardization/scoring/overlay)

```bash
.venv/bin/python bin/package/check_v1_raster_grid.py
```

## 6. Known Issues

- V1/V2 R-factor and USLE A products are deprecated; do not regenerate the old
  workflow. See `RESULTS.md` §R-factor.
- PE1 is `engineering_pilot`, not research-selected; replace if the mentor names
  a Peru site.
- PE1 and V1 reference grids are separate (EPSG:32718 vs EPSG:32735); do not
  cross-overlay without reprojecting to a shared grid.
- 16 hits of the deprecated `R-invariant` shorthand remain in the dead V2
  R-factor set; deferred until V2 resumes.

## Lineage

Absorbs content from:
- `execution_status_policy.md` (full claim-level ladder + sub-rules)
- `real_data_execution_preflight_gate.md` (full gate: scope split, IFPM-D01/D06,
  Step S1-S5, go/no-go criteria)
- `real_data_preprocessing_design.md` (full preprocessing design: grid/CRS/
  resampling/NoData/standardization rules)
- `bin/README.md` (runbook summary)
- `v1_terrain_reference_grid_rule.md` and `peru_pilot_terrain_reference_grid_rule.md`
  (reference-grid rules — those files remain the authoritative grid-spec source)
