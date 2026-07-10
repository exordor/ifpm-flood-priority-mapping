# Artifact Index

Status: active. Index of project artifacts by type, with keep / archive / delete
disposition. This is a navigation layer — dataset registries, output manifests,
and per-script headers remain the authoritative detail sources.

## Type tags

`code` · `dataset` · `model` · `notebook` · `figure` · `screenshot` · `prompt` ·
`generated_asset` · `log` · `report` · `configuration`

## Code (`bin/` and `ifpm-flood-pipeline/src/`)

The pipeline is a 7-stage DAG orchestrated by `bin/pipeline.py`. See
`bin/README.md` for the full stage map and run commands.

| group | location | role | disposition |
|---|---|---|---|
| acquire | `bin/acquire/` | download, plan, inventory raw data | keep |
| factors | `bin/factors/` | derive terrain / hydrology / USLE factors | keep |
| criteria | `bin/criteria/` | assemble 0-1 standardized MCDA criteria | keep |
| scenarios | `bin/scenarios/` | weighted overlay + sensitivity / stability | keep |
| visualize | `bin/visualize/` | mentor/boss-facing figures | keep |
| package | `bin/package/` | boundary export, evidence packaging, grid checks | keep |
| investigate | `bin/investigate/` | one-off R-factor / sensitivity checks | keep (R-factor track) |
| shared helpers | `bin/_lib/` | shared utilities | keep |
| terminology gate | `bin/check_active_terminology.py`, `check_glossary_sources.py`, `check_project_terminology.py` | active terminology enforcement | keep (binding) |
| boundary validator | `bin/validate-boundary.sh` | workspace boundary check | keep (binding) |
| DAG orchestrator | `bin/pipeline.py` | 7-stage DAG runner (`list`, `dot`, `run`) | keep (binding runbook) |
| deliverable pipeline | `ifpm-flood-pipeline/src/` | minimal AHP-MCDA + weighted overlay (CLI: `ahp`, `run`, `standardize`, `raster-diagnostics`) | keep |

### Archived code

| code | original location | reason | archive |
|---|---|---|---|
| V1/V2 R-factor chain | originally under `bin/factors/` and `bin/visualize/` | R-factor work paused (IFPM-074); now guarded under archive | `bin/_archive/superseded_rfactor_chain_2026-06/` (contains `derive_v1_chirps_rfactor.py`, `derive_v2_rfactor_candidates.py`, `derive_v2_usle_soil_loss.py`, `derive_v1_usle_soil_loss.py`, `plot_v2_rfactor_comparison_board.py`, `compare_v2_rfactor_candidates.py`, plus the explore/verify helpers and the ERA5 empirical boards). `bin/criteria/build_era5_rfactor_raster.py` is still in place under `bin/criteria/` but R-factor-paused. |
| v0.1 autonomous set | originally under `bin/criteria/`, `bin/scenarios/`, `bin/visualize/` | superseded by v0.2 criteria_stack | `bin/_archive/superseded_v0_1_autonomous_2026-06/` (contains `build_v1_autonomous_criteria_stack.py`, `run_v1_autonomous_priority_scenarios.py`, `plot_v1_autonomous_prototype_board.py`; per terminology audit 2026-07-03) |
| outlet exploration | originally `bin/_archive/superseded_outlet_exploration_2026-06/` | superseded by V1 working-boundary waiver | `bin/_archive/superseded_outlet_exploration_2026-06/` (already archived) |

## Datasets (`data/` — ignored; registry is the authoritative record)

Each real dataset has a registry note under `context/docs/data-management/registry/`.
**Do not duplicate registry content here.** Use the registry as the source of
truth.

