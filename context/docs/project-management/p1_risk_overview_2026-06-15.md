# P1 Risk Overview And Claim Boundary Strategy

Date: 2026-06-15

Status: internal index and strategy note for the three P1 (blocking) risks identified in the
2026-06-15 project risk analysis. This document does not authorize any download, AHP overlay,
flood-risk interpretation, or intervention-priority interpretation. It links the three P1
decision packages, records the claim-boundary fallback strategy, and lists the decision questions
to surface to the mentor.

## Purpose

The 2026-06-15 risk analysis identified three P1 blocking risks whose resolution determines
whether the project can move from a synthetic-tested pipeline to an interpretable real-data
deliverable. All three are decision-type blockers, not engineering tasks. They cannot be
self-resolved by the HiWi under the AGENTS.md modelling-claim boundary. This overview exists so a
reviewer can see the three risks, their packages, their fallbacks, and the mentor asks in one
place.

## P1 Risk Register

### R1.1 Validation Data Effectively Zero

- Risk: no local validation evidence. DFO has 0 V1 points; Geoportal Flood Prone Zones 0
  features; no EM-DAT/GloFAS/Copernicus EMS; no flood-extent polygons; no sediment observations.
- Consequence: deliverables can only be priority/suitability maps, not validated flood-risk maps.
- Decision package: `p1_validation_data_decision_package_2026-06-15.md`.
- Preflight scaffolding (public-safe Tier A candidates, NOT authorized):
  - `context/docs/data-management/registry/emdat_public_validation_candidate.md`
  - `context/docs/data-management/preflight/emdat_public_validation_candidate.md`
  - `context/docs/data-management/registry/glofas_public_validation_candidate.md`
  - `context/docs/data-management/preflight/glofas_public_validation_candidate.md`
- Self-resolvable: partially. Tier A public sources are downloadable but likely low V1 spatial
  precision. Tier B (Sentinel-1 SAR) needs engineering plus a confirmed event date. Tier C
  (ZINWA/DMS/local) needs mentor introduction.
- Default fallback: reframe to priority/suitability map with acknowledged validation gap.

### R1.2 Mining / ASM Data Critically Insufficient

- Risk: only 2 weak OSM proxy polygons; no Zimbabwe Geological Survey, MMMD, EMA, or ZINWA
  mining data; no Sentinel-2 disturbance mapping; Peru mining data entirely absent.
- Consequence: two of seven AHP criteria (Mining Location & Intensity; Rehabilitation Potential)
  have no defensible quantitative evidence. Project title's "artisanal mining" framing is at
  risk.
- Decision package: `p1_mining_data_decision_package_2026-06-15.md`.
- Mentor request template: `Mining_Data_Access_Request_Template_2026-06-15.md`.
- Self-resolvable: no. Highest-value local sources are non-public. Sentinel-2 derivation needs a
  domain rule and validation sample from the mentor.
- Default fallback: demote Mining and Rehabilitation from quantitative AHP criteria to
  qualitative/context evidence; restate the V1 hierarchy as a reduced criteria set.

### R1.3 AHP Weights Have No Expert Source

- Risk: only a synthetic test matrix exists; no expert pairwise comparisons; no protocol; no
  sensitivity scenario. P2-2 warned the synthetic matrix could become de facto expert judgement.
- Consequence: any real-data overlay would produce a plausible-looking but indefensible priority
  map.
- Decision package: `p1_ahp_weighting_decision_package_2026-06-15.md`.
- Elicitation instrument: `AHP_Elicitation_Protocol_And_Template_2026-06-15.md` (includes blank
  template and a NON-AUTHORITATIVE illustrative structural prior; CR verified at 0.0406).
- Self-resolvable: no. AHP weights encode expert judgement and cannot be supplied by the HiWi.
- Default fallback: keep the pipeline runnable on synthetic data only; label all outputs as
  workflow diagnostics.

## Consolidated Claim Boundary Strategy

The three fallbacks share one principle: **if a P1 blocker cannot be closed with real evidence
before the deadline, narrow the claim, do not fake the evidence.**

