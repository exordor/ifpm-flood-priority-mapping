# Experiments

Current experiments only. Older Zimbabwe, former-Peru-area (`peru_former`)
and R-factor experiments are in Git history (this file before 2026-10-10).

Each output folder holds its own manifest with exact inputs, weights and hashes.
Commands run from the workspace root.

One-off diagnostic scripts were removed on 2026-10-11 (refactor phase 1); their results stay
in the output folders and in this file. Recover any of them with `git show 6e2ed8b:<path>`.
Helpers the final Goslar run still needs moved to `bin/_lib/goslar_comparison.py` and
`bin/_lib/fixed_scale.py` (was `bin/analysis/abzucht_fixed_scale_normalization.py`).

## Secocha, Peru

Boundary `secocha_reference_extent`: a 30 km² window taken from the
coordinate frame of INGEMMET A7367 Map 7. It is a map reference extent, not a
catchment or event footprint. Outputs: `outputs/secocha_pim_chain/`.

| Experiment | Command | Result |
|---|---|---|
| Five-criterion PIM (`supervisor_full_spec_v07_secocha`) | `bin/factors/run_secocha_pim_chain.py` | 30 m grid, Supervisor weights, no NoData filling. 15.65% of valid cells High (0.6–0.8), none Very High. Mining is a separate overlay, not in the score. |
| Chain checks | `bin/validate/validate_secocha_pim_chain.py` | Writes `quality_assurance/chain_validation.json`: grids match, criteria within 0–1, PIM valid coverage 97.20%. |
| 2023 event comparison | `bin/analysis/digitize_secocha_a7367_map7_event.py` | Two 5 February classes digitized from Map 7 (0.211 km², in `outputs/secocha_2023_validation/observed_hazard/`). PIM covers 66.2% of these cells; 19.1% of covered cells are High versus 15.6% study-wide. The digitized polygons have not been independently reviewed. |

## Goslar, Germany

Uses the same chain and Supervisor weights as Secocha (`bin/factors/run_goslar_pim_chain.py`),
compared against official regulatory flood zones (HQ100 etc.), not observed event footprints.

| Experiment | Output folder / command | Result |
|---|---|---|
| Abzucht HQ100 overlay | `compare_abzucht_hq100.py` | HQ100 mean PIM 0.475 vs 0.418 in a 1 km outside ring. |
| Expanded area and display rectangle (`fixed_scale`) | `run_abzucht_expanded.py [--fill-display-rectangle]` | Extends coverage to all HQ100 cells with normalization anchors fixed from the original area. HQ100 mean 0.470, 6.06% of HQ100 cells ≥0.6. |
| Explanation figures (`explanation`) | `explain_abzucht_comparison.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/explain_abzucht_comparison.py`) | Flood criterion 0.507 inside HQ100 vs 0.373 in the ring; PIM 0.470 vs 0.419. Only 5.8% of cells have all 14 components. |
| Input gaps (`gap_repair`, `input_completion`) | `repair_abzucht_gaps.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/repair_abzucht_gaps.py`), `complete_abzucht_inputs.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/complete_abzucht_inputs.py`) | GHSL population and 2017 SoilGrids fill the population and soil gaps in HQ100. These are source replacements, not recovered observations. |
| Weight sensitivity (`weight_sensitivity`) | `tune_abzucht_weights.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/tune_abzucht_weights.py`) | Flood weight 34–80% tested. 80% gives the largest inside/outside gap at the 0.6 cutoff, but it is at the edge of the range and depends on the cutoff. HQ100 was used to tune, so it cannot also validate. |
| Spatial checks (`spatial_offset`, `river_alignment`, `atkis_dop_check`) | `diagnose_abzucht_spatial_offset.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/diagnose_abzucht_spatial_offset.py`), `check_abzucht_river_alignment.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/check_abzucht_river_alignment.py`), `check_abzucht_atkis_dop.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/check_abzucht_atkis_dop.py`) | 386 of 420 high cells lie outside HQ100. Model drainage is a median 47 m from the official Abzucht line. |
| Multi-river comparison (`multiriver_comparison`, `multiriver_flood_weights_50_60_70`) | `compare_goslar_multiriver.py`, `compare_multiriver_weights.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/compare_multiriver_weights.py`) | Flood criterion is higher inside every covered regulatory zone; PIM is not. Raising the flood weight to 50/60/70% helps Abzucht but not Oker or Innerste. |
| Semantics audit (`component_semantics`, `input_semantics_followup`) | `diagnose_multiriver_low_scores.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/diagnose_multiriver_low_scores.py`), `audit_multiriver_input_semantics.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/audit_multiriver_input_semantics.py`) | Oker scores low on sediment and land use. "Bare soil" is really tree-cover loss and "expansion" is static proximity; field names were left unchanged. |
| Facility-distance fix (`facility_edge_repair`) | `repair_multiriver_facility_edges.py` (removed 2026-10-11; recover: `git show 6e2ed8b:bin/analysis/repair_multiriver_facility_edges.py`) | Facilities outside the grid were being dropped; fixed with a padded grid. Innerste mean rises 0.418 → 0.448. |
| **Full multi-river extent** (`goslar_multiriver_full_extent/fixed_scale`) | `run_goslar_multiriver_full.py`, then `report_goslar_multiriver_full.py` | 739 km² covering all 14 official products (8 regulatory zones, 6 hydraulic scenarios); flood weights 34/50/60/70%. Within 1 km, the flood criterion is higher inside all 8 regulatory zones, but PIM is higher only for Wedde, Abzucht and Ecker. **Main open issue.** |