| dataset_id | registry note | status |
|---|---|---|
| `srtm_1arcsec_zimbabwe_prototype` | `registry/srtm_1arcsec_zimbabwe_prototype.md` | downloaded |
| `srtm_1arcsec_peru_pilot` | `registry/srtm_1arcsec_peru_pilot.md` | downloaded |
| `chirps_v3_zimbabwe_prototype` | `registry/chirps_v3_zimbabwe_prototype.md` | downloaded |
| `esa_worldcover_2021_v1_methodology` | `registry/esa_worldcover_2021_v1_methodology.md` | downloaded |
| `esa_worldcover_2021_peru_pilot` | `registry/esa_worldcover_2021_peru_pilot.md` | downloaded |
| `soilgrids_250m_sediment_candidate` | `registry/soilgrids_250m_sediment_candidate.md` | downloaded |
| `soilgrids_250m_peru_pilot` | `registry/soilgrids_250m_sediment_candidate.md` (Peru analogue) | downloaded |
| `geofabrik_osm_zimbabwe_prototype` | `registry/geofabrik_osm_zimbabwe_prototype.md` | downloaded |
| `geofabrik_osm_peru_pilot` | `registry/geofabrik_osm_peru_pilot.md` | downloaded |
| `ingemmet_catastro_minero_peru_pilot` | `registry/ingemmet_catastro_minero_peru_pilot.md` | downloaded |
| `hydrosheds_zimbabwe_prototype` | `registry/hydrosheds_zimbabwe_prototype.md` | downloaded (boundary discovery) |
| `hydrosheds_peru_prototype` | `registry/hydrosheds_peru_prototype.md` | downloaded (boundary discovery) |
| `hydrorivers_africa_visual_review` | `registry/hydrorivers_africa_visual_review.md` | visual review |
| `ghsl_zimbabwe_v1_methodology` | `registry/ghsl_zimbabwe_v1_methodology.md` | downloaded |
| `worldpop_zwe_2020_v1_methodology` | `registry/worldpop_zwe_2020_v1_methodology.md` | downloaded |
| `jrc_global_surface_water_v1_methodology` | `registry/jrc_global_surface_water_v1_methodology.md` | downloaded |
| `wdpca_zimbabwe_v1_methodology` | `registry/wdpca_zimbabwe_v1_methodology.md` | downloaded |
| `era5_hourly_precip_v1_rfactor` | `registry/era5_hourly_precip_v1_rfactor.md` | downloaded (R-factor diagnostic) |
| `emdat_public_validation_candidate` | `registry/emdat_public_validation_candidate.md` + preflight | downloaded (Zimbabwe profile only) |
| `mentor_voi_rainfall_measurements_2026-06-24` | `registry/mentor_voi_rainfall_measurements_2026-06-24.md` | downloaded (non-reusable) |
| `zimbabwe_geoportal_subcatchments_2025` | `registry/zimbabwe_geoportal_subcatchments_2025.md` | downloaded (boundary comparison) |
| `zimbabwe_geoportal_candidate_outlet_layers` | `registry/zimbabwe_geoportal_candidate_outlet_layers.md` | visual review |
| `usgs_africa_gis_mineral_zimbabwe_prototype` | `registry/usgs_africa_gis_mineral_zimbabwe_prototype.md` | registry |
| `dfo_global_flood_archive_v1_methodology` | `registry/dfo_global_flood_archive_v1_methodology.md` | methodology |

Abandoned candidates: `copernicus_dem_zimbabwe_prototype`, `glofas_public_validation_candidate`
(under `data-management/_archive/abandoned_candidates_2026-06/`).

## Outputs (`outputs/` — ignored; manifests are the authoritative record)

Per-output manifests and `handoff.md` files are the authoritative record. See
`EXPERIMENTS.md` for the experiment-keyed registry. **Do not duplicate output
file lists here.**

Key index files that already exist:
- `exports/v1_methodology_mentor_report_package_2026-06-13/figure_index.csv`
  (one mentor packet)
- Per-experiment: `outputs/boundary_v1/<experiment_id>/*_manifest.csv`,
  `outputs/<group>/*_manifest.csv`

No central figure/output index exists across all of `outputs/`. If needed, a
generated `outputs/_index.csv` could be added by a small script.

## Configurations

