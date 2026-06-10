# Upper Mzingwane Boundary Decision Record

Updated: 2026-06-10

Status: HydroBASINS and Zimbabwe Geoportal candidates compared; boundary not accepted.

## Decision State

The HydroSHEDS boundary-discovery step produced candidate HydroBASINS units. A follow-up
Zimbabwe Geoportal Sub-Catchments comparison found a named `Upper Mzingwane` feature. Neither
step accepts a final Upper Mzingwane prototype boundary.

Current working verdict: `NO-GO` for SRTM download, CHIRPS download, overlay, scoring, map
interpretation, or flood-risk claims that depend on an accepted Upper Mzingwane boundary.

## Inputs Used

- Existing local HydroBASINS standard Africa artifact:
  `data/raw/hydrosheds_zimbabwe_prototype/hybas_af_lev01-12_v1c.zip`
- SHA-256:
  `6b331a6e89d56c3a542dcee39a7e6e8700d0cf7c94083c5946c7db0d262a48d6`
- Extracted shapefile levels inspected from ignored `data/raw/` paths.
- Anchor points: Mzingwane Dam, Esigodini, and downstream Gwanda contrast point.
- Zimbabwe Geoportal Sub-Catchments artifact:
  `data/raw/zimbabwe_geoportal_subcatchments_2025/sub_catchments-1761163234.zip`
- Zimbabwe Geoportal SHA-256:
  `fb5a3528ca677f420e5030f146a7699027e93c765fcebe7ef45a59611b6f0cd2`
- Extracted Geoportal Shapefile inspected from ignored `data/raw/` paths.

No SRTM, CHIRPS, HydroRIVERS, validation data, overlay input, map output, or interpretation
dataset has been downloaded or processed for this decision package.

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

Primary issue: level 7 `HYBAS_ID=1071528840` has `SUB_AREA=3700.0 km2`, while the untraced
`~2138 km2` Upper Mzingwane reference still needs source, outlet, area-method, and
boundary-definition checks. That mismatch is enough to block automatic acceptance.

Zimbabwe Geoportal alternative:

- The Sub-Catchments layer contains a named `Upper Mzingwane` polygon.
- It contains Mzingwane Dam and Esigodini.
- It does not contain Gwanda; Gwanda falls in the Geoportal `Shashe` feature.
- It is valid polygon geometry in `EPSG:4326`.
- Its geodesic area is about `7321.5 km2`.
- HydroBASINS level 7 `HYBAS_ID=1071528840` has about `98.9%` geometric coverage by it, but
  covers only about `49.8%` of the Geoportal `Upper Mzingwane` feature.

Updated issue: the Geoportal feature is a stronger local named-boundary candidate, but it is
larger than both the HydroBASINS level 7 candidate and the untraced `~2138 km2` reference. The
likely problem is boundary-definition scope, not a simple download or geometry error. The overlap
values are geometric diagnostics only; they do not prove drainage topology or modelling
equivalence.

## Decision Options

1. Mentor or local authority supplies the accepted Upper Mzingwane boundary.
2. Mentor accepts Geoportal `Upper Mzingwane` as a broad local or management-style unit.
3. Mentor accepts HydroBASINS level 7 `HYBAS_ID=1071528840` as a narrower hydrological unit,
   with an area and coverage waiver.
4. Project traces the source of the untraced `~2138 km2` reference and obtains or digitizes the
   corresponding boundary.
5. Project defines a reviewed level 8 or level 7 union and compares it to local evidence.

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
- Geoportal comparison table:
  `outputs/zimbabwe_geoportal_subcatchments_2025/`
  `zimbabwe_geoportal_upper_mzingwane_boundary_comparison_2026-06-10.csv`
- HydroBASINS level 7 overlap table:
  `outputs/zimbabwe_geoportal_subcatchments_2025/`
  `zimbabwe_geoportal_upper_mzingwane_hydrobasins_level7_overlaps_2026-06-10.csv`

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

Review mode: subagent-assisted adversarial review plus local final pass.

Correctness and domain-boundary angle:

- Finding: the decision package could accidentally make the level 7 HydroBASINS candidate or the
  named Geoportal feature look accepted; wording that implied stronger hydrological authority
  overstated the Geoportal evidence.
- Triage: kept the status as `boundary not accepted`, described Geoportal as a local named or
  management-unit candidate, repeated both area mismatches, and listed unresolved decision paths
  before any SRTM, CHIRPS, overlay, or interpretation.

Engineering and workspace-boundary angle:

- Finding: local diagnostic PNG and CSV files, the real Shapefile, and the direct resource URL
  could be mistaken for release material.
- Triage: kept raw data under ignored `data/raw/`, kept diagnostics under ignored `outputs/`,
  referenced them as local-only diagnostics, labelled the direct resource URL as internal
  reproducibility evidence only, and documented that data or outputs must not be copied into
  `context/`, `ifpm-flood-pipeline/`, or release archives without a public-safe and
  redistribution review.

State-consistency angle:

- Finding: older planning notes could imply that no local boundary comparison had happened.
- Triage: updated this decision record, the task board, the real-data gate, and the
  Geoportal-specific registry/preflight notes to distinguish the completed boundary-comparison
  exception from still-blocked broader real-data downloads.

Reproducibility angle:

- Finding: area and overlap numbers needed a clear method statement.
- Triage: recorded the WGS84 geodesic area method in the Geoportal comparison and preflight
  notes and labelled overlaps as geometric diagnostics only.

## Next Action

Trace the source of the untraced `~2138 km2` reference or use
`context/docs/project-management/zimbabwe_geoportal_subcatchments_boundary_comparison_2026-06-10.md`
in the next mentor discussion to ask which boundary definition is intended.
