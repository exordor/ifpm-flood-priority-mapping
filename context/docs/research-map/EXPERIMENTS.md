# Experiments

Status: active. Master registry of every experiment_id, joined to IFPM-NNN task
IDs, status, claim level, and result summary. Per-experiment detail lives in
`RESULTS.md` and in each `outputs/<experiment_id>/handoff.md`.

Naming convention: `boundary_id / experiment_id`. `boundary_v1` is the
Zimbabwe prototype boundary. The active Peru boundary is now
`peru_secocha_a7367_reference_extent_v1`, a provisional reference window for
Secocha. The former Peru boundary `peru_hybas_l7_6070641200` and its
`outputs/srtm_1arcsec_peru_pilot/` experiments are frozen from 2026-08-09;
they remain readable as the previous-area baseline but are not active and must
not receive new model writes. `boundary_v1` remains secondary/background unless
explicitly reopened.

## Current mainline focus (2026-08-09)

Peru-first work should now build on
`peru_secocha_a7367_reference_extent_v1`. Boundary activation and the data
coverage audit and five-criterion rerun are complete. The rerun uses a Secocha
SRTM tile, SoilGrids K window, CHIRPS extraction, a zero-feature SERNANP layer-0
query, reused WorldCover/WorldPop/Geofabrik Peru sources, and an external
INGEMMET mining overlay. The area switch did not change the Supervisor v07
weights. A semi-automatic Map 7 event candidate and an original INGEMMET A7367
hazard-polygon query are available; independent observed-footprint confirmation
and coverage-aware validation remain outstanding.

## Active Secocha experiments (`outputs/peru_secocha_a7367_reference_extent_v1/`)

| experiment_id | IFPM-NNN | status | claim_level | result_summary | handoff |
|---|---|---|---|---|---|
| `secocha_area_activation` | scope transition | complete | diagnostic_only | A7367 Map 7 30 km² reference window activated; previous Peru boundary frozen with checksum-bound key artifacts | `outputs/peru_scope/active_peru_research_area.json` |
| `secocha_data_coverage_audit` | data readiness | complete | diagnostic_only | Source gaps closed or explicitly bounded; SERNANP national definitive layer 0 has a confirmed zero-feature result within 25 km | `outputs/peru_secocha_a7367_reference_extent_v1/source_acquisition/source_manifest.json` |
| `supervisor_full_spec_v07_secocha` | active mainline | complete | provisional | Five-criterion PIM on the Secocha 30 m grid with unchanged Supervisor v07 weights and strict NoData common support; 15.65% of valid cells are High and none are Very High under fixed 0.2 intervals; mining remains external | `outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios/run_manifest.json` |
| `secocha_chain_quality_assurance` | verification | complete | The final PIM and five main criteria are grid-compatible and bounded 0-1; PIM valid coverage is 97.20%; prior Peru key artifacts retain frozen hashes; current QGIS workspace and portable packages load 30/30 layers | `outputs/peru_secocha_a7367_reference_extent_v1/quality_assurance/chain_validation.json` |
| `secocha_a7367_map7_event_digitization` | historical validation | complete candidate | validation_candidate | Two explicit 5 February Map 7 classes extracted separately and unioned; candidate area 0.211 km², PIM coverage 66.2%, High share 19.1% versus 15.6% study-wide; QGIS package now loads 30/30 layers including original INGEMMET polygons | `outputs/secocha_2023_validation/observed_hazard/digitization_manifest.json` |

## Secondary Zimbabwe experiments (`outputs/boundary_v1/<experiment_id>/`)

| experiment_id | IFPM-NNN | status | claim_level | result_summary | handoff |
|---|---|---|---|---|---|
| `criteria_stack_v0_2` | IFPM-089 | in_progress | provisional | Honest-label 5-criteria stack; mining/exposure hardening planned not implemented | `outputs/boundary_v1/criteria_stack_v0_2/handoff.md` |
| `priority_scenarios_v0_2` | IFPM-089 | complete | sensitivity_scenario | 4 weight scenarios on v0.2 criteria; 431.907 km² selected in the top 20% under all scenarios | `outputs/boundary_v1/priority_scenarios_v0_2/handoff.md` |
| `rainfall_sensitivity_v0_3` | IFPM-090 | complete | sensitivity_scenario | Adds rainfall_climatology (CHIRPS coarse-to-grid, A-010); effective res ~5 km | `outputs/boundary_v1/rainfall_sensitivity_v0_3/` |
| `hotspot_exposure_diagnostic_v0_3` | IFPM-090 | complete | diagnostic_only | Tests co-location of v0.2 top-20% priority areas with exposure indicators; weak co-location | `outputs/boundary_v1/hotspot_exposure_diagnostic_v0_3/` |
| `rainfall_exposure_v0_4` | IFPM-097 | complete | sensitivity_scenario | Zimbabwe direct weights only; Sediment uses independent K/LS/C 0.35/0.35/0.30; 96.609% five-criterion common-support coverage and 3.391% remains unscored | `outputs/boundary_v1/rainfall_exposure_v0_4/` |
| `mining_decay_priority_sensitivity` | IFPM-074 track | complete | sensitivity_scenario | Decay-function sensitivity on mining proximity; structure test only | `outputs/boundary_v1/mining_decay_priority_sensitivity/` |

## Frozen previous-area Peru experiments (`outputs/srtm_1arcsec_peru_pilot/`)

Status for every entry in this section: historical/frozen as of 2026-08-09.
Existing results and checksums are preserved; do not rerun into this root.

