# V1 Full Methodology Evidence Sweep

Status: completed as candidate evidence package for mentor review. This is not an AHP overlay,
not a flood-risk map, not an intervention-priority map, and not final thesis boundary evidence.

## Scope

This sweep responds to the requirement to process every methodology factor into comparable
candidate evidence, rather than leaving unprocessed factors as informal future work.

Covered factor families:

- Flood hazard
- Rainfall
- Terrain
- Land use / ASM pressure
- Environmental sensitivity
- Socioeconomic vulnerability
- Rehabilitation potential

## New Downloaded Inputs

- ESA WorldCover 2021 v200 tile:
  `data/raw/esa_worldcover_2021_v1_methodology/`
- WorldPop Zimbabwe 2020 UN-adjusted population raster:
  `data/raw/worldpop_zwe_2020_v1_methodology/`
- GHSL Zimbabwe 2025 built-up surface and population grids:
  `data/raw/ghsl_zimbabwe_v1_methodology/`
- JRC Global Surface Water occurrence, seasonality, recurrence, change, and transitions:
  `data/raw/jrc_global_surface_water_v1_methodology/`
- DFO Global Flood Archive via HDX:
  `data/raw/dfo_global_flood_archive_v1_methodology/`
- WDPCA Zimbabwe protected/conserved areas via HDX:
  `data/raw/wdpca_zimbabwe_v1_methodology/`

Download evidence:

- `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`

DFO Global Flood Archive was downloaded through the HDX CKAN resource after the browser-visible
DFO `temp` path returned 404 from the local command-line session. It is represented as
Zimbabwe-level historical context, not as V1 flood extent.

WDPCA Zimbabwe protected/conserved areas were downloaded through HDX and screened against V1.

## Processed Outputs

- Evidence matrix:
  `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_evidence_matrix.csv`
- Layer summary:
  `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_layer_summary.csv`
- Review vector layers:
  `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_review_layers.gpkg`
- Land-cover class areas:
  `outputs/v1_full_methodology_evidence_sweep/v1_worldcover_class_area.csv`
- JRC surface-water summaries:
  `outputs/v1_full_methodology_evidence_sweep/v1_jrc_surface_water_summary.csv`
- GHSL built-up/population summaries:
  `outputs/v1_full_methodology_evidence_sweep/v1_ghsl_summary.csv`
- DFO Zimbabwe historical flood records:
  `outputs/v1_full_methodology_evidence_sweep/v1_dfo_zimbabwe_flood_events.csv`
- WDPCA protected/conserved-area summary:
  `outputs/v1_full_methodology_evidence_sweep/v1_wdpca_protected_area_summary.csv`
- Rehabilitation proxy components:
  `outputs/v1_full_methodology_evidence_sweep/v1_rehabilitation_proxy_components.csv`
- Separate figure panels:
  - `outputs/v1_full_methodology_evidence_sweep/panel_land_use_worldcover.png`
  - `outputs/v1_full_methodology_evidence_sweep/panel_surface_water_occurrence.png`
  - `outputs/v1_full_methodology_evidence_sweep/panel_protected_areas_wdpca.png`
  - `outputs/v1_full_methodology_evidence_sweep/panel_population_exposure.png`
  - `outputs/v1_full_methodology_evidence_sweep/panel_rehabilitation_proximity.png`
- Handoff and caption:
  - `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_evidence_handoff.md`
  - `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_caption.md`

## Local Evidence Snapshot

- WorldCover dominant V1 classes: shrubland `55.3%`, tree cover `23.3%`, grassland `14.8%`,
  cropland `5.6%`, bare/sparse vegetation `0.4%`.
- WorldPop 2020 V1 population sum: about `79,776` people from native raster cells.
- GHSL 2025 V1 population sum: about `102,560` people from native raster cells; GHSL built-up
  surface sum is about `14,535,924` in native GHSL units. This is treated as socioeconomic
  exposure cross-check, not vulnerability truth.
- Geoportal Flood Prone Zones local V1 overlap: `0` features.
- DFO Zimbabwe-related historical flood records: `9`; valid event points inside V1 plus one
  degree: `0`.
- WDPCA protected/conserved areas overlapping V1: `2` polygons, about `53.4 km2` of geometry
  overlap.
- OSM mining pressure remains weak proxy evidence: `2` quarry/industrial polygons in V1.
- Rehabilitation/accessibility components now include distance and 0-1 proximity diagnostics to
  rivers, roads, and mining proxy features on the V1 30 m terrain grid.

## Dependency Note

The local root `.venv/` now includes `scipy` for `scipy.ndimage.distance_transform_edt`, used to
generate V1 distance/proximity evidence components. This dependency is local tooling only and is
not part of the public `ifpm-flood-pipeline/` dependency contract.

## Limits

- No AHP weights were created.
- No weighted overlay was run.
- CHIRPS was not resampled to the V1 30 m terrain grid.
- DFO historical flood data is point/centroid context only; it is not a local inundation layer.
- WDPCA protected areas are processed as context evidence, but their use as an AHP criterion still
  needs mentor/domain approval.
- OSM mining features are not official active ASM footprints.
- GHSL and WorldPop disagree in epoch, method, and native grid; they are complementary exposure
  evidence and should not be averaged or combined without an accepted rule.