| config | location | role | disposition |
|---|---|---|---|
| deliverable pipeline configs | `ifpm-flood-pipeline/configs/` | public-safe sample configs | keep |
| example pairwise matrix | `ifpm-flood-pipeline/configs/example_pairwise_matrix.csv` | AHP example (slide matrix NOT here — it is `sensitivity_scenario` only, not promoted) | keep |
| scenario weights | `outputs/boundary_v1/<experiment_id>/scenario_weights.csv` | per-experiment scenario weight records | keep |
| criteria manifests | `outputs/boundary_v1/<experiment_id>/*_criteria_manifest.csv` | per-experiment criteria composition records | keep |

## Prompts

No central prompt registry exists. Mentor-message drafts and prompt-style
content live under `context/docs/mentor-explanation/`. External-LLM review
prompts (e.g. `gpt_pro_review_prompt.md`) are referenced in IFPM-087 next action
but not centrally indexed.

## Figures / reports (mentor- and boss-facing)

| package | location | status |
|---|---|---|
| Scenario-mean paper-style single maps | `outputs/sensitivity_figures/paper_style_single_maps/` | sensitivity/appendix figures only; not the public direct-weight main result |
| Peru five PIM criterion maps | `outputs/slide_ready_figures/peru_pim_criteria_maps/` | refreshed from current PIM criteria; no global titles or captions |
| Peru exposure and capacity-context maps | `outputs/slide_ready_figures/peru_exposure_context_maps/` | WorldPop, mapped buildings, exposure indicators, INEI poverty, and health remoteness; poverty/health context layers are not PIM inputs |
| Peru direct-weight priority screening maps | `outputs/slide_ready_figures/peru_direct_weight_priority_maps/` | five-class and highest-priority-quintile single maps from the current direct-weight scenario; unscored cells shown explicitly |
| Peru weighted-contribution map | `outputs/slide_ready_figures/peru_pim_contribution_map/` | largest weighted criterion contribution per common-valid cell plus realized contribution summary; not a sensitivity or causal-driver map |
| July 18 integrated comparison board | `outputs/zimbabwe_peru_prototype_comparison/` | mentor_review_ready; secondary/background after D-PERU-FIRST |
| Dominant-criterion pixel map | `outputs/mentor_boss_priority_explanation/{zimbabwe,peru}/` | mentor_review_ready |
| Boss process figure | `outputs/mentor_boss_priority_explanation/data_analysis_process_for_boss.pdf` | mentor_review_ready |
| R-factor send packet | `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.png`, `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.png` | conditional send (Fig 1, Fig 2 only) |
| Terrain mentor package | `outputs/v1_terrain_mentor_package/mentor_v1_terrain_diagnostic_board.png` | mentor_review_ready |
| Multi-criteria evidence board | `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_evidence_board.png` | superseded |

## Terminology dead/alive verdict (from 2026-07-02 audit)

| file | verdict | action |
|---|---|---|
| `bin/factors/derive_peru_pilot_usle_soil_loss.py` | LIVE | rewritten 2026-07-03 (5× deprecated shorthand → standard "K×LS×C erosion-source structure" wording) |
| `bin/_archive/superseded_rfactor_chain_2026-06/derive_v2_usle_soil_loss.py` | dead (V2 paused, archived) | do not rewrite now; handle when V2 resumes |
| `bin/_archive/superseded_rfactor_chain_2026-06/plot_v2_rfactor_comparison_board.py` | dead (V2 paused, archived) | same |
| `bin/criteria/build_era5_rfactor_raster.py` | dead (R-factor route changed; still in place, not archived) | same |
| `outputs/boundary_v1/priority_scenarios_v0_2/handoff.md` | LIVE | rewritten 2026-07-03 (1× deprecated shorthand) |
| `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md` | deprecation marker | keep |
| `context/docs/data-management/registry/geofabrik_osm_peru_pilot.md` | LIVE | low priority: 1× snake_case, fix on next touch |

Active prevention rule: run `.venv/bin/python bin/check_active_terminology.py`
before sending any mentor/boss-facing package.

## Lineage

Absorbs content from:
- `task_progress_board.md` per-IFPM-NNN evidence/file pointers
- `terminology_audit_2026-07-02.md` Execution Appendix (dead/alive verdicts)
- `data-management/registry/` (dataset_id list — registry notes remain authoritative)
- `bin/README.md` (pipeline stage map)
- `outputs/` directory listing
