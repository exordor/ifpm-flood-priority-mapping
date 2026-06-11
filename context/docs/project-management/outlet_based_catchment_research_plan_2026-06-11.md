# Outlet-Based Catchment Research Plan

Updated: 2026-06-11

Status: internal research-plan update after mentor feedback.

## Mentor Feedback

The mentor did not treat the current problem as a simple choice between three ready-made
boundaries. Her feedback reframed the question:

- the issue is about choosing the catchment area;
- if possible, start from the outlet;
- the outlet should be where flood impact is strongest and may be linked to the mining area;
- use the catchment area near or upstream of that outlet as the first prototype study area.

Interpretation: the first prototype should be problem-led and hydrologically defined. The
boundary should not be chosen only because a named `Upper Mzingwane` polygon exists.

## Updated Research Logic

Previous framing:

1. choose between literature `~2138 km2`, HydroBASINS `~3700 km2`, or Geoportal `~7321.5 km2`;
2. use the selected polygon as the study mask.

Updated framing:

1. identify a flood/mining-relevant outlet or pour point;
2. delineate the upstream catchment for that outlet;
3. compare the resulting catchment with the existing candidate boundaries;
4. accept the outlet-based catchment, or record a waiver if a proxy boundary is used.

This means `Upper Mzingwane` can remain the regional context, while the actual prototype unit
becomes:

`upstream catchment of the selected flood/mining-relevant outlet`.

## Why This Is Better

- It ties the study area to the flood process and mining-pressure question.
- It avoids forcing equivalence between non-equivalent named boundaries.
- It gives a reproducible path once the outlet coordinate is known.
- It makes the eventual area a result of the outlet choice, not a target number to fit.
- It creates a clearer thesis method: problem point -> catchment delineation -> data clipping ->
  diagnostics -> optional weighted overlay.

## Boundary Options After Reframing

The existing boundaries are now reference layers, not automatic choices.

| Boundary concept | New role |
| --- | --- |
| Literature `~2138 km2` Upper Mzingwane | Comparison target and literature context only unless the original polygon/outlet is obtained. |
| HydroBASINS level 7 `HYBAS_ID=1071528840` | Reproducible proxy candidate and possible parent unit for outlet-based delineation. |
| Zimbabwe Geoportal `Upper Mzingwane` `~7321.5 km2` | Local named/management context and area-check comparison. |
| Future outlet-based catchment | Preferred first prototype boundary if mentor supplies or approves an outlet. |

## Immediate Information Needed

Ask the mentor for a rough outlet definition. Exact coordinates are ideal, but not required for
the first pass.

Acceptable first-pass evidence:

- a rough point on a map;
- nearby town or settlement;
- river confluence;
- dam, reservoir outlet, or gauging point;
- mining area and the downstream point where flood/sediment impact matters;
- local name of the river reach or affected area.

Minimum decision fields to record:

- outlet name or description;
- latitude/longitude if available;
- why this outlet is relevant to flood impact;
- why it is relevant to mining pressure or sediment movement;
- whether the outlet is authoritative, mentor-selected, or provisional;
- whether downstream impact beyond the outlet is inside or outside scope.

## Proposed Workflow

### Phase 1: Outlet Clarification

Goal: turn mentor feedback into one or more candidate outlet points.

Actions:

1. Ask the mentor for a rough outlet location.
2. If no coordinate is available, ask for a nearby place, dam, confluence, mine, or map mark.
3. Record the candidate outlet in a decision note without claiming it is final.
4. Do not download SRTM, CHIRPS, or run overlay in this phase.

Exit evidence:

- candidate outlet table;
- outlet rationale;
- status: `mentor-selected`, `mentor-provisional`, or `needs confirmation`.

### Phase 2: Catchment Delineation Preflight

Goal: decide how to delineate the upstream catchment after the outlet is known.

Preferred branches:

1. HydroBASINS branch:
   - snap the outlet to the nearest relevant HydroBASINS unit or pour point;
   - identify the upstream unit or reviewed union;
   - use this as a fast reproducible proxy.
2. DEM branch:
   - use a DEM and flow-direction workflow to delineate the outlet catchment;
   - only start after SRTM/DEM download preflight is closed.
3. Hybrid branch:
   - use HydroBASINS for first approximation;
   - later refine with DEM if mentor requires a tighter outlet-derived boundary.

Exit evidence:

- selected delineation branch;
- accepted outlet coordinate or provisional point;
- expected input datasets and disk footprint;
- explicit statement that no flood-risk interpretation is produced yet.

### Phase 3: Boundary Comparison

Goal: compare the outlet-based catchment against existing evidence.

Checks:

- area in square kilometres;
- overlap with HydroBASINS level 7 candidate;
- overlap with Geoportal `Upper Mzingwane`;
- distance or containment relationship to Mzingwane Dam, Esigodini, Gwanda, and mining-relevant
  anchors;
- comparison with the literature `~2138 km2` value without forcing an area match.

Exit evidence:

- diagnostic map;
- comparison table;
- decision note saying whether the outlet-based catchment is accepted, rejected, or accepted
  with waiver.

### Phase 4: First Real-Data Prototype

Only after outlet and catchment acceptance:

1. close dataset-specific preflight for the smallest required source data;
2. download only the needed SRTM/DEM and optional rainfall subset;
3. clip or aggregate to the accepted outlet-based catchment;
4. run diagnostics first;
5. produce workflow or preliminary susceptibility outputs only if all gates allow it.

## What Changes In The Thesis Framing

Before:

`Upper Mzingwane boundary selection problem`

After:

`Outlet-based flood/mining catchment definition within the Upper Mzingwane context`

Suggested thesis wording:

> The Zimbabwe prototype is located in the Upper Mzingwane context, but the operational study
> boundary is defined hydrologically from a selected outlet relevant to flood impact and
> mining-related sediment or land-use pressure.

This wording avoids claiming that the prototype exactly reproduces the literature `~2138 km2`
boundary unless that boundary is actually obtained.

## Updated No-Go Rule

SRTM, CHIRPS, overlay, and interpretation remain blocked until:

- a candidate outlet is recorded;
- the outlet's relevance to flood/mining impact is documented;
- a delineation branch is selected;
- the resulting catchment boundary is accepted or explicitly waived.

## Mentor Follow-Up Message

Short version:

```text
Yes, that helps. I understand the boundary should be defined from the outlet, not only from an
existing named polygon.

For the next step, could you point me roughly to the outlet or downstream point that is most
relevant for the flooding/mining issue? A nearby town, dam, river junction, mining area, or rough
map location is enough for a first test. I can then delineate the upstream catchment from that
point and compare it with the HydroBASINS and Geoportal options.
```

## Adversarial Review

Correctness/domain angle:

- Risk: treating `outlet-based` as a complete boundary decision before an outlet is known.
- Response: this plan treats outlet-based delineation as the preferred strategy, but keeps SRTM,
  CHIRPS, overlay, and interpretation blocked until the outlet and catchment are accepted.

Engineering/workspace angle:

- Risk: using outlet feedback to start uncontrolled downloads.
- Response: this plan keeps all real-data downloads behind the existing registry, preflight, and
  authorization gates.

Communication angle:

- Risk: asking the mentor another abstract boundary question.
- Response: the next mentor ask is concrete: provide a rough outlet, nearby place, dam,
  confluence, mine, or map point.
