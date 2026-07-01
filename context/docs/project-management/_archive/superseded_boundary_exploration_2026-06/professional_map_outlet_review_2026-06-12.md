# Professional Map Outlet Review

Updated: 2026-06-12

Status: V1 accepted with waiver for controlled prototype use. No final thesis boundary is accepted.

## Purpose

This note corrects the previous script-first interpretation. The C1-C7 HydroBASINS outputs are
now treated as machine-derived topology priors only. The next boundary discussion should start
from professional map interpretation and the mentor's latest cue:

> Level-8 basin containing Mzingwane Dam and the main Mzingwane River channel downstream toward
> Gwanda.

## Data Used

Downloaded and verified for this visual review:

- HydroRIVERS Africa Shapefile:
  `data/raw/hydrorivers_africa_visual_review/HydroRIVERS_v10_af_shp.zip`
- Geofabrik Zimbabwe OSM GPKG:
  `data/raw/geofabrik_osm_zimbabwe_prototype/zimbabwe-latest-free.gpkg.zip`
- Zimbabwe Geoportal Rivers and Flood Prone Zones:
  `data/raw/zimbabwe_geoportal_candidate_outlet_layers/`

Prepared review layers:

- HydroRIVERS review lines: 589 features.
- Geoportal Rivers: 83 river lines and 8 water areas in the review envelope.
- OSM: 885 waterways, 6497 roads, 52 places, 201 POIs, 790 landuse polygons, and 232 water
  features in the review envelope.
- Geoportal Flood Prone Zones: 0 features intersect the review envelope.

No CHIRPS overlay or flood-risk interpretation was run. DEM-based delineation remains deferred
because the current decision need is mentor validation of a Level-8 outlet/catchment concept, not
an independent terrain-derived watershed claim.

## Mentor Feedback Received

On 2026-06-12, the mentor was sent the evidence board with the plain-language statement:

> V1 follows the Level-8 HydroBASINS chain, includes Mzingwane Dam, and follows the main
> Mzingwane/Umzingwani channel downstream toward Gwanda.

The mentor responded with a thumbs-up reaction. Treat this as enough support for
`accepted_with_waiver_for_controlled_prototype`. It is not by itself a formal final thesis
boundary approval.

## Visual Candidates

| Visual id | Linked prior | Role | Area km2 | Interpretation |
| --- | --- | --- | ---: | --- |
| V1 | `HB_L8_1081528840_full_l7_chain` | primary mentor-review candidate | 3689.5 | Best current interpretation of the mentor cue: L8-based upstream chain containing Mzingwane Dam and routing down the main Mzingwane/Umzingwani channel toward Gwanda. |
| V2 | `HB_L8_1081528170_broader_nested` | upstream alternative | 3408.0 | Captures reservoir influence and main-channel routing but has less downstream exposure near Gwanda than V1. |
| V3 | `HB_L8_1081522660_literature_near` | machine prior only | 1879.9 | Former C1. Area is closer to the unresolved literature value, but it does not match the new downstream-exposure cue. |
| V4 | nearest mapped Mzingwane/Umzingwani river section near Gwanda | impact reach reference | n/a | Useful for discussing downstream exposure, but not by itself an upstream catchment boundary. |
| V5 | Geoportal Upper Mzingwane | context only | 7321.5 | Useful named management context, but too broad and has no HydroBASINS outlet topology. |

V1, V2, and V3 have been snapped from their machine outlet-proxy boundary points to the nearest
named Mzingwane/Umzingwani river line for visual review. The original machine proxy coordinates
and snap distances are preserved in `visual_outlet_candidates.csv`.

## Outputs

Local-only outputs under ignored `outputs/professional_outlet_review/`:

- `mentor_outlet_evidence_board.png`
- `mentor_outlet_evidence_board.pdf`
- `visual_outlet_candidates.csv`
- `visual_outlet_candidates.gpkg`
- `professional_outlet_review_layers.gpkg`
- `prepared_layer_counts.csv`
- `source_manifest.csv`

## Current Interpretation

Use V1 as the working prototype boundary for controlled terrain preflight, not as a final
accepted thesis boundary.

Why:

- It follows the mentor's Level-8 wording better than the previous C1.
- It keeps Mzingwane Dam in the upstream catchment.
- It follows the main Mzingwane/Umzingwani river channel downstream toward the Gwanda exposure
  area.
- It is based on a reproducible HydroBASINS L8 chain while being visually snapped to a named
  river line for map review.

Remaining limitations:

- The downloaded Geoportal Flood Prone Zones layer does not intersect the review envelope, so it
  cannot support local flood-impact placement.
- OSM mine/quarry evidence is only contextual; it does not prove active mining disturbance.
- The mentor reaction supports moving V1 from `mentor-review candidate` to
  `accepted_with_waiver_for_controlled_prototype`.
- The waiver supports controlled terrain preflight only. CHIRPS, overlay, interpretation, and
  final thesis boundary acceptance still need separate decisions.

## Current Next Step

Use the V1 working boundary package for SRTM tile/download preflight only.

The next mentor question, if needed, should not ask again whether V1 exists; it should ask whether
the prototype-only waiver can later be upgraded to a final thesis boundary after the DEM and
diagnostic checks are reviewed.