Goslar and Abzucht outputs are under `outputs/goslar_abzucht_diagnostics/<experiment>/`
unless named otherwise; each has a `READING_NOTE.md`. Tests:
`.venv/bin/python -m unittest discover -s tests`.

## Goslar input chain notes (moved from registry)

Condensed from the former registry notes `goslar_pim_chain_sources` and
`goslar_official_hydrology_and_flood_data`. Source facts stay in those registry notes.

**Chain** (`bin/factors/run_goslar_pim_chain.py`; outputs under
`outputs/goslar_pim_chain/priority_scenarios/`, manifest `run_manifest.json`):

1. Boundary: raster mask from `goslar_wrrl_basin` (153.779 km², union of the
   seven official WRRL water-body polygons intersecting the ZLW focus extent; active since
   2026-08-17). The original ZLW print-layout extent (`outputs/goslar_focus_boundary/`,
   22.882 km²) is kept as a weight-0 minimum study-area anchor and is fully contained.
2. Grid: EPSG:32632, 30 m, 635 × 611 cells.
3. Terrain: Copernicus DEM GLO-30; slope (central difference); WhiteboxTools fill → D8 → flow
   accumulation → streams (threshold 500) → distance to drainage → TWI, all on a +1 km buffered
   DEM and aligned back to the grid; LS factor (Moore & Nieber, capped at 50, channel-masked).
4. Land cover: WorldCover C-factor and land-use pressure LUTs (10 m → 30 m). Soil K: Williams
   (1995), 0-30 cm depth-weighted, US units × 0.1317 to SI (250 m → 30 m).
5. Rainfall: DWD REGNIE June-August mean 1991-2020 (1 km → 30 m).
6. Roads: Overpass road proximity. Protected areas: Natura 2000 proximity. Population: Zensus 2022.
7. Standardization: 2-98 percentile min-max. NoData is kept, not filled.

**Weights** (identical to Secocha Supervisor v07; no Goslar-specific reweighting):
FH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14. FH = rainfall 0.35 + TWI 0.25 + drainage 0.40;
SE = K 0.25 / LS 0.50 / C 0.25; LU = LC 0.40 / BV 0.35 / BE 0.25; ES = water/wetland 0.65 +
protected 0.35; SV = road 0.35 / settlement 0.35 / critical infrastructure 0.30.

**Decisions and repairs**

- 2026-08-07: inputs switched to Copernicus DEM (from SRTM), Natura 2000 (from OSM protected
  areas), Zensus 2022 (from WorldPop DEU 2020), REGNIE 1991-2020 (from 2014-2023) and a pinned
  SoilGrids snapshot (from a live `/latest/` read).
- 2026-08-12 repair: OSM roads were rasterized in EPSG:4326 onto the EPSG:32632 grid (0 road
  pixels in the focus box); after projecting first, 5,931 pixels. WorldCover and SoilGrids NoData
  had been set to 0; now kept as NoData (soil K keeps 2,661 NaN cells). Hydrology had run on the
  focus-clipped DEM, truncating upstream accumulation; now runs on the +1 km buffer.
- 2026-08-14: a temporary Goslar-specific LU/SV reweighting was withdrawn to keep the Secocha
  weights. A mining context overlay (LBEG/NIBIS mining rights + OSM mining features, 12 km) was
  added as a separate layer, outside the score.
- 2026-08-17: boundary changed from the ZLW box to the WRRL union; SoilGrids and roads refetched
  for that window; critical infrastructure changed from the WorldCover built-up proxy to
  proximity to 375 filtered OSM facilities (2 km linear decay); 2024 CLMS Bare Soil After replaced
  the all-zero WorldCover bare-soil proxy.
- 2026-08-18: the land-change component switched to CLMS tree-cover-density decline 2018-2024.
- Packaging: QGIS FullAudit (36 layers) and ReviewMap (24 layers) under
  `exports/qgis_packages/goslar/`, built by `bin/package/build_goslar_qgis_full_audit.py`;
  the priority result and five criteria use equal-interval classes 0.2/0.4/0.6/0.8/1.0.

