# Upper Mzingwane Boundary Decision Package

Status: mentor-facing internal draft. Boundary not accepted.

## Purpose

This package summarizes the HydroBASINS boundary-discovery result and the follow-up Zimbabwe
Geoportal Sub-Catchments comparison for the Zimbabwe / Upper Mzingwane prototype. It turns the
area mismatch into a mentor decision question.

It is not a flood-risk map, intervention-priority map, validation result, or final model claim.
It uses the already downloaded HydroBASINS standard Africa artifact and one Zimbabwe Geoportal
Sub-Catchments Shapefile only. No SRTM, CHIRPS, HydroRIVERS, overlay, scoring, or risk
interpretation has been run.

## Short Meeting Message

I tested HydroBASINS and the Zimbabwe Geoportal Sub-Catchments layer as possible boundary sources
for the Upper Mzingwane prototype. The best single HydroBASINS candidate is level 7
`HYBAS_ID=1071528840`, `PFAF_ID=1245086`. It contains the Mzingwane Dam and Esigodini anchor
points and excludes the downstream Gwanda contrast point.

However, I do not think it should be accepted automatically. Its area is about `3700.0 km2`,
which is larger than the reported but source/geometry-unresolved `~2138 km2` Upper
Mzingwane reference that still needs outlet, area-method, and boundary-geometry checks.

The Zimbabwe Geoportal layer does contain a named `Upper Mzingwane` polygon, and it also contains
Mzingwane Dam and Esigodini while excluding Gwanda. But its area is about `7321.5 km2`, so it is
even broader than the HydroBASINS level 7 candidate. The next modelling step needs a mentor
decision on which boundary definition is intended.

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

Zimbabwe Geoportal Sub-Catchments alternative:

- Named feature: `Upper Mzingwane`
- Geodesic area: about `7321.5 km2`
- Contains Mzingwane Dam and Esigodini.
- Excludes Gwanda, which falls in the Geoportal `Shashe` feature.
- HydroBASINS level 7 `HYBAS_ID=1071528840` has about `98.9%` geometric overlap with the
  Geoportal feature, but covers only about `49.8%` of it.

This suggests a boundary-definition mismatch rather than a simple data error. The overlap values
are geometric diagnostics only; they do not prove drainage topology or modelling equivalence.

## Decision Options

### Option A: Candidate Geoportal Upper Mzingwane

If the mentor chooses this option, use the Zimbabwe Geoportal `Upper Mzingwane` polygon as a
broad local or management-style sub-catchment unit.

This option is appropriate if the study needs local named-boundary or management-unit
consistency more than global HydroBASINS comparability, and if the larger `7321.5 km2` scope is
acceptable after the layer's management or hydrological definition is confirmed.

Implication: record that the prototype boundary is a broad Geoportal named sub-catchment, not
the reported but source/geometry-unresolved `~2138 km2` study-area reference.

### Option B: Candidate HydroBASINS Level 7 With A Waiver

If the mentor chooses this option, accept `HYBAS_ID=1071528840`, `PFAF_ID=1245086` as the
working prototype boundary even though it is larger than the reported but
source/geometry-unresolved `~2138 km2` Upper Mzingwane area reference.

This option is appropriate if the first prototype should prioritize traceable workflow execution
and HydroBASINS compatibility over strict local boundary matching.

Implication: record an area-mismatch waiver before any SRTM, CHIRPS, overlay, or interpretation.

### Option C: Obtain The 2138 km2 Boundary Geometry

Find, obtain, or digitize the boundary geometry behind the reported but source/geometry-unresolved
`~2138 km2` reference.

This option is appropriate if the intended thesis case study is specifically that narrower
published-study area.

Implication: SRTM, CHIRPS, overlay, and model interpretation stay blocked until the boundary
source is identified and checked.

### Option D: Review A HydroBASINS Union

Construct a candidate union from level 8 units under `PFAF_ID=1245086`, then compare its area and
shape against local boundary evidence.

This option is appropriate if level 7 is too broad but no local boundary file is immediately
available.

Implication: this needs an explicit union rule and mentor review before it can become the working
boundary.

## Recommended Mentor Question

Which boundary should define the first Zimbabwe prototype slice?

1. Zimbabwe Geoportal `Upper Mzingwane` as a broad named sub-catchment, about `7321.5 km2`.
2. HydroBASINS level 7 `HYBAS_ID=1071528840` as a narrower hydrological unit, about `3700 km2`.
3. The narrower reported but source/geometry-unresolved `~2138 km2` boundary, if that is
   the intended published-study area.
4. A reviewed HydroBASINS union if neither single candidate is acceptable.

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
- Geoportal comparison tables:
  `outputs/zimbabwe_geoportal_subcatchments_2025/`
  `zimbabwe_geoportal_upper_mzingwane_boundary_comparison_2026-06-10.csv`
  and
  `outputs/zimbabwe_geoportal_subcatchments_2025/`
  `zimbabwe_geoportal_upper_mzingwane_hydrobasins_level7_overlaps_2026-06-10.csv`

Area and overlap method: geometries were loaded in `EPSG:4326`, intersections were computed
between candidate polygons, and areas were calculated as WGS84 geodesic areas in square
kilometres. The resulting overlaps are geometric diagnostics only.

These files are decision aids only. They should not be treated as release material until the
HydroSHEDS, Zimbabwe Geoportal, and derived-output policies are reviewed.