| experiment_id | IFPM-NNN | status | claim_level | result_summary | handoff |
|---|---|---|---|---|---|
| `peru_hybas_l7_6070641200_criteria_stack` (3-criteria) | IFPM-093 | complete | provisional | First Arequipa Region stack: flood, erosion, land cover | `outputs/srtm_1arcsec_peru_pilot/criteria_stack/` |
| `peru_hybas_l7_6070641200_criteria_stack` (5-criteria) | IFPM-094 | complete | provisional | +mining (OSM indicator) +exposure (OSM roads) | `outputs/srtm_1arcsec_peru_pilot/criteria_stack/` |
| `peru_hybas_l7_6070641200_criteria_stack` (component rasters, INGEMMET mining) | IFPM-095/096 | complete | provisional | component inputs for flood, sediment, land use/ASM, environmental, socioeconomic, rainfall; includes TWI/drainage and LS/C diagnostic sublayers | `outputs/srtm_1arcsec_peru_pilot/criteria_stack/` |
| `peru_hybas_l7_6070641200_environmental_sensitivity_v0_1` | IFPM-096 | complete | provisional | WorldCover/OSM water-wetland context 0.60 plus SERNANP national definitive protected-area layer 0 context 0.40; layer 0 checked, with no geometry in Arequipa Region + 5 km; other protected-area layers not queried | `outputs/srtm_1arcsec_peru_pilot/environmental_sensitivity_v0_1/` |
| `peru_hybas_l7_6070641200_exposure_indicators` | IFPM-096 gap closure | complete | provisional | 0.45 road/access + 0.55 infrastructure exposure; infrastructure is an explicit 0.50 WorldPop population + 0.50 OSM mapped-building placeholder. INEI poverty and OSM health remoteness remain diagnostic context outside the PIM. | `outputs/srtm_1arcsec_peru_pilot/exposure_indicators/` |
| `peru_hybas_l7_6070641200_soil_k_factor` | criteria governance | complete | provisional | Corrected SoilGrids source-window extraction; K aligns to Arequipa Region and is bilinear-aligned to 30 m while retaining a 250 m effective-resolution warning; 98.8674% Arequipa Region coverage | `outputs/srtm_1arcsec_peru_pilot/soil_k_factor/` |
| `peru_hybas_l7_6070641200_priority_scenarios` | IFPM-093/094/095/096 | complete | sensitivity_scenario | Peru direct weights only; Sediment uses K/LS/C 0.30/0.45/0.25 and Land Use uses a value function distinct from C; 521.356 km² in the highest-priority quintile; 95.0998% five-criterion common-support coverage; 4.9002% remains unscored with LS/K/other causes exposed by support rasters | `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/` |
| `peru_hybas_l7_6070641200_gap_closure_analysis` | Peru evidence-gap work | complete | diagnostic_only | WorldPop accounting is checksum-bound in the output CSV and remains endogenous. Of 25 SINPAD records, 12 are scoreable and 2 are selected; 1 of 4 flood-specific records is scoreable and none is selected. This is not validation. | `outputs/peru_gap_closure_analysis/` |
| `peru_hybas_l7_6070641200_criterion_dependency_diagnostics` | criteria governance | complete | diagnostic_only | Quantifies shared WorldCover dependence, road-led Socioeconomic ordering, water-led Environmental context, and selected-quintile changes under component-removal alternatives; does not recalibrate supplied AHP weights | `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/criterion_dependency_diagnostics.csv` |
| `peru_hybas_l7_6070641200_rainfall_criterion` | IFPM-096 | complete | sensitivity_scenario | CHIRPS latam Dec-Mar mean, bilinear to Arequipa Region 30 m grid and normalized from Arequipa Region boundary values only (A-012); effective resolution remains ~5 km | `outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/` |
| `peru_hybas_l7_6070641200_ls_factor` | IFPM-093 | complete | diagnostic_only | Arequipa Region LS hillslope mean 3.70 (vs V1 1.563) | `outputs/srtm_1arcsec_peru_pilot/ls_factor/` |
| `peru_hybas_l7_6070641200_usle_soil_loss` | IFPM-093 | complete | provisional | Arequipa Region USLE A mean 8.74 t/ha/yr (LOW R=238.6); vs V1 0.50 | `outputs/srtm_1arcsec_peru_pilot/usle_soil_loss/` |

## Zimbabwe terrain/factor chain (legacy flat names — `outputs/srtm_1arcsec_zimbabwe_prototype/`)

| output group | IFPM-NNN | status | claim_level | result_summary |
|---|---|---|---|---|
| `terrain_preprocessing` | IFPM-052 | complete | diagnostic_only | V1 DEM EPSG:32735 30 m, elev 863-1531 m; slope 0-55.6°; valid fraction 1.0 |
| `hydrology_derivatives` | IFPM-075 | complete | diagnostic_only | Filled DEM, D8 flow dir, flow acc (max 4,036,878 cells = 3633 km²), TWI 3.13-27.23 |
| `ls_factor` | IFPM-077 | complete | diagnostic_only | LS hillslope mean 1.563, p95 5.511 (Moore-Nieber, channel-masked, capped 50) |
| `terrain_standardization` | IFPM-055 | complete | diagnostic_only | Lowland/low-slope/high-slope candidates, 2-98 pct min-max |
| `hydrology_standardization` | IFPM-084 | complete | mentor_review_ready (candidates only) | TWI + drainage proximity 0-1 candidates; grid_compatible=true |
| `k_factor` | IFPM-072 / criteria alignment | complete | provisional | Corrected SoilGrids spatial K aligned to the V1 30 m reference grid while retaining a 250 m effective-resolution warning; normalized layer used in the direct Zimbabwe Sediment criterion |
| `c_factor` (esa_worldcover_2021_v1_methodology) | IFPM-076 | complete | diagnostic_only | V1 area-weighted mean C 0.0429; lookup after mode resampling 10m→30m |

## Zimbabwe prototype iterations (legacy flat names)