**HWRM and HQ100 coverage checks**

- The ZLW focus extent had no HWRM overlap; the WRRL reference grid has 62 direct 30 m overlap
  cells.
- 2026-09-08 (`outputs/goslar_reference_exploration_2026_09_08/`): the Abzucht HQ100 polygon
  (`uesg_id=917`) is 0.495468 km²; 0.297448 km² (60.03%) lies inside the WRRL boundary. Of 561
  30 m cell centres inside the polygon and raster extent, 337 are valid and 224 NoData.

**Known limits of the chain**: hydrology covers only a +1 km buffer, not a full upstream
catchment; soil K covers about 94% of the boundary at 250 m effective resolution; REGNIE is 1 km
evidence; Natura 2000 omits national designations; Zensus counts residents only.

## Interpretation limits (Goslar)

These apply to every Goslar/Abzucht result note and are stated here once.

- The official extents (HQ100, the other HQ scenarios, regulatory zones) are model or regulatory zones, not observed 2017 flood footprints. HQ100 was used to tune the flood weight, so it is not independent validation.
- High scores outside the official extents are not false positives, and overlap shares are not prediction accuracy.
- Where soil K or hillslope LS is missing, the erosion term uses C only; a low erosion contribution there does not mean low erosion.
- Census cells missing from the published population table may be true zeros or suppressed for confidentiality. They are not filled with zero.
- The outer 1 km ring is a descriptive reference zone, not a matched control.
- Scores are not re-stretched to improve agreement with the flood extents.
- 0.6 is the existing priority class threshold, not a calibrated flood threshold.


## 2026-10-11 — Mac validation of the new `ifpm` entry point

- Environment: `uv sync --extra hydrology` (CPython 3.12.12).
- Quick checks: `.venv/bin/python -m unittest tests.test_ifpm_normalize tests.test_ifpm_scoring tests.test_ifpm_config` passed 19 tests; `.venv/bin/python -m ifpm list` listed four Goslar extents and one Secocha extent.
- Full suite: `.venv/bin/python -m unittest discover -s tests` ran 177 tests in 368.881 seconds: 2 failures, 2 errors, 2 skipped. Problems: missing former Peru scenario script at its legacy path; missing `openpyxl`; Zimbabwe population path assertion uses an old directory name; missing Zimbabwe rainfall-exposure `handoff.md`. Buffered stdout followed the unittest summary, so the literal last three lines were map-export messages, not the result summary. Legacy tests also regenerated QGIS packages and Zimbabwe figure outputs.
- Secocha commands: `.venv/bin/python -m ifpm run secocha`, then `.venv/bin/python -m ifpm verify secocha`. Run exited 0; verification exited 1. Output: `outputs/_rerun/secocha/`. Result: 14/19 files pass, 5 fail, no missing files. Maximum differences: road access 1.50e-03; built/agriculture/road expansion 7.50e-04; landuse 1.88e-04; socioeconomic 5.25e-04; final priority 1.05e-04. Cause not established.
- Goslar commands: `.venv/bin/python -m ifpm run goslar`, then `.venv/bin/python -m ifpm verify goslar`. All four extents completed; run exited 0, verification exited 1. Output: `outputs/_rerun/goslar/`. Result: 54/55 files pass, 1 fail, no missing files. All checked rasters are byte-identical. The only failure is `source_inventory.csv`: eight rows differ only in `source_path`, using legacy directory names in the rerun.
- Evidence: `outputs/_rerun/validation_logs/{tests,secocha_run,secocha_verify,goslar_run,goslar_verify}.log`. Rerun outputs retained; no implementation changes made. Acceptance criteria were not met.
- Follow-up (same day). Secocha: the 5 failing files trace to 3 extra road cells in the rerun, all in column 166 (rows 90, 102, 170; east grid and boundary edge, x=696500). Road ends clipped at the boundary land one floating-point step inside the edge with this GEOS/GDAL build, so the edge cell is burned; the ifpm code matches the old script line for line. Accepted as known differences: `configs/secocha.yaml` `known_differences` lists the 5 files, which `ifpm verify` reports as KNOWN (counted as pass while the raster difference stays ≤ 2e-3). Result: 19/19 pass (5 KNOWN). Goslar: the eight `source_path` values came from the `products` layer of the two `comparison_boundaries.gpkg` files; after those paths were updated, `ifpm run goslar --extent multiriver` plus `verify goslar` gives 55/55. Legacy tests that regenerate files under `outputs/` are now skipped unless `IFPM_WRITE_OUTPUTS=1`.
