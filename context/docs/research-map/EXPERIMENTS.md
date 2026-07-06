# Experiments

Status: active. Master registry of every experiment_id, joined to IFPM-NNN task
IDs, status, claim level, and result summary. Per-experiment detail lives in
`RESULTS.md` and in each `outputs/<experiment_id>/handoff.md`.

Naming convention: `boundary_id / experiment_id`. `boundary_v1` is the Zimbabwe
prototype boundary; `pe1` is the southern Peru comparison catchment in Arequipa
Region, mainly the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa
city (treated as a parallel boundary_id for path purposes, even though it is
not nested under `boundary_v1`).

## Convention-compliant experiments (`outputs/boundary_v1/<experiment_id>/`)

| experiment_id | IFPM-NNN | status | claim_level | result_summary | handoff |
|---|---|---|---|---|---|
| `criteria_stack_v0_2` | IFPM-089 | in_progress | provisional | Honest-label 5-criteria stack; mining/exposure hardening planned not implemented | `outputs/boundary_v1/criteria_stack_v0_2/handoff.md` |
| `priority_scenarios_v0_2` | IFPM-089 | complete | sensitivity_scenario | 4 weight scenarios on v0.2 criteria; stable top-20% hotspot 431.907 km² | `outputs/boundary_v1/priority_scenarios_v0_2/handoff.md` |
| `rainfall_sensitivity_v0_3` | IFPM-090 | complete | sensitivity_scenario | Adds rainfall_climatology (CHIRPS coarse-to-grid, A-010); effective res ~5 km | `outputs/boundary_v1/rainfall_sensitivity_v0_3/` |
| `hotspot_exposure_diagnostic_v0_3` | IFPM-090 | complete | diagnostic_only | Tests co-location of v0.2 hotspots with exposure proxies; weak co-location | `outputs/boundary_v1/hotspot_exposure_diagnostic_v0_3/` |
| `rainfall_exposure_v0_4` | IFPM-097 | complete | sensitivity_scenario | Merged v0.3 rainfall + exposure; feeds 7/18 comparison pack | `outputs/boundary_v1/rainfall_exposure_v0_4/` |
| `mining_decay_priority_sensitivity` | IFPM-074 track | complete | sensitivity_scenario | Decay-function sensitivity on mining proximity; structure test only | `outputs/boundary_v1/mining_decay_priority_sensitivity/` |

## Convention-compliant Peru experiments (`outputs/srtm_1arcsec_peru_pilot/`)

| experiment_id | IFPM-NNN | status | claim_level | result_summary | handoff |
|---|---|---|---|---|---|
| `pe1_criteria_stack` (3-criteria) | IFPM-093 | complete | provisional | First PE1 stack: flood, erosion, land cover | `outputs/srtm_1arcsec_peru_pilot/criteria_stack/` |
| `pe1_criteria_stack` (5-criteria) | IFPM-094 | complete | provisional | +mining (OSM proxy) +exposure (OSM roads) | `outputs/srtm_1arcsec_peru_pilot/criteria_stack/` |
| `pe1_criteria_stack` (5-framework / 6 scored layers, INGEMMET mining) | IFPM-095/096 | complete | provisional | +rainfall (CHIRPS latam Dec-Mar) +official INGEMMET ASM points; same implementation-layer mapping as V1 | `outputs/srtm_1arcsec_peru_pilot/criteria_stack/` |
| `pe1_priority_scenarios` | IFPM-093/094/095/096 | complete | sensitivity_scenario | Equal + slide-matrix + flood_erosion_heavy; stable top-20% hotspot 258.538 km² in current rerun | `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/` |
| `pe1_rainfall_criterion` | IFPM-096 | complete | sensitivity_scenario | CHIRPS latam Dec-Mar mean, bilinear to PE1 30 m grid (A-012) | `outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/` |
| `pe1_ls_factor` | IFPM-093 | complete | diagnostic_only | PE1 LS hillslope mean 3.70 (vs V1 1.563) | `outputs/srtm_1arcsec_peru_pilot/ls_factor/` |
| `pe1_usle_soil_loss` | IFPM-093 | complete | provisional | PE1 USLE A mean 8.74 t/ha/yr (LOW R=238.6); vs V1 0.50 | `outputs/srtm_1arcsec_peru_pilot/usle_soil_loss/` |

## Zimbabwe terrain/factor chain (legacy flat names — `outputs/srtm_1arcsec_zimbabwe_prototype/`)

