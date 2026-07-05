# P2 Risk R2.5 Final Boundary Acceptance Decision Package

Date: 2026-06-15

Status: internal decision package and mentor escalation addendum. This document does not accept
any boundary, authorize any download, or authorize AHP overlay, flood-risk interpretation, or
intervention-priority interpretation. It consolidates the boundary-acceptance state and records
the remaining levers, since the public-source hunt is exhausted.

## Risk Statement

R2.5 (P2): the final thesis boundary is not accepted.

V1 / `HB_L8_1081528840_full_l7_chain` (about 3689.5 km2) is
`accepted_with_waiver_for_controlled_prototype` only. It is not the final thesis boundary. The
candidate boundaries are not equivalent and differ by up to 3.4x:

| Boundary source | Area | Geometry available? |
|---|---:|---|
| V1 HydroBASINS Level-8 chain (current working boundary) | about 3689.5 km2 | yes (waiver-only) |
| Geoportal named `Upper Mzingwane` sub-catchment | about 7321.5 km2 | yes (comparison only) |
| Literature `~2138 km2` reference | about 2138 km2 | NO reusable geometry found |

Consequence: every area-dependent quantitative result (population sum, rainfall volume,
priority-class area) is unstable until the final boundary is fixed. The V1 waiver permits
controlled prototype terrain diagnostics but blocks overlay, interpretation, and any
final-map claim.

## Why The Public-Source Hunt Is Exhausted

IFPM-043 traced the `~2138 km2` reference across modern published papers and found that authors
repeatedly report or use this area but none exposes reusable geometry, outlet point, projection,
or area method. The strongest source leads identified were:

- ZINWA's unpublished National catchment database;
- older Bulawayo/Matabeleland-Zambezi feasibility-study maps;
- Surveyor General map channels;
- author-requested study-area polygons.

All of these require direct human request (mentor, author, ZINWA, or map-holder). No further
automated public-source search is likely to yield reusable geometry for the `~2138 km2`
boundary.

## Remaining Levers

The boundary acceptance can now only move forward through one of:

1. Mentor provides the boundary polygon (the highest-value, lowest-cost lever if the mentor
   holds it or can obtain it from ZINWA or the original authors).
2. Mentor requests the polygon from the authors of a `~2138 km2`-citing paper, from ZINWA, or
   from the feasibility-study/map holders.
3. Mentor accepts V1 as the final thesis boundary (promoting it from waiver to accepted),
   with the documented area and the HydroBASINS lineage.
4. Mentor accepts the Geoportal named sub-catchment (about 7321.5 km2) as the final boundary.

Options 3 and 4 require acknowledging that the chosen boundary does not match the literature's
`~2138 km2` and documenting the discrepancy in any thesis/public output. Option 1 or 2 is
preferred because they would reconcile the V1 working boundary with the literature reference.

## Relationship To The Real-Data Gate

Per `context/docs/research-map/REPRODUCIBILITY.md` §3 IFPM-D06:

- V1 is `closed with waiver for controlled prototype SRTM terrain diagnostics only`.
- Final boundary acceptance remains open.
- The waiver does not authorize 30 m CHIRPS resampling, overlay, flood-risk interpretation, or
  intervention-priority interpretation.

Closing this P2 risk means closing IFPM-D06 for the final boundary, which in turn unblocks
sub-basin aggregation (R2.4 Branch 2) and any area-dependent reporting.

## Recommended Action

Escalate the boundary decision to the mentor as a single explicit ask, separate from the P1
risk bundle, because it has a different evidence base (the hunt is done; the lever is human
request, not more analysis):

> The public-source hunt for the `~2138 km2` boundary geometry is exhausted. Do you hold the
> Upper Mzingwane boundary polygon, or can you request it from ZINWA or the original authors?
> If not, should V1 (about 3689.5 km2) be promoted from prototype waiver to the accepted thesis
> boundary, with the area discrepancy documented?

## Decision Questions For Mentor

1. Do you hold the Upper Mzingwane boundary polygon, or can you obtain it from ZINWA / the
   original authors / the feasibility-study map holders?
2. If the polygon cannot be obtained, should V1 (about 3689.5 km2) be promoted to the accepted
   thesis boundary?
3. If V1 is accepted, is the area discrepancy with the literature `~2138 km2` reference to be
   documented as a limitation?
4. Is the Geoportal named sub-catchment (about 7321.5 km2) a viable alternative if V1 is
   rejected?

## Boundaries And Blockers

- No boundary is accepted by this document.
- No download or overlay is authorized.
- This package only consolidates the state and surfaces the mentor ask; it does not add new
  evidence.
- Promoting V1 to the final boundary requires explicit mentor sign-off and a recorded decision
  note.

## Cross-References

- Risk overview: `p2_risk_overview_2026-06-15.md`.
- Preflight gate: `context/docs/research-map/REPRODUCIBILITY.md` §3 (IFPM-D06).
- Source hunt (exhausted): `upper_mzingwane_boundary_source_hunt_2026-06-10.md`,
  `upper_mzingwane_boundary_fact_check_2026-06-10.md`.
- V1 working boundary decision: `v1_working_boundary_decision_2026-06-12.md`.
- HydroBASINS discovery: `hydrosheds_boundary_discovery_result_2026-06-10.md`.
- Geoportal comparison: `zimbabwe_geoportal_subcatchments_boundary_comparison_2026-06-10.md`.
- Decision tasks: IFPM-D06 (Upper Mzingwane boundary acceptance), IFPM-068 (this package).
