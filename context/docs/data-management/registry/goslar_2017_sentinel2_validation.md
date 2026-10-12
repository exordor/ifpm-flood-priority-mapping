# Dataset Registry: Goslar July 2017 Sentinel-2 event-window validation candidate

- Dataset id: `goslar_2017_sentinel2_event_window`
- Status: downloaded and processed 2026-08-17/18; event-window context, not part of the PIM score
- Event: July 2017 Goslar/Harz flood
- Source: Copernicus Sentinel-2 L2A via Element 84 Earth Search COGs
- Scenes: `S2B_32UNC_20170721_0_L2A` (pre-event) and
  `S2B_32UNC_20170731_0_L2A` (post-event)
- Access date: 2026-08-17
- Licence: Copernicus Sentinel data terms; retain
  `Contains modified Copernicus Sentinel data`
- Reproducible command:
  `.venv/bin/python bin/acquire/pull_goslar_2017_sentinel2_validation.py`
  (Script removed 2026-10-11; recover with `git show cc4f247:bin/acquire/pull_goslar_2017_sentinel2_validation.py`.)
- Raw scene-window destination:
  `data/validation/goslar_harz_2024_focus_area/satellite_2017/scenes/`
- Derived outputs: `outputs/goslar_2017_satellite_validation/`
- Catalog snapshots:
  `data/validation/goslar_harz_2024_focus_area/satellite_2017/catalog/`

## Candidate method and QA

The derived candidate uses NDWI `(B03-B08)/(B03+B08)`, a threshold `NDWI > 0.15`,
and valid SCL classes 4-7. Outputs are clipped to
`goslar_wrrl_basin`.

Current QA:

- official basin cells: 1,537,799 at 10 m
- before-water candidates: 3,235 cells
- after-water candidates: 30,057 cells
- persistent water: 3,183 cells
- new surface-water candidates: 26,874 cells
- lost water candidates: 52 cells

Not an observed peak-flood footprint: the after scene is five days after the peak, optical
imagery cannot see through canopy or clouds, and the NDWI rule has no shadow/terrain correction.

## 2026-08-18 L2 independent-context consistency

Command:
`.venv/bin/python bin/analysis/goslar_l2_independent_consistency.py`
(Script removed 2026-10-11; recover with `git show cc4f247:bin/analysis/goslar_l2_independent_consistency.py`.)

Outputs:

- `outputs/goslar_l2_independent_consistency/l2_consistency_report.json`
- `outputs/goslar_l2_independent_consistency/l2_consistency_summary.csv`
- `outputs/goslar_l2_independent_consistency/l2_consistency_summary.md`

Result: **mixed_or_unclear**.

1. HWRM regulatory context: `consistent`; PIM mean is 0.536 inside modelled
   hazard polygons versus 0.478 outside (descriptive difference 0.058).
2. Sentinel-2 new-water candidate: `inconsistent_or_unclear`; mean PIM at the
   candidate cells is 0.460 versus 0.480 in the background.
3. Internal flood-hazard terrain/hydrology diagnostic:
   `weakly_consistent`; Spearman rho is 0.074 for TWI and -0.646 for distance
   to drainage.

No precision, recall, AUC or IoU metric is reported. The report records input SHA-256 hashes,
a fixed random seed, resampling method and bootstrap limits.

## Known gaps

- Sentinel-1 GRD coverage exists for the event window, but calibrated SAR
  processing has not been done.
- NLWKN pages expose gauge summaries; no machine-readable 2017 time series was
  found.