| experiment_id (legacy) | IFPM-NNN | status | claim_level | result_summary | handoff |
|---|---|---|---|---|---|
| `v1_autonomous_prototype_v0_1` | IFPM-087 | complete (frozen baseline) | provisional | 5 criteria, 4 scenarios; 436.907 km² selected in the top 20% under all scenarios; mean σ 0.04697 | `outputs/v1_autonomous_prototype_v0_1/` (process note archived) |
| `v1_working_boundary` | IFPM-049 | complete | provisional | V1 area 3689.484 km²; Mzingwane Dam + Esigodini inside; Gwanda outside | `outputs/v1_working_boundary/v1_working_boundary_manifest.csv` |
| `v1_full_methodology_evidence_sweep` | IFPM-059 | complete (superseded) | diagnostic_only | 7-criteria evidence matrix; superseded by v0.2 honest labels | (process note archived) |
| `v1_terrain_mentor_package` | IFPM-056 | complete | mentor_review_ready | Low-slope susceptibility primary candidate; high-slope runoff alternative | `outputs/v1_terrain_mentor_package/` |
| `v1_usle_soil_loss` | IFPM-077 | **DEPRECATED** | n/a (deprecated) | A-mean 0.50 t/ha/yr; ~87% < 1 t/ha/yr; A absolute R-dependent and deprecated | `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md` |

## R-factor investigation experiments — DEFERRED RECORD (out of critical path since 2026-07-06, see D-RFACTOR-QUARANTINE)

These experiments are preserved as a deferred technical record. R-factor is no
longer on the current Peru critical path: the active Sediment criterion combines
normalized K, LS, and C with local AHP subweights and does not calculate USLE A.
Reopen R only if a quantitative soil-loss rate (ton/ha/yr) becomes necessary.

Outputs at: `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/` and
`outputs/v1_usle_soil_loss/rfactor_empirical_era5/`.

| experiment_id | IFPM-NNN | status | claim_level | result_summary |
|---|---|---|---|---|
| `rfactor_method_exploration` | IFPM-081 | complete (deferred) | deferred | 6 literature methods on V1 CHIRPS; two incompatible families ~6× apart |
| `rfactor_empirical_era5` | IFPM-082 | complete (deferred) | deferred (was provisional lower bound) | ERA5 hourly EI30 R mean 358-506; supports lower range as independent check |
| `rfactor_full_verification` | IFPM-080/085 | complete | n/a (audit) | Hand-calc verification of all formulas; one sourcing inaccuracy fixed |
| `v2_rfactor_candidates` | IFPM-079 | **deprecated** | n/a (deprecated) | V2 smoother-R; premise invalid (bimodality was artifact); V2 A outputs removed 2026-07-01 |
| `chirps_v1_rainfall_comparison` | IFPM-058 | complete | mentor_review_ready | 561 CHIRPS inputs; recent annual + rainy-season anomaly both ~17.5%; pentad peak different pattern |

## Boundary discovery experiments (legacy flat names — most process notes archived)

| experiment_id | IFPM-NNN | status | result_summary |
|---|---|---|---|
| `hydrosheds_boundary_discovery` | IFPM-039 | complete | HydroBASINS Africa candidate HYBAS/PFAF ids; boundary not accepted |
| `zimbabwe_geoportal_subcatchments_comparison` | IFPM-041 | complete | Geoportal `Upper Mzingwane` ~7321.5 km²; HydroBASINS L7 inside covers 49.8% |
| `upper_mzingwane_fact_check` | IFPM-042/043 | complete | ~2138 km² reference has external support but no reusable geometry |
| `candidate_outlet_exploration` | IFPM-045/046 | complete (superseded) | C1 first-pass prior; demoted after mentor cue |
| `professional_outlet_review` | IFPM-048 | complete | V1 = Upper Mzingwane (~3689 km²) accepted with waiver; C1 demoted to machine prior |
| `peru_boundary_discovery` | IFPM-091 | complete | HydroBASINS SA candidates 2.8-14,300 km²; Arequipa Region selected by rule |

## Reporting / comparison packages (not modelling experiments)

| package | IFPM-NNN | status | claim_level | contents |
|---|---|---|---|---|
| `peru_report_figure_chain` | (figure governance) | current | mixed; see manifest | Only current reporting entrypoint: raw inputs, five criteria, direct-weight PIM, evidence context, contribution explanation, and SINPAD diagnostic |
| `zimbabwe_peru_prototype_comparison` | IFPM-097 | archived after D-PERU-FIRST | sensitivity_scenario | Historical 2×2 comparison board under the 2026-07-11 figure-governance archive |
| `mentor_boss_priority_explanation` | (july18 work) | archived | mentor_review_ready | Historical per-pixel winning criterion and boss-process package under the figure-governance archive |
| `mentor_boundary_decision` | IFPM-040 | archived | mentor_review_ready | Historical mentor-facing boundary decision package under the figure-governance archive |
| `mentor_voi_rainfall_intake` | IFPM-086 | complete | diagnostic_only | Mentor Voi rainfall archive intake; daily records, no strict EI30 |
| `teams_handoff` | (various) | complete | mentor_review_ready | Mentor Teams message drafts |

## Legacy-name → convention mapping

| Legacy flat path | Should be read as |
|---|---|
| `outputs/v1_autonomous_prototype_v0_1/` | `boundary_v1 / autonomous_prototype_v0_1` |
| `outputs/v1_autonomous_prototype_v0_2/` | `boundary_v1 / criteria_stack_v0_2` inventory |
| `outputs/srtm_1arcsec_zimbabwe_prototype/*` | `boundary_v1 / <derivative>` (terrain chain) |
| `outputs/chirps_v3_zimbabwe_prototype/*` | `boundary_v1 / rainfall_*` |
| `outputs/srtm_1arcsec_peru_pilot/*` | `peru_hybas_l7_6070641200 / <derivative>` (treated as a parallel boundary_id) |
| `outputs/esa_worldcover_2021_v1_methodology/` | `boundary_v1 / c_factor` |
| `outputs/soilgrids_250m_sediment_candidate/` | `boundary_v1 / k_factor` |

