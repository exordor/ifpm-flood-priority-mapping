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

I tested two public boundary sources for the Upper Mzingwane prototype: the HydroBASINS database
and the Zimbabwe Geoportal Sub-Catchments layer. The best single HydroBASINS candidate is its
level-7 catchment that contains Mzingwane Dam and Esigodini and excludes the downstream town of
Gwanda.

However, I do not think it should be accepted automatically. Its area is about `3700 km2`, which
is larger than the reported but source-unresolved `~2138 km2` Upper Mzingwane reference that
still needs outlet, area-method, and boundary-geometry checks.

The Zimbabwe Geoportal layer does contain a named `Upper Mzingwane` polygon, and it also contains
Mzingwane Dam and Esigodini while excluding Gwanda. But its area is about `7321 km2`, so it is
even broader than the HydroBASINS candidate. The next modelling step needs a mentor decision on
which boundary definition is intended.

## Evidence Summary

Mzingwane-scale context:

- The HydroBASINS level-6 basin covering the wider Mzingwane area.
- Area about `15986 km2`.
- Contains Mzingwane Dam and Esigodini, but is far too broad for Upper Mzingwane.

Primary single-unit candidate:

- The HydroBASINS level-7 catchment upstream of the Mzingwane Dam area.
- Area about `3700 km2`.
- Contains Mzingwane Dam and Esigodini, and excludes the downstream Gwanda contrast point.

Downstream contrast unit:

- The adjacent HydroBASINS level-7 catchment further downstream.
- Area about `7907 km2`.
- Contains the Gwanda contrast point.

Nested level-8 sub-catchments (smaller units inside the level-7 candidate):

| Anchor / note | Sub-catchment area km2 | Upstream area km2 |
| --- | ---: | ---: |
| contains Esigodini | `749` | `749` |
| contains Mzingwane Dam | `547` | `547` |
| closest by upstream area | `163` | `1885` |
| broader candidate | `1067` | `3418` |

The level-7 unit is the cleanest single-unit candidate from the current anchor-point test, but it
is probably too broad if the intended study area is the narrower Upper Mzingwane sub-catchment.
No single level-8 sub-catchment matches all current expectations.

Zimbabwe Geoportal Sub-Catchments alternative:

- Named feature: `Upper Mzingwane`
- Geodesic area: about `7321 km2`
- Contains Mzingwane Dam and Esigodini.
- Excludes Gwanda, which falls in the Geoportal `Shashe` feature.
- The HydroBASINS level-7 candidate has about `98.9%` geometric overlap with the Geoportal
  feature, but covers only about `49.8%` of it.

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

If the mentor chooses this option, accept the HydroBASINS level-7 catchment as the working
prototype boundary even though it is larger than the reported but source-unresolved `~2138 km2`
Upper Mzingwane area reference.

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

Construct a candidate union from the level-8 sub-catchments inside the level-7 candidate, then
compare its area and shape against local boundary evidence.

This option is appropriate if level 7 is too broad but no local boundary file is immediately
available.

Implication: this needs an explicit union rule and mentor review before it can become the working
boundary.

## Recommended Mentor Question

Which boundary should define the first Zimbabwe prototype slice?

1. Zimbabwe Geoportal `Upper Mzingwane` as a broad named sub-catchment, about `7321 km2`.
2. The HydroBASINS level-7 catchment as a narrower hydrological unit, about `3700 km2`.
3. The narrower reported but source-unresolved `~2138 km2` boundary, if that is the intended
   published-study area.
4. A reviewed HydroBASINS union if neither single candidate is acceptable.

Until this is decided, I will keep SRTM, CHIRPS, overlay, scoring, and risk interpretation
blocked.

## Supporting Material

I have a candidate table and a diagnostic map showing the boundary options against the anchor
points (Mzingwane Dam, Esigodini, Gwanda). I can share them in the meeting. The areas above are
WGS84 geodesic areas in square kilometres, and the overlap values are geometric diagnostics only
— they do not prove drainage topology or modelling equivalence.

These are decision aids, not release material.

---

## Appendix: Database Identifiers (For Traceability Only)

The human-readable labels above map to these HydroBASINS database identifiers. They are kept
here for engineering traceability; the mentor does not need them.

| Label used above | HYBAS_ID | PFAF_ID |
| --- | --- | --- |
| Mzingwane-scale level-6 context | 1061548150 | 124508 |
| Primary level-7 candidate | 1071528840 | 1245086 |
| Downstream contrast level-7 unit | 1071542430 | 1246002 |
| level-8 sub-catchment (Esigodini) | 1081520450 | 12450868 |
| level-8 sub-catchment (Mzingwane Dam) | 1081520560 | 12450869 |
| level-8 sub-catchment (closest upstream) | 1081522660 | 12450865 |
| level-8 sub-catchment (broader candidate) | 1081528170 | 12450863 |

