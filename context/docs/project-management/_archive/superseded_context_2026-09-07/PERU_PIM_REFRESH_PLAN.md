# Peru PIM Refresh Implementation Plan

> **For agentic workers:** execute this plan task by task with test-first changes and
> verification checkpoints. Do not create version-numbered script names.

**Goal:** Upgrade the Peru socioeconomic criterion with population and built-
infrastructure exposure, rerun the mentor direct AHP PIM scenario, refresh
slide-ready maps, and rerun WorldPop exposure accounting and SINPAD co-location diagnostics.

**Architecture:** A new upstream criterion builder writes one grid-compatible
`exposure_indicators_0_1.tif` plus auditable component rasters and manifests. The PIM
scenario runner consumes that raster as the fifth main criterion while preserving
the existing five-criterion hierarchy and main weights. INEI poverty and OSM health-
service remoteness are produced as response-capacity context layers but are not
silently inserted into the mentor hierarchy. SINPAD remains point context and
never enters the weighted overlay.

**Tech stack:** Python 3.11+, NumPy, Rasterio, GeoPandas, SciPy, Matplotlib,
standard-library `unittest`, existing IFPM raster helpers.

## Global Constraints

- Work on branch `codex/peru-pim-refresh`; do not implement on `main`.
- Use stable semantic script names. Put run identity in manifests, outputs, or Git.
- Preserve the five main criteria: FH, SE, LM, ES, SV.
- Preserve only the current `mentor_peru_direct_pim` scenario.
- Preserve NoData outside the study boundary and report component coverage.
- Keep CHIRPS scale warnings and all current non-SV criteria unchanged.
- Label the result `provisional` / `mentor_review_ready`, not `validated` or final.
- Do not commit unless the user separately asks for a commit.

---

### Task 1: Lock the socioeconomic criterion contract

**Files:**
- Create: `tests/test_peru_exposure_indicators.py`
- Create: `bin/criteria/build_peru_exposure_indicators.py`

**Consumes:**
- Reference grid: `outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif`
- Boundary: `outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg`
- Population: `data/raw/worldpop_peru_population/per_ppp_2020_UNadj_peru_hybas_l7_6070641200_bbox.tif`
- Roads: `outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/road_access_proximity_0_1.tif`
- Buildings and health POIs: `data/raw/geofabrik_osm_peru_pilot/extracted/`
- Poverty table: `data/raw/inei_peru_poverty_2018/arequipa_district_poverty_2018.csv`
- District polygons: Geofabrik `admin_level8` polygons intersecting the study boundary.

**Produces:**
- `outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_0_1.tif`
- `population_exposure_0_1.tif`, `built_infrastructure_exposure_0_1.tif`,
  `infrastructure_exposure_0_1.tif`, `poverty_context_0_1.tif`, and
  `health_service_remoteness_0_1.tif` in the same output directory.
- `exposure_indicators_components.csv`, `district_poverty_match.csv`,
  `exposure_indicators_grid_check.csv`,
  `exposure_indicators_contribution_diagnostics.csv`, and
  `exposure_indicators_manifest.json`.

**Scoring contract:**

```text
population_exposure = robust_normalize(log1p(WorldPop count), upper=p99)
built_infrastructure_exposure = circular 1 km focal density of OSM building presence
infrastructure_exposure = 0.50 population_exposure
                        + 0.50 built_infrastructure_exposure
exposure_indicators = 0.45 road_access_proximity
                    + 0.55 infrastructure_exposure
```

The 0.45/0.55 split follows the supplied Peru sub-criteria table. The internal
0.50/0.50 infrastructure split is an explicit implementation placeholder and must
be visible in the manifest. Poverty is the midpoint of the INEI 95% interval,
scaled on the documented 0-100 percentage range. Health remoteness is distance to
the nearest OSM clinic/doctor/hospital, clipped at 20 km and scaled 0-1. These two
context layers are not included in `exposure_indicators` in this run.

- [x] Write unit tests for robust normalization, NoData preservation,
  weighted combination, district-name normalization, and health-remoteness direction.
- [x] Run
  `.venv/bin/python -m unittest tests/test_peru_exposure_indicators.py -v` and
  confirm failures are caused by the missing implementation.
- [x] Implement the tested functions and CLI/data I/O.
- [x] Rerun the unit test and require all tests to pass.
- [x] Run `.venv/bin/python bin/criteria/build_peru_exposure_indicators.py`.
- [x] Verify all outputs match EPSG:32718, 30 m, 2571 x 2629, preserve boundary
  NoData, and have finite values in [0,1].

### Task 2: Connect the new criterion to the five-criterion PIM

**Files:**
- Create: `tests/test_peru_hybas_l7_6070641200_socioeconomic_integration.py`
- Modify: `bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py`
- Modify: `bin/README.md`

**Consumes:**
- `outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_0_1.tif`

**Produces:**
- Updated `pim_criteria/socioeconomic_0_1.tif` and subcriteria lineage rows.
- The direct scenario ID and unchanged main weights.

- [x] Write an integration test asserting that the scenario runner consumes
  the new socioeconomic raster, records road 0.45 and infrastructure 0.55, and
  retains only the mentor direct scenario.
- [x] Replace the road-only PIM component with the upstream exposure indicators.
- [x] Update the module description, `INPUTS`, `OUTPUTS`, `COMPONENT_PATHS`, and subcriteria
  manifest rows without changing FH/SE/LM/ES logic.
- [x] Add the reproducible pipeline command to `bin/README.md`.
- [x] Rerun the integration test and the existing mentor/five-criterion checks.

