# Experiments

Current experiments only. Older Zimbabwe, former-Peru-area (`peru_hybas_l7_6070641200`)
and R-factor experiments are in Git history (this file before 2026-10-10).

Each output folder holds its own manifest with exact inputs, weights and hashes.
Commands run from the workspace root.

## Secocha, Peru

Boundary `peru_secocha_a7367_reference_extent_v1`: a 30 km² window taken from the
coordinate frame of INGEMMET A7367 Map 7. It is a map reference extent, not a
catchment or event footprint. Outputs: `outputs/peru_secocha_a7367_reference_extent_v1/`.

| Experiment | Command | Result |
|---|---|---|
| Five-criterion PIM (`supervisor_full_spec_v07_secocha`) | `bin/factors/run_peru_secocha_chain.py` | 30 m grid, Supervisor weights, no NoData filling. 15.65% of valid cells High (0.6–0.8), none Very High. Mining is a separate overlay, not in the score. |
| Chain checks | `bin/validate/validate_peru_secocha_chain.py` | Writes `quality_assurance/chain_validation.json`: grids match, criteria within 0–1, PIM valid coverage 97.20%. |
| 2023 event comparison | `bin/analysis/digitize_secocha_a7367_map7_event.py` | Two 5 February classes digitized from Map 7 (0.211 km², in `outputs/secocha_2023_validation/observed_hazard/`). PIM covers 66.2% of these cells; 19.1% of covered cells are High versus 15.6% study-wide. The digitized polygons have not been independently reviewed. |

## Goslar, Germany

Uses the same chain and Supervisor weights as Secocha (`bin/factors/run_goslar_peru_style_chain.py`),
compared against official regulatory flood zones (HQ100 etc.), not observed event footprints.

| Experiment | Output folder / command | Result |
|---|---|---|
| Abzucht HQ100 overlay | `compare_abzucht_hq100.py` | HQ100 mean PIM 0.475 vs 0.418 in a 1 km outside ring. |
| Expanded area and display rectangle (`frozen_scale_v1`) | `run_abzucht_expanded.py [--fill-display-rectangle]` | Extends coverage to all HQ100 cells with normalization anchors fixed from the original area. HQ100 mean 0.470, 6.06% of HQ100 cells ≥0.6. |
| Explanation figures (`explanation_v1`) | `explain_abzucht_comparison.py` | Flood criterion 0.507 inside HQ100 vs 0.373 in the ring; PIM 0.470 vs 0.419. Only 5.8% of cells have all 14 components. |
| Input gaps (`gap_repair_v1`, `input_completion_v2`) | `repair_abzucht_gaps.py`, `complete_abzucht_inputs.py` | GHSL population and 2017 SoilGrids fill the population and soil gaps in HQ100. These are source replacements, not recovered observations. |
| Weight sensitivity (`weight_sensitivity_v1`) | `tune_abzucht_weights.py` | Flood weight 34–80% tested. 80% gives the largest inside/outside gap at the 0.6 cutoff, but it is at the edge of the range and depends on the cutoff. HQ100 was used to tune, so it cannot also validate. |
| Spatial checks (`spatial_offset_v1`, `river_alignment_v1`, `atkis_dop_check_v1`) | `diagnose_abzucht_spatial_offset.py`, `check_abzucht_river_alignment.py`, `check_abzucht_atkis_dop.py` | 386 of 420 high cells lie outside HQ100. Model drainage is a median 47 m from the official Abzucht line. |
| Multi-river comparison (`multiriver_comparison_v1`, `multiriver_weights_50_60_70_v1`) | `compare_goslar_multiriver.py`, `compare_multiriver_weights.py` | Flood criterion is higher inside every covered regulatory zone; PIM is not. Raising the flood weight to 50/60/70% helps Abzucht but not Oker or Innerste. |
| Semantics audit (`component_semantics_v1`, `input_semantics_followup_v1`) | `diagnose_multiriver_low_scores.py`, `audit_multiriver_input_semantics.py` | Oker scores low on sediment and land use. "Bare soil" is really tree-cover loss and "expansion" is static proximity; field names were left unchanged. |
| Facility-distance fix (`facility_edge_repair_v1`) | `repair_multiriver_facility_edges.py` | Facilities outside the grid were being dropped; fixed with a padded grid. Innerste mean rises 0.418 → 0.448. |
| **Full multi-river extent** (`goslar_multiriver_full_extent_v1/frozen_scale_v1`) | `run_goslar_multiriver_full.py`, then `report_goslar_multiriver_full.py` | 739 km² covering all 14 official products (8 regulatory zones, 6 hydraulic scenarios); flood weights 34/50/60/70%. Within 1 km, the flood criterion is higher inside all 8 regulatory zones, but PIM is higher only for Wedde, Abzucht and Ecker. **Main open issue.** |

Goslar and Abzucht outputs are under `outputs/goslar_abzucht_display_rectangle_v1/<experiment>/`
unless named otherwise; each has a Chinese `READING_NOTE.md`. Tests:
`.venv/bin/python -m unittest discover -s tests`.
