# Peru PIM Refresh Implementation Plan

> **For agentic workers:** execute this plan task by task with test-first changes and
> verification checkpoints. Do not create version-numbered script names.

**Goal:** Upgrade the Peru socioeconomic criterion with population and built-
infrastructure exposure, rerun the equal and mentor AHP PIM scenarios, refresh
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
- Preserve the two public scenarios: `equal_active_pim` and
  `mentor_peru_direct_pim`.
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
- Reference grid: `outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/pe1_dem_utm18s_30m.tif`
- Boundary: `outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg`
- Population: `data/raw/worldpop_peru_population/per_ppp_2020_UNadj_pe1_bbox.tif`
- Roads: `outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/exposure_indicators_0_1.tif`
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
- Create: `tests/test_pe1_socioeconomic_integration.py`
- Modify: `bin/scenarios/run_pe1_priority_scenarios.py`
- Modify: `bin/README.md`

**Consumes:**
- `outputs/srtm_1arcsec_peru_pilot/exposure_indicators/exposure_indicators_0_1.tif`

**Produces:**
- Updated `pim_criteria/socioeconomic_0_1.tif` and subcriteria lineage rows.
- The same two scenario IDs and unchanged main weights.

- [x] Write an integration test asserting that the scenario runner consumes
  the new socioeconomic raster, records road 0.45 and infrastructure 0.55, and
  retains exactly the equal and mentor scenarios.
- [x] Replace the road-only PIM component with the upstream exposure indicators.
- [x] Update the module description, `INPUTS`, `OUTPUTS`, `COMPONENT_PATHS`, and subcriteria
  manifest rows without changing FH/SE/LM/ES logic.
- [x] Add the reproducible pipeline command to `bin/README.md`.
- [x] Rerun the integration test and the existing mentor/five-criterion checks.

### Task 3: Rerun the scenario outputs and quantify the change

**Files:**
- Modify: `bin/scenarios/run_pe1_priority_scenarios.py` only if a comparison export
  cannot be produced from existing summaries.
- Output: `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/`

- [x] Record the pre-refresh mentor PIM checksum and current scenario summary in a
  temporary run comparison record under `outputs/`.
- [x] Run
  `.venv/bin/python bin/pipeline.py run --target run_pe1_priority_scenarios`.
- [x] Require common valid coverage >= 0.95 and two scenario rows only.
- [x] Verify the mentor weights remain FH=0.35, SE=0.25, LM=0.20, ES=0.12,
  SV=0.08 and the equal baseline remains 0.20 each.
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
- Both scenario rasters are regenerated from the new fifth criterion.
- The five criterion maps and single priority maps are refreshed and visually valid.
- WorldPop and SINPAD summaries reference the refreshed mentor PIM checksum.
- Poverty and health layers are reproducible context evidence, not hidden AHP inputs.
- No version-numbered script is added.
- No raw data, generated outputs, or unrelated `pre/` files are staged.