### Task 3: Rerun the scenario outputs and quantify the change

**Files:**
- Modify: `bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py` only if a comparison export
  cannot be produced from existing summaries.
- Output: `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/`

- [x] Record the pre-refresh mentor PIM checksum and current scenario summary in a
  temporary run comparison record under `outputs/`.
- [x] Run
  `.venv/bin/python bin/pipeline.py run --target run_peru_hybas_l7_6070641200_priority_scenarios`.
- [x] Require common valid coverage >= 0.95 and one direct scenario row only.
- [x] Verify the mentor weights remain FH=0.35, SE=0.25, LM=0.20, ES=0.12,
  SV=0.08.
- [x] Write `exposure_refresh_comparison.csv` with old/new raster checksums,
  mean absolute PIM change, Spearman rank correlation, top-20% overlap, and area.

### Task 4: Refresh slide-ready maps

**Files:**
- Create: `bin/visualize/export_peru_exposure_context_maps.py`
- Create: `bin/visualize/export_peru_direct_weight_priority_maps.py`
- Create: `bin/visualize/export_peru_pim_contribution_map.py`
- Modify only if required: `bin/visualize/export_peru_pim_criteria_maps.py`
- Modify only if required: `bin/visualize/export_paper_style_single_maps.py`
- Output: `outputs/slide_ready_figures/`

- [x] Export population exposure, built infrastructure, exposure indicators,
  poverty context, and health-service remoteness as separate GIS-style maps.
- [x] Keep each exported map free of a global title and caption; include coordinate
  ticks, legend/colorbar, scale bar, north arrow, and boundary.
- [x] Rerun Peru five-criterion and paper-style priority exporters.
- [x] Verify PNG and PDF exports exist, are nonblank, and use current source raster
  checksums in their index/manifest.
- [x] Visually inspect the new socioeconomic criterion, direct-weight PIM,
  and top-20% priority-area maps for clipping, overlap, and misleading labels.

### Task 5: Rerun exposure accounting and event-point diagnostics

**Files:**
- Modify only if required: `bin/analysis/summarize_peru_population_by_pim_class.py`
- Modify: `bin/analysis/compare_peru_pim_sinpad_colocation.py`
- Output: `outputs/peru_gap_closure_analysis/`

- [x] Run the WorldPop/PIM summary against the refreshed mentor raster.
- [x] Run the SINPAD/PIM co-location diagnostic against the refreshed mentor raster.
- [x] Verify event counts remain traceable to 25 records / 11 unique locations and that no
  claim uses WorldPop as observed affected population.
- [x] Run `py_compile`, `git diff --check`, relevant check scripts, and terminology
  checks.
- [x] Perform two adversarial reviews: GIS/data semantics and engineering/repo
  boundaries. Fix P1/P2 findings and rerun verification.
- [x] Hand off exact commands, generated outputs, changed files, claim boundaries,
  and remaining data limitations.

## Acceptance Criteria

- The scenario runner no longer describes or implements socioeconomic as road-only.
- The direct scenario raster is regenerated from the new fifth criterion.
- The five criterion maps and single priority maps are refreshed and visually valid.
- WorldPop and SINPAD summaries reference the refreshed mentor PIM checksum.
- Poverty and health layers are reproducible context evidence, not hidden AHP inputs.
- No version-numbered script is added.
- No raw data, generated outputs, or unrelated `pre/` files are staged.

## Approved one-page Peru board design (2026-07-13)

**Single claim:** the direct-weight Peru prototype identifies relative priority
patterns on 95.0998% complete five-criterion support, with flood conditioning
providing the largest weighted contribution across 85.4% of scoreable cells.
The board must not imply validated flood risk or rescue priority.

**Target and format:** one 3:2 landscape board at 3600 x 2400 px for mentor
review, exported as PNG and PDF. Existing governed maps remain the evidence
source; the generator may crop redundant white margins and legends for
thumbnails but may not redraw or alter their map evidence.

**Layout:**

1. Header: public-facing action title, Arequipa/Arequipa Region location, direct-weight
   equation, and `prototype / not validated flood risk` status.
2. Main row: raw-input factor overview on the left, direct-weight PIM as the
   largest central panel, and mining/population, weighted-contribution, and
   SINPAD diagnostics on the right.
3. Criteria strip: five equally sized criterion thumbnails in framework order
   (FH, SE, LM, ES, SV), each showing its main weight and plain evidence label.
4. Bottom table: five rows with `Criterion`, `Weight`, `Implementation`,
   `Coverage`, and `Evidence limitation`. Long diagnostic prose stays out of the
   visible board and remains in the source CSV.

**Evidence sources:**

- `outputs/peru_report_figure_chain/current/01..10_*.png`
- `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/criterion_data_strength.csv`
- `outputs/slide_ready_figures/peru_pim_contribution_map/contribution_summary.csv`
- `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/priority_screening_summary.csv`

**Outputs:**

- `outputs/peru_integrated_briefing_board/peru_integrated_briefing_board.png`
- `outputs/peru_integrated_briefing_board/peru_integrated_briefing_board.pdf`
- `outputs/peru_integrated_briefing_board/manifest.csv`

**QA:** all visible text must remain readable at full-slide display; no map,
legend, table cell, or status label may overlap; the result map must remain the
visual focus; source and packaged checksums must be recorded; rendered PNG and
PDF must be visually inspected; and the active terminology, five-criterion,
mentor-weight, and repository-boundary checks must pass.
