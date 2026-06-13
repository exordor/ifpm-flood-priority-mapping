# V1 Multi-Criteria Evidence Package

Status: mentor-facing evidence package generated from existing local layers.

Updated: 2026-06-13

## Purpose

This package moves the V1 prototype from terrain-only diagnostics to a multi-criteria evidence
review. It is intended to help the mentor decide which evidence families can enter a first
prototype criteria set.

## Inputs

- V1 working boundary and anchor checks.
- V1 terrain diagnostic rasters.
- HydroRIVERS, Zimbabwe Geoportal river/water/flood-prone layers, and Geofabrik OSM roads,
  places, landuse, water, and waterways from the professional outlet review package.
- CHIRPS rainfall comparison is now available as a separate package:
  `context/docs/project-management/chirps_v1_rainfall_comparison_2026-06-13.md`.
  The multi-criteria board does not resample or overlay CHIRPS.

Runtime note: `fiona==1.10.1` was installed into the root `.venv` for local GIS tooling
inspection and compatibility.

## Outputs

- `outputs/v1_multicriteria_evidence_package/panel_a_v1_river_context.png`
- `outputs/v1_multicriteria_evidence_package/panel_a_v1_river_context.pdf`
- `outputs/v1_multicriteria_evidence_package/panel_b_v1_terrain_diagnostics.png`
- `outputs/v1_multicriteria_evidence_package/panel_b_v1_terrain_diagnostics.pdf`
- `outputs/v1_multicriteria_evidence_package/panel_c_v1_exposure_mining_proxy.png`
- `outputs/v1_multicriteria_evidence_package/panel_c_v1_exposure_mining_proxy.pdf`
- `outputs/v1_multicriteria_evidence_package/panel_d_v1_criteria_decision_table.png`
- `outputs/v1_multicriteria_evidence_package/panel_d_v1_criteria_decision_table.pdf`
- `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_evidence_board.png`
- `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_evidence_board.pdf`
- `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_caption.md`
- `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_caption.txt`
- `outputs/v1_multicriteria_evidence_package/v1_candidate_criteria_evidence_table.csv`
- `outputs/v1_multicriteria_evidence_package/v1_multicriteria_layer_counts.csv`
- `outputs/v1_multicriteria_evidence_package/v1_multicriteria_review_layers.gpkg`
- `outputs/v1_multicriteria_evidence_package/v1_multicriteria_handoff.md`

Use the split panels as the primary mentor-facing material. The combined board is retained only as
a secondary overview because it compresses too much map/table information into one figure.

## Key Evidence Notes

- Terrain is available as diagnostic 30 m rasters, but slope direction still needs mentor
  interpretation.
- Geoportal Flood Prone Zones have zero local overlap in the current review package.
- Exposure evidence is available from OSM places, roads, bridge tags, and road-river crossing
  proxies.
- Mining pressure is represented only by weak OSM quarry/industrial proxy features, not official
  mining truth.
- Rainfall is no longer a pure data gap. It is now a criterion-choice gap: the mentor still needs
  to decide whether annual background, rainy-season accumulation, anomaly, monthly peak, pentad
  peak, or daily sensitivity should enter the prototype criteria set.

## Mentor Decision Question

Which evidence families should enter the first prototype criteria set: terrain, rainfall,
exposure, mining pressure, and/or river-flood context?

Specific follow-up decisions: slope direction, which CHIRPS rainfall interpretation to use,
exposure role, and whether OSM mining proxies are acceptable or official mining data is required.

## Limits

- CHIRPS rainfall comparison is handled in the separate IFPM-058 package.
- No rainfall raster was resampled to 30 m.
- No AHP weights were applied.
- No weighted overlay was run.
- No flood-risk or intervention-priority map was produced.
- V1 remains `accepted_with_waiver_for_controlled_prototype`, not a final thesis boundary.
