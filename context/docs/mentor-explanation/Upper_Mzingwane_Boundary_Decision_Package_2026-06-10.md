# Upper Mzingwane Boundary Decision Package

Status: mentor-facing internal draft. Boundary not accepted.

## Purpose

This package summarizes the HydroBASINS boundary-discovery result for the Zimbabwe / Upper
Mzingwane prototype and turns it into a mentor decision question.

It is not a flood-risk map, intervention-priority map, validation result, or final model claim.
It uses the already downloaded HydroBASINS standard Africa artifact only. No SRTM, CHIRPS,
HydroRIVERS, overlay, scoring, or risk interpretation has been run.

## Short Meeting Message

I tested HydroBASINS as a possible boundary source for the Upper Mzingwane prototype. The best
single HydroBASINS candidate is level 7 `HYBAS_ID=1071528840`, `PFAF_ID=1245086`. It contains the
Mzingwane Dam and Esigodini anchor points and excludes the downstream Gwanda contrast point.

However, I do not think it should be accepted automatically. Its area is about `3700.0 km2`,
which is larger than the commonly reported Upper Mzingwane sub-catchment area of about
`2138 km2`. The next modelling step needs either an authoritative local boundary, a mentor
waiver accepting this HydroBASINS level 7 unit, or a reviewed level 8 union.

## Evidence Summary

Mzingwane-scale context:

- Level 6, `HYBAS_ID=1061548150`, `PFAF_ID=124508`
- `SUB_AREA=15986.1 km2`, `UP_AREA=15987.0 km2`
- Contains Mzingwane Dam and Esigodini, but is too broad for Upper Mzingwane.

Primary single-unit candidate:

- Level 7, `HYBAS_ID=1071528840`, `PFAF_ID=1245086`
- `SUB_AREA=3700.0 km2`, `UP_AREA=3700.4 km2`
- Contains Mzingwane Dam and Esigodini, and excludes the downstream Gwanda contrast point.

Downstream contrast unit:

- Level 7, `HYBAS_ID=1071542430`, `PFAF_ID=1246002`
- `SUB_AREA=7907.3 km2`, `UP_AREA=7907.4 km2`
- Contains the Gwanda contrast point.

Nested level 8 candidates:

| HYBAS_ID | PFAF_ID | SUB_AREA km2 | UP_AREA km2 | Anchor note |
| --- | ---: | ---: | ---: | --- |
| `1081520450` | `12450868` | `749.2` | `749.3` | Esigodini |
| `1081520560` | `12450869` | `546.9` | `546.9` | Mzingwane Dam |
| `1081522660` | `12450865` | `163.3` | `1885.2` | closest by upstream area |
| `1081528170` | `12450863` | `1067.4` | `3418.0` | broader candidate |

The level 7 unit is the cleanest single-unit candidate from the current anchor-point test, but it
is probably too broad if the intended study area is the narrower Upper Mzingwane sub-catchment.
No single level 8 candidate matches all current expectations.

## Decision Options

### Option A: Use An Authoritative Local Boundary

Ask for a local catchment boundary from the mentor, an official hydrological unit, or a trusted
local GIS source.

Use this if the study needs local hydrological correctness more than global HydroBASINS
comparability.

Implication: delay SRTM, CHIRPS, overlay, and model interpretation until the boundary file is
received, registered, checked, and compared.

### Option B: Accept HydroBASINS Level 7 With A Waiver

Accept `HYBAS_ID=1071528840`, `PFAF_ID=1245086` as the working prototype boundary even though it
is larger than the common Upper Mzingwane area reference.

Use this if the first prototype should prioritize traceable workflow execution and HydroBASINS
compatibility over strict local boundary matching.

Implication: record an area-mismatch waiver before any SRTM, CHIRPS, overlay, or interpretation.

### Option C: Review A Level 8 Union

Construct a candidate union from level 8 units under `PFAF_ID=1245086`, then compare its area and
shape against local boundary evidence.

Use this if level 7 is too broad but no local boundary file is immediately available.

Implication: this needs an explicit union rule and mentor review before it can become the working
boundary.

## Recommended Mentor Question

Which boundary should define the first Zimbabwe prototype slice?

1. A local or official Upper Mzingwane boundary that you can provide or point me to.
2. HydroBASINS level 7 `HYBAS_ID=1071528840` with an explicit area-mismatch waiver.
3. A reviewed level 8 HydroBASINS union under `PFAF_ID=1245086`.

Until this is decided, I will keep SRTM, CHIRPS, overlay, scoring, and risk interpretation
blocked.

## Local Diagnostic Outputs

Local-only diagnostic files were generated under ignored `outputs/` paths:

- Candidate table:
  `outputs/hydrosheds_boundary_decision/upper_mzingwane_boundary_candidate_table_2026-06-10.csv`
- Diagnostic figure:
  `outputs/hydrosheds_boundary_decision/`
  `upper_mzingwane_boundary_candidates_diagnostic_2026-06-10.png`
- Output manifest:
  `outputs/hydrosheds_boundary_decision/upper_mzingwane_boundary_decision_outputs_2026-06-10.txt`

These files are decision aids only. They should not be treated as release material until the
HydroSHEDS redistribution and derived-output policy is reviewed.
