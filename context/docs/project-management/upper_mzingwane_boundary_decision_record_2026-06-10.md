# Upper Mzingwane Boundary Decision Record

Updated: 2026-06-10

Status: decision package prepared; boundary not accepted.

## Decision State

The HydroSHEDS boundary-discovery step produced candidate HydroBASINS units, but it did not
accept a final Upper Mzingwane prototype boundary.

Current working verdict: `NO-GO` for SRTM download, CHIRPS download, overlay, scoring, map
interpretation, or flood-risk claims that depend on an accepted Upper Mzingwane boundary.

## Inputs Used

- Existing local HydroBASINS standard Africa artifact:
  `data/raw/hydrosheds_zimbabwe_prototype/hybas_af_lev01-12_v1c.zip`
- SHA-256:
  `6b331a6e89d56c3a542dcee39a7e6e8700d0cf7c94083c5946c7db0d262a48d6`
- Extracted shapefile levels inspected from ignored `data/raw/` paths.
- Anchor points: Mzingwane Dam, Esigodini, and downstream Gwanda contrast point.

No new source data was downloaded for this decision package.

## Candidate Assessment

- Level 6 `HYBAS_ID=1061548150`, `PFAF_ID=124508`:
  too broad for Upper Mzingwane.
- Level 7 `HYBAS_ID=1071528840`, `PFAF_ID=1245086`:
  plausible primary candidate, but too broad to accept automatically.
- Level 7 `HYBAS_ID=1071542430`, `PFAF_ID=1246002`:
  downstream contrast unit containing Gwanda.
- Level 8 `HYBAS_ID=1081520450`, `PFAF_ID=12450868`:
  nested candidate containing Esigodini only.
- Level 8 `HYBAS_ID=1081520560`, `PFAF_ID=12450869`:
  nested candidate containing Mzingwane Dam only.
- Level 8 `HYBAS_ID=1081522660`, `PFAF_ID=12450865`:
  closest upstream-area candidate.
- Level 8 `HYBAS_ID=1081528170`, `PFAF_ID=12450863`:
  broader nested candidate.

Primary issue: level 7 `HYBAS_ID=1071528840` has `SUB_AREA=3700.0 km2`, while the commonly
reported Upper Mzingwane sub-catchment area is about `2138 km2`. That mismatch is enough to block
automatic acceptance.

## Decision Options

1. Mentor or local authority supplies the accepted Upper Mzingwane boundary.
2. Mentor accepts HydroBASINS level 7 `HYBAS_ID=1071528840` with an area-mismatch waiver.
3. Project defines a reviewed level 8 union under `PFAF_ID=1245086` and compares it to local
   evidence.

No option has been accepted yet.

## Local Outputs

Generated local-only diagnostics:

- Candidate table:
  `outputs/hydrosheds_boundary_decision/upper_mzingwane_boundary_candidate_table_2026-06-10.csv`
- Diagnostic figure:
  `outputs/hydrosheds_boundary_decision/`
  `upper_mzingwane_boundary_candidates_diagnostic_2026-06-10.png`
- Output manifest:
  `outputs/hydrosheds_boundary_decision/upper_mzingwane_boundary_decision_outputs_2026-06-10.txt`

These outputs stay under ignored `outputs/` paths. They are not committed release assets and
must not be copied into `context/`, `ifpm-flood-pipeline/`, public docs, or release archives
without a public-safe and redistribution review.

## Actions Still Blocked

- SRTM download or clipping.
- CHIRPS download or rainfall-window processing.
- HydroRIVERS download.
- Weighted overlay using real data.
- Flood-risk, intervention-priority, or rehabilitation interpretation.
- Public release of HydroSHEDS-derived maps or geometry.

## Adversarial Review

Review mode: local two-angle fallback. Subagent delegation was not used in this turn because the
user did not explicitly request parallel subagents for this step.

Correctness and domain-boundary angle:

- Finding: the decision package could accidentally make the level 7 candidate look accepted.
- Triage: kept the status as `boundary not accepted`, repeated the area mismatch, and listed
  the three unresolved decision paths before any SRTM, CHIRPS, overlay, or interpretation.

Engineering and workspace-boundary angle:

- Finding: local diagnostic PNG and CSV files could be mistaken for release material.
- Triage: kept them under ignored `outputs/`, referenced them as local-only diagnostics, and
  documented that they must not be copied into `context/`, `ifpm-flood-pipeline/`, or release
  archives without a public-safe and redistribution review.

State-consistency angle:

- Finding: older planning notes still implied that no real data download had happened.
- Triage: updated the mentor summary, preprocessing design, task board, and preflight gate to
  distinguish the completed HydroBASINS boundary-discovery exception from still-blocked broader
  real-data downloads.

## Next Action

Use
`context/docs/mentor-explanation/Upper_Mzingwane_Boundary_Decision_Package_2026-06-10.md`
in the next mentor discussion and ask for one accepted boundary path.