Legacy filenames are kept as compatibility artefacts; new scripts use explicit
`boundary_id` and `experiment_id` fields per AGENTS.md §Version naming convention.

## Excluded from this registry

- Pure factor-processing outputs that have no experimental claim (raw manifests,
  tile inventories, anchor checks).
- Archived/superseded process notes (`_archive/superseded_*`).
- Deprecated product directories marked with `DEPRECATED_*.md`.

## Lineage

Absorbs content from:
- `task_progress_board.md` (every IFPM-NNN Done entry, condensed to registry rows)
- `boundary_v1_criteria_stack_v0_2_2026-06-29.md` (criteria_stack_v0_2 scope)
- `rfactor_investigation_consolidated.md` §Outputs and tooling
- Directories under `outputs/`


## 2026-09-08 Abzucht HQ100 overlay

- `boundary_id`: `goslar_wrrl_water_bodies_reference_v1`;
  `experiment_id`: `abzucht_hq100_overlay_v1`; status: `diagnostic_only`.
- User scope: compare flood evidence without restricting it to the 2017 event.
- Command: `.venv/bin/python bin/analysis/compare_abzucht_hq100.py`.
- Inputs: existing NLWKN Abzucht HQ100 polygon (`uesg_id=917`, 2026 regulatory
  product, local August snapshot) and existing PIM/criterion rasters. Weights
  and model unchanged. Original HQextrem PDF is not used as vector ground truth.
- Outputs: `outputs/goslar_wrrl_water_bodies_reference_v1/abzucht_hq100_overlay_v1/`
  contains comparison PNG/SVG, CSV statistics and contributions, GeoPackage,
  categorical GeoTIFF and input-hash manifest.
- Covered HQ100 mean PIM 0.4754, versus 0.4177 in the outside 1 km ring and
  0.4790 across the full valid project. PIM >=0.6 shares: 8.31%, 1.11%, 4.86%.
  This supports higher scores relative to nearby context, not a project-wide
  mean increase or event-validation result. The ring is not a matched control.
- Exact polygon area 0.49547 km²; 60.03% intersects the project boundary.
  Cell-center sample: 337 valid, 224 NoData. NoData excluded, not low priority.
  All-touched sensitivity changes the valid count to 831 and high share to
  about 6.4%, while mean remains about 0.474. Narrow-zone pixel selection matters.
- Largest mean contribution is the flood-conditioning criterion; land cover
  also raises the HQ100 mean relative to the ring. Erosion contributes less.
- Checks: input hashes, exact reference grids, weighted reconstruction,
  NoData/threshold-edge and shifted-grid tests; two independent reviews found
  no P1/P2 issues. Keyed figure labels address a low-priority maintainability
  observation. PNG/SVG rendered and visually checked; grey contrast warning
  from asset audit reviewed as legible.
- Remaining scope: outside-boundary portion has no PIM; native HQextrem depth
  data not integrated. No flood-probability or observed-event accuracy claim.


## 2026-09-08 expanded Abzucht coverage experiment

- Classification: wrapper/helper `TOOLING`; outputs `OUTPUT`; status `diagnostic_only`.
- User-approved expansion: original boundary union complete Abzucht HQ100
  polygon plus a 1 km buffer. This comparison extent is not a new catchment.
- `boundary_id=goslar_abzucht_expanded_reference_v1`, `experiment_id=frozen_scale_v1`.
- Area: 153.778655 -> 160.205453 km². Output tree:
  `outputs/goslar_abzucht_expanded_reference_v1/frozen_scale_v1/`.
- Reproduce: `.venv/bin/python bin/analysis/run_abzucht_expanded.py`.
  This wrapper imports the existing chain with isolated output paths; it
  reconstructs seven normalization anchors on original inputs with raster
  writes disabled. Replay requires exact grid/support and numeric agreement.
  It then fixes those bounds, weights and 0.2-wide score classes, keeps the
  baseline 30 m pixel lattice and recomputes expanded buffered hydrology.
- Existing inputs suffice; no remote data downloaded. CLMS loss is regenerated
  from native 2018/2024 mosaics. Both source hashes plus rainfall inputs,
  source code and frozen parameters are pinned in expansion_manifest.json.
- HQ100 cell-center coverage grows from 337/561 to 561/561. Complete-region
  mean 0.469790; PIM >=0.6 share 6.06%; outside 1 km ring mean 0.418965.
  The old covered subset rescored mean is 0.475134; added subset mean 0.461749.
- Existing area mean absolute score change 0.0000323, maximum 0.103230;
  109 common cells change by more than 0.01. Hydrology/proximity can change
  locally even with frozen normalization. old_area_score_change.tif records it.
- IMPORTANT: scoring coverage is not full component support. HQ100 has valid
  K in 239/561 cells, population in 255/561, hillslope LS in 446/561, TCD in
  561/561. Four availability rasters preserve these distinctions. Legacy
  within-criterion averaging renormalizes available components; retained for
  controlled comparability, not an assertion that missing inputs are zero.
  Population absent-record semantics remain unresolved. LS excludes channels
  by the inherited method, so absence is not uniformly missing source data.
- Original baseline rasters/boundary are unchanged (seven hash checks).
  Six focused tests pass, including fixed-anchor invariance, NoData and shifted
  grids. Independent domain and engineering reviews found no remaining P1/P2;
  38 non-buffered rasters match the expanded grid. PNG/SVG preview checked.