| output group | IFPM-NNN | status | claim_level | result_summary |
|---|---|---|---|---|
| `terrain_preprocessing` | IFPM-052 | complete | diagnostic_only | V1 DEM EPSG:32735 30 m, elev 863-1531 m; slope 0-55.6°; valid fraction 1.0 |
| `hydrology_derivatives` | IFPM-075 | complete | diagnostic_only | Filled DEM, D8 flow dir, flow acc (max 4,036,878 cells = 3633 km²), TWI 3.13-27.23 |
| `ls_factor` | IFPM-077 | complete | diagnostic_only | LS hillslope mean 1.563, p95 5.511 (Moore-Nieber, channel-masked, capped 50) |
| `terrain_standardization` | IFPM-055 | complete | diagnostic_only | Lowland/low-slope/high-slope candidates, 2-98 pct min-max |
| `hydrology_standardization` | IFPM-084 | complete | mentor_review_ready (candidates only) | TWI + drainage proximity 0-1 candidates; grid_compatible=true |
| `k_factor` (soilgrids_250m_sediment_candidate) | IFPM-072 | complete | diagnostic_only | K (0-5 cm, US) mean 0.1695, range [0.082, 0.251]; native 250 m, NOT resampled |
| `c_factor` (esa_worldcover_2021_v1_methodology) | IFPM-076 | complete | diagnostic_only | V1 area-weighted mean C 0.0429; lookup after mode resampling 10m→30m |

## Zimbabwe prototype iterations (legacy flat names)

| experiment_id (legacy) | IFPM-NNN | status | claim_level | result_summary | handoff |
|---|---|---|---|---|---|
| `v1_autonomous_prototype_v0_1` | IFPM-087 | complete (frozen baseline) | provisional | 5 criteria, 4 scenarios; stable top-20% hotspot 436.907 km²; mean σ 0.04697 | `outputs/v1_autonomous_prototype_v0_1/` (process note archived) |
| `v1_working_boundary` | IFPM-049 | complete | provisional | V1 area 3689.484 km²; Mzingwane Dam + Esigodini inside; Gwanda outside | `outputs/v1_working_boundary/v1_working_boundary_manifest.csv` |
| `v1_full_methodology_evidence_sweep` | IFPM-059 | complete (superseded) | diagnostic_only | 7-criteria evidence matrix; superseded by v0.2 honest labels | (process note archived) |
| `v1_terrain_mentor_package` | IFPM-056 | complete | mentor_review_ready | Low-slope susceptibility primary candidate; high-slope runoff alternative | `outputs/v1_terrain_mentor_package/` |
| `v1_usle_soil_loss` | IFPM-077 | **DEPRECATED** | n/a (deprecated) | A-mean 0.50 t/ha/yr; ~87% < 1 t/ha/yr; A absolute R-dependent and deprecated | `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md` |

## R-factor investigation experiments — DEFERRED RECORD (out of critical path since 2026-07-06, see D-RFACTOR-QUARANTINE)

These experiments are preserved as a deferred technical record. R-factor is no
longer on the critical path: the sediment criterion is served by the K×LS×C
erosion-source structure layer, and priority hotspots are independent of the
rainfall-erosivity factor R (H-HOTSPOT-R-INVARIANT). Reopened only if the mentor requires a quantitative
USLE A (ton/ha/yr) or rejects the K×LS×C approach.

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
| `peru_boundary_discovery` | IFPM-091 | complete | HydroBASINS SA candidates 2.8-14,300 km²; PE1 selected by rule |

## Reporting / comparison packages (not modelling experiments)

| package | IFPM-NNN | status | claim_level | contents |
|---|---|---|---|---|
| `zimbabwe_peru_prototype_comparison` | IFPM-097 | complete | sensitivity_scenario | 2×2 main board, dominant-criterion colouring, hotspot frequency, claim-level note, Teams draft |
| `mentor_boss_priority_explanation` | (july18 work) | complete | mentor_review_ready | Per-pixel winning criterion, contribution shares, boss process figure |
| `mentor_boundary_decision` | IFPM-040 | complete | mentor_review_ready | Mentor-facing boundary decision package |
| `mentor_voi_rainfall_intake` | IFPM-086 | complete | diagnostic_only | Mentor Voi rainfall archive intake; daily records, no strict EI30 |
| `teams_handoff` | (various) | complete | mentor_review_ready | Mentor Teams message drafts |

## Legacy-name → convention mapping

| Legacy flat path | Should be read as |
|---|---|
| `outputs/v1_autonomous_prototype_v0_1/` | `boundary_v1 / autonomous_prototype_v0_1` |
| `outputs/v1_autonomous_prototype_v0_2/` | `boundary_v1 / criteria_stack_v0_2` inventory |
| `outputs/srtm_1arcsec_zimbabwe_prototype/*` | `boundary_v1 / <derivative>` (terrain chain) |
| `outputs/chirps_v3_zimbabwe_prototype/*` | `boundary_v1 / rainfall_*` |
| `outputs/srtm_1arcsec_peru_pilot/*` | `pe1 / <derivative>` (treated as a parallel boundary_id) |
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
