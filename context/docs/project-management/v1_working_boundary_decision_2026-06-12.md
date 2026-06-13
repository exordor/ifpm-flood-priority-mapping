# V1 Working Boundary Decision Note

Updated: 2026-06-12

Status: `accepted_with_waiver_for_controlled_prototype`. Not a final thesis boundary.

## Decision

Use V1 / `HB_L8_1081528840_full_l7_chain` as the working prototype catchment boundary for the
next controlled data-preparation step, with a prototype-only waiver.

This decision is based on the professional map review and the mentor's 2026-06-12 thumbs-up
reaction after receiving the evidence board and the statement that V1 follows the Level-8
HydroBASINS chain, includes Mzingwane Dam, and follows the main Mzingwane/Umzingwani channel
downstream toward Gwanda.

## Boundary Candidate

- Candidate id: V1
- Linked machine candidate: `HB_L8_1081528840_full_l7_chain`
- HydroBASINS target id: `1081528840`
- `NEXT_DOWN`: `1081531130`
- Area: about `3689.484 km2`
- Snapped outlet review point: longitude `29.327242`, latitude `-20.920845`
- Original machine proxy point: longitude `29.315766`, latitude `-20.937291`
- Snap distance to named Mzingwane/Umzingwani river line: about `2177.9 m`
- Working-boundary package:
  `outputs/v1_working_boundary/v1_working_boundary.gpkg`
- Boundary diagnostic:
  `outputs/v1_working_boundary/v1_boundary_diagnostic.png`

## Rationale

V1 is preferred over the earlier C1 machine prior because it better matches the mentor's wording:

- it is based on a Level-8 HydroBASINS chain;
- it keeps Mzingwane Dam in the upstream catchment;
- it follows the main Mzingwane/Umzingwani channel downstream toward Gwanda;
- it better represents reservoir influence, flood routing, mining disturbance context, and
  downstream exposure in one hydrologically meaningful working unit.

## Limits

This note does not claim that V1 is the final academic boundary for the thesis.

Open limits:

- the mentor feedback was a reaction acknowledgement, not a detailed written boundary approval;
- Geoportal Flood Prone Zones had zero intersecting features in the review envelope;
- OSM mine/quarry evidence is contextual and does not prove active mining disturbance;
- DEM-derived watershed delineation has not yet been run;
- CHIRPS and flood-risk overlay have not been run.

## Waiver

V1 is accepted only for controlled prototype data preparation. This waiver allows the project to
plan and later download a small terrain dataset for diagnostics inside the V1 working mask.

This waiver does not allow:

- final thesis boundary claims;
- CHIRPS download or rainfall-window decisions;
- AHP-MCDA overlay;
- flood-risk interpretation;
- intervention-priority interpretation.

## Generated Evidence

- `outputs/v1_working_boundary/v1_working_boundary_manifest.csv`
- `outputs/v1_working_boundary/v1_anchor_check.csv`
- `outputs/v1_working_boundary/v1_working_boundary.gpkg`
- `outputs/v1_working_boundary/v1_boundary_diagnostic.png`
- `outputs/v1_working_boundary/v1_boundary_diagnostic.pdf`

Anchor check result:

- Mzingwane Dam: inside V1.
- Esigodini: inside V1.
- Gwanda: outside V1.
- Filabusi approx: outside V1.
- West Nicholson approx: outside V1.

## Next Step

Use V1 as the mask for SRTM tile preflight only. Before any interpretation or final map claim,
keep the output labelled as prototype unless the mentor gives a clear final boundary acceptance.