- Main artifacts: expanded_boundary.gpkg, expansion_manifest.json,
  frozen_normalization.json, availability/change rasters, chain/priority_scenarios,
  overlay/abzucht_hq100_comparison.png, overlay/comparison.csv.
- Initial attempted run errors (resolved): missing `_lib` import path; inherited
  slope stage cropped empty edge rows and failed exact grid equality. Added
  bin import path and explicit reference-aligned slope calculation. Unused
  legacy bare-soil lineage removed; strict replay support gate strengthened.


## 2026-09-08 filled Abzucht display rectangle

- User-requested map rectangle: HQ100 bounds plus 500 m per side, added to
  previous project/buffer union; `goslar_abzucht_display_rectangle_v1 / frozen_scale_v1`.
- Command: `.venv/bin/python bin/analysis/run_abzucht_expanded.py --fill-display-rectangle`.
- Output: `outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1/`.
  `display_rectangle_priority.tif` contains only the display rectangle on the
  preserved grid; overlay PNG/SVG and coverage manifests accompany it.
- Complete scoring support: 29,315/29,315 rectangle cell centers; project
  union area 164.689707 km². HQ100 mean 0.469790, high share 6.06%.
- Raw component coverage remains partial (K 61.4%, population 26.1%, LS 96.6%,
  TCD 100% within the rectangle). Legacy available-component averaging remains
  explicit. This fills geographic scoring coverage, not source-data gaps.
- Status `diagnostic_only`. No new downloads; fixed baseline anchors and
  weights. Baseline hashes unchanged; isolated outputs. Six tests and two
  independent review angles pass; rectangle raster all-finite check passed.


## 2026-09-09 comparison explanation improvements

- User goal: complete flood-subindicator comparison, component availability,
  and three geographically located cases with road context and contributions.
- `goslar_abzucht_display_rectangle_v1 / explanation_v1`, `diagnostic_only`.
  TOOLING: `bin/analysis/explain_abzucht_comparison.py`; outputs remain under
  `outputs/goslar_abzucht_display_rectangle_v1/explanation_v1/`.
- Command: `.venv/bin/python bin/analysis/explain_abzucht_comparison.py`.
- Three PNG/SVG figures, score CSV, component count GeoTIFF, cases JSON/GPKG,
  Chinese READING_NOTE and hash manifest generated. No scores/weights changed.
- FH mean HQ100/full 1 km ring: 0.507/0.373; PIM 0.470/0.419. Full ring extends
  beyond the displayed rectangle and is not a matched statistical control.
- All 14 modeled components available in 1693/29315 (5.78%) rectangle cells.
  Availability counts span 10-14; this is not a quality or accuracy measure.
- Cases selected nearest group PIM medians with deterministic ties. A's low
  erosion contribution uses only C because K/LS are unavailable; no physical
  low-erosion conclusion is supported by that value alone.
- Nine focused tests pass. Component/criterion/PIM reconstruction checked,
  input hashes verified. Two independent reviews passed after correcting
  availability legend range and overlapping label. All three images previewed.

## 2026-09-14 Abzucht input-gap experiment

- `goslar_abzucht_display_rectangle_v1 / gap_repair_v1`: diagnostic audit plus
  separate GHSL2020 population and flat-slope TWI sensitivity scenarios.
- Commands: `.venv/bin/python bin/acquire/pull_abzucht_ghsl_population.py`, then
  `.venv/bin/python bin/analysis/repair_abzucht_gaps.py`.
- One public 41 MB GHSL tile pinned under `data/raw/ghsl2020_abzucht_population/`;
  registry: `context/docs/data-management/registry/ghsl2020_abzucht_population.md`.
- Outputs: `outputs/goslar_abzucht_display_rectangle_v1/gap_repair_v1/` contains
  native/30 m population rasters, candidate PIM rasters, CSV comparisons,
  coverage and change figures, READING_NOTE and input/output hash manifest.
- National census replay yields no extra supported model pixels. Unpublished
  census cells remain unknown; population improvement comes from full-component
  GHSL substitution, not recovered census observations or zero imputation.
- Rectangle population availability 26.05% to100%; all14 components 5.78% to
  59.77% with GHSL plus0.1-degree flat-slope scenario. SoilK and channel-excluded
  LS unchanged. TWI67 formerly missing rectangle cells are numerical scenarios.
- Rectangle PIM mean0.425 to0.397; HQ1000.470 to0.445. These are source/method
  effects, not evidence of reduced flood risk. Original weights/anchors retained.
- Population resampling mass discrepancy0.00352%; baseline replay max1.19e-7.
  Fourteen focused tests and figure audit pass. Two independent reviews completed;
  source-cache hash-verification P2 fixed and re-reviewed. Original inputs preserved.

## 2026-09-14 return to the original Abzucht comparison question

- `goslar_abzucht_display_rectangle_v1 / original_question_v1`, diagnostic presentation
  using `frozen_scale_v1` only; GHSL replacement stays a separate sensitivity branch.
- Command: `.venv/bin/python bin/analysis/present_abzucht_original_question.py`.
- Main PNG/SVG/PDF maps three overlap categories with existing A/B/C points and
  contributions; category GeoTIFF, summary CSV, Chinese explanation, English draft
  and hash manifest are under `outputs/goslar_abzucht_display_rectangle_v1/original_question_v1/`.
- HQ100 high34/561 (6.06%); inside below threshold527; outside high386 within the
  display rectangle. No accuracy/false-alarm interpretation. Scores and weights unchanged.
- Source hashes, grids, case positions and contributions checked on execution;
  two independent reviews found no P1/P2. Figure preview corrected legend placement.

## 2026-09-14 user-requested Abzucht weight sensitivity

- `goslar_abzucht_display_rectangle_v1 / weight_sensitivity_v1`, status
  `sensitivity_scenario`; local Goslar branch, without changing Secocha or the
  frozen Abzucht baseline. User explicitly requested iterative weight adjustment.