| Scenario | Deliverable claim | What outputs may show | What outputs must NOT claim |
|---|---|---|---|
| All three P1 closed | Validated flood & sediment priority map | Real-data overlay, priority classes, validation metrics | Absolute flood probability, engineering design depths |
| R1.3 closed, R1.1+R1.2 open | Multi-criteria priority/suitability map (no validation, reduced or full criteria) | Real-data overlay with expert weights, labelled "no independent validation" | Validated risk, intervention plan, mining footprint truth |
| R1.3 open | Synthetic workflow diagnostics only | Pipeline outputs on synthetic fixtures, methodology walk-through | Any real-data priority map, any interpretable result |
| R1.2 open (mining demoted) | Reduced-criteria priority map | 5-criteria overlay (Flood, Sediment, LandUse/Exposed, Environmental, Socioeconomic) | Mining-intervention plan, rehabilitation suitability as scored criterion |

This strategy is consistent with:
- root `AGENTS.md` modelling-claim boundary;
- `ifpm-flood-pipeline/AGENTS.md` modelling-claim boundary;
- the real-data execution preflight gate NO-GO state for overlay and interpretation;
- the public-safe gate for any future `docs_public/` material.

## What This Package Does NOT Do

- It does not authorize any real download. Tier A preflight drafts require Step S3 authorization
  and mentor scope confirmation first.
- It does not authorize any AHP overlay on real data. That remains blocked by IFPM-D01/D06 and
  Step S5 and IFPM-D03/D04/D05.
- It does not promote the illustrative AHP prior to `configs/`. It stays internal and
  non-authoritative.
- It does not accept any boundary. V1 remains `accepted_with_waiver_for_controlled_prototype`.
- It does not start Peru-side work. Peru remains blocked by IFPM-D02.

## Mentor Decision Bundle

The three packages surface the following consolidated mentor asks. Present them together so the
mentor can sequence them:

1. R1.1-Q1 to Q4: does the mentor/ZINWA/DCP hold flood-extent polygons, gauge records, or impact
   reports for Upper Mzingwane 1985-2024? Is validation a hard thesis requirement, or is a
   priority/suitability map acceptable?
2. R1.2-Q1 to Q5: can the mentor introduce ZGS/MMMD/EMA/ZINWA contacts, or hold ASM site lists?
   What rule separates concessions from active disturbance (IFPM-D05)? If no official mining
   data, is a reduced-criteria V1 map acceptable?
3. R1.3-Q1 to Q5: will the mentor supply or delegate the AHP pairwise matrix? Is the 7-criteria
   hierarchy still intended, or should it be revised? What CR threshold and sensitivity
   scenarios are required?

## New Tracking Tasks

- IFPM-061: P1 R1.1 validation data decision package (this overview + R1.1 package + EM-DAT/GloFAS
  scaffolding). Status: decision package complete; awaits mentor answers; Tier A downloads still
  gated.
- IFPM-062: P1 R1.2 mining data decision package + mentor request template. Status: decision
  package complete; awaits mentor introduction or fallback confirmation.
- IFPM-063: P1 R1.3 AHP weighting decision package + elicitation protocol + non-authoritative
  illustrative prior (CR 0.0406). Status: instrument complete; awaits expert elicitation.

## Verification Performed

- Illustrative structural prior CR verified locally via numpy principal-eigenvalue method:
  lambda_max = 7.32188, CI = 0.05365, CR = 0.0406 (<= 0.1), reciprocal OK. This confirms the
  matrix is structurally consistent and safe to show to an expert as a starting point. It does
  NOT make it authoritative.
- No real data was downloaded.
- No files were written to `ifpm-flood-pipeline/`, `data/`, or `outputs/` by this package.
- All new files are under `context/`.

## Cross-References

- Source risk analysis: 2026-06-15 in-session project risk and data-gap analysis.
- Preflight gate: `real_data_execution_preflight_gate.md`.
- Task board: `task_progress_board.md`.
- Packages: `p1_validation_data_decision_package_2026-06-15.md`,
  `p1_mining_data_decision_package_2026-06-15.md`,
  `p1_ahp_weighting_decision_package_2026-06-15.md`.
- Instruments: `Mining_Data_Access_Request_Template_2026-06-15.md`,
  `AHP_Elicitation_Protocol_And_Template_2026-06-15.md`.
