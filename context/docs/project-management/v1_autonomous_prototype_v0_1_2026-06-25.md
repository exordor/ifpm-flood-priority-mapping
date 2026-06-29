# V1 autonomous prototype v0.1

Date: 2026-06-25

Status: provisional autonomous scoring complete.

## Purpose

This step moves beyond mentor-gated evidence boards and runs a controlled autonomous V1 prototype
score under explicit assumptions. It is not a final flood-risk map, intervention-priority map, or
final thesis boundary claim.

The goal is to test whether priority hotspots are stable under reasonable criteria-weight choices.

## Inputs

The run uses existing V1, grid-compatible local outputs only:

| criterion | input components | role |
|---|---|---|
| Flood / hydrology | TWI high-wetness + drainage proximity | flood-susceptibility proxy |
| Sediment structure | safe `a_structure_K_LS_C_30m.tif` | R-invariant sediment spatial structure |
| Land use / ASM pressure | C-factor pressure + OSM mining-proxy proximity | land-cover/mining pressure proxy |
| Environmental sensitivity | river/water proximity proxy | environmental context proxy |
| Socioeconomic exposure | road/access proximity proxy | exposure/access proxy |

Voi is not part of the main workflow. The Voi intake showed daily rainfall outside the study area,
so it remains an optional external R-range sanity check only.

## Commands

```bash
.venv/bin/python bin/build_v1_autonomous_criteria_stack.py
.venv/bin/python bin/check_v1_raster_grid.py --rasters \
  outputs/v1_autonomous_prototype_v0_1/criteria/flood_hydrology_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/criteria/sediment_structure_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/criteria/landuse_asm_pressure_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/criteria/environmental_sensitivity_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/criteria/socioeconomic_exposure_0_1.tif \
  --output outputs/v1_autonomous_prototype_v0_1/criteria_stack_grid_check.csv
.venv/bin/python bin/run_v1_autonomous_priority_scenarios.py
.venv/bin/python bin/check_v1_raster_grid.py --rasters \
  outputs/v1_autonomous_prototype_v0_1/priority_mean_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/priority_std_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/top20_frequency_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/scenarios/priority_equal_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/scenarios/priority_methodology_slide_candidate_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/scenarios/priority_flood_sediment_heavy_0_1.tif \
  outputs/v1_autonomous_prototype_v0_1/scenarios/priority_exposure_heavy_0_1.tif \
  --output outputs/v1_autonomous_prototype_v0_1/priority_grid_check.csv
.venv/bin/python bin/plot_v1_autonomous_prototype_board.py
```

## Outputs

All outputs are local and ignored under `outputs/v1_autonomous_prototype_v0_1/`.

Key files:

- `criteria_stack_manifest.csv`
- `criteria_readiness_table.csv`
- `criteria_stack_grid_check.csv`
- `scenario_weights.csv`
- `scenario_priority_summary.csv`
- `hotspot_stability_summary.csv`
- `priority_mean_0_1.tif`
- `priority_std_0_1.tif`
- `top20_frequency_0_1.tif`
- `v1_autonomous_prototype_board.png`
- `v1_autonomous_prototype_board.pdf`
- `v1_autonomous_prototype_handoff.md`
- `gpt_pro_review_prompt.md`

## Main results

All five criteria and all seven checked priority rasters passed the V1 raster grid gate:

- CRS: `EPSG:32735`
- resolution: `30 m`
- dtype: `float32`
- NoData: `-9999.0`
- valid fraction inside V1: `1.0`

Scenario weights:

| scenario | purpose |
|---|---|
| `equal` | neutral baseline |
| `methodology_slide_candidate` | mentor-slide matrix as candidate/example weights |
| `flood_sediment_heavy` | stress test for hazard/sediment interpretation |
| `exposure_heavy` | stress test for exposure-driven interpretation |

The mentor-slide candidate matrix has consistency ratio `0.022046`, so it is internally
consistent. It is still not treated as a final accepted AHP source.

Hotspot stability:

- Top-20% in all scenarios: `436.907 km2`
- Top-20% in any scenario: `1066.03 km2`
- Mean priority standard deviation: `0.04697`
- 95th percentile priority standard deviation: `0.078981`

## Important caveats

- This is a provisional autonomous prototype, not a validated flood-risk map.
- V1 remains a prototype-only working boundary.
- Rainfall/R is not inserted as a 30 m pixel-level layer.
- The sediment criterion uses safe R-invariant spatial structure; scalar R affects magnitude, not
  hotspot rank.
- Population and protected-area layers remain context-only in this v0.1 because they are not used
  as accepted 30 m grid-compatible criteria.
- OSM mining/access evidence is proxy evidence and should not be treated as official ASM truth.

## Adversarial review

Domain/correctness:

- P1 avoided: outputs are labelled as provisional prototype, not final risk/intervention maps.
- P1 avoided: deprecated old R/A products are not used as accepted model outputs.
- P1 fixed during review: the sediment structure label was corrected from `K x LS x C x P` to
  `K x LS x C`, matching the actual safe input file `a_structure_K_LS_C_30m.tif`.
- P2 caveat: road proximity may overstate socioeconomic exposure because it does not encode
  vulnerability or observed damage.
- P2 caveat: environmental sensitivity is simplified to river/water proximity in v0.1.
- P2 caveat: sediment-structure NoData inside V1 is conservatively filled as low pressure (`0`) to
  pass the grid gate; formal modelling should trace the missing-cell source instead of treating
  this as measured zero erosion.

Engineering/data-governance:

- Outputs remain under ignored `outputs/`.
- No new data were downloaded.
- No files in `ifpm-flood-pipeline/` were modified.
- Criteria and priority rasters pass the V1 grid gate.

## Next action

Use `gpt_pro_review_prompt.md` to get an external critique of criteria defensibility and hotspot
stability. Then either refine the weakest criterion or package v0.1 as the autonomous prototype
baseline for thesis-method discussion.