- Command: `.venv/bin/python bin/analysis/tune_abzucht_weights.py`.
  Tooling and focused tests: `bin/analysis/tune_abzucht_weights.py`,
  `tests/test_abzucht_weight_sensitivity.py`.
- Two rounds: flood weights 34/45/55/65/75/80%, then 76–79%; other four weights
  shrink proportionally. Fixed input criteria, support, normalization and 0.6
  threshold. A 100% endpoint is explanatory only, excluded from selection.
- Objective: maximize HQ100-inside minus full 1 km outside-ring high-score share.
  80% is best in this bounded search: inside 6.06% to 16.93%, outside 1.02% to
  2.94%, gap 5.04 to 14.00 percentage points. It is at the search boundary;
  no interior optimum established. The 80% cap retains 20% non-flood influence
  as a candidate policy, not a validated scientific constraint.
- Selection is threshold-dependent: at 0.5, 76% ranks best; at 0.7, no tested
  candidate <=80% has any HQ100 cells above threshold. HQ100 now guides tuning
  in this experiment and cannot serve as its independent validation.
- Outputs under `outputs/goslar_abzucht_display_rectangle_v1/weight_sensitivity_v1/`:
  11 score rasters, change/driver rasters, weight/comparison/threshold/contribution
  tables, PNG/SVG/PDF comparisons, Chinese note and hash manifest. Missing raw
  components remain an inherited limitation; coverage does not establish data quality.
- Source hashes, exact grids, baseline replay and reopened raster metrics checked;
  20 focused Abzucht tests and workspace boundary check pass. Two independent
  reviews prompted threshold-qualified wording and staged publication fixes.

## 2026-09-14 Abzucht input completion and weight recheck

- `goslar_abzucht_display_rectangle_v1 / input_completion_v2`, status
  `sensitivity_scenario`. User explicitly requested maximum-effort input completion.
- Raw acquisitions: 16 official archived SoilGrids2017 property/depth clips plus
  XML (389,541 bytes), and official BK50 soil-type polygons (352,256 bytes).
  Registries: `registry/soilgrids2017_abzucht.md` and
  `registry/lbeg_bk50_abzucht_probe_2026-09-14.md` under data-management.
- Commands: `.venv/bin/python bin/acquire/pull_abzucht_soilgrids2017.py`,
  `.venv/bin/python bin/acquire/pull_abzucht_bk50_context.py`,
  `.venv/bin/python bin/analysis/complete_abzucht_inputs.py`.
- Entire population component uses previously pinned GHSL2020; entire soil
  component uses Williams K derived from archived2017 texture/carbon predictions,
  explicit 0–30cm depth integration and SI conversion. Old normalization anchors
  retained; version differences and saturation counts reported. Neither source
  replacement is claimed to recover missing current-version observations.
- HQ100: population255→561/561; soil239→561/561. All14 finite77→446/561 under
  hillslope LS, while all applicable inputs89→561/561. The115 channel cells retain
  LS not-applicable and explicit K/C=.5/.5; missing any applicable input blocks
  scoring. A separate all-terrain LS counterfactual has561/561 all14 finite.
- Soil coverage outside HQ100 remains incomplete: ring21,120/21,198;
  rectangle29,136/29,315. Residual gaps remain NoData, with land-cover diagnostics.
  BK50 has soil-type context for561/561 HQ100 cells but provides no numerical K;
  no values inferred from soil names. Raw geometry preserved, repair only in memory.
- Four data/method branches ×10 weight candidates re-run on common support.
  At fixed0.6 cutoff,80% remains best in tested34–80% range. HQ100 high share
  at80%: original16.93%, population-only13.19%, soil+hillslope17.29%,
  all-terrain LS20.32%. Different LS applicability is not a recovered observation.
- Outputs: raw/normalized K, input/criterion/score rasters, applicability and
  residual-gap masks, coverage and weight tables, four PNG/SVG/PDF figure sets,
  Chinese note and hash manifest under the experiment directory.
- 25 focused tests pass; raw cache and output rasters reopened; boundary check
  passes. Two independent reviews addressed derived-data placement and reporting
  precision. No original baseline, Secocha output, or approved weight was replaced.

## 2026-09-14 Abzucht high-cell distance diagnostic

- `goslar_abzucht_display_rectangle_v1 / spatial_offset_v1`, `diagnostic_only`.
  Command: `.venv/bin/python bin/analysis/diagnose_abzucht_spatial_offset.py`.
  Same 30 m grid, display rectangle and PIM ≥0.6 threshold in original 34%,
  completed-input 34%, and completed-input 80% scenarios.
- Original 34%: 420 high cells, 34 centres inside HQ100, 386 outside; 34
  outside high cells have squares touching HQ100, while 291 are >150 m away by
  centre. All 561 HQ100 centre cells are scored in all three scenarios.
  The outside highs are not automatically prediction errors: HQ100 is one
  modeled Abzucht scenario and PIM is a multi-criterion priority score.
- Outputs: per-cell distances, distance-bucket and scenario tables, three
  classified rasters, three PNG/SVG/PDF figure sets, Chinese interpretation note,
  and hash manifest in `outputs/goslar_abzucht_display_rectangle_v1/spatial_offset_v1/`.
  Model-stream overlap is endogenous to the drainage-proximity indicator and
  does not independently validate river location.

## 2026-09-14 Abzucht independent-river alignment diagnostic

- `goslar_abzucht_display_rectangle_v1 / river_alignment_v1`, `diagnostic_only`.
  Command: `.venv/bin/python bin/analysis/check_abzucht_river_alignment.py`.
  Existing official WRRL Abzucht/Oker segments, original fixed 34% PIM, the
  DEM-derived t500 drainage, HQ100, and completed-input 34% PIM are compared on
  the same 30 m grid. No weight or data source was changed.
