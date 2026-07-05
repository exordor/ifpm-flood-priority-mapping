# boundary_v1 / criteria_stack_v0_2 Hardening Plan

Date: 2026-06-29

Status: first inventory implemented; `criteria_stack_v0_2` honest-label criteria stack
implemented for `boundary_v1`.

Naming rule:

- `boundary_v1` = the prototype-only working catchment.
- `criteria_stack_v0_1` = archived baseline criteria-stack experiment.
- `criteria_stack_v0_2` = current honest-label criteria-stack repair.

## Purpose

`boundary_v1 / criteria_stack_v0_1` proves that the grid-compatible prototype can run across five methodology-aligned
criteria and four weight scenarios. The next step is not another broad method experiment. The next
step is to harden the weakest criteria:

1. `landuse_asm_pressure`
2. `socioeconomic_exposure`

These two criteria currently work technically, but their evidence is weakest. Mining/ASM is based
on OSM quarry/industrial proxy evidence. Socioeconomic exposure is based mainly on road/access
proximity, not directly on observed exposed people, assets, or flood-damaged infrastructure.

The `criteria_stack_v0_2` correction also fixes two semantic/data-policy problems from
`criteria_stack_v0_1`:

- `K x LS x C` is now named `erosion_structure_proxy`, not sediment risk.
- `criteria_stack_v0_2` preserves NoData instead of filling missing sediment-structure cells as
  low pressure.

## Baseline To Preserve

`boundary_v1 / criteria_stack_v0_1` remains the frozen baseline:

- Boundary: `boundary_v1` prototype-only working catchment.
- Reference grid: `boundary_v1` 30 m `EPSG:32735` terrain grid.
- Output package: `outputs/v1_autonomous_prototype_v0_1/`.
- Figure: `v1_autonomous_prototype_board.png`.
- Interpretation: provisional autonomous prototype, not final flood-risk/intervention evidence.

No `criteria_stack_v0_2` output should overwrite archived `criteria_stack_v0_1` outputs.

## criteria_stack_v0_2 Scope

The active output package is:

`outputs/boundary_v1/criteria_stack_v0_2/`

Planned package:

- `evidence_gap_table.csv`
- `candidate_data_upgrade_matrix.csv`
- `revised_criteria_manifest.csv`
- `hotspot_comparison_summary.csv`
- `hardening_board.png/pdf`
- `handoff.md`

Implemented in the first inventory pass:

- `evidence_gap_table.csv`
- `candidate_data_upgrade_matrix.csv`
- `revised_criteria_manifest.csv`
- `inventory_handoff.md`

Implemented in the criteria-stack repair pass:

- `criteria_stack_manifest.csv`
- `nodata_coverage_report.csv`
- `criteria_stack_v0_1_to_v0_2_comparison.csv`
- `standardization_notes.csv`
- `criteria/*.tif`
- `criteria_preview.png`

## Hardening Track A: Mining / ASM Pressure

Current v0.1 input:

- C-factor pressure from WorldCover.
- OSM mining-proxy proximity.

Known weakness:

- OSM quarry/industrial polygons are not official active ASM evidence.
- Mining concessions, active disturbance, rehabilitation sites, and water-impact evidence are
  missing.

`criteria_stack_v0_2` actions:

1. Split the old hidden average into `land_cover_pressure` and `mining_pressure`.
2. Keep the OSM mining proxy as `weak_proxy`.
3. Create a mining evidence gap table with required fields:
   - source
   - geometry type
   - active/inactive status available
   - date available
   - official/proxy status
   - V1 overlap
   - usable as criterion yes/no
4. Search existing local outputs for any mining-relevant layer already downloaded.
5. If no stronger layer exists, do not invent one. Mark mining as `weak_proxy_context`.
6. Prepare a data-request mapping from missing mining fields to mentor trip asks.

Preferred future data:

- official ASM site points;
- concession/claim boundaries with status;
- active mining disturbance polygons;
- rehabilitation/EMA records;
- mine-related water-quality or sediment complaints if available.

## Hardening Track B: Socioeconomic Exposure

Current v0.1 input:

- OSM road/access proximity.

Known weakness:

- Road proximity is an accessibility / exposure proxy, not observed flood vulnerability.
- It does not identify people, assets, bridges, clinics, schools, or known flood-damaged places.

`criteria_stack_v0_2` actions:

1. Inventory all existing exposure-relevant local outputs:
   - WorldPop;
   - GHSL population;
   - GHSL built-up;
   - OSM roads;
   - OSM places;
   - road-river crossing proxy;
   - anchor places such as Esigodini, Gwanda context, Filabusi, West Nicholson.
2. Decide which exposure layers are grid-compatible and which must remain native/zonal/context.
3. Avoid forcing coarse population data into 30 m pixel overlay if it creates false precision.
4. Create two candidate exposure alternatives:
   - `exposure_access_proxy`: roads and road-river crossings.
   - `exposure_population_context`: native population / built-up summary, not necessarily 30 m.
5. Compare archived `criteria_stack_v0_1` hotspots against exposure components without calling it
   validation.
6. Rename road-only evidence to `road_accessibility_proxy` until population, built-up, damaged
   assets, or affected settlements are integrated.

Preferred future data:

- observed affected settlements;
- flood-damaged roads or bridges;
- local critical infrastructure;
- official ward/village population;
- asset exposure or vulnerability records.

## Decision Rules

`criteria_stack_v0_2` may update the criteria stack only if the replacement evidence is stronger
than `criteria_stack_v0_1` by at
least one of these rules:

- official source instead of public proxy;
- observed flood/mining impact instead of generic proximity;
- better temporal match;
- clear V1 overlap;
- documented licence and reproducibility;
- no false precision from resampling.

If evidence is not stronger, `criteria_stack_v0_2` should keep the baseline criterion and mark the
missing dataset in the mentor trip request list.

## What Not To Do

- Do not overwrite archived `criteria_stack_v0_1` outputs.
- Do not call `criteria_stack_v0_2` a validated flood-risk map.
- Do not turn OSM mining proxy into official ASM evidence.
- Do not treat road proximity as socioeconomic vulnerability.
- Do not treat river proximity as environmental sensitivity.
- Do not fill NoData as low pressure.
- Do not resample rainfall or coarse population to 30 m and present it as true pixel-level
  evidence.
- Do not update public pipeline APIs.

## Verification Plan

- Run `bash bin/validate-boundary.sh`.
- Run `git diff --check`.
- Confirm new outputs are under ignored `outputs/boundary_v1/criteria_stack_v0_2/`.
- Confirm no raw data are copied into `context/` or `ifpm-flood-pipeline/`.
- Confirm archived `criteria_stack_v0_1` outputs remain unchanged unless explicitly rerun as
  baseline.
- Run adversarial review:
  - Domain/correctness: check whether weak proxy evidence is overstated.
  - Engineering/data-governance: check output locations, registry needs, and public-safe boundary.

## Next Implementation Step

Inventory script implemented:

`bin/package/prepare_boundary_v1_criteria_stack_v0_2_inventory.py`

Single responsibility: inspect existing local outputs and produce gap/upgrade tables for
mining/ASM and exposure. It should not download new data, plot maps, or run overlay.

Criteria repair script implemented:

`bin/criteria/build_boundary_v1_criteria_stack_v0_2.py`

Single responsibility: read the `criteria_stack_v0_2` config, build honest-label grid-compatible
criteria rasters, preserve NoData, and write a NoData coverage report plus a small preview map.

Next implementation step: compare archived `criteria_stack_v0_1` stable hotspots against the
`criteria_stack_v0_2` split criteria and inventory layers (`road_river_crossings_v1`, OSM places,
GHSL/WorldPop native summaries, and mining proxy) without calling the comparison validation.