- Along 6.50 km of official Abzucht line inside HQ100, 217 length-weighted
  30 m samples have median/p90 distances of 47.1/118.4 m to the nearest model
  drainage cell centre; 138/217 are within 60 m. Seventeen runs have at least
  three consecutive samples >30 m from any model drainage cell, the longest
  about 750 m. These are network-proximity distances, not observed river-position
  errors or one-to-one Abzucht-channel alignment. The selected WRRL source
  features carry date 2015-12-21.
- Among 291 original high cells >150 m outside HQ100, seven lie within 60 m of
  the two mapped WRRL river segments and 281 lie >90 m from both. WRRL does not
  inventory every small ditch; this does not establish that those cells lack
  real channels. Three rule-selected cases expose original criterion
  contributions and completed-input score sensitivity.
- Outputs: map (PNG/SVG/PDF), official-line samples and sustained-gap runs, original high-cell
  distances, case table, Chinese note, summary and hashes under
  `outputs/goslar_abzucht_display_rectangle_v1/river_alignment_v1/`.

## 2026-09-14 Abzucht finer-watercourse and orthophoto check

- `goslar_abzucht_display_rectangle_v1 / atkis_dop_check_v1`, `diagnostic_only`.
  Command: `.venv/bin/python bin/analysis/check_abzucht_atkis_dop.py`.
  LGLN ATKIS Basis-DLM watercourse axes and three DOP20 context images are kept
  outside PIM scoring. The DOP metadata date applies to each queried image
  center point only; no 2017 flood extent is inferred from these images.
- The 217 WRRL Abzucht samples lie a median 0.06 m from an ATKIS axis. All 140
  samples in the 17 previously identified model-drainage gap runs lie within
  15 m of an ATKIS axis. ATKIS and WRRL main-line geometry is nearly coincident,
  so these are not two independent confirmations of river position.
- Of 291 original high cells more than 150 m outside HQ100, 129 are within
  60 m of an ATKIS axis; 129 remain over 90 m from an axis. Case C is about
  309 m from the nearest mapped axis. These distances test spatial proximity,
  not flood occurrence or underground drainage. Output tables, three aerial
  overlays, interpretation note and hash manifest are in
  `outputs/goslar_abzucht_display_rectangle_v1/atkis_dop_check_v1/`.

## 2026-09-14 Goslar multi-river comparison, original baseline

- `goslar_abzucht_display_rectangle_v1 / multiriver_comparison_v1`, `diagnostic_only`.
  Explicit user scope: existing original model support, original population/soil,
  fixed normalization and weights; excludes GHSL and weight-sensitivity branches.
- Command: `.venv/bin/python bin/analysis/compare_goslar_multiriver.py`.
  Focused checks: `.venv/bin/python -m unittest discover -s tests -p test_goslar_multiriver.py`.
- Eight regulatory rivers inventoried: Abzucht, Grane, Oker, Innerste overlap;
  Wedde, Radau, Ecker, Schamlah have no model coverage. Six Oker/Innerste HWRM
  return-period products remain separate. Regulatory dates are not event dates.
- Output folder: `outputs/goslar_abzucht_display_rectangle_v1/multiriver_comparison_v1/`.
  Contains 11 PNG/SVG two-panel maps, 336 spatial-statistic rows, source/coverage
  inventory, criterion contributions, 26 representative cases, QGIS GeoPackage,
  Chinese explanation and checksummed manifest. Figures contain neutral labels.
- Center inclusion and 500/1000/2000 m clean rings, plus all-touched sensitivity.
  Rings exclude all acquired official flood footprints; NoData is excluded.
  All ten covered products have positive flood-indicator mean contrasts in six
  settings. PIM contrast varies by river; Abzucht remains positive. This is
  descriptive scenario correspondence, not flood prediction accuracy.
- Abzucht regression: 561 cells, 34 at PIM>=0.6, mean 0.4697896122.
  Original input and score hashes verified; no model writes. Two Oker HQ20
  self-intersections repaired only in memory with negligible area change,
  recorded in output manifest; neither repaired polygon overlaps model support.
- Independent domain and engineering reviews checked masks, counts, source
  dates, deduplication, cases and unchanged inputs. Review prompted neutral
  regulatory labels, whole-zone driver decomposition and recursive lineage checks.

## 2026-09-14 Multi-river fixed-input flood weights 50/60/70 percent

- `goslar_abzucht_display_rectangle_v1 / multiriver_weights_50_60_70_v1`,
  `sensitivity_scenario`; explicit user request to increase flood criterion weight.
- Command: `.venv/bin/python bin/analysis/compare_multiriver_weights.py`.
  Uses original frozen criteria/population/soil and preceding multi-river geometries,
  cleaned rings, six inclusion/radius settings. Non-flood weights shrink proportionally.
- Outputs: three GeoTIFF scenarios, 15 PNG/SVG pairs, weights, 336 statistical rows,
  56 main comparison rows and note/manifest under the named output folder.
- Original 34% scenario replays preceding comparison; 183,028-cell support preserved.
  Mean contrasts increase, but high-score proportion contrasts do not improve uniformly.
  Abzucht improves; Grane is nonmonotonic; regulatory Oker and Innerste remain negative
  in high-score proportion contrast at 70%. No automatic weight selection.
- Six weight helper tests and five spatial comparison tests pass; all 30 figure assets
  audited and 15 map pairs previewed. Independent domain/math review verifies scores,
  masks and complete 34% replay. Original baseline/source files remain unchanged.

## 2026-09-14 Non-flood low-score semantics audit

- `goslar_abzucht_display_rectangle_v1 / component_semantics_v1`, `diagnostic_only`.
  Command: `.venv/bin/python bin/analysis/diagnose_multiriver_low_scores.py`.
- Output: per-river inside/ring component/raw summaries, WorldCover composition,
  effective component weights, K/LS/C normalization replay and Chinese reading note.
  No model edits. All input/output hashes verified; four normalization tests pass.
- Oker low scores primarily sediment0.046/landuse0.222; environmental0.910 and
  socioeconomic0.842 are high. Low slope/cover factors accord with current proxies,
  not a claim of low inundation risk. Innerste slope is higher than local ring;
  its 12-cell evidence cannot support a generic flatter-floodplain explanation.
- Semantic audit finds tree-cover loss mislabeled broadly as bare soil/vegetation,
  and static built/agricultural/road proximity mislabeled expansion. Interpretations
  corrected in note; legacy model fields left intact. Population gaps cannot be
  treated as absent people; intentional channel LS exclusion differs from missing input.
- Independent semantic and numeric review; replay max error below3e-8. Review prompted
  explicit anchor hashing and failure on finite-mask inequality. Local proxy validity,
  census blank-cell semantics and OSM completeness remain unverified.

## 2026-09-14 Input semantics follow-up

- `goslar_abzucht_display_rectangle_v1 / input_semantics_followup_v1`, diagnostic_only.
  Command: `.venv/bin/python bin/analysis/audit_multiriver_input_semantics.py`.
  14 display aliases, 126 component-scale/contribution rows, retained/excluded
  facility GeoPackage and distance summary; official census metadata hash/evidence.
- Corrected population interpretation: published omission may be true zero or CKM zero;
  nationwide extraction recovery adds no finite population cells in model support.
- Confirmed P2 legacy facility-distance edge truncation: rasterizing only within grid
  drops nearest existing school for all12 Innerste cells. Frozen mean0.010973 vs
  all-retained point-distance diagnostic0.477717; original raster independently
  reproduced within2.98e-8. Baseline unchanged; fix requires separate buffered-distance run.
- Tree-cover decline spans broad model-wide values (mean0.215, p95~0.968), so low
  Oker values do not establish global normalization failure. Mean contributions
  computed cellwise with available-component weights; reconstruction verified.
- Two independent checks cover census source and facility/numeric consistency.
  Input/output hashes verified. Do not equate2238 filtered objects (many hydrants)
  with missing real critical facilities, or diagnostic distances with fixed PIM.

## 2026-09-14 Facility-distance edge correction

- `goslar_abzucht_display_rectangle_v1 / facility_edge_repair_v1`, sensitivity_scenario.
  Command: `.venv/bin/python bin/analysis/repair_multiriver_facility_edges.py`.
- Original375 retained facilities rasterized on2040m padded aligned grid, EDT with
  unchanged2km decay, then cropped to original grid. Padding3000m gives identical
  facility scores. No new facility classes/population/weights;183028-cell support unchanged.
-361 facility cells corrected. Four PIM scenarios34/50/60/70 and delta rasters,
  672 before/after statistical rows,8 PNG/SVG pairs and reading note. Original
  artifacts preserved; unchanged-facility cells preserve original PIM bitwise.
- Innerste regulatory12-cell mean at34% increases0.418 to0.448, but no cells
  reach0.6. Abzucht/Grane/Oker primary comparisons unchanged. This fixes a real
  preprocessing bias, not the broader index/extent interpretation mismatch.
- Four focused tests pass (outside source, aligned grid, larger padding, rejection);
  all maps previewed and asset audit passed. Independent all-source nearest-cell
  reconstruction exactly matches facility raster; second review checks weighted
  deltas and provenance. P3 floating replay on unaffectedcells removed explicitly.

## 2026-09-14 Full retained multi-river comparison extent

- `goslar_multiriver_full_extent_v1 / frozen_scale_v1`, diagnostic_only with34/50/60/70% flood-weight sensitivity outputs. Commands: `.venv/bin/python bin/analysis/run_goslar_multiriver_full.py`, then `.venv/bin/python bin/analysis/report_goslar_multiriver_full.py`.
- Old area union all14 retained official products buffered2km:738.957km²,821048 scored30m cells; original EPSG32632 lattice/normalization anchors retained. All14 product center-cell score coverages100%. Eight regulatory products and six hydraulic scenarios remain separate.
- Four DEM tiles and10020m terrain buffer; enlarged SoilGrids window, Natura2024 polygons, and September14 OSM roads/facilities acquired under data/. Road query support independently reconstructed: evaluation+3050m completely covered;113207 unique road ways,2432 selected facilities. Stale July cache and failed Ohsome attempt excluded.
-18 PNG/SVG pairs,1344 comparison rows, coverage and criterion-contribution CSVs, QGIS-readable polygons/rasters, reading note, validation and hashes. Narrow-map tick overlap corrected in report renderer; conclusions remain outside figures.
- Main1km center comparison: flood indicator higher inside for all8 regulatory rivers, PIM higher inside only Wedde/Abzucht/Ecker. Original-overlap PIM MAE0.003297,max0.163668 across183028 cells; this combines domain/reprojection/edge-support and vector-vintage effects, not boundary-only improvement.
- Native SoilGrids overlap identical; aligned values/support differ after reprojection. Original population policy retained;12006 common finite population cells,27 former finite cells now absent,maxnormalizeddelta0.030600. Full score coverage does not imply complete component evidence.
-19 focused unit checks passed (`python -m unittest` with test_goslar_multiriver, test_abzucht_frozen_normalization, test_abzucht_weight_sensitivity, test_facility_edge_repair); readback reconstructs all4 scores within1.21e-7, checks all14 geometries/grids/masks/inside counts and original hashes. Two independent review angles covered engineering/source support and domain/numerics. Original outputs preserved; no final flood-prediction accuracy claim.
